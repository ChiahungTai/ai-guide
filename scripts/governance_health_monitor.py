#!/usr/bin/env python3
"""governance health monitor（AIR-116 S5——五面 governance health 排程收編）。

前形＝AIR-100 S-E muse approve-drift monitor（僅 muse approve 腿）——S5 對帳後
吸收：五面 health 腿全部由 install.py `--verify`（probe 面）＋`--check --surface
all`（parity 面）供給（單一實作源，muse approve 態已內含於兩者），本 script
只編排：子進程呼叫＋輸出透傳落 log＋退出碼彙整。

fail-loud（與前形同語義）：任一子命令非零＝告警行＋exit 1——「查不到＝告警
非靜默綠」；launchd 對非零 exit 不觸發重跑（StartInterval 節流，日頻）。

排程：deploy/governance-health-monitor.plist（版控源）；裝載／卸載＝
`uv run python governance/install.py --surface monitor [--uninstall]`。
子進程走 uv run python（F-4：machine python3=3.9 會被 installer 地板守衛拒）。
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UV = str(Path.home() / ".local/bin/uv")
TIMEOUT = 900  # --verify 含 codex host-level fixture（真 codex exec，最長 180s）

MODES = (
    ("verify", ["--verify", "--surface", "all"]),
    ("check", ["--check", "--surface", "all"]),
)


def run_mode(argv: list[str]) -> int:
    cmd = [UV, "run", "python", "governance/install.py", *argv]
    print(f"[governance-health] $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                          timeout=TIMEOUT)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main() -> int:
    failed = []
    for name, argv in MODES:
        try:
            rc = run_mode(argv)
        except subprocess.TimeoutExpired:
            print(f"[governance-health] FAIL：{name} timeout（{TIMEOUT}s）"
                  "——告警（fail-loud）")
            failed.append(name)
            continue
        if rc != 0:
            failed.append(name)
    if failed:
        print(f"[governance-health] FAIL：{'、'.join(failed)} 非零——"
              "五面 governance health 異常，檢查上方輸出（fail-loud）")
        return 1
    print("[governance-health] PASS：--verify＋--check 全綠")
    return 0


if __name__ == "__main__":
    sys.exit(main())
