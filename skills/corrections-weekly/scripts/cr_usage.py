#!/usr/bin/env python3
"""CR 使用量挖掘（corrections-weekly 的 CR 健檢機械面——三源三證據類）。

源1 ZCode db（structured call evidence）：撈時間窗內所有 sessions（含
subagent——升級①的 cr-research 用量算數；side_chat/fork 亦計入——全 workspace
消費語義，判讀時知悉計數含這些形態）的 tool part，統計 CR 消費三指標：CR 家族
skill 調用（cr-query＋code-reality）、CR MCP 工具呼叫、對照 Bash rg 呼叫量。
源2 bridge jobs（structured call＋output evidence）：`~/Github/*/.delegate-bridge/
jobs/*.jsonl`（mtime 窗）——呼叫證據只認 `item.completed`＋`item.type=
command_execution` 的 `command` 欄位 match CR CLI（正樣本 job-mtx2eakq 鎖
schema；command 欄位以外的文字面提及≠呼叫——條文引用與呼叫混淆是誤報主體）；
寫入面 subcommand（build/snapshot/delta_tour/project）另計；`[SRC]`／
「未 index 驗證」／degraded marker＝output evidence（evidence-bearing，非
CR calls）。
源3 agent 產出（output evidence）：`~/.zcode/cli/agents/sess_*/agent_*/
output.txt`（mtime 窗）同指紋——output face 只有文字，一律計 evidence 不計 call。
源4 receipt closure 對帳（AIR-224——AC6 七分項）：`~/Github/*/.review/*.md`
（mtime 窗；帳本隨 commit 清除，窗口內在場者才計——durable 觀察面歸卡／EP
notes，非本腳本掃描面）掃 legs 名冊／per-leg cr receipt／cr-closure／
legacy-exempt 章計七分項（eligible／declared／observed-evidence／receipt／
degraded／N-A／silent fallback 各獨立計數）；bridge brief route 宣告掃 jobs
jsonl `turn.input.user` payload prompt（不掃全檔文字——skill 條文流經
task.lifecycle.output 的誤報是审计實證主體）；in-harness crsurface 分布掃 db
part 文字。SM-6 宣告 vs 實呼 histogram 歸收線核對手工貼卡（禁腳本化——
bridge-dispatch「結構證據收線核對」條款），本腳本只供分項計數。
輸出計數＋distinct 單位供 LLM 判讀（腳本不判讀——advisory 面）。

Run: uv run python cr_usage.py [--days 7]
Exit: 0=正常（含零使用）；1=源1 db 失敗（唯讀、fail-loud——結構化主源不可靜默缺場）；
源2/3 目錄缺場＝正常零計數（非每機都有 bridge jobs）。
"""

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path

DB = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
GITHUB = Path.home() / "Github"
AGENTS_ROOT = Path.home() / ".zcode" / "cli" / "agents"

# 呼叫證據＝command 欄位執行 CR CLI；路徑形（skills/code-reality/SKILL.md）
# 因 "code-reality" 後接 "/" 不匹配，天然排除文件讀取誤報。
CR_CALL_RE = re.compile(
    r"\bcode-reality\s+(scip_refs|graph_query|hub_refs|search|symbols|"
    r"chain_tour|boundary\w*|snapshot|delta_tour|tour_\w+|runtime_edges|"
    r"project|build|graph_db|refresh|hook\w*|sidecar_migrate)\b"
)
WRITE_FACE = {"build", "snapshot", "delta_tour", "project"}
EVIDENCE_RES = {
    "src": re.compile(r"\[SRC\]"),
    "unverified": re.compile(r"未\s*index\s*驗證|unverified"),
    "degraded": re.compile(r"\[WARN\]\s*structural context degraded"),
}

# ---------- 源4（AIR-224 receipt closure 對帳） ----------
# 語法鏡像：receipt 承載語法單一源＝workflow-review-pattern「per-leg CR receipt
# 語法」；route 值域單一源＝bridge-dispatch；機械驗收面＝review_ledger.py lint
# （本腳本只計數不驗收——advisory）。
ROUTE_DECL_RE = re.compile(
    r"route[：:]\s*(live-cr(?::MCP|:CLI)?|preprovided-cr|degraded|n/a)"
)
CRSURFACE_RE = re.compile(r"crsurface=(mcp|attach|cli|absent)")
LEGS_LINE_RE = re.compile(r"legs\s*[：:]", re.IGNORECASE)
CR_RECEIPT_RE = re.compile(r"cr\(route=([a-z-]+(?::MCP|:CLI)?)[^)]*\)")
CR_NA_RE = re.compile(r"cr:\s*n/a\s*[（(]reason=")
CR_CLOSURE_RE = re.compile(r"cr-closure\s*[：:](.*)")
CR_CLOSURE_ITEM_RE = re.compile(r"[A-Za-z0-9_.-]+\s+(checked|rejected)\b")
EXEMPT_MARK = "legacy-exempt"
EPHEMERAL_REF = ".delegate-bridge/jobs/"


