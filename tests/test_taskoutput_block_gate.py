"""taskoutput_block_gate hook 測試（AIR-249）——TaskOutput 阻塞等待紀律閘。

判準（codex 討論腿修正後 GO）：deny 僅當 tool==TaskOutput（PreToolUse）且
tool_input.block is True 且 tool_input.timeoutMs 為 number 且 > 60000。
其餘（block=false／block=true 有界短等待 ≤60000／無 timeoutMs／字串 "true"／
字串 timeoutMs／壞 JSON／非 TaskOutput／非 PreToolUse／任何例外）一律放行
（fail-open）。deny 零副作用（stateless，不落任何檔）。
"""

import json

from conftest import load_module

tbg = load_module("hooks/taskoutput_block_gate.py")

SESSION = "sess_test-249"


def _payload(event, tool, tool_input):
    return json.dumps(
        {
            "hook_event_name": event,
            "session_id": SESSION,
            "tool_name": tool,
            "tool_input": tool_input,
        }
    )


def _taskoutput_payload(block, timeoutMs="__absent__"):
    tool_input = {"task_id": "exec_test-1"}
    if block != "__absent__":
        tool_input["block"] = block
    if timeoutMs != "__absent__":
        tool_input["timeoutMs"] = timeoutMs
    return _payload("PreToolUse", "TaskOutput", tool_input)


def test_deny_long_block_wait(capsys):
    code = tbg.run(_taskoutput_payload(True, 60001))
    out = capsys.readouterr()
    assert code == 2
    data = json.loads(out.out)
    d = data["hookSpecificOutput"]
    assert d["hookEventName"] == "PreToolUse"
    assert d["permissionDecision"] == "deny"
    assert "block=false" in d["permissionDecisionReason"]
    assert "60000" in d["permissionDecisionReason"]


def test_boundary_60000_allowed(capsys):
    assert tbg.run(_taskoutput_payload(True, 60000)) == 0
    assert capsys.readouterr().out == ""


def test_block_true_without_timeout_allowed(capsys):
    # timeoutMs 缺席＝工具預設 30s（有界短等待）→ 放行
    assert tbg.run(_taskoutput_payload(True)) == 0


def test_block_false_allowed_any_timeout(capsys):
    assert tbg.run(_taskoutput_payload(False, 300000)) == 0


def test_block_string_true_fail_open(capsys):
    # 字串 "true" 非 boolean——malformed，fail-open 放行
    assert tbg.run(_taskoutput_payload("true", 300000)) == 0


def test_timeoutms_string_fail_open(capsys):
    assert tbg.run(_taskoutput_payload(True, "120000")) == 0


def test_non_taskoutput_tool_allowed(capsys):
    assert tbg.run(_payload("PreToolUse", "Bash", {"command": "ls"})) == 0


def test_non_pretooluse_event_allowed(capsys):
    assert tbg.run(_payload("PostToolUse", "TaskOutput", {"block": True, "timeoutMs": 300000})) == 0


def test_bad_json_fail_open(capsys):
    assert tbg.run("not json {") == 0


def test_non_dict_payload_fail_open(capsys):
    assert tbg.run(json.dumps(["list"])) == 0


def test_tool_input_non_dict_fail_open(capsys):
    raw = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "session_id": SESSION,
            "tool_name": "TaskOutput",
            "tool_input": ["not", "a", "dict"],
        }
    )
    assert tbg.run(raw) == 0


def test_negative_timeout_allowed(capsys):
    assert tbg.run(_taskoutput_payload(True, -1)) == 0


def test_deny_no_file_side_effects(tmp_path, capsys, monkeypatch):
    # stateless 閘——deny 路徑不落任何檔（.agent-tmp 無 marker 類產物）
    monkeypatch.chdir(tmp_path)
    tbg.run(_taskoutput_payload(True, 120000))
    capsys.readouterr()
    assert not (tmp_path / ".agent-tmp").exists()
