#!/usr/bin/env python3
"""AIR-93 池 state 對帳網——memory pool 唯讀偵測器。

Invariant（AIR-93 雙討論收斂定案）：池的任何變動必須能證明來自 approved
consolidation。合法流程下池 HEAD＝已審核基線；繞閘寫入（muse post-session
原生路徑、shell 直寫、未來新 writer）只會出現在 working tree delta——
`git status --porcelain` 非空即 flag。

設計約束：
- 唯讀：永不 checkout/add/commit/回復——處置權在 consolidation 補審
  （codex advisory：自動回復須 CAS 互斥語義，不在此層）。
- 威脅模型通案：不管寫入者是誰，繞過管道即留 delta。
- fail-closed：git 缺席、pool 不在任何 git repo、marker malformed——
  「無法證明乾淨」≠「乾淨」，一律 fail loud。
- marker 三態與 muse-plugins/memory-governance hook 同源：absent →
  not_governed（native 寫入本來合法，無執法面）；protocol 必須是整數 1。

消費端：consolidation 開頭／memory-audit 機械層（exit 契約）。
exit code：0＝clean/not_governed；1＝infra/contract 錯（fail loud）；
2＝dirty（flag——consolidation 先補審這批 delta 再跑正常流程）。

用法：uv run python scripts/reconcile_memory_pool.py <repo-root> [--json]
"""

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MARKER_REL = Path(".agents") / "memory-governance.json"
POOL_REL = Path(".agents") / "memory"
# AIR-63 S3：pending 讀取覆層（_pending.md）是 generate_pending.py 的合法自產物
# （T4-1 訊號③——手動／夜波 Phase0 refresh 即自產；provisional 不入池 git 歷史，
# 池 .gitignore 套用前 porcelain 亦不構成 delta）。豁免僅此一檔、非整池放行：
# 該檔宣告 provisional、永不進 canonical，其內容要進池仍須過 consolidation；
# 資料源 inbox 的執法面不受影響。
ALLOWED_SELF_PRODUCED = ("_pending.md",)


class ReconcileError(Exception):
    """無法判定池狀態（fail-closed 家族：git 缺席／pool 無 git／marker malformed）。"""


@dataclass(frozen=True)
class PoolDelta:
    code: str
    path: str


@dataclass(frozen=True)
class ReconcileResult:
    status: str  # "clean" | "dirty" | "not_governed"
    entries: list[PoolDelta] = field(default_factory=list)
    detail: str = ""


def _git(*args: str) -> str:
    # GIT_OPTIONAL_LOCKS=0：git status 預設 refresh index 並寫 .git/index——
    # 唯讀偵測器禁帶這個副作用（F5；池 index 是 consolidation 的 CAS 基準面）。
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        done = subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True, env=env
        )
    except FileNotFoundError as e:
        raise ReconcileError(
            f"git binary unavailable——baseline unestablishable (fail-closed): {e}"
        ) from e
    except subprocess.CalledProcessError as e:
        raise ReconcileError(
            f"git {' '.join(args[:2])} failed (fail-closed): {e.stderr.strip()}"
        ) from e
    return done.stdout


def _validate_marker(marker: Path) -> None:
    # protocol 語義與單一源 hook 同源（muse_memory_governance.sh:130-135）：
    # JSON number semantic equality——jq 把 1.0/1e0 視為 1 by design，Python 端
    # 對齊接受 int|float 的 1；bool 顯式排除（json true 被兩源同拒——hook 端
    # jq -e 'true == 1' 為 false）。
    try:
        doc = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ReconcileError(f"marker malformed (fail-closed): {marker}: {e}") from e
    protocol = doc.get("protocol") if isinstance(doc, dict) else None
    if (
        not isinstance(protocol, (int, float))
        or isinstance(protocol, bool)
        or protocol != 1
    ):
        raise ReconcileError(
            f"marker malformed/unsupported: {marker} (protocol must be the number 1)"
        )


def _parse_porcelain(raw: str) -> list[PoolDelta]:
    # porcelain -z：NUL 分隔、路徑不轉義（CJK 檔名安全）；rename/copy 的來源
    # path 是獨立 token，XY 兩欄皆可為 R/C（staged 與 worktree rename——F4），
    # 配對時吃掉來源 token；malformed token fail loud 不猜格式。
    tokens = [t for t in raw.split("\0") if t]
    entries: list[PoolDelta] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if len(tok) < 4:
            raise ReconcileError(f"porcelain malformed token (fail-closed): {tok!r}")
        code, path = tok[:2], tok[3:]
        if "R" in code or "C" in code:
            i += 1  # rename/copy 的來源路徑 token
        entries.append(PoolDelta(code=code, path=path))
        i += 1
    return entries


