"""dutymail 信箱 monitor hook 測試（AIR-254.4——review 修復 U2/U3/U4 重寫）。

語義裁定（marshal judge 採納）：bounded monitor reports **holderless
pending**（AIR-258 B′ 解凍改常態語義——pending 在 INBOX 等人判讀，非
異常窗口）。資料面只留兩個唯讀 face——`holder status`（live 偵測）＋
`receive status`（pendingCount）；events face
消費全面退役（collect_events／頁上限／events_cursor 游標語義不再存在）。

涵蓋（工單覆蓋面）：
- 決策表（per address）：①live=True（本 session hold 或他方 live——處理面
  由 holder 承擔）→ 靜默＋last_pending baseline 歸零；②live=False
  （holderless）→ receive status pendingCount：>0 且 ≠ baseline → 一行
  advisory（holderless pending N 封）＋baseline=N；>0 且 == baseline →
  靜默（防每 prompt 轟炸）；==0 → 靜默＋baseline 歸零。
- baseline state：形 {"addresses": {"<alias>": {"last_pending": int}}}；
  session-local、路徑可注入、0600 atomic 寫、advance-after-emit。
- per-address 容錯（U4）：單 address face 失敗 → stderr 註記續跑其他門牌
  （前位成功 advisory 保留）。
- eligibility gate：cwd 在 script repo 外／缺席 → 零查詢零輸出零推進；
  缺 session_id → 零查詢。
- fail-soft：store 缺席（storage class）／unknown-address／pendingCount
  形漂移 → 該門牌 stderr 註記＋零 stdout；stdin 壞 JSON／未知事件 → 靜默
  exit 0；args 誤用 exit 2；baseline 寫入失敗寧重不漏。
- session 隔離：兩 session baseline 互不干擾（per-session state 檔）。
- 舊全域 scbus-address-monitor 檔零讀取（模組 source 零 scbus 字樣）＋
  monitor state 落 duty-monitor/<safe_session_id>.json。
- monitor ≠ holder：呼叫面僅 holder status／receive status 唯讀——零
  bind／prepare／ack（三軸不互代理）。
- governance 接線（U3）：zcode 模板 monitor group 單一 marshal 條目（
  ai-guide-primary 死門牌條目退役）；cc dormant 同形；install merge 面
  新 group append、既有條目零動、冪等、uninstall 只拆本套件 group。

測試全走 injectable runner（fake dutymail 回固定 JSON）＋fake state 路徑
（tmp_path）——不碰真 store（真 store 往返＝工單真實資料五步）。
"""

import io
import json
import os
import sys
from types import SimpleNamespace

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


# ── fake dutymail（typed contract：成功 stdout 一個 JSON；失敗 raise）──


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


def _status_doc(epoch=4, live=False):
    return _ok({
        "addressId": "a1", "alias": ADDRESS, "bindingEpoch": epoch,
        "leaseExpiresAtUs": 0, "live": live,
    })


def _recv_doc(pending=0):
    """receive status face（3.1.0 真機形）：pendingCount＋primaryCursor。"""
    return _ok({
        "addressId": "a1", "bindingEpoch": 4, "lastDeliverySeq": 5,
        "liveBatch": None, "pendingCount": pending, "primaryCursor": 5,
    })


def _seq_runner(steps):
    """injectable runner：steps 依呼叫序回傳（str stdout 或 Exception）。"""
    calls = []

    def run(argv):
        calls.append(list(argv))
        step = steps[len(calls) - 1]
        if isinstance(step, Exception):
            raise step
        return step

    run.calls = calls
    return run


def _seed_baseline(state_file, last_pending, address=ADDRESS):
    """seed baseline 檔（merge 進既有 doc——同檔多門牌場景不互相覆寫）。"""
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    doc = {"addresses": {}}
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
            if isinstance(loaded, dict) and isinstance(
                loaded.get("addresses"), dict
            ):
                doc = loaded
    doc["addresses"][address] = {"last_pending": last_pending}
    with open(state_file, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def _read_state(state_file):
    with open(state_file, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _last_pending(state_file, address=ADDRESS):
    return _read_state(state_file)["addresses"][address]["last_pending"]


# ── 決策表：live=True（holding／他方 live）靜默＋baseline 歸零 ─────────


class TestHoldSilent:
    def test_live_holder_silent_baseline_reset(self, state_file):
        """live=True（本 session hold——duty-receive 同邊界已 bind/renew）
        → 靜默＋baseline 歸零（處理面由 holder 承擔，提醒面安靜）。"""
        _seed_baseline(state_file, 3)
        runner = _seq_runner([_status_doc(epoch=4, live=True)])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out) == (0, "")
        assert runner.calls == [
            ["holder", "status", "--address", ADDRESS]
        ]
        commit()
        assert _last_pending(state_file) == 0

    def test_foreign_live_silent_covered(self, state_file):
        """他方 live（另一 session holding——epoch 非本 session）→ 靜默
        （covered：與 duty_receive 衝突行同語義——處理面由現 holder 承擔）
        ＋baseline 歸零。"""
        _seed_baseline(state_file, 2)
        runner = _seq_runner([_status_doc(epoch=9, live=True)])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out) == (0, "")
        commit()
        assert _last_pending(state_file) == 0

    def test_live_already_zero_baseline_no_write(self, state_file):
        """live=True 且 baseline 已 0／缺席 → 零寫入需求：commit=None。"""
        runner = _seq_runner([_status_doc(live=True)])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert not os.path.exists(state_file)


