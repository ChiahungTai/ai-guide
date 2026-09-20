"""harness_waiter 契約測試（AIR-149 S1——ZCode 子 agent 凍結偵測＋收割）.

oracle 分級：
- TC-1（T1-T9 轉移表）＝S 級 frozen spec——module docstring 逐字表對照＋逐轉移行為機驗
- TC-2＝H 級真實殭屍 corpus（references/fixtures/stale-running，manifest.json 快照時點計數）
- TC-3／TC-5＝I 級 impl 衍生（合成 layout，tmp_path，不讀真 ~/.zcode）
- TC-4 dogfood 歸主 session，本檔不冒充

測試全程合成 layout（ZCodeLayout(cli_root=tmp_path)），零真機依賴。
"""

import ast
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/harness_waiter.py")

SCRIPT = REPO_ROOT / "scripts" / "harness_waiter.py"
CORPUS_DIR = (
    REPO_ROOT
    / "ai-analysis"
    / "_tasks"
    / "2026-09"
    / "09-20-harness-liveness-watcher"
    / "references"
    / "fixtures"
    / "stale-running"
)

T0 = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)
AGENT = "agent_aaa1"
TASK = f"sess_subagent_{AGENT}"
CREATED = "2026-09-20T11:00:00.000Z"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def make_layout(tmp_path: Path):
    return _mod.ZCodeLayout(cli_root=tmp_path / "zcode-cli")


def ns(t: datetime) -> int:
    return int(t.timestamp() * 1_000_000_000)


def write_metadata(
    layout,
    parent: str,
    agent_id: str,
    *,
    status: str = "running",
    created: str = CREATED,
    raw: str | None = None,
) -> str:
    task = f"sess_subagent_{agent_id}"
    d = layout.agents_root / parent / agent_id
    d.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (d / "metadata.json").write_text(raw)
    else:
        meta = {
            "agentId": agent_id,
            "childSessionId": task,
            "createdAt": created,
            "status": status,
            "parentSessionId": parent,
        }
        (d / "metadata.json").write_text(json.dumps(meta))
    return task


def touch_rollout(layout, task: str, *, size: int = 100, mtime: datetime = T0) -> Path:
    p = layout.rollout_file(task)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x" * size)
    stamp = ns(mtime)
    os.utime(p, ns=(stamp, stamp))
    return p


def touch_dir_file(
    root: Path, name: str, *, size: int = 10, mtime: datetime = T0
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    p = root / name
    p.write_bytes(b"y" * size)
    stamp = ns(mtime)
    os.utime(p, ns=(stamp, stamp))
    return p


def reg_path(tmp_path: Path) -> Path:
    return tmp_path / ".agent-tmp" / "liveness-registry.json"


def write_registry(
    tmp_path: Path, entries: list, *, name: str = "liveness-registry.json"
) -> Path:
    p = tmp_path / ".agent-tmp" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"entries": entries}))
    return p


def reg_entry_dict(
    task: str = TASK,
    attempt: str = "att-1",
    created: str = CREATED,
    **extra,
) -> dict:
    d = {
        "taskId": task,
        "attemptId": attempt,
        "createdAt": created,
        "sink": "out.md",
        "expected": {"anchor": "DONE"},
        "survivingHandles": [],
    }
    d.update(extra)
    return d


def reg_entry(task=TASK, attempt="att-1", created=CREATED, budget=None, handles=()):
    return _mod.RegistryEntry(
        task_id=task,
        attempt_id=attempt,
        created_at=created,
        sink="out.md",
        expected={"anchor": "DONE"},
        surviving_handles=tuple(handles),
        silence_budget_min=budget,
    )


def clock(*times: datetime):
    it = iter(times)
    return lambda: next(it)


def run_watcher(tmp_path, entries, layout, *, times, poll_interval_s=600.0, **kw):
    rp = write_registry(tmp_path, entries)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=poll_interval_s,
        now_fn=clock(*times),
        sleep_fn=kw.pop("sleep_fn", lambda s: None),
        stdout=out,
        stderr=err,
        **kw,
    )
    return code, out.getvalue(), err.getvalue()


def last_json(stdout: str) -> dict:
    return json.loads(stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 基礎：路徑 derivation＋status 欄位＋registry loader
# ---------------------------------------------------------------------------


def test_path_derivation(tmp_path):
    layout = make_layout(tmp_path)
    root = tmp_path / "zcode-cli"
    assert layout.rollout_file(TASK) == root / "rollout" / f"model-io-{TASK}.jsonl"
    assert layout.exec_dir(TASK) == root / "exec" / TASK
    assert layout.artifact_dir(TASK) == root / "artifacts" / TASK
    assert layout.agents_root == root / "agents"


def test_agent_id_derivation():
    assert _mod.agent_id_from_task("sess_subagent_agent_x1") == "agent_x1"
    assert _mod.agent_id_from_task("sess_plain") is None
    assert _mod.agent_id_from_task("sess_subagent_") is None


def test_status_fields(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=77, mtime=T0 - timedelta(seconds=30))
    art = touch_dir_file(
        layout.artifact_dir(TASK), "a.txt", mtime=T0 - timedelta(seconds=10)
    )
    _exe = touch_dir_file(
        layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0 - timedelta(seconds=20)
    )
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    st = src.status(TASK)
    assert isinstance(st, _mod.TaskStatus)
    assert st.state == "running"
    assert st.generation == (TASK, CREATED)
    assert st.created_at == CREATED
    assert st.output_cursor == 77
    assert st.exec_lease == ()
    assert st.exec_lease_checked is True
    assert st.last_activity == datetime.fromtimestamp(
        art.stat().st_mtime_ns / 1e9, tz=UTC
    )
    assert st.cursors.rollout_size == 77
    assert st.cursors.artifact_size == 10
    assert st.cursors.exec_size == 10


def test_status_invalid_task_id(tmp_path):
    src = _mod.ZCodeLivenessSource(make_layout(tmp_path))
    face = src.status("sess_plain")
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "invalid-task-id"


def test_status_metadata_corrupt_missing_key(tmp_path):
    layout = make_layout(tmp_path)
    src = _mod.ZCodeLivenessSource(layout)
    write_metadata(
        layout,
        "sess_p1",
        AGENT,
        raw=json.dumps({"agentId": AGENT, "createdAt": CREATED, "status": "running"}),
    )
    face = src.status(TASK)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "metadata-corrupt"


def test_status_metadata_glob_ambiguous(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    write_metadata(layout, "sess_p2", AGENT)
    src = _mod.ZCodeLivenessSource(layout)
    face = src.status(TASK)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "metadata-glob-ambiguous"


def test_status_terminal_without_rollout_is_legal(tmp_path):
    # terminal 後 rollout 清理＝機器合法行為（實機實證）——不得誤報 unknown
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    st = src.status(TASK)
    assert isinstance(st, _mod.TaskStatus)
    assert st.state == "completed"
    assert st.cursors.rollout_size is None
    assert st.last_activity is None


def test_f11_terminal_lease_probe_failure_short_circuits(tmp_path):
    # F-11：terminal＋lsof 不可判定＝checked=False（freeze 迴圈不誤醒），
    # 非 unknown face；verify 端另行 fail-closed
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)
    touch_dir_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: None)
    st = src.status(TASK)
    assert isinstance(st, _mod.TaskStatus)
    assert st.exec_lease_checked is False
    assert st.exec_lease == ()
    # freeze 迴圈面：terminal 短路，不受 probe 失敗影響
    det = _mod.FreezeDetector(src, threshold_min=20.0, poll_interval_s=600.0)
    res, _state = det.poll(reg_entry(), _mod.WatchState(), T0)
    assert isinstance(res, _mod.PollTerminal)


