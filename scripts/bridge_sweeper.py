#!/usr/bin/env python3
"""bridge_ledger_sweeper — prompt 邊界收線 backstop 核心（AIR-267）。

一句話：SessionStart／UserPromptSubmit 邊界掃 `bridge runs ⋈ liveness.jsonl`，
偵測「孤兒 running（無活 waiter）」與「terminal completed 無 collected 逾齡」
兩態——值變化才出一行 advisory；處置（arm/show/收線）恆歸 session LLM。

核心不變量（EP ai-analysis/_tasks/10-07-bridge-sweeper/ep.md）：
- invariant 1 提醒面非處置面：只讀（runs 唯讀 face＋liveness 台帳唯讀）——
  絕不 arm/stop/寫 liveness/寫 ledger。
- invariant 2 機械真相源＝liveness 台帤（waiter 自有；本模組只讀）：在場判據
  ＝armed−collected 配對＋heartbeat 新鮮度（default 30 分鐘，可調——對齊
  waiter HEARTBEAT_STALE_THRESHOLD，J-4）——
  禁進程掃描判在場（跨 session false-covered，tri 最大風險項）。
- invariant 3 語義分層：只報機械層——措辭恆「可能未收」；「session 層驗收
  已完成」是另一層，本模組零宣稱（一次 show 不等於真正收線）。
- invariant 4 fail-soft 恆安靜：face/台帤任何失敗＝stderr 註記＋零 stdout
  ＋exit 0——絕不擋 prompt、絕不轟炸。
- owner 分工凍結：sweeper=prompt 邊界提醒；watcher_pairing_nag=Stop 配對；
  liveness 台帤=waiter 自有。
- out of scope：reconcile 變異（waiter T7 擁有）、「worker 活著 ledger 無行」
  （無可靠 process→job identity——只會假警報）、bridge 原生 consume 標記面。

偵測規則（每輪掃描；值變化才出聲——EP 規則表）：
- R1 孤兒 running：running 行 且 該 jobId 無 armed 事件、或 armed 但
  heartbeat 逾新鮮度窗（default 30 分鐘，可調）
  → `[bridge-sweeper] running job <id> 無活 waiter——恢復 playbook：arm waiter`
  running 行卻帶 collected＝ledger staleness（reconcile 面）——不提醒
  （watcher_pairing_nag 同款不誤發裁定）。
- R2 terminal 未收：terminal(completed) 行 且 無 collected 事件 且 終態
  逾齡（default 30 分鐘）——前提＝liveness 有 armed 痕跡（真孤兒類）；
  無痕跡（pre-liveness 時代/手動收線）不可判安靜（J-2）
  → `[bridge-sweeper] <N> 個 terminal job 可能未收（<ids 前 3>）——收線：bridge_show`
  terminal 非 completed（failed-* 等）不提醒——失敗態處置是 dispatch 語義
  非收線語義（v1 收窄；known limitation 記 bridge-dispatch skill）。
- 乾淨＝零 stdout。
- liveness 台帤缺席（新機器/清過 .agent-tmp）＝R2 退化不可判——只跑 R1
  （runs 自身可判）；stderr 註記不轟炸。
- 時間戳無可計齊（naive/壞形）＝非 staleness 不報（bridge producer canonical
  ——no ageable data is never reported；提醒面 fail-safe 方向＝安靜）。

節流與安靜（tri Q3 收斂；先例＝duty_mailbox_monitor）：
- SessionStart：全掃（無節流、無 signature 壓制——session 回場提醒一次）。
- UserPromptSubmit：90s 節流窗（state 記 last_scan_at；窗內＝零查詢零輸出）
  ＋anomaly signature 去重（R1/R2 **id 全集**結構簽章（sorted＋json+sha256
  ——J-6）==baseline→靜默；變化才出聲＋更新 baseline；異常消失→baseline
  歸零；R2 顯示層前 3 截斷不參與簽章——第四成員起交換照出聲）。
- cwd eligibility gate：cwd 在本 repo（script 所在 checkout，含卡 WT）或
  帶 liveness 台帤的 repo（bridge 派工發生在任何 repo）才跑；否則零查詢
  零輸出。
- state：`${XDG_STATE_HOME:-~/.local/state}/ai-guide/bridge-sweeper/
  <safe_session_id>.json`（0600 atomic；路徑可注入——測試 tmp）。

決策表（hook 運作面；stdout 皆協議 JSON 或空、exit 恆 0；唯一例外＝註冊
args 誤用 argparse exit 2——misconfig 歸註冊單一源修復）：

| 情境 | stdout | exit |
|---|---|---|
| 偵測命中且值變化（R1 每孤兒一行＋R2 聚合一行） | hookSpecificOutput | 0 |
| 乾淨／同 signature／節流窗內／gate 不過／缺 session_id | 空（零查詢） | 0 |
| face 失敗（binary 缺席／exit 非零／stdout 壞形） | 空＋stderr 註記 | 0 |
| liveness 台帤缺席 | 照跑（R1）＋stderr 註記 | 0 |
| stdin 壞 JSON／未知事件（hook 前導面） | 空（fail-soft） | 0 |

wt-close drain 面（AIR-267 S2；`drain` 子命令）：移除 WT 前歸檔
`<wt>/.delegate-bridge/jobs/`＋`<wt>/.agent-tmp/liveness.jsonl` 至
`~/.agents/bridge-ledger-archive/<wt-basename>-<YYYYMMDD-HHMMSS>/`
（0600、防碰撞時間戳；v1 無 TTL/GC——量測後再議）。drain 失敗＝exit 1
fail-loud（wt-close die 保現場）——證據隨 WT 移除即滅，靜默失敗不可接受；
與 hook 面的 fail-soft（提醒可丟）分層。

部署 runtime＝governance-resolved Python 3.12（hooks/AGENTS.md），另被
wt-close.sh 以系統 python3（3.9）調用 drain——全檔維持 Python 3.9 語法
相容（無 annotations union／無 match；duty_receive 家族同款）。

binary 解析（與 scripts/duty_receive.py `_resolve_binary` 同源解析紀律）：
env DELEGATE_BRIDGE_BIN → PATH `delegate-bridge` → plugin cache 版本最新
（禁手 pin 版化路徑）。runs 唯讀 face 以 subprocess 呼叫（cwd＝repo root
——ledger per-workspace 解析）。

測試形態：injectable runner（回 runs JSON）＋liveness 事件 list＋tmp state
dir——零真 bridge 呼叫（真場 smoke＝AC5，marshal 職責）。
"""

