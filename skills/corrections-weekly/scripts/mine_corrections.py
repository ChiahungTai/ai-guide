#!/usr/bin/env python3
"""糾正候選挖掘（corrections-weekly 的機械面——ZCode db 面）。

撈時間窗內 main sessions 的 user text part 中含糾正關鍵詞者，輸出候選清單
供 LLM 判讀分類（腳本不判斷「是否真糾正」——關鍵詞有假陽性）。

排除：subagent sessions（sess_subagent%）、非 interactive sessions
（side_chat 會複製 parent 的 user 訊息致計數 3x 通膨、fork 同理）、
<task-notification> 注入、compact 摘要、slash-command 開頭訊息、
排程/harness 機器注入（🔴 喚醒頭、【】prompt 頭、TodoWrite 提醒、
compact 續讀摘要頭、Read replay、<subagent-message> 轉投——實測佔
候選 ~1/3，非人類糾正訊號）。

Run: uv run python mine_corrections.py [--days 7] [--max-chars 200]
Exit: 0=正常（含零候選）；1=db 失敗（唯讀、fail-loud）。
"""

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path

DB = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
# (?<!要) 排除疑問句形態「要不要／需不需要」（非糾正，實測佔假陽性 ~17%）
KEYWORDS = re.compile(
    r"不對|錯了|為什麼沒|為什麼不|你又|重複|不需要|(?<!要)不要|不是這樣"
)
# 機器注入訊息的開頭特徵（非人類輸入）——cron/at 喚醒頭、cron prompt 括號頭、
# Read replay、subagent 轉投。TodoWrite 提醒與 compact 續讀摘要頭可能嵌入
# 訊息中段，走 SQL NOT LIKE（見 main）。
MACHINE_HEADS = (
    "🔴",
    "【",
    "Called the Read tool",
    "<subagent-message>",
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-chars", type=int, default=200)
    args = ap.parse_args()

    since = int((time.time() - args.days * 86400) * 1000)
    try:
        db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        print(f"[FAIL] db 開啟失敗：{exc}")
        return 1
    try:
        rows = db.execute(
            "SELECT s.id, p.time_created, p.data FROM part p "
            "JOIN message m ON p.message_id = m.id "
            "JOIN session s ON p.session_id = s.id "
            "WHERE p.time_created >= ? "
            "AND s.id NOT LIKE 'sess\\_subagent%' ESCAPE '\\' "
            "AND s.task_type = 'interactive' "
            "AND json_extract(m.data, '$.role') = 'user' "
            "AND json_extract(p.data, '$.type') = 'text' "
            "AND p.data NOT LIKE '%<task-notification>%' "
            "AND p.data NOT LIKE '%isCompactSummary%' "
            "AND p.data NOT LIKE '%The TodoWrite tool hasn%' "
            "AND p.data NOT LIKE '%This session is being continued%' "
            "ORDER BY p.time_created ASC",
            (since,),
        ).fetchall()
    except sqlite3.Error as exc:
        print(f"[FAIL] 查詢失敗：{exc}")
        return 1
    finally:
        db.close()

    candidates = []
    for sid, ts, raw in rows:
        try:
            text = (json.loads(raw).get("text") or "").strip()
        except json.JSONDecodeError:
            continue  # 非 JSON part（schema 演進容錯），靜默跳過單列不炸整跑
        if not text or text.startswith("/") or text.startswith(MACHINE_HEADS):
            continue
        if KEYWORDS.search(text):
            candidates.append((sid, ts, text))

    print(f"[OK] mine_corrections: {len(candidates)} 候選 / {args.days}d 窗")
    for sid, ts, text in candidates:
        when = time.strftime("%m-%d %H:%M", time.localtime(ts / 1000))
        snippet = text.replace("\n", " ")[: args.max_chars]
        print(f"---\n[{when}] {sid[:16]}\n{snippet}")
    if not candidates:
        print("（零候選——本窗無糾正關鍵詞命中）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
