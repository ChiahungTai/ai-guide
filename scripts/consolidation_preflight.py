#!/usr/bin/env python3
"""AIR-127 memory 收斂波前置檢查——唯讀 tri-state preflight。

把 memory-audit 波前三步的偵測面包成一支腳本——順序不變量從散文變機械。
包既有檢查（不加新偵測邏輯）：

1. 池 delta gate（AIR-93）：import scripts/reconcile_memory_pool.py 的
   reconcile_pool——pool working tree delta 即 flag。單一狀態源：消費端
   （T4-1）直接吃本腳本 --json 的 entries，禁重跑 porcelain 取第二份。
2. wave marker（AIR-49 波前①）：`<pool>/_wave-in-progress` 在場＝上波
   中斷未收斂＝停波待處置（禁自動整池 reset——marker 只證明有未完成波，
   不證明當前差異屬於它）。
3. 活躍 writer mtime（波前散文 age 訊號）：dirty 檔任一距今 <30 分鐘＝
   活躍 writer 在場（停波不覆寫——並行 writer 撞波防護）；全部 ≥30 分鐘
   ＝無活躍 writer 訊號（T4-1 異常篩——語義判斷——之後才可能走流入快照，
   不在本層）。

verdict（AIR-127 已決策勿重辯①）：
- exit 0＝clean 開波（含 not_governed——native 寫入合法，與 reconciler
  同語義；skill 散文：「exit 0（clean/not_governed）→ 開波初始化後起跑」）
- exit 1＝無法判定停波（fail-closed：git 缺席／pool 無 git／governance
  marker malformed／repo root 不存在——基礎設施壞時 dirty 清單不可信，
  蓋過 dirty）
- exit 2＝dirty 附清單（pool delta entries／wave marker 在場）

寫操作（T4-1 逐檔處置／流入快照 commit／開波初始化寫 marker／波後差異
處置）不在此層——本腳本唯讀，與 reconciler 同紀律（GIT_OPTIONAL_LOCKS=0
由 reconciler 內建）。

用法：uv run python scripts/consolidation_preflight.py <repo-root> [--json]
"""

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any  # JSON payload 邊界（動態形狀，序列化前無法收斂型別）

_RP_PATH = Path(__file__).resolve().parent / "reconcile_memory_pool.py"
_spec = importlib.util.spec_from_file_location("reconcile_memory_pool", _RP_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load reconciler from {_RP_PATH}")
_rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rp)

WAVE_MARKER = "_wave-in-progress"
# memory-audit 波前散文：dirty 檔「任一 < 30 分鐘」（活躍 writer 在場）→ 停波
ACTIVE_WRITER_WINDOW_MIN = 30

_VERDICT_NAMES = {0: "clean", 1: "undetermined", 2: "dirty"}


def _resolve_entry_file(pool: Path, repo_root: Path, entry_path: str) -> Path | None:
    """porcelain path（相對池 git root）→ 池內實檔案。

    候選序：pool-relative（nested layout——entry.path 已相對 pool）→
    repo-root-relative（flat layout——entry.path 帶 .agents/memory 前綴）；
    兩者皆不存在＝deleted delta，無 mtime 可查。
    """
    for candidate in (pool / entry_path, repo_root / entry_path):
        if candidate.exists():
            return candidate
    return None


def _age_of(path: Path | None) -> tuple[str, float | None]:
    """age 訊號分類（波前散文 age 檢查的機械化）：<30 分鐘＝active。"""
    if path is None:
        return "no-file", None
    age_min = (time.time() - path.stat().st_mtime) / 60
    category = "active" if age_min < ACTIVE_WRITER_WINDOW_MIN else "stale"
    return category, round(age_min, 1)


def check_pool_delta(repo_root: Path) -> dict[str, Any]:
    """池 delta gate（AIR-93）：唯一狀態源＝reconcile_pool，不重跑 porcelain。"""
    pool = repo_root / _rp.POOL_REL
    try:
        result = _rp.reconcile_pool(repo_root)
    except _rp.ReconcileError as e:
        return {"status": "error", "entries": [], "detail": str(e)}
    entries: list[dict[str, Any]] = []
    for e in result.entries:
        category, age_min = _age_of(_resolve_entry_file(pool, repo_root, e.path))
        entries.append(
            {
                "code": e.code,
                "path": e.path,
                "age_category": category,
                "age_minutes": age_min,
            }
        )
    return {"status": result.status, "entries": entries, "detail": result.detail}


def check_wave_marker(repo_root: Path) -> dict[str, Any]:
    """wave marker 在場檢查（AIR-49 波前①）——存在性事實，內容不解析格式。"""
    marker = repo_root / _rp.POOL_REL / WAVE_MARKER
    if not marker.exists() and not marker.is_symlink():
        return {"present": False, "detail": f"no wave marker at {marker}"}
    try:
        head = marker.read_text(encoding="utf-8")[:200].strip()
        detail = (
            f"wave marker present at {marker}——上波中斷未收斂"
            f"（內容前 200 chars，供 baseline 三方對照：{head}）"
        )
    except OSError as e:
        detail = f"wave marker present at {marker} but unreadable（baseline 不可考）：{e}"
    return {"present": True, "detail": detail}