import argparse
import functools
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

HOOK_TAG = "bridge-sweeper"
SUPPORTED_BOUNDARIES = ("SessionStart", "UserPromptSubmit")

RUNNING = "running"
COMPLETED = "completed"

# R1 heartbeat 新鮮度窗（分鐘；可調）。J-4（tri Important 1）：對齊
# bridge_waiter HEARTBEAT_STALE_THRESHOLD_MIN=30——waiter 合法輪詢間距
# 可達 20m（動態 T 的 T_GROW_CAP），15m 窗會把 healthy long wait 誤判死
# 亡（scripts/bridge_waiter.py 卡死判準註解同據）。
HEARTBEAT_FRESH_WINDOW_MIN = 30.0
# R2 終態逾齡窗（分鐘；EP default 30）
TERMINAL_AGE_MIN = 30.0
# UserPromptSubmit 節流窗（秒；tri Q3 收斂 90s）
THROTTLE_WINDOW_S = 90.0

RUNNER_ENV = "DELEGATE_BRIDGE_BIN"
# J-7（tri MED）：內層 bridge subprocess timeout（秒）——8s＜host 註冊
# timeoutMs 10s（governance zcode 條目）：host 面先到前，內層逾時已轉
# SweeperFaceError 進 fail-soft catch——catch 必有機會跑（階梯順序保證）。
BRIDGE_RUNS_TIMEOUT_SECONDS = 8
PLUGIN_CACHE_BASE = "~/.zcode/cli/plugins/cache/delegate-market/delegate"
PLUGIN_BIN_PATTERNS = (
    os.path.join("*", "bin", "delegate-bridge"),
    os.path.join("*", "bin", "*", "delegate-bridge"),
)

