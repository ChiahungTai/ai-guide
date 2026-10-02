"""arc_goal_compile 契約測試（AIR-135.1.1 C5b goal compiler core）。

釘住的 invariant（卡面已決策勿重辯）：
- 純 compiler：無 process side effects；同卡同 baseline 兩跑 byte-equal（決定性）。
- 集合不變式四條為核心 oracle：verifier-bearing/已勾 AC == exactly-once
  predicates、no-verifier AC == exactly-once judgment_required、聯集=全部、
  交集=空——judgment_required 靜默丟失是最危險失效形，專項斷言。
- 不合 grammar fail-closed 為 judgment_required；malformed／歧義 fail-loud；
  duplicate ac_id fail-loud；已勾 AC 須帶 baseline 身份。
- roundtrip＝artifact serialize→parse→canonical serialize byte-equal
  （不做 card roundtrip——投影本意 lossy-on-prose）。
"""

import json
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

gc = load_module("scripts/arc_goal_compile.py")
spec = load_module("scripts/arc_spec.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "arc_goal"
GOLDEN_CARD = FIXTURES / "air-135.4.md"
MIXED_CARD = FIXTURES / "mixed-card.md"
BASELINE = "1a140ef0"
GOLDEN_SOURCE = "backlog/tasks/air-135.4 - Code-Lens——整合-code-tours＋pr-lens-的-human-code-viewport.md"


def _compile(path: Path, baseline: str | None = BASELINE) -> dict:
    return gc.compile_card(
        path.read_text(encoding="utf-8"),
        source_card=path.name,
        baseline=baseline,
    )


# ---------------------------------------------------------------------------
# golden：AIR-135.4 真實卡（六條 AC 全 prose 無 grammar 形 → 全 judgment_required）
# ---------------------------------------------------------------------------


class TestGoldenAir1354:
    def test_all_six_acs_classified_judgment_required(self) -> None:
        contract = _compile(GOLDEN_CARD)
        assert contract["schema"] == "acceptance-contract/1"
        assert contract["card_id"] == "AIR-135.4"
        assert contract["ac_ids"] == ["1", "2", "3", "4", "5", "6"]
        assert contract["predicates"] == []
        assert [j["ac_id"] for j in contract["judgment_required"]] == [
            "1", "2", "3", "4", "5", "6",
        ]
        assert all(
            j["reason"] == "no-explicit-verifier"
            for j in contract["judgment_required"]
        )
        assert contract["card_baseline"] == BASELINE

    def test_ac6_code_span_without_arrow_is_not_verifier(self) -> None:
        """AC#6 帶 `.html` code span 但無 arrow——code span 單獨存在不構成
        verifier（禁猜 prose 的回歸錨）。"""
        contract = _compile(GOLDEN_CARD)
        assert "6" in {j["ac_id"] for j in contract["judgment_required"]}

    def test_summary_line(self) -> None:
        contract = _compile(GOLDEN_CARD)
        assert (
            gc.summary_line(contract)
            == "predicates: 0／judgment-required: 6（1, 2, 3, 4, 5, 6）"
        )


# ---------------------------------------------------------------------------
# mixed 分類（合成卡：四類 AC 各一）
# ---------------------------------------------------------------------------


class TestMixedClassification:
    @pytest.fixture()
    def contract(self) -> dict:
        return _compile(MIXED_CARD)

    def test_predicate_from_explicit_verifier(self, contract: dict) -> None:
        p2 = next(p for p in contract["predicates"] if p["ac_id"] == "2")
        assert p2["kind"] == "command_expected"
        assert p2["verifier"] == "uv run pytest tests/test_demo.py -q"
        assert p2["expected"] == "exit 0"
        assert p2["satisfied"] is False
        assert p2["satisfied_at_baseline"] is None

    def test_checked_without_verifier_is_satisfied_predicate(
        self, contract: dict
    ) -> None:
        p1 = next(p for p in contract["predicates"] if p["ac_id"] == "1")
        assert p1["satisfied"] is True
        assert p1["kind"] is None
        assert p1["verifier"] is None
        assert p1["satisfied_at_baseline"] == BASELINE

    def test_checked_with_verifier_keeps_verifier(self, contract: dict) -> None:
        p4 = next(p for p in contract["predicates"] if p["ac_id"] == "4")
        assert p4["satisfied"] is True
        assert p4["kind"] == "command_expected"
        assert p4["verifier"] == 'rg "foo" bar.py'
        assert p4["satisfied_at_baseline"] == BASELINE

    def test_prose_goes_to_judgment_required(self, contract: dict) -> None:
        assert [j["ac_id"] for j in contract["judgment_required"]] == ["3"]
        assert contract["judgment_required"][0]["reason"] == "no-explicit-verifier"

    def test_summary_line_mixed(self, contract: dict) -> None:
        assert gc.summary_line(contract) == "predicates: 3／judgment-required: 1（3）"


# ---------------------------------------------------------------------------
# 集合不變式——judgment_required 靜默丟失即 FAIL（最危險失效形的專項斷言）
# ---------------------------------------------------------------------------


class TestSetInvariants:
    def test_judgment_required_loss_fails(self) -> None:
        """丟失任一 no-verifier AC 即 FAIL——exactly-once＋聯集=全部。"""
        contract = _compile(MIXED_CARD)
        no_verifier_ids = {"3"}
        jud_ids = {j["ac_id"] for j in contract["judgment_required"]}
        assert jud_ids == no_verifier_ids, "judgment_required 靜默丟失"
        assert len(contract["judgment_required"]) == len(no_verifier_ids), (
            "judgment_required exactly-once 違約"
        )
        pred_ids = {p["ac_id"] for p in contract["predicates"]}
        assert pred_ids | jud_ids == set(contract["ac_ids"]), "聯集≠全部 AC"
        assert not pred_ids & jud_ids, "交集非空"

    def test_golden_card_union_covers_all(self) -> None:
        contract = _compile(GOLDEN_CARD)
        jud_ids = {j["ac_id"] for j in contract["judgment_required"]}
        assert jud_ids | set() == set(contract["ac_ids"])

    def test_plan_side_rejects_dropped_judgment_entry(self) -> None:
        """arc_spec validate 對丟失 judgment_required 的 plan 也 FAIL
        （無卡環境的機驗面——ac_ids 承載輸入對照）。"""
        contract = _compile(MIXED_CARD)
        broken = json.loads(json.dumps(contract))
        broken["judgment_required"] = []
        errors = spec.validate("arc-plan", _plan_with(broken), stage="compile")
        assert any("missing from acceptance_contract" in e for e in errors)


def _plan_with(contract: dict) -> dict:
    """合法 ArcPlan 殼＋嵌 contract（plan_hash 重算——嵌塊入 hash 覆蓋面）。"""
    plan = {
        "schema": "arc-plan/1",
        "card_id": contract["card_id"],
        "card_baseline": BASELINE,
        "version": 1,
        "supersedes": None,
        "plan_hash": "",
        "work_units": [
            {
                "unit_id": f"{contract['card_id']}#W1",
                "title": "compiler core 驗證殼",
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
        "plan_changes": [],
        "acceptance_contract": contract,
    }
    plan["plan_hash"] = spec.plan_content_hash(plan)
    return plan


# ---------------------------------------------------------------------------
# 負例：duplicate ac_id／malformed verifier／無 AC 段／缺 baseline
# ---------------------------------------------------------------------------


class TestFailLoud:
    def test_duplicate_ac_id(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="Duplicate AC id `#2`"):
            _compile(FIXTURES / "duplicate-ac-id.md")

    def test_malformed_verifier_trailing_arrow(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="malformed verifier"):
            _compile(FIXTURES / "malformed-verifier.md")

    def test_malformed_verifier_empty_command(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="malformed verifier"):
            _compile(FIXTURES / "malformed-empty-command.md")

    def test_ambiguous_multiple_verifiers(self) -> None:
        text = (
            "---\nid: AIR-TEST-AMBI\n---\n\n## Acceptance Criteria\n"
            "- [ ] 兩個驗證式 `a` → 1 與 `b` → 2\n"
        )
        with pytest.raises(gc.GoalCompileError, match="歧義"):
            gc.compile_card(text, source_card="inline")

    def test_mixed_good_and_malformed(self) -> None:
        text = (
            "---\nid: AIR-TEST-MIXEDSIG\n---\n\n## Acceptance Criteria\n"
            "- [ ] `a` → 1\n  `b` →\n"
        )
        with pytest.raises(gc.GoalCompileError, match="歧義|malformed"):
            gc.compile_card(text, source_card="inline")

    def test_no_ac_section(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="Acceptance Criteria"):
            _compile(FIXTURES / "no-ac-section.md")

    def test_checked_ac_requires_baseline(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="baseline"):
            gc.compile_card(
                MIXED_CARD.read_text(encoding="utf-8"),
                source_card=MIXED_CARD.name,
                baseline=None,
            )

    def test_bad_baseline_format(self) -> None:
        with pytest.raises(gc.GoalCompileError, match="hex 7-40"):
            gc.compile_card(
                MIXED_CARD.read_text(encoding="utf-8"),
                source_card=MIXED_CARD.name,
                baseline="zzz",
            )

    def test_prose_arrow_without_code_span_is_judgment_not_error(self) -> None:
        """純文字箭頭（arrow 前是 prose）不構成 verifier 也不算 malformed——
        禁猜 prose 的正向回歸錨（air-78 實卡形）。"""
        text = (
            "---\nid: AIR-TEST-PROSEARROW\n---\n\n## Acceptance Criteria\n"
            "- [ ] 三 invariant 機械驗證：full→`--model X`、lite→`--model Y`\n"
        )
        contract = gc.compile_card(text, source_card="inline")
        assert contract["predicates"] == []
        assert [j["ac_id"] for j in contract["judgment_required"]] == ["1"]


# ---------------------------------------------------------------------------
# 決定性＋roundtrip
# ---------------------------------------------------------------------------


class TestDeterminismAndRoundtrip:
    def test_same_card_two_runs_byte_equal(self) -> None:
        rendered_a = gc.render_markdown(_compile(GOLDEN_CARD))
        rendered_b = gc.render_markdown(_compile(GOLDEN_CARD))
        assert rendered_a == rendered_b
        assert rendered_a.encode("utf-8") == rendered_b.encode("utf-8")

    def test_mixed_card_two_runs_byte_equal(self) -> None:
        rendered_a = gc.render_markdown(_compile(MIXED_CARD))
        rendered_b = gc.render_markdown(_compile(MIXED_CARD))
        assert rendered_a == rendered_b

    def test_roundtrip_canonical_byte_equal(self) -> None:
        contract = _compile(MIXED_CARD)
        s1 = gc.canonical_json(contract)
        parsed = json.loads(s1)
        s2 = gc.canonical_json(parsed)
        assert s1 == s2

    def test_contract_validates_against_arc_plan_schema(self) -> None:
        """compiler 產出可直接嵌 ArcPlan 且過 schema 深檢（兩階段組裝的接縫）。"""
        for card in (GOLDEN_CARD, MIXED_CARD):
            plan = _plan_with(_compile(card))
            assert spec.validate("arc-plan", plan, stage="compile") == []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_help_exit_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as excinfo:
            gc.main(["--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "verifier" in out
        assert "judgment_required" in out or "judgment-required" in out

    def test_real_card_run(self, tmp_path: Path) -> None:
        out_file = tmp_path / "contract.md"
        rc = gc.main([str(GOLDEN_CARD), "--baseline", BASELINE, "--out", str(out_file)])
        assert rc == 0
        rendered = out_file.read_text(encoding="utf-8")
        assert "```json" in rendered
        payload = json.loads(rendered.split("```json", 1)[1].split("```", 1)[0])
        assert payload["card_id"] == "AIR-135.4"
        assert payload["predicates"] == []

    def test_exit_2_on_no_ac_section(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = gc.main([str(FIXTURES / "no-ac-section.md")])
        assert rc == 2
        assert "Acceptance Criteria" in capsys.readouterr().err

    def test_exit_2_on_missing_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        rc = gc.main([str(FIXTURES / "does-not-exist.md")])
        assert rc == 2
        assert "not found" in capsys.readouterr().err
