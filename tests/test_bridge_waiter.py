"""bridge_waiter 契約測試（AIR-146——fan-in wait watcher，synthetic 層）.

AC 對應（oracle 分級：狀態機轉移表＝S 級 frozen spec 住 module docstring；
本檔＝I 級 impl 衍生機驗；AC#1 的 H 級真實歷史 job replay 由主 session
L4 複驗，本檔不冒充）：

- AC#1 → test_ac1_*
- AC#2 → test_ac2_* ＋ test_compute_t0_* / test_next_arm_timeout_* /
  test_crossed_floor_*
- AC#3 → test_ac3_*
- AC#4 → test_ac4_*
- AC#5 → test_ac5_*
- AC#6 → test_ac6_* ＋ test_compare_semver / test_version_from_path /
  test_e2e_version_pin_fail_loud

測試全程用假 bridge（FakeBridge / tests/fixtures/fake_bridge.py），
不打真 bridge。
"""

import ast
import io
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/bridge_waiter.py")

BridgeClient = _mod.BridgeClient
SCRIPT = REPO_ROOT / "scripts" / "bridge_waiter.py"
STUB = REPO_ROOT / "tests" / "fixtures" / "fake_bridge.py"

NOW = datetime(2026, 9, 20, 1, 10, tzinfo=UTC)
TS5M = "2026-09-20T01:05:00.000Z"  # NOW 前 5 分鐘
NOW_ISO_NEAR = "2026-09-20T01:09:30.000Z"
MID_TS = "2026-09-20T01:02:00.000Z"  # NOW 前 8 分鐘
OLD_TS = "2026-09-20T00:55:00.000Z"  # NOW 前 15 分鐘


def show_payload(
    job: str = "job-a",
    status: str = "running",
    hb: str | None = None,
    ev: str | None = None,
    sid: str = "s1",
    ts: str = "2026-09-20T01:09:00.000Z",
    family: str = "codex",
    final_text: str = "",
) -> dict:
    extra: dict = {}
    if hb is not None:
        extra["heartbeatAt"] = hb
    if ev is not None:
        extra["lastEventAt"] = ev
    return {
        "job": {
            "id": job,
            "status": status,
            "family": family,
            "sessionId": sid,
            "timestamp": ts,
            "extra": extra,
        },
        "finalText": final_text,
    }


def completed_payload(job: str = "job-a", final_text: str = "done") -> dict:
    return show_payload(job=job, status="completed", final_text=final_text)


class FakeBridge:
    """假 bridge CLI——version/wait/show 三面，依 script 供給回應。"""

    def __init__(
        self,
        waits: list[dict] | None = None,
        shows: dict[str, object] | None = None,
        version: str | None = "2.0.22",
        bin_path: str = "/fake/delegate/2.0.22/bin/delegate-bridge",
    ) -> None:
        self.bin_path = bin_path
        self._version = version
        self._waits = list(waits or [])
        self._shows = dict(shows or {})
        self.wait_calls: list[dict] = []
        self.show_calls: list[str] = []

    def version(self) -> str | None:
        return self._version

    def wait(
        self, job_ids: list[str], timeout_ms: int, stuck_after_ms: int
    ) -> tuple[int, str, str]:
        self.wait_calls.append(
            {
                "ids": list(job_ids),
                "timeout_ms": timeout_ms,
                "stuck_after_ms": stuck_after_ms,
            }
        )
        step = self._waits.pop(0) if self._waits else {"exit": 0}
        return (
            int(step["exit"]),
            str(step.get("stdout", "")),
            str(step.get("stderr", "")),
        )

    def show(self, job_id: str) -> dict:
        self.show_calls.append(job_id)
        entry = self._shows[job_id]
        if isinstance(entry, list):
            if not entry:
                raise AssertionError(f"show 序列耗盡：{job_id}")
            entry = entry.pop(0)
        if isinstance(entry, dict) and "raise_kind" in entry:
            raise _mod.BridgeError(
                str(entry["raise_kind"]), str(entry.get("message", ""))
            )
        return entry  # type: ignore[return-value]