def test_f1_verify_incomplete_lease_on_terminal_no_rollout(tmp_path):
    # F-1 Critical：terminal＋rollout 已清＋exec 殘留有 writer→禁假 STOP_CONFIRMED
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    exe = touch_dir_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [str(exe)])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 4
    assert tail["state"] == "STOP_INCOMPLETE"
    assert any("exec-lease-active" in r for r in tail["reasons"])
    assert str(exe) in tail["survivingHandles"]


def test_f1_verify_confirmed_terminal_no_rollout_clean_exec(tmp_path):
    # F-1 修復不破壞乾淨路徑：terminal＋rollout 已清＋exec/artifact 靜止＋無 lease
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_dir_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 0
    assert tail["state"] == "STOP_CONFIRMED"
    assert tail["survivingHandles"] == []


def test_f11_verify_incomplete_lease_unknown(tmp_path):
    # F-1/F-11 組合：probe 不可判定→verify fail-closed（禁假確認）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)
    touch_dir_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: None)
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 4
    assert any("lease-unknown" in r for r in tail["reasons"])


def test_f6_registry_created_at_unparseable_fail_loud(tmp_path):
    bad = tmp_path / "r5.json"
    bad.write_text(
        json.dumps({"entries": [dict(reg_entry_dict(), createdAt="not-a-time")]})
    )
    face = _mod.load_registry(bad)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "registry-schema"


def test_f6_metadata_created_at_unparseable_corrupt(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    meta_file = layout.agents_root / "sess_p1" / AGENT / "metadata.json"
    meta = json.loads(meta_file.read_text())
    meta["createdAt"] = "not-a-time"
    meta_file.write_text(json.dumps(meta))
    src = _mod.ZCodeLivenessSource(layout)
    face = src.status(TASK)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "metadata-corrupt"


def test_registry_loader_faces(tmp_path):
    missing = _mod.load_registry(tmp_path / "nope.json")
    assert (
        isinstance(missing, _mod.UnknownFace) and missing.reason == "registry-missing"
    )
    bad_shape = tmp_path / "r1.json"
    bad_shape.write_text("{}")
    assert _mod.load_registry(bad_shape).reason == "registry-schema"
    bad_entry = tmp_path / "r2.json"
    bad_entry.write_text(json.dumps({"entries": [{"taskId": "t"}]}))
    assert _mod.load_registry(bad_entry).reason == "registry-schema"
    bad_sink = tmp_path / "r3.json"
    bad_sink.write_text(json.dumps({"entries": [dict(reg_entry_dict(), sink=42)]}))
    assert _mod.load_registry(bad_sink).reason == "registry-schema"
    bad_budget = tmp_path / "r4.json"
    bad_budget.write_text(
        json.dumps({"entries": [dict(reg_entry_dict(), silenceBudget=-1)]})
    )
    assert _mod.load_registry(bad_budget).reason == "registry-schema"
    ok = write_registry(tmp_path, [dict(reg_entry_dict(), silenceBudget=45.5)])
    entries = _mod.load_registry(ok)
    assert not isinstance(entries, _mod.UnknownFace)
    assert entries[0].silence_budget_min == 45.5
    assert entries[0].task_id == TASK


def test_t1_t9_frozen_table_in_docstring():
    doc = _mod.__doc__ or ""
    for i in range(1, 10):
        assert f"| T{i} |" in doc, f"轉移表 T{i} 缺 module docstring"


# ---------------------------------------------------------------------------
# TC-1：T1-T9 狀態機逐轉移
# ---------------------------------------------------------------------------


def test_t1_registry_entry_monitored_polling_starts(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=10))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[T0, T0 + timedelta(seconds=600)],
        max_cycles=2,
    )
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "error"
    assert "max-cycles" in tail["reason"]
    assert "[harness_waiter] cycle=1" in out  # MONITORED：開始輪詢


def test_t2_any_surface_progress_continues_counting(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=10))

    def bump(_s: float) -> None:
        touch_rollout(layout, TASK, size=200, mtime=T0 + timedelta(hours=2))

    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[T0, T0 + timedelta(seconds=600), T0 + timedelta(seconds=1200)],
        sleep_fn=bump,
        max_cycles=3,
    )
    assert code == 1  # max-cycles 內部錯，非 freeze
    assert "freeze-wake" not in out
    assert "verdict=fresh" in out


def test_t2_poll_gap_anomaly_deducts_interval(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[T0, T0 + timedelta(hours=2)],
        max_cycles=2,
    )
    assert code == 1
    assert "freeze-wake" not in out
    assert "poll-gap-deducted" in out  # 扣除間隔（單一語義）


