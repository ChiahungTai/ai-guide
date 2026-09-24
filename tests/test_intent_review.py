"""intent_review 契約測試（AIR-135.1 S3——Intent Review 驗收腿工作單編譯器）。

釘住的 invariant（卡面＋S1/S2 延伸已決策勿重辯）：
- D1 畫線：generate 純編譯（靜態物產出）——無 runner／無執行編排（歸 135.7）。
- AC#7 語義承載：intent verbatim／成功謂詞自 spec 凍結欄逐字（禁改寫）；
  final artifact／機械驗證證據包自 plan work_units sink 面投影；read-set
  排除規則在場（排除的是 implementer reasoning 非驗收事實）。
- PLAN_CHANGES 複核段：逐筆 what＋diff；零偏差＝零偏差聲明；per-batch 判定
  欄三值（無偏移／表面符合語義已偏／intent 本身變更）。
- receipt.intent_review 回寫面（arc_spec 新選填欄）：verdict 枚舉 GO／
  GO-WITH-FIXES／NO-GO 拒未知；minimum＝verdict＋leg＋read_set_exclusion。
- fail-loud（codex 文案形，同 S1/S2）：缺欄一次列全部、schema marker 不符、
  spec／plan 身份衝突（雙 authoritative）、plan_hash 漂移即錯。
"""

import json

import pytest
from conftest import load_module

_arc = load_module("scripts/arc_spec.py")
_mod = load_module("scripts/intent_review.py")


# ---------------------------------------------------------------------------
# 建構器：spec／plan／receipt 最小合法實例（同 test_arc_spec 慣例）
# ---------------------------------------------------------------------------


def _spec() -> dict:
    return {
        "schema": "arc-spec/1",
        "card_id": "AIR-94",
        "card_baseline": "d6b05d0",
        "source_card": "backlog/tasks/air-94 - ai-rules→ai-guide-改名落地.md",
        "intent_verbatim": "target=ai-guide；user 2026-09-14 拍板立即執行",
        "non_goals": "禁 push（consent 在 user）",
        "revert_budget": "deep-work 弧全程禁 commit/push",
        "pre_authorizations": "目錄 mv＝flash 主 session 最終段親執行",
        "assumptions": "DRAFT-8 三輪定案；codex 裁定零技術耦合",
        "success_predicate": "investigation.md 驗收節 1–8 全數通過",
    }


def _plan(plan_changes: list | None = None) -> dict:
    plan = {
        "schema": "arc-plan/1",
        "card_id": "AIR-94",
        "card_baseline": "d6b05d0",
        "version": 1,
        "supersedes": None,
        "work_units": [
            {
                "unit_id": "AIR-94#W1",
                "title": "flash 調查",
                "role": "implement",
                "phase": "Build",
                "depends_on": [],
            }
        ],
        "budget_context": {"revert_exposure_cap": 0, "usage_cap": 0},
        "terminal_semantics": {
            "on_budget_exhausted": "budget-limited",
            "raise_cap": "human-action",
            "settle_gate": "human",
        },
        "plan_changes": plan_changes or [],
    }
    plan["plan_hash"] = _arc.plan_content_hash(plan)
    return plan


def _receipt() -> dict:
    return {
        "schema": "slice-receipt/1",
        "slice_id": "AIR-94#W1-slice",
        "card_id": "AIR-94",
        "unit_id": "AIR-94#W1",
        "plan_version": 1,
        "plan_hash": "a" * 64,
        "job_id": "job-muflra3f",
        "family": "local",
        "status": "completed",
        "delivery": {
            "mode": "artifact",
            "sink": ".agent-tmp/ai-guide-rename/investigation.md",
            "l1_present": True,
            "l2_anchor": True,
            "anchor_hits": ["驗收節 1"],
            "verdict": "delivered",
        },
        "bounded_receipt_projection": {"final_text_non_empty": True},
    }


def _plan_with_sinks() -> dict:
    """sink 面投影測資：implement／verify 帶 sink、review 帶 sink（須被排除）。"""
    plan = _plan()
    plan["work_units"] = [
        {
            "unit_id": "AIR-94#W1",
            "title": "flash implement",
            "role": "implement",
            "phase": "Build",
            "depends_on": [],
            "sink": "src/rename/investigation.md",
        },
        {
            "unit_id": "AIR-94#W4",
            "title": "flash implement 落地",
            "role": "implement",
            "phase": "Build",
            "depends_on": ["AIR-94#W1"],
            "sink": {"mode": "artifact", "path": "docs/rename-notes.md"},
        },
        {
            "unit_id": "AIR-94#W5",
            "title": "verify 收尾",
            "role": "verify",
            "phase": "Verify",
            "depends_on": ["AIR-94#W4"],
            "sink": "reports/verify.json",
        },
        {
            "unit_id": "AIR-94#W6",
            "title": "codex code-review",
            "role": "review",
            "phase": "Verify",
            "depends_on": ["AIR-94#W4"],
            "sink": ".agent-tmp/findings.md",
        },
    ]
    plan["plan_hash"] = _arc.plan_content_hash(plan)
    return plan


