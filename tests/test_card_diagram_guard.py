"""card-diagram-guard v5 單元測試——閘一（協議① desc 圖）＋閘二（終態圖契約
Done-transition）＋閘三（AIR-170 黑話掃描：Description 主體內部代號禁令）
＋結案結構 predicate 群（AIR-193：AC 殘留 a／status 軌跡 b／五段 marker c／
refs 警告 d／skip 語義分離／hooksPath 探針）。

harness：tmp git repo，HEAD 放 baseline 卡、index 放 staged 修改，直接跑 guard script 驗 exit code。
"""

import os
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
# AIR-193 五段樣板預設內容（Done 卡五段須齊——kanban「卡即 handoff」）
AC_TICKED = "- [x] #1 已完成項\n"
PLAN_BODY = "baseline／範圍／驗收\n"
NOTES_BODY = "結算筆記\n"


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


def _card(
    status: str,
    desc: str,
    fs: str | None = None,
    notes: str | None = None,
    ac: str | None = None,
    plan: str | None = None,
    refs: list[str] | None = None,
) -> str:
    """組卡。AIR-193 後 Done 卡五段須齊：ac／plan／notes 預設給樣板內容（ticked AC／
    樣板 plan／預設 notes），傳 "" 明確省略該段（測缺失用）；fs=None＝省略 FS；
    refs 非 None 時 frontmatter 加 references 清單。"""
    head = ["---", "id: AIR-900", "title: test", "status: " + status]
    if refs is not None:
        head += ["references:"] + ["  - " + r for r in refs]
    parts = head + [
        "---",
        "",
        "## Description",
        "<!-- SECTION:DESCRIPTION:BEGIN -->",
        desc,
        "<!-- SECTION:DESCRIPTION:END -->",
    ]
    if ac != "":
        parts += [
            "",
            "## Acceptance Criteria",
            "<!-- AC:BEGIN -->",
            AC_TICKED if ac is None else ac,
            "<!-- AC:END -->",
        ]
    if plan != "":
        parts += [
            "",
            "## Implementation Plan",
            "<!-- SECTION:PLAN:BEGIN -->",
            PLAN_BODY if plan is None else plan,
            "<!-- SECTION:PLAN:END -->",
        ]
    if notes != "":
        parts += [
            "",
            "## Implementation Notes",
            "<!-- SECTION:NOTES:BEGIN -->",
            NOTES_BODY if notes is None else notes,
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


def _run_guard(
    repo: Path, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(GUARD)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _commit_baseline(
    repo: Path, status: str, desc: str, fs: str | None, **card_kwargs
) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    Path(repo / card).write_text(_card(status, desc, fs, **card_kwargs))
    _git(repo, "add", card)
    _git(repo, "commit", "-q", "-m", "baseline")


def _stage_card(
    repo: Path,
    status: str,
    desc: str,
    fs: str | None,
    notes: str | None = None,
    **card_kwargs,
) -> None:
    card = "backlog/tasks/air-900 - test.md"
    (repo / card).parent.mkdir(parents=True, exist_ok=True)
    (repo / card).write_text(_card(status, desc, fs, notes, **card_kwargs))
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
    """legacy 卡（baseline 無 desc 圖）結案免終態圖——AIR-193 後段結構仍須齊：
    staged 給 FS 段（文字無圖）滿足五段地板，豁免面只免「圖」。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_NO_DIAGRAM, None)
    _stage_card(repo, "Done", DESC_NO_DIAGRAM, FS_NO_DIAGRAM)
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


# ── 結案結構 predicate 群（AIR-193 切片二）────────────────────────


def test_struct_ac_unticked_done_fails(tmp_path):
    """181 式樣本：Done 卡 AC 有未勾（無豁免標註）→ 擋（結案漏 tick 零 catcher 破口）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(
        repo,
        "Done",
        DESC_WITH_DIAGRAM,
        FS_WITH_DIAGRAM,
        ac="- [ ] #1 沒勾的項目\n- [x] #2 已勾項目\n",
    )
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "AC 殘留" in r.stderr
    assert "1 格未勾" in r.stderr
    assert "沒勾的項目" in r.stderr


def test_struct_ac_unticked_all_exempt_passes(tmp_path):
    """豁免語義：未勾行同行帶顯性拆卡/移交/總驗標註＝不計，全帶標註＝不擋（survey 條文）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(
        repo,
        "Done",
        DESC_WITH_DIAGRAM,
        FS_WITH_DIAGRAM,
        ac=(
            "- [ ] #1 殘項歸 AIR-999 小修批\n"
            "- [ ] #2 移交下批收斂\n"
            "- [ ] #3 拆卡另議\n"
            "- [ ] #4 總驗卡吸收\n"
        ),
    )
    assert _run_guard(repo).returncode == 0


def test_struct_status_todo_to_done_fails(tmp_path):
    """135.3 式樣本（本切片判準）：HEAD=To Do → staged=Done＝擋。

    註：工作序測試樣本字面寫「HEAD=To Do→staged=Done 合法通過」，與 b 條文
    「HEAD 非 In Progress→擋（破口＝To Do 直達 Done）」及 survey「軌跡合法
    （In Progress→Done）」矛盾——依 b 條文實作；若 marshal 裁決反向，
    改 guard 的 status_trajectory_violation 一處判準即可。
    """
    repo = _repo(tmp_path)
    _commit_baseline(repo, "To Do", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "status 軌跡" in r.stderr


def test_struct_status_in_progress_to_done_passes(tmp_path):
    """軌跡合法形：In Progress→Done 通過（survey「軌跡合法」）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    assert _run_guard(repo).returncode == 0


def test_struct_status_birth_done_entry_fails(tmp_path):
    """空白（無 HEAD 版本＝birth-Done entry）→ staged Done＝擋（工作序樣本「空白→擋」）。"""
    repo = _repo(tmp_path)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "status 軌跡" in r.stderr


def test_struct_status_already_done_edit_passes(tmp_path):
    """HEAD=Done→staged=Done＝已 Done 卡後續編輯，非軌跡事件不擋。

    註：工作序樣本字面寫「HEAD=Done→staged=Done 擋」，但那會擋掉 AIR-181 型
    「Done 後補勾」commit 本身、並破壞閘二「已 Done 不重觸發」既有契約——
    依後者實作，本測試釘住該語義。
    """
    repo = _repo(tmp_path)
    _commit_baseline(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    assert _run_guard(repo).returncode == 0


def test_struct_status_other_value_to_done_fails(tmp_path):
    """HEAD status 為其他值（如 In Review）→ Done 同樣擋（非 In Progress 即非合法軌跡）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Review", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "In Review" in r.stderr


def test_struct_section_missing_ac_fails(tmp_path):
    """AC marker 缺失＝c 擋（同時是 a 的繞行封口：刪 AC 段不能逃漏 tick 檢查）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM, ac="")
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "AC section 缺失" in r.stderr


def test_struct_section_missing_plan_warns(tmp_path):
    """marshal seal 裁定（0925）：PLAN/NOTES 缺失降 warning（存量相容）——不擋、stderr 提示。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM, plan="")
    r = _run_guard(repo)
    assert r.returncode == 0
    assert "PLAN section 缺失" in r.stderr
    assert "存量卡相容" in r.stderr


def test_struct_section_double_wrap_fails(tmp_path):
    """雙包裹（task edit 真實事故形態，kanban「卡編輯前查驗」）：NOTES BEGIN×2 → 擋。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(
        repo,
        "Done",
        DESC_WITH_DIAGRAM,
        FS_WITH_DIAGRAM,
        notes="筆記\n<!-- SECTION:NOTES:BEGIN -->\n",
    )
    r = _run_guard(repo)
    assert r.returncode == 1
    assert "NOTES markers malformed" in r.stderr


def test_struct_skip_env_disables_struct_only(tmp_path):
    """CARDCLOSE_STRUCT_SKIP=1：結構 predicate 逃生口（stderr 大聲標注），圖閘不受影響。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM, ac="- [ ] #1 沒勾\n")
    r = _run_guard(repo, {"CARDCLOSE_STRUCT_SKIP": "1"})
    assert r.returncode == 0
    assert "CARDCLOSE_STRUCT_SKIP" in r.stderr


def test_diagram_skip_keeps_struct_fail_closed(tmp_path):
    """CARD_DIAGRAM_SKIP 收窄：圖在場豁免不波及結構 predicate——181 卡照擋。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM, ac="- [ ] #1 沒勾\n")
    r = _run_guard(repo, {"CARD_DIAGRAM_SKIP": "1"})
    assert r.returncode == 1
    assert "AC 殘留" in r.stderr
    # 閘二確實被豁免（無「收 Done 缺」類訊息），擋的是結構 predicate
    assert "收 Done 缺" not in r.stderr


def test_refs_missing_path_warns_but_passes(tmp_path):
    """predicate d 警告級：refs 查無落地＝stderr 警告、不擋 commit（MOS-28 型）。"""
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(
        repo,
        "Done",
        DESC_WITH_DIAGRAM,
        FS_WITH_DIAGRAM,
        refs=["docs/not-tracked-yet.md"],
    )
    r = _run_guard(repo)
    assert r.returncode == 0
    assert "git 查無" in r.stderr


def test_refs_tracked_path_no_warning(tmp_path):
    repo = _repo(tmp_path)
    _commit_baseline(repo, "In Progress", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM)
    _stage_card(repo, "Done", DESC_WITH_DIAGRAM, FS_WITH_DIAGRAM, refs=["README.md"])
    r = _run_guard(repo)
    assert r.returncode == 0
    assert "git 查無" not in r.stderr


def test_hooks_path_unset_warns(tmp_path):
    """#2 探針：tmp repo 未設 core.hooksPath＝fail-open 面顯性警告一行（不擋）。"""
    repo = _repo(tmp_path)
    _stage_card(repo, "To Do", DESC_WITH_DIAGRAM, None)
    r = _run_guard(repo)
    assert r.returncode == 0
    assert "core.hooksPath 未設" in r.stderr
