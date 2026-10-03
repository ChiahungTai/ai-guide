"""resolver_behavior_probe 契約測試（AIR-245——behavior lane 後半）。

釘住的契約（codex §C；工單 §2.B）：
- 鏈形：structured proposed decision artifact → resolver_decision_check
  （單一源）→ verdict；probe 禁自刻第二份 invariant 實作。
- INCONCLUSIVE 契約：provider/runtime failure（explicit marker／artifact
  缺席／malformed／結構不合法）記 INCONCLUSIVE 如實上報——禁
  retry-to-green（probe 無任何重試路徑）。
- exit：0＝所有完成樣本 admissible；1＝≥1 完成樣本違反 hard invariant；
  2＝corpus／參數不合法。
"""

import copy
import json
from pathlib import Path

from conftest import REPO_ROOT, load_module

probe = load_module("scripts/resolver_behavior_probe.py")
check = load_module("scripts/resolver_decision_check.py")

CORPUS = REPO_ROOT / "tests" / "fixtures" / "resolver-behavior"


def _admissible_decision() -> dict:
    return {
        "schema": "resolver-decision/1",
        "decision_id": "probe-synthetic",
        "contract": {
            "role": "implement",
            "authority": "apply",
            "judgment_floor": "execution",
            "qualifications": ["implement_from_accepted_ep"],
            "capabilities": [],
            "surface": "glm-family",
            "escalation": "invariant-or-public-boundary→decision-escalation",
            "independence": None,
        },
        "dispatched_contract": {
            "role": "implement",
            "authority": "apply",
            "judgment_floor": "execution",
            "qualifications": ["implement_from_accepted_ep"],
            "capabilities": [],
            "surface": "glm-family",
            "escalation": "invariant-or-public-boundary→decision-escalation",
            "independence": None,
        },
        "policy": {
            "preferred_family": "muse",
            "on_unavailable": "fallback",
            "fallback_families": ["glm"],
        },
        "planning_rows": [
            {"family": "muse", "freshness": "fresh", "state": "unavailable"},
            {"family": "glm", "freshness": "fresh", "state": "available"},
        ],
        "live_availability": [
            {"family": "muse", "freshness": "fresh", "state": "unavailable"},
            {"family": "glm", "freshness": "fresh", "state": "available"},
        ],
        "qualified_families": ["muse", "glm"],
        "selected": {
            "family": "glm",
            "model": "GLM-5.3-Flash",
            "effort": "high",
            "binding": "bridge-glm-5.3-flash",
            "eligibility_source": "live_availability",
        },
    }


def _make_corpus(tmp_path: Path, responses: dict[str, list[object]]) -> Path:
    """responses：{case_dir_name: [rep 內容（dict）或 None（缺席）]}。"""
    corpus = tmp_path / "corpus"
    for case_name, reps in responses.items():
        resp_dir = corpus / case_name / "responses"
        resp_dir.mkdir(parents=True)
        case = {
            "schema": "resolver-behavior-case/1",
            "case_id": case_name,
            "description": "synthetic",
            "scenario": {},
        }
        (corpus / case_name / "case.json").write_text(
            json.dumps(case, ensure_ascii=False), encoding="utf-8"
        )
        for i, rep in enumerate(reps, start=1):
            if rep is None:
                continue
            (resp_dir / f"rep-{i}.json").write_text(
                json.dumps(rep, ensure_ascii=False), encoding="utf-8"
            )
    return corpus


class TestDraftCorpus:
    def test_draft_corpus_completed_samples_all_admissible(self, capsys) -> None:
        code = probe.main(["--corpus", str(CORPUS), "--reps", "5"])
        assert code == 0
        out = capsys.readouterr().out
        assert "completed_admissible=15" in out
        assert "violation=0" in out
        assert "inconclusive=5" in out

    def test_draft_corpus_inconclusive_reported_as_is(self, capsys) -> None:
        probe.main(["--corpus", str(CORPUS), "--reps", "5"])
        out = capsys.readouterr().out
        assert "INCONCLUSIVE" in out
        assert "禁 retry-to-green" in out
        # case-04 的 1308 failure reason 須逐字帶出
        assert "1308" in out

    def test_draft_corpus_multi_candidate_no_winner_comparison(
        self, capsys
    ) -> None:
        """case-03 reps 交替選 glm／muse——每 rep 各自判 admissible，
        probe 不收斂到單一 winner。"""
        probe.main(["--corpus", str(CORPUS), "--reps", "5"])
        out = capsys.readouterr().out
        rep_lines = [
            line
            for line in out.splitlines()
            if line.startswith(
                "[case-03-multi-candidate-admissible-set] rep-"
            )
        ]
        assert len(rep_lines) == 5
        assert all("ADMISSIBLE" in line for line in rep_lines)
        assert not any("VIOLATION" in line for line in rep_lines)


