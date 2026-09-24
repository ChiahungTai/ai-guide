#!/usr/bin/env python3
"""dispatch_ledger — dispatch 期望登記台帳＋唯讀 sweep reporter（AIR-135.7 AC#3／AC#6）.

0924 審查缺口：liveness.jsonl（bridge_waiter 事件流）是運行事件流，不是 dispatch
期望登記——本工具把「期望面」分出來，期望與實際分欄：

- 期望面：dispatch 當下以 liveness 六欄登記（AC#3：dispatch id／carrier／dispatch
  時間 wall-clock UTC／sink／collection mode＋owner／liveness source），JSON 台帳住
  `.agent-tmp/dispatch-expectations.json`（gitignored 面）——registry 只存期望，
  實際狀態權威在 bridge 帳本，漂移即訊號。
- 實際面：bridge jobs.json（兩帳本——ai-guide＋delegate-bridge 兩 state root）的
  終態 row，唯讀對接；sweep 報告把期望 vs 實際分欄並列。

sweep（AC#6②）＝唯讀 reporter：只報狀態轉移不報存量（上次掃描 vs 本次的 delta；
reporter 記憶住 `.agent-tmp/dispatch-sweep-state.json`——sweep 唯一寫入面，可刪、
刪了下次視為首次掃描全量回報）；偵測與處置分離——永不自動重派／殺。
exit 0＝有單（有轉移可報）、1＝無單、2＝環境錯（台帳缺／毀、state root 缺）。
"""

import argparse
import datetime as dt
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 1
RUNNING = "running"
COMPLETED = "completed"
COLLECTION_MODES = ("foreground-wait", "detached")

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = REPO_ROOT / ".agent-tmp" / "dispatch-expectations.json"
DEFAULT_SWEEP_STATE = REPO_ROOT / ".agent-tmp" / "dispatch-sweep-state.json"
DEFAULT_SINK_BASE = REPO_ROOT
# bridge ledger 是 per-repo 的——兩帳本與 agent_liveness_sweep v1 同根
DEFAULT_STATE_ROOTS = (
    Path("/Users/ctai/Github/ai-guide/.delegate-bridge"),
    Path("/Users/ctai/Github/delegate-bridge/.delegate-bridge"),
)


class LedgerError(Exception):
    """台帳面環境錯誤（缺檔／毀損／schema 不合）——fail loud，禁靜默修復。"""


class LedgerMissing(LedgerError):
    """台帳檔不存在（查詢/sweep 面視為環境錯；register 面視為首建）。"""


@dataclass
class ActualRow:
    """bridge jobs.json 單一 row 的指針（實際面非權威複製——權威仍在帳本）。"""

    dispatch_id: str
    root: Path
    status: str


# ---------- 時間 ----------


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def iso(value: dt.datetime) -> str:
    return value.isoformat(timespec="seconds")


def parse_iso(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)  # naive 按 AC#3 wall-clock UTC 語意
    return parsed.astimezone(dt.UTC)  # 台帳統一正規化 UTC


# ---------- 台帳（期望面） ----------


def empty_ledger_doc() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "contract": "AIR-135.7 AC#3 collection contract＋AC#6 liveness ledger",
        "note": "registry 只存期望；實際狀態權威＝bridge jobs.json（唯讀對接），漂移即訊號",
        "expectations": {},
    }


def load_ledger(path: Path) -> dict:
    if not path.exists():
        raise LedgerMissing(f"台帳不存在：{path}（先 register 建立期望）")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise LedgerError(f"台帳無法解析（{exc}）——禁靜默修復：{path}") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("expectations"), dict):
        raise LedgerError(f"台帳 schema 不合（缺 expectations dict）：{path}")
    return doc


def load_ledger_or_new(path: Path) -> dict:
    if not path.exists():
        return empty_ledger_doc()
    return load_ledger(path)


