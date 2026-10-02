"""scbus 門牌 receipt-timeline 監看提醒 hook 測試（AIR-233 消費面重寫）。

涵蓋（工單六項＋AIR-225.1 既有 fail-soft 契約保留）：
- receipts face 消費：runner 注入 mock（codex 草規形——items 帶
  envelope_id/message_id/from/accepted_at_us/stages＋next_cursor/has_more）；
  新到 N 封→提醒行計數正確＋cursor 推進（advance-after-emit——commit 由
  呼叫端在 stdout 寫出後執行）。
- 無新→靜默且 state 零動；冷啟動→只建 cursor 不告警（防歷史洪水）；
  分頁（has_more）收齊才推進。
- state 寫失敗→寧重不漏（提醒照出、cursor 不動、下次重複提醒）；
  state 損壞→顯性 reconcile（stderr 註記＋視同冷啟動重建）。
- monitor eligibility gate：cwd repo 外→零查詢零輸出零推進；cwd 缺席
  fail-closed。
- degraded：face 失敗（缺席／非零 exit／壞 JSON／形漂移）→零 stdout exit 0
  ＋stderr「receipts face 未落地」註記；SCBUS_MONITOR_RUNNER 環境變數 shim
  注入（真 subprocess 整合面）。
- 語義邊界：items 內容（envelope header/body 欄位）絕不進輸出（count-only）。
- governance 接線：zcode/cc 模板雙事件獨立 group＋manifest inventory；
  install merge 面新 group append、既有條目零動、冪等、uninstall 只拆本套件
  group（registrations 雙模板 AIR-233 零動——script 名與 args 不變）。
"""

import io
import json
import os
import sys

import pytest

from conftest import load_module

mod = load_module("hooks/scbus-address-pending-reminder.py")
gov = load_module("governance/install.py")

ADDRESS = "ai-guide-marshal"
REPO = "/fake/ai-guide/repo"


def _stdin(event="UserPromptSubmit", cwd=REPO):
    """合法 monitor invocation 形——cwd 在鎖內（gate autouse fixture 對齊）。"""
    return json.dumps({"hook_event_name": event, "session_id": "s1", "cwd": cwd})


UPS_STDIN = _stdin()
SS_STDIN = _stdin(event="SessionStart")


@pytest.fixture(autouse=True)
def _gate(monkeypatch):
    """eligibility gate 鎖定測試 repo——預設 stdin cwd 即鎖內。"""
    monkeypatch.setattr(mod, "script_repo_root", lambda: REPO)


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "state" / "scbus-address-monitor.json")


def _item(i, accepted_us):
    """receipts face 單 item（codex 草規形——唯讀 timeline，無 body/preview）。"""
    return {
        "envelope_id": "env-%d" % i,
        "message_id": "msg-%d" % i,
        "from": {"harness": "zcode", "session_id": "s-%d" % i, "name": None},
        "accepted_at_us": accepted_us,
        "stages": [
            {"stage": "accepted", "at_us": accepted_us},
            {
                "stage": "acked_at",
                "at_us": accepted_us + 1000,
                "generation": 4,
            },
        ],
    }


def _receipts(items, next_cursor, has_more, extra_first=None):
    """合成 receipts face stdout。extra_first：併入首 item 的額外欄位
    （釘住「item 內容絕不進 hook 輸出」語義邊界）。"""
    if extra_first and items:
        items = [dict(items[0], **extra_first)] + items[1:]
    return json.dumps(
        {
            "status": "ok",
            "op": "address-receipts",
            "address": ADDRESS,
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }
    )


def _page_runner(pages):
    """injectable runner：pages 依呼叫序回傳（str stdout 或 Exception）。"""
    calls = []

    def run(argv):
        calls.append(argv)
        page = pages[len(calls) - 1]
        if isinstance(page, Exception):
            raise page
        return page

    run.calls = calls
    return run


