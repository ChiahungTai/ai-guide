"""dutymail 信箱 monitor hook 測試（AIR-254.4——AIR-233 提醒面降級重寫）。

涵蓋（工單覆蓋面）：
- hold 偵測：duty-receive per-session state 在場（token＋epoch＋address 對上）
  且 holder status bindingEpoch==state.epoch 且 live=true → 本 session
  holding → 靜默＋游標推進至 head（查 events 拿最新 retained cursor 存入，
  不輸出）；epoch 不符／live=False／status 失敗 → 未 hold（advisory 路徑）。
- 未 hold advisory：events --kind accepted 自 session 本地游標起新事件
  N>0 → 一行 advisory（「本 session 未 hold——新到 N 封信（recovery
  window…）」）＋游標推進（advance-after-emit——commit 由呼叫端在 stdout
  寫出後執行）；N=0 → 靜默（游標已在 head，零推進需求零寫入）。
- 冷啟動（無游標）：掃到 head 只建游標靜默（防歷史洪水）；空 timeline
  無游標可建（零寫入）。
- 分頁：有 items 頁恆帶非 null nextCursor 續翻、空頁（nextCursor=null）
  終止；頁數上限（10）raise → fail-soft 不 emit 不推進。
- eligibility gate：cwd 在 script repo 外／缺席 → 零查詢零輸出零推進；
  缺 session_id → 零查詢（session-local 游標無 key）。
- fail-soft：store 缺席（storage class）／face 失敗／壞 JSON／未知事件 →
  零 stdout exit 0＋stderr 註記；args 誤用 exit 2；游標推進失敗寧重不漏。
- session 隔離：兩 session 游標互不干擾（per-session state 檔）＋hold
  判定 per-session（s1 holding 不使 s2 靜默）。
- 舊全域 scbus-address-monitor 檔零讀取：模組 source 零 scbus 字樣（
  路徑常數缺席）＋monitor state 落 duty-monitor/<safe_session_id>.json。
- monitor ≠ holder：呼叫面僅 events／holder status 唯讀——零 bind／
  prepare／ack（三軸不互代理）。
- governance 接線：zcode/cc 模板雙事件獨立 group（新拓撲：UPS groups＝
  compact-restore-inject＋duty-receive＋duty-mailbox-monitor）＋manifest
  inventory 換名＋舊名全面退役；install merge 面新 group append、既有條目
  零動、冪等、uninstall 只拆本套件 group。

測試全走 injectable runner（fake dutymail 回固定 JSON）＋fake state 路徑
（tmp_path）——不碰真 store（真 store 往返＝工單真實資料五步）。
"""

import io
import json
import os
import sys

import pytest
from conftest import REPO_ROOT, load_module

mod = load_module("hooks/duty_mailbox_monitor.py")
gov = load_module("governance/install.py")

ADDRESS = "ai-guide-marshal"
REPO = "/fake/ai-guide/repo"


def _stdin(event="UserPromptSubmit", cwd=REPO, session_id="sess-1"):
    return json.dumps(
        {"hook_event_name": event, "session_id": session_id, "cwd": cwd}
    )


UPS_STDIN = _stdin()
SS_STDIN = _stdin(event="SessionStart")


@pytest.fixture(autouse=True)
def _gate(monkeypatch):
    """eligibility gate 鎖定測試 repo——預設 stdin cwd 即鎖內。"""
    monkeypatch.setattr(mod, "script_repo_root", lambda: REPO)


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "state" / "monitor" / "sess-1.json")


@pytest.fixture
def holder_dir(tmp_path):
    return str(tmp_path / "holder")


# ── fake dutymail（typed contract：成功 stdout 一個 JSON；失敗 raise）──


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


def _events_doc(seqs, next_cursor):
    """events face 頁（dutymail 3.1.0 凍結形）：items[]＋nextCursor。

    payloadJson 帶可辨識秘密字串——釘 count-only 語義（item 內容絕不進輸出）。
    """
    items = [
        {
            "atUs": 1000 + i,
            "eventSeq": seq,
            "kind": "accepted",
            "payloadJson": json.dumps(
                {"envelopeId": f"env-{seq}", "secret": f"TOP-SECRET-{seq}"}
            ),
        }
        for i, seq in enumerate(seqs)
    ]
    return _ok({"items": items, "nextCursor": next_cursor})


def _status_doc(epoch=4, live=False):
    return _ok({
        "addressId": "a1", "alias": ADDRESS, "bindingEpoch": epoch,
        "leaseExpiresAtUs": 0, "live": live,
    })