# ── 決策表：holderless pending advisory（B′ 常態語義）─────────────────


class TestHolderlessPending:
    def test_advisory_exact_wording_and_baseline(self, state_file):
        """live=False＋pendingCount=2 且 ≠ baseline → 一行 advisory（裁定
        措辭逐字）＋baseline=2（advance-after-emit）。"""
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert code == 0
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert doc["hookSpecificOutput"]["additionalContext"] == (
            "[duty-monitor] " + ADDRESS + "：holderless pending 2 封"
            "（pending 在 INBOX 等人判讀——B′：workspace 信終點＝durable"
            " INBOX；dutymail receive status 可查）"
        )
        # 呼叫面凍結：holder status → receive status（唯讀兩 face）
        assert runner.calls == [
            ["holder", "status", "--address", ADDRESS],
            ["receive", "status", "--address", ADDRESS],
        ]
        assert commit is not None
        commit()
        assert _last_pending(state_file) == 2

    def test_same_pending_count_silent_anti_spam(self, state_file):
        """pendingCount>0 且 == baseline（未變化）→ 靜默——防每 prompt
        轟炸；baseline 保留（N 不被歸零）。"""
        _seed_baseline(state_file, 2)
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert _last_pending(state_file) == 2

    def test_pending_zero_silent_baseline_reset(self, state_file):
        """live=False＋pendingCount==0 → 靜默＋baseline 歸零。"""
        _seed_baseline(state_file, 5)
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=0),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out) == (0, "")
        commit()
        assert _last_pending(state_file) == 0

    def test_pending_grows_new_advisory(self, state_file):
        """baseline=1 → pendingCount=3（值變化）→ 新 advisory＋baseline=3。"""
        _seed_baseline(state_file, 1)
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=3),
        ])
        _code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert "holderless pending 3 封" in out
        commit()
        assert _last_pending(state_file) == 3

    def test_cold_baseline_pending_alerts(self, state_file):
        """冷啟動（無 baseline）＋holderless pending>0 → 立即 advisory——
        pendingCount 是現值非事件史，無歷史洪水問題（裁定語義）。"""
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=4),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert "holderless pending 4 封" in out

    def test_advance_after_emit_not_before(self, state_file):
        """baseline 寫入只發生在 commit()（stdout 寫出後）——run() 返回
        當下未動。"""
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        _code, _out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert not os.path.exists(state_file)
        commit()
        assert _read_state(state_file) == {
            "addresses": {ADDRESS: {"last_pending": 2}}
        }

    def test_sessionstart_event_name(self, state_file):
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        _code, out, _commit = mod.run(
            SS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "SessionStart"

    def test_grok_snake_event_value_normalized(self, state_file):
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        raw = json.dumps(
            {"hookEventName": "user_prompt_submit", "sessionId": "sess-1",
             "cwd": REPO}
        )
        _code, out, _commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "UserPromptSubmit"

    def test_multiple_addresses_two_lines_both_advance(self, state_file):
        _seed_baseline(state_file, 0, address="a-marshal")
        _seed_baseline(state_file, 0, address="b-marshal")
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        _code, out, commit = mod.run(
            UPS_STDIN, ["a-marshal", "b-marshal"], runner=runner,
            state_file=state_file,
        )
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert ctx.count("\n") == 1
        assert "a-marshal：holderless pending 1 封" in ctx
        assert "b-marshal：holderless pending 2 封" in ctx
        commit()
        doc = _read_state(state_file)
        assert doc["addresses"]["a-marshal"]["last_pending"] == 1
        assert doc["addresses"]["b-marshal"]["last_pending"] == 2

    def test_count_only_no_face_detail_leak(self, state_file):
        """count-only：face 回應其他欄位（liveBatch／primaryCursor 等）絕不
        進輸出——advisory 只含 alias＋整數計數。"""
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert "primaryCursor" not in out
        assert "addressId" not in out


# ── per-address 容錯（U4）：單門牌失敗續跑其他 ─────────────────────────


class TestPerAddressFaultTolerance:
    def test_partial_failure_keeps_earlier_advisory(self, state_file, capsys):
        """前位門牌成功 advisory 保留；後位 face 失敗 → stderr 註記續跑、
        不擋 turn、exit 0。"""
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),  # a-marshal 成功
            mod.core.DutymailFaceError(  # b-marshal holder status 失敗
                code="unknown-address", error_class="admission",
                message="no address with alias", retryable=False,
                exit_code=3,
            ),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, ["a-marshal", "b-marshal"], runner=runner,
            state_file=state_file,
        )
        assert code == 0
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert "a-marshal：holderless pending 1 封" in ctx
        assert "b-marshal" not in ctx
        err = capsys.readouterr().err
        assert "b-marshal" in err
        assert "unknown-address" in err
        commit()
        assert _last_pending(state_file, address="a-marshal") == 1

    def test_receive_status_failure_stderr_note(self, state_file, capsys):
        """holder status 過（live=False）但 receive status 失敗 → 該門牌
        stderr 註記＋零 stdout、baseline 不動。"""
        _seed_baseline(state_file, 2)
        runner = _seq_runner([
            _status_doc(live=False),
            mod.core.DutymailFaceError(
                code="wait-timeout", error_class="wait-timeout",
                message="busy", retryable=True, exit_code=6,
            ),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "fail-soft" in err
        assert "wait-timeout" in err
        assert _last_pending(state_file) == 2

    def test_pending_count_shape_drift_fail_soft(self, state_file, capsys):
        """pendingCount 非非負整數 → shape-drift fail-soft（stderr 註記、
        零 stdout——禁靜默歸零）。"""
        runner = _seq_runner([
            _status_doc(live=False), _ok({"pendingCount": "many"}),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert "shape-drift" in capsys.readouterr().err


# ── monitor eligibility gate（cwd 鎖——照 AIR-225.1 模式）─────────────


class TestEligibilityGate:
    def test_cwd_outside_repo_silent_no_query_no_state(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        raw = _stdin(cwd="/tmp/other-project")
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []  # 零查詢
        assert not os.path.exists(state_file)  # 零推進

    def test_cwd_missing_fail_closed(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit",
                          "session_id": "sess-1"})
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_cwd_subdirectory_of_repo_proceeds(self, state_file):
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        raw = _stdin(cwd=REPO + "/hooks/deep/dir")
        _code, out, _commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert "holderless pending 1 封" in out

    def test_prefix_sibling_path_not_eligible(self):
        assert mod.is_eligible(REPO + "-x/sub") is False
        assert mod.is_eligible(None) is False
        assert mod.is_eligible("") is False
        assert mod.is_eligible(123) is False
        assert mod.is_eligible(REPO) is True
        assert mod.is_eligible(REPO + "/sub") is True

    def test_missing_session_id_zero_queries(self, state_file):
        """缺 session_id → session-local baseline 無 key——零查詢零輸出。"""
        runner = _seq_runner([AssertionError("must not call dutymail")])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": REPO})
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []


# ── fail-soft 決策表（stdin 面）───────────────────────────────────────


class TestFailSoftContract:
    def test_store_absent_stderr_note_zero_stdout(self, state_file, capsys):
        """store 缺席（storage class）＝stderr 一行註記＋零 stdout exit 0。"""
        runner = _seq_runner([mod.core.DutymailFaceError(
            code="store-incompatible", error_class="storage",
            message="pre-migration", retryable=False, exit_code=4,
        )])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "store 缺席" in err
        assert "duty-monitor" in err

    def test_unknown_address_stderr_note(self, state_file, capsys):
        runner = _seq_runner([mod.core.DutymailFaceError(
            code="unknown-address", error_class="admission",
            message="no address with alias", retryable=False, exit_code=3,
        )])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "dutymail face 失敗" in err
        assert "unknown-address" in err

    def test_bad_stdin_json(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "{not json", [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_empty_stdin(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "", [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)

    def test_stdin_not_object(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            "[1,2]", [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)

    def test_unknown_event_silent(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        raw = _stdin(event="Stop")
        code, out, commit = mod.run(
            raw, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_no_address_flag_zero_stdout(self, state_file):
        runner = _seq_runner([AssertionError("must not call dutymail")])
        code, out, commit = mod.run(
            UPS_STDIN, [], runner=runner, state_file=state_file,
        )
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_args_misuse_exit2(self, tmp_path, monkeypatch):
        """註冊 args 誤用（未知 flag——argparse 拒絕）＝exit 2 大聲；
        缺 --address 非誤用（無監看責任靜默）。"""
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        with pytest.raises(SystemExit) as exc:
            mod.main(["--bogus-flag"])
        assert exc.value.code == 2

    def test_main_commit_failure_exit0_stderr_note(self, tmp_path, capsys,
                                                   monkeypatch):
        """baseline 寫入失敗不擋 turn——advisory 照出、exit 0、stderr 註記
        （寧重不漏——下次重複提醒）。"""
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])

        def boom(path, doc):
            raise OSError("disk on fire")

        monkeypatch.setattr(mod.core, "save_state", boom)
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = mod.main(["--address", ADDRESS], runner=runner)
        assert rc == 0
        captured = capsys.readouterr()
        assert "holderless pending 1 封" in captured.out
        assert "baseline 寫入失敗" in captured.err


# ── monitor ≠ holder：呼叫面僅唯讀 faces ─────────────────────────────


class TestMonitorNotHolder:
    def test_readonly_faces_only(self, state_file):
        """全情境掃描：runner 呼叫僅 holder status／receive status——零
        bind／prepare／ack（三軸不互代理，monitor ≠ holder）。"""
        runner = _seq_runner([
            _status_doc(live=True),  # 門牌一：live 靜默
            _status_doc(live=False), _recv_doc(pending=1),  # 門牌二：advisory
        ])
        mod.run(
            UPS_STDIN, ["a-marshal", ADDRESS], runner=runner,
            state_file=state_file,
        )
        for call in runner.calls:
            if call[0] == "holder":
                assert call[1] == "status"
            else:
                assert call[0] == "receive" and call[1] == "status"

    def test_state_file_0600_atomic(self, state_file):
        """session-local baseline 檔 0600＋atomic 寫（不留 tmp 殘屍）。"""
        import stat

        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        _code, _out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        commit()
        mode = stat.S_IMODE(os.stat(state_file).st_mode)
        assert mode == 0o600
        leftovers = [
            f for f in os.listdir(os.path.dirname(state_file))
            if f.endswith(".tmp")
        ]
        assert leftovers == []

    def test_corrupt_state_treated_as_cold_start(self, state_file, capsys):
        """state 檔壞形 → 視同冷啟動重建（stderr 註記）——不擋 turn。"""
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        code, out, commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert code == 0
        assert "holderless pending 1 封" in out  # 冷 baseline＝None≠1——告警
        assert "監看 state" in capsys.readouterr().err
        commit()
        assert _last_pending(state_file) == 1

    def test_baseline_value_shape_drift_treated_as_cold(self, state_file,
                                                        capsys):
        """baseline 值形漂移（非整數）→ stderr 註記後視同 None 重建。"""
        _seed_baseline(state_file, "many")
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        _code, out, _commit = mod.run(
            UPS_STDIN, [ADDRESS], runner=runner, state_file=state_file,
        )
        assert "holderless pending 2 封" in out
        assert "baseline" in capsys.readouterr().err


# ── session 隔離：per-session baseline ────────────────────────────────


class TestSessionIsolation:
    def test_two_sessions_baselines_isolated(self, tmp_path):
        """兩 session baseline 互不干擾：s1 推進不影響 s2（各自 state 檔）。"""
        s1 = str(tmp_path / "monitor" / "s1.json")
        s2 = str(tmp_path / "monitor" / "s2.json")
        raw1 = _stdin(session_id="s1")
        raw2 = _stdin(session_id="s2")
        runner1 = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        _code, out1, commit1 = mod.run(
            raw1, [ADDRESS], runner=runner1, state_file=s1,
        )
        assert "holderless pending 2 封" in out1
        commit1()
        assert _last_pending(s1) == 2
        # s2 冷啟動：s1 的 baseline 不洩入 s2——同值也各自告警一次。
        runner2 = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=2),
        ])
        code2, out2, commit2 = mod.run(
            raw2, [ADDRESS], runner=runner2, state_file=s2,
        )
        assert code2 == 0
        assert "holderless pending 2 封" in out2
        commit2()
        assert _last_pending(s2) == 2
        assert _last_pending(s1) == 2  # s1 不被 s2 動

    def test_s1_silent_does_not_silence_s2(self, tmp_path):
        """s1 邊界 live=True 靜默（當時有 holder）不使 s2 靜默——per-session
        baseline 各自判定。"""
        s1 = str(tmp_path / "monitor" / "s1.json")
        s2 = str(tmp_path / "monitor" / "s2.json")
        runner1 = _seq_runner([_status_doc(live=True)])
        raw1 = _stdin(session_id="s1")
        _code, out1, _c1 = mod.run(
            raw1, [ADDRESS], runner=runner1, state_file=s1,
        )
        assert out1 == ""
        runner2 = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        raw2 = _stdin(session_id="s2")
        _code, out2, _c2 = mod.run(
            raw2, [ADDRESS], runner=runner2, state_file=s2,
        )
        assert "holderless pending 1 封" in out2


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
        runner = _seq_runner([
            _status_doc(live=False), _recv_doc(pending=1),
        ])
        raw = _stdin(session_id="s9")
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner)
        assert code == 0
        assert "holderless pending 1 封" in out
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
            " 'bindingEpoch': 4, 'leaseExpiresAtUs': None, 'live': False}}))\n"
            "    raise SystemExit(0)\n"
            "if argv[:2] == ['receive', 'status']:\n"
            "    print(json.dumps({'schemaVersion': 1, 'ok': True,"
            " 'result': {'addressId': 'a1', 'bindingEpoch': 4,"
            " 'lastDeliverySeq': 5, 'liveBatch': None,"
            " 'pendingCount': 1, 'primaryCursor': 5}}))\n"
            "    raise SystemExit(0)\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return shim

    def test_env_bin_shim_main_flow(self, tmp_path, monkeypatch, capsys):
        """DUTYMAIL_BIN 指向 shim——main() 真 subprocess 整合面：holderless
        pending 1 → advisory＋baseline 寫入。"""
        monkeypatch.setenv("DUTYMAIL_BIN", str(self._shim(tmp_path)))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = mod.main(["--address", ADDRESS])
        assert rc == 0
        captured = capsys.readouterr()
        assert "holderless pending 1 封" in captured.out
        state = tmp_path / "ai-guide" / "duty-monitor" / "sess-1.json"
        assert json.loads(state.read_text())["addresses"][ADDRESS][
            "last_pending"] == 1
        # main() 未注入 runner——走 core._default_runner＋env binary 解析


# ── governance 接線：registrations 單一 marshal 條目＋manifest ────────


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
        """UPS groups＝compact-restore-inject＋duty-receive＋duty-monitor＋
        bridge-sweeper（monitor group 單一 marshal 條目——primary 死門牌已
        退役；AIR-267 追加 sweeper prompt 邊界腿）。"""
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        ss = _groups(doc, "SessionStart")
        assert _hook_scripts(ups[0]) == ["compact-restore-inject.py"]
        assert _hook_scripts(ups[1]) == ["duty_receive.py"]
        assert _hook_scripts(ups[2]) == ["duty_mailbox_monitor.py"]
        assert _hook_scripts(ups[3]) == ["bridge_ledger_sweeper.py"]
        assert _hook_scripts(ss[0]) == ["duty_receive.py"]
        assert _hook_scripts(ss[1]) == ["duty_mailbox_monitor.py"]
        assert _hook_scripts(ss[2]) == ["bridge_ledger_sweeper.py"]

    def test_primary_dead_entry_retired_everywhere(self):
        """ai-guide-primary 死門牌條目退役 pin（AC——rg 零命中的測試面
        鏡像）：zcode/cc registrations 零殘留。"""
        for rel in ("registrations/zcode.json", "registrations/cc.json"):
            raw = (gov.MANIFEST_PATH.parent / rel).read_text(encoding="utf-8")
            assert "ai-guide-primary" not in raw

    def test_zcode_template_existing_entries_untouched(self):
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        assert len(ups) == 4  # AIR-267 追加 bridge-sweeper group
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
        assert len(ups) == 5  # scbus＋compact＋duty-receive＋duty-monitor＋sweeper（AIR-267）
        assert len(ss) == 4  # scbus＋duty-receive＋duty-monitor＋sweeper（AIR-267）
        assert ss[0] == live_ss[0]  # scbus async 條目零動
        # 新拓撲 append 順序＝模板順序：duty-receive group 先、duty-monitor、
        # bridge-sweeper 尾（AIR-267）
        assert gov._group_scripts(ups[2]) == frozenset({"duty_receive.py"})
        assert gov._group_scripts(ups[3]) == frozenset({"duty_mailbox_monitor.py"})
        assert gov._group_scripts(ups[4]) == frozenset({"bridge_ledger_sweeper.py"})
        assert gov._group_scripts(ss[1]) == frozenset({"duty_receive.py"})
        assert gov._group_scripts(ss[2]) == frozenset({"duty_mailbox_monitor.py"})
        assert gov._group_scripts(ss[3]) == frozenset({"bridge_ledger_sweeper.py"})

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


# ── AIR-255 A：installer prune（ownership-aware）＋removal receipt ────


def _prune_fixture(monkeypatch, tmp_path):
    """zcode render fixture：canonical/REPO_ROOT 錨到 tmp repo（fence 可控）。

    回 (repo, tmpl)——tmpl＝render 後模板 subtree（{enabled, events}，路徑
    全落 tmp repo hooks/）。"""
    repo = tmp_path / "checkout"
    (repo / "hooks").mkdir(parents=True)
    monkeypatch.setattr(gov, "REPO_ROOT", repo)
    monkeypatch.setattr(gov, "_CANONICAL_CACHE", {str(repo): repo})
    monkeypatch.setattr(gov, "_HOOK_PATTERN_CACHE", {})
    monkeypatch.setattr(gov, "_HOOK_PYTHON_CACHE", str(repo / "python3.12"))
    raw = (gov.MANIFEST_PATH.parent / "registrations/zcode.json").read_text()
    return repo, json.loads(gov.render(raw))


def _repo_group(repo, name, on_disk=False, command=None):
    """受管形 group（installer render 形：command＝interpreter、args＝
    repo hooks 絕對路徑）；on_disk=True 同步在 tmp repo 落 script 檔。"""
    if on_disk:
        (repo / "hooks" / name).write_text("# script\n")
    return {
        "hooks": [
            {
                "type": "process",
                "command": command or str(repo / "python3.12"),
                "args": [f"{repo}/hooks/{name}"],
                "timeoutMs": 10000,
            }
        ]
    }


def _foreign_group(tmp_path, name="foreign.py"):
    other = tmp_path / "other-checkout" / "hooks"
    return {
        "hooks": [
            {
                "type": "process",
                "command": "/usr/bin/python3",
                "args": [f"{other}/{name}"],
                "timeoutMs": 10000,
            }
        ]
    }


def _live_with_stale(repo, tmp_path, tmpl, extras):
    """live config root：模板 group 全在場＋extras 插 UserPromptSubmit 前端。"""
    live = json.loads(json.dumps(tmpl))
    live["events"]["UserPromptSubmit"] = [
        *extras,
        *live["events"]["UserPromptSubmit"],
    ]
    return {"hooks": live}


def _script_names(events_doc):
    names = set()
    for groups in events_doc.values():
        for g in groups:
            names |= gov._group_scripts(g)
    return names


class TestReconcilePlan:
    def test_remove_judgement_four_cases(self, tmp_path, monkeypatch):
        """remove 判準四案例：managed+absent→刪／managed+present（rename
        殘留）→刪（無視 script 存在性）／外部路徑→warn 不刪／模板內→留。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"] = [
            _repo_group(repo, "scbus-address-pending-reminder.py"),  # 已刪檔
            _repo_group(repo, "old-name-residue.py", on_disk=True),  # rename 殘留
            _foreign_group(tmp_path),  # 外部路徑
            *live["events"]["UserPromptSubmit"],
        ]
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        removed = {
            p.rsplit("/", 1)[-1] for e in plan["remove"] for p in e["scripts"]
        }
        assert removed == {
            "scbus-address-pending-reminder.py",
            "old-name-residue.py",
        }
        warned = {
            p.rsplit("/", 1)[-1]
            for e in plan["orphan_warn"]
            for p in e["scripts"]
        }
        assert warned == {"foreign.py"}
        assert plan["add"] == []  # 模板 group 全在場
        assert plan["update"] == []

    def test_pure_command_user_group_ignored(self, tmp_path, monkeypatch):
        """純 command 用戶 group（scbus 形，無 script 路徑引用）＝零動作
        零警示——用戶 group 保留。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "scbus hook --harness zcode"
                        " --event user-prompt-submit",
                    }
                ]
            },
            *live["events"]["UserPromptSubmit"],
        ]
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        assert plan["remove"] == []
        assert plan["orphan_warn"] == []

    def test_plan_detects_add_and_update(self, tmp_path, monkeypatch):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"].pop()  # 少一條模板 group → add
        live["events"]["SessionStart"][0]["hooks"][0]["timeoutMs"] = 99999
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        assert {e["event"] for e in plan["add"]} == {"UserPromptSubmit"}
        assert {e["event"] for e in plan["update"]} == {"SessionStart"}
        assert plan["remove"] == []


