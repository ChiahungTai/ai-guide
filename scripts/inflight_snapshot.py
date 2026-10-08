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
2. **session 發現（seam）**：`session_discovery.collect_rows(live_only=
   True)`（AIR-254.1／AIR-277——本檔不直查源，session store 讀取單一
   choke point 在 seam；coverage=zcode-only 隨 rows 轉發至輸出）。--live
   過濾＝`liveness == "live"` 且 `session_id` 以 `sess_` 開頭（非 sess_
   前綴雜訊自然排除）。**live＝未封存，非存活觀測**（沿用 seam caveat；
   下游解讀對照 age_min）。欄位：session_id 前 13 碼／name（←seam
   label，sidecar 優先合併）／workspace 尾段／status／age_min
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

sys.path.insert(
    0, str(Path(__file__).resolve().parent)
)  # scripts/ 非 package——同目錄 seam import（AIR-254.1）

from session_discovery import collect_rows

BRIDGE_JOBS_DIR = Path(".delegate-bridge") / "jobs"
COMPLETED_STATUSES = frozenset({"completed", "turn.completed"})


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
# 路 2：session 發現（經 seam——AIR-254.1）
# ---------------------------------------------------------------------------


def collect_scbus_sessions(
    run: Callable[..., str] | None = None, *, sidecar: Path | None = None
) -> dict[str, Any]:
    """seam `collect_rows(live_only=True)`——live＋`sess_` 過濾在 seam 做。

    欄位映射語義不變：session 前 13 碼／name←seam label（sidecar 優先
    合併）／workspace 尾段／status／age_min。coverage 鍵自 seam 轉發
    （現值 zcode-only——覆蓋縮限對下游可見，AIR-281①）。`run` 參數＝
    遺留槽：AIR-277 換源後 seam 直讀 session store、**值被忽略**
    （seam `collect_rows` 為既有消費端呼叫相容保留；注入面＝`db_path`），
    禁新依賴。
    """
    data = collect_rows(
        run if run is not None else _run_cmd, sidecar=sidecar, live_only=True
    )
    rows = []
    for row in data["rows"]:
        workspace = PurePath(str(row.get("workspace_root") or "-")).name
        rows.append(
            {
                "session": row["session_id"][:13],
                "name": row.get("label") or "-",
                "workspace": workspace or "-",
                "status": str(row.get("status") or "-"),
                "age_min": row.get("age_min"),
            }
        )
    return {
        "unavailable": False,
        "rows": rows,
        "count": len(rows),
        "registry_total": data["registry_total"],
        "coverage": data.get("coverage"),
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
    lines = ["## live sessions（harness-native seam；liveness=live 且 sess_*）"]
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
        f"- live sess_* {data['count']} 列（總列 {data['registry_total']}）｜"
        f"coverage={data.get('coverage') or '-'}——live＝未封存，非存活觀測"
        "（下游解讀對照 age_min）",
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
