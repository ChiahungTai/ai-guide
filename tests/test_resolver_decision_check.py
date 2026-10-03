"""resolver_decision_check 契約測試（AIR-245——decision validator）。

釘住的 invariant（codex §C 設計權威＝verdict-codex.md §C；AIR-240
authority 邊界）：
- invariant 1：on_unavailable=delay＋preferred family live-unavailable
  ⇒ selected 必空（zero dispatch）。
- invariant 2：selected family ∈ fallback_families 顯式集合（preferred
  除外）∧ 已 qualified ∧ live AvailabilitySnapshot=fresh＋available——
  stale/unknown/row 缺席（＝unknown）永不可 selected；preferred 同樣受
  live available 管轄。
- invariant 3：selected 以 advisory planning rows 當 eligibility ⇒ 違規
  （advisory 證據不得偷升 live authority）——planning rows 全 stale/
  unknown 為指定 case；plan 表達 explicit fallback_families 本身不違規。
- invariant 4：hard requirement 不得被 fallback 降低——dispatched_contract
  與 contract 任一 hard 欄相異即違規。
- admissible 語義（evaluator-not-router）：多合法 soft-ranked candidate
  並存——選其中任一皆 admissible，checker 不比 winner、無排序建議。
- fail-loud：schema 不符／必填缺席／枚舉外值／檔案缺 → exit 2。
"""

import copy
import json
from pathlib import Path

from conftest import REPO_ROOT, load_module

check = load_module("scripts/resolver_decision_check.py")

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "resolver"


def _contract() -> dict:
    return {
        "role": "implement",
        "authority": "apply",
        "judgment_floor": "execution",
        "qualifications": ["implement_from_accepted_ep"],
        "capabilities": [],
        "surface": "glm-family",
    }


def _selected(family: str, source: str = "live_availability") -> dict:
    return {
        "family": family,
        "model": "GLM-5.3-Flash",
        "effort": "high",
        "binding": "bridge-glm-5.3-flash",
        "eligibility_source": source,
    }


def _base() -> dict:
    """合法 fallback 決策（glm ∈ 顯式集合＋qualified＋live fresh available）。"""
    return {
        "schema": "resolver-decision/1",
        "decision_id": "synthetic",
        "contract": _contract(),
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
        "selected": _selected("glm"),
        "dispatched_contract": _contract(),
    }