def test_t3_full_silence_freeze_harvest_wake(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[
            T0,
            T0 + timedelta(seconds=600),
            T0 + timedelta(seconds=1200),
        ],
    )
    assert code == 3
    tail = last_json(out)
    assert tail["state"] == "freeze-wake"
    assert tail["taskId"] == TASK
    assert tail["attemptId"] == "att-1"
    assert "TaskStop" in tail["suggestedAction"]
    pending = tmp_path / ".agent-tmp" / "liveness" / "pending" / f"{TASK}.json"
    assert pending.exists()
    receipt = json.loads(pending.read_text())
    assert receipt["attemptId"] == "att-1"
    assert receipt["harvestDir"] == tail["harvestDir"]
    manifest = json.loads(Path(tail["manifestPath"]).read_text())
    assert manifest["schema"] == "harness-harvest-manifest/1"
    bundle = Path(tail["harvestDir"])
    assert (bundle / "metadata.json").exists()
    assert (bundle / "rollout.tail.jsonl").exists()
    assert manifest["harvestPartial"] is False


def test_t4_resume_during_quarantine_still_cut(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    calls = {"n": 0}
    real_status = src.status

    def counting(task_id):
        calls["n"] += 1
        if calls["n"] == 4:  # 3 次輪詢後的 harvest re-status——quarantine 期恢復
            touch_rollout(layout, TASK, size=999, mtime=T0 + timedelta(seconds=1300))
        return real_status(task_id)

    src.status = counting  # type: ignore[method-assign]
    rp = write_registry(tmp_path, [reg_entry_dict()])
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=600.0,
        now_fn=clock(T0, T0 + timedelta(seconds=600), T0 + timedelta(seconds=1200)),
        sleep_fn=lambda s: None,
        source=src,
        stdout=out,
        stderr=err,
    )
    assert code == 3  # 仍照砍——恢復不取消 wake
    tail = last_json(out.getvalue())
    assert tail["resumedDuringQuarantine"] is True


def test_t5_generation_mismatch_immediate_wake(tmp_path):
    layout = make_layout(tmp_path)

    def rewrite(_s: float) -> None:
        write_metadata(layout, "sess_p1", AGENT, created="2026-09-20T09:00:00.000Z")

    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[T0, T0 + timedelta(seconds=600)],
        sleep_fn=rewrite,
    )
    assert code == 2
    tail = last_json(out)
    assert tail["state"] == "hard-death-wake"
    assert "generation-mismatch" in tail["reason"]


def test_t5_metadata_gone_is_hard_death(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    meta_file = layout.agents_root / "sess_p1" / AGENT / "metadata.json"

    def gone(_s: float) -> None:
        meta_file.unlink()

    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[T0, T0 + timedelta(seconds=600)],
        sleep_fn=gone,
    )
    assert code == 2
    assert last_json(out)["state"] == "hard-death-wake"


def test_t5_registry_entry_removed_is_hard_death(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    rp = write_registry(tmp_path, [reg_entry_dict()])

    def shrink(_s: float) -> None:
        rp.write_text(json.dumps({"entries": []}))

    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=600.0,
        now_fn=clock(T0, T0 + timedelta(seconds=600)),
        sleep_fn=shrink,
        stdout=out,
        stderr=err,
    )
    assert code == 2
    tail = last_json(out.getvalue())
    assert tail["state"] == "hard-death-wake"
    assert tail["reason"] == "registry-entry-changed"


def test_f4_pure_addition_absorbed_not_hard_death(tmp_path):
    # F-4：正常追加註冊（純增項）＝吸納續 watch，非 hard-death 假喚醒
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=10))
    other = "sess_subagent_agent_bbb2"
    write_metadata(layout, "sess_p2", "agent_bbb2")
    touch_rollout(layout, other, mtime=T0 - timedelta(seconds=10))
    rp = write_registry(tmp_path, [reg_entry_dict()])

    def add_entry(_s: float) -> None:
        data = json.loads(rp.read_text())
        data["entries"].append(reg_entry_dict(task=other))
        rp.write_text(json.dumps(data))

    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=600.0,
        now_fn=clock(T0, T0 + timedelta(seconds=600)),
        sleep_fn=add_entry,
        max_cycles=2,
        stdout=out,
        stderr=err,
    )
    assert code == 1  # max-cycles 內部錯收場，非 exit 2
    assert "hard-death-wake" not in out.getvalue()
    assert "純增項吸納" in out.getvalue()
    assert other in out.getvalue()  # 第二 task 進入輪詢


def test_f4_attempt_change_is_hard_death(tmp_path):
    # 同 task 換 attempt＝重派跡象——維持 exit 2
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=10))
    rp = write_registry(tmp_path, [reg_entry_dict()])

    def reattempt(_s: float) -> None:
        rp.write_text(json.dumps({"entries": [reg_entry_dict(attempt="att-2")]}))

    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=600.0,
        now_fn=clock(T0, T0 + timedelta(seconds=600)),
        sleep_fn=reattempt,
        stdout=out,
        stderr=err,
    )
    assert code == 2
    tail = last_json(out.getvalue())
    assert tail["reason"] == "registry-entry-changed"


def test_t5_registry_created_at_mismatch_fast_path(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created="2026-09-20T08:00:00.000Z")],
        layout,
        times=[T0],
    )
    assert code == 2
    tail = last_json(out)
    assert tail["state"] == "hard-death-wake"
    assert "generation-mismatch" in tail["reason"]


def test_t6_anchor_missing_unknown_no_freeze_claim(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)  # rollout 缺席
    code, out, _err = run_watcher(tmp_path, [reg_entry_dict()], layout, times=[T0])
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "unknown"
    assert tail["reason"] == "rollout-anchor-missing"
    assert not (tmp_path / ".agent-tmp" / "liveness" / "pending").exists()


def test_t6_registry_file_missing_fail_loud(tmp_path):
    layout = make_layout(tmp_path)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        tmp_path / ".agent-tmp" / "liveness-registry.json",
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        now_fn=clock(T0),
        sleep_fn=lambda s: None,
        stdout=out,
        stderr=err,
    )
    assert code == 1
    assert last_json(out.getvalue())["reason"] == "registry-missing"


def test_t6_metadata_unparseable_unknown(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, raw="{not json")
    code, out, _err = run_watcher(tmp_path, [reg_entry_dict()], layout, times=[T0])
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "unknown"
    assert tail["reason"] == "metadata-unparseable"


