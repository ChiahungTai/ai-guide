#!/usr/bin/env python3
"""resolver_decision_check——resolver decision invariant checker（AIR-245）。

decision validator：輸入一份 proposed DispatchPlan/Trace（structured JSON，
schema `resolver-decision/1`），只驗 hard invariants 四條——**禁 RoutingPolicy
soft ranking、禁第二 resolver**（evaluator-not-router 同構）：selected 過
hard gate 即 admissible；多合法 candidate 並存時不比 winner、無排序建議欄位
（admissible set 語義）。判斷腿（qualification hard filter 的執行、soft
ranking、candidate 產生）仍歸 model-routing resolver instruction protocol。

hard invariants（codex §C 設計權威＝.agent-tmp/air-238-followups/
verdict-codex.md §C；AIR-240 authority 邊界）：
- invariant 1：on_unavailable=delay＋preferred family live-unavailable
  ⇒ selected 必空（zero dispatch）。
- invariant 2：selected family ∈ fallback_families 顯式集合（preferred
  除外）∧ 已 qualified ∧ live AvailabilitySnapshot=fresh＋available——
  stale/unknown/row 缺席（＝unknown）永不可 selected；preferred 同樣受
  live available 管轄。
- invariant 3：selected 以 advisory planning rows 當 eligibility ⇒ 違規
  （advisory 證據不得偷升 live authority，AIR-240）——planning rows 全
  stale/unknown（或缺席）為指定 case；plan 表達 explicit fallback_families
  本身不違規。
- invariant 4：hard requirement 不得被 fallback 降低——dispatched_contract
  與 contract 的 hard 欄逐一相等；任一相異即違規（WorkUnitContract 欄不變）。

輸入契約（fail-closed）：
- live_availability／planning_rows rows＝{family, freshness, state}——
  pool 級投影在 capture 時完成（checker 只消費 family 級 tri-state）。
- qualified_families＝resolver 步驟 2 hard filter 結果（checker 信任此
  輸入不重算——重算＝第二 resolver）。
- selected.eligibility_source ∈ {live_availability, entitlement_planning}
  ＝eligibility 證據來源申報（invariant 3 的機械見證欄；缺席＝輸入錯誤）。
- policy 形狀鏡射 arc_spec temporal 閉集：delay 禁帶非空 fallback_families、
  fallback 須帶非空顯式集合、fallback_families 禁含 preferred_family。
- selected 在場而 dispatched_contract 缺席＝輸入錯誤（無法驗證 hard
  requirement 未被降低，fail-closed）。

exit 契約：0＝admissible；2＝invariant 違規逐行明列或輸入不合法（fail-loud，
沿 arc_spec 風格）。
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA = "resolver-decision/1"
FRESH = "fresh"
STALE = "stale"
FRESHNESS = (FRESH, STALE)
STATES = ("available", "unavailable", "unknown")
ON_UNAVAILABLE = ("delay", "fallback")
ELIGIBILITY_SOURCES = ("live_availability", "entitlement_planning")
# invariant 4 逐欄比較的 WorkUnitContract hard 欄（schema 欄位集＝
# model-routing skill「WorkUnitContract schema」表）
HARD_CONTRACT_FIELDS = (
    "role",
    "authority",
    "judgment_floor",
    "qualifications",
    "capabilities",
    "surface",
    "independence",
)
REQUIRED_TOP = (
    "schema",
    "decision_id",
    "contract",
    "policy",
    "planning_rows",
    "live_availability",
    "qualified_families",
    "selected",
)

INADMISSIBLE = "stale/unknown 不可 dispatch"


class DecisionInputError(Exception):
    """檔案層錯誤（不存在／JSON 壞）——exit 2 fail-loud。"""


def load_decision(path: Path) -> dict:
    if not path.is_file():
        raise DecisionInputError(f"decision 檔不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DecisionInputError(f"decision 檔 JSON 壞：{path}（{exc}）") from exc
    if not isinstance(data, dict):
        raise DecisionInputError(
            f"decision 須為 JSON object（top-level），got {type(data).__name__}"
        )
    return data


# ---- 輸入驗證（schema 層；回錯誤行 list）----


def _require_str_list(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not all(
        isinstance(v, str) and v for v in value
    ):
        errors.append(f"{label} 須為非空字串 list，got {value!r}")


def _validate_policy(policy: object, errors: list[str]) -> None:
    if not isinstance(policy, dict):
        errors.append(f"policy 須為 object，got {type(policy).__name__}")
        return
    preferred = policy.get("preferred_family")
    if not isinstance(preferred, str) or not preferred:
        errors.append(f"policy.preferred_family 須為非空字串，got {preferred!r}")
    on_unavailable = policy.get("on_unavailable")
    if on_unavailable not in ON_UNAVAILABLE:
        errors.append(
            f"policy.on_unavailable 須為 {'/'.join(ON_UNAVAILABLE)}，"
            f"got {on_unavailable!r}"
        )
    fallbacks = policy.get("fallback_families")
    _require_str_list(fallbacks, "policy.fallback_families", errors)
    if errors:
        return
    # 以下鏡射 arc_spec temporal 閉集（plan compile 已驗；decision 層防禦）
    if on_unavailable == "delay" and fallbacks:
        errors.append(
            "policy 形狀不合法：on_unavailable=delay 禁與非空 "
            "fallback_families 並存（雙 authoritative policy）"
        )
    if on_unavailable == "fallback" and not fallbacks:
        errors.append(
            "policy 形狀不合法：on_unavailable=fallback 須帶非空顯式 "
            "fallback_families（explicit-only）"
        )
    if preferred in fallbacks:
        errors.append(
            f"policy 形狀不合法：fallback_families 禁含 preferred_family "
            f"`{preferred}`（相異家族才叫 fallback）"
        )


def _validate_rows(rows: object, label: str, errors: list[str], seen: set) -> None:
    if not isinstance(rows, list):
        errors.append(f"{label} 須為 list，got {type(rows).__name__}")
        return
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{label}[{i}] 須為 object")
            continue
        family = row.get("family")
        if not isinstance(family, str) or not family:
            errors.append(f"{label}[{i}].family 須為非空字串，got {family!r}")
            continue
        if family in seen:
            errors.append(f"{label} 重複 family `{family}`（每 family 恰一 row）")
        seen.add(family)
        if row.get("freshness") not in FRESHNESS:
            errors.append(
                f"{label}[{i}].freshness 須為 {'/'.join(FRESHNESS)}，"
                f"got {row.get('freshness')!r}"
            )
        if row.get("state") not in STATES:
            errors.append(
                f"{label}[{i}].state 須為 {'/'.join(STATES)}，"
                f"got {row.get('state')!r}"
            )


def _validate_input(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != SCHEMA:
        errors.append(f"schema 須為 {SCHEMA!r}，got {data.get('schema')!r}")
    decision_id = data.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id:
        errors.append(f"decision_id 須為非空字串，got {decision_id!r}")
    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"必填欄缺席：{key}")
    if errors:
        return errors
    if not isinstance(data["contract"], dict):
        errors.append("contract 須為 object（WorkUnitContract）")
    _validate_policy(data["policy"], errors)
    _validate_rows(
        data["planning_rows"], "planning_rows", errors, seen=set()
    )
    _validate_rows(
        data["live_availability"], "live_availability", errors, seen=set()
    )
    _require_str_list(
        data["qualified_families"], "qualified_families", errors
    )
    selected = data["selected"]
    if selected is not None:
        if not isinstance(selected, dict):
            errors.append(f"selected 須為 null 或 object，got {type(selected).__name__}")
            return errors
        family = selected.get("family")
        if not isinstance(family, str) or not family:
            errors.append(f"selected.family 須為非空字串，got {family!r}")
        if selected.get("eligibility_source") not in ELIGIBILITY_SOURCES:
            errors.append(
                f"selected.eligibility_source 須為 "
                f"{'/'.join(ELIGIBILITY_SOURCES)}，"
                f"got {selected.get('eligibility_source')!r}"
            )
        if not isinstance(data["contract"], dict) or not isinstance(
            data.get("dispatched_contract"), dict
        ):
            errors.append(
                "selected 在場而 dispatched_contract 缺席或非 object——"
                "無法驗證 hard requirement 未被降低（fail-closed）"
            )
    return errors


# ---- hard invariants（回違規行 list）----


def _row(rows: list, family: str) -> dict | None:
    for row in rows:
        if row.get("family") == family:
            return row
    return None


def _live_desc(row: dict | None) -> str:
    if row is None:
        return "live row 缺席＝unknown"
    return f"state={row['state']}, freshness={row['freshness']}"


def _planning_all_stale(rows: list) -> bool:
    return all(
        row.get("freshness") == STALE or row.get("state") == "unknown"
        for row in rows
    )


def _check_invariants(data: dict) -> list[str]:
    violations: list[str] = []
    policy = data["policy"]
    preferred: str = policy["preferred_family"]
    live_rows = data["live_availability"]
    selected = data["selected"]

    # ---- invariant 1：delay＋preferred live-unavailable ⇒ zero dispatch ----
    if policy["on_unavailable"] == "delay":
        live_row = _row(live_rows, preferred)
        preferred_unavailable = (
            live_row is None
            or live_row["state"] != "available"
            or live_row["freshness"] != FRESH
        )
        if preferred_unavailable and selected is not None:
            violations.append(
                f"invariant-1 VIOLATION: on_unavailable=delay 且 preferred "
                f"family `{preferred}` live 不可用（{_live_desc(live_row)}）"
                f"——selected 必空（zero dispatch）"
            )

    if selected is None:
        return violations
    family: str = selected["family"]

    # ---- invariant 2：explicit set ∧ qualified ∧ live fresh available ----
    if family != preferred and family not in policy["fallback_families"]:
        violations.append(
            f"invariant-2 VIOLATION: selected family `{family}` 不在 "
            f"fallback_families 顯式集合（preferred=`{preferred}`、"
            f"顯式集合={policy['fallback_families']}）——explicit-only"
        )
    if family not in data["qualified_families"]:
        violations.append(
            f"invariant-2 VIOLATION: selected family `{family}` 未通過 "
            f"qualification hard filter（不在 qualified_families）"
        )
    live_row = _row(live_rows, family)
    if (
        live_row is None
        or live_row["state"] != "available"
        or live_row["freshness"] != FRESH
    ):
        violations.append(
            f"invariant-2 VIOLATION: selected family `{family}` live 非 "
            f"available（{_live_desc(live_row)}）——{INADMISSIBLE}"
        )

    # ---- invariant 3：advisory planning rows 不得偷升 live authority ----
    if selected["eligibility_source"] == "entitlement_planning":
        planning_rows = data["planning_rows"]
        if _planning_all_stale(planning_rows):
            violations.append(
                f"invariant-3 VIOLATION: selected family `{family}` 以 "
                "advisory planning rows 當 eligibility——planning rows 全 "
                "stale/unknown（或缺席）不產生 eligibility，advisory 證據"
                "不得偷升 live authority（AIR-240）"
            )
        else:
            violations.append(
                f"invariant-3 VIOLATION: selected family `{family}` 以 "
                "advisory planning rows 當 eligibility——"
                "EntitlementWindowSnapshot 屬 advisory planning evidence，"
                "非 dispatch live authority（AIR-240），不得偷升"
            )

    # ---- invariant 4：hard requirement 不得被 fallback 降低 ----
    contract = data["contract"]
    dispatched = data["dispatched_contract"]
    for field in HARD_CONTRACT_FIELDS:
        if contract.get(field) != dispatched.get(field):
            violations.append(
                f"invariant-4 VIOLATION: hard requirement 被 fallback 降低——"
                f"contract.{field} {contract.get(field)!r} → "
                f"dispatched_contract.{field} {dispatched.get(field)!r}"
                f"（WorkUnitContract 欄不變）"
            )
    return violations


def validate_decision(data: object) -> tuple[list[str], list[str]]:
    """純函數：回 (input_errors, invariant_violations)。probe 消費面。"""
    if not isinstance(data, dict):
        return [f"decision 須為 JSON object，got {type(data).__name__}"], []
    input_errors = _validate_input(data)
    if input_errors:
        return input_errors, []
    return [], _check_invariants(data)


# ---- CLI ----


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="resolver_decision_check",
        description=(
            "AIR-245 resolver decision invariant checker：只驗 hard "
            "invariants，禁 soft ranking／禁第二 resolver（多合法 candidate "
            "判 admissible set 不比 winner）"
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("validate", help="驗一份 proposed decision（JSON 檔）")
    pv.add_argument("file", help="decision 檔路徑")

    args = p.parse_args(argv)
    assert args.cmd == "validate"
    try:
        data = load_decision(Path(args.file))
    except DecisionInputError as exc:
        print(f"[resolver-decision-check] INPUT ERROR: {exc}", file=sys.stderr)
        return 2
    input_errors, violations = validate_decision(data)
    if input_errors:
        for err in input_errors:
            print(f"[resolver-decision-check] INPUT ERROR: {err}", file=sys.stderr)
        print(
            f"[resolver-decision-check] {len(input_errors)} input error(s)"
            " — fail-loud",
            file=sys.stderr,
        )
        return 2
    if violations:
        for v in violations:
            print(f"[resolver-decision-check] {v}", file=sys.stderr)
        print(
            f"[resolver-decision-check] {len(violations)} invariant "
            "violation(s) — 禁派工（fail-loud）",
            file=sys.stderr,
        )
        return 2
    print(
        f"ADMISSIBLE resolver-decision: {args.file} — hard invariants 4/4 "
        "pass（soft ranking 未評估——多合法 candidate 不比 winner）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
