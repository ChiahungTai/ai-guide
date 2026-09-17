#!/usr/bin/env python3
"""ai-guide 新機器 bootstrap 編排器（AIR-110）——冪等、stdlib-only。

唯一安裝入口＝governance/install.py 穩定 CLI 契約（governance/manifest.toml
[bootstrap_cli]），不下手工 config。五階段：

  Phase 1 preflight——uv 在 PATH、repo root（.git）、G1 secrets（<repo>/
  settings.json gitignored local-only——缺席 fail-loud 引導手動拷，不自動建
  不代寫，拍板①）、hooksPath（非 .githooks＝WARN 列修復指引，G3）。
  Phase 2 core——primary 跑 installer --surface all（exit 透傳）；
  secondary 本弧僅介面（拍板②）。
  Phase 3 approve 暫停點——三項手動 approve（CC /hooks、codex trust、ZCode
  重開 session）；approve 恆手動（拍板④），無 --approved 停此 exit 0。
  Phase 4 verify 編排——installer --verify／--check、memory-topology、
  check_single_source、hooksPath、spine degraded（在場與否皆報告非擋）。
  Phase 5 面外清單——跨 repo 工具＋G5/G6 等（列印不安裝）。

冪等：編排器自身無狀態——重跑發出相同命令序列；installer noop 冪等由
AIR-116 保證。新機器全裝總覽文檔＝hooks/MULTI-MACHINE.md。
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ("uv", "run", "python", "governance/install.py")
HOOKS_PATH_EXPECTED = ".githooks"
EXIT_FAIL = 1

ROLES = ("primary", "secondary")


def _spine_index() -> Path:
    # 函數內求值（HOME-shim 沙箱可覆蓋）；module 載入時凍結會繞過沙箱。
    return Path.home() / ".agents" / "memory-spine" / "index.md"


def _probe(status: str, name: str, detail: str = "") -> None:
    line = f"[probe] {status:<4}  {name}"
    if detail:
        line += f"：{detail}"
    print(line)


def _hooks_path_value() -> str:
    """git config core.hooksPath 輸出（未設/查詢失敗＝空字串）。"""
    r = subprocess.run(
        ("git", "config", "--get", "core.hooksPath"),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout.strip() if r.returncode == 0 else ""


def _check_hooks_path() -> None:
    """hooksPath 輸出探針：.githooks＝PASS；否則 WARN＋修復指引（G3，不擋）。"""
    value = _hooks_path_value()
    if value == HOOKS_PATH_EXPECTED:
        _probe("PASS", "hooksPath", f"core.hooksPath={value}")
    else:
        _probe(
            "WARN",
            "hooksPath",
            f"core.hooksPath={value or '（未設）'}——修復：git -C <repo> config core.hooksPath .githooks"
            "（per-clone；控制面隔離閘未上線＝guard 不生效）",
        )


def preflight() -> bool:
    """Phase 1 唯讀檢查；回 False＝有 FAIL 項（fail-loud，不續行）。"""
    ok = True

    uv_path = shutil.which("uv")
    if uv_path:
        _probe("PASS", "uv", uv_path)
    else:
        _probe("FAIL", "uv", "uv 不在 PATH——先安裝 uv（https://docs.astral.sh/uv/）")
        ok = False

    git_dir = REPO_ROOT / ".git"  # worktree 形態 .git 是檔案——存在性即可
    if git_dir.exists():
        _probe("PASS", "repo-root", str(REPO_ROOT))
    else:
        _probe("FAIL", "repo-root", f"{REPO_ROOT} 無 .git——請在 repo clone 內執行")
        ok = False

    settings = REPO_ROOT / "settings.json"
    if settings.exists():
        _probe("PASS", "G1-secrets", f"{settings} 在場（gitignored local-only）")
    else:
        _probe(
            "FAIL",
            "G1-secrets",
            f"從舊機拷貝 settings.json（含 API keys）到 {settings}"
            "（fail-loud：不自動建、不代寫；CC ~/.claude/settings.json symlink 前置鏈依賴它）",
        )
        ok = False

    _check_hooks_path()
    return ok


def _print_approve_steps() -> None:
    print(
        "手動 approve 三項（approve 分欄單一源＝governance/README.md「approve 分欄」節）："
    )
    print("  1. Claude Code：開 /hooks UI 目視審查新增條目（無 CLI 替代）")
    print(
        "  2. codex：新 session startup review 或 /hooks TUI trust approve（installer 不代寫 [hooks.state]）"
    )
    print("  3. ZCode：重開 session 生效（per-session 快照，舊 session 不生效非失敗）")


def verify_probes() -> bool:
    """Phase 4 探針編排（輸出透傳）；回 False＝有 FAIL 項。"""
    ok = True

    def run_cmd(argv: tuple[str, ...], name: str) -> None:
        nonlocal ok
        r = subprocess.run(argv, cwd=str(REPO_ROOT), check=False)
        status = "PASS" if r.returncode == 0 else "FAIL"
        _probe(status, name, f"exit {r.returncode}")
        if r.returncode != 0:
            ok = False

    run_cmd(INSTALLER + ("--surface", "all", "--verify"), "installer --verify")
    run_cmd(
        INSTALLER + ("--surface", "all", "--check"), "installer --check --surface all"
    )
    run_cmd(("bash", "hooks/verify-memory-topology.sh"), "memory-topology")
    run_cmd(
        ("uv", "run", "python", "skills/scan-project/scripts/check_single_source.py"),
        "check_single_source",
    )
    _check_hooks_path()

    spine = _spine_index()
    if spine.exists():
        _probe("PASS", "memory-spine", f"{spine} 在場（跨池共享）")
    else:
        _probe(
            "WARN",
            "memory-spine",
            f"{spine} 缺席＝degraded（報告非擋；設置見 ~/.agents/memory-spine/）",
        )
    return ok


def print_external_list() -> None:
    """Phase 5 面外清單（列印不安裝）。"""
    print("跨 repo 工具（各自 repo/skill 為安裝真相源，bootstrap 不安裝）：")
    print(
        "  - delegate-bridge plugin（marketplace 安裝；repo ~/Github/delegate-bridge——細節見 repo docs/）"
    )
    print(
        "  - code-reality binary（uv tool install／cargo；真相源＝skills/code-reality/SKILL.md）"
    )
    print(
        "  - NT 查詢工具鏈（nt-query/nt-v1-query——已遷 mosaic repo-local .agents/skills/）"
    )
    print("  - mosaic com.mosaic.* launchd 排程（mosaic repo 側管理）")
    print("  - entitlements-probe（deploy/entitlements-probe.plist 手動裝載）")
    print("面外步驟（installer 範圍外——hooks/MULTI-MACHINE.md「新機器全裝總覽」節）：")
    print("  - G1 secrets：<repo>/settings.json 從舊機拷貝（preflight 已擋缺席）")
    print(
        "  - G3 hooksPath：git config core.hooksPath .githooks（per-clone，preflight 列修復指引）"
    )
    print("  - G5 backlog-cleanup plist：未版控（另 flash 承接）")
    print("  - G6 池傳輸：新機器空池起步——hooks/MULTI-MACHINE.md §1")
    print("  - spine：~/.agents/memory-spine/ 跨池共享（缺席＝degraded 非擋）")
    print(
        "  - cron/monitor 裝載＝primary-only（--role secondary 不裝；MULTI-MACHINE.md §4）"
    )


def _print_plan() -> None:
    """--dry-run：印 Phase 2-5 將執行的計畫（零安裝執行）。"""
    print("== Phase 2/5: core installer（計畫——未執行）==")
    print(f"  [wrap] {' '.join(INSTALLER)} --surface all")
    print("== Phase 3/5: approve 暫停點（計畫——未執行）==")
    _print_approve_steps()
    print("  無 --approved＝停此 exit 0；完成 approve 後帶 --approved 續跑")
    print("== Phase 4/5: verify 編排（計畫——未執行）==")
    print(f"  [probe] {' '.join(INSTALLER)} --surface all --verify")
    print(f"  [probe] {' '.join(INSTALLER)} --surface all --check")
    print("  [probe] bash hooks/verify-memory-topology.sh")
    print("  [probe] uv run python skills/scan-project/scripts/check_single_source.py")
    print("  [probe] git config --get core.hooksPath（輸出探針）")
    print(
        "  [probe] memory-spine degraded 檢查（~/.agents/memory-spine/index.md 在場與否皆報告非擋）"
    )
    print_external_list()


def _parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="ai-guide 新機器 bootstrap 編排器（冪等；全裝總覽＝hooks/MULTI-MACHINE.md）",
    )
    ap.add_argument(
        "--role",
        choices=ROLES,
        default="primary",
        help="primary＝本機全裝；secondary＝本弧未實作僅介面（拍板②）",
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="印計畫不執行（preflight 唯讀檢查照跑）"
    )
    ap.add_argument(
        "--approved",
        action="store_true",
        help="approve 步已手動完成——續跑 Phase 4 verify＋Phase 5 面外清單",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)

    if args.role == "secondary":
        print(
            "--role secondary：本弧未實作，僅介面（拍板②——cron/monitor 裝載對象歸 primary；副機安裝面後續弧承接）"
        )
        return 0

    print("== Phase 1/5: preflight ==")
    if not preflight():
        print(
            "[FAIL] preflight 有 FAIL 項——fail-loud 不續行（修復後重跑）",
            file=sys.stderr,
        )
        return EXIT_FAIL

    if args.dry_run:
        _print_plan()
        print("[dry-run] 零安裝執行——計畫如上；移除 --dry-run 進入安裝")
        return 0

    print("== Phase 2/5: core installer ==")
    print(f"[wrap] {' '.join(INSTALLER)} --surface all")
    r = subprocess.run(
        INSTALLER + ("--surface", "all"), cwd=str(REPO_ROOT), check=False
    )
    if r.returncode != 0:
        print(
            f"[FAIL] installer exit {r.returncode}（透傳；線索＝~/.local/share/ai-guide/governance-plan-journal/）",
            file=sys.stderr,
        )
        return r.returncode

    print("== Phase 3/5: approve 暫停點 ==")
    _print_approve_steps()
    if not args.approved:
        print("完成 approve 後帶 --approved 續跑（approve 恆手動——拍板④）")
        return 0

    print("== Phase 4/5: verify 編排 ==")
    probes_ok = verify_probes()

    print("== Phase 5/5: 面外清單（列印不安裝）==")
    print_external_list()

    if not probes_ok:
        print("[FAIL] verify 探針有 FAIL 項——見上方 [probe] FAIL 行", file=sys.stderr)
        return EXIT_FAIL
    print(
        "bootstrap 完成：探針全數 PASS/WARN（WARN＝報告非擋）。重跑＝冪等（installer noop＋同命令序列）。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