def _page_runner(pages):
    """injectable runner：pages 依呼叫序回傳（str stdout 或 Exception）。"""
    calls = []

    def run(argv):
        calls.append(list(argv))
        page = pages[len(calls) - 1]
        if isinstance(page, Exception):
            raise page
        return page

    run.calls = calls
    return run


def _seed_holder_state(holder_dir, session_id="sess-1", epoch=4,
                       token="tok-holder", address=ADDRESS):
    """duty-receive per-session holder state（monitor 只讀它的形）。"""
    os.makedirs(holder_dir, exist_ok=True)
    path = os.path.join(holder_dir, session_id + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "address": address, "epoch": epoch, "token": token,
                "bound_at_iso": "2026-10-05T00:00:00+00:00",
            },
            fh,
        )
    return path


def _seed_monitor_state(state_file, cursor, address=ADDRESS):
    """seed 游標檔（merge 進既有 doc——同檔多門牌場景不互相覆寫）。"""
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    doc = {"addresses": {}}
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
            if isinstance(loaded, dict) and isinstance(
                loaded.get("addresses"), dict
            ):
                doc = loaded
    doc["addresses"][address] = {"events_cursor": cursor}
    with open(state_file, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def _read_state(state_file):
    with open(state_file, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _monitor_cursor(state_file, address=ADDRESS):
    doc = _read_state(state_file)
    return doc["addresses"][address]["events_cursor"]


# ── hold 偵測：holding 靜默＋游標推進至 head ──────────────────────────


class TestHoldDetection:
    def test_holding_silent_cursor_to_head(self, state_file, holder_dir):
        """本 session holding（state epoch==status epoch＋live）→ 零輸出、
        游標推進至 head（查 events 拿最新 retained cursor，不輸出）。"""
        _seed_monitor_state(state_file, "cur-0")
        _seed_holder_state(holder_dir, epoch=4)
        runner = _page_runner([
            _status_doc(epoch=4, live=True),
            _events_doc([4, 5], "cur-5"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out) == (0, "")
        assert commit is not None
        commit()
        assert _monitor_cursor(state_file) == "cur-5"
        assert runner.calls[0] == ["holder", "status", "--address", ADDRESS]

    def test_holding_cold_cursor_still_silent(self, state_file, holder_dir):
        """holding＋冷啟動（無游標）→ 同樣靜默建游標（head 掃描）。"""
        _seed_holder_state(holder_dir, epoch=7)
        runner = _page_runner([
            _status_doc(epoch=7, live=True),
            _events_doc([1], "cur-1"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out) == (0, "")
        commit()
        assert _monitor_cursor(state_file) == "cur-1"

    def test_holding_already_at_head_no_write(self, state_file, holder_dir):
        """holding 且游標已在 head（空頁）→ 零推進需求：commit=None、檔不動。"""
        _seed_monitor_state(state_file, "cur-3")
        _seed_holder_state(holder_dir, epoch=4)
        runner = _page_runner([
            _status_doc(epoch=4, live=True),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert _monitor_cursor(state_file) == "cur-3"

    def test_epoch_mismatch_not_holding_advisory(self, state_file,
                                                 holder_dir):
        """status epoch != state epoch（他方換代）→ 未 hold → advisory。"""
        _seed_monitor_state(state_file, "cur-0")
        _seed_holder_state(holder_dir, epoch=3)
        runner = _page_runner([
            _status_doc(epoch=9, live=True),  # 別的 session 持有
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out

    def test_live_false_not_holding_advisory(self, state_file, holder_dir):
        """live=False（lease 過期）→ 未 hold → advisory。"""
        _seed_monitor_state(state_file, "cur-0")
        _seed_holder_state(holder_dir, epoch=4)
        runner = _page_runner([
            _status_doc(epoch=4, live=False),
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out

    def test_status_failure_falls_to_not_holding(self, state_file,
                                                 holder_dir):
        """status face 失敗 → 未 hold（4b）——events 照查、advisory 照出
        （status 失敗不毒化本輪）。"""
        _seed_monitor_state(state_file, "cur-0")
        _seed_holder_state(holder_dir, epoch=4)
        runner = _page_runner([
            mod.core.DutymailFaceError(
                code="store-incompatible", error_class="storage",
                message="boom", retryable=False, exit_code=4,
            ),
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert code == 0
        assert "新到 1 封信" in out
        commit()
        assert _monitor_cursor(state_file) == "cur-4"

    def test_no_holder_state_skips_status_call(self, state_file, holder_dir):
        """無 duty-receive state → 直接 events（零 holder status 呼叫）。"""
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out
        assert runner.calls[0][0] == "events"

    def test_holder_state_address_mismatch_skips_status(self, state_file,
                                                        holder_dir):
        """holder state 屬他門牌（--address 多門牌場景）→ 不代判 holding。"""
        _seed_monitor_state(state_file, "cur-0", address="b-marshal")
        _seed_holder_state(holder_dir, epoch=4, address="b-marshal")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, _out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert runner.calls[0][0] == "events"  # 零 status 呼叫


# ── 未 hold advisory：一行＋游標推進（advance-after-emit）────────────


class TestNotHoldingAdvisory:
    def test_advisory_line_exact_wording_and_count(self, state_file,
                                                   holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4, 5], "cur-5"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert code == 0
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        ctx = doc["hookSpecificOutput"]["additionalContext"]
        assert ctx == (
            "[duty-monitor] " + ADDRESS + "：本 session 未 hold——新到 2 封信"
            "（recovery window；開 duty session 處理或 `dutymail receive"
            " status` 查看待處理）"
        )
        # 呼叫面凍結：events＋--kind accepted＋--limit＋--cursor（分頁續翻）
        assert runner.calls[0] == [
            "events", "--address", ADDRESS, "--kind", "accepted",
            "--limit", "100", "--cursor", "cur-0",
        ]
        assert runner.calls[1][runner.calls[1].index("--cursor") + 1] == "cur-5"
        commit()
        assert _monitor_cursor(state_file) == "cur-5"

    def test_advance_after_emit_not_before(self, state_file, holder_dir):
        """游標推進只發生在 commit()（stdout 寫出後）——run() 返回當下未動。"""
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-9"),
            _events_doc([], None),
        ])
        _code, _out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert commit is not None
        assert _monitor_cursor(state_file) == "cur-0"
        commit()
        assert _monitor_cursor(state_file) == "cur-9"

    def test_sessionstart_event_name(self, state_file, holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out, _commit = mod.run(
            SS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "SessionStart"

    def test_grok_snake_event_value_normalized(self, state_file, holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        raw = json.dumps(
            {"hookEventName": "user_prompt_submit", "sessionId": "sess-1",
             "cwd": REPO}
        )
        _code, out, _commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "UserPromptSubmit"

    def test_zero_new_silent_state_untouched(self, state_file, holder_dir):
        """N=0 → 靜默——游標已在 head（空頁＝無新 token），零寫入。"""
        _seed_monitor_state(state_file, "cur-3")
        runner = _page_runner([_events_doc([], None)])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert _monitor_cursor(state_file) == "cur-3"

    def test_multiple_addresses_two_lines_both_advance(self, state_file,
                                                       holder_dir):
        _seed_monitor_state(state_file, "cur-0", address="a-marshal")
        _seed_monitor_state(state_file, "cur-0", address="b-marshal")
        runner = _page_runner([
            _events_doc([4], "a-end"),
            _events_doc([], None),
            _events_doc([5, 6], "b-end"),
            _events_doc([], None),
        ])
        _code, out, commit = mod.run(
            UPS_STDIN, ["a-marshal", "b-marshal"], runner=runner,
            state_file=state_file, holder_state_dir=holder_dir,
        )
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert ctx.count("\n") == 1
        assert "a-marshal：本 session 未 hold——新到 1 封信" in ctx
        assert "b-marshal：本 session 未 hold——新到 2 封信" in ctx
        commit()
        doc = _read_state(state_file)
        assert doc["addresses"]["a-marshal"]["events_cursor"] == "a-end"
        assert doc["addresses"]["b-marshal"]["events_cursor"] == "b-end"

    def test_item_payload_never_leaks_into_output(self, state_file,
                                                  holder_dir):
        """count-only：payloadJson 內容（envelopeId／secret）絕不進輸出。"""
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "TOP-SECRET" not in out
        assert "envelopeId" not in out
        assert "payloadJson" not in out


# ── 冷啟動：靜默建游標（防歷史洪水）──────────────────────────────────


class TestColdStart:
    def test_cold_start_builds_cursor_no_alert(self, state_file, holder_dir):
        """無 state 檔＝冷啟動：掃到 head 只建游標、不告警；首查不帶
        --cursor（自 timeline 開頭）。"""
        assert not os.path.exists(state_file)
        runner = _page_runner([
            _events_doc([1, 2], "cur-2"),
            _events_doc([3], "cur-3"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out) == (0, "")
        assert "--cursor" not in runner.calls[0]
        assert runner.calls[1][runner.calls[1].index("--cursor") + 1] == "cur-2"
        commit()
        assert _read_state(state_file) == {
            "addresses": {ADDRESS: {"events_cursor": "cur-3"}}
        }

    def test_cold_start_empty_timeline_no_state_write(self, state_file,
                                                      holder_dir):
        """空 timeline（首查即空頁 null）＝無游標可建——零寫入。"""
        runner = _page_runner([_events_doc([], None)])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert not os.path.exists(state_file)

    def test_cold_start_then_new_events_alerts_only_delta(self, state_file,
                                                          holder_dir):
        """冷啟動建游標後，新事件才 advisory——歷史不重灌。"""
        runner = _page_runner([
            _events_doc([1], "cur-base"),
            _events_doc([], None),
        ])
        _code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert out == ""  # 冷啟動不告警
        commit()
        runner2 = _page_runner([
            _events_doc([2], "cur-next"),
            _events_doc([], None),
        ])
        _code, out2, _ = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner2, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out2
        assert "新到 2" not in out2


# ── 分頁：nextCursor 非空續翻、空頁終止、頁數上限 fail-soft ───────────


class TestPaging:
    def test_multipage_collected_before_advance(self, state_file, holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4, 5], "cur-mid"),
            _events_doc([6], "cur-end"),
            _events_doc([], None),
        ])
        _code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert "新到 3 封信" in ctx
        commit()
        assert _monitor_cursor(state_file) == "cur-end"

    def test_paging_cap_exceeded_fail_soft(self, state_file, holder_dir):
        """頁數上限（EVENTS_MAX_PAGES=10）→ raise → fail-soft：不 emit 不
        推進（防 face 異常無限迴圈）。"""
        _seed_monitor_state(state_file, "cur-0")
        pages = [
            _events_doc([i], f"cur-p{i}") for i in range(mod.EVENTS_MAX_PAGES)
        ]
        runner = _page_runner(pages)
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert len(runner.calls) == mod.EVENTS_MAX_PAGES
        assert _monitor_cursor(state_file) == "cur-0"

    def test_shape_drift_silent(self, state_file, holder_dir):
        """items 非 list／nextCursor 形漂移 → DutymailFaceError → fail-soft。"""
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([_ok({"items": 3, "nextCursor": None})])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)

    def test_unparsable_stdout_silent(self, state_file, holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner(["Traceback (most recent call last):"])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)


# ── session 隔離：per-session 游標＋per-session hold 判定 ─────────────


class TestSessionIsolation:
    def test_two_sessions_cursors_isolated(self, tmp_path, holder_dir):
        """兩 session 游標互不干擾：s1 推進不影響 s2（各自 state 檔）。"""
        s1 = str(tmp_path / "monitor" / "s1.json")
        s2 = str(tmp_path / "monitor" / "s2.json")
        _seed_monitor_state(s1, "cur-0")
        raw1 = _stdin(session_id="s1")
        raw2 = _stdin(session_id="s2")
        runner1 = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out1, commit1 = mod.run(
            raw1, [ADDRESS], runner=runner1, state_file=s1,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out1
        commit1()
        assert _monitor_cursor(s1) == "cur-4"
        # s2 冷啟動：s1 的推進不洩入 s2——靜默建自己的游標。
        runner2 = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        code2, out2, commit2 = mod.run(
            raw2, [ADDRESS], runner=runner2, state_file=s2,
            holder_state_dir=holder_dir,
        )
        assert (code2, out2) == (0, "")  # 冷啟動靜默
        commit2()
        assert _monitor_cursor(s2) == "cur-4"
        assert _monitor_cursor(s1) == "cur-4"  # s1 不被 s2 動

    def test_hold_scoped_to_session(self, tmp_path, holder_dir):
        """s1 holding 不使 s2 靜默——hold 判定讀 per-session duty-receive
        state（session 隔離的 hold 面）。"""
        s1 = str(tmp_path / "monitor" / "s1.json")
        s2 = str(tmp_path / "monitor" / "s2.json")
        _seed_monitor_state(s1, "cur-0")
        _seed_monitor_state(s2, "cur-0")
        _seed_holder_state(holder_dir, session_id="s1", epoch=4)
        raw1 = _stdin(session_id="s1")
        raw2 = _stdin(session_id="s2")
        # s1：holding → status＋events 靜默推進
        runner1 = _page_runner([
            _status_doc(epoch=4, live=True),
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out1, _c1 = mod.run(
            raw1, [ADDRESS], runner=runner1, state_file=s1,
            holder_state_dir=holder_dir,
        )
        assert out1 == ""
        # s2：無 holder state → 未 hold → advisory
        runner2 = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, out2, _c2 = mod.run(
            raw2, [ADDRESS], runner=runner2, state_file=s2,
            holder_state_dir=holder_dir,
        )
        assert "本 session 未 hold——新到 1 封信" in out2


# ── monitor eligibility gate（cwd 鎖——照 AIR-225.1 模式）─────────────


class TestEligibilityGate:
    def test_cwd_outside_repo_silent_no_query_no_state(self, state_file,
                                                       holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([AssertionError("must not call dutymail")])
        raw = _stdin(cwd="/tmp/other-project")
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []  # 零查詢
        assert _monitor_cursor(state_file) == "cur-0"  # 零推進

    def test_cwd_missing_fail_closed(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit",
                          "session_id": "sess-1"})
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_cwd_subdirectory_of_repo_proceeds(self, state_file, holder_dir):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        raw = _stdin(cwd=REPO + "/hooks/deep/dir")
        _code, out, _commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert "新到 1 封信" in out

    def test_prefix_sibling_path_not_eligible(self):
        assert mod.is_eligible(REPO + "-x/sub") is False
        assert mod.is_eligible(None) is False
        assert mod.is_eligible("") is False
        assert mod.is_eligible(123) is False
        assert mod.is_eligible(REPO) is True
        assert mod.is_eligible(REPO + "/sub") is True

    def test_missing_session_id_zero_queries(self, state_file, holder_dir):
        """缺 session_id → session-local 游標無 key——零查詢零輸出。"""
        runner = _page_runner([AssertionError("must not call dutymail")])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": REPO})
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []


# ── fail-soft 決策表（照 AIR-225.1 模式）─────────────────────────────


class TestFailSoftContract:
    def test_store_absent_stderr_note_zero_stdout(self, state_file,
                                                  holder_dir, capsys):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([mod.core.DutymailFaceError(
            code="store-incompatible", error_class="storage",
            message="pre-migration", retryable=False, exit_code=4,
        )])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "store 缺席" in err
        assert "duty-monitor" in err
        assert _monitor_cursor(state_file) == "cur-0"

    def test_other_face_failure_stderr_note(self, state_file, holder_dir,
                                            capsys):
        _seed_monitor_state(state_file, "cur-0")
        runner = _page_runner([mod.core.DutymailFaceError(
            code="unknown-address", error_class="admission",
            message="no address with alias", retryable=False, exit_code=3,
        )])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "dutymail face 失敗" in err
        assert "unknown-address" in err  # 實際錯誤摘要隨行

    def test_bad_stdin_json(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "{not json", [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_empty_stdin(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "", [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)

    def test_stdin_not_object(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "[1,2]", [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)

    def test_unknown_event_silent(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        raw = _stdin(event="Stop")
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_no_address_flag_zero_stdout(self, state_file, holder_dir):
        runner = _page_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            UPS_STDIN, [], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_args_misuse_exit2(self, tmp_path, monkeypatch):
        """註冊 args 誤用（未知 flag——argparse 拒絕）＝exit 2 大聲；
        缺 --address 非誤用（舊 hook 語義——無監看責任靜默）。"""
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        with pytest.raises(SystemExit) as exc:
            mod.main(["--bogus-flag"])
        assert exc.value.code == 2

    def test_main_commit_failure_exit0_stderr_note(self, tmp_path, capsys,
                                                   monkeypatch):
        """游標推進失敗不擋 turn——advisory 照出、exit 0、stderr 註記
        （寧重不漏——下次重複提醒）。"""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        state = tmp_path / "ai-guide" / "duty-monitor" / "sess-1.json"
        os.makedirs(str(state.parent), exist_ok=True)
        state.write_text(
            json.dumps({"addresses": {ADDRESS: {"events_cursor": "cur-0"}}}),
            encoding="utf-8",
        )
        runner = _page_runner([
            _events_doc([4], "cur-9"),
            _events_doc([], None),
        ])

        def boom(path, doc):
            raise OSError("disk on fire")

        monkeypatch.setattr(mod.core, "save_state", boom)
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = mod.main(["--address", ADDRESS], runner=runner)
        assert rc == 0
        captured = capsys.readouterr()
        assert "新到 1 封信" in captured.out
        assert "游標推進失敗" in captured.err
        # cursor 不動——下次重複提醒
        assert json.loads(state.read_text())["addresses"][ADDRESS][
            "events_cursor"] == "cur-0"


# ── monitor ≠ holder：呼叫面僅唯讀 faces ─────────────────────────────


class TestMonitorNotHolder:
    def test_readonly_faces_only(self, state_file, holder_dir):
        """全情境掃描：runner 呼叫僅 events／holder status——零 bind／
        prepare／ack（三軸不互代理，monitor ≠ holder）。"""
        _seed_monitor_state(state_file, "cur-0")
        _seed_holder_state(holder_dir, epoch=4)
        runner = _page_runner([
            _status_doc(epoch=4, live=True),
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        for call in runner.calls:
            if call[0] == "holder":
                assert call[1] == "status"
            else:
                assert call[0] == "events"

    def test_state_file_0600_atomic(self, state_file, holder_dir):
        """session-local 游標檔 0600＋atomic 寫（不留 tmp 殘屍）。"""
        import stat

        runner = _page_runner([
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        _code, _out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        commit()
        mode = stat.S_IMODE(os.stat(state_file).st_mode)
        assert mode == 0o600
        leftovers = [
            f for f in os.listdir(os.path.dirname(state_file))
            if f.endswith(".tmp")
        ]
        assert leftovers == []

    def test_corrupt_state_treated_as_cold_start(self, state_file, holder_dir,
                                                 capsys):
        """state 檔壞形 → 視同冷啟動重建（stderr 註記）——不擋 turn。"""
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = _page_runner([
            _events_doc([1], "cur-1"),
            _events_doc([], None),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
            holder_state_dir=holder_dir,
        )
        assert (code, out) == (0, "")  # 冷啟動語義——靜默重建
        assert "監看 state" in capsys.readouterr().err
        commit()
        assert _monitor_cursor(state_file) == "cur-1"


# ── 舊全域 scbus 檔零讀取＋monitor state 路徑形 ──────────────────────


class TestLegacyGlobalStateZeroRead:
    def test_module_source_zero_scbus_references(self):
        """舊全域檔（scbus-address-monitor.json）與舊 hook 名零引用——
        路徑常數缺席（source 級防線；runtime 面由路徑形測試釘）。"""
        source = (REPO_ROOT / "hooks" / "duty_mailbox_monitor.py").read_text(
            encoding="utf-8"
        )
        assert "scbus" not in source

    def test_monitor_state_path_session_scoped(self, tmp_path):
        """monitor state 落 duty-monitor/<safe_session_id>.json（session
        id sanitizer 與 duty-receive 同源——非舊全域單檔）。"""
        got = mod.monitor_state_path("sess 1/x", base_dir=str(tmp_path))
        assert got == str(tmp_path / "sess_1_x.json")
        assert mod.monitor_state_path("", base_dir=str(tmp_path)) == str(
            tmp_path / "unknown.json"
        )

    def test_legacy_global_file_never_created(self, tmp_path, monkeypatch):
        """跑一輪全流程——XDG state 樹下零 scbus-address-monitor 檔。"""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        holder_dir = str(tmp_path / "holder")
        _seed_holder_state(holder_dir, session_id="s9", epoch=4)
        runner = _page_runner([
            _status_doc(epoch=4, live=True),
            _events_doc([4], "cur-4"),
            _events_doc([], None),
        ])
        raw = _stdin(session_id="s9")
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner,
                                    holder_state_dir=holder_dir)
        assert (code, out) == (0, "")
        commit()
        for root, _dirs, files in os.walk(str(tmp_path)):
            for name in files:
                assert "scbus" not in name
        assert (tmp_path / "ai-guide" / "duty-monitor" / "s9.json").exists()


# ── DUTYMAIL_BIN shim（真 subprocess 整合面——env 注入 binary）────────


class TestRunnerEnvShim:
    def _shim(self, tmp_path):
        shim = tmp_path / "dutymail-shim.py"
        shim.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "argv = sys.argv[1:]\n"
            "if argv[:2] == ['holder', 'status']:\n"
            "    print(json.dumps({'schemaVersion': 1, 'ok': True,"
            " 'result': {'addressId': 'a1', 'alias': 'ai-guide-marshal',"
            " 'bindingEpoch': 0, 'leaseExpiresAtUs': None, 'live': False}}))\n"
            "    raise SystemExit(0)\n"
            "cur = argv[argv.index('--cursor') + 1] if '--cursor' in argv"
            " else None\n"
            "if cur == 'tok-0':\n"
            "    items = [{'atUs': 1, 'eventSeq': 9, 'kind': 'accepted',"
            " 'payloadJson': '{}'}]\n"
            "    print(json.dumps({'schemaVersion': 1, 'ok': True,"
            " 'result': {'items': items, 'nextCursor': 'tok-9'}}))\n"
            "else:\n"
            "    print(json.dumps({'schemaVersion': 1, 'ok': True,"
            " 'result': {'items': [], 'nextCursor': None}}))\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return shim

    def test_env_bin_shim_main_flow(self, tmp_path, monkeypatch, capsys):
        """DUTYMAIL_BIN 指向 shim——main() 真 subprocess 整合面：暖游標
        tok-0 → 新 1 封 → advisory＋游標推進 tok-9。"""
        monkeypatch.setenv("DUTYMAIL_BIN", str(self._shim(tmp_path)))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        state = tmp_path / "ai-guide" / "duty-monitor" / "sess-1.json"
        os.makedirs(str(state.parent), exist_ok=True)
        state.write_text(
            json.dumps({"addresses": {ADDRESS: {"events_cursor": "tok-0"}}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = mod.main(["--address", ADDRESS])
        assert rc == 0
        captured = capsys.readouterr()
        assert "新到 1 封信" in captured.out
        assert json.loads(state.read_text())["addresses"][ADDRESS][
            "events_cursor"] == "tok-9"
        # main() 未注入 runner——走 core._default_runner＋env binary 解析


# ── governance 接線：registrations 雙事件獨立 group＋manifest 換名 ────


def _registration(rel):
    return json.loads((gov.MANIFEST_PATH.parent / rel).read_text())


def _groups(doc, event):
    events = doc.get("events", doc)
    return events.get(event, [])


def _hook_scripts(group):
    return [
        h.get("args", [h.get("command", "")])[0].rsplit("/", 1)[-1]
        if h.get("args")
        else h.get("command", "")
        for h in group.get("hooks", [])
    ]


class TestRegistrationWiring:
    def test_zcode_template_both_events_sync_groups(self):
        doc = _registration("registrations/zcode.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            hits = [
                g
                for g in _groups(doc, event)
                if "duty_mailbox_monitor.py" in _hook_scripts(g)
            ]
            assert len(hits) == 1, event
            entry = hits[0]["hooks"][0]
            assert entry["type"] == "process"
            assert "async" not in entry  # sync——additionalContext 通道
            assert entry.get("timeoutMs")
            assert entry["args"][1:] == ["--address", "ai-guide-marshal"]

    def test_zcode_group_composition_new_topology(self):
        """UPS groups＝compact-restore-inject＋duty-receive＋duty-monitor
        （monitor group 兩門牌條目——marshal＋primary，args 照舊）。"""
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        ss = _groups(doc, "SessionStart")
        assert _hook_scripts(ups[0]) == ["compact-restore-inject.py"]
        assert _hook_scripts(ups[1]) == ["duty_receive.py"]
        assert _hook_scripts(ups[2]) == [
            "duty_mailbox_monitor.py", "duty_mailbox_monitor.py",
        ]
        assert ups[2]["hooks"][1]["args"][1:] == [
            "--address", "ai-guide-primary",
        ]
        assert _hook_scripts(ss[0]) == ["duty_receive.py"]
        assert _hook_scripts(ss[1]) == [
            "duty_mailbox_monitor.py", "duty_mailbox_monitor.py",
        ]

    def test_zcode_template_existing_entries_untouched(self):
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        assert len(ups) == 3
        compact = [
            g for g in ups if "compact-restore-inject.py" in _hook_scripts(g)
        ]
        assert len(compact) == 1
        entry = compact[0]["hooks"][0]
        assert entry["type"] == "process"
        assert entry.get("enabled") is True
        assert entry.get("timeoutMs") == 10000
        assert set(doc["events"]) >= {
            "PreToolUse",
            "Stop",
            "PostToolUse",
            "UserPromptSubmit",
            "SessionStart",
        }

    def test_cc_dormant_template_same_shape(self):
        doc = _registration("registrations/cc.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            hits = [
                g
                for g in _groups(doc, event)
                if "duty_mailbox_monitor.py" in _hook_scripts(g)
            ]
            assert len(hits) == 1, event

    def test_manifest_inventory_renamed(self):
        manifest = gov.load_manifest()
        scripts = manifest["surfaces"]["hooks"]["scripts"]
        assert "hooks/duty_mailbox_monitor.py" in scripts
        assert "hooks/scbus-address-pending-reminder.py" not in scripts

    def test_old_script_name_retired_everywhere(self):
        """舊名全面退役 pin：registrations 零 scbus-address-pending-
        reminder 條目（AC——rg 零命中的測試面鏡像）。"""
        for rel in ("registrations/zcode.json", "registrations/cc.json"):
            raw = (gov.MANIFEST_PATH.parent / rel).read_text(encoding="utf-8")
            assert "scbus-address-pending-reminder" not in raw


class TestInstallMergeFace:
    def _template(self):
        raw = (gov.MANIFEST_PATH.parent / "registrations/zcode.json").read_text()
        # render_uninstall：展開 REPO（identity 靠真實 hooks 路徑），HOOK_PYTHON 保留
        return json.loads(gov.render_uninstall(raw))

    def _live(self):
        """模擬 live config root——既有形態取自模板既有 group（byte 等值隔離
        「內容更新」語義）；scbus canonical 條目照 live config 實際形（純
        command 字串、SS 帶 async）。"""
        tmpl = self._template()
        compact_ups = [
            g
            for g in tmpl["events"]["UserPromptSubmit"]
            if "compact-restore-inject.py" in gov._group_scripts(g)
        ]
        return {
            "hooks": {
                "enabled": True,
                "events": {
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "scbus hook --harness zcode --event user-prompt-submit",
                                }
                            ]
                        },
                        *compact_ups,
                    ],
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "scbus hook --harness zcode --event session-start",
                                    "async": True,
                                }
                            ]
                        }
                    ],
                },
            }
        }

    def test_merge_appends_new_groups_keeps_existing(self):
        live = self._live()
        tmpl = self._template()
        new_root, changed = gov.merge_json_hooks(
            live, tmpl, "hooks", remove=False
        )
        assert changed
        ups = new_root["hooks"]["events"]["UserPromptSubmit"]
        ss = new_root["hooks"]["events"]["SessionStart"]
        live_ups = live["hooks"]["events"]["UserPromptSubmit"]
        live_ss = live["hooks"]["events"]["SessionStart"]
        assert ups[0] == live_ups[0]
        assert ups[1] == live_ups[1]
        assert len(ups) == 4
        assert len(ss) == 3
        assert ss[0] == live_ss[0]  # scbus async 條目零動
        # 新拓撲 append 順序＝模板順序：duty-receive group 先、duty-monitor 尾
        assert gov._group_scripts(ups[2]) == frozenset({"duty_receive.py"})
        assert gov._group_scripts(ups[3]) == frozenset({"duty_mailbox_monitor.py"})
        assert gov._group_scripts(ss[1]) == frozenset({"duty_receive.py"})
        assert gov._group_scripts(ss[2]) == frozenset({"duty_mailbox_monitor.py"})

    def test_merge_idempotent(self):
        live = self._live()
        tmpl = self._template()
        once, _changed = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
        _again, changed = gov.merge_json_hooks(once, tmpl, "hooks", remove=False)
        assert not changed

    def test_uninstall_removes_only_package_groups(self):
        live = self._live()
        tmpl = self._template()
        merged, _changed = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
        back, changed = gov.merge_json_hooks(merged, tmpl, "hooks", remove=True)
        assert changed
        events = back["hooks"]["events"]
        assert len(events["UserPromptSubmit"]) == 1
        assert gov._group_scripts(events["UserPromptSubmit"][0]) == frozenset()
        assert events["SessionStart"] == live["hooks"]["events"]["SessionStart"]
        assert gov._group_scripts(events["SessionStart"][0]) == frozenset()

    def test_identity_no_collapse_with_canonical_or_compact(self):
        tmpl = self._template()
        for event in ("UserPromptSubmit", "SessionStart"):
            ours = [
                gov._group_identity(g)
                for g in tmpl["events"][event]
                if "duty_mailbox_monitor.py" in gov._group_scripts(g)
            ]
            assert len(ours) == 1, event
            assert len(ours[0][1]) == 1
            others = {
                gov._group_identity(g) for g in tmpl["events"][event]
            } - set(ours)
            assert ours[0] not in others
