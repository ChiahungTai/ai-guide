#!/usr/bin/env python3
"""K1 POC——rollout「model I/O → 及時 append」採樣器（AIR-149 S1 驗證策略）.

用法：
    uv run python poc/poc_three_surface.py <taskId> [--window SEC] [--interval SEC]

對 `~/.zcode/cli/rollout/model-io-<taskId>.jsonl` 定時採樣 size/mtime，
輸出 append 事件時間軸＋判定（appending／silent）。K1 的可證偽命題：
「工作中 subagent 的 rollout 於 model I/O 期持續 append」——採樣窗內
零 append 即凍結判準的 rollout 面失效訊號（pivot 依據，EP kill criteria K1）。

邊界（reviewer F-5）：K1 的「誘導純推理 subagent＋併行採樣」全跑需 spawn
授權（worker 禁再委派），與 TC-4 同場景挪 S4 dogfood；本 POC 實跑證據取自
live subagent session（採樣窗與其他工具呼叫重疊——token 生成期即 model
I/O 期），驗證 append 及時性；「thinking token 亦寫 rollout」的獨立分離
驗證留 S4 誘導跑。
"""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

ROLLOUT_ROOT = Path.home() / ".zcode" / "cli" / "rollout"


def sample(rollout: Path) -> tuple[int, int]:
    stat = rollout.stat()
    return stat.st_size, stat.st_mtime_ns


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("task_id", help="subagent taskId（childSessionId 全形）")
    parser.add_argument(
        "--window", type=float, default=30.0, help="採樣窗秒（預設 30）"
    )
    parser.add_argument(
        "--interval", type=float, default=2.0, help="採樣間隔秒（預設 2）"
    )
    args = parser.parse_args()

    rollout = ROLLOUT_ROOT / f"model-io-{args.task_id}.jsonl"
    if not rollout.is_file():
        print(f"FAIL rollout 缺席：{rollout}", file=__import__("sys").stderr)
        return 1
    print(f"sampling {rollout}")
    print(f"window={args.window}s interval={args.interval}s")
    start = time.monotonic()
    events: list[dict] = []
    last_size, last_mtime_ns = sample(rollout)
    print(f"t=+0.0s size={last_size} mtime_ns={last_mtime_ns}")
    while time.monotonic() - start < args.window:
        time.sleep(args.interval)
        size, mtime_ns = sample(rollout)
        elapsed = time.monotonic() - start
        if size != last_size:
            events.append(
                {
                    "t": round(elapsed, 1),
                    "from": last_size,
                    "to": size,
                    "delta": size - last_size,
                }
            )
            print(f"t=+{elapsed:.1f}s APPEND +{size - last_size}B size={size}")
        last_size, last_mtime_ns = size, mtime_ns
    verdict = "appending" if events else "silent"
    result = {
        "poc": "poc_three_surface",
        "taskId": args.task_id,
        "windowS": args.window,
        "sampledAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
        "appends": len(events),
        "events": events,
        "verdict": verdict,
        "k1-reading": (
            "rollout 於採樣窗內持續 append——model I/O 即時落盤，"
            "凍結判準的 rollout 面有效"
            if events
            else "採樣窗內零 append——"
            "若發生於工作中 subagent 即 K1 kill observation（pivot 訊號）"
        ),
        "scope-note": "live session 採樣；純推理誘導全跑挪 S4（spawn 授權邊界）",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
