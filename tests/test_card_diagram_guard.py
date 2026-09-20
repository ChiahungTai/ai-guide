"""card-diagram-guard v3 單元測試——閘一（協議① desc 圖）＋閘二（終態圖契約 Done-transition）。

harness：tmp git repo，HEAD 放 baseline 卡、index 放 staged 修改，直接跑 guard script 驗 exit code。
"""

import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / ".githooks" / "card-diagram-guard.py"

DESC_WITH_DIAGRAM = "人話\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
DESC_NO_DIAGRAM = "人話無圖\n"
FS_WITH_DIAGRAM = "結算\n\n```mermaid\nflowchart LR\n  A2 --> B2\n```\n"
FS_NO_DIAGRAM = "結算文字只有人話\n"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "user.email", "t@t")
    (repo / "README.md").write_text("seed\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _card(status: str, desc: str, fs: str | None) -> str:
    parts = [
        "---",
        "id: AIR-900",
        "title: test",
        "status: " + status,
        "---",
        "",
        "## Description",
        "<!-- SECTION:DESCRIPTION:BEGIN -->",
        desc,
        "<!-- SECTION:DESCRIPTION:END -->",
    ]
    if fs is not None:
        parts += [
            "",
            "## Final Summary",
            "<!-- SECTION:FINAL_SUMMARY:BEGIN -->",
            fs,
            "<!-- SECTION:FINAL_SUMMARY:END -->",
        ]
    return "\n".join(parts) + "\n"


def _run_guard(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GUARD)], cwd=repo, capture_output=True, text=True, check=False
    )


def _commit_baseline(repo: Path, status: str, desc: str, fs: str | None) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    Path(repo / card).write_text(_card(status, desc, fs))
    _git(repo, "add", card)
    _git(repo, "commit", "-q", "-m", "baseline")


def _stage_card(repo: Path, status: str, desc: str, fs: str | None) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    (repo / card).write_text(_card(status, desc, fs))
    _git(repo, "add", card)


def test_gate1_new_card_without_desc_mermaid_fails(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_NO_DIAGRAM, None)
    assert _run_guard(repo).returncode == 1


def test_gate1_new_card_with_desc_mermaid_passes(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_WITH_DIAGRAM, None)
    assert _run_guard(repo).returncode == 0


def test_gate2_done_without_fs_mermaid_fails(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, None)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, None)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "終態圖" in r.stderr


def test_gate2_done_with_fs_mermaid_passes(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, None)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    assert _run_guard(repo).returncode == 0


def test_gate2_done_missing_fs_section_fails(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, None)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, None)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "Final Summary" in r.stderr


def test_gate2_done_fs_without_mermaid_fails(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_NO_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_NO_DIAGRAM)
    assert _run_guard(repo).returncode == 1


def test_gate2_legacy_card_without_entry_diagram_exempt(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_NO_DIAGRAM, None)
    _stage_card(repo, "Done", DESC_NO_DIAGRAM, None)
    assert _run_guard(repo).returncode == 0


def test_gate2_already_done_typo_edit_not_retriggered(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", "人話修 typo\n\n```mermaid\nflowchart LR\n  A --> B\n```\n", FS_NO_DIAGRAM)
    assert _run_guard(repo).returncode == 0


def test_gate2_in_progress_edit_not_triggered(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "To Do", DESC_WITH_DIAGRAM, None)
    _stage_card(repo, "In Progress", DESC_WITH_DIAGRAM, None)
    assert _run_guard(repo).returncode == 0


def test_gate2_birth_done_entry_requires_fs_mermaid(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, None)
    assert _run_guard(repo).returncode == 1
