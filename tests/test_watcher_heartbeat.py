"""watcher heartbeat 腿＋stale 判準＋分態＋單次 re-arm 測試（AIR-158）.

liveness 腿 amendment（前例 AIR-152 同形態）：watcher 運行中週期 append
heartbeat（跟隨 wait/re-arm 輪詢節奏，不獨立計時）；stall advisory exit 記
advisory 行（分態——有目的退出非無聲死亡）；watcher_death_suspect 只消費
liveness 台帳 heartbeat 軸，與 bridge 雙軸 _job_stalled 互斥可判；
scripts/watcher_rearm.py 對 stale armed rows 單次 re-arm（rearmed row 在案
→只報警不再重掛）；watcher_pairing_nag 催告語義升級死亡檔。

frozen spec 零變：heartbeat/advisory 僅新增 append 事件，T1-T8 狀態機與
exit 契約由 tests/test_bridge_waiter.py＋test_bridge_dispatch_watcher_
doctrine.py＋test_watcher_liveness.py 釘住（本檔不重釘）。
"""

import io
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/bridge_waiter.py")
REARM = load_module("scripts/watcher_rearm.py")
NAG = load_module("hooks/watcher_pairing_nag.py")

WAITER_SRC = REPO_ROOT / "scripts" / "bridge_waiter.py"
NAG_SRC = REPO_ROOT / "hooks" / "watcher_pairing_nag.py"

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
TS_FRESH = "2026-09-21T11:58:00.000Z"  # NOW 前 2 分鐘
TS_ADVANCED = "2026-09-21T11:59:30.000Z"  # NOW 前 30 秒（progressed 面）
TS_OLD = "2026-09-21T11:45:00.000Z"  # NOW 前 15 分鐘（worker 軸跨 5m floor）
WAKE_JSON = (
    '{"wake":"stuck","jobId":"job-a","axes":["runtime"],'
    '"silenceMinutes":{"worker":6.1,"runtime":11.2}}'
)


def _payload(
    status: str = "running",
    hb: str | None = TS_FRESH,
    ev: str | None = TS_FRESH,
    ts: str = TS_FRESH,
    final_text: str = "done",
) -> dict:
    extra: dict = {}
    if hb is not None:
        extra["heartbeatAt"] = hb
    if ev is not None:
        extra["lastEventAt"] = ev
    return {
        "job": {
            "id": "job-a",
            "status": status,
            "family": "codex",
            "sessionId": "s1",
            "timestamp": ts,
            "extra": extra,
        },
        "finalText": final_text,
    }


class FakeClient:
    """version/wait/show 最小面（wait 依 script 供給 exit）。"""

    bin_path = "/fake/delegate/2.0.22/bin/delegate-bridge"

    def __init__(
        self,
        shows: dict,
        waits: list[dict] | None = None,
        version: str = "2.0.22",
    ) -> None:
        self._shows = shows
        self._waits = list(waits or [])
        self._version = version

    def version(self) -> str:
        return self._version

    def wait(
        self,
        job_ids: list[str],
        timeout_ms: int,
        stuck_after_ms: int,
        *,
        wake_on_stuck: bool = False,
        wake_axis: str = "runtime",
    ) -> tuple[int, str, str]:
        step = self._waits.pop(0) if self._waits else {"exit": 0}
        return (
            int(step["exit"]),
            str(step.get("stdout", "")),
            str(step.get("stderr", "")),
        )

    def show(self, job_id: str) -> dict:
        entry = self._shows[job_id]
        if isinstance(entry, list):
            return entry.pop(0)
        return entry


def _run(client: FakeClient, liveness_path: Path | None) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        client,
        ["job-a"],
        now=lambda: NOW,
        stdout=out,
        stderr=err,
        liveness_path=liveness_path,
    )
    return code, out.getvalue(), err.getvalue()