class TestPruneMergeFace:
    def test_no_flag_zero_removal(self, tmp_path, monkeypatch):
        """不帶 prune flag 的 merge＝零移除（行為完全不變）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        new_root, _changed = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False
        )
        assert "scbus-address-pending-reminder.py" in _script_names(
            new_root["hooks"]["events"]
        )

    def test_prune_stale_removes_exactly_plan_remove(
        self, tmp_path, monkeypatch
    ):
        """plan 單源：merge（prune_stale）移除集＝plan["remove"]；dry-run
        預覽與 apply 同一份計算。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        extras = [
            _repo_group(repo, "scbus-address-pending-reminder.py"),
            _repo_group(repo, "old-name-residue.py", on_disk=True),
            _foreign_group(tmp_path),
        ]
        live_root = _live_with_stale(repo, tmp_path, tmpl, extras)
        live_sub = live_root["hooks"]
        plan = gov._hooks_reconcile_plan(live_sub, tmpl, repo / "hooks")
        new_root, changed = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        assert changed
        names = _script_names(new_root["hooks"]["events"])
        for e in plan["remove"]:
            for p in e["scripts"]:
                assert p.rsplit("/", 1)[-1] not in names
        # 外部路徑 group 保留（orphan_warn 只列不刪；_group_scripts 只認本
        # repo 路徑——以 args 原文判定在場）
        assert any(
            "foreign.py" in str(h.get("args", []))
            for groups in new_root["hooks"]["events"].values()
            for g in groups
            for h in g.get("hooks", [])
        )

    def test_prune_stale_idempotent(self, tmp_path, monkeypatch):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        once, _c1 = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        _twice, c2 = gov.merge_json_hooks(
            once, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        assert not c2


class TestPruneApplyFace:
    def _apply_target(self, cfg, prune=True):
        t = {
            "kind": "json-subtree:zcode",
            "target": str(cfg),
            "template": "registrations/zcode.json",
            "merge_root": "hooks",
            "action": "merge",
        }
        if prune:
            t["prune_stale"] = True
        return gov._apply_target({}, t, "install")

    def test_receipt_and_backup_on_removal(
        self, tmp_path, monkeypatch, capsys
    ):
        """apply：先 backup 再移除；逐條 removed 行＋restart receipt 文案
        （禁宣稱 N 個 running session）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        assert self._apply_target(cfg) == "written"
        out = capsys.readouterr().out
        assert (
            "removed: UserPromptSubmit/{scbus-address-pending-reminder.py}"
            in out
        )
        assert "已移除 1 條 hook 引用" in out
        assert "既有 ZCode sessions 可能仍持 startup snapshot" in out
        assert "重開 session" in out and "每 prompt 可能報錯" in out
        assert "running session" not in out  # 禁程序枚舉宣稱
        assert list(cfg.parent.glob("config.json.bak-*-gov"))  # backup 在場
        doc = json.loads(cfg.read_text())
        assert "scbus-address-pending-reminder.py" not in _script_names(
            doc["hooks"]["events"]
        )

    def test_no_receipt_when_no_stale(self, tmp_path, monkeypatch, capsys):
        _repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"hooks": tmpl}, indent=2) + "\n")
        assert self._apply_target(cfg, prune=False) == "noop"
        assert self._apply_target(cfg) == "noop"
        assert "已移除" not in capsys.readouterr().out

    def test_dry_run_preview_lists_plan(self, tmp_path, monkeypatch, capsys):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [
                _repo_group(repo, "scbus-address-pending-reminder.py"),
                _foreign_group(tmp_path),
            ],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        manifest = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                }
            }
        }
        gov._print_prune_preview(manifest)
        out = capsys.readouterr().out
        assert "remove" in out
        assert "scbus-address-pending-reminder.py" in out
        assert "foreign.py" in out  # orphan_warn 只列不刪


class TestPrunePlanBuild:
    def test_prune_flag_scopes_to_json_subtree(self):
        manifest = gov.load_manifest()
        plan = gov.build_plan(manifest, "hooks", "install", prune_stale=True)
        zc = [
            t for t in plan["targets"]
            if t["kind"] == "json-subtree:zcode"
        ]
        assert zc and zc[0].get("prune_stale") is True
        assert all(
            not t.get("prune_stale")
            for t in plan["targets"]
            if t["kind"] != "json-subtree:zcode"
        )

    def test_default_build_plan_no_prune(self):
        manifest = gov.load_manifest()
        plan = gov.build_plan(manifest, "hooks", "install")
        assert all(not t.get("prune_stale") for t in plan["targets"])


class TestPruneCliFace:
    def test_prune_stale_check_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale", "--check"],
        )
        assert gov.main() == gov.EXIT_GUARD
        assert "prune-stale" in capsys.readouterr().err

    def test_prune_stale_uninstall_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale",
             "--uninstall"],
        )
        assert gov.main() == gov.EXIT_GUARD

    def test_prune_stale_dry_run_preview_via_cli(
        self, tmp_path, monkeypatch, capsys
    ):
        """"--prune-stale --dry-run＝只印 plan（預覽與 apply 同源）＋
        --zcode-config 注入面只改讀寫目標。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config-fixture.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale",
             "--dry-run", "--zcode-config", str(cfg)],
        )
        assert gov.main() == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "scbus-address-pending-reminder.py" in out
        assert "remove" in out


