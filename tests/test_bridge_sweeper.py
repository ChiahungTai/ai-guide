"""bridge-ledger sweeper 測試（AIR-267 S3——TC-S1..S8）。

涵蓋（EP ai-analysis/_tasks/10-07-bridge-sweeper/ep.md）：
- TC-S1 R1 兩形：running 行無 armed 事件／armed 但 heartbeat 逾新鮮度窗
  （default 15 分鐘）；armed+fresh heartbeat 靜默；running 行帶 collected
  ＝ledger staleness（reconcile out of scope）不提醒。
- TC-S2 R2：terminal(completed) 無 collected 且終態逾齡（default 30 分鐘）
  →一行「可能未收」；未逾齡靜默；有 collected 靜默；>3 ids 只列前 3。
- TC-S3 非 completed terminal（failed-* 等）不提醒（v1 收窄）。
- TC-S4 節流＋signature 去重：UserPromptSubmit 90s 窗內第二掃靜默零查詢；
  窗外同 signature 靜默、值變出聲；SessionStart 全掃（無節流無壓制）。
- TC-S5 fail-soft：runner 拋錯／stdout 壞形→零 stdout＋exit 0。
- TC-S6 liveness 缺席＝R2 退化不可判（只跑 R1）＋stderr 註記。
- TC-S7 eligibility gate：非 repo cwd 零查詢零輸出；帶 liveness 台帳的
  他 repo cwd 可跑（EP：cwd 在本 repo 或帶台帳的 repo）。
- TC-S8 drain：造臨時 WT 形目錄→歸檔 jobs/＋liveness.jsonl→0600＋內容
  在場；無證據零動作；wt-close preflight（報告不歸檔）／full（真歸檔）
  整合。
- AC3 措辭釘：源碼「可能未收」在場；「已驗收/已消費/已領取」零命中；
  禁 pgrep/Popen/system(（唯讀 face 經 subprocess.run 呼叫 bridge CLI）。
- governance 接線（S4）：zcode 模板兩事件各一條目（sync）；manifest
  scripts 清單在列。

測試全 fixture 注入（fake runs JSON＋liveness 事件 list＋tmp state dir）
——零真 bridge 呼叫、零真 ~/.agents 觸碰（archive root 可注入）。
"""

import json
import os
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

core = load_module("scripts/bridge_sweeper.py")
hook = load_module("hooks/bridge_ledger_sweeper.py")

REPO = "/fake/ai-guide/repo"
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)

R1_LINE = (
    "[bridge-sweeper] running job {job} 無活 waiter——恢復 playbook：arm waiter"
)
R2_LINE = (
    "[bridge-sweeper] {n} 個 terminal job 可能未收（{ids}）——收線：bridge_show"
)


# ── fixture 注入 helpers ────────────────────────────────────────────────


