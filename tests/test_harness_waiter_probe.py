"""harness_waiter --probe 契約測試（AIR-162——唯讀聚合；T1-T9 frozen 主體零變）.

oracle 分級：
- supervisionState 五態判定＝S 級 frozen 設計（card AIR-162〔已決策勿重辯〕
  ①分離兩軸②死亡宣稱僅 A 級③D 級永不支撐死亡④身份窗綁定⑦wake early
  declare death late——雙腿收斂 detection-codex/muse-result.md）
- observations 三欄／A-D 分級／manualReview 旗＝I 級 impl 衍生（合成 layout，
  tmp_path，零真機依賴）

probe 是唯讀聚合新面：零處置（不 stop 不重派不收割不記帳）、零 registry 寫入。
"""

import io
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/harness_waiter.py")

CREATED = "2026-09-20T11:00:00.000Z"
AGENT = "agent_aaa1"
TASK = f"sess_subagent_{AGENT}"


# ---------------------------------------------------------------------------
# helpers（與 test_harness_waiter.py 同構——獨立複製避免耦合 frozen 測試檔）
# ---------------------------------------------------------------------------


def make_layout(tmp_path: Path):
    return _mod.ZCodeLayout(cli_root=tmp_path / "zcode-cli")


def dt(h: int, m: int, s: int = 0) -> datetime:
    return datetime(2026, 9, 20, h, m, s, tzinfo=UTC)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ns(t: datetime) -> int:
    return int(t.timestamp() * 1_000_000_000)


def write_metadata(
    layout,
    parent: str,
    agent_id: str,
    *,
    status: str = "running",
    created: str = CREATED,
) -> str:
    task = f"sess_subagent_{agent_id}"
    d = layout.agents_root / parent / agent_id
    d.mkdir(parents=True, exist_ok=True)
    meta = {
        "agentId": agent_id,
        "childSessionId": task,
        "createdAt": created,
        "status": status,
        "parentSessionId": parent,
    }
    (d / "metadata.json").write_text(json.dumps(meta))
    return task


def reg_entry_dict(
    task: str = TASK, attempt: str = "att-1", created: str = CREATED, **extra
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


def write_registry(tmp_path: Path, entries: list) -> Path:
    p = tmp_path / ".agent-tmp" / "liveness-registry.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"entries": entries}))
    return p


def reg_path(tmp_path: Path) -> Path:
    return tmp_path / ".agent-tmp" / "liveness-registry.json"


def touch_file(p: Path, *, size: int = 10, mtime: datetime) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"z" * size)
    stamp = ns(mtime)
    os.utime(p, ns=(stamp, stamp))
    return p


HB_FILE = ".agent-tmp/heartbeats/probe.jsonl"


def write_heartbeat(
    tmp_path: Path, *, emitted: datetime, interval: int = 60, attempt: str = "att-1"
) -> Path:
    p = tmp_path / HB_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "schema": "child-heartbeat/1",
        "seq": 1,
        "taskId": TASK,
        "attemptId": attempt,
        "state": "working",
        "emittedAt": iso(emitted),
        "note": None,
        "intervalSecs": interval,
    }
    p.write_text(json.dumps(rec) + "\n")
    return p


def run_probe(tmp_path, layout, *, task=TASK, entries=None, registry=True, now=None):
    """run_probe 包裝：回 (exit_code, tail_payload, stdout, stderr)."""
    if registry:
        rp = write_registry(tmp_path, entries if entries is not None else [])
    else:
        rp = reg_path(tmp_path)  # 檔不落地＝registry 缺席
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_probe(
        layout,
        rp,
        task,
        now_fn=lambda: now or dt(12, 0),
        stdout=out,
        stderr=err,
    )
    tail = json.loads(out.getvalue().strip().splitlines()[-1])
    return code, tail, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# supervisionState 五態（S 級 frozen 設計對照）
# ---------------------------------------------------------------------------


