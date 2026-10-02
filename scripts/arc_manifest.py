#!/usr/bin/env python
"""arc_manifest——AIR-234 per-unit assigned-predicate manifest 投影器。

acceptance_contract（arc_goal_compile 輸出的 ```json 區塊，schema
`acceptance-contract/1`）×unit 分派表（schema `arc-units/1`）→ 每 unit 一份
assigned-predicate manifest（schema `arc-manifest/1`）：worker 帶著它負責的
AC predicates 清單上工，handback 逐 predicate 回 verdict（join＝
scripts/arc_handback_join.py）。

set 不變式四條（工單 §5.1 三條＋repair-1 R2 檔名唯一；違反任一＝逐行錯誤
stderr＋exit 2，永不靜默投影）：
1. units 的 ac_ids 聯集 == contract `ac_ids`（少＝漏分派、多＝未知 ac_id）
2. units 兩兩不相交（重疊＝同一 predicate 雙頭分派）
3. `unit_id` 無重複
4. 衍生 manifest 檔名無碰撞（撞名＝第二檔靜默覆蓋第一檔，禁）

輸出：`DIR/<unit_id「#」後綴>.json`（如 `AIR-234#impl-a`→`impl-a.json`）::

    {"schema": "arc-manifest/1", "card_id": "…", "unit_id": "…",
     "contract_hash": "<hex64>",
     "predicates": [{"ac_id", "kind", "verifier", "expected",
                     〔選填〕"reason"／"satisfied"／"satisfied_at_baseline"}, …]}

predicate 條目形（repair-1 R1 覆蓋語義＝assigned ac_ids 全數投影）：
- 有 predicate 者：四鍵照投影；契約 predicate 帶 `satisfied`／
  `satisfied_at_baseline` 時原樣 pass-through 兩欄（baseline 已滿足證據不丟）
- judgment_required 者（arc_goal_compile 合法產物）：投影
  `{"ac_id", "kind": "judgment_required", "verifier": "", "expected": "",
    "reason": <contract judgment_required 條目的 reason>}`

`contract_hash`＝sha256(canonical_json(contract))；canonical＝sort_keys＋
緊湊分隔符＋UTF-8（與 scripts/arc_spec.py 同形）。

邊界：
- pure projector：無 process side effects（不 spawn、不寫卡、不觸 git）；
  contract/unit 表仍是唯一 source of truth，本工具只投影不裁語義。
- fail-loud 補充（四不變式之外的結構防線，同 exit 2）：top-level 非 JSON
  object、schema 值不符、contract/units card_id 不一致、judgment_required
  條目 malformed／重複／與 predicates 重疊、assigned ac 契約外（predicates
  與 judgment_required 皆無）、unit_id 無「#」後綴或後綴含路徑字元（檔名
  衍生不可為）。
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
    """schema 值＋card_id 一致＋容器形狀——四不變式外的結構防線（fail-loud）。"""
    errors: list[str] = []
    if not isinstance(contract, dict):
        errors.append(
            f"invalid: contract reason=須為 JSON object（top-level），"
            f"got {type(contract).__name__}"
        )
    if not isinstance(units_doc, dict):
        errors.append(
            f"invalid: units reason=須為 JSON object（top-level），"
            f"got {type(units_doc).__name__}"
        )
    _fail(errors)
    errors = []
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
    if not isinstance(contract.get("judgment_required"), list):
        errors.append(
            "invalid: contract reason=judgment_required 須為 list"
            "（acceptance-contract/1 形）"
        )
    else:
        errors.extend(_validate_judgment_required(contract))
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


def _validate_judgment_required(contract: dict) -> list[str]:
    """judgment_required 逐條目驗證（R1 投影源 integrity）——條目須為含非空
    字串 ac_id／reason 的 object、無重複、與 predicates 不重疊（重疊＝kind
    投影歧義，fail-loud）。"""
    errors: list[str] = []
    jud = contract["judgment_required"]
    pred_ids: set[str] = set()
    if isinstance(contract.get("predicates"), list):
        pred_ids = {
            p["ac_id"]
            for p in contract["predicates"]
            if isinstance(p, dict) and isinstance(p.get("ac_id"), str)
        }
    seen: set[str] = set()
    for i, j in enumerate(jud):
        if (
            not isinstance(j, dict)
            or not isinstance(j.get("ac_id"), str)
            or not j["ac_id"]
            or not isinstance(j.get("reason"), str)
            or not j["reason"]
        ):
            errors.append(
                f"invalid: judgment_required[{i}] reason=須為含非空字串 "
                f"ac_id／reason 的 object"
            )
            continue
        if j["ac_id"] in seen:
            errors.append(
                f"invalid: judgment_required ac_id={j['ac_id']} reason=重複"
            )
        seen.add(j["ac_id"])
        if j["ac_id"] in pred_ids:
            errors.append(
                f"invalid: ac_id={j['ac_id']} reason=同時出現在 predicates 與 "
                f"judgment_required（kind 投影歧義）"
            )
    return errors


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
    """單 unit 投影——覆蓋語義＝assigned ac_ids 全數投影（repair-1 R1）：
    有 predicate 者四鍵（契約帶 satisfied/satisfied_at_baseline 時原樣
    pass-through）；judgment_required 者投影 kind="judgment_required"＋
    contract reason；按 ac_id 排序。"""
    assigned = set(unit["ac_ids"])
    by_ac: dict[str, dict] = {p["ac_id"]: p for p in contract["predicates"]}
    by_jud: dict[str, dict] = {
        j["ac_id"]: j for j in contract["judgment_required"]
    }
    outside = sorted(assigned - set(by_ac) - set(by_jud))
    if outside:
        raise ManifestError(
            f"invalid: ac_id={outside} reason=unit {unit['unit_id']} 分派到契約外"
            f" ac（predicates 與 judgment_required 皆無；fail-loud）"
        )
    predicates: list[dict] = []
    for ac in sorted(assigned, key=lambda a: (len(a), a)):
        if ac in by_ac:
            p = by_ac[ac]
            entry: dict = {
                "ac_id": ac,
                "kind": p["kind"],
                "verifier": p["verifier"],
                "expected": p["expected"],
            }
            for key in ("satisfied", "satisfied_at_baseline"):
                if key in p:
                    entry[key] = p[key]
        else:
            entry = {
                "ac_id": ac,
                "kind": "judgment_required",
                "verifier": "",
                "expected": "",
                "reason": by_jud[ac]["reason"],
            }
        predicates.append(entry)
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
    pairs = [
        (_manifest_filename(unit["unit_id"]), project_unit(contract, unit))
        for unit in units_doc["units"]
    ]
    by_name: dict[str, list[str]] = {}
    for filename, manifest in pairs:
        by_name.setdefault(filename, []).append(manifest["unit_id"])
    _fail(
        [
            f"invalid: manifest 檔名={filename} reason={uids} 後綴撞名"
            f"（不變式 4：第二檔靜默覆蓋第一檔，禁）"
            for filename, uids in by_name.items()
            if len(uids) > 1
        ]
    )
    return pairs


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