def _write(tmp_path: Path, data: dict, name: str = "decision.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _run(tmp_path: Path, data: dict, name: str = "decision.json") -> tuple[int, str]:
    path = _write(tmp_path, data, name)
    code = check.main(["validate", str(path)])
    return code, path.name


# ---- invariant 1：delay＋preferred live-unavailable ⇒ zero dispatch ----


class TestInvariant1:
    def test_delay_preferred_unavailable_zero_dispatch_admissible(self) -> None:
        code = check.main(
            ["validate", str(FIXTURES / "delay-zero-dispatch.json")]
        )
        assert code == 0

    def test_delay_with_selected_when_preferred_unavailable_violates(
        self, tmp_path
    ) -> None:
        data = copy.deepcopy(_base())
        data["policy"] = {
            "preferred_family": "muse",
            "on_unavailable": "delay",
            "fallback_families": [],
        }
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_delay_preferred_available_select_preferred_admissible(
        self, tmp_path
    ) -> None:
        data = copy.deepcopy(_base())
        data["policy"] = {
            "preferred_family": "muse",
            "on_unavailable": "delay",
            "fallback_families": [],
        }
        data["selected"] = _selected("muse")
        data["live_availability"] = [
            {"family": "muse", "freshness": "fresh", "state": "available"},
            {"family": "glm", "freshness": "fresh", "state": "available"},
        ]
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 0


# ---- invariant 2：explicit set ∧ qualified ∧ live fresh available ----


class TestInvariant2:
    def test_fallback_stale_selected_rejected(self) -> None:
        code = check.main(
            ["validate", str(FIXTURES / "fallback-stale-selected.json")]
        )
        assert code == 2

    def test_fallback_stale_selected_message_names_stale_unknown(
        self, capsys
    ) -> None:
        check.main(["validate", str(FIXTURES / "fallback-stale-selected.json")])
        err = capsys.readouterr().err
        assert "stale/unknown 不可 dispatch" in err
        assert "invariant-2" in err

    def test_fallback_outside_explicit_set_rejected(self) -> None:
        code = check.main(
            ["validate", str(FIXTURES / "fallback-outside-explicit-set.json")]
        )
        assert code == 2

    def test_fallback_outside_explicit_set_message_names_set(
        self, capsys
    ) -> None:
        check.main(
            ["validate", str(FIXTURES / "fallback-outside-explicit-set.json")]
        )
        err = capsys.readouterr().err
        assert "不在 fallback_families" in err

    def test_fallback_live_available_admissible(self) -> None:
        code = check.main(
            ["validate", str(FIXTURES / "fallback-live-available.json")]
        )
        assert code == 0

    def test_selected_unknown_state_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["live_availability"][1]["state"] = "unknown"
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_selected_live_row_missing_is_unknown_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["live_availability"] = [
            {"family": "muse", "freshness": "fresh", "state": "unavailable"},
        ]
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_selected_unqualified_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["qualified_families"] = ["muse"]
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_preferred_selected_but_live_stale_rejected(self, tmp_path) -> None:
        """preferred 同樣受 live available 管轄（fallback policy 下選
        preferred、live row stale → invariant-2）。"""
        data = copy.deepcopy(_base())
        data["selected"] = _selected("muse")
        data["live_availability"][0] = {
            "family": "muse",
            "freshness": "stale",
            "state": "available",
        }
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2


# ---- invariant 3：advisory planning rows 不得偷升 live authority ----


class TestInvariant3:
    def test_planning_stale_eligibility_rejected(self) -> None:
        """codex §C 指定 case：plan 可表達 explicit fallback；以 stale
        planning rows 當 eligibility 的 proposed dispatch 判 fail。"""
        code = check.main(
            [
                "validate",
                str(FIXTURES / "fallback-planning-stale-eligibility.json"),
            ]
        )
        assert code == 2

    def test_planning_stale_eligibility_message(self, capsys) -> None:
        check.main(
            [
                "validate",
                str(FIXTURES / "fallback-planning-stale-eligibility.json"),
            ]
        )
        err = capsys.readouterr().err
        assert "invariant-3" in err
        assert "偷升" in err
        # fallback intent 本身（explicit fallback_families）不得被標記
        assert "fallback_families 顯式集合" not in err

    def test_same_fixture_with_live_eligibility_admissible(
        self, tmp_path
    ) -> None:
        """同一情境改申報 live authority 為 eligibility 來源 → admissible
        （checker 管的是 authority basis，非 fallback intent）。"""
        data = json.loads(
            (
                FIXTURES / "fallback-planning-stale-eligibility.json"
            ).read_text(encoding="utf-8")
        )
        data["selected"]["eligibility_source"] = "live_availability"
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 0

    def test_plan_expressing_explicit_fallback_with_zero_dispatch_admissible(
        self, tmp_path
    ) -> None:
        """plan 表達 explicit fallback 本身不違規——zero dispatch 即
        admissible（invariant 3 只打以 planning rows 當 eligibility 的
        selected，不打 fallback intent）。"""
        data = copy.deepcopy(_base())
        data["planning_rows"] = [
            {"family": "muse", "freshness": "stale", "state": "unknown"},
            {"family": "glm", "freshness": "stale", "state": "unknown"},
        ]
        data["selected"] = None
        del data["dispatched_contract"]
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 0

    def test_all_stale_planning_rows_cited_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["planning_rows"] = [
            {"family": "muse", "freshness": "stale", "state": "unknown"},
            {"family": "glm", "freshness": "stale", "state": "available"},
        ]
        data["selected"] = _selected("glm", source="entitlement_planning")
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2


# ---- invariant 4：hard requirement 不得被 fallback 降低 ----


class TestInvariant4:
    def test_contract_judgment_floor_lowered_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["contract"]["judgment_floor"] = "decision"
        # dispatched 仍 execution——decision → execution＝降級
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_contract_qualifications_dropped_rejected(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["dispatched_contract"]["qualifications"] = []
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2

    def test_contract_identical_admissible(self) -> None:
        code = check.main(
            ["validate", str(FIXTURES / "fallback-live-available.json")]
        )
        assert code == 0

    def test_selected_without_dispatched_contract_input_error(
        self, tmp_path
    ) -> None:
        data = copy.deepcopy(_base())
        del data["dispatched_contract"]
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 2


# ---- admissible 語義（evaluator-not-router：不比 winner）----


class TestAdmissibleSemantics:
    def test_multi_candidate_any_winner_admissible(self, tmp_path) -> None:
        """多合法 soft-ranked candidate 並存：選其中任一皆 admissible。"""
        path = FIXTURES / "multi-candidate-admissible.json"
        assert check.main(["validate", str(path)]) == 0
        data = json.loads(path.read_text(encoding="utf-8"))
        data["selected"] = _selected("muse")
        code = check.main(["validate", str(_write(tmp_path, data))])
        assert code == 0

    def test_admissible_output_declares_no_winner_comparison(
        self, capsys
    ) -> None:
        check.main(
            ["validate", str(FIXTURES / "multi-candidate-admissible.json")]
        )
        out = capsys.readouterr().out
        assert "ADMISSIBLE" in out
        assert "不比 winner" in out


# ---- fail-loud 輸入驗證（exit 2，沿 arc_spec 風格）----


class TestFailLoudInput:
    def test_missing_file_exit_2(self) -> None:
        assert check.main(["validate", "/nonexistent/decision.json"]) == 2

    def test_malformed_json_exit_2(self, tmp_path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        assert check.main(["validate", str(path)]) == 2

    def test_wrong_schema_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["schema"] = "resolver-decision/9"
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_missing_policy_block_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        del data["policy"]
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_bad_on_unavailable_enum_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["policy"]["on_unavailable"] = "retry"
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_delay_with_nonempty_fallback_set_exit_2(self, tmp_path) -> None:
        """鏡射 arc_spec temporal 閉集：delay 禁與 fallback_families 並存。"""
        data = copy.deepcopy(_base())
        data["policy"]["on_unavailable"] = "delay"
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_fallback_with_empty_set_exit_2(self, tmp_path) -> None:
        """explicit-only：fallback 須帶非空顯式集合。"""
        data = copy.deepcopy(_base())
        data["policy"]["fallback_families"] = []
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_fallback_set_contains_preferred_exit_2(self, tmp_path) -> None:
        """相異家族才叫 fallback——fallback_families 禁含 preferred。"""
        data = copy.deepcopy(_base())
        data["policy"]["fallback_families"] = ["glm", "muse"]
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_selected_without_eligibility_source_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        del data["selected"]["eligibility_source"]
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_bad_eligibility_source_enum_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["selected"]["eligibility_source"] = "gut_feeling"
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_duplicate_live_rows_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["live_availability"].append(
            {"family": "glm", "freshness": "stale", "state": "unknown"}
        )
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2

    def test_planning_row_bad_freshness_enum_exit_2(self, tmp_path) -> None:
        data = copy.deepcopy(_base())
        data["planning_rows"][0]["freshness"] = "ancient"
        assert check.main(["validate", str(_write(tmp_path, data))]) == 2