def test_probe_running_registered_within_timebox_monitored(tmp_path):
    # Scenario ①：running→MONITORED（registry row＝C、native running row＝C）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert code == 0
    assert tail["supervisionState"] == "MONITORED"
    assert tail["strongestEvidence"] == "C"
    assert tail["manualReview"] is False
    assert tail["observations"]["addressable"] == "yes"


def test_probe_terminal_metadata_state_terminal_grade_a(tmp_path):
    # metadata terminal＝唯一權威狀態訊號（A 級）→ TERMINAL
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert code == 0
    assert tail["supervisionState"] == "TERMINAL"
    assert tail["strongestEvidence"] == "A"
    assert tail["observations"]["addressable"] == "no"


def test_probe_generation_mismatch_hard_death_evidence(tmp_path):
    # registry createdAt ≠ metadata createdAt＝generation mismatch（A 級）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, created="2026-09-20T11:30:00.000Z")
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(12, 0)
    )
    assert code == 2  # 鏡像 watcher hard-death wake 語義
    assert tail["supervisionState"] == "HARD_DEATH_EVIDENCE"
    assert tail["strongestEvidence"] == "A"


def test_probe_registered_metadata_gone_hard_death_evidence(tmp_path):
    # 已註冊身份的 metadata 錨點消失＝A 級 hard-death fast path（T5 對稱）
    layout = make_layout(tmp_path)  # 無 metadata
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(12, 0)
    )
    assert code == 2
    assert tail["supervisionState"] == "HARD_DEATH_EVIDENCE"
    assert tail["strongestEvidence"] == "A"
    assert tail["manualReview"] is False


def test_probe_timebox_expired_not_dead(tmp_path):
    # Scenario ③：timebox 到＝TIMEBOX_EXPIRED（A 級時間盒事實）——不宣稱 dead
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 25)
    )
    assert code == 0
    assert tail["supervisionState"] == "TIMEBOX_EXPIRED"
    assert tail["strongestEvidence"] == "A"
    assert "DEAD" not in tail["supervisionState"].upper().replace("_", "")
    assert tail["manualReview"] is False


def test_probe_timebox_silence_budget_override(tmp_path):
    # entry silenceBudget 覆寫預設 20m——30 分鐘 box：25m 仍 MONITORED
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, tail, _out, _err = run_probe(
        tmp_path,
        layout,
        entries=[reg_entry_dict(silenceBudget=30)],
        now=dt(11, 25),
    )
    assert code == 0
    assert tail["supervisionState"] == "MONITORED"


def test_probe_nonexistent_id_unknown_needs_human_not_death(tmp_path):
    # Scenario ④＋規則③：D 級缺席（無 registry 無 metadata）永不支撐死亡——
    # never-existed／reaped／打錯 id 不可區分→UNKNOWN fail-loud＋manualReview
    layout = make_layout(tmp_path)
    code, tail, _out, _err = run_probe(tmp_path, layout, entries=[], now=dt(12, 0))
    assert code == 1
    assert tail["supervisionState"] == "UNKNOWN"
    assert tail["manualReview"] is True
    assert tail["strongestEvidence"] == "D"


def test_probe_invalid_task_id_unknown_fail_loud(tmp_path):
    layout = make_layout(tmp_path)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, task="bogus-no-prefix", entries=[], now=dt(12, 0)
    )
    assert code == 1
    assert tail["supervisionState"] == "UNKNOWN"


def test_probe_corrupt_registry_fail_loud(tmp_path):
    # 損壞比缺失危險——registry 不可解析＝UNKNOWN fail-loud（禁覆蓋禁猜）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    rp = reg_path(tmp_path)
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text("{corrupt")
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_probe(
        layout, rp, TASK, now_fn=lambda: dt(12, 0), stdout=out, stderr=err
    )
    assert code == 1
    tail = json.loads(out.getvalue().strip().splitlines()[-1])
    assert tail["supervisionState"] == "UNKNOWN"