class TestVerdicts:
    def test_violation_sample_exit_1(self, tmp_path, capsys) -> None:
        bad = copy.deepcopy(_admissible_decision())
        bad["live_availability"][1]["freshness"] = "stale"
        corpus = _make_corpus(
            tmp_path,
            {"case-x": [bad, _admissible_decision()]},
        )
        code = probe.main(["--corpus", str(corpus), "--reps", "2"])
        assert code == 1
        out = capsys.readouterr().out
        assert "VIOLATION" in out
        assert "stale/unknown 不可 dispatch" in out

    def test_explicit_inconclusive_marker_counted(self, tmp_path) -> None:
        corpus = _make_corpus(
            tmp_path,
            {
                "case-x": [
                    {"status": "inconclusive", "reason": "GLM 1308 usage limit"},
                    _admissible_decision(),
                ]
            },
        )
        code = probe.main(["--corpus", str(corpus), "--reps", "2"])
        assert code == 0

    def test_missing_rep_is_inconclusive(self, tmp_path, capsys) -> None:
        corpus = _make_corpus(tmp_path, {"case-x": [_admissible_decision()]})
        code = probe.main(["--corpus", str(corpus), "--reps", "5"])
        assert code == 0
        out = capsys.readouterr().out
        assert "rep artifact 缺席" in out

    def test_malformed_rep_is_inconclusive(self, tmp_path, capsys) -> None:
        corpus = tmp_path / "corpus" / "case-x" / "responses"
        corpus.mkdir(parents=True)
        case = corpus.parent / "case.json"
        case.write_text(
            json.dumps(
                {
                    "schema": "resolver-behavior-case/1",
                    "case_id": "case-x",
                    "description": "synthetic",
                    "scenario": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (corpus / "rep-1.json").write_text("{not json", encoding="utf-8")
        code = probe.main(["--corpus", str(corpus.parent.parent), "--reps", "1"])
        # F1（R1）新語義：全 INCONCLUSIVE corpus＝零完成 admissible 樣本 →
        # exit 3（不可宣稱 pass）；非 1 即證 malformed 未被誤判 violation
        assert code == 3
        out = capsys.readouterr().out
        assert "INCONCLUSIVE" in out

    def test_schema_invalid_decision_is_inconclusive_not_violation(
        self, tmp_path
    ) -> None:
        """結構不合法的 proposed decision＝無法判讀（INCONCLUSIVE），不是
        invariant violation——checker 是違規判定唯一源。"""
        broken = {"schema": "resolver-decision/1", "decision_id": "x"}
        corpus = _make_corpus(tmp_path, {"case-x": [broken]})
        code = probe.main(["--corpus", str(corpus), "--reps", "1"])
        # F1（R1）新語義：零完成 admissible 樣本 → exit 3；非 1 即證結構
        # 不合法未被誤判 violation（checker 是違規判定唯一源）
        assert code == 3

    def test_all_inconclusive_corpus_zero_admissible_exits_3(
        self, tmp_path, capsys
    ) -> None:
        """F1（R1）：completed_admissible=0 且 artifacts>0 → 顯性非零
        exit（3）——全 INCONCLUSIVE 不可宣稱 pass。"""
        corpus = _make_corpus(
            tmp_path,
            {
                "case-x": [
                    {"status": "inconclusive", "reason": "GLM 1308 usage limit"},
                    {"status": "inconclusive", "reason": "muse 429 at capacity"},
                ]
            },
        )
        code = probe.main(["--corpus", str(corpus), "--reps", "2"])
        assert code == 3
        out = capsys.readouterr().out
        assert "completed_admissible=0" in out


class TestFailLoud:
    def test_missing_corpus_exit_2(self) -> None:
        assert (
            probe.main(["--corpus", "/nonexistent/corpus", "--reps", "5"]) == 2
        )

    def test_reps_below_one_exit_2(self) -> None:
        assert probe.main(["--corpus", str(CORPUS), "--reps", "0"]) == 2

    def test_corpus_without_cases_exit_2(self, tmp_path) -> None:
        empty = tmp_path / "corpus"
        empty.mkdir()
        assert probe.main(["--corpus", str(empty), "--reps", "5"]) == 2

    def test_malformed_case_json_exit_2(self, tmp_path) -> None:
        corpus = tmp_path / "corpus" / "case-x"
        corpus.mkdir(parents=True)
        (corpus / "case.json").write_text("{not json", encoding="utf-8")
        assert probe.main(["--corpus", str(corpus.parent), "--reps", "1"]) == 2

    def test_zero_artifacts_across_corpus_exit_2(self, tmp_path) -> None:
        corpus = _make_corpus(tmp_path, {"case-x": [None, None]})
        assert probe.main(["--corpus", str(corpus), "--reps", "2"]) == 2


class TestCheckerSingleSource:
    def test_probe_reuses_checker_module_not_own_invariants(self) -> None:
        """probe 餵 checker 單一源——probe 模組禁自刻 invariant 邏輯
        （以同 input 跑兩模組、admissible 判定一致為代理驗證）。"""
        decision = _admissible_decision()
        input_errors, violations = check.validate_decision(decision)
        assert input_errors == []
        assert violations == []
        # probe 分類同一份 input → admissible（非 violation/inconclusive）
        cls, _ = probe._classify_decision(decision)
        assert cls == "admissible"