def _bridge_ts(dt):
    """bridge format_iso_ms 形 timestamp：YYYY-MM-DDTHH:MM:SS.sssZ。"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _at(minutes_ago):
    return _bridge_ts(NOW - timedelta(minutes=minutes_ago))


def _row(job_id, status, minutes_ago):
    return {
        "id": job_id,
        "status": status,
        "timestamp": _at(minutes_ago),
        "family": "glm",
        "sessionId": "caller-1",
    }


def _armed(job_id, minutes_ago):
    return {
        "schema": "liveness/1",
        "event": "armed",
        "jobId": job_id,
        "armedAt": _at(minutes_ago),
        "pid": 101,
    }


def _hb(job_id, minutes_ago):
    return {
        "schema": "liveness/1",
        "event": "heartbeat",
        "jobId": job_id,
        "ts": _at(minutes_ago),
        "pid": 101,
    }


def _collected(job_id, minutes_ago):
    return {
        "schema": "liveness/1",
        "event": "collected",
        "jobId": job_id,
        "exitState": "completed",
        "collectedAt": _at(minutes_ago),
    }


def _runner(rows):
    """fake bridge face：回固定 runs JSON；記錄呼叫（零真 bridge 呼叫）。"""
    calls = []

    def run(argv):
        calls.append(list(argv))
        return json.dumps(rows)

    run.calls = calls
    return run


def _boom(argv):
    raise RuntimeError("bridge face down")


@pytest.fixture(autouse=True)
def _gate(monkeypatch):
    """eligibility 鎖定測試 fake repo（duty 家族測試同款）。"""
    monkeypatch.setattr(core, "script_repo_root", lambda: REPO)
    monkeypatch.setattr(hook.core, "script_repo_root", lambda: REPO)


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path / "state")


@pytest.fixture
def liveness_file(tmp_path):
    path = tmp_path / "liveness.jsonl"
    path.write_text("", encoding="utf-8")
    return str(path)


def _write_liveness(path, events):
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(
            json.dumps(ev, ensure_ascii=False) + "\n" for ev in events
        )


def _run_hook(
    runner,
    boundary="UserPromptSubmit",
    session="s1",
    state_dir=None,
    liveness_path=None,
    now=NOW,
    cwd=REPO,
):
    """便捷包：run_hook＋advance-after-emit（commit 即時執行）。"""
    lines, commit = core.run_hook(
        boundary,
        cwd,
        session,
        runner=runner,
        state_dir=state_dir,
        liveness_path=liveness_path,
        now=now,
    )
    if commit is not None:
        commit()
    return lines


# ── TC-S1 R1 兩形 ───────────────────────────────────────────────────────


def test_s1_r1_running_no_armed():
    rows = [_row("j1", "running", 40)]
    lines = core.scan_once(_runner(rows), [], NOW)
    assert lines == [R1_LINE.format(job="j1")]


def test_s1_r1_armed_but_heartbeat_stale():
    rows = [_row("j1", "running", 60)]
    events = [_armed("j1", 60), _hb("j1", 20)]  # heartbeat 20m > 15m 窗
    lines = core.scan_once(_runner(rows), events, NOW)
    assert lines == [R1_LINE.format(job="j1")]


def test_s1_r1_armed_fresh_heartbeat_silent():
    rows = [_row("j1", "running", 30)]
    events = [_armed("j1", 30), _hb("j1", 2)]  # fresh——有活 waiter
    assert core.scan_once(_runner(rows), events, NOW) == []


def test_s1_r1_running_row_with_collected_skipped():
    """running 行卻帶 collected＝ledger staleness（reconcile 變異＝waiter T7
    擁有，EP out of scope）——不提醒（watcher_pairing_nag 同款不誤發裁定）。"""
    rows = [_row("j1", "running", 90)]
    events = [_armed("j1", 90), _hb("j1", 80), _collected("j1", 70)]
    assert core.scan_once(_runner(rows), events, NOW) == []


def test_s1_r1_window_adjustable():
    rows = [_row("j1", "running", 60)]
    events = [_armed("j1", 60), _hb("j1", 20)]
    # 窗放寬至 30m → 同 fixture 靜默（EP：新鮮度窗可調）
    assert core.scan_once(_runner(rows), events, NOW,
                          heartbeat_fresh_min=30.0) == []


# ── TC-S2 R2 ───────────────────────────────────────────────────────────


def test_s2_r2_terminal_uncollected_over_age():
    rows = [_row("j1", "completed", 40)]
    events = [_armed("j1", 90), _hb("j1", 80)]  # armed 過但無 collected
    lines = core.scan_once(_runner(rows), events, NOW)
    assert lines == [R2_LINE.format(n=1, ids="j1")]


def test_s2_r2_terminal_recent_silent():
    rows = [_row("j1", "completed", 10)]  # 未逾 30m 齡
    events = [_armed("j1", 40), _hb("j1", 20)]
    assert core.scan_once(_runner(rows), events, NOW) == []


def test_s2_r2_collected_silent():
    rows = [_row("j1", "completed", 40)]
    events = [_armed("j1", 90), _hb("j1", 80), _collected("j1", 39)]
    assert core.scan_once(_runner(rows), events, NOW) == []


def test_s2_r2_ids_capped_at_three():
    rows = [_row(f"j-{i}", "completed", 40) for i in range(4)]
    events = [_armed(f"j-{i}", 90) for i in range(4)]
    lines = core.scan_once(_runner(rows), events, NOW)
    assert lines == [R2_LINE.format(n=4, ids="j-0、j-1、j-2…")]


def test_s2_r2_no_liveness_trace_silent():
    """AC5 真場 smoke 回歸釘：無 armed 痕跡的 terminal 行＝pre-liveness 時代
    或手動收線面——不可判，fail-safe 安靜（實證：全報＝578 行誤報洪水）。"""
    rows = [_row("j-ancient", "completed", 40), _row("j-manual", "completed", 60)]
    events = [_armed("j-other", 90)]  # 僅無關 job 有痕跡
    assert core.scan_once(_runner(rows), events, NOW) == []


def test_s2_r2_and_r1_mixed():
    rows = [_row("j-run", "running", 20), _row("j-done", "completed", 40)]
    events = [_armed("j-done", 90), _hb("j-done", 80)]
    lines = core.scan_once(_runner(rows), events, NOW)
    assert lines == [
        R1_LINE.format(job="j-run"),
        R2_LINE.format(n=1, ids="j-done"),
    ]


# ── TC-S3 非 completed terminal 不提醒 ─────────────────────────────────


def test_s3_non_completed_terminal_not_flagged():
    rows = [_row("j1", "failed-usage", 40), _row("j2", "interrupted", 40)]
    assert core.scan_once(_runner(rows), [], NOW) == []


# ── TC-S4 節流＋signature 去重 ──────────────────────────────────────────


def test_s4_throttle_window_silent_no_query(tmp_path, state_dir, liveness_file):
    _write_liveness(liveness_file, [])
    rows = [_row("j1", "running", 40)]
    runner = _runner(rows)
    # T0 冷啟動：出聲
    first = _run_hook(runner, liveness_path=liveness_file, state_dir=state_dir)
    assert first == [R1_LINE.format(job="j1")]
    assert len(runner.calls) == 1
    # T0+30s（90s 窗內）：靜默＋零查詢
    second = _run_hook(
        runner, liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=30),
    )
    assert second == []
    assert len(runner.calls) == 1  # 節流＝不再打 face


def test_s4_signature_same_value_silent(tmp_path, state_dir, liveness_file):
    _write_liveness(liveness_file, [])
    rows = [_row("j1", "running", 40)]
    runner = _runner(rows)
    first = _run_hook(runner, liveness_path=liveness_file, state_dir=state_dir)
    assert first == [R1_LINE.format(job="j1")]
    # T0+120s（窗外）：同 signature → 靜默（防每 prompt 轟炸）但照掃
    second = _run_hook(
        runner, liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=120),
    )
    assert second == []
    assert len(runner.calls) == 2  # 掃了（節流窗外）——去重壓制輸出


def test_s4_signature_value_change_speaks(tmp_path, state_dir, liveness_file):
    _write_liveness(liveness_file, [])
    runner = _runner([_row("j1", "running", 40)])
    assert _run_hook(runner, liveness_path=liveness_file,
                     state_dir=state_dir) != []
    # 值變：新孤兒出現 → 出聲
    runner2 = _runner(
        [_row("j1", "running", 40), _row("j2", "running", 5)]
    )
    third = _run_hook(
        runner2, liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=120),
    )
    assert third == [
        R1_LINE.format(job="j1"),
        R1_LINE.format(job="j2"),
    ]


def test_s4_signature_cleared_then_reappears(
    tmp_path, state_dir, liveness_file
):
    _write_liveness(liveness_file, [])
    runner = _runner([_row("j1", "running", 40)])
    assert _run_hook(runner, liveness_path=liveness_file,
                     state_dir=state_dir) != []
    # 異常消失（job 收掉）→ 靜默＋baseline 歸零
    clean = _runner([_row("j1", "completed", 10)])
    _write_liveness(
        liveness_file, [_armed("j1", 40), _collected("j1", 5)]
    )
    assert _run_hook(
        clean, liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=120),
    ) == []
    # 異常復現 → 重新出聲（baseline 已歸零）
    back = _runner([_row("j2", "running", 3)])
    assert _run_hook(
        back, liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=240),
    ) == [R1_LINE.format(job="j2")]


def test_s4_session_start_full_scan_within_throttle_window(
    tmp_path, state_dir, liveness_file
):
    """SessionStart＝全掃（無節流、無 signature 壓制）——窗內照掃照出聲。"""
    _write_liveness(liveness_file, [])
    runner = _runner([_row("j1", "running", 40)])
    assert _run_hook(runner, liveness_path=liveness_file,
                     state_dir=state_dir) != []
    ss = _run_hook(
        runner, boundary="SessionStart", liveness_path=liveness_file,
        state_dir=state_dir, now=NOW + timedelta(seconds=10),
    )
    assert ss == [R1_LINE.format(job="j1")]
    assert len(runner.calls) == 2


def test_s4_state_file_0600_and_per_session(
    tmp_path, state_dir, liveness_file
):
    _write_liveness(liveness_file, [])
    runner = _runner([_row("j1", "running", 40)])
    _run_hook(runner, liveness_path=liveness_file, state_dir=state_dir)
    sfile = Path(state_dir) / "s1.json"
    assert sfile.exists()
    assert stat.S_IMODE(sfile.stat().st_mode) == 0o600
    doc = json.loads(sfile.read_text(encoding="utf-8"))
    assert isinstance(doc.get("last_scan_at"), str)
    assert isinstance(doc.get("signature"), str)
    # 另 session 冷啟動（per-session state 檔互不干擾）→ 同異常照出聲
    other = _run_hook(
        runner, session="s2", liveness_path=liveness_file, state_dir=state_dir,
        now=NOW + timedelta(seconds=30),
    )
    assert other == [R1_LINE.format(job="j1")]


# ── TC-S5 fail-soft ────────────────────────────────────────────────────


def test_s5_runner_raises_zero_stdout_exit_zero(
    capsys, state_dir, liveness_file
):
    _write_liveness(liveness_file, [])
    lines, commit = core.run_hook(
        "UserPromptSubmit", REPO, "s1", runner=_boom,
        state_dir=state_dir, liveness_path=liveness_file, now=NOW,
    )
    assert lines == []
    assert commit is None
    err = capsys.readouterr().err
    assert "fail-soft" in err


def test_s5_unparsable_stdout_fail_soft(state_dir, liveness_file):
    _write_liveness(liveness_file, [])
    lines, _ = core.run_hook(
        "UserPromptSubmit", REPO, "s1",
        runner=lambda argv: "not-json",
        state_dir=state_dir, liveness_path=liveness_file, now=NOW,
    )
    assert lines == []


def test_s5_hook_face_error_zero_stdout_exit_zero(state_dir, liveness_file):
    payload = json.dumps(
        {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
         "cwd": REPO}
    )
    code, out, commit = hook.run(
        payload, runner=_boom, state_dir=state_dir,
        liveness_path=liveness_file,
    )
    assert (code, out, commit) == (0, "", None)


def test_s5_hook_envelope_shape(state_dir, liveness_file):
    """出聲時＝hookSpecificOutput.additionalContext（sync 通道）包事件名。"""
    _write_liveness(liveness_file, [])
    payload = json.dumps(
        {"hook_event_name": "UserPromptSubmit", "session_id": "s1",
         "cwd": REPO}
    )
    code, out, commit = hook.run(
        payload, runner=_runner([_row("j1", "running", 40)]),
        state_dir=state_dir, liveness_path=liveness_file,
    )
    assert code == 0
    doc = json.loads(out)
    specific = doc["hookSpecificOutput"]
    assert specific["hookEventName"] == "UserPromptSubmit"
    assert specific["additionalContext"] == R1_LINE.format(job="j1")
    assert commit is not None


def test_s5_hook_unknown_event_silent():
    payload = json.dumps({"hook_event_name": "Stop", "session_id": "s1",
                          "cwd": REPO})
    code, out, commit = hook.run(payload)
    assert (code, out, commit) == (0, "", None)


# ── TC-S6 liveness 缺席退化 ────────────────────────────────────────────


def test_s6_liveness_absent_r2_degraded_r1_only(capsys, state_dir):
    rows = [_row("j-run", "running", 20), _row("j-done", "completed", 40)]
    lines, _ = core.run_hook(
        "UserPromptSubmit", REPO, "s1", runner=_runner(rows),
        state_dir=state_dir,
        liveness_path=str(Path(state_dir) / "nonexistent.jsonl"),
        now=NOW,
    )
    assert lines == [R1_LINE.format(job="j-run")]  # R2 退化不可判——只有 R1
    err = capsys.readouterr().err
    assert "liveness" in err  # stderr 註記（不轟炸）


def test_s6_scan_once_none_events_r2_only_degraded():
    rows = [_row("j-run", "running", 20), _row("j-done", "completed", 40)]
    lines = core.scan_once(_runner(rows), None, NOW)
    assert lines == [R1_LINE.format(job="j-run")]


# ── TC-S7 eligibility gate ─────────────────────────────────────────────


def test_s7_cwd_outside_repo_zero_query(monkeypatch):
    monkeypatch.setattr(core, "_git_toplevel", lambda cwd: None)
    runner = _runner([_row("j1", "running", 40)])
    lines, _ = core.run_hook(
        "UserPromptSubmit", "/elsewhere/other", "s1", runner=runner,
        now=NOW,
    )
    assert lines == []
    assert runner.calls == []  # 零查詢


def test_s7_cwd_in_liveness_ledger_repo_eligible(
    monkeypatch, tmp_path, state_dir
):
    """帶 liveness 台帳的 repo（非 script repo）也跑——bridge 派工發生在
    任何 repo，台帳在場＝掃描面成立。"""
    other = tmp_path / "mosaic-wt"
    (other / ".agent-tmp").mkdir(parents=True)
    lv = other / ".agent-tmp" / "liveness.jsonl"
    lv.write_text("", encoding="utf-8")
    monkeypatch.setattr(core, "_git_toplevel", lambda cwd: str(other))
    runner = _runner([_row("j1", "running", 40)])
    lines, _ = core.run_hook(
        "UserPromptSubmit", str(other / "pkg"), "s1", runner=runner,
        state_dir=state_dir, liveness_path=str(lv), now=NOW,
    )
    assert lines == [R1_LINE.format(job="j1")]


def test_s7_no_session_id_silent(state_dir, liveness_file):
    lines, _ = core.run_hook(
        "UserPromptSubmit", REPO, "", runner=_runner([]),
        state_dir=state_dir, liveness_path=liveness_file, now=NOW,
    )
    assert lines == []


# ── AC3 措辭釘＋唯讀 face 釘 ───────────────────────────────────────────


def test_ac3_wording_and_readonly_pins():
    core_src = (REPO_ROOT / "scripts" / "bridge_sweeper.py").read_text(
        encoding="utf-8"
    )
    hook_src = (REPO_ROOT / "hooks" / "bridge_ledger_sweeper.py").read_text(
        encoding="utf-8"
    )
    assert "可能未收" in core_src  # 語義分層：機械層措辭在場
    for src in (core_src, hook_src):
        for banned in ("已驗收", "已消費", "已領取"):
            assert banned not in src, banned
    # invariant 2：禁 pgrep（跨 session false-covered）；唯讀 face 走 subprocess.run
    for src in (core_src, hook_src):
        for banned in ("pgrep", "Popen", "system("):
            assert banned not in src, banned


# ── TC-S8 drain（wt-close 段函式；archive root 可注入——零真 ~/.agents 觸碰）──


def _seed_wt_evidence(wt):
    jobs = wt / ".delegate-bridge" / "jobs"
    jobs.mkdir(parents=True)
    (jobs / "jobs.json").write_text('[{"id": "j1"}]\n', encoding="utf-8")
    (jobs / "j1.jsonl").write_text('{"e": 1}\n', encoding="utf-8")
    agent_tmp = wt / ".agent-tmp"
    agent_tmp.mkdir(parents=True, exist_ok=True)  # identity contract 已建
    (agent_tmp / "liveness.jsonl").write_text(
        '{"event": "armed"}\n', encoding="utf-8"
    )
    return wt


def test_s8_drain_archives_jobs_and_liveness(tmp_path):
    wt = _seed_wt_evidence(tmp_path / "repo-air-9")
    archive = tmp_path / "archive"
    lines = core.archive_wt_bridge_evidence(
        str(wt), archive_root=str(archive),
        now=datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC),
    )
    dest = archive / "repo-air-9-20261007-120000"
    assert dest.is_dir()
    assert (dest / "jobs" / "jobs.json").read_text(encoding="utf-8") == (
        '[{"id": "j1"}]\n'
    )
    assert (dest / "jobs" / "j1.jsonl").exists()
    assert (dest / "liveness.jsonl").exists()
    # 0600 檔案面（目錄 0700）
    for f in (dest / "jobs" / "jobs.json", dest / "liveness.jsonl"):
        assert stat.S_IMODE(f.stat().st_mode) == 0o600
    assert stat.S_IMODE(dest.stat().st_mode) == 0o700
    # 歸檔清單一行
    assert len(lines) == 1
    assert str(dest) in lines[0]


def test_s8_drain_noop_without_evidence(tmp_path):
    wt = tmp_path / "repo-air-10"
    wt.mkdir()
    archive = tmp_path / "archive"
    assert core.archive_wt_bridge_evidence(str(wt), archive_root=str(archive)) == []
    assert not archive.exists()  # 無證據＝零動作


def test_s8_drain_liveness_only(tmp_path):
    wt = tmp_path / "repo-air-11"
    (wt / ".agent-tmp").mkdir(parents=True)
    (wt / ".agent-tmp" / "liveness.jsonl").write_text("x\n", encoding="utf-8")
    archive = tmp_path / "archive"
    core.archive_wt_bridge_evidence(str(wt), archive_root=str(archive))
    dests = list(archive.iterdir())
    assert len(dests) == 1
    assert (dests[0] / "liveness.jsonl").exists()
    assert not (dests[0] / "jobs").exists()


# ── TC-S8 整合：wt-close drain（preflight 報告不歸檔／full 真歸檔）─────

CLOSE_SCRIPT = REPO_ROOT / "scripts" / "wt-close.sh"
GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]


def _git(repo, *args):
    r = subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args],
        check=True, capture_output=True, text=True,
    )
    return r.stdout.strip()


def _seed_close_repo(base):
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".agent-tmp/\n.delegate-bridge/\n")
    (repo / "f.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _open_card_wt(repo, card="air-1"):
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
                "opened_at": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return wt


def test_s8_wt_close_drain_integration(tmp_path):
    archive = tmp_path / "bridge-archive"
    repo = _seed_close_repo(tmp_path)
    wt = _open_card_wt(repo)
    _seed_wt_evidence(wt)
    env = dict(os.environ, BRIDGE_LEDGER_ARCHIVE=str(archive))

    pre = subprocess.run(
        ["bash", str(CLOSE_SCRIPT), "--wt", str(wt), "--preflight"],
        capture_output=True, text=True, check=False, env=env,
    )
    assert pre.returncode == 0, pre.stderr
    assert "bridge 證據" in pre.stdout  # 歸檔清單一行（preflight 皆跑）
    assert not archive.exists()  # preflight 零變更——不歸檔

    full = subprocess.run(
        ["bash", str(CLOSE_SCRIPT), "--wt", str(wt)],
        capture_output=True, text=True, check=False, env=env,
    )
    assert full.returncode == 0, full.stderr
    assert "bridge 證據" in full.stdout
    dests = list(archive.iterdir())
    assert len(dests) == 1
    assert (dests[0] / "jobs" / "jobs.json").exists()
    lv = dests[0] / "liveness.jsonl"
    assert lv.exists()
    assert stat.S_IMODE(lv.stat().st_mode) == 0o600
    assert not wt.exists()  # 收線照常完成


# ── S4 governance 接線 ─────────────────────────────────────────────────


def _registration(rel):
    return json.loads(
        (REPO_ROOT / "governance" / rel).read_text(encoding="utf-8")
    )


def _hook_scripts(group):
    return [h["args"][0].rsplit("/", 1)[-1] for h in group["hooks"]]


def test_s4_governance_zcode_both_events_registered():
    doc = _registration("registrations/zcode.json")
    for event in ("UserPromptSubmit", "SessionStart"):
        hits = [
            g for g in doc["events"][event]
            if "bridge_ledger_sweeper.py" in _hook_scripts(g)
        ]
        assert len(hits) == 1, event
        entry = hits[0]["hooks"][0]
        assert entry["type"] == "process"
        assert "async" not in entry  # sync——additionalContext 通道
        assert entry.get("enabled") is True
        assert entry.get("timeoutMs")


def test_s4_governance_manifest_scripts_listed():
    manifest = (REPO_ROOT / "governance" / "manifest.toml").read_text(
        encoding="utf-8"
    )
    assert '"hooks/bridge_ledger_sweeper.py"' in manifest
