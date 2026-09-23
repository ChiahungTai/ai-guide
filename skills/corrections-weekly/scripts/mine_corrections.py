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

Run: uv run python mine_corrections.py [--days 7 | --since <ms-ts> [--until <ms-ts>]] [--max-chars 200]
兩種窗形態互斥：週報（--days N，預設 7）；每弧結算（AIR-135.8）＝--since 弧起點毫秒
epoch（建議＝弧 baseline commit 時間）、--until 缺省＝現在——弧窗只看本弧新增訊號。
Exit: 0=正常（含零候選）；1=db 失敗（唯讀、fail-loud）；2=參數誤用（argparse）。
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
    ap.add_argument("--days", type=int, default=None, help="回看天數（週報形態；預設 7）")
    ap.add_argument(
        "--since",
        type=int,
        default=None,
        help="弧窗起點（毫秒 epoch——如弧 baseline commit ts；與 --days 互斥）",
    )
    ap.add_argument(
        "--until",
        type=int,
        default=None,
        help="弧窗終點（毫秒 epoch；預設＝現在；須與 --since 併用）",
    )
    ap.add_argument("--max-chars", type=int, default=200)
    args = ap.parse_args()

    if args.since is not None:
        if args.days is not None:
            ap.error("--since/--until 與 --days 互斥——弧窗用 --since [--until]，週報用 --days")
        since = args.since
        until = args.until if args.until is not None else int(time.time() * 1000)
        if until < since:
            ap.error(
                f"--until < --since（反向弧窗）——參數誤用禁走零候選空跳通道：since={since} until={until}"
            )
        window = (
            f"{time.strftime('%m-%d %H:%M', time.localtime(since / 1000))}"
            f"~{time.strftime('%m-%d %H:%M', time.localtime(until / 1000))}"
        )
    else:
        if args.until is not None:
            ap.error("--until 須與 --since 併用（弧窗形態）")
        days = args.days if args.days is not None else 7
        since = int((time.time() - days * 86400) * 1000)
        until = int(time.time() * 1000)
        window = f"{days}d"
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
            "WHERE p.time_created >= ? AND p.time_created < ? "
            "AND s.id NOT LIKE 'sess\\_subagent%' ESCAPE '\\' "
            "AND s.task_type = 'interactive' "
            "AND json_extract(m.data, '$.role') = 'user' "
            "AND json_extract(p.data, '$.type') = 'text' "
            "AND p.data NOT LIKE '%<task-notification>%' "
            "AND p.data NOT LIKE '%isCompactSummary%' "
            "AND p.data NOT LIKE '%The TodoWrite tool hasn%' "
            "AND p.data NOT LIKE '%This session is being continued%' "
            "ORDER BY p.time_created ASC",
            (since, until),
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

    print(f"[OK] mine_corrections: {len(candidates)} 候選 / {window} 窗")
    for sid, ts, text in candidates:
        when = time.strftime("%m-%d %H:%M", time.localtime(ts / 1000))
        snippet = text.replace("\n", " ")[: args.max_chars]
        print(f"---\n[{when}] {sid[:16]}\n{snippet}")
    if not candidates:
        print("（零候選——本窗無糾正關鍵詞命中）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
