#!/usr/bin/env python3
"""zombie_core — spawn 僵屍判定核心（AIR-296；GLM 90 樣本校準簽章單一源）.

一句話：ZCode 原生 subagent 的僵屍三簽章／五級告警／去重鍵的唯一實作——
session-local（harness_waiter advisory face）與全域 sweeper
（agent_liveness_sweep --zcode-scan）共用本核心，禁第二實作。

承重發現（GLM 90 樣本，卡 AIR-296 notes）
------
metadata.json 終生只寫兩次（spawn＋收尾）——「metadata 凍結」對執行中
agent 是常態，禁當僵屍判準。真心跳面＝artifacts（每 tool call 一檔）；
判定軸＝createdAt（registered_at）與 artifacts 最新檔（last_progress_at），
禁 metadata mtime 直接比較。

實測佈局（真機唯讀驗證 2026-10-09）
------
- metadata＝`<cli>/agents/sess_<parent>/<agentId>/metadata.json`
- artifacts 心跳＝`<cli>/artifacts/sess_subagent_<agentId>/`
- output.txt（型 B 面）＝metadata `outputFile` 欄指向
  `agents/sess_<parent>/<agentId>/output.txt`——**不在 artifacts 內**

三簽章（機械判準照抄——GLM 90 樣本校準）
------
| 型 | 機械判準 | 閾值依據 |
|---|---|---|
| A stillbirth | running ∧ artifacts 缺/空 ∧ age>60min | 60min＞首檔 max 48min（n=40：p50=12/p95=38/max=48） |
| 中斷氣 | running ∧ artifacts 最新檔凍結>180min | ≈1.7×輪內間距 max 106min |
| B silent-completion | running ∧ output.txt 存在 → 即報 | output.txt 只在收尾寫一次；誤報面≈零 |

五級告警（codex 表）與 producer 對照
------
| 級 | producer | 備註 |
|---|---|---|
| START_MISSING | sweeper（型 A 60min 校準）＋waiter（spawn+5m 提前驗活＋2m 複查） | 提前版對慢啟動活體有雜訊——advisory 可接受 |
| SILENCE | sweeper（中斷氣 180min）＋waiter 既有 20m timebox 收割（T4） | |
| COMPLETION_SUSPECTED | sweeper（型 B 即報）＋waiter（產物＋靜止 ≥15m 三條件） | 只提醒 collection owner，禁自動宣告完成 |
| HARD_DEATH | waiter T5 既有權威路徑（generation mismatch／註冊身份消失） | sweeper 無 registry join 不產生——缺席非證據（AIR-162 矩陣） |
| UNKNOWN | 本核心 MetaError（JSON 損壞／必要欄位缺／createdAt 不可解析） | fail-loud 列報——禁自動結案 |

鐵律：偵測/處置分離（AIR-135.7）——本核心純判定，零處置面；禁自動
TaskStop／重派／寫 completed；處置恆人裁。唯讀保證：全部函式只 stat/read。
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# --- 五級告警（codex 表——層級唯一命名源） ---

ALERT_START_MISSING = "START_MISSING"
ALERT_SILENCE = "SILENCE"
ALERT_COMPLETION_SUSPECTED = "COMPLETION_SUSPECTED"
ALERT_HARD_DEATH = "HARD_DEATH"
ALERT_UNKNOWN = "UNKNOWN"

# --- 校準閾值（GLM 90 樣本；waiter 提前驗活＝codex 五級表） ---

STILLBIRTH_AGE_MIN_DEFAULT = 60.0  # 型 A：>首檔 max 48min
INTERRUPTED_FROZEN_MIN_DEFAULT = 180.0  # 中斷氣：≈1.7×間距 max 106min
START_MISSING_MIN_DEFAULT = 5.0  # codex：spawn 5m 無開工證據
START_MISSING_RECHECK_MIN_DEFAULT = 2.0  # codex：間隔 2m 再確認
COMPLETION_QUIESCE_MIN_DEFAULT = 15.0  # codex：活動靜止 ≥15m

# metadata status 面：running＝分類對象；此集合＝terminal face（跳過）；
# 其他未知值＝terminal_other（coverage 可見，不猜）
TERMINAL_STATUSES = frozenset({"completed", "failed", "stopped"})

SUBAGENT_DIR_PREFIX = "sess_subagent_"
OUTPUT_BASENAME = "output.txt"


def dedup_key(attempt_id: str, alert_type: str) -> str:
    """attempt_id+alert_type 去重鍵（同 attempt 同級不重複通知的消費端契約）."""
    return f"{attempt_id}+{alert_type}"


@dataclass(frozen=True)
class MetaError:
    """fail-loud 面：metadata 不可判讀（UNKNOWN 事件來源——禁猜禁誤報）."""

    reason: str
    detail: str = ""


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return parsed if parsed.tzinfo is not None else None


def read_metadata(path: Path) -> dict | MetaError:
    """讀單具 metadata——JSON 損壞／必要欄位缺／createdAt 不可解析＝MetaError.

    createdAt 為 **running 條件的判定軸**（age 計算）——僅對 status=running
    必要；terminal 條件無 createdAt 合法（舊 schema 實證 2026-10-09：74 具
    stopped＋completedAt 無 createdAt——非損壞，terminal face 跳過分類）。
    """
    try:
        raw = path.read_text()
    except OSError as exc:
        return MetaError("metadata-unreadable", str(exc))
    try:
        meta = json.loads(raw)
    except json.JSONDecodeError as exc:
        return MetaError("metadata-corrupt", str(exc))
    if not isinstance(meta, dict):
        return MetaError("metadata-corrupt", "非 JSON object")
    for key in ("agentId", "status"):
        value = meta.get(key)
        if not isinstance(value, str) or not value:
            return MetaError("metadata-corrupt", f"缺必要欄位：{key}")
    created = meta.get("createdAt")
    if not isinstance(created, str) or not created:
        if meta["status"] == "running":
            return MetaError("metadata-corrupt", "缺必要欄位：createdAt（running 判定軸）")
    elif _parse_iso(created) is None and meta["status"] == "running":
        return MetaError("metadata-corrupt", f"createdAt 不可解析：{created}")
    return meta


# ---------------------------------------------------------------------------
# 唯讀 stat 面
# ---------------------------------------------------------------------------


def artifacts_dir_for(artifacts_root: Path, agent_id: str) -> Path:
    """artifacts 心跳面路徑（真機實證：sess_subagent_<agentId>）."""
    return artifacts_root / (SUBAGENT_DIR_PREFIX + agent_id)


def output_file_for(agent_dir: Path) -> Path:
    """output.txt fallback 路徑（metadata 缺 outputFile 欄時——同 dir 慣例）."""
    return agent_dir / OUTPUT_BASENAME


@dataclass(frozen=True)
class FaceSnapshot:
    """心跳面＋產物面的唯讀 stat 快照（檔案 stat 失敗＝清除競速，跳過該檔）."""

    artifacts_files: int = 0
    newest_activity: datetime | None = None  # artifacts 最新檔與 output.txt 取 max
    output_path: Path | None = None
    output_size: int | None = None
    output_mtime: datetime | None = None


def face_snapshot(artifacts_dir: Path, output_file: Path | None) -> FaceSnapshot:
    """唯讀 stat：artifacts 檔數＋最新活動（含 output.txt 寫入）＋output.txt 面位."""
    newest: datetime | None = None
    count = 0
    if artifacts_dir.is_dir():
        for p in artifacts_dir.iterdir():
            try:
                if not p.is_file():
                    continue
                st = p.stat()
            except OSError:
                continue  # 列舉後消失＝清理競速——可選面不 fail
            count += 1
            mtime = datetime.fromtimestamp(st.st_mtime, tz=UTC)
            if newest is None or mtime > newest:
                newest = mtime
    out_path: Path | None = None
    out_size: int | None = None
    out_mtime: datetime | None = None
    if output_file is not None:
        try:
            if output_file.is_file():
                st = output_file.stat()
                out_path = output_file
                out_size = st.st_size
                out_mtime = datetime.fromtimestamp(st.st_mtime, tz=UTC)
        except OSError:
            pass  # stat 撞清除＝缺席面（禁猜）
    if out_mtime is not None and (newest is None or out_mtime > newest):
        newest = out_mtime
    return FaceSnapshot(
        artifacts_files=count,
        newest_activity=newest,
        output_path=out_path,
        output_size=out_size,
        output_mtime=out_mtime,
    )


# ---------------------------------------------------------------------------
# 判定核心
# ---------------------------------------------------------------------------


def _evidence(
    meta: dict, face: FaceSnapshot, now: datetime, age_min: float
) -> dict:
    def age_of(ts: datetime | None) -> float | None:
        if ts is None:
            return None
        return round(max(0.0, (now - ts).total_seconds() / 60.0), 1)

    return {
        "ageMin": round(age_min, 1),
        "artifactsFiles": face.artifacts_files,
        "newestArtifactAgeMin": age_of(face.newest_activity),
        "outputPath": str(face.output_path) if face.output_path else None,
        "outputSize": face.output_size,
        "outputMtimeAgeMin": age_of(face.output_mtime),
    }


def classify_running_agent(
    meta: dict,
    face: FaceSnapshot,
    now: datetime,
    *,
    stillbirth_age_min: float = STILLBIRTH_AGE_MIN_DEFAULT,
    interrupted_frozen_min: float = INTERRUPTED_FROZEN_MIN_DEFAULT,
) -> tuple[str | None, dict]:
    """三簽章判定（caller 保證 status=running；否則 caller 自行跳過）.

    回 (alert_level | None, evidence)。None＝無事件（running-fresh 或時鐘
    回撥禁判）。優先序：COMPLETION_SUSPECTED（產物在場＝可回收）＞
    START_MISSING（type A）＞ SILENCE（中斷氣）。
    """
    created = _parse_iso(meta["createdAt"])
    if created is None:  # read_metadata 已擋——防禦面
        return None, {"metadataCorrupt": "createdAt unparseable"}
    age_min = (now - created).total_seconds() / 60.0
    ev = _evidence(meta, face, now, age_min)
    if age_min < 0:
        # 時鐘回撥（createdAt 在未來）＝禁判——禁誤報
        ev["clockAnomaly"] = True
        return None, ev
    # 型 B：output.txt 存在 → 即報（收尾寫一次；mtime 早於 createdAt 的
    # 野外異常不改存在性判準——evidence 帶雙時間戳供人裁）
    if face.output_path is not None:
        return ALERT_COMPLETION_SUSPECTED, ev
    # 型 A：artifacts 缺/空 ∧ age>60min
    if face.artifacts_files == 0 and age_min > stillbirth_age_min:
        return ALERT_START_MISSING, ev
    # 中斷氣：最新活動凍結>180min
    if face.newest_activity is not None:
        frozen_min = (now - face.newest_activity).total_seconds() / 60.0
        if frozen_min > interrupted_frozen_min:
            return ALERT_SILENCE, ev
    return None, ev


def start_evidence_present(face: FaceSnapshot, *, exec_file_count: int = 0) -> bool:
    """開工證據（waiter START_MISSING 驗活面）：artifacts 或 exec 任一面有檔，
    或 output.txt 在場（產物在場＝工作已發生——completion face 擁有其判讀，
    START_MISSING 不得重複旗標）.

    exec 目錄存在≠證據（type A 雙胞胎 exec 目錄在場零檔）——只認檔數。
    """
    return (
        face.artifacts_files > 0 or exec_file_count > 0 or face.output_path is not None
    )


def completion_suspected(
    meta: dict,
    face: FaceSnapshot,
    now: datetime,
    *,
    quiesce_min: float = COMPLETION_QUIESCE_MIN_DEFAULT,
) -> tuple[bool, dict]:
    """waiter 面 COMPLETION_SUSPECTED 三條件之二（running 由 caller 保證）：
    可信產物（output.txt）＋活動靜止 ≥quiesce_min。回 (是否成立, evidence)——
    只提醒 collection owner，禁自動宣告完成。"""
    created = _parse_iso(meta["createdAt"])
    age_min = (
        (now - created).total_seconds() / 60.0 if created is not None else -1.0
    )
    ev = _evidence(meta, face, now, age_min)
    ev["quiesceThresholdMin"] = quiesce_min
    if face.output_path is None:
        return False, ev
    if face.newest_activity is None:
        return False, ev
    quiesced = (now - face.newest_activity).total_seconds() / 60.0
    ev["quiesceMin"] = round(quiesced, 1)
    return quiesced >= quiesce_min, ev


# ---------------------------------------------------------------------------
# 全庫掃描（sweeper 消費面——唯讀；事件台帳）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ZombieEvent:
    """結構化事件台帳列——attempt_id+alert_type 去重鍵隨事件輸出（sweeper
    唯讀，去重由消費端執行）."""

    agent_id: str
    parent_session_id: str
    attempt_id: str
    alert_type: str
    dedup_key: str
    created_at: str | None
    age_min: float | None
    metadata_path: str
    evidence: dict
    cwd: str | None = None
    profile_id: str | None = None
    description: str | None = None
    detected_at: str = ""

    def to_dict(self) -> dict:
        return {
            "agentId": self.agent_id,
            "parentSessionId": self.parent_session_id,
            "attemptId": self.attempt_id,
            "alertType": self.alert_type,
            "dedupKey": self.dedup_key,
            "createdAt": self.created_at,
            "ageMin": self.age_min,
            "metadataPath": self.metadata_path,
            "cwd": self.cwd,
            "profileId": self.profile_id,
            "description": self.description,
            "detectedAt": self.detected_at,
            "evidence": self.evidence,
        }


def iter_agent_metadata(agents_root: Path) -> Iterator[Path]:
    """全庫 metadata 列舉（agents/sess_<parent>/<agentId>/metadata.json）."""
    yield from sorted(agents_root.glob("sess_*/agent_*/metadata.json"))


def scan_zcode_agents(
    agents_root: Path,
    artifacts_root: Path,
    now: datetime,
    *,
    stillbirth_age_min: float = STILLBIRTH_AGE_MIN_DEFAULT,
    interrupted_frozen_min: float = INTERRUPTED_FROZEN_MIN_DEFAULT,
) -> dict:
    """掃全庫 metadata 套三簽章——回 {events: [ZombieEvent], coverage: {...}}.

    UNKNOWN（JSON 損壞等）＝fail-loud 事件列報——禁自動結案（消費端禁把它
    當 resolved）；terminal／terminal_other 不出事件（coverage 可見）；
    running 無事件＝running_fresh；時鐘回撥＝clock_anomaly（禁判不誤報）。
    """
    events: list[ZombieEvent] = []
    cov = {
        "discovered": 0,
        "running": 0,
        "terminal": 0,
        "terminal_other": 0,
        "running_fresh": 0,
        "clock_anomaly": 0,
    }
    detected = now.isoformat(timespec="seconds")
    for path in iter_agent_metadata(agents_root):
        cov["discovered"] += 1
        meta_or_err = read_metadata(path)
        if isinstance(meta_or_err, MetaError):
            # UNKNOWN：agentId 欄不可信——attempt_id＝metadata 路徑（唯一可
            # 機驗身份），dedup 不變式（dedup_key＝attempt_id+alert_type）恆成立
            events.append(
                ZombieEvent(
                    agent_id=path.parent.name,
                    parent_session_id=path.parent.parent.name,
                    attempt_id=str(path),
                    alert_type=ALERT_UNKNOWN,
                    dedup_key=dedup_key(str(path), ALERT_UNKNOWN),
                    created_at=None,
                    age_min=None,
                    metadata_path=str(path),
                    evidence={"reason": meta_or_err.reason, "detail": meta_or_err.detail},
                    detected_at=detected,
                )
            )
            continue
        meta = meta_or_err
        status = meta["status"]
        if status == "running":
            cov["running"] += 1
        elif status in TERMINAL_STATUSES:
            cov["terminal"] += 1
            continue
        else:
            cov["terminal_other"] += 1
            continue
        output_raw = meta.get("outputFile")
        output_file = (
            Path(output_raw)
            if isinstance(output_raw, str) and output_raw
            else output_file_for(path.parent)
        )
        face = face_snapshot(
            artifacts_dir_for(artifacts_root, meta["agentId"]), output_file
        )
        level, ev = classify_running_agent(
            meta,
            face,
            now,
            stillbirth_age_min=stillbirth_age_min,
            interrupted_frozen_min=interrupted_frozen_min,
        )
        if ev.get("clockAnomaly"):
            cov["clock_anomaly"] += 1
            continue
        if level is None:
            cov["running_fresh"] += 1
            continue
        events.append(
            ZombieEvent(
                agent_id=meta["agentId"],
                parent_session_id=str(
                    meta.get("parentSessionId") or path.parent.parent.name
                ),
                attempt_id=meta["agentId"],
                alert_type=level,
                dedup_key=dedup_key(meta["agentId"], level),
                created_at=meta["createdAt"],
                age_min=ev.get("ageMin"),
                metadata_path=str(path),
                evidence=ev,
                cwd=meta.get("cwd") if isinstance(meta.get("cwd"), str) else None,
                profile_id=(
                    meta.get("profileId")
                    if isinstance(meta.get("profileId"), str)
                    else None
                ),
                description=(
                    meta.get("description")
                    if isinstance(meta.get("description"), str)
                    else None
                ),
                detected_at=detected,
            )
        )
    return {"events": events, "coverage": cov}