# ---------------------------------------------------------------------------
# generate：零偏差態
# ---------------------------------------------------------------------------


class TestGenerateZeroDeviation:
    def test_zero_deviation_declaration(self) -> None:
        wo = _mod.generate(_spec(), _plan())
        pcr = wo["plan_changes_review"]
        assert pcr["zero_deviation"] is True
        assert "零偏差聲明" in pcr["declaration"]
        assert pcr["batches"] == []

    def test_intent_verbatim_and_predicate_verbatim(self) -> None:
        """AC#7：intent verbatim／成功謂詞自 spec 凍結欄逐字——禁改寫。"""
        spec = _spec()
        wo = _mod.generate(spec, _plan())
        assert wo["intent_verbatim"] == spec["intent_verbatim"]
        assert wo["success_predicate"] == spec["success_predicate"]

    def test_read_set_exclusion_rule_present(self) -> None:
        """AC#7：排除中間 plan／review／court 討論——排除的是 implementer
        reasoning 非驗收事實；policy 單一源＝arc_spec ROLE_READ_SET。"""
        wo = _mod.generate(_spec(), _plan())
        rs = wo["read_set"]
        assert rs["policy"] == "chain-exclusion"
        assert rs["policy"] == _arc.ROLE_READ_SET["intent-review"][0]
        assert any("中間 plan" in e for e in rs["excluded"])
        assert any("review" in e for e in rs["excluded"])
        assert "implementer reasoning" in rs["rule"]

    def test_sink_projection_implement_and_evidence(self) -> None:
        """final artifact←implement sink 面；證據包←verify/test sink 面；
        review 腿產物＝中間鏈——不入本單任一投影面。"""
        wo = _mod.generate(_spec(), _plan_with_sinks())
        assert wo["final_artifacts"] == [
            {"unit_id": "AIR-94#W1", "title": "flash implement", "path": "src/rename/investigation.md"},
            {"unit_id": "AIR-94#W4", "title": "flash implement 落地", "path": "docs/rename-notes.md"},
        ]
        assert wo["evidence_pack"] == [
            {"unit_id": "AIR-94#W5", "title": "verify 收尾", "path": "reports/verify.json"}
        ]
        assert all("findings.md" not in a["path"] for a in wo["final_artifacts"])
        assert wo["jit_sink_units"] == []

    def test_sink_absent_jit_note(self) -> None:
        """plan 層 sink 缺席＝DispatchSlice JIT（D2/D5）——記 jit_sink_units
        誠實標注，非靜默。"""
        wo = _mod.generate(_spec(), _plan())
        assert wo["final_artifacts"] == []
        assert wo["jit_sink_units"] == ["AIR-94#W1"]

    def test_gate_semantics_first_batch_carried(self) -> None:
        """「首批恆跑不抽樣」語義照 135.3 卡面承載；verdict 枚舉單一源＝
        arc_spec（工單不重定）。"""
        wo = _mod.generate(_spec(), _plan())
        assert "恆跑不抽樣" in wo["gate_semantics"]["first_batch"]
        assert "閘外小弧自報為足" in wo["gate_semantics"]["trigger"]
        assert tuple(wo["receipt_writeback"]["verdict_enum"]) == tuple(
            _arc.INTENT_REVIEW_VERDICTS
        )

    def test_render_json_block_round_trip(self) -> None:
        md = _mod.render(_mod.generate(_spec(), _plan()))
        block = md.split("```json", 1)[1].split("```", 1)[0]
        assert json.loads(block)["intent_verbatim"] == _spec()["intent_verbatim"]


# ---------------------------------------------------------------------------
# generate：有偏差態＋PLAN_CHANGES 複核段
# ---------------------------------------------------------------------------


class TestGenerateWithDeviations:
    def test_deviation_batches_carry_what_diff(self) -> None:
        changes = [{"what": "W4 改以 sed 批次落點", "diff": "原文：逐檔 mv → 現行：批次 mv"}]
        wo = _mod.generate(_spec(), _plan(plan_changes=changes))
        pcr = wo["plan_changes_review"]
        assert pcr["zero_deviation"] is False
        assert pcr["declaration"] is None
        assert len(pcr["batches"]) == 1
        batch = pcr["batches"][0]
        assert batch["what"] == changes[0]["what"]
        assert batch["diff"] == changes[0]["diff"]
        assert batch["review_verdict"] == ""  # 審查腿判定欄待填

    def test_batch_verdict_options(self) -> None:
        """per-batch 判定欄三值（AC#7 0920 修訂語彙）。"""
        wo = _mod.generate(_spec(), _plan(plan_changes=[{"what": "w", "diff": "d"}]))
        assert wo["plan_changes_review"]["verdict_options"] == (
            "無偏移",
            "表面符合語義已偏",
            "intent 本身變更",
        )

    def test_render_deviation_table(self) -> None:
        changes = [{"what": "偏差什麼", "diff": "原文 → 現行"}]
        md = _mod.render(_mod.generate(_spec(), _plan(plan_changes=changes)))
        assert "PLAN_CHANGES 複核段" in md
        assert "偏差什麼" in md and "原文 → 現行" in md
        assert "無偏移／表面符合語義已偏／intent 本身變更" in md
        assert "待審查腿填" in md