def test_t6_lease_prober_failure_no_freeze_claim(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, mtime=T0 - timedelta(hours=2))
    touch_dir_file(
        layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0 - timedelta(hours=2)
    )
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: None)
    rp = write_registry(tmp_path, [reg_entry_dict()])
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        now_fn=clock(T0),
        sleep_fn=lambda s: None,
        source=src,
        stdout=out,
        stderr=err,
    )
    assert code == 1
    tail = last_json(out.getvalue())
    assert tail["state"] == "unknown"
    assert tail["reason"] == "lease-prober-failed"


def test_t7_no_stop_code_path_in_module():
    source = SCRIPT.read_text()
    assert "os.kill" not in source
    tree = ast.parse(source)
    banned = {"kill", "terminate", "send_signal", "system"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in banned, f"watcher 不得有 stop 代碼路徑：{node.attr}"


def test_t7_taskstop_only_as_suggestion_string():
    source = SCRIPT.read_text()
    assert "TaskStop" in source  # 建議動作字串在場
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) in {
            "run",
            "Popen",
            "call",
        }:
            assert "TaskStop" not in ast.dump(node), (
                "TaskStop 只能是建議字串，不得進任何呼叫路徑"
            )


def test_all_terminal_exits_zero(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))
    code, out, _err = run_watcher(tmp_path, [reg_entry_dict()], layout, times=[T0])
    assert code == 0
    assert last_json(out)["state"] == "all-terminal"


def test_empty_registry_exits_zero_without_polling(tmp_path):
    layout = make_layout(tmp_path)
    code, out, _err = run_watcher(
        tmp_path, [], layout, times=[]
    )  # now 序列空＝不得輪詢
    assert code == 0
    assert last_json(out)["state"] == "empty-registry"


# ---------------------------------------------------------------------------
# TC-2：真實殭屍 corpus——零誤報 active
# ---------------------------------------------------------------------------


def _corpus_index() -> list[dict]:
    manifest = json.loads((CORPUS_DIR / "manifest.json").read_text())
    files = sorted(p.name for p in CORPUS_DIR.glob("agent_*.json"))
    listed = sorted(e["file"] for e in manifest["entries"])
    assert files == listed, "corpus 檔案與 manifest.json 計數漂移"
    assert manifest["count"] == len(files)
    return manifest["entries"]


def test_tc2_corpus_snapshot_integrity():
    entries = _corpus_index()
    assert len(entries) >= 1
    md = (CORPUS_DIR / "MANIFEST.md").read_text()
    assert "快照時點" in md
    for e in entries:
        assert e["agentId"] in md


def test_tc2_corpus_zero_false_active(tmp_path):
    layout = make_layout(tmp_path)
    for e in _corpus_index():
        fixture = json.loads((CORPUS_DIR / e["file"]).read_text())
        parent = fixture["parentSessionId"]
        agent_id = fixture["agentId"]
        d = layout.agents_root / parent / agent_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "metadata.json").write_text(json.dumps(fixture))
        # rollout 缺席 corpus——不建 rollout 檔
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    for e in _corpus_index():
        fixture = json.loads((CORPUS_DIR / e["file"]).read_text())
        st = src.status(fixture["childSessionId"])
        assert isinstance(st, _mod.UnknownFace), f"{e['agentId']} 誤報為可判讀 active"
        assert st.reason == "rollout-anchor-missing"


def test_tc2_corpus_detector_never_fresh(tmp_path):
    layout = make_layout(tmp_path)
    for e in _corpus_index():
        fixture = json.loads((CORPUS_DIR / e["file"]).read_text())
        d = layout.agents_root / fixture["parentSessionId"] / fixture["agentId"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "metadata.json").write_text(json.dumps(fixture))
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    det = _mod.FreezeDetector(src, threshold_min=20.0, poll_interval_s=600.0)
    now = datetime.now(tz=UTC)
    for e in _corpus_index():
        fixture = json.loads((CORPUS_DIR / e["file"]).read_text())
        entry = reg_entry(task=fixture["childSessionId"], created=fixture["createdAt"])
        res, _state = det.poll(entry, _mod.WatchState(), now)
        assert not isinstance(res, _mod.PollFresh), f"{e['agentId']} 誤報 fresh"
        assert not isinstance(res, _mod.PollFrozen) or res.elapsed_s >= 1200.0


def test_tc2_corpus_loop_reports_unknown_no_freeze_wake(tmp_path):
    layout = make_layout(tmp_path)
    entries = []
    for e in _corpus_index():
        fixture = json.loads((CORPUS_DIR / e["file"]).read_text())
        d = layout.agents_root / fixture["parentSessionId"] / fixture["agentId"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "metadata.json").write_text(json.dumps(fixture))
        entries.append(
            reg_entry_dict(task=fixture["childSessionId"], created=fixture["createdAt"])
        )
    code, out, _err = run_watcher(
        tmp_path, entries, layout, times=[datetime.now(tz=UTC)]
    )
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "unknown"
    assert "freeze-wake" not in out
    assert not (tmp_path / ".agent-tmp" / "liveness" / "pending").exists()


# ---------------------------------------------------------------------------
# TC-3：凍結判準矩陣（合成 mtime／lease／poll-gap／時鐘回撥）
# ---------------------------------------------------------------------------


def _poll_seq_with_setup(tmp_path, entry, times, setup, prober=None):
    layout = make_layout(tmp_path)
    setup(layout)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=prober or (lambda paths: []))
    det = _mod.FreezeDetector(src, threshold_min=20.0, poll_interval_s=600.0)
    state = _mod.WatchState()
    results = []
    for t in times:
        res, state = det.poll(entry, state, t)
        results.append(res)
    return results, layout, src, det


def test_tc3_artifact_progress_keeps_fresh(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(hours=1))
        touch_dir_file(
            layout.artifact_dir(TASK), "a.txt", mtime=T0 - timedelta(seconds=5)
        )

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(), [T0], setup)
    assert isinstance(results[0], _mod.PollFresh)


def test_tc3_exec_lease_exempts_long_silent_call(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(hours=2))
        touch_dir_file(
            layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0 - timedelta(hours=2)
        )

    results, *_ = _poll_seq_with_setup(
        tmp_path, reg_entry(), [T0], setup, prober=lambda paths: list(paths)
    )
    assert isinstance(results[0], _mod.PollFresh)  # SM-2：長工具呼叫豁免


