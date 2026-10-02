"""scbus 門牌 pending 監看提醒 hook 測試（AIR-225.1）。

涵蓋（卡 AC＋前置驗證 P-B）：
- pending>0 注入：additionalContext 含 address＋count＋指針＋禁權聲明；
  UPS 與 SessionStart 各自 hookEventName 正確（單 script 兩事件）。
- pending=0／無 --address：零 stdout exit 0（靜默不擋 turn）。
- fail-soft：scbus 缺席／命令失敗／stdout 壞 JSON／門牌不在清單／stdin 壞／
  未知事件——一律零 stdout exit 0（繼承 L2：ZCode exit 2＝擋 turn）。
- 語義邊界：上游 holder-less preview 欄位絕不進輸出（禁洩信件內容）。
- governance 接線：zcode/cc 模板雙事件獨立 group＋manifest inventory；
  install merge 面新 group append、既有條目（scbus canonical／
  compact-restore-inject）零動、冪等、uninstall 只拆本套件 group。
"""

import json

from conftest import load_module

mod = load_module("hooks/scbus-address-pending-reminder.py")
gov = load_module("governance/install.py")

ADDRESS = "ai-guide-marshal"
UPS_STDIN = json.dumps(
    {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "cwd": "/tmp"}
)
SS_STDIN = json.dumps(
    {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": "/tmp"}
)


def _listing(**counts):
    """合成 `scbus address ls --pending` stdout——counts: address→pending 數。

    首封 pending header 帶 preview 欄位（上游 holder-less 形態）——釘住
    「preview 絕不進 hook 輸出」的語義邊界。
    """
    entries = []
    for addr, n in counts.items():
        headers = [
            {
                "envelope_id": f"env-{i}",
                "from": "someone",
                "mode": "queue",
                "created_at_us": 1,
            }
            for i in range(n)
        ]
        if headers:
            headers[0]["preview"] = "TOP-SECRET-BODY-PREVIEW"
        entries.append({"address": addr, "binding": None, "pending": headers})
    return json.dumps(
        {"status": "ok", "count": len(entries), "addresses": entries}
    )


def _runner(stdout=None, exc=None):
    """injectable runner：回傳固定 stdout 或 raise；未呼叫不炸（用 sentinel 斷言）。"""
    calls = []

    def run(argv):
        calls.append(argv)
        if exc is not None:
            raise exc
        return stdout

    run.calls = calls
    return run


def _out_context(raw, addresses, runner):
    code, out = mod.run(raw, addresses, runner=runner)
    return code, out


# ── pending>0：注入一行（兩事件 hookEventName 正確——P-B）──────────


class TestPendingPositiveInjects:
    def test_ups_injects_address_count_and_pointer(self):
        runner = _runner(_listing(**{ADDRESS: 2}))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert code == 0
        doc = json.loads(out)
        ctx = doc["hookSpecificOutput"]["additionalContext"]
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "[" + mod.HOOK_TAG + "] " + ADDRESS + " pending=2" in ctx
        assert "scbus address ls --pending" in ctx
        assert "recv/ack/acquire" in ctx
        assert runner.calls == [["scbus", "address", "ls", "--pending"]]

    def test_sessionstart_event_name(self):
        runner = _runner(_listing(**{ADDRESS: 1}))
        code, out = _out_context(SS_STDIN, [ADDRESS], runner)
        assert code == 0
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert ADDRESS + " pending=1" in doc["hookSpecificOutput"]["additionalContext"]

    def test_grok_snake_event_value_normalized(self):
        raw = json.dumps({"hookEventName": "user_prompt_submit"})
        runner = _runner(_listing(**{ADDRESS: 1}))
        _code, out = _out_context(raw, [ADDRESS], runner)
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    def test_preview_never_leaks_into_context(self):
        runner = _runner(_listing(**{ADDRESS: 3}))
        _code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert "TOP-SECRET-BODY-PREVIEW" not in out
        assert "preview" not in out

    def test_repeated_address_only_positive_lines(self):
        runner = _runner(_listing(**{"ai-guide-marshal": 2, "other-marshal": 0}))
        _code, out = _out_context(
            UPS_STDIN, ["ai-guide-marshal", "other-marshal"], runner
        )
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert "ai-guide-marshal pending=2" in ctx
        assert "other-marshal" not in ctx

    def test_multiple_positive_addresses_two_lines(self):
        runner = _runner(_listing(**{"a-marshal": 1, "b-marshal": 4}))
        _code, out = _out_context(UPS_STDIN, ["a-marshal", "b-marshal"], runner)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert ctx.count("\n") == 1
        assert "a-marshal pending=1" in ctx
        assert "b-marshal pending=4" in ctx


# ── pending=0／無參數：零 stdout 靜默──────────────────────────────


class TestSilentPaths:
    def test_pending_zero_zero_stdout(self):
        runner = _runner(_listing(**{ADDRESS: 0}))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_no_address_flag_zero_stdout_without_scbus_call(self):
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context(UPS_STDIN, [], runner)
        assert (code, out) == (0, "")
        assert runner.calls == []


# ── fail-soft：任何錯誤零 stdout exit 0───────────────────────────


class TestFailSoft:
    def test_scbus_binary_missing(self):
        runner = _runner(exc=FileNotFoundError("scbus"))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_scbus_nonzero_exit(self):
        runner = _runner(exc=RuntimeError("exit 1: envelope_corrupt"))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_scbus_bad_json_stdout(self):
        runner = _runner("Traceback (most recent call last):")
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_scbus_unexpected_shape(self):
        runner = _runner(json.dumps({"status": "ok", "addresses": "not-a-list"}))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_address_not_in_listing(self):
        runner = _runner(_listing(other=1))
        code, out = _out_context(UPS_STDIN, [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_bad_stdin_json(self):
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context("{not json", [ADDRESS], runner)
        assert (code, out) == (0, "")
        assert runner.calls == []

    def test_empty_stdin(self):
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context("", [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_stdin_not_object(self):
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context("[1,2]", [ADDRESS], runner)
        assert (code, out) == (0, "")

    def test_unknown_event_silent_without_scbus_call(self):
        raw = json.dumps({"hook_event_name": "Stop"})
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context(raw, [ADDRESS], runner)
        assert (code, out) == (0, "")
        assert runner.calls == []

    def test_missing_event_name_silent(self):
        raw = json.dumps({"session_id": "s1"})
        runner = _runner(exc=AssertionError("must not call scbus"))
        code, out = _out_context(raw, [ADDRESS], runner)
        assert (code, out) == (0, "")


# ── governance 接線：registrations 雙事件獨立 group＋merge 面──────


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
        assert len(ups) == 2  # compact-restore-inject ＋ 新 pending-reminder
        compact = [
            g for g in ups if "compact-restore-inject.py" in _hook_scripts(g)
        ]
        assert len(compact) == 1
        entry = compact[0]["hooks"][0]
        assert entry["type"] == "process"
        assert entry.get("enabled") is True
        assert entry.get("timeoutMs") == 10000
        # 新增 SessionStart 事件鍵不擠掉既有事件面
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
        # 既有兩 UPS group 原樣在前、scbus canonical（空 scripts identity）不動
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
        # 套件 group（compact-restore＋pending-reminder×2）全拆；scbus canonical
        # 條目（非本套件——空 scripts identity 不相符）原樣保留
        events = back["hooks"]["events"]
        assert len(events["UserPromptSubmit"]) == 1
        assert gov._group_scripts(events["UserPromptSubmit"][0]) == frozenset()
        assert events["SessionStart"] == live["hooks"]["events"]["SessionStart"]
        assert gov._group_scripts(events["SessionStart"][0]) == frozenset()

    def test_identity_no_collapse_with_canonical_or_compact(self):
        tmpl = self._template()
        # identity 是 per-event scope（merge/check 逐事件比對）——UPS 與 SS
        # 兩條目共用同一 identity 合法；同事件內須恰一、且可解析非空。
        for event in ("UserPromptSubmit", "SessionStart"):
            ours = [
                gov._group_identity(g)
                for g in tmpl["events"][event]
                if "scbus-address-pending-reminder.py" in gov._group_scripts(g)
            ]
            assert len(ours) == 1, event
            assert len(ours[0][1]) == 1
            # 與同事件其他 group（compact / scbus canonical）identity 不相撞
            others = {
                gov._group_identity(g) for g in tmpl["events"][event]
            } - set(ours)
            assert ours[0] not in others
