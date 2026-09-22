#!/usr/bin/env python
"""compact checkpoint 機制件——格式驗證＋restore-proven＋cleanup guard（AIR-155）。

三件職責（卡 AC#2/#3）：
1. checkpoint 格式驗證——「四問可答」機械判準（目標／已完成／下一步／懸掛動作），
   壞檔 fail-loud（CheckpointError，禁靜默續行）。
2. restore-proven 判準——restore 驗證通過才發 proven receipt；receipt 綁
   checkpoint 檔案內容 sha256 與路徑，checkpoint 事後被換即失效。
3. cleanup guard——restore 未 proven 時擋 cleanup（CleanupBlockedError）；
   proven 後放行。

欄位相容映射（唯讀對齊 skills/_common/task-recovery.md「寫入端」必要欄位表，
定義源禁改；本表只宣稱映射不重定義）：

| checkpoint 欄位      | task-recovery 欄位                     | 必要 |
|----------------------|----------------------------------------|------|
| objective            | 目標與成功條件                          | ✓    |
| completed            | 現行階段（做到哪、哪些已驗）            | ✓    |
| next_action          | 下一個可執行 action                     | ✓    |
| pending              | 懸掛動作／背景 job／open findings       | ✓    |
| decisions            | 已決策理由及排除方案                    |      |
| evidence             | 已驗/未驗證據指針                       |      |
| read_set             | read-set 與未恢復範圍                   |      |
| durable_owner        | 落點優先序（EP/journal 指針）           |      |
| scope/cwd/baseline   | scope/cwd/baseline＋本弧 dirty          |      |
| authorization        | 授權來源與範圍指針                      |      |

四問判準是「可答」非「有進度」：completed/pending 允許空 list（弧起點的
合法回答），objective/next_action 須非空白字串。額外欄位不拒絕（前向相容）。

消費形態：函式 API（restore hook、skill 段與後續 trigger 接線消費）；約定落點
由 checkpoint_paths 給出——checkpoint 與 proven 同住
<cwd>/.agent-tmp/compact-checkpoints/<session_id>/ 成對放置（AIR-155 segment 2
起為單一源；caller 自帶落點者仍可指定路徑）。
"""

import datetime
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "compact-checkpoint/1"
PROVEN_SCHEMA = "compact-restore-proven/1"

# 約定落點（checkpoint_paths 單一源）——hook／skill fallback／寫入端共用
CHECKPOINTS_SUBDIR = "compact-checkpoints"
CHECKPOINT_FILENAME = "checkpoint.json"
PROVEN_FILENAME = "restore-proven.json"

_SESSION_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")

# 四問欄位：字串題（須非空白）與清單題（須為 list，可空）
STRING_FIELDS = ("objective", "next_action")
LIST_FIELDS = ("completed", "pending")


class CheckpointError(Exception):
    """checkpoint/proven 契約錯（缺檔、壞 JSON、缺欄、型別錯）——fail loud。"""


class CleanupBlockedError(CheckpointError):
    """restore 未 proven 時的 cleanup 擋行——恢復證明前禁清 recovery artifact。"""


@dataclass(frozen=True)
class Checkpoint:
    """四問的已驗答案（validate_checkpoint 的回傳型別）。"""

    objective: str
    completed: list[Any]  # Any＝JSON 邊界（條目可為字串或結構化值）
    next_action: str
    pending: list[Any]  # 同上


def sanitize_session_id(session_id: str) -> str:
    """session id → 單一安全路徑元件；非 [A-Za-z0-9._-] 一律換 _，危險值換佔位。"""
    cleaned = _SESSION_UNSAFE.sub("_", session_id)
    return cleaned if cleaned not in ("", ".", "..") else "_"


def checkpoint_paths(cwd: Path, session_id: str) -> tuple[Path, Path]:
    """checkpoint 與 proven 的約定落點（單一源，禁各處手拼路徑）。

    `<cwd>/.agent-tmp/compact-checkpoints/<sanitize(session_id)>/` 下成對放置
    checkpoint.json＋restore-proven.json（cleanup guard 同目錄同擋）。消費者：
    hooks/compact-restore-inject.py（restore 注入）、compact-prep skill
    （寫入端與 fallback 恢復）。
    """
    directory = (
        Path(cwd) / ".agent-tmp" / CHECKPOINTS_SUBDIR / sanitize_session_id(session_id)
    )
    return directory / CHECKPOINT_FILENAME, directory / PROVEN_FILENAME


