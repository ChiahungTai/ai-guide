"""控制面 canonical 隔離閘測試（AIR-106）。

guard 是行為閘門核心——regression 直接改變隔離面：
漏抓 = 控制面條文落 canonical 即生效（F8 activation-before-review 洞重現）；
誤傷 = backlog／一般檔在 main 的合法 commit（例外①–④）被擋。
"""

import subprocess
from pathlib import Path

import pytest

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
# block：main 上控制面路徑 staged（一路徑一斷言——regex 各交替分支 typo 即紅）
# ---------------------------------------------------------------------------


def _stage(repo: Path, rel: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("x\n")
    _git(repo, "add", rel)


@pytest.mark.parametrize(
    "rel",
    [
        "rules/tool-discipline.md",
        "skills/foo/SKILL.md",
        "agents/roles/reviewer.md",
        "hooks/block-x.py",
        "deploy/entitlements-probe.plist",
        "muse-plugins/memory-governance/x.md",
        ".githooks/pre-commit",
        "tests/test_githooks.py",
        "scripts/deploy_agents.py",
        "ai-development-guide.md",
        "ai-analysis/blueprint/AGENTS.md",
        "CLAUDE.md",
    ],
)
def test_block_control_plane_paths_on_main(tmp_path, rel):
    repo = _init_repo(tmp_path)
    _stage(repo, rel)
    r = _run_guard(repo)
    assert r.returncode == 1, f"應擋未擋：{rel}"
    assert "控制面路徑禁落 canonical main" in r.stderr


def test_block_non_ascii_path_quotepath_regression(tmp_path):
    """quotePath regression（fresh 腿 F1 P0）：非 ASCII 路徑預設被 octal-escape＋
    引號包裹，pattern 三分支全失效＝gate 靜默放行。stderr 須見 raw 路徑。"""
    repo = _init_repo(tmp_path)
    _stage(repo, "rules/工具規範.md")
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "rules/工具規範.md" in r.stderr


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
