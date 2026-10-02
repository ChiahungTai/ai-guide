#!/usr/bin/env python
"""arc_manifest——AIR-234 per-unit assigned-predicate manifest 投影器。

acceptance_contract（arc_goal_compile 輸出的 ```json 區塊，schema
`acceptance-contract/1`）×unit 分派表（schema `arc-units/1`）→ 每 unit 一份
assigned-predicate manifest（schema `arc-manifest/1`）：worker 帶著它負責的
AC predicates 清單上工，handback 逐 predicate 回 verdict（join＝
scripts/arc_handback_join.py）。

set 不變式三條（工單 §5.1 釘死，核心 oracle——違反任一＝逐行錯誤 stderr＋
exit 2，永不靜默投影）：
1. units 的 ac_ids 聯集 == contract `ac_ids`（少＝漏分派、多＝未知 ac_id）
2. units 兩兩不相交（重疊＝同一 predicate 雙頭分派）
3. `unit_id` 無重複

輸出：`DIR/<unit_id「#」後綴>.json`（如 `AIR-234#impl-a`→`impl-a.json`）::

    {"schema": "arc-manifest/1", "card_id": "…", "unit_id": "…",
     "contract_hash": "<hex64>",
     "predicates": [{"ac_id", "kind", "verifier", "expected"}, …]}

`contract_hash`＝sha256(canonical_json(contract))；canonical＝sort_keys＋
緊湊分隔符＋UTF-8（與 scripts/arc_spec.py 同形）。

邊界：
- pure projector：無 process side effects（不 spawn、不寫卡、不觸 git）；
  contract/unit 表仍是唯一 source of truth，本工具只投影不裁語義。
- fail-loud 補充（工單三不變式之外的結構防線，同 exit 2）：schema 值不符、
  contract/units card_id 不一致、unit 分派到 judgment-required ac（無
  predicate 可投影）、unit_id 無「#」後綴或後綴含路徑字元（檔名衍生不可為）。
- exit 0＝成功＋stdout 一行摘要（units 數＋predicates 總數）；
  exit 2＝契約/結構錯（錯誤逐行 stderr）。

CLI：`uv run python scripts/arc_manifest.py CONTRACT --units UNITS --out-dir DIR`
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ACCEPTANCE_CONTRACT_SCHEMA = "acceptance-contract/1"
ARC_UNITS_SCHEMA = "arc-units/1"
MANIFEST_SCHEMA = "arc-manifest/1"


class ManifestError(Exception):
    """contract/units 結構或 set 不變式違約——fail-loud（exit 2）。"""


def canonical_json(data: dict) -> str:
    """canonical JSON——sort_keys＋緊湊分隔符＋UTF-8（同 arc_spec 慣例）。"""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def contract_hash(contract: dict) -> str:
    """sha256 of canonical JSON（契約內容指紋——manifest 可回指所屬 contract）。"""
    return hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()


def _fail(errors: list[str]) -> None:
    if errors:
        raise ManifestError("\n".join(errors))


def _validate_structures(contract: dict, units_doc: dict) -> None:
    """schema 值＋card_id 一致＋容器形狀——三不變式外的結構防線（fail-loud）。"""
    errors: list[str] = []
    if contract.get("schema") != ACCEPTANCE_CONTRACT_SCHEMA:
        errors.append(
            f"invalid: contract schema={contract.get('schema')!r} reason="
            f"須為 {ACCEPTANCE_CONTRACT_SCHEMA!r}（arc_goal_compile 輸出）"
        )
    if units_doc.get("schema") != ARC_UNITS_SCHEMA:
        errors.append(
            f"invalid: units schema={units_doc.get('schema')!r} reason="
            f"須為 {ARC_UNITS_SCHEMA!r}"
        )
    if contract.get("card_id") != units_doc.get("card_id"):
        errors.append(
            f"invalid: card_id reason=contract={contract.get('card_id')!r} "
            f"units={units_doc.get('card_id')!r} 不一致"
        )
    if not isinstance(contract.get("ac_ids"), list) or not isinstance(
        contract.get("predicates"), list
    ):
        errors.append(
            "invalid: contract reason=ac_ids／predicates 須為 list"
            "（acceptance-contract/1 形）"
        )
    if not isinstance(units_doc.get("units"), list):
        errors.append("invalid: units reason=units 須為 list（arc-units/1 形）")
    for i, unit in enumerate(units_doc.get("units", []) if isinstance(units_doc.get("units"), list) else []):
        if not isinstance(unit, dict):
            errors.append(f"invalid: units[{i}] reason=須為 object")
            continue
        unit_id = unit.get("unit_id")
        ac_ids = unit.get("ac_ids")
        if not isinstance(unit_id, str) or not unit_id:
            errors.append(f"invalid: units[{i}] reason=unit_id 須為非空字串")
        if not isinstance(ac_ids, list) or not all(
            isinstance(a, str) for a in ac_ids
        ):
            errors.append(
                f"invalid: units[{i}] reason=ac_ids 須為字串 list"
            )
    _fail(errors)


def check_set_invariants(contract: dict, units_doc: dict) -> None:
    """set 不變式三條（工單 §5.1 釘死）——違反逐行錯誤（一次全列，非首報即停）。"""
    errors: list[str] = []
    all_ac: set[str] = set(contract["ac_ids"])
    units = units_doc["units"]

    unit_ids = [u["unit_id"] for u in units]
    seen: set[str] = set()
    for uid in unit_ids:
        if uid in seen:
            errors.append(f"invalid: unit_id={uid} reason=重複 unit_id（不變式 3）")
        seen.add(uid)

    assigned_union: set[str] = set()
    per_unit: list[tuple[str, set[str]]] = []
    for u in units:
        acs = set(u["ac_ids"])
        per_unit.append((u["unit_id"], acs))
        overlap = assigned_union & acs
        if overlap:
            owners = [
                uid
                for uid, prev in per_unit
                if prev & acs and uid != u["unit_id"]
            ]
            errors.append(
                f"invalid: ac_id={sorted(overlap)} reason=units {owners}＋"
                f"{u['unit_id']} 重疊（雙頭分派；不變式 2）"
            )
        assigned_union |= acs

    missing = sorted(all_ac - assigned_union)
    for ac in missing:
        errors.append(f"missing: ac_id={ac} reason=未分派給任何 unit（漏分派；不變式 1）")
    unknown = sorted(assigned_union - all_ac)
    if unknown:
        errors.append(
            f"invalid: ac_id={unknown} reason=未知 ac_id（不在 contract ac_ids；"
            f"不變式 1 反向）"
        )
    _fail(errors)


def _manifest_filename(unit_id: str) -> str:
    """`AIR-234#impl-a`→`impl-a.json`——無「#」或後綴含路徑字元＝fail-loud。"""
    if "#" not in unit_id:
        raise ManifestError(
            f"invalid: unit_id={unit_id} reason=須帶「#」後綴以衍生 manifest 檔名"
        )
    suffix = unit_id.rsplit("#", 1)[1]
    if not suffix or "/" in suffix or "\\" in suffix or ".." in suffix:
        raise ManifestError(
            f"invalid: unit_id={unit_id} reason=「#」後綴須為安全檔名（非空、"
            f"無路徑字元）"
        )
    return f"{suffix}.json"