def load_checkpoint(path: Path) -> dict[str, Any]:
    """讀檔＋JSON 解析＋schema 錨定；任何契約違反 raise CheckpointError。"""
    if not path.exists():
        raise CheckpointError(f"checkpoint not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CheckpointError(f"bad json in checkpoint {path}: {e}") from e
    if not isinstance(data, dict):
        raise CheckpointError(
            f"checkpoint must be a JSON object, got {type(data).__name__}: {path}"
        )
    if data.get("schema") != SCHEMA:
        raise CheckpointError(
            f"unsupported checkpoint schema: {data.get('schema')!r} (expect {SCHEMA!r})"
        )
    return data


def validate_checkpoint(data: dict[str, Any]) -> Checkpoint:
    """四問可答機械判準——一次收集全部違反後 raise（非逐欄中斷）。"""
    violations: list[str] = []
    for field in STRING_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            violations.append(f"{field} must be a non-empty string, got {value!r}")
    for field in LIST_FIELDS:
        value = data.get(field)
        if not isinstance(value, list):
            violations.append(f"{field} must be a list, got {type(value).__name__}")
    if violations:
        raise CheckpointError(
            "checkpoint failed four-question criterion (" + "; ".join(violations) + ")"
        )
    return Checkpoint(
        objective=data["objective"],
        completed=data["completed"],
        next_action=data["next_action"],
        pending=data["pending"],
    )


def _checkpoint_digest(checkpoint_path: Path) -> str:
    """proven 綁定鍵——checkpoint 檔案 bytes 的 sha256（非路徑非語義）。"""
    return hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()


def write_restore_proven(
    proven_path: Path,
    checkpoint_path: Path,
    *,
    verified_by: str = "",
    notes: str = "",
) -> Path:
    """restore 驗證通過後發 proven receipt（原子寫）。

    前置：checkpoint 必須先通過讀檔＋schema＋四問驗證——驗不過不發 proven
    （raise，且不留下半套 receipt）。receipt 記 checkpoint 絕對路徑＋內容
    sha256；verify_restore_proven 以兩者判 proven 是否仍有效。
    """
    checkpoint_path = checkpoint_path.resolve()
    validate_checkpoint(load_checkpoint(checkpoint_path))  # 驗不過即 raise
    proven_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": PROVEN_SCHEMA,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _checkpoint_digest(checkpoint_path),
        "verified_at": datetime.datetime.now()
        .astimezone()
        .isoformat(timespec="seconds"),
        "verified_by": verified_by,
        "notes": notes,
    }
    tmp = proven_path.with_name(proven_path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, proven_path)  # 原子換入——中斷不留半套 receipt
    return proven_path


def verify_restore_proven(
    proven_path: Path, checkpoint_path: Path
) -> tuple[bool, list[str]]:
    """核對 proven receipt 是否仍有效。回傳 (proven?, 失效原因)。

    缺 receipt＝未 proven（False，常態非錯）；receipt 壞 JSON／schema 錯＝
    raise（fail loud——cleanup guard 呼叫端因此被擋且看見原因）。proven 綁
    checkpoint 路徑＋bytes hash：任一不符即 False；checkpoint 現值重驗四問。
    """
    checkpoint_path = checkpoint_path.resolve()
    if not proven_path.exists():
        return False, ["proven_receipt_missing"]
    try:
        proven = json.loads(proven_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise CheckpointError(f"bad json in proven receipt {proven_path}: {e}") from e
    if not isinstance(proven, dict) or proven.get("schema") != PROVEN_SCHEMA:
        found = (
            proven.get("schema") if isinstance(proven, dict) else type(proven).__name__
        )
        raise CheckpointError(
            f"unsupported proven schema: {found!r} (expect {PROVEN_SCHEMA!r})"
        )

    failed: list[str] = []
    if proven.get("checkpoint_path") != str(checkpoint_path):
        failed.append("checkpoint_path_mismatch")
    if not checkpoint_path.exists():
        failed.append("checkpoint_missing")
    else:
        if proven.get("checkpoint_sha256") != _checkpoint_digest(checkpoint_path):
            failed.append("checkpoint_hash_mismatch")
        else:
            # hash 相符仍重驗四問——防禦 proven 被外部手段偽造於壞 checkpoint 上
            try:
                validate_checkpoint(load_checkpoint(checkpoint_path))
            except CheckpointError as e:
                failed.append(f"checkpoint_invalid({e})")
    return (not failed), failed


def is_restore_proven(proven_path: Path, checkpoint_path: Path) -> bool:
    """proven 謂詞；receipt 損壞等契約錯沿 verify_restore_proven raise。"""
    proven, _ = verify_restore_proven(proven_path, checkpoint_path)
    return proven


def assert_cleanup_allowed(checkpoint_path: Path, proven_path: Path) -> None:
    """cleanup guard——未 proven 時 raise CleanupBlockedError 擋 cleanup。

    數據完整性優先：恢復證明前禁清 recovery artifact（checkpoint＋proven）。
    放行＝靜默返回（proven 且綁定仍有效）。
    """
    proven, reasons = verify_restore_proven(proven_path, checkpoint_path)
    if not proven:
        raise CleanupBlockedError(
            f"cleanup blocked: restore not proven (reasons: {', '.join(reasons)}); "
            f"complete restore verification before removing recovery artifacts "
            f"checkpoint={checkpoint_path} proven={proven_path}"
        )
