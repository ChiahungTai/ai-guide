#!/usr/bin/env python3
"""harness_waiter — ZCode 子 agent 凍結偵測＋收割＋停止協議（AIR-149 S1＋S2）.

一句話：ZCode Task-tool subagent 沒有獨立 process 可監看——本 watcher 以檔案
系統四觀察面偵測「全面靜默」，凍結即先收割後喚醒主 session 處置（砍歸主
session）；「無訊號 ≠ 死亡」，判死不走 liveness inference（user 裁決 0920：
20 分鐘全面零輸出＝bug 處理）。

契約源
------
- EP：ai-analysis/_tasks/2026-09/09-20-harness-liveness-watcher/ep.md（S1 節）
- 設計裁決：同任務 references/research.md（AIR-148 probe＋codex 兩輪攻防）
- 兄弟形態參考：bridge_waiter.py（**AIR-146 已落本 branch**——bridge 側兄弟，結構
  參考、代碼不共用）

觀察面（frozen 定義；路徑常數集中 ZCodeLayout，禁散落）
--------------------------------------------------------
- rollout＝`<cli>/rollout/model-io-<taskId>.jsonl`（最佳 liveness 檔——每次
  model I/O 即時 append）
- exec＝`<cli>/exec/<taskId>/`（工具執行中 zsh 持 fd 直寫；完成後目錄清空）
- artifact＝`<cli>/artifacts/<taskId>/`
- metadata＝`<cli>/agents/sess_<parent>/agent_<id>/metadata.json`
  （registry 存 taskId＝childSessionId `sess_subagent_agent_<id>`；adapter
  以 glob 解析 parent；agentId 由 taskId 機械映射）
- terminal 面＝metadata `status`（running/completed/failed/stopped；spawn 與
  terminal 兩點寫入，run 期間 mtime 零推進——反指標，禁當 liveness）

`taskId` 慣例（機器實證 2026-09-20）：childSessionId 全形
`sess_subagent_agent_<uuid>`；rollout 檔名與 exec/artifact 目錄名皆直接使用
該全形 id（EP 條文 `sess_<taskId>` 前綴記法以機器佈局為準——偏差記錄見卡）。

fail-loud（frozen 擴充）：錨點缺失、JSON 不可解析／半寫 torn read、glob 歧
義、lsof 不可判定——一律 `unknown(原因)`，禁 crash 禁猜禁誤報。時鐘回撥
（elapsed<0）＝視為 Fresh＋telemetry `clock-rollback`。

凍結判準（frozen；research.md §三）
------------------------------------
rollout＋artifact 無推進＋無 exec fd lease（lsof）＋無 terminal，連續 20m
（預設；registry entry `silenceBudget`〔分鐘〕可覆寫）。poll gap 異常（機器
睡眠）→該段扣除（單一語義：異常 gap 只記一個 poll interval，F9 裁決擇扣除
不重置）。靜默量取 `min(輪詢累積, 表面 mtime 齡期)`——前者承擔睡眠扣除、後
者承擔 watcher 啟動前已存在的靜默（殭屍 corpus 面）。

狀態機（frozen spec 轉移表——EP S1 節逐字；S 級 oracle，TC-1 對照本表；
實作者不得改表，改表走 EP amendment）
------------------------------------------------------------------

| # | 來源態 | 事件 | 條件 | 到達態 | watcher 動作 |
|---|---|---|---|---|---|
| T1 | （註冊） | S2 registry entry 建立 | — | MONITORED | 開始輪詢 |
| T2 | MONITORED | 輪詢 | 三面任一推進 | MONITORED | 計數續走（poll gap 異常→扣除間隔） |
| T3 | MONITORED | 輪詢 | 全面靜默 ≥20m | HARVESTED | bounded 收割（partial 標記）→寫 pending intervention receipt（dedup：已有 pending 不重發）→exit 3 喚醒 |
| T4 | MONITORED/HARVESTED | quarantine 期活動恢復 | 任一面推進 | （記 `resumed_during_quarantine=true` telemetry） | **仍照砍**——主 session TaskStop 不因恢復取消（user 裁決） |
| T5 | MONITORED | generation mismatch／registry entry 消失 | metadata 異動對照 | （hard-death fast path） | **立即 wake**（exit 2），不等 20m——禁 retry |
| T6 | 任意 | 佈局錨點缺失／registry 缺 entry | adapter 查證失敗 | UNKNOWN | fail-loud 診斷，零誤報 |
| T7 | （主 session） | TaskStop 下達 | — | STOP_REQUESTED | 主 session 執行（非 watcher） |
| T8 | STOP_REQUESTED | verification | grace 內 metadata terminal＋cursors 靜止 | STOP_CONFIRMED | harvest B/delta（主 session 以 `--harvest-delta` 呼叫本 script）→主 session 決定 RETRY_SAFE |
| T9 | STOP_REQUESTED | verification | 仍有寫入者 | STOP_INCOMPLETE | 禁重派＋detached child 處置清單 |

不變量：watcher 永不 stop／重派（TaskStop 歸主 session）；「無訊號≠死亡」；
EXECUTION_DEAD 語義由 STOP 鏈承載、RETRY_SAFE 獨立判定；wake 對「第一個凍
結」收割即 exit——其餘 entry 中止監視，主 session 處置後重啟 watcher 續監
（v1 從簡）。

偏差 ledger（fresh review round 1——結案時補卡面 ledger；本表為 in-file 對照）
------------------------------------------------------------------------------
1. 觀察面路徑記法：EP `sess_<taskId>` 前綴 vs 機器實證目錄名＝taskId 全形
   ——以機器佈局為準（見上「taskId 慣例」）。
2. registry 存 taskId（S2 schema）非 EP S1 文句的 agentId——adapter 以
   `sess_subagent_<rest>→<rest>` 機械映射推 agentId 再 glob。
3. terminal 判定先於 rollout 錨點要求——terminal 後 rollout 清理＝機器合法
   行為（completed agent 實證）；running＋rollout 缺仍 unknown fail-loud。
4. verify 模式 exit 延伸面（0=CONFIRMED／4=INCOMPLETE）——frozen exit 表為
   主迴圈 wake 語義，INCOMPLETE 以 stdout 尾行 `state` 機判（EP review F2）。
5. 靜默量雙源取小 min(輪詢累積〔含 gap 扣除〕, mtime 齡期)——後者承擔
   watcher 啟動前已存在的靜默（EP 未明定；corpus 面需要）。
6. registry 監視集異動分流（F-4）：減項／attempt 變更＝exit 2；純增項＝
   吸納續 watch（增項非死亡訊號，防正常追加註冊假喚醒）。
7. lsof exit 1 歧義（F-2）：stderr 非空＝錯誤→None；空＝無命中→[]。
8. lease 路徑 realpath 正規化（F-3）：/tmp vs /private/tmp symlink 實證。
9. TaskStatus.exec_lease_checked（F-11）：terminal＋prober 不可判定＝
   checked=False 短路（freeze 迴圈不誤醒）；verify 對未查成 fail-closed
   STOP_INCOMPLETE（F-1 禁假確認——terminal 仍列舉 exec/artifact＋probe）。
10. timestamp 不可解析＝fail-loud（F-6）：registry createdAt→registry-schema；
    metadata createdAt 對稱→metadata-corrupt（禁靜默跳過 T5 對照）。

exit 契約（frozen——watcher 主迴圈）
-------------------------------------
- 0＝正常收場（含空 registry、全 terminal）
- 2＝hard-death wake（generation mismatch／metadata 消失／registry entry 異動）
- 3＝freeze wake（stdout 尾附 harvest receipt JSON＋pending intervention）
- 其他非零＝內部錯／fail-loud（診斷至 stderr＋stdout 尾行狀態 JSON；本檔
  用 1）
- verification 模式延伸面（`--verify`，EP review F2 增補——frozen 表為主迴
  圈 wake 語義，verify 以 stdout 尾行 `state` 欄為機械判準）：0＝
  STOP_CONFIRMED、4＝STOP_INCOMPLETE（禁重派）、1＝fail-loud
- 註冊模式延伸面（`--register`，S2）：0＝registered、1＝fail-loud（欄位
  無效／schema 不符／重註冊；stdout 尾行 `state`＝registered／unknown）

stdout：compact progress log＋尾行狀態／receipt JSON（單行，機械可判）；
stderr＝診斷。

用法
----
    uv run python scripts/harness_waiter.py <registry>
        [--poll-interval SEC] [--freeze-threshold MIN] [--max-cycles N]
    uv run python scripts/harness_waiter.py <registry> --verify <taskId>
        [--grace SEC]
    uv run python scripts/harness_waiter.py <registry> --harvest-delta \
        <taskId> <manifestPath>
    uv run python scripts/harness_waiter.py <registry> --register <taskId>
        --attempt-id <id> --sink <path> [--expected <json>]
        [--surviving-handle HANDLE]... [--silence-budget-min MIN]

registry＝workspace-local `.agent-tmp/liveness-registry.json`（寫入面＝
`--register`；atomic write 契約——watcher 逐輪重讀偵測 entry 異動）。schema：
`{"entries": [{taskId, attemptId, createdAt, sink, expected,
survivingHandles[], silenceBudget?}]}`；watcher 讀面：檔缺席＝fail-loud；
entries 空＝exit 0（等待語義：無可監視物）。register 寫面：同 taskId 重註冊
＝fail-loud（新 attempt 前先移除舊 entry）；既有檔損壞／schema 不符＝
fail-loud 禁覆蓋；`createdAt`＝generation anchor，由 register 自 agent
metadata 機械讀取（**非牆鐘**——T5 以此對照 metadata，寫牆鐘＝每次輪詢
hard-death）；`sink`/`expected`＝AIR-135.7 AC#2 bounded receipt 欄位
投影；`survivingHandles`＝dispatch 前已知 detached job 的 ownership handle
（in-harness brief 禁未登記 long-lived/daemonized child）；`silenceBudget`
＝有期限 silence lease（缺席＝20m 標準門檻）。

收割（bounded）：metadata copy→表面 manifest（檔數上限）→rollout raw tail
（位元組上限；JSONL 收 raw bytes——append 中末行半截合法，kill 後再解析）；
超限 `harvestPartial=true` 照樣標。pending intervention receipt＝
`<workspace>/.agent-tmp/liveness/pending/<taskId>.json`，dedup key＝
taskId＋attemptId，已存在同 attempt 不重發。
"""

