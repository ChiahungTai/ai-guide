#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""watcher pairing nag（Stop hook）——bridge 派工×watcher 在場配對催告
（AIR-135 Q8 MVP-2；AIR-152。post-build-gate 形態：budget 2、fail-open、
只報新增未配對不報存量）。

判定（純機械，全中才攔）：
  1. 本 session 的 bridge job——cwd repo `.delegate-bridge/jobs.json` 的
     row.sessionId == payload.session_id（sessionId 為 null 的 row 不歸屬
     任何 session、不催告——不誤報他 session 的存量；bridge 面 sessionId
     傳播補齊前此閘覆蓋有限，缺口如實）
  2. status == "running" 且 dispatch（row.timestamp）超寬限 10 分鐘
  3. 無 liveness 登記——`.agent-tmp/liveness.jsonl` 無該 jobId 的 JSON 記錄
     （armed／collected 皆算在場：waiter 只在 job 終態寫 collected——running
     row 卻有 collected＝ledger 過期，催告反而誤報；登記腿＝
     scripts/bridge_waiter.py arm/collect append，AIR-146 frozen spec amendment）

命中 → block-with-reason 一次（每 session 預算 2 次；每 jobId 至多一次；
超預算只記 audit 行不擋）。reason 內嵌填好 jobId 的 watcher arm 命令
（可 copy-paste）與 foreground-wait 免責出路。配對語義單一源＝AIR-135.7
（Dispatch⇄collection 配對；terminal≠complete）。

輸出契約：block＝stdout `{"decision":"block","reason":…}`（post-build-gate
同款 dialect，harness Stop block 面）；恆 exit 0——fail-open：任何內部錯誤
（payload 異形／ledger 讀取失敗／state 寫入失敗）＝放行＋stderr 診斷
（催告閘非安全閘，禁讓 turn 崩）。**無 bypass env**（break-glass＝human 停
registration）。
state／audit 落 `.agent-tmp/`（gitignored lifecycle 區，跨 session 自然分檔：
state per-session id、audit append-only jsonl）。
hook runtime python 3.9（機器 python3）——禁 3.10+ 語法。
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

GRACE_MINUTES = 10.0
BLOCK_BUDGET = 2
LEDGER_REL = os.path.join(".delegate-bridge", "jobs.json")
LIVENESS_REL = os.path.join(".agent-tmp", "liveness.jsonl")
STATE_REL = os.path.join(".agent-tmp", "watcher-pairing-nag.json")
AUDIT_REL = os.path.join(".agent-tmp", "watcher-pairing-nag-audit.jsonl")


def _iso_to_aware(value):
    """bridge timestamp（ISO，可帶 Z／offset）→ aware datetime；不可判讀回 None。"""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None  # naive 不做時區假設——不可計齊＝不催告（fail-safe 方向）
    return parsed.astimezone(timezone.utc)


def _git_toplevel(cwd):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return cwd


def _repo_file(repo, rel):
    return os.path.join(repo, rel)


def _liveness_has(job_id, liveness_path):
    """liveness.jsonl 逐行 JSON 解析、jobId 欄位全等比對（壞行跳過）。

    禁子串比對——`job-a` 子串會誤配 `job-a-1` 的登記（codex 152-C4）；
    登記腿 schema（AIR-152）＝`{"event":"armed|collected","jobId":…,…}`。
    """
    try:
        with open(liveness_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue  # 壞行跳過
                if isinstance(rec, dict) and rec.get("jobId") == job_id:
                    return True
    except OSError:
        return False
    return False


def _load_state(state_path):
    try:
        with open(state_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("sessions"), dict):
            return data
    except Exception:
        pass
    return {"sessions": {}}


def _save_state(state_path, state):
    """回 True＝已持久化、False＝寫入失敗——後者由 evaluate fail-open（不擋）。

    state 寫不入＝預算與去重無法承諾，此時攔截會變成無界限重複攔
    （codex 152-C5：契約明列 state 寫入失敗屬 fail-open 面）。
    """
    try:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False)
        return True
    except Exception as exc:
        print("[watcher_pairing_nag] state 寫入失敗（fail-open 不擋）: %r" % (exc,),
              file=sys.stderr)
        return False


def _audit(repo, payload):
    try:
        path = _repo_file(repo, AUDIT_REL)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "event": "budget-exhausted",
                "at": datetime.now(timezone.utc).isoformat(),
                "session": payload.get("session_id", ""),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _waiter_arm_line(job_id):
    """可 copy-paste 的 watcher arm 命令（waiter 與本 hook 同 repo——部署面一致）。"""
    waiter = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts", "bridge_waiter.py",
    )
    return "uv run python %s %s" % (waiter, job_id)


def evaluate(payload):
    """回 block reason 字串（應攔）或 None（放行）。內部錯誤由 caller fail-open 接住。"""
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return None
    cwd = payload.get("cwd")
    cwd = cwd if isinstance(cwd, str) and cwd else os.getcwd()
    repo = _git_toplevel(cwd)

    ledger_path = _repo_file(repo, LEDGER_REL)
    try:
        with open(ledger_path, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:
        return None  # 無 ledger／不可解析＝非 bridge repo 或缺損——放行
    if not isinstance(rows, list):
        return None

    now = datetime.now(timezone.utc)
    unpaired = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") != "running":
            continue
        if row.get("sessionId") != session_id:
            continue
        job_id = row.get("id")
        if not isinstance(job_id, str) or not job_id:
            continue
        if _liveness_has(job_id, _repo_file(repo, LIVENESS_REL)):
            continue  # watcher 在場（登記腿）
        dispatched = _iso_to_aware(row.get("timestamp"))
        if dispatched is None:
            continue
        if (now - dispatched).total_seconds() < GRACE_MINUTES * 60:
            continue  # 寬限窗內
        unpaired.append(job_id)
    if not unpaired:
        return None

    state_path = _repo_file(repo, STATE_REL)
    state = _load_state(state_path)
    entry = state["sessions"].setdefault(session_id, {"count": 0, "nagged": []})
    nagged = entry.setdefault("nagged", [])
    fresh = [j for j in unpaired if j not in nagged]  # 只報新增未配對，不報存量
    if not fresh:
        return None
    if entry.get("count", 0) >= BLOCK_BUDGET:
        _audit(repo, payload)  # 超預算：只記 audit 行不擋
        return None

    arm_lines = "\n".join("  " + _waiter_arm_line(j) for j in fresh)
    reason = (
        "bridge job 派工後無 watcher 在場（AIR-135.7 配對語義；超寬限 "
        "%d 分鐘且 .agent-tmp/liveness.jsonl 無登記）：%s\n"
        "離場前先掛起 watcher（派工去睡＝watcher 接手盯場），逐 job：\n%s\n"
        "或以 foreground wait 收完再走（免責：在回覆聲明前台等待理由與收法）。"
        % (int(GRACE_MINUTES), ", ".join(fresh), arm_lines)
    )
    entry["count"] = entry.get("count", 0) + 1
    nagged.extend(fresh)
    if not _save_state(state_path, state):
        return None  # state 寫不入＝預算/去重無法承諾——fail-open 不擋（152-C5）
    return reason


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    try:
        reason = evaluate(payload)
    except Exception as exc:  # fail-open：禁讓 turn 崩
        print("[watcher_pairing_nag] fail-open: %r" % (exc,), file=sys.stderr)
        reason = None
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
