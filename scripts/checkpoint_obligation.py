#!/usr/bin/env python3
"""checkpoint_obligation — AIR-135.7 W4 AC#5：checkpoint obligation＋context-delivery budget.

AC#5（與 AIR-135.6 Context Continuity 對接）：ArcPlan/DispatchSlice 在 semantic
boundary 能產 checkpoint obligation 與 context-delivery budget（artifact pointer、
bounded receipt、collector state、next read-set），避免把完整歷史／穩定材料重貼進
每次 dispatch；跨 window/session re-resolution 從 latest verified checkpoint＋
actual runtime facts 接續。

schema 語義單一源＝`skills/_common/task-recovery.md`（135.6 v2 rescope 定案）：
checkpoint 必要欄位十欄表中，本模組只投影 **dispatch 面可機械產** 的欄（目標指針、
現行階段、baseline/dirty 指針、sink/collector/收法、下一個可執行 action、read-set）；
語義欄（已決策理由、open findings、授權、已驗/未驗證據）**不產**——引用 durable
owner（卡），禁重抄（task-recovery「已有欄位不重抄」鐵律）。

transient/durable 分離（本模組的存在邊界）：
- 本模組產物全部是 packet（transient——落 `.agent-tmp/` 面）；durable checkpoint
  的 owner 恆為卡 notes——模組只產「durable 指針」欄（卡 id＋note 錨），
  **禁任何寫卡行為**（全模組零檔案寫入面，CLI 唯讀）。
- packet 消費完即棄；跨 window/session 接續的 durable 錨點是卡 notes 上的
  checkpoint 指針，不是本 packet。

單一源消費（消費 import、禁反向修改）：dispatch artifact 解析與欄位機驗單一源＝
`arc_spec.validate`（經 `w3_checkpoint_link.parse_dispatch_slice`）；JIT 佔位判準
（`is_jit_dispatch_id`）與 liveness source 解析鏈（`resolve_liveness_source`）
單一源＝`w3_checkpoint_link`；bounded receipt 欄位集語義源＝`dispatch_ledger.py`
register 面（AC#3 liveness 六欄）——本模組只投影欄位集，禁二刻語義。

CLI：
- `uv run python scripts/checkpoint_obligation.py build --slice <dispatch-artifact.md> --runtime <runtime.json>`
  → stdout：obligation＋delivery_budget pretty JSON（packet，transient）
  exit 0＝成功；2＝契約／環境錯（slice 檔缺／無 fenced block／schema 不合／
  validator 未過；runtime 檔缺／壞 JSON／欄位不合／JIT 佔位 id）——fail loud
  禁靜默修復。
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCHEMA_OBLIGATION = "checkpoint-obligation/1"
SCHEMA_BUDGET = "context-delivery-budget/1"

# AC#5「semantic boundary」枚舉——plan recompile／budget 耗盡／window 跨越／
# worker terminal：ArcPlan/DispatchSlice 在這些邊界上「能產」checkpoint obligation
# （is_semantic_boundary 是產出前的分類判準）；枚舉外 transition 一律非 boundary。
BOUNDARY_TRANSITIONS = ("plan-recompile", "budget-exhausted", "window-crossing", "worker-terminal")

# runtime facts（AC#5：dispatch id、sink 狀態、liveness 源）——obligation 面的輸入契約。
# 三鍵齊備才可建 obligation（缺一即 re-resolution 無法從 actual runtime facts 接續）。
RUNTIME_KEYS = ("dispatch_id", "sink_state", "liveness_source")

# sink 狀態三態（runtime facts 的 sink 狀態軸）：verified＝三步機驗過（存在→非空→
# 錨點）；missing＝collector 查驗缺席；unverified＝尚未機驗（terminal≠complete 未閉）。
SINK_STATES = ("verified", "unverified", "missing")

# AC#5 上下界：超界禁把完整歷史／穩定材料重貼進 dispatch——只給指針。
DEFAULT_MAX_REINJECT_BYTES = 4096

# 下一個可執行 action（十欄 9）——由 runtime sink_state 機械衍生（非自由敘述），
# 語義錨 AC#4（terminal≠complete、禁原樣重派）。
_NEXT_ACTION_BY_SINK_STATE = {
    "verified": "collect-and-proceed——sink 三步機驗已過（terminal≠complete 閉合），按 plan 拓撲推進下一 slice",
    "unverified": "machine-verify-sink——collector 依 accept.predicate＋anchors 三步機驗（存在→非空→錨點）；terminal≠complete，禁只認 job 終態",
    "missing": "terminal-sink-missing——縮 slice／改交付形態，禁原樣重派（AC#4）",
}


class CheckpointObligationError(Exception):
    """obligation/budget 面契約錯（runtime 欄位不合、slice 機械欄缺席）——fail loud。"""


def _load_sibling(name: str, token: str):
    path = Path(__file__).resolve().with_name(name)
    spec = importlib.util.spec_from_file_location(f"_air1357_w4_{token}", path)
    if spec is None or spec.loader is None:
        raise CheckpointObligationError(f"cannot load {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_W3_MOD = None


def w3_mod():
    global _W3_MOD
    if _W3_MOD is None:
        _W3_MOD = _load_sibling("w3_checkpoint_link.py", "w3_checkpoint_link")
    return _W3_MOD


# ---------- 輸入欄位 guard（fail-loud；欄位機驗單一源仍在 arc_spec.parse 面） ----------


def _req_str(source: dict, key: str, label: str = "") -> str:
    shown = label or key
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        got = type(value).__name__
        raise CheckpointObligationError(
            f"dispatch-slice 缺 machine 欄 `{shown}`（got {got}）——obligation 面不可靜默缺席（先過 arc_spec.validate）"
        )
    return value.strip()


def _req_dict(source: dict, key: str) -> dict:
    value = source.get(key)
    if not isinstance(value, dict):
        raise CheckpointObligationError(
            f"dispatch-slice 欄 `{key}` 須為 object，got {type(value).__name__}——先過 arc_spec.validate"
        )
    return value


def _req_int(source: dict, key: str) -> int:
    value = source.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise CheckpointObligationError(
            f"dispatch-slice 欄 `{key}` 須為整數，got {type(value).__name__}——先過 arc_spec.validate"
        )
    return value


def _validate_runtime(runtime: dict) -> dict:
    """runtime facts 契約：三鍵齊備、禁未知鍵、dispatch_id 禁 JIT 佔位、sink_state 枚舉."""
    if not isinstance(runtime, dict):
        raise CheckpointObligationError(
            f"runtime 須為 JSON object，got {type(runtime).__name__}"
        )
    keys = set(runtime)
    missing = sorted(set(RUNTIME_KEYS) - keys)
    unknown = sorted(keys - set(RUNTIME_KEYS))
    if missing:
        raise CheckpointObligationError(
            f"runtime 缺欄 {missing}。Required runtime keys: {', '.join(RUNTIME_KEYS)}"
        )
    if unknown:
        raise CheckpointObligationError(
            f"Unknown runtime keys {unknown}. Recognized runtime keys: {', '.join(RUNTIME_KEYS)}"
        )
    dispatch_id = runtime["dispatch_id"]
    if not isinstance(dispatch_id, str):
        raise CheckpointObligationError(
            f"runtime.dispatch_id 須為字串，got {type(dispatch_id).__name__}"
        )
    w3 = w3_mod()
    stripped_id = dispatch_id.strip()
    if w3.is_jit_dispatch_id(stripped_id):
        raise CheckpointObligationError(
            f"runtime.dispatch_id 為 JIT 佔位（`{stripped_id or '空值'}`）——obligation 面須 marshal "
            "派工當下的真實 id（bridge job id 或 zcode-native session/agent 路徑）；禁把佔位串寫進 packet"
        )
    sink_state = runtime["sink_state"]
    if not isinstance(sink_state, str) or sink_state not in SINK_STATES:
        raise CheckpointObligationError(
            f"Unknown sink_state `{sink_state}` for checkpoint obligation. "
            f"Available sink states: {', '.join(SINK_STATES)}"
        )
    liveness_source = runtime["liveness_source"]
    if not isinstance(liveness_source, str):
        raise CheckpointObligationError(
            f"runtime.liveness_source 須為字串，got {type(liveness_source).__name__}"
        )
    return {"dispatch_id": stripped_id, "sink_state": sink_state, "liveness_source": liveness_source}


def _sink_face(slice: dict) -> tuple[str, str, dict]:
    """sink＋accept 投影（w3 extract_checkpoint 同形正規化；mode 缺值不靜默收下）."""
    w3 = w3_mod()
    sink = _req_dict(slice, "sink")
    mode = str(sink.get("mode") or "").strip()
    if mode not in w3.SINK_MODES:
        raise CheckpointObligationError(
            f"未知 sink mode `{mode}`；可用值：{'、'.join(w3.SINK_MODES)}"
        )
    sink_path = str(sink.get("path") or "").strip()
    accept = slice.get("accept") or {}
    predicate = str(accept.get("predicate") or "").strip()
    anchors = [str(a).strip() for a in (accept.get("anchors") or [])]
    return mode, sink_path, {"predicate": predicate, "anchors": anchors}


def _read_set_face(slice: dict) -> tuple[str, list]:
    """read-set 投影：policy 必到、pointers 選填（S1 顯式決策：無指針 slice 合法）."""
    read_set = _req_dict(slice, "read_set")
    policy = _req_str(read_set, "policy", "read_set.policy")
    pointers = read_set.get("pointers") or []
    if not isinstance(pointers, list) or not all(isinstance(p, str) for p in pointers):
        raise CheckpointObligationError(
            "`read_set.pointers` 須為字串列表（或缺席）——先過 arc_spec.validate"
        )
    return policy, [str(p).strip() for p in pointers]


# ---------- obligation（十欄中 dispatch 面可機械產者；語義欄只留 durable 指針） ----------


def build_obligation(slice: dict, runtime: dict) -> dict:
    """DispatchSlice＋runtime facts →checkpoint obligation packet（transient）.

    十欄投影（schema 語義源＝task-recovery.md）：目標指針（unit_id→卡）、現行階段
    （unit_id＋plan 回指）、baseline/dirty 指針（owning_wt＋card_baseline 機械比對
    鍵——dirty 內容不產）、sink/collector/收法（work-order §10 對應——引用不重抄）、
    下一個可執行 action（sink_state 機械衍生）、read-set。語義欄（已決策理由／
    open findings／授權／已驗未驗證據）不產——durable_checkpoint 只留卡指針。
    """
    facts = _validate_runtime(runtime)
    w3 = w3_mod()
    mode, sink_path, accept = _sink_face(slice)
    policy, pointers = _read_set_face(slice)
    card_id = _req_str(slice, "card_id")
    unit_id = _req_str(slice, "unit_id")
    slice_id = _req_str(slice, "slice_id")
    role = _req_str(slice, "role")
    plan_version = _req_int(slice, "plan_version")
    plan_hash = _req_str(slice, "plan_hash")
    card_baseline = _req_str(slice, "card_baseline")
    carrier = _req_str(slice, "carrier")
    collection_mode = _req_str(slice, "collection_mode")
    owning_wt = _req_dict(slice, "owning_wt")
    wt_path = _req_str(owning_wt, "path", "owning_wt.path")
    wt_branch = _req_str(owning_wt, "branch", "owning_wt.branch")
    declared_ledger = str(slice.get("ledger") or "").strip()
    liveness_source = w3.resolve_liveness_source(
        facts["liveness_source"], {"declared_ledger": declared_ledger}
    )
    return {
        "schema": SCHEMA_OBLIGATION,
        # 十欄 1 目標與成功條件——指針（unit_id→卡節點錨；成功條件 durable owner＝卡 AC）
        "goal_pointer": {
            "unit_id": unit_id,
            "card_id": card_id,
            "success_pointer": f"card:{card_id}#AC",
        },
        # 十欄 2 現行階段——unit_id＋plan 回指定位（phase 標題語義由 unit_id 回查 plan，不重抄）
        "current_stage": {
            "slice_id": slice_id,
            "unit_id": unit_id,
            "role": role,
            "plan_version": plan_version,
            "plan_hash": plan_hash,
        },
        # 十欄 3 scope/cwd/baseline＋dirty——指針與機械比對鍵（dirty 內容歸 work-order §3 面）
        "tree_pointer": {
            "owning_wt": {"path": wt_path, "branch": wt_branch},
            "card_baseline": card_baseline,
        },
        # 十欄 7 背景 jobId/owner/收法——jobId＝dispatch_id、collector 狀態權威＝liveness 源帳本
        "delivery_and_collection": {
            "sink": {"mode": mode, "path": sink_path if mode == "artifact" else ""},
            "accept": accept,
            "sink_state": facts["sink_state"],
            "dispatch": {
                "dispatch_id": facts["dispatch_id"],
                "carrier": carrier,
                "collection_mode": collection_mode,
                "liveness_source": liveness_source,
            },
            "collection_form_pointer": (
                "收法單一源＝work-order §10 交付報告格式＋model-routing「完成回報收法」（引用不重抄）"
            ),
        },
        # 十欄 9 下一個可執行 action——sink_state 機械衍生，非自由敘述
        "next_action": {
            "action": _NEXT_ACTION_BY_SINK_STATE[facts["sink_state"]],
            "basis": f"runtime.sink_state={facts['sink_state']}",
        },
        # 十欄 10 read-set——dispatch 面宣告的 role-dependent read-set
        "next_read_set": {"policy": policy, "pointers": pointers},
        # 語義欄（十欄 4/5/6/8）的 durable 指針——卡 id＋note 錨，禁重抄、禁寫卡
        "durable_checkpoint": {
            "owner": "card-notes",
            "card_id": card_id,
            "notes_anchor": "Implementation Notes",
            "rule": (
                "checkpoint 為 durable、本 packet 為 transient；語義欄（已決策理由／open findings／"
                "授權／已驗未驗證據）以卡為 durable owner 禁重抄（task-recovery 十欄表「已有欄位不重抄」）"
            ),
        },
    }


# ---------- context-delivery budget（AC#5 括號枚舉四件＋上下界） ----------


def build_delivery_budget(slice: dict) -> dict:
    """DispatchSlice →context-delivery budget packet（transient；runtime-free 面）.

    AC#5 括號枚舉四件：artifact pointer（slice sink 指針非內容）、bounded receipt
    欄位集（照 dispatch_ledger 期望六欄投影，禁二刻）、collector state 指針
    （liveness source——collector 狀態權威在帳本，禁複製）、next read-set（slice
    role-dependent read-set 首讀面）。上下界：max_reinject_bytes——超界禁把完整
    歷史／穩定材料重貼進 dispatch，只給指針。runtime 未到面：dispatch_id 為 JIT
    時歸 jit_at_dispatch 槽，派工當下補。
    """
    w3 = w3_mod()
    mode, sink_path, _accept = _sink_face(slice)
    policy, pointers = _read_set_face(slice)
    carrier = _req_str(slice, "carrier")
    collection_mode = _req_str(slice, "collection_mode")
    declared_ledger = str(slice.get("ledger") or "").strip()
    dispatch_id = str(slice.get("dispatch_id") or "").strip()
    # 台帳 register 面 sink 為字串欄（artifact 路徑或 receipt-only 字面）——照抄其形
    declared: dict = {
        "carrier": carrier,
        "sink": sink_path if mode == "artifact" else "receipt-only",
        "collection_mode": collection_mode,
        "liveness_source": declared_ledger,
    }
    jit_slots = ["dispatched_at", "collector_owner"]
    if not dispatch_id or w3.is_jit_dispatch_id(dispatch_id):
        jit_slots.insert(0, "dispatch_id")
    else:
        declared["dispatch_id"] = dispatch_id
    return {
        "schema": SCHEMA_BUDGET,
        # artifact pointer——sink 指針非內容；receipt-only 無 artifact path（w3 契約同形空串）
        "artifact_pointer": {"mode": mode, "path": sink_path if mode == "artifact" else ""},
        # bounded receipt 欄位集——AC#3 liveness 六欄投影（單一源＝dispatch_ledger register 面）
        "bounded_receipt_fields": {
            "single_source": (
                "scripts/dispatch_ledger.py register 面——AC#3 liveness 六欄（本投影只列欄位集，禁二刻語義）"
            ),
            "declared": declared,
            "jit_at_dispatch": jit_slots,
        },
        # collector state 指針——狀態權威在 liveness 源帳本，禁複製進 packet
        "collector_state_pointer": w3.resolve_liveness_source(None, {"declared_ledger": declared_ledger}),
        "next_read_set": {"policy": policy, "pointers": pointers},
        "max_reinject_bytes": DEFAULT_MAX_REINJECT_BYTES,
        "reinjection_rule": "AC#5：超界禁把完整歷史／穩定材料重貼進 dispatch——只給指針",
    }


# ---------- semantic boundary 分類（AC#5） ----------


def is_semantic_boundary(transition: str) -> bool:
    """弧內 phase transition 分類：boundary 事件→True、其餘→False.

    boundary 枚舉＝BOUNDARY_TRANSITIONS（AC#5「semantic boundary」語義：plan
    recompile／budget 耗盡／window 跨越／worker terminal——ArcPlan/DispatchSlice
    在這些邊界上產 checkpoint obligation）。分類謂詞對枚舉外值恆 False——禁為
    未知 transition 發明語義；新 boundary 事件須先進枚舉（模組常數）才為真。
    """
    return str(transition).strip() in BOUNDARY_TRANSITIONS


# ---------- CLI（唯讀；packet 走 stdout） ----------


def _load_runtime_file(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheckpointObligationError(f"runtime 檔無法讀取：{path}（{exc}）") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckpointObligationError(f"runtime 檔無法解析（{exc}）：{path}") from exc
    if not isinstance(data, dict):
        raise CheckpointObligationError(
            f"runtime 須為 JSON object，got {type(data).__name__}：{path}"
        )
    return data


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AIR-135.7 W4 AC#5：checkpoint obligation＋context-delivery budget（packet 產出面；唯讀）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser(
        "build",
        help="semantic boundary 當下產 obligation＋budget packet（stdout pretty JSON；禁寫卡禁寫檔）",
    )
    build.add_argument("--slice", type=Path, required=True, help="dispatch artifact 路徑（```json fenced block、schema dispatch-slice/1）")
    build.add_argument("--runtime", type=Path, required=True, help="runtime facts JSON（dispatch_id／sink_state／liveness_source）")
    return parser.parse_args(argv)


def cmd_build(args: argparse.Namespace) -> int:
    w3 = w3_mod()
    try:
        try:
            text = args.slice.read_text(encoding="utf-8")
        except OSError as exc:
            raise CheckpointObligationError(
                f"dispatch artifact 無法讀取：{args.slice}（{exc}）"
            ) from exc
        slice_data = w3.parse_dispatch_slice(text, str(args.slice))
        runtime = _load_runtime_file(args.runtime)
        obligation = build_obligation(slice_data, runtime)
        budget = build_delivery_budget(slice_data)
    except CheckpointObligationError as exc:
        print(f"[FAIL] checkpoint_obligation: {exc}", file=sys.stderr)
        return 2
    except w3.LinkError as exc:
        print(f"[FAIL] checkpoint_obligation: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"obligation": obligation, "delivery_budget": budget}, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return cmd_build(args)


if __name__ == "__main__":
    sys.exit(main())