def test_probe_registry_missing_tolerated_d_grade(tmp_path):
    # registry 檔缺席＝D 級缺席面（probe 唯讀聚合不禁整個 verdict——metadata
    # 仍可判）；與 watcher T6 fail-loud 不同面（probe 輸入是 task 非 registry）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=None, registry=False, now=dt(11, 5)
    )
    assert code == 0
    assert tail["supervisionState"] == "MONITORED"
    grades = {row["grade"] for row in tail["evidence"]}
    assert "D" in grades  # registry-absent 缺席面入冊


def test_probe_unregistered_running_still_monitored(tmp_path):
    # 未註冊但 metadata running→MONITORED（native running row＝C 級可尋址）；
    # 無 window anchor→workspaceActivity unknown
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=None, registry=False, now=dt(11, 5)
    )
    assert code == 0
    assert tail["supervisionState"] == "MONITORED"
    assert tail["observations"]["workspaceActivity"] == "unknown"


def test_probe_metadata_unparseable_unknown(tmp_path):
    layout = make_layout(tmp_path)
    d = layout.agents_root / "sess_p1" / AGENT
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text("{half-written")
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(12, 0)
    )
    assert code == 1
    assert tail["supervisionState"] == "UNKNOWN"
    assert tail["manualReview"] is True


def test_probe_clock_rollback_no_timebox_claim(tmp_path):
    # createdAt 在未來＝時鐘不可信——禁判 timebox（Frozen 條款對稱）→MONITORED
    layout = make_layout(tmp_path)
    future = "2026-09-20T13:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=future)
    code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict(created=future)], now=dt(12, 0)
    )
    assert code == 0
    assert tail["supervisionState"] == "MONITORED"
    assert any("clock-rollback" in row.get("detail", "") for row in tail["evidence"])


# ---------------------------------------------------------------------------
# observations 三欄（recentExecution／addressable／workspaceActivity）
# ---------------------------------------------------------------------------


def test_recent_execution_fresh_heartbeat_yes(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    write_heartbeat(tmp_path, emitted=dt(11, 4))  # age 60s ≤ 120s 門檻
    entry = reg_entry_dict(expectedHeartbeat=True, heartbeatFile=HB_FILE)
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[entry], now=dt(11, 5)
    )
    assert tail["observations"]["recentExecution"] == "yes"
    assert tail["strongestEvidence"] == "B"  # 可歸因 heartbeat＝B 級


def test_recent_execution_stale_heartbeat_no(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    write_heartbeat(tmp_path, emitted=dt(11, 0))  # age 300s > 120s 門檻
    entry = reg_entry_dict(expectedHeartbeat=True, heartbeatFile=HB_FILE)
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[entry], now=dt(11, 5)
    )
    assert tail["observations"]["recentExecution"] == "no"


def test_recent_execution_absent_heartbeat_unknown(tmp_path):
    # 缺席合法（D 級）——禁推 no，禁推死亡
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    entry = reg_entry_dict(expectedHeartbeat=True, heartbeatFile=HB_FILE)
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[entry], now=dt(11, 5)
    )
    assert tail["observations"]["recentExecution"] == "unknown"


def test_recent_execution_other_attempt_not_credited(tmp_path):
    # attemptId 不符的 heartbeat 記錄禁計入本 attempt（歸因鐵律）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    write_heartbeat(tmp_path, emitted=dt(11, 4), attempt="att-0")
    entry = reg_entry_dict(expectedHeartbeat=True, heartbeatFile=HB_FILE)
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[entry], now=dt(11, 5)
    )
    assert tail["observations"]["recentExecution"] == "unknown"


def test_workspace_activity_in_window_yes_task_scoped(tmp_path):
    # exec face（task-scoped，路徑即身份）mtime ∈ [createdAt, now] → yes；
    # 單一註冊 entry＋task-scoped 面＝機械歸因，不 ambiguous
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(layout.exec_dir(TASK) / "lease", mtime=dt(11, 3))
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "yes"
    assert tail["attributionAmbiguous"] is False
    assert tail["manualReview"] is False


