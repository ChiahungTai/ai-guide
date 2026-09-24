#!/usr/bin/env python3
"""w3_checkpoint_link — AC#4 compiler 產出面接線：dispatch artifact → W2 期望台帳.

AIR-135.7 W3（arc-plan AIR-135.7#W3）：AC#4 的 bounded slices＋checkpoint
predicate 不能只靠 prompt 建議——由 AIR-135.1 compiler 編譯進 DispatchSlice
機器欄；本工具把該產出面接進 W2 期望登記台帳（scripts/dispatch_ledger.py 的
register 面），上游首例＝批量夜 #2 mini-batch 的 dispatch-W1.md（唯讀對接）。

三個子命令：

- extract：從 dispatch artifact 抽機器欄（```json fenced block、schema
  dispatch-slice/1），欄位級機驗單一源＝arc_spec.validate（compiler 自己的
  validator——本工具禁重刻欄位檢查）；再投影 checkpoint 契約（sink＋accept
  {predicate, anchors}）與 bounded slice 身分（slice_id／unit_id／plan 回指）。
- register：把 checkpoint 契約餵 W2 台帳（六欄＋anchor／anchors＋
  checkpoint_contract 溯源塊）。dispatch_id 為 JIT 佔位（JIT-AT-DISPATCH／
  UNRESOLVABLE*）時必須由 --dispatch-id 提供 marshal 派工當下的真實 id——
  fail loud，禁把佔位串寫進台帳。
- show：唯讀查詢台帳單一期望（--ledger＋--id），stdout 印 entry pretty JSON。
  id 解析：exact 命中 → `-` 邊界前綴恰一對應（語義平移自
  scripts/dispatch_ledger.py resolve_row）；零／多對應、台帳缺／毀／
  schema_version 非 1 皆 fail loud。show 禁寫台帳。

映射語義（欄位軸對照）：
- sink.mode=artifact → 台帳 sink 路徑＋anchor=首錨點（W2 sink 三步機驗消費
  單錨）；全錨點收進 anchors 供 collector 全驗。sink.mode=receipt-only →
  台帳 sink=receipt-only、不設單錨（bounded receipt 驗收歸 collector）。
- DispatchSlice 的 collection_mode（arc_spec 枚舉 waiter/bounded-receipt/
  manual）與 W2 台帳 collection-mode（card AC#3 語彙 foreground-wait/detached）
  是兩卡各定的詞彙軸——本工具不靜默映射：declared 值逐字收進
  checkpoint_contract.declared_collection_mode，台帳欄由 marshal 於派工面
  以 --collection-mode 決定（詞彙收斂前為已知 drift，發現即回報）。

exit 0＝成功；2＝契約／環境錯（artifact 缺、無／多 dispatch-slice block、
schema 不合、validator 未過、JIT id 未解析、台帳缺／毀／schema_version 非 1、
show id 無／多對應）——fail loud 禁靜默修復。
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

SCHEMA_DISPATCH_SLICE = "dispatch-slice/1"
KIND = "dispatch-slice"
STAGE = "dispatch"
SINK_MODES = ("artifact", "receipt-only")
JIT_MARKERS = ("JIT-AT-DISPATCH", "UNRESOLVABLE")
DEFAULT_LIVENESS_SOURCE = "bridge:jobs.json"

REPO_ROOT = Path(__file__).resolve().parents[1]
_FENCED_JSON = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


class LinkError(Exception):
    """接線面契約／環境錯——fail loud，禁靜默修復。"""


def _load_sibling(name: str, token: str):
    path = Path(__file__).resolve().with_name(name)
    spec = importlib.util.spec_from_file_location(f"_air1357_w3_{token}", path)
    if spec is None or spec.loader is None:
        raise LinkError(f"cannot load {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_LEDGER_MOD = None
_ARC_MOD = None


def ledger_mod():
    global _LEDGER_MOD
    if _LEDGER_MOD is None:
        _LEDGER_MOD = _load_sibling("dispatch_ledger.py", "dispatch_ledger")
    return _LEDGER_MOD


def arc_mod():
    global _ARC_MOD
    if _ARC_MOD is None:
        _ARC_MOD = _load_sibling("arc_spec.py", "arc_spec")
    return _ARC_MOD


# ---------- dispatch artifact 解析（唯讀） ----------


def parse_dispatch_slice(text: str, source: str) -> dict:
    """抽 schema=dispatch-slice/1 的機器欄；欄位機驗單一源＝arc_spec.validate."""
    blocks = _FENCED_JSON.findall(text)
    if not blocks:
        raise LinkError(f"{source} 內無 ```json fenced block——dispatch artifact 機器欄缺（校驗入口契約）")
    parsed: list[dict] = []
    for i, raw in enumerate(blocks, start=1):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LinkError(f"{source} 第 {i} 個 ```json block 無法解析（{exc}）——禁靜默跳過") from exc
        if not isinstance(data, dict):
            raise LinkError(f"{source} 第 {i} 個 ```json block 非 JSON object（{type(data).__name__}）")
        parsed.append(data)
    matches = [d for d in parsed if d.get("schema") == SCHEMA_DISPATCH_SLICE]
    if not matches:
        found = sorted({str(d.get("schema")) for d in parsed})
        raise LinkError(
            f"{source} 內無 schema={SCHEMA_DISPATCH_SLICE} 機器欄；可用 schema：{SCHEMA_DISPATCH_SLICE}；實際找到：{found}"
        )
    if len(matches) > 1:
        ids = [str(d.get("slice_id") or "<unnamed>") for d in matches]
        raise LinkError(f"{source} 含多個 dispatch-slice block（{ids}）——一 artifact 一 slice，禁靜默擇一")
    data = matches[0]
    arc = arc_mod()
    try:
        errors = arc.validate(KIND, data, STAGE)
    except arc.ArcSpecError as exc:
        raise LinkError(f"{source} dispatch-slice 契約錯（arc_spec.validate）：{exc}") from exc
    if errors:
        details = "\n".join(f"  - {e}" for e in errors)
        raise LinkError(
            f"{source} dispatch-slice validator 未過（{len(errors)} 項；單一驗證源＝arc_spec）：\n{details}"
        )
    return data


def is_jit_dispatch_id(value: str) -> bool:
    stripped = value.strip()
    return not stripped or any(marker in stripped for marker in JIT_MARKERS)


def extract_checkpoint(artifact: Path) -> dict:
    """讀 dispatch artifact →checkpoint 契約投影（validator 未過即 LinkError）.

    欄位機驗單一源＝arc_spec.validate（sink.path 非空等欄位面）；validator 對
    accept 內鍵「有鍵才驗」——artifact 模式的 predicate／anchors 非空由本函式
    的台帳映射面守衛把關（錨點機驗面＝terminal≠complete，禁靜默收空）。
    """
    try:
        text = artifact.read_text(encoding="utf-8")
    except OSError as exc:
        raise LinkError(f"dispatch artifact 無法讀取：{artifact}（{exc}）") from exc
    data = parse_dispatch_slice(text, str(artifact))
    sink = data["sink"]
    accept = data.get("accept") or {}
    mode = str(sink.get("mode"))
    if mode not in SINK_MODES:  # validator 對 sink.mode 缺鍵不擋（有值才驗）——映射面 fail loud
        raise LinkError(f"{artifact} 未知 sink mode `{mode}`；可用值：{'、'.join(SINK_MODES)}")
    predicate = str(accept.get("predicate") or "").strip()
    anchors = [str(a).strip() for a in (accept.get("anchors") or [])]
    if mode == "artifact":
        # validator 對 accept 內鍵為「有鍵才驗」——accept={} 能過欄位驗證；
        # 台帳映射面不可靜默收下空 checkpoint predicate（錨點機驗面＝terminal≠complete）
        if not predicate:
            raise LinkError(f"{artifact} sink.mode=artifact 但 accept.predicate 空——checkpoint predicate 必填")
        if not anchors:
            raise LinkError(f"{artifact} sink.mode=artifact 但 accept.anchors 空——無錨點的 checkpoint 無法機驗")
    return {
        "schema": SCHEMA_DISPATCH_SLICE,
        "source_artifact": str(artifact),
        "dispatch_id": str(data.get("dispatch_id") or "").strip(),
        "dispatch_id_jit": is_jit_dispatch_id(str(data.get("dispatch_id") or "")),
        "carrier": str(data.get("carrier") or "").strip(),
        "declared_collection_mode": str(data.get("collection_mode") or "").strip(),
        "declared_ledger": str(data.get("ledger") or "").strip(),
        "sink": {
            "mode": mode,
            "path": str(sink.get("path") or "").strip(),
        },
        "accept": {
            "predicate": predicate,
            "anchors": anchors,
        },
        "slice": {
            "slice_id": str(data.get("slice_id") or "").strip(),
            "unit_id": str(data.get("unit_id") or "").strip(),
            "card_id": str(data.get("card_id") or "").strip(),
            "card_baseline": str(data.get("card_baseline") or "").strip(),
            "plan_version": data.get("plan_version"),
            "plan_hash": str(data.get("plan_hash") or "").strip(),
        },
    }


# ---------- 台帳映射（W2 register 面） ----------


def resolve_liveness_source(explicit: str | None, contract: dict) -> str:
    """--liveness-source 覆寫 → slice ledger 欄逐字 → bridge 預設（六欄不可空）."""
    return (explicit or "").strip() or contract["declared_ledger"] or DEFAULT_LIVENESS_SOURCE


def build_entry(
    contract: dict,
    dispatch_id: str,
    collection_mode: str,
    collector_owner: str,
    liveness_source: str,
    dispatched_at: str,
) -> dict:
    """checkpoint 契約 →W2 台帳 entry（六欄＋anchor/anchors＋溯源塊）."""
    sink = contract["sink"]
    anchors = contract["accept"]["anchors"]
    entry: dict = {
        "dispatch_id": dispatch_id,
        "carrier": contract["carrier"],
        "dispatched_at": dispatched_at,
        "sink": sink["path"] if sink["mode"] == "artifact" else "receipt-only",
        "collection_mode": collection_mode,
        "collector_owner": collector_owner,
        "liveness_source": liveness_source,
    }
    if sink["mode"] == "artifact" and anchors:
        entry["anchor"] = anchors[0]  # W2 sink 三步機驗消費單錨
    if anchors:
        entry["anchors"] = anchors  # 全錨點收驗歸 collector
    entry["checkpoint_contract"] = {
        "source_artifact": contract["source_artifact"],
        "compiled_schema": contract["schema"],
        "slice_id": contract["slice"]["slice_id"],
        "unit_id": contract["slice"]["unit_id"],
        "plan_version": contract["slice"]["plan_version"],
        "plan_hash": contract["slice"]["plan_hash"],
        "accept_predicate": contract["accept"]["predicate"],
        "declared_collection_mode": contract["declared_collection_mode"],
    }
    return entry


# ---------- 台帳唯讀查詢（show 面——禁寫台帳） ----------


def load_expectation_ledger(path: Path) -> dict:
    """show 面唯讀載入：缺檔／毀損／schema_version 非 1 → LinkError（CLI exit 2）."""
    led = ledger_mod()
    try:
        doc = led.load_ledger(path)  # 台帳解析 schema 單一源＝dispatch_ledger.load_ledger
    except led.LedgerError as exc:  # LedgerMissing（缺檔）在 show 面同為環境錯
        raise LinkError(str(exc)) from exc
    version = doc.get("schema_version")
    if isinstance(version, bool) or version != 1:  # bool 是 int 子類——JSON true 不得冒充 1
        raise LinkError(f"台帳 schema_version 非 1（實際 {version!r}）：{path}")
    return doc


def find_expectation(ledger: dict, dispatch_id: str) -> dict:
    """--id 解析：exact 命中 key，否則 `-` 邊界前綴恰一對應；零／多對應 fail loud.

    語義平移自 dispatch_ledger.resolve_row（該處吃 dict[str, ActualRow]，台帳
    key 面型別不合故平移）；前綴軸同為 `id + "-"` 邊界（與 resolve_row 一致）
    ——兩處禁各自漂移，改語義須對照單一源同步。
    """
    expectations = ledger["expectations"]
    if dispatch_id in expectations:
        return expectations[dispatch_id]
    matches = sorted(full for full in expectations if full.startswith(dispatch_id + "-"))
    if len(matches) == 1:
        return expectations[matches[0]]
    if matches:
        raise LinkError(f"台帳 id `{dispatch_id}` 前綴撞多（前 3：{matches[:3]}）——禁靜默擇一")
    raise LinkError(f"台帳無此期望 id `{dispatch_id}`（exact 與 `-` 邊界前綴皆無對應）")


# ---------- CLI ----------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    led = ledger_mod()
    parser = argparse.ArgumentParser(
        description="AC#4 compiler 產出面接線：dispatch artifact → W2 期望台帳（AIR-135.7 W3）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ext = sub.add_parser("extract", help="唯讀抽取 checkpoint 契約（validator 單一源＝arc_spec）")
    ext.add_argument("--artifact", type=Path, required=True, help="dispatch artifact 路徑（如 mini-batch dispatch-W1.md）")
    ext.add_argument("--json", action="store_true", help="機器可讀 JSON 輸出")

    reg = sub.add_parser("register", help="checkpoint 契約餵 W2 台帳（dispatch 當下登記）")
    reg.add_argument("--artifact", type=Path, required=True, help="dispatch artifact 路徑")
    reg.add_argument("--dispatch-id", default=None, help="派工當下真實 id（bridge job id 或 zcode-native session/agent 路徑）；artifact 為 JIT 佔位時必填")
    reg.add_argument("--collection-mode", choices=list(led.COLLECTION_MODES), default="detached")
    reg.add_argument("--collector-owner", default="marshal")
    reg.add_argument("--liveness-source", default=None, help="預設＝slice ledger 欄逐字，次選 bridge:jobs.json")
    reg.add_argument("--at", default=None, help="dispatch 時間 ISO（預設現在；wall-clock UTC 語意）")
    reg.add_argument("--ledger", type=Path, default=led.DEFAULT_LEDGER)

    shw = sub.add_parser("show", help="唯讀查詢台帳單一期望（pretty JSON；禁寫台帳）")
    shw.add_argument("--ledger", type=Path, required=True, help="W2 台帳路徑（show 面必填）")
    shw.add_argument("--id", dest="dispatch_id", required=True, help="dispatch id（exact 或 `-` 邊界前綴恰一對應）")
    return parser.parse_args(argv)


def cmd_extract(args: argparse.Namespace) -> int:
    try:
        contract = extract_checkpoint(args.artifact)
    except LinkError as exc:
        print(f"[FAIL] w3_checkpoint_link: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(contract, ensure_ascii=False, indent=2))
        return 0
    sink = contract["sink"]
    jit_note = "（JIT 佔位——register 時以 --dispatch-id 提供）" if contract["dispatch_id_jit"] else ""
    lines = [
        f"slice：{contract['slice']['slice_id']}（unit {contract['slice']['unit_id']}，plan v{contract['slice']['plan_version']}，hash {contract['slice']['plan_hash'][:12]}…）",
        f"sink：{sink['mode']} {sink['path']}".rstrip(),
        f"checkpoint predicate：{contract['accept']['predicate']}；錨點：{contract['accept']['anchors']}",
        f"dispatch_id：{contract['dispatch_id']}{jit_note}",
        f"carrier：{contract['carrier']}；declared collection_mode：{contract['declared_collection_mode']}",
    ]
    print("\n".join(lines))
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    led = ledger_mod()
    try:
        contract = extract_checkpoint(args.artifact)
    except LinkError as exc:
        print(f"[FAIL] w3_checkpoint_link: {exc}", file=sys.stderr)
        return 2
    override = (args.dispatch_id or "").strip()
    if contract["dispatch_id_jit"] and is_jit_dispatch_id(override):
        print(
            "[FAIL] w3_checkpoint_link: dispatch_id 為 JIT 佔位（"
            f"{contract['dispatch_id'] or '空值'}）——register 時以 --dispatch-id 提供 marshal 派工"
            "當下的真實 id（bridge job id 或 zcode-native session/agent 路徑）；禁把佔位串寫進台帳",
            file=sys.stderr,
        )
        return 2
    dispatch_id = override or contract["dispatch_id"]
    try:
        ledger = led.load_ledger_or_new(args.ledger)  # 毀損台帳在此 fail loud，不覆寫
    except led.LedgerError as exc:
        print(f"[FAIL] w3_checkpoint_link: {exc}", file=sys.stderr)
        return 2
    try:
        dispatched_at = led.iso(led.parse_iso(args.at)) if args.at else led.iso(led.utc_now())
    except ValueError as exc:
        print(f"[FAIL] w3_checkpoint_link: --at 無法解析（{exc}）", file=sys.stderr)
        return 2
    liveness_source = resolve_liveness_source(args.liveness_source, contract)
    entry = build_entry(contract, dispatch_id, args.collection_mode, args.collector_owner, liveness_source, dispatched_at)
    entry["registered_at"] = led.iso(led.utc_now())
    existed = dispatch_id in ledger["expectations"]
    led.save_json_atomic(args.ledger, led.register_expectation(ledger, entry))
    action = "update" if existed else "registered"
    anchor_note = entry.get("anchor") or "receipt-only（無單錨）"
    print(
        f"[OK] w3_checkpoint_link: {action} {dispatch_id} → {args.ledger}"
        f"（slice {contract['slice']['slice_id']}，錨點 {anchor_note}）",
        file=sys.stderr,
    )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        ledger = load_expectation_ledger(args.ledger)
        entry = find_expectation(ledger, args.dispatch_id)
    except LinkError as exc:
        print(f"[FAIL] w3_checkpoint_link: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "extract":
        return cmd_extract(args)
    if args.command == "show":
        return cmd_show(args)
    return cmd_register(args)


if __name__ == "__main__":
    sys.exit(main())
