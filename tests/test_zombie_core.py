"""zombie_core 契約測試（AIR-296——GLM 90 樣本校準簽章單一源）.

oracle 分級：
- 三簽章＋閾值＝H 級（GLM 90 樣本校準證據——卡 notes 逐字判準：
  型 A＝running∧artifacts 缺/空∧age>60min；中斷氣＝最新檔凍結>180min；
  型 B＝running∧output.txt 存在即報；60min＞首檔 max 48min、180min≈1.7×間距 max 106min）
- 五級分類＋去重鍵＝codex 五級表（卡面權威）
- 合成 layout（tmp_path）零真機依賴；真機 90 例驗證歸 sweeper 真跑節（ledger 記錄）
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import load_module

_core = load_module("scripts/zombie_core.py")

T0 = datetime(2026, 10, 9, 4, 0, 0, tzinfo=UTC)
AGENT = "agent_z1"
PARENT = "sess_p1"


def ns(t: datetime) -> int:
    return int(t.timestamp() * 1_000_000_000)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def write_meta(
    root: Path,
    *,
    agent: str = AGENT,
    parent: str = PARENT,
    status: str = "running",
    created: str | None = None,
    output_file: str | None = None,
    raw: str | None = None,
) -> Path:
    d = root / "agents" / parent / agent
    d.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (d / "metadata.json").write_text(raw)
        return d / "metadata.json"
    meta = {
        "agentId": agent,
        "childSessionId": f"sess_subagent_{agent}",
        "parentSessionId": parent,
        "createdAt": created or iso(T0 - timedelta(hours=2)),
        "status": status,
    }
    if output_file is not None:
        meta["outputFile"] = output_file
    (d / "metadata.json").write_text(json.dumps(meta))
    return d / "metadata.json"


def make_face(root: Path, *, agent: str = AGENT, files: int = 0, newest: datetime | None = None):
    """合成 artifacts 心跳面（files 檔、最新 mtime=newest）。"""
    adir = _core.artifacts_dir_for(root / "artifacts", agent)
    if files:
        adir.mkdir(parents=True, exist_ok=True)
        for i in range(files):
            p = adir / f"call_{i}-tool-result-x.json"
            p.write_bytes(b"{}")
            stamp = ns(newest or T0)
            os.utime(p, ns=(stamp, stamp))
    return adir


def read_meta(path: Path) -> dict:
    return json.loads(path.read_text())


# --- 佈局面：artifacts dir 命名（sess_subagent_ 前綴——真機實證） ---


def test_artifacts_dir_naming():
    root = Path("/x")
    assert _core.artifacts_dir_for(root / "artifacts", "agent_a1") == (
        root / "artifacts" / "sess_subagent_agent_a1"
    )


def test_output_file_fallback_lives_in_agent_dir():
    # 真機實證：output.txt 住 agents/sess_<parent>/<agentId>/（metadata outputFile 欄指向），非 artifacts 內
    d = Path("/x/agents/sess_p/agent_a")
    assert _core.output_file_for(d) == d / "output.txt"


# --- read_metadata：fail-loud 面（JSON 損壞／必要欄位缺＝UNKNOWN 來源） ---


def test_read_metadata_ok(tmp_path):
    p = write_meta(tmp_path, created=iso(T0 - timedelta(minutes=30)))
    meta = _core.read_metadata(p)
    assert isinstance(meta, dict)
    assert meta["agentId"] == AGENT


def test_read_metadata_corrupt_json(tmp_path):
    p = write_meta(tmp_path, raw="{not json")
    err = _core.read_metadata(p)
    assert isinstance(err, _core.MetaError)
    assert err.reason == "metadata-corrupt"


def test_read_metadata_missing_required_field(tmp_path):
    p = write_meta(tmp_path, raw=json.dumps({"agentId": AGENT, "status": "running"}))
    err = _core.read_metadata(p)
    assert isinstance(err, _core.MetaError)


def test_read_metadata_unparseable_created_at(tmp_path):
    p = write_meta(tmp_path, created="not-a-timestamp")
    err = _core.read_metadata(p)
    assert isinstance(err, _core.MetaError)
    assert err.reason == "metadata-corrupt"


def test_terminal_without_created_at_is_valid_legacy_schema(tmp_path):
    # 舊 schema 實證（2026-10-09 真機 74 具）：stopped＋completedAt 無 createdAt
    # ＝合法 terminal face（非損壞）——createdAt 僅 running 判定軸必要
    d = tmp_path / "agents" / PARENT / AGENT
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(
        json.dumps(
            {
                "agentId": AGENT,
                "status": "stopped",
                "completedAt": "2026-09-01T01:58:35.733Z",
            }
        )
    )
    meta = _core.read_metadata(d / "metadata.json")
    assert isinstance(meta, dict)
    assert meta["status"] == "stopped"


def test_running_without_created_at_is_corrupt(tmp_path):
    # running 缺判定軸（createdAt）＝禁判——UNKNOWN fail-loud
    d = tmp_path / "agents" / PARENT / AGENT
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text(
        json.dumps({"agentId": AGENT, "status": "running"})
    )
    err = _core.read_metadata(d / "metadata.json")
    assert isinstance(err, _core.MetaError)
    assert "createdAt" in err.detail


# --- face_snapshot：唯讀 stat 面 ---


def test_face_snapshot_absent_dir(tmp_path):
    face = _core.face_snapshot(tmp_path / "artifacts" / "nope", None)
    assert face.artifacts_files == 0
    assert face.newest_activity is None
    assert face.output_size is None


def test_face_snapshot_counts_and_newest(tmp_path):
    make_face(tmp_path, files=3, newest=T0 - timedelta(minutes=200))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    assert face.artifacts_files == 3
    assert face.newest_activity is not None
    age = (T0 - face.newest_activity).total_seconds() / 60
    assert 199 <= age <= 201


def test_face_snapshot_output_file(tmp_path):
    make_face(tmp_path, files=1, newest=T0 - timedelta(minutes=10))
    out = tmp_path / "agents" / PARENT / AGENT / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"report body")
    stamp = ns(T0 - timedelta(minutes=5))
    os.utime(out, ns=(stamp, stamp))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), out
    )
    assert face.output_size == len(b"report body")
    # newest_activity 含 output.txt（最後一次寫入也是活動）
    assert face.newest_activity is not None
    age = (T0 - face.newest_activity).total_seconds() / 60
    assert 4 <= age <= 6


# --- classify_running_agent：三簽章（GLM 校準判準逐條） ---


def stillbirth(tmp_path):
    """型 A 標準場景：running 2h、artifacts 從未建立。"""
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=2)))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    return read_meta(p), face


def test_type_a_stillbirth_over_60min(tmp_path):
    meta, face = stillbirth(tmp_path)
    level, ev = _core.classify_running_agent(
        meta, face, T0, stillbirth_age_min=60.0, interrupted_frozen_min=180.0
    )
    assert level == "START_MISSING"
    assert ev["ageMin"] > 60


def test_type_a_threshold_boundary_young_not_flagged(tmp_path):
    # 30min 齡、artifacts 缺席——<60min 不得旗標（首檔 p50=12min，慢啟動是常態）
    p = write_meta(tmp_path, created=iso(T0 - timedelta(minutes=30)))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, _ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level is None


def test_type_a_empty_artifacts_dir_counts_as_missing(tmp_path):
    # artifacts 目錄在場但零檔＝仍屬「缺/空」
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=2)))
    make_face(tmp_path, files=0)
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, _ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level == "START_MISSING"


def test_interrupted_air_frozen_over_180min(tmp_path):
    # 中斷氣：artifacts 在場、最新檔凍結 4h、無 output.txt
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=6)))
    make_face(tmp_path, files=5, newest=T0 - timedelta(minutes=240))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level == "SILENCE"
    assert ev["newestArtifactAgeMin"] > 180


def test_interrupted_threshold_boundary_fresh_not_flagged(tmp_path):
    # 最新檔 90min——<180min 不得旗標（輪內間距 max 106min 內屬正常）
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=6)))
    make_face(tmp_path, files=5, newest=T0 - timedelta(minutes=90))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, _ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level is None


def test_type_b_output_txt_exists_immediate(tmp_path):
    # 型 B：running ∧ output.txt 存在 → 即報（無靜止窗條件——sweeper 面）
    out = tmp_path / "agents" / PARENT / AGENT / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"final report")
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=6)), output_file=str(out))
    make_face(tmp_path, files=5, newest=T0 - timedelta(minutes=240))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), out
    )
    level, ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level == "COMPLETION_SUSPECTED"
    assert ev["outputSize"] == len(b"final report")


def test_type_b_precedence_over_silence(tmp_path):
    # 同時滿足中斷氣與型 B——COMPLETION_SUSPECTED 優先（產物在場＝可回收）
    out = tmp_path / "agents" / PARENT / AGENT / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"report")
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=6)), output_file=str(out))
    make_face(tmp_path, files=5, newest=T0 - timedelta(minutes=400))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), out
    )
    level, _ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level == "COMPLETION_SUSPECTED"


def test_running_fresh_no_event(tmp_path):
    # 活體：artifacts 新鮮、無 output.txt
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=1)))
    make_face(tmp_path, files=4, newest=T0 - timedelta(minutes=10))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, _ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level is None


def test_clock_rollback_future_created_at_not_classified(tmp_path):
    # createdAt 在未來＝時鐘回撥——禁判（禁誤報）
    p = write_meta(tmp_path, created=iso(T0 + timedelta(hours=1)))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    level, ev = _core.classify_running_agent(read_meta(p), face, T0)
    assert level is None
    assert ev.get("clockAnomaly") is True


# --- 五級常數＋dedup key（codex 五級表） ---


def test_five_alert_levels_present():
    levels = {
        _core.ALERT_START_MISSING,
        _core.ALERT_SILENCE,
        _core.ALERT_COMPLETION_SUSPECTED,
        _core.ALERT_HARD_DEATH,
        _core.ALERT_UNKNOWN,
    }
    assert len(levels) == 5


def test_dedup_key_attempt_plus_alert():
    assert _core.dedup_key("agent_x", "SILENCE") == "agent_x+SILENCE"


# --- completion_suspected（session-local 三條件：產物＋靜止 ≥15m＋running 由 caller 保證） ---


def test_completion_suspected_requires_quiesce(tmp_path):
    out = tmp_path / "agents" / PARENT / AGENT / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"report")
    p = write_meta(tmp_path, created=iso(T0 - timedelta(hours=1)), output_file=str(out))
    make_face(tmp_path, files=2, newest=T0 - timedelta(minutes=10))
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), out
    )
    ok, _ev = _core.completion_suspected(read_meta(p), face, T0, quiesce_min=15.0)
    assert ok is False  # 靜止僅 10min < 15min

    ok, ev = _core.completion_suspected(
        read_meta(p), face, T0 + timedelta(minutes=10), quiesce_min=15.0
    )
    assert ok is True
    assert ev["quiesceMin"] >= 15


# --- start_evidence_present（waiter START_MISSING 驗活面） ---


def test_start_evidence_absent_when_both_faces_empty(tmp_path):
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    assert _core.start_evidence_present(face, exec_file_count=0) is False


def test_start_evidence_present_via_artifacts_or_exec(tmp_path):
    make_face(tmp_path, files=1, newest=T0)
    face = _core.face_snapshot(
        _core.artifacts_dir_for(tmp_path / "artifacts", AGENT), None
    )
    assert _core.start_evidence_present(face, exec_file_count=0) is True
    empty_face = _core.face_snapshot(
        tmp_path / "artifacts" / "nope", None
    )
    assert _core.start_evidence_present(empty_face, exec_file_count=2) is True


def test_start_evidence_present_via_output_txt(tmp_path):
    # output.txt 在場＝工作已發生（completion face 擁有判讀——START_MISSING 禁重複旗標）
    out = tmp_path / "agents" / PARENT / AGENT / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"done")
    empty_face = _core.face_snapshot(
        tmp_path / "artifacts" / "nope", out
    )
    assert _core.start_evidence_present(empty_face, exec_file_count=0) is True


# --- scan_zcode_agents：全庫掃描合成（sweeper 消費面） ---


def test_scan_zcode_agents_full_scenarios(tmp_path):
    now = T0
    # 型 A 死胎
    write_meta(tmp_path, agent="agent_a", created=iso(now - timedelta(hours=2)))
    # 中斷氣
    write_meta(tmp_path, agent="agent_b", created=iso(now - timedelta(hours=6)))
    make_face(tmp_path, agent="agent_b", files=3, newest=now - timedelta(minutes=240))
    # 型 B
    out = tmp_path / "agents" / PARENT / "agent_c" / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"done report")
    write_meta(
        tmp_path, agent="agent_c", created=iso(now - timedelta(hours=3)),
        output_file=str(out),
    )
    make_face(tmp_path, agent="agent_c", files=2, newest=now - timedelta(minutes=200))
    # 活體
    write_meta(tmp_path, agent="agent_d", created=iso(now - timedelta(minutes=10)))
    # terminal（不在事件範圍）
    write_meta(tmp_path, agent="agent_e", status="completed")
    # JSON 損壞
    write_meta(tmp_path, agent="agent_f", raw="{broken")
    # 時鐘回撥
    write_meta(tmp_path, agent="agent_g", created=iso(now + timedelta(hours=1)))

    result = _core.scan_zcode_agents(
        tmp_path / "agents",
        tmp_path / "artifacts",
        now,
        stillbirth_age_min=60.0,
        interrupted_frozen_min=180.0,
    )
    by_type = {e.alert_type for e in result["events"]}
    assert by_type == {"START_MISSING", "SILENCE", "COMPLETION_SUSPECTED", "UNKNOWN"}
    types = {e.agent_id: e.alert_type for e in result["events"]}
    assert types["agent_a"] == "START_MISSING"
    assert types["agent_b"] == "SILENCE"
    assert types["agent_c"] == "COMPLETION_SUSPECTED"
    assert types["agent_f"] == "UNKNOWN"
    cov = result["coverage"]
    assert cov["discovered"] == 7
    assert cov["terminal"] == 1
    assert cov["running_fresh"] == 1  # agent_d 活體
    assert cov["clock_anomaly"] == 1  # agent_g 時鐘回撥禁判（獨立計數，不誤報）
    # 去重鍵格式
    for e in result["events"]:
        assert e.dedup_key == _core.dedup_key(e.attempt_id, e.alert_type)


def test_scan_zombie_event_fields(tmp_path):
    now = T0
    write_meta(tmp_path, agent="agent_a", created=iso(now - timedelta(hours=2)))
    result = _core.scan_zcode_agents(tmp_path / "agents", tmp_path / "artifacts", now)
    (e,) = result["events"]
    d = e.to_dict()
    assert d["agentId"] == "agent_a"
    assert d["attemptId"] == "agent_a"
    assert d["parentSessionId"] == PARENT
    assert d["alertType"] == "START_MISSING"
    assert d["dedupKey"] == "agent_a+START_MISSING"
    assert "detectedAt" in d and "ageMin" in d
