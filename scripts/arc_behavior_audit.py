#!/usr/bin/env python3
"""arc_behavior_audit——marshal mode 弧結算審計，一行 JSON（AIR-135 Q7 MVP；AIR-152）。

三流（Q7 收斂：最低干擾審計，非閘）：
  1. 源碼直改數——git log merge-base(trunk, HEAD)..HEAD 觸檔數，扣除 exempt
     前綴（bookkeeping 目錄）。**歸因近似**：branch 級 MVP 無法區分 main-session
     直改與 worker commit（worker 產出以 agent-id 歸因非 git author——Q7 豁免表）
  2. spawn 數——`.zcode` agent gate jsonl 行數（路徑 --gate-log 傳入）；雙源之
     一，bridge 委派走 Bash 不經 Agent tool，**必須併流 3 才不誤判 0 spawn**
  3. bridge 委派數——cwd repo `.delegate-bridge/jobs.json` 計數
  ＋modelID 分佈——--zcode-db 傳 db.sqlite；schema 未驗（probe-first），查不到
  表／欄位一律 `"status":"unavailable"` 降級，**禁腦補**

附加欄 `workingTreeDirtySourceFiles`：未 commit 的 working tree 直改（branch
log 看不到的當下弧面；同標近似）。

輸出＝單行 compact JSON（ AIR-135.8 correction 挖掘輸入）。**掛點現況**：standalone
diagnostic——post-build 收斂段的常駐接線歸 AIR-151 的 SKILL 收斂小節（skills/post-build/
SKILL.md）；本腳本不假設已被自動消費（codex 152-C7：禁宣稱未接線的消費鏈）。
報告自標「挖掘線索非違規判定」；誤報豁免（Q7）：≤2 檔合法／卡檔 journal 回覆
不算／破網 fallback-attach 豁免／worker 產出以 agent-id 歸因。
任何內部錯誤逐欄降級（該欄 unavailable＋reason），整體恆 exit 0 輸出一行。
"""

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "arc-behavior-audit/1"
DEFAULT_EXEMPT_PREFIXES = (
    "backlog/",
    ".agent-tmp/",
    ".delegate-bridge/",
    "ai-analysis/",
    ".agents/",
    ".zcode/",
)
MODEL_COL_CANDIDATES = ("modelid", "model_id", "model", "modelname", "model_name")
SESSION_COL_CANDIDATES = ("sessionid", "session_id")


def _git(repo: str, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args], capture_output=True, text=True, check=False
        )
        return proc.stdout if proc.returncode == 0 else ""
    except OSError:
        return ""


def _is_exempt(rel: str, prefixes: tuple[str, ...]) -> bool:
    return any(rel.startswith(p) for p in prefixes)


def _source_files(paths: list[str], prefixes: tuple[str, ...]) -> list[str]:
    seen: list[str] = []
    for rel in paths:
        rel = rel.strip()
        if not rel or _is_exempt(rel, prefixes) or rel in seen:
            continue
        seen.append(rel)
    return seen