def project_unit(contract: dict, unit: dict) -> dict:
    """單 unit 投影——predicates 取該 unit assigned ac_ids 對應的 contract
    predicates（四鍵：ac_id/kind/verifier/expected；按 ac_id 排序）。"""
    assigned = set(unit["ac_ids"])
    by_ac: dict[str, dict] = {p["ac_id"]: p for p in contract["predicates"]}
    no_predicate = sorted(assigned - set(by_ac))
    if no_predicate:
        raise ManifestError(
            f"invalid: ac_id={no_predicate} reason=unit {unit['unit_id']} 分派到"
            f"無 predicate 的 ac（judgment-required 或契約外——禁產生 predicates "
            f"空的 manifest；fail-loud）"
        )
    predicates = [
        {
            "ac_id": ac,
            "kind": by_ac[ac]["kind"],
            "verifier": by_ac[ac]["verifier"],
            "expected": by_ac[ac]["expected"],
        }
        for ac in sorted(assigned, key=lambda a: (len(a), a))
    ]
    return {
        "schema": MANIFEST_SCHEMA,
        "card_id": contract["card_id"],
        "unit_id": unit["unit_id"],
        "contract_hash": contract_hash(contract),
        "predicates": predicates,
    }


def project_manifests(contract: dict, units_doc: dict) -> list[tuple[str, dict]]:
    """contract×units → [(檔名, manifest dict)]；任何違約 raise ManifestError。"""
    _validate_structures(contract, units_doc)
    check_set_invariants(contract, units_doc)
    return [
        (_manifest_filename(unit["unit_id"]), project_unit(contract, unit))
        for unit in units_doc["units"]
    ]


def _load_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise ManifestError(f"{label} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ManifestError(f"{label} malformed JSON: {path}（{e}）") from e


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arc_manifest",
        description=(
            "AIR-234 per-unit assigned-predicate manifest 投影器："
            "acceptance_contract×unit 分派表 → 每 unit 一檔 manifest"
            "（set 不變式違約 fail-loud）"
        ),
        epilog=(
            "contract＝arc_goal_compile 輸出的 ```json 區塊（acceptance-contract/1）；"
            "units＝arc-units/1 分派表；manifest schema＝arc-manifest/1"
        ),
    )
    parser.add_argument("contract", help="acceptance_contract JSON 檔路徑")
    parser.add_argument("--units", required=True, help="arc-units/1 分派表 JSON 檔路徑")
    parser.add_argument("--out-dir", required=True, help="manifest 輸出目錄（不存在則建立）")

    args = parser.parse_args(argv)
    try:
        contract = _load_json(Path(args.contract), "contract")
        units_doc = _load_json(Path(args.units), "units")
        manifests = project_manifests(contract, units_doc)
    except ManifestError as e:
        for line in str(e).splitlines():
            print(f"[arc-manifest] ERROR: {line}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_predicates = 0
    for filename, manifest in manifests:
        out_path = out_dir / filename
        out_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        total_predicates += len(manifest["predicates"])
    print(
        f"[arc-manifest] units: {len(manifests)}／predicates: {total_predicates}"
        f" → {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