def run(
    fake: FakeBridge, job_ids: list[str], now: object = None, **kw: object
) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        fake,
        job_ids,
        now=now if now is not None else (lambda: NOW),
        stdout=out,
        stderr=err,
        **kw,
    )
    return code, out.getvalue(), err.getvalue()


def last_state_json(stdout: str) -> dict:
    return json.loads(stdout.strip().splitlines()[-1])


def receipt_rows(stdout: str) -> list[dict]:
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    receipts = [json.loads(ln) for ln in lines if '"schema"' in ln]
    assert len(receipts) == 1, f"CollectionReceipt 恰一份，得 {len(receipts)}"
    assert json.loads(lines[-1])["schema"] == _mod.RECEIPT_SCHEMA, (
        "receipt 必須是 stdout 尾行"
    )
    return receipts[0]["jobs"]


# ---------------------------------------------------------------------------
# 單元：動態 T（AC#2 的公式面）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("family", "kind", "expected"),
    [
        ("codex", "discussion", 5.0),
        ("glm", "implementation", 15.0),
        ("glm", "research", 15.0),  # 90/3=30 → clamp 15
        ("muse", "unspecified", 10.0),
        ("alien", "whatever", 10.0),
    ],
)
def test_compute_t0_clamps_prior_third(family: str, kind: str, expected: float) -> None:
    assert _mod.compute_t0(family, kind) == expected


def test_next_arm_timeout_grow_cap_shrink_floor() -> None:
    assert _mod.next_arm_timeout(5.0, True, 9.0) == pytest.approx(7.5)
    assert _mod.next_arm_timeout(15.0, True, 9.0) == pytest.approx(20.0)  # cap
    assert _mod.next_arm_timeout(11.25, False, 2.0) == pytest.approx(1.0)  # floor
    assert _mod.next_arm_timeout(8.0, False, 6.0) == pytest.approx(3.0)
    assert _mod.next_arm_timeout(8.0, False, None) == pytest.approx(1.0)


def test_crossed_floor_none_not_staleness_nan_blocked() -> None:
    # 0921 對齊 bridge producer canonical（task.rs：no ageable data is never reported）
    assert _mod.crossed_floor(5.0, 5.0) is False  # 恰在 floor 未跨
    assert _mod.crossed_floor(5.1, 5.0) is True
    assert _mod.crossed_floor(None, 5.0) is False  # 無可計齊 stamp ≠ staleness——不報 stalled
    assert _mod.crossed_floor(float("nan"), 5.0) is True  # IEEE 754 fail-open 防護


def test_parse_iso_ts() -> None:
    assert _mod.parse_iso_ts("2026-09-20T01:00:00.000Z") is not None
    assert _mod.parse_iso_ts("2026-09-20T01:00:00+00:00") is not None
    assert _mod.parse_iso_ts("2026-09-20T01:00:00") is None  # naive → fail-closed（F4）
    assert _mod.parse_iso_ts("garbage") is None
    assert _mod.parse_iso_ts(None) is None
    assert _mod.parse_iso_ts(123) is None


def test_compare_semver_and_path_fallback() -> None:
    assert _mod.compare_semver("2.0.22", "2.0.19") > 0
    assert _mod.compare_semver("2.0.22", "2.0.22") == 0
    assert _mod.version_from_path("/x/delegate/2.0.9/bin/delegate-bridge") == "2.0.9"
    assert _mod.version_from_path("/opt/bin/delegate-bridge") is None


# ---------------------------------------------------------------------------
# AC#1 124 → 內部 re-arm、零 redispatch
# ---------------------------------------------------------------------------


def test_ac1_124_rearms_internally_never_leaks() -> None:
    fake = FakeBridge(
        waits=[{"exit": 124}, {"exit": 0}],
        shows={
            "job-a": [
                show_payload(hb=TS5M, ev=TS5M, ts=TS5M),
                show_payload(hb="2026-09-20T01:06:00.000Z", ev=TS5M, ts=TS5M),
                completed_payload(),
            ]
        },
    )
    code, _, _ = run(fake, ["job-a"], kind="discussion")
    assert code == 0, "124 不得外洩——最終 exit 由 terminal 面決定"
    assert len(fake.wait_calls) == 2, "124 後必須內部 re-arm 一次"
    assert fake.wait_calls[0]["timeout_ms"] == 300000
    assert fake.wait_calls[1]["timeout_ms"] == 450000


