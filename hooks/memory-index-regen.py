#!/usr/bin/env python3
"""
Stop hook: memory 索引冪等重生成（跨 Claude/ZCode 單一實作）。

從 stdin JSON 共用欄位 cwd（缺漏時退 CLAUDE_PROJECT_DIR env）推導 memory 目錄：
- Claude: ~/.claude/projects/<cwd 非英數→dash>/memory（底線也轉 dash——專案名編碼陷阱）
- ZCode:  ~/.zcode/cli/memories/projects/<basename>-<sha256(cwd)[:16]>/memory
  （兩腿皆 symlink → 同一實體 pool——AIR-223 直鏈拓撲均指池 real dir；
  resolve() 去重只跑一次）
Self-gating：目錄無 _generate_index.py 則靜默跳過（裝 script 即 opt-in）。
恆 exit 0——Stop 的 exit 2 會強制主模型再跑一輪（ZCode hooks 文檔明載），
regen 失敗只回報不阻斷。generator 資產源：skills/memory-audit/scripts/generate_index.py。
對應 rule: rules/context-management.md「Memory 生命周期規範」。
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

GENERATOR_NAME = "_generate_index.py"
# 信任邊界：Stop hook 每 turn 自動執行 memory 目錄內發現的 generator——執行前與
# 資產源 byte 比對，不符即跳過；資產源缺席同樣跳過（fail-closed——信任邊界不能
# 在無從驗證時蒸發成照舊執行）。__file__-relative 推導——本 hook 由 repo 路徑
# 註冊執行，資產恆在本 repo 內，跨機器 clone 不失準。
ASSET_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "memory-audit"
    / "scripts"
    / "generate_index.py"
)


def sha16(cwd: str) -> str:
    """ZCode memory 目錄名的 hash 段：sha256(專案絕對路徑) 前 16 hex。"""
    return hashlib.sha256(cwd.encode()).hexdigest()[:16]


def claude_memory_dir(cwd: str, home: Path) -> Path:
    """Claude 端：專案路徑所有非英數字元 → dash（mosaic_alpha → mosaic-alpha）。"""
    encoded = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    return home / ".claude" / "projects" / encoded / "memory"


def zcode_memory_dir(cwd: str, home: Path) -> Path:
    """ZCode 端：basename 原樣（底線保留）＋ dash ＋ sha16。"""
    return (
        home
        / ".zcode"
        / "cli"
        / "memories"
        / "projects"
        / f"{Path(cwd).name}-{sha16(cwd)}"
        / "memory"
    )


def run_for_cwd(cwd: str, home: Path) -> list[str]:
    """對推導出的各 memory 目錄跑 generator；回傳每目錄一行的結果摘要。"""
    notes: list[str] = []
    seen: set[Path] = set()
    for d in (claude_memory_dir(cwd, home), zcode_memory_dir(cwd, home)):
        gen = d / GENERATOR_NAME
        if not gen.exists():
            continue
        try:
            resolved = gen.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if not ASSET_SOURCE.exists():
            notes.append(
                f"[memory-index-regen] {d}: 資產源缺席（{ASSET_SOURCE}）——跳過執行"
                "（fail-closed；hook repo 的 memory-audit generator 資產不在場）"
            )
            try:
                (d / "_regen-skipped-stale").write_text(
                    "資產源缺席——Stop hook fail-closed 跳過重生成；"
                    "確認 repo 完整後下次成功 regen 自動移除本標記\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            continue
        if gen.read_bytes() != ASSET_SOURCE.read_bytes():
            notes.append(
                f"[memory-index-regen] {d}: generator 與資產源不符——跳過執行"
                "（cp 刷新部署副本或移除）"
            )
            # 跳過是 by-design（信任邊界），但 stdout 不進 context＝靜默停滯——
            # marker 讓「索引不再自動重生成」fail-visible（09-06 pending-decisions ③）
            try:
                (d / "_regen-skipped-stale").write_text(
                    "generator 與資產源不符——Stop hook 跳過重生成；"
                    "cp 資產源刷新本副本後，下次成功 regen 自動移除本標記\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            continue
        r = subprocess.run(
            [sys.executable, str(gen)], capture_output=True, text=True, check=False
        )
        last = ((r.stdout + r.stderr).strip().splitlines() or [f"exit {r.returncode}"])[
            -1
        ]
        notes.append(f"[memory-index-regen] {d}: {last}")
        # Stop 的 stdout 不進模型 context（ZCode 文檔）——exit 1＝gate 失敗（09-05 S1
        # ＋AIR-27：池超限或 frontmatter 違規，兩者索引皆已照寫出〔違規＝跳過壞條目〕；
        # 修復後 regen 成功即清），需實體可見錨點；`_` 前綴不進索引
        try:
            marker = d / "_regen-failed"
            if r.returncode != 0:
                marker.write_text(last + "\n", encoding="utf-8")
            elif marker.exists():
                marker.unlink()
            stale_marker = d / "_regen-skipped-stale"
            if r.returncode == 0 and stale_marker.exists():
                stale_marker.unlink()
        except OSError:
            pass
    return notes


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}
    if not isinstance(data, dict):  # 合法但非 object 的 JSON（如 []）——守住恆 exit 0
        data = {}
    cwd = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or ""
    if cwd:
        for note in run_for_cwd(cwd, Path.home()):
            print(note)
    sys.exit(0)


if __name__ == "__main__":
    main()
