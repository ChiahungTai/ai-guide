"""closeout_check --all-done 歷史軌跡稽核測試（AIR-208 F2，muse 設計測試清單）
＋F1 CLI 接線釘測（AC#1：guard 與 CLI 同報 duplicate＋residue）。

harness：pytest tmp_path 內建 tmp git repo，逐 commit 造 status 歷史。
baseline 注入：guard 常數 STATUS_TRAJECTORY_AUDIT_BASELINE 是 ai-guide repo 的
immutable OID，tmp repo 必然無此 commit——測試以「patch guard 模組常數＝tmp repo
anchor commit sha」驅動正常路徑；以「保留真常數」自然落在 baseline-unavailable
fail-closed 路徑（＝shallow clone 語義，muse 清單 6）。
"""

import contextlib
import importlib.util
import io
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOSEOUT = REPO_ROOT / "scripts" / "closeout_check.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("closeout_check_under_test", CLOSEOUT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CLI = _load_cli()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _head_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


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


def _card_text(
    status: str, card_id: str = "AIR-900", ac: str | None = "- [x] #1 done\n"
) -> str:
    """五段齊的合法卡（結構 predicate 全過——隔離歷史稽核變因）；ac=None＝整段
    省略 AC markers（heading-fallback 形態測試用）。"""
    parts = [
        "---",
        "id: " + card_id,
        "title: test",
        "status: " + status,
        "---",
        "",
        "## Description",
        "<!-- SECTION:DESCRIPTION:BEGIN -->",
        "人話描述",
        "<!-- SECTION:DESCRIPTION:END -->",
    ]
    if ac is not None:
        parts += [
            "",
            "## Acceptance Criteria",
            "<!-- AC:BEGIN -->",
            ac,
            "<!-- AC:END -->",
        ]
    parts += [
        "",
        "## Implementation Plan",
        "<!-- SECTION:PLAN:BEGIN -->",
        "plan",
        "<!-- SECTION:PLAN:END -->",
        "",
        "## Implementation Notes",
        "<!-- SECTION:NOTES:BEGIN -->",
        "notes",
        "<!-- SECTION:NOTES:END -->",
        "",
        "## Final Summary",
        "<!-- SECTION:FINAL_SUMMARY:BEGIN -->",
        "summary",
        "<!-- SECTION:FINAL_SUMMARY:END -->",
    ]
    return "\n".join(parts) + "\n"


def _commit_file(repo: Path, relpath: str, text: str, msg: str) -> str:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    _git(repo, "add", relpath)
    _git(repo, "commit", "-q", "-m", msg)
    return _head_sha(repo)


def _baseline_commit(repo: Path) -> str:
    """空 commit 當 tmp repo 的軌跡 baseline anchor，回 sha。"""
    _git(repo, "commit", "-q", "--allow-empty", "-m", "trajectory baseline")
    return _head_sha(repo)


def _run_all_done(repo: Path, baseline_sha: str, *extra: str):
    """in-process 跑 CLI --all-done（chdir＋patch guard baseline 常數）。回 (rc, out, err)。"""
    g = CLI._load_guard()
    g.STATUS_TRAJECTORY_AUDIT_BASELINE = baseline_sha
    orig_loader = CLI._load_guard
    CLI._load_guard = lambda: g
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            rc = CLI.main(["--all-done", *extra])
        return rc, buf_out.getvalue(), buf_err.getvalue()
    finally:
        CLI._load_guard = orig_loader
        os.chdir(old_cwd)


CARD = "backlog/tasks/air-900 - test.md"


# ── muse 清單 1：WT=Done、HEAD=Done、baseline 後 To Do→Done → violation ──


def test_f2_todo_to_done_post_baseline_violation(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("To Do"), "create")
    baseline = _baseline_commit(repo)
    flip_sha = _commit_file(repo, CARD, _card_text("Done"), "flip todo->done directly")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "歷史軌跡" in out
    assert "To Do" in out and "Done" in out
    assert flip_sha[:12] in out  # AC#3：含跳變 commit hash


