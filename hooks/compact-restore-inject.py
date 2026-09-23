#!/usr/bin/env python3
"""compact restore 注入 hook（AIR-155 segment 2，ZCode UserPromptSubmit sync）。

職責：新 context 開口（compact 後首個 user prompt）時，若本 session 有未消費
的 compact checkpoint，注入 thin pointer——路徑＋sha256＋head/tail 預覽＋
「先讀檔再續任務」指令（禁全文進 context；codex spill 語義同構：接續材料以
檔案承載、context 只帶指針）。驗證/proven/cleanup 判準全部消費
scripts/compact_checkpoint.py——hook 注入與 skill fallback 走同一驗證。

compaction 閘（AC-B）：inject/corrupt 之前先過一道閘——gate_pass ⇔ zcode
session DB（~/.zcode/cli/db/db.sqlite）存在晚於 baseline 的 compaction part
記錄（baseline＝proven receipt verified_at 的 epoch ms；無 receipt＝0）。
持續責任制下 checkpoint 幾乎常駐，存在性本身不是注入理由——沒有「proven
之後又發生 compaction」就不注入（誤拿防護）。gate_pass=False 時已消費回
consumed、其餘回 none；DB 檔缺席／查詢任何異常 → 視同無記錄（fail-open
優先於 gate）。gate 與 checkpoint 內容判定正交：gate 過後才走下表分流。

決策表（evaluate；stdout 皆協議 JSON 或空）：

| 情境                                          | stdout            | stderr | exit |
|-----------------------------------------------|-------------------|--------|------|
| 無 checkpoint                                  | 空（靜默）         | 空     | 0    |
| gate 未過＋已 proven（綁定仍有效）              | 空（consumed 靜默）| 空     | 0    |
| gate 未過＋未 proven 或 receipt 壞              | 空（靜默）         | 空     | 0    |
| gate 過＋有未消費 checkpoint（四問驗證通過）     | thin pointer JSON | 空     | 0    |
| gate 過＋已 restore-proven（綁定仍有效）          | thin pointer JSON（re-restore：proven 後又 compaction，已恢復 context 被再壓） | 空     | 0    |
| gate 過＋checkpoint 損壞（驗證失敗）             | 損壞警示 JSON      | 診斷   | 0    |
| gate 過＋proven receipt 損壞（無法判定消費）     | thin pointer JSON | 診斷   | 0    |
| 任何其他錯誤（stdin 壞 JSON、機制載入失敗）      | 空                | 診斷   | 0    |

fail-open 契約：本 hook 絕不擋 user prompt——任何錯誤一律 stderr 診斷＋exit 0
＋不注入。checkpoint／proven receipt 損壞則是「對恢復端 fail-loud」：注入警示
指針而非靜默跳過（數據完整性優先——損壞比缺失更危險，靜默跳過＝恢復材料無聲
損失），對 harness 仍 fail-open。

消費即靜默：restore 端驗證通過後以 write_restore_proven 發 proven receipt
（綁 checkpoint 內容 sha256）；hook 見有效 proven 即不再注入。checkpoint 事後
再更新且 baseline 之後又有新 compaction → gate 過＋hash 漂移 → proven 失效 →
hook 重新注入；只有 hash 漂移（新工作未伴隨 compaction）時 gate 未過、維持
靜默（AC-B 誤拿防護，非缺陷）。

ZCode 協議（ref-docs/harness/zcode hooks.md）：stdin 一行 JSON（session_id、
cwd、hook_event_name）；UserPromptSubmit 不用 matcher、每次 user prompt 觸發；
stdout 只有去空白後以 { 開頭的合法 JSON 被協議解析，hookSpecificOutput.
additionalContext 注入 context；空 stdout＝成功無效果；輸出上限 32768 bytes
（根級 maxOutputBytes 預設）。repo 未註冊／無 checkpoint 的 repo 每次成本為
一次 stat——靜默零輸出。

部署 runtime 由 governance installer 解析 uv-managed Python 3.12（hooks/AGENTS.md）；
mixed-session／rollback 窗期仍維持 Python 3.9 語法相容，改動後兩面都驗。
"""

import datetime
import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

HOOK_TAG = "compact-restore-inject"
HEAD_TAIL_BYTES = 400  # thin pointer 預覽預算（head/tail 各此值，UTF-8 bytes）
OUTPUT_GUARD_BYTES = 30000  # 組裝後最終 guard（ZCode 上限 32768）
ZCODE_DB_PATH = os.path.expanduser("~/.zcode/cli/db/db.sqlite")

