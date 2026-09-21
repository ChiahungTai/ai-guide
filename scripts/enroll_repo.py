#!/usr/bin/env python3
"""enroll_repo——repo 一命令收編 marshal admission guard（AIR-135 Q8 V8；AIR-152）。

寫 marker profile（`.agents/marshal-governance.json`）＋當場驗證（以 guard
本體 load_profile 判三態——驗證與執行面同一 schema 實作）＋印下一步。
marker opt-in 拓撲的零摩擦收編端；未收編可見面＝
`scripts/agent_liveness_sweep.py --enrollment-root <dir>`。

usage
-----
    uv run python scripts/enroll_repo.py --repo <path> [--trunk main]
        [--level branch|wt] [--source-roots P ...] [--allowlist P ...]
    uv run python scripts/enroll_repo.py --repo <path> --check

- `--level branch`（預設）：canonical ∧ branch==trunk ∧ sourceRoots 命中才
  deny——一般 app repo 推薦（feature branch 工作不受擾）
- `--level wt`：canonical 主樹任何 branch 命中即 deny——控制面治理形
  （ai-guide 自身形態；ai-guide 另有控制面 guard patterns 單一源，marker
  sourceRoots 留空即可）
- `--source-roots`：repo 相對路徑 regex，matcher＝`re.search`——**前綴語請錨定
  寫 `^src/`**（未錨定 `src/` 會命中 `docs/src/…` 任意含子串路徑；codex 152 複審）
- `--level branch` 且 sourceRoots 空＝閘不擋任何檔（schema 有效但零保護）——
  預設拒收，除非 `--allow-empty-roots` 明示（codex 152 複審：禁回報 no-op 為成功）
- `--check`：只報收編狀態（enrolled／absent／malformed），不寫；exit 0＝
  enrolled、1＝未收編或 malformed
- marker 恆帶 allowlist `^\\.agents/marshal-governance\\.json$`（marker 自身
  修復出口；guard 另有硬豁免——雙保險且 profile 自述）

寫入面只有 marker 一檔（mkdir -p .agents）；不碰 hooksPath／config——hook 註冊
是 machine 面（user-level，`governance/install.py`／`scripts/bootstrap.py`），
與 repo 收編正交。
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

MARKER_REL = Path(".agents") / "marshal-governance.json"
MARKER_SELF_ALLOWLIST = r"^\.agents/marshal-governance\.json$"


def _load_guard_schema():
    """載 hooks/marshal_admission_guard.py——load_profile 為三態判定單一源。"""
    guard = Path(__file__).resolve().parents[1] / "hooks" / "marshal_admission_guard.py"
    spec = importlib.util.spec_from_file_location("marshal_admission_guard", guard)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git_toplevel(repo: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def _primary_root(guard, repo: str) -> str | None:
    """canonical PRIMARY 根（git-common-dir 父目錄）——guard 讀 marker 的同一錨。

    runtime authority＝guard 的 load_profile(primary)；收編寫入／檢查若錨在
    worktree toplevel，linked WT 上會出現「[OK] enrolled 但 guard 永遠讀不到」
    的假收編（codex 152-C1）——本函式令寫入／檢查／guard 三者同一錨。
    """
    try:
        common = guard._git_common_dir(repo)
    except RuntimeError:
        return None
    return os.path.dirname(common) or None


def build_profile(args: argparse.Namespace) -> dict:
    return {
        "protocol": 1,
        "trunk": args.trunk,
        "invariantLevel": args.level,
        "sourceRoots": list(args.source_roots),
        "allowlist": [MARKER_SELF_ALLOWLIST, *list(args.allowlist)],
    }


def status_line(status: str, marker: Path, profile: dict | None) -> str:
    if status == "ok" and profile:
        return (
            "enrolled invariantLevel=%s trunk=%s sourceRoots=%d allowlist=%d"
            % (
                profile.get("invariantLevel"),
                profile.get("trunk"),
                len(profile.get("sourceRoots", [])),
                len(profile.get("allowlist", [])),
            )
        )
    if status == "malformed":
        return "malformed（修復或刪除：%s）" % marker
    return "absent（未收編——marker：%s）" % marker


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="enroll_repo",
        description="repo 一命令收編 marshal admission guard（寫 marker＋驗證）",
    )
    parser.add_argument("--repo", required=True, help="目標 repo 路徑（git repo）")
    parser.add_argument("--trunk", default="main", help="trunk branch 名（預設 main）")
    parser.add_argument(
        "--level",
        choices=["branch", "wt"],
        default="branch",
        help="invariant 級（預設 branch：canonical∧branch==trunk 才擋）",
    )
    parser.add_argument(
        "--source-roots",
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="受治理路徑（repo 相對 regex；可多值）",
    )
    parser.add_argument(
        "--allowlist",
        nargs="*",
        default=[],
        metavar="PATTERN",
        help="豁免路徑（regex，先於 sourceRoots 判定；可多值）",
    )
    parser.add_argument("--check", action="store_true", help="只報收編狀態，不寫")
    parser.add_argument(
        "--allow-empty-roots",
        action="store_true",
        help="branch 級允許空 sourceRoots（no-op marker——明示豁免用）",
    )
    args = parser.parse_args()

    toplevel = _git_toplevel(args.repo)
    if not toplevel:
        print("[FAIL] enroll_repo：%s 不是 git repo（working tree）" % args.repo,
              file=sys.stderr)
        return 2
    guard = _load_guard_schema()
    primary = _primary_root(guard, toplevel)
    if not primary:
        print("[FAIL] enroll_repo：canonical PRIMARY 不可判定（%s）" % toplevel,
              file=sys.stderr)
        return 2
    marker = Path(primary) / MARKER_REL

    status, profile = guard.load_profile(primary)
    if args.check:
        print("%s: %s" % (primary, status_line(status, marker, profile)))
        return 0 if status == "ok" else 1

    new_profile = build_profile(args)
    if args.level == "branch" and not args.source_roots and not args.allow_empty_roots:
        print(
            "[FAIL] enroll_repo：branch 級且 sourceRoots 空＝零保護的 no-op marker"
            "（schema 有效但不擋任何檔）。確認要這樣就帶 --allow-empty-roots 重跑；"
            "否則帶 --source-roots（前綴語錨定寫 ^src/）",
            file=sys.stderr,
        )
        return 2
    if os.path.realpath(toplevel) != os.path.realpath(primary):
        print("[NOTE] %s 是 linked worktree——marker 寫在 canonical PRIMARY（%s）；"
              "guard 讀取面即該處" % (toplevel, primary), file=sys.stderr)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        json.dumps(new_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    vstatus, vprofile = guard.load_profile(primary)
    if vstatus != "ok":
        print("[FAIL] enroll_repo：寫後驗證未過（%s）——marker:%s" % (vstatus, marker),
              file=sys.stderr)
        return 2
    print("[OK] 已收編 %s" % toplevel)
    print("  marker：%s" % marker)
    print("  %s" % status_line(vstatus, marker, vprofile))
    print("  生效面：PreToolUse Edit|Write（user-level hook 註冊後對本 repo 生效；"
          "未註冊機器：uv run python governance/install.py）")
    print("下一步：")
    print("  1. commit marker（repo 治理配置，隨 repo 走）")
    print("  2. 盤點可見面：uv run python scripts/agent_liveness_sweep.py "
          "--enrollment-root <repos 根目錄>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