# ── muse 清單 2：To Do→In Progress→Done（baseline 後）→ clean ──


def test_f2_todo_to_in_progress_to_done_clean(tmp_path):
    repo = _repo(tmp_path)
    baseline = _baseline_commit(repo)
    _commit_file(repo, CARD, _card_text("To Do"), "create")
    _commit_file(repo, CARD, _card_text("In Progress"), "wip")
    _commit_file(repo, CARD, _card_text("Done"), "close")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out
    assert "PASS" in out


# ── muse 清單 3：非法跳變在 baseline 之前、之後無變遷 → clean（祖父化證明）──


def test_f2_pre_baseline_illegal_jump_grandfathered(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("To Do"), "create")
    _commit_file(repo, CARD, _card_text("Done"), "illegal flip pre-baseline")
    baseline = _baseline_commit(repo)
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out


# ── muse 清單 4：清單 3＋baseline 後一次 Done→Done 內容編輯 → clean ──


def test_f2_pre_baseline_jump_plus_post_done_edit_clean(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("To Do"), "create")
    _commit_file(repo, CARD, _card_text("Done"), "illegal flip pre-baseline")
    baseline = _baseline_commit(repo)
    _commit_file(
        repo, CARD, _card_text("Done").replace("notes", "notes 補記"), "done->done edit"
    )
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out


# ── muse 清單 5：tasks→completed rename＋合法軌跡 → clean ──


def test_f2_rename_to_completed_legal_clean(tmp_path):
    repo = _repo(tmp_path)
    # anchor：Done 卡留 tasks/（盲點集合非空——稽核實際會跑）
    _commit_file(
        repo,
        "backlog/tasks/air-900 - anchor.md",
        _card_text("Done", card_id="AIR-900"),
        "anchor done",
    )
    mover = "backlog/tasks/air-901 - mover.md"
    _commit_file(repo, mover, _card_text("To Do", card_id="AIR-901"), "create mover")
    baseline = _baseline_commit(repo)
    _commit_file(repo, mover, _card_text("In Progress", card_id="AIR-901"), "wip")
    # rename＋翻 Done 同一 commit（git mv 後改內容）
    newp = "backlog/completed/air-901 - mover.md"
    (repo / newp).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", mover, newp)
    (repo / newp).write_text(_card_text("Done", card_id="AIR-901"), encoding="utf-8")
    _git(repo, "add", newp)
    _git(repo, "commit", "-q", "-m", "close and move")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out


# ── round-2（muse#1＋codex#2）：violation scope 綁盲點集合 id ──────────────
# 舊測試（rename_with_illegal_flip_fails）把「completed 側他卡非法翻轉也 FAIL」
# 鎖成預期——scope expansion 與設計（completed 僅 path universe）衝突，本測試反轉
# 鎖定：非盲點卡 lineage 事件照走（rename 鏈）但不產 verdict。