def _active_writer_summary(delta: dict[str, Any]) -> dict[str, Any]:
    if delta["status"] != "dirty":
        return {
            "any_active": None,
            "window_minutes": ACTIVE_WRITER_WINDOW_MIN,
            "detail": "no pool delta——age 訊號不適用",
        }
    # AIR-127 codex finding：deleted/no-file entry 無 mtime——age 未知不可折成
    # 「非活躍」（可能一秒前被 active writer 刪除）；保守計入 active，只有
    # 「每筆都有 age 且全部 ≥30 分鐘」才允許 any_active=False（可流入快照）。
    any_active = any(
        e["age_category"] != "stale" for e in delta["entries"]
    )
    unknown = sum(e["age_category"] == "no-file" for e in delta["entries"])
    detail = (
        "任一 dirty 檔 <30 分鐘——活躍 writer 在場，停波不覆寫"
        if any_active
        else "dirty 檔全部 ≥30 分鐘——無活躍 writer 訊號（T4-1 後才可能流入快照）"
    )
    if unknown:
        detail += f"；{unknown} 筆 deleted delta 無 mtime＝age 未知，保守視為活躍"
    return {
        "any_active": any_active,
        "window_minutes": ACTIVE_WRITER_WINDOW_MIN,
        "detail": detail,
    }


def run_preflight(repo_root: Path) -> tuple[int, dict[str, Any]]:
    """跑波前檢查並合成 verdict；1 蓋過 2 蓋過 0（fail-closed 優先）。"""
    payload: dict[str, Any] = {
        "repo": str(repo_root),
        "verdict_name": None,
        "checks": {},
    }
    if not repo_root.is_dir():
        # reconciler 對不存在 root 會回 not_governed（=0）——verdict 0 意味
        # 開波，拼錯路徑不得換取開波（fail-closed）
        payload["checks"]["pool_delta"] = {
            "status": "error",
            "entries": [],
            "detail": f"repo root not a directory: {repo_root}",
        }
        payload["checks"]["wave_marker"] = {"present": False, "detail": "skipped"}
        payload["checks"]["active_writer"] = _active_writer_summary(
            payload["checks"]["pool_delta"]
        )
        payload["verdict"] = 1
        payload["verdict_name"] = _VERDICT_NAMES[1]
        return 1, payload

    delta = check_pool_delta(repo_root)
    marker = check_wave_marker(repo_root)
    active = _active_writer_summary(delta)
    payload["checks"] = {
        "pool_delta": delta,
        "wave_marker": marker,
        "active_writer": active,
    }

    if delta["status"] == "error":
        verdict = 1  # 無法判定——dirty 清單在壞基礎設施上不可信
    elif delta["status"] == "dirty" or marker["present"]:
        verdict = 2
    else:
        verdict = 0
    payload["verdict"] = verdict
    payload["verdict_name"] = _VERDICT_NAMES[verdict]
    return verdict, payload


def _print_human(verdict: int, payload: dict[str, Any]) -> None:
    checks = payload["checks"]
    delta = checks["pool_delta"]
    marker = checks["wave_marker"]
    active = checks["active_writer"]
    if verdict == 0:
        print(
            f"[OK] consolidation_preflight: verdict=clean——開波"
            f"（pool_delta={delta['status']}、wave marker 不在場）"
        )
        print(f"  {delta['detail']}")
        return
    if verdict == 1:
        print(
            "[FAIL] consolidation_preflight: verdict=undetermined——停波"
            "（fail-closed：無法證明池狀態≠池乾淨）"
        )
        print(f"  pool_delta: {delta['status']}——{delta['detail']}")
        if marker["present"]:
            print(f"  wave_marker: {marker['detail']}")
        return
    n = len(delta["entries"])
    print(
        f"[FAIL] consolidation_preflight: verdict=dirty——停波"
        f"（pool delta {n} 筆待處置；wave marker {'在場' if marker['present'] else '不在場'}）"
    )
    for e in delta["entries"]:
        if e["age_category"] == "no-file":
            age_note = "age 不可得（deleted）"
        else:
            age_note = f"age={e['age_minutes']}min {e['age_category']}"
        print(f"  {e['code']} {e['path']} ({age_note})")
    if marker["present"]:
        print(f"  wave_marker: {marker['detail']}")
    print(f"  active_writer: {active['detail']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AIR-127 memory wave-front read-only preflight (tri-state)"
    )
    parser.add_argument(
        "repo", type=Path, help="repo root containing .agents/memory"
    )
    parser.add_argument(
        "--json", action="store_true", help="machine-readable payload on stdout"
    )
    args = parser.parse_args(argv)

    verdict, payload = run_preflight(args.repo)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        _print_human(verdict, payload)
    return verdict


if __name__ == "__main__":
    sys.exit(main())
