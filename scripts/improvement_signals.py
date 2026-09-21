#!/usr/bin/env python3
"""improvement signals——quota-constrained 發現機制的機械掃描器（AIR-151 MVP，零 LLM invocation）。

彙整四類免費訊號、輸出 capped JSON（每類 top-20 指針＋計數，禁貼全文），供 post-build
「improvement 收斂」段讀取：有 admissible 訊號才收斂 ≤3 條候選，無＝整段跳過。本掃描器
只報計數與指針，不做語義判讀（actionable 與否＝收斂段 LLM 判定）。

四類訊號與資料源：
  ①review_residue      `<repo>/.review/*.md` 未閉 findings（狀態非 terminal）計數＋指針；
                        terminal 值域與 review_ledger.py 同源（resolved/verified/closed）
  ②liveness_anomaly    `<repo>/.delegate-bridge/jobs.json` 近 N 天四桶計數：
                        auth-failed／interrupted（status 直配）；rate-limited（終態失敗
                        且 errorExcerpt 命中 rate-limit 簽名）；terminal-other（其餘
                        終態失敗——**未驗 sink**，不得冒稱 sink-missing（codex
                        151-C4：generic 失敗掛 sink 名會把收斂段指向錯的問題）；
                        精確 sink 三步 face 需 jsonl replay，見 agent_liveness_sweep.py）
  ③cross_arc_recurrence 同檔案被 ≥3 次 commit 觸及（`git log --since` 掃）churn 計數
  ④budget_overspend    session-journal（`<repo>/.agent-tmp/session-journal.md`）的
                        revert／stall 關鍵字行計數（全檔掃——journal 非窗口性資料）

用法：
  uv run python scripts/improvement_signals.py --repo . --since 7
  uv run python scripts/improvement_signals.py --repo . --since 7 --kpi .agents/improvement-kpi.jsonl

exit 0＝掃描完成（訊號源缺席不算錯——計數 0＋notes 記錄，fail-soft 機械面）。
"""
import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

CAP = 20  # 每類訊號指針硬上限（capped 收斂輸入——禁貼全文）
EXCERPT = 120  # 單指針截斷長度
RECURRENCE_THRESHOLD = 3  # 跨弧重現：同檔 commit 數門檻

REVIEW_DIR = ".review"
JOBS_RELPATH = ".delegate-bridge/jobs.json"
JOURNAL_RELPATH = ".agent-tmp/session-journal.md"

# 與 skills/post-build/scripts/review_ledger.py TERMINAL_STATUSES 同值域（單一源在彼，
# 此處不 import 非 package 腳本——改動時兩處對照）
FINDING_TERMINAL = ("resolved", "verified", "closed")
RATE_RE = re.compile(r"rate.?limit|429|quota|too many requests|overloaded|capacity", re.IGNORECASE)
REVERT_RE = re.compile(r"\brevert|rolled back|回滾|回退|撤銷", re.IGNORECASE)
STALL_RE = re.compile(r"\bstall|stuck|卡住|停滯|無進展", re.IGNORECASE)


def _clip(text: str, width: int = EXCERPT) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:width] + ("…" if len(text) > width else "")


# ---------- ①review 殘留 ----------

def _table_rows_without_fences(text: str) -> list[list[str]]:
    """抓 markdown 表格資料列（``` 圍欄內跳過——格式範例非資料，同 review_ledger F-6）。

    回傳每列的 cell 清單（含表頭列）。
    """
    rows: list[list[str]] = []
    fenced = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if fenced or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and set(cells[0]) <= {"-", ":", " "}:
            continue  # 分隔列
        rows.append(cells)
    return rows


def scan_review_residue(repo: Path) -> dict:
    review_dir = repo / REVIEW_DIR
    out: dict = {"count": 0, "pointers": [], "scanned_files": 0}
    if not review_dir.is_dir():
        out["note"] = f"{REVIEW_DIR}/ 不存在（零殘留常態）"
        return out
    for md in sorted(review_dir.glob("*.md")):
        rows = _table_rows_without_fences(md.read_text(errors="replace"))
        # 表頭判定：cell 完整等於「狀態」——子字串比對會吃到資料列內容（舊帳本實證：
        # 「A1 對帳狀態欄」）；無此欄的 legacy 帳本＝機械不可分類，跳過（arc 多已收斂）
        header_idx = next(
            (i for i, cells in enumerate(rows) if any(c == "狀態" for c in cells)), None
        )
        if header_idx is None:
            continue
        header = rows[header_idx]
        st_i = next(i for i, c in enumerate(header) if c == "狀態")
        id_i = next((i for i, c in enumerate(header) if c.lower() in ("id", "#")), None)
        q_i = next(
            (i for i, c in enumerate(header) if c in ("問題", "發現", "內容")),
            None,
        )
        out["scanned_files"] += 1
        for cells in rows[header_idx + 1 :]:
            if len(cells) <= st_i:
                continue
            status = cells[st_i].strip()
            if status.startswith(FINDING_TERMINAL):
                continue
            fid = cells[id_i].strip() if id_i is not None and id_i < len(cells) else "—"
            body = cells[q_i].strip() if q_i is not None and q_i < len(cells) else status
            out["pointers"].append(f"{md.name}::{_clip(fid, 24)} {_clip(body)}")
    out["count"] = len(out["pointers"])
    out["pointers"] = out["pointers"][:CAP]
    return out


# ---------- ②liveness 異常 ----------

