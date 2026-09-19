#!/usr/bin/env python3
"""Pending-decision 台帳——「等 user 決策」項目的單一 queue（AIR-135.6/135.7 機械化）。

決策項散落聊天訊息／STATE.md／卡 notes 會漏（0919 user 指出的結構性缺口）。本腳本
把「需要 user 決定」的項目即時落進單一台帳（DECISIONS-PENDING.md，repo root、
gitignored），三觸發點掃尾（session 開場／compact 前／結案前），結案擋門：
`lint --card <id>` 有 open 項即 exit 1——卡標 Done 前必過。

用法：
  uv run python scripts/decisions_pending.py add <卡id或-> "<問題一句>" [選項A/B/...]
  uv run python scripts/decisions_pending.py close <D-id> "<決策一句＋去處>"
  uv run python scripts/decisions_pending.py ls [--open]
  uv run python scripts/decisions_pending.py lint --card <卡id>   # Done-gate：open 項 exit 1

台帳格式（機器可解析 markdown 表；狀態＝open|decided|obsolete）：
  | D-001 | 2026-09-19 | AIR-135.2 | 問題 | 選項 | open |
決策落帳時 close 行尾加決策指針（寫進哪個卡 notes／commit）。
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "DECISIONS-PENDING.md"
ROW = re.compile(
    r"^\| (D-\d+) \| (\d{4}-\d{2}-\d{2}) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| (\S+)(?: \|([^|]*))?\|?\s*$"
)


def _load() -> list[dict]:
    rows: list[dict] = []
    if not LEDGER.exists():
        return rows
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            rows.append(
                {
                    "id": m.group(1),
                    "date": m.group(2),
                    "card": m.group(3).strip(),
                    "question": m.group(4).strip(),
                    "options": m.group(5).strip(),
                    "status": m.group(6).strip(),
                    "note": (m.group(7) or "").strip(),
                }
            )
    return rows


def _next_id(rows: list[dict]) -> str:
    nums = [int(r["id"][2:]) for r in rows if r["id"].startswith("D-")]
    return f"D-{max(nums, default=0) + 1:03d}"


def _save(rows: list[dict]) -> None:
    lines = [
        "# Pending decisions（等 user 決策的單一台帳——機械維護，勿手散記他處）",
        "",
        "| id | 日期 | 卡 | 問題 | 選項 | 狀態 | 備註 |",
        "|----|------|----|------|------|------|------|",
    ]
    lines += [
        f"| {r['id']} | {r['date']} | {r['card']} | {r['question']} | {r['options']} "
        f"| {r['status']} | {r['note']} |"
        for r in rows
    ]
    lines += [
        "",
        "> 三觸發點掃尾：session 開場／compact 前／結案前（`ls --open`）。"
        "卡標 Done 前 `lint --card <id>` 須 exit 0。close 行附決策去處指針。",
    ]
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_add = sub.add_parser("add")
    p_add.add_argument("card", help=" owning 卡 id，無卡填 -")
    p_add.add_argument("question")
    p_add.add_argument("options", nargs="?", default="")
    p_close = sub.add_parser("close")
    p_close.add_argument("did")
    p_close.add_argument("resolution")
    p_ls = sub.add_parser("ls")
    p_ls.add_argument("--open", action="store_true")
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--card", required=True)
    args = ap.parse_args()

    rows = _load()
    if args.cmd == "add":
        row = {
            "id": _next_id(rows),
            "date": datetime.date.today().isoformat(),
            "card": args.card,
            "question": args.question,
            "options": args.options,
            "status": "open",
            "note": "",
        }
        rows.append(row)
        _save(rows)
        print(f"[OK] {row['id']} 已登記（{row['card']}）——結案/compact 前會再掃到")
    elif args.cmd == "close":
        for r in rows:
            if r["id"] == args.did and r["status"] == "open":
                r["status"] = "decided"
                r["note"] = args.resolution
                _save(rows)
                print(f"[OK] {args.did} closed：{args.resolution}")
                return
        print(f"[FAIL] {args.did} 不存在或已關閉")
        sys.exit(1)
    elif args.cmd == "ls":
        for r in rows:
            if args.open and r["status"] != "open":
                continue
            print(f"{r['id']} [{r['status']}] {r['card']}：{r['question']}")
    elif args.cmd == "lint":
        open_for = [
            r
            for r in rows
            if r["status"] == "open" and args.card in (r["card"], "-")
        ]
        if open_for:
            for r in open_for:
                print(f"[FAIL] open decision {r['id']}：{r['question']}（擋 {args.card} Done）")
            sys.exit(1)
        print(f"[OK] {args.card} 無 open pending decisions")


if __name__ == "__main__":
    main()
