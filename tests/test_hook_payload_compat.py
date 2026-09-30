"""hook payload 相容層＋dual-shape pipe-test（AIR-218 B2）。

契約：CC/ZCode 恆送 snake_case 容器鍵＋PascalCase event 值＋CC tool 名；
grok 送 camelCase 容器鍵（toolName/toolInput/sessionId/hookEventName）＋
snake_case event 值＋grok real tool 名（run_terminal_command/read_file/
search_replace），read_file 工具參數內鍵用 target_file 而非 file_path。

雙讀語義＝snake 優先、camel fallback——CC 形下第二項是死碼（行為零變；
既有 hook 測試零回歸是機械面）。policy 判斷留各 hook，compat 層只做
鍵值正規化。
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

from conftest import load_module

compat = load_module("hooks/hook_payload_compat.py")
ksg = load_module("hooks/kanban-skill-gate.py")

HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
BLOCK_MEMORY = HOOKS_DIR / "block-memory-index-write.py"

SESSION = "sess_compat-1"


# ---------------------------------------------------------------------------
# compat 層單元：鍵值正規化（容器鍵/event 值/tool 值/target_file）
# ---------------------------------------------------------------------------


def test_container_key_snake_priority_camel_fallback():
    # 兩鍵並存（grok payload 對 hook_event_name 帶雙鍵）→ snake 優先；
    # 僅 camel 在場 → fallback 命中
    both = {"tool_name": "Edit", "toolName": "search_replace"}
    assert compat.tool_name(both) == "Edit"
    camel_only = {"toolName": "search_replace"}
    assert compat.tool_name(camel_only) == "Edit"


def test_event_value_snake_normalized_to_cc_pascal():
    # grok hookEventName 帶 snake 值 → 正規化為 CC PascalCase（hook 比較面共用）
    assert compat.hook_event_name({"hookEventName": "pre_tool_use"}) == "PreToolUse"
    assert compat.hook_event_name({"hookEventName": "post_tool_use"}) == "PostToolUse"
    assert compat.hook_event_name({"hookEventName": "user_prompt_submit"}) == (
        "UserPromptSubmit"
    )
    # CC 形（snake 鍵＋PascalCase 值）原樣通過
    assert compat.hook_event_name({"hook_event_name": "PreToolUse"}) == "PreToolUse"
    # grok 雙鍵形：snake 鍵帶 PascalCase 值（binary-bundled docs L283）→ 原值
    dual = {"hook_event_name": "Stop", "hookEventName": "stop"}
    assert compat.hook_event_name(dual) == "Stop"


def test_tool_value_grok_real_name_mapped_to_cc():
    assert compat.tool_name({"toolName": "run_terminal_command"}) == "Bash"
    assert compat.tool_name({"toolName": "read_file"}) == "Read"
    assert compat.tool_name({"toolName": "search_replace"}) == "Edit"
    # CC 名 passthrough；未知值原樣（非轄面工具不擴集合）
    assert compat.tool_name({"tool_name": "Bash"}) == "Bash"
    assert compat.tool_name({"tool_name": "Glob"}) == "Glob"
    assert compat.tool_name({}) is None


def test_tool_input_target_file_normalized_to_file_path():
    # grok read_file 內鍵 target_file → file_path（file_path 缺席時補）
    grok = {"toolName": "read_file", "toolInput": {"target_file": "/a/SKILL.md"}}
    assert compat.tool_input(grok).get("file_path") == "/a/SKILL.md"
    # CC 形 file_path 原樣；兩鍵並存 file_path 勝
    cc = {"tool_input": {"file_path": "/b.md"}}
    assert compat.tool_input(cc).get("file_path") == "/b.md"
    both = {"toolInput": {"file_path": "/c.md", "target_file": "/d.md"}}
    assert compat.tool_input(both).get("file_path") == "/c.md"
    # 非 dict（malformed）→ None（各 hook 既有 isinstance 分支語義不變）
    assert compat.tool_input({"tool_input": "not-a-dict"}) is None
    assert compat.tool_input({}) is None


def test_session_id_dual_read():
    assert compat.session_id({"session_id": SESSION}) == SESSION
    assert compat.session_id({"sessionId": SESSION}) == SESSION
    assert compat.session_id({"session_id": SESSION, "sessionId": "other"}) == SESSION
    assert compat.session_id({}) is None
    assert compat.session_id({"sessionId": 123}) is None  # 非字串 → None


def test_compat_module_python39_parse_compatible():
    # hooks 部署面 3.9 rollback 相容 gate（同 test_governance_check 形態；
    # compat 檔非 manifest scripts，於本檔釘住）
    source = (HOOKS_DIR / "hook_payload_compat.py").read_text(encoding="utf-8")
    ast.parse(source, feature_version=(3, 9))


# ---------------------------------------------------------------------------
# block-memory-index-write：dual-shape pipe-test（deny exit 2）
# ---------------------------------------------------------------------------


def _make_pool(tmp_path):
    pool = tmp_path / "pool"
    pool.mkdir()
    (pool / "_generate_index.py").write_text("# generator stub\n", encoding="utf-8")
    return pool


def _pipe(script: Path, payload: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )


def test_block_memory_cc_shape_denies_index_write(tmp_path):
    # CC 形（snake 容器鍵＋Write）——既有行為回歸釘住
    pool = _make_pool(tmp_path)
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": str(pool / "MEMORY.md"), "content": "x"},
        }
    )
    result = _pipe(BLOCK_MEMORY, payload)
    assert result.returncode == 2, result.stderr
    assert "[Hook Blocked]" in result.stderr


def test_block_memory_grok_shape_denies_index_write(tmp_path):
    # grok 形（camel 容器鍵＋search_replace）——B2 主測試：外層容器鍵是唯一
    # 致命層（AIR-217 B2a 直證），經 compat 層正規化後同樣觸發 deny
    pool = _make_pool(tmp_path)
    payload = json.dumps(
        {
            "hookEventName": "pre_tool_use",
            "toolName": "search_replace",
            "toolInput": {
                "file_path": str(pool / "MEMORY.md"),
                "old_string": "",
                "new_string": "x",
            },
        }
    )
    result = _pipe(BLOCK_MEMORY, payload)
    assert result.returncode == 2, result.stderr
    assert "[Hook Blocked]" in result.stderr


def test_block_memory_grok_shape_new_entry_with_suffix_denied(tmp_path):
    # grok 形新建條目帶弧狀態後綴 → ④ 狀態後綴擋（tool 分支前的 tool-agnostic 檢查）
    pool = _make_pool(tmp_path)
    payload = json.dumps(
        {
            "hookEventName": "pre_tool_use",
            "toolName": "search_replace",
            "toolInput": {"file_path": str(pool / "arc-landed.md")},
        }
    )
    result = _pipe(BLOCK_MEMORY, payload)
    assert result.returncode == 2, result.stderr
    assert "弧狀態後綴" in result.stderr


def test_block_memory_grok_shape_normal_write_passes(tmp_path):
    # 非 pool 目錄寫入（grok 形）→ exit 0 放行（compat 層不引入誤擋）
    payload = json.dumps(
        {
            "hookEventName": "pre_tool_use",
            "toolName": "search_replace",
            "toolInput": {
                "file_path": str(tmp_path / "outside" / "note.md"),
                "old_string": "",
                "new_string": "x",
            },
        }
    )
    result = _pipe(BLOCK_MEMORY, payload)
    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# kanban-skill-gate：dual-shape 事件分流（PostToolUse Read 落 marker／
# PreToolUse Bash deny）
# ---------------------------------------------------------------------------


def _kban_skill_file(tmp_path):
    skill = tmp_path / "skills" / "kanban-board" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("# kanban skill\n", encoding="utf-8")
    return skill


def _cc_read_payload(skill, cwd):
    return json.dumps(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": str(skill)},
            "cwd": str(cwd),
            "session_id": SESSION,
        }
    )


def _grok_read_payload(skill, cwd):
    return json.dumps(
        {
            "hookEventName": "post_tool_use",
            "toolName": "read_file",
            "toolInput": {"target_file": str(skill)},
            "cwd": str(cwd),
            "sessionId": SESSION,
        }
    )


def _grok_bash_payload(command, cwd):
    return json.dumps(
        {
            "hookEventName": "pre_tool_use",
            "toolName": "run_terminal_command",
            "toolInput": {"command": command},
            "cwd": str(cwd),
            "sessionId": SESSION,
        }
    )


def _marker(cwd):
    return Path(cwd) / ".agent-tmp" / "kanban-skill-gate" / (SESSION + ".read")


def test_kanban_cc_shape_read_writes_marker(tmp_path, capsys):
    _kban_skill_file(tmp_path)
    code = ksg.run(_cc_read_payload(_kban_skill_file(tmp_path), tmp_path))
    capsys.readouterr()
    assert code == 0
    assert _marker(tmp_path).is_file()


def test_kanban_grok_shape_read_writes_marker(tmp_path, capsys):
    # grok camel 形：event 值 post_tool_use→PostToolUse、read_file→Read、
    # target_file→file_path 三層正規化後落 marker
    _kban_skill_file(tmp_path)
    code = ksg.run(_grok_read_payload(_kban_skill_file(tmp_path), tmp_path))
    capsys.readouterr()
    assert code == 0
    assert _marker(tmp_path).is_file()


def test_kanban_grok_shape_read_marker_then_bash_allow_end_to_end(tmp_path, capsys):
    # 兩形混合（grok 讀規範→marker 在場→grok 形動卡指令放行）
    _kban_skill_file(tmp_path)
    assert ksg.run(_grok_read_payload(_kban_skill_file(tmp_path), tmp_path)) == 0
    capsys.readouterr()
    code = ksg.run(_grok_bash_payload('backlog task create "新卡" -l infra', tmp_path))
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out == ""


def test_kanban_grok_shape_bash_denies_without_marker(tmp_path, capsys):
    # marker 缺席＋grok 形動卡指令 → deny exit 2（B2 主測試）
    code = ksg.run(_grok_bash_payload('backlog task edit air-1 --notes "x"', tmp_path))
    captured = capsys.readouterr()
    assert code == 2
    data = json.loads(captured.out)
    assert data["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_kanban_grok_shape_non_card_command_passes(tmp_path, capsys):
    # 非動卡指令（grok 形）→ 放行（分流不誤傷）
    code = ksg.run(_grok_bash_payload("backlog board", tmp_path))
    capsys.readouterr()
    assert code == 0
