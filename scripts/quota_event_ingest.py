#!/usr/bin/env python3
"""quota_event_ingest——quota-event ingress closure（AIR-244）。

補上 AIR-239「reader 有、writer 無」的 contract hole：把持有原始 provider
failure message 的 authoritative failure surface——bridge 台帳 jobs.json 的
`errorExcerpt` 欄（dispatch 失敗時 bridge 記帳的原始錯誤節錄；實證 298 rows
中 19 筆全落在 failure 態，completed 零出現）——分類成額度事件，append 到
`<probe-dir>/quota-events.jsonl`（entitlement_window_snapshot 的 intake 載體
D2）。閉環：writer 寫出的 raw row 由既有 reader 重 parse（parser 單一源
probe_entitlements.capture_quota_event）→ state=unavailable＋retryable_at。

兩個生產入口（同一分類/寫入路徑）：
- `ingest-event`——單事件顯式 ingest（family/message/observed-at 由呼叫端
  給；session 從 spawn 失敗階梯／DispatchTrace 手動接線用）。
- `ingest`——bridge ledger sweep：讀 jobs.json（預設兩 state root，同
  dispatch_ledger.DEFAULT_STATE_ROOTS 慣例），對帶 errorExcerpt 的 row 逐一
  分類（觸發面＝errorExcerpt 在場，signature 分類歸 parser——ledger status
  分類開放集，白名單化會靜默漏未來 failure 類別）。

契約（codex 審核 §B 項目 2 釘死面）：
- 簽名命中 → 恰一筆 `{"family","message","observed_at_utc"}` append（三鍵
  verbatim 禁加工——reader intake 契約＝raw message）。
- 簽名未中（None，含 1302 rate-path／426 websocket）→ 0 筆——unknown
  signature 禁偽造；事件檔不建（缺席＝零事件，reader D2）。
- family 非白名單／observed-at 非 ISO → fail-loud exit 2 禁透傳；sweep 全程
  all-or-nothing——分類完全部 row 才落盤，途中有 malformed 即整批零寫入。
- 冪等：同 (family, message, observed_at_utc) 已在檔（或同批重複）→ skip
  不重複寫——重跑 sweep 恰一筆不變。
- whitelist-外 family（ledger 實證含 grok）＝不在 quota-event 契約內 →
  skip＋計數（skip 非偽造；fail-loud 只留給契約內資料的 malformed）。
- evaluator-not-router：只 intake 事件，禁任何 availability/retry 判讀欄位
  （判讀歸 entitlement_window_snapshot 重 parse；本檔無時鐘——observed_at
  一律來自 surface verbatim）。

已知限制（journal 記錄）：真實 GLM 1308 訊息的重置時間戳為空格格式
（"reset at 2026-09-28 17:00:20"），parser 的 ISO 簽名只認 T 格式 →
retryable_at=unknown（reader 端 retryable_at=None）。parser 單一源行為，
本卡不動 probe 檔；閉環的 retryable 帶值路徑由 ISO 格式簽名承載。

用法：
  uv run python scripts/quota_event_ingest.py ingest-event \
      --family glm --message "<failure message>" --observed-at <ISO Z> \
      [--probe-dir ~/.agents/probe-entitlements]
  uv run python scripts/quota_event_ingest.py ingest \
      [--ledger PATH]... [--probe-dir ~/.agents/probe-entitlements]

exit：0＝完成（含 0 筆新事件）；2＝輸入缺席或不合法（fail-loud）。
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBE_DIR = Path.home() / ".agents/probe-entitlements"
# bridge 台帳兩 state root（同 dispatch_ledger.DEFAULT_STATE_ROOTS 慣例——
# bridge jobs 帳本是 per-repo＋delegate-bridge 本體兩處）
DEFAULT_LEDGERS = (
    Path("/Users/ctai/Github/ai-guide/.delegate-bridge/jobs.json"),
    Path("/Users/ctai/Github/delegate-bridge/.delegate-bridge/jobs.json"),
)
EVENT_KEYS = ("family", "message", "observed_at_utc")


class IngestInputError(Exception):
    """輸入缺席或不合法——fail-loud exit 2（損壞比缺失危險）。"""


def _load_repo_module(rel: str, name: str):
    """importlib 載入 repo 內非 package 腳本（parser 單一源重用，禁自刻）。"""
    path = REPO_ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise IngestInputError(f"module load failed: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _event_key(event: dict[str, str]) -> tuple[str, str, str]:
    return (event["family"], event["message"], event["observed_at_utc"])


# ---- 輸入載入 ----


def load_ledger_rows(path: Path) -> list[dict[str, Any]]:
    """bridge jobs.json 載入（fail-loud：檔缺／JSON malformed／非 row list）。"""
    if not path.is_file():
        raise IngestInputError(f"bridge ledger 缺席：{path}——fail-loud（exit 2）")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestInputError(f"bridge ledger malformed：{path}（{exc}）") from exc
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise IngestInputError(f"bridge ledger 非 row list：{path}")
    return rows


def load_existing_keys(path: Path) -> set[tuple[str, str, str]]:
    """既有 quota-events.jsonl 的 (family, message, observed_at_utc) 鍵集。

    冪等去重依據；malformed 既有行 fail-loud（reader 對同檔同樣 exit 2，
    讀寫契約一致）。
    """
    if not path.is_file():
        return set()
    keys: set[tuple[str, str, str]] = set()
    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            line = json.loads(raw_line)
            key = (line["family"], line["message"], line["observed_at_utc"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise IngestInputError(
                f"既有 quota-events.jsonl line {line_no} malformed：{exc}——fail-loud"
            ) from exc
        if not all(isinstance(part, str) for part in key):
            raise IngestInputError(
                f"既有 quota-events.jsonl line {line_no} 欄位非字串——fail-loud"
            )
        keys.add(key)
    return keys


# ---- 分類與寫入 ----


def classify_event(
    probe_mod: Any, family: str, message: str, observed_at: str, *, context: str
) -> Any:
    """capture_quota_event 單一源分類；ValueError（family/time malformed）
    包 context 後 fail-loud。回 None＝簽名未中（禁偽造，非錯誤）。"""
    try:
        return probe_mod.capture_quota_event(family, message, observed_at)
    except ValueError as exc:
        raise IngestInputError(f"{context}: {exc}") from exc


def sweep_rows(
    rows: list[dict[str, Any]], probe_mod: Any
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """ledger rows → 事件 dict list（all-or-nothing：malformed 即 raise）。

    觸發面＝errorExcerpt 在場（原始 failure message 節錄）；family 缺席
    （legacy row）與 whitelist-外 family（grok）skip＋計數——skip 非偽造；
    契約內 row 的 family/time malformed 纔 fail-loud。
    """
    events: list[dict[str, str]] = []
    stats = {
        "candidates": 0,
        "no_family": 0,
        "out_of_contract": 0,
        "no_signature": 0,
    }
    for idx, row in enumerate(rows, start=1):
        excerpt = row.get("errorExcerpt")
        if not isinstance(excerpt, str) or not excerpt.strip():
            continue  # 非 failure row（實證 errorExcerpt 只在 failure 態）
        stats["candidates"] += 1
        family = row.get("family")
        if not isinstance(family, str):
            stats["no_family"] += 1  # legacy row 無 family 欄——無歸因面
            continue
        context = f"ledger row {idx}（id={row.get('id', '?')} family={family}）"
        if family not in probe_mod.QUOTA_EVENT_FAMILIES:
            stats["out_of_contract"] += 1  # quota-event 契約外 family
            continue
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp.strip():
            raise IngestInputError(
                f"{context}: timestamp 缺席——契約內 failure row malformed，fail-loud"
            )
        event = classify_event(probe_mod, family, excerpt, timestamp, context=context)
        if event is None:
            stats["no_signature"] += 1  # 未知簽名（含 1302 rate-path）禁偽造
            continue
        events.append(
            {
                "family": family,
                "message": excerpt,
                "observed_at_utc": timestamp,
            }
        )
    return events, stats


def append_events(probe_dir: Path, events: list[dict[str, str]]) -> tuple[int, int]:
    """append 新事件（批內＋既有檔雙重去重）→ (appended, total)。

    三鍵 verbatim 禁加工；零新事件不建檔（檔案缺席＝零事件，reader D2）。
    """
    path = probe_dir / "quota-events.jsonl"
    seen = load_existing_keys(path)
    fresh: list[dict[str, str]] = []
    for event in events:
        key = _event_key(event)
        if key in seen:
            continue
        seen.add(key)
        fresh.append({k: event[k] for k in EVENT_KEYS})
    if fresh:
        probe_dir.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for event in fresh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return len(fresh), len(events)


# ---- CLI ----


def _run_single(args: argparse.Namespace) -> int:
    probe_mod = _load_repo_module("scripts/probe_entitlements.py", "probe_entitlements")
    event = classify_event(
        probe_mod,
        args.family,
        args.message,
        args.observed_at,
        context="ingest-event",
    )
    if event is None:
        print("[QuotaEventIngest] 簽名未命中——0 筆（unknown signature 禁偽造）")
        return 0
    probe_dir = Path(args.probe_dir).expanduser()
    appended, _ = append_events(
        probe_dir,
        [
            {
                "family": args.family,
                "message": args.message,
                "observed_at_utc": args.observed_at,
            }
        ],
    )
    duplicate = 0 if appended else 1
    print(
        f"[QuotaEventIngest] ingest-event family={args.family} "
        f"appended={appended} duplicate={duplicate} "
        f"probe_dir={probe_dir}"
    )
    return 0


def _run_sweep(args: argparse.Namespace) -> int:
    probe_mod = _load_repo_module("scripts/probe_entitlements.py", "probe_entitlements")
    probe_dir = Path(args.probe_dir).expanduser()
    ledger_paths = (
        [Path(p).expanduser() for p in args.ledger]
        if args.ledger
        else list(DEFAULT_LEDGERS)
    )
    events: list[dict[str, str]] = []
    totals = {
        "candidates": 0,
        "no_family": 0,
        "out_of_contract": 0,
        "no_signature": 0,
    }
    for ledger_path in ledger_paths:
        rows = load_ledger_rows(ledger_path)
        ledger_events, stats = sweep_rows(rows, probe_mod)
        events.extend(ledger_events)
        for name, value in stats.items():
            totals[name] += value
    appended, _ = append_events(probe_dir, events)
    print(
        f"[QuotaEventIngest] ingest ledgers={len(ledger_paths)} "
        f"candidates={totals['candidates']} hits={len(events)} "
        f"appended={appended} duplicate={len(events) - appended} "
        f"skipped: no_family={totals['no_family']} "
        f"out_of_contract={totals['out_of_contract']} "
        f"no_signature={totals['no_signature']} probe_dir={probe_dir}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="quota_event_ingest",
        description="quota-event ingress closure——bridge failure surface → 事件檔（AIR-244）",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_single = sub.add_parser(
        "ingest-event", help="單事件顯式 ingest（family/message/observed-at 顯式給）"
    )
    p_single.add_argument(
        "--family", required=True, help="family（白名單 codex/glm/muse）"
    )
    p_single.add_argument(
        "--message", required=True, help="原始 failure message（verbatim）"
    )
    p_single.add_argument("--observed-at", required=True, help="觀察時間 ISO 8601")
    p_single.add_argument("--probe-dir", default=str(DEFAULT_PROBE_DIR))
    p_sweep = sub.add_parser(
        "ingest", help="bridge ledger sweep（errorExcerpt intake，預設兩 state root）"
    )
    p_sweep.add_argument(
        "--ledger",
        action="append",
        help="jobs.json 路徑（可多重；缺省＝DEFAULT_LEDGERS）",
    )
    p_sweep.add_argument("--probe-dir", default=str(DEFAULT_PROBE_DIR))
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest-event":
            return _run_single(args)
        return _run_sweep(args)
    except IngestInputError as exc:
        print(f"[FAIL] {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
