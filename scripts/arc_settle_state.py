#!/usr/bin/env python
"""arc_settle_state——AIR-135.11 值星收線機械隊列：per-arc settle-state projection store。

邊界（卡面已決策勿重辯）：
- settle-state 是 per-arc projection state，**非 card truth 第二源**——每弧只存
  可重建的推進位置（七態＋authoritative artifact pointer＋seq），狀態真值仍在
  卡與收線動作的實據；轉移由收線動作顯式驅動（set／advance），禁後台自動推進
  （無 watcher、無 daemon——marshal 只吃 READY_TO_JUDGE queue）。per-arc
  **單寫者假設**：收線動作顯式驅動即隱含序列化（同一弧同一時點只有收線 CPU
  寫入；無鎖、無後台併發寫入面——repair-1 R4）。
- 七態：IMPLEMENTING / REVIEWING / READY_TO_JUDGE / NEEDS_REPAIR /
  READY_TO_LAND / LANDED / BLOCKED。

合法轉移表（卡面狀態圖＋任態→BLOCKED 逃逸線；LANDED 語義單一化＝repair-1
R2 裁決：LANDED 唯一合法後繼即 BLOCKED，BLOCKED 為唯一真終態）::

    IMPLEMENTING  → REVIEWING
    REVIEWING     → READY_TO_JUDGE
    READY_TO_JUDGE → READY_TO_LAND | NEEDS_REPAIR
    NEEDS_REPAIR  → IMPLEMENTING
    READY_TO_LAND → LANDED
    任態          → BLOCKED（逃逸線含 LANDED——landing 後發現問題走此線）
    BLOCKED       → （無——真終態，advance 一律 exit 2；show 仍可讀）

CLI（argparse＋fail-loud 風格照 scripts/arc_goal_compile.py；錯誤逐行 stderr、
文案列可用值、exit 2）：
- `set --arc A --state S --pointer P --dir D`——**僅限新建**（新 arc seq 從 1；
  既有 arc 拒收 exit 2「arc 已存在——用 advance 推進」——seq 單調合卡面，
  repair-1 R1：set 無覆寫面）。
- `advance --arc A --state S [--pointer P] --dir D`——現態→S 須合法轉移；
  非法＝逐行錯誤列「現態＋合法後繼」exit 2；seq+1；--pointer 缺省＝保留既有
  指針，給定＝全量更新（非空）。
- `show --arc A --dir D`——印現態＋指針＋seq。
- `queue --dir D --state S`——列出該 state 全部 arc（arc_id 排序；損壞 state
  檔 fail-loud 禁靜默跳過——狀態無聲消失是最危險失效形）。

state 檔：`<dir>/<arc_id>.json`＝{"schema": "arc-settle-state/1", "arc_id",
"state", "pointer"（非空）, "seq"（≥1 整數）} 恰五鍵；canonical JSON
（sort_keys＋緊湊分隔符，同 arc_spec／arc_goal_compile 慣例）；寫檔原子
（同目錄 tmp＋os.replace）；無時鐘依賴（seq 單調即序）。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCHEMA = "arc-settle-state/1"
STATES = (
    "IMPLEMENTING",
    "REVIEWING",
    "READY_TO_JUDGE",
    "NEEDS_REPAIR",
    "READY_TO_LAND",
    "LANDED",
    "BLOCKED",
)
# 合法轉移表——鍵集＝全態（缺鍵＝狀態機破洞，測試釘死）
TRANSITIONS: dict[str, tuple[str, ...]] = {
    "IMPLEMENTING": ("REVIEWING", "BLOCKED"),
    "REVIEWING": ("READY_TO_JUDGE", "BLOCKED"),
    "READY_TO_JUDGE": ("READY_TO_LAND", "NEEDS_REPAIR", "BLOCKED"),
    "NEEDS_REPAIR": ("IMPLEMENTING", "BLOCKED"),
    "READY_TO_LAND": ("LANDED", "BLOCKED"),
    "LANDED": ("BLOCKED",),
    "BLOCKED": (),
}

RECORD_KEYS = frozenset({"schema", "arc_id", "state", "pointer", "seq"})
# arc id＝檔名安全字元（禁路徑分隔／空白／前導點——traversal 防線）
ARC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class SettleStateError(Exception):
    """契約/狀態機錯——fail-loud（exit 2），不靜默。"""


def _validate_arc_id(arc_id: str) -> None:
    if not ARC_ID_RE.match(arc_id):
        raise SettleStateError(
            f"Invalid arc id `{arc_id}` — 須符合 [A-Za-z0-9][A-Za-z0-9._-]*"
            f"（檔名安全；禁路徑分隔／空白／前導點）"
        )


def _validate_state(state: str) -> None:
    if state not in STATES:
        raise SettleStateError(f"Invalid state `{state}` — 可用值: {', '.join(STATES)}")


def _validate_pointer(pointer: str) -> str:
    cleaned = pointer.strip()
    if not cleaned:
        raise SettleStateError(
            "pointer 不可為空——settle-state 每態須帶 authoritative artifact 指針"
            "（非空；禁佔位空白）"
        )
    return cleaned


def state_path(directory: Path, arc_id: str) -> Path:
    return directory / f"{arc_id}.json"


def load_state(path: Path) -> dict:
    """讀單一 state 檔＋完整性檢查（損壞比缺失更危險——fail-loud 禁靜默跳過）。"""
    if not path.exists():
        raise SettleStateError(f"state 檔不存在: {path}")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SettleStateError(f"state 檔 JSON 損壞: {path}（{e}）") from e
    if not isinstance(record, dict) or set(record) != set(RECORD_KEYS):
        raise SettleStateError(
            f"state 檔欄位契約違約: {path}——須恰為 {sorted(RECORD_KEYS)}"
        )
    if record["schema"] != SCHEMA:
        raise SettleStateError(
            f"state 檔 schema 不符: {path}（{record['schema']!r} != {SCHEMA!r}）"
        )
    if record["arc_id"] != path.name.removesuffix(".json"):
        raise SettleStateError(
            f"state 檔 arc_id 與檔名不符: {path}（arc_id={record['arc_id']!r}）"
        )
    _validate_state(record["state"])
    if not isinstance(record["pointer"], str) or not record["pointer"].strip():
        raise SettleStateError(f"state 檔 pointer 空白: {path}")
    seq = record["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
        raise SettleStateError(f"state 檔 seq 須為 ≥1 整數: {path}（{seq!r}）")
    return record


def save_state(directory: Path, record: dict) -> Path:
    """原子寫檔（同目錄 tmp＋os.replace）；canonical JSON；無時鐘依賴。"""
    directory.mkdir(parents=True, exist_ok=True)
    final = state_path(directory, record["arc_id"])
    tmp = directory / f".{record['arc_id']}.json.tmp"
    tmp.write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, final)
    return final


def _record(arc_id: str, state: str, pointer: str, seq: int) -> dict:
    return {
        "schema": SCHEMA,
        "arc_id": arc_id,
        "state": state,
        "pointer": pointer,
        "seq": seq,
    }


def cmd_set(args: argparse.Namespace) -> int:
    _validate_arc_id(args.arc)
    _validate_state(args.state)
    pointer = _validate_pointer(args.pointer)
    directory = Path(args.dir)
    if state_path(directory, args.arc).exists():
        # repair-1 R1：set 僅限新建——既有 arc 一律 advance 推進（seq 單調
        # 合卡面；fail-loud 禁靜默覆寫重置 seq）
        print(
            f"[arc-settle] ERROR: arc 已存在——用 advance 推進: "
            f"{state_path(directory, args.arc)}（現態查 show；set 不覆寫、"
            f"seq 不重置）",
            file=sys.stderr,
        )
        return 2
    path = save_state(directory, _record(args.arc, args.state, pointer, 1))
    print(f"[arc-settle] set {args.arc} -> {args.state} (seq=1) pointer={pointer}")
    print(f"[arc-settle] state file: {path}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    _validate_arc_id(args.arc)
    _validate_state(args.state)
    directory = Path(args.dir)
    record = load_state(state_path(directory, args.arc))
    current = record["state"]
    successors = TRANSITIONS[current]
    if args.state not in successors:
        # 逐行錯誤列「現態＋合法後繼」——fail-loud 禁靜默吞非法推進
        print(
            f"[arc-settle] ERROR: 非法轉移: 現態={current} 目標={args.state}",
            file=sys.stderr,
        )
        if successors:
            for successor in successors:
                print(f"[arc-settle]   合法後繼: {successor}", file=sys.stderr)
        else:
            print(
                f"[arc-settle]   合法後繼: （無——{current} 為終態，禁 advance）",
                file=sys.stderr,
            )
        return 2
    pointer = record["pointer"]
    if args.pointer is not None:
        pointer = _validate_pointer(args.pointer)
    new_seq = record["seq"] + 1
    path = save_state(directory, _record(args.arc, args.state, pointer, new_seq))
    print(
        f"[arc-settle] advance {args.arc}: {current} -> {args.state} "
        f"(seq={new_seq}) pointer={pointer}"
    )
    print(f"[arc-settle] state file: {path}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    _validate_arc_id(args.arc)
    record = load_state(state_path(Path(args.dir), args.arc))
    print(f"arc: {record['arc_id']}")
    print(f"state: {record['state']}")
    print(f"pointer: {record['pointer']}")
    print(f"seq: {record['seq']}")
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    _validate_state(args.state)
    directory = Path(args.dir)
    if not directory.is_dir():
        raise SettleStateError(f"queue 目錄不存在: {directory}")
    matches: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        # 損壞 state 檔 fail-loud——靜默跳過＝該弧狀態無聲消失
        record = load_state(path)
        if record["state"] == args.state:
            matches.append(record)
    for record in matches:
        print(
            f"{record['arc_id']} state={record['state']} "
            f"seq={record['seq']} pointer={record['pointer']}"
        )
    print(f"[arc-settle] queue {args.state}: {len(matches)} arc(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="arc_settle_state",
        description=(
            "AIR-135.11 值星收線機械隊列：per-arc settle-state projection store"
            "（七態狀態機；marshal 只吃 READY_TO_JUDGE queue）"
        ),
        epilog=(
            "settle-state 是 projection 非 card truth 第二源；轉移由收線動作顯式"
            "驅動（set／advance），禁後台自動推進"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="新建 arc state 檔（僅限新建；既有 arc 拒收，seq 從 1）")
    p_set.add_argument("--arc", required=True, help="arc id（檔名安全字元）")
    p_set.add_argument("--state", required=True, help=f"七態之一: {', '.join(STATES)}")
    p_set.add_argument("--pointer", required=True, help="authoritative artifact 指針（非空）")
    p_set.add_argument("--dir", required=True, help="settle-queue 目錄")
    p_set.set_defaults(func=cmd_set)

    p_adv = sub.add_parser("advance", help="現態→目標態（須合法轉移；seq+1）")
    p_adv.add_argument("--arc", required=True, help="arc id（檔名安全字元）")
    p_adv.add_argument("--state", required=True, help=f"七態之一: {', '.join(STATES)}")
    p_adv.add_argument(
        "--pointer",
        default=None,
        help="authoritative artifact 指針；缺省＝保留既有，給定＝全量更新（非空）",
    )
    p_adv.add_argument("--dir", required=True, help="settle-queue 目錄")
    p_adv.set_defaults(func=cmd_advance)

    p_show = sub.add_parser("show", help="印現態＋指針＋seq")
    p_show.add_argument("--arc", required=True, help="arc id（檔名安全字元）")
    p_show.add_argument("--dir", required=True, help="settle-queue 目錄")
    p_show.set_defaults(func=cmd_show)

    p_queue = sub.add_parser("queue", help="列出該 state 全部 arc")
    p_queue.add_argument("--dir", required=True, help="settle-queue 目錄")
    p_queue.add_argument("--state", required=True, help=f"七態之一: {', '.join(STATES)}")
    p_queue.set_defaults(func=cmd_queue)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SettleStateError as e:
        print(f"[arc-settle] ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