def test_ac1_zero_redispatch_ids_subset_and_no_dispatch_surface() -> None:
    fake = FakeBridge(
        waits=[{"exit": 124}, {"exit": 0}],
        shows={
            "job-a": [
                show_payload(hb=TS5M, ev=TS5M, ts=TS5M),
                show_payload(hb="2026-09-20T01:06:00.000Z", ev=TS5M, ts=TS5M),
                completed_payload(),
            ]
        },
    )
    code, _, _ = run(fake, ["job-a"], kind="discussion")
    assert code == 0
    for call in fake.wait_calls:
        assert set(call["ids"]) <= {"job-a"}, "wait id 集不得超出原 fan-in 集"
    assert not any(hasattr(fake, name) for name in ("dispatch", "task", "stop")), (
        "watcher 依賴面不得有 dispatch/task/stop 面"
    )


# ---------------------------------------------------------------------------
# AC#2 動態 T＋silence 跨 floor 僅 advisory
# ---------------------------------------------------------------------------


def test_ac2_fresh_progress_grows_next_arm() -> None:
    fake = FakeBridge(
        waits=[{"exit": 124}, {"exit": 124}, {"exit": 124}, {"exit": 0}],
        shows={
            "job-a": [
                show_payload(hb=TS5M, ev=None, ts=TS5M),
                show_payload(hb="2026-09-20T01:06:00.000Z", ev=None, ts=TS5M),
                show_payload(hb="2026-09-20T01:07:00.000Z", ev=None, ts=TS5M),
                show_payload(hb="2026-09-20T01:07:00.000Z", ev=None, ts=TS5M),
                completed_payload(),
            ]
        },
    )
    code, _, _ = run(fake, ["job-a"], kind="discussion")
    assert code == 0
    timeouts = [c["timeout_ms"] for c in fake.wait_calls]
    assert timeouts == [300000, 450000, 675000, 150000], timeouts
    stuck = {c["stuck_after_ms"] for c in fake.wait_calls}
    assert stuck == {600000}, "stuck-after 鏡射 runtime floor（codex/glm 10m）"


def test_ac2_runtime_silence_cross_floor_exits_3_advisory_only() -> None:
    fake = FakeBridge(
        shows={"job-a": show_payload(hb=NOW_ISO_NEAR, ev=None, ts=OLD_TS)},
    )
    code, out, err = run(fake, ["job-a"])
    assert code == 3
    assert fake.wait_calls == [], "跨 floor 時不得再 arm"
    marker = last_state_json(out)
    assert marker["state"] == "stalled-advisory"
    assert "不處置" in err


