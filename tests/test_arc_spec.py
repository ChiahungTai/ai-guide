"""arc_spec 契約測試（AIR-135.1 S1——schema-first compiler）。

釘住的 invariant（卡面 Plan D1-D8 已決策勿重辯）：
- D3 欄位二分——每欄顯式標注 machine-invariant／llm-guidance；prompt 材料
  禁塞 machine-invariant 欄。
- fail-loud（codex multi_agents_common.rs:395-442 文案形）——缺 machine-
  invariant 欄／歧義值／未知枚舉＝exit 非 0＋錯誤列出可用值。
- ArcPlan 單調版本號＋決定性內容 hash（sha256 of canonical JSON，禁
  process-salted hash）；DispatchSlice／receipt 回指 plan 版本。
- D5/D8——family/model/binding/ledger 留欄、dispatch stage 才要求（resolver
  JIT 填值）；D6——BudgetLimited 終態＋raise-cap 人類動作＋settle 人類 gate。
- D7——receipt 沿用 CollectionReceipt 欄位集＋plan 版本回指；terminal≠complete。
"""

import json
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/arc_spec.py")


# ---------------------------------------------------------------------------
# 建構器：四物的最小合法實例
# ---------------------------------------------------------------------------

TERMINAL_SEMANTICS = {
    "on_budget_exhausted": "budget-limited",
    "raise_cap": "human-action",
    "settle_gate": "human",
}

PLAN_HASH = "a" * 64


def _arc_spec() -> dict:
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


def _arc_plan() -> dict:
    return {
        "schema": "arc-plan/1",
        "card_id": "AIR-94",
        "card_baseline": "d6b05d0",
        "version": 1,
        "supersedes": None,
        "plan_hash": PLAN_HASH,
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
        "terminal_semantics": dict(TERMINAL_SEMANTICS),
        "plan_changes": [],
    }


def _plan_with_valid_hash() -> dict:
    plan = _arc_plan()
    plan["plan_hash"] = _mod.plan_content_hash(plan)
    return plan


def _slice(with_resolver: bool = True) -> dict:
    data = {
        "schema": "dispatch-slice/1",
        "slice_id": "AIR-94#W1-slice",
        "card_id": "AIR-94",
        "card_baseline": "d6b05d0",
        "plan_version": 1,
        "plan_hash": PLAN_HASH,
        "unit_id": "AIR-94#W1",
        "role": "implement",
        "authority": "writer",
        "capability_mode": "ReadWrite",
        "owning_wt": {"path": "/Users/ctai/Github/ai-guide", "branch": "air-94"},
        "read_set": {
            "policy": "full-context",
            "pointers": ["backlog/tasks/air-94 - ai-rules→ai-guide-改名落地.md"],
        },
        "sink": {
            "mode": "artifact",
            "path": ".agent-tmp/ai-guide-rename/investigation.md",
        },
        "accept": {
            "predicate": "exists+readable+nonempty",
            "anchors": ["驗收節 1", "驗收節 8"],
        },
        "budget_context": {"revert_remaining": 0, "slice_budget": 0, "debit_events": []},
        "terminal_semantics": dict(TERMINAL_SEMANTICS),
        "carrier": "zcode-agent",
        "collection_mode": "bounded-receipt",
        "commit_delegation": "none",
    }
    if with_resolver:
        data.update(
            {
                "family": "local",
                "model": "builtin:zai-coding-plan/GLM-5.3-Flash",
                "binding": "presets default→model-routing catalog 解析",
                "ledger": ".delegate-bridge/jobs.json",
                "dispatch_id": "job-muflra3f",
            }
        )
    return data