# ── AIR-255 修復輪 F-1：--zcode-config 旁路面收斂（僅演練 zcode 面）──


def _drill_manifest(tmp_path, repo, cfg):
    """F-1 演練測試 fake manifest：全部面寫入目標導到 tmp fake target
    （零寫入斷言＝這些路徑最終不存在）。"""
    grok_cfg = tmp_path / "grok-fake-target.json"
    codex_cfg = tmp_path / "codex-fake-target.toml"
    skills_link = tmp_path / "fake-skills-link"
    manifest = {
        "registrations": {
            "grok": {
                "merge": "file",
                "target": str(grok_cfg),
                "template": "registrations/grok.json",
            },
            "zcode": {
                "target": str(cfg),
                "template": "registrations/zcode.json",
                "merge_root": "hooks",
            },
            "codex": {
                "target": str(codex_cfg),
                "template": "registrations/codex.toml",
            },
        },
        "surfaces": {
            "skills": {
                "symlinks": [
                    {"link": str(skills_link), "target": str(repo / "skills")}
                ]
            },
            "rules": {"argv": ["wrap-rules"]},
            "agents": {"argv": ["wrap-agents"]},
            "memory": {"plugin_path": "p", "plugin_id": "x", "pool_setup": "s"},
        },
    }
    return manifest, grok_cfg, codex_cfg, skills_link


