"""控制面 canonical 隔離閘測試（AIR-106）。

guard 是行為閘門核心——regression 直接改變隔離面：
漏抓 = 控制面條文落 canonical 即生效（F8 activation-before-review 洞重現）；
誤傷 = backlog／一般檔在 main 的合法 commit（例外①–④）被擋。
"""

import os
import subprocess
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent.parent / ".githooks" / "control-plane-guard.sh"
PRE_COMMIT = Path(__file__).resolve().parent.parent / ".githooks" / "pre-commit"
CARD_DIAGRAM_GUARD = Path(__file__).resolve().parent.parent / ".githooks" / "card-diagram-guard.py"


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
    if rel.startswith("backlog/tasks/"):
        # card-diagram guard v2：backlog 卡須合法 SECTION markers＋mermaid 圖（135.5 協議①）
        f.write_text(
            "## Description\n"
            "<!-- SECTION:DESCRIPTION:BEGIN -->\n"
            "desc\n\n"
            "```mermaid\nflowchart LR\n  A --> B\n```\n"
            "<!-- SECTION:DESCRIPTION:END -->\n"
        )
    else:
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
        "governance/install.py",
        "governance/registrations/zcode.json",
        ".githooks/pre-commit",
        "tests/test_githooks.py",
        "scripts/deploy_agents.py",
        "scripts/sync_agents.py",
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
# allow：卡 branch、backlog／一般路徑；生成器類 scripts（deploy/sync_agents）在閘面
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


# ---------------------------------------------------------------------------
# backlog fast path（AIR-125 AC#1）：staged 全屬 backlog/ → 跳 pytest 腿
# （guard＋py_compile 照跑）。沙箱＝hook 副本＋可編譯空 .py（py_compile 腿真跑通）；
# 沙箱無測試環境——pytest 腿一旦被觸發必失敗，故「exit 0」即短路證據。
# ---------------------------------------------------------------------------


def _hook_sandbox(tmp_path: Path) -> Path:
    repo = _init_repo(tmp_path)
    hooks_dir = repo / ".githooks"
    hooks_dir.mkdir()
    (hooks_dir / "control-plane-guard.sh").write_text(GUARD.read_text())
    (hooks_dir / "pre-commit").write_text(PRE_COMMIT.read_text())
    (hooks_dir / "card-diagram-guard.py").write_text(CARD_DIAGRAM_GUARD.read_text())
    hooks_dir.chmod(0o755)
    (hooks_dir / "control-plane-guard.sh").chmod(0o755)
    (hooks_dir / "pre-commit").chmod(0o755)
    # py_compile 腿的真實 glob 目標（空可編譯檔——腿通但不涉及測試環境）
    (repo / "hooks").mkdir()
    (repo / "hooks" / "keep.py").write_text("")
    (repo / "skills" / "memory-audit" / "scripts").mkdir(parents=True)
    (repo / "skills" / "memory-audit" / "scripts" / "keep.py").write_text("")
    return repo


def _run_precommit(repo: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "PRE_COMMIT"}
    return subprocess.run(
        ["bash", str(repo / ".githooks" / "pre-commit")],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_fastpath_backlog_only_skips_pytest(tmp_path):
    """staged 全屬 backlog/ → hook 短路 exit 0＋[fast-path] 訊息、無 pytest 痕跡。
    含非 ASCII 卡檔名腿（quotePath=false 判準——control-plane-guard 同款教訓）。
    冪等：同一 staged 態連跑兩次同結果（AC#1 冪等驗證）。"""
    repo = _hook_sandbox(tmp_path)
    _stage(repo, "backlog/tasks/air-9 - 中文卡名.md")
    for _ in range(2):
        r = _run_precommit(repo)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "[fast-path]" in r.stdout, r.stdout
        assert "pytest" not in r.stdout + r.stderr


def test_fastpath_not_triggered_for_non_backlog(tmp_path):
    repo = _hook_sandbox(tmp_path)
    _stage(repo, "scripts/util.py")
    r = _run_precommit(repo)
    assert r.returncode != 0  # 沙箱無測試環境——pytest 腿被觸發即非 0
    assert "[fast-path]" not in r.stdout


def test_fastpath_not_triggered_for_mixed_staged(tmp_path):
    repo = _hook_sandbox(tmp_path)
    _stage(repo, "backlog/tasks/air-9 - x.md")
    _stage(repo, "scripts/util.py")
    r = _run_precommit(repo)
    assert r.returncode != 0
    assert "[fast-path]" not in r.stdout


def test_fastpath_empty_staged_not_triggered(tmp_path):
    """空 staged（手動直跑 hook 場）不判 fast path——「全屬」對空集採保守走全量。"""
    repo = _hook_sandbox(tmp_path)
    r = _run_precommit(repo)
    assert r.returncode != 0
    assert "[fast-path]" not in r.stdout


# ---------------------------------------------------------------------------
# live-reading 隔離（AIR-125 AC#2）：hook 設 PRE_COMMIT=1 → live 面測試 skip。
# 職責歸位：live drift 偵測單一歸宿＝installer --check＋launchd monitor 日頻，
# 不在 commit gate——commit gate 對機器 live config 維持確定性。
# ---------------------------------------------------------------------------


REPO_ROOT = PRE_COMMIT.parent.parent
LIVE_TEST_FILE = "tests/test_matcher_parity.py"


def _pytest_rs_output(pre_commit_env: str | None) -> str:
    """以 subprocess 跑 live 面測試檔（-rs 顯示 skip reason），回傳合併輸出。"""
    env = {k: v for k, v in os.environ.items() if k != "PRE_COMMIT"}
    if pre_commit_env is not None:
        env["PRE_COMMIT"] = pre_commit_env
    r = subprocess.run(
        ["uv", "run", "pytest", LIVE_TEST_FILE, "-rs", "-q", "--no-header"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
        check=False,
    )
    return r.stdout + r.stderr


def test_precommit_exports_pre_commit_env_before_pytest():
    """hook 側錨：export PRE_COMMIT=1 須先於 pytest 腿（live 面才能辨識 hook 模式）。"""
    text = PRE_COMMIT.read_text(encoding="utf-8")
    export_idx = text.index("export PRE_COMMIT=1")
    pytest_idx = text.index("uv run pytest")
    assert export_idx < pytest_idx


def test_live_face_skipped_when_pre_commit_env_set():
    """帶 PRE_COMMIT=1 → live 面測試被 skip，skip reason 帶 hook 模式標記（-rs 可見）。"""
    out = _pytest_rs_output("1")
    assert "skipped" in out.lower(), out
    assert "PRE_COMMIT" in out, out


@pytest.mark.skipif(
    os.environ.get("PRE_COMMIT") == "1",
    reason="對照腿須移除 PRE_COMMIT 巢跑——在 commit gate 內執行＝gate 內重開"
           " live 面（有 live config 的機器上破壞 AC#2 確定性，codex review"
           " 補抓）；對照驗證歸常規（無標記）pytest 場",
)
def test_live_face_not_pre_commit_skipped_without_env():
    """對照腿：不帶 PRE_COMMIT → 無 hook 模式 skip（pass 或 live-config-absent skip
    ——card WT 缺 gitignored settings.json 屬後者，reason 不含 PRE_COMMIT）。"""
    out = _pytest_rs_output(None)
    assert "PRE_COMMIT" not in out, out