def test_ac2_worker_axis_cross_floor_also_advisory() -> None:
    # worker 軸 stale（15m）、runtime 軸 fresh（0.5m）——D1-01 兩軸獨立，worker 跨線即 advisory
    fake = FakeBridge(
        shows={
            "job-a": show_payload(hb=OLD_TS, ev=NOW_ISO_NEAR, ts=OLD_TS),
        },
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 3
    assert last_state_json(out)["state"] == "stalled-advisory"


def test_ac2_refresh_round_runtime_cross_floor_exits_3() -> None:
    times = iter([NOW, NOW + timedelta(minutes=3)])
    fake = FakeBridge(
        waits=[{"exit": 124}],
        shows={
            "job-a": [
                # 初始：runtime 8m ≤ 10、worker 0.5m——兩軸未跨
                show_payload(hb=NOW_ISO_NEAR, ev=MID_TS, ts=MID_TS),
                # now+3m：runtime 11m 跨線、worker 3.5m 未跨——runtime 軸觸發
                show_payload(hb=NOW_ISO_NEAR, ev=MID_TS, ts=MID_TS),
            ]
        },
    )
    code, out, _ = run(fake, ["job-a"], now=lambda: next(times))
    assert code == 3
    assert len(fake.wait_calls) == 1
    assert last_state_json(out)["state"] == "stalled-advisory"


# ---------------------------------------------------------------------------
# AC#3 恰一次 collect、failure 立即喚醒、receipt 於 stdout
# ---------------------------------------------------------------------------


def test_ac3_terminal_completed_collects_exactly_once_exit_0() -> None:
    fake = FakeBridge(
        waits=[{"exit": 0}],
        shows={
            "job-a": completed_payload("job-a", "done a"),
            "job-b": completed_payload("job-b", "done b"),
        },
    )
    code, out, _ = run(fake, ["job-a", "job-b"])
    assert code == 0
    assert fake.show_calls.count("job-a") == 2, "初始快照＋恰一次 collect"
    assert fake.show_calls.count("job-b") == 2
    rows = receipt_rows(out)
    assert [r["jobId"] for r in rows] == ["job-a", "job-b"]
    assert all(r["status"] == "completed" for r in rows)


def test_ac3_receipt_json_is_stdout_tail() -> None:
    fake = FakeBridge(
        waits=[{"exit": 0}],
        shows={"job-a": completed_payload("job-a", "done")},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 0
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["schema"] == _mod.RECEIPT_SCHEMA
    assert receipt["exitState"] == "completed"
    assert receipt["bridgeCliVersion"] == "2.0.22"


def test_ac3_terminal_failure_wakes_immediately_exit_1() -> None:
    fake = FakeBridge(
        waits=[{"exit": 1}],
        shows={
            "job-a": [
                show_payload(),  # running 進 wait
                show_payload(status="failed-usage", final_text=""),  # wait 期間失敗
            ]
        },
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 1
    assert len(fake.wait_calls) == 1, "terminal failure 立即喚醒，不再 re-arm"
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["exitState"] == "terminal-non-completed"
    assert receipt["jobs"][0]["status"] == "failed-usage"


def test_ac3_sink_gate_fail_flips_to_non_completed(tmp_path: Path) -> None:
    missing = str(tmp_path / "absent.md")
    fake = FakeBridge(
        waits=[{"exit": 0}],
        shows={"job-a": completed_payload("job-a", "done")},
    )
    code, out, _ = run(fake, ["job-a"], sinks={"job-a": missing})
    assert code == 1, "completed 但 sink 缺＝terminal-sink-missing 面，非 completed"
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["exitState"] == "terminal-non-completed"
    assert receipt["jobs"][0]["delivery"]["verdict"] == "undelivered"
    assert receipt["jobs"][0]["delivery"]["l1_present"] is False


def test_ac3_sink_three_steps_and_receipt_only(tmp_path: Path) -> None:
    sink = tmp_path / "out.md"
    sink.write_text("body\nRECEIPT-ANCHOR-146\n", encoding="utf-8")
    empty = tmp_path / "empty.md"
    empty.write_text("", encoding="utf-8")

    assert (
        _mod.check_delivery(str(sink), ["RECEIPT-ANCHOR-146"], None)["verdict"]
        == "delivered"
    )
    miss = _mod.check_delivery(str(sink), ["NO-SUCH-ANCHOR"], None)
    assert miss["verdict"] == "undelivered" and miss["l2_anchor"] is False
    manual = _mod.check_delivery(str(sink), [], None)
    assert manual["verdict"] == "manual-anchor" and manual["l2_anchor"] is None
    ro_ok = _mod.check_delivery(None, [], "report body")
    assert ro_ok["verdict"] == "delivered"
    ro_empty = _mod.check_delivery(None, [], "  \n\t")
    assert ro_empty["verdict"] == "undelivered"


def test_check_delivery_anchor_in_large_file_tail(tmp_path: Path) -> None:
    """F3：錨點在 250k 檔尾也須命中（全 content 搜尋——N1 修後無窗口）。"""
    sink = tmp_path / "big.md"
    sink.write_text("x" * 250_000 + "\nTAIL-ANCHOR-146\n", encoding="utf-8")
    result = _mod.check_delivery(str(sink), ["TAIL-ANCHOR-146"], None)
    assert result["verdict"] == "delivered"
    assert result["anchor_hits"] == ["TAIL-ANCHOR-146"]


def test_check_delivery_anchor_in_middle_gap_region(tmp_path: Path) -> None:
    """N1：token@120k-of-250k（舊雙窗會漏的 gap 帶）→ delivered。"""
    sink = tmp_path / "gap.md"
    body = "x" * 120_000 + "\nMID-ANCHOR-146\n" + "y" * 129_000
    sink.write_text(body, encoding="utf-8")
    result = _mod.check_delivery(str(sink), ["MID-ANCHOR-146"], None)
    assert result["verdict"] == "delivered"
    assert result["anchor_hits"] == ["MID-ANCHOR-146"]


def test_ac2_advisory_human_line_rounded() -> None:
    """F7：advisory 人讀行的 silence 分鐘須 round(x, 1)。"""
    stamp = "2026-09-20T00:54:59.000Z"  # NOW−15m1s → 15.0166…m
    fake = FakeBridge(shows={"job-a": show_payload(hb=stamp, ev=stamp, ts=stamp)})
    code, out, _ = run(fake, ["job-a"])
    assert code == 3
    assert "worker=15.0m" in out
    assert "15.01666" not in out


def test_ac3_completed_with_manual_anchor_exits_0(tmp_path: Path) -> None:
    sink = tmp_path / "out.md"
    sink.write_text("content", encoding="utf-8")
    fake = FakeBridge(
        waits=[{"exit": 0}],
        shows={"job-a": completed_payload("job-a", "done")},
    )
    code, out, _ = run(fake, ["job-a"], sinks={"job-a": str(sink)})
    assert code == 0, "錨點未具名＝人工判定面，不擋 exit；receipt 標 manual-anchor"
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["jobs"][0]["delivery"]["verdict"] == "manual-anchor"
    assert receipt["summary"]["manualAnchor"] == 1


# ---------------------------------------------------------------------------
# AC#4 N-job fan-in 至最後一顆 terminal 才 completion
# ---------------------------------------------------------------------------


def test_ac4_fan_in_completes_only_after_last_terminal() -> None:
    fake = FakeBridge(
        waits=[{"exit": 124}, {"exit": 0}],
        shows={
            "job-a": [
                show_payload(job="job-a", hb=TS5M, ev=TS5M, ts=TS5M),
                completed_payload("job-a", "done a"),
                completed_payload("job-a", "done a"),
            ],
            "job-b": [
                show_payload(job="job-b", hb=TS5M, ev=TS5M, ts=TS5M),
                show_payload(
                    job="job-b", hb="2026-09-20T01:06:00.000Z", ev=TS5M, ts=TS5M
                ),
                completed_payload("job-b", "done b"),
            ],
            "job-c": [
                show_payload(job="job-c", hb=TS5M, ev=TS5M, ts=TS5M),
                show_payload(
                    job="job-c", hb="2026-09-20T01:06:00.000Z", ev=TS5M, ts=TS5M
                ),
                completed_payload("job-c", "done c"),
            ],
        },
    )
    code, out, _ = run(fake, ["job-a", "job-b", "job-c"], kind="discussion")
    assert code == 0
    assert fake.wait_calls[0]["ids"] == ["job-a", "job-b", "job-c"]
    assert fake.wait_calls[1]["ids"] == ["job-b", "job-c"], (
        "已 terminal 者退出 re-arm 集"
    )
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["summary"]["total"] == 3
    assert receipt["summary"]["completed"] == 3


# ---------------------------------------------------------------------------
# AC#5 generation mismatch → reconcile 禁 retry；missing/corrupt fail-loud
# ---------------------------------------------------------------------------


def test_ac5_generation_mismatch_reconcile_no_retry() -> None:
    fake = FakeBridge(
        waits=[{"exit": 124}],
        shows={
            "job-a": [
                show_payload(sid="s1"),
                show_payload(sid="s2"),  # running row 身分變＝ledger 重生
            ]
        },
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    marker = last_state_json(out)
    assert marker["state"] == "unknown/reconcile"
    assert len(fake.wait_calls) == 1, "reconcile 喚醒後禁 retry"


def test_ac5_job_not_found_reconcile() -> None:
    fake = FakeBridge(
        shows={
            "job-a": {
                "raise_kind": "not-found",
                "message": "Job not found: job-a",
            }
        },
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "unknown/reconcile"
    assert fake.wait_calls == []


def test_ac5_missing_or_corrupt_status_fail_loud() -> None:
    payload = show_payload()
    del payload["job"]["status"]
    fake = FakeBridge(shows={"job-a": payload})
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "error"
    assert fake.wait_calls == []


def test_ac5_wait_disappeared_is_reconcile() -> None:
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "Job disappeared mid-wait: job-a", "stdout": ""}],
        shows={"job-a": show_payload()},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "unknown/reconcile"


def test_wait_usage_passthrough_exit_2() -> None:
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "Usage: delegate-bridge wait ...", "stdout": ""}],
        shows={"job-a": show_payload()},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert "unknown/reconcile" not in out, "usage 透傳不得冒充 reconcile"


def test_wait_unexpected_exit_fail_loud() -> None:
    fake = FakeBridge(waits=[{"exit": 7}], shows={"job-a": show_payload()})
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "error"


def test_ac3_single_id_usage_error_terminal_lands_in_collect() -> None:
    """F1 回歸：single-id wait 對 terminal usage-error（wait_exit_for_status
    Some(2)、stderr 空、輸出走 stdout）回 exit 2——不得透傳，須 show 重探落
    collect 相。"""
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "", "stdout": ""}],
        shows={
            "job-a": [
                show_payload(),  # running 進 wait
                show_payload(status="usage-error"),  # 重探：已 terminal
                show_payload(status="usage-error"),  # collect 相
            ]
        },
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 1, "terminal 非 completed → exit 1，receipt 必在"
    assert len(fake.wait_calls) == 1
    receipt = json.loads(out.strip().splitlines()[-1])
    assert receipt["schema"] == _mod.RECEIPT_SCHEMA
    assert receipt["jobs"][0]["status"] == "usage-error"
    assert receipt["exitState"] == "terminal-non-completed"