class TestZcodeConfigDrillScoping:
    """F-1（修復輪）：--zcode-config 在場（install/dry-run）＝僅演練 zcode 面
    ——其他面 skip＋一行註記＋fake target 零寫入；uninstall 行為不變（旗標
    只覆寫 zcode 面 target，不過濾面）。缺席→全面照跑＝既有測試群
    （test_governance_fail_independence 等）。"""

    @staticmethod
    def _recorders(monkeypatch):
        """wrap／memory 面執行記錄器（演練時不得被呼叫）。"""
        wraps: list[str] = []
        monkeypatch.setattr(
            gov, "run_wrap",
            lambda argv, extra=None: wraps.append(argv[0]) or 0,
        )
        muses: list[int] = []
        monkeypatch.setattr(gov, "_require_muse_cli", lambda: muses.append(1))
        monkeypatch.setattr(
            gov, "subprocess",
            SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="", stderr=""
            )),
        )
        return wraps, muses

    @staticmethod
    def _stale_cfg(monkeypatch, tmp_path):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config-fixture.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        monkeypatch.setattr(gov, "JOURNAL_DIR", tmp_path / "journal")
        # 同檔在前的 CLI dry-run 測試經 main()→set_dry_run() 污染模組全域
        # _DRY_RUN（一次性 latch）——install/uninstall 演練要真寫 fixture，釘回 False。
        monkeypatch.setattr(gov, "_DRY_RUN", False)
        return repo, cfg

    def test_drill_install_only_zcode_face(
        self, tmp_path, monkeypatch, capsys
    ):
        """surface=all＋flag＋install：僅 zcode 面 apply（其他面 fake target
        零寫入、wrap/memory 面零執行）＋skip 一行註記（跳過 6 面）。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, grok_cfg, codex_cfg, skills_link = _drill_manifest(
            tmp_path, repo, cfg
        )
        wraps, muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "all", "install", prune_stale=True, zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 6 面" in out
        assert "json-subtree:zcode" in out  # zcode 面 apply
        assert "render-file" not in out and "toml-groups" not in out
        assert "手動步驟" not in out  # 演練不印其他面的手動步驟
        assert wraps == [] and muses == []
        # zcode 面真寫入（fixture）：stale 已 prune＋receipt 在場
        assert "已移除 1 條 hook 引用" in out
        doc = json.loads(cfg.read_text())
        assert "scbus-address-pending-reminder.py" not in _script_names(
            doc["hooks"]["events"]
        )
        # 其他面 fake target 零寫入
        assert not grok_cfg.exists()
        assert not codex_cfg.exists()
        assert not skills_link.exists()

    def test_drill_install_non_hooks_surface_zero_apply(
        self, tmp_path, monkeypatch, capsys
    ):
        """surface 非 hooks/all：zcode 面不在 scope——零 apply、cfg 零寫入
        （skills 面 skip：link 不建立）。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        before = cfg.read_text()
        manifest, _grok, _codex, skills_link = _drill_manifest(
            tmp_path, repo, cfg
        )
        wraps, muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "skills", "install", zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 1 面" in out
        assert "json-subtree:zcode" not in out
        assert wraps == [] and muses == []
        assert cfg.read_text() == before
        assert not skills_link.exists()

    def test_drill_dry_run_zcode_only_preview(
        self, tmp_path, monkeypatch, capsys
    ):
        """dry-run＋flag：預覽同過濾（僅 zcode 面 plan；wrap 面零執行）
        ＋prune 預覽在場。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, _grok, _codex, _link = _drill_manifest(tmp_path, repo, cfg)
        wraps, _muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "all", "dry-run", prune_stale=True,
            zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 6 面" in out
        assert "json-subtree:zcode" in out
        assert "render-file" not in out and "toml-groups" not in out
        assert "symlink" not in out
        assert wraps == []  # wrap --dry-run 不跑
        assert "scbus-address-pending-reminder.py" in out  # prune 預覽
        assert "remove" in out

    def test_uninstall_with_flag_not_filtered(
        self, tmp_path, monkeypatch, capsys
    ):
        """uninstall 行為不變：flag 在場仍全面 uninstall（grok/codex 缺席
        target 走 not-present leave、zcode 面 target＝fixture 照拆模板
        group）——無演練過濾、無 skip 註記。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, _grok, _codex, _link = _drill_manifest(tmp_path, repo, cfg)
        monkeypatch.setattr(gov, "JOURNAL_DIR", tmp_path / "journal")
        rc = gov.cmd_install_uninstall(
            manifest, "hooks", "uninstall", zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" not in out
        # 全面 uninstall：grok/codex（缺席）＋zcode（在場）三面都執行
        assert "render-file" in out and "toml-groups" in out
        assert "not-present（leave）" in out and "written" in out
        doc = json.loads(cfg.read_text())
        names = _script_names(doc["hooks"]["events"])
        assert "zcode_agent_background_gate.py" not in names  # 模板 group 已拆
        assert "scbus-address-pending-reminder.py" in names  # uninstall 不 prune


class TestPruneCheckFace:
    def test_check_reports_stale_managed_with_prune_hint(
        self, tmp_path, monkeypatch
    ):
        """--check 對 stale 受管殘留報 drift＋--prune-stale 修法提示。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        m = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                    "target_is_symlink": False,
                }
            }
        }
        drifts: list = []
        gov.check_json_face(m, "zcode", drifts)
        hits = [msg for _, msg in drifts if "prune-stale" in msg]
        assert hits
        assert "scbus-address-pending-reminder.py" in hits[0]

    def test_check_pure_command_group_no_new_drift(
        self, tmp_path, monkeypatch
    ):
        """純 command 用戶 group（無套件腳本）→ check 零新增 drift
        （既有行為保留）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [{
                "hooks": [{
                    "type": "command",
                    "command": "scbus hook --harness zcode",
                }]
            }],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        m = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                    "target_is_symlink": False,
                }
            }
        }
        drifts: list = []
        gov.check_json_face(m, "zcode", drifts)
        assert drifts == []