def save_json_atomic(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def register_expectation(doc: dict, entry: dict) -> dict:
    doc["expectations"][entry["dispatch_id"]] = entry
    return doc


# ---------- 實際面（bridge jobs.json——唯讀） ----------


def load_actual_index(state_roots: list[Path]) -> dict[str, ActualRow]:
    index: dict[str, ActualRow] = {}
    for root in state_roots:
        rows_path = root / "jobs.json"
        if not rows_path.exists():
            continue
        try:
            rows = json.loads(rows_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[WARN] dispatch_ledger: {rows_path} 無法解析（{exc}）——該根以缺席計", file=sys.stderr)
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("status"), str):
                index[row["id"]] = ActualRow(dispatch_id=row["id"], root=root, status=row["status"])
    return index


def resolve_row(dispatch_id: str, index: dict[str, ActualRow]) -> tuple[ActualRow | None, str]:
    """exact 命中→唯一前綴對應（短形 id job-mu7xpicu vs 全形 job-mu7px22a-b1ccwa）。"""
    if dispatch_id in index:
        return index[dispatch_id], ""
    matches = sorted(full for full in index if full.startswith(dispatch_id))
    if len(matches) == 1:
        return index[matches[0]], f"前綴對應 {matches[0]}"
    if len(matches) > 1:
        return None, f"id 前綴撞多 row（{matches[:3]}）——保守視為未解析"
    return None, ""


# ---------- sink 三步（存在→非空→錨點）與狀態判定 ----------


def sink_verdict(entry: dict, row: ActualRow | None, sink_base: Path) -> tuple[bool, str]:
    sink = str(entry.get("sink") or "")
    if sink == "receipt-only":
        if row is not None:
            # bounded receipt 非空驗收歸 collector（AC#2）——sweep 只驗實際面 row 在場，不代驗
            return True, "receipt-only：實際面 row 在場；bounded receipt 驗收歸 collector（sweep 不代驗）"
        return False, "receipt-only：實際面無 row"
    if not sink:
        return False, "sink 欄空值"
    path = Path(sink) if sink.startswith("/") else sink_base / sink
    if not path.exists():
        return False, f"{sink} 缺"
    try:
        size = path.stat().st_size
    except OSError as exc:
        return False, f"{sink} stat-fail（{exc}）"
    if size == 0:
        return False, f"{sink} 空"
    anchor = str(entry.get("anchor") or "")
    if not anchor:
        return True, f"{sink} 存在＋非空；錨點人工（未登記 anchor）"
    try:
        content = path.read_text(encoding="utf-8", errors="replace")[:200_000]
    except OSError as exc:
        return False, f"{sink} read-fail（{exc}）"
    if anchor in content:
        return True, f"{sink} 三步過（錨點 {anchor}）"
    return False, f"{sink} 非空但無錨點（{anchor}）"


def status_of(entry: dict, row: ActualRow | None, resolve_note: str, sink_base: Path) -> tuple[str, str]:
    """期望 vs 實際 join 出單一狀態：in-flight／matched／sink-missing／terminal-drift／unresolved。"""
    if row is None:
        note = resolve_note or "實際面查無 row（bridge 兩帳本皆無——非 bridge 載體或 spawn 未落帳）"
        return "unresolved", note
    if row.status == RUNNING:
        return "in-flight", f"實際面 running @ {row.root.name}"
    ok, sink_note = sink_verdict(entry, row, sink_base)
    if row.status != COMPLETED:
        # bridge persisted status set 是 OPEN（job.rs is_known_status）——非 running 未知名一律視 terminal face
        return "terminal-drift", f"實際面 terminal={row.status} @ {row.root.name}；sink：{sink_note}"
    if ok:
        return "matched", f"實際面 completed @ {row.root.name}；sink：{sink_note}"
    return "sink-missing", f"terminal-sink-missing（completed 但 sink 驗收不過）；{sink_note}"


def compute_statuses(ledger: dict, index: dict[str, ActualRow], sink_base: Path) -> dict[str, dict]:
    expectations = ledger["expectations"]
    result: dict[str, dict] = {}
    for dispatch_id, raw_entry in expectations.items():
        if not isinstance(raw_entry, dict):
            raise LedgerError(f"台帳 schema 不合（{dispatch_id} 非 dict）")
        row, resolve_note = resolve_row(dispatch_id, index)
        status, note = status_of(raw_entry, row, resolve_note, sink_base)
        result[dispatch_id] = {
            "status": status,
            "note": note,
            "actual_status": row.status if row else None,
            "actual_root": str(row.root) if row else None,
        }
    return result


# ---------- sweep（唯讀 reporter——只報轉移） ----------


def load_sweep_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise LedgerError(f"sweep state 無法解析（{exc}）——刪除該檔可重置為首次掃描：{path}") from exc
    statuses = doc.get("statuses") if isinstance(doc, dict) else None
    if not isinstance(statuses, dict):
        raise LedgerError(f"sweep state schema 不合（缺 statuses dict）：{path}")
    return {str(key): str(value) for key, value in statuses.items()}


def save_sweep_state(path: Path, statuses: dict[str, str]) -> None:
    save_json_atomic(path, {"statuses": statuses, "updated_at": iso(utc_now())})


def diff_transitions(last: dict[str, str], current: dict[str, dict]) -> list[dict]:
    transitions: list[dict] = []
    for dispatch_id in sorted(set(last) | set(current)):
        if dispatch_id not in current:
            transitions.append(
                {"dispatch_id": dispatch_id, "kind": "removed", "from": last[dispatch_id], "to": None, "note": "台帳已無此期望"}
            )
            continue
        info = current[dispatch_id]
        if dispatch_id not in last:
            kind = "new"
        elif last[dispatch_id] != info["status"]:
            kind = "change"
        else:
            continue
        transitions.append(
            {
                "dispatch_id": dispatch_id,
                "kind": kind,
                "from": None if kind == "new" else last[dispatch_id],
                "to": info["status"],
                "note": info["note"],
                "actual_status": info["actual_status"],
                "actual_root": info["actual_root"],
            }
        )
    return transitions


def run_sweep(
    ledger_path: Path,
    state_roots: list[Path],
    sink_base: Path,
    state_path: Path,
    as_json: bool,
) -> tuple[int, str]:
    ledger = load_ledger(ledger_path)
    index = load_actual_index(state_roots)
    current = compute_statuses(ledger, index, sink_base)
    last = load_sweep_state(state_path)
    transitions = diff_transitions(last, current)
    save_sweep_state(state_path, {key: value["status"] for key, value in current.items()})
    now = utc_now()
    if as_json:
        payload = {
            "generated_at": iso(now),
            "ledger": str(ledger_path),
            "state_roots": [str(root) for root in state_roots],
            "counts": {"expectations": len(current), "transitions": len(transitions)},
            "transitions": transitions,
            "read_only": True,
            "disposition": "偵測與處置分離——永不自動重派／殺（AC#6②）",
        }
        return (0 if transitions else 1), json.dumps(payload, ensure_ascii=False, indent=2)
    lines = [
        f"dispatch ledger sweep（唯讀 reporter——只報轉移不報存量）"
        f" | 台帳 {ledger_path} | expectations={len(current)} transitions={len(transitions)}"
        f" | {now.strftime('%Y-%m-%d %H:%M')} UTC"
    ]
    for tr in transitions:
        if tr["kind"] == "removed":
            lines.append(f"- {tr['dispatch_id']} | removed（was {tr['from']}）| 台帳已無此期望")
        elif tr["kind"] == "new":
            lines.append(f"- {tr['dispatch_id']} | new {tr['to']} | {tr['note']}")
        else:
            lines.append(f"- {tr['dispatch_id']} | {tr['from']} → {tr['to']} | {tr['note']}")
    if not transitions:
        lines.append("（無狀態轉移）")
    lines.append("[ACTION] 處置分離：本工具唯讀——永不自動重派／殺；依 AIR-135.7 契約由 Marshal 裁決")
    return (0 if transitions else 1), "\n".join(lines)


# ---------- CLI ----------


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="dispatch 期望登記台帳＋唯讀 sweep reporter（AIR-135.7 AC#3／AC#6）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    reg = sub.add_parser("register", help="dispatch 當下登記期望（liveness 六欄）")
    reg.add_argument("--id", dest="dispatch_id", required=True, help="dispatch id（bridge job id 或 zcode-native session/agent 路徑）")
    reg.add_argument("--carrier", required=True, help="carrier（glm／muse／codex／zcode-native——決定 stuck 閾值）")
    reg.add_argument("--sink", default="receipt-only", help="artifact 預期路徑；收斂型查證填 receipt-only（預設）")
    reg.add_argument("--collection-mode", choices=list(COLLECTION_MODES), default="detached")
    reg.add_argument("--collector-owner", default="marshal")
    reg.add_argument("--liveness-source", default="bridge:jobs.json", help="metadata.json 或 jobs.json 所屬 ledger")
    reg.add_argument("--anchor", default=None, help="sink 錨點 token（三步機驗第三步；未登記＝錨點人工）")
    reg.add_argument("--at", default=None, help="dispatch 時間 ISO（預設現在；wall-clock UTC 語意）")
    reg.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)

    show = sub.add_parser("show", help="查詢台帳（存量視圖——sweep 才是轉移面）")
    show.add_argument("--id", dest="dispatch_id", default=None)
    show.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)

    swp = sub.add_parser("sweep", help="唯讀 sweep reporter——只報狀態轉移（exit 0 有單／1 無單）")
    swp.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    swp.add_argument("--state-root", type=Path, nargs="+", default=None, metavar="DIR", help="bridge 狀態根（預設＝ai-guide＋delegate-bridge 兩根）")
    swp.add_argument("--sink-base", type=Path, default=DEFAULT_SINK_BASE, help="相對 sink 路徑解析基準（預設 repo root）")
    swp.add_argument("--state", type=Path, default=DEFAULT_SWEEP_STATE, help="reporter 記憶（sweep 唯一寫入面；刪除＝重置首次掃描）")
    swp.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def cmd_register(args: argparse.Namespace) -> int:
    try:
        dispatched_at = iso(parse_iso(args.at)) if args.at else iso(utc_now())
    except ValueError as exc:
        print(f"[FAIL] dispatch_ledger: --at 無法解析（{exc}）", file=sys.stderr)
        return 2
    if not args.dispatch_id.strip() or not args.carrier.strip():
        print("[FAIL] dispatch_ledger: --id／--carrier 不可空", file=sys.stderr)
        return 2
    if not args.sink.strip():
        print("[FAIL] dispatch_ledger: --sink 不可空（artifact 路徑或 receipt-only）", file=sys.stderr)
        return 2
    try:
        ledger = load_ledger_or_new(args.ledger)  # 毀損台帳在此 fail loud，不覆寫
    except LedgerError as exc:
        print(f"[FAIL] dispatch_ledger: {exc}", file=sys.stderr)
        return 2
    existed = args.dispatch_id in ledger["expectations"]
    entry = {
        "dispatch_id": args.dispatch_id,
        "carrier": args.carrier,
        "dispatched_at": dispatched_at,
        "sink": args.sink,
        "collection_mode": args.collection_mode,
        "collector_owner": args.collector_owner,
        "liveness_source": args.liveness_source,
    }
    if args.anchor:
        entry["anchor"] = args.anchor
    entry["registered_at"] = iso(utc_now())
    save_json_atomic(args.ledger, register_expectation(ledger, entry))
    action = "update" if existed else "registered"
    print(f"[OK] dispatch_ledger: {action} {args.dispatch_id} → {args.ledger}", file=sys.stderr)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        ledger = load_ledger(args.ledger)
    except LedgerMissing as exc:
        print(f"[FAIL] dispatch_ledger: {exc}", file=sys.stderr)
        return 1
    except LedgerError as exc:
        print(f"[FAIL] dispatch_ledger: {exc}", file=sys.stderr)
        return 2
    if args.dispatch_id is None:
        print(json.dumps(ledger, ensure_ascii=False, indent=2))
        return 0
    entry = ledger["expectations"].get(args.dispatch_id)
    if entry is None:
        print(f"[FAIL] dispatch_ledger: 台帳無此期望 {args.dispatch_id}", file=sys.stderr)
        return 1
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    if args.state_root:
        missing = [root for root in args.state_root if not root.is_dir()]
        if missing:
            print(f"[FAIL] dispatch_ledger: state root 不存在：{missing}", file=sys.stderr)
            return 2
        state_roots = list(args.state_root)
    else:
        state_roots = [root for root in DEFAULT_STATE_ROOTS if root.is_dir()]
        if not state_roots:
            print(f"[FAIL] dispatch_ledger: 無可用的預設 state root（{DEFAULT_STATE_ROOTS}）", file=sys.stderr)
            return 2
    try:
        code, output = run_sweep(args.ledger, state_roots, args.sink_base, args.state, args.json)
    except LedgerError as exc:
        print(f"[FAIL] dispatch_ledger: {exc}", file=sys.stderr)
        return 2
    print(output)
    label = "有單" if code == 0 else "無單"
    print(f"[OK] dispatch_ledger sweep: exit={code}（{label}）", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "register":
        return cmd_register(args)
    if args.command == "show":
        return cmd_show(args)
    return cmd_sweep(args)


if __name__ == "__main__":
    sys.exit(main())
