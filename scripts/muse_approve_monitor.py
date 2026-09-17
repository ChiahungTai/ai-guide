#!/usr/bin/env python3
"""muse approve-drift monitor（AIR-100 S-E——governance plugin approve 漂移告警）。

muse-memory-governance plugin 每次 content update 後必須重新 approve，否則
runtime 閘靜默下線（fail-open 窗口——PreToolUse 導流失效，muse 寫入直落池/
被原生接受）。真訊號＝`muse plugins inspect <id> --json` 的
`runtime_capabilities[].status == "trusted_enabled"`（`modified`＝停火待重
approve；語義源＝muse-plugins/memory-governance/README.md 運維節）。

fail-closed（D3 admission 家族）：命令失敗、JSON 解析失敗、capability 清單空、
任一 capability 非 trusted_enabled——一律告警＋非零 exit，「無法證明 trusted」
≠「trusted」。

排程：deploy/muse-approve-monitor.plist（日頻；版控源，安裝＝user 機器操作）。
用法：uv run python scripts/muse_approve_monitor.py [--plugin-id <id>]
"""

import argparse
import json
import subprocess
from collections.abc import Callable

DEFAULT_PLUGIN_ID = "muse-memory-governance"
TRUSTED_STATUS = "trusted_enabled"
ALERT_TAG = "[muse-approve-drift]"
APPROVE_POINTER = (
    "重跑 `muse plugins approve {plugin_id}`"
    "（muse-plugins/memory-governance/README.md 運維節）"
)


def evaluate(doc: object) -> tuple[bool, str]:
    """判定 inspect payload；回 (trusted, reason)。

    任一 capability 非 trusted_enabled、清單空、鍵缺失、payload 非 dict——
    都是不 trusted（fail-closed，不猜部分信任）。
    """
    if not isinstance(doc, dict):
        return False, f"payload 非 dict（got {type(doc).__name__}）"
    caps = doc.get("runtime_capabilities")
    if not isinstance(caps, list):
        return False, "runtime_capabilities 鍵缺失或非陣列"
    if not caps:
        return False, "runtime_capabilities 空——plugin 無任何 trusted capability"
    bad = [
        f"{_cap_name(c)}={c.get('status')!r}"
        for c in caps
        if not isinstance(c, dict) or c.get("status") != TRUSTED_STATUS
    ]
    if bad:
        return False, "非 trusted_enabled: " + ", ".join(bad)
    return True, f"{len(caps)} capability 全數 {TRUSTED_STATUS}"


def _cap_name(cap: object) -> str:
    if isinstance(cap, dict):
        candidate = cap.get("candidate")
        if isinstance(candidate, dict):
            return str(candidate.get("stable_id") or candidate.get("capability_id") or "?")
    return "?"


def run_monitor(
    plugin_id: str,
    runner: Callable[[list[str]], str] | None = None,
) -> tuple[int, list[str]]:
    """跑 inspect → evaluate；回 (exit_code, 輸出行)。

    runner 注入供單元測試；預設 subprocess 跑真實 muse CLI（命令失敗/缺席＝
    fail-closed 告警，非靜默綠）。
    """
    cmd = ["muse", "plugins", "inspect", plugin_id, "--json"]
    if runner is None:

        def runner(argv: list[str]) -> str:
            # timeout=30（F-15）：CLI 掛死不得讓日頻 monitor 無限等待；
            # TimeoutExpired 為 Exception 子類，落下方同一 fail-closed 面。
            done = subprocess.run(
                argv, capture_output=True, text=True, check=False, timeout=30
            )
            if done.returncode != 0:
                raise RuntimeError(
                    f"muse plugins inspect exit {done.returncode}: {done.stderr.strip()}"
                )
            return done.stdout

    try:
        stdout = runner(cmd)
        doc = json.loads(stdout)
    except Exception as exc:  # F-14：muse 壞掉場景（缺席/掛死/壞 JSON）最需告警——
        # 收斂為一律產生標籤告警行，不得無標籤 traceback 靜默漏接。
        reason = f"inspect 不可判定（fail-closed）：{exc}"
        return 1, [f"[FAIL] muse_approve_monitor: {ALERT_TAG} {reason}"]
    trusted, reason = evaluate(doc)
    if trusted:
        return 0, [f"[OK] muse_approve_monitor: {plugin_id} {reason}"]
    alert = f"governance plugin 非 trusted（{reason}）——{APPROVE_POINTER.format(plugin_id=plugin_id)}"
    return 1, [f"[FAIL] muse_approve_monitor: {ALERT_TAG} {alert}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="muse governance plugin approve-drift monitor（fail-closed）"
    )
    parser.add_argument(
        "--plugin-id", default=DEFAULT_PLUGIN_ID, help=f"預設 {DEFAULT_PLUGIN_ID}"
    )
    args = parser.parse_args(argv)
    code, lines = run_monitor(args.plugin_id)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
