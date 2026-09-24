"""AIR-135.7 W2——dispatch_ledger 契約測試（期望登記台帳＋唯讀 sweep reporter）.

釘住 AC#3（liveness 六欄期望登記、registry 只存期望）與 AC#6②（sweep＝唯讀
reporter、只報狀態轉移不報存量、exit 0 有單／1 無單／2 環境錯、偵測與處置
分離——永不自動重派／殺）。路徑隔離：fixture 全落 pytest tmp_path；bridge
jobs.json 用 fixture 合成，不碰真實帳本。
"""

import datetime as dt
import json
from pathlib import Path

import pytest
from conftest import load_module

_led = load_module("scripts/dispatch_ledger.py")

NOW_ISO = "2026-09-25T03:00:00+00:00"


# ---------- fixture helpers ----------


def _job(jid: str, status: str) -> dict:
    return {
        "id": jid,
        "status": status,
        "timestamp": NOW_ISO,
        "family": "glm",
        "summary": "done" if status == "completed" else "",
    }


def _write_jobs(root: Path, rows: list[dict]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "jobs.json").write_text(json.dumps(rows), encoding="utf-8")


def _register(ledger: Path, jid: str, **kw: str) -> int:
    argv = [
        "register",
        "--ledger",
        str(ledger),
        "--id",
        jid,
        "--carrier",
        kw.pop("carrier", "glm"),
        "--at",
        kw.pop("at", NOW_ISO),
    ]
    flag_map = {
        "sink": "--sink",
        "collection_mode": "--collection-mode",
        "owner": "--collector-owner",
        "source": "--liveness-source",
        "anchor": "--anchor",
    }
    for key, flag in flag_map.items():
        if key in kw:
            argv += [flag, kw[key]]
    return _led.main(argv)


def _sweep(capsys: pytest.CaptureFixture[str], tmp_path: Path, ledger: Path, root: Path, *extra: str) -> tuple[int, str]:
    argv = [
        "sweep",
        "--ledger",
        str(ledger),
        "--state-root",
        str(root),
        "--sink-base",
        str(tmp_path),
        "--state",
        str(tmp_path / "sweep-state.json"),
        *extra,
    ]
    code = _led.main(argv)
    return code, capsys.readouterr().out


# ---------- register（AC#3 六欄期望登記） ----------


