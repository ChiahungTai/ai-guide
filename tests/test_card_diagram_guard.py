"""card-diagram-guard v4 單元測試——閘一（協議① desc 圖）＋閘二（終態圖契約
Done-transition）＋閘三（AIR-170 黑話掃描：Description 主體內部代號禁令）。

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
# 黑話 desc（有圖——隔離閘三變因）：D4/C5a/job-mu 在 prose、flash B 在 mermaid label
DESC_JARGON = (
    "這卡修 D4、C5a 與 job-mu-3f2a 的問題\n\n"
    '```mermaid\nflowchart LR\n  A["flash B"] --> B2\n```\n'
)
# 黑話全在豁免行（路徑特徵）＝證據指針，非主體黑話
DESC_JARGON_EXEMPT = (
    "證據指針（豁免行）：\n"
    ".agent-tmp/air-9/d4-notes.md 見 D4 記錄\n"
    "另見 backlog/tasks/air-9 - C5a 修補.md\n"
    "歷程 http://x/d4-log 內 C5a\n"
    "\n```mermaid\nflowchart LR\n  A --> B\n```\n"
)
# CJK 接鄰（F1 修正案）：\b 邊界在 Unicode 模式下 CJK 屬 \w，接鄰即失效——零命中事故
DESC_JARGON_CJK = "這卡修D4與C5a的問題\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
DESC_JARGON_CJK2 = "先完成D4再說\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
NOTES_JARGON = "進度：D4、C5a、flash B、job-mu-3f2a 出現在 Notes 不掃\n"


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


def _card(status: str, desc: str, fs: str | None, notes: str | None = None) -> str:
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
    if notes is not None:
        parts += [
            "",
            "## Notes",
            "<!-- SECTION:NOTES:BEGIN -->",
            notes,
            "<!-- SECTION:NOTES:END -->",
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
        [sys.executable, str(GUARD)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit_baseline(repo: Path, status: str, desc: str, fs: str | None) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    Path(repo / card).write_text(_card(status, desc, fs))
    _git(repo, "add", card)
    _git(repo, "commit", "-q", "-m", "baseline")


def _stage_card(
    repo: Path, status: str, desc: str, fs: str | None, notes: str | None = None
) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    (repo / card).write_text(_card(status, desc, fs, notes))
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
    _stage_card(
        repo,
        "Done",
        "人話修 typo\n\n```mermaid\nflowchart LR\n  A --> B\n```\n",
        FS_NO_DIAGRAM,
    )
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


# ── 閘三：黑話掃描（AIR-170 v4）──────────────────────────────────


def test_gate3_jargon_in_description_fails(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_JARGON, None)
    r = _run_guard(repo)
    assert r.returncode == 1
    # prose 行（desc 首行＝全檔 line 9）與 mermaid label 行都列行號＋命中詞
    assert "黑話" in r.stderr
    assert "line 9" in r.stderr
    assert "D4" in r.stderr
    assert "C5a" in r.stderr
    assert "job-mu-3f2a" in r.stderr
    assert "flash B" in r.stderr
    assert "改寫為人話" in r.stderr


def test_gate3_jargon_cjk_adjacent_fails(tmp_path):
    """F1：CJK 接鄰代號須命中——「這卡修D4與C5a的問題」擋 D4 與 C5a 兩詞。"""
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_JARGON_CJK, None)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "黑話" in r.stderr
    assert "D4" in r.stderr
    assert "C5a" in r.stderr


def test_gate3_jargon_cjk_wrapped_fails(tmp_path):
    """F1：代號前後皆 CJK（「先完成D4再說」）也須命中 D4。"""
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_JARGON_CJK2, None)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "D4" in r.stderr


def test_gate3_jargon_on_path_lines_exempt(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_JARGON_EXEMPT, None)
    assert _run_guard(repo).returncode == 0


def test_gate3_jargon_outside_description_not_scanned(tmp_path):
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_WITH_DIAGRAM, None, notes=NOTES_JARGON)
    assert _run_guard(repo).returncode == 0


def test_gate3_legacy_jargon_desc_notes_edit_passes(tmp_path):
    """delta 觸發面：desc 未動的修改（Notes）不追殺 legacy 黑話（同閘一遷移語義）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_JARGON, None)
    _stage_card(repo, "In Progress", DESC_JARGON, None, notes="結算筆記\n")
    assert _run_guard(repo).returncode == 0


def test_gate3_legacy_jargon_desc_edit_triggers(tmp_path):
    """desc 一旦修改（delta）即掃——下次觸及時順手搬。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_JARGON, None)
    _stage_card(repo, "In Progress", DESC_JARGON + "補一段\n", None)
    assert _run_guard(repo).returncode == 1