# wt-close drain 歸檔面（AIR-267 S2）
ARCHIVE_DEFAULT_ROOT = os.path.join("~/.agents", "bridge-ledger-archive")
LEDGER_JOBS_REL = os.path.join(".delegate-bridge", "jobs")
LIVENESS_REL = os.path.join(".agent-tmp", "liveness.jsonl")

# liveness 台帤 schema liveness/1（waiter 自有；本模組只讀）——時間戳鍵全集
# （watcher_pairing_nag 同款鏡像；drift 由 tests regex/fixture 釘）
LIVENESS_TS_KEYS = ("ts", "armedAt", "collectedAt", "advisedAt", "rearmedAt")
# live heartbeat 面（J-5，tri Important 2）：算「waiter 近期在場」的活事件
# 時間戳鍵＝armed/heartbeat/rearmed 三鍵；advisory(advisedAt)/collected
# (collectedAt) 是完結類事件——不算活心跳（advisedAt 誤算＝把 waiter 的
# 卡死提醒當成在場證據→誤安靜）。全集常數保留作 schema 聲明。
LIVENESS_LIVE_TS_KEYS = ("ts", "armedAt", "rearmedAt")

_SAFE_SESSION_RE = re.compile(r"[^A-Za-z0-9._-]+")


class SweeperFaceError(RuntimeError):
    """bridge runs face 失敗（binary 缺席／exit 非零／stdout 壞形）。

    hook 面＝fail-soft 吸收（stderr＋零 stdout＋exit 0）；drain 面另由
    CLI 分層 fail-loud。"""


# ── binary 解析（duty_receive._resolve_binary 同源紀律：env→PATH→cache 版本最新）──


def _version_key(candidate):
    """plugin cache 候選路的版本排序鍵——版本＝`bin/` 前一目錄名（duty_receive
    同源語義，數值比較）。"""
    parts = os.path.normpath(candidate).split(os.sep)
    version = (
        parts[parts.index("bin") - 1] if "bin" in parts else parts[-1]
    )
    pieces = []
    for piece in version.split("."):
        if piece.isdigit():
            pieces.append((0, int(piece), ""))
        else:
            pieces.append((1, 0, piece))
    return tuple(pieces)


def _resolve_binary():
    env_bin = os.environ.get(RUNNER_ENV)
    if env_bin:
        return env_bin
    on_path = shutil.which("delegate-bridge")
    if on_path:
        return on_path
    base = os.path.expanduser(PLUGIN_CACHE_BASE)
    candidates = []
    for pattern in PLUGIN_BIN_PATTERNS:
        candidates.extend(glob.glob(os.path.join(base, pattern)))
    if not candidates:
        raise SweeperFaceError(
            "delegate-bridge binary 缺席（" + RUNNER_ENV
            + " / PATH / plugin cache 皆未命中）"
        )
    return max(candidates, key=_version_key)