import argparse
import glob as glob_mod
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

WATCHER_NAME = "harness_waiter"
WAKE_RECEIPT_SCHEMA = "liveness-wake-receipt/1"
PENDING_RECEIPT_SCHEMA = "liveness-pending-intervention/1"
HARVEST_MANIFEST_SCHEMA = "harness-harvest-manifest/1"
HARVEST_DELTA_SCHEMA = "harness-harvest-delta/1"

EXIT_OK = 0
EXIT_FAILLOUD = 1
EXIT_HARD_DEATH = 2
EXIT_FREEZE = 3
EXIT_VERIFY_INCOMPLETE = 4

DEFAULT_FREEZE_THRESHOLD_MIN = 20.0
DEFAULT_POLL_INTERVAL_S = 60.0
DEFAULT_VERIFICATION_GRACE_S = 30.0
POLL_GAP_FACTOR = 2.0  # gap > interval×此倍數＝異常（機器睡眠）→扣除間隔

TERMINAL_STATES = frozenset({"completed", "failed", "stopped"})

MAX_TAIL_BYTES = 65_536
MAX_MANIFEST_FILES = 2_000

_SUBAGENT_PREFIX = "sess_subagent_"


# ---------------------------------------------------------------------------
# 路徑常數集中地（觀察面 frozen 定義的唯一落點）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ZCodeLayout:
    """ZCode CLI 觀察面路徑——cli_root 可注入（測試用 tmp_path，零真機依賴）."""

    cli_root: Path

    @classmethod
    def default(cls) -> "ZCodeLayout":
        return cls(cli_root=Path.home() / ".zcode" / "cli")

    @property
    def rollout_root(self) -> Path:
        return self.cli_root / "rollout"

    @property
    def exec_root(self) -> Path:
        return self.cli_root / "exec"

    @property
    def artifact_root(self) -> Path:
        return self.cli_root / "artifacts"

    @property
    def agents_root(self) -> Path:
        return self.cli_root / "agents"

    def rollout_file(self, task_id: str) -> Path:
        return self.rollout_root / f"model-io-{task_id}.jsonl"

    def exec_dir(self, task_id: str) -> Path:
        return self.exec_root / task_id

    def artifact_dir(self, task_id: str) -> Path:
        return self.artifact_root / task_id


def agent_id_from_task(task_id: str) -> str | None:
    """taskId（childSessionId 全形）→ agentId 機械映射；非 subagent 形→None."""
    if not task_id.startswith(_SUBAGENT_PREFIX):
        return None
    agent_id = task_id[len(_SUBAGENT_PREFIX) :]
    return agent_id or None


# ---------------------------------------------------------------------------
# 觀察結果型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cursors:
    """四表面 cursor 快照（進度比對用；None＝該面目錄缺席＝合法）。"""

    rollout_size: int | None
    rollout_mtime_ns: int | None
    artifact_mtime_ns: int | None
    artifact_size: int | None
    exec_mtime_ns: int | None
    exec_size: int | None


@dataclass(frozen=True)
class TaskStatus:
    """`status(taskId)` 的可判讀結果（EP S1 欄位集）.

    exec_lease_checked＝False 表示 lease 面未查成（prober 不可判定；僅
    terminal 容許——F-11 terminal 短路 probe 失敗，freeze 迴圈不誤醒）；
    verify 對未查成 fail-closed STOP_INCOMPLETE（F-1 禁假確認）。
    """

    task_id: str
    state: str
    generation: tuple[str, str]  # (childSessionId, createdAt)
    created_at: str
    last_activity: datetime | None
    output_cursor: int
    exec_lease: tuple[str, ...]
    exec_lease_checked: bool
    cursors: Cursors


@dataclass(frozen=True)
class UnknownFace:
    """fail-loud 面：原因明示，禁猜禁誤報（T6）。"""

    reason: str
    detail: str = ""


