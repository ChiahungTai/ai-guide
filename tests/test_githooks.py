"""控制面 canonical 隔離閘測試（AIR-106）。

guard 是行為閘門核心——regression 直接改變隔離面：
漏抓 = 控制面條文落 canonical 即生效（F8 activation-before-review 洞重現）；
誤傷 = backlog／一般檔在 main 的合法 commit（例外①–④）被擋。
"""

import subprocess
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / ".githooks" / "control-plane-guard.sh"
PRE_COMMIT = Path(__file__).resolve().parent.parent / ".githooks" / "pre-commit"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


def _init_repo(tmp_path: Path, branch: str = "main") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", branch, str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "README.md").write_text("seed\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _run_guard(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(GUARD)], cwd=repo, capture_output=True, text=True
    )


# ---------------------------------------------------------------------------
# block：main 上控制面路徑 staged
# ---------------------------------------------------------------------------


def _stage(repo: Path, rel: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x\n")
    _git(repo, "add", rel)


def test_block_rules_on_main(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(repo, "rules/tool-discipline.md")
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "控制面路徑禁落 canonical main" in r.stderr
    assert "rules/tool-discipline.md" in r.stderr


def test_block_deep_module_agents_md(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(repo, "ai-analysis/blueprint/AGENTS.md")
    r = _run_guard(repo)
    assert r.returncode == 1


def test_block_skills_and_root_guide(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(repo, "skills/foo/SKILL.md")
    _stage(repo, "ai-development-guide.md")
    r = _run_guard(repo)
    assert r.returncode == 1


def test_block_unborn_main_head(tmp_path):
    """fresh clone 首 commit（unborn HEAD）不得繞過——symbolic-ref 仍讀到 main。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _stage(repo, "rules/x.md")
    r = _run_guard(repo)
    assert r.returncode == 1


# ---------------------------------------------------------------------------
# allow：卡 branch、backlog／一般路徑、scripts 不在閘面
# ---------------------------------------------------------------------------


def test_allow_card_branch_with_control_plane(tmp_path):
    repo = _init_repo(tmp_path, branch="air-1")
    _stage(repo, "rules/x.md")
    r = _run_guard(repo)
    assert r.returncode == 0


def test_allow_backlog_only_on_main(tmp_path):
    """例外①②③（建卡／開工／結案 metadata）只觸 backlog/——不得被擋。"""
    repo = _init_repo(tmp_path)
    _stage(repo, "backlog/tasks/air-1 - x.md")
    r = _run_guard(repo)
    assert r.returncode == 0


def test_allow_plain_files_on_main(tmp_path):
    repo = _init_repo(tmp_path)
    _stage(repo, "scripts/util.py")
    _stage(repo, "ai-analysis/reports/note.md")
    r = _run_guard(repo)
    assert r.returncode == 0


def test_allow_detached_head(tmp_path):
    """detached HEAD 非隔離對象（明示狀態，逃生靠 --no-verify 紀律）。"""
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "--detach")
    _stage(repo, "rules/x.md")
    r = _run_guard(repo)
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# 組裝：pre-commit 先跑 guard 再跑測試閘（block case 經真實 git commit 驗證）
# ---------------------------------------------------------------------------


def test_precommit_blocks_via_git_commit(tmp_path):
    """經真實 git commit 觸發 pre-commit——guard 先於 pytest（block 時不見 pytest 輸出）。"""
    repo = _init_repo(tmp_path)
    hooks = repo / ".githooks"
    hooks.mkdir()
    (hooks / "control-plane-guard.sh").write_text(GUARD.read_text())
    (hooks / "pre-commit").write_text(PRE_COMMIT.read_text())
    hooks.chmod(0o755)
    (hooks / "control-plane-guard.sh").chmod(0o755)
    (hooks / "pre-commit").chmod(0o755)
    _git(repo, "config", "core.hooksPath", ".githooks")
    _stage(repo, "skills/foo/SKILL.md")
    r = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "x"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "控制面路徑禁落 canonical main" in r.stderr
    assert "pytest" not in r.stdout + r.stderr
