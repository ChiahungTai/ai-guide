"""child_heartbeat 契約測試（AIR-160 AC#4）.

驗證式：atomic append sidecar——seq 自動遞增、emittedAt 由 helper 寫（呼叫端
禁生成）、半行（torn tail）容錯丟棄、亂序偵測。oracle＝I 級（impl 衍生——
格式契約單一源即本模組；watcher 讀面為消費者投影）。

契約面（supervision contract——skills/agent-workflow/SKILL.md「Worker
supervision contract」節）：child 只寫自己的 sidecar、禁自報 collected、
emittedAt 由 helper 機械寫。
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/child_heartbeat.py")

NOW = datetime(2026, 9, 20, 11, 5, 0, tzinfo=UTC)


def hb_path(tmp_path: Path) -> Path:
    return tmp_path / ".agent-tmp" / "heartbeats" / "sess_subagent_agent_x1.jsonl"


def rec_line(seq: int, *, attempt: str = "att-1", state: str = "working") -> str:
    return (
        json.dumps(
            {
                "schema": "child-heartbeat/1",
                "seq": seq,
                "taskId": "sess_subagent_agent_x1",
                "attemptId": attempt,
                "state": state,
                "emittedAt": "2026-09-20T11:04:00.000+00:00",
                "note": None,
                "intervalSecs": 60,
            },
            ensure_ascii=False,
        )
        + "\n"
    )


# ---------------------------------------------------------------------------
# 正常 append
# ---------------------------------------------------------------------------


def test_append_creates_sidecar_with_helper_emitted_at(tmp_path):
    path = hb_path(tmp_path)
    record, anomalies = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert anomalies == []
    assert record["schema"] == "child-heartbeat/1"
    assert record["seq"] == 1
    assert record["taskId"] == "sess_subagent_agent_x1"
    assert record["attemptId"] == "att-1"
    assert record["state"] == "working"
    # emittedAt 由 helper 機械寫（注入時鐘）——非呼叫端生成
    assert record["emittedAt"] == "2026-09-20T11:05:00.000+00:00"
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == record


def test_cli_has_no_time_flag_emitted_at_forced_from_helper():
    # 偽造禁令的機械面：CLI 無 --emitted-at 旗標——時間只能由 helper 寫
    try:
        _mod.main(
            [
                "--file",
                "x.jsonl",
                "--task-id",
                "t",
                "--attempt-id",
                "a",
                "--state",
                "working",
                "--emitted-at",
                "2026-01-01T00:00:00+00:00",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2  # argparse unrecognized argument
    else:
        raise AssertionError("--emitted-at 旗標不應存在（emittedAt 禁呼叫端生成）")


def test_done_state_is_legal_child_self_report(tmp_path):
    path = hb_path(tmp_path)
    record, _anomalies = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="done",
        note="finish",
        now=NOW,
    )
    assert record["state"] == "done"
    assert record["note"] == "finish"


def test_invalid_state_fail_loud(tmp_path):
    path = hb_path(tmp_path)
    try:
        _mod.append_heartbeat(
            path,
            task_id="t",
            attempt_id="a",
            state="collected",  # child 禁自報 collected——狀態集只有 working|done
            now=NOW,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("state=collected 應拒絕（child 禁自報 collected）")
    assert not path.exists()


def test_cli_roundtrip_and_exit_codes(tmp_path, capsys):
    path = hb_path(tmp_path)
    argv = [
        "--file",
        str(path),
        "--task-id",
        "sess_subagent_agent_x1",
        "--attempt-id",
        "att-1",
        "--state",
        "working",
        "--note",
        "step1",
    ]
    assert _mod.main(argv) == 0
    first = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert first["seq"] == 1
    assert _mod.main([*argv, "--state", "done"]) == 0
    second = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert second["seq"] == 2
    assert second["state"] == "done"


# ---------------------------------------------------------------------------
# seq 遞增
# ---------------------------------------------------------------------------


def test_seq_increments_across_appends(tmp_path):
    path = hb_path(tmp_path)
    seqs = []
    for i in range(3):
        record, _ = _mod.append_heartbeat(
            path,
            task_id="sess_subagent_agent_x1",
            attempt_id="att-1",
            state="working",
            now=NOW,
        )
        seqs.append(record["seq"])
    assert seqs == [1, 2, 3]


def test_seq_continues_from_max_after_manual_gap(tmp_path):
    # 既有檔 seq 1..3（外部產生）→ helper 從 max+1 續——禁重號
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rec_line(1) + rec_line(2) + rec_line(3))
    record, anomalies = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert anomalies == []
    assert record["seq"] == 4


def test_seq_ignores_other_attempt_records(tmp_path):
    # join 語義：記錄按 attempt 歸屬——helper 遞增看全部有效記錄的 max（台帳單調）
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rec_line(1) + rec_line(2, attempt="att-0"))
    record, _ = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert record["seq"] == 3


# ---------------------------------------------------------------------------
# 半行（torn tail）容錯
# ---------------------------------------------------------------------------


def test_torn_tail_discarded_and_append_continues(tmp_path):
    # crash 半寫：末行無換行＝半截——append 前補換行終止該行（不改寫既有位元組），
    # 讀面丟棄；seq 從最後有效記錄續
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torn = json.dumps(
        {
            "schema": "child-heartbeat/1",
            "seq": 2,
            "taskId": "sess_subagent_agent_x1",
            "attemptId": "att-1",
            "state": "working",
            "emittedAt": "2026-09-20T11:04:30.000+00:0",
        }
    )[:40]  # 半截 JSON，無換行
    path.write_text(rec_line(1) + torn)
    record, anomalies = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert record["seq"] == 2  # 半截 seq=2 未落地——從有效 max(1)+1 續
    assert "torn-tail-discarded" in anomalies
    raw = path.read_bytes()
    # append-only：既有位元組原樣保留（rec_line(1)＋半截原文），僅補換行＋新行
    assert raw.startswith((rec_line(1) + torn).encode())
    records, read_anomalies = _mod.read_sidecar(path)
    assert [r["seq"] for r in records] == [1, 2]
    # append 已補換行終止半行——檔案 newline 結尾，torn-tail anomaly 消退；
    # 被終止的半截行以 corrupt-line 語義丟棄
    assert "torn-tail-discarded" not in read_anomalies
    assert "corrupt-line-discarded" in read_anomalies


def test_corrupt_middle_line_skipped_valid_lines_kept(tmp_path):
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rec_line(1) + "{oops not json\n" + rec_line(2))
    records, anomalies = _mod.read_sidecar(path)
    assert [r["seq"] for r in records] == [1, 2]
    assert "corrupt-line-discarded" in anomalies
    record, _ = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert record["seq"] == 3


def test_missing_file_yields_empty_records(tmp_path):
    records, anomalies = _mod.read_sidecar(hb_path(tmp_path))
    assert records == []
    assert anomalies == []


# ---------------------------------------------------------------------------
# 亂序偵測
# ---------------------------------------------------------------------------


def test_out_of_order_detected_and_append_heals_monotonic(tmp_path):
    # seq 回退（1,3,2）＝台帳異常——偵測大聲（anomaly），append 照常從 max+1 癒合
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rec_line(1) + rec_line(3) + rec_line(2))
    records, anomalies = _mod.read_sidecar(path)
    assert [r["seq"] for r in records] == [1, 3, 2]  # 偵測不刪證據
    assert "seq-out-of-order" in anomalies
    record, append_anomalies = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert record["seq"] == 4  # max(3)+1——單調癒合
    assert "seq-out-of-order" in append_anomalies


def test_cli_surfaces_anomalies_on_stderr_nonzero_free(tmp_path, capsys):
    # telemetry 面禁靜默——異常上 stderr，但 append 成功＝exit 0（禁擋 worker 主作業）
    path = hb_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rec_line(1) + rec_line(3) + rec_line(2))
    code = _mod.main(
        [
            "--file",
            str(path),
            "--task-id",
            "sess_subagent_agent_x1",
            "--attempt-id",
            "att-1",
            "--state",
            "working",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "seq-out-of-order" in captured.err
    assert json.loads(captured.out.strip().splitlines()[-1])["seq"] == 4


def test_cli_unwritable_target_fail_loud(tmp_path):
    # 目錄位被普通檔占住——parent mkdir 失敗＝IO fail-loud exit 1
    block = tmp_path / "block"
    block.write_text("not a dir")
    code = _mod.main(
        [
            "--file",
            str(block / "hb.jsonl"),
            "--task-id",
            "t",
            "--attempt-id",
            "a",
            "--state",
            "working",
        ]
    )
    assert code == 1


# ---------------------------------------------------------------------------
# 週期 cadence（AIR-160 修復：muse Important——cadence 未定義）
# 契約：heartbeat 週期預設 60s；watcher stale 門檻＝2×週期；週期寫進 sidecar
# row（`intervalSecs`）供 watcher 對帳——擇「寫進 row」：self-describing
# telemetry，per-task 週期調整不需改契約
# ---------------------------------------------------------------------------


def test_interval_secs_defaults_to_contract_60s(tmp_path):
    path = hb_path(tmp_path)
    record, _ = _mod.append_heartbeat(
        path,
        task_id="sess_subagent_agent_x1",
        attempt_id="att-1",
        state="working",
        now=NOW,
    )
    assert record["intervalSecs"] == 60


def test_cli_interval_secs_flag_roundtrip(tmp_path, capsys):
    path = hb_path(tmp_path)
    argv = [
        "--file",
        str(path),
        "--task-id",
        "sess_subagent_agent_x1",
        "--attempt-id",
        "att-1",
        "--state",
        "working",
        "--interval-secs",
        "120",
    ]
    assert _mod.main(argv) == 0
    record = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert record["intervalSecs"] == 120


def test_cli_interval_secs_non_positive_rejected(tmp_path):
    # 非正整數＝旗標錯（exit 2），禁落地半套 row
    path = hb_path(tmp_path)
    for bad in ("0", "-5"):
        try:
            _mod.main(
                [
                    "--file",
                    str(path),
                    "--task-id",
                    "t",
                    "--attempt-id",
                    "a",
                    "--state",
                    "working",
                    "--interval-secs",
                    bad,
                ]
            )
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"--interval-secs {bad} 應拒絕")
    assert not path.exists()


def test_api_interval_secs_invalid_fail_loud(tmp_path):
    path = hb_path(tmp_path)
    for bad in (0, -1, True, "60"):
        try:
            _mod.append_heartbeat(
                path,
                task_id="t",
                attempt_id="a",
                state="working",
                interval_secs=bad,
                now=NOW,
            )
        except ValueError:
            pass
        else:
            raise AssertionError(f"interval_secs={bad!r} 應 ValueError")


def test_valid_record_rejects_missing_or_bad_interval_secs():
    row = {
        "schema": "child-heartbeat/1",
        "seq": 1,
        "taskId": "t",
        "attemptId": "a",
        "state": "working",
        "emittedAt": "2026-09-20T11:04:00.000+00:00",
        "note": None,
        "intervalSecs": 60,
    }
    assert _mod._valid_record(dict(row)) is not None
    missing = dict(row)
    del missing["intervalSecs"]
    for bad in (
        missing,
        {**row, "intervalSecs": 0},
        {**row, "intervalSecs": True},
        {**row, "intervalSecs": "60"},
    ):
        assert _mod._valid_record(bad) is None, (
            f"intervalSecs={bad.get('intervalSecs')!r} 應丟棄"
        )