def _lines(path: Path) -> list[dict]:
    return [
        json.loads(ln)
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


# ---------------------------------------------------------------------------
# AC#1 heartbeat 腿：格式＋append（arm 時＋每次輪詢後）＋停用面＋損壞容錯
# ---------------------------------------------------------------------------


def test_heartbeat_appended_at_arm_and_after_each_poll(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    client = FakeClient(
        shows={
            "job-a": [
                _payload(hb=TS_FRESH, ev=TS_FRESH, ts=TS_FRESH),
                _payload(hb=TS_ADVANCED, ev=TS_FRESH, ts=TS_FRESH),
                _payload(status="completed"),
            ]
        },
        waits=[{"exit": 124}, {"exit": 0}],
    )
    code, _out, _ = _run(client, path)
    assert code == 0
    hbs = [e for e in _lines(path) if e["event"] == "heartbeat"]
    assert len(hbs) == 2, "T1 首輪＋124 輪詢後各一輪 heartbeat"
    assert all(e["jobId"] == "job-a" for e in hbs)
    armed = [e for e in _lines(path) if e["event"] == "armed"]
    collected = [e for e in _lines(path) if e["event"] == "collected"]
    assert len(armed) == 1 and len(collected) == 1, "既有登記腿語義不變"


def test_heartbeat_row_format(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    client = FakeClient(shows={"job-a": _payload(status="completed")})
    code, _, _ = _run(client, path)
    assert code == 0
    hb = next(e for e in _lines(path) if e["event"] == "heartbeat")
    assert hb["schema"] == "liveness/1"
    assert isinstance(hb["pid"], int) and hb["pid"] > 0
    ts = datetime.fromisoformat(hb["ts"])  # 可計齊 ISO（帶 offset）
    assert ts.tzinfo is not None


def test_heartbeat_disabled_without_liveness_path(tmp_path):
    client = FakeClient(shows={"job-a": _payload(status="completed")})
    code, _, _ = _run(client, None)
    assert code == 0
    assert not (tmp_path / ".agent-tmp").exists(), "不傳 liveness_path＝腿停用"


def test_heartbeat_write_failure_tolerated(tmp_path):
    """輔助腿容錯：路徑不可寫 → stderr 診斷、frozen spec exit 契約不變。"""
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    client = FakeClient(shows={"job-a": _payload(status="completed")})
    code, out, err = _run(client, blocker / "liveness.jsonl")
    assert code == 0
    assert '"schema":"collection-receipt/1"' in out
    assert "liveness 登記失敗" in err


def test_heartbeat_survives_corrupt_existing_ledger(tmp_path):
    """既有台帳含壞行 → append-only 照寫不炸（損壞容錯語義延伸）。"""
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("garbage line\n{broken json\n", encoding="utf-8")
    client = FakeClient(shows={"job-a": _payload(status="completed")})
    code, _, _ = _run(client, path)
    assert code == 0
    rows = _mod.parse_liveness_rows(path.read_text(encoding="utf-8"))
    hbs = [e for e in rows if e["event"] == "heartbeat"]
    assert len(hbs) == 1


# ---------------------------------------------------------------------------
# 分態腿：stall advisory exit 記 advisory 行（有目的退出≠無聲死亡）
# ---------------------------------------------------------------------------


def test_legacy_stall_advisory_exit_records_advisory_row(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    client = FakeClient(shows={"job-a": _payload(hb=TS_OLD, ev=TS_OLD, ts=TS_OLD)})
    code, _out, _ = _run(client, path)
    assert code == 3, "legacy T4 advisory 語義不變"
    adv = [e for e in _lines(path) if e["event"] == "advisory"]
    assert len(adv) == 1 and adv[0]["jobId"] == "job-a"
    assert datetime.fromisoformat(adv[0]["advisedAt"]).tzinfo is not None
    # 分態：advisory 行在案 → 之後掃描不得誤判 watcher 死亡
    rows = _mod.parse_liveness_rows(path.read_text(encoding="utf-8"))
    later = NOW + timedelta(hours=2)
    assert (
        _mod.watcher_death_suspect([r for r in rows if r["jobId"] == "job-a"], later)
        is False
    )


def test_native_wake_exit3_also_records_advisory_row(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    client = FakeClient(
        shows={"job-a": _payload()},
        waits=[{"exit": 3, "stdout": WAKE_JSON}],
        version="2.0.23",
    )
    code, _, _ = _run(client, path)
    assert code == 3
    adv = [e for e in _lines(path) if e["event"] == "advisory"]
    assert len(adv) == 1 and adv[0]["jobId"] == "job-a"


# ---------------------------------------------------------------------------
# AC#2 stale 判準：watcher_death_suspect（liveness heartbeat 軸）
# ---------------------------------------------------------------------------


def _live_row(event: str, minutes_ago: float, job: str = "job-a") -> dict:
    ts = (NOW - timedelta(minutes=minutes_ago)).isoformat()
    key = {
        "armed": "armedAt",
        "heartbeat": "ts",
        "collected": "collectedAt",
        "advisory": "advisedAt",
        "rearmed": "rearmedAt",
    }[event]
    return {"schema": "liveness/1", "event": event, "jobId": job, key: ts, "pid": 1}


def test_death_suspect_after_stale_threshold():
    rows = [_live_row("armed", 90), _live_row("heartbeat", 90)]
    assert _mod.watcher_death_suspect(rows, NOW) is True


def test_alive_when_heartbeat_recent():
    rows = [_live_row("armed", 90), _live_row("heartbeat", 10)]
    assert _mod.watcher_death_suspect(rows, NOW) is False


def test_armed_only_no_heartbeat_goes_stale():
    """舊版 watcher（heartbeat 腿前）死於首輪前——armedAt 老化即 stale。"""
    rows = [_live_row("armed", 90)]
    assert _mod.watcher_death_suspect(rows, NOW) is True


def test_collected_or_advisory_rows_never_death():
    for extra in (_live_row("collected", 1), _live_row("advisory", 89)):
        rows = [_live_row("armed", 90), _live_row("heartbeat", 90), extra]
        assert _mod.watcher_death_suspect(rows, NOW) is False


def test_no_armed_row_is_not_death():
    assert _mod.watcher_death_suspect([_live_row("heartbeat", 90)], NOW) is False
    assert _mod.watcher_death_suspect([], NOW) is False


def test_unparseable_timestamps_fail_safe_not_death():
    rows = [
        {
            "schema": "liveness/1",
            "event": "armed",
            "jobId": "job-a",
            "armedAt": "garbage",
        }
    ]
    assert _mod.watcher_death_suspect(rows, NOW) is False


def test_parse_liveness_rows_skips_corrupt_lines():
    text = (
        "garbage\n"
        "{broken\n"
        "\n"
        "[1, 2]\n"
        + json.dumps({"event": "armed", "jobId": "job-a", "armedAt": "x"})
        + "\n"
    )
    rows = _mod.parse_liveness_rows(text)
    assert len(rows) == 1 and rows[0]["event"] == "armed"


def test_liveness_last_seen_takes_newest_parseable():
    rows = [_live_row("armed", 90), _live_row("heartbeat", 10)]
    assert _mod.liveness_last_seen(rows) == NOW - timedelta(minutes=10)
    assert _mod.liveness_last_seen([{"event": "armed", "jobId": "j"}]) is None


def test_threshold_pinned_across_waiter_and_nag_above_poll_cap():
    """鏡像常數防 drift：nag 與 waiter 保持獨立實作但同值；
    閾值必須高於 T_GROW_CAP_MIN（正常輪詢間距上限）以免誤判。"""
    pat = re.compile(r"HEARTBEAT_STALE_THRESHOLD_MIN\s*=\s*([0-9.]+)")
    waiter = pat.search(WAITER_SRC.read_text(encoding="utf-8"))
    nag = pat.search(NAG_SRC.read_text(encoding="utf-8"))
    assert waiter and nag, "兩檔皆須有 HEARTBEAT_STALE_THRESHOLD_MIN 常數"
    assert float(waiter.group(1)) == float(nag.group(1))
    assert float(waiter.group(1)) > _mod.T_GROW_CAP_MIN, (
        "閾值須高於最大 re-arm 間距（20m cap）——dogfood 複核點"
    )


# ---------------------------------------------------------------------------
# AC#3 分態互斥：job stall（bridge 雙軸）與 watcher death（liveness 軸）互不誤發
# ---------------------------------------------------------------------------


def _snapshot(hb: str, ev: str, ts: str):
    # load_module returns a runtime module, not a static type namespace.
    return _mod.JobSnapshot(
        job_id="job-a",
        status="running",
        family="codex",
        session_id="s1",
        timestamp=ts,
        heartbeat_at=hb,
        last_event_at=ev,
    )


def test_stall_and_death_axes_disjoint():
    stale_snap = _snapshot(TS_OLD, TS_OLD, TS_OLD)
    fresh_snap = _snapshot(TS_FRESH, TS_FRESH, TS_FRESH)
    live_fresh = [_live_row("armed", 90), _live_row("heartbeat", 2)]
    live_stale = [_live_row("armed", 90), _live_row("heartbeat", 90)]
    # job stall（bridge 軸 stale）不得誤發 watcher death
    assert _mod._job_stalled(stale_snap, "discussion", NOW) is True
    assert _mod.watcher_death_suspect(live_fresh, NOW) is False
    # watcher death（liveness 軸 stale）不得誤發 job stall
    assert _mod._job_stalled(fresh_snap, "discussion", NOW) is False
    assert _mod.watcher_death_suspect(live_stale, NOW) is True


def test_advisory_record_leg_keeps_stalled_job_out_of_death_bucket(tmp_path):
    """端到端分態：stall → advisory exit → 台帳帶 advisory 行 → 死亡判準 False。"""
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    client = FakeClient(shows={"job-a": _payload(hb=TS_OLD, ev=TS_OLD, ts=TS_OLD)})
    code, _, _ = _run(client, path)
    assert code == 3
    rows = _mod.parse_liveness_rows(path.read_text(encoding="utf-8"))
    assert _mod.watcher_death_suspect(rows, NOW + timedelta(hours=2)) is False


# ---------------------------------------------------------------------------
# AC#4 watcher_rearm：掃描分桶＋單次 re-arm＋broken alert
# ---------------------------------------------------------------------------


def test_scan_plan_buckets():
    rows = (
        [_live_row("armed", 90), _live_row("heartbeat", 90)]  # job-a：死→rearm
        + [
            _live_row("armed", 90, "job-b"),
            _live_row("heartbeat", 90, "job-b"),
            _live_row("rearmed", 80, "job-b"),
            _live_row("heartbeat", 70, "job-b"),
        ]  # 重掛後又死→broken
        + [
            _live_row("armed", 90, "job-c"),
            _live_row("heartbeat", 2, "job-c"),
        ]  # 活→fresh
        + [
            _live_row("armed", 90, "job-d"),
            _live_row("heartbeat", 1, "job-d"),
            _live_row("collected", 1, "job-d"),
        ]  # 收完→concluded
        + [
            _live_row("armed", 90, "job-e"),
            _live_row("heartbeat", 89, "job-e"),
            _live_row("advisory", 89, "job-e"),
        ]  # stall 已 wake→concluded
    )
    plan = REARM.scan_plan(rows, NOW)
    assert plan["rearm"] == ["job-a"]
    assert plan["broken"] == ["job-b"]
    assert plan["fresh"] == ["job-c"]
    assert plan["concluded"] == ["job-d", "job-e"]


def test_scan_plan_corrupt_lines_tolerated():
    rows = _mod.parse_liveness_rows(
        "garbage\n{broken\n"
        + json.dumps(_live_row("armed", 90, "job-a"))
        + "\n"
        + json.dumps(_live_row("heartbeat", 90, "job-a"))
        + "\n"
    )
    plan = REARM.scan_plan(rows, NOW)
    assert plan["rearm"] == ["job-a"]


def test_execute_plan_spawns_once_and_appends_rearmed_row(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(_live_row("armed", 90, "job-a"))
        + "\n"
        + json.dumps(_live_row("heartbeat", 90, "job-a"))
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def spawn(job_id: str) -> int:
        calls.append(job_id)
        return 4242

    rows = _mod.parse_liveness_rows(path.read_text(encoding="utf-8"))
    plan = REARM.scan_plan(rows, datetime.now(UTC))
    rearmed = REARM.execute_plan(
        plan, liveness_path=path, spawn=spawn, err=io.StringIO()
    )
    assert rearmed == ["job-a"] and calls == ["job-a"]
    rows = _mod.parse_liveness_rows(path.read_text(encoding="utf-8"))
    rec = [r for r in rows if r["event"] == "rearmed"]
    assert len(rec) == 1 and rec[0]["jobId"] == "job-a" and rec[0]["pid"] == 4242
    assert datetime.fromisoformat(rec[0]["rearmedAt"]).tzinfo is not None

    # 第二輪：rearmed row 在案 → 只報警不再重掛（單次、禁無限迴圈）
    later = datetime.now(UTC) + timedelta(hours=2)
    plan2 = REARM.scan_plan(
        _mod.parse_liveness_rows(path.read_text(encoding="utf-8")), later
    )
    assert plan2["rearm"] == [] and plan2["broken"] == ["job-a"]
    REARM.execute_plan(plan2, liveness_path=path, spawn=spawn, err=io.StringIO())
    assert calls == ["job-a"], "broken 桶不得再 spawn"


def test_main_rearms_with_fake_spawn_and_emits_tail_json(tmp_path, capsys):
    liveness = tmp_path / ".agent-tmp" / "liveness.jsonl"
    liveness.parent.mkdir(parents=True)
    liveness.write_text(
        json.dumps(_live_row("armed", 90, "job-a"))
        + "\n"
        + json.dumps(_live_row("heartbeat", 90, "job-a"))
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def spawn(job_id: str) -> int:
        calls.append(job_id)
        return 7

    code = REARM.main(
        [
            "--liveness-path",
            str(liveness),
            "--bridge-bin",
            "/fake/bin",
            "--waiter",
            "/fake/waiter.py",
            "--log",
            str(tmp_path / "rearm.log"),
        ],
        spawn=spawn,
        now=datetime.now(UTC),
    )
    assert code == 0 and calls == ["job-a"]
    tail = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert tail["schema"] == REARM.REARM_SCHEMA
    assert tail["rearmed"] == ["job-a"]


def test_main_missing_ledger_is_noop_exit_0(tmp_path):
    code = REARM.main(
        ["--liveness-path", str(tmp_path / "absent" / "liveness.jsonl")],
        spawn=lambda j: 1,
        now=datetime.now(UTC),
    )
    assert code == 0


# ---------------------------------------------------------------------------
# AC#4 nag 升級：armed row 在場但 heartbeat 停滯 → 「watcher 疑似死亡」催告
# ---------------------------------------------------------------------------


def _make_repo(tmp_path: Path, rows: list) -> Path:
    repo = tmp_path / "repo"
    (repo / ".delegate-bridge").mkdir(parents=True)
    (repo / ".delegate-bridge" / "jobs.json").write_text(
        json.dumps(rows, ensure_ascii=False), encoding="utf-8"
    )
    return repo


def _nag_job(job_id: str, session: str, minutes_ago: float) -> dict:
    return {
        "id": job_id,
        "status": "running",
        "sessionId": session,
        "timestamp": (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat(),
    }


def _write_liveness(repo: Path, lines: list[dict]) -> None:
    liveness = repo / ".agent-tmp" / "liveness.jsonl"
    liveness.parent.mkdir(parents=True, exist_ok=True)
    liveness.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in lines) + "\n",
        encoding="utf-8",
    )


def _nag_rows(job_id: str, spec: list[tuple[str, float]]) -> list[dict]:
    key_map = {
        "armed": "armedAt",
        "heartbeat": "ts",
        "collected": "collectedAt",
        "advisory": "advisedAt",
        "rearmed": "rearmedAt",
    }
    rows = []
    for event, ago in spec:
        rows.append(
            {
                "schema": "liveness/1",
                "event": event,
                "jobId": job_id,
                key_map[event]: (
                    datetime.now(UTC) - timedelta(minutes=ago)
                ).isoformat(),
                "pid": 1,
            }
        )
    return rows


def test_nag_dead_watcher_urges_rearm(tmp_path):
    repo = _make_repo(tmp_path, [_nag_job("job-a-1", "sess-1", 120.0)])
    _write_liveness(repo, _nag_rows("job-a-1", [("armed", 90), ("heartbeat", 90)]))
    reason = NAG.evaluate({"session_id": "sess-1", "cwd": str(repo)})
    assert reason is not None
    assert "疑似死亡" in reason
    assert "watcher_rearm.py" in reason  # 單次自動重掛入口已內嵌
    assert "job-a-1" in reason


def test_nag_fresh_heartbeat_no_block(tmp_path):
    repo = _make_repo(tmp_path, [_nag_job("job-a-1", "sess-1", 120.0)])
    _write_liveness(repo, _nag_rows("job-a-1", [("armed", 90), ("heartbeat", 2)]))
    assert NAG.evaluate({"session_id": "sess-1", "cwd": str(repo)}) is None


def test_nag_advisory_row_suppresses_dead_bucket(tmp_path):
    """分態：stall 已 advisory wake 過——死亡檔不誤發。"""
    repo = _make_repo(tmp_path, [_nag_job("job-a-1", "sess-1", 120.0)])
    _write_liveness(
        repo,
        _nag_rows("job-a-1", [("armed", 90), ("heartbeat", 90), ("advisory", 89.5)]),
    )
    assert NAG.evaluate({"session_id": "sess-1", "cwd": str(repo)}) is None


def test_nag_dead_and_unpaired_share_one_block_and_budget(tmp_path):
    repo = _make_repo(
        tmp_path,
        [_nag_job("job-dead", "sess-1", 120.0), _nag_job("job-new", "sess-1", 120.0)],
    )
    _write_liveness(repo, _nag_rows("job-dead", [("armed", 90), ("heartbeat", 90)]))
    reason = NAG.evaluate({"session_id": "sess-1", "cwd": str(repo)})
    assert reason is not None
    assert "job-dead" in reason and "job-new" in reason
    state = json.loads(
        (repo / ".agent-tmp" / "watcher-pairing-nag.json").read_text(encoding="utf-8")
    )
    entry = state["sessions"]["sess-1"]
    assert entry["count"] == 1, "兩檔併一次 block，預算計一次"


def test_nag_dead_job_nagged_only_once(tmp_path):
    repo = _make_repo(tmp_path, [_nag_job("job-a-1", "sess-1", 120.0)])
    _write_liveness(repo, _nag_rows("job-a-1", [("armed", 90), ("heartbeat", 90)]))
    payload = {"session_id": "sess-1", "cwd": str(repo)}
    assert NAG.evaluate(payload) is not None
    assert NAG.evaluate(payload) is None, "同 job 死亡檔至多催告一次"


def test_nag_row_without_timestamp_not_dead(tmp_path):
    """無可計齊時間戳（舊格式行）＝非 staleness——維持在場語義不誤報。"""
    repo = _make_repo(tmp_path, [_nag_job("job-a-1", "sess-1", 120.0)])
    _write_liveness(repo, [{"event": "armed", "jobId": "job-a-1"}])
    assert NAG.evaluate({"session_id": "sess-1", "cwd": str(repo)}) is None