def scan_receipt_ledgers(since_s: float) -> dict:
    """掃窗口內帳本檔的 per-leg receipt 七分項原料（每項獨立計數）。"""
    out = {
        "ledgers": 0,
        "exempt_ledgers": 0,
        "eligible": 0,
        "na_legs": 0,
        "receipts": 0,
        "degraded": 0,
        "na_receipts": 0,
        "closures": 0,
        "silent_fallback": 0,
        "ephemeral_refs": 0,
        "per_repo": {},
    }
    if not GITHUB.is_dir():
        return out
    for lf in GITHUB.glob("*/.review/*.md"):
        try:
            if lf.stat().st_mtime < since_s:
                continue
            text = lf.read_text(errors="replace")
        except OSError:
            continue
        out["ledgers"] += 1
        repo = lf.parts[-3] if len(lf.parts) >= 3 else "?"
        rec = out["per_repo"].setdefault(repo, {"ledgers": 0, "receipts": 0})
        rec["ledgers"] += 1
        eligible = na_legs = receipts = na_receipts = degraded = 0
        closures = ephemeral = 0
        for line in text.splitlines():
            m = LEGS_LINE_RE.search(line)
            if m:
                for item in re.split(r"[；;]", line[m.end() :]):
                    parts = item.split()
                    if len(parts) >= 3 and parts[-1] == "trigger":
                        eligible += 1
                    elif len(parts) >= 3 and parts[-1] == "n/a":
                        na_legs += 1
            for rm in CR_RECEIPT_RE.finditer(line):
                receipts += 1
                if rm.group(1) == "degraded":
                    degraded += 1
            na_receipts += len(CR_NA_RE.findall(line))
            cm = CR_CLOSURE_RE.search(line)
            if cm:
                # 逐 item 計數（一行可載多腿：`cr-closure：L1 checked；L2 rejected`）
                closures += len(CR_CLOSURE_ITEM_RE.findall(cm.group(1)))
            ephemeral += len(
                re.findall(r"evidence=[^)|]*" + re.escape(EPHEMERAL_REF), line)
            )
        if EXEMPT_MARK in text:
            out["exempt_ledgers"] += 1
        # silent fallback＝eligible 腿無 route receipt（負值截 0——n/a 腿不在分子）
        silent = max(0, eligible - receipts)
        out["eligible"] += eligible
        out["na_legs"] += na_legs
        out["receipts"] += receipts
        out["degraded"] += degraded
        out["na_receipts"] += na_receipts
        out["closures"] += closures
        out["silent_fallback"] += silent
        out["ephemeral_refs"] += ephemeral
        rec["receipts"] += receipts
    return out


def scan_brief_routes(since_s: float) -> dict:
    """掃窗口內 bridge brief（turn.input.user payload prompt）的 route 宣告行。"""
    out = {"jobs": 0, "declared_jobs": 0, "values": {}}
    if not GITHUB.is_dir():
        return out
    for jf in GITHUB.glob("*/.delegate-bridge/jobs/*.jsonl"):
        try:
            if jf.stat().st_mtime < since_s:
                continue
            text = jf.read_text(errors="replace")
        except OSError:
            continue
        out["jobs"] += 1
        declared = 0
        for line in text.splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("payload_type") != "turn.input.user":
                continue
            prompt = str((e.get("payload") or {}).get("prompt") or "")
            for m in ROUTE_DECL_RE.finditer(prompt):
                declared += 1
                v = m.group(1)
                out["values"][v] = out["values"].get(v, 0) + 1
        if declared:
            out["declared_jobs"] += 1
    return out


def scan_crsurface(since_ms: int) -> dict:
    """掃 db part 文字面 crsurface= 分布（dispatch preview 落在 session 文字）。"""
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT json_extract(p.data, '$.text') FROM part p "
            "WHERE p.time_created >= ? AND p.data LIKE '%crsurface=%'",
            (since_ms,),
        ).fetchall()
    finally:
        db.close()
    values: dict[str, int] = {}
    for (t,) in rows:
        for m in CRSURFACE_RE.finditer(str(t or "")):
            values[m.group(1)] = values.get(m.group(1), 0) + 1
    return values


