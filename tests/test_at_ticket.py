"""at_ticket 契約測試（AIR-157 AC#1–#4）.

驗證式（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）：
- AC#1 狀態機：五主態四異常合法轉移表全覆蓋＋表外轉移 raise fail-loud
- AC#2 arm fail-loud：ARMED 必帶 arm receipt；SCHEDULER_REJECTED 禁靜默
  降級（禁背景 sleep 替代；rejected 不可復活回主線）
- AC#3 cleanup 依 resume_at＋state＋grace：SETTLED/CANCELLED 才可清；
  mtime 不參與判定（誤刪防護）；ARMED 過期＝MISSED 誠實標記候選
- AC#4 skills/at/SKILL.md 改版錨點：狀態機＋禁降級＋MISSED 誠實標記
  ＋notification adapter 化（rg 檢查點）

oracle＝I 級（impl 衍生——狀態契約單一源即 scripts/at_ticket.py；
SKILL.md 錨點為 anti-regression 固化）。
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/at_ticket.py")

SKILL = REPO_ROOT / "skills" / "at" / "SKILL.md"

NOW = datetime(2026, 9, 22, 12, 0, 0, tzinfo=UTC)
RESUME_AT = datetime(2026, 9, 22, 12, 1, 0, tzinfo=UTC)
GRACE = 7 * 86400
MISSED_AFTER = 3600


def _new(state: str | None = None) -> dict:
    """建一張 SCHEDULED ticket；state 給定時做狀態手術（表驅動測試用）."""
    ticket = _mod.new_ticket(
        ticket_id="at-20260922-1201",
        goal="繼續 EP 段落 3",
        resume_at=RESUME_AT,
        scheduled_at=NOW,
        task_ref="AIR-157",
        owner_ref="ai-analysis/_tasks/x/ep.md#s3",
        project_path="/repo",
        now=NOW,
    )
    if state is not None:
        ticket["state"] = state
    return ticket


def _apply(ticket: dict, target: str, **kw: object) -> dict:
    return _mod.apply_transition(ticket, target, now=NOW + timedelta(minutes=1), **kw)


def _cli_create(tmp_path: Path) -> Path:
    """以 API 建 ticket 後走 CLI 面的測試起點."""
    d = tmp_path / "tickets"
    ticket = _mod.new_ticket(
        ticket_id="at-20260922-1201", goal="g", resume_at=RESUME_AT, now=NOW
    )
    path = d / "at-20260922-1201.json"
    _mod.write_ticket(path, ticket)
    return path


# ---------------------------------------------------------------------------
# AC#1：狀態機——五主態四異常＋合法轉移表
# ---------------------------------------------------------------------------


def test_state_sets_five_main_four_exception():
    assert _mod.MAIN_STATES == (
        "SCHEDULED",
        "ARMED",
        "FIRED",
        "RESTORE_PROVEN",
        "SETTLED",
    )
    assert _mod.EXCEPTION_STATES == (
        "SCHEDULER_REJECTED",
        "MISSED",
        "RESTORE_FAILED",
        "CANCELLED",
    )
    assert _mod.ALL_STATES == set(_mod.MAIN_STATES) | set(_mod.EXCEPTION_STATES)


def test_terminal_cleanable_states_are_settled_and_cancelled():
    assert _mod.CLEANABLE_STATES == {"SETTLED", "CANCELLED"}


def test_legal_transition_table_full_coverage():
    # 全表逐對驗證：每個合法 (from, to) 都能成功轉移並落 history row
    for src, targets in _mod.TRANSITIONS.items():
        for tgt in sorted(targets):
            ticket = _new(src)
            out = _apply(
                ticket,
                tgt,
                arm_receipt={"jobId": "j-1"},
                reason="CronCreate 被拒",
                note="n",
            )
            assert out["state"] == tgt, (src, tgt)
            row = out["history"][-1]
            assert row["from"] == src and row["to"] == tgt
            assert row["at"] == (NOW + timedelta(minutes=1)).isoformat(
                timespec="seconds"
            )


def test_illegal_transitions_raise_fail_loud():
    # 表外全組合（81 − 合法對數）一律 IllegalTransition——禁靜默亂跳
    for src in sorted(_mod.ALL_STATES):
        for tgt in sorted(_mod.ALL_STATES - _mod.TRANSITIONS[src]):
            ticket = _new(src)
            with pytest.raises(_mod.IllegalTransition):
                _apply(
                    ticket,
                    tgt,
                    arm_receipt={"jobId": "j"},
                    reason="r",
                    note="n",
                )


def test_unknown_target_state_raises():
    with pytest.raises(ValueError, match="未知狀態"):
        _apply(_new(), "WARPED")


def test_corrupt_current_state_is_ticketcorrupt_not_keyerror():
    # F6：轉移表外的 current state＝檔損壞面——顯式 TicketCorrupt 禁裸 KeyError
    with pytest.raises(_mod.TicketCorrupt, match="WARPED"):
        _apply(_new("WARPED"), "ARMED")


def test_exception_states_cannot_return_to_main_path():
    # 禁復活：異常態回主線（含自環）＝靜默降級的背面——全數非法
    for src in (
        "SCHEDULER_REJECTED",
        "MISSED",
        "RESTORE_FAILED",
        "CANCELLED",
    ):
        for tgt in (
            "SCHEDULED",
            "ARMED",
            "FIRED",
            "RESTORE_PROVEN",
            "SETTLED",
            src,
        ):
            ticket = _new(src)
            with pytest.raises(_mod.IllegalTransition):
                _apply(
                    ticket,
                    tgt,
                    arm_receipt={"jobId": "j"},
                    reason="r",
                    note="n",
                )


def test_new_ticket_starts_scheduled_with_created_history():
    ticket = _new()
    assert ticket["schema"] == "at-ticket/1"
    assert ticket["state"] == "SCHEDULED"
    assert ticket["history"] == [
        {
            "at": NOW.isoformat(timespec="seconds"),
            "from": None,
            "to": "SCHEDULED",
            "note": "created",
        }
    ]
    assert ticket["resumeAt"] == RESUME_AT.isoformat(timespec="seconds")
    assert ticket["taskRef"] == "AIR-157"


def test_new_ticket_naive_resume_at_rejected():
    with pytest.raises(ValueError, match="tz-aware"):
        _mod.new_ticket(
            ticket_id="t",
            goal="g",
            # naive datetime 故意禁——helper 須 ValueError fail-loud
            resume_at=datetime(2026, 9, 22, 12, 1),  # noqa: DTZ001
            now=NOW,
        )


def test_tickets_dir_convention_is_agent_tmp():
    assert _mod.TICKETS_DIRNAME == Path(".agent-tmp") / "at-tickets"


# ---------------------------------------------------------------------------
# ticket 檔：atomic 寫＋fail-loud 讀
# ---------------------------------------------------------------------------


def test_write_read_roundtrip_no_tmp_residue(tmp_path):
    path = tmp_path / ".agent-tmp" / "at-tickets" / "at-20260922-1201.json"
    ticket = _new()
    _mod.write_ticket(path, ticket)
    assert _mod.read_ticket(path) == ticket
    assert list(path.parent.glob("*.tmp")) == []


def test_write_is_whole_file_replace(tmp_path):
    # atomic replace：同路徑重寫＝整檔替換，禁半新半舊
    path = tmp_path / "t.json"
    _mod.write_ticket(path, _new("SETTLED"))
    _mod.write_ticket(path, _new("CANCELLED"))
    assert _mod.read_ticket(path)["state"] == "CANCELLED"


def test_write_failure_cleans_tmp_residue(tmp_path, monkeypatch):
    # F5：寫入異常路徑禁殘留 .tmp（暫存集中紀律——殘檔即垃圾）
    path = tmp_path / "t.json"

    def _boom(fd: int, view: memoryview) -> int:
        raise OSError("simulated write failure")

    monkeypatch.setattr(_mod.os, "write", _boom)
    with pytest.raises(OSError, match="simulated"):
        _mod.write_ticket(path, _new())
    assert list(tmp_path.glob("*.tmp")) == []
    assert not path.exists()


def test_read_missing_ticket_fail_loud(tmp_path):
    with pytest.raises(FileNotFoundError):
        _mod.read_ticket(tmp_path / "nope.json")


def test_read_corrupt_ticket_fail_loud(tmp_path):
    # 數據完整性優先：損壞比缺失危險——禁靜默當不存在
    path = tmp_path / "t.json"
    path.write_text("{oops not json")
    with pytest.raises(_mod.TicketCorrupt):
        _mod.read_ticket(path)


def test_read_schema_violation_fail_loud(tmp_path):
    path = tmp_path / "t.json"
    bad = _new()
    bad["state"] = "WARPED"
    path.write_text(json.dumps(bad, ensure_ascii=False))
    with pytest.raises(_mod.TicketCorrupt):
        _mod.read_ticket(path)


# ---------------------------------------------------------------------------
# AC#2：arm fail-loud——receipt 必留＋SCHEDULER_REJECTED 禁靜默降級
# ---------------------------------------------------------------------------


def test_arm_without_receipt_raises():
    with pytest.raises(ValueError, match="arm receipt"):
        _apply(_new("SCHEDULED"), "ARMED")


def test_arm_with_empty_receipt_raises():
    with pytest.raises(ValueError, match="arm receipt"):
        _apply(_new("SCHEDULED"), "ARMED", arm_receipt={})


def test_arm_with_receipt_records_armed(tmp_path):
    path = tmp_path / "t.json"
    ticket = _new()
    _mod.write_ticket(path, ticket)
    out = _apply(ticket, "ARMED", arm_receipt={"jobId": "cron-42"})
    assert out["state"] == "ARMED"
    assert out["history"][-1]["armReceipt"] == {"jobId": "cron-42"}


def test_reject_requires_reason():
    with pytest.raises(ValueError, match="reason"):
        _apply(_new("SCHEDULED"), "SCHEDULER_REJECTED")


def test_restore_failed_requires_reason():
    # F4：RESTORE_FAILED 證據強制與 SCHEDULER_REJECTED 對稱——診斷禁靜默
    with pytest.raises(ValueError, match="reason"):
        _apply(_new("FIRED"), "RESTORE_FAILED")


def test_restore_failed_records_reason_in_history():
    out = _apply(_new("FIRED"), "RESTORE_FAILED", reason="恢復失敗：實物核對不過")
    assert out["state"] == "RESTORE_FAILED"
    assert out["history"][-1]["reason"] == "恢復失敗：實物核對不過"


def test_missed_requires_note():
    with pytest.raises(ValueError, match="note"):
        _apply(_new("ARMED"), "MISSED")


def test_missed_records_unsupported_window_evidence():
    out = _apply(
        _new("ARMED"),
        "MISSED",
        note="unsupported window：host 關閉整夜無 covering trigger",
    )
    assert out["state"] == "MISSED"
    assert "unsupported window" in out["history"][-1]["note"]


def test_cli_new_roundtrip(tmp_path, capsys):
    d = tmp_path / ".agent-tmp" / "at-tickets"
    code = _mod.main(
        [
            "new",
            "--dir",
            str(d),
            "--goal",
            "繼續 EP 段落 3",
            "--resume-at",
            "2026-09-22T12:01:00+00:00",
            "--task-ref",
            "AIR-157",
            "--owner-ref",
            "ep.md#s3",
            "--project-path",
            "/repo",
        ]
    )
    assert code == 0
    row = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert row["state"] == "SCHEDULED"
    path = Path(row["path"])
    assert path.is_file()
    assert _mod.read_ticket(path)["taskRef"] == "AIR-157"


def test_cli_new_duplicate_ticket_id_fail_loud(tmp_path, capsys):
    d = tmp_path / "t"
    argv = [
        "new",
        "--dir",
        str(d),
        "--goal",
        "g",
        "--resume-at",
        "2026-09-22T12:01:00+00:00",
    ]
    assert _mod.main(argv) == 0
    capsys.readouterr()
    assert _mod.main(argv) == 1  # 同 id 重建＝禁靜默覆蓋


def test_cli_transition_armed_requires_receipt(tmp_path, capsys):
    path = _cli_create(tmp_path)
    code = _mod.main(["transition", "--ticket", str(path), "--to", "ARMED"])
    assert code == 1
    assert "arm receipt" in capsys.readouterr().err


def test_cli_reject_fail_loud_exit1_stderr_diagnosis(tmp_path, capsys):
    # 記錄落地但事件＝fail-loud：exit 1＋stderr 診斷（禁靜默降級措辭在場）
    path = _cli_create(tmp_path)
    code = _mod.main(["reject", "--ticket", str(path), "--reason", "CronCreate 被拒"])
    captured = capsys.readouterr()
    assert code == 1
    assert "SCHEDULER_REJECTED" in captured.err
    assert "禁靜默降級" in captured.err
    assert "背景 sleep" in captured.err
    assert _mod.read_ticket(path)["state"] == "SCHEDULER_REJECTED"


def test_cli_transition_illegal_exit1_state_untouched(tmp_path, capsys):
    path = _cli_create(tmp_path)
    code = _mod.main(["transition", "--ticket", str(path), "--to", "FIRED"])
    assert code == 1
    assert "非法轉移" in capsys.readouterr().err
    assert _mod.read_ticket(path)["state"] == "SCHEDULED"


def test_cli_rejected_cannot_rearm(tmp_path, capsys):
    # 禁降級回頭：rejected 之後帶著 receipt 也不准 ARMED
    path = _cli_create(tmp_path)
    _mod.main(["reject", "--ticket", str(path), "--reason", "x"])
    capsys.readouterr()
    code = _mod.main(
        [
            "transition",
            "--ticket",
            str(path),
            "--to",
            "ARMED",
            "--arm-receipt-json",
            '{"jobId": "j"}',
        ]
    )
    assert code == 1
    assert _mod.read_ticket(path)["state"] == "SCHEDULER_REJECTED"


def test_cli_transition_to_missed_with_note(tmp_path, capsys):
    path = _cli_create(tmp_path)
    _mod.main(
        [
            "transition",
            "--ticket",
            str(path),
            "--to",
            "ARMED",
            "--arm-receipt-json",
            '{"jobId": "j"}',
        ]
    )
    capsys.readouterr()
    code = _mod.main(
        [
            "transition",
            "--ticket",
            str(path),
            "--to",
            "MISSED",
            "--note",
            "unsupported window：CronList 顯示未觸發",
        ]
    )
    assert code == 0
    assert _mod.read_ticket(path)["state"] == "MISSED"


# ---------------------------------------------------------------------------
# AC#3：cleanup 依 resume_at＋state＋grace——mtime 淘汰
# ---------------------------------------------------------------------------


def test_terminal_past_grace_cleanable():
    late = RESUME_AT + timedelta(seconds=GRACE)
    assert _mod.cleanable(_new("SETTLED"), now=late, grace_s=GRACE)
    assert _mod.cleanable(_new("CANCELLED"), now=late, grace_s=GRACE)


def test_terminal_within_grace_not_cleanable():
    within = RESUME_AT + timedelta(days=1)
    assert not _mod.cleanable(_new("SETTLED"), now=within, grace_s=GRACE)
    assert not _mod.cleanable(_new("CANCELLED"), now=within, grace_s=GRACE)


def test_non_terminal_never_cleanable_regardless_of_age():
    # 舊 mtime 邏輯誤刪防護：非 terminal 票齡再舊也禁清
    late = RESUME_AT + timedelta(days=30)
    for state in (
        "SCHEDULED",
        "ARMED",
        "FIRED",
        "RESTORE_PROVEN",
        "SCHEDULER_REJECTED",
        "MISSED",
        "RESTORE_FAILED",
    ):
        ticket = _new(state)
        ticket["resumeAt"] = (RESUME_AT + timedelta(days=8)).isoformat()
        assert not _mod.cleanable(ticket, now=late, grace_s=GRACE), state


def test_mtime_irrelevant_to_cleanup(tmp_path):
    # 直接打擊舊邏輯：mtime 撥回 2000 年，未到期 SCHEDULED ticket 仍不可清
    path = tmp_path / "t.json"
    ticket = _new("SCHEDULED")
    ticket["resumeAt"] = (RESUME_AT + timedelta(days=8)).isoformat()
    _mod.write_ticket(path, ticket)
    os.utime(path, (946684800, 946684800))  # 2000-01-01
    loaded = _mod.read_ticket(path)
    assert not _mod.cleanable(loaded, now=RESUME_AT + timedelta(days=30), grace_s=GRACE)


def test_classify_buckets(tmp_path):
    d = tmp_path / "tickets"

    def put(tid: str, state: str, resume_at: datetime) -> None:
        ticket = _new(state)
        ticket["ticketId"] = tid
        ticket["resumeAt"] = resume_at.isoformat(timespec="seconds")
        _mod.write_ticket(d / f"{tid}.json", ticket)

    put("a-settled", "SETTLED", NOW - timedelta(days=8))  # grace 已過
    put("b-armed", "ARMED", NOW - timedelta(days=2))  # 過期未 fire
    put("c-sched", "SCHEDULED", NOW - timedelta(days=2))  # 排程已過未 arm
    put("d-future", "SCHEDULED", NOW + timedelta(days=1))  # 未到期
    put("e-settled-fresh", "SETTLED", NOW + timedelta(days=1))  # terminal 未滿 grace
    rows = {
        r["ticketId"]: r
        for r in _mod.sweep_dir(
            d,
            now=NOW + timedelta(days=1),
            grace_s=GRACE,
            missed_after_s=MISSED_AFTER,
        )
    }
    assert rows["a-settled"]["bucket"] == "cleanable"
    assert rows["b-armed"]["bucket"] == "missed-candidate"
    assert rows["c-sched"]["bucket"] == "past-due"
    assert rows["d-future"]["bucket"] == "hold"
    assert rows["e-settled-fresh"]["bucket"] == "hold"


def test_armed_just_past_due_is_hold_until_missed_tolerance():
    # 過期未滿 missed tolerance（時鐘誤差窗）＝仍在 hold，不急標 MISSED
    just_past = RESUME_AT + timedelta(minutes=5)
    assert just_past >= RESUME_AT  # sanity
    ticket = _new("ARMED")
    row = _mod.classify(
        ticket, now=RESUME_AT + timedelta(minutes=5), missed_after_s=MISSED_AFTER
    )
    assert row["bucket"] == "hold"


def test_sweep_empty_dir_returns_empty(tmp_path):
    assert _mod.sweep_dir(tmp_path / "absent", now=NOW, grace_s=GRACE) == []


def test_sweep_corrupt_ticket_fail_loud(tmp_path):
    # sweep 對損壞票 fail-loud——禁靜默跳過（數據完整性優先）
    d = tmp_path / "tickets"
    d.mkdir()
    (d / "broken.json").write_text("{half")
    with pytest.raises(_mod.TicketCorrupt):
        _mod.sweep_dir(d, now=NOW, grace_s=GRACE)


def test_sweep_ignores_non_json_files(tmp_path):
    d = tmp_path / "tickets"
    d.mkdir()
    (d / "notes.txt").write_text("stray")
    assert _mod.sweep_dir(d, now=NOW, grace_s=GRACE) == []


def test_cli_classify_outputs_rows(tmp_path, capsys):
    _cli_create(tmp_path)
    _cli_create(tmp_path / "_")  # 鄰目錄不干擾
    d = tmp_path / "tickets"
    code = _mod.main(["classify", "--dir", str(d)])
    assert code == 0
    rows = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert isinstance(rows, list) and len(rows) == 1
    assert rows[0]["bucket"] == "hold"


# ---------------------------------------------------------------------------
# AC#4：skills/at/SKILL.md 改版 rg 檢查點（anti-regression 錨點）
# ---------------------------------------------------------------------------


def _skill_text() -> str:
    return SKILL.read_text()


def test_skill_documents_full_state_machine():
    text = _skill_text()
    for state in (*_mod.MAIN_STATES, *_mod.EXCEPTION_STATES):
        assert state in text, f"SKILL.md 缺狀態機狀態 {state}"
    assert "scripts/at_ticket.py" in text  # helper 工具指涉
    assert ".agent-tmp/at-tickets/" in text  # ticket 路徑慣例


def test_skill_no_silent_degradation_clause():
    text = _skill_text()
    assert "禁靜默降級" in text
    assert "背景 sleep" in text  # 禁退背景 sleep 替代
    assert "SCHEDULER_REJECTED" in text
    assert "arm receipt" in text  # arm 成功必有回執


def test_skill_missed_honest_marker():
    text = _skill_text()
    assert "MISSED" in text
    assert "unsupported window" in text  # 誠實標 unsupported window
    assert "at-ticket MISSED" in text  # badge 語義
    assert "zcode scheduled task" in text  # POC 為後續卡指涉


def test_skill_cleanup_by_resume_at_state_grace():
    text = _skill_text()
    assert "resume_at＋state＋grace" in text
    assert "SETTLED 或 CANCELLED 才可清" in text
    # 舊 mtime 邏輯淘汰——舊句不得殘留
    assert "mtime>7" not in text
    assert "夜間清淤" not in text


def test_skill_notification_adapter_optional_say():
    text = _skill_text()
    assert "say -v Meijia" in text  # 樣板保留
    assert "可選" in text  # say 降可選（headless 必敗——adapter 化）
