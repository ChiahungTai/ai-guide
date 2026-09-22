"""wt-close.sh TRUNK_ADVANCED 條件分支契約測試（AIR-166 F2——AIR-164 新增分支零覆蓋補測）。

釘住的 invariant（scripts/wt-close.sh：merge 前 merge-base --is-ancestor 捕捉、
收線尾 warn＋receipt result 欄）：

- full 收斂且 trunk 實際前進（merge 前 card branch 未含於 trunk）→ stderr 印
  CR freshness 提醒，receipt result 欄＝pass;graph-stale-reminded（非正確性
  依賴——不改 exit code、不自動 build）。
- 零 commit close（card branch == trunk tip，trunk 未被推動）→ receipt 純
  pass，無提醒。

Fixture：tmp git repo＋手工 identity contract（模擬 wt-open 產物，手法同
test_wt_sweep.py）。full 模式會真的 ff merge 進 main（primary worktree 清潔
由 seed 保證）；close 成功後卡 WT 與 branch 皆應移除。
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from conftest import REPO_ROOT

CLOSE_SCRIPT = REPO_ROOT / "scripts" / "wt-close.sh"
GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def _seed_repo(base: Path) -> Path:
    """tmp 消費端 repo：main 基線＋.agent-tmp ignore（identity contract 不構成 dirty）。"""
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".agent-tmp/\n")
    (repo / "f.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _open_card_wt(repo: Path, card: str = "air-1") -> Path:
    """模擬 wt-open：worktree add＋手工 identity contract（owning 線＝main）。"""
    wt = repo.parent / f"repo-{card}"
    _git(repo, "worktree", "add", "-b", card, str(wt))
    ident_dir = wt / ".agent-tmp"
    ident_dir.mkdir()
    (ident_dir / "wt-identity.json").write_text(
        json.dumps(
            {
                "v": 1,
                "mode": "card",
                "task": card,
                "owning_line": "main",
                "base_ref": "main",
                "base_hash": _git(repo, "rev-parse", "main"),
                "branch": card,
                "wt_path": str(wt),
                "opened_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return wt


def _close(wt: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(CLOSE_SCRIPT), "--wt", str(wt)],
        capture_output=True,
        text=True,
        check=False,
    )


def _last_full_result(repo: Path) -> str:
    """receipt log（.git/wt-close.log，格式 timestamp|mode|wt|branch|result）最後一筆 full 行的 result 欄。"""
    lines = [
        ln
        for ln in (repo / ".git" / "wt-close.log")
        .read_text(encoding="utf-8")
        .splitlines()
        if "|full|" in ln
    ]
    assert lines, "預期至少一筆 full receipt"
    return lines[-1].split("|")[4]


def test_trunk_advanced_receipt_reminds_graph_stale(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt = _open_card_wt(repo)
    (wt / "w.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(air-1) work")
    tip = _git(wt, "rev-parse", "HEAD")

    done = _close(wt)

    assert done.returncode == 0, done.stderr
    assert "CR freshness 提醒" in done.stderr  # 提醒面（stderr warn）
    assert _last_full_result(repo) == "pass;graph-stale-reminded"  # receipt 面
    assert tip in _git(repo, "rev-list", "main")  # trunk 實際前進（吸收 card commit）
    assert not wt.exists()  # 正常收線：WT 已移除
    assert _git(repo, "branch", "--list", "air-1") == ""  # branch 已刪（-d 非 -D）


def test_zero_commit_close_receipt_plain_pass(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    main_tip = _git(repo, "rev-parse", "main")
    wt = _open_card_wt(repo)  # 零 commit：branch == trunk tip

    done = _close(wt)

    assert done.returncode == 0, done.stderr
    assert "CR freshness 提醒" not in done.stderr
    assert _last_full_result(repo) == "pass"  # 純 pass，無提醒
    assert _git(repo, "rev-parse", "main") == main_tip  # trunk 未被推動
    assert not wt.exists()