def test_ac5_wait_entry_not_found_is_reconcile() -> None:
    """F2 回歸：wait 入口 die(2)「Job not found」（rust 正典字串）＝T7
    reconcile，非 usage 透傳。"""
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "Job not found: job-a", "stdout": ""}],
        shows={"job-a": show_payload()},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    marker = last_state_json(out)
    assert marker["state"] == "unknown/reconcile"


def test_ac5_wait_exit2_reprobe_not_found_is_reconcile() -> None:
    """F1 重探腿：exit 2 無正典字串、show 重探 not-found → reconcile。"""
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "", "stdout": ""}],
        shows={"job-a": {"raise_kind": "not-found", "message": "Job not found: job-a"}},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "unknown/reconcile"


def test_wait_exit2_still_running_is_usage_passthrough() -> None:
    """F1 反例腿：重探仍有 running（真 usage 面，如壞旗標）→ 透傳 exit 2。"""
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "error: unexpected argument '--bogus'"}],
        shows={"job-a": show_payload()},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert "unknown/reconcile" not in out


def test_ac5_wait_canonical_string_case_insensitive() -> None:
    """N3：wait 正典字串比對 case-insensitive（與 show 分類器 .lower() 對稱）。"""
    fake = FakeBridge(
        waits=[{"exit": 2, "stderr": "JOB NOT FOUND: job-a", "stdout": ""}],
        shows={"job-a": show_payload()},
    )
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert last_state_json(out)["state"] == "unknown/reconcile"