def scan_db(since_ms: int) -> tuple[dict, set, dict, int]:
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "SELECT s.id, json_extract(p.data, '$.tool') AS tool, "
            "json_extract(p.data, '$.state.input.command') AS cmd "
            "FROM part p JOIN session s ON p.session_id = s.id "
            "WHERE p.time_created >= ? "
            "AND json_extract(p.data, '$.type') = 'tool' "
            "AND (json_extract(p.data, '$.tool') LIKE 'mcp__plugin%' "
            "     OR json_extract(p.data, '$.tool') IN ('Bash', 'Skill'))",
            (since_ms,),
        ).fetchall()
        skill_rows = db.execute(
            "SELECT s.id, json_extract(p.data, '$.state.input.skill') AS skill "
            "FROM part p JOIN session s ON p.session_id = s.id "
            "WHERE p.time_created >= ? "
            "AND json_extract(p.data, '$.type') = 'tool' "
            "AND json_extract(p.data, '$.tool') = 'Skill'",
            (since_ms,),
        ).fetchall()
    finally:
        db.close()
    cr_skill_map, cr_skill_total, cr_mcp, rg = {}, set(), {}, 0
    for sid, skill in skill_rows:
        s = str(skill or "")
        if "cr-query" in s or "code-reality" in s:
            cr_skill_map.setdefault(s, set()).add(sid)
            cr_skill_total.add(sid)
    for sid, tool, cmd in rows:
        name = tool or ""
        if name.startswith("mcp__plugin") and "code-reality" in name:
            cr_mcp.setdefault(name, set()).add(sid)
        elif name == "Bash" and cmd:
            c = str(cmd)
            if c.startswith("rg ") or " rg " in c:
                rg += 1
    return cr_skill_map, cr_skill_total, cr_mcp, rg


def scan_bridge(since_s: float) -> dict:
    out = {
        "jobs": 0,
        "call_jobs": 0,
        "calls": 0,
        "write_face": 0,
        "evid_jobs": 0,
        "per_repo": {},
        "markers": {k: 0 for k in EVIDENCE_RES},
    }
    if not GITHUB.is_dir():
        return out
    for jf in GITHUB.glob("*/.delegate-bridge/jobs/*.jsonl"):
        try:
            if jf.stat().st_mtime < since_s:
                continue
            text = jf.read_text(errors="replace")
        except OSError:
            continue
        out["jobs"] += 1
        repo = jf.parts[-4] if len(jf.parts) >= 4 else "?"
        rec = out["per_repo"].setdefault(
            repo, {"jobs": 0, "call_jobs": 0, "evid_jobs": 0}
        )
        rec["jobs"] += 1
        has_call = False
        for line in text.splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "item.completed":
                continue
            item = e.get("item") or {}
            if item.get("type") != "command_execution":
                continue
            m = CR_CALL_RE.search(str(item.get("command") or ""))
            if m:
                has_call = True
                out["calls"] += 1
                if m.group(1) in WRITE_FACE:
                    out["write_face"] += 1
        has_evid = False
        for name, rx in EVIDENCE_RES.items():
            if rx.search(text):
                has_evid = True
                out["markers"][name] += 1
        if has_call:
            out["call_jobs"] += 1
            rec["call_jobs"] += 1
        if has_evid:
            out["evid_jobs"] += 1
            rec["evid_jobs"] += 1
    return out