# zcode session DB 的 compaction part 最新時間戳（AC-B 指定查詢）——
# time_created 為 epoch 毫秒；json_extract 需 SQLite JSON1（缺即例外→fail-open）
_COMPACTION_MAX_SQL = (
    "SELECT max(p.time_created) FROM part p"
    " JOIN message m ON p.message_id = m.id"
    " WHERE m.session_id = ? AND json_extract(p.data, '$.type') = 'compaction'"
)

CCP = None  # scripts/compact_checkpoint.py（load_ccp lazy 載入後快照）


def load_ccp():
    """載入同 repo scripts/compact_checkpoint.py——驗證機制單一源，消費勿重寫。"""
    global CCP
    if CCP is None:
        path = Path(__file__).resolve().parents[1] / "scripts" / "compact_checkpoint.py"
        spec = importlib.util.spec_from_file_location("compact_checkpoint", path)
        if spec is None or spec.loader is None:
            raise ImportError("cannot build import spec for " + str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        CCP = module
    return CCP


def _max_compaction_ms(db_path, session_id):
    """zcode DB 內該 session 最新 compaction part 的 time_created（epoch ms）。

    無記錄回 None。唯讀開啟（mode=ro）——DB 缺席直接回 None、絕不副作用建
    檔；sqlite 異常不在此捕，由 evaluate 的 try/except 吸收（fail-open）。
    """
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        row = conn.execute(_COMPACTION_MAX_SQL, (session_id,)).fetchone()
    finally:
        conn.close()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def _proven_baseline_ms(proven_path):
    """compaction 閘的 baseline＝proven receipt verified_at 的 epoch ms。

    缺 receipt／壞 JSON／無 verified_at／解析失敗一律 0（從未 proven）。
    只取「最後一次 proven 發生在何時」當比較基準——綁定有效性（hash 比對）
    交給 gate 後的原分流判定。
    """
    try:
        data = json.loads(Path(proven_path).read_text(encoding="utf-8"))
        if CCP is not None and data.get("schema") != CCP.PROVEN_SCHEMA:
            return (
                0  # schema 錯的 receipt 不當 baseline（F4：與 JSON 壞同判 從未 proven）
            )
        verified_at = data["verified_at"]
        return int(datetime.datetime.fromisoformat(verified_at).timestamp() * 1000)
    except Exception:
        return 0


def evaluate(cwd, session_id, db_path=None, query_compaction=None):
    """決策核心（純函式，stdin 無關——測試直接呼叫）。

    回傳 (action, info)；action ∈ none / consumed / inject / corrupt。
    info 帶 checkpoint_path／proven_path／sha256（inject/corrupt/consumed 時），
    proven receipt 損壞時另帶 receipt_error。

    AC-B compaction 閘：inject/corrupt 之前先查 zcode DB——無「晚於 baseline
    （proven verified_at；無 receipt＝0）的 compaction part」即靜默（誤拿
    防護：checkpoint 幾乎常駐，存在性本身不是注入理由）。gate_pass=False 時
    已消費回 consumed、其餘回 none。db_path 預設 ZCODE_DB_PATH；
    query_compaction（db_path, session_id → epoch ms | None）可注入 stub。
    """
    ccp = load_ccp()
    checkpoint_path, proven_path = ccp.checkpoint_paths(Path(cwd), session_id)
    if not checkpoint_path.exists():
        return "none", {}
    info = {
        "checkpoint_path": str(checkpoint_path),
        "proven_path": str(proven_path),
        "sha256": ccp._checkpoint_digest(checkpoint_path),
    }
    query = query_compaction if query_compaction is not None else _max_compaction_ms
    db = db_path if db_path is not None else ZCODE_DB_PATH
    try:
        latest = query(db, session_id)
    except Exception:
        latest = None  # 查詢任何異常 → 視同無記錄（fail-open 優先於 gate）
    if latest is None or latest <= _proven_baseline_ms(proven_path):
        # 無晚於 baseline 的 compaction → 不注入；能證明已消費才回 consumed
        try:
            if ccp.is_restore_proven(proven_path, checkpoint_path):
                return "consumed", info
        except ccp.CheckpointError:
            pass
        return "none", {}
    try:
        ccp.validate_checkpoint(ccp.load_checkpoint(checkpoint_path))
    except ccp.CheckpointError as exc:
        # 損壞比缺失更危險——對恢復端 fail-loud（注入警示），對 harness fail-open
        return "corrupt", dict(info, error=str(exc))
    try:
        proven = ccp.is_restore_proven(proven_path, checkpoint_path)
    except ccp.CheckpointError as exc:
        # receipt 壞＝消費狀態無法判定；靜默＝未消費 checkpoint 可能無聲損失 → 照未消費注入
        return "inject", dict(info, receipt_error=str(exc))
    if proven:
        # F3（settlement review）：proven 綁定仍有效但 proven 之後又發生 compaction
        # ＝已恢復的 context 被再次壓縮 → 重新注入（re-restore），消費狀態
        # 「有效至下一次 compaction 為止」。靜默會讓恢復責任掉回人肉提醒。
        return "inject", dict(info, re_restore="proven predates latest compaction")
    return "inject", info


def _preview(raw: bytes) -> str:
    """head/tail 各 HEAD_TAIL_BYTES 的預覽；中段以「中略」標記（bytes 切再解碼）。"""
    if len(raw) <= HEAD_TAIL_BYTES * 2:
        return raw.decode("utf-8", errors="ignore")
    head = raw[:HEAD_TAIL_BYTES].decode("utf-8", errors="ignore")
    tail = raw[-HEAD_TAIL_BYTES:].decode("utf-8", errors="ignore")
    return head + "\n…(中略)…\n" + tail


def build_context(action, info):
    """thin pointer 本文；none/consumed 回空字串（＝零輸出靜默）。"""
    if action not in ("inject", "corrupt"):
        return ""
    lines = ["<" + HOOK_TAG + ">"]
    if action == "inject":
        raw = Path(info["checkpoint_path"]).read_bytes()
        lines.append(
            "偵測到本 session 的未消費 compact checkpoint（壓縮前 context 的持續外部化狀態）："
        )
        lines.append("- checkpoint: " + info["checkpoint_path"])
        lines.append("- sha256: " + info["sha256"])
        lines.append("- 內容 head/tail 預覽:")
        lines.append(_preview(raw))
        lines.append(
            "先讀上方檔案全文再續任務（本指針非內容本體，禁只憑預覽續行）；"
            "恢復順序照 task-recovery，驗證通過後以 scripts/compact_checkpoint.py "
            "write_restore_proven 發 proven——proven 後本 hook 自動靜默；"
            "驗證未過前禁清 checkpoint/proven（cleanup guard）。"
        )
        if "receipt_error" in info:
            lines.append(
                "- 注意: proven receipt 損壞（" + info["receipt_error"] + "）"
                "——消費狀態無法判定，照未消費處理。"
            )
    else:
        lines.append(
            "警告：本 session 的 compact checkpoint 存在但驗證失敗（損壞）——禁靜默續行："
        )
        lines.append("- checkpoint: " + info["checkpoint_path"])
        lines.append("- 驗證錯誤: " + info["error"])
        lines.append(
            "損壞的恢復材料比缺失更危險；先檢查該檔（load_checkpoint 詳因見 stderr）"
            "再決定修復或重建，處理前禁清該目錄。"
        )
    lines.append("</" + HOOK_TAG + ">")
    return "\n".join(lines)


def run(raw, db_path=None, query_compaction=None):
    """stdin 原文 → (exit_code, stdout payload)。永不 raise、exit 恆 0（fail-open）。

    db_path／query_compaction 透傳 evaluate（測試注入 stub 用，預設走實機 DB）。
    """
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            raise TypeError("stdin not a JSON object")
        session_id = str(payload.get("session_id", ""))
        cwd = str(payload.get("cwd", ""))
        if not session_id or not cwd:
            raise ValueError("stdin missing session_id/cwd")
        action, info = evaluate(
            Path(cwd),
            session_id,
            db_path=db_path,
            query_compaction=query_compaction,
        )
        if action == "consumed":
            return 0, ""  # 消費即靜默（零輸出，不擾 log）
        context = build_context(action, info)
        if not context:
            return 0, ""
        out = json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
        if len(out.encode("utf-8")) > OUTPUT_GUARD_BYTES:
            print(
                HOOK_TAG
                + ": 注入 "
                + str(len(out.encode("utf-8")))
                + " bytes 超上限，跳過",
                file=sys.stderr,
            )
            return 0, ""
        return 0, out
    except Exception as exc:  # fail-open by design——絕不擋 user prompt
        print(HOOK_TAG + ": fail-open（" + repr(exc) + "）", file=sys.stderr)
        return 0, ""


def main() -> int:
    code, out = run(sys.stdin.read())
    if out:
        sys.stdout.write(out)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