# ---------------------------------------------------------------------------
# AC#6 無 stop/judge/commit 路徑；版本 pin fail-loud
# ---------------------------------------------------------------------------


def test_ac6_no_stop_judge_commit_code_path() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                called.add(func.attr)
            elif isinstance(func, ast.Name):
                called.add(func.id)
    assert called.isdisjoint({"stop", "judge", "commit"}), sorted(
        called & {"stop", "judge", "commit"}
    )
    public = {
        name
        for name in dir(BridgeClient)
        if not name.startswith("_") and callable(getattr(BridgeClient, name))
    }
    assert public <= {"version", "wait", "show"}, public


def test_ac6_version_pin_fail_loud_with_upgrade_guidance() -> None:
    fake = FakeBridge(version="2.0.19")
    code, out, err = run(fake, ["job-a"])
    assert code == 2
    marker = last_state_json(out)
    assert marker["state"] == "error"
    assert "2.0.22" in marker["reason"]
    assert "升級" in marker["reason"] or "升級" in err
    assert fake.wait_calls == []


def test_ac6_version_pin_path_segment_fallback() -> None:
    fake = FakeBridge(
        version=None,
        bin_path="/x/delegate/2.0.22/bin/delegate-bridge",
        waits=[{"exit": 0}],
        shows={"job-a": completed_payload()},
    )
    code, _, _ = run(fake, ["job-a"])
    assert code == 0, "--version 不支援時以 registry pin 路徑段判定"


