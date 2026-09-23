"""kanban-skill-gate hook 測試（AIR-170 交付一）——動卡前紀律閘。

四軸（工單明定）：deny（無 marker＋匹配指令）／allow（有 marker）／
非匹配指令放行（list/board 不算動卡）／marker 查詢異常 fail-open；
另釘 PostToolUse Read 偵測面（目標路徑尾段判定落 marker、非目標讀取
不落、寫入照 .agent-tmp 約定）與 stdin 壞 JSON fail-open。
"""

import json
from pathlib import Path

from conftest import load_module

ksg = load_module("hooks/kanban-skill-gate.py")

SESSION = "sess_test-1234"
SKILL_REL = Path("skills/kanban-board/SKILL.md")


def _payload(event, tool, tool_input, cwd, session_id=SESSION):
    return json.dumps(
        {
            "hook_event_name": event,
            "session_id": session_id,
            "cwd": str(cwd),
            "tool_name": tool,
            "tool_input": tool_input,
        }
    )


def _bash_payload(command, cwd):
    return _payload("PreToolUse", "Bash", {"command": command}, cwd)


def _marker(cwd):
    return Path(cwd) / ".agent-tmp" / "kanban-skill-gate" / (SESSION + ".read")


def test_deny_without_marker(tmp_path, capsys):
    code = ksg.run(_bash_payload('backlog task create "新卡" -l infra', tmp_path))
    captured = capsys.readouterr()
    assert code == 2
    data = json.loads(captured.out)
    spec = data["hookSpecificOutput"]
    assert spec["hookEventName"] == "PreToolUse"
    assert spec["permissionDecision"] == "deny"
    assert (
        "先讀 skills/kanban-board/SKILL.md 再動卡" in spec["permissionDecisionReason"]
    )
    assert "先讀 skills/kanban-board/SKILL.md 再動卡" in captured.err


def test_deny_compound_command(tmp_path):
    code = ksg.run(_bash_payload("cd /tmp && backlog task edit 170 -s Done", tmp_path))
    assert code == 2


def test_allow_with_marker(tmp_path, capsys):
    _marker(tmp_path).parent.mkdir(parents=True)
    _marker(tmp_path).write_text("read\n")
    code = ksg.run(_bash_payload('backlog task edit 170 --plan "spec"', tmp_path))
    assert code == 0
    assert capsys.readouterr().out == ""


def test_non_matching_command_passes_without_marker(tmp_path, capsys):
    # 註：指令文本「他處引號內」含 backlog task create 字樣（如 git commit -m
    # "backlog task create ..."）仍會命中——regex 是字面匹配（工單明定），
    # 誤擋面＝deny＋指引、讀規範一次即消，屬可接受紀律閘代價，不在此釘行為。
    for cmd in (
        "backlog task list",
        "backlog board",
        "backlog draft promote DRAFT-3",
        "backlog task list --plain",
        "uv run pytest tests/test_kanban_skill_gate.py",
    ):
        assert ksg.run(_bash_payload(cmd, tmp_path)) == 0
        assert capsys.readouterr().out == ""


def test_failopen_on_missing_session_id(tmp_path, capsys):
    raw = _payload(
        "PreToolUse",
        "Bash",
        {"command": "backlog task create x"},
        tmp_path,
        session_id="",
    )
    assert ksg.run(raw) == 0
    assert capsys.readouterr().out == ""


def test_failopen_on_session_id_key_absent(tmp_path, capsys):
    """缺鍵（payload.get→None）不得被 str(None)="None" 當合法 id——entrypoint
    實跑抓到的回歸釘住（缺 session_id 的匹配指令須放行非 deny）。"""
    payload = json.loads(_bash_payload("backlog task create x", tmp_path))
    del payload["session_id"]
    assert ksg.run(json.dumps(payload)) == 0
    assert capsys.readouterr().out == ""


def test_failopen_on_malformed_stdin(capsys):
    assert ksg.run("not-json{{") == 0
    assert capsys.readouterr().out == ""


def test_posttooluse_read_kanban_skill_writes_marker(tmp_path):
    skill = tmp_path / SKILL_REL
    skill.parent.mkdir(parents=True)
    skill.write_text("# kanban\n")
    raw = _payload("PostToolUse", "Read", {"file_path": str(skill)}, tmp_path)
    assert ksg.run(raw) == 0
    assert _marker(tmp_path).is_file()


def test_posttooluse_read_relative_path_writes_marker(tmp_path):
    skill = tmp_path / SKILL_REL
    skill.parent.mkdir(parents=True)
    skill.write_text("# kanban\n")
    raw = _payload(
        "PostToolUse", "Read", {"file_path": "skills/kanban-board/SKILL.md"}, tmp_path
    )
    assert ksg.run(raw) == 0
    assert _marker(tmp_path).is_file()


def test_posttooluse_other_read_writes_no_marker(tmp_path):
    other = tmp_path / "README.md"
    other.write_text("x\n")
    raw = _payload("PostToolUse", "Read", {"file_path": str(other)}, tmp_path)
    assert ksg.run(raw) == 0
    assert not (tmp_path / ".agent-tmp").exists()


def test_read_marker_then_bash_allow_end_to_end(tmp_path):
    skill = tmp_path / SKILL_REL
    skill.parent.mkdir(parents=True)
    skill.write_text("# kanban\n")
    assert (
        ksg.run(_payload("PostToolUse", "Read", {"file_path": str(skill)}, tmp_path))
        == 0
    )
    assert ksg.run(_bash_payload("backlog task create y", tmp_path)) == 0