def _job_ts(entry: dict) -> _dt.datetime | None:
    raw = entry.get("timestamp")
    if not isinstance(raw, str):
        return None
    try:
        return _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def scan_liveness(repo: Path, since_days: int, now: _dt.datetime) -> dict:
    kinds = ["terminal-other", "rate-limited", "auth-failed", "interrupted"]
    out: dict = {"count": 0, "by_kind": {k: 0 for k in kinds}, "pointers": []}
    jobs_path = repo / JOBS_RELPATH
    if not jobs_path.exists():
        out["note"] = f"{JOBS_RELPATH} 不存在"
        return out
    try:
        entries = json.loads(jobs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        out["note"] = f"jobs.json 讀取失敗：{exc}"
        return out
    if not isinstance(entries, list):
        out["note"] = "jobs.json 非陣列"
        return out
    cutoff = now - _dt.timedelta(days=since_days)
    undated = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        ts = _job_ts(entry)
        if ts is None:
            undated += 1
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=_dt.UTC)
        if ts < cutoff:
            continue
        status = str(entry.get("status") or "")
        excerpt = str(entry.get("errorExcerpt") or "")
        if status == "auth-failed":
            kind = "auth-failed"
        elif status == "interrupted":
            kind = "interrupted"
        elif status in ("running", "completed"):
            continue  # 非 anomaly（completed 但 sink 未驗＝jsonl face，非 index 面——見 docstring）
        elif RATE_RE.search(excerpt):
            kind = "rate-limited"
        else:
            kind = "terminal-other"  # 未驗 sink——不得冒稱 sink-missing（codex 151-C4）
        out["by_kind"][kind] += 1
        out["pointers"].append(f"{entry.get('id', '?')} [{status}→{kind}] {_clip(excerpt)}")
    out["count"] = sum(out["by_kind"].values())
    out["pointers"] = out["pointers"][:CAP]
    if undated:
        out["note"] = f"{undated} 筆無 timestamp 未計入窗口"
    return out


# ---------- ③跨弧重現 ----------

def scan_recurrence(repo: Path, since_days: int) -> dict:
    out: dict = {"count": 0, "pointers": [], "threshold": RECURRENCE_THRESHOLD}
    since = (_dt.datetime.now(_dt.UTC).date() - _dt.timedelta(days=since_days)).isoformat()
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "core.quotepath=false",  # 非 ASCII 路徑保留原樣（指針可讀）
            "log",
            f"--since={since}",
            "--name-only",
            "--pretty=format:",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        out["note"] = f"git log 失敗：{_clip(proc.stderr)}"
        return out
    counts: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        path = line.strip()
        if path:
            counts[path] = counts.get(path, 0) + 1
    hot = [(p, n) for p, n in counts.items() if n >= RECURRENCE_THRESHOLD]
    hot.sort(key=lambda x: (-x[1], x[0]))
    out["count"] = len(hot)
    out["pointers"] = [{"path": p, "commits": n} for p, n in hot[:CAP]]
    return out


# ---------- ④預算超支 ----------

def scan_budget(repo: Path) -> dict:
    out: dict = {"count": 0, "by_kind": {"revert": 0, "stall": 0}, "pointers": []}
    journal = repo / JOURNAL_RELPATH
    if not journal.exists():
        out["note"] = f"{JOURNAL_RELPATH} 不存在（本 WT 無 journal 常態）"
        return out
    for line_no, line in enumerate(journal.read_text(errors="replace").splitlines(), 1):
        hit = bool(REVERT_RE.search(line))
        stall = bool(STALL_RE.search(line))
        if hit:
            out["by_kind"]["revert"] += 1
        if stall:
            out["by_kind"]["stall"] += 1
        if hit or stall:
            kinds = [k for k, on in (("revert", hit), ("stall", stall)) if on]
            out["pointers"].append(f"L{line_no}[{'/'.join(kinds)}] {_clip(line, 100)}")
    out["count"] = sum(out["by_kind"].values())
    out["pointers"] = out["pointers"][:CAP]
    return out


# ---------- KPI 彙總（reviewed→opened→settled，per source） ----------

def aggregate_kpi(kpi_path: Path) -> dict:
    events = ("reviewed", "opened", "settled", "dismissed")
    out: dict = {"per_source": {}, "total": dict.fromkeys(events, 0)}
    if not kpi_path.exists():
        out["note"] = "KPI 檔不存在（漏斗零事件常態）"
        return out
    malformed = 0
    for line in kpi_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        source = str(rec.get("source") or "-")
        event = str(rec.get("event") or "")
        if event not in out["total"]:
            continue
        bucket = out["per_source"].setdefault(source, dict.fromkeys(events, 0))
        bucket[event] += 1
        out["total"][event] += 1
    if malformed:
        out["note"] = f"{malformed} 行 malformed 跳過"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="repo root（訊號源皆相對此根）")
    ap.add_argument("--since", type=int, default=7, help="窗口天數（liveness／churn 用；預設 7）")
    ap.add_argument("--kpi", type=Path, default=None, help="improvement-kpi.jsonl 路徑（給定則附 KPI 彙總）")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    now = _dt.datetime.now(_dt.UTC)
    report = {
        "repo": str(repo),
        "since_days": args.since,
        "generated_at": now.isoformat(timespec="seconds"),
        "signals": {
            "review_residue": scan_review_residue(repo),
            "liveness_anomaly": scan_liveness(repo, args.since, now),
            "cross_arc_recurrence": scan_recurrence(repo, args.since),
            "budget_overspend": scan_budget(repo),
        },
    }
    counts = {name: sig.get("count", 0) for name, sig in report["signals"].items()}
    report["any_signal"] = any(counts.values())
    report["admission_gate"] = {
        "mechanical_any_signal": report["any_signal"],
        "semantic_actionable": "由 post-build improvement 收斂段 LLM 判定——本掃描器不判語義",
    }
    if args.kpi is not None:
        report["kpi"] = aggregate_kpi(args.kpi)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
