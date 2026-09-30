#!/usr/bin/env python3
"""
PreToolUse hook: 攔截 python -c 命令含換行 + # 註解。

原因：Claude Code 對「python -c 換行後 #」觸發權限提示（CLI 無法判斷跨行
註解是否被注入惡意內容）。本 hook 在命令發出前攔截，強制 AI 改用單行或
落成 .py 檔，根除權限卡關。

對應 rule: rules/bash-hard-rules.md「python -c 禁止寫註解」。
偵測邏輯見 is_violation()。hook crash（非 0 非 2 exit）為非阻斷，工具仍執行。
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_payload_compat as compat


def is_violation(command: str) -> bool:
    """python -c 命令 + 含換行 + 換行後出現 # 註解。

    保守策略：寧可誤擋（false positive）也不漏（false negative 會觸發權限卡關）。
    單行 python -c 不觸發（換行是必要條件）。
    """
    if not re.search(r"\bpython3?\s+-c\b", command):
        return False
    if "\n" not in command:
        return False
    return bool(re.search(r"\n\s*#", command))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        # hook crash = 非阻斷，工具仍執行。記錄但不卡關。
        print(f"[block-python-c-comment] stdin parse error: {exc}", file=sys.stderr)
        sys.exit(1)

    # 容器鍵雙讀（AIR-218）：run_terminal_command→Bash 映射；CC 形零變。
    if compat.tool_name(data) != "Bash":
        sys.exit(0)

    command = (compat.tool_input(data) or {}).get("command", "")
    if not command or not is_violation(command):
        sys.exit(0)

    # exit 2 + stderr：Claude Code 將 stderr 回饋給 Claude 作為修正指引
    print(
        "[Hook Blocked] python -c 命令含換行 + # 註解。\n"
        "原因：換行後接 # 會觸發 Claude Code 權限提示卡關。\n"
        "修正方式（擇一）：\n"
        "  1. 改用單行 python -c（移除換行與註解）\n"
        "  2. 寫成 .py 檔案，再用 uv run python <file>.py 執行",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
