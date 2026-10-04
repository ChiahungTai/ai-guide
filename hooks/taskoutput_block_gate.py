#!/usr/bin/env python3
r"""taskoutput_block_gate——TaskOutput 阻塞等待紀律閘（AIR-249）。

職責：PreToolUse 攔 `TaskOutput(block=true, timeoutMs>60000)`——marshal
派完背景任務後抱著 turn 長等是重犯失誤（背景任務 exit 即自動發完成通知，
長阻塞從非必要操作）。deny 僅限**長**等待：有界短等待（timeoutMs ≤ 60000，
含缺席＝工具預設 30s）是 ZCode 正式等待語義的正當用途（mid-turn 需要結果
才能下一步／completed 即返），照常放行——blanket deny 已被 codex 討論腿
否證（verdict＝修正後 GO，fuse 反轉為主規則）。本閘是紀律閘不是
correctness 閘——任何異常（壞 JSON／非 dict payload／字串 "true"／
字串 timeoutMs／例外）一律放行（fail-open），禁擋死正當查詢。

判準（routing 兩條＋tool_input 三條，全中才 deny）：event==PreToolUse ∧
tool==TaskOutput（routing）∧ block is True ∧ timeoutMs 為 number（bool 排除）
∧ timeoutMs > 60000（60000 邊界含＝放行）。

deny 輸出＝zcode 官方 PreToolUse 拒絕 schema（同 kanban-skill-gate：
`hookSpecificOutput.hookEventName="PreToolUse"`＋`permissionDecision:"deny"`
＋`permissionDecisionReason`；exit 2）。放行＝空 stdout＋exit 0。stateless
——不落任何檔（marker／日誌皆無），deny 零副作用。

instruction owner＝rules/tool-discipline.md「背景執行」節（既有規則的
enforcement，非新規則）。部署 runtime 由 governance installer 解析
uv-managed Python 3.12（hooks/AGENTS.md）；維持 Python 3.9 語法相容
（無 match、無 X|Y union），改動後跑 3.9 compatibility gate。
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_payload_compat as compat

HOOK_TAG = "taskoutput-block-gate"
TIMEOUT_CEILING_MS = 60000

DENY_REASON = (
    "[Hook Blocked] TaskOutput 長阻塞等待（taskoutput-block-gate）：背景任務"
    "（背景 shell／run_in_background agent）exit 即自動發完成通知——結束 turn"
    " 或做不重疊工作，由通知回收；查狀態用 block=false；有界短等待"
    "（timeoutMs ≤ 60000）是正當用途照常放行，本次因超過上限被擋。"
    "（紀律閘：異常時 fail-open；owner＝rules/tool-discipline.md 背景執行節）"
)


def _is_long_block_wait(tool_input):
    """三條判準：block is True ∧ timeoutMs 是 number ∧ > 60000。"""
    if not isinstance(tool_input, dict):
        return False
    if tool_input.get("block") is not True:
        return False
    timeout_ms = tool_input.get("timeoutMs")
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, (int, float)):
        return False
    return timeout_ms > TIMEOUT_CEILING_MS


def _deny():
    payload = json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": DENY_REASON,
            }
        },
        ensure_ascii=False,
    )
    print(payload)
    print("[" + HOOK_TAG + "] " + DENY_REASON, file=sys.stderr)
    return 2


def run(raw):
    """stdin 原文 → exit code（deny 時 stdout 已印；其餘恆靜默）。永不 raise。"""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        if compat.hook_event_name(payload) != "PreToolUse":
            return 0
        if compat.tool_name(payload) != "TaskOutput":
            return 0
        tool_input = compat.tool_input(payload)
        if tool_input is None:
            return 0
        if _is_long_block_wait(tool_input):
            return _deny()
        return 0
    except Exception as exc:  # fail-open——紀律閘禁擋死正當查詢
        print("[" + HOOK_TAG + "] fail-open（" + repr(exc) + "）", file=sys.stderr)
        return 0


def main():
    return run(sys.stdin.read())


if __name__ == "__main__":
    sys.exit(main())
