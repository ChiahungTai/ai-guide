"""backlog_precheck.sh 反向檢查測試（AIR-108）。

反向檢查是收卡防護核心——regression 直接改變防護面：
漏抓 = 做完未收卡（SC-32 形態——實作落地、卡面落後，下個 session 當新工重派）；
誤傷 = bookkeeping commit（chore(backlog)）或 Done 卡被擋（結案序列死鎖）。
"""

import subprocess
from pathlib import Path

PRECHECK = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "kanban-board"
    / "scripts"
    / "backlog_precheck.sh"
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


def _card(repo: Path, card_id: str, status: str) -> None:
    f = repo / "backlog" / "tasks" / f"{card_id.lower()}-t.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"---\nid: {card_id}\nstatus: {status}\n---\n")
    _git(repo, "add", str(f.relative_to(repo)))


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "commit", "-q", "--allow-empty", "-m", msg)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    return repo


def _run(repo: Path, *ids: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(PRECHECK), *ids], cwd=repo, capture_output=True, text=True
    )


def test_block_todo_with_impl_commit(tmp_path):
    """To Do 卡＋本線實作 commit → [需裁決] 擋（做完未收卡）。"""
    repo = _init_repo(tmp_path)
    _card(repo, "AIR-900", "To Do")
    _commit(repo, "feat(air-900): 實作某功能")
    r = _run(repo, "AIR-900")
    assert r.returncode == 1
    assert "[需裁決]" in r.stdout
    assert "feat(air-900)" in r.stdout


def test_allow_todo_with_bookkeeping_only(tmp_path):
    """To Do 卡＋僅 bookkeeping commit（chore(backlog)）→ 可清。"""
    repo = _init_repo(tmp_path)
    _card(repo, "AIR-901", "To Do")
    _commit(repo, "chore(backlog): AIR-901 開工——In Progress＋refs")
    r = _run(repo, "AIR-901")
    assert r.returncode == 0
    assert "[可清]" in r.stdout


def test_allow_done_card_with_impl_commit(tmp_path):
    """Done 卡＋實作 commit → 反向檢查跳過（翻卡即裁決完成——結案序列不死鎖）。"""
    repo = _init_repo(tmp_path)
    _card(repo, "AIR-902", "Done")
    _commit(repo, "feat(air-902): 實作某功能")
    r = _run(repo, "AIR-902")
    assert r.returncode == 0
    assert "[可清]" in r.stdout


def test_block_in_progress_unchanged(tmp_path):
    """In Progress 卡 → 既有阻擋不變。"""
    repo = _init_repo(tmp_path)
    _card(repo, "AIR-903", "In Progress")
    _commit(repo, "chore(backlog): AIR-903 開工")
    r = _run(repo, "AIR-903")
    assert r.returncode == 1
    assert "[不可清]" in r.stdout


def test_cross_line_and_reverse_both_fire(tmp_path):
    """跨線＋反向兩訊號並存 → 兩訊息都出、exit 1（無矛盾可清輸出）。"""
    repo = _init_repo(tmp_path)
    _card(repo, "AIR-904", "To Do")
    _commit(repo, "feat(air-904): 實作某功能")
    # 造跨線訊號：他 branch 有提及此卡的 commit
    _git(repo, "checkout", "-q", "-b", "other")
    _commit(repo, "docs: air-904 相關討論")
    _git(repo, "checkout", "-q", "main")
    r = _run(repo, "AIR-904")
    assert r.returncode == 1
    assert "跨線訊號" in r.stdout
    assert "[需裁決]" in r.stdout
    assert r.stdout.count("[可清]") == 0