def test_ac6_version_undeterminable_fail_loud() -> None:
    fake = FakeBridge(version=None, bin_path="/opt/bin/delegate-bridge")
    code, out, _ = run(fake, ["job-a"])
    assert code == 2
    assert "無法判定" in last_state_json(out)["reason"]


def test_usage_duplicate_or_unknown_sink_ids() -> None:
    with pytest.raises(_mod.UsageError):
        run(FakeBridge(shows={}), ["job-a", "job-a"])
    with pytest.raises(_mod.UsageError):
        run(FakeBridge(shows={}), ["job-a"], sinks={"job-z": "/x"})


# ---------------------------------------------------------------------------
# E2E：subprocess 打 tests/fixtures/fake_bridge.py（仍不打真 bridge）
# ---------------------------------------------------------------------------


def _e2e_env(tmp_path: Path, scenario: dict) -> dict[str, str]:
    STUB.chmod(0o755)  # subprocess 直接 exec——需執行位
    scenario_path = tmp_path / "scenario.json"
    state_path = tmp_path / "state.json"
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    env = dict(os.environ)
    env["FAKE_BRIDGE_SCENARIO"] = str(scenario_path)
    env["FAKE_BRIDGE_STATE"] = str(state_path)
    return env


def _iso_in_past(seconds: float) -> str:
    dt = datetime.now().astimezone() - timedelta(seconds=seconds)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def test_e2e_subprocess_happy_path_with_rearm(tmp_path: Path) -> None:
    sink = tmp_path / "sink.md"
    sink.write_text("report\nRECEIPT-ANCHOR-146\n", encoding="utf-8")
    # identity 欄（ts）各快照必須逐字相同——分次呼叫 _iso_in_past 會差毫秒、誤觸 T7
    ts_old = _iso_in_past(30)
    hb_new = _iso_in_past(10)
    scenario = {
        "version": "2.0.22",
        "waits": [
            {"exit": 124, "stdout": "job-a running\n", "stderr": ""},
            {"exit": 0, "stdout": "job-a completed\n", "stderr": ""},
        ],
        "shows": {
            "job-a": [
                show_payload(hb=ts_old, ev=ts_old, ts=ts_old),
                show_payload(hb=hb_new, ev=hb_new, ts=ts_old),
                completed_payload("job-a", "final report"),
            ]
        },
    }
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "job-a",
            "--bridge-bin",
            str(STUB),
            "--kind",
            "discussion",
            "--sink",
            f"job-a:{sink}",
            "--anchor",
            "job-a:RECEIPT-ANCHOR-146",
        ],
        capture_output=True,
        text=True,
        env=_e2e_env(tmp_path, scenario),
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "arm round=2" in proc.stdout, "124 後必須 re-arm（第二次 arm）"
    assert "job-a completed" in proc.stdout
    receipt = json.loads(proc.stdout.strip().splitlines()[-1])
    assert receipt["schema"] == _mod.RECEIPT_SCHEMA
    assert receipt["exitState"] == "completed"
    assert receipt["jobs"][0]["delivery"]["verdict"] == "delivered"


def test_e2e_version_pin_fail_loud(tmp_path: Path) -> None:
    scenario = {"version": "2.0.19", "waits": [], "shows": {}}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "job-a", "--bridge-bin", str(STUB)],
        capture_output=True,
        text=True,
        env=_e2e_env(tmp_path, scenario),
        timeout=120,
        check=False,
    )
    assert proc.returncode == 2
    marker = json.loads(proc.stdout.strip().splitlines()[-1])
    assert marker["state"] == "error"
    assert "2.0.22" in marker["reason"]


def test_e2e_help_runs() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0
    assert "jobId" in proc.stdout
    assert "CollectionReceipt" in proc.stdout
