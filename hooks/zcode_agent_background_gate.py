#!/usr/bin/env python3
"""PreToolUse gate：ZCode Agent 派發一律背景（rewrite 式，零浪費）。

省略或 run_in_background != true 時，回 allow + updatedInput 補
run_in_background: true——同一個 call 內生效，不拒絕、不重派。
逃生口：prompt 前 200 字含 `[fg]`（機械子串）→ 原樣放行。
所有事件旁錄 .agent-tmp/zcode-agent-gate.jsonl（省略形態取證＋行為審計）。
fail-open：任何內部錯誤靜默原樣放行，禁干擾派發。
"""

import json
import os
import sys
from datetime import datetime, timezone

LOG = "/Users/ctai/Github/ai-guide/.agent-tmp/zcode-agent-gate.jsonl"

RB_LABEL = {"<ABSENT>": "absent", True: "true", False: "false"}


def main() -> None:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        event = {"_parse_error": True}
    tool_input = event.get("tool_input")
    rb = (
        tool_input.get("run_in_background", "<ABSENT>")
        if isinstance(tool_input, dict)
        else "<NO_DICT>"
    )
    action = "pass_through"
    output = None
    if (
        event.get("tool_name") in ("Agent", "Task")
        and isinstance(tool_input, dict)
        and rb is not True
        and "[fg]" not in str(tool_input.get("prompt", ""))[:200]
    ):
        new_input = dict(tool_input)
        new_input["run_in_background"] = True
        action = "rewrite_from_" + RB_LABEL.get(rb, str(rb).lower())
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Agent 派發一律背景：已補 run_in_background: true。",
                "updatedInput": new_input,
            }
        }
    if output:
        # rewrite 先輸出——audit 失敗不得連帶丟掉本次 enforcement
        print(json.dumps(output, ensure_ascii=False))
    try:
        record = {
            "_ts": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 — rollback compatibility 仍涵蓋 Python 3.9
            "tool_name": event.get("tool_name"),
            "tool_input_keys": sorted(tool_input.keys())
            if isinstance(tool_input, dict)
            else None,
            "run_in_background": rb,
            "gate_action": action,
            "session_id": event.get("session_id"),
        }
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # audit 只 lose log 本身；rewrite 已輸出不受影響


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open：gate 錯誤不得擋派發，一律 exit 0 原樣放行
    sys.exit(0)
