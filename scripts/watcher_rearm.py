#!/usr/bin/env python3
"""watcher_rearm — bridge watcher 死亡辨識＋單次 auto-rearm（AIR-158）.

pull-only 監督閉環的收口：bridge_waiter 自己無聲死亡時（liveness.jsonl
armed 後 heartbeat 停滯、無 collected/advisory 終面），本工具掃台帳辨識
stale armed rows，對它們**重掛 watcher 一次**（liveness 記
`{"event":"rearmed","jobId","rearmedAt","pid"}`）；同 jobId 已有 rearmed
row → 只報 broken alert 不再重掛（單次、禁無限迴圈——已決策勿重辯⑤）。
bridge job 本體的 stop／重派恆不碰（處置權歸 caller——偵測與處置分離）。

分態（已決策勿重辯①）：死亡判準＝scripts/bridge_waiter.py
`watcher_death_suspect`（只消費 liveness heartbeat 軸），與 job stall
（bridge 雙軸、T4 STALLED_ADVISORY）互斥——stall 已 advisory wake 過的 job
帶 advisory 行，落 concluded 桶不重掛。

用法：
    uv run python scripts/watcher_rearm.py [--liveness-path PATH]
        [--bridge-bin PATH] [--waiter PATH] [--log PATH]

輸出：人讀行＋stdout 尾行單行 JSON（schema=watcher-rearm/1，rearmed／
broken／fresh／concluded 機械可判）；exit 0＝reporter 面（本工具的處置僅限
單次 re-arm；失敗診斷走 stderr）。
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

REARM_SCHEMA = "watcher-rearm/1"
REARMED_EVENT = "rearmed"


def _load_bridge_waiter():
    """載同目錄 bridge_waiter（非 package 腳本，importlib 路徑載入）。"""
    path = Path(__file__).resolve().parent / "bridge_waiter.py"
    spec = importlib.util.spec_from_file_location("_bridge_waiter_for_rearm", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_bridge_waiter()


def scan_plan(rows: list[dict], now: datetime) -> dict[str, list[str]]:
    """純函式：liveness rows → 處置計畫（rearm／broken／fresh／concluded）。

    分桶判準：
    - concluded：有 collected（監督完成）或 advisory（stall 已 wake 交辦）
    - rearm：watcher_death_suspect 命中且無 rearmed row
    - broken：death suspect 且已有 rearmed row——只報警不再重掛
    - fresh：heartbeat 尚新（沉默是成功）
    """
    faces: dict[str, list[dict]] = {}
    for row in rows:
        job_id = row.get("jobId")
        if not isinstance(job_id, str) or not job_id:
            continue
        faces.setdefault(job_id, []).append(row)
    plan: dict[str, list[str]] = {
        "rearm": [],
        "broken": [],
        "fresh": [],
        "concluded": [],
    }
    for job_id in sorted(faces):
        rows_for = faces[job_id]
        if any(r.get("event") in _mod.LIVENESS_CONCLUDED_EVENTS for r in rows_for):
            plan["concluded"].append(job_id)
        elif not _mod.watcher_death_suspect(rows_for, now):
            plan["fresh"].append(job_id)
        elif any(r.get("event") == REARMED_EVENT for r in rows_for):
            plan["broken"].append(job_id)
        else:
            plan["rearm"].append(job_id)
    return plan


def execute_plan(
    plan: dict[str, list[str]],
    *,
    liveness_path: Path,
    spawn: Callable[[str], int],
    err,
) -> list[str]:
    """執行 rearm 桶：逐 job spawn watcher＋append rearmed row；回實際重掛清單。

    broken 桶不在此處置（單次保證：rearmed row 在案即永不二度重掛）。
    """
    rearmed: list[str] = []
    for job_id in plan["rearm"]:
        try:
            pid = spawn(job_id)
        except OSError as exc:
            _mod._emit(err, f"[watcher_rearm] spawn 失敗（{job_id}）：{exc}")
            continue
        _mod._liveness_append(
            liveness_path,
            {
                "event": REARMED_EVENT,
                "jobId": job_id,
                "rearmedAt": datetime.now().astimezone().isoformat(),
                "pid": pid,
            },
            err,
        )
        rearmed.append(job_id)
    return rearmed


def build_spawner(
    waiter: Path, bridge_bin: str, liveness_path: Path, log_path: Path
) -> Callable[[str], int]:
    """spawn bridge_waiter 背景 watcher（detached；輸出落 log append）。"""

    def spawn(job_id: str) -> int:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(waiter),
                    job_id,
                    "--bridge-bin",
                    bridge_bin,
                    "--liveness-path",
                    str(liveness_path),
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        return proc.pid

    return spawn


def main(
    argv: list[str] | None = None,
    *,
    spawn: Callable[[str], int] | None = None,
    now: datetime | None = None,
) -> int:
    repo_scripts = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        prog="watcher_rearm",
        description=(
            "bridge watcher 死亡辨識＋單次 auto-rearm（AIR-158——掃 liveness"
            " 台帳；rearmed 過的 job 只報警不再重掛）"
        ),
    )
    parser.add_argument(
        "--liveness-path",
        default=None,
        metavar="PATH",
        help="liveness 台帳路徑（預設 <cwd repo>/.agent-tmp/liveness.jsonl）",
    )
    parser.add_argument(
        "--bridge-bin",
        default=os.environ.get("DELEGATE_BRIDGE_BIN", "delegate-bridge"),
        metavar="PATH",
        help="delegate-bridge CLI 路徑（傳給重掛的 watcher）",
    )
    parser.add_argument(
        "--waiter",
        default=str(repo_scripts / "bridge_waiter.py"),
        metavar="PATH",
        help="bridge_waiter 腳本路徑（預設同目錄）",
    )
    parser.add_argument(
        "--log",
        default=None,
        metavar="PATH",
        help="重掛 watcher 的輸出 log（預設 <台帳同目錄>/watcher-rearm.log）",
    )
    args = parser.parse_args(argv)

    liveness_path = (
        Path(args.liveness_path)
        if args.liveness_path
        else _mod._default_liveness_path()
    )
    text = ""
    try:
        text = liveness_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass  # 缺台帳＝無 armed rows——照 reporter 面輸出空計畫
    plan = scan_plan(_mod.parse_liveness_rows(text), now or datetime.now().astimezone())
    if spawn is None:
        log_path = (
            Path(args.log) if args.log else liveness_path.parent / "watcher-rearm.log"
        )
        spawn = build_spawner(
            Path(args.waiter), args.bridge_bin, liveness_path, log_path
        )
    out = sys.stdout
    rearmed = execute_plan(
        plan, liveness_path=liveness_path, spawn=spawn, err=sys.stderr
    )
    for job_id in rearmed:
        _mod._emit(out, f"[watcher_rearm] REARMED: {job_id}——watcher 已單次重掛")
    for job_id in plan["broken"]:
        _mod._emit(
            out,
            f"[watcher_rearm] BROKEN: {job_id}——watcher 疑似死亡且已 re-arm 過，"
            "不再重掛（人工介入：查 registry／手動 arm bridge_waiter）",
        )
    _mod._emit(
        out,
        json.dumps(
            {
                "schema": REARM_SCHEMA,
                "tool": "watcher_rearm",
                "liveness": str(liveness_path),
                "rearmed": rearmed,
                "broken": plan["broken"],
                "fresh": plan["fresh"],
                "concluded": plan["concluded"],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
