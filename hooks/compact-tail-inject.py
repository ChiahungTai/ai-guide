#!/usr/bin/env python3
"""SessionStart(compact) 注入器——compact 後自動補給 raw tail＋STATE.md。

背景（2026-08-23 compact-lab 實驗）：/compact 摘要會壓掉 verbatim 交付物
（指示要求無效）、harness re-injection 快照可能過時。結構性解法＝compact 後
注入「壓縮前最後幾輪原文」。tail 原文由 Claude Code transcript JSONL
（stdin hook input 的 transcript_path）唯讀取得。

平台支援：Claude Code 官方支援 SessionStart + matcher "compact"
（hooks-guide「Re-inject context after compaction」官方食譜；2026-08-30 接線
進 settings.json）。ZCode 端 compact source 不派發 SessionStart
（2026-08-24 L4 實證）——該端維持 compact-prep 手動三動作，本 hook 不註冊。

fail-open：任何錯誤 → 空輸出 exit 0（注入失敗不擋 session）。診斷走 stderr。
stdout 有 32KB 協議上限——預算以 UTF-8 bytes 計（CJK 場景 ensure_ascii=False
下 3 bytes/字元），組完最終 guard。
"""

import json
import sys
from pathlib import Path

CANDIDATE_ENTRIES = 60  # 由最新往回的掃描窗口
TAIL_BUDGET_BYTES = 20000
STATE_BUDGET_BYTES = 4000
OUTPUT_GUARD_BYTES = 30000  # 最終防線（framing＋JSON 結構開銷後仍須 < 32768）
INJECT_MARKER = "<compact-tail-inject>"  # 跳過上代注入，防連續 compact 遞迴膨脹
INJECT_PREFIX = (
    INJECT_MARKER + "\n以下為 /compact 壓縮前的對話尾部原文與專案 STATE，"
    "由 SessionStart hook 注入。tail 是壓縮前尾段的**原文**——與摘要衝突時的"
    "裁決規則：摘要中若含對尾段內容的明確更正或裁決，以更正為準；其餘以 tail "
    "原文為準（優於任何重新注入的舊快照）。STATE.md 為專案 session 觀察層。\n"
)
INJECT_SUFFIX = "</compact-tail-inject>"
TRUNCATION_MARKER = "[truncated]\n"


def _texts_of(message: dict) -> list[str]:
    """CC transcript message.content 的 text 抽取（str 或 block list 兩型）。"""
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [
            b.get("text", "")
            for b in content
            if isinstance(b, dict)
            and b.get("type") == "text"
            and isinstance(b.get("text"), str)
        ]
    return []


def _bounded_suffix(text: str, budget: int) -> str:
    """截掉最舊 bytes；非負預算連 marker 都放不下時回空字串。"""
    if budget < 0:
        raise ValueError("negative tail budget")
    raw = text.encode("utf-8")
    if len(raw) <= budget:
        return text
    remaining = budget - len(TRUNCATION_MARKER.encode("utf-8"))
    if remaining < 0:
        return ""
    suffix = raw[-remaining:].decode("utf-8", errors="ignore") if remaining else ""
    return TRUNCATION_MARKER + suffix