def test_tc3_frozen_beyond_threshold(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=1300))

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(), [T0], setup)
    assert isinstance(results[0], _mod.PollFrozen)
    assert results[0].elapsed_s >= 1200.0


def test_tc3_boundary_19m59s_fresh(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=1199))

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(), [T0], setup)
    assert isinstance(results[0], _mod.PollFresh)


def test_tc3_boundary_exact_20m_frozen(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=1200))

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(), [T0], setup)
    assert isinstance(results[0], _mod.PollFrozen)


def test_tc3_poll_gap_deduction(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))

    results, *_ = _poll_seq_with_setup(
        tmp_path,
        reg_entry(),
        [T0, T0 + timedelta(hours=2)],
        setup,
    )
    assert isinstance(results[1], _mod.PollFresh)
    assert results[1].elapsed_s <= 660.0  # 2h gap 只記一個 interval


def test_tc3_clock_rollback_fresh_with_telemetry(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))

    results, *_ = _poll_seq_with_setup(
        tmp_path, reg_entry(), [T0, T0 - timedelta(minutes=10)], setup
    )
    assert isinstance(results[1], _mod.PollFresh)
    assert "clock-rollback" in results[1].telemetry


def test_tc3_silence_budget_override(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=400))

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(budget=5.0), [T0], setup)
    assert isinstance(results[0], _mod.PollFrozen)  # 5m 預算 vs 400s 靜默


def test_tc3_terminal_transition_not_freeze(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT, status="stopped")
        touch_rollout(layout, TASK, mtime=T0 - timedelta(hours=5))

    results, *_ = _poll_seq_with_setup(tmp_path, reg_entry(), [T0], setup)
    assert isinstance(results[0], _mod.PollTerminal)
    assert results[0].state == "stopped"


def test_tc3_midwatch_progress_resets_silence(tmp_path):
    def setup(layout):
        write_metadata(layout, "sess_p1", AGENT)
        touch_rollout(layout, TASK, mtime=T0 - timedelta(seconds=60))

    layout = make_layout(tmp_path)
    setup(layout)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    det = _mod.FreezeDetector(src, threshold_min=20.0, poll_interval_s=600.0)
    state = _mod.WatchState()
    r1, state = det.poll(reg_entry(), state, T0)
    touch_rollout(layout, TASK, size=500, mtime=T0 + timedelta(seconds=300))
    r2, state = det.poll(reg_entry(), state, T0 + timedelta(seconds=600))
    r3, state = det.poll(reg_entry(), state, T0 + timedelta(seconds=1200))
    assert isinstance(r1, _mod.PollFresh)
    assert isinstance(r2, _mod.PollFresh) and r2.elapsed_s == 0.0
    assert isinstance(r3, _mod.PollFresh) and r3.elapsed_s == 600.0


# ---------------------------------------------------------------------------
# 收割器：bounded＋partial＋pending dedup＋delta
# ---------------------------------------------------------------------------


def test_harvest_bundle_and_manifest(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=300, mtime=T0 - timedelta(seconds=60))
    touch_dir_file(layout.artifact_dir(TASK), "a.txt", mtime=T0 - timedelta(seconds=30))
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(src, layout, tmp_path / ".agent-tmp" / "liveness")
    result = harv.harvest(reg_entry())
    assert not isinstance(result, _mod.UnknownFace)
    manifest, bundle = result
    assert manifest["schema"] == "harness-harvest-manifest/1"
    assert manifest["taskId"] == TASK
    assert manifest["agentId"] == AGENT
    assert manifest["harvestPartial"] is False
    assert (bundle / "metadata.json").exists()
    tail = (bundle / "rollout.tail.jsonl").read_bytes()
    assert tail == b"x" * 300
    assert manifest["tails"]["rollout"]["partial"] is False
    assert manifest["tails"]["rollout"]["sha256"] == hashlib.sha256(tail).hexdigest()
    surfaces = {f["surface"] for f in manifest["files"]}
    assert surfaces == {"rollout", "artifact"}
    assert manifest["cursors"]["rolloutSize"] == 300