def scan_agent_outputs(since_s: float) -> dict:
    out = {"files": 0, "evid_files": 0, "markers": {k: 0 for k in EVIDENCE_RES}}
    if not AGENTS_ROOT.is_dir():
        return out
    for of in AGENTS_ROOT.glob("sess_*/agent_*/output.txt"):
        try:
            if of.stat().st_mtime < since_s:
                continue
            text = of.read_text(errors="replace")
        except OSError:
            continue
        out["files"] += 1
        has_evid = False
        for name, rx in EVIDENCE_RES.items():
            if rx.search(text):
                has_evid = True
                out["markers"][name] += 1
        if has_evid:
            out["evid_files"] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    if args.days <= 0:
        ap.error("--days 必須 > 0")

    since_ms = int((time.time() - args.days * 86400) * 1000)
    since_s = time.time() - args.days * 86400

    try:
        cr_skill_map, cr_skill_total, cr_mcp, rg = scan_db(since_ms)
    except sqlite3.Error as exc:
        print(f"[FAIL] db 查詢失敗：{exc}")
        return 1

    def line(label: str, mapping: dict) -> None:
        for name in sorted(mapping, key=lambda k: -len(mapping[k])):
            print(f"{label}\t{len(mapping[name])} sessions\t{name}")

    print(f"[OK] cr_usage: {args.days}d 窗（三源：ZCode db／bridge jobs／agent 產出）")
    print("== 源1 ZCode db（structured call evidence）==")
    print("-- CR Skill 調用（cr-query＋code-reality）--")
    if cr_skill_map:
        print(f"cr-skill-total\t{len(cr_skill_total)} sessions")
        line("cr-skill", cr_skill_map)
    else:
        print("（零）")
    print("-- CR MCP 工具（distinct sessions）--")
    if cr_mcp:
        line("cr-mcp", cr_mcp)
    else:
        print("（零）")
    print(f"-- 對照：Bash rg 呼叫 part 數 --\n{rg}")

    print("== 源2 bridge jobs（call＝command 欄位實證；evidence≠call）==")
    b = scan_bridge(since_s)
    print(f"jobs\t{b['jobs']}")
    print(
        f"call-evidence jobs\t{b['call_jobs']}（CR CLI 呼叫 {b['calls']} 次；寫入面 {b['write_face']} 次）"
    )
    print(
        f"evidence-bearing jobs\t{b['evid_jobs']}（markers: "
        + ", ".join(f"{k}={v}" for k, v in b["markers"].items())
        + "）"
    )
    for repo in sorted(b["per_repo"], key=lambda r: -b["per_repo"][r]["jobs"]):
        r = b["per_repo"][repo]
        print(
            f"repo\t{repo}\tjobs={r['jobs']}\tcall={r['call_jobs']}\tevidence={r['evid_jobs']}"
        )

    print("== 源3 agent 產出（output evidence face，無 call 證據）==")
    a = scan_agent_outputs(since_s)
    print(f"files\t{a['files']}")
    print(
        f"evidence-bearing files\t{a['evid_files']}（markers: "
        + ", ".join(f"{k}={v}" for k, v in a["markers"].items())
        + "）"
    )

    print(
        "== 源4 receipt closure 對帳（AIR-224——七分項獨立計數；帳本源="
        "~/Github/*/.review/*.md mtime 窗，durable 觀察面歸卡/EP notes）=="
    )
    try:
        crs = scan_crsurface(since_ms)
    except sqlite3.Error as exc:
        print(f"[FAIL] db 查詢失敗：{exc}")
        return 1
    ledg = scan_receipt_ledgers(since_s)
    brief = scan_brief_routes(since_s)
    print(
        f"ledgers\t{ledg['ledgers']}（exempt={ledg['exempt_ledgers']}"
        + (
            f"；exempt-rate={ledg['exempt_ledgers'] / ledg['ledgers']:.2f}"
            if ledg["ledgers"]
            else ""
        )
        + "）"
    )
    decl_vals = (
        ", ".join(f"{k}={v}" for k, v in sorted(brief["values"].items()))
        or "零"
    )
    crs_vals = (
        ", ".join(f"{k}={v}" for k, v in sorted(crs.items())) or "零"
    )
    print(
        f"declared\tbrief_jobs={brief['declared_jobs']}/{brief['jobs']}"
        f"（值分布: {decl_vals}）；in-harness crsurface 分布: {crs_vals}"
    )
    print(f"eligible\t{ledg['eligible']}（legs 名冊 trigger 腿；n/a 腿 {ledg['na_legs']}）")
    print(f"observed-evidence\t源2 call-evidence jobs={b['call_jobs']}")
    print(f"receipt\t{ledg['receipts']}")
    print(f"degraded\t{ledg['degraded']}（receipt 內 degraded route——fresh-F7 獨立分項行）")
    print(
        f"n-a\t顯式 n/a receipt={ledg['na_receipts']}"
    )
    print(f"silent-fallback\t{ledg['silent_fallback']}（eligible−receipts，負值截 0）")
    if ledg["receipts"]:
        print(
            f"rates\treceipt-rate={ledg['receipts'] / max(ledg['eligible'], 1):.2f}"
            f"（receipts/eligible）　closure-rate={ledg['closures'] / ledg['receipts']:.2f}"
            f"（closures={ledg['closures']}/receipts）"
        )
    else:
        print("rates\tn/a（窗口內零 receipt）")
    print(f"ephemeral-evidence refs\t{ledg['ephemeral_refs']}（WT-local job jsonl 形——不得滿足 converged receipt）")
    print(
        "sm6-histogram\t宣告 live-cr 腿的實呼 histogram 歸收線核對手工貼卡"
        "（禁腳本化——bridge-dispatch「結構證據收線核對」）；本節分項僅供 LLM 判讀"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