def test_workspace_activity_all_pre_window_no(tmp_path):
    # 面上檔案全數早於 createdAt＝窗外（非本 attempt 活動）→ no（非 unknown）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(layout.exec_dir(TASK) / "stale", mtime=dt(10, 0))
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "no"


def test_workspace_activity_no_files_unknown(tmp_path):
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "unknown"


def test_workspace_activity_shared_face_ambiguous_needs_human(tmp_path):
    # 共享面（sink）窗內活動＋registry 有其他 co-registered entry＝attribution
    # ambiguous→manualReview（規則④：無身份綁定的活動禁歸因原 worker）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(tmp_path / "out.md", mtime=dt(11, 3))  # sink＝共享面
    other = reg_entry_dict(task="sess_subagent_agent_other")
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict(), other], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "yes"
    assert tail["attributionAmbiguous"] is True
    assert tail["manualReview"] is True


def test_workspace_activity_sink_face_alone_still_ambiguous(tmp_path):
    # 即使無 co-registered entry——sink／handles 非路徑身份綁定（相對路徑可撞）
    # →共享面窗內活動恆 ambiguous（C 級封頂不進 B）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(tmp_path / "out.md", mtime=dt(11, 3))
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "yes"
    assert tail["attributionAmbiguous"] is True


def test_workspace_activity_future_mtime_ambiguous(tmp_path):
    # mtime > now＝時鐘異常——禁歸因→ambiguous（fail-closed 方向）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(layout.exec_dir(TASK) / "future", mtime=dt(11, 59))
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict()], now=dt(11, 5)
    )
    assert tail["attributionAmbiguous"] is True


def test_workspace_activity_task_scoped_beats_shared_coentry(tmp_path):
    # task-scoped 面（exec dir 路徑身份）＋co-registered entry：task-scoped
    # 歸因成立不 ambiguous；共享面才有歧義
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    touch_file(layout.exec_dir(TASK) / "lease", mtime=dt(11, 3))
    other = reg_entry_dict(task="sess_subagent_agent_other")
    _code, tail, _out, _err = run_probe(
        tmp_path, layout, entries=[reg_entry_dict(), other], now=dt(11, 5)
    )
    assert tail["observations"]["workspaceActivity"] == "yes"
    assert tail["attributionAmbiguous"] is False


# ---------------------------------------------------------------------------
# docstring 契約面＋CLI 接線
# ---------------------------------------------------------------------------


def test_probe_evidence_grade_table_in_docstring():
    doc = _mod.__doc__ or ""
    assert "| A（authoritative） |" in doc
    assert "| B（corroborated） |" in doc
    assert "| C（single weak） |" in doc
    assert "| D（absence） |" in doc
    assert "永不支撐死亡" in doc
    assert "attribution_ambiguous" in doc
    assert "registry.createdAt ≤ mtime ≤ now" in doc


def test_probe_supervision_states_enumerated_in_docstring():
    doc = _mod.__doc__ or ""
    for state in (
        "TERMINAL",
        "HARD_DEATH_EVIDENCE",
        "TIMEBOX_EXPIRED",
        "MONITORED",
        "UNKNOWN",
    ):
        assert state in doc


def test_probe_cli_flag_registered():
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(Path(_mod.__file__).resolve()), "--help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0
    assert "--probe" in proc.stdout


def test_probe_cli_mutually_exclusive_with_verify(tmp_path):
    rp = write_registry(tmp_path, [])
    with pytest.raises(SystemExit) as excinfo:
        _mod.main(
            [str(rp), "--probe", TASK, "--verify", TASK],
            layout=make_layout(tmp_path),
        )
    assert excinfo.value.code == 2  # argparse 互斥組錯誤


def test_probe_exit_contract_in_docstring():
    doc = _mod.__doc__ or ""
    assert "--probe" in doc
    assert "supervision-probe/1" in doc