def _is_self_produced(path: str, pool_rel: str) -> bool:
    """porcelain path（相對 git root）是否命中自產物豁免清單（pool 內相對路徑比對）。"""
    allowed = {
        n if pool_rel == "." else f"{pool_rel}/{n}" for n in ALLOWED_SELF_PRODUCED
    }
    return path in allowed


def reconcile_pool(repo_root: Path) -> ReconcileResult:
    """對單一 governed repo 的 pool 做唯讀對帳；無法判定時 raise ReconcileError。

    已知殘留限制（如實標註，F7 裁決）：nested layout（pool 自帶 .git）下
    pool 目錄連 .git 一起刪除＝基線本體消失，無外部基準可偵測——此為先天
    極限，非本工具覆蓋範圍；flat layout 的刪除由 outer git 的 D delta 接住。
    """
    marker = repo_root / MARKER_REL
    # absent 判定與單一源 hook 同源（-e + -L 雙檢）：broken symlink 不是
    # absent，是 declared-but-broken → 交 _validate_marker read failure
    # fail loud（F2——exists() 對 broken symlink 回 False 會讓砍 marker
    # 換取 not_governed 成為可用手法）。
    if not marker.exists() and not marker.is_symlink():
        return ReconcileResult(
            status="not_governed",
            detail=f"no governance marker at {marker}——native pool writes are legitimate here",
        )
    _validate_marker(marker)

    pool = repo_root / POOL_REL
    if not pool.is_dir():
        # pool 目錄缺失≠clean（F7）：刪除是 mutation。從 repo_root 解析 git，
        # tracked 刪除會以 D delta 浮出；pool 從未被追蹤則無訊號（clean 帶
        # 明確 detail）；repo_root 也不在 git 內＝無基準→fail loud。
        git_root = Path(
            _git("-C", str(repo_root), "rev-parse", "--show-toplevel").strip()
        )
        rel = os.path.relpath(pool, git_root)
        entries = _parse_porcelain(
            _git(
                "-C",
                str(git_root),
                "status",
                "--porcelain",
                "-z",
                "--untracked-files=all",
                "--",
                rel,
            )
        )
        if entries:
            return ReconcileResult(status="dirty", entries=entries)
        return ReconcileResult(
            status="clean",
            detail="pool directory absent and no tracked deletion signal——pool never tracked or never existed",
        )

    git_root = Path(_git("-C", str(pool), "rev-parse", "--show-toplevel").strip())
    rel = os.path.relpath(pool, git_root)
    # --untracked-files=all：顯式固定 untracked policy（F1）——不帶時
    # status.showUntrackedFiles=no config 能讓 teardown 新增檔整批隱形。
    raw = _git(
        "-C",
        str(git_root),
        "status",
        "--porcelain",
        "-z",
        "--untracked-files=all",
        "--",
        rel,
    )
    entries = _parse_porcelain(raw)
    # AIR-63 S3：自產物豁免在 parse 後過濾（pool 目錄整刪分支不適用——該分支
    # 是最大級 mutation，豁免不得稀釋其偵測）。
    entries = [e for e in entries if not _is_self_produced(e.path, rel)]
    if entries:
        return ReconcileResult(status="dirty", entries=entries)
    return ReconcileResult(status="clean", detail="pool working tree matches HEAD")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AIR-93 memory pool read-only reconciler"
    )
    parser.add_argument("repo", type=Path, help="repo root containing .agents/memory")
    parser.add_argument(
        "--json", action="store_true", help="machine-readable payload on stdout"
    )
    args = parser.parse_args(argv)

    try:
        result = reconcile_pool(args.repo)
    except ReconcileError as e:
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "repo": str(args.repo), "detail": str(e)}
                )
            )
        else:
            print(f"[FAIL] reconcile_memory_pool: {e}")
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "status": result.status,
                    "repo": str(args.repo),
                    "entries": [
                        {"code": e.code, "path": e.path} for e in result.entries
                    ],
                },
                ensure_ascii=False,
            )
        )
    elif result.status == "dirty":
        lines = "\n".join(f"  {e.code} {e.path}" for e in result.entries)
        print(
            f"[FAIL] reconcile_memory_pool: unapproved pool delta ({len(result.entries)} entries)——consolidation 補審後收編或丟棄\n{lines}"
        )
    elif result.status == "not_governed":
        print(f"[OK] reconcile_memory_pool: not governed——{result.detail}")
    else:
        print(f"[OK] reconcile_memory_pool: clean——{result.detail}")

    return 0 if result.status in ("clean", "not_governed") else 2


if __name__ == "__main__":
    sys.exit(main())