def _seed_state(state_file, cursor="cur-0", address=ADDRESS):
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as fh:
        json.dump({address: {"emitted_cursor": cursor}}, fh)


def _shim(doc, tmp_path, name="receipts-shim.py"):
    """SCBUS_MONITOR_RUNNER shim 執行檔——stdout 固定印 doc JSON。

    JSON 以 quoted-string 內嵌（JSON 字面值 null/false 非 Python literal，
    直接內嵌 source 會 NameError）。"""
    shim = tmp_path / name
    shim.write_text(
        "#!/usr/bin/env python3\n"
        "import json\n"
        "print(" + json.dumps(json.dumps(doc)) + ")\n",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim


def _read_state(state_file):
    with open(state_file, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ── 新到 N 封：提醒行計數＋cursor 推進（advance-after-emit）──────────


class TestNewReceiptsAlertAndCursor:
    def test_alert_line_semantics_and_count(self, state_file):
        _seed_state(state_file, "cur-0")
        runner = _page_runner([_receipts([_item(1, 100), _item(2, 200),
                                          _item(3, 300)], "cur-1", False)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert code == 0
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        ctx = doc["hookSpecificOutput"]["additionalContext"]
        assert "[" + mod.HOOK_TAG + "] " + ADDRESS in ctx
        assert "自上次知會後新到 3 封收件紀錄" in ctx
        assert "accepted≠送達 UI≠內文可讀" in ctx  # astra 邊界二語義校注
        assert "scbus address ls --pending" in ctx  # 讀取指針
        assert "SC UI" in ctx
        assert "recv/ack/acquire" in ctx  # 禁權聲明
        # 呼叫面照 face 草規：address receipts＋--address＋--after-cursor＋--limit
        assert runner.calls == [[
            "scbus", "address", "receipts",
            "--address", ADDRESS,
            "--limit", "100",
            "--after-cursor", "cur-0",
        ]]

    def test_advance_after_emit_not_before(self, state_file):
        """cursor 推進只發生在 commit()（stdout 寫出後）——run() 返回當下
        state 未動。"""
        _seed_state(state_file, "cur-0")
        runner = _page_runner([_receipts([_item(1, 100)], "cur-9", False)])
        _code, _out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert commit is not None
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-0"
        commit()
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-9"

    def test_sessionstart_event_name(self, state_file):
        _seed_state(state_file)
        runner = _page_runner([_receipts([_item(1, 100)], "c1", False)])
        _code, out, _commit = mod.run(SS_STDIN, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "SessionStart"

    def test_grok_snake_event_value_normalized(self, state_file):
        _seed_state(state_file)
        runner = _page_runner([_receipts([_item(1, 100)], "c1", False)])
        raw = json.dumps({"hookEventName": "user_prompt_submit", "cwd": REPO})
        _code, out, _commit = mod.run(raw, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert json.loads(out)["hookSpecificOutput"][
            "hookEventName"] == "UserPromptSubmit"

    def test_multipage_has_more_collected_before_advance(self, state_file):
        """has_more=true 續翻收齊——cursor 只推進到已消費完的位置。"""
        _seed_state(state_file, "cur-0")
        page1 = _receipts([_item(i, i) for i in range(100)], "cur-mid", True)
        page2 = _receipts([_item(101, 900), _item(102, 901)], "cur-end", False)
        runner = _page_runner([page1, page2])
        _code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                     state_file=state_file)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert "自上次知會後新到 102 封收件紀錄" in ctx
        assert runner.calls[1][
            runner.calls[1].index("--after-cursor") + 1] == "cur-mid"
        commit()
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-end"

    def test_multiple_addresses_two_lines_and_both_advance(self, state_file):
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "a-marshal": {"emitted_cursor": "cur-0"},
                    "b-marshal": {"emitted_cursor": "cur-0"},
                },
                fh,
            )
        pages = [
            _receipts([_item(1, 100)], "a-end", False),
            _receipts(
                [_item(1, 200), _item(2, 201), _item(3, 202), _item(4, 203)],
                "b-end",
                False,
            ),
        ]
        runner = _page_runner(pages)
        _code, out, commit = mod.run(
            UPS_STDIN, ["a-marshal", "b-marshal"], runner=runner,
            state_file=state_file,
        )
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert ctx.count("\n") == 1
        assert "a-marshal：自上次知會後新到 1 封" in ctx
        assert "b-marshal：自上次知會後新到 4 封" in ctx
        commit()
        doc = _read_state(state_file)
        assert doc["a-marshal"]["emitted_cursor"] == "a-end"
        assert doc["b-marshal"]["emitted_cursor"] == "b-end"

    def test_item_fields_never_leak_into_output(self, state_file):
        """count-only 語義邊界：item 的 envelope header／body／preview 欄位
        絕不進輸出（face 形漂移多帶欄位也不洩）。"""
        _seed_state(state_file)
        runner = _page_runner([
            _receipts([_item(1, 100)], "c1", False,
                      extra_first={"body": "TOP-SECRET-BODY",
                                   "preview": "TOP-SECRET-PREVIEW"}),
        ])
        _code, out, _commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert "TOP-SECRET" not in out
        assert "envelope_id" not in out
        assert "stages" not in out


# ── 無新／冷啟動：靜默與只建 cursor────────────────────────────────────


class TestSilentAndColdStart:
    def test_zero_new_silent_state_untouched(self, state_file):
        _seed_state(state_file, "cur-0")
        runner = _page_runner([_receipts([], None, False)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-0"

    def test_no_address_flag_zero_stdout_without_scbus_call(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        code, out, commit = mod.run(UPS_STDIN, [], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_cold_start_builds_cursor_no_alert(self, state_file):
        """無 state 檔＝冷啟動：掃至 timeline 尾端只建 cursor、不告警
        （防歷史洪水）；首查不帶 --after-cursor。"""
        assert not os.path.exists(state_file)
        page1 = _receipts([_item(1, 100), _item(2, 200)], "c1", True)
        page2 = _receipts(
            [_item(i, i * 100) for i in range(3, 7)], "c-end", False
        )
        runner = _page_runner([page1, page2])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out) == (0, "")
        assert "--after-cursor" not in runner.calls[0]
        assert runner.calls[1][runner.calls[1].index("--after-cursor") + 1] == "c1"
        commit()
        assert _read_state(state_file) == {ADDRESS: {"emitted_cursor": "c-end"}}

    def test_cold_start_empty_timeline_no_state_write(self, state_file):
        """空 timeline 且 face 未給端點 token——無 cursor 可建，下輪重掃。"""
        runner = _page_runner([_receipts([], None, False)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert not os.path.exists(state_file)

    def test_cold_start_new_items_then_warm_alerts_only_delta(self, state_file):
        """冷啟動建 cursor 後，新 delivery 才告警——歷史不重灌。"""
        runner = _page_runner([_receipts([_item(1, 100)], "c-base", False)])
        _code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                     state_file=state_file)
        assert out == ""  # 冷啟動不告警
        commit()
        runner2 = _page_runner([_receipts([_item(2, 900)], "c-next", False)])
        _code, out2, _ = mod.run(UPS_STDIN, [ADDRESS], runner=runner2,
                                 state_file=state_file)
        assert "自上次知會後新到 1 封" in out2


# ── state 寫失敗／損壞：寧重不漏＋顯性 reconcile──────────────────────


class TestStateResilience:
    def test_state_write_failure_duplicate_next_run(self, state_file,
                                                    monkeypatch):
        """寫失敗寧可重複提醒：提醒照出（emitted）、推進失敗 cursor 不動、
        下次同批重複提醒（寧重不漏）。"""
        _seed_state(state_file, "cur-0")

        def boom(path, doc):
            raise OSError("disk on fire")

        orig_save = mod.save_state
        monkeypatch.setattr(mod, "save_state", boom)
        runner = _page_runner(
            [_receipts([_item(1, 100), _item(2, 200)], "cur-9", False)]
        )
        _code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                     state_file=state_file)
        assert "自上次知會後新到 2 封" in out  # 提醒照出
        with pytest.raises(OSError):
            commit()  # 推進失敗——main() 吸收成 stderr、exit 0
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-0"

        # 下次 invocation：cursor 仍在 cur-0——同批重複提醒（寧重不漏）。
        # 不用 monkeypatch.undo()——會連動拆掉 autouse gate fixture 的鎖。
        monkeypatch.setattr(mod, "save_state", orig_save)
        runner2 = _page_runner(
            [_receipts([_item(1, 100), _item(2, 200)], "cur-9", False)]
        )
        _code, out2, _ = mod.run(UPS_STDIN, [ADDRESS], runner=runner2,
                                 state_file=state_file)
        assert "自上次知會後新到 2 封" in out2

    def test_corrupt_state_file_reconciled_as_cold_start(self, state_file,
                                                         capsys):
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        runner = _page_runner([_receipts([_item(1, 100)], "c-end", False)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out) == (0, "")  # 不告警（冷啟動語義）
        assert "損壞" in capsys.readouterr().err  # 顯性 reconcile
        commit()
        assert _read_state(state_file) == {ADDRESS: {"emitted_cursor": "c-end"}}

    def test_corrupt_cursor_value_reconciled(self, state_file, capsys):
        _seed_state(state_file, cursor=123)  # 非 str——cursor 損壞
        runner = _page_runner([_receipts([_item(1, 100)], "c-end", False)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out) == (0, "")
        assert "emitted_cursor 損壞" in capsys.readouterr().err
        commit()
        assert _read_state(state_file) == {ADDRESS: {"emitted_cursor": "c-end"}}

    def test_main_commit_failure_exit0_stderr_note(self, tmp_path, capsys,
                                                   monkeypatch):
        """main() 面：推進失敗不擋 turn——提醒照出、exit 0、stderr 註記。

        main() 無 runner／state_file 參數——查詢走 SCBUS_MONITOR_RUNNER shim、
        state 走 XDG_STATE_HOME（皆 env 注入）。"""
        shim = _shim(
            {
                "status": "ok",
                "op": "address-receipts",
                "address": ADDRESS,
                "items": [_item(1, 100)],
                "next_cursor": "cur-9",
                "has_more": False,
            },
            tmp_path,
            name="commit-fail-shim.py",
        )
        monkeypatch.setenv(mod.RUNNER_ENV, str(shim))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        state = tmp_path / "ai-guide" / "scbus-address-monitor.json"
        os.makedirs(str(state.parent), exist_ok=True)
        state.write_text(
            json.dumps({ADDRESS: {"emitted_cursor": "cur-0"}}),
            encoding="utf-8",
        )

        def boom(path, doc):
            raise OSError("disk on fire")

        monkeypatch.setattr(mod, "save_state", boom)
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = mod.main(["--address", ADDRESS])
        assert rc == 0
        captured = capsys.readouterr()
        assert "自上次知會後新到 1 封" in captured.out
        assert "cursor 推進失敗" in captured.err


# ── monitor eligibility gate（cwd 鎖）────────────────────────────────


class TestEligibilityGate:
    def test_cwd_outside_repo_silent_no_query_no_state(self, state_file):
        _seed_state(state_file, "cur-0")
        runner = _page_runner([AssertionError("must not call scbus")])
        raw = _stdin(cwd="/tmp/other-project")
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []  # 零查詢
        assert _read_state(state_file)[
            ADDRESS]["emitted_cursor"] == "cur-0"  # 不推進

    def test_cwd_missing_fail_closed(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit"})
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_cwd_subdirectory_of_repo_proceeds(self, state_file):
        _seed_state(state_file)
        runner = _page_runner([_receipts([_item(1, 100)], "c1", False)])
        raw = _stdin(cwd=REPO + "/hooks/deep/dir")
        _code, out, _commit = mod.run(raw, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert "自上次知會後新到 1 封" in out

    def test_cwd_repo_root_exact_proceeds(self, state_file):
        _seed_state(state_file)
        runner = _page_runner([_receipts([_item(1, 100)], "c1", False)])
        _code, out, _commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                      state_file=state_file)
        assert "自上次知會後新到 1 封" in out

    def test_prefix_sibling_path_not_eligible(self):
        """字面前綴鎖不吞 sibling：/fake/ai-guide/repo-x 不在 repo 內。"""
        assert mod.is_eligible(REPO + "-x/sub") is False
        assert mod.is_eligible(None) is False
        assert mod.is_eligible("") is False
        assert mod.is_eligible(123) is False
        assert mod.is_eligible(REPO) is True
        assert mod.is_eligible(REPO + "/sub") is True


# ── degraded：face 失敗靜默＋stderr 註記；shim 注入面─────────────────


class TestDegradedFaceUnavailable:
    def test_runner_failure_silent_with_degraded_note(self, state_file,
                                                      capsys):
        _seed_state(state_file)
        runner = _page_runner([RuntimeError("exit 2: unknown command")])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)  # 零 stdout exit 0
        err = capsys.readouterr().err
        assert "receipts face 未落地——sc-router 卡追蹤中" in err
        assert "fail-soft" in err

    def test_bad_json_stdout_silent(self, state_file):
        _seed_state(state_file)
        runner = _page_runner(["Traceback (most recent call last):"])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_shape_drift_items_not_list_silent(self, state_file):
        _seed_state(state_file)
        runner = _page_runner([json.dumps({"status": "ok", "items": 3})])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_has_more_without_next_cursor_silent(self, state_file):
        _seed_state(state_file, "cur-0")
        runner = _page_runner([_receipts([_item(1, 100)], None, True)])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_paging_cap_exceeded_silent_no_advance(self, state_file):
        """分頁上限觸發 raise → fail-soft：不 emit 不推進（寧重不漏）。"""
        _seed_state(state_file, "cur-0")
        pages = [
            _receipts([_item(i, i)], "c-p%d" % i, True)
            for i in range(mod.RECEIPTS_MAX_PAGES)
        ]
        runner = _page_runner(pages)
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert len(runner.calls) == mod.RECEIPTS_MAX_PAGES
        assert _read_state(state_file)[ADDRESS]["emitted_cursor"] == "cur-0"

    def test_runner_env_var_routes_to_shim(self, state_file, tmp_path,
                                           monkeypatch):
        """SCBUS_MONITOR_RUNNER 環境變數指向 shim 執行檔——stub-first 整合面
        （真 subprocess、無函式注入）。"""
        shim = _shim(
            {
                "status": "ok",
                "op": "address-receipts",
                "address": ADDRESS,
                "items": [_item(1, 100), _item(2, 200)],
                "next_cursor": "cur-shim-end",
                "has_more": False,
            },
            tmp_path,
        )
        monkeypatch.setenv(mod.RUNNER_ENV, str(shim))
        _seed_state(state_file, "cur-0")
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], state_file=state_file)
        assert code == 0
        assert "自上次知會後新到 2 封" in out
        commit()
        assert _read_state(state_file)[
            ADDRESS]["emitted_cursor"] == "cur-shim-end"

    def test_runner_env_var_shim_failure_silent(self, state_file, tmp_path,
                                                monkeypatch):
        shim = tmp_path / "failing-shim.py"
        shim.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "sys.stderr.write('unknown command')\n"
            "sys.exit(3)\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        monkeypatch.setenv(mod.RUNNER_ENV, str(shim))
        _seed_state(state_file, "cur-0")
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_default_runner_nonzero_exit_raises(self, tmp_path, monkeypatch):
        shim = tmp_path / "exit-shim.py"
        shim.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n")
        shim.chmod(0o755)
        monkeypatch.setenv(mod.RUNNER_ENV, str(shim))
        with pytest.raises(RuntimeError, match="scbus exit 1"):
            mod._default_runner(["scbus", "address", "receipts"])


# ── fail-soft 既有契約（AIR-225.1 全保留）────────────────────────────


class TestFailSoftContract:
    def test_bad_stdin_json(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        code, out, commit = mod.run("{not json", [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_empty_stdin(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        code, out, commit = mod.run("", [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_stdin_not_object(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        code, out, commit = mod.run("[1,2]", [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_unknown_event_silent_without_scbus_call(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        raw = json.dumps({"hook_event_name": "Stop", "cwd": REPO})
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_missing_event_name_silent(self, state_file):
        runner = _page_runner([AssertionError("must not call scbus")])
        raw = json.dumps({"session_id": "s1", "cwd": REPO})
        code, out, commit = mod.run(raw, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)

    def test_cold_start_face_failure_retries_next_run(self, state_file):
        """冷啟動遇 face 失敗：靜默零寫——下輪仍冷啟動可重建（不毒化 state）。"""
        runner = _page_runner([RuntimeError("exit 2")])
        code, out, commit = mod.run(UPS_STDIN, [ADDRESS], runner=runner,
                                    state_file=state_file)
        assert (code, out, commit) == (0, "", None)
        assert not os.path.exists(state_file)


# ── governance 接線：registrations 雙事件獨立 group＋merge 面（零動）──


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
                if "scbus-address-pending-reminder.py" in _hook_scripts(g)
            ]
            assert len(hits) == 1, event
            entry = hits[0]["hooks"][0]
            assert entry["type"] == "process"
            assert "async" not in entry  # sync——additionalContext 只進 sync 通道
            assert entry.get("timeoutMs")
            assert entry["args"][1:] == ["--address", "ai-guide-marshal"]

    def test_zcode_template_existing_entries_untouched(self):
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        assert len(ups) == 2  # compact-restore-inject ＋ pending-reminder
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
                if "scbus-address-pending-reminder.py" in _hook_scripts(g)
            ]
            assert len(hits) == 1, event

    def test_manifest_inventory_lists_script(self):
        manifest = gov.load_manifest()
        assert "hooks/scbus-address-pending-reminder.py" in manifest["surfaces"][
            "hooks"
        ]["scripts"]


class TestInstallMergeFace:
    def _template(self):
        raw = (gov.MANIFEST_PATH.parent / "registrations/zcode.json").read_text()
        # render_uninstall：展開 REPO（identity 靠真實 hooks 路徑），HOOK_PYTHON 保留
        return json.loads(gov.render_uninstall(raw))

    def _live(self):
        """模擬 live config root——既有形態取自模板既有 group（保證 byte 等值、
        隔離「內容更新」語義，聚焦本卡新增 group 的 append 行為）；scbus
        canonical 條目照 live config 實際形（純 command 字串、SS 帶 async）。"""
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
        assert len(ups) == 3
        assert len(ss) == 2
        assert ss[0] == live_ss[0]  # scbus async 條目零動
        tail_ups = gov._group_scripts(ups[2])
        tail_ss = gov._group_scripts(ss[1])
        assert tail_ups == frozenset({"scbus-address-pending-reminder.py"})
        assert tail_ss == tail_ups

    def test_merge_idempotent(self):
        live = self._live()
        tmpl = self._template()
        once, _ = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
        _again, changed = gov.merge_json_hooks(once, tmpl, "hooks", remove=False)
        assert not changed

    def test_uninstall_removes_only_package_groups(self):
        live = self._live()
        tmpl = self._template()
        merged, _ = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
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
                if "scbus-address-pending-reminder.py" in gov._group_scripts(g)
            ]
            assert len(ours) == 1, event
            assert len(ours[0][1]) == 1
            others = {
                gov._group_identity(g) for g in tmpl["events"][event]
            } - set(ours)
            assert ours[0] not in others