def _default_runner(argv, cwd=None):
    """真實 bridge 呼叫（唯讀 face；無 shell）；cwd＝repo root（ledger
    per-workspace 解析）。非零 exit／逾時＝SweeperFaceError（hook 上層
    fail-soft；逾時階梯見 BRIDGE_RUNS_TIMEOUT_SECONDS 註解）。"""
    try:
        proc = subprocess.run(
            [_resolve_binary()] + list(argv),
            capture_output=True,
            text=True,
            timeout=BRIDGE_RUNS_TIMEOUT_SECONDS,
            check=False,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as exc:
        raise SweeperFaceError(
            f"bridge CLI timeout（>{BRIDGE_RUNS_TIMEOUT_SECONDS}s）"
        ) from exc
    if proc.returncode != 0:
        raise SweeperFaceError(
            f"bridge CLI exit {proc.returncode}：{proc.stderr.strip()[:200]}"
        )
    return proc.stdout


# ── 時間戳（bridge ISO 形；naive＝不可計齊——非 staleness 不報）─────────


def _iso_to_aware(value):
    """bridge/liveness timestamp（ISO，可帶 Z／offset）→ aware datetime；
    不可判讀／naive → None（不做時區假設——fail-safe 方向＝安靜）。"""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone()


def _system_now():
    return datetime.now().astimezone()


# ── eligibility＋repo 解析（AIR-233 模式＋帶台帤 repo 擴充）────────────


def script_repo_root():
    """本模組所在 repo 根（scripts/ 上一層）。測試 monkeypatch 此函式換鎖。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git_toplevel(cwd):
    """cwd 的 git toplevel；非 repo／失敗＝None（fail-closed）。"""
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return None


def _resolve_repo(cwd):
    """eligibility gate＋掃描 repo 解析 → repo root | None。

    None＝gate 不過（零查詢零輸出）：cwd 缺席／非字串／不在本 repo 且其
    repo 無 liveness 台帤。本 repo 分支無條件過（EP「cwd 在本 repo」）；
    他 repo 分支須 `<top>/.agent-tmp/liveness.jsonl` 在場（EP「或帶
    liveness 台帤的 repo」——bridge 派工發生在任何 repo，台帤在場＝掃描
    面成立；無台帤的外部 repo 不打 bridge face）。"""
    if not isinstance(cwd, str) or not cwd:
        return None
    root = script_repo_root()
    real = os.path.realpath(cwd)
    if real == root or real.startswith(root + os.sep):
        return _git_toplevel(real) or root
    top = _git_toplevel(real)
    if top and os.path.isfile(os.path.join(top, LIVENESS_REL)):
        return top
    return None


# ── liveness 台帤（唯讀；schema liveness/1——waiter 自有）───────────────


def load_liveness(path):
    """讀 liveness.jsonl → 事件 list；缺席／不可讀＝None（R2 退化不可判）。
    壞行跳過（AIR-152 損壞容錯語義）。"""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            events.append(rec)
    return events


def _liveness_index(events):
    """事件 list → per-jobId {armed, collected, latest_ts}。

    jobId 全等比對（禁子串——`job-a` 會誤配 `job-a-1`，watcher_pairing_nag
    152-C4 同款）；latest_ts＝該 job 活事件（heartbeat 新鮮度判準的基準）
    時間戳最大者——只認 live 鍵（armedAt/ts/rearmedAt：任一活事件都證明
    watcher 近期在場）；advisory/collected 完結事件不計（J-5）。"""
    index = {}
    for rec in events:
        if not isinstance(rec, dict):
            continue
        job_id = rec.get("jobId")
        if not (isinstance(job_id, str) and job_id):
            continue
        entry = index.setdefault(
            job_id, {"armed": False, "collected": False, "latest_ts": None}
        )
        event = rec.get("event")
        if event == "armed":
            entry["armed"] = True
        elif event == "collected":
            entry["collected"] = True
        for key in LIVENESS_LIVE_TS_KEYS:
            ts = _iso_to_aware(rec.get(key))
            if ts is not None and (
                entry["latest_ts"] is None or ts > entry["latest_ts"]
            ):
                entry["latest_ts"] = ts
    return index


# ── 掃描（純函式；face 失敗 raise——上層 fail-soft）─────────────────────


def _fetch_runs(runner):
    out = runner(["runs", "--json"])
    try:
        rows = json.loads(out)
    except ValueError as exc:
        raise SweeperFaceError(
            f"runs stdout 不可解析：{out[:120]!r}"
        ) from exc
    if not isinstance(rows, list):
        raise SweeperFaceError(f"runs stdout 非 JSON array：{out[:120]!r}")
    return rows


def _scan_ids(
    runner,
    liveness_events,
    now,
    heartbeat_fresh_min=HEARTBEAT_FRESH_WINDOW_MIN,
    terminal_age_min=TERMINAL_AGE_MIN,
):
    """runs（runner 回 JSON）⋈ liveness 事件（None＝台帤缺席）→ (r1, r2)。

    純函式回 id 集合（signature 與顯示的共同上游——集合語義先於截斷）；
    face 失敗 raise SweeperFaceError（hook 上層 fail-soft 吸收）。"""
    rows = _fetch_runs(runner)
    per_job = _liveness_index(liveness_events or [])
    r1 = []
    r2 = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        job_id = row.get("id")
        if not (isinstance(job_id, str) and job_id):
            continue
        status = row.get("status")
        if not isinstance(status, str):
            continue
        info = per_job.get(job_id)
        if status == RUNNING:
            if info is not None and info["collected"]:
                # running 行卻帶 collected＝ledger staleness（reconcile 變異
                # ＝waiter T7 擁有，EP out of scope）——不提醒
                continue
            if info is None or not info["armed"]:
                r1.append(job_id)  # 無 armed 事件（台帤缺席同形）
                continue
            latest = info["latest_ts"]
            if latest is None:
                continue  # 無可計齊＝非 staleness 不報（fail-safe 安靜）
            if not (
                (now - latest).total_seconds() <= heartbeat_fresh_min * 60
            ):
                r1.append(job_id)  # armed 但 heartbeat 逾新鮮度窗
        elif status == COMPLETED:
            if liveness_events is None:
                continue  # 台帤缺席——R2 退化不可判（只跑 R1）
            if info is None or not info["armed"]:
                # 無 armed 痕跡＝pre-liveness 時代行或無 waiter 的手動收線面
                # （AC5 真場 smoke 實證：777 行僅少數有 waiter 痕跡——全報
                # ＝578 行誤報洪水）。真孤兒類＝「有 armed 無 collected」；
                # 無痕跡不可判——fail-safe 安靜。
                continue
            if info["collected"]:
                continue  # armed−collected 配對完成
            term_ts = _iso_to_aware(row.get("timestamp"))
            if term_ts is None:
                continue
            if not ((now - term_ts).total_seconds() <= terminal_age_min * 60):
                r2.append(job_id)  # 終態逾齡且 armed 無 collected——可能未收
    return r1, r2


def _advisory_lines(r1, r2):
    """(r1, r2) id 集合 → advisory 行（顯示層：R2 前 3 截斷只在這裡——
    signature 對集合全集簽，截斷不影響去重判準；J-6）。"""
    lines = [
        f"[{HOOK_TAG}] running job {job} 無活 waiter"
        "——恢復 playbook：arm waiter"
        for job in r1
    ]
    if r2:
        shown = "、".join(r2[:3]) + ("…" if len(r2) > 3 else "")
        lines.append(
            f"[{HOOK_TAG}] {len(r2)} 個 terminal job 可能未收（{shown}）"
            "——收線：bridge_show"
        )
    return lines


def scan_once(
    runner,
    liveness_events,
    now,
    heartbeat_fresh_min=HEARTBEAT_FRESH_WINDOW_MIN,
    terminal_age_min=TERMINAL_AGE_MIN,
):
    """runs ⋈ liveness → advisories（CLI/smoke 面；EP 規則表措辭凍結）。

    乾淨＝[]；face 失敗 raise SweeperFaceError（hook 上層 fail-soft 吸收）。"""
    r1, r2 = _scan_ids(
        runner, liveness_events, now,
        heartbeat_fresh_min=heartbeat_fresh_min,
        terminal_age_min=terminal_age_min,
    )
    return _advisory_lines(r1, r2)


# ── per-session state（節流窗＋anomaly signature baseline；0600 atomic）──


def _state_base_dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(base, "ai-guide", "bridge-sweeper")


def state_path(session_id, base_dir=None):
    """state 檔路徑（per-session；base_dir 可注入——測試 fake state）。
    safe session id sanitizer 與 duty-receive 同源語義（鏡像——duty 家族
    hook 保持獨立低成本，不跨層 import）。"""
    safe = _SAFE_SESSION_RE.sub("_", session_id) or "unknown"
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, safe + ".json")


def load_sweeper_state(path):
    """讀 state → dict；缺檔/壞形＝冷啟動 {}（stderr 註記——session-local
    檔，重建後果＝該 session 重新 baseline，方向安全）。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        print(
            f"[{HOOK_TAG}] state 損壞——視同冷啟動重建"
            f"（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return {}
    return doc if isinstance(doc, dict) else {}


def save_state(path, doc):
    """atomic 寫（pid 後綴 tmp＋os.replace）＋0600（duty_receive 同源語義）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _signature(r1_ids, r2_ids):
    """anomaly 結構簽章（J-6，tri Important 3）。

    對 {"r1": sorted, "r2": sorted} id 全集做 json.dumps+sha256——對
    R2 顯示層前 3 截斷免疫（第四成員起交換＝簽章變→出聲）；sorted 對
    runs 順序免疫。空集合照簽＝baseline 歸零。"""
    payload = json.dumps(
        {"r1": sorted(r1_ids), "r2": sorted(r2_ids)},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── run_hook：eligibility→節流→掃描→signature 去重→輸出 ───────────────


def run_hook(
    boundary,
    cwd,
    session_id,
    runner=None,
    state_dir=None,
    liveness_path=None,
    now=None,
):
    """單一 prompt 邊界掃描 → (advisory 行 list, commit | None)。

    永不 raise、恒安靜方向（invariant 4）：任何失敗＝stderr 註記＋([], None)。
    commit＝state 推進 closure（last_scan_at＋signature baseline）——呼叫端
    在 stdout 寫出成功後才執行（advance-after-emit；寫失敗寧可下輪重掃）。
    SessionStart＝全掃（無節流無 signature 壓制）；UserPromptSubmit＝90s
    節流＋signature 去重。"""
    try:
        if boundary not in SUPPORTED_BOUNDARIES:
            return [], None
        if not (isinstance(session_id, str) and session_id):
            return [], None
        repo = _resolve_repo(cwd)
        if repo is None:
            return [], None  # gate 不過——零查詢零輸出
        now = now if now is not None else _system_now()
        sfile = state_path(session_id, state_dir)
        state = load_sweeper_state(sfile)
        if boundary == "UserPromptSubmit":
            last = _iso_to_aware(state.get("last_scan_at"))
            if last is not None and not (
                (now - last).total_seconds() >= THROTTLE_WINDOW_S
            ):
                return [], None  # 節流窗內——零查詢零輸出零推進
        lv_path = (
            liveness_path
            if liveness_path is not None
            else os.path.join(repo, LIVENESS_REL)
        )
        events = load_liveness(lv_path)
        if events is None:
            print(
                f"[{HOOK_TAG}] liveness 台帤缺席（{lv_path}）——R2 退化"
                "不可判，只跑 R1",
                file=sys.stderr,
            )
        run_fn = runner
        if run_fn is None:
            run_fn = functools.partial(_default_runner, cwd=repo)
        r1, r2 = _scan_ids(run_fn, events, now)
        lines = _advisory_lines(r1, r2)
        signature = _signature(r1, r2)
        speak = bool(lines) and (
            boundary == "SessionStart"
            or signature != state.get("signature")
        )
        new_state = {"last_scan_at": now.isoformat(), "signature": signature}

        def commit():
            save_state(sfile, new_state)

        return (lines if speak else []), commit
    except Exception as exc:  # fail-soft by design——絕不擋 prompt
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return [], None


# ── wt-close drain（AIR-267 S2）────────────────────────────────────────


def _drain_items(wt_path):
    """WT 內在場的 bridge 證據 → [(label, path)]（jobs/ 目錄＋liveness 檔）。"""
    items = []
    jobs = os.path.join(wt_path, LEDGER_JOBS_REL)
    if os.path.isdir(jobs):
        items.append(("jobs", jobs))
    liveness = os.path.join(wt_path, LIVENESS_REL)
    if os.path.isfile(liveness):
        items.append(("liveness.jsonl", liveness))
    return items


def archive_wt_bridge_evidence(wt_path, archive_root=None, now=None):
    """wt-close drain 段——歸檔 jobs/＋liveness.jsonl → 歸檔清單行 list。

    無證據＝[] 零動作（不建目錄）。歸檔：`<archive_root>/<wt-basename>-
    <YYYYMMDD-HHMMSS>/`（防碰撞——同秒撞名加序號）；檔案 0600、目錄 0700
    （archive_root 由 CLI 注入——測試 tmp，零真 ~/.agents 觸碰）。失敗
    raise（CLI 層 fail-loud——證據隨 WT 移除即滅，wt-close die 保現場）。"""
    items = _drain_items(wt_path)
    if not items:
        return []
    root = (
        archive_root if archive_root is not None
        else os.path.expanduser(ARCHIVE_DEFAULT_ROOT)
    )
    stamp = (
        now if now is not None else _system_now()
    ).strftime("%Y%m%d-%H%M%S")
    wt_name = os.path.basename(os.path.normpath(wt_path))
    base = os.path.join(root, f"{wt_name}-{stamp}")
    dest = base
    n = 1
    while os.path.exists(dest):
        dest = f"{base}-{n}"
        n += 1
    os.makedirs(dest)
    for label, src in items:
        target = os.path.join(dest, label)
        if os.path.isdir(src):
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    for dirpath, _dirnames, filenames in os.walk(dest):
        os.chmod(dirpath, 0o700)
        for filename in filenames:
            os.chmod(os.path.join(dirpath, filename), 0o600)
    labels = "、".join(label for label, _src in items)
    return [f"bridge 證據歸檔：{labels} → {dest}"]


# ── CLI 面（模組＋CLI；hook 前導＝hooks/bridge_ledger_sweeper.py）───────


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "bridge ledger sweeper（AIR-267；prompt 邊界收線 backstop——"
            "唯讀提醒面）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan_p = sub.add_parser(
        "scan",
        help="手動單輪掃描（AC5 真場 smoke 用；SessionStart 語義＝全掃）",
    )
    scan_p.add_argument(
        "--cwd", default=os.getcwd(), metavar="PATH",
        help="掃描錨點 cwd（預設當前目錄；repo 解析經 git toplevel）",
    )
    scan_p.add_argument(
        "--session-id", required=True, metavar="ID",
        help="per-session state 檔 key（CLI 無 stdin payload 須顯式）",
    )
    scan_p.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="state 目錄覆寫（預設 XDG state／~/.local/state）",
    )
    scan_p.add_argument(
        "--liveness-path", default=None, metavar="PATH",
        help="liveness 台帤路徑覆寫（預設 <repo>/.agent-tmp/liveness.jsonl）",
    )
    drain_p = sub.add_parser(
        "drain",
        help="wt-close drain 段（AIR-267 S2）：歸檔 jobs/＋liveness.jsonl",
    )
    drain_p.add_argument(
        "--wt", required=True, metavar="PATH", help="要歸檔的 WT 路徑",
    )
    drain_p.add_argument(
        "--archive-root", default=None, metavar="DIR",
        help="歸檔根目錄覆寫（預設 ~/.agents/bridge-ledger-archive）",
    )
    drain_p.add_argument(
        "--list-only", action="store_true",
        help="只報在場證據不歸檔（wt-close preflight 面——零變更）",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "scan":
        lines, commit = run_hook(
            "SessionStart",
            args.cwd,
            args.session_id,
            state_dir=args.state_dir,
            liveness_path=args.liveness_path,
        )
        for line in lines:
            print(line)  # scan 面：純文字行（真場 smoke 判讀）
        if commit is not None:
            try:
                commit()
            except Exception as exc:  # 寧重不漏——不擋
                print(
                    f"[{HOOK_TAG}] state 寫入失敗——下輪重掃（{exc!r}）",
                    file=sys.stderr,
                )
        return 0  # fail-soft 恆 0（面失敗＝stderr＋零 stdout）
    if args.command == "drain":
        if args.list_only:
            items = _drain_items(args.wt)
            if items:
                root = (
                    args.archive_root
                    if args.archive_root is not None
                    else os.path.expanduser(ARCHIVE_DEFAULT_ROOT)
                )
                labels = "、".join(label for label, _src in items)
                print(
                    f"bridge 證據在場：{labels}——full 收線時歸檔至 {root}"
                )
            return 0
        try:
            lines = archive_wt_bridge_evidence(
                args.wt, archive_root=args.archive_root
            )
        except Exception as exc:
            # fail-loud：證據保全優先（wt-close die 保現場）——與 hook 面
            # fail-soft 分層（提醒可丟、證據不可）
            print(f"[{HOOK_TAG}] drain 失敗（{exc!r}）", file=sys.stderr)
            return 1
        for line in lines:
            print(line)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