def test_register_writes_six_column_expectation(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    assert _register(ledger, "job-aaa-111111", carrier="glm") == 0
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    # registry 只存期望——台帳無實際面區塊（實際面權威＝bridge jobs.json，唯讀對接）
    assert set(doc) == {"schema_version", "contract", "note", "expectations"}
    entry = doc["expectations"]["job-aaa-111111"]
    assert entry["dispatch_id"] == "job-aaa-111111"
    assert entry["carrier"] == "glm"
    assert entry["dispatched_at"] == NOW_ISO
    assert entry["sink"] == "receipt-only"
    assert entry["collection_mode"] == "detached"
    assert entry["collector_owner"] == "marshal"
    assert entry["liveness_source"] == "bridge:jobs.json"
    assert entry["registered_at"]
    assert "anchor" not in entry


def test_register_carries_all_six_columns_when_given(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    code = _register(
        ledger,
        "sess_zzz",
        carrier="zcode-native",
        sink="/tmp/artifact.md",
        collection_mode="foreground-wait",
        owner="reviewer",
        source="zcode-native:metadata.json",
        anchor="W2-DONE-WHEN",
    )
    assert code == 0
    entry = json.loads(ledger.read_text(encoding="utf-8"))["expectations"]["sess_zzz"]
    assert entry["sink"] == "/tmp/artifact.md"
    assert entry["collection_mode"] == "foreground-wait"
    assert entry["collector_owner"] == "reviewer"
    assert entry["liveness_source"] == "zcode-native:metadata.json"
    assert entry["anchor"] == "W2-DONE-WHEN"


def test_register_upserts_same_id(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    assert _register(ledger, "job-aaa-111111") == 0
    assert _register(ledger, "job-aaa-111111", sink="/x/a.md") == 0
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    assert len(doc["expectations"]) == 1
    assert doc["expectations"]["job-aaa-111111"]["sink"] == "/x/a.md"


def test_register_missing_id_is_argparse_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _led.main(["register", "--ledger", str(tmp_path / "l.json"), "--carrier", "glm"])
    assert excinfo.value.code == 2
    assert not (tmp_path / "l.json").exists()


def test_register_bad_collection_mode_is_argparse_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        _led.main(
            ["register", "--ledger", str(tmp_path / "l.json"), "--id", "j", "--carrier", "glm", "--collection-mode", "bogus"]
        )
    assert excinfo.value.code == 2


def test_register_blank_carrier_fails_loud(tmp_path: Path) -> None:
    assert _register(tmp_path / "l.json", "job-a", carrier="  ") == 2
    assert not (tmp_path / "l.json").exists()


def test_register_blank_sink_fails_loud(tmp_path: Path) -> None:
    assert _register(tmp_path / "l.json", "job-a", sink=" ") == 2
    assert not (tmp_path / "l.json").exists()


def test_register_bad_at_fails_loud(tmp_path: Path) -> None:
    assert _register(tmp_path / "l.json", "job-a", at="not-a-date") == 2
    assert not (tmp_path / "l.json").exists()


def test_register_corrupt_ledger_fails_no_repair(tmp_path: Path) -> None:
    ledger = tmp_path / "l.json"
    ledger.write_text("{ not json", encoding="utf-8")
    before = ledger.read_bytes()
    assert _register(ledger, "job-a") == 2
    assert ledger.read_bytes() == before


# ---------- show（存量查詢視圖） ----------


def test_show_lists_inventory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    capsys.readouterr()
    assert _led.main(["show", "--ledger", str(ledger)]) == 0
    assert "job-aaa-111111" in capsys.readouterr().out


def test_show_single_missing_id_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    capsys.readouterr()
    assert _led.main(["show", "--ledger", str(ledger), "--id", "job-nope"]) == 1


def test_show_missing_ledger_exit_1(tmp_path: Path) -> None:
    assert _led.main(["show", "--ledger", str(tmp_path / "absent.json")]) == 1


# ---------- 實際面 row 解析與狀態判定 ----------


def test_resolve_exact_and_unique_prefix_and_ambiguous() -> None:
    index = {
        "job-mu7px22a-b1ccwa": _led.ActualRow("job-mu7px22a-b1ccwa", Path("/r"), "completed"),
        "job-mu9zzzz-ffff": _led.ActualRow("job-mu9zzzz-ffff", Path("/r"), "running"),
    }
    row, note = _led.resolve_row("job-mu7px22a-b1ccwa", index)
    assert row is not None and note == ""
    row, note = _led.resolve_row("job-mu7px22a", index)
    assert row is not None and "job-mu7px22a-b1ccwa" in note
    row, note = _led.resolve_row("job-mu", index)
    assert row is None and "撞多" in note
    row, note = _led.resolve_row("sess_zzz", index)
    assert row is None and note == ""


def test_status_in_flight_for_running_row(tmp_path: Path) -> None:
    row = _led.ActualRow("job-a", tmp_path, "running")
    status, note = _led.status_of({"sink": "receipt-only"}, row, "", tmp_path)
    assert status == "in-flight" and "running" in note


def test_status_matched_receipt_only(tmp_path: Path) -> None:
    row = _led.ActualRow("job-a", tmp_path, "completed")
    status, note = _led.status_of({"sink": "receipt-only"}, row, "", tmp_path)
    assert status == "matched" and "collector" in note


def test_status_matched_path_sink_three_step(tmp_path: Path) -> None:
    sink = tmp_path / "artifact.md"
    sink.write_text("body with W2-DONE-WHEN anchor\n", encoding="utf-8")
    row = _led.ActualRow("job-a", tmp_path, "completed")
    entry = {"sink": "artifact.md", "anchor": "W2-DONE-WHEN"}
    status, note = _led.status_of(entry, row, "", tmp_path)
    assert status == "matched" and "三步過" in note


def test_status_sink_missing_variants(tmp_path: Path) -> None:
    row = _led.ActualRow("job-a", tmp_path, "completed")
    status, note = _led.status_of({"sink": "nope.md"}, row, "", tmp_path)
    assert status == "sink-missing" and "缺" in note
    (tmp_path / "empty.md").write_text("", encoding="utf-8")
    status, note = _led.status_of({"sink": "empty.md"}, row, "", tmp_path)
    assert status == "sink-missing" and "空" in note
    (tmp_path / "b.md").write_text("no anchor here\n", encoding="utf-8")
    status, note = _led.status_of({"sink": "b.md", "anchor": "MISSING-ANCHOR"}, row, "", tmp_path)
    assert status == "sink-missing" and "錨點" in note
    # 無 anchor 登記＝錨點人工——前兩步（存在＋非空）過即 pass
    assert _led.status_of({"sink": "b.md"}, row, "", tmp_path)[0] == "matched"


def test_status_terminal_drift_for_non_completed_terminal(tmp_path: Path) -> None:
    for status in ("failed", "output-token-limit"):
        row = _led.ActualRow("job-a", tmp_path, status)
        got, note = _led.status_of({"sink": "receipt-only"}, row, "", tmp_path)
        assert got == "terminal-drift" and status in note


def test_status_unresolved_when_no_row(tmp_path: Path) -> None:
    status, note = _led.status_of({"sink": "receipt-only"}, None, "", tmp_path)
    assert status == "unresolved" and note


# ---------- sweep（AC#6②：唯讀、只報轉移、exit 碼契約） ----------


def test_sweep_first_run_reports_all_new_exit_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "completed"), _job("job-bbb-222222", "running")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    _register(ledger, "job-bbb-222222")
    _register(ledger, "job-ccc-333333")
    capsys.readouterr()
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 0
    assert "new matched" in out
    assert "new in-flight" in out
    assert "new unresolved" in out
    assert "[ACTION]" in out  # 處置分離宣示
    assert (tmp_path / "sweep-state.json").exists()


def test_sweep_no_change_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "completed")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    capsys.readouterr()
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 0
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 1
    assert "（無狀態轉移）" in out


def test_sweep_transition_on_status_change(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "running")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    capsys.readouterr()
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 0
    _write_jobs(root, [_job("job-aaa-111111", "completed")])
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 0
    assert "in-flight → matched" in out
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 1


def test_sweep_reports_removed_expectation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "running"), _job("job-bbb-222222", "running")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    _register(ledger, "job-bbb-222222")
    capsys.readouterr()
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 0
    doc = json.loads(ledger.read_text(encoding="utf-8"))
    del doc["expectations"]["job-bbb-222222"]
    ledger.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 0
    assert "removed" in out and "was in-flight" in out