def direct_edits(repo: str, trunk: str, prefixes: tuple[str, ...]) -> dict:
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() or "unknown"
    merge_base = _git(repo, "merge-base", trunk, "HEAD").strip()
    if not merge_base:
        return {
            "count": None,
            "files": [],
            "note": "unavailable：merge-base(%s, HEAD) 不可判定" % trunk,
        }
    # git log 失敗≠零 commit——失敗須降級 unavailable 禁吞成 0（codex 152 複審）
    proc = subprocess.run(
        ["git", "-C", repo, "log", "--name-only", "--pretty=format:",
         merge_base + "..HEAD"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return {
            "count": None,
            "files": [],
            "note": "unavailable：git log 失敗（%s）" % proc.stderr.strip()[:120],
        }
    files = _source_files(proc.stdout.splitlines(), prefixes)
    return {
        "count": len(files),
        "files": files,
        "attribution": "approximate",
        "scope": "merge-base(%s, HEAD)..HEAD 觸檔（非 worker 歸因——MVP 從簡）" % trunk,
        "branch": branch,
    }


def dirty_tree(repo: str, prefixes: tuple[str, ...]) -> dict:
    out = _git(repo, "status", "--porcelain")
    files: list[str] = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        rel = line[3:].strip().strip('"')
        if rel and not _is_exempt(rel, prefixes):
            files.append(rel)
    return {"count": len(files), "files": files, "attribution": "approximate"}


def spawn_count(gate_log: str | None, session: str | None) -> dict:
    if not gate_log:
        return {"count": None, "note": "unavailable：未提供 --gate-log"}
    path = Path(gate_log)
    if not path.exists():
        return {"count": None, "note": "unavailable：gate log 不存在（%s）" % gate_log}
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError as exc:
        return {"count": None, "note": "unavailable：%r" % (exc,)}
    hits = [ln for ln in lines if ln.strip()]
    if session:
        hits = [ln for ln in hits if session in ln]
    return {
        "count": len(hits),
        "source": str(path),
        "note": "gate jsonl 行數（Agent tool 面）——bridge 委派見 bridgeDelegations",
    }


def bridge_delegations(repo: str, session: str | None) -> dict:
    ledger = Path(repo) / ".delegate-bridge" / "jobs.json"
    if not ledger.exists():
        return {"count": None, "note": "unavailable：無 ledger（%s）" % ledger}
    try:
        rows = json.loads(ledger.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"count": None, "note": "unavailable：%r" % (exc,)}
    if not isinstance(rows, list):
        return {"count": None, "note": "unavailable：ledger 非 list 形"}
    if session:
        rows = [r for r in rows if isinstance(r, dict) and r.get("sessionId") == session]
    return {
        "count": len(rows),
        "ledger": str(ledger),
        "note": "bridge task 走 Bash 不經 Agent tool——與 spawn 數併看",
    }


def _named_col(cols: list[tuple], candidates: tuple[str, ...]) -> str | None:
    for row in cols:
        name = str(row[1]).lower()
        if name in candidates:
            return str(row[1])
    return None


def model_distribution(zcode_db: str | None, session: str | None) -> dict:
    """probe-first：db schema 未驗——任何一步不成立即 unavailable 降級，禁腦補。

    實證（2026-09-21，bridge zcode-home db）：`model_usage` 表帶
    `session_id`＋`model_id`——per-session assistant modelID 分佈機械可行；
    session 過濾以 session_id 欄優先（role 欄退守）。
    """
    if not zcode_db:
        return {"status": "unavailable", "reason": "未提供 --zcode-db"}
    path = Path(zcode_db)
    if not path.exists():
        return {"status": "unavailable", "reason": "db 不存在（%s）" % zcode_db}
    conn = None
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % path.as_posix(), uri=True)
        conn.row_factory = sqlite3.Row
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        for table in tables:
            try:
                cols = conn.execute("PRAGMA table_info(%s)" % table).fetchall()
            except sqlite3.DatabaseError:
                continue
            model_col = _named_col(cols, MODEL_COL_CANDIDATES)
            if not model_col:
                continue
            query = "SELECT %s AS m, COUNT(*) AS n FROM %s" % (model_col, table)
            params: list = []
            filter_note = "無過濾"
            if session:
                session_col = _named_col(cols, SESSION_COL_CANDIDATES)
                if not session_col:
                    # session 歸屬不可行＝全表／role 代替都是腦補——降級不回傳
                    # （codex 152-C6：probe-first 禁以 global 冒充 session 面）
                    continue
                query += " WHERE %s = ?" % session_col
                params.append(session)
                filter_note = "session_id 欄過濾"
            query += " GROUP BY %s ORDER BY n DESC LIMIT 20" % model_col
            try:
                rows = conn.execute(query, params).fetchall()
            except sqlite3.DatabaseError as exc:
                return {
                    "status": "unavailable",
                    "reason": "table %s 查詢失敗：%s" % (table, exc),
                }
            if rows:
                return {
                    "status": "probed",
                    "table": table,
                    "modelColumn": model_col,
                    "sessionFilter": filter_note,
                    "distribution": {str(r["m"]): r["n"] for r in rows},
                    "note": "probe-first：表/欄位候選命中非 schema 保證",
                }
        return {
            "status": "unavailable",
            "reason": "tables=%s 無 model 欄候選命中" % tables[:10],
        }
    except sqlite3.Error as exc:
        return {"status": "unavailable", "reason": repr(exc)}
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="arc_behavior_audit",
        description="marshal mode 弧結算審計——直改／spawn／委派／modelID 一行 JSON",
    )
    parser.add_argument("--repo", default=".", help="目標 repo（預設 .）")
    parser.add_argument("--trunk", default="main", help="trunk branch（預設 main）")
    parser.add_argument(
        "--session", default=None, help="session id（gate log 子串過濾＋ledger sessionId 過濾）"
    )
    parser.add_argument("--gate-log", default=None, help=".zcode agent gate jsonl 路徑")
    parser.add_argument("--zcode-db", default=None, help="ZCode db.sqlite 路徑（probe-first）")
    parser.add_argument(
        "--exempt-prefix",
        nargs="*",
        default=list(DEFAULT_EXEMPT_PREFIXES),
        help="非源碼 exempt 前綴（預設 bookkeeping 目錄集）",
    )
    args = parser.parse_args()

    repo = str(Path(args.repo).resolve())
    prefixes = tuple(args.exempt_prefix)
    audit = {
        "schema": SCHEMA,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "trunk": args.trunk,
        "directSourceEdits": direct_edits(repo, args.trunk, prefixes),
        "workingTreeDirtySourceFiles": dirty_tree(repo, prefixes),
        "spawns": spawn_count(args.gate_log, args.session),
        "bridgeDelegations": bridge_delegations(repo, args.session),
        "modelIdDistribution": model_distribution(args.zcode_db, args.session),
        "verdict": "挖掘線索非違規判定（AIR-135 Q7）",
        "exemptions": "≤2 檔合法／卡檔 journal 回覆不算／破網 fallback-attach 豁免／"
        "worker 產出以 agent-id 歸因非 git author",
    }
    print(json.dumps(audit, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