def lsof_lease_prober(paths: Sequence[Path]) -> list[str] | None:
    """lsof 偵測 open fd lease；回 None＝lsof 不可判定（fail-loud 面）.

    lsof exit 0＝有命中；exit 1＝「無命中或錯誤」——二者不可由 exit code
    区分（實測皆 exit 1）：stderr 非空→錯誤→None（F-2），空→無命中→[]。
    其他 exit／逾時／找不到 binary＝None（禁猜）。路徑比對兩側先
    realpath 正規化（F-3：/tmp vs /private/tmp symlink 實證），回報值維持
    caller 傳入路徑。`-F pn` machine-readable 輸出，`n` 行為路徑。
    """
    if not paths:
        return []
    cmd = ["lsof", "-F", "pn", "--", *[str(p) for p in paths]]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 1 and proc.stderr.strip():
        return None  # exit 1 ＋ stderr 非空＝查詢錯誤（如檔案不存在），非無命中
    if proc.returncode not in (0, 1):
        return None
    reported = {
        os.path.realpath(line[1:])
        for line in proc.stdout.splitlines()
        if line.startswith("n")
    }
    return [str(p) for p in paths if os.path.realpath(str(p)) in reported]


def _files_in_dir(d: Path) -> list[Path]:
    """單層檔案列舉（exec/artifact 目錄為 flat 佈局）；缺席→空."""
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file())


def _newest_in_dir(d: Path) -> tuple[int | None, int | None]:
    """可選表面（exec/artifact）最新檔；檔案 stat 失敗（清除競速）→跳過該檔."""
    files = _files_in_dir(d)
    stats = []
    for p in files:
        try:
            stats.append(p.stat())
        except OSError:
            continue  # 列舉後消失＝表面清理競速——可選面不因它 fail-loud
    if not stats:
        return None, None
    newest = max(stats, key=lambda s: s.st_mtime_ns)
    return newest.st_mtime_ns, newest.st_size


class ZCodeLivenessSource:
    """四觀察面 adapter——路徑解析＋錨點存在性＋fail-loud（B path 換源不動語義）."""

    def __init__(
        self,
        layout: ZCodeLayout,
        lease_prober: Callable[[Sequence[Path]], list[str] | None] | None = None,
    ) -> None:
        self._layout = layout
        self._prober = lease_prober or lsof_lease_prober

    @property
    def layout(self) -> ZCodeLayout:
        return self._layout

    def resolve_metadata(self, agent_id: str) -> Path | UnknownFace:
        pattern = str(self._layout.agents_root / "sess_*" / agent_id / "metadata.json")
        hits = sorted(Path(p) for p in glob_mod.glob(pattern))
        if not hits:
            return UnknownFace("metadata-anchor-missing", f"glob 零命中：{pattern}")
        if len(hits) > 1:
            return UnknownFace(
                "metadata-glob-ambiguous",
                f"{len(hits)} 命中：{[str(h) for h in hits]}",
            )
        return hits[0]

    def read_metadata(self, path: Path) -> dict | UnknownFace:
        try:
            raw = path.read_text()
        except OSError as exc:
            return UnknownFace("metadata-unreadable", str(exc))
        try:
            meta = json.loads(raw)
        except json.JSONDecodeError as exc:
            # 半寫 torn read 同面——metadata 兩點寫入外的讀撞＝不可解析
            return UnknownFace("metadata-unparseable", str(exc))
        if not isinstance(meta, dict):
            return UnknownFace("metadata-corrupt", "非 JSON object")
        for key in ("agentId", "childSessionId", "createdAt", "status"):
            if not isinstance(meta.get(key), str) or not meta[key]:
                return UnknownFace("metadata-corrupt", f"缺必要欄位：{key}")
        if _parse_iso(meta["createdAt"]) is None:
            # F-6 對稱面：timestamp 不可解析＝禁靜默跳過 generation 對照
            return UnknownFace(
                "metadata-corrupt", f"createdAt 不可解析：{meta['createdAt']}"
            )
        return meta

    def status(self, task_id: str) -> TaskStatus | UnknownFace:
        agent_id = agent_id_from_task(task_id)
        if agent_id is None:
            return UnknownFace("invalid-task-id", task_id)
        meta_path = self.resolve_metadata(agent_id)
        if isinstance(meta_path, UnknownFace):
            return meta_path
        meta = self.read_metadata(meta_path)
        if isinstance(meta, UnknownFace):
            return meta
        state = meta["status"]
        terminal = state in TERMINAL_STATES
        rollout = self._layout.rollout_file(task_id)
        # F-10：stat 包 OSError——rollout 是必要錨點面，讀撞＝unknown 禁猜
        r_stat: os.stat_result | None = None
        if rollout.is_file():
            try:
                r_stat = rollout.stat()
            except OSError as exc:
                return UnknownFace("rollout-stat-failed", str(exc))
        if r_stat is None and not terminal:
            # running 而無 rollout＝liveness 錨點缺失——fail-loud 禁誤報
            # （terminal 後 rollout 清理＝機器合法行為，2026-09-20 實機實證）
            return UnknownFace("rollout-anchor-missing", str(rollout))
        a_mtime, a_size = _newest_in_dir(self._layout.artifact_dir(task_id))
        e_mtime, e_size = _newest_in_dir(self._layout.exec_dir(task_id))
        cursors = Cursors(
            rollout_size=r_stat.st_size if r_stat is not None else None,
            rollout_mtime_ns=r_stat.st_mtime_ns if r_stat is not None else None,
            artifact_mtime_ns=a_mtime,
            artifact_size=a_size,
            exec_mtime_ns=e_mtime,
            exec_size=e_size,
        )
        # 寫入者面（F-1）：terminal 亦列舉 exec/artifact 並 probe lease——
        # verify 的 STOP_CONFIRMED 不得跳過 detached writer 檢查
        exec_files = _files_in_dir(self._layout.exec_dir(task_id))
        raw_lease = self._prober(exec_files) if exec_files else []
        if raw_lease is None:
            if terminal:
                # F-11：terminal 短路 probe 失敗——freeze 迴圈不因 lsof 壞
                # 誤醒；以 checked=False 交 verify fail-closed（禁假確認）
                return TaskStatus(
                    task_id=task_id,
                    state=state,
                    generation=(meta["childSessionId"], meta["createdAt"]),
                    created_at=meta["createdAt"],
                    last_activity=None,
                    output_cursor=r_stat.st_size if r_stat is not None else 0,
                    exec_lease=(),
                    exec_lease_checked=False,
                    cursors=cursors,
                )
            return UnknownFace(
                "lease-prober-failed", "lsof 不可用或非預期 exit——禁猜 lease 面"
            )
        mtimes = [r_stat.st_mtime_ns] if r_stat is not None else []
        mtimes += [v for v in (a_mtime, e_mtime) if v is not None]
        return TaskStatus(
            task_id=task_id,
            state=state,
            generation=(meta["childSessionId"], meta["createdAt"]),
            created_at=meta["createdAt"],
            last_activity=(
                datetime.fromtimestamp(max(mtimes) / 1e9, tz=UTC) if mtimes else None
            ),
            output_cursor=r_stat.st_size if r_stat is not None else 0,
            exec_lease=tuple(str(p) for p in raw_lease),
            exec_lease_checked=True,
            cursors=cursors,
        )


