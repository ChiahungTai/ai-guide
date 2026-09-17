#!/usr/bin/env python3
"""審查帳本 lint＋parse——`.review/<branch>.md` 機械驗收閘（AIR-121）。

雙子命令：
- ``lint <ledger.md>``：canonical 格式驗證（寫入時 gate）——identity 三行
  （reviewed revision／scope／review_profile）＋Finding Record 表 canonical 欄位
  （ID／嚴重度／位置／問題／建議／驗證式／狀態／決策）＋值域
  （decision ∈ ✅❌⚠️；terminal status ∈ resolved|verified|closed）。
- ``parse <ledger.md>``：容錯讀＋tally（歷史帳本回歸／消費面）——跨表 ID-join
  last-wins（發現時態表被 apply 終態表覆蓋）、prose 計數禁用（否定句陷阱：
  「零 ❌、零 ⚠️」不得入計數）、解析不出→明確 ``[FAIL]`` 類別拒收（unknown，
  禁猜 resolved）。

exit 契約：``0`` 成功／``1`` 解析失敗（fail-closed）／``2`` 帳本不存在／
``3`` identity stale。

嚴格度分工：lint 是 canonical gate（identity 須字面 ``reviewed revision``）；
parse 是容錯讀者（任何 ``reviewed`` 行即可錨定）。歷史漂移語義：狀態自由文字
（如 implemented）不計 terminal、欄位缺席＝unknown——誤差方向安全：只省略
不捏造，unknown 一律計入「未決」。
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_MISSING = 2
EXIT_STALE = 3

DECISION_EMOJI: tuple[str, ...] = ("✅", "❌", "⚠️")
TERMINAL_STATUSES: tuple[str, ...] = ("resolved", "verified", "closed")
PENDING_STATUSES: tuple[str, ...] = ("open", "needs-confirmation")

REVIEWED_REVISION_RE = re.compile(r"reviewed\s*revision", re.IGNORECASE)
PROFILE_KEYWORDS: tuple[str, ...] = (
    "review_profile",
    "review profile",
    "審查 profile",
    "review 形態",
    "審查形態",
)

# canonical 欄位 → header 關鍵詞（header 小寫後 contains；ID 走精確比對）
CANONICAL_COLUMNS: tuple[tuple[str, tuple[str, ...] | None], ...] = (
    ("ID", None),
    ("嚴重度", ("嚴重度", "severity")),
    ("位置", ("位置", "location")),
    ("問題", ("問題", "finding", "發現")),
    ("建議", ("建議", "remedy", "suggestion")),
    ("驗證式", ("驗證", "verif")),
    ("狀態", ("狀態", "status")),
    ("決策", ("決策", "decision", "裁決", "judge")),
)

DECISION_COL_KEYWORDS: tuple[str, ...] = ("決策", "decision", "裁決", "judge")
STATUS_COL_KEYWORDS: tuple[str, ...] = ("狀態", "status")

_KEEP = object()  # join 時「本表無此欄」哨兵——後表缺欄不覆蓋前表值


@dataclass
class FindingRow:
    fid: str
    decision: str | None
    raw_status: str | None


# ---------- 表格解析 ----------


def split_row(line: str) -> list[str]:
    """切 cell；容錯 inline escaped pipe（``\\|``——rg pattern 常見於驗證式欄）。"""
    esc = "\x00"
    cells = line.strip().strip("|").replace("\\|", esc).split("|")
    return [c.strip().replace(esc, "|") for c in cells]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


def split_tables(lines: list[str]) -> list[list[list[str]]]:
    """連續 pipe 行＝一個表 block；回傳逐表 raw rows（含 header 與 separator）。"""
    tables: list[list[list[str]]] = []
    buf: list[str] = []
    for line in lines:
        if line.lstrip().startswith("|"):
            buf.append(line)
        elif buf:
            tables.append([split_row(x) for x in buf])
            buf = []
    if buf:
        tables.append([split_row(x) for x in buf])
    return tables


def normalize_table(raw_rows: list[list[str]]) -> list[list[str]]:
    if not raw_rows:
        return []
    header = raw_rows[0]
    data = [r for r in raw_rows[1:] if not is_separator_row(r)]
    return [header, *data]


def identity_region(lines: list[str]) -> list[str]:
    """identity 檢查範圍＝第一個表之前的行（header 區塊）。"""
    region: list[str] = []
    for line in lines:
        if line.lstrip().startswith("|"):
            break
        region.append(line)
    return region


# ---------- identity 檢查 ----------


def has_reviewed_revision(region: list[str], *, strict: bool) -> bool:
    for line in region:
        if strict:
            if REVIEWED_REVISION_RE.search(line):
                return True
        elif "reviewed" in line.lower():
            return True
    return False


def has_scope(region: list[str]) -> bool:
    return any("scope" in line.lower() or "範圍" in line for line in region)


def has_review_profile(region: list[str]) -> bool:
    lowered = [line.lower() for line in region]
    return any(any(k in line for k in PROFILE_KEYWORDS) for line in lowered)


# ---------- 欄位定位 ----------


def id_col_index(headers: list[str]) -> int | None:
    """ID 欄：header 精確等於 ``id``（大小寫不敏）或 ``#``——精確比對避免
    ``confidence`` 這類含 ``id`` 子字串的誤命中。"""
    for i, h in enumerate(headers):
        hl = h.strip().lower()
        if hl in ("id", "#"):
            return i
    return None


def col_index(headers: list[str], keywords: tuple[str, ...]) -> int | None:
    for i, h in enumerate(headers):
        hl = h.lower()
        if any(k in hl for k in keywords):
            return i
    return None


def find_canonical_col(headers: list[str], col: str) -> int | None:
    for name, keywords in CANONICAL_COLUMNS:
        if name == col:
            if keywords is None:
                return id_col_index(headers)
            return col_index(headers, keywords)
    return None


# ---------- 值域 ----------


def cell_decision(cell: str) -> str | None:
    for d in DECISION_EMOJI:
        if d in cell:
            return d
    return None


def status_bucket(raw: str | None) -> str:
    """狀態分桶：terminal 三值／open（含 needs-confirmation）／absent／自由文字。"""
    if raw is None or not raw.strip():
        return "absent"
    value = raw.strip().lower()
    for t in TERMINAL_STATUSES:
        if value.startswith(t):
            return t
    for p in PENDING_STATUSES:
        if value.startswith(p):
            return "open"
    return "unknown:" + value[:24]


# ---------- 核心解析（容錯讀） ----------


def parse_ledger(text: str) -> dict | None:
    """回 None＝找不到含 ID 欄的 findings 表（fail-closed 拒收）。"""
    lines = text.splitlines()
    raw_tables = split_tables(lines)
    tables = [t for t in (normalize_table(r) for r in raw_tables) if len(t) > 1]

    keyed: list[tuple[int, list[list[str]]]] = []
    for rows in tables:
        id_i = id_col_index(rows[0])
        if id_i is not None:
            keyed.append((id_i, rows))

    joined: dict[str, FindingRow] = {}
    decision_source = "none"
    unparsed = 0
    total_rows = 0

    for id_i, rows in keyed:
        headers = rows[0]
        dec_i = col_index(headers, DECISION_COL_KEYWORDS)
        st_i = col_index(headers, STATUS_COL_KEYWORDS)
        if dec_i is not None and decision_source == "none":
            decision_source = headers[dec_i].strip() or "none"
        for row in rows[1:]:
            total_rows += 1
            needed = max(x for x in (id_i, dec_i, st_i) if x is not None)
            if len(row) <= needed:
                unparsed += 1
                continue
            fid = row[id_i].strip() or f"(row{total_rows})"
            new_dec = cell_decision(row[dec_i]) if dec_i is not None else _KEEP
            new_status = row[st_i] if st_i is not None else _KEEP
            existing = joined.get(fid)
            if existing is None:
                joined[fid] = FindingRow(
                    fid=fid,
                    decision=None if new_dec is _KEEP else new_dec,
                    raw_status=None if new_status is _KEEP else new_status,
                )
            else:
                # ID-join last-wins：後表有該欄即覆蓋（發現時態 → apply 終態）
                if new_dec is not _KEEP:
                    existing.decision = new_dec
                if new_status is not _KEEP:
                    existing.raw_status = new_status

    if not keyed:
        return None

    decisions = {d: 0 for d in DECISION_EMOJI}
    decisions["unknown"] = 0
    status_counts = {"resolved": 0, "verified": 0, "closed": 0, "open": 0}
    unknown_total = 0
    for f in joined.values():
        decisions[f.decision if f.decision is not None else "unknown"] += 1
        bucket = status_bucket(f.raw_status)
        if bucket in status_counts:
            status_counts[bucket] += 1
        else:
            unknown_total += (
                1  # unknown:<自由文字> 與 absent 同歸 unknown（fail-closed）
            )

    pending = status_counts["open"] + unknown_total
    return {
        "findings": len(joined),
        "tables": len(tables),
        "dec": decisions,
        "decision_source": decision_source,
        "st": status_counts,
        "unknown_status": unknown_total,
        "未決": pending,
        "unparsed": unparsed,
    }


# ---------- 子命令 ----------


def cmd_lint(text: str, name: str) -> int:
    region = identity_region(text.splitlines())
    if not has_reviewed_revision(region, strict=True):
        print(
            f"[{name}] [FAIL] identity.stale: 無 reviewed revision 行（identity 無法錨定）"
        )
        return EXIT_STALE

    violations: list[str] = []
    if not has_scope(region):
        violations.append("identity.missing_scope: 無 scope 行")
    if not has_review_profile(region):
        violations.append("identity.missing_review_profile: 無 review_profile 行")

    tables = [
        t
        for t in (normalize_table(r) for r in split_tables(text.splitlines()))
        if len(t) > 1
    ]
    finding_table: list[list[str]] | None = None
    id_i: int | None = None
    for rows in tables:
        idx = id_col_index(rows[0])
        if idx is not None:
            finding_table = rows
            id_i = idx
            break
    if finding_table is None or id_i is None:
        violations.append("table.missing: 無 Finding Record 表（找不到含 ID 欄的表格）")
        for v in violations:
            print(f"[{name}] [FAIL] {v}")
        return EXIT_FAIL

    headers = finding_table[0]
    missing_cols = [
        c for c, _ in CANONICAL_COLUMNS if find_canonical_col(headers, c) is None
    ]
    if missing_cols:
        violations.append("columns.missing: " + ",".join(missing_cols))

    dec_i = find_canonical_col(headers, "決策")
    st_i = find_canonical_col(headers, "狀態")
    bad_decision: list[str] = []
    bad_status: list[str] = []
    malformed: list[str] = []
    for row in finding_table[1:]:
        needed = max(x for x in (id_i, dec_i, st_i) if x is not None)
        if len(row) <= needed:
            malformed.append(
                row[id_i][:16] if id_i < len(row) else f"row{len(malformed) + 1}"
            )
            continue
        fid = row[id_i].strip() or "?"
        if dec_i is not None:
            matches = [d for d in DECISION_EMOJI if d in row[dec_i]]
            if len(matches) != 1:
                bad_decision.append(fid)
        if st_i is not None and status_bucket(row[st_i]) not in TERMINAL_STATUSES:
            bad_status.append(fid)
    if bad_decision:
        violations.append("decision.domain: " + ",".join(bad_decision))
    if bad_status:
        violations.append("status.not_terminal: " + ",".join(bad_status))
    if malformed:
        violations.append("row.malformed: " + ",".join(malformed))

    if violations:
        for v in violations:
            print(f"[{name}] [FAIL] {v}")
        return EXIT_FAIL
    print(f"[{name}] [OK] canonical")
    return EXIT_OK


def cmd_parse(text: str, name: str) -> int:
    region = identity_region(text.splitlines())
    if not has_reviewed_revision(region, strict=False):
        print(
            f"[{name}] [FAIL] identity.stale: 無 reviewed 行（identity 無法錨定——"
            "拒收，禁猜 resolved）"
        )
        return EXIT_STALE

    result = parse_ledger(text)
    if result is None:
        print(
            f"[{name}] [FAIL] no_findings_table: 找不到含 ID 欄的 findings 表（fail-closed 拒收）"
        )
        return EXIT_FAIL

    print(
        f"[{name}] findings={result['findings']} tables={result['tables']} "
        f"decisions ✅={result['dec']['✅']}/❌={result['dec']['❌']}/⚠️={result['dec']['⚠️']}"
        f"/unknown={result['dec']['unknown']} (source={result['decision_source']}) "
        f"status resolved={result['st']['resolved']}/verified={result['st']['verified']}"
        f"/closed={result['st']['closed']}/open={result['st']['open']}"
        f"/unknown={result['unknown_status']} 未決={result['未決']} unparsed={result['unparsed']}"
    )
    return EXIT_OK


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("lint", "parse"):
        print("usage: review_ledger.py lint|parse <ledger.md>", file=sys.stderr)
        return EXIT_FAIL
    subcommand, target = argv[1], Path(argv[2])
    if not target.is_file():
        print(f"review_ledger: [FAIL] missing: {target}", file=sys.stderr)
        return EXIT_MISSING
    text = target.read_text(encoding="utf-8")
    if subcommand == "lint":
        return cmd_lint(text, target.name)
    return cmd_parse(text, target.name)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
