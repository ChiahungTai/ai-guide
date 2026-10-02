#!/usr/bin/env python
"""arc_handback_join——AIR-234 manifest×handback 結構 join（fail-closed 缺項閘）。

manifest（`arc-manifest/1`，scripts/arc_manifest.py 產物）×handback
（`arc-handback/1`，worker 交付）→ 機械 join：worker 自報 DONE 是否結構齊全
——缺任何 assigned predicate 的 verdict 即拒收（transport terminal 不等於
DONE；collection 用本工具把缺項擋在 DONE 前）。

**語義分離（工單 §5.2 釘死，勿重辯）**：join 只驗結構齊全——verdict 為
`FAIL`／`NOT-DONE` 仍 exit 0。語義裁決（FAIL 要不要修、NOT-DONE 要不要
NOT-DONE 结案）歸 collection，不歸 join；本工具永不越權變 semantic gate。

join 規則（全過→exit 0＋stdout 一行 `join OK: N predicates`）：
1. 兩檔 top-level 為 JSON object；schema 值正確；`card_id` 一致；`unit_id`
   一致
2. manifest predicates 逐條目驗證（object＋非空字串 `ac_id`＋無重複——
   malformed／重複即拒收，禁縮水集合假 PASS；repair-1 R3）
3. manifest 每 predicate 恰一個 verdict；handback 無未知 `ac_id`
4. `verdict` ∈ {`PASS`, `FAIL`, `NOT-DONE`}
5. `evidence` 非空字串

違反→stdout 逐行列缺項（`missing: ac_id=…`／`invalid: ac_id=… reason=…`）
＋exit 2；一次全列不首報即停。檔案層錯誤（不存在／JSON 壞）→stderr
ERROR＋exit 2。

CLI：`uv run python scripts/arc_handback_join.py --manifest MANIFEST --handback HANDBACK`
"""

import argparse
import json
import sys
from pathlib import Path

MANIFEST_SCHEMA = "arc-manifest/1"
HANDBACK_SCHEMA = "arc-handback/1"
VALID_VERDICTS = ("PASS", "FAIL", "NOT-DONE")


def join(manifest: dict, handback: dict) -> list[str]:
    """結構 join——回錯誤行 list（空＝全過）；純函數、不觸 IO。"""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        errors.append(
            f"invalid: manifest reason=須為 JSON object（top-level），"
            f"got {type(manifest).__name__}"
        )
    if not isinstance(handback, dict):
        errors.append(
            f"invalid: handback reason=須為 JSON object（top-level），"
            f"got {type(handback).__name__}"
        )
    if errors:
        return errors

    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append(
            f"invalid: manifest schema={manifest.get('schema')!r} reason="
            f"須為 {MANIFEST_SCHEMA!r}"
        )
    if handback.get("schema") != HANDBACK_SCHEMA:
        errors.append(
            f"invalid: handback schema={handback.get('schema')!r} reason="
            f"須為 {HANDBACK_SCHEMA!r}"
        )
    if manifest.get("card_id") != handback.get("card_id"):
        errors.append(
            f"invalid: card_id reason=manifest={manifest.get('card_id')!r} "
            f"handback={handback.get('card_id')!r} 不一致"
        )
    if manifest.get("unit_id") != handback.get("unit_id"):
        errors.append(
            f"invalid: unit_id reason=manifest={manifest.get('unit_id')!r} "
            f"handback={handback.get('unit_id')!r} 不一致"
        )

    predicates = manifest.get("predicates")
    if not isinstance(predicates, list):
        errors.append("invalid: manifest reason=predicates 須為 list")
        predicates = []
    # 規則 2（repair-1 R3）：manifest predicates 逐條目驗證——非 object／非
    # 非空字串 ac_id／重複 ac_id 都逐行 invalid，禁縮水集合假 PASS
    manifest_acs: list[str] = []
    seen_ac: set[str] = set()
    for i, p in enumerate(predicates):
        if not isinstance(p, dict):
            errors.append(f"invalid: predicates[{i}] reason=須為 object")
            continue
        ac = p.get("ac_id")
        if not isinstance(ac, str) or not ac:
            errors.append(
                f"invalid: predicates[{i}] reason=ac_id 須為非空字串"
            )
            continue
        if ac in seen_ac:
            errors.append(
                f"invalid: ac_id={ac} reason=manifest predicates 重複"
                f"（每 ac_id 恰一條）"
            )
            continue
        seen_ac.add(ac)
        manifest_acs.append(ac)

    verdicts = handback.get("verdicts")
    if not isinstance(verdicts, list):
        errors.append("invalid: handback reason=verdicts 須為 list")
        verdicts = []

    by_ac: dict[object, list[dict]] = {}
    for i, v in enumerate(verdicts):
        if not isinstance(v, dict):
            errors.append(f"invalid: verdicts[{i}] reason=須為 object")
            continue
        by_ac.setdefault(v.get("ac_id"), []).append(v)

    # 規則 2 前半：manifest 每 predicate 恰一個 verdict（缺＝missing、多＝invalid）
    for ac in manifest_acs:
        got = by_ac.get(ac)
        if got is None:
            errors.append(f"missing: ac_id={ac}")
        elif len(got) > 1:
            errors.append(
                f"invalid: ac_id={ac} reason=duplicate verdict（{len(got)} 份；"
                f"每 predicate 恰一）"
            )

    # 規則 2 後半＋規則 3/4：handback 側逐項驗
    known = set(manifest_acs)
    for ac, vs in by_ac.items():
        if ac not in known:
            errors.append(
                f"invalid: ac_id={ac} reason=未知 ac_id（不在 manifest assigned "
                f"predicates）"
            )
            continue  # 越權 verdict 不再驗語義欄位，避免重複噪音
        v = vs[0]
        if v.get("verdict") not in VALID_VERDICTS:
            errors.append(
                f"invalid: ac_id={ac} reason=verdict 須為 {'/'.join(VALID_VERDICTS)}"
                f"，got {v.get('verdict')!r}"
            )
        evidence = v.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            errors.append(
                f"invalid: ac_id={ac} reason=evidence 須為非空字串（禁無證據 PASS）"
            )
    return errors


class JoinFileError(Exception):
    """檔案層錯誤（不存在／JSON 壞）——stderr ERROR＋exit 2。"""


def _load_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise JoinFileError(f"{label} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise JoinFileError(f"{label} malformed JSON: {path}（{e}）") from e


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arc_handback_join",
        description=(
            "AIR-234 manifest×handback 結構 join：缺任何 assigned predicate "
            "verdict／非三值／evidence 空＝exit 2 逐行列缺項"
        ),
        epilog=(
            "語義分離：verdict 為 FAIL/NOT-DONE 仍 exit 0——語義裁決歸 "
            "collection，不歸 join"
        ),
    )
    parser.add_argument("--manifest", required=True, help="arc-manifest/1 JSON 檔路徑")
    parser.add_argument("--handback", required=True, help="arc-handback/1 JSON 檔路徑")

    args = parser.parse_args(argv)
    try:
        manifest = _load_json(Path(args.manifest), "manifest")
        handback = _load_json(Path(args.handback), "handback")
    except JoinFileError as e:
        print(f"[arc-join] ERROR: {e}", file=sys.stderr)
        return 2

    errors = join(manifest, handback)
    if errors:
        for line in errors:
            print(line)
        return 2
    print(f"join OK: {len(manifest.get('predicates') or [])} predicates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
