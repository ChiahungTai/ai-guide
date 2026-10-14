#!/usr/bin/env python3
"""審查帳本 lint＋parse——``.review/<branch>.md`` 機械驗收閘（AIR-121）。

雙子命令：
- ``lint <ledger.md> [--stage discovery|converged]``：canonical 格式驗證（寫入時
  gate）——identity 三行（reviewed 錨／scope／review_profile）＋Finding Record 表
  canonical 欄位（ID／嚴重度／位置／問題／建議／驗證式／狀態／決策）＋值域
  （decision ∈ ✅❌⚠️；terminal status 見 TERMINAL_STATUSES）＋per-leg CR receipt
  （AIR-224——converged 面：``legs`` 名冊強制行、命中 trigger 腿缺 receipt FAIL、
  degraded 無非空 reason FAIL、n/a 腿缺顯式 sentinel FAIL、live/preprovided 無
  evidence FAIL、孤兒腿 FAIL、ephemeral bridge ref（``.delegate-bridge/jobs/``）
  拒收；行首 ``legacy-exempt（cutoff=…）`` 逐字形章放行三類舊檔缺 receipt 語義）。
  grammar 單一源＝workflow-review-pattern「per-leg CR receipt 語法」，本檔為
  consumer-equivalent 鏡像。``--stage`` 對齊
  帳本生命週期（預設 converged＝全查）：
  - ``discovery``（post-build 階段 2——judge 前）：只查 identity 錨＋欄位存在性；
    decision/status **值域不查**（發現時態 decision＝「—」、status＝open 是常態，
    值域檢查會與生命週期互斥——F-1）；per-leg CR receipt 檢查亦不查（muse-F2——
    cr 檢查收斂到 converged 面，與 post-build 階段 2 閘契約同制）。
  - ``converged``（收斂態落卡／commit 2.6——帳本已是終態）：全查（值域＋cr receipt 含）。
- ``parse <ledger.md>``：容錯讀＋tally（歷史帳本回歸／消費面）——跨表 ID-join
  last-wins（發現時態表被 apply 終態表覆蓋）、prose 計數禁用（否定句陷阱：
  「零 ❌、零 ⚠️」不得入計數）、解析不出→明確 ``[FAIL]`` 類別拒收（unknown，
  禁猜 resolved）。``` 圍欄內的表格是格式說明範例非資料表——跳過不計（F-6）；
  含 ID 欄表頭的 header-only 表（零資料列）＝零 findings 的合法編碼、非拒收
  對象（AIR-331——缺 ID 表頭仍 fail-closed）。

多表語義（AIR-333 裁決③ join-aware 分類）：lint 與 parse 共用表定位
（``find_keyed_tables``）與 join 實作（``join_keyed_tables``——單一 last-wins
語義，禁兩套並存）。對 lint：第一張 keyed 表＝Finding 定義表（全 canonical 欄位，
不變）；其後的 keyed 表若 header 含「狀態」或「決策」欄、且全部資料列 fid
（strip 後非空）已見於前表＝狀態 patch 表（歷史 Apply 記錄表 ``ID｜狀態｜…``
形）——豁免 columns.missing，在場欄位值域與 malformed 照查；零資料列後表＝
vacuous patch；引入新 fid、缺狀態／決策欄或含空白 fid 列＝整表按 Finding Record
全檢（混合表整表計，不逐列豁免）——不變式：每 fid 首次出現必落在受全 canonical
檢查的表。converged 值域以 join 後每 fid 終態為準：主表發現時態列（open／—）被
patch 覆寫成 terminal／合法決策即收斂，不因前表歷史列誤判；decision last-wins
以「最終生效 cell」為單位（F-01）——cell 內多 emoji 並存（如「✅❌」）不縮水成
首個 emoji，converged 要求終態 cell 恰一 distinct emoji（歷史非法 cell 被後續
合法 patch 覆寫＝查終態即過）。keyed 表資料列完整性以 header 宣告欄位數為準
（F-02——lint 面 ``len(row)`` 須涵蓋 header 非 empty cells，不足＝row.malformed）；
全 keyed 表逐列查空白 fid（F-03）＝獨立 violation ``fid.blank``（discovery＋
converged 皆拒），join 對空白 fid 當 unparsed 省略、禁 ``(rowN)`` 補名偽 finding。
跨表聚合違規（decision.domain／status.not_terminal／fid.blank／row.malformed）
同一 fid 保序去重（``dict.fromkeys``）；columns.missing 逐表列報不去重——靜默去重
會遮蔽第二張壞表。

exit 契約：``0`` 成功／``1`` 解析失敗（fail-closed）／``2`` 帳本不存在／
``3`` identity stale。

嚴格度分工：lint 是 canonical gate（identity 錨＝``reviewed=`` 或
``reviewed revision`` 兩形皆 canonical——對齊 canonical 模板與歷史帳本，F-3）；
parse 是容錯讀者（任何 ``reviewed`` 行即可錨定）。**parse PASS ≠ lint PASS**：
parse 容忍歷史帳本的 partial Apply／缺欄／unknown（一律計入「未決」），lint 是
新寫入帳本的 canonical gate——新帳本落盤前跑 lint，FAIL 先修帳本（把 patch 併回
主表或補欄），不以 parse 結果主張 canonical。歷史漂移語義：狀態自由文字
（如 implemented）不計 terminal、欄位缺席＝unknown——誤差方向安全：只省略
不捏造。cell 內出現 pipe 一律寫轉義形 ``\\|``
（驗證式欄 rg pattern 常見）——split_row 容錯讀取此形，未轉義裸 pipe 會拆壞
欄位（F-7）。
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
# terminal 值域（F-2 對齊）：verified|closed＝canonical terminal（status 生命週期終點，
# 鏈上實際寫入者——post-build 階段 3 主鏈編排者）；resolved＝容錯 terminal（歷史帳本
# 方言，如 AIR-91 收斂帳本以 resolved 落終態）——parse 視同 terminal、lint converged
# 接受，新寫入應用 verified/closed（單一源＝workflow-review-pattern「status 生命週期」）。
TERMINAL_STATUSES: tuple[str, ...] = ("resolved", "verified", "closed")
PENDING_STATUSES: tuple[str, ...] = ("open", "needs-confirmation")

# ---------- per-leg CR receipt lint（AIR-224——S1 grammar 的 consumer-equivalent 鏡像） ----------
# grammar 單一源＝workflow-review-pattern「per-leg CR receipt 語法」節；route 值域
# 單一源＝bridge-dispatch「結構查證腿——evidence route 宣告」（本檔只鏡像檢查，
# 不重定義語義）。cr 檢查屬 converged 面（muse-F2——discovery 態不呼叫，收斂態才
# 全查）；ephemeral evidence 拒收隨之併入 converged 面（producer 未落地前 bridge
# receipt 可觀察、不得以 durable-complete 收線——EP Amendment）。
CR_ROUTES: tuple[str, ...] = ("live-cr:MCP", "live-cr:CLI", "preprovided-cr", "degraded")

# 行首錨定（muse-F8）：名冊／receipt／n/a／豁免章只認「行首（容 `> ` blockquote 與
# `- `/`* ` 列表符）」起手的行——identity 區 prose（scope 行等）內嵌 grammar 文本
# （格式說明）不計入 receipt、不誤解析名冊、不誤豁免。
_LINE_ITEM_PREFIX = r"^\s*(?:>\s*)?(?:[-*]\s*)?"

# receipt 行：`<leg key>: cr(route=<route>, evidence=<ref>|reason=<why>)`
# leg key 含 `/`（fresh-F2——grammar 佔位符＝`<family/leg>`，如 `muse/L1`）；
# 排除 `/` 會同檔出 `missing_leg: muse/L1`＋`orphan_leg: L1`（join 破裂）。
CR_RECEIPT_RE = re.compile(
    _LINE_ITEM_PREFIX
    + r"(?P<leg>[A-Za-z0-9_./-]+)\s*:\s*"
    r"cr\(route=(?P<route>[a-z-]+(?::MCP|:CLI)?)\s*,\s*(?P<payload>[^)]*)\)"
)
# n/a applicability sentinel（非 route 值）：`<leg key>: cr: n/a（reason=…；…）`
CR_NA_RE = re.compile(
    _LINE_ITEM_PREFIX
    + r"(?P<leg>[A-Za-z0-9_./-]+)\s*:\s*cr:\s*n/a\s*[（(]reason=(?P<reason>[^）)]+)[）)]"
)
# legs 名冊（強制行）：`legs：<leg key> <jobId> trigger|n/a；…`（receipt 以 leg key join）
LEGS_RE = re.compile(_LINE_ITEM_PREFIX + r"legs\s*[：:]", re.IGNORECASE)
LEG_ROSTER_TAGS: tuple[str, ...] = ("trigger", "n/a")
# ephemeral observation 形態（EP Amendment）：WT-local bridge job jsonl 路徑
EPHEMERAL_BRIDGE_REF = ".delegate-bridge/jobs/"

# legacy-exempt 凍結 cutoff（fresh-F4——S2 內定義）：僅 reviewed 錨早於此 baseline 的
# 帳本可蓋 `legacy-exempt（cutoff=<本常數值>）`豁免章；lint 機驗章格式＋cutoff 引用
# 一致，帳本時序（hash 是否真早於 cutoff）歸蓋章弧的判斷紀律（telemetry 加 exempt
# 率分項防大量靜默豁免）。cutoff 值＝AIR-224 baseline main commit b41b4ed1。
CR_RECEIPT_CUTOFF = "b41b4ed1"
# 章形收緊（fresh-F4/muse-F3＋muse-F8 行首錨定）：有效章＝行首
# `legacy-exempt（cutoff=<cutoff>）` 逐字形（半形括號亦收）——scope prose 無意
# 共現（同行含兩詞但非章形）不豁免也不誤報；行首起手而非章形＝exempt_invalid。
LEGACY_EXEMPT_STAMP_RE = re.compile(
    _LINE_ITEM_PREFIX
    + r"legacy-exempt\s*[（(]\s*cutoff\s*=\s*"
    + re.escape(CR_RECEIPT_CUTOFF)
    + r"\s*[）)]"
)
LEGACY_EXEMPT_LINE_RE = re.compile(_LINE_ITEM_PREFIX + r"legacy-exempt\b")
# 豁免面縮小（fresh-F4/muse-F3）：有效章僅放行三類「舊檔缺 receipt 語義」；
# roster_malformed／orphan_leg／bad_route／degraded 無 reason／no_evidence／
# ephemeral_evidence 照常查——自蓋章不全繞道。
EXEMPTIBLE_VIOLATION_PREFIXES: tuple[str, ...] = (
    "cr.receipt.roster_missing",
    "cr.receipt.missing_leg",
    "cr.receipt.missing_na",
)

# identity 錨兩形皆 canonical（F-3）：`reviewed revision：...`（歷史帳本形）與
# `reviewed=<hash>`（canonical 模板 identity 行形）。
REVIEWED_REVISION_RE = re.compile(r"reviewed\s*(?:revision|=)", re.IGNORECASE)
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
    # F-01：終態 decision cell（last-wins）的 distinct emoji 集——多 emoji 並存
    # 不縮水；``decision`` 仍為首 emoji（parse 容錯計數），converged gate 用本欄
    decision_emojis: tuple[str, ...] = ()


# ---------- 表格解析 ----------


def split_row(line: str) -> list[str]:
    """切 cell；容錯 inline escaped pipe（``\\|``——rg pattern 常見於驗證式欄）。"""
    esc = "\x00"
    cells = line.strip().strip("|").replace("\\|", esc).split("|")
    return [c.strip().replace(esc, "|") for c in cells]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


def split_tables(lines: list[str]) -> list[list[list[str]]]:
    """連續 pipe 行＝一個表 block；回傳逐表 raw rows（含 header 與 separator）。

    ``` 圍欄內的 pipe 行是格式說明範例（非資料表）——跳過不計（F-6）；圍欄邊界
    flush 緩衝，防圍欄前後兩張真表被誤併成同一表。
    """
    tables: list[list[list[str]]] = []
    buf: list[str] = []
    in_fence = False

    def flush() -> None:
        nonlocal buf
        if buf:
            tables.append([split_row(x) for x in buf])
            buf = []

    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("|"):
            buf.append(line)
        else:
            flush()
    flush()
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


def cell_decision_emojis(cell: str) -> tuple[str, ...]:
    """cell 內 distinct 決策 emoji（DECISION_EMOJI 順序）——F-01：join 保留終態
    cell 的完整 emoji 集，多 emoji 並存（「✅❌」）不縮水成首個 emoji。"""
    return tuple(d for d in DECISION_EMOJI if d in cell)


# ---------- per-leg CR receipt（AIR-224） ----------


def parse_legs_roster(region: list[str]) -> tuple[bool, dict[str, str], list[str]]:
    """掃 identity 區 legs 名冊。回 (名冊在場, leg→tag, malformed items)。

    名冊形態：`legs：<leg key> <jobId> trigger|n/a；…`——item 以 ``；``/``;`` 分隔、
    空白切詞，首詞＝leg key、末詞＝tag（trigger|n/a）。malformed item 不入帳，
    由 caller 出 violation（fail-closed）。
    """
    found = False
    roster: dict[str, str] = {}
    malformed: list[str] = []
    for line in region:
        m = LEGS_RE.search(line)
        if not m:
            continue
        found = True
        for item in re.split(r"[；;]", line[m.end() :]):
            item = item.strip()
            if not item:
                continue
            parts = item.split()
            tag = parts[-1] if parts else ""
            if len(parts) < 3 or tag not in LEG_ROSTER_TAGS:
                malformed.append(item[:40])
                continue
            roster[parts[0]] = tag
    return found, roster, malformed


def scan_cr_receipts(
    region: list[str],
) -> tuple[dict[str, tuple[str, str]], dict[str, str]]:
    """掃 identity 區 per-leg receipt。回 (leg→(route, payload), leg→n/a reason)。"""
    receipts: dict[str, tuple[str, str]] = {}
    na: dict[str, str] = {}
    for line in region:
        for m in CR_RECEIPT_RE.finditer(line):
            receipts[m.group("leg")] = (m.group("route"), m.group("payload"))
        for m in CR_NA_RE.finditer(line):
            na[m.group("leg")] = m.group("reason")
    return receipts, na


def cr_receipt_violations(region: list[str]) -> list[str]:
    """cr-receipt converged 面檢查（EP S2 清單；muse-F2 收斂——discovery 態不呼叫，
    caller 以 stage gate）——命中 trigger 腿缺 receipt／degraded 無非空 reason／
    n/a 缺顯式 sentinel／名冊缺場或孤兒腿／ephemeral evidence 拒收。"""
    violations: list[str] = []
    found, roster, malformed = parse_legs_roster(region)
    receipts, na = scan_cr_receipts(region)

    if not found:
        violations.append(
            "cr.receipt.roster_missing: 無 legs 名冊行（AIR-224 強制行——per-leg "
            "receipt join 前提；凍結 cutoff 前舊檔蓋 legacy-exempt 章放行）"
        )
    for item in malformed:
        violations.append(f"cr.receipt.roster_malformed: {item}")

    if found:
        for leg, tag in roster.items():
            if tag == "trigger" and leg not in receipts:
                violations.append(
                    f"cr.receipt.missing_leg: 命中 trigger 腿缺 cr receipt: {leg}"
                )
            if tag == "n/a" and leg not in na:
                violations.append(
                    f"cr.receipt.missing_na: n/a 腿缺顯式 n/a receipt（非空欄）: {leg}"
                )
        for leg in receipts:
            if leg not in roster:
                violations.append(f"cr.receipt.orphan_leg: receipt 腿不在 legs 名冊: {leg}")
        for leg in na:
            if leg not in roster:
                violations.append(
                    f"cr.receipt.orphan_leg: n/a receipt 腿不在 legs 名冊: {leg}"
                )

    for leg, (route, payload) in receipts.items():
        if route not in CR_ROUTES:
            violations.append(f"cr.receipt.bad_route: {leg} route={route}")
            continue
        if route == "degraded":
            # muse-F4：reason 值 strip 後須非空——`reason=`/`reason=  ` 不算附 reason
            m = re.search(r"reason=([^|)]*)", payload)
            reason = m.group(1).strip() if m else ""
            if not reason:
                violations.append(f"cr.receipt.degraded_no_reason: {leg}")
            continue
        m = re.search(r"evidence=([^|)]*)", payload)
        ref = m.group(1).strip() if m else ""
        if not ref:
            violations.append(f"cr.receipt.no_evidence: {leg}")
        elif EPHEMERAL_BRIDGE_REF in ref:
            violations.append(
                f"cr.receipt.ephemeral_evidence: {leg}（WT-local job jsonl＝"
                "ephemeral observation——不得滿足 converged receipt；durable "
                "producer 另案）"
            )
    return violations


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


def find_keyed_tables(
    tables: list[list[list[str]]],
) -> list[tuple[int, list[list[str]]]]:
    """含 ID 欄的 keyed 表（文件順序保序）——parse 與 lint 共用的表定位。"""
    keyed: list[tuple[int, list[list[str]]]] = []
    for rows in tables:
        idx = id_col_index(rows[0])
        if idx is not None:
            keyed.append((idx, rows))
    return keyed


def join_keyed_tables(
    keyed: list[tuple[int, list[list[str]]]],
) -> tuple[dict[str, FindingRow], int, int, str]:
    """跨表 ID-join last-wins——parse_ledger 與 cmd_lint converged 共用的唯一
    join 實作（AIR-333：兩子命令共用同一資料解釋語義，禁兩套 last-wins 並存
    漂移；嚴格度差異歸各自的消費端檢查，不歸 join 本身）。

    後表有 decision/status 欄即覆蓋前表值（發現時態 → apply 終態）；decision
    覆蓋以原始 cell 為單位（F-01——同時保留終態 cell 的 distinct emoji 集
    ``decision_emojis``，多 emoji 並存不縮水成首個 emoji；``decision`` 仍為首
    emoji，供 parse 容錯計數）；後表缺欄保留前表值（``_KEEP`` 哨兵）；欄數不足
    列與空白 fid 列（F-03——禁 ``(rowN)`` 補名偽 finding 繞過首現不變式）不入帳
    （計 unparsed——fail-closed 只省略不捏造；空白 fid 的 violation 歸 lint
    ``fid.blank``）。回 (fid→合併 FindingRow, unparsed 列數, 掃過資料列數,
    decision_source)。
    """
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
            fid = row[id_i].strip()
            if not fid:
                unparsed += 1
                continue
            new_dec_cell = row[dec_i] if dec_i is not None else _KEEP
            new_status = row[st_i] if st_i is not None else _KEEP
            existing = joined.get(fid)
            if existing is None:
                joined[fid] = FindingRow(
                    fid=fid,
                    decision=None if new_dec_cell is _KEEP else cell_decision(new_dec_cell),
                    raw_status=None if new_status is _KEEP else new_status,
                    decision_emojis=(
                        () if new_dec_cell is _KEEP else cell_decision_emojis(new_dec_cell)
                    ),
                )
            else:
                # ID-join last-wins：後表有該欄即覆蓋（發現時態 → apply 終態）；
                # decision 覆蓋以原始 cell 為單位（F-01——emoji 集隨 cell 重算）
                if new_dec_cell is not _KEEP:
                    existing.decision = cell_decision(new_dec_cell)
                    existing.decision_emojis = cell_decision_emojis(new_dec_cell)
                if new_status is not _KEEP:
                    existing.raw_status = new_status
    return joined, unparsed, total_rows, decision_source


def parse_ledger(text: str) -> dict | None:
    """回 None＝找不到含 ID 欄的 findings 表（fail-closed 拒收）。"""
    lines = text.splitlines()
    raw_tables = split_tables(lines)
    # header-only 表（含 ID 欄表頭、零資料列）保留——零資料列＝零 findings 的合法
    # 編碼，整表濾掉會把合法帳本誤殺成 no_findings_table（AIR-331）
    tables = [t for t in (normalize_table(r) for r in raw_tables) if t]
    keyed = find_keyed_tables(tables)
    if not keyed:
        return None

    joined, unparsed, _total_rows, decision_source = join_keyed_tables(keyed)

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


def cmd_lint(text: str, name: str, stage: str = "converged") -> int:
    region = identity_region(text.splitlines())
    if not has_reviewed_revision(region, strict=True):
        print(
            f"[{name}] [FAIL] identity.stale: 無 reviewed 錨行（reviewed= 或 "
            "reviewed revision——identity 無法錨定）"
        )
        return EXIT_STALE

    violations: list[str] = []
    if not has_scope(region):
        violations.append("identity.missing_scope: 無 scope 行")
    if not has_review_profile(region):
        violations.append("identity.missing_review_profile: 無 review_profile 行")

    # legacy-exempt（AIR-224 fresh-F4/muse-F3）：章形收緊為行首
    # `legacy-exempt（cutoff=<值>）` 逐字形（muse-F8 行首錨定——scope prose 無意
    # 共現不豁免）；章在場而非章形＝無效豁免（禁自由豁免）
    exempt_candidates = [line for line in region if LEGACY_EXEMPT_LINE_RE.search(line)]
    legacy_exempt = False
    if exempt_candidates:
        if any(LEGACY_EXEMPT_STAMP_RE.search(line) for line in exempt_candidates):
            legacy_exempt = True
        else:
            violations.append(
                "cr.receipt.exempt_invalid: legacy-exempt 章形不符（須行首 "
                "legacy-exempt（cutoff=" + CR_RECEIPT_CUTOFF + "）逐字形——機械錨"
                "不符，禁自由豁免）"
            )
    if stage == "converged":
        # muse-F2：cr-receipt 檢查收斂到 converged 面（discovery 只查 identity——
        # post-build 階段 2 閘契約「只查 identity 錨＋欄位存在性」）
        cr_violations = cr_receipt_violations(region)
        if legacy_exempt:
            # fresh-F4/muse-F3：豁免面縮小——僅放行三類「舊檔缺 receipt 語義」，
            # 其餘（malformed/orphan/bad_route/degraded 無 reason/no_evidence）照常查
            cr_violations = [
                v
                for v in cr_violations
                if not v.startswith(EXEMPTIBLE_VIOLATION_PREFIXES)
            ]
        violations.extend(cr_violations)

    # header-only 表保留（AIR-331——同 parse_ledger；零資料列 canonical 表＝
    # 合法帳本，濾掉會誤報 table.missing）
    tables = [
        t
        for t in (normalize_table(r) for r in split_tables(text.splitlines()))
        if t
    ]
    keyed_tables = find_keyed_tables(tables)
    if not keyed_tables:
        violations.append("table.missing: 無 Finding Record 表（找不到含 ID 欄的表格）")
        for v in violations:
            print(f"[{name}] [FAIL] {v}")
        return EXIT_FAIL

    # 多表分類（AIR-333 裁決③ join-aware——與 parse_ledger 的 ID-join 容忍面
    # 對齊）：第一張 keyed 表＝Finding 定義表（全 canonical 不變）；其後 keyed
    # 表 (a) header 含「狀態」或「決策」欄且 (b) 全部資料列 fid 已見於前表＝
    # patch 表（歷史 Apply 記錄表形）——豁免 columns.missing，在場欄位值域與
    # malformed 照查；零資料列後表＝vacuous patch；含新 fid、缺 (a) 或含空白
    # fid 列（F-03——空白列不入 (b) 判定，整表掉回全 canonical 檢查）＝整表按
    # Finding Record 全檢（混合表整表計，不逐列豁免）。不變式：每 fid 首次出現
    # 必落在受全 canonical 檢查的表——patch 定義上只含 seen fid，新 fid 必使
    # 整表升級全檢。
    bad_decision: list[str] = []
    bad_status: list[str] = []
    malformed: list[str] = []
    blank_fid: list[str] = []
    seen: set[str] = set()
    row_no = 0  # 跨表資料列計數（與 join_keyed_tables total_rows 同軸——fid.blank 定位）
    for t_idx, (id_i, finding_table) in enumerate(keyed_tables):
        headers = finding_table[0]
        data_rows = finding_table[1:]
        has_state_col = (
            find_canonical_col(headers, "狀態") is not None
            or find_canonical_col(headers, "決策") is not None
        )
        row_fids: list[str] = []
        has_blank_fid = False
        for row in data_rows:
            row_no += 1
            if len(row) > id_i and not row[id_i].strip():
                # F-03：空白 fid fail-closed——獨立 violation（fid.blank），且該列
                # 破壞 (b)「全∈seen」使整表掉出 patch 分類
                has_blank_fid = True
                blank_fid.append(f"row{row_no}")
            elif len(row) > id_i:
                row_fids.append(row[id_i].strip())
        is_patch = t_idx > 0 and not has_blank_fid and (
            not data_rows or (has_state_col and all(f in seen for f in row_fids))
        )
        seen.update(row_fids)

        if not is_patch:
            missing_cols = [
                c for c, _ in CANONICAL_COLUMNS if find_canonical_col(headers, c) is None
            ]
            if missing_cols:
                violations.append("columns.missing: " + ",".join(missing_cols))

        dec_i = find_canonical_col(headers, "決策")
        st_i = find_canonical_col(headers, "狀態")
        # 列完整性以 header 宣告欄位數為準（F-02——舊判準 max(id,dec,st) 索引漏
        # 尾端非狀態欄缺失：「F-01 | closed」缺 apply 落點不報）
        header_cols = sum(1 for h in headers if h.strip())
        for row in data_rows:
            if len(row) < header_cols:
                malformed.append(
                    row[id_i][:16] if id_i < len(row) else f"row{len(malformed) + 1}"
                )
                continue
            fid = row[id_i].strip() or "?"
            # 值域檢查僅 converged（F-1：discovery 態 decision=—／status=open 是
            # 常態）。patch 表在場欄位逐列照查（AIR-333）；定義表逐列值域由下方
            # join 後終態檢查承接——主表發現時態列可被後表覆寫，pre-join 逐列查
            # 會誤判（裁決②移除面）
            if stage == "converged" and is_patch:
                if dec_i is not None:
                    matches = [d for d in DECISION_EMOJI if d in row[dec_i]]
                    if len(matches) != 1:
                        bad_decision.append(fid)
                if st_i is not None and status_bucket(row[st_i]) not in TERMINAL_STATUSES:
                    bad_status.append(fid)

    if stage == "converged":
        # converged 值域＝join 後每 fid 終態（共用 join_keyed_tables——與 parse
        # 同一 last-wins 語義；discovery 維持不查值域）。F-01：終態 decision cell
        # 須恰一 distinct emoji——「✅❌」並存不得縮水成首個 emoji 過閘
        joined, _unparsed, _total_rows, _source = join_keyed_tables(keyed_tables)
        for f in joined.values():
            if f.decision not in DECISION_EMOJI or len(f.decision_emojis) != 1:
                bad_decision.append(f.fid)
            if status_bucket(f.raw_status) not in TERMINAL_STATUSES:
                bad_status.append(f.fid)

    # 跨表聚合違規保序去重（AIR-333 附帶③——同 fid 兩表皆違規只列一次，
    # 消費皆 substring／exit code 無定位損失）；columns.missing 逐表列報不去重
    #（靜默去重會遮蔽第二張壞表）
    if bad_decision:
        violations.append(
            "decision.domain: " + ",".join(dict.fromkeys(bad_decision))
        )
    if bad_status:
        violations.append("status.not_terminal: " + ",".join(dict.fromkeys(bad_status)))
    if blank_fid:
        violations.append("fid.blank: " + ",".join(dict.fromkeys(blank_fid)))
    if malformed:
        violations.append("row.malformed: " + ",".join(dict.fromkeys(malformed)))

    if violations:
        for v in violations:
            print(f"[{name}] [FAIL] {v}")
        return EXIT_FAIL
    print(f"[{name}] [OK] canonical (stage={stage})")
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


USAGE = (
    "usage: review_ledger.py lint <ledger.md> [--stage discovery|converged] "
    "| parse <ledger.md>"
)


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args or args[0] not in ("lint", "parse"):
        print(USAGE, file=sys.stderr)
        return EXIT_FAIL
    subcommand = args[0]
    target: str | None = None
    stage = "converged"  # 預設＝現行為（converged 全查）——F-1
    i = 1
    while i < len(args):
        tok = args[i]
        if tok == "--stage":
            if i + 1 >= len(args):
                print(USAGE, file=sys.stderr)
                return EXIT_FAIL
            stage = args[i + 1]
            i += 2
        elif tok.startswith("--stage="):
            stage = tok.removeprefix("--stage=")
            i += 1
        elif target is None:
            target = tok
            i += 1
        else:
            print(USAGE, file=sys.stderr)
            return EXIT_FAIL
    if target is None or stage not in ("discovery", "converged"):
        print(USAGE, file=sys.stderr)
        return EXIT_FAIL
    if subcommand == "parse" and stage != "converged":
        # parse 是容錯讀（無 stage 語義）——拒絕誤用
        print(USAGE, file=sys.stderr)
        return EXIT_FAIL
    path = Path(target)
    if not path.is_file():
        print(f"review_ledger: [FAIL] missing: {path}", file=sys.stderr)
        return EXIT_MISSING
    text = path.read_text(encoding="utf-8")
    if subcommand == "lint":
        return cmd_lint(text, path.name, stage)
    return cmd_parse(text, path.name)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
