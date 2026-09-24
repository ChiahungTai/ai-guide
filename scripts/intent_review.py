#!/usr/bin/env python
"""intent_review——AIR-135.1 S3：Intent Review 驗收腿工作單編譯器（135.3 AC#7 語義承載面）。

邊界（卡面＋S1/S2 延伸已決策勿重辯）：
- D1 畫線同前：純編譯＋校驗——generate 是靜態物產出；Intent Review 的執行
  編排（腿派工／liveness／collection）歸 AIR-135.7——本檔不建 runner。
- AC#7 語義引用不重定：read-set 排除、機械驗證證據包、「首批恆跑不抽樣」
  等照 135.3 卡面條文——工作單只承載；chain-exclusion policy 單一源＝
  arc_spec.ROLE_READ_SET["intent-review"]。
- receipt.intent_review 回寫面：定義源＝arc_spec.py receipt schema 新選填欄
  （machine-invariant、required_at=never，同 N6 receipt_sink 慣例）＋
  INTENT_REVIEW_VERDICTS 枚舉；本檔只引用不重定。

素材投影（AC#7 exit intent 雙證之獨立腿）：
- intent verbatim／成功謂詞←ArcSpec entry 凍結欄逐字（禁改寫）
- final artifact 指針←ArcPlan work_units 的 sink 面（implement 角色）；
  plan 層 sink 缺席＝DispatchSlice JIT 落地（D2/D5）——記 jit_sink_units
  誠實標注非靜默
- 機械驗證證據包←work_units 的 verify／test 角色 sink 面（test 輸出／
  invariant 結果——須機械產出，非實作方自述）
- 排除面：中間 plan（ArcPlan 全文／EP）／中間 review（findings）／court
  討論——排除的是 implementer reasoning 非驗收事實
- PLAN_CHANGES 複核段←plan_changes[] 逐筆（what＋diff）；無偏差＝零偏差
  聲明；per-batch 審查腿判定欄三值（無偏移／表面符合語義已偏／intent
  本身變更）

fail-loud（codex multi_agents_common.rs:395-442 文案形，同 S1/S2）：上游
spec／plan 先過 S1 validator（缺欄一次列全部、plan_hash 漂移即錯——Intent
Review 不得以漂移計畫為基準）、schema marker 不符列期望值、spec／plan 身份
衝突（card_id／card_baseline 雙 authoritative）即錯——不靜默猜。

檔案形態：工作單以「人類可讀 markdown＋```json 區塊」承載（render 同
sample-dispatch 慣例）；工作單自身非 arc_spec 四物 kind——contract 由
tests/test_intent_review.py 釘住。

CLI：無（純函式庫——呼叫 generate(spec, plan)／render(wo)；端到端驗證跑
bash .agent-tmp/air-135.1/s3_seal_and_validate.sh）。
"""

import importlib.util
import json
from pathlib import Path

SCHEMA_INTENT_REVIEW_WO = "intent-review-wo/1"

# per-batch 審查腿判定欄三值（135.3 AC#7 0920 修訂語彙——「表面符合、語義已偏」）
BATCH_VERDICT_OPTIONS: tuple[str, ...] = (
    "無偏移",
    "表面符合語義已偏",
    "intent 本身變更",
)


class IntentReviewError(Exception):
    """工作單編譯契約錯——收集式訊息一次報全部（同 arc_spec 慣例），fail loud。"""