# ---------------------------------------------------------------------------
# registry（S2 schema 的 S1 讀取面）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegistryEntry:
    task_id: str
    attempt_id: str
    created_at: str
    sink: str
    expected: object
    surviving_handles: tuple[str, ...]
    silence_budget_min: float | None


def _require_str(entry: dict, key: str) -> str | None:
    value = entry.get(key)
    return value if isinstance(value, str) and value else None


def load_registry(path: Path) -> list[RegistryEntry] | UnknownFace:
    """registry 讀取＋schema 校驗——檔缺席＝錨點缺失 fail-loud；空＝[]（exit 0）."""
    if not path.is_file():
        return UnknownFace("registry-missing", str(path))
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return UnknownFace("registry-unparseable", str(exc))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        return UnknownFace("registry-schema", '需 {"entries": [...]}')
    entries: list[RegistryEntry] = []
    for i, raw in enumerate(payload["entries"]):
        if not isinstance(raw, dict):
            return UnknownFace("registry-schema", f"entries[{i}] 非 object")
        task_id = _require_str(raw, "taskId")
        attempt_id = _require_str(raw, "attemptId")
        created_at = _require_str(raw, "createdAt")
        sink = _require_str(raw, "sink")
        if task_id is None or attempt_id is None or created_at is None or sink is None:
            return UnknownFace(
                "registry-schema",
                f"entries[{i}] 缺必要欄位 taskId/attemptId/createdAt/sink",
            )
        if _parse_iso(created_at) is None:
            # F-6：T5 fast path 的對照基準不可解析＝禁靜默跳過——fail-loud
            return UnknownFace(
                "registry-schema",
                f"entries[{i}] createdAt 不可解析：{created_at}",
            )
        handles_raw = raw.get("survivingHandles")
        if not isinstance(handles_raw, list) or not all(
            isinstance(h, str) for h in handles_raw
        ):
            return UnknownFace(
                "registry-schema", f"entries[{i}] survivingHandles 需 list[str]"
            )
        budget_raw = raw.get("silenceBudget")
        budget: float | None = None
        if budget_raw is not None:
            if not isinstance(budget_raw, (int, float)) or isinstance(budget_raw, bool):
                return UnknownFace(
                    "registry-schema", f"entries[{i}] silenceBudget 需數值（分鐘）"
                )
            if not (budget_raw > 0):
                return UnknownFace(
                    "registry-schema", f"entries[{i}] silenceBudget 需正數"
                )
            budget = float(budget_raw)
        entries.append(
            RegistryEntry(
                task_id=task_id,
                attempt_id=attempt_id,
                created_at=created_at,
                sink=sink,
                expected=raw.get("expected"),
                surviving_handles=tuple(handles_raw),
                silence_budget_min=budget,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# 凍結判準（FreezeDetector）
# ---------------------------------------------------------------------------


@dataclass
class WatchState:
    """單 entry 的輪詢累積狀態（T2 計數續走／T5 generation 對照）."""

    last_cursors: Cursors | None = None
    silent_acc_s: float = 0.0
    prev_poll_at: datetime | None = None
    generation: tuple[str, str] | None = None
    telemetry: tuple[str, ...] = ()


@dataclass(frozen=True)
class PollFresh:
    elapsed_s: float
    telemetry: tuple[str, ...] = ()


@dataclass(frozen=True)
class PollFrozen:
    elapsed_s: float
    cursors: Cursors


@dataclass(frozen=True)
class PollTerminal:
    state: str


@dataclass(frozen=True)
class PollHardDeath:
    reason: str


@dataclass(frozen=True)
class PollUnknown:
    reason: str
    detail: str = ""


PollResult = PollFresh | PollFrozen | PollTerminal | PollHardDeath | PollUnknown


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


class FreezeDetector:
    """凍結判準：三面 stat＋fd lease（lsof）＋poll-gap 扣除（frozen 判準表）."""

    def __init__(
        self,
        source: ZCodeLivenessSource,
        *,
        threshold_min: float = DEFAULT_FREEZE_THRESHOLD_MIN,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    ) -> None:
        self._source = source
        self._threshold_min = threshold_min
        self._poll_interval_s = poll_interval_s

    def threshold_for(self, entry: RegistryEntry) -> float:
        if entry.silence_budget_min is not None:
            return entry.silence_budget_min
        return self._threshold_min

    def poll(
        self, entry: RegistryEntry, state: WatchState, now: datetime
    ) -> tuple[PollResult, WatchState]:
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            if st.reason == "metadata-anchor-missing":
                # T5：metadata 消失＝identity 不在——hard-death fast path
                return PollHardDeath("metadata-gone"), state
            return PollUnknown(st.reason, st.detail), state

        # T5：registry attempt createdAt 對照（首次 poll 即比——fast path）
        reg_created = _parse_iso(entry.created_at)
        meta_created = _parse_iso(st.created_at)
        if (
            reg_created is not None
            and meta_created is not None
            and (reg_created != meta_created)
        ):
            return PollHardDeath("generation-mismatch-registry-createdAt"), state
        # T5：輪詢間 generation（childSessionId＋createdAt）異動對照
        if state.generation is not None and st.generation != state.generation:
            return PollHardDeath("generation-mismatch"), state

        threshold_s = self.threshold_for(entry) * 60.0
        if st.state in TERMINAL_STATES:
            reset = WatchState(
                last_cursors=st.cursors,
                prev_poll_at=now,
                generation=st.generation,
            )
            return PollTerminal(st.state), reset

        gap = (
            None
            if state.prev_poll_at is None
            else (now - state.prev_poll_at).total_seconds()
        )
        direct = (
            0.0
            if st.last_activity is None
            else (now - st.last_activity).total_seconds()
        )
        telemetry: list[str] = []
        if direct < 0:
            # F-7：表面 mtime 在未來（時鐘回撥）——記 telemetry，acc 依自身規則
            telemetry.append("clock-rollback")
        if gap is not None and gap < 0:
            # 時鐘回撥：elapsed<0 → Fresh＋telemetry（frozen 條款）
            telemetry.append("clock-rollback")
            acc = 0.0
        elif state.last_cursors is not None and st.cursors != state.last_cursors:
            acc = 0.0  # T2：三面任一推進——計數歸零續走
        elif st.exec_lease:
            acc = 0.0  # SM-2：open fd lease＝長工具呼叫豁免
        elif gap is None:
            acc = max(direct, 0.0)  # 首輪：表面 mtime 齡期即已存在的靜默
        elif gap > self._poll_interval_s * POLL_GAP_FACTOR:
            # SM-7：poll gap 異常（機器睡眠）→扣除間隔（只記一個 interval）
            telemetry.append("poll-gap-deducted")
            acc = state.silent_acc_s + min(gap, self._poll_interval_s)
        else:
            acc = state.silent_acc_s + gap

        new_state = WatchState(
            last_cursors=st.cursors,
            silent_acc_s=acc,
            prev_poll_at=now,
            generation=st.generation,
            telemetry=tuple(telemetry),
        )
        effective = min(acc, max(direct, 0.0))
        if effective >= threshold_s:
            return PollFrozen(effective, st.cursors), new_state
        return PollFresh(effective, tuple(telemetry)), new_state


# ---------------------------------------------------------------------------
# 收割器（bounded；raw bytes；partial 標記）
# ---------------------------------------------------------------------------


def _sanitize(component: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", component)
    return cleaned or "unnamed"


def cursors_to_dict(c: Cursors) -> dict:
    return {
        "rolloutSize": c.rollout_size,
        "rolloutMtimeNs": c.rollout_mtime_ns,
        "artifactMtimeNs": c.artifact_mtime_ns,
        "artifactSize": c.artifact_size,
        "execMtimeNs": c.exec_mtime_ns,
        "execSize": c.exec_size,
    }


class Harvester:
    """bounded 收割：manifest→metadata copy→rollout raw tail；超限 partial 標記."""

    def __init__(
        self,
        source: ZCodeLivenessSource,
        layout: ZCodeLayout,
        liveness_root: Path,
        *,
        max_tail_bytes: int = MAX_TAIL_BYTES,
        max_manifest_files: int = MAX_MANIFEST_FILES,
    ) -> None:
        self._source = source
        self._layout = layout
        self._liveness_root = liveness_root
        self._max_tail_bytes = max_tail_bytes
        self._max_manifest_files = max_manifest_files

    def _surface_files(self, task_id: str) -> list[tuple[str, Path]]:
        pairs: list[tuple[str, Path]] = [
            ("rollout", self._layout.rollout_file(task_id))
        ]
        pairs += [
            ("artifact", p) for p in _files_in_dir(self._layout.artifact_dir(task_id))
        ]
        pairs += [("exec", p) for p in _files_in_dir(self._layout.exec_dir(task_id))]
        return pairs

    def _bundle_dir(self, task_id: str, attempt_id: str, leaf: str = "") -> Path:
        bundle = (
            self._liveness_root / "harvest" / _sanitize(task_id) / _sanitize(attempt_id)
        )
        if leaf:
            bundle = bundle / leaf
        bundle.mkdir(parents=True, exist_ok=True)
        return bundle

    def harvest(
        self, entry: RegistryEntry, freeze_cursors: Cursors | None = None
    ) -> tuple[dict, Path] | UnknownFace:
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            return st
        agent_id = agent_id_from_task(entry.task_id)
        meta_path = (
            self._source.resolve_metadata(agent_id)
            if agent_id is not None
            else UnknownFace("invalid-task-id", entry.task_id)
        )
        if isinstance(meta_path, UnknownFace):
            return meta_path
        bundle = self._bundle_dir(entry.task_id, entry.attempt_id)
        try:
            (bundle / "metadata.json").write_bytes(meta_path.read_bytes())
        except OSError as exc:
            return UnknownFace("harvest-metadata-copy-failed", str(exc))
        listing = self._surface_files(entry.task_id)
        truncated = len(listing) > self._max_manifest_files
        files = []
        for surface, path in listing[: self._max_manifest_files]:
            try:
                stat = path.stat()
            except OSError as exc:
                # F-10：收割 manifest 必須準確——stat 讀撞＝fail-loud 不收割
                return UnknownFace("harvest-stat-failed", str(exc))
            files.append(
                {
                    "surface": surface,
                    "path": str(path),
                    "size": stat.st_size,
                    "mtimeNs": stat.st_mtime_ns,
                }
            )
        rollout_path = self._layout.rollout_file(entry.task_id)
        try:
            # F-8：seek-based tail——殭屍 rollout 可達數百 MB，禁全檔載入
            size = rollout_path.stat().st_size
            with rollout_path.open("rb") as fh:
                fh.seek(max(0, size - self._max_tail_bytes))
                tail = fh.read()
        except OSError as exc:
            return UnknownFace("harvest-rollout-read-failed", str(exc))
        (bundle / "rollout.tail.jsonl").write_bytes(tail)
        tail_partial = size > len(tail)
        resumed: bool | None = None
        if freeze_cursors is not None:
            resumed = st.cursors != freeze_cursors
        manifest = {
            "schema": HARVEST_MANIFEST_SCHEMA,
            "watcher": WATCHER_NAME,
            "taskId": entry.task_id,
            "agentId": agent_id,
            "attemptId": entry.attempt_id,
            "harvestAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "harvestPartial": bool(truncated or tail_partial),
            "cursors": cursors_to_dict(st.cursors),
            "filesTruncated": truncated,
            "files": files,
            "tails": {
                "rollout": {
                    "path": "rollout.tail.jsonl",
                    "bytes": len(tail),
                    "sha256": hashlib.sha256(tail).hexdigest(),
                    "partial": tail_partial,
                }
            },
            "metadata": {
                "path": "metadata.json",
                "status": st.state,
                "createdAt": st.created_at,
            },
            "resumedDuringQuarantine": resumed,
        }
        (bundle / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        return manifest, bundle

    def harvest_delta(
        self, entry: RegistryEntry, manifest_path: Path
    ) -> tuple[dict, Path] | UnknownFace:
        """STOP 後增量收割（harvest B；主 session 以 --harvest-delta 呼叫）."""
        try:
            prev = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            return UnknownFace("delta-prev-manifest-unparseable", str(exc))
        if (
            not isinstance(prev, dict)
            or prev.get("schema") != HARVEST_MANIFEST_SCHEMA
            or prev.get("taskId") != entry.task_id
            or not isinstance(prev.get("cursors"), dict)
        ):
            return UnknownFace(
                "delta-prev-manifest-schema",
                "需 harvest manifest（schema/taskId/cursors 對得上）",
            )
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            return st
        listing = self._surface_files(entry.task_id)
        truncated = len(listing) > self._max_manifest_files
        prev_sizes = {
            f.get("path"): f.get("size")
            for f in prev.get("files", [])
            if isinstance(f, dict)
        }
        new_files: list[dict] = []
        grown_files: list[dict] = []
        for surface, path in listing[: self._max_manifest_files]:
            try:
                stat = path.stat()
            except OSError as exc:
                # F-10：delta 判準（寫入者偵測）必須準確——讀撞＝fail-loud
                return UnknownFace("harvest-stat-failed", str(exc))
            row = {
                "surface": surface,
                "path": str(path),
                "size": stat.st_size,
                "mtimeNs": stat.st_mtime_ns,
            }
            prev_size = prev_sizes.get(str(path))
            if prev_size is None:
                new_files.append(row)
            elif stat.st_size > prev_size:
                row["prevSize"] = prev_size
                grown_files.append(row)
        cursors = cursors_to_dict(st.cursors)
        resumed = cursors != prev["cursors"]
        attempt_id = (
            str(prev["attemptId"])
            if isinstance(prev.get("attemptId"), str)
            else "delta"
        )
        bundle = self._bundle_dir(entry.task_id, attempt_id, leaf="delta")
        delta = {
            "schema": HARVEST_DELTA_SCHEMA,
            "watcher": WATCHER_NAME,
            "taskId": entry.task_id,
            "attemptId": attempt_id,
            "prevManifestPath": str(manifest_path),
            "prevCursors": prev["cursors"],
            "cursors": cursors,
            "newFiles": new_files,
            "grownFiles": grown_files,
            "harvestPartial": truncated,
            "resumedDuringQuarantine": resumed,
        }
        (bundle / "manifest.json").write_text(
            json.dumps(delta, ensure_ascii=False, indent=2) + "\n"
        )
        return delta, bundle


def write_pending_receipt(
    liveness_root: Path,
    entry: RegistryEntry,
    manifest: dict,
    harvest_dir: Path,
    *,
    elapsed_s: float,
    resumed: bool,
) -> Path:
    """pending intervention receipt——dedup key＝taskId＋attemptId，同 attempt 不重發."""
    pending_dir = liveness_root / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    path = pending_dir / f"{_sanitize(entry.task_id)}.json"
    if path.is_file():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = None
        if isinstance(existing, dict) and existing.get("attemptId") == entry.attempt_id:
            return path  # dedup：已有 pending 不重發
    manifest_path = harvest_dir / "manifest.json"
    receipt = {
        "schema": PENDING_RECEIPT_SCHEMA,
        "taskId": entry.task_id,
        "attemptId": entry.attempt_id,
        "dedupKey": f"{entry.task_id}+{entry.attempt_id}",
        "harvestDir": str(harvest_dir),
        "manifestPath": str(manifest_path),
        "survivingHandles": list(entry.surviving_handles),
        "frozenElapsedMin": round(elapsed_s / 60.0, 2),
        "resumedDuringQuarantine": resumed,
        "suggestedAction": f"TaskStop {entry.task_id}",
        "createdAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return path


# ---------------------------------------------------------------------------
# 輸出 helpers
# ---------------------------------------------------------------------------


class _Writable(Protocol):
    """stdout/stderr 的最小寫入面（sys.stdout／TextIOBase／StringIO 共通）."""

    def write(self, s: str) -> int | None: ...

    def flush(self) -> None: ...


def _emit(file: _Writable, text: str) -> None:
    file.write(text + "\n")
    file.flush()


def _dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _emit_face(
    out: _Writable,
    err: _Writable,
    state: str,
    *,
    task_id: str | None,
    face: UnknownFace,
) -> int:
    _emit(
        out,
        _dumps(
            {
                "state": state,
                "taskId": task_id,
                "reason": face.reason,
                "detail": face.detail,
            }
        ),
    )
    _emit(err, f"[{WATCHER_NAME}] {state}: {face.reason} {face.detail}".rstrip())
    return EXIT_FAILLOUD


def _system_now() -> datetime:
    return datetime.now(tz=UTC)


# ---------------------------------------------------------------------------
# 主迴圈（T1-T6；狀態機實作對應 module docstring frozen spec）
# ---------------------------------------------------------------------------


def run_watcher(
    layout: ZCodeLayout,
    registry_path: Path,
    liveness_root: Path | None = None,
    *,
    threshold_min: float = DEFAULT_FREEZE_THRESHOLD_MIN,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    max_cycles: int | None = None,
    now_fn: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    now = now_fn or _system_now
    do_sleep = sleep_fn or time.sleep
    liveness = (
        liveness_root
        if liveness_root is not None
        else registry_path.parent / "liveness"
    )
    src = source or ZCodeLivenessSource(layout)
    detector = FreezeDetector(
        src, threshold_min=threshold_min, poll_interval_s=poll_interval_s
    )
    harvester = Harvester(src, layout, liveness)

    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=None, face=entries)
    if not entries:
        _emit(err, f"[{WATCHER_NAME}] registry 空——無可監視物（等待語義）")
        _emit(out, _dumps({"state": "empty-registry", "entries": 0}))
        return EXIT_OK

    # F-4：基線＝task→attempt；純增項吸納續 watch，減項／attempt 變更才 hard-death
    baseline: dict[str, str] = {e.task_id: e.attempt_id for e in entries}
    states: dict[str, WatchState] = {e.task_id: WatchState() for e in entries}
    cycle = 0
    while True:
        cycle += 1
        if max_cycles is not None and cycle > max_cycles:
            _emit(
                out,
                _dumps(
                    {"state": "error", "reason": f"max-cycles-exceeded:{max_cycles}"}
                ),
            )
            _emit(err, f"[{WATCHER_NAME}] max-cycles {max_cycles} 用盡——內部錯收場")
            return EXIT_FAILLOUD
        current = load_registry(registry_path)
        if isinstance(current, UnknownFace):
            return _emit_face(out, err, "unknown", task_id=None, face=current)
        # T5：registry entry 消失／attempt 變更＝hard-death fast path（禁 retry）；
        # 純增項（正常追加註冊）＝吸納進監視集續 watch（F-4：增項非死亡訊號）
        current_map = {e.task_id: e for e in current}
        gone_or_refenced = [
            task
            for task, attempt in baseline.items()
            if task not in current_map or current_map[task].attempt_id != attempt
        ]
        if gone_or_refenced:
            tail = {
                "state": "hard-death-wake",
                "taskId": None,
                "reason": "registry-entry-changed",
                "detail": f"registry 監視集減項／attempt 變更：{gone_or_refenced}"
                "——重生／重派跡象，禁 retry",
            }
            _emit(out, _dumps(tail))
            _emit(err, f"[{WATCHER_NAME}] {tail['reason']}——立即 wake，禁 retry")
            return EXIT_HARD_DEATH
        for entry in current:
            if entry.task_id not in baseline:
                baseline[entry.task_id] = entry.attempt_id
                states[entry.task_id] = WatchState()
                _emit(
                    out,
                    f"[{WATCHER_NAME}] registry 純增項吸納：{entry.task_id}"
                    f"（attempt={entry.attempt_id}）——續 watch",
                )

        cycle_now = now()
        results: list[tuple[RegistryEntry, PollResult]] = []
        for entry in current:
            verdict, states[entry.task_id] = detector.poll(
                entry, states[entry.task_id], cycle_now
            )
            kind = type(verdict).__name__.removeprefix("Poll").lower()
            tele = getattr(verdict, "telemetry", ())
            _emit(
                out,
                f"[{WATCHER_NAME}] cycle={cycle} task={entry.task_id} "
                f"verdict={kind} elapsed={getattr(verdict, 'elapsed_s', 0.0):.1f}s "
                f"tele={','.join(tele) if tele else '-'}",
            )
            results.append((entry, verdict))

        hard: tuple[RegistryEntry, PollHardDeath] | None = None
        unknown: tuple[RegistryEntry, PollUnknown] | None = None
        frozen: tuple[RegistryEntry, PollFrozen] | None = None
        for entry, verdict in results:
            if isinstance(verdict, PollHardDeath) and hard is None:
                hard = (entry, verdict)
            elif isinstance(verdict, PollUnknown) and unknown is None:
                unknown = (entry, verdict)
            elif isinstance(verdict, PollFrozen) and frozen is None:
                frozen = (entry, verdict)

        if hard is not None:
            entry, verdict = hard
            _emit(
                out,
                _dumps(
                    {
                        "state": "hard-death-wake",
                        "taskId": entry.task_id,
                        "reason": verdict.reason,
                        "detail": "generation mismatch／metadata 消失——禁 retry",
                    }
                ),
            )
            _emit(err, f"[{WATCHER_NAME}] hard-death: {entry.task_id}——立即 wake")
            return EXIT_HARD_DEATH

        if unknown is not None:
            entry, verdict = unknown
            return _emit_face(
                out,
                err,
                "unknown",
                task_id=entry.task_id,
                face=UnknownFace(verdict.reason, verdict.detail),
            )

        if frozen is not None:
            # T3／wake 後生命週期：對第一個凍結收割＋exit 3——其餘 entry 中止監視
            entry, verdict = frozen
            harvest = harvester.harvest(entry, freeze_cursors=verdict.cursors)
            if isinstance(harvest, UnknownFace):
                return _emit_face(
                    out, err, "unknown", task_id=entry.task_id, face=harvest
                )
            manifest, bundle = harvest
            pending = write_pending_receipt(
                liveness,
                entry,
                manifest,
                bundle,
                elapsed_s=verdict.elapsed_s,
                resumed=bool(manifest.get("resumedDuringQuarantine")),
            )
            wake = {
                "state": "freeze-wake",
                "schema": WAKE_RECEIPT_SCHEMA,
                "taskId": entry.task_id,
                "attemptId": entry.attempt_id,
                "frozenElapsedMin": round(verdict.elapsed_s / 60.0, 2),
                "resumedDuringQuarantine": manifest.get("resumedDuringQuarantine"),
                "harvestDir": str(bundle),
                "manifestPath": str(bundle / "manifest.json"),
                "pendingReceiptPath": str(pending),
                "survivingHandles": list(entry.surviving_handles),
                "suggestedAction": f"TaskStop {entry.task_id}",
                "manifest": manifest,
            }
            _emit(out, _dumps(wake))
            _emit(
                err,
                f"[{WATCHER_NAME}] freeze: {entry.task_id} "
                f"{verdict.elapsed_s:.0f}s 靜默——已收割，喚醒主 session 處置",
            )
            return EXIT_FREEZE

        terminal_states = [v.state for _e, v in results if isinstance(v, PollTerminal)]
        if len(terminal_states) == len(results):
            _emit(
                out,
                _dumps(
                    {
                        "state": "all-terminal",
                        "summary": {
                            "entries": len(results),
                            "terminal": sorted(set(terminal_states)),
                        },
                    }
                ),
            )
            return EXIT_OK

        do_sleep(poll_interval_s)


# ---------------------------------------------------------------------------
# STOP verification（T8/T9）與 harvest delta invocation
# ---------------------------------------------------------------------------


def run_verify(
    layout: ZCodeLayout,
    registry_path: Path,
    task_id: str,
    *,
    grace_s: float = DEFAULT_VERIFICATION_GRACE_S,
    sleep_fn: Callable[[float], None] | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--verify <taskId>：metadata terminal＋cursors grace 靜止→STOP_CONFIRMED.

    fail-closed：任何面無法確認（含 metadata 消失、lsof 不可判定）＝
    STOP_INCOMPLETE（禁重派歸主 session 判定）。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    do_sleep = sleep_fn or time.sleep
    src = source or ZCodeLivenessSource(layout)
    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=task_id, face=entries)
    entry = next((e for e in entries if e.task_id == task_id), None)
    if entry is None:
        return _emit_face(
            out,
            err,
            "unknown",
            task_id=task_id,
            face=UnknownFace("registry-entry-missing-for-verify", str(registry_path)),
        )

    surviving = list(entry.surviving_handles)
    reasons: list[str] = []

    def _face_reason(face: UnknownFace) -> str:
        return f"{face.reason}: {face.detail}".rstrip(": ")

    first = src.status(task_id)
    cursors_before: Cursors | None = None
    if isinstance(first, UnknownFace):
        reasons.append(_face_reason(first))
    else:
        cursors_before = first.cursors
    do_sleep(grace_s)
    st2 = src.status(task_id)
    terminal_state: str | None = None
    if isinstance(st2, UnknownFace):
        reasons.append(_face_reason(st2))
    else:
        terminal_state = st2.state
        if st2.state not in TERMINAL_STATES:
            reasons.append(f"metadata-not-terminal:{st2.state}")
        if cursors_before is not None and st2.cursors != cursors_before:
            reasons.append("cursors-moved-during-grace")
        if not st2.exec_lease_checked:
            # F-11 面：probe 不可判定——verify 端 fail-closed 禁假確認
            reasons.append("lease-unknown:prober-undecidable")
        if st2.exec_lease:
            surviving.extend(le for le in st2.exec_lease if le not in surviving)
            reasons.append("exec-lease-active")
    if not reasons and terminal_state in TERMINAL_STATES:
        _emit(
            out,
            _dumps(
                {
                    "state": "STOP_CONFIRMED",
                    "taskId": task_id,
                    "terminal": terminal_state,
                    "cursorsStable": True,
                    "survivingHandles": surviving,
                }
            ),
        )
        _emit(err, f"[{WATCHER_NAME}] STOP_CONFIRMED: {task_id}")
        return EXIT_OK
    _emit(
        out,
        _dumps(
            {
                "state": "STOP_INCOMPLETE",
                "taskId": task_id,
                "reasons": reasons,
                "survivingHandles": surviving,
            }
        ),
    )
    _emit(
        err,
        f"[{WATCHER_NAME}] STOP_INCOMPLETE: {task_id}——禁重派，detached child 見 survivingHandles",
    )
    return EXIT_VERIFY_INCOMPLETE


def run_harvest_delta(
    layout: ZCodeLayout,
    liveness_root: Path,
    task_id: str,
    manifest_path: Path,
    *,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--harvest-delta <taskId> <manifest>：STOP_CONFIRMED 後增量收割（harvest B）."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    src = source or ZCodeLivenessSource(layout)
    harvester = Harvester(src, layout, liveness_root)
    try:
        prev = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        prev = None
    raw_attempt = prev.get("attemptId") if isinstance(prev, dict) else None
    attempt_id = raw_attempt if isinstance(raw_attempt, str) else "delta"
    entry = RegistryEntry(
        task_id=task_id,
        attempt_id=attempt_id,
        created_at="",
        sink="",
        expected=None,
        surviving_handles=(),
        silence_budget_min=None,
    )
    result = harvester.harvest_delta(entry, manifest_path)
    if isinstance(result, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=task_id, face=result)
    delta, bundle = result
    _emit(
        out,
        _dumps(
            {
                "state": "harvest-delta",
                "taskId": task_id,
                "manifestPath": str(bundle / "manifest.json"),
                "delta": delta,
            }
        ),
    )
    _emit(
        err,
        f"[{WATCHER_NAME}] harvest-delta: {task_id} "
        f"new={len(delta['newFiles'])} grown={len(delta['grownFiles'])} "
        f"resumed={delta['resumedDuringQuarantine']}",
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# dispatch 註冊（S2 寫入端——schema 逐欄對齊 load_registry 讀取面）
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, payload: dict) -> None:
    """atomic write：同目錄隱名 tmp＋os.replace（讀面永見完整檔，無半寫）."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def run_register(
    layout: ZCodeLayout,
    registry_path: Path,
    task_id: str,
    *,
    attempt_id: str | None,
    sink: str | None,
    expected_raw: str | None = None,
    surviving_handles: Sequence[str] = (),
    silence_budget_min: float | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--register <taskId>：dispatch 當下寫入 registry entry（S2 寫入端）.

    `createdAt` 由 agent metadata 機械讀取（generation anchor——T5 對照
    基準，禁寫牆鐘）；metadata 不可解析／childSessionId 不符＝fail-loud。
    其餘 fail-loud 面：欄位無效（task 非 subagent 形／attempt/sink 空／
    expected 非 JSON／silenceBudget 非正數）、同 taskId 重註冊、既有
    registry 損壞或 schema 不符（禁覆蓋——損壞比缺失危險）。失敗一律不
    落地半套檔；成功以 atomic write 全檔替換。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    def fail(reason: str, detail: str) -> int:
        return _emit_face(
            out, err, "unknown", task_id=task_id, face=UnknownFace(reason, detail)
        )

    agent_id = agent_id_from_task(task_id)
    if agent_id is None:
        return fail("invalid-task-id", f"需 {_SUBAGENT_PREFIX} 前綴：{task_id}")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        return fail("invalid-attempt-id", "需非空字串（--attempt-id）")
    if not isinstance(sink, str) or not sink.strip():
        return fail("invalid-sink", "需非空字串（--sink）")
    expected: object = None
    if expected_raw is not None:
        try:
            expected = json.loads(expected_raw)
        except json.JSONDecodeError as exc:
            return fail("expected-unparseable", f"需 JSON 字串：{exc}")
    if silence_budget_min is not None and not (
        isinstance(silence_budget_min, (int, float))
        and not isinstance(silence_budget_min, bool)
        and silence_budget_min > 0
    ):
        return fail("silence-budget-invalid", "需正數（分鐘）")
    handles = tuple(h.strip() for h in surviving_handles)
    if any(not h for h in handles):
        return fail("invalid-surviving-handle", "handle 需非空白（--surviving-handle）")

    src = source or ZCodeLivenessSource(layout)
    meta_path = src.resolve_metadata(agent_id)
    if isinstance(meta_path, UnknownFace):
        # spawn 未落地／taskId 打錯——註冊當下就可判，禁猜禁拖到輪詢
        return fail(meta_path.reason, meta_path.detail)
    meta = src.read_metadata(meta_path)
    if isinstance(meta, UnknownFace):
        return fail(meta.reason, meta.detail)
    if meta["childSessionId"] != task_id:
        return fail(
            "metadata-generation-mismatch",
            f"childSessionId 不符：{meta['childSessionId']}",
        )

    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        if entries.reason != "registry-missing":
            return fail(entries.reason, entries.detail)  # 禁覆蓋損壞 registry
        raw_entries: list = []
    else:
        try:
            payload = json.loads(registry_path.read_text())
        except (OSError, ValueError) as e:
            return fail("registry-read-failed", f"第二次讀取失敗：{e}")
        raw_entries = payload["entries"]
        if any(e.task_id == task_id for e in entries):
            return fail(
                "duplicate-registration",
                f"taskId 已註冊：{task_id}——新 attempt 前先移除舊 entry",
            )
    entry: dict = {
        "taskId": task_id,
        "attemptId": attempt_id,
        "createdAt": meta["createdAt"],
        "sink": sink,
        "expected": expected,
        "survivingHandles": list(handles),
    }
    if silence_budget_min is not None:
        entry["silenceBudget"] = float(silence_budget_min)
    raw_entries.append(entry)
    _atomic_write_json(registry_path, {"entries": raw_entries})
    _emit(
        out,
        _dumps(
            {
                "state": "registered",
                "taskId": task_id,
                "attemptId": attempt_id,
                "registryPath": str(registry_path),
                "entry": entry,
            }
        ),
    )
    _emit(err, f"[{WATCHER_NAME}] registered: {task_id} attempt={attempt_id}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None, *, layout: ZCodeLayout | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=WATCHER_NAME,
        description=(
            "ZCode 子 agent 凍結偵測＋收割＋停止協議（AIR-149 S1＋S2）——"
            "watcher 永不 stop／重派，wake 歸主 session 處置"
        ),
        epilog="契約：EP 09-20-harness-liveness-watcher S1＋S2；"
        "狀態機 frozen spec 見 module docstring。",
    )
    parser.add_argument(
        "registry",
        type=Path,
        metavar="registry",
        help="workspace-local liveness registry（.agent-tmp/liveness-registry.json）",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify",
        metavar="taskId",
        default=None,
        help="STOP verification：metadata terminal＋cursors grace 靜止→"
        "STOP_CONFIRMED（exit 0）／STOP_INCOMPLETE（exit 4）",
    )
    mode.add_argument(
        "--harvest-delta",
        nargs=2,
        metavar=("taskId", "manifest"),
        default=None,
        help="STOP_CONFIRMED 後增量收割（harvest B）",
    )
    mode.add_argument(
        "--register",
        metavar="taskId",
        default=None,
        help="dispatch 註冊：寫入 registry entry（S2）——需 --attempt-id/--sink；"
        "同 taskId 重註冊＝fail-loud",
    )
    parser.add_argument(
        "--attempt-id",
        default=None,
        help="--register 必帶：本 attempt 唯一識別",
    )
    parser.add_argument(
        "--sink",
        default=None,
        help="--register 必帶：bounded receipt sink（AIR-135.7 AC#2 投影）",
    )
    parser.add_argument(
        "--expected",
        default=None,
        help="--register 選帶：sink 驗收條件（JSON 字串）",
    )
    parser.add_argument(
        "--surviving-handle",
        action="append",
        default=None,
        metavar="HANDLE",
        help="--register 選帶：dispatch 前已知 detached job ownership handle（可多次）",
    )
    parser.add_argument(
        "--silence-budget-min",
        type=float,
        default=None,
        metavar="MIN",
        help="--register 選帶：silence lease 分鐘（缺席＝20m 標準門檻）",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
        help=f"輪詢間隔秒（預設 {DEFAULT_POLL_INTERVAL_S:.0f}）",
    )
    parser.add_argument(
        "--freeze-threshold",
        type=float,
        default=DEFAULT_FREEZE_THRESHOLD_MIN,
        help=f"凍結門檻分鐘（預設 {DEFAULT_FREEZE_THRESHOLD_MIN:.0f}；"
        "entry silenceBudget 可逐案覆寫）",
    )
    parser.add_argument(
        "--grace",
        type=float,
        default=DEFAULT_VERIFICATION_GRACE_S,
        help=f"--verify cursors 靜止觀察窗秒（預設 {DEFAULT_VERIFICATION_GRACE_S:.0f}）",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="輪詢上限（測試／看門狗用；預設無限）",
    )
    args = parser.parse_args(argv)

    layout = layout or ZCodeLayout.default()
    liveness = args.registry.parent / "liveness"
    if args.verify is not None:
        return run_verify(layout, args.registry, args.verify, grace_s=args.grace)
    if args.harvest_delta is not None:
        task_id, manifest = args.harvest_delta
        return run_harvest_delta(layout, liveness, task_id, Path(manifest))
    if args.register is not None:
        return run_register(
            layout,
            args.registry,
            args.register,
            attempt_id=args.attempt_id,
            sink=args.sink,
            expected_raw=args.expected,
            surviving_handles=tuple(args.surviving_handle or ()),
            silence_budget_min=args.silence_budget_min,
        )
    return run_watcher(
        layout,
        args.registry,
        liveness,
        threshold_min=args.freeze_threshold,
        poll_interval_s=args.poll_interval,
        max_cycles=args.max_cycles,
    )


if __name__ == "__main__":
    raise SystemExit(main())
