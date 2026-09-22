"""wt-sweep 契約測試（AIR-159——orphan card WT TTL sweep，synthetic 層）。

釘住的 invariant（邊界基準＝delegate-bridge wt-reaper-evaluation §2）：

- 三條件齊才列孤兒：①identity contract 存在且自洽 ②dispatcher session 死
  （活動面靜默 ≥ TTL——合約無 session id，代理判定，詳 wt-sweep 模組
  docstring）③開張年齡 ≥ TTL。缺一即排除並記原因。
- 預設 dry-run：只報告不動手；prune 顯式才回收。
- 可證無損才 prune：working tree 乾淨＋branch 無未 merge 獨有 commit（或
  force 顯式）＋非鎖＋非呼叫端自身 WT＋owning 線可解析；回收動作複用
  wt-close.sh（subprocess），禁複製語義——receipt log（.git/wt-close.log
  的 full 行）是複用的機械證據。
- exit 契約：0＝掃描完成（含零孤兒、prune 個別失敗），1＝fail-loud
  （root 非 repo／git 失敗／參數錯）。

Fixture：tmp git repo＋手工 identity contract（模擬 wt-open 產物；時間面
以 os.utime 控制活動面 mtime、opened_at 字串直接回寫過去時間）。tmp repo
的 .gitignore 含 .agent-tmp/（消費端 repo 慣例，否則 contract 本身即 dirty）。
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/wt-sweep.py")
sweep, main, SweepError = _mod.sweep, _mod.main, _mod.SweepError
SCRIPT = REPO_ROOT / "scripts" / "wt-sweep.py"
CLOSE_SCRIPT = REPO_ROOT / "scripts" / "wt-close.sh"
HOUR = 3600.0
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
    """tmp 消費端 repo：main 基線＋.agent-tmp ignore（模擬真實 repo 慣例）。"""
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".agent-tmp/\n.delegate-bridge/\n")
    (repo / "f.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _open_card_wt(
    repo: Path,
    card: str = "air-1",
    *,
    opened_hours_ago: float = 0.0,
    owning: str = "main",
    mode: str = "card",
) -> Path:
    """模擬 wt-open：worktree add＋手工 identity contract（opened_at 可回寫）。"""
    branch = f"ephemeral/{card}" if mode == "ephemeral" else card
    wt = repo.parent / f"repo-{branch.removeprefix('ephemeral/')}"
    _git(repo, "worktree", "add", "-b", branch, str(wt))
    base_hash = _git(repo, "rev-parse", "main")
    opened = (datetime.now().astimezone() - timedelta(hours=opened_hours_ago)).strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )
    ident_dir = wt / ".agent-tmp"
    ident_dir.mkdir()
    (ident_dir / "wt-identity.json").write_text(
        json.dumps(
            {
                "v": 1,
                "mode": mode,
                "task": card,
                "owning_line": owning,
                "base_ref": owning,
                "base_hash": base_hash,
                "branch": branch,
                "wt_path": str(wt),
                "card_file": f"backlog/tasks/{card} - x.md",
                "opened_at": opened,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return wt


def _age_surfaces(wt: Path, hours_ago: float) -> None:
    """把活動面 mtime 回寫到過去（identity 檔＋.agent-tmp 樹含目錄自身＋git 面）。"""
    t = time.time() - hours_ago * HOUR
    git_dir = Path(_git(wt, "rev-parse", "--absolute-git-dir"))
    os.utime(git_dir / "HEAD", (t, t))
    common = Path(_git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    branch = _git(wt, "branch", "--show-current")
    if branch:
        ref = common / "refs" / "heads" / branch
        if ref.is_file():
            os.utime(ref, (t, t))  # commit 活動面：loose ref 檔
    agent_tmp = wt / ".agent-tmp"
    os.utime(agent_tmp, (t, t))  # 目錄自身也是活動面（_newest_mtime 會 stat target）
    for p in agent_tmp.rglob("*"):
        os.utime(p, (t, t))


def _orphan_fixture(base: Path, card: str = "air-1", **kw) -> tuple[Path, Path]:
    repo = _seed_repo(base)
    wt = _open_card_wt(repo, card, opened_hours_ago=100.0, **kw)
    _age_surfaces(wt, 100.0)
    return repo, wt


def _row_by_path(report: dict, wt: Path) -> dict:
    rows = [r for r in report["worktrees"] if r["path"] == str(wt)]
    assert len(rows) == 1, f"預期恰一列：{wt}（got {rows}）"
    return rows[0]


# ---- 三條件矩陣：①contract ②session 死（活動面靜默）③TTL 逾 ----


def test_orphan_all_three_conditions(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    r = sweep(repo, ttl_hours=72.0)
    row = _row_by_path(r, wt)
    assert row["verdict"] == "orphan"
    assert row["orphan"] is True
    assert row["prune_eligible"] is True  # clean＋零獨有 commit＋非鎖＋非 self
    assert row["skip_reasons"] == []
    assert row["age_hours"] >= 99.0
    assert row["last_activity_hours"] >= 99.0


def test_ttl_not_exceeded_fresh_excluded(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt = _open_card_wt(repo, opened_hours_ago=1.0)
    _age_surfaces(wt, 1.0)
    row = _row_by_path(sweep(repo, ttl_hours=72.0), wt)
    assert row["verdict"] == "fresh"
    assert row["orphan"] is False
    assert row["prune_eligible"] is False


def test_session_alive_active_excluded(tmp_path: Path) -> None:
    # 開張 100h 但最近有 scratch 活動（.agent-tmp journal 剛寫）＝session 活著
    repo, wt = _orphan_fixture(tmp_path)
    journal = wt / ".agent-tmp" / "session-journal.md"
    journal.write_text("checkpoint\n", encoding="utf-8")  # mtime＝now
    row = _row_by_path(sweep(repo, ttl_hours=72.0), wt)
    assert row["verdict"] == "active"
    assert row["orphan"] is False


def test_git_activity_refreshes_liveness(tmp_path: Path) -> None:
    # 活動面三選一：git 活動（commit→gitdir HEAD mtime）也續命
    repo, wt = _orphan_fixture(tmp_path)
    (wt / "g.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(air-1) work")
    row = _row_by_path(sweep(repo, ttl_hours=72.0), wt)
    assert row["verdict"] == "active"


# ---- 排除類：非孤兒／非本 WT ----


def test_no_identity_contract_foreign_counted_never_pruned(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    foreign_wt = repo.parent / "repo-manual"
    _git(repo, "worktree", "add", "-b", "manual", str(foreign_wt))
    r = sweep(repo, ttl_hours=72.0, prune=True, force=True)
    assert r["foreign"]["count"] == 1
    assert r["foreign"]["paths"] == [str(foreign_wt)]
    assert foreign_wt.exists()  # 無 contract＝foreign：永不判定、永不動
    row = _row_by_path(r, wt)
    assert row["verdict"] == "orphan" and row["prune_eligible"] is True


def test_identity_wt_path_mismatch_excluded(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    ident = wt / ".agent-tmp" / "wt-identity.json"
    raw = json.loads(ident.read_text(encoding="utf-8"))
    raw["wt_path"] = "/somewhere/else"
    ident.write_text(json.dumps(raw), encoding="utf-8")
    row = _row_by_path(sweep(repo, ttl_hours=72.0), wt)
    assert row["verdict"] == "identity-mismatch"
    assert row["orphan"] is False


def test_corrupt_contract_excluded_not_fail(tmp_path: Path) -> None:
    # 單一 WT contract 損壞＝該列 broken alert（永不 prune），不炸整趟掃描
    repo, wt = _orphan_fixture(tmp_path)
    (wt / ".agent-tmp" / "wt-identity.json").write_text("not-json", encoding="utf-8")
    r = sweep(repo, ttl_hours=72.0)
    row = _row_by_path(r, wt)
    assert row["verdict"] == "identity-corrupt"
    assert row["orphan"] is False
    assert wt.exists()


def test_unsupported_contract_version_excluded(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    ident = wt / ".agent-tmp" / "wt-identity.json"
    raw = json.loads(ident.read_text(encoding="utf-8"))
    raw["v"] = 99
    ident.write_text(json.dumps(raw), encoding="utf-8")
    row = _row_by_path(sweep(repo, ttl_hours=72.0), wt)
    assert row["verdict"] == "unsupported-version"


def test_main_worktree_never_candidate(tmp_path: Path) -> None:
    repo, _wt = _orphan_fixture(tmp_path)
    r = sweep(repo, ttl_hours=72.0)
    main_row = _row_by_path(r, repo)
    assert main_row["verdict"] == "main"
    assert main_row["prune_eligible"] is False


def test_wt_dir_missing_broken_alert(tmp_path: Path) -> None:
    # porcelain 有登記但目錄已滅＝broken alert（建議人工 git worktree prune，sweep 不代執行）
    repo, wt = _orphan_fixture(tmp_path)
    import shutil

    shutil.rmtree(wt)
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert row["verdict"] == "wt-dir-missing"
    assert row["orphan"] is False


# ---- 可證無損判定（orphan 成立後的第二道閘）----


def test_dirty_orphan_skipped_and_kept(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    (wt / "dirty.txt").write_text("未 commit 工作\n", encoding="utf-8")
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert row["verdict"] == "orphan"
    assert "dirty" in row["skip_reasons"]
    assert row["prune_eligible"] is False
    assert wt.exists()  # 髒樹永不回收


def test_unmerged_commits_skip_without_force(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    (wt / "w.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(air-1) work")
    _age_surfaces(wt, 100.0)
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert "unmerged-commits" in row["skip_reasons"]
    assert row["unique_commits"] == 1
    assert wt.exists() and _git(repo, "rev-parse", "--verify", "air-1")


def test_force_prune_converges_via_wt_close(tmp_path: Path) -> None:
    # force 顯式：獨有 commit 放行——回收複用 wt-close full（收斂進 owning 線），
    # receipt log 的 full 行是「複用非複製語義」的機械證據
    repo, wt = _orphan_fixture(tmp_path)
    (wt / "w.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(air-1) work")
    tip_before = _git(wt, "rev-parse", "HEAD")
    _age_surfaces(wt, 100.0)
    r = sweep(repo, ttl_hours=72.0, prune=True, force=True)
    row = _row_by_path(r, wt)
    assert row["prune_result"] is not None
    assert row["prune_result"]["status"] == "pruned"
    assert row["prune_result"]["close_rc"] == 0
    assert not wt.exists()
    assert _git(repo, "branch", "--list", "air-1") == ""  # branch 已刪（-d 非 -D）
    assert tip_before in _git(repo, "rev-list", "main")  # 獨有 commit 經收斂入線
    receipt = (repo / ".git" / "wt-close.log").read_text(encoding="utf-8")
    assert "|full|" in receipt  # 走的是 wt-close full 路徑


def test_locked_wt_skipped(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    _git(repo, "worktree", "lock", str(wt))
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert "locked" in row["skip_reasons"]
    assert wt.exists()


def test_self_cwd_wt_skipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # 呼叫端自己站在 WT 裡＝永不回收自身（eval doc §2b prune scope）
    repo, wt = _orphan_fixture(tmp_path)
    monkeypatch.chdir(wt)
    r = sweep(repo, ttl_hours=72.0, prune=True, force=True)
    row = _row_by_path(r, wt)
    assert "self-cwd" in row["skip_reasons"]
    assert wt.exists()


def test_owning_line_missing_skipped(tmp_path: Path) -> None:
    # owning 線已滅＝無從證明 merged，禁回收（fail-closed）
    repo, wt = _orphan_fixture(tmp_path, owning="feature-x")
    r = sweep(repo, ttl_hours=72.0, prune=True, force=True)
    row = _row_by_path(r, wt)
    assert "owning-line-missing" in row["skip_reasons"]
    assert wt.exists()


def test_ephemeral_orphan_prunable_and_pruned(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt = _open_card_wt(repo, "quick-fix", opened_hours_ago=100.0, mode="ephemeral")
    _age_surfaces(wt, 100.0)
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert row["verdict"] == "orphan" and row["prune_eligible"] is True
    assert row["prune_result"]["status"] == "pruned"
    assert not wt.exists()
    assert _git(repo, "branch", "--list", "ephemeral/quick-fix") == ""


# ---- dry-run vs prune ----


def test_dry_run_default_touches_nothing(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    r = sweep(repo, ttl_hours=72.0)  # 預設：報告而已
    row = _row_by_path(r, wt)
    assert row["verdict"] == "orphan" and row["prune_eligible"] is True
    assert row["prune_result"] is None
    assert wt.exists()
    assert "air-1" in _git(
        repo, "branch", "--list", "air-1"
    )  # 「+」前綴＝他 WT checkout 中
    assert not (repo / ".git" / "wt-close.log").exists()  # wt-close 從未被呼叫


def test_prune_removes_orphan_wt_and_branch(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    r = sweep(repo, ttl_hours=72.0, prune=True)
    row = _row_by_path(r, wt)
    assert row["prune_result"]["status"] == "pruned"
    assert not wt.exists()
    assert _git(repo, "branch", "--list", "air-1") == ""
    assert (
        _git(repo, "rev-parse", "main") == row["base_hash"]
    )  # trunk 不動（無獨有 commit）
    assert r["summary"]["pruned"] == 1 and r["summary"]["failed"] == 0


def test_zero_orphans_exit_zero(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt = _open_card_wt(repo, opened_hours_ago=1.0)
    r = sweep(repo, ttl_hours=72.0)
    assert r["summary"]["orphans"] == 0
    assert wt.exists()


# ---- exit 契約＋JSON 形狀（CLI 面）----


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_scan_exit_zero_and_json_shape(tmp_path: Path) -> None:
    repo, wt = _orphan_fixture(tmp_path)
    done = _run_cli("--root", str(repo), "--json")
    assert done.returncode == 0, done.stderr
    payload = json.loads(done.stdout)
    assert payload["root"] == str(repo)
    assert payload["ttl_hours"] == 72.0
    assert payload["summary"]["scanned"] == 2  # main＋card WT
    row = _row_by_path(payload, wt)
    assert row["verdict"] == "orphan"


def test_cli_fail_loud_non_repo(tmp_path: Path) -> None:
    done = _run_cli("--root", str(tmp_path), "--json")
    assert done.returncode == 1
    assert "ERROR" in done.stderr


@pytest.mark.parametrize("bad", ["0", "-1", "abc"])
def test_cli_fail_loud_bad_ttl(tmp_path: Path, bad: str) -> None:
    repo, _ = _orphan_fixture(tmp_path)
    done = _run_cli("--root", str(repo), "--ttl", bad)
    assert done.returncode == 1
    assert "ERROR" in done.stderr


def test_sweep_error_on_git_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _orphan_fixture(tmp_path)
    calls = {"n": 0}
    real_run = subprocess.run

    def fake_run(cmd, **kw):
        if cmd[:2] == ["git", "-C"]:
            calls["n"] += 1
            raise FileNotFoundError("git missing")
        return real_run(cmd, **kw)

    monkeypatch.setattr(_mod.subprocess, "run", fake_run)
    with pytest.raises(SweepError):
        sweep(repo, ttl_hours=72.0)


def test_human_report_mentions_verdicts(tmp_path: Path) -> None:
    repo, _wt = _orphan_fixture(tmp_path)
    done = _run_cli("--root", str(repo))
    assert done.returncode == 0
    assert "orphan" in done.stdout
    assert "summary" in done.stdout
