#!/usr/bin/env python3
"""K2 POC——lsof 對「靜默命令開 fd」的偵測實測（AIR-149 S1 驗證策略）.

機制驗證（reviewer F-5 裁決：2 分鐘 sleep 即可，25m 真實 workload 命中率
驗證顯式挪 S4 dogfood）：

1. spawn 靜默 holder（`sleep 120` stdout 重導檔案——fd 持開、零寫入，
   模擬 exec 面「zsh 持 fd 直寫但 mtime/size 不動」的 SM-2 情境）
2. harness_waiter.lsof_lease_prober 對該檔→必命中（exit 0）
3. 同 fd 經 symlink 路徑查→亦命中（realpath 正規化，F-3）
4. 不存在檔→exit 1＋stderr 非空→None（F-2：錯誤非無命中，禁猜）
5. holder 終止後再查→[]（fd 釋放＝無 lease）

零寫入驗證：holder 存活期間檔案 size 不變——證明「無 mtime/size 推進」
不等於「無 writer」，lease 面不可省（EP K2 假設的機制基礎）。
"""

import importlib.util
import json
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SCRATCH = REPO_ROOT / ".agent-tmp" / "poc-fd-lease"
SCRIPT = REPO_ROOT / "scripts" / "harness_waiter.py"

spec = importlib.util.spec_from_file_location("harness_waiter", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    CHECKS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    held = SCRATCH / "call_poc-stdout.log"
    holder = subprocess.Popen(
        ["sleep", "120"],
        stdout=held.open("wb"),
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.5)  # 讓 holder 的 fd 就位
        result = mod.lsof_lease_prober([held])
        check(
            "silent-holder-fd-detected",
            result == [str(held)],
            f"prober={result}（靜默 sleep 持 stdout fd）",
        )
        size_before = held.stat().st_size
        time.sleep(1.0)
        size_after = held.stat().st_size
        check(
            "zero-write-while-held",
            size_before == size_after,
            f"size={size_before}→{size_after}（fd 持開但零寫入＝mtime/size 反指標）",
        )
        link = SCRATCH / "link-to-stdout.log"
        if link.is_symlink():
            link.unlink()
        link.symlink_to(held)
        via_link = mod.lsof_lease_prober([link])
        check(
            "symlink-path-normalized-hit",
            via_link == [str(link)],
            f"prober({link.name})={via_link}（realpath 正規化，F-3）",
        )
        gone = SCRATCH / "no-such-file.log"
        undecidable = mod.lsof_lease_prober([gone])
        check(
            "missing-file-undecidable",
            undecidable is None,
            f"prober={undecidable}（exit 1＋stderr 非空＝錯誤非無命中，F-2）",
        )
    finally:
        holder.terminate()
        holder.wait(timeout=10)
    time.sleep(0.3)
    released = mod.lsof_lease_prober([held])
    check(
        "fd-released-no-lease",
        released == [],
        f"prober={released}（holder 終止後＝無 lease）",
    )
    summary = {
        "poc": "poc_fd_lease",
        "pass": all(ok for _n, ok, _d in CHECKS),
        "checks": [{"name": n, "ok": ok, "detail": d} for n, ok, d in CHECKS],
        "scope-note": "機制驗證；25m 真實 workload 命中率驗證挪 S4 dogfood",
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
