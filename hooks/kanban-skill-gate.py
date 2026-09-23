#!/usr/bin/env python3
r"""kanban-skill-gate——動卡前紀律閘（AIR-170 交付一；單一腳本雙事件）。

職責：本 session 尚未讀寫卡規範（skills/kanban-board/SKILL.md）就想跑
`backlog task create/edit`（建卡/改卡）時擋下執行，指引先讀規範；讀過
（session marker 在場）即放行。本閘是紀律閘不是 correctness 閘——marker
查詢任何異常一律放行（fail-open），禁擋死建卡。

事件分流（stdin JSON 的 hook_event_name；ZCode/CC hook 協議共用 payload）：
- PostToolUse（matcher `Read`）：tool_input.file_path 以 cwd 定基 resolve
  （~/.agents/skills 母鏈 symlink 讀取同樣命中）後路徑尾段 ==
  skills/kanban-board/SKILL.md → 落 marker
  `<cwd>/.agent-tmp/kanban-skill-gate/<sanitize(session_id)>.read`
  （寫失敗只 stderr 診斷——不影響 Read 已完成的事實）。
- PreToolUse（matcher `Bash`）：tool_input.command 命中
  `\bbacklog\s+task\s+(?:create|edit)\b`（list/board/draft promote 等不算）
  → 查 marker：missing → deny；present／anomaly → 放行。

deny 輸出＝zcode 官方 PreToolUse 拒絕 schema（ref-docs/harness/zcode/cn/
docs/hooks.md「PreToolUse：修改或拒绝工具调用」节：`hookSpecificOutput.
hookEventName="PreToolUse"`＋`permissionDecision:"deny"`＋
`permissionDecisionReason`；退出碼 2＝阻斷快捷方式）——exit 2＋stdout
上述 JSON＋stderr 同步指引一句「先讀 skills/kanban-board/SKILL.md 再動卡」。
放行＝空 stdout＋exit 0（「stdout 为空表示成功且无附加效果」）。跨 harness
deny 慣例同 marshal_admission_guard（ZCode exit 2 已證、CC exit 2 阻斷）。

fail-open 面：stdin 壞 JSON／payload 非 dict／session_id 缺席（marker 無從
歸屬）／tool_input 非 dict／任何例外 → 放行＋stderr 診斷。

hook 執行面 python3＝CommandLineTools 3.9（hooks/AGENTS.md）——禁 3.10+
語法（無 match、無 X|Y union）；改動後必以 bare python3 實跑複驗，不可只信
測試綠。
"""

import json
import re
import sys
import time
from pathlib import Path

HOOK_TAG = "kanban-skill-gate"
KANBAN_SKILL_TAIL = ("skills", "kanban-board", "SKILL.md")
MARKER_DIR = (".agent-tmp", "kanban-skill-gate")
SESSION_ID_MAX = 80
SANITIZE_RE = re.compile(r"[^A-Za-z0-9._-]+")
TASK_CMD_RE = re.compile(r"\bbacklog\s+task\s+(?:create|edit)\b")

DENY_REASON = (
    "[Hook Blocked] 動卡前未讀寫卡規範（kanban-skill-gate）：本 session 尚未讀 "
    "skills/kanban-board/SKILL.md——先讀 skills/kanban-board/SKILL.md 再動卡"
    "（讀後本閘即放行；本閘為紀律閘，marker 查詢異常時 fail-open）。"
)


def _sanitize_session_id(session_id):
    """session_id → 安全檔名片段；非字串／空白／退化（`.`、`..`）回 None（＝anomaly）。

    缺鍵（payload.get→None）必須在此攔——str(None)="None" 會被當合法 id，
    使 marker 查詢誤判 missing 而 deny（bare python3 實跑抓到的回歸）。
    """
    if not isinstance(session_id, str) or not session_id.strip():
        return None
    sid = SANITIZE_RE.sub("_", session_id)[:SESSION_ID_MAX]
    if not sid or sid in (".", ".."):
        return None
    return sid


def _marker_path(cwd, session_id):
    sid = _sanitize_session_id(session_id)
    if sid is None:
        return None
    return Path(cwd).joinpath(*MARKER_DIR) / (sid + ".read")


def _marker_state(cwd, session_id):
    """marker 狀態：present／missing／anomaly（anomaly 由呼叫端 fail-open）。"""
    marker = _marker_path(cwd, session_id)
    if marker is None:
        return "anomaly"
    try:
        return "present" if marker.is_file() else "missing"
    except OSError:
        return "anomaly"


def _mark_session_read(cwd, session_id):
    """PostToolUse(Read) 命中目標 → 落 marker；任何失敗只診斷不擋。"""
    marker = _marker_path(cwd, session_id)
    if marker is None:
        print(
            "[" + HOOK_TAG + "] session_id 缺席——marker 無從歸屬，略過落檔",
            file=sys.stderr,
        )
        return
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%S\n"), encoding="utf-8")
    except OSError as exc:
        print(
            "[" + HOOK_TAG + "] marker 寫入失敗（" + repr(exc) + "）", file=sys.stderr
        )


def _is_kanban_skill_read(file_path, cwd):
    """resolve（cwd 定基＋追 symlink）後尾段 == skills/kanban-board/SKILL.md。"""
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = Path(cwd) / p
        p = p.resolve()
    except (OSError, RuntimeError):
        return False
    return len(p.parts) >= 3 and p.parts[-3:] == KANBAN_SKILL_TAIL


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
    """stdin 原文 → exit code（stdout 於 deny 時已印；其餘恆靜默）。永不 raise。"""
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        event = payload.get("hook_event_name")
        tool = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return 0
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0
        if event == "PostToolUse" and tool == "Read":
            file_path = tool_input.get("file_path")
            if (
                isinstance(file_path, str)
                and file_path
                and _is_kanban_skill_read(file_path, cwd)
            ):
                _mark_session_read(cwd, payload.get("session_id"))
            return 0
        if event == "PreToolUse" and tool == "Bash":
            command = tool_input.get("command")
            if (
                isinstance(command, str)
                and TASK_CMD_RE.search(command)
                and _marker_state(cwd, payload.get("session_id")) == "missing"
            ):
                return _deny()
        return 0
    except Exception as exc:  # fail-open——紀律閘禁擋死建卡
        print("[" + HOOK_TAG + "] fail-open（" + repr(exc) + "）", file=sys.stderr)
        return 0


def main():
    return run(sys.stdin.read())


if __name__ == "__main__":
    sys.exit(main())
