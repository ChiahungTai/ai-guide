#!/usr/bin/env python3
"""inflight_snapshot — 弧結算／handoff「在飛總表」機械生成 helper（AIR-168 AC#3）.

一句話：弧結算／handoff 時的「在飛總表」禁手抄——本 helper 查三路現值輸出
markdown 表（`--json` 輸出同構 JSON），表頭帶生成時間。每路獨立 try/except：
一路失敗標 `unavailable` 續跑其他路，exit 恆 0；查不到的源標 unavailable
而非空白（禁手抄契約：全部欄位來自指令現值）。

資料源三路
----
1. **bridge jobs**：cwd 的 `.delegate-bridge/jobs/*.jsonl`，每檔取最後一行
   （非空行）parse：jobId（檔名 stem）／status／model／timestamp。status
   抽取＝巢狀結構 BFS 找第一個 `status` 鍵，無則退 `type` 值
   （`turn.completed` 視同 completed）；status 非 completed＝在飛。model＝
   BFS 找 `model` 鍵，無則 `-`。timestamp＝`recorded_at`（µs epoch）轉
   ISO，無則檔案 mtime。壞 JSONL 行標 `parse-error` 續跑；無 jobs 目錄＝
   `skipped`（非錯）。
2. **scbus sessions**：`scbus list`（JSON）——過濾 `observed_liveness ==
   "live"` 且 `session_id` 以 `sess_` 開頭（排除 scbus-ext-* 幽靈與雜訊）。
   欄位：session_id 前 13 碼／name／workspace 尾段／status／age_min
   （`age` 秒 → 分；缺 `age` 時以 `last_seen_us` 對 now 推算）。
3. **git 面**：`git worktree list --porcelain`（非 primary 的 WT）＋
   `git branch --list 'air-*'`＋`git status --porcelain`（dirty 檔計數）。
   三個子命令各自容錯，一個失敗只標該區段 unavailable。

用法
----
    uv run python scripts/inflight_snapshot.py [--json]

exit：恆 0（三路獨立容錯；失敗在輸出內標 `unavailable` 大聲回報，不擋
呼叫鏈——弧結算／handoff 的總表生成不應因單一源缺席而中斷）。
"""

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import Any

BRIDGE_JOBS_DIR = Path(".delegate-bridge") / "jobs"
COMPLETED_STATUSES = frozenset({"completed", "turn.completed"})
LIVE_VALUE = "live"
SESS_PREFIX = "sess_"


def _run_cmd(cmd: list[str], *, cwd: Path | None = None) -> str:
    """跑外部命令回 stdout；非零 exit／缺席＝例外（交呼叫端容錯）。"""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
    return proc.stdout


