#!/usr/bin/env python3
"""Pending-decision 台帳——「等 user 決策」項目的單一 queue（AIR-135.6/135.7 機械化）。

決策項散落聊天訊息／STATE.md／卡 notes 會漏（0919 user 指出的結構性缺口）。本腳本
把「需要 user 決定」的項目即時落進單一台帳（DECISIONS-PENDING.md，repo root、
gitignored），三觸發點掃尾（session 開場／compact 前／結案前），結案擋門：
`lint --card <id>` 有 open 且 blocking 的項目即 exit 1——卡標 Done 前必過。

用法：
  uv run python scripts/decisions_pending.py add <卡id或-> "<問題一句>" [選項A/B/...]
  uv run python scripts/decisions_pending.py close <D-id> "<決策一句＋去處>" [--obsolete]
  uv run python scripts/decisions_pending.py promote <D-id> "<開卡卡id>"   # improvement 專用
  uv run python scripts/decisions_pending.py update <D-id> --evidence-ref <指針>  # improvement 重現更新
  uv run python scripts/decisions_pending.py ls [--open] [--stale-days N]
  uv run python scripts/decisions_pending.py lint --card <卡id>   # Done-gate：open blocking 項 exit 1
  uv run python scripts/decisions_pending.py add-improvement <卡id或-> "<一行人話>" \
      --source <訊號源> --evidence-ref <指針> --class <類別> --cost S|M|L   # AIR-151

台帳格式（機器可解析 markdown 表；狀態＝open|decided|obsolete）：
  | D-001 | 2026-09-19 | AIR-135.2 | 問題 | 選項 | open | 備註 | kind | gate | meta |
後三欄 AIR-151 增補；舊 7 欄列照讀（kind 預設 decision、gate 預設 blocking、meta 空）。
- `kind`＝row 類型：`decision`（等 user 決策，預設）｜`improvement`（AIR-151 發現候選）
- `gate`＝lint 語義：`blocking`（open 時擋 lint --card，預設）｜`nonblocking`
  （discovery 不得阻塞 originating arc 的 Settle/Done——improvement kind 必帶此值）
- `meta`＝`key=value;key=value`（improvement 帶 source／evidence_ref／class／cost）

KPI 記數（AIR-151 source-segmented 轉化漏斗，append-only jsonl）：
  reviewed（--add-improvement 落帳）→ opened（promote 開卡）→ settled（promoted row
  的 close——開卡後 Settle 收線的終態）；未 promote 即 close＝dismissed（另一終態，
  與 opened 互斥——不可把 dismissed 記成 settled，否則漏斗語義謊報）。
  只記數不砍源；砍源＝晨間人裁決。路徑錨定同台帳（git common dir 父目錄
  `.agents/improvement-kpi.jsonl`——跨 WT 單一副本）。
  彙總消費端＝`scripts/improvement_signals.py --kpi <path>`。

日期＝本機日曆日（`date.today()`；非 UTC——Asia/Taipei 00:00–08:00 間 UTC 日期
會慢一天，TTL 計齊跟著錯，codex 151-C5）。

測試／隔離重導向：各子命令支援 `--ledger <path>`／`--kpi-file <path>`（預設用上述錨點）。

決策落帳時 close 行尾加決策指針（寫進哪個卡 notes／commit）。
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

# 台帳固定住主 checkout（git common dir 的父目錄）——任何 worktree 跑都寫同一檔，
# 防 per-WT 台帳 split-brain；gitignored（活過 commit 與夜清，但單一副本）
LEDGER = (
    Path(
        subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent,
            check=False,
        ).stdout.strip()
    ).parent
    / "DECISIONS-PENDING.md"
)
# AIR-151 KPI 漏斗記數——與台帳同錨點（跨 WT 單一副本）、append-only jsonl
KPI_FILE = LEDGER.parent / ".agents" / "improvement-kpi.jsonl"

ROW = re.compile(
    r"^\| (D-\d+) \| (\d{4}-\d{2}-\d{2}) \| ([^|]*) \| ([^|]*) \| ([^|]*) \| (\S+)"
    r"(?: \|([^|]*))?"  # 備註（7 欄舊形可缺）
    r"(?: \|([^|]*))?"  # kind（10 欄新形；缺＝decision）
    r"(?: \|([^|]*))?"  # gate（缺＝blocking）
    r"(?: \|([^|]*))?"  # meta
    r"\|?\s*$"
)  # cell 用 * 不用 +——空 cell（如 options／note 空）時 + 會吃掉 padding space 使後續 \| 失配

# improvement 候選的合法訊號源（四類機械掃描器——improvement_signals.py 同源；
# 自由文字會製造 typo 分桶污染 source-segmented KPI，codex 151-C2）
SOURCES = (
    "review_residue",
    "liveness_anomaly",
    "cross_arc_recurrence",
    "budget_overspend",
)


def _today() -> str:
    """本機日曆日（非 UTC——Taipei 00:00–08:00 UTC 日期慢一天，TTL 跟著錯）。"""
    return datetime.date.today().isoformat()


def _load(ledger: Path) -> list[dict]:
    rows: list[dict] = []
    if not ledger.exists():
        return rows
    for line in ledger.read_text(encoding="utf-8").splitlines():
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
                    "kind": (m.group(8) or "").strip() or "decision",
                    "gate": (m.group(9) or "").strip() or "blocking",
                    "meta": (m.group(10) or "").strip(),
                }
            )
    return rows


def _next_id(rows: list[dict]) -> str:
    nums = [int(r["id"][2:]) for r in rows if r["id"].startswith("D-")]
    return f"D-{max(nums, default=0) + 1:03d}"


def _save(rows: list[dict], ledger: Path) -> None:
    lines = [
        "# Pending decisions（等 user 決策的單一台帳——機械維護，勿手散記他處）",
        "",
        "| id | 日期 | 卡 | 問題 | 選項 | 狀態 | 備註 | kind | gate | meta |",
        "|----|------|----|------|------|------|------|------|------|------|",
    ]
    lines += [
        f"| {r['id']} | {r['date']} | {r['card']} | {r['question']} | {r['options']} "
        f"| {r['status']} | {r['note']} | {r['kind']} | {r['gate']} | {r['meta']} |"
        for r in rows
    ]
    lines += [
        "",
        "> 三觸發點掃尾：session 開場／compact 前／結案前（`ls --open`）。"
        "卡標 Done 前 `lint --card <id>` 須 exit 0（open 且 gate=blocking 才擋——"
        "kind=improvement 帶 gate=nonblocking 不擋，AIR-151）。close 行附決策去處指針。",
    ]
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sanitize(text: str) -> str:
    """meta 值清洗——禁 `|`（破表格）與 `;`（破 key=value 分隔）。"""
    return re.sub(r"[|;\n]", " ", text).strip()


def _parse_meta(meta: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in meta.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _append_kpi(kpi_file: Path, event: str, row: dict) -> None:
    """improvement 轉化漏斗記數（reviewed→opened→settled；未 promote 即 close＝
    dismissed——與 opened 互斥的終態）——append-only，壞檔不靜默。"""
    meta = _parse_meta(row.get("meta", ""))
    rec = {
        "ts": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "event": event,
        "id": row["id"],
        "source": meta.get("source") or "-",
        "class": meta.get("class") or "-",
        "cost_bucket": meta.get("cost") or "-",
    }
    kpi_file.parent.mkdir(parents=True, exist_ok=True)
    with kpi_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _add_io_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--ledger", type=Path, default=LEDGER, help=argparse.SUPPRESS)
    p.add_argument("--kpi-file", type=Path, default=KPI_FILE, help=argparse.SUPPRESS)


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
    p_close.add_argument(
        "--obsolete",
        action="store_true",
        help="以 obsolete 終態關閉（dismiss／defer／TTL 過期——非 decided）",
    )
    p_promote = sub.add_parser("promote", help="improvement row 晉級開卡（KPI opened）")
    p_promote.add_argument("did")
    p_promote.add_argument("card_ref", help="晉級後的開卡卡 id")
    p_ls = sub.add_parser("ls")
    p_ls.add_argument("--open", action="store_true")
    p_ls.add_argument(
        "--stale-days",
        type=int,
        default=None,
        help="TTL 面：只列 date 早於 N 天前的 open improvement（晨間裁決清單；未給＝不過濾）",
    )
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--card", required=True)
    p_imp = sub.add_parser(
        "add-improvement",
        help="AIR-151 improvement 候選落帳（kind=improvement gate=nonblocking，KPI reviewed）",
    )
    p_imp.add_argument("card", help="owning 卡 id，無卡填 -")
    p_imp.add_argument("question", help="一行人話候選描述")
    p_imp.add_argument(
        "--source",
        required=True,
        choices=list(SOURCES),
        help="訊號源（四類機械掃描器——enum 禁自由文字污染 KPI 分桶）",
    )
    p_imp.add_argument("--evidence-ref", required=True, help="證據指針（檔案／job id／行號）")
    p_imp.add_argument("--class", dest="klass", required=True, help="候選類別（如 friction/reliability/efficiency）")
    p_imp.add_argument("--cost", required=True, choices=["S", "M", "L"], help="預估成本")
    p_update = sub.add_parser(
        "update",
        help="improvement row 重現更新（換 evidence 指針＋recurrence+1——不建新 row）",
    )
    p_update.add_argument("did")
    p_update.add_argument("--evidence-ref", required=True, help="最新證據指針")
    p_update.add_argument("--note", default="", help="附加備註（併入 note 尾）")
    for p in (p_add, p_close, p_promote, p_ls, p_lint, p_imp, p_update):
        _add_io_args(p)
    argv = sys.argv[1:]
    if argv and argv[0] == "--add-improvement":  # 文檔拼法——argparse 對 - 開頭子命令首位會誤判成 optional
        argv[0] = "add-improvement"
    args = ap.parse_args(argv)

    rows = _load(args.ledger)
    if args.cmd == "add":
        row = {
            "id": _next_id(rows),
            "date": _today(),
            "card": args.card,
            "question": args.question,
            "options": args.options,
            "status": "open",
            "note": "",
            "kind": "decision",
            "gate": "blocking",
            "meta": "",
        }
        rows.append(row)
        _save(rows, args.ledger)
        print(f"[OK] {row['id']} 已登記（{row['card']}）——結案/compact 前會再掃到")
    elif args.cmd == "add-improvement":
        meta_parts = [
            f"source={_sanitize(args.source)}",
            f"evidence_ref={_sanitize(args.evidence_ref)}",
            f"class={_sanitize(args.klass)}",
            f"cost={args.cost}",
            "recurrence=1",
            f"lastSeen={_today()}",
        ]
        row = {
            "id": _next_id(rows),
            "date": _today(),
            "card": args.card,
            "question": args.question,
            "options": "",
            "status": "open",
            "note": "",
            "kind": "improvement",
            "gate": "nonblocking",  # 卡規格：improvement kind 必帶 nonblocking——hardcode 不給旗標
            "meta": ";".join(meta_parts),
        }
        rows.append(row)
        _save(rows, args.ledger)
        _append_kpi(args.kpi_file, "reviewed", row)
        print(f"[OK] {row['id']} improvement 候選已登記（nonblocking——不擋 {row['card']} Settle/Done）")
    elif args.cmd == "update":
        for r in rows:
            if r["id"] == args.did and r["kind"] == "improvement" and r["status"] == "open":
                meta = _parse_meta(r["meta"])
                meta["evidence_ref"] = _sanitize(args.evidence_ref)
                meta["recurrence"] = str(int(meta.get("recurrence", "1") or "1") + 1)
                meta["lastSeen"] = _today()
                r["meta"] = ";".join(f"{k}={v}" for k, v in meta.items())
                if args.note:
                    r["note"] = (r["note"] + "；" + _sanitize(args.note)).strip("；")
                _save(rows, args.ledger)
                print(f"[OK] {args.did} updated（recurrence={meta['recurrence']}，evidence 已換新）")
                return
        print(f"[FAIL] {args.did} 不存在、非 open improvement row")
        sys.exit(1)
    elif args.cmd == "close":
        for r in rows:
            # promoted improvement（decided＋promoted 註記）可達 settled 終態——
            # reviewed→opened→settled 漏斗的末段（codex 151-C3）
            promoted = (
                r["kind"] == "improvement"
                and r["status"] == "decided"
                and r["note"].startswith("promoted")
            )
            if r["id"] == args.did and promoted:
                r["status"] = "obsolete"
                r["note"] = f"settled：{args.resolution}"
                _save(rows, args.ledger)
                _append_kpi(args.kpi_file, "settled", r)
                print(f"[OK] {args.did} settled：{args.resolution}")
                return
            if r["id"] == args.did and r["status"] == "open":
                r["status"] = "obsolete" if args.obsolete else "decided"
                r["note"] = args.resolution
                _save(rows, args.ledger)
                if r["kind"] == "improvement":
                    # 未 promote 即收＝另一終態——不可記 settled（漏斗語義，codex 151-C3）
                    _append_kpi(args.kpi_file, "dismissed", r)
                print(f"[OK] {args.did} closed（{r['status']}）：{args.resolution}")
                return
        print(f"[FAIL] {args.did} 不存在或已關閉")
        sys.exit(1)
    elif args.cmd == "promote":
        for r in rows:
            if r["id"] == args.did and r["status"] == "open":
                if r["kind"] != "improvement":
                    print(f"[FAIL] {args.did} 非 improvement row——promote 僅適用 discovery 候選")
                    sys.exit(1)
                r["status"] = "decided"
                r["note"] = f"promoted → {args.card_ref}（凍結單向，更新只在卡上）"
                _save(rows, args.ledger)
                _append_kpi(args.kpi_file, "opened", r)
                print(f"[OK] {args.did} promoted → {args.card_ref}（KPI opened 已記）")
                return
        print(f"[FAIL] {args.did} 不存在或已關閉")
        sys.exit(1)
    elif args.cmd == "ls":
        meta_of = {r["id"]: _parse_meta(r["meta"]) for r in rows}
        stale_cutoff = ""
        if getattr(args, "stale_days", None):
            stale_cutoff = (
                datetime.date.today() - datetime.timedelta(days=args.stale_days)
            ).isoformat()
        for r in rows:
            if args.open and r["status"] != "open":
                continue
            kind_tag = f"/{r['kind']}" if r["kind"] != "decision" else ""
            meta = meta_of.get(r["id"], {})
            extra = ""
            if r["kind"] == "improvement":
                extra = (
                    f" [{r['date']} src={meta.get('source', '-')} ev={meta.get('evidence_ref', '-')}"
                    f" cls={meta.get('class', '-')} cost={meta.get('cost', '-')}"
                    f" rec={meta.get('recurrence', '-')}]"
                )
                # TTL 面：--stale-days 給定時只列超齡 open improvement（晨間裁決清單）
                if stale_cutoff and r["date"] > stale_cutoff:
                    continue
            elif stale_cutoff:
                continue
            print(f"{r['id']} [{r['status']}{kind_tag}] {r['date']} {r['card']}：{r['question']}{extra}")
    elif args.cmd == "lint":
        open_for = [
            r
            for r in rows
            if r["status"] == "open"
            and r["gate"] != "nonblocking"  # improvement 收斂不阻塞 originating arc（AIR-151）
            and args.card in (r["card"], "-")
        ]
        if open_for:
            for r in open_for:
                print(f"[FAIL] open decision {r['id']}：{r['question']}（擋 {args.card} Done）")
            sys.exit(1)
        print(f"[OK] {args.card} 無 open pending decisions")


if __name__ == "__main__":
    main()