def test_f2_non_blind_completed_flip_not_reported(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(
        repo,
        "backlog/tasks/air-900 - anchor.md",
        _card_text("Done", card_id="AIR-900"),
        "anchor done",
    )
    mover = "backlog/tasks/air-901 - mover.md"
    _commit_file(repo, mover, _card_text("To Do", card_id="AIR-901"), "create mover")
    baseline = _baseline_commit(repo)
    newp = "backlog/completed/air-901 - mover.md"
    (repo / newp).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", mover, newp)
    (repo / newp).write_text(_card_text("Done", card_id="AIR-901"), encoding="utf-8")
    _git(repo, "add", newp)
    _git(repo, "commit", "-q", "-m", "illegal close and move (non-blind card)")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out


# ── muse 清單 6：baseline 不可用（shallow clone 語義）→ fail-closed 非零非 pass ──


def test_f2_baseline_unavailable_fails_closed(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done")
    real_baseline = CLI._load_guard().STATUS_TRAJECTORY_AUDIT_BASELINE
    rc, out, err = _run_all_done(repo, real_baseline)  # tmp repo 必無此 OID
    assert rc != 0
    assert "ERROR" in out
    assert "baseline" in (out + err)
    assert "歷史軌跡違規" not in out  # 不是 violation——是無法驗證


def test_f2_baseline_not_ancestor_fails_closed(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done")
    # baseline＝未被 merge 的 side branch commit（存在但非 HEAD 祖先）
    _git(repo, "checkout", "-q", "-b", "side")
    side_sha = _commit_file(repo, "side.txt", "side\n", "side commit")
    _git(repo, "checkout", "-q", "main")
    _commit_file(repo, "README.md", "main advance\n", "main advance")
    rc, out, _err = _run_all_done(repo, side_sha)
    assert rc != 0
    assert "ERROR" in out
    assert "祖先" in out


# ── muse 清單 7：post-baseline 中間 commit 解析失敗 → history-gap 警告、不報 violation ──


def test_f2_post_baseline_parse_failure_gap_warns_no_violation(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done pre-baseline")
    baseline = _baseline_commit(repo)
    broken = _card_text("Done").replace("status: Done", "state: Done")
    _commit_file(repo, CARD, broken, "broken edit")
    _commit_file(repo, CARD, _card_text("Done"), "restore")
    rc, out, err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "history-gap" in err
    assert "歷史軌跡" not in out


# ── muse 清單 8：baseline 後新建卡首見即 Done → violation（birth-Done）──


def test_f2_birth_done_post_baseline_violation(tmp_path):
    repo = _repo(tmp_path)
    baseline = _baseline_commit(repo)
    _commit_file(repo, CARD, _card_text("Done"), "born done")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "歷史軌跡" in out
    assert "（新建" in out


# ── codex 腿：同 commit 重複卡 id（D/A 無法唯一配對的確定形）→ identity-ambiguous ──


def test_f2_duplicate_ids_identity_ambiguous_fails_closed(tmp_path):
    repo = _repo(tmp_path)
    baseline = _baseline_commit(repo)
    # 同「一個」commit 新增兩個同 id 卡檔——A 側 id 重複＝無法唯一配對
    (repo / "backlog/tasks/air-950 - a.md").parent.mkdir(parents=True, exist_ok=True)
    (repo / "backlog/tasks/air-950 - a.md").write_text(
        _card_text("Done", card_id="AIR-950"), encoding="utf-8"
    )
    (repo / "backlog/tasks/air-950 - b.md").write_text(
        _card_text("Done", card_id="AIR-950"), encoding="utf-8"
    )
    _git(repo, "add", "backlog/tasks")
    _git(repo, "commit", "-q", "-m", "add dup ids in one commit")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out
    assert "ERROR" in out


# ── plan ⑤：--no-history 逃生 flag（預設全審）──


def test_f2_no_history_flag_skips_audit(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("To Do"), "create")
    baseline = _baseline_commit(repo)
    _commit_file(repo, CARD, _card_text("Done"), "flip todo->done directly")
    rc, out, err = _run_all_done(repo, baseline, "--no-history")
    assert rc == 0
    assert "歷史軌跡" not in out
    assert "--no-history" in err


# ── 歷史稽核只跑 --all-done（明確卡路徑呼叫不觸發、不因 baseline 缺而炸）──


def test_f2_no_audit_on_explicit_card_invocation(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done")
    g = CLI._load_guard()  # baseline 維持真常數（tmp repo 無此 OID）
    orig_loader = CLI._load_guard
    CLI._load_guard = lambda: g
    old_cwd = os.getcwd()
    os.chdir(repo)
    try:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            rc = CLI.main([CARD])
        out = buf_out.getvalue()
    finally:
        CLI._load_guard = orig_loader
        os.chdir(old_cwd)
    assert rc == 0
    assert "PASS" in out
    assert "ERROR" not in out


# ── AIR-208 F1 CLI 接線釘測（AC#1：guard 與 CLI 同報 duplicate＋residue）──


def test_f1_cli_reports_duplicate_and_residue(tmp_path):
    repo = _repo(tmp_path)
    text = _card_text("Done", ac=None) + (
        "\n## Acceptance Criteria\n- [x] #1 全勾\n"
        "\n## Acceptance Criteria\n- [ ] #2 藏洞項\n"
    )
    _commit_file(repo, CARD, text, "dup heading card")
    baseline = _head_sha(repo)
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "AC 標題重複" in out
    assert "AC 殘留" in out
    assert "藏洞項" in out


# ══ AIR-208 round-2（review 合議 findings）══════════════════════════════
# 大幅改寫 filler——使 git -M 相似度退化 <50%，rename 拆成 D+A 兩事件
_SPLIT_OLD_FILLER = "".join(f"舊版脈絡行 {i}：alpha 說明 alpha\n" for i in range(60))
_SPLIT_NEW_FILLER = "".join(f"新版脈絡行 {i}：beta 記錄 beta\n" for i in range(60))


def _split_rename_commit(repo: Path, src: str, dst: str, new_text: str) -> None:
    (repo / dst).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", src, dst)
    (repo / dst).write_text(new_text, encoding="utf-8")
    _git(repo, "add", dst)
    _git(repo, "commit", "-q", "-m", "massive rewrite plus rename")


def _assert_degraded_to_d_a(repo: Path) -> None:
    """釘住 -M 確實退化為 D+A——本組測試真正走在 split-rename 配對路徑。"""
    out = subprocess.run(
        [
            "git",
            "diff-tree",
            "--no-commit-id",
            "-r",
            "-M",
            "--name-status",
            "HEAD^",
            "HEAD",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    codes = sorted(ln.split("\t")[0] for ln in out.strip().splitlines())
    assert codes == ["A", "D"], f"-M 未退化為 D+A：{codes}"


# ── codex#1（高）：M/R 不得丟棄 frontmatter id——identity 自證 fail-closed ──


def test_f2_m_event_id_swap_identity_ambiguous_fails_closed(tmp_path):
    """同路徑 M 事件換 id＋翻 Done——新 identity 繼承舊 identity 的合法前驅
    （In Progress→Done），繞過 birth-Done 檢查的攻擊形 → identity-ambiguous。"""
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("In Progress"), "create in progress")
    baseline = _baseline_commit(repo)
    _commit_file(repo, CARD, _card_text("Done", card_id="AIR-999"), "swap id and flip")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out


def test_f2_rename_different_id_identity_ambiguous_fails_closed(tmp_path):
    """-M 把不同 id 的兩卡判成 rename（相似度高）→ lineage id 不一致 → error。"""
    repo = _repo(tmp_path)
    src = "backlog/tasks/air-901 - src.md"
    _commit_file(repo, src, _card_text("In Progress", card_id="AIR-901"), "create")
    baseline = _baseline_commit(repo)
    dst = "backlog/completed/air-902 - dst.md"
    (repo / dst).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", src, dst)
    (repo / dst).write_text(_card_text("Done", card_id="AIR-902"), encoding="utf-8")
    _git(repo, "add", dst)
    _git(repo, "commit", "-q", "-m", "rename carrying different id")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out


# ── muse#1＋codex#2(a)：gate 與盲點集合解耦——post-baseline 卡事件即跑 ──


def test_f2_audit_gate_decoupled_from_done_cards(tmp_path):
    """無任何 Done 卡（--all-done 候選空）但 completed 側有 post-baseline 事件——
    舊碼靜默跳過（證據完整性 error 被吞），修正後稽核照跑、identity error 照報。"""
    repo = _repo(tmp_path)
    src = "backlog/tasks/air-907 - x.md"
    _commit_file(repo, src, _card_text("In Progress", card_id="AIR-907"), "create")
    baseline = _baseline_commit(repo)
    dst = "backlog/completed/air-908 - y.md"
    (repo / dst).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", src, dst)
    (repo / dst).write_text(_card_text("Done", card_id="AIR-908"), encoding="utf-8")
    _git(repo, "add", dst)
    _git(repo, "commit", "-q", "-m", "id change under rename, no done cards")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out


def test_f2_no_post_baseline_events_skips_audit(tmp_path):
    """baseline 後僅非卡檔變更——無可審歷史，稽核跳過須顯性註記（fail-visible）。"""
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done pre-baseline")
    baseline = _baseline_commit(repo)
    _commit_file(repo, "README.md", "docs only\n", "non-card change")
    rc, out, err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out
    assert "無卡檔事件" in err


# ── muse#2＋codex#3：error/gap 分流——git 指令失敗＝error 非零，非警告放行 ──


class _ShFail:
    returncode = 1
    stdout = ""
    stderr = "simulated failure"


def test_f2_diff_tree_failure_is_error_not_gap(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done")
    baseline = _baseline_commit(repo)
    _commit_file(
        repo, CARD, _card_text("Done").replace("notes", "notes 補記"), "post edit"
    )
    orig_sh = CLI.sh

    def broken_sh(*args, **kwargs):
        if len(args) > 3 and args[0] == "git" and args[3] == "diff-tree":
            return _ShFail()
        return orig_sh(*args, **kwargs)

    CLI.sh = broken_sh
    try:
        rc, out, _err = _run_all_done(repo, baseline)
    finally:
        CLI.sh = orig_sh
    assert rc != 0
    assert "ERROR" in out
    assert "diff-tree 失敗" in out


def test_f2_git_show_failure_is_error_not_gap(tmp_path):
    repo = _repo(tmp_path)
    _commit_file(repo, CARD, _card_text("Done"), "done")
    baseline = _baseline_commit(repo)
    _commit_file(
        repo, CARD, _card_text("Done").replace("notes", "notes 補記"), "post edit"
    )
    orig_sh = CLI.sh

    def broken_sh(*args, **kwargs):
        # 只打斷稽核的歷史 blob 讀取（<sha>:<path>）——WT/HEAD 讀取（HEAD: 前綴）照常
        if (
            len(args) > 4
            and args[0] == "git"
            and args[3] == "show"
            and ":" in args[4]
            and not args[4].startswith("HEAD:")
        ):
            return _ShFail()
        return orig_sh(*args, **kwargs)

    CLI.sh = broken_sh
    try:
        rc, out, _err = _run_all_done(repo, baseline)
    finally:
        CLI.sh = orig_sh
    assert rc != 0
    assert "ERROR" in out
    assert "git show" in out


# ── muse#6＋codex#4：pin 測試——純 rename Done→Done、D 側重複 id ──


def test_f2_pure_rename_done_to_done_clean(tmp_path):
    """純 git mv 無內容變更（Done→Done R100）→ 自然過（clean pin）。"""
    repo = _repo(tmp_path)
    _commit_file(
        repo,
        "backlog/tasks/air-900 - anchor.md",
        _card_text("Done", card_id="AIR-900"),
        "anchor done",
    )
    src = "backlog/tasks/air-906 - mover.md"
    _commit_file(repo, src, _card_text("Done", card_id="AIR-906"), "create done mover")
    baseline = _baseline_commit(repo)
    dst = "backlog/completed/air-906 - mover.md"
    (repo / dst).parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", src, dst)
    _git(repo, "commit", "-q", "-m", "pure move, no content change")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out
    assert "identity-ambiguous" not in out


def test_f2_d_side_duplicate_ids_identity_ambiguous_fails_closed(tmp_path):
    """同 commit 刪兩張同 id 卡——D 側重複 id＝identity-ambiguous（A 側對應測試
    已有，此為 muse#6 指名的 D 側 pin；同時依賴 gate 解耦：無 Done 卡稽核照跑）。"""
    repo = _repo(tmp_path)
    a = "backlog/tasks/air-950 - a.md"
    b = "backlog/tasks/air-950 - b.md"
    _commit_file(repo, a, _card_text("In Progress", card_id="AIR-950"), "create a")
    _commit_file(repo, b, _card_text("In Progress", card_id="AIR-950"), "create b dup")
    baseline = _baseline_commit(repo)
    _git(repo, "rm", "-q", a, b)
    _git(repo, "commit", "-q", "-m", "delete two same-id cards in one commit")
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out


# ── codex#4：真實 D+A split-rename（-M 退化）——唯一配對成功＋缺 id fail-closed ──


def test_f2_split_rename_unique_pairing_clean(tmp_path):
    """同 id 卡大幅改寫＋rename 使 -M 退化為 D+A——id 唯一配對復原 lineage
    （In Progress→Done 合法）；配對失敗會以 birth-Done 報 violation，rc==0 即證明
    唯一配對成功。"""
    repo = _repo(tmp_path)
    src = "backlog/tasks/air-903 - big.md"
    old_text = _card_text("In Progress", card_id="AIR-903") + "\n" + _SPLIT_OLD_FILLER
    _commit_file(repo, src, old_text, "create big card")
    baseline = _baseline_commit(repo)
    dst = "backlog/tasks/air-903 - renamed.md"
    new_text = _card_text("Done", card_id="AIR-903") + "\n" + _SPLIT_NEW_FILLER
    _split_rename_commit(repo, src, dst, new_text)
    _assert_degraded_to_d_a(repo)
    rc, out, err = _run_all_done(repo, baseline)
    assert rc == 0
    assert "歷史軌跡" not in out
    assert "identity-ambiguous" not in out
    assert "history-gap" not in err


def test_f2_split_rename_missing_new_id_fails_closed(tmp_path):
    """D+A 形一：rename＋改寫後新 blob 缺 frontmatter id——無法以 id 配對 lineage
    → identity-ambiguous fail-closed（非靜默 birth 放行）。"""
    repo = _repo(tmp_path)
    src = "backlog/tasks/air-904 - lose.md"
    old_text = _card_text("In Progress", card_id="AIR-904") + "\n" + _SPLIT_OLD_FILLER
    _commit_file(repo, src, old_text, "create")
    baseline = _baseline_commit(repo)
    dst = "backlog/tasks/air-904 - renamed.md"
    new_text = (
        _card_text("Done").replace("id: AIR-900\n", "") + "\n" + _SPLIT_NEW_FILLER
    )
    _split_rename_commit(repo, src, dst, new_text)
    _assert_degraded_to_d_a(repo)
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out
    assert "缺 frontmatter id" in out


def test_f2_split_rename_missing_old_id_fails_closed(tmp_path):
    """D+A 形二：rename 前舊 blob 缺 frontmatter id——同樣無法配對 → fail-closed。"""
    repo = _repo(tmp_path)
    src = "backlog/tasks/air-905 - noname.md"
    old_text = (
        _card_text("In Progress").replace("id: AIR-900\n", "")
        + "\n"
        + _SPLIT_OLD_FILLER
    )
    _commit_file(repo, src, old_text, "create without id")
    baseline = _baseline_commit(repo)
    dst = "backlog/tasks/air-905 - named.md"
    new_text = _card_text("Done", card_id="AIR-905") + "\n" + _SPLIT_NEW_FILLER
    _split_rename_commit(repo, src, dst, new_text)
    _assert_degraded_to_d_a(repo)
    rc, out, _err = _run_all_done(repo, baseline)
    assert rc != 0
    assert "identity-ambiguous" in out
    assert "缺 frontmatter id" in out
