#!/usr/bin/env python3
"""child_heartbeat — child 端心跳 sidecar append helper（AIR-160 AC#4；pilot：impl-lite＋cr-research）.

一句話：background worker 以 JSONL append-only sidecar 週期回報 working/done，
讓 harness_waiter 的 stale 偵測比 timebox 更靈敏（AIR-160 heartbeat 協議）。

契約面（凍結定義源＝skills/agent-workflow/SKILL.md「Worker supervision
contract」節；本檔是格式與寫入的機械面）：
- **child 只寫自己的 sidecar**——禁寫 parent registry（liveness-registry.json）、
  **禁自報 collected**（台帳分家；collected 是 parent 專屬動作）；`done` 是
  child 的完成自述，parent 收帳以自己的對帳為準（heartbeat 永不覆蓋 terminal）
- **`emittedAt` 由 helper 機械寫入**——CLI 不提供時間旗標（偽造禁令的機械面：
  無旗標＝呼叫端無法偽造；測試注入走 `append_heartbeat(now=...)` 程式面）
- **`seq` 由 helper 讀既有記錄自動遞增**（max(valid seq)+1）——呼叫端禁給
- **append-only**：半截末行（torn tail——crash 半寫無換行）以補換行終止後由
  讀面丟棄，禁改寫既有位元組；亂序（seq 回退）偵測＝anomaly 大聲回報（append
  照常——telemetry 面禁靜默，也禁因台帳異常擋 worker 主作業）
- 寫入原子性：`O_APPEND` 單一寫入者契約（child 唯一寫者）＋行級單次 write

記錄格式（一行一 JSON object；schema `child-heartbeat/1`；讀面消費者＝
scripts/harness_waiter.py sidecar join——**格式變更兩檔同步**）：

    {"schema": "child-heartbeat/1", "seq": 1, "taskId": "...",
     "attemptId": "...", "state": "working", "emittedAt": "<ISO-8601 UTC>",
     "note": null, "intervalSecs": 60}

心跳週期（cadence）：**預設 60s**（`--interval-secs`；契約定義源＝
skills/agent-workflow/SKILL.md「Worker supervision contract」節——
harness_waiter stale 門檻＝2×週期）。週期寫進 row（`intervalSecs`）——
擇「寫進 row」而非 skill 單方面固定值：row 自載宣告週期＝self-describing
telemetry，watcher 門檻可對帳 child 實際宣告，per-task 週期調整不需改契約。

用法
----
    uv run python scripts/child_heartbeat.py --file .agent-tmp/heartbeats/<taskId>.jsonl \
        --task-id <taskId> --attempt-id <attemptId> --state working|done \
        [--interval-secs 60] [--note "..."]

exit：0＝append 成功（anomaly 不計失敗——上 stderr）；1＝IO fail-loud；
2＝旗標錯（argparse）。
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = "child-heartbeat/1"
# child 禁自報 collected（偽造禁令）——狀態集只有 working|done
STATES = frozenset({"working", "done"})


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _valid_record(rec: object) -> dict | None:
    """記錄欄位驗證——不合形者回 None（讀面丟棄語義，不 raise）."""
    if not isinstance(rec, dict):
        return None
    seq = rec.get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        return None
    interval = rec.get("intervalSecs")
    if not isinstance(interval, int) or isinstance(interval, bool) or interval < 1:
        return None
    for key in ("taskId", "attemptId", "emittedAt"):
        if not isinstance(rec.get(key), str) or not rec[key]:
            return None
    if rec.get("schema") != SCHEMA or rec.get("state") not in STATES:
        return None
    if _parse_iso(rec["emittedAt"]) is None:
        return None
    return rec


def read_sidecar(path: Path) -> tuple[list[dict], list[str]]:
    """tolerant read——回 (有效記錄們, 異常清單).

    半截末行（無換行）與不可解析／欄位不合行＝丟棄（append-only 台帳的讀面
    語義）；seq 回退（亂序）＝anomaly `seq-out-of-order`（偵測不刪證據——
    記錄保留）。檔缺席＝([], [])（缺席合法——advisory 面）。
    """
    anomalies: list[str] = []
    if not path.is_file():
        return [], anomalies
    try:
        raw = path.read_bytes()
    except OSError as exc:
        anomalies.append(f"sidecar-unreadable:{exc}")
        return [], anomalies
    torn = bool(raw) and not raw.endswith(b"\n")
    if torn:
        anomalies.append("torn-tail-discarded")
    lines = raw.decode(errors="replace").split("\n")
    body = lines[:-1]  # 末元素恆為空串或半截——丟棄
    records: list[dict] = []
    for line in body:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            anomalies.append("corrupt-line-discarded")
            continue
        rec = _valid_record(parsed)
        if rec is None:
            anomalies.append("corrupt-line-discarded")
            continue
        if records and rec["seq"] <= records[-1]["seq"]:
            anomalies.append("seq-out-of-order")
        records.append(rec)
    return records, anomalies


def _append_line(path: Path, line: str, *, torn_tail: bool) -> None:
    """O_APPEND 單一寫入者行級原子 append；torn tail 先補換行終止半行.

    只 append 不改寫既有位元組——半截行以補上的換行終止成丟棄行。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = line.encode("utf-8")
    if torn_tail:
        payload = b"\n" + payload
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def append_heartbeat(
    path: Path,
    *,
    task_id: str,
    attempt_id: str,
    state: str,
    note: str | None = None,
    now: datetime | None = None,
    interval_secs: int = 60,
) -> tuple[dict, list[str]]:
    """計算 seq→組記錄→append；回 (落地記錄, 繼承的台帳異常).

    `now` 僅測試注入面（CLI 不暴露——emittedAt 禁呼叫端生成）；`state` 不在
    STATES、`interval_secs` 非正整數＝ValueError（fail-loud，不落地半套）。
    seq＝max(valid seq)+1——亂序台帳自癒為單調。`interval_secs` 寫進 row
    （`intervalSecs`）——watcher stale 門檻（2×週期）的對帳依據。
    """
    if state not in STATES:
        raise ValueError(
            f"state 需 {sorted(STATES)}（child 禁自報 collected）：{state!r}"
        )
    if (
        not isinstance(interval_secs, int)
        or isinstance(interval_secs, bool)
        or interval_secs < 1
    ):
        raise ValueError(f"interval_secs 需正整數（心跳週期秒數）：{interval_secs!r}")
    if not task_id.strip() or not attempt_id.strip():
        raise ValueError("taskId/attemptId 需非空")
    records, anomalies = read_sidecar(path)
    try:
        raw = path.read_bytes()
    except OSError:
        raw = b""
    torn_tail = bool(raw) and not raw.endswith(b"\n")
    record = {
        "schema": SCHEMA,
        "seq": max((r["seq"] for r in records), default=0) + 1,
        "taskId": task_id,
        "attemptId": attempt_id,
        "state": state,
        "emittedAt": (now or datetime.now(tz=UTC)).isoformat(timespec="milliseconds"),
        "note": note,
        "intervalSecs": interval_secs,
    }
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    _append_line(path, line, torn_tail=torn_tail)
    return record, anomalies


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"需正整數：{raw!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"需正整數（≥1）：{raw!r}")
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="child_heartbeat",
        description="child 端心跳 sidecar append helper（AIR-160）——"
        "emittedAt/seq 由 helper 機械寫，CLI 無對應旗標（偽造禁令）",
    )
    parser.add_argument("--file", type=Path, required=True, help="sidecar JSONL 路徑")
    parser.add_argument("--task-id", required=True, help="taskId（spawn prompt 注入）")
    parser.add_argument(
        "--attempt-id", required=True, help="attemptId（spawn prompt 注入）"
    )
    parser.add_argument(
        "--state", required=True, choices=sorted(STATES), help="working｜done"
    )
    parser.add_argument(
        "--interval-secs",
        type=_positive_int,
        default=60,
        help="心跳週期秒數（預設 60——契約預設；寫進 row 的 intervalSecs 供 "
        "watcher stale 門檻 2×週期 對帳）",
    )
    parser.add_argument("--note", default=None, help="選帶註記")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        record, anomalies = append_heartbeat(
            args.file,
            task_id=args.task_id,
            attempt_id=args.attempt_id,
            state=args.state,
            note=args.note,
            interval_secs=args.interval_secs,
        )
    except OSError as exc:
        print(f"[child_heartbeat] fail-loud: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {**record, "anomalies": anomalies},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    for anomaly in anomalies:
        # telemetry 面禁靜默——台帳異常大聲，但 append 成功不計失敗
        print(f"[child_heartbeat] anomaly: {anomaly}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
