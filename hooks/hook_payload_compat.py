#!/usr/bin/env python3
"""Hook stdin payload 相容層（AIR-218 B2）——跨 harness 鍵值正規化薄層。

職責邊界：本檔**只做鍵值正規化**（容器鍵雙讀＋event 值＋tool 名＋
read_file 內鍵），policy 判斷一律留各 hook；禁塞任何領域邏輯
（memory 領域 helper＝memory_hook_common.py，兩檔互不隸屬）。

雙讀語義（snake 優先、camel fallback）：
- CC（hooks.md:761 common field 表）與 ZCode（contracts.md:25 stdin 含
  Claude snake_case alias）恆送 snake_case → 第一項命中，第二項是死碼
  → CC/ZCode 行為零變。
- grok 送 camelCase 容器鍵（toolName/toolInput/sessionId/hookEventName；
  binary-bundled docs `10-hooks.md` L283/L473——線上鏡像 `features/hooks.md:44`）
  → fallback 命中。

值層差異（鍵名之外的第二層）：
- event 值：grok `hookEventName` 帶 snake_case 值（"pre_tool_use"）→
  正規化為 CC PascalCase（"PreToolUse"）；CC 原值原樣通過。
- tool 值：grok payload `toolName` 帶 real name（alias 只作用於 matcher 面）
  ——run_terminal_command→Bash、read_file→Read、search_replace→Edit
  （Edit|Write|MultiEdit 三合一，下游分支語義由各 hook 自持）；
  CC 名原樣通過。
- read_file 內鍵：grok 用 `target_file` 非 `file_path`（AIR-217 B2a
  NDJSON 行為直證）→ file_path 缺席時補鍵（shallow copy，不改原 dict）。

部署 runtime＝governance-resolved Python 3.12；mixed-session／rollback
窗期保留 Python 3.9 語法相容（無 match、無 X|Y union）。
"""

# grok real tool name → CC 工具名（消費面＝各 hook 的 tool 比較點；
# 僅列 hook 實際消費的映射，禁無消費者擴充）
GROK_TOOL_TO_CC = {
    "run_terminal_command": "Bash",
    "read_file": "Read",
    "search_replace": "Edit",
}

# grok snake_case event 值 → CC PascalCase（我方註冊事件全集＋被動事件）
GROK_EVENT_TO_CC = {
    "session_start": "SessionStart",
    "session_end": "SessionEnd",
    "user_prompt_submit": "UserPromptSubmit",
    "pre_tool_use": "PreToolUse",
    "post_tool_use": "PostToolUse",
    "post_tool_use_failure": "PostToolUseFailure",
    "permission_denied": "PermissionDenied",
    "stop": "Stop",
    "stop_failure": "StopFailure",
    "stop_cancelled": "StopCancelled",
    "notification": "Notification",
    "subagent_start": "SubagentStart",
    "subagent_stop": "SubagentStop",
    "pre_compact": "PreCompact",
    "post_compact": "PostCompact",
}


def field(payload, snake, camel):
    """通用容器鍵雙讀：snake 優先（CC/ZCode 恆送）、camel fallback（grok）。"""
    value = payload.get(snake)
    if value is None:
        value = payload.get(camel)
    return value


def hook_event_name(payload):
    """事件名正規化為 CC PascalCase 值；非字串 → None。"""
    value = field(payload, "hook_event_name", "hookEventName")
    if not isinstance(value, str):
        return None
    return GROK_EVENT_TO_CC.get(value, value)


def tool_name(payload):
    """tool 名正規化為 CC 名（grok real name 經映射）；非字串 → None。"""
    value = field(payload, "tool_name", "toolName")
    if not isinstance(value, str):
        return None
    return GROK_TOOL_TO_CC.get(value, value)


def tool_input(payload):
    """tool_input 容器雙讀＋read_file 內鍵 target_file→file_path。

    非 dict／缺席 → None（各 hook 既有 isinstance 分支語義不變）——
    非 dict 刻意 fail-open（與既有 absent→放行語義對齊；malformed
    對照測試歸 L1b）；補鍵走 shallow copy，永不改動 caller 的原 dict。
    """
    value = field(payload, "tool_input", "toolInput")
    if not isinstance(value, dict):
        return None
    if "file_path" not in value and "target_file" in value:
        value = dict(value)
        value["file_path"] = value["target_file"]
    return value


def session_id(payload):
    """session_id/sessionId 雙讀；非字串 → None。"""
    value = field(payload, "session_id", "sessionId")
    return value if isinstance(value, str) else None
