"""batch scheduling 契約測試（AIR-246——ArcPlan temporal_allocation 第一個
真正 temporal consumer）。

釘住的語義（codex §D 契約——勿重辯）：
- 時間閘：future `planned_not_before` 的 arc 不進 eligible set；時間到
  （now >= planned_not_before）才進——`now` 顯式注入（禁裸 datetime.now：
  signature 釘死 keyword-only 無預設）。
- 排序（非新 priority engine）：priority 為主鍵（呼叫端既有 priority 語義
  不動）；同 priority 內 temporal 只做 tiebreak——無 planned_not_before
  （無時間下界＝隨時可開工）先於有界者、有界者早窗先；鍵全同者保持輸入
  順序（queue stable order）。
- authority 邊界（C checker 不被繞）：preferred_family 排程證據屬 advisory
  planning evidence——只能影響排程/排序；live AvailabilitySnapshot stale/
  unknown → zero dispatch（AIR-245 resolver_decision_check hard invariants
  閘住；planning evidence 全 fresh 也不得偷升 dispatch eligibility）。
"""

import inspect
import json
from datetime import UTC, datetime

import pytest
from conftest import REPO_ROOT, load_module

sched = load_module("scripts/arc_batch_schedule.py")
spec = load_module("scripts/arc_spec.py")
decision_check = load_module("scripts/resolver_decision_check.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "arc-plan"
NOW = datetime(2026, 10, 2, 12, 0, 0, tzinfo=UTC)


def _e(
    arc_id: str,
    *,
    priority: int = 0,
    planned: datetime | None = None,
    preferred: str | None = None,
) -> sched.ArcEntry:
    return sched.ArcEntry(
        arc_id=arc_id,
        priority=priority,
        planned_not_before=planned,
        preferred_family=preferred,
    )


def _ids(result: dict) -> list[str]:
    return [d["arc_id"] for d in result["eligible"]]


# ---------------------------------------------------------------------------
# 時間閘：future 不進 eligible／時間到才進
# ---------------------------------------------------------------------------


class TestTimeGate:
    def test_future_not_before_excluded(self) -> None:
        """future planned_not_before 不進 eligible set（AC#3 第一腿）。"""
        result = sched.schedule(
            [_e("future-arc", planned=datetime(2026, 10, 2, 18, 0, 0, tzinfo=UTC))],
            now=NOW,
        )
        assert _ids(result) == []
        assert result["deferred"] == [
            {
                "arc_id": "future-arc",
                "planned_not_before": "2026-10-02T18:00:00+00:00",
                "reason": "planned_not_before",
            }
        ]

    def test_eligible_after_window_opens(self) -> None:
        """時間到（now == planned_not_before 邊界含）才進 eligible。"""
        window = datetime(2026, 10, 2, 18, 0, 0, tzinfo=UTC)
        before = sched.schedule([_e("arc", planned=window)], now=NOW)
        at = sched.schedule([_e("arc", planned=window)], now=window)
        after = sched.schedule(
            [_e("arc", planned=window)], now=window.replace(hour=19)
        )
        assert _ids(before) == []
        assert _ids(at) == ["arc"]
        assert _ids(after) == ["arc"]
        assert at["deferred"] == []
        assert after["deferred"] == []

    def test_untimed_always_eligible(self) -> None:
        result = sched.schedule([_e("no-window")], now=NOW)
        assert _ids(result) == ["no-window"]
        assert result["deferred"] == []


# ---------------------------------------------------------------------------
# 排序：priority 主鍵（既有語義）＋temporal 只做 tiebreak＋queue stable
# ---------------------------------------------------------------------------


class TestStableOrder:
    def test_same_priority_input_order_preserved(self) -> None:
        """同 priority 全無 temporal 鍵——輸出＝輸入順序（queue stable）。"""
        result = sched.schedule(
            [_e("b"), _e("a"), _e("c")], now=NOW
        )
        assert _ids(result) == ["b", "a", "c"]

    def test_temporal_tiebreak_earlier_window_first(self) -> None:
        """同 priority 內 temporal 只做 tiebreak：早窗先於晚窗。"""
        result = sched.schedule(
            [
                _e("late", planned=datetime(2026, 10, 2, 11, 0, 0, tzinfo=UTC)),
                _e("early", planned=datetime(2026, 10, 2, 10, 0, 0, tzinfo=UTC)),
            ],
            now=NOW,
        )
        assert _ids(result) == ["early", "late"]

    def test_untimed_sorts_before_timed_same_priority(self) -> None:
        """無時間下界（隨時可開工）先於有界者——同 priority tiebreak。"""
        result = sched.schedule(
            [
                _e("timed", planned=datetime(2026, 10, 2, 10, 0, 0, tzinfo=UTC)),
                _e("untimed"),
            ],
            now=NOW,
        )
        assert _ids(result) == ["untimed", "timed"]

    def test_full_tie_keeps_input_order(self) -> None:
        """priority 與 temporal 鍵全同——保持輸入順序（stable order）。"""
        window = datetime(2026, 10, 2, 10, 0, 0, tzinfo=UTC)
        result = sched.schedule(
            [_e("x2", planned=window), _e("x1", planned=window)], now=NOW
        )
        assert _ids(result) == ["x2", "x1"]

    def test_priority_primary_temporal_cannot_override(self) -> None:
        """priority 是主鍵——temporal tiebreak 禁越級（不改既有 priority 語義）。"""
        result = sched.schedule(
            [
                _e("low-prio", priority=1, planned=datetime(2026, 10, 2, 10, 0, 0, tzinfo=UTC)),
                _e("high-prio", priority=2, planned=datetime(2026, 10, 2, 11, 0, 0, tzinfo=UTC)),
            ],
            now=NOW,
        )
        assert _ids(result) == ["high-prio", "low-prio"]

    def test_mixed_gate_and_order(self) -> None:
        """future 被閘住不影響 eligible 排序；deferred 保持輸入順序。"""
        result = sched.schedule(
            [
                _e("future-1", planned=datetime(2026, 10, 2, 18, 0, 0, tzinfo=UTC)),
                _e("ready-2"),
                _e("future-2", planned=datetime(2026, 10, 2, 20, 0, 0, tzinfo=UTC)),
                _e("ready-1"),
            ],
            now=NOW,
        )
        assert _ids(result) == ["ready-2", "ready-1"]
        assert [d["arc_id"] for d in result["deferred"]] == ["future-1", "future-2"]


# ---------------------------------------------------------------------------
# now 可注入（禁裸 datetime.now）＋輸入驗證 fail-loud
# ---------------------------------------------------------------------------


class TestDeterminismContract:
    def test_now_is_required_keyword_only(self) -> None:
        """`now` 須為 keyword-only 且無預設——裸 datetime.now（模組內建時鐘）
        由 signature 機械排除（AIR-239 R2 單一時鐘姿態：時鐘一律注入）。"""
        params = inspect.signature(sched.schedule).parameters
        now = params["now"]
        assert now.kind is inspect.Parameter.KEYWORD_ONLY
        assert now.default is inspect.Parameter.empty

    def test_naive_now_rejected(self) -> None:
        with pytest.raises(ValueError, match="tz"):
            # naive 值是受測標的（拒絕 naive 時鐘）——noqa 故意
            sched.schedule([_e("a")], now=datetime(2026, 10, 2, 12, 0, 0))  # noqa: DTZ001

    def test_duplicate_arc_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="duplicate"):
            sched.schedule([_e("dup"), _e("dup")], now=NOW)

    def test_entry_naive_planned_not_before_rejected(self) -> None:
        with pytest.raises(ValueError, match="tz"):
            sched.ArcEntry(
                # naive 值是受測標的（拒絕 naive 時間）——noqa 故意
                arc_id="a",
                planned_not_before=datetime(2026, 10, 2, 18, 0, 0),  # noqa: DTZ001
            )

    def test_empty_arc_id_rejected(self) -> None:
        with pytest.raises(ValueError, match="arc_id"):
            sched.ArcEntry(arc_id="  ")

    def test_type_errors_for_wrong_types(self) -> None:
        """型別錯誤 TypeError（值錯誤 ValueError 分流——docstring 錯誤契約）。"""
        with pytest.raises(TypeError, match="priority"):
            sched.ArcEntry(arc_id="a", priority="high")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="dict"):
            sched.entry_from_plan(["not", "a", "dict"])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ArcPlan 消費面＋multi-arc dogfood（correctness receipt）