def test_sweep_is_read_only_over_watched_sources(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "completed")])
    sink = tmp_path / "artifact.md"
    sink.write_text("content\n", encoding="utf-8")
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111", sink="artifact.md")
    capsys.readouterr()
    watched = [root / "jobs.json", ledger, sink]
    before = {p: p.read_bytes() for p in watched}
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 0
    for path in watched:
        assert path.read_bytes() == before[path], f"sweep 改動了被觀察源 {path}"
    # reporter 記憶是 sweep 唯一寫入面
    state = json.loads((tmp_path / "sweep-state.json").read_text(encoding="utf-8"))
    assert state["statuses"] == {"job-aaa-111111": "matched"}


def test_sweep_state_reset_via_delete(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "completed")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    capsys.readouterr()
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 0
    assert _sweep(capsys, tmp_path, ledger, root)[0] == 1
    (tmp_path / "sweep-state.json").unlink()
    code, out = _sweep(capsys, tmp_path, ledger, root)
    assert code == 0 and "new matched" in out  # 刪記憶＝視為首次掃描全量回報


def test_sweep_json_payload(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [_job("job-aaa-111111", "completed"), _job("job-bbb-222222", "running")])
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    _register(ledger, "job-bbb-222222")
    capsys.readouterr()
    code, out = _sweep(capsys, tmp_path, ledger, root, "--json")
    assert code == 0
    payload = json.loads(out)
    assert payload["read_only"] is True
    assert payload["counts"] == {"expectations": 2, "transitions": 2}
    assert len(payload["transitions"]) == 2
    by_id = {tr["dispatch_id"]: tr for tr in payload["transitions"]}
    assert by_id["job-aaa-111111"]["to"] == "matched"
    assert by_id["job-aaa-111111"]["actual_status"] == "completed"
    assert by_id["job-bbb-222222"]["to"] == "in-flight"


def test_sweep_missing_ledger_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "sr"
    _write_jobs(root, [])
    code, _out = _sweep(capsys, tmp_path, tmp_path / "absent.json", root)
    assert code == 2


def test_sweep_explicit_missing_state_root_exit_2(tmp_path: Path) -> None:
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    assert _led.main(["sweep", "--ledger", str(ledger), "--state-root", str(tmp_path / "nope")]) == 2


def test_sweep_no_default_root_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_led, "DEFAULT_STATE_ROOTS", (tmp_path / "x", tmp_path / "y"))
    ledger = tmp_path / "l.json"
    _register(ledger, "job-aaa-111111")
    assert _led.main(["sweep", "--ledger", str(ledger)]) == 2


def test_load_sweep_state_corrupt_raises(tmp_path: Path) -> None:
    state = tmp_path / "s.json"
    state.write_text("!!", encoding="utf-8")
    with pytest.raises(_led.LedgerError):
        _led.load_sweep_state(state)


# ---------- 時間解析 ----------


def test_parse_iso_variants() -> None:
    assert _led.parse_iso("2026-09-25T03:00:00Z").tzinfo is not None
    assert _led.parse_iso("2026-09-25T03:00:00").utcoffset() == dt.timedelta(0)
    with pytest.raises(ValueError):
        _led.parse_iso("bogus")