def test_harvest_partial_tail_bounded(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=200, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(
        src, layout, tmp_path / ".agent-tmp" / "liveness", max_tail_bytes=64
    )
    manifest, bundle = harv.harvest(reg_entry())
    tail = (bundle / "rollout.tail.jsonl").read_bytes()
    assert len(tail) == 64
    assert manifest["tails"]["rollout"]["partial"] is True
    assert manifest["harvestPartial"] is True  # SM-9：超限照樣標


def test_harvest_file_count_cap(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=10, mtime=T0)
    for i in range(5):
        touch_dir_file(layout.artifact_dir(TASK), f"a{i}.txt", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(
        src, layout, tmp_path / ".agent-tmp" / "liveness", max_manifest_files=3
    )
    manifest, _bundle = harv.harvest(reg_entry())
    assert manifest["filesTruncated"] is True
    assert len(manifest["files"]) == 3
    assert manifest["harvestPartial"] is True


def test_harvest_unknown_passthrough(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)  # rollout 缺
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(src, layout, tmp_path / ".agent-tmp" / "liveness")
    face = harv.harvest(reg_entry())
    assert isinstance(face, _mod.UnknownFace)


def test_harvest_resumed_flag_from_freeze_cursors(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=10, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(src, layout, tmp_path / ".agent-tmp" / "liveness")
    st = src.status(TASK)
    frozen_cursors = st.cursors
    manifest, _b = harv.harvest(reg_entry(), freeze_cursors=frozen_cursors)
    assert manifest["resumedDuringQuarantine"] is False
    touch_rollout(layout, TASK, size=20, mtime=T0 + timedelta(seconds=30))
    manifest2, _b2 = harv.harvest(reg_entry(), freeze_cursors=frozen_cursors)
    assert manifest2["resumedDuringQuarantine"] is True


def test_pending_receipt_dedup_same_attempt(tmp_path):
    liveness = tmp_path / ".agent-tmp" / "liveness"
    liveness.mkdir(parents=True)
    entry = reg_entry()
    _mod.write_pending_receipt(
        liveness,
        entry,
        {"schema": "harness-harvest-manifest/1"},
        liveness / "h",
        elapsed_s=1250.0,
        resumed=False,
    )
    pending = liveness / "pending" / f"{TASK}.json"
    first = json.loads(pending.read_text())
    _mod.write_pending_receipt(
        liveness,
        entry,
        {"schema": "harness-harvest-manifest/1"},
        liveness / "h2",
        elapsed_s=1300.0,
        resumed=True,
    )
    second = json.loads(pending.read_text())
    assert first == second  # dedup：已有 pending 不重發


def test_pending_receipt_overwrite_new_attempt(tmp_path):
    liveness = tmp_path / ".agent-tmp" / "liveness"
    liveness.mkdir(parents=True)
    _mod.write_pending_receipt(
        liveness,
        reg_entry(attempt="att-0"),
        {},
        liveness / "h",
        elapsed_s=1.0,
        resumed=False,
    )
    path = _mod.write_pending_receipt(
        liveness,
        reg_entry(attempt="att-1"),
        {},
        liveness / "h2",
        elapsed_s=2.0,
        resumed=False,
    )
    data = json.loads(path.read_text())
    assert data["attemptId"] == "att-1"


def test_harvest_delta_growth(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=100, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    liveness = tmp_path / ".agent-tmp" / "liveness"
    harv = _mod.Harvester(src, layout, liveness)
    prev_manifest, _bundle = harv.harvest(reg_entry())
    prev_path = liveness / "prev-manifest.json"
    prev_path.write_text(json.dumps(prev_manifest))
    touch_rollout(layout, TASK, size=180, mtime=T0 + timedelta(seconds=60))
    result = harv.harvest_delta(reg_entry(), prev_path)
    assert not isinstance(result, _mod.UnknownFace)
    delta, dbundle = result
    assert delta["schema"] == "harness-harvest-delta/1"
    grown = {g["path"] for g in delta["grownFiles"]}
    assert any("model-io" in p for p in grown)
    assert delta["resumedDuringQuarantine"] is True  # STOP 後仍有寫入者
    assert (dbundle / "manifest.json").exists()


def test_harvest_delta_no_change(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_rollout(layout, TASK, size=100, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    liveness = tmp_path / ".agent-tmp" / "liveness"
    harv = _mod.Harvester(src, layout, liveness)
    prev_manifest, _bundle = harv.harvest(reg_entry())
    prev_path = liveness / "prev-manifest.json"
    prev_path.write_text(json.dumps(prev_manifest))
    delta, _db = harv.harvest_delta(reg_entry(), prev_path)
    assert delta["newFiles"] == []
    assert delta["grownFiles"] == []
    assert delta["resumedDuringQuarantine"] is False


def test_harvest_delta_bad_prev_manifest(tmp_path):
    layout = make_layout(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text("{oops")
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(src, layout, tmp_path / ".agent-tmp" / "liveness")
    face = harv.harvest_delta(reg_entry(), bad)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "delta-prev-manifest-unparseable"


def test_harvest_delta_task_mismatch(tmp_path):
    layout = make_layout(tmp_path)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    harv = _mod.Harvester(src, layout, tmp_path / ".agent-tmp" / "liveness")
    prev = tmp_path / "m.json"
    prev.write_text(
        json.dumps(
            {
                "schema": "harness-harvest-manifest/1",
                "taskId": "sess_subagent_agent_other",
                "cursors": {},
                "files": [],
            }
        )
    )
    face = harv.harvest_delta(reg_entry(), prev)
    assert isinstance(face, _mod.UnknownFace)
    assert face.reason == "delta-prev-manifest-schema"


# ---------------------------------------------------------------------------
# STOP verification（T8/T9 invocation 面）
# ---------------------------------------------------------------------------


def run_verify(tmp_path, layout, *, task=TASK, grace_s=0.0, prober=None, source=None):
    write_registry(tmp_path, [reg_entry_dict()])  # registry 恆登記 TASK
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_verify(
        layout,
        reg_path(tmp_path),
        task,
        grace_s=grace_s,
        sleep_fn=lambda s: None,
        source=source,
        stdout=out,
        stderr=err,
    )
    return code, last_json(out.getvalue())


def test_t8_verify_confirmed(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 0
    assert tail["state"] == "STOP_CONFIRMED"
    assert tail["survivingHandles"] == []


def test_t9_verify_incomplete_still_running(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="running")
    touch_rollout(layout, TASK, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 4
    assert tail["state"] == "STOP_INCOMPLETE"
    assert any("metadata-not-terminal" in r for r in tail["reasons"])


def test_t9_verify_incomplete_cursors_moved(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)

    def grow(_s: float) -> None:
        touch_rollout(layout, TASK, size=500, mtime=T0 + timedelta(seconds=5))

    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    rp = write_registry(tmp_path, [reg_entry_dict()])
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_verify(
        layout,
        rp,
        TASK,
        grace_s=30.0,
        sleep_fn=grow,
        source=src,
        stdout=out,
        stderr=err,
    )
    assert code == 4
    tail = last_json(out.getvalue())
    assert any("cursors-moved" in r for r in tail["reasons"])


def test_t9_verify_incomplete_detached_lease(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)
    exe = touch_dir_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [str(exe)])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 4
    assert tail["state"] == "STOP_INCOMPLETE"
    assert str(exe) in tail["survivingHandles"]  # SM-5：detached child 處置清單


def test_t9_verify_incomplete_metadata_gone(tmp_path):
    layout = make_layout(tmp_path)  # metadata 缺
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    code, tail = run_verify(tmp_path, layout, source=src)
    assert code == 4
    assert tail["state"] == "STOP_INCOMPLETE"


def test_verify_unregistered_task_fail_loud(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    code, tail = run_verify(
        tmp_path, layout, task="sess_subagent_agent_ghost", source=src
    )
    assert code == 1
    assert tail["state"] == "unknown"


def test_harvest_delta_invocation_exit_zero(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    touch_rollout(layout, TASK, size=100, mtime=T0)
    src = _mod.ZCodeLivenessSource(layout, lease_prober=lambda paths: [])
    liveness = tmp_path / ".agent-tmp" / "liveness"
    harv = _mod.Harvester(src, layout, liveness)
    prev_manifest, _b = harv.harvest(reg_entry())
    prev_path = liveness / "prev.json"
    prev_path.write_text(json.dumps(prev_manifest))
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_harvest_delta(
        layout, liveness, TASK, prev_path, source=src, stdout=out, stderr=err
    )
    assert code == 0
    tail = last_json(out.getvalue())
    assert tail["state"] == "harvest-delta"


# ---------------------------------------------------------------------------
# CLI e2e（subprocess；stdlib only，零網路）
# ---------------------------------------------------------------------------


def test_cli_missing_registry_fail_loud(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(tmp_path / "nope" / "liveness-registry.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 1
    tail = json.loads(proc.stdout.strip().splitlines()[-1])
    assert tail["state"] == "unknown"
    assert tail["reason"] == "registry-missing"


def test_lsof_lease_prober_no_matches(tmp_path):
    lone = tmp_path / "quiet.log"
    lone.write_text("hi")
    result = _mod.lsof_lease_prober([lone])
    assert result == []  # lsof 在場、無 lease＝空清單（非 None）


def test_f3_lsof_self_held_fd_positive(tmp_path):
    # F-3 正向：本測試行程自持 open fd——lsof 必命中
    target = tmp_path / "held.log"
    with open(target, "w") as fh:
        fh.write("x")
        result = _mod.lsof_lease_prober([target])
        assert result == [str(target)]


def test_f3_lsof_symlink_path_normalized(tmp_path):
    # F-3：/tmp vs /private/tmp 類 symlink 路徑——realpath 正規化兩側後必命中
    target = tmp_path / "held.log"
    link = tmp_path / "link.log"
    with open(target, "w") as fh:
        fh.write("x")
        link.symlink_to(target)
        result = _mod.lsof_lease_prober([link])
        assert result == [str(link)]


def test_f2_lsof_missing_file_is_undecidable(tmp_path):
    # F-2：不存在檔→lsof exit 1＋stderr 非空＝錯誤非無命中→None 不可判定
    result = _mod.lsof_lease_prober([tmp_path / "nope" / "gone.log"])
    assert result is None


def test_f12_main_verify_mode_missing_entry_fail_loud(tmp_path, capsys):
    # F-12：main() 層級——--verify 未註冊 task→exit 1 unknown（registry 先查）
    rp = write_registry(tmp_path, [reg_entry_dict()])
    code = _mod.main([str(rp), "--verify", "sess_subagent_agent_ghost"])
    assert code == 1
    tail = last_json(capsys.readouterr().out)
    assert tail["state"] == "unknown"
    assert tail["reason"] == "registry-entry-missing-for-verify"


def test_f12_main_watcher_mode_missing_registry_fail_loud(tmp_path, capsys):
    code = _mod.main([str(tmp_path / "nope" / "liveness-registry.json")])
    assert code == 1
    tail = last_json(capsys.readouterr().out)
    assert tail["reason"] == "registry-missing"


# ---------------------------------------------------------------------------
# S2：dispatch 註冊（--register 寫入端；schema 逐欄對齊 S1 讀取面）
# ---------------------------------------------------------------------------


def run_register(
    tmp_path,
    task=TASK,
    *,
    attempt="att-1",
    sink="out.md",
    expected=None,
    handles=(),
    budget=None,
    created=CREATED,
    metadata_absent=False,
    source=None,
):
    # register 讀 metadata 取 generation anchor（createdAt）——先佈建觀察面
    layout = make_layout(tmp_path)
    agent_id = _mod.agent_id_from_task(task)
    if agent_id is not None and not metadata_absent:
        write_metadata(layout, "sess_p1", agent_id, created=created)
        touch_rollout(layout, task, mtime=T0 - timedelta(seconds=10))
    rp = reg_path(tmp_path)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_register(
        layout,
        rp,
        task,
        attempt_id=attempt,
        sink=sink,
        expected_raw=expected,
        surviving_handles=tuple(handles),
        silence_budget_min=budget,
        source=source,
        stdout=out,
        stderr=err,
    )
    return code, out.getvalue(), rp


def test_s2_register_roundtrip_visible_to_reader(tmp_path):
    code, out, rp = run_register(
        tmp_path,
        expected='{"anchor": "DONE"}',
        handles=("exec/sess_x/call_1-stdout.log",),
        budget=45.5,
    )
    assert code == 0
    tail = last_json(out)
    assert tail["state"] == "registered"
    entries = _mod.load_registry(rp)
    assert not isinstance(entries, _mod.UnknownFace)
    assert len(entries) == 1
    e = entries[0]
    assert e.task_id == TASK
    assert e.attempt_id == "att-1"
    # createdAt＝generation anchor（自 metadata 機械讀取，非牆鐘——T5 對照基準）
    assert e.created_at == CREATED
    assert e.sink == "out.md"
    assert e.expected == {"anchor": "DONE"}
    assert e.surviving_handles == ("exec/sess_x/call_1-stdout.log",)
    assert e.silence_budget_min == 45.5
    assert _mod._parse_iso(e.created_at) is not None


def test_s2_register_metadata_missing_fail_loud(tmp_path):
    # spawn 未落地／taskId 打錯——註冊當下 fail-loud，禁拖到輪詢才爆
    code, out, rp = run_register(tmp_path, metadata_absent=True)
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "unknown"
    assert tail["reason"] == "metadata-anchor-missing"
    assert not rp.exists()


def test_s2_register_entry_matches_frozen_schema_key_set(tmp_path):
    code, _out, rp = run_register(tmp_path)
    assert code == 0
    raw = json.loads(rp.read_text())["entries"][0]
    # frozen schema：{taskId, attemptId, createdAt, sink, expected,
    # survivingHandles[], silenceBudget?}——可省欄位以缺席表達
    assert set(raw) == {
        "taskId",
        "attemptId",
        "createdAt",
        "sink",
        "expected",
        "survivingHandles",
    }
    entries = _mod.load_registry(rp)
    e = entries[0]
    assert e.expected is None
    assert e.surviving_handles == ()
    assert e.silence_budget_min is None


def test_s2_register_second_task_appends(tmp_path):
    run_register(tmp_path)
    other = "sess_subagent_agent_bbb2"
    code, _out, rp = run_register(tmp_path, task=other, attempt="att-2")
    assert code == 0
    entries = _mod.load_registry(rp)
    assert [e.task_id for e in entries] == [TASK, other]


def test_s2_register_duplicate_task_fail_loud_entry_unchanged(tmp_path):
    run_register(tmp_path)
    code, out, rp = run_register(tmp_path, attempt="att-2")
    assert code == 1
    tail = last_json(out)
    assert tail["state"] == "unknown"
    assert tail["reason"] == "duplicate-registration"
    entries = _mod.load_registry(rp)
    assert len(entries) == 1
    assert entries[0].attempt_id == "att-1"  # 拒絕不落地


def test_s2_register_corrupt_existing_registry_fail_loud_no_clobber(tmp_path):
    rp = reg_path(tmp_path)
    rp.parent.mkdir(parents=True, exist_ok=True)
    cases = [
        '{"entries": [{"taskId": "x"',  # 半寫 torn JSON
        '{"entries": {"bad": 1}}',  # schema 形狀錯
        json.dumps({"entries": [{"taskId": "t"}]}),  # entry 缺必要欄位
    ]
    for bad in cases:
        rp.write_text(bad)
        code, out, rp2 = run_register(tmp_path)
        assert code == 1
        tail = last_json(out)
        assert tail["state"] == "unknown"
        assert tail["reason"].startswith("registry-")
        assert rp2.read_text() == bad  # 禁覆蓋損壞 registry


def test_s2_register_invalid_inputs_fail_loud(tmp_path):
    cases = [
        ({"expected": "{oops"}, "expected-unparseable"),
        ({"budget": 0}, "silence-budget-invalid"),
        ({"budget": -5.0}, "silence-budget-invalid"),
        ({"task": "sess_plain"}, "invalid-task-id"),
        ({"attempt": ""}, "invalid-attempt-id"),
        ({"sink": ""}, "invalid-sink"),
        ({"handles": ("   ",)}, "invalid-surviving-handle"),
    ]
    for kw, reason in cases:
        code, out, rp = run_register(tmp_path, **kw)
        assert code == 1, f"{kw} 應 fail-loud"
        assert last_json(out)["reason"] == reason
        assert not rp.exists(), f"{kw} 失敗不得落地半套 registry"


def test_s2_register_missing_required_flags_fail_loud(tmp_path):
    layout = make_layout(tmp_path)
    rp = reg_path(tmp_path)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_register(
        layout,
        rp,
        TASK,
        attempt_id=None,
        sink=None,
        expected_raw=None,
        surviving_handles=(),
        silence_budget_min=None,
        stdout=out,
        stderr=err,
    )
    assert code == 1
    assert last_json(out.getvalue())["reason"] == "invalid-attempt-id"


def test_s2_register_atomic_no_temp_residue(tmp_path):
    code, _out, rp = run_register(tmp_path)
    assert code == 0
    assert sorted(p.name for p in rp.parent.iterdir()) == ["liveness-registry.json"]


def test_s2_register_then_watcher_monitors(tmp_path):
    # 寫入端→S1 讀取端全鏈：register（anchor 取自 metadata）→watcher
    # 對 completed task 立即 all-terminal（T5 對照通過＝anchor 語義正確）
    run_register(tmp_path)
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        reg_path(tmp_path),
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        now_fn=clock(T0),
        sleep_fn=lambda s: None,
        stdout=out,
        stderr=err,
    )
    assert code == 0
    assert last_json(out.getvalue())["state"] == "all-terminal"


def test_s2_register_childsession_mismatch_fail_loud(tmp_path):
    # F4（fresh 審查）：childSessionId 與 taskId 不符 → metadata-generation-mismatch
    # fail-loud、registry 不落地
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    mp = next((layout.agents_root / "sess_p1" / AGENT).glob("metadata.json"))
    mp.write_text(
        mp.read_text().replace("sess_subagent_agent_aaa1", "sess_subagent_OTHER")
    )
    rp = reg_path(tmp_path)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_register(
        layout, rp, TASK, attempt_id="att-1", sink="out.md", stdout=out, stderr=err
    )
    assert code == 1
    assert "metadata-generation-mismatch" in err.getvalue()
    assert not rp.exists()


def test_s2_cli_register_flags_roundtrip(tmp_path, capsys):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    rp = reg_path(tmp_path)
    code = _mod.main(
        [
            str(rp),
            "--register",
            TASK,
            "--attempt-id",
            "att-9",
            "--sink",
            "reports/out.md",
            "--expected",
            '{"anchor": "DONE"}',
            "--surviving-handle",
            "h1",
            "--surviving-handle",
            "h2",
            "--silence-budget-min",
            "30",
        ],
        layout=make_layout(tmp_path),
    )
    assert code == 0
    tail = last_json(capsys.readouterr().out)
    assert tail["state"] == "registered"
    e = _mod.load_registry(rp)[0]
    assert e.attempt_id == "att-9"
    assert e.sink == "reports/out.md"
    assert e.expected == {"anchor": "DONE"}
    assert e.surviving_handles == ("h1", "h2")
    assert e.silence_budget_min == 30.0


def test_s2_cli_register_duplicate_exit_nonzero(tmp_path, capsys):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    rp = reg_path(tmp_path)
    base = [str(rp), "--register", TASK, "--attempt-id", "a", "--sink", "s"]
    assert _mod.main(base, layout=layout) == 0
    capsys.readouterr()
    assert (
        _mod.main([*base[:-4], "--attempt-id", "b", "--sink", "s2"], layout=layout) == 1
    )


def test_s2_usage_documents_register():
    doc = _mod.__doc__ or ""
    assert "--register" in doc
    assert "--surviving-handle" in doc


def test_cli_help_shows_register():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0
    assert "--register" in proc.stdout


def test_cli_register_e2e_roundtrip(tmp_path):
    # e2e：$HOME 指向 fake home——ZCodeLayout.default() 解析到佈建的 metadata
    home = tmp_path / "home"
    agents = home / ".zcode" / "cli" / "agents" / "sess_p1" / AGENT
    agents.mkdir(parents=True)
    (agents / "metadata.json").write_text(
        json.dumps(
            {
                "agentId": AGENT,
                "childSessionId": TASK,
                "createdAt": CREATED,
                "status": "running",
                "parentSessionId": "sess_p1",
            }
        )
    )
    rp = tmp_path / "ws" / ".agent-tmp" / "liveness-registry.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(rp),
            "--register",
            TASK,
            "--attempt-id",
            "att-1",
            "--sink",
            "out.md",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "HOME": str(home)},
    )
    assert proc.returncode == 0
    entries = _mod.load_registry(rp)
    assert not isinstance(entries, _mod.UnknownFace)
    assert entries[0].task_id == TASK
    assert entries[0].created_at == CREATED