class TestBackupRetention:
    def test_backup_keep_n_rotation(self, tmp_path):
        """備份保留 pin：自家後綴只留最近 BAK_KEEP 份（1201 教訓——mtime
        排序）。AIR-255 ⑤核對＝已有 keep-N，此測試釘住不退化。

        同秒同 pid 的 backup 檔名相同（互覆）——以預置檔＋distinct mtime
        模擬跨 run 累積，再觸發一次 backup_target 驗證 prune。"""
        f = tmp_path / "cfg.json"
        f.write_text("v0")
        oldest = tmp_path / "cfg.json.bak-20260101-000000-111-gov"
        oldest.write_text("oldest")
        os.utime(oldest, (1_000_000, 1_000_000))
        for i in range(gov.BAK_KEEP - 1):
            bak = tmp_path / f"cfg.json.bak-2026010{i + 2}-000000-111-gov"
            bak.write_text(f"recent{i}")
            os.utime(bak, (2_000_000 + i, 2_000_000 + i))
        f.write_text("v-new")
        gov.backup_target(f)  # 新備份 mtime＝now——最新
        baks = list(tmp_path.glob("cfg.json.bak-*-gov"))
        assert len(baks) == gov.BAK_KEEP
        assert not oldest.exists()  # mtime 最舊者被 prune