# ---------------------------------------------------------------------------


class TestPlanConsumption:
    def _load_plan(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_entry_from_plan_reads_top_level_temporal(self) -> None:
        plan = self._load_plan("link-valid-plan.json")
        entry = sched.entry_from_plan(plan)
        assert entry.arc_id == "AIR-246"
        assert entry.planned_not_before == datetime(2026, 10, 2, 18, 0, 0, tzinfo=UTC)
        assert entry.preferred_family == "muse"

    def test_entry_from_plan_without_temporal(self) -> None:
        plan = self._load_plan("single-review-valid.json")
        entry = sched.entry_from_plan(plan)
        assert entry.planned_not_before is None
        assert entry.preferred_family is None

    def test_entry_from_plan_bad_not_before_fails_loud(self) -> None:
        plan = self._load_plan("link-valid-plan.json")
        plan["temporal_allocation"]["planned_not_before"] = "not-a-timestamp"
        with pytest.raises(ValueError, match="planned_not_before"):
            sched.entry_from_plan(plan)

    def test_multi_arc_dogfood_correctness_receipt(self) -> None:
        """首次真實 multi-arc dogfood——只驗 correctness receipt（工單 §4：
        「哪一家省、窗利用率」數據不足留後續 tuning，禁塞本卡）。"""
        plans = [
            self._load_plan("link-valid-plan.json"),
            self._load_plan("temporal-valid.json"),
            self._load_plan("single-review-valid.json"),
        ]
        entries = sched.entries_from_plans(plans)
        assert [e.arc_id for e in entries] == ["AIR-246", "AIR-240", "AIR-102"]

        before = sched.schedule(entries, now=NOW)
        assert _ids(before) == ["AIR-102"]
        assert [d["arc_id"] for d in before["deferred"]] == ["AIR-246", "AIR-240"]

        after = sched.schedule(entries, now=datetime(2026, 10, 2, 19, 0, 0, tzinfo=UTC))
        # 窗開後全數 eligible——untimed（無時間下界）tiebreak 先於有界者，
        # 同窗（18:00）兩 arc 保持輸入順序（stable order）
        assert _ids(after) == ["AIR-102", "AIR-246", "AIR-240"]
        assert after["deferred"] == []

    def test_dogfood_receipt_machine_readable(self) -> None:
        """correctness receipt＝一行 JSON（機驗可 parse；工單 §4：只驗
        correctness receipt，「哪一家省、窗利用率」留後續 tuning）。"""
        plans = [
            self._load_plan("link-valid-plan.json"),
            self._load_plan("temporal-valid.json"),
        ]
        receipt = json.loads(
            sched.render_receipt(sched.schedule(sched.entries_from_plans(plans), now=NOW))
        )
        assert receipt["schema"] == "arc-batch-schedule/1"
        assert receipt["eligible"] == []
        assert [d["arc_id"] for d in receipt["deferred"]] == ["AIR-246", "AIR-240"]


# ---------------------------------------------------------------------------
# authority 邊界：排程證據繞不過 live check（AIR-245 C checker 閘）
# ---------------------------------------------------------------------------


def _contract() -> dict:
    return {
        "role": "implement",
        "authority": "apply",
        "judgment_floor": "execution",
        "qualifications": ["implement_from_accepted_ep"],
        "capabilities": [],
        "surface": "glm-family",
        "escalation": "invariant-or-public-boundary→decision-escalation",
        "independence": None,
    }


def _decision(
    *,
    selected: dict | None,
    planning_rows: list[dict],
    live_rows: list[dict],
) -> dict:
    """batch 輸出的排程證據（plan/slice 寫的 preferred/fallback）→ proposed
    dispatch decision——dispatch 面仍須過 AIR-245 hard invariants。"""
    return {
        "schema": "resolver-decision/1",
        "decision_id": "air-246-batch-gate",
        "contract": _contract(),
        "policy": {
            "preferred_family": "muse",
            "on_unavailable": "fallback",
            "fallback_families": ["codex"],
        },
        "planning_rows": planning_rows,
        "live_availability": live_rows,
        "qualified_families": ["muse", "codex"],
        "selected": selected,
        "dispatched_contract": _contract() if selected is not None else None,
    }


FRESH_AVAILABLE = {"freshness": "fresh", "state": "available"}
LIVE_STALE_UNKNOWN = [
    {"family": "muse", "freshness": "stale", "state": "unknown"},
    {"family": "codex", "freshness": "stale", "state": "unknown"},
]


class TestAuthorityBoundary:
    def test_stale_live_zero_dispatch_preferred_selected(self) -> None:
        """plan/slice 寫了 preferred/fallback 也繞不過 live check——live 全
        stale/unknown 時 selected preferred ⇒ invariant 違規（禁派工）。"""
        decision = _decision(
            selected={"family": "muse", "eligibility_source": "live_availability"},
            planning_rows=[
                {"family": "muse", **FRESH_AVAILABLE},
                {"family": "codex", **FRESH_AVAILABLE},
            ],
            live_rows=LIVE_STALE_UNKNOWN,
        )
        input_errors, violations = decision_check.validate_decision(decision)
        assert input_errors == []
        assert violations, "stale live 下的 selected 必須被 hard invariant 擋下"
        assert any("invariant-2" in v for v in violations)

    def test_stale_live_zero_dispatch_fallback_selected(self) -> None:
        """fallback 寫進 plan/slice 也一樣——selected fallback 在 stale live
        下違規。"""
        decision = _decision(
            selected={"family": "codex", "eligibility_source": "live_availability"},
            planning_rows=[{"family": "codex", **FRESH_AVAILABLE}],
            live_rows=[
                {"family": "muse", "freshness": "stale", "state": "unknown"},
                {"family": "codex", "freshness": "stale", "state": "unknown"},
            ],
        )
        _, violations = decision_check.validate_decision(decision)
        assert any("invariant-2" in v for v in violations)

    def test_zero_dispatch_admissible_regardless_of_planning_evidence(self) -> None:
        """live stale/unknown → zero dispatch（selected=None）＝admissible——
        planning evidence 再 fresh 也不產生 dispatch 義務。"""
        decision = _decision(
            selected=None,
            planning_rows=[
                {"family": "muse", **FRESH_AVAILABLE},
                {"family": "codex", **FRESH_AVAILABLE},
            ],
            live_rows=LIVE_STALE_UNKNOWN,
        )
        input_errors, violations = decision_check.validate_decision(decision)
        assert input_errors == []
        assert violations == []

    def test_planning_evidence_cannot_be_promoted_to_eligibility(self) -> None:
        """preferred family planning evidence 只能影響排程/排序——以 planning
        rows 當 dispatch eligibility ⇒ invariant-3 違規（advisory 禁偷升
        live authority，AIR-240）。"""
        decision = _decision(
            selected={
                "family": "muse",
                "eligibility_source": "entitlement_planning",
            },
            planning_rows=[
                {"family": "muse", **FRESH_AVAILABLE},
                {"family": "codex", **FRESH_AVAILABLE},
            ],
            live_rows=LIVE_STALE_UNKNOWN,
        )
        input_errors, violations = decision_check.validate_decision(decision)
        assert input_errors == []
        assert any("invariant-3" in v for v in violations)

    def test_schedule_output_has_no_dispatch_decision(self) -> None:
        """batch 模組輸出僅排程面（eligible/deferred）——不含 dispatch 決策欄
        （selected/dispatch），authority 歸 resolver live check。"""
        result = sched.schedule(
            [_e("a", preferred="muse"), _e("b", preferred="codex")], now=NOW
        )
        assert set(result) == {"eligible", "deferred"}
        for row in result["eligible"] + result["deferred"]:
            assert "selected" not in row
            assert "dispatch" not in row