def _fetch_tail_blocks(transcript_path: str) -> list[tuple[str, str]]:
    """由 transcript JSONL 尾段累積 raw text 到 bytes 預算。

    截斷砍最舊、保最新（verbatim 標的在最後）。排除 compact 摘要列、
    sidechain（subagent）列；逐 text block 排除完整 producer envelope，保留一般提及。
    """
    entries: list[tuple[str, str, str]] = []  # (role, hh:mm:ss, text)
    with open(transcript_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(e, dict) or e.get("type") not in ("user", "assistant"):
                continue
            if e.get("isCompactSummary") or e.get("isSidechain"):
                continue
            text = "\n".join(
                t
                for t in _texts_of(e.get("message") or {})
                if t
                and not (
                    t.strip().startswith(INJECT_PREFIX + "\n\n")
                    and t.strip().endswith("\n\n" + INJECT_SUFFIX)
                )
            ).strip()
            if not text:
                continue
            ts = str(e.get("timestamp", ""))
            hhmmss = ts.split("T")[-1][:8] or ts[:8]
            try:
                (hhmmss + text).encode("utf-8")
            except UnicodeEncodeError:
                continue  # 壞 record 不連帶丟棄其餘有效對話
            entries.append((e["type"], hhmmss, text))
    blocks: list[tuple[str, str]] = []
    used = 0
    for role, hhmmss, text in reversed(entries[-CANDIDATE_ENTRIES:]):  # 新 → 舊
        header = f"### [{role}] {hhmmss}\n"
        block = header + text
        b = len(block.encode("utf-8"))
        separator = 2 if blocks else 0
        if used + separator + b > TAIL_BUDGET_BYTES:
            if not blocks:
                blocks.append(
                    (
                        header,
                        _bounded_suffix(
                            text,
                            TAIL_BUDGET_BYTES - len(header.encode("utf-8")),
                        ),
                    )
                )
            break
        blocks.append((header, text))
        used += separator + b
    return list(reversed(blocks))


def fetch_tail(transcript_path: str) -> str:
    """保留既有文字介面；內部另持有 header，wire 截斷不解析使用者文字。"""
    return "\n\n".join(
        header + text for header, text in _fetch_tail_blocks(transcript_path)
    )


def read_state(cwd: str) -> str:
    state = Path(cwd) / "STATE.md" if cwd else None
    if state and state.is_file():
        return (
            state.read_text(encoding="utf-8")
            .encode("utf-8")[:STATE_BUDGET_BYTES]
            .decode("utf-8", errors="ignore")
        )
    return ""


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print("compact-tail-inject: stdin 非 JSON，跳過", file=sys.stderr)
        return
    # 只在 compact 後注入；startup/resume/clear 時完整 context 已在，注入是重複
    if not isinstance(data, dict):
        return
    if data.get("source") != "compact":
        print(
            f"compact-tail-inject: source={data.get('source')} 非 compact，跳過",
            file=sys.stderr,
        )
        return
    session_id = data.get("session_id") or ""
    transcript_path = data.get("transcript_path") or ""
    if not transcript_path:
        # transcript_path 是唯一的原文資料源；缺了無法安全取 tail（不能猜別的
        # session 檔——同 worktree 並行 session 會撈到別人的對話）→ fail-open no-op
        print(
            "compact-tail-inject: stdin 無 transcript_path，跳過（無法安全定位原文）",
            file=sys.stderr,
        )
        return
    try:
        blocks = _fetch_tail_blocks(transcript_path)
        tail = "\n\n".join(header + text for header, text in blocks)
        state = read_state(data.get("cwd", ""))
    except Exception as exc:  # fail-open by design
        print(f"compact-tail-inject: fail-open（{exc}）", file=sys.stderr)
        return
    if not tail and not state:
        print("compact-tail-inject: 無可注入內容", file=sys.stderr)
        return
    parts = [INJECT_PREFIX]

    def render(raw_tail: str) -> str:
        framed = parts.copy()
        if raw_tail:
            framed.append(f"<raw-tail session={session_id}>\n{raw_tail}\n</raw-tail>")
        if state:
            framed.append(f"<state-md>\n{state}\n</state-md>")
        framed.append(INJECT_SUFFIX)
        return json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": data.get("hook_event_name", "SessionStart"),
                    "additionalContext": "\n\n".join(framed),
                }
            },
            ensure_ascii=False,
        )

    out = render(tail)
    while len(blocks) > 1 and len(out.encode("utf-8")) > OUTPUT_GUARD_BYTES:
        blocks.pop(0)
        out = render("\n\n".join(header + text for header, text in blocks))
    if blocks and len(out.encode("utf-8")) > OUTPUT_GUARD_BYTES:
        # 實際序列化尺寸包含 escape、framing、STATE 與 metadata；保最新字元。
        header, text = blocks[-1]
        low, high = 0, len(text)
        while low < high:
            keep = (low + high + 1) // 2
            candidate = render(header + TRUNCATION_MARKER + text[-keep:])
            if len(candidate.encode("utf-8")) <= OUTPUT_GUARD_BYTES:
                low = keep
            else:
                high = keep - 1
        out = render(header + TRUNCATION_MARKER + (text[-low:] if low else ""))
    if len(out.encode("utf-8")) > OUTPUT_GUARD_BYTES:  # 組裝後最終 guard
        print(
            f"compact-tail-inject: 輸出 {len(out.encode('utf-8'))} bytes 超上限，跳過",
            file=sys.stderr,
        )
        return
    sys.stdout.write(out)


if __name__ == "__main__":
    main()