def _receipt() -> dict:
    return {
        "schema": "slice-receipt/1",
        "slice_id": "AIR-94#W1-slice",
        "card_id": "AIR-94",
        "unit_id": "AIR-94#W1",
        "plan_version": 1,
        "plan_hash": PLAN_HASH,
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


def _errors(kind: str, data: dict, stage: str = "dispatch") -> list[str]:
    return _mod.validate(kind, data, stage=stage)


# ---------------------------------------------------------------------------
# schema registry（DONE-WHEN #1：每欄標注 machine-invariant／LLM-guidance）
# ---------------------------------------------------------------------------


class TestSchemaRegistry:
    def test_four_kinds_registered(self) -> None:
        assert set(_mod.KINDS) == {"arc-spec", "arc-plan", "dispatch-slice", "receipt"}

    def test_every_field_annotated_machine_or_llm(self) -> None:
        for kind, art in _mod.ARTIFACTS.items():
            for f in art.fields:
                assert f.kind in ("machine-invariant", "llm-guidance"), (kind, f.name)

    def test_every_artifact_has_required_machine_invariant_fields(self) -> None:
        for kind, art in _mod.ARTIFACTS.items():
            required = [
                f
                for f in art.fields
                if f.kind == "machine-invariant" and f.required_at == "always"
            ]
            assert required, kind

    def test_entry_six_columns_are_machine_invariant(self) -> None:
        fields = {f.name: f for f in _mod.ARTIFACTS["arc-spec"].fields}
        for col in (
            "intent_verbatim",
            "non_goals",
            "revert_budget",
            "pre_authorizations",
            "assumptions",
            "success_predicate",
        ):
            assert col in fields and fields[col].kind == "machine-invariant", col

    def test_prompt_material_is_llm_guidance(self) -> None:
        """D3：敘述性 prompt 材料禁入 machine-invariant 欄。"""
        fields = {f.name: f for f in _mod.ARTIFACTS["dispatch-slice"].fields}
        assert fields["prompt_material"].kind == "llm-guidance"

    def test_resolver_fields_are_dispatch_stage(self) -> None:
        """D5/D8：family/model/binding/ledger 留欄、dispatch stage 才要求。"""
        fields = {f.name: f for f in _mod.ARTIFACTS["dispatch-slice"].fields}
        for name in ("family", "model", "binding", "ledger"):
            assert fields[name].required_at == "dispatch", name


# ---------------------------------------------------------------------------
# contract 錯（raise ArcSpecError）
# ---------------------------------------------------------------------------


class TestContractErrors:
    def test_validate_unknown_kind_raises(self) -> None:
        with pytest.raises(_mod.ArcSpecError) as ei:
            _mod.validate("foo", {})
        assert "Available kinds" in str(ei.value)

    def test_validate_unknown_stage_raises(self) -> None:
        with pytest.raises(_mod.ArcSpecError) as ei:
            _mod.validate("arc-spec", _arc_spec(), stage="prod")
        assert "Available stages" in str(ei.value)


# ---------------------------------------------------------------------------
# ArcSpec
# ---------------------------------------------------------------------------


class TestArcSpecValidation:
    def test_valid_arc_spec_passes(self) -> None:
        assert _errors("arc-spec", _arc_spec()) == []

    def test_missing_revert_budget_lists_required(self) -> None:
        data = _arc_spec()
        del data["revert_budget"]
        errs = _errors("arc-spec", data)
        assert len(errs) == 1
        msg = errs[0]
        assert "Missing machine-invariant field" in msg
        assert "`revert_budget`" in msg
        assert "Required machine-invariant fields" in msg
        assert "success_predicate" in msg  # 列出全部必填（codex 文案形）

    def test_missing_success_predicate_fails(self) -> None:
        """AC#1：priced-autonomy 必要欄位（成功謂詞）缺場＝禁派工。"""
        data = _arc_spec()
        del data["success_predicate"]
        assert _errors("arc-spec", data) != []

    def test_blank_value_counts_as_missing(self) -> None:
        data = _arc_spec()
        data["intent_verbatim"] = "   "
        errs = _errors("arc-spec", data)
        assert any("intent_verbatim" in e and "blank" in e for e in errs)

    def test_bad_baseline_hex_fails(self) -> None:
        data = _arc_spec()
        data["card_baseline"] = "zzzz"
        assert any("card_baseline" in e for e in _errors("arc-spec", data))


# ---------------------------------------------------------------------------
# ArcPlan（版本＋hash＋work units）
# ---------------------------------------------------------------------------


class TestArcPlanValidation:
    def test_valid_plan_passes(self) -> None:
        assert _errors("arc-plan", _plan_with_valid_hash()) == []

    def test_nullable_fields_absent_key_fails(self) -> None:
        """nullable（supersedes/plan_changes）＝key 在場允許 null/[]；key 缺席仍 fail-loud。"""
        p = _plan_with_valid_hash()
        del p["supersedes"]
        del p["plan_changes"]
        errs = _errors("arc-plan", p)
        assert any("`supersedes`" in e for e in errs)
        assert any("`plan_changes`" in e for e in errs)

    def test_nested_scalar_guards_fail(self) -> None:
        """muse N1：巢狀欄純量型態原為靜默跳過（silent-pass）——guard 補後須報。"""
        for key, scalar in (
            ("work_units", "all"),
            ("budget_context", "unlimited"),
            ("plan_changes", "none"),
        ):
            p = _plan_with_valid_hash()
            p[key] = scalar
            errs = _errors("arc-plan", p)
            assert any(f"`{key}`" in e for e in errs), (key, errs)

    def test_plan_hash_golden_vector(self) -> None:
        """muse N5：golden vector 釘死序列化形——impl 內部序列化漂移即紅（防 self-referential 全綠）。"""
        fixed = {"schema": "arc-plan/1", "card_id": "GOLDEN", "version": 1, "plan_hash": "ignored"}
        assert _mod.plan_content_hash(fixed) == (
            "dbcac2c947e03f5317bf00b99049a8111eab32d1e557cb1b8d0d81355de9b724"
        )

    def test_plan_hash_deterministic_regardless_of_key_order(self) -> None:
        """AC#2：決定性內容 hash——canonical JSON（sort_keys），禁 process-salted。"""
        p1 = _plan_with_valid_hash()
        p2 = {k: p1[k] for k in reversed(list(p1))}
        assert _mod.plan_content_hash(p1) == _mod.plan_content_hash(p2)

    def test_plan_hash_excludes_itself(self) -> None:
        p = _arc_plan()
        p["plan_hash"] = "x"
        h1 = _mod.plan_content_hash(p)
        p["plan_hash"] = "y"
        assert _mod.plan_content_hash(p) == h1

    def test_plan_hash_mismatch_fails_loud(self) -> None:
        p = _plan_with_valid_hash()
        p["work_units"][0]["title"] = "tampered"
        assert any("Plan hash mismatch" in e for e in _errors("arc-plan", p))

    def test_version_must_be_positive_int(self) -> None:
        p = _plan_with_valid_hash()
        p["version"] = 0
        assert any("version" in e for e in _errors("arc-plan", p))
        p["version"] = True  # bool 是 int 子類——須拒
        assert any("version" in e for e in _errors("arc-plan", p))

    def test_supersedes_must_be_older(self) -> None:
        p = _plan_with_valid_hash()
        p["version"] = 2
        p["plan_hash"] = _mod.plan_content_hash(p)
        p["supersedes"] = 2
        assert any("supersedes" in e for e in _errors("arc-plan", p))

    def test_duplicate_unit_id_is_dual_authority(self) -> None:
        """AC#1：雙 authoritative 值＝fail-loud。"""
        p = _plan_with_valid_hash()
        wu = dict(p["work_units"][0])
        wu["title"] = "second"
        p["work_units"].append(wu)
        p["plan_hash"] = _mod.plan_content_hash(p)
        assert any("Duplicate work unit id" in e for e in _errors("arc-plan", p))

    def test_unknown_role_in_work_unit_lists_available(self) -> None:
        p = _plan_with_valid_hash()
        p["work_units"][0]["role"] = "tester"
        errs = _errors("arc-plan", p)
        assert any("Unknown role" in e and "implement" in e for e in errs)

    def test_plan_changes_entry_requires_diff(self) -> None:
        """D4：PLAN_CHANGES 修訂須附 diff 交驗收腿複核。"""
        p = _plan_with_valid_hash()
        p["plan_changes"] = [{"what": "cap 放寬"}]
        assert any("plan_changes" in e for e in _errors("arc-plan", p))

    def test_budget_context_nonfinite_fails(self) -> None:
        """codex 先例：非有限值預算＝Fatal（IEEE 754 fail-open 防護）。"""
        p = _plan_with_valid_hash()
        p["budget_context"]["usage_cap"] = float("nan")
        assert any("finite" in e for e in _errors("arc-plan", p))

    def test_terminal_semantics_fixed_shape(self) -> None:
        """D6：BudgetLimited 終態＋raise-cap 人類動作＋settle 人類 gate。"""
        p = _plan_with_valid_hash()
        p["terminal_semantics"]["settle_gate"] = "auto"
        errs = _errors("arc-plan", p)
        assert any("settle_gate" in e and "human" in e for e in errs)


class TestBudgetCapThreeState:
    """改版批次（晨間合議定案）：budget cap 欄三態——number／null／"unlimited"。

    同值異義防再犯（0-佔位覆轍）：0＝零自治（具體帽）、null（key 在場）＝未設
    （消費端自行判讀，非無帽）、"unlimited"＝無帽（decision-5 政策語義顯式形）；
    revert 欄維持純數值（可逆預算必須具體）。
    """

    def _plan_capped(self, cap: object) -> dict:
        p = _plan_with_valid_hash()
        p["budget_context"]["usage_cap"] = cap
        p["plan_hash"] = _mod.plan_content_hash(p)
        return p

    # --- arc-plan.usage_cap 三態 ---

    def test_plan_usage_cap_number_passes(self) -> None:
        assert _errors("arc-plan", self._plan_capped(5)) == []

    def test_plan_usage_cap_zero_still_specific_cap(self) -> None:
        """0＝零自治（具體帽）——現行行為不變。"""
        assert _errors("arc-plan", self._plan_capped(0)) == []

    def test_plan_usage_cap_null_passes(self) -> None:
        assert _errors("arc-plan", self._plan_capped(None)) == []

    def test_plan_usage_cap_unlimited_passes(self) -> None:
        assert _errors("arc-plan", self._plan_capped("unlimited")) == []

    def test_plan_usage_cap_other_string_lists_available(self) -> None:
        p = self._plan_capped("lots")
        errs = _errors("arc-plan", p)
        assert any("Unknown budget cap `lots`" in e and "unlimited" in e for e in errs)

    def test_plan_usage_cap_missing_key_fails(self) -> None:
        """key 缺席≠null 未設——三態須顯式（禁靜默當未設）。"""
        p = _plan_with_valid_hash()
        del p["budget_context"]["usage_cap"]
        p["plan_hash"] = _mod.plan_content_hash(p)
        errs = _errors("arc-plan", p)
        assert any("usage_cap" in e and "missing" in e for e in errs)

    def test_plan_usage_cap_bool_fails(self) -> None:
        assert any("usage_cap" in e for e in _errors("arc-plan", self._plan_capped(True)))

    def test_plan_usage_cap_nonfinite_fails(self) -> None:
        p = self._plan_capped(float("nan"))
        assert any("usage_cap" in e and "finite" in e for e in _errors("arc-plan", p))

    def test_plan_usage_cap_negative_fails(self) -> None:
        p = self._plan_capped(-1)
        assert any("usage_cap" in e and ">= 0" in e for e in _errors("arc-plan", p))

    def test_plan_revert_exposure_cap_null_fails(self) -> None:
        """revert 敞口帽維持純數值（可逆預算必須具體）——null 拒。"""
        p = _plan_with_valid_hash()
        p["budget_context"]["revert_exposure_cap"] = None
        errs = _errors("arc-plan", p)
        assert any("revert_exposure_cap" in e and "NoneType" in e for e in errs)

    # --- dispatch-slice.slice_budget 三態 ---

    def test_slice_budget_three_states_pass(self) -> None:
        for value in (0, 5, None, "unlimited"):
            s = _slice()
            s["budget_context"]["slice_budget"] = value
            assert _errors("dispatch-slice", s) == [], value

    def test_slice_budget_bad_string_lists_available(self) -> None:
        s = _slice()
        s["budget_context"]["slice_budget"] = "no-cap"
        errs = _errors("dispatch-slice", s)
        assert any(
            "Unknown budget cap `no-cap`" in e and "null (unset)" in e for e in errs
        )

    def test_slice_budget_missing_key_fails(self) -> None:
        s = _slice()
        del s["budget_context"]["slice_budget"]
        errs = _errors("dispatch-slice", s)
        assert any("slice_budget" in e and "missing" in e for e in errs)

    def test_slice_revert_remaining_null_fails(self) -> None:
        """revert_remaining 維持純數值——null 拒。"""
        s = _slice()
        s["budget_context"]["revert_remaining"] = None
        errs = _errors("dispatch-slice", s)
        assert any("revert_remaining" in e and "NoneType" in e for e in errs)


# ---------------------------------------------------------------------------
# DispatchSlice
# ---------------------------------------------------------------------------


class TestDispatchSliceValidation:
    def test_compile_stage_passes_without_resolver_fields(self) -> None:
        data = _slice(with_resolver=False)
        assert _errors("dispatch-slice", data, stage="compile") == []

    def test_sink_mode_unknown_fails(self) -> None:
        """muse N2：sink.mode 無枚舉時 carrier-pigeon 也 VALID——補 codex 式列可用值。"""
        s = _slice()
        s["sink"] = {"mode": "carrier-pigeon"}
        errs = _errors("dispatch-slice", s)
        assert any("Unknown sink mode" in e and "carrier-pigeon" in e for e in errs)

    def test_read_set_without_pointers_valid(self) -> None:
        """muse N3 顯式決策（b）：pointers 選填（S1——receipt-only 通知型 slice 合法；S2 覆核）。"""
        s = _slice()
        s["read_set"] = {"policy": "full-context"}
        assert _errors("dispatch-slice", s) == []

    def test_dispatch_stage_passes_with_resolver_fields(self) -> None:
        assert _errors("dispatch-slice", _slice()) == []

    def test_dispatch_stage_requires_resolver_fields(self) -> None:
        data = _slice(with_resolver=False)
        joined = "\n".join(_errors("dispatch-slice", data, stage="dispatch"))
        for field in ("family", "model", "binding", "ledger", "dispatch_id"):
            assert f"`{field}`" in joined, field

    def test_unknown_role_lists_available(self) -> None:
        data = _slice()
        data["role"] = "tester"
        errs = _errors("dispatch-slice", data)
        assert any(
            "Unknown role `tester`" in e and "Available roles" in e for e in errs
        )

    def test_review_role_forbids_full_context(self) -> None:
        """AC#2：review 類禁逐字繼承 implementer reasoning——policy 限縮。"""
        data = _slice()
        data["role"] = "review"
        errs = _errors("dispatch-slice", data)
        assert any(
            "read_set policy `full-context`" in e and "problem-contract-only" in e
            for e in errs
        )

    def test_intent_review_requires_chain_exclusion(self) -> None:
        """AC#2（0920 修訂）：Intent Review slice＝chain-exclusion。"""
        data = _slice()
        data["role"] = "intent-review"
        data["read_set"] = {"policy": "problem-contract-only", "pointers": ["x.md"]}
        errs = _errors("dispatch-slice", data)
        assert any("chain-exclusion" in e for e in errs)

    def test_dual_authoritative_sink_conflict(self) -> None:
        """AC#1：雙 authoritative sink＝fail-loud。"""
        data = _slice()
        data["sink"] = {"mode": "receipt-only", "path": "a.md"}
        errs = _errors("dispatch-slice", data)
        assert any("Conflicting authoritative sink" in e for e in errs)

    def test_artifact_sink_requires_accept(self) -> None:
        """AC#2：sink 為 artifact 時 accept（exists+readable+nonempty＋anchors）必帶。"""
        data = _slice()
        del data["accept"]
        assert any("`accept`" in e for e in _errors("dispatch-slice", data))

    def test_writer_with_readonly_capability_conflict(self) -> None:
        data = _slice()
        data["capability_mode"] = "ReadOnly"
        errs = _errors("dispatch-slice", data)
        assert any("Conflicting authority" in e for e in errs)

    def test_owning_wt_identity_subfields_required(self) -> None:
        """AC#6：owning WT identity（path＋branch）缺子欄＝歧義。"""
        data = _slice()
        data["owning_wt"] = {"path": "/Users/ctai/Github/ai-guide"}
        errs = _errors("dispatch-slice", data)
        assert any("`owning_wt.branch`" in e for e in errs)

    def test_wrong_typed_dict_field_fails(self) -> None:
        """dict 型 machine-invariant 欄給純量＝歧義值，fail-loud。"""
        data = _slice()
        data["read_set"] = "full-context"
        errs = _errors("dispatch-slice", data)
        assert any("`read_set` must be an object" in e for e in errs)

    def test_nonfinite_budget_fails(self) -> None:
        data = _slice()
        data["budget_context"]["revert_remaining"] = float("nan")
        assert any("finite" in e for e in _errors("dispatch-slice", data))

    def test_negative_budget_fails(self) -> None:
        data = _slice()
        data["budget_context"]["revert_remaining"] = -1
        assert any(">= 0" in e for e in _errors("dispatch-slice", data))

    def test_unknown_family_lists_available(self) -> None:
        data = _slice()
        data["family"] = "weixin"
        errs = _errors("dispatch-slice", data)
        assert any("Unknown family `weixin`" in e and "glm" in e for e in errs)


class TestReceiptSinkField:
    """N6（AIR-135.1 S2）：dispatch-slice.receipt_sink 選填欄——slice 回執落點。"""

    def test_receipt_sink_is_optional_machine_invariant(self) -> None:
        fields = {f.name: f for f in _mod.ARTIFACTS["dispatch-slice"].fields}
        f = fields["receipt_sink"]
        assert f.kind == "machine-invariant"
        assert f.required_at == "never"  # 選填不進 required 集

    def test_receipt_sink_absent_still_valid(self) -> None:
        """未填＝慣例路徑 <wt>/.agent-tmp/<卡id>/<slice-id>-receipt.md 生效，不擋派工。"""
        s = _slice()
        assert "receipt_sink" not in s
        assert _errors("dispatch-slice", s) == []

    def test_receipt_sink_present_valid_blank_fails(self) -> None:
        s = _slice()
        s["receipt_sink"] = ".agent-tmp/air-135.1/s1-receipt.md"
        assert _errors("dispatch-slice", s) == []
        s["receipt_sink"] = "   "
        errs = _errors("dispatch-slice", s)
        assert any("`receipt_sink`" in e and "blank" in e for e in errs)


# ---------------------------------------------------------------------------
# receipt（D7：CollectionReceipt 欄位集＋plan 回指；terminal≠complete）
# ---------------------------------------------------------------------------


class TestReceiptValidation:
    def test_valid_receipt_passes(self) -> None:
        assert _errors("receipt", _receipt()) == []

    def test_completed_with_undelivered_fails(self) -> None:
        r = _receipt()
        r["delivery"]["verdict"] = "undelivered"
        errs = _errors("receipt", r)
        assert any("terminal≠complete" in e for e in errs)

    def test_plan_back_reference_required(self) -> None:
        """D7：receipt 須回指 plan 版本。"""
        r = _receipt()
        del r["plan_version"]
        assert any("`plan_version`" in e for e in _errors("receipt", r))

    def test_unknown_status_lists_available(self) -> None:
        r = _receipt()
        r["status"] = "done"
        errs = _errors("receipt", r)
        assert any(
            "Unknown status `done`" in e and "budget-limited" in e for e in errs
        )

    def test_final_text_flag_must_be_bool(self) -> None:
        r = _receipt()
        r["bounded_receipt_projection"]["final_text_non_empty"] = "yes"
        assert any("boolean" in e for e in _errors("receipt", r))


class TestManualAnchorTightening:
    """改版批次（J-3 收緊）：manual-anchor 逃生口須附錨證；delivered 路徑行為不變。"""

    def test_manual_anchor_zero_hits_fails(self) -> None:
        r = _receipt()
        r["delivery"]["verdict"] = "manual-anchor"
        r["delivery"]["anchor_hits"] = []
        errs = _errors("receipt", r)
        assert any(
            "manual-anchor verdict requires at least one anchor hit" in e for e in errs
        )

    def test_manual_anchor_missing_anchor_hits_fails(self) -> None:
        r = _receipt()
        r["delivery"]["verdict"] = "manual-anchor"
        del r["delivery"]["anchor_hits"]
        errs = _errors("receipt", r)
        assert any(
            "manual-anchor verdict requires at least one anchor hit" in e for e in errs
        )

    def test_manual_anchor_with_one_hit_passes(self) -> None:
        r = _receipt()
        r["delivery"]["verdict"] = "manual-anchor"
        r["delivery"]["anchor_hits"] = ["JUDGE-VERDICT"]
        assert _errors("receipt", r) == []

    def test_delivered_path_unaffected(self) -> None:
        """delivered 不走 manual-anchor 錨證閘（行為不變）。"""
        r = _receipt()
        r["delivery"]["anchor_hits"] = []
        errs = _errors("receipt", r)
        assert not any("manual-anchor verdict requires" in e for e in errs)

    def test_gate_bound_to_completed_status(self) -> None:
        """閘綁 status=completed——非 completed 不觸發錨證要求。"""
        r = _receipt()
        r["status"] = "failed"
        r["delivery"]["verdict"] = "manual-anchor"
        r["delivery"]["anchor_hits"] = []
        errs = _errors("receipt", r)
        assert not any("manual-anchor verdict requires" in e for e in errs)


class TestPlanHashSourceField:
    """改版批次：receipt.plan_hash_source 選填欄（muse N-2——receipt 只存 hash 不存源）。"""

    def test_field_is_optional_machine_invariant(self) -> None:
        fields = {f.name: f for f in _mod.ARTIFACTS["receipt"].fields}
        f = fields["plan_hash_source"]
        assert f.kind == "machine-invariant"
        assert f.required_at == "never"  # 選填不進 required 集（同 receipt_sink 慣例）

    def test_absent_still_valid(self) -> None:
        r = _receipt()
        assert "plan_hash_source" not in r
        assert _errors("receipt", r) == []

    def test_present_valid(self) -> None:
        r = _receipt()
        r["plan_hash_source"] = ".agent-tmp/air-135.1/mini-batch/AIR-135.7/arc-plan.md"
        assert _errors("receipt", r) == []

    def test_blank_fails(self) -> None:
        r = _receipt()
        r["plan_hash_source"] = "   "
        errs = _errors("receipt", r)
        assert any("`plan_hash_source`" in e and "blank" in e for e in errs)


# ---------------------------------------------------------------------------
# 檔案解析＋CLI
# ---------------------------------------------------------------------------


class TestFileAndCli:
    def test_parse_markdown_json_block(self, tmp_path: Path) -> None:
        p = tmp_path / "slice.md"
        p.write_text(
            "# DispatchSlice\n\n```json\n"
            + json.dumps(_slice(), ensure_ascii=False)
            + "\n```\n",
            encoding="utf-8",
        )
        data = _mod.parse_artifact_file(p, "dispatch-slice")
        assert data["slice_id"] == "AIR-94#W1-slice"

    def test_parse_json_file(self, tmp_path: Path) -> None:
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(_plan_with_valid_hash()), encoding="utf-8")
        assert _mod.parse_artifact_file(p, "arc-plan")["version"] == 1

    def test_parse_missing_block_fails(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.md"
        p.write_text("# no json", encoding="utf-8")
        with pytest.raises(_mod.ArcSpecError):
            _mod.parse_artifact_file(p, "arc-plan")

    def test_parse_schema_marker_mismatch(self, tmp_path: Path) -> None:
        p = tmp_path / "x.md"
        p.write_text("```json\n{\"schema\": \"arc-plan/9\"}\n```", encoding="utf-8")
        with pytest.raises(_mod.ArcSpecError) as ei:
            _mod.parse_artifact_file(p, "arc-plan")
        assert "Available schema markers" in str(ei.value)

    def test_cli_validate_valid_exit_0(self, tmp_path: Path) -> None:
        p = tmp_path / "s.md"
        p.write_text(
            "```json\n" + json.dumps(_slice(), ensure_ascii=False) + "\n```",
            encoding="utf-8",
        )
        assert (
            _mod.main(
                ["validate", "--kind", "dispatch-slice", "--stage", "dispatch", str(p)]
            )
            == 0
        )

    def test_cli_validate_missing_field_exit_2_with_message(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        data = _slice(with_resolver=False)
        p = tmp_path / "s.md"
        p.write_text(
            "```json\n" + json.dumps(data, ensure_ascii=False) + "\n```",
            encoding="utf-8",
        )
        code = _mod.main(
            ["validate", "--kind", "dispatch-slice", "--stage", "dispatch", str(p)]
        )
        assert code == 2
        assert "family" in capsys.readouterr().err

    def test_cli_schema_lists_annotations(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert _mod.main(["schema", "--kind", "dispatch-slice"]) == 0
        out = capsys.readouterr().out
        assert "machine-invariant" in out and "llm-guidance" in out
        assert "prompt_material" in out and "sink" in out

    def test_cli_unknown_kind_exit_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _mod.main(["validate", "--kind", "foo", "/dev/null"]) == 2
        assert "Available kinds" in capsys.readouterr().err