def _find_first(obj: Any, key: str) -> Any:
    """巢狀 dict/list 結構找第一個 `key` 的值（深度優先，找不到回 None）。"""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = _find_first(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_first(item, key)
            if found is not None:
                return found
    return None


def _to_iso(epoch_s: float) -> str:
    return (
        datetime.fromtimestamp(epoch_s, tz=UTC)
        .astimezone()
        .isoformat(timespec="seconds")
    )


def _now_iso() -> str:
    return datetime.now(tz=UTC).astimezone().isoformat(timespec="seconds")


def _unavailable(exc: Exception) -> dict[str, Any]:
    return {"unavailable": True, "error": f"{type(exc).__name__}: {exc}"}


# ---------------------------------------------------------------------------
# 路 1：bridge jobs
# ---------------------------------------------------------------------------


def _parse_bridge_row(job_id: str, raw_line: str, mtime: float) -> dict[str, Any]:
    """最後一行 JSON → job 欄位；壞行標 parse-error（呼叫端續跑）。"""
    base = {"job_id": job_id, "model": "-", "timestamp": _to_iso(mtime)}
    try:
        record = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        return {**base, "status": "parse-error", "error": str(exc)}
    status_value = _find_first(record, "status")
    if isinstance(status_value, str) and status_value:
        status = status_value
    else:
        type_value = record.get("type") if isinstance(record, dict) else None
        status = str(type_value) if type_value else "unknown"
    model_value = _find_first(record, "model")
    model = model_value if isinstance(model_value, str) and model_value else "-"
    recorded_at = _find_first(record, "recorded_at")
    if isinstance(recorded_at, (int, float)):
        base["timestamp"] = _to_iso(recorded_at / 1_000_000)
    return {**base, "status": status, "model": model}


def collect_bridge_jobs(jobs_dir: Path) -> dict[str, Any]:
    """掃 `*.jsonl` 最後一行；status 非 completed＝在飛。無目錄＝skip。"""
    out: dict[str, Any] = {
        "unavailable": False,
        "jobs_dir": str(jobs_dir),
        "in_flight": [],
        "completed": 0,
        "total": 0,
        "parse_errors": 0,
    }
    if not jobs_dir.is_dir():
        out["skipped"] = True
        out["note"] = f"jobs 目錄不存在（skip）：{jobs_dir}"
        return out
    for path in sorted(jobs_dir.glob("*.jsonl")):
        out["total"] += 1
        try:
            lines = [
                ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
            ]
            mtime = path.stat().st_mtime
        except OSError as exc:
            out["in_flight"].append(
                {
                    "job_id": path.stem,
                    "status": "parse-error",
                    "model": "-",
                    "timestamp": "-",
                    "error": str(exc),
                }
            )
            out["parse_errors"] += 1
            continue
        if not lines:
            out["in_flight"].append(
                {
                    "job_id": path.stem,
                    "status": "empty",
                    "model": "-",
                    "timestamp": _to_iso(mtime),
                    "error": "檔案無非空行",
                }
            )
            continue
        row = _parse_bridge_row(path.stem, lines[-1], mtime)
        if row["status"] == "parse-error":
            out["parse_errors"] += 1
        if row["status"] not in COMPLETED_STATUSES:
            out["in_flight"].append(row)
        else:
            out["completed"] += 1
    return out


# ---------------------------------------------------------------------------
# 路 2：scbus sessions
# ---------------------------------------------------------------------------


def collect_scbus_sessions(run: Callable[..., str] | None = None) -> dict[str, Any]:
    """`scbus list` 過濾 live＋`sess_` 前綴；幽靈與雜訊排除。"""
    runner = run if run is not None else _run_cmd
    payload = json.loads(runner(["scbus", "list"]))
    sessions = payload["sessions"]
    rows = []
    for session in sessions:
        if not isinstance(session, dict):
            continue
        sid = str(session.get("session_id") or "")
        if not sid.startswith(SESS_PREFIX):
            continue
        if session.get("observed_liveness") != LIVE_VALUE:
            continue
        age = session.get("age")
        if not isinstance(age, (int, float)):
            last_seen = session.get("last_seen_us")
            age = (
                datetime.now(tz=UTC).timestamp() - last_seen / 1_000_000
                if isinstance(last_seen, (int, float))
                else -1.0
            )
        workspace = PurePath(str(session.get("workspace_root") or "-")).name
        rows.append(
            {
                "session": sid[:13],
                "name": session.get("name") or "-",
                "workspace": workspace or "-",
                "status": str(session.get("status") or "-"),
                "age_min": round(age / 60)
                if isinstance(age, (int, float)) and age >= 0
                else None,
            }
        )
    return {
        "unavailable": False,
        "rows": rows,
        "count": len(rows),
        "registry_total": payload.get("count", len(sessions)),
    }


# ---------------------------------------------------------------------------
# 路 3：git 面（三子命令各自容錯）
# ---------------------------------------------------------------------------


def collect_worktrees(run: Callable[..., str] | None = None) -> dict[str, Any]:
    runner = run if run is not None else _run_cmd
    raw = runner(["git", "worktree", "list", "--porcelain"])
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        tag, _, value = line.partition(" ")
        current[tag] = value
    if current:
        entries.append(current)
    primary = entries[0].get("worktree", "-") if entries else "-"
    rows = []
    for entry in entries[1:]:
        branch_ref = entry.get("branch", "")
        branch = branch_ref.removeprefix("refs/heads/") if branch_ref else None
        rows.append(
            {"path": entry.get("worktree", "-"), "branch": branch or "(detached)"}
        )
    return {"unavailable": False, "primary": primary, "rows": rows}


def collect_card_branches(run: Callable[..., str] | None = None) -> dict[str, Any]:
    runner = run if run is not None else _run_cmd
    raw = runner(["git", "branch", "--list", "air-*"])
    branches = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # git marker 三態：`* `＝本 WT current、`+ `＝他 worktree checkout、空白＝無
        name = stripped.removeprefix("*").removeprefix("+").strip()
        branches.append({"name": name, "current": stripped.startswith("*")})
    return {"unavailable": False, "branches": branches}


def collect_dirty_files(run: Callable[..., str] | None = None) -> dict[str, Any]:
    runner = run if run is not None else _run_cmd
    raw = runner(["git", "status", "--porcelain"])
    count = len([ln for ln in raw.splitlines() if ln.strip()])
    return {"unavailable": False, "count": count}


# ---------------------------------------------------------------------------
# 組裝與輸出
# ---------------------------------------------------------------------------


def build_snapshot(cwd: Path, run: Callable[..., str] | None = None) -> dict[str, Any]:
    """三路現值組裝；每路獨立 try/except——一路失敗標 unavailable 續跑。"""
    snap: dict[str, Any] = {"generated_at": _now_iso()}
    try:
        snap["bridge_jobs"] = collect_bridge_jobs(cwd / BRIDGE_JOBS_DIR)
    except Exception as exc:  # ops 腳本刻意 best-effort 寬捕（pyproject BLE001 ignore）
        snap["bridge_jobs"] = _unavailable(exc)
    try:
        snap["scbus_sessions"] = collect_scbus_sessions(run=run)
    except Exception as exc:
        snap["scbus_sessions"] = _unavailable(exc)
    for name, collector in (
        ("worktrees", collect_worktrees),
        ("card_branches", collect_card_branches),
        ("dirty_files", collect_dirty_files),
    ):
        try:
            snap[name] = collector(run)
        except Exception as exc:
            snap[name] = _unavailable(exc)
    return snap


def _render_bridge_jobs(data: dict[str, Any]) -> list[str]:
    lines = ["## bridge jobs"]
    if data.get("unavailable"):
        return [lines[0], f"- unavailable：{data.get('error')}"]
    if data.get("skipped"):
        return [lines[0], f"- skip：{data.get('note')}"]
    lines += ["", "| job | status | model | timestamp |", "|---|---|---|---|"]
    for row in data["in_flight"]:
        lines.append(
            f"| {row.get('job_id', '-')} | {row.get('status', '-')} |"
            f" {row.get('model', '-')} | {row.get('timestamp', '-')} |"
        )
    lines += [
        "",
        f"- completed {data['completed']}／在飛 {len(data['in_flight'])}"
        f"（parse-error {data['parse_errors']}）／總 {data['total']}",
    ]
    return lines


def _render_scbus(data: dict[str, Any]) -> list[str]:
    lines = ["## scbus live sessions（observed_liveness=live 且 sess_*）"]
    if data.get("unavailable"):
        return [lines[0], f"- unavailable：{data.get('error')}"]
    lines += [
        "",
        "| session | name | workspace | status | age_min |",
        "|---|---|---|---|---|",
    ]
    for row in data["rows"]:
        lines.append(
            f"| {row['session']} | {row['name']} | {row['workspace']} | {row['status']}"
            f" | {row['age_min']} |"
        )
    lines += [
        "",
        f"- live sess_* {data['count']} 列（registry 總列 {data['registry_total']}）",
    ]
    return lines


def _render_worktrees(data: dict[str, Any]) -> list[str]:
    lines = ["## worktrees（非 primary）"]
    if data.get("unavailable"):
        return [lines[0], f"- unavailable：{data.get('error')}"]
    if not data["rows"]:
        return [lines[0], "- （無非 primary worktree）"]
    lines += ["", "| path | branch |", "|---|---|"]
    for row in data["rows"]:
        lines.append(f"| {row['path']} | {row['branch']} |")
    return lines


def _render_card_branches(data: dict[str, Any]) -> list[str]:
    lines = ["## card branches（air-*）"]
    if data.get("unavailable"):
        return [lines[0], f"- unavailable：{data.get('error')}"]
    if not data["branches"]:
        return [lines[0], "- （無 air-* branch）"]
    for branch in data["branches"]:
        marker = " ←current" if branch["current"] else ""
        lines.append(f"- {branch['name']}{marker}")
    return lines


def _render_dirty_files(data: dict[str, Any]) -> list[str]:
    lines = ["## dirty files"]
    if data.get("unavailable"):
        return [lines[0], f"- unavailable：{data.get('error')}"]
    return [lines[0], f"- 計數：{data['count']}"]


def render_markdown(snap: dict[str, Any]) -> str:
    """同構五區段 markdown（表頭帶生成時間）。"""
    lines = [f"# 在飛總表（inflight snapshot）— {snap['generated_at']}", ""]
    lines += _render_bridge_jobs(snap["bridge_jobs"])
    lines.append("")
    lines += _render_scbus(snap["scbus_sessions"])
    lines.append("")
    lines += _render_worktrees(snap["worktrees"])
    lines.append("")
    lines += _render_card_branches(snap["card_branches"])
    lines.append("")
    lines += _render_dirty_files(snap["dirty_files"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="弧結算／handoff 在飛總表機械生成（AIR-168 AC#3；禁手抄）"
    )
    parser.add_argument(
        "--json", action="store_true", help="輸出同構 JSON（預設 markdown）"
    )
    args = parser.parse_args(argv)
    snap = build_snapshot(Path.cwd())
    if args.json:
        print(json.dumps(snap, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(snap), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