# ---------------------------------------------------------------------------
# generate：fail-loud（缺欄一次列全部、marker、身份衝突、hash 漂移）
# ---------------------------------------------------------------------------


class TestGenerateFailLoud:
    def test_missing_spec_field_fails_loud(self) -> None:
        spec = _spec()
        del spec["intent_verbatim"]
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(spec, _plan())
        msg = str(ei.value)
        assert "intent_verbatim" in msg
        assert "Required machine-invariant fields" in msg

    def test_blank_spec_field_counts_as_missing(self) -> None:
        spec = _spec()
        spec["success_predicate"] = "   "
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(spec, _plan())
        assert "success_predicate" in str(ei.value)

    def test_bad_spec_schema_marker(self) -> None:
        spec = _spec()
        spec["schema"] = "arc-spec/2"
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(spec, _plan())
        assert "Unknown schema marker" in str(ei.value)

    def test_bad_plan_schema_marker(self) -> None:
        plan = _plan()
        plan["schema"] = "arc-plan/2"
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(_spec(), plan)
        assert "Unknown schema marker" in str(ei.value)

    def test_conflicting_card_id_is_dual_authority(self) -> None:
        spec = _spec()
        spec["card_id"] = "AIR-95"
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(spec, _plan())
        assert "Conflicting card_id" in str(ei.value)

    def test_conflicting_baseline_is_dual_authority(self) -> None:
        spec = _spec()
        spec["card_baseline"] = "abc1234"
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(spec, _plan())
        assert "Conflicting card_baseline" in str(ei.value)

    def test_plan_hash_drift_fails(self) -> None:
        """Intent Review 不得以漂移計畫為基準（D2 禁原地改）。"""
        plan = _plan()
        plan["plan_hash"] = "b" * 64
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(_spec(), plan)
        assert "Plan hash mismatch" in str(ei.value)

    def test_missing_plan_changes_key_fails(self) -> None:
        """plan_changes 鍵缺席違 arc-plan schema（required＋nullable）——上游
        validator 先擋（generate 不靜默補空）。"""
        plan = _plan()
        del plan["plan_changes"]
        with pytest.raises(_mod.IntentReviewError) as ei:
            _mod.generate(_spec(), plan)
        assert "plan_changes" in str(ei.value)


# ---------------------------------------------------------------------------
# receipt.intent_review 回寫面（arc_spec 新選填欄；同 N6 receipt_sink 慣例）
# ---------------------------------------------------------------------------


class TestReceiptIntentReviewField:
    def test_field_is_optional_machine_invariant(self) -> None:
        fields = {f.name: f for f in _arc.ARTIFACTS["receipt"].fields}
        f = fields["intent_review"]
        assert f.kind == "machine-invariant"
        assert f.required_at == "never"  # 選填不進 required 集——閘外小弧自報為足

    def test_absent_still_valid(self) -> None:
        assert "intent_review" not in _receipt()
        assert _arc.validate("receipt", _receipt()) == []

    def test_valid_intent_review_passes(self) -> None:
        r = _receipt()
        r["intent_review"] = {
            "verdict": "GO-WITH-FIXES",
            "leg": "agent_20b1c349",
            "read_set_exclusion": "chain-exclusion：未讀中間 plan／review／court 討論",
        }
        assert _arc.validate("receipt", r) == []

    def test_unknown_verdict_lists_available(self) -> None:
        r = _receipt()
        r["intent_review"] = {"verdict": "PASS", "leg": "x", "read_set_exclusion": "y"}
        errs = _arc.validate("receipt", r)
        assert any(
            "Unknown intent review verdict `PASS`" in e and "GO-WITH-FIXES" in e
            for e in errs
        )

    def test_missing_verdict_fails(self) -> None:
        r = _receipt()
        r["intent_review"] = {"leg": "x", "read_set_exclusion": "y"}
        assert any(
            "`intent_review.verdict`" in e for e in _arc.validate("receipt", r)
        )

    def test_missing_leg_and_exclusion_fail(self) -> None:
        r = _receipt()
        r["intent_review"] = {"verdict": "GO"}
        errs = _arc.validate("receipt", r)
        assert any("`intent_review.leg`" in e for e in errs)
        assert any("`intent_review.read_set_exclusion`" in e for e in errs)

    def test_non_dict_fails(self) -> None:
        r = _receipt()
        r["intent_review"] = "GO"
        assert any("must be an object" in e for e in _arc.validate("receipt", r))
