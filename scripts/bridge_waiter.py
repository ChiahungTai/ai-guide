#!/usr/bin/env python3
"""bridge_waiter — delegate-bridge fan-in wait watcher（AIR-146）.

一句話：AI 派工後去睡；本 watcher 接手盯場——全 terminal 才叫醒收結果，
疑似卡住只通知不處置，`wait` exit 124 恆內部消化 re-arm，永不外洩。
UX 北極星（digest §1.14）：正常長跑期間主 session 完全不醒；完成才醒，
明確 stall 才醒，124 永遠不醒。

契約源
------
- 卡：backlog/tasks/air-146（AC#1-#6）
- 設計裁決：ai-guide `.agent-tmp/air-135/watcher/adjudication.md`（九問＝contract）
- bridge CLI 事實：delegate-bridge repo
  `plugins/delegate/skills/delegate-run-output/SKILL.md`
  「Dispatch ⇄ collection discipline」＋「Receipt acceptance」節；
  rust 錨點（digest §4 已驗證）：批次 `wait` 等全 terminal 才返
  （0＝全 completed／1＝任一非 completed／124＝timeout／2＝usage）；
  `show <id> --json`＝`{job, finalText}`；running row 的 `extra` 攜
  `heartbeatAt`（worker 軸）／`lastEventAt`（runtime 軸），terminal row strip 兩軸。

狀態機（frozen spec，S 級 oracle——adjudication Q9 裁決；變更須走卡 amendment）
--------------------------------------------------------------------------------

States: RUNNING_FRESH | STALLED_ADVISORY | TERMINAL | UNKNOWN_RECONCILE

| #  | 來源          | 事件（bridge CLI 面）                        | 條件                        | 到達             | watcher 動作                              | exit |
|----|---------------|----------------------------------------------|-----------------------------|------------------|-------------------------------------------|------|
| T1 | （啟動）      | --version probe＋全 id show 得               | 版本 ≥ MIN＋status 可讀     | RUNNING_FRESH    | 快照雙軸＋identity；T=T0=clamp(P50/3,5,15) | —    |
| T2 | RUNNING_FRESH | wait exit 124                                | 任一 job 任一軸 stamp 前進  | RUNNING_FRESH    | T=min(T×1.5, 20m)；re-arm                  | —    |
| T3 | RUNNING_FRESH | wait exit 124                                | 無前進＋silence 未跨 floor  | RUNNING_FRESH    | T=max(1m, min(T, time_to_floor/2))；re-arm | —    |
| T4 | RUNNING_FRESH | wait exit 124／arm 前檢查                    | 任一 running job worker 或 runtime silence 跨 floor | STALLED_ADVISORY | compact progress log；不 stop 不重派 | 3    |
| T5 | RUNNING_FRESH | wait exit 0／exit 2 重探全 terminal         | 全 completed 且 delivery 過 | TERMINAL         | 恰一次 collect；stdout 尾 CollectionReceipt | 0    |
| T6 | RUNNING_FRESH | wait exit 1／exit 2 重探全 terminal／sink 驗收不過 | 任一非 completed/undelivered | TERMINAL   | 恰一次 collect；stdout 尾 CollectionReceipt | 1    |
| T7 | RUNNING_FRESH | wait「not found／disappeared mid-wait」／重探 not-found／running row 的 sessionId/timestamp 變 | ledger 重生／重派跡象 | UNKNOWN_RECONCILE | 喚醒 caller；禁 retry 禁 redispatch | 2    |
| T8 | 任意          | JSON 不可解析／status 缺失／wait 非預期 exit | ledger 缺損                 | （fail-loud）    | 診斷至 stderr＋stdout 尾行標記             | 2    |
| T9 | （啟動）      | 版本 probe                                   | < MIN 或不可判定            | （fail-loud）    | 升級指引（stderr＋stdout 尾行標記）        | 2    |

不變量（代碼面保證）：124 恆內部消化；無 stop／judge／commit 代碼路徑
（AC#6）；stalled/reconcile 只喚醒不處置（偵測與處置分離）；每 job 恰一次
collect（terminal 相的 show＋receipt 驗收 pass 只跑一遍，AC#3）；
bridge ledger 私有面零接觸——只走公開 CLI（§1.2 存取邊界）。

exit 契約（adjudication Q4）
----------------------------
- 0＝全 terminal completed（含 delivery 機驗過；manual-anchor 視同過、receipt 標記）
- 1＝任一 terminal 非 completed（含 completed 但 sink 三步驗收不過的
  terminal-sink-missing 面——AIR-135.7 AC#2 判定句）
- 3＝stalled-advisory（compact progress log；僅通知不處置）
- 124 恆內部消化不外洩
- 2＝fail-loud 面，三種面貌分流（F1/F2 修）：①wait stderr 帶
  「disappeared mid-wait」或「Job not found」（rust 正典字串）→
  unknown/reconcile（禁 retry）；②其餘 exit 2 先對 wait 集逐 id `show` 重探——
  任一 not-found → unknown/reconcile、任一 ledger 缺損 → error、
  全 terminal（single-id wait 對 terminal row 的 usage-error 面，
  wait_exit_for_status(Some(2))，status.rs:305-313）→ 落 T5/T6 collect 相、
  仍有 running → 真 usage
  透傳（無 stdout 標記）；③版本不符 → error。reconcile／error 的 stdout
  尾行為單行 JSON，`state` 欄（unknown/reconcile｜error）機械可判。

stdout：compact progress log＋尾行 CollectionReceipt／狀態標記 JSON；
stderr＝診斷。CollectionReceipt schema＝AIR-135.7 AC#2 bounded receipt
欄位集的 watcher 側機驗投影（adjudication Q3：非新 schema；sink 三步程序
單一源＝delegate-run-output「Receipt acceptance」節，本檔引用不自創）。
語義判定（top findings／blockers／pending-human-decision 等）歸 caller——
watcher 止步線（digest §1.8）。

用法
----
    uv run python scripts/bridge_waiter.py <jobId...>
        [--kind discussion|implementation|research]
        [--sink jobId:PATH]... [--anchor jobId:TOKEN]...
        [--bridge-bin PATH]

動態 T（digest §1.4）：T0=clamp(P50_prior/3, 5m, 15m)，prior 表＝
family×work-kind 內嵌常數（adjudication Q2：單消費者 YAGNI，不進 config）；
fresh progress T×1.5 cap 20m；無前進 T=min(T, 剩至 floor/2) 最低 1m。
卡死判準（§1.5）：worker 軸（heartbeatAt）／runtime 軸（lastEventAt）獨立，
fresh worker 不掩蓋 silent runtime（D1-01）；runtime silence floor
codex/glm 10m、research 25m（codex 裁量 20-30m 帶中值）；worker hard-liveness
5m；stalled 永遠 advisory。無可計齊 stamp（兩軸皆無 ageable data）＝非
staleness 不報 stalled（0921 對齊 task.rs canonical——codex 腿 drift finding；
codex web 長生成期 heartbeat 滯後屬常態，worker 5m floor 對高強度研究工單
偏緊，誤報 advisory 容忍或 --kind research 抬 runtime floor）。
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from io import TextIOBase
from pathlib import Path
from typing import Protocol

MIN_BRIDGE_VERSION = "2.0.22"

RECEIPT_SCHEMA = "collection-receipt/1"
WATCHER_NAME = "bridge_waiter"

RUNNING = "running"
COMPLETED = "completed"

# 動態 T 常數（分鐘；digest §1.4 公式）
T0_CLAMP_MIN_MIN = 5.0
T0_CLAMP_MAX_MIN = 15.0
T_GROW_FACTOR = 1.5
T_GROW_CAP_MIN = 20.0
T_SHRINK_FLOOR_MIN = 1.0

# 卡死判準常數（分鐘；digest §1.5）
WORKER_SILENCE_FLOOR_MIN = 5.0
RUNTIME_SILENCE_FLOOR_MIN = 10.0
RUNTIME_SILENCE_FLOOR_RESEARCH_MIN = 25.0  # codex 裁量 20-30m 帶中值

# duration prior（P50 分鐘；family×work-kind 內嵌常數——adjudication Q2）
DURATION_PRIOR_P50_MIN: dict[tuple[str, str], float] = {
    ("codex", "discussion"): 15.0,
    ("glm", "implementation"): 45.0,
    ("codex", "research"): 90.0,
    ("glm", "research"): 90.0,
    ("muse", "research"): 90.0,
}
FAMILY_DEFAULT_P50_MIN: dict[str, float] = {"codex": 15.0, "glm": 45.0, "muse": 30.0}
GLOBAL_DEFAULT_P50_MIN = 30.0

_SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class BridgeError(RuntimeError):
    """bridge CLI 呼叫失敗（kind＝not-found｜corrupt）。"""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


class LedgerCorruptError(RuntimeError):
    """ledger 缺損面：status 缺失／payload 形態錯——missing/corrupt fail-loud（T8）。"""


class VersionGateError(RuntimeError):
    """bridge CLI 版本不符或不可判定（T9）。"""


class UsageError(RuntimeError):
    """caller 用法錯（重複 id／sink 指到集外 id）。"""


class BridgeCli(Protocol):
    """watcher 對 bridge CLI 的最小依賴面（測試以 fake 實作）。"""

    bin_path: str

    def version(self) -> str | None: ...

    def wait(
        self, job_ids: list[str], timeout_ms: int, stuck_after_ms: int
    ) -> tuple[int, str, str]: ...

    def show(self, job_id: str) -> dict: ...


def _default_runner(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


class BridgeClient:
    """delegate-bridge 公開 CLI 的 subprocess 包裝——唯讀三面：version/wait/show。

    刻意不提供 stop／dispatch／judge 任何寫入或處置面（AC#6 代碼面保證）。
    """

    def __init__(
        self,
        bin_path: str,
        runner: Callable[[list[str]], subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.bin_path = bin_path
        self._runner = runner or _default_runner

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return self._runner([self.bin_path, *args])

    def version(self) -> str | None:
        """probe `--version`；CLI 未支援（現行 2.0.22 面）回 None——走路徑 pin fallback。"""
        proc = self._run(["--version"])
        return proc.stdout.strip() if proc.returncode == 0 else None

    def wait(
        self, job_ids: list[str], timeout_ms: int, stuck_after_ms: int
    ) -> tuple[int, str, str]:
        proc = self._run(
            [
                "wait",
                *job_ids,
                "--timeout",
                str(int(timeout_ms)),
                "--stuck-after",
                str(int(stuck_after_ms)),
            ]
        )
        return proc.returncode, proc.stdout, proc.stderr

    def show(self, job_id: str) -> dict:
        proc = self._run(["show", job_id, "--json"])
        if proc.returncode != 0:
            kind = "not-found" if "not found" in proc.stderr.lower() else "corrupt"
            raise BridgeError(
                kind, f"show {job_id} exit {proc.returncode}: {proc.stderr.strip()}"
            )
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise BridgeError(
                "corrupt", f"show {job_id} stdout 不可解析：{exc}"
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("job"), dict):
            raise BridgeError("corrupt", f"show {job_id} 缺 job 物件")
        return payload


# ---------------------------------------------------------------------------
# 版本 pin（T9；adjudication Q1）
# ---------------------------------------------------------------------------


def parse_semver(text: str) -> tuple[int, int, int] | None:
    match = _SEMVER_RE.search(text)
    if match is None:
        return None
    return int(match[1]), int(match[2]), int(match[3])


def compare_semver(a: str, b: str) -> int:
    va, vb = parse_semver(a), parse_semver(b)
    if va is None or vb is None:
        raise VersionGateError(f"版本號不可解析：{a!r} vs {b!r}")
    return (va > vb) - (va < vb)


def version_from_path(bin_path: str) -> str | None:
    """registry pin 路徑段 fallback：.../delegate/<semver>/bin/...（pin 唯一真相源）。"""
    resolved = shutil.which(bin_path) or os.path.abspath(bin_path)
    for part in Path(resolved).parts:
        if _SEMVER_RE.fullmatch(part):
            return part
    return None


def ensure_bridge_version(client: BridgeCli) -> str:
    """probe --version，不支援時以 registry pin 路徑段判定；不符 fail-loud（T9）。

    偏差註記：bridge CLI 2.0.22 無 --version 面（實測 exit 2 Unknown
    subcommand）——adjudication Q1 的 probe 依 --version 先行、路徑 pin 兜底，
    版本意圖（pin＋fail-loud＋升級指引）不變。
    """
    raw = client.version()
    candidates: list[str] = [raw] if raw else []
    pinned = version_from_path(client.bin_path)
    if pinned is not None:
        candidates.append(pinned)
    if not candidates:
        raise VersionGateError(
            "bridge CLI 版本無法判定（--version 不支援且路徑無 registry pin 版本段）"
            f"——最低需求 {MIN_BRIDGE_VERSION}；升級：zcode 端更新 delegate plugin"
            f"（delegate-bridge ≥ {MIN_BRIDGE_VERSION}）後重跑"
        )
    version = candidates[0]
    if compare_semver(version, MIN_BRIDGE_VERSION) < 0:
        raise VersionGateError(
            f"bridge CLI {version} 低於最低需求 {MIN_BRIDGE_VERSION}"
            f"（wait 批次語義＋heartbeatAt/lastEventAt 雙軸的驗證基準）——"
            f"升級：zcode plugins update delegate 後重跑"
        )
    return version


# ---------------------------------------------------------------------------
# 時間戳／雙軸卡死判準（digest §1.5）
# ---------------------------------------------------------------------------


def parse_iso_ts(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # naive 時間戳不做本地時區假設——不可計齊＝axis 無資料（canonical：非 staleness）
        return None
    return parsed.astimezone()


def crossed_floor(silence: float | None, floor_min: float) -> bool:
    """對齊 bridge producer canonical（task.rs：no ageable data is never reported——
    單一實作聲明，0921 codex 腿 drift finding）：None（兩軸皆無可計齊 stamp）＝非
    staleness，不報 stalled；terminal/124/not-found 路徑照常 wake，不賴此軸。
    IEEE 754 比較 fail-open 防護：正 gate 用 not (x <= floor) 形，NaN → 擋。
    """
    if silence is None:
        return False
    return not (silence <= floor_min)


def _axis_silence_minutes(
    now: datetime, row_ts: str | None, axis_stamp: str | None
) -> float | None:
    """age = now − newest(axis stamp, row timestamp)——bridge 雙軸同式（task.rs:156-168）。"""
    stamps = [
        ts for ts in (parse_iso_ts(row_ts), parse_iso_ts(axis_stamp)) if ts is not None
    ]
    if not stamps:
        return None
    return (now - max(stamps)).total_seconds() / 60.0


def worker_silence_minutes(snapshot: "JobSnapshot", now: datetime) -> float | None:
    return _axis_silence_minutes(now, snapshot.timestamp, snapshot.heartbeat_at)


def runtime_silence_minutes(snapshot: "JobSnapshot", now: datetime) -> float | None:
    return _axis_silence_minutes(now, snapshot.timestamp, snapshot.last_event_at)


def runtime_floor_minutes(kind: str) -> float:
    return (
        RUNTIME_SILENCE_FLOOR_RESEARCH_MIN
        if kind == "research"
        else RUNTIME_SILENCE_FLOOR_MIN
    )


def _time_to_floor_minutes(
    snapshot: "JobSnapshot", kind: str, now: datetime
) -> float | None:
    silence = runtime_silence_minutes(snapshot, now)
    if silence is None:
        return None
    return runtime_floor_minutes(kind) - silence


# ---------------------------------------------------------------------------
# 動態 T（digest §1.4）
# ---------------------------------------------------------------------------


def compute_t0(family: str, kind: str) -> float:
    p50 = DURATION_PRIOR_P50_MIN.get(
        (family, kind),
        FAMILY_DEFAULT_P50_MIN.get(family, GLOBAL_DEFAULT_P50_MIN),
    )
    return min(max(p50 / 3.0, T0_CLAMP_MIN_MIN), T0_CLAMP_MAX_MIN)


def next_arm_timeout(
    t_min: float, progressed: bool, time_to_floor_min: float | None
) -> float:
    if progressed:
        return min(t_min * T_GROW_FACTOR, T_GROW_CAP_MIN)
    if time_to_floor_min is None:
        return T_SHRINK_FLOOR_MIN
    return max(T_SHRINK_FLOOR_MIN, min(t_min, time_to_floor_min / 2.0))


# ---------------------------------------------------------------------------
# 快照／receipt
# ---------------------------------------------------------------------------


@dataclass
class JobSnapshot:
    """running row 的公開面快照（liveness＋identity 雙用途）。"""

    job_id: str
    status: str
    family: str
    session_id: str | None
    timestamp: str | None
    heartbeat_at: str | None
    last_event_at: str | None


def snapshot_job(client: BridgeCli, job_id: str) -> JobSnapshot:
    payload = client.show(job_id)
    job = payload["job"]
    status = job.get("status")
    if not isinstance(status, str) or not status:
        raise LedgerCorruptError(
            f"job {job_id} status 缺失或非字串——missing/corrupt status fail-loud"
        )
    extra = job.get("extra")
    extra_map: dict = extra if isinstance(extra, dict) else {}
    family = job.get("family")
    session_id = job.get("sessionId")
    timestamp = job.get("timestamp")
    heartbeat = extra_map.get("heartbeatAt")
    last_event = extra_map.get("lastEventAt")
    return JobSnapshot(
        job_id=job_id,
        status=status,
        family=family if isinstance(family, str) else "unknown",
        session_id=session_id if isinstance(session_id, str) else None,
        timestamp=timestamp if isinstance(timestamp, str) else None,
        heartbeat_at=heartbeat if isinstance(heartbeat, str) else None,
        last_event_at=last_event if isinstance(last_event, str) else None,
    )


def check_delivery(
    sink: str | None, anchor_tokens: list[str], final_text: str | None
) -> dict:
    """sink 三步機驗：存在→非空→錨點（L1/L2 gate；L3 語義＝人工，永不自動判定）。

    程序單一源＝delegate-run-output「Receipt acceptance」節（引用不自創）；
    receipt-only（未具名 sink）以 response 非空代驗（同 sweep v1 慣例）。
    """
    if not sink:
        ok = bool((final_text or "").strip())
        return {
            "mode": "receipt-only",
            "sink": None,
            "l1_present": ok,
            "l1_detail": "response 非空 OK" if ok else "FAIL——response 空",
            "l2_anchor": None,
            "anchor_hits": [],
            "verdict": "delivered" if ok else "undelivered",
        }
    path = Path(sink)
    if not path.exists():
        return _delivery(sink, False, "缺", None, [], "undelivered")
    try:
        size = path.stat().st_size
    except OSError as exc:
        return _delivery(sink, False, f"stat-fail（{exc}）", None, [], "undelivered")
    if not (size > 0):  # fail-closed：0/負值皆視為空（NaN 比較恆 False → 進此擋）
        return _delivery(sink, False, "空", None, [], "undelivered")
    if not anchor_tokens:
        return _delivery(sink, True, "存在＋非空", None, [], "manual-anchor")
    try:
        # read_text() 本就載入全檔——全 content 搜尋，無窗口 gap／縫隙（N1 修）
        content = path.read_text(errors="replace")
    except OSError as exc:
        return _delivery(sink, True, f"read-fail（{exc}）", False, [], "undelivered")
    hits = [token for token in anchor_tokens if token in content]
    if hits:
        return _delivery(sink, True, "存在＋非空", True, hits, "delivered")
    return _delivery(sink, True, "存在＋非空", False, [], "undelivered")


def _delivery(
    sink: str,
    l1: bool,
    l1_detail: str,
    l2: bool | None,
    hits: list[str],
    verdict: str,
) -> dict:
    return {
        "mode": "artifact",
        "sink": sink,
        "l1_present": l1,
        "l1_detail": l1_detail,
        "l2_anchor": l2,
        "anchor_hits": hits,
        "verdict": verdict,
    }


def _collect_row(
    job_id: str,
    payload: dict,
    sinks: dict[str, str],
    anchors: dict[str, list[str]],
) -> dict:
    job = payload.get("job")
    if not isinstance(job, dict):
        raise LedgerCorruptError(f"job {job_id} show payload 缺 job 物件")
    status = job.get("status")
    if not isinstance(status, str) or not status:
        raise LedgerCorruptError(
            f"job {job_id} status 缺失——missing/corrupt status fail-loud"
        )
    final_text = payload.get("finalText")
    final_text = final_text if isinstance(final_text, str) else None
    family = job.get("family")
    sink = sinks.get(job_id)
    if status == COMPLETED:
        delivery = check_delivery(sink, anchors.get(job_id, []), final_text)
    else:
        delivery = {
            "mode": "artifact" if sink else "receipt-only",
            "sink": sink,
            "l1_present": None,
            "l1_detail": "status 非 completed——止步於 status gate（terminal≠complete）",
            "l2_anchor": None,
            "anchor_hits": [],
            "verdict": "not-assessed",
        }
    bounded = {
        "finalTextNonEmpty": bool((final_text or "").strip()),
        "note": (
            "AIR-135.7 AC#2 bounded receipt 欄位集投影；語義欄（top findings／"
            "blockers／unverified／pending-human-decision）判定歸 caller"
        ),
    }
    return {
        "jobId": job_id,
        "status": status,
        "family": family if isinstance(family, str) else "unknown",
        "delivery": delivery,
        "boundedReceiptProjection": bounded,
    }


def build_collection_receipt(
    rows: list[dict],
    *,
    exit_state: str,
    kind: str,
    bridge_version: str,
    arms: int,
) -> dict:
    completed = sum(1 for row in rows if row["status"] == COMPLETED)
    undelivered = sum(1 for row in rows if row["delivery"]["verdict"] == "undelivered")
    manual = sum(1 for row in rows if row["delivery"]["verdict"] == "manual-anchor")
    return {
        "schema": RECEIPT_SCHEMA,
        "watcher": WATCHER_NAME,
        "bridgeCliVersion": bridge_version,
        "kind": kind,
        "arms": arms,
        "exitState": exit_state,
        "summary": {
            "total": len(rows),
            "completed": completed,
            "nonCompleted": len(rows) - completed,
            "undelivered": undelivered,
            "manualAnchor": manual,
        },
        "jobs": rows,
    }


# ---------------------------------------------------------------------------
# 輸出 helpers
# ---------------------------------------------------------------------------


def _emit(file: TextIOBase, text: str) -> None:
    file.write(text + "\n")
    file.flush()


def _dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _emit_state(out: TextIOBase, err: TextIOBase, state: str, extra: dict) -> int:
    _emit(out, _dumps({"state": state, **extra}))
    _emit(err, f"[watcher] {state}: {extra.get('reason', '')}")
    return 2


def _emit_advisory(
    out: TextIOBase,
    err: TextIOBase,
    snapshots: dict[str, JobSnapshot],
    running_ids: list[str],
    kind: str,
    now: datetime,
) -> int:
    detail: dict[str, dict] = {}
    for job_id in running_ids:
        snap = snapshots[job_id]
        worker = worker_silence_minutes(snap, now)
        runtime = runtime_silence_minutes(snap, now)
        detail[job_id] = {
            "workerSilenceMin": None if worker is None else round(worker, 1),
            "runtimeSilenceMin": None if runtime is None else round(runtime, 1),
        }
        worker_txt = "n/a" if worker is None else f"{round(worker, 1)}m"
        runtime_txt = "n/a" if runtime is None else f"{round(runtime, 1)}m"
        _emit(
            out,
            f"[watcher] stalled: {job_id} worker={worker_txt} "
            f"runtime={runtime_txt} "
            f"(floor worker={WORKER_SILENCE_FLOOR_MIN}m "
            f"runtime={runtime_floor_minutes(kind)}m)",
        )
    _emit(out, _dumps({"state": "stalled-advisory", "jobs": detail}))
    _emit(
        err,
        "[watcher] stalled-advisory——僅通知不處置（不 stop 不重派；處置權在 caller）",
    )
    return 3


def _reconcile_or_error(
    out: TextIOBase, err: TextIOBase, job_id: str, exc: BridgeError
) -> int:
    if exc.kind == "not-found":
        return _emit_state(
            out, err, "unknown/reconcile", {"jobId": job_id, "reason": str(exc)}
        )
    return _emit_state(out, err, "error", {"jobId": job_id, "reason": str(exc)})


def _reprobe_wait_set(client: BridgeCli, wait_ids: list[str]) -> tuple[str, str | None]:
    """wait exit 2 後的 show 重探（F1/F2 修）——回（face, job_id）。

    - 任一 not-found → ("reconcile", id)——T7：ledger 重生／重派，禁 retry
    - 任一 ledger 缺損 → ("error", id)——T8 fail-loud
    - 全部存在且全 terminal → ("terminal", None)——single-id wait 對 terminal
      row（如 usage-error，wait_exit_for_status(Some(2))、stderr 空）回 2 的
      可達面，落 T5/T6 collect 相
    - 其餘（仍有 running）→ ("running", None)——真 usage 面（透傳）
    """
    saw_running = False
    for job_id in wait_ids:
        try:
            snap = snapshot_job(client, job_id)
        except BridgeError as exc:
            if exc.kind == "not-found":
                return "reconcile", job_id
            return "error", job_id
        except LedgerCorruptError:
            return "error", job_id
        if snap.status == RUNNING:
            saw_running = True
    return ("running" if saw_running else "terminal"), None


def _job_stalled(snapshot: JobSnapshot, kind: str, now: datetime) -> bool:
    """雙軸獨立判準（D1-01：fresh worker 不掩蓋 silent runtime）。"""
    if crossed_floor(worker_silence_minutes(snapshot, now), WORKER_SILENCE_FLOOR_MIN):
        return True
    return crossed_floor(
        runtime_silence_minutes(snapshot, now), runtime_floor_minutes(kind)
    )


def _validate_usage(
    job_ids: list[str], sinks: dict[str, str], anchors: dict[str, list[str]]
) -> None:
    if not job_ids:
        raise UsageError("至少一個 jobId")
    if len(set(job_ids)) != len(job_ids):
        raise UsageError("jobId 重複")
    unknown = (set(sinks) | set(anchors)) - set(job_ids)
    if unknown:
        raise UsageError(
            f"--sink/--anchor 指了不在 fan-in 集的 jobId：{sorted(unknown)}"
        )


def _system_now() -> datetime:
    return datetime.now().astimezone()


# ---------------------------------------------------------------------------
# 主迴圈（狀態機實作——轉移編號對應 module docstring frozen spec）
# ---------------------------------------------------------------------------


def run_watcher(
    client: BridgeCli,
    job_ids: list[str],
    *,
    kind: str = "unspecified",
    sinks: dict[str, str] | None = None,
    anchors: dict[str, list[str]] | None = None,
    now: Callable[[], datetime] | None = None,
    stdout: TextIOBase | None = None,
    stderr: TextIOBase | None = None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    now_fn = now or _system_now
    sinks_map = dict(sinks or {})
    anchors_map = {key: list(value) for key, value in (anchors or {}).items()}
    _validate_usage(job_ids, sinks_map, anchors_map)

    # T9 版本 pin
    try:
        bridge_version = ensure_bridge_version(client)
    except VersionGateError as exc:
        return _emit_state(out, err, "error", {"reason": str(exc)})
    except BridgeError as exc:
        return _emit_state(
            out, err, "error", {"reason": f"bridge CLI probe 失敗：{exc}"}
        )

    # T1 初始快照
    snapshots: dict[str, JobSnapshot] = {}
    for job_id in job_ids:
        try:
            snapshots[job_id] = snapshot_job(client, job_id)
        except BridgeError as exc:
            return _reconcile_or_error(out, err, job_id, exc)
        except LedgerCorruptError as exc:
            return _emit_state(out, err, "error", {"jobId": job_id, "reason": str(exc)})

    running_ids = [j for j in job_ids if snapshots[j].status == RUNNING]
    if running_ids:
        # T4 arm 前檢查
        if any(_job_stalled(snapshots[j], kind, now_fn()) for j in running_ids):
            return _emit_advisory(out, err, snapshots, running_ids, kind, now_fn())
        t_min = max(compute_t0(snapshots[j].family, kind) for j in running_ids)
    else:
        t_min = 0.0

    arms = 0
    while running_ids:
        # T2/T3/T4 的 arm 面；批次 wait 等全 terminal 才返（rust cmd_wait_batch）
        arms += 1
        stuck_ms = int(runtime_floor_minutes(kind) * 60_000)
        _emit(
            out,
            f"[watcher] arm round={arms} T={t_min:.1f}m "
            f"running={len(running_ids)}/{len(job_ids)} kind={kind}",
        )
        try:
            code, wait_out, wait_err = client.wait(
                running_ids,
                timeout_ms=int(t_min * 60_000),
                stuck_after_ms=stuck_ms,
            )
        except BridgeError as exc:
            return _emit_state(out, err, "error", {"reason": f"wait 執行失敗：{exc}"})
        if wait_out:
            _emit(out, wait_out.rstrip())
        if wait_err:
            _emit(err, wait_err.rstrip())

        if code in (0, 1):
            break  # T5/T6：批次已全 terminal

        if code == 2:
            # exit 2 三面貌（F1/F2）：①「disappeared mid-wait」／「Job not found」
            # （rust 正典字串，main.rs:268/357/382；比對 case-insensitive——
            # 與 show 分類器 .lower() 對稱，N3）＝T7 reconcile 禁 retry；
            # ② single-id wait 對 terminal row（如 usage-error——
            # wait_exit_for_status(Some(2))、stderr 空）＝已 terminal，
            # show 重探後落 collect 相（T5/T6）；
            # ③ 其餘（真 usage，如壞旗標）才透傳。
            wait_err_lower = wait_err.lower()
            if (
                "disappeared mid-wait" in wait_err_lower
                or "job not found" in wait_err_lower
            ):
                # T7：row 消失／不存在＝ledger 重生／bridge 重啟——禁 retry
                return _emit_state(
                    out,
                    err,
                    "unknown/reconcile",
                    {
                        "reason": (
                            "wait 回報 job 消失或不存在——"
                            "ledger 重生／重派跡象，禁 retry"
                        ),
                        "stderr": wait_err.strip()[:200],
                    },
                )
            face, face_job = _reprobe_wait_set(client, running_ids)
            if face == "reconcile":
                return _emit_state(
                    out,
                    err,
                    "unknown/reconcile",
                    {
                        "jobId": face_job,
                        "reason": "show 重探 not-found——ledger 重生／重派跡象，禁 retry",
                    },
                )
            if face == "error":
                return _emit_state(
                    out,
                    err,
                    "error",
                    {
                        "jobId": face_job,
                        "reason": "show 重探遇 ledger 缺損——missing/corrupt fail-loud",
                    },
                )
            if face == "terminal":
                break  # 已全 terminal——落 T5/T6 collect 相
            return 2  # 真 usage 透傳（bridge 已印 usage 至本 stderr）

        if code != 124:
            # T8：非預期 exit——fail-loud
            return _emit_state(
                out, err, "error", {"reason": f"wait 非預期 exit {code}"}
            )

        # exit 124：內部消化——re-arm 前刷新快照（絕不外洩，AC#1）
        now_round = now_fn()
        progressed = False
        still_running: list[str] = []
        for job_id in running_ids:
            try:
                current = snapshot_job(client, job_id)
            except BridgeError as exc:
                return _reconcile_or_error(out, err, job_id, exc)
            except LedgerCorruptError as exc:
                return _emit_state(
                    out, err, "error", {"jobId": job_id, "reason": str(exc)}
                )
            previous = snapshots[job_id]
            if current.status != RUNNING:
                snapshots[job_id] = current  # 已 terminal——收進 collect 集
                continue
            # T7：generation identity 檢查——running row 身分變＝重生，禁 retry
            if (
                current.session_id != previous.session_id
                or current.timestamp != previous.timestamp
            ):
                return _emit_state(
                    out,
                    err,
                    "unknown/reconcile",
                    {
                        "jobId": job_id,
                        "reason": "running row 的 sessionId/timestamp 變更——"
                        "ledger 重生／重派跡象，禁 retry",
                    },
                )
            snapshots[job_id] = current
            if _job_stalled(current, kind, now_round):
                # T4：跨 floor——stalled 永遠 advisory（不 stop 不重派）
                still_ids = [*still_running, job_id]
                return _emit_advisory(out, err, snapshots, still_ids, kind, now_round)
            if (
                current.heartbeat_at != previous.heartbeat_at
                or current.last_event_at != previous.last_event_at
            ):
                progressed = True  # T2 條件：任一軸 stamp 前進
            still_running.append(job_id)

        running_ids = still_running
        if not running_ids:
            break  # 全數在本輪 124 窗內 terminal——進 collect

        # T2/T3：動態 T
        floors = [
            _time_to_floor_minutes(snapshots[j], kind, now_round) for j in running_ids
        ]
        time_to_floor = (
            min(f for f in floors if f is not None)
            if any(f is not None for f in floors)
            else None
        )
        t_min = next_arm_timeout(t_min, progressed, time_to_floor)
        _emit(
            out,
            f"[watcher] round={arms}: progressed={progressed} "
            f"next_arm={t_min:.1f}m running={len(running_ids)}/{len(job_ids)}",
        )

    # T5/T6：恰一次 collect（每 job 剛好一遍 show＋receipt 驗收 pass）
    rows: list[dict] = []
    for job_id in job_ids:
        try:
            payload = client.show(job_id)
        except BridgeError as exc:
            return _reconcile_or_error(out, err, job_id, exc)
        except LedgerCorruptError as exc:
            return _emit_state(out, err, "error", {"jobId": job_id, "reason": str(exc)})
        try:
            rows.append(_collect_row(job_id, payload, sinks_map, anchors_map))
        except LedgerCorruptError as exc:
            return _emit_state(out, err, "error", {"jobId": job_id, "reason": str(exc)})

    all_delivered = all(
        row["status"] == COMPLETED
        and row["delivery"]["verdict"] in ("delivered", "manual-anchor")
        for row in rows
    )
    exit_state = "completed" if all_delivered else "terminal-non-completed"
    receipt = build_collection_receipt(
        rows,
        exit_state=exit_state,
        kind=kind,
        bridge_version=bridge_version,
        arms=arms,
    )
    _emit(out, _dumps(receipt))
    return 0 if exit_state == "completed" else 1


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bridge_waiter",
        description=(
            "delegate-bridge fan-in wait watcher——124 內部 re-arm、"
            "terminal 輸出 CollectionReceipt（AIR-146）"
        ),
        epilog="契約：backlog/tasks/air-146；狀態機 frozen spec 見 module docstring。",
    )
    parser.add_argument(
        "job_ids",
        nargs="+",
        metavar="jobId",
        help="要 fan-in 等待的 bridge job id（≥1）",
    )
    parser.add_argument(
        "--kind",
        default="unspecified",
        help="work-kind（discussion|implementation|research）——P50 prior 與 "
        "runtime silence floor 查表鍵",
    )
    parser.add_argument(
        "--sink",
        action="append",
        default=[],
        metavar="jobId:PATH",
        help="具名 artifact sink（可重複）；未具名者按 receipt-only 驗收",
    )
    parser.add_argument(
        "--anchor",
        action="append",
        default=[],
        metavar="jobId:TOKEN",
        help="work-order 具名錨點（可重複；L2 gate 的判準 token）",
    )
    parser.add_argument(
        "--bridge-bin",
        default=os.environ.get("DELEGATE_BRIDGE_BIN", "delegate-bridge"),
        help="delegate-bridge CLI 路徑（預設 PATH 上的 delegate-bridge，"
        "或 $DELEGATE_BRIDGE_BIN）",
    )
    args = parser.parse_args(argv)

    sinks: dict[str, str] = {}
    for spec in args.sink:
        job_id, sep, path = spec.partition(":")
        if not sep or not job_id or not path:
            parser.error(f"--sink 需 jobId:PATH 形，得：{spec!r}")
        sinks[job_id] = path
    anchors: dict[str, list[str]] = {}
    for spec in args.anchor:
        job_id, sep, token = spec.partition(":")
        if not sep or not job_id or not token:
            parser.error(f"--anchor 需 jobId:TOKEN 形，得：{spec!r}")
        anchors.setdefault(job_id, []).append(token)

    client = BridgeClient(args.bridge_bin)
    try:
        return run_watcher(
            client,
            list(args.job_ids),
            kind=args.kind,
            sinks=sinks,
            anchors=anchors,
        )
    except UsageError as exc:
        print(f"bridge_waiter: usage 錯誤：{exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        # bin 路徑失效（bare shell 未帶 DELEGATE_BRIDGE_BIN／pin 漂移）＝clean fail-loud，
        # 禁 silent exit 0 也禁 traceback——caller 須收到可操作的修法指引（0921 dogfood 實證）
        print(
            f"bridge_waiter: bridge binary 不可達（fail-loud）：{exc}\n"
            "  修法：--bridge-bin <絕對路徑> 或 export DELEGATE_BRIDGE_BIN——路徑由\n"
            "  installed_plugins.json registry pin 解析（禁手拼版本化 cache 路徑）。",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
