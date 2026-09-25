#!/usr/bin/env python3
# closeout 複查腿 CLI（AIR-193 切片二·survey top3）——結案 predicate 群手動消費態。
# 掛點決策（AC#3）：hook（.githooks/card-diagram-guard.py pre-commit）為正典、本 CLI
# 為複查腿——判定邏輯單一源＝guard 的純函式（import 呼叫），禁二刻。
# 用途：guard 不在場 clone（core.hooksPath 未設）、Done 後補勾／補件複查（AIR-181
# 代勾形態）、--all-done 全板 Done 卡巡檢。
# 用法：
#   uv run python scripts/closeout_check.py "backlog/tasks/air-181 ....md" ...
#   uv run python scripts/closeout_check.py --all-done
# 輸出：stdout 逐卡缺項清單（人話）；refs 未落地走警告（stderr，不計違規）。
# exit code＝違規卡數（0＝全過；非 Done 卡跳過不計）。
# runtime：系統 python3（3.9）相容——與 guard 同款約束。
import argparse
import glob
import importlib.util
import os
import subprocess
import sys


def _load_guard():
    """載 .githooks/card-diagram-guard.py 為模組——判定函式單一源。"""
    path = os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.pardir,
            ".githooks",
            "card-diagram-guard.py",
        )
    )
    spec = importlib.util.spec_from_file_location("card_diagram_guard", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def _repo_root():
    r = sh("git", "rev-parse", "--show-toplevel")
    return r.stdout.strip() if r.returncode == 0 else None


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _head_status(g, root, relpath):
    r = sh("git", "-C", root, "show", "HEAD:" + relpath)
    return g.frontmatter_status(r.stdout) if r.returncode == 0 else None


def _is_tracked_factory(root):
    def is_tracked(path):
        return bool(sh("git", "-C", root, "ls-files", "--", path).stdout.strip())

    return is_tracked


def check_card(g, path, root):
    """對單卡跑結案 predicate 群——回 (violations, warnings, status)。"""
    text = _read(path)
    status = g.frontmatter_status(text)
    violations = []
    warnings = []
    if status != "Done":
        return violations, warnings, status
    violations.extend(g.section_marker_violations(text))
    warnings.extend(g.section_marker_warnings(text))
    violations.extend(g.ac_residue_violations(text))
    relpath = os.path.relpath(os.path.abspath(path), root)
    v = g.status_trajectory_violation(_head_status(g, root, relpath), status)
    if v:
        violations.append(v)
    for p in g.missing_ref_paths(text, _is_tracked_factory(root)):
        warnings.append("refs 路徑 git 查無（未落地？MOS-28 型）：" + p)
    return violations, warnings, status


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "closeout 複查腿——結案 predicate 群手動消費態"
            "（判定源＝.githooks/card-diagram-guard.py）"
        )
    )
    parser.add_argument("cards", nargs="*", help="卡檔路徑（backlog/tasks/*.md）")
    parser.add_argument(
        "--all-done", action="store_true", help="掃 backlog/tasks/ 全部 status: Done 卡"
    )
    args = parser.parse_args(argv)
    g = _load_guard()
    if args.all_done:
        root = _repo_root()
        if not root:
            print(
                "ERROR: 不在 git repo 內——--all-done 需 repo root 定位 backlog/tasks/",
                file=sys.stderr,
            )
            return 2
        cards = [
            p
            for p in sorted(glob.glob(os.path.join(root, "backlog", "tasks", "*.md")))
            if g.frontmatter_status(_read(p)) == "Done"
        ]
    else:
        if not args.cards:
            parser.error("至少給一張卡檔路徑，或 --all-done")
        root = _repo_root() or os.getcwd()
        cards = args.cards
    bad = 0
    for path in cards:
        violations, warnings, status = check_card(g, path, root)
        if status != "Done":
            print(f"SKIP {path}——status={status}，非結案對象")
            continue
        if violations:
            bad += 1
            print(f"FAIL {path}——{len(violations)} 項違規：")
            for i, v in enumerate(violations, 1):
                print(f"  {i}. {v}")
        else:
            print(f"PASS {path}")
        for w in warnings:
            print("  警告（不擋）：" + w, file=sys.stderr)
    return bad


if __name__ == "__main__":
    sys.exit(main())