def _load_arc_spec():
    path = Path(__file__).resolve().with_name("arc_spec.py")
    spec = importlib.util.spec_from_file_location("_air1351_arc_spec_iv", path)
    if spec is None or spec.loader is None:
        raise IntentReviewError(f"cannot load arc_spec module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_arc = _load_arc_spec()


# ---------------------------------------------------------------------------
# 投影小工具
# ---------------------------------------------------------------------------


def _sink_path(unit: dict) -> str | None:
    """work unit 的 sink 面 → 指針字串（plan 層 sink 為選填投影欄；無＝None）。"""
    sink = unit.get("sink")
    if isinstance(sink, str) and sink.strip():
        return sink.strip()
    if isinstance(sink, dict):
        path = sink.get("path")
        if isinstance(path, str) and path.strip():
            return path.strip()
    return None


# ---------------------------------------------------------------------------
# generate 主體
# ---------------------------------------------------------------------------


def generate(spec: dict, plan: dict) -> dict:
    """ArcSpec＋ArcPlan → Intent Review 工作單物件（純編譯；契約錯 raise IntentReviewError）。

    AC#7 雙證之獨立腿素材投影——只承載驗收事實（intent verbatim／成功謂詞／
    final artifact／機械驗證證據包／PLAN_CHANGES 偏差記錄），排除 implementer
    reasoning（中間 plan／review／court 討論不入 read-set）。
    """
    if not isinstance(spec, dict):
        raise IntentReviewError(
            f"spec must be an object for intent_review.generate, got {type(spec).__name__}"
        )
    if not isinstance(plan, dict):
        raise IntentReviewError(
            f"plan must be an object for intent_review.generate, got {type(plan).__name__}"
        )
    if spec.get("schema") != _arc.SCHEMA_ARC_SPEC:
        raise IntentReviewError(
            f"Unknown schema marker `{spec.get('schema')}` for intent-review spec. "
            f"Expected schema marker: {_arc.SCHEMA_ARC_SPEC}"
        )
    if plan.get("schema") != _arc.SCHEMA_ARC_PLAN:
        raise IntentReviewError(
            f"Unknown schema marker `{plan.get('schema')}` for intent-review plan. "
            f"Expected schema marker: {_arc.SCHEMA_ARC_PLAN}"
        )

    # 上游密封先驗（單一源：S1 validator——缺欄一次列全部、plan_hash 漂移即錯）
    errors: list[str] = []
    for label, kind, data in (("spec", "arc-spec", spec), ("plan", "arc-plan", plan)):
        upstream = _arc.validate(kind, data, stage="compile")
        errors.extend(f"[{label}] {e}" for e in upstream)

    # spec／plan 身份一致（雙 authoritative 衝突 fail-loud，同 S2 family 衝突同構）
    for key in ("card_id", "card_baseline"):
        sv, pv = spec.get(key), plan.get(key)
        if sv is not None and pv is not None and sv != pv:
            errors.append(
                f"Conflicting {key} for intent-review work order: "
                f"spec.{key}=`{sv}`, plan.{key}=`{pv}` — 雙 authoritative（fail-loud）"
            )
    if errors:
        raise IntentReviewError("\n".join(errors))

    # sink 面投影：implement→final artifact、verify/test→證據包、review→排除面
    final_artifacts: list[dict] = []
    evidence_pack: list[dict] = []
    jit_units: list[str] = []
    for i, unit in enumerate(plan["work_units"]):
        role = unit.get("role")
        if role not in ("implement", "verify", "test"):
            continue  # review 腿產物＝中間鏈——不入本單（排除面）
        unit_id = str(unit.get("unit_id") or f"work_units[{i}]")
        sink = _sink_path(unit)
        if sink is None:
            jit_units.append(unit_id)  # plan 層無指針＝DispatchSlice JIT（D2/D5）
            continue
        entry = {"unit_id": unit_id, "title": str(unit.get("title") or ""), "path": sink}
        if role == "implement":
            final_artifacts.append(entry)
        else:
            evidence_pack.append(entry)

    changes = plan.get("plan_changes") or []
    zero = not changes
    batches = [
        {
            "index": i,
            "what": str(ch["what"]),
            "diff": str(ch["diff"]),
            "review_verdict": "",  # 審查腿判定欄（per-batch；verdict_options 三值）
        }
        for i, ch in enumerate(changes, start=1)
    ]
    declaration = (
        "零偏差聲明：plan_changes 為空——實作全程無 ArcPlan 偏差（D4 Deviations-only 流）。"
        "注意：零偏差≠無語義漂移，「表面符合、語義已偏」仍須對照 final artifact 判定。"
    ) if zero else None

    return {
        "schema": SCHEMA_INTENT_REVIEW_WO,
        "card_id": spec["card_id"],
        "card_baseline": spec["card_baseline"],
        "source_card": spec.get("source_card"),
        "plan_version": plan["version"],
        "plan_hash": plan["plan_hash"],
        "role": "intent-review",
        "review_question": (
            "完成的東西仍解 Intent_0 嗎？（本腿首要抓捕「表面符合、語義已偏」"
            "——look-ahead／復權／fee model 類）"
        ),
        "intent_verbatim": spec["intent_verbatim"],
        "success_predicate": spec["success_predicate"],
        "final_artifacts": final_artifacts,
        "evidence_pack": evidence_pack,
        "jit_sink_units": jit_units,
        "read_set": {
            "policy": _arc.ROLE_READ_SET["intent-review"][0],  # chain-exclusion（S1 單一源）
            "allowed": [
                "intent verbatim（本單凍結欄）",
                "成功謂詞（本單凍結欄）",
                "final artifact 指針（本單投影面）",
                "機械驗證證據包（test 輸出／invariant 結果——機械產出非自述）",
                "PLAN_CHANGES 複核段（偏差事實 what＋diff）",
            ],
            "excluded": [
                "中間 plan（ArcPlan 全文／EP／Shape 討論）",
                "中間 review（code-review／ep-review findings）",
                "court／judge 討論（判決書、findings 裁決串）",
            ],
            "rule": "排除的是 implementer reasoning 非驗收事實（AC#7 0920 修訂）",
        },
        "plan_changes_review": {
            "zero_deviation": zero,
            "declaration": declaration,
            "batches": batches,
            "verdict_options": BATCH_VERDICT_OPTIONS,
        },
        "gate_semantics": {
            "trigger": (
                "tier standard＋full 且任一（revert 敞口花掉過半／假設台帳有 invalidated row／"
                "本弧動過跨卡契約）——閘外小弧自報為足"
            ),
            "first_batch": (
                "信任畢業前（首批）獨立腿恆跑不抽樣——低花費綠地弧三閘條件全 false＝"
                "silent drift 盲區（0920 dry-run）；信任畢業後可降抽樣"
            ),
            "receipt_split": "自報缺失＝弧不完整；獨立腿缺失（閘內）＝exit Align 未過關",
            "orchestration": (
                "Intent Review 執行編排（腿派工／liveness／collection）歸 AIR-135.7——"
                "本工作單只承載語義（D1 畫線）"
            ),
        },
        "receipt_writeback": {
            "receipt_field": "intent_review",
            "required_keys": ("verdict", "leg", "read_set_exclusion"),
            "verdict_enum": _arc.INTENT_REVIEW_VERDICTS,
            "schema_kind": _arc.SCHEMA_SLICE_RECEIPT,
            "note": (
                "machine-invariant、required_at=never（選填，同 N6 receipt_sink 慣例）——"
                "閘外小弧自報為足；閘內獨立腿缺失＝exit Align 未過關"
            ),
        },
    }


# ---------------------------------------------------------------------------
# 渲染（人類可讀＋機器 json 欄；sample-dispatch 同慣例）
# ---------------------------------------------------------------------------


def render(wo: dict) -> str:
    """工作單物件 → 人類可讀 markdown（含機器 json 區塊；純渲染不改資料）。"""
    rs = wo["read_set"]
    pcr = wo["plan_changes_review"]
    lines: list[str] = [
        f"# Intent Review 工作單——{wo['card_id']}（plan v{wo['plan_version']}）",
        "",
        "> AC#7 exit intent 雙證之**獨立腿**工作單（135.3 卡面語義引用不重定；"
        "D1 畫線＝純編譯，執行編排歸 135.7）。",
        "> 回寫契約：verdict 落 canonical receipt（slice-receipt/1）選填欄 "
        "`intent_review`——machine-invariant、required_at=never（同 N6 receipt_sink 慣例）。",
        "",
        "## 審查腿速讀",
        "",
        f"- **意圖（intent verbatim，凍結禁改寫）**：{wo['intent_verbatim']}",
        f"- **成功謂詞**：{wo['success_predicate']}",
        f"- **本腿唯一問題**：{wo['review_question']}",
        "- **final artifact 指針**（自 plan work_units sink 面——implement 角色）：",
    ]
    if wo["final_artifacts"]:
        lines += [
            f"  - `{a['unit_id']}` {a['title']} → `{a['path']}`"
            for a in wo["final_artifacts"]
        ]
    else:
        lines.append(
            "  - （本 plan 無 implement sink 指針——final artifact 於 DispatchSlice JIT 落地，D2/D5）"
        )
    if wo["jit_sink_units"]:
        listed = "、".join(f"`{u}`" for u in wo["jit_sink_units"])
        lines.append(f"  - sink 待 JIT 單位：{listed}")
    lines.append(
        "- **機械驗證證據包**（test 輸出／invariant 結果——須機械產出，非實作方自述）："
    )
    if wo["evidence_pack"]:
        lines += [
            f"  - `{e['unit_id']}` {e['title']} → `{e['path']}`" for e in wo["evidence_pack"]
        ]
    else:
        lines.append(
            "  - （本 plan 無 verify/test sink——閘內弧 exit 前須由 marshal 補指針）"
        )
    lines += [
        "",
        f"## read-set 排除規則（policy＝{rs['policy']}，定義源 arc_spec.py ROLE_READ_SET）",
        "",
        "**可讀**：",
    ]
    lines += [f"- {item}" for item in rs["allowed"]]
    lines += ["", f"**排除**（{rs['rule']}）："]
    lines += [f"- {item}" for item in rs["excluded"]]
    lines += ["", "## PLAN_CHANGES 複核段", ""]
    if pcr["zero_deviation"]:
        lines.append(f"**{pcr['declaration']}**")
    else:
        options = "／".join(pcr["verdict_options"])
        lines += [
            f"| # | what | diff | 審查腿判定（{options}） |",
            "|---|------|------|------|",
        ]
        for b in pcr["batches"]:
            what = str(b["what"]).replace("|", "\\|")
            diff = str(b["diff"]).replace("|", "\\|")
            lines.append(f"| {b['index']} | {what} | {diff} | （待審查腿填） |")
    g = wo["gate_semantics"]
    wb = wo["receipt_writeback"]
    lines += [
        "",
        "## 觸發閘與抽樣（135.3 卡面條文引用，本單不重定）",
        "",
        f"- **觸發閘**：{g['trigger']}",
        f"- **首批恆跑**：{g['first_batch']}",
        f"- **receipt 分欄**：{g['receipt_split']}",
        f"- **編排**：{g['orchestration']}",
        "",
        "## receipt 回寫面（verdict minimum contract）",
        "",
        f"- 欄位：receipt.`{wb['receipt_field']}`（選填；machine-invariant、"
        "required_at=never——同 N6 receipt_sink 慣例）",
        "- minimum keys：`verdict`（枚舉 GO／GO-WITH-FIXES／NO-GO）＋`leg`（審查腿身份）"
        "＋`read_set_exclusion`（chain-exclusion 自述）",
        "- 校驗：`uv run python scripts/arc_spec.py validate --kind receipt <receipt 檔>`"
        "——verdict 未知值 fail-loud 列可用值",
        "- 閘外小弧自報為足；閘內獨立腿缺失＝exit Align 未過關",
        "",
        "## 機器欄（本工作單 contract 由 tests/test_intent_review.py 釘住；非 arc_spec 四物 kind）",
        "",
        "```json",
        json.dumps(wo, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI（無——純函式庫；同 receipt_normalize 慣例）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print(
        "intent_review 是純函式庫——呼叫 generate(spec, plan)／render(wo)；"
        "端到端驗證跑 bash .agent-tmp/air-135.1/s3_seal_and_validate.sh",
        file=sys.stderr,
    )
    raise SystemExit(2)
