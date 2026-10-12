#!/usr/bin/env python3
"""dutymail 值星收信處理器核心（AIR-254.3 S1——模組＋CLI；AIR-312 repo
身份制）。

職責：以明確 CLI 呼叫（AIR-312 起 SessionStart／UserPromptSubmit 自動
hook 已退役且入口 inert no-op——普通 once 消費面＝S2 inbox 子命令
（`inbox`／`show`／`pending-replies`／`mark-read`／`reply`，skills/
mail-handle 契約）；本 processor（`process`）保留作歷史相容、非 skill
新預設），
以 epoch-fenced holder 身分對 per-repo mailbox（alias＝repo basename，
如 ai-guide）執行一個完整收信週期——`holder` 面取權威 → `receive
prepare` 取 bounded 批次 → 逐封 triage → 全部處置完才 `receive ack`。
輸出＝digest 行＋surface 一行摘要（hook 層包成
hookSpecificOutput.additionalContext；CLI 層印純文字行；B′ AIR-258——
envelope 全文不注入 conversation，全文判讀面＝SC INBOX）。

核心不變量（EP invariant 對應）：
- ack 是唯一 cursor 前進邊，只在本批每一封都有 disposition 紀錄後
  下達——絕不 flush-ack（處置中斷＝ack 呼叫不到達；未完成批次以
  `--invalidate` 顯式作廢，信不動，下輪重 prepare，寧重不漏）。
- 自動處理 default-deny：`triage` 需 class×action 表（config）允許＋
  intent 機械驗證全過；三條代碼層底線 config 無法放寪——solicit 恆
  surface、未列 class 恆 surface、恆人工名單 class（handoff／patrol／
  work-order）恆 surface。auto 處理＝digest 吸收（計數行），
  輸出語義「例行已處理」，絕不宣稱 work accepted；AIR-287 bi 修復：
  digest 呈現完成（commit 起點）＝disposition ledger 推進邊界——
  auto→handled／surface→needs-human（單一源＝duty_disposition 模組
  docstring「處理推進」裁定；ack 是 transport cursor，不作推進前提）。
- holder 權威經 `holder bind` consent CAS 取得，絕不繞過；binding
  active（3.8.0 bound／3.7.0 live）在場＝不搶（換代正當路徑＝對方
  SessionEnd 釋放後 rebind；ZCode 無 SessionEnd 面——holder 可證已死
  ＝death-evidence takeover，`_holder_death_evidence`）；rebind CAS
  失敗＝HolderConflict（surface 衝突訊息、單次嘗試、不重試轟炸）。
  AIR-288：3.8.0 renew 面拔除（authority 無時鐘）——token 有效至被
  fence，fencing 交 prepare 既有 rebind 路徑；清潔關閉釋出面＝
  `release_holder`（codex/grok SessionEnd hook 接線）。
- holder state（bearer token）存 per-session 檔 0600、atomic 寫、
  路徑可注入（測試 fake state，不碰真 store）。
- 跨址 custody fence（AIR-312 repo 身份制）：process 只准消費呼叫端
  repo 自己的 address——canonical alias＝呼叫端 git common-dir 反推
  primary root 的 basename（linked WT／subdir／symlink 同一身份；非
  git／bare／git-dir 佈局無法判定＝ConfigError deny-all fail-closed）。
  requested address 須 exact-match canonical name；錯址在任何 consuming
  side effect 前拒絕：CLI 入口 arg 驗證 exit 2＋process_once bind 前
  核心閘（CustodyFenceError fail-closed——gate 不下沉 face wrapper，
  唯讀跨址診斷不受此閘）。AIR-311 per-caller consume TOML 已隨本卡
  退役——無授權檔、無 migration bypass（殘留 consume 檔不授予任何
  位址，載入面無視其存在）。
- v1 絕不主動送信：本檔不觸達 send／replies 面（回信＝outward，須
  逐次 AUTH，非本處理器範圍；授權面豁免與條件＝rules/
  outward-action-consent.md「卡級討論授權」節——AIR-308 deferred
  指針同步）。

dutymail typed contract（3.1.0 凍結）：每命令恰一個 JSON；成功＝
stdout `{"schemaVersion":1,"ok":true,"result":{...}}`；typed failure＝
stderr `{"schemaVersion":1,"ok":false,"error":{code,class,message,
retryable}}`＋空 stdout，exit class 2 usage／3 admission／4 storage／
5 fencing／6 wait-timeout。binary 解析順序：env DUTYMAIL_BIN →
PATH `dutymail` → zcode plugin cache → claude plugin cache（各 rung
取版本最新；禁手 pin 版化路徑）。全 miss＝`BinaryMissing` typed
raise——與 store 缺席（class 4 storage 合法軟 path）分流：hook 面
consecutive-miss sidecar 計數、達門檻 stderr advisory（exit 恆 0，
AIR-274 M1）；CLI 面 typed 訊息 exit 1（不再 traceback）。

測試形態：核心函式吃 injectable runner（`runner(argv) -> stdout`
str；typed failure 以 DutymailFaceError raise）——fake dutymail 回
固定 JSON，零真 store 往返（真往返＝S3，marshal 職責）。
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime

HOOK_TAG = "duty-receive"
DEFAULT_MAX_COUNT = 8  # bounded batch（EP：max-count 預設 8）
SURFACE_ID_LIMIT = 3  # surface 摘要行 envelope_id 列表上限（B′：全文面＝SC INBOX）
DUTYMAIL_TIMEOUT_SECONDS = 30
RUNNER_ENV = "DUTYMAIL_BIN"
# binary consecutive-miss advisory 門檻（AIR-274 M1）：hook 面連續 miss
# 達此數才 stderr advisory（未達靜默；binary 在場呼叫歸零——resolve
# 已過，含 face 失敗；唯 BinaryMissing 不歸零）。
MISS_ADVISORY_THRESHOLD = 3
PLUGIN_CACHE_BASE = "~/.zcode/cli/plugins/cache/delegate-market/delegate"
# 第四 rung（AIR-273）：CC 端 hooks 的 binary 存活不依賴 zcode cache——
# zcode cache 清掉時 fallback 到 claude plugin cache（形態同第三 rung）。
CLAUDE_PLUGIN_CACHE_BASE = (
    "~/.claude/plugins/cache/delegate-market/delegate"
)
PLUGIN_BIN_PATTERN = os.path.join(
    "*", "bin", "aarch64-apple-darwin", "dutymail"
)

# prepare/ack 撞上的 fencing 碼（class 5，3.8.0 現役面）——呼叫端集合。
# AIR-288（db-98 B 案 holder timer 拔除）：`lease-expired` 退役——3.8.0
# 原生不再發生（authority＝address＋epoch＋token＋binding active，無時
# 鐘），自呼叫端集合移除、凍結詞彙留 RETIRED_FENCING_CODES 供混版對照。
# 3.7.0 相容：lease 過期仍＝class 5 fencing，由 `_is_fencing`（按 class
# 路由）接入既有 rebind 路徑——不 renew 只會 lease 自然過期。
# DB-105 v5（AIR-299）：`holder-role-mismatch` 收錄（role tiering class
# 5）——語義＝章別接線錯誤（wiring error），**不是 recovery 觸發條件**：
# 見 WIRING_ERROR_CODES／`_is_fencing` 豁免（禁重綁/重試，fail-loud）。
FENCING_CODES = frozenset(
    {"stale-epoch", "holder-token-mismatch", "holder-role-mismatch"}
)
RETIRED_FENCING_CODES = frozenset({"lease-expired"})
# class 5 內的接線錯誤碼（DB-105 v5）——章別配置錯，恢復（rebind/重試）
# 無意義：`_is_fencing` 豁免、exception 原樣傳播交 per-address fail-soft。
WIRING_ERROR_CODES = frozenset({"holder-role-mismatch"})
# bind CAS 失敗碼（class 5，frozen）
CAS_CONFLICT_CODE = "epoch-conflict"
# 批次已死碼（cursor 未前進；信仍 pending）——清記錄落 fresh prepare
BATCH_DEAD_CODES = frozenset(
    {"batch-expired", "batch-fenced", "batch-invalidated",
     "batch-token-mismatch"}
)
BATCH_CONFLICT_CODE = "batch-conflict"
# receipt 類 idempotency 鍵（body machine-headers：辨識被回執的原工作）
IDEMPOTENCY_KEYS = ("task", "card")
VALID_INTENTS = frozenset({"inform", "solicit", "receipt"})
ALLOWED_AUTO_INTENTS = ("inform", "receipt")  # solicit 底線不可入表
# 恆人工名單（EP owner 裁決）：這些 class 絕不可 auto——工作分派面需要
# 人判讀；表列 action="auto" 即 ConfigError（比照 solicit 條款）
ALWAYS_SURFACE_CLASSES = frozenset({"handoff", "patrol", "work-order"})
ROW_KEYS = frozenset({"class", "auto_intent", "action"})

MINUTES_US = 60_000_000


# ── typed failure／配置錯誤／holder 衝突 ─────────────────────────────


class ConfigError(RuntimeError):
    """分診表（governance/dutymail-processor.toml）缺席或壞形——
    fail-loud exit 3（不靜默全 surface：配置錯誤要大聲）。"""


class CustodyFenceError(RuntimeError):
    """跨址 custody fence（AIR-312 repo 身份制）——requested address 非
    呼叫端 repo canonical alias（exact match 失敗）＝address 屬他 repo
    custody：holder 全序列（status/bind/prepare/ack）不得開始，禁消費
    （fail-closed）。canonical alias 單一源＝caller_repo_address（呼叫
    端 git common-dir 反推 primary root 的 basename）。CLI 入口 arg
    驗證 exit 2；process_once 起手（ensure_holder 前）是核心閘。"""


class DutymailFaceError(RuntimeError):
    """dutymail face typed failure（或 stdout 形狀漂移）。

    error_class＝CLI 凍結五類字串（usage/admission/storage/fencing/
    wait-timeout）；storage＝store 缺席／不相容（pre-migration 世界，
    hook 層 fail-soft 靜默）。
    """

    def __init__(self, code, error_class, message, retryable, exit_code):
        super().__init__(f"{code}({error_class}): {message}")
        self.code = code
        self.error_class = error_class
        self.message = message
        self.retryable = retryable
        self.exit_code = exit_code

    @property
    def is_storage(self):
        return self.error_class == "storage"


def _is_fencing(exc):
    """class 5 fencing 判定（AIR-288 雙版路由面）：按 CLI 凍結五類的
    `error_class` 路由、非 code 列舉——3.7.0 退役碼 `lease-expired`
    （混版窗口 binary 可能是 3.7.0，不 renew 只會 lease 自然過期）與
    3.8.0 現役碼（stale-epoch／holder-token-mismatch）同樣接入既有
    rebind 路徑。DB-105 v5 豁免（AIR-299）：`holder-role-mismatch`
    （wiring error——章別接線錯誤）雖屬 class 5 卻**不觸發 recovery**
    （rebind/重試對配置錯誤無意義），exception 原樣傳播交 per-address
    fail-soft。消費面限 prepare/ack 錯誤：`epoch-conflict`（同屬
    class 5）只在 bind CAS 面出現，由 `_bind_fresh` 攔下轉
    HolderConflict，不到這裡。"""
    return (
        exc.error_class == "fencing"
        and exc.code not in WIRING_ERROR_CODES
    )


class HolderConflict(RuntimeError):
    """holder 衝突——surface 訊息、單次嘗試、不重試轟炸（唯一
    consuming authority 裁決）。兩觸發：binding active 在場（另一
    session 持有消費權威——不搶，待對方釋放換代）；rebind consent CAS
    失敗（status 與 bind 之間 race window 内他方先 bind——epoch 已
    前進）。"""


class BinaryMissing(RuntimeError):
    """dutymail binary 解析全 miss（DUTYMAIL_BIN／PATH／zcode・claude
    plugin cache 皆缺席）——環境壞，有別於 store 缺席的合法軟 path
    （DutymailFaceError class 4）。hook 面＝consecutive-miss sidecar
    計數、達門檻 stderr advisory（exit 恆 0——AIR-274 M1 消音缺口
    服務）；CLI 面＝typed 訊息 exit 1（不再 generic traceback）。"""


# ── binary 解析（DUTYMAIL_BIN → PATH → zcode cache → claude cache 版本最新）──


def _version_key(candidate):
    """plugin cache 候選路的版本排序鍵——版本＝`bin/` 前一目錄名，
    數值比較（3.1.0 > 2.12.0 > 10.0.0 語義正確）。"""
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


STABLE_FACE = os.path.join(
    os.path.expanduser("~"), ".local", "lib", "delegate-bridge",
    "runtime", "current", "dutymail",
)


def _resolve_binary():
    env_bin = os.environ.get(RUNNER_ENV)
    if env_bin:
        return env_bin
    # stable face（M3 cutover——bridge db-96 durable home；路徑恆定
    # 不隨 plugin cache 版本剪除浮動；atomic flip 機制保證 binary 完整性）。
    stable = STABLE_FACE
    if os.path.isfile(stable) and os.access(stable, os.X_OK):
        return stable
    on_path = shutil.which("dutymail")
    if on_path:
        return on_path
    # cache rungs 依序（zcode 先、claude 後——既有優先序零變，AIR-273
    # 第四 rung 只在 candidates 追加）；每 rung 內取版本最新。
    # stable face 缺席時的 fallback——保留作防禦縱深。
    for base in (PLUGIN_CACHE_BASE, CLAUDE_PLUGIN_CACHE_BASE):
        candidates = glob.glob(
            os.path.join(os.path.expanduser(base), PLUGIN_BIN_PATTERN)
        )
        if candidates:
            return max(candidates, key=_version_key)
    raise BinaryMissing(
        "dutymail binary not found（" + RUNNER_ENV
        + " / stable face / PATH / zcode・claude plugin cache 皆缺席）"
    )


def _default_runner(argv):
    """真實 dutymail 呼叫（無 shell）；非零 exit＝解析 stderr typed
    failure 成 DutymailFaceError raise（fail-soft 由上層吸收）。解析
    成功但 spawn 失敗（env 釘死路徑不存在等）＝BinaryMissing typed
    raise——缺席面恆 typed，不走裸 FileNotFoundError traceback。"""
    try:
        proc = subprocess.run(
            [_resolve_binary()] + list(argv),
            capture_output=True,
            text=True,
            timeout=DUTYMAIL_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BinaryMissing(
            "dutymail binary spawn 失敗（解析成功但路徑不存在）："
            f"{_resolve_binary()!r}"
        ) from exc
    if proc.returncode != 0:
        raise _face_error_from_stderr(proc.stderr, proc.returncode)
    return proc.stdout


def _face_error_from_stderr(stderr, exit_code):
    try:
        doc = json.loads(stderr) if stderr.strip() else None
    except ValueError:
        doc = None
    if isinstance(doc, dict) and isinstance(doc.get("error"), dict):
        body = doc["error"]
        return DutymailFaceError(
            code=str(body.get("code", "unknown")),
            error_class=str(body.get("class", "unknown")),
            message=str(body.get("message", "")),
            retryable=bool(body.get("retryable", False)),
            exit_code=exit_code,
        )
    return DutymailFaceError(
        code="unknown",
        error_class="unknown",
        message=(stderr or "").strip()[:200] or f"exit {exit_code}",
        retryable=False,
        exit_code=exit_code,
    )


def _call(runner, argv):
    """runner 呼叫＋stdout 契約解析 → result dict（形狀漂移 fail-loud
    raise，交上層 fail-soft；禁靜默歸零）。"""
    out = runner(list(argv))
    try:
        doc = json.loads(out)
    except ValueError as exc:
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"unparsable stdout: {out[:120]!r}", False, 0,
        ) from exc
    if not isinstance(doc, dict):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"stdout 非 JSON object: {out[:120]!r}", False, 0,
        )
    if doc.get("ok") is True and isinstance(doc.get("result"), dict):
        return doc["result"]
    if isinstance(doc.get("error"), dict):
        body = doc["error"]
        raise DutymailFaceError(
            code=str(body.get("code", "unknown")),
            error_class=str(body.get("class", "unknown")),
            message=str(body.get("message", "")),
            retryable=bool(body.get("retryable", False)),
            exit_code=0,
        )
    raise DutymailFaceError(
        "shape-drift", "unknown", f"unexpected stdout: {out[:120]!r}",
        False, 0,
    )


# ── dutymail faces（薄包裝——argv 凍結語義，不重定義）────────────────


def holder_status(runner, address):
    return _call(runner, ["holder", "status", "--address", address])


def holder_active(status):
    """holder status「binding active」布林（AIR-288 雙版投影）：3.8.0
    欄位＝`bound`（db-98 B 案：live 改名＋leaseExpiresAtUs 移除）、
    3.7.0＝`live`——get-or-fallback 先取新欄位、缺席退舊欄位（混版
    窗口 binary 是哪版都同判定）。**雙欄位皆缺席＝shape-drift
    fail-loud**（AIR-288 judge MF2）：bridge bind 是純 epoch CAS、不查
    active（holder.rs bind 只比 expected_epoch）——把缺席誤判成 False
    會讓本閘放行、靜默搶走 live holder，正是 no-steal 閘要防的事；同
    `bindingEpoch` 驗證先例 raise。欄位在場但值非 `True`（None 等）
    不誤判。"""
    if "bound" in status:
        return status["bound"] is True
    if "live" in status:
        return status["live"] is True
    raise DutymailFaceError(
        "shape-drift", "unknown",
        f"holder status 投影欄位雙缺席（bound/live）：{sorted(status)}",
        False, 0,
    )


def holder_bind(runner, address, expected_epoch):
    return _call(
        runner,
        ["holder", "bind", "--address", address,
         "--expected-epoch", str(expected_epoch)],
    )


def receive_prepare(runner, address, token, max_count=None, invalidate=False):
    argv = ["receive", "prepare", "--address", address, "--token", token]
    if max_count is not None:
        argv += ["--max-count", str(max_count)]
    if invalidate:
        argv += ["--invalidate"]
    return _call(runner, argv)


def receive_ack(runner, address, token, batch_token):
    return _call(
        runner,
        ["receive", "ack", "--address", address, "--token", token,
         "--batch", batch_token],
    )


def receive_status(runner, address):
    """`receive status` 唯讀 face——pendingCount 現值（monitor 消費面；
    處理器本身不消費——digest 年齡取自批次 dispositions）。"""
    return _call(runner, ["receive", "status", "--address", address])


def holder_release(runner, address, token):
    """`holder release` face（AIR-288 MF1——db-98 S4）：token 驗證、
    未 ack 批次 fencing、mail/cursor/epoch 保留。清潔關閉＝release，
    非走人。"""
    return _call(
        runner,
        ["holder", "release", "--address", address, "--token", token],
    )


# ── per-session holder state（bearer capability；0600；atomic 寫）─────


def _state_base_dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(base, "ai-guide", "duty-receive")


_SAFE_SESSION_RE = re.compile(r"[^A-Za-z0-9._-]+")


def state_path(session_id, base_dir=None):
    """state 檔路徑（per-session；base_dir 可注入——測試 fake state）。"""
    safe = _SAFE_SESSION_RE.sub("_", session_id) or "unknown"
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, safe + ".json")


def load_state(path):
    """讀 state → dict | None。缺檔＝冷啟動；壞 JSON／非 dict＝視同冷啟動
    重新 bind（token 遺失安全——rebind 路徑自癒；stderr 註記）。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        print(
            f"[{HOOK_TAG}] holder state 損壞——視同冷啟動重新 bind"
            f"（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return None
    return doc if isinstance(doc, dict) else None


def save_state(path, doc):
    """atomic 寫（pid 後綴 tmp＋os.replace）＋0600——bearer capability
    檔案面。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


# death-evidence 接管陳舊門檻（AIR-288 judge MF1）：holding session 的
# state 檔 mtime 落後現值超過此數＝prompt 心跳停擺、前任 holder 可證
# 已死（24h——跨週末長閒置 session 不誤殺；誤判無數據風險：舊 token
# prepare 收 fencing → 既有 rebind 路徑過 active 閘，CAS 恆為兜底）。
HOLDER_STALE_SECONDS = 24 * 3600


def _touch_heartbeat(state_file, st):
    """prompt 心跳（AIR-288 MF1）：值星 session 每 valid-state 邊界重寫
    state 檔（mtime 前進＋`heartbeat_iso` 落盤）——death-evidence 接管
    的新鮮度證據源：mtime 停止前進＝session 心跳停擺。生產呼叫面在
    per-session advisory lock 內（hook run() critical section）。心跳是
    證據非正確性——寫失敗只失去舉證能力，不擋收信（CAS 恆為最後防線）。"""
    try:
        doc = dict(st)
        doc["heartbeat_iso"] = datetime.now(UTC).isoformat(
            timespec="seconds"
        )
        save_state(state_file, doc)
    except OSError:
        pass


def _sibling_states(state_dir):
    """state dir 兄弟 session state 清單（(path, doc) 對；`*.json`）。
    缺目錄＝空；壞 JSON／非 dict 略過——損壞檔既非新鮮也非死亡證據
    （crash-only：不可解析的東西不構成舉證）。"""
    if not state_dir or not os.path.isdir(state_dir):
        return []
    out = []
    for path in glob.glob(os.path.join(state_dir, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict):
            out.append((path, doc))
    return out


def _holder_death_evidence(state_dir, address, epoch, now_s=None,
                           stale_seconds=HOLDER_STALE_SECONDS):
    """death-evidence 判定（AIR-288 judge MF1(ii)——ZCode 無 SessionEnd
    面）：active holder（status binding active＋epoch N）的兄弟 session
    state 中 **epoch 吻合者全陳舊**（mtime 落後 ≥ stale_seconds）⇒
    True——前任 holder prompt 心跳停擺、可證已死，`bind --expected-epoch
    N` 接管（S6 正當化條件「prior owner provably cannot be alive」機械
    化；對齊 `holder takeover` help 的 authoritative death evidence 條款
    ——dutymail 不 impose policy，接管規則是消費端自律）。任一吻合
    state 新鮮在場、或無任何吻合 state（外點消費者／手動 bind——無從
    舉證）⇒ False，HolderConflict 照舊。stat 失敗（掃描與判定之間檔案
    消失）＝保守 False。誤判無數據風險：見 HOLDER_STALE_SECONDS 註。"""
    now = time.time() if now_s is None else now_s
    matching = [
        path
        for path, doc in _sibling_states(state_dir)
        if doc.get("address") == address and doc.get("epoch") == epoch
    ]
    if not matching:
        return False
    for path in matching:
        try:
            age = now - os.stat(path).st_mtime
        except OSError:
            return False
        if age < stale_seconds:
            return False
    return True


def _valid_holder_state(st, address):
    return (
        st is not None
        and st.get("address") == address
        and isinstance(st.get("token"), str)
        and bool(st["token"])
        and isinstance(st.get("epoch"), int)
    )


# ── per-session 併發鎖（AIR-255 B：dedicated lock file＋bounded fallback）──
#
# 同 session 兩邊界（SessionStart／UserPromptSubmit）或 hook 重疊執行時，
# process_once 的 load→decide→save＋ack commit 序列可能交錯（double-present
# ／state lost update）。防護＝同一 session 一把短 critical-section advisory
# lock：dedicated 固定路徑 lock file（duty-receive/<safe_sid>.lock——禁鎖
# state 檔本身：save 走 tmp+os.replace，inode 更換＝兩 process 各鎖到不同
# inode 的假鎖）。鎖失敗永不擋 prompt 熱路徑：非阻塞短重試（總等待 ≤2s）後
# fallback 照跑——容許 bounded 重複呈報（fencing／one-live-batch／ack 冪等
# 仍是信不丟的最後防線），fallback 計數走 dedicated sidecar（<safe_sid>
# .fallbacks——muse 可觀測性：重報率突增才複議更重的鎖；F-2 修復輪起不寫
# state 主檔：無鎖 read-modify-write 對主檔有回滾 holder token/epoch 的
# race，_bind_fresh 全新 dict 落盤也會掃掉計數）。macOS/Linux fcntl 可用，
# 不做跨平台抽象。

import fcntl  # 同區塊定位（鎖段落）而非檔首

LOCK_RETRY_DELAYS = (0.5, 0.5, 0.5, 0.5)  # 4×0.5s＝總等待 ≤2s


def lock_path(session_id, base_dir=None):
    """dedicated per-session lock file 路徑（與 state 同目錄、獨立檔）。"""
    safe = _SAFE_SESSION_RE.sub("_", session_id) or "unknown"
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, safe + ".lock")


class SessionLockHandle:
    """flock handle。held=False＝fallback 形（未持有鎖，release 無副作用）。"""

    def __init__(self, held, path, fd=None, error=None):
        self.held = held
        self.path = path
        self._fd = fd
        self.error = error

    def release(self):
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None


def acquire_session_lock(
    session_id, base_dir=None, delays=LOCK_RETRY_DELAYS, sleep=time.sleep
):
    """取 per-session advisory lock → SessionLockHandle。

    LOCK_EX|LOCK_NB 失敗→delays 逐次重試（首試不睡）；仍失敗＝fallback
    handle（held=False——呼叫端照跑＋stderr 註記＋計數）。開檔／權限
    OSError＝fail-open 同 fallback 路徑（不擋 prompt）。鎖檔空內容——
    不承載 state（flock 只用 fd）。
    """
    path = lock_path(session_id, base_dir)
    fd = None
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    except OSError as exc:
        return SessionLockHandle(False, path, error=repr(exc))
    for delay in (None, *delays):
        if delay is not None:
            sleep(delay)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return SessionLockHandle(True, path, fd=fd)
        except OSError:
            continue
    os.close(fd)
    return SessionLockHandle(False, path)


def fallback_path(session_id, base_dir=None):
    """lock fallback 計數 sidecar 路徑（與 state/lock 同目錄、獨立檔）。"""
    safe = _SAFE_SESSION_RE.sub("_", session_id) or "unknown"
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, safe + ".fallbacks")


def _read_int_sidecar(path, label):
    """sidecar 單一 int 讀數（.fallbacks／.misses 共用）。缺檔＝0；
    不可讀／壞內容（含負數）＝0＋stderr 一行註記——可觀測性計數（非
    authoritative），讀失敗不 raise。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read().strip()
    except FileNotFoundError:
        return 0
    except OSError as exc:
        print(
            f"[{HOOK_TAG}] {label} 計數檔不可讀——視同 0"
            f"（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return 0
    try:
        value = int(raw)
    except ValueError:
        print(
            f"[{HOOK_TAG}] {label} 計數檔損壞——視同 0 重計"
            f"（內容 {raw!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return 0
    if value < 0:
        # 負 int 非合法計數——同壞檔處置（.fallbacks/.misses 共用契約）。
        print(
            f"[{HOOK_TAG}] {label} 計數檔含負數——視同 0 重計"
            f"（內容 {raw!r}；路徑 {path}）",
            file=sys.stderr,
        )
        return 0
    return value


def _atomic_write_int(path, value):
    """sidecar 單一 int 寫入（.fallbacks／.misses 共用形態）：pid 後綴
    tmp＋os.replace（atomic overwrite）＋0600。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(str(value))
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def read_lock_fallbacks(path):
    """讀 sidecar 計數 → int（--help／hook 端未來消費的讀數 API）。

    缺檔＝0；壞內容／不可讀＝0＋stderr 一行註記——可觀測性計數（趨勢
    偵測用途，非 authoritative），讀失敗不 raise。
    """
    return _read_int_sidecar(path, "fallback")


def bump_lock_fallback(session_id, base_dir=None):
    """fallback 計數 += 1——dedicated sidecar（<safe_sid>.fallbacks，內容＝
    單一 int，atomic overwrite：pid 後綴 tmp＋os.replace＋0600）。

    F-2（修復輪）：計數不寫 state 主檔——原實作對主檔無鎖 read-modify-
    write，與 holder 寫入並發時會以 stale dict 落盤（回滾他方 token/
    epoch 記錄）；_bind_fresh 全新 dict 落盤也把計數歸零（F-3）。sidecar
    讓主檔只剩 holder 權威、計數生命週期獨立——兩問題自然解。計數在
    並發 bump 間仍可少量丟失（可觀測性趨勢用途，非 authoritative）。
    壞檔由 read_lock_fallbacks 視同 0 重計（stderr 一行）。
    """
    path = fallback_path(session_id, base_dir)
    count = read_lock_fallbacks(path) + 1
    _atomic_write_int(path, count)


# ── binary consecutive-miss 計數（AIR-274 M1：消音缺口服務）──────────
#
# BinaryMissing（resolver 全 miss——環境壞）與 store 缺席（class 4 合法
# 軟 path）分流：前者以 per-session sidecar 連續計數，達門檻 stderr
# advisory（hook 面消音不再靜默）；binary 在場呼叫歸零（resolve 已過
# ——含 face 失敗；唯 BinaryMissing 不歸零）。形態與 .fallbacks sidecar
# 同（state 同目錄獨立檔、單一 int、atomic overwrite 0600、壞檔視同
# 0 重計）——非 authoritative，計數少量丟失可容忍。


def miss_path(session_id, base_dir=None):
    """binary miss 計數 sidecar 路徑（與 state/lock 同目錄、獨立檔）。"""
    safe = _SAFE_SESSION_RE.sub("_", session_id) or "unknown"
    root = base_dir if base_dir is not None else _state_base_dir()
    return os.path.join(root, safe + ".misses")


def read_miss_count(path):
    """讀 miss 計數 → int。缺檔＝0；壞內容／不可讀＝0＋stderr 一行
    註記（非 authoritative——讀失敗不 raise）。"""
    return _read_int_sidecar(path, "miss")


def bump_binary_miss(session_id, base_dir=None):
    """miss 計數 += 1 → 新計數（atomic overwrite 0600）。寫失敗只
    stderr 一行註記、照回計數——advisory 判準不受阻。"""
    path = miss_path(session_id, base_dir)
    count = read_miss_count(path) + 1
    try:
        _atomic_write_int(path, count)
    except OSError as exc:
        print(
            f"[{HOOK_TAG}] miss 計數寫入失敗——照回計數"
            f"（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )
    return count


def reset_binary_miss(session_id, base_dir=None):
    """計數歸零（binary 在場呼叫＝resolve 已過——含 face 失敗；唯
    BinaryMissing 不歸零）——sidecar 檔移除；
    缺檔 no-op；失敗只 stderr 一行、不 raise（呼叫端在 face 熱路徑）。"""
    path = miss_path(session_id, base_dir)
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(
            f"[{HOOK_TAG}] miss 計數歸零失敗（{exc!r}；路徑 {path}）",
            file=sys.stderr,
        )


# ── policy：class×action 表（default-deny；未知鍵 fail-loud）──────────


class Policy:
    """default-deny 判定。三條代碼層底線（表無法放寪）：solicit 恆
    deny、未列 class 恒 deny、恆人工名單 class（ALWAYS_SURFACE_CLASSES）
    恒 deny；列為 auto 需 intent 在該 class 的 auto_intent 內。

    consume_addresses＝跨址 custody fence 授權集（AIR-312 repo 身份制；
    exact match）——duty_receive process 只准消費呼叫端 repo 的 canonical
    alias（單一源＝caller_repo_address：呼叫端 git common-dir 反推
    primary root 的 basename，經 load_policy 載入）。直構 Policy 未給
    ＝空集＝deny-all（fail-closed：繞過 load_policy 的 caller 消費不到
    任何 address）。"""

    def __init__(self, rules, consume_addresses=frozenset()):
        self._rules = rules  # class -> (action, frozenset(auto_intent))
        self.consume_addresses = frozenset(consume_addresses)

    def allows(self, klass, intent):
        if intent == "solicit":
            return False
        if klass in ALWAYS_SURFACE_CLASSES:
            return False
        rule = self._rules.get(klass)
        if rule is None:
            return False
        action, auto_intents = rule
        return action == "auto" and intent in auto_intents


# ── repo 身份（AIR-312）：canonical alias＝呼叫端 git common-dir 反推
#    primary root 的 basename——一 repo 一信箱，linked WT／subdir／
#    symlink 同一身份；非 git／bare／無法判定 fail-closed ──────────────

# git rev-parse 解析逾時（正常毫秒級；上限防掛死熱路徑——病態 git 掛死
# 不佔滿呼叫預算；逾時＝無法判定＝deny）
GIT_RESOLVE_TIMEOUT_SECONDS = 3


def _git_common_dir(cwd):
    """cwd 的 git common-dir（絕對路徑）→ str | None。

    linked worktree／primary 皆回 primary 的 `.git` 目錄。bare repo
    （`git rev-parse --is-bare-repository`＝true）→ None（fail-closed
    前置——bare 命名 `<x>/.git` 的 common-dir basename 恰為 `.git`，
    無此檢查會誤判 `<x>` 為 primary root）。舊 git 無
    `--path-format=absolute` 時退路：輸出可能相對 cwd——join 後絕對化。
    非 git／git 掛死／git 缺席＝None（fail-closed 前置）。cwd 可注入
    （測試）；None＝process cwd。"""
    base = cwd if cwd else os.getcwd()
    try:
        bare = subprocess.run(
            ["git", "rev-parse", "--is-bare-repository"],
            capture_output=True, text=True, check=False, cwd=base,
            timeout=GIT_RESOLVE_TIMEOUT_SECONDS,
        )
        if bare.returncode == 0 and bare.stdout.strip() == "true":
            return None
        proc = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute",
             "--git-common-dir"],
            capture_output=True, text=True, check=False, cwd=base,
            timeout=GIT_RESOLVE_TIMEOUT_SECONDS,
        )
        if proc.returncode == 0:
            out = proc.stdout.strip()
            return out or None
        proc = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, check=False, cwd=base,
            timeout=GIT_RESOLVE_TIMEOUT_SECONDS,
        )
        if proc.returncode != 0:
            return None
        out = proc.stdout.strip()
        if not out:
            return None
        return out if os.path.isabs(out) else os.path.abspath(
            os.path.join(base, out)
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _caller_primary_root(cwd=None):
    """呼叫端 repo 的 primary root（realpath）→ str | None（fail-closed）。

    以 common-dir 佈局反推：primary／linked worktree 的 common-dir 恆
    `<primary>/.git` → dirname 即 primary root。basename 非 `.git` 的
    git-dir 佈局（bare repo：common-dir＝repo 本體 `<x>.git`；bare 命名
    `<x>/.git` 由 `_git_common_dir` 的 `--is-bare-repository` 前置拒絕；
    submodule：`<super>/.git/modules/<name>`；分離 gitdir）＝無法判定
    primary root → None（寧擋不放）。root 以 realpath 規範化（macOS
    /tmp 符號連結面；symlink 進入路徑同身份）。"""
    common = _git_common_dir(cwd)
    if not common or os.path.basename(common) != ".git":
        return None
    root = os.path.dirname(common)
    if not root or not os.path.isdir(root):
        return None
    return os.path.realpath(root)


def caller_repo_address(cwd=None):
    """呼叫端 repo 的 canonical mailbox alias＝primary root basename →
    str。身份無法判定（非 git／bare／git-dir 佈局不明）＝ConfigError
    deny-all fail-loud（無法判定呼叫端 repo＝不消費——寧擋不放）。
    cwd 可注入（測試）；預設＝process cwd（CLI 面＝呼叫 shell、hook
    面＝harness project dir）。"""
    root = _caller_primary_root(cwd)
    if root is None:
        raise ConfigError(
            "無法判定呼叫端 repo（非 git／bare／git-dir 佈局無法判定）"
            "＝不消費（custody deny-all fail-loud）"
        )
    return os.path.basename(root)


def load_policy(path, caller_root=None):
    """載入分診表＋custody 授權 → Policy（AIR-312 repo 身份制）。

    分診表讀 `path`（script root 的 processor.toml——中央基線不 fork；
    triage-only：出現 consume_addresses 鍵＝未知頂層鍵 ConfigError）。
    custody 授權集由呼叫端 repo 身份推導：canonical alias＝
    caller_repo_address（`caller_root`＝呼叫端定位目錄——repo root 或
    repo 內任意層，linked WT／subdir 同身份；None＝process cwd；可注入
    測試）。分診表缺席／TOML 壞形／未知鍵／壞值、或身份無法判定一律
    ConfigError（呼叫端 fail-loud exit 3——不靜默全 surface、不靜默放
    行）。"""
    try:
        with open(path, "rb") as fh:
            doc = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"分診表缺席：{path}") from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"分診表解析失敗（{path}）：{exc}") from exc
    extra = set(doc) - {"class_rule"}
    if extra:
        raise ConfigError(
            f"分診表未知頂層鍵：{sorted(extra)}"
            f"（triage-only 僅允許 class_rule——custody 授權集已 "
            f"repo 身份制＝caller_repo_address 推導，無授權檔）"
        )
    rows = doc.get("class_rule", [])
    if not isinstance(rows, list):
        raise ConfigError("class_rule 應為 array of tables")
    rules = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ConfigError(f"class_rule[{i}] 非 table")
        keys = set(row)
        if keys != ROW_KEYS:
            raise ConfigError(
                f"class_rule[{i}] 鍵集不符：得 {sorted(keys)}，"
                f"應 {sorted(ROW_KEYS)}"
            )
        klass = row["class"]
        if not isinstance(klass, str) or not klass:
            raise ConfigError(f"class_rule[{i}].class 應為非空字串")
        intents = row["auto_intent"]
        if (
            not isinstance(intents, list)
            or not all(isinstance(x, str) for x in intents)
        ):
            raise ConfigError(
                f"class {klass}：auto_intent 應為字串陣列"
            )
        if "solicit" in intents:
            raise ConfigError(
                f"class {klass}：solicit 恆 surface——auto_intent 不可"
                "放寪（代碼層 default-deny 底線）"
            )
        bad = [x for x in intents if x not in ALLOWED_AUTO_INTENTS]
        if bad:
            raise ConfigError(
                f"class {klass}：auto_intent 含未知 intent {bad}"
                f"（允許：{list(ALLOWED_AUTO_INTENTS)}）"
            )
        action = row["action"]
        if action not in ("auto", "surface"):
            raise ConfigError(
                f"class {klass}：action 應為 auto|surface，得 {action!r}"
            )
        if klass in ALWAYS_SURFACE_CLASSES and action == "auto":
            raise ConfigError(
                f"class {klass}：恆人工 class——action 不可為 auto"
                "（代碼層 default-deny 底線，表不可放寪）"
            )
        if klass in rules:
            raise ConfigError(f"class {klass} 重複定義")
        rules[klass] = (action, frozenset(intents))
    canonical = caller_repo_address(caller_root)
    return Policy(rules, frozenset({canonical}))


# ── triage：default-deny 分診（純函式）──────────────────────────────


@dataclass
class Disposition:
    """單封處置紀錄。action＝auto（digest 吸收）｜surface（摘要呈報——
    B′：全文面＝SC INBOX，canonical 欄位僅供內部，不進輸出）。"""

    action: str
    reason: str
    klass: str | None
    intent: str | None
    envelope_id: str | None
    from_session: str | None
    created_at_us: int | None
    canonical: str


def _positive_int(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def _non_negative_int(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
    )


def triage(item, policy):
    """prepare envelopes 元素 → Disposition（default-deny）。

    auto 需全過：canonicalEnvelope 可解析 dict → delivery.intent 合法 →
    body 可解析 JSON object → class 鍵在場 →（receipt 類）in_reply_to
    或 body idempotency 鍵（task/card）在場 → policy.allows(class,
    intent)。任一不成立＝surface（原因隨行）。
    """
    canonical = None
    envelope_id = None
    if isinstance(item, dict):
        raw = item.get("canonicalEnvelope")
        envelope_id = item.get("envelopeId")
        if isinstance(raw, str):
            canonical = raw
        if not isinstance(envelope_id, str):
            envelope_id = None
    if canonical is None:
        return Disposition(
            "surface", "bad-envelope", None, None, envelope_id,
            None, None, json.dumps(item, ensure_ascii=False, default=str),
        )
    try:
        env = json.loads(canonical)
    except ValueError:
        env = None
    if not isinstance(env, dict):
        return Disposition(
            "surface", "bad-envelope", None, None, envelope_id,
            None, None, canonical,
        )
    frm = env.get("from") if isinstance(env.get("from"), dict) else {}
    from_session = frm.get("session_id")
    if not isinstance(from_session, str):
        from_session = None
    created = env.get("created_at_us")
    created = created if _positive_int(created) else None
    delivery = (
        env.get("delivery") if isinstance(env.get("delivery"), dict) else {}
    )
    intent = delivery.get("intent")
    if intent not in VALID_INTENTS:
        return Disposition(
            "surface", "bad-intent", None, None, envelope_id,
            from_session, created, canonical,
        )
    body = env.get("body")
    body_doc = None
    if isinstance(body, str):
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            body_doc = parsed
    if body_doc is None:
        return Disposition(
            "surface", "bad-body", None, intent, envelope_id,
            from_session, created, canonical,
        )
    klass = body_doc.get("class")
    if not isinstance(klass, str) or not klass:
        return Disposition(
            "surface", "bad-body", None, intent, envelope_id,
            from_session, created, canonical,
        )
    if intent == "receipt":
        has_irt = isinstance(env.get("in_reply_to"), str) and bool(
            env["in_reply_to"]
        )
        has_idem = any(
            isinstance(body_doc.get(k), str) and bool(body_doc[k])
            for k in IDEMPOTENCY_KEYS
        )
        if not (has_irt or has_idem):
            return Disposition(
                "surface", "receipt-no-idempotency", klass, intent,
                envelope_id, from_session, created, canonical,
            )
    if policy.allows(klass, intent):
        return Disposition(
            "auto", "policy-allow", klass, intent, envelope_id,
            from_session, created, canonical,
        )
    return Disposition(
        "surface", "policy-deny", klass, intent, envelope_id,
        from_session, created, canonical,
    )


# ── 輸出渲染（digest-first；surface 一行摘要）──────────────────────────


def _klass_counts(dispositions):
    """dispositions → class 計數 dict（klass 缺席歸 unknown）——digest
    主行與 surface 摘要行共用（AIR-261 F3：原兩處內聯迴圈抽 helper）。"""
    counts: dict[str, int] = {}
    for d in dispositions:
        label = d.klass if d.klass else "unknown"
        counts[label] = counts.get(label, 0) + 1
    return counts


def render(address, dispositions, now_us):
    """dispositions → 輸出行（digest 行＋surface 一行摘要）。auto 由 digest
    吸收（「例行已處理」——絕不宣稱 work accepted）；B′ 解凍（AIR-258，
    SC-305 上線）後 surface 項不注入全文——人類判讀面＝SC INBOX（durable
    投影），本處壓成 class 計數＋可執行查詢指針（dutymail events
    --address）＋前 SURFACE_ID_LIMIT 封 id 對照（無 body；處置語義不變
    ——surface 項照樣計入 ack 前處置）。"""
    if not dispositions:
        return []
    surf = [d for d in dispositions if d.action == "surface"]
    n_auto = len(dispositions) - len(surf)
    counts = _klass_counts(dispositions)
    head = (
        f"[{HOOK_TAG}] {address}：新到 {len(dispositions)}、"
        f"{n_auto} 件例行已處理、{len(surf)} 件等你"
    )
    ages = [
        # clamp 0：created_at_us 在未來（時鐘偏移）時 age 為負——負年齡
        # 顯示不合理，下限 0 分鐘（S3 finding #3）。取全部 dispositions
        # （auto＋surface）——全 auto 批次也顯示最舊年齡、auto 更舊時
        # 不低估（review 修復 U9）。
        max(0, now_us - d.created_at_us)
        for d in dispositions
        if d.created_at_us is not None
    ]
    if ages:
        minutes = round(max(ages) / MINUTES_US)
        head += f"（最舊 {minutes} 分鐘）"
    head += "；class：" + "、".join(
        f"{k}×{v}" for k, v in counts.items()
    )
    lines = [head]
    if surf:
        surf_counts = _klass_counts(surf)
        ids = [d.envelope_id if d.envelope_id else "unknown" for d in surf]
        id_list = "、".join(ids[:SURFACE_ID_LIMIT])
        if len(ids) > SURFACE_ID_LIMIT:
            id_list += "…"
        # F2（AIR-261）：fallback 指針須可執行——events face 無 positional
        # id 形（僅 --address/--kind/--limit/--cursor）；id 清單留行內供對照
        # （ids：段），不再是命令參數。
        lines.append(
            f"[{HOOK_TAG}] {address}：{len(surf)} 件等你——"
            + "、".join(f"{k}×{v}" for k, v in surf_counts.items())
            + f"（全文見 SC INBOX／dutymail events --address {address}"
            + f"；ids：{id_list}）"
        )
    return lines


# ── ensure_holder：fresh bind／有 token 直用（AIR-288：renew 面拔除）──


def ensure_holder(address, runner, state_file):
    """取得 holder 權威 → 有效 state dict（3.8.0 db-98 B 案：renew 面
    拔除——authority＝address＋epoch＋token＋binding active，無時鐘）。

    無 token → status（觀察 epoch＋binding active）→ active holder 在場
    ＝不搶（HolderConflict surface）；active=False 才 bind（consent CAS）。
    有 token → 直用（零 holder face 呼叫——heartbeat 退役；3.8.0 無時鐘
    權威下 token 有效至被 fence；3.7.0 混版窗口 lease 自然過期＝class 5
    fencing，由 `_prepare_with_recovery` 既有 rebind 路徑接收——status→
    rebind、同樣過 active 閘）。valid-state 邊界重寫 state 檔＝prompt
    心跳（`_touch_heartbeat`——death-evidence 新鮮度源）。rebind CAS
    失敗（epoch-conflict，race window 内他方先 bind）＝HolderConflict。
    storage 錯誤原樣傳出（上層 fail-soft pre-migration）。
    """
    st = load_state(state_file)
    if _valid_holder_state(st, address):
        _touch_heartbeat(state_file, st)
        return st
    return _bind_fresh(address, runner, state_file)


def release_holder(runner, state_file):
    """清潔關閉釋出（AIR-288 judge MF1(i)——bridge item 6(a)）：以
    state 的 live token 呼 `holder release`（token 驗證、未 ack 批次
    fencing、mail/cursor/epoch 保留——「Clean shutdown is release —
    not walking away」）→ 成功後**移除 state 檔**（session 終局：
    token 已作廢、批次已 fence，下一 session 冷啟 rebind、寧重不漏
    吸收 fenced 批）。無 state／無有效 token＝無可釋出 → False（零
    face 呼叫）。release face 失敗 → DutymailFaceError 原樣傳出（hook
    端 fail-soft 包裝——release 失敗不擋 session 收尾；殘局由 ZCode
    death-evidence 接管兜底）。"""
    st = load_state(state_file)
    if st is None or not _valid_holder_state(st, st.get("address")):
        return False
    holder_release(runner, st["address"], st["token"])
    try:
        os.remove(state_file)
    except OSError:
        pass  # 殘檔無害——token 已作廢（下一次 _valid 後 prepare fencing 自癒）
    return True


def _bind_fresh(address, runner, state_file):
    observed = holder_status(runner, address)
    epoch = observed.get("bindingEpoch")
    # observed epoch 驗證＝非負整數：fresh address（從未 bind）的合法值
    # 就是 0（unbound e=0）——首次 bind 的 consent CAS 觀察值正是
    # `--expected-epoch 0`（S3 真實 store 實測 3.7.0 形：bindingEpoch=0
    # ＋live=False＋leaseExpiresAtUs=None；3.8.0 同 epoch 面，live 改名
    # bound、leaseExpiresAtUs 移除）。bind 後的 epoch 恆 ≥1（下方
    # result 面維持正整數驗證）。
    if not _non_negative_int(epoch):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder status bindingEpoch 非非負整數：{observed!r}",
            False, 0,
        )
    # holder 搶奪防護（S3 finding #2）：binding active 在場（3.8.0
    # bound／3.7.0 live）＝另一 session 正持有消費權威——**不 bind 不搶**
    # （並行 session／卡 WT spawned agents 的 ping-pong 防護）；值星換代
    # 正當路徑＝對方釋放（SessionEnd release——codex/grok 面）或死亡
    # （ZCode 無 SessionEnd——death-evidence 接管）後 rebind。CAS
    # （epoch-conflict）保留為 status 與 bind 之間 race window 的最後
    # 防線。「active=True 且 epoch==我 state epoch」（我方 token 失效
    # 邊角）經此同一規則落衝突不搶——對方釋放後自癒，信不丟（prepare
    # 不消耗）。 death-evidence 接管（AIR-288 judge MF1(ii)）：前任
    # holder 的兄弟 state（epoch 吻合）全陳舊＝prompt 心跳停擺、可證
    # 已死（S6「prior owner provably cannot be alive」機械化）——不
    # raise、落下方 CAS bind 接管；bind 當下 epoch 已被推進＝
    # epoch-conflict → HolderConflict（race 兜底）。
    if holder_active(observed) and not _holder_death_evidence(
        os.path.dirname(state_file) or None, address, epoch
    ):
        raise HolderConflict(
            f"{address}：另一 session holding（epoch {epoch}）——本"
            " session 不搶，待對方釋放換代；處理面照舊由現 holder 承擔"
        )
    try:
        result = holder_bind(runner, address, epoch)
    except DutymailFaceError as exc:
        if exc.code == CAS_CONFLICT_CODE:
            raise HolderConflict(
                f"{address}：holder 衝突——bind CAS 失敗（epoch 已被其他"
                "值星推進），本輪不處理信件、不重試"
            ) from exc
        raise
    token = result.get("holderToken")
    new_epoch = result.get("bindingEpoch")
    if not isinstance(token, str) or not token:
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder bind holderToken 缺席：{sorted(result)}", False, 0,
        )
    if not _positive_int(new_epoch):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder bind bindingEpoch 非正整數：{sorted(result)}",
            False, 0,
        )
    st = {
        "address": address,
        "epoch": new_epoch,
        "token": token,
        "bound_at_iso": datetime.now(UTC).isoformat(
            timespec="seconds"
        ),
    }
    save_state(state_file, st)
    return st


# ── process_once：一個邊界的完整收信週期 ─────────────────────────────


def _without_batch(st):
    st = dict(st)
    st.pop("batch_token", None)
    st.pop("batch_disposed", None)
    return st


def _clear_batch(state_file):
    st = load_state(state_file) or {}
    st = _without_batch(st)
    if st:
        save_state(state_file, st)


def _resolve_legacy_batch(address, runner, st, state_file):
    """上一邊界遺留未 ack 批次（state 記錄）處置 → (st, invalidate_next)。

    已處置（batch_disposed）→ 先試 ack（冪等重試——同 epoch replayed
    回原 receipt）；wiring error（AIR-299 holder-role-mismatch）原樣
    傳播（配置錯非 transient，不留保留桶）；批次已死（expired/fenced/
    invalidated）或 token 已 fenced → 清記錄落 fresh prepare；storage
    等其他失敗 → 保留紀錄（prepare 稍後自然失敗，交上層 fail-soft）。
    未處置 → 不代 ack，回 invalidate_next=True（寧重不漏：prepare
    --invalidate 重 prepare）。
    """
    batch_token = st.get("batch_token")
    if not isinstance(batch_token, str) or not batch_token:
        return st, False
    if st.get("batch_disposed") is True:
        try:
            receive_ack(runner, address, st["token"], batch_token)
        except DutymailFaceError as exc:
            if exc.code in WIRING_ERROR_CODES:
                raise  # 接線錯誤（AIR-299）——原樣傳播，不留 transient 桶
            if exc.code in BATCH_DEAD_CODES or _is_fencing(exc):
                pass  # 批次已死——清記錄，fresh prepare 重取同批信
            else:
                return st, False  # store 缺席等——保留紀錄先試 ack 下輪
        else:
            pass  # ack 成功（fresh 或 replayed）——cursor 已前進
        st = _without_batch(st)
        save_state(state_file, st)
        return st, False
    return st, True


def _prepare_with_recovery(address, runner, st, state_file, max_count,
                           invalidate):
    """prepare（單次重試上限，不轟炸）→ (result, effective_st)。

    batch-conflict（crash-before-state-write 孤兒批）→ --invalidate
    重試一次；fencing 家族（class 5——3.8.0 現役 stale-epoch/token
    mismatch＋3.7.0 混版 lease-expired，`_is_fencing` 按 class 接收）
    → status→rebind→以新 token 重試一次（舊批隨 rebind 自動 fenced）。
    豁免（AIR-299）：holder-role-mismatch（wiring error）不進恢復——
    原樣傳播。"""
    try:
        return (
            receive_prepare(
                runner, address, st["token"],
                max_count=max_count, invalidate=invalidate,
            ),
            st,
        )
    except DutymailFaceError as exc:
        if exc.is_storage:
            raise
        if exc.code == BATCH_CONFLICT_CODE:
            return (
                receive_prepare(
                    runner, address, st["token"],
                    max_count=max_count, invalidate=True,
                ),
                st,
            )
        if _is_fencing(exc):
            st2 = _bind_fresh(address, runner, state_file)
            return (
                receive_prepare(
                    runner, address, st2["token"],
                    max_count=max_count, invalidate=invalidate,
                ),
                st2,
            )
        raise


def process_once(address, runner, policy, state_file,
                 max_count=DEFAULT_MAX_COUNT, now_us=None,
                 disposition_sink=None, resolution_sink=None):
    """完整收信週期 → (lines, commit | None)。

    流程：ensure_holder → 遺留批次收斂 → prepare（bounded）→ state
    記 batch_token（undisposed——crash window 防線）→ 逐封 triage（
    全純計算；任一 raise＝ack 不被呼叫——絕不 flush-ack）→ render。
    commit＝resolution 推進＋ack＋state 收斂，由呼叫端在輸出寫出成功
    後執行（advance-after-emit：先呈報後 commit）。空批次（正典形＝
    envelopes==[] 且 batchToken==None）＝([], None) 零輸出；其他非正
    典形 shape-drift raise（fail-loud，交上層 fail-soft）。

    disposition_sink（AIR-287 最小接線；可選）：triage 後以
    `sink(address, dispositions, now_us)` 記 received 帳（consumer
    disposition ledger，單一源＝scripts/duty_disposition.py）。sink
    生產面必須自帶 failure containment（duty_disposition.
    make_received_sink／make_safe_sink）——本函式不吞 sink 例外：
    sink raise＝本函式 raise、ack 不達（寧重不漏，信件下輪重 prepare
    ——禁半記帳半前進）。None（預設）＝零記帳，既有行為不變。

    resolution_sink（AIR-287 bi 修復必修 1——codex F1；可選）：
    digest 呈現完成邊界（commit 起點、ack 前）以
    `resolution_sink(address, dispositions, now_us)` 推進處理狀態
    （auto→handled／surface→needs-human；單一源＝duty_disposition.
    record_resolution——推進點裁定見該模組 docstring）。ack 是
    transport cursor（bridge 語義 ack≠done），不作推進前提。sink
    raise＝commit raise、ack 不達（寧重不漏——推進失敗仍 ack＝
    「已消費但帳面恆停 received」假陽性 stale）。None（預設）＝不
    推進，既有行為不變。

    跨址 custody fence（AIR-312 repo 身份制）：起手即驗 address ＝呼叫
    端 repo canonical alias（holder bind 前核心閘——任何 holder
    status/bind/prepare/ack 之前；canonical 單一源＝caller_repo_address
    ——git common-dir 反推 primary root basename，見 load_policy）；
    錯址＝CustodyFenceError fail-closed，runner 零呼叫。閘只圈
    process_once（custody 邊界），不下沉 _call／face wrapper——唯讀
    跨址（status/events/wait 診斷）是合法行為，禁誤傷。
    """
    if address not in policy.consume_addresses:
        raise CustodyFenceError(
            f"address 屬他 repo custody——禁消費：{address}"
            f"（canonical alias＝呼叫端 repo 身份——git common-dir 反推"
            f" primary root basename，exact match）"
        )
    now = now_us if now_us is not None else time.time_ns() // 1000
    st = ensure_holder(address, runner, state_file)
    st, invalidate_next = _resolve_legacy_batch(
        address, runner, st, state_file
    )
    prepared, st = _prepare_with_recovery(
        address, runner, st, state_file, max_count, invalidate_next
    )
    envelopes = prepared.get("envelopes")
    batch_token = prepared.get("batchToken")
    if envelopes == [] and batch_token is None:
        return [], None  # 正典空批（凍結契約：[]＋null token）——靜默
    # 非正典形一律 shape-drift fail-loud（U6 收緊）：有信無 token／
    # envelopes 非 list／空批帶 token——禁靜默返空吞信（交上層 fail-soft）。
    if (
        not isinstance(envelopes, list)
        or envelopes == []
        or not (isinstance(batch_token, str) and batch_token)
    ):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"prepare result 形漂移：envelopes={envelopes!r}、"
            f"batchToken={batch_token!r}",
            False, 0,
        )
    st = dict(st)
    st["batch_token"] = batch_token
    st["batch_disposed"] = False
    save_state(state_file, st)
    dispositions = [triage(item, policy) for item in envelopes]
    if disposition_sink is not None:
        disposition_sink(address, dispositions, now)  # AIR-287：記帳接線
    lines = render(address, dispositions, now)
    token = st["token"]

    def commit():
        if resolution_sink is not None:
            # digest 呈現完成邊界（呼叫端契約：輸出成功寫出後才
            # commit）——auto→handled／surface→needs-human；ack 前
            # （ack＝transport cursor，非工作完成前提——AIR-287 bi
            # 必修 1 推進點裁定＝duty_disposition 模組 docstring）。
            resolution_sink(address, dispositions, now)
        st2 = load_state(state_file) or dict(st)
        st2["batch_token"] = batch_token
        st2["batch_disposed"] = True  # 輸出已寫出——處置完成紀錄
        save_state(state_file, st2)
        try:
            receive_ack(runner, address, token, batch_token)
        except DutymailFaceError as exc:
            if exc.code in BATCH_DEAD_CODES:
                _clear_batch(state_file)  # 批次已死：cursor 未前進，
                # 信仍 pending——下輪重 prepare 重呈報（寧重不漏）
            else:
                raise  # storage 等——保留 disposed 紀錄，下輪先試 ack
        else:
            _clear_batch(state_file)

    return lines, commit


# ── S2 ordinary inbox（AIR-312 S2：read→read，原信留原處，只記待回覆）──
#
# 普通 inbox 模型（user 裁定）：看完即 read（transport ACK＝自動標已讀
# 邊），信留原處可重看；只需保留待回覆（寄出成功 receipt 才解除）；工作
# 歸既有卡。本節是 S2 消費面唯一入口——禁調 legacy process_once、
# _prepare_with_recovery 或 disposition sinks（五態 ledger 已 superseded）。
#
# 狀態佈局（per-repo，XDG state／ai-guide/duty-receive/repos/<編碼>/）：
# - pending-replies.json（0600 atomic）：最小待回覆 {incoming ID → note／
#   target／reply pin}，不複製 incoming 原文。
# - pending-replies.lock：per-repo 短鎖（flock；只罩檔案變更＋send 臨界
#   段，不罩 LLM 思考）。
# - inbox-holder.json：自家短 holder token（消費期間短持有；crash 恢復
#   用，無 session registry）。
# per-session state 檔（state_path）是 legacy process 面，與本節互不讀寫。
# repos/ 中間層：base 頂同時住 legacy per-session 檔，repo 目錄另起
# repos/ 命名空間故不與 session 檔碰撞；編碼函式與 mail_waiter 的
# safe_repo_dirname 同語義（percent-encode，不折疊）。

import fcntl as _s2_fcntl  # per-repo 短鎖（與既有 session 鎖同機制）
import hashlib as _s2_hashlib
from contextlib import contextmanager as _s2_contextmanager


class S2Error(RuntimeError):
    """S2 消費面錯誤（fail-loud：CLI 面恆非零 exit，無 fail-soft 成功）。

    exit_code：2＝custody fence（錯址），3＝身份無法判定／配置，
    1＝其餘（含 transport 失敗的如實上報）。
    """

    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


# byte-wise percent 編碼安全集（單一定義——mail_waiter 自本函式委派，
# 不留副本）。code-point 舊制對非 ASCII 以「字」為單位編碼，會與 ASCII
# percent 序列碰撞（「┯」U+252F 與 "%2F" 同映 %252F——injective 破裂）
# ；byte-wise UTF-8 逐 byte 一對一（解碼唯一）。ASCII 輸出與舊制同
# （既有 state 目錄零遷移）；非 ASCII 舊編碼目錄成孤兒（無人再寫，
# watcher 重 arm 重建）。
_SAFE_REPO_BYTES = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-"
)


def safe_repo_dirname(identity):
    """identity → injective 目錄名（UTF-8 byte-wise percent-encode）：
    `A-Za-z0-9._-` 逐 byte 原樣、其餘 byte → `%XX`（大寫 hex）、空→
    unknown。單一定義——mail_waiter.safe_repo_dirname 委派本函式。"""
    safe = "".join(
        chr(b) if b in _SAFE_REPO_BYTES else f"%{b:02X}"
        for b in (identity or "").encode("utf-8")
    )
    return safe or "unknown"


def s2_repo_dir(address, state_dir=None):
    """S2 per-repo 狀態目錄（state_dir 可注入——測試隔離；預設 XDG）。"""
    base = state_dir if state_dir is not None else _state_base_dir()
    return os.path.join(base, "repos", safe_repo_dirname(address))


def pending_path(address, state_dir=None):
    """待回覆檔路徑（per-repo；0600 atomic 寫）。"""
    return os.path.join(s2_repo_dir(address, state_dir),
                        "pending-replies.json")


def pending_lock_path(address, state_dir=None):
    """待回覆短鎖路徑（dedicated lock file；禁鎖資料檔本身）。"""
    return os.path.join(s2_repo_dir(address, state_dir),
                        "pending-replies.lock")


def inbox_holder_path(address, state_dir=None):
    """自家短 holder token 路徑（per-repo；crash 恢復用）。"""
    return os.path.join(s2_repo_dir(address, state_dir),
                        "inbox-holder.json")


@_s2_contextmanager
def _pending_lock(address, state_dir=None):
    """per-repo 短 critical-section 鎖（blocking flock；呼叫端只罩檔案
    變更＋send 臨界段——transport 呼叫可入內，LLM 思考禁入內）。"""
    path = pending_lock_path(address, state_dir)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        _s2_fcntl.flock(fd, _s2_fcntl.LOCK_EX)
        yield
    finally:
        try:
            _s2_fcntl.flock(fd, _s2_fcntl.LOCK_UN)
        finally:
            os.close(fd)


def load_pending_replies(path):
    """讀待回覆檔 → dict | None。缺檔＝無待回覆（None）；壞 JSON／非
    dict／address 缺席＝S2Error fail-loud（狀態損壞不大聲會丟回覆義務，
    禁視同空）。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise S2Error(f"待回覆檔損壞——fail-loud（{exc!r}；路徑 {path}）")
    if not isinstance(doc, dict) or not isinstance(doc.get("address"), str):
        raise S2Error(f"待回覆檔形漂移（路徑 {path}）")
    replies = doc.get("replies")
    if replies is None:
        doc["replies"] = {}
    elif not isinstance(replies, dict):
        raise S2Error(f"待回覆檔 replies 非 object（路徑 {path}）")
    return doc


def save_pending_replies(path, doc):
    """atomic 寫（pid 後綴 tmp＋os.replace）＋0600。OSError 原樣傳出
    （呼叫端＝no-ACK 條件）。"""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _pending_ensure(address, state_dir=None):
    """pending 檔存在保證（缺席建空骨架；既有不動——no-note 讀不清除
    義務）。回傳 doc。"""
    path = pending_path(address, state_dir)
    doc = load_pending_replies(path)
    if doc is None:
        doc = {"address": address, "replies": {}}
        save_pending_replies(path, doc)
        return doc
    if doc.get("address") != address:
        raise S2Error(
            f"待回覆檔 address 不符（檔內 {doc.get('address')!r}≠{address!r}）"
            "——不猜 ownership，fail-loud"
        )
    return doc


def _pending_upsert_note(address, state_dir, envelope_id, note, target):
    """先持久記待回覆（ACK 前；既有 reply pin 保留——crash 重試冪等）。
    呼叫端保證 note/target 雙全。"""
    with _pending_lock(address, state_dir):
        doc = _pending_ensure(address, state_dir)
        entry = doc["replies"].get(envelope_id)
        if not isinstance(entry, dict):
            entry = {}
        entry["note"] = note
        entry["target"] = target
        entry.setdefault("created_at_iso",
                         datetime.now(UTC).isoformat(timespec="seconds"))
        entry.setdefault("reply_envelope_id", None)
        entry.setdefault("reply_sha256", None)
        doc["replies"][envelope_id] = entry
        save_pending_replies(pending_path(address, state_dir), doc)


def _pending_clear_reply(address, state_dir, incoming_id):
    """成功 receipt 後解除待回覆（reply 臨界段內呼叫）。"""
    path = pending_path(address, state_dir)
    doc = load_pending_replies(path)
    if doc is None or incoming_id not in doc.get("replies", {}):
        raise S2Error(f"待回覆缺席、無法解除：{incoming_id}")
    del doc["replies"][incoming_id]
    save_pending_replies(path, doc)


# ── S2 讀信面（producer mail list/get 原文＋body string 完整）──────────


def decode_canonical_item(item):
    """mail item → (env dict | None, absence | None)。

    成功回 (env, None)——env 是 canonicalEnvelope 二次解析後的完整
    object，`body` 保持 string 原樣（不 JSON-decode、不截斷；plain/long
    text 皆合法）。原文缺席（exported／unslotted／壞形）回 (None,
    reason)——呼叫端明示呈現、禁默默 ACK（absence stays explicit）。"""
    if not isinstance(item, dict):
        return None, "item 非 object"
    canon = item.get("canonicalEnvelope")
    payload = item.get("payloadState")
    export = item.get("exportRef")
    if canon is None:
        return None, (
            f"body absent（payloadState={payload!r} exportRef={export!r}）——"
            "exported compaction 或歷史缺體，原信不可重看、禁 ACK"
        )
    if not isinstance(canon, str) or not canon:
        return None, f"body absent（canonicalEnvelope 非全文 string）"
    try:
        env = json.loads(canon)
    except ValueError as exc:
        return None, f"canonicalEnvelope 解析失敗（{exc!r}）——禁 ACK"
    if not isinstance(env, dict):
        return None, "canonicalEnvelope 非 object——禁 ACK"
    body = env.get("body")
    if not isinstance(body, str):
        return None, "body 非 string——禁 ACK（frozen envelope 要求 string）"
    return env, None


def mail_list(runner, address, box="pending", cursor=None, limit=None):
    """`mail list` 唯讀面 → result dict（tokenless zero-write；cursor 原樣
    透傳——preserve cursor）。box∈{pending,all,acked}（預設 pending）。"""
    if box not in ("pending", "all", "acked"):
        raise S2Error(f"box 非法：{box!r}（應 pending|all|acked）", 2)
    argv = ["mail", "list", "--address", address, "--box", box]
    if cursor is not None:
        argv += ["--cursor", cursor]
    if limit is not None:
        argv += ["--limit", str(limit)]
    return _call(runner, argv)


def mail_get(runner, address, envelope_id):
    """`mail get` 唯讀面 → result dict（含 item＋primaryCursor）。"""
    if not isinstance(envelope_id, str) or not envelope_id:
        raise S2Error("envelope id 須為非空字串", 2)
    return _call(
        runner, ["mail", "get", "--address", address,
                 "--envelope-id", envelope_id])


def _s2_bind_no_takeover(runner, address):
    """S2 短 holder 取得 → (token, epoch)。

    status 觀察 binding active 在場＝另一 holder 正持有——無條件拒絕
    （S2 不做 age/death 接管：既有 _bind_fresh 的 death-evidence 路徑
    在此不適用；換代正當路徑＝對方釋放後下一次顯式操作重試）。rebind
    CAS 競敗（epoch-conflict）同樣拒絕不重試。"""
    observed = holder_status(runner, address)
    epoch = observed.get("bindingEpoch")
    if not _non_negative_int(epoch):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder status bindingEpoch 非非負整數：{observed!r}",
            False, 0,
        )
    if holder_active(observed):
        raise S2Error(
            f"{address}：另一 holder 正持有（epoch {epoch}）——S2 不搶、"
            "不做 death 接管；待對方釋放後下一次顯式操作重試"
            "（pending 已保留）"
        )
    try:
        result = holder_bind(runner, address, epoch)
    except DutymailFaceError as exc:
        if exc.code == CAS_CONFLICT_CODE:
            raise S2Error(
                f"{address}：holder 競敗（bind CAS epoch-conflict）——"
                "本輪不消費、不重試（pending 已保留）"
            ) from exc
        raise
    token = result.get("holderToken")
    new_epoch = result.get("bindingEpoch")
    if not isinstance(token, str) or not token:
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder bind holderToken 缺席：{sorted(result)}", False, 0,
        )
    if not _positive_int(new_epoch):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder bind bindingEpoch 非正整數：{sorted(result)}",
            False, 0,
        )
    return token, new_epoch


def _load_inbox_holder(address, state_dir=None):
    """讀自家短 holder 檔 → dict | None（缺檔＝無；壞形＝S2Error）。"""
    path = inbox_holder_path(address, state_dir)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise S2Error(f"holder 檔損壞——fail-loud（{exc!r}；路徑 {path}）")
    if (
        not isinstance(doc, dict)
        or doc.get("address") != address
        or not isinstance(doc.get("token"), str)
        or not doc["token"]
        or not isinstance(doc.get("epoch"), int)
    ):
        raise S2Error(f"holder 檔形漂移（路徑 {path}）——不猜 ownership")
    return doc


def _save_inbox_holder(address, state_dir, epoch, token):
    """存自家短 holder（0600 atomic）。OSError 原樣傳出（呼叫端＝釋放
    已取 token 後報錯、不靜默失權）。"""
    path = inbox_holder_path(address, state_dir)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    doc = {
        "address": address, "epoch": epoch, "token": token,
        "bound_at_iso": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _clear_inbox_holder(address, state_dir=None):
    """刪自家 holder 檔（缺席 no-op；其他 OSError 保留作 evidence 上報）。"""
    try:
        os.remove(inbox_holder_path(address, state_dir))
    except FileNotFoundError:
        pass


def _s2_release_best_effort(runner, address, token):
    """釋放自家 token（best-effort）→ True（已釋放）| False（失敗保留
    evidence）。失敗不 raise——呼叫端如實上報、保留 holder 檔＋pending。"""
    try:
        holder_release(runner, address, token)
    except (DutymailFaceError, BinaryMissing, OSError):
        return False
    return True


def _clear_stale_holder_on_reread(address, runner, state_dir=None):
    """已 ACK 重看短路前清自家殘留 holder（零 ACK/prepare）→ 併入 result
    的 dict 片段。

    saved holder 在場＝前次消費在 release 前崩潰的殘留——檔案即自家
    custody 記錄，token 屬自家：best-effort release＋成功才清檔；失敗
    保留檔案＋揭露。holder 檔損壞＝無 token 可釋放——保留＋揭露，不擋
    唯讀重看。"""
    try:
        saved = _load_inbox_holder(address, state_dir)
    except S2Error as exc:
        return {"released_stale_holder": False,
                "stale_holder_note": f"holder 檔損壞——保留作 evidence（{exc}）"}
    if saved is None:
        return {}
    with _pending_lock(address, state_dir):
        released = _s2_release_best_effort(runner, address, saved["token"])
        if released:
            _clear_inbox_holder(address, state_dir)
    if released:
        return {"released_stale_holder": True}
    return {"released_stale_holder": False,
            "stale_holder_note": (
                "殘留 holder release 失敗——檔案保留作 evidence"
                f"（token {saved['token']}）")}


def mark_read(address, envelope_id, runner, state_dir=None,
              note=None, target=None):
    """S2 標已讀（一次一封）→ result dict。

    順序（裁定算法）：輸入驗證 → mail get 原文在場性驗證 → 已 ACK 重看
    短路（不消費）→ 待回覆先持久（ACK 前；失敗＝no-ACK）→ 自家短 holder
    取得（活 holder 無條件拒）→ prepare max-count=1 前綴精確驗證（錯位＝
    no-ACK/no-skip）→ ACK → 只釋放自家 token。

    不調 legacy process_once／_prepare_with_recovery／disposition sinks。
    任一失敗保留 pending＋evidence 並 raise（CLI 面非零；無 fail-soft）。
    """
    if not isinstance(address, str) or not address:
        raise S2Error("address 須為非空字串", 2)
    if not isinstance(envelope_id, str) or not envelope_id:
        raise S2Error("envelope id 須為非空字串", 2)
    if (note is None) != (target is None):
        raise S2Error("note 與 target 須雙給（回覆需要兩者）或雙無", 2)
    if note is not None and (
        not isinstance(note, str) or not note
        or not isinstance(target, str) or not target
    ):
        raise S2Error("note/target 須為非空字串", 2)
    result = mail_get(runner, address, envelope_id)
    item = result.get("item")
    if not isinstance(item, dict):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"mail get 缺 item：{sorted(result) if isinstance(result, dict) else result!r}",
            False, 0,
        )
    if item.get("envelopeId") != envelope_id:
        # ID echo 檢查（與 send_reply incoming 對稱）：回應與查詢不符＝
        # 對象不明——禁 ACK、禁任何持久化/holder 動作。
        raise S2Error(
            f"mail get ID 不符（查詢 {envelope_id!r}≠回 "
            f"{item.get('envelopeId')!r}）——禁 ACK、不動任何狀態"
        )
    env, absence = decode_canonical_item(item)
    if absence is not None:
        raise S2Error(f"{envelope_id}：{absence}")
    if item.get("deliverySeq") is None:
        raise S2Error(
            f"{envelope_id}：unslotted 歷史列（deliverySeq null，只在 box "
            "all 可見）——非 pending 前綴、禁 ACK；請以 show 重看原文"
        )
    pending_flag = item.get("pending")
    if pending_flag is False:
        # 已 ACK 重看：不消費（零 holder 取得／prepare／ack）。有 note 仍
        # 記義務；無 note 永不清除既有義務（只讀）。進短路前清自家殘留
        # holder（前次 release 前崩潰遺留——best-effort，失敗保留揭露）。
        reread_extra = _clear_stale_holder_on_reread(
            address, runner, state_dir)
        if note is not None:
            try:
                with _pending_lock(address, state_dir):
                    doc = _pending_ensure(address, state_dir)
                    entry = doc["replies"].get(envelope_id)
                    if not isinstance(entry, dict):
                        entry = {}
                    entry["note"] = note
                    entry["target"] = target
                    entry.setdefault(
                        "created_at_iso",
                        datetime.now(UTC).isoformat(timespec="seconds"))
                    entry.setdefault("reply_envelope_id", None)
                    entry.setdefault("reply_sha256", None)
                    doc["replies"][envelope_id] = entry
                    save_pending_replies(
                        pending_path(address, state_dir), doc)
            except OSError as exc:
                raise S2Error(f"待回覆寫入失敗——未更動（{exc!r}）") from exc
            out = {"envelope_id": envelope_id, "acked": False,
                   "reread": True, "pending": True, "envelope": env}
            out.update(reread_extra)
            return out
        out = {"envelope_id": envelope_id, "acked": False,
               "reread": True, "pending": False, "envelope": env}
        out.update(reread_extra)
        return out
    if pending_flag is not True:
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"mail item pending 非布林：{pending_flag!r}", False, 0,
        )
    # pending 前綴成員：先持久（note 有則記義務；無則僅建空骨架——失敗
    # 即 no-ACK），再短持有消費。
    try:
        with _pending_lock(address, state_dir):
            _pending_ensure(address, state_dir)
    except OSError as exc:
        raise S2Error(
            f"待回覆檔寫入失敗——no-ACK（{exc!r}）") from exc
    if note is not None:
        try:
            _pending_upsert_note(
                address, state_dir, envelope_id, note, target)
        except OSError as exc:
            raise S2Error(
                f"待回覆寫入失敗——no-ACK（{exc!r}）") from exc
    # 同 repo consume 段短鎖：holder 取得→save→prepare→ACK→release 整段
    # 序列化——兩個並行 mark_read 不再交錯 token（第二個進鎖時看到第一個
    # 的終態）。段內禁呼叫任何再取 _pending_lock 的函式（fcntl 非重入，
    # 自我死鎖）：note 寫入在段外、_mark_read_with_token 只動 holder 檔
    # 與 transport、_save/_load_inbox_holder 不取鎖——保持此性質。
    with _pending_lock(address, state_dir):
        saved = _load_inbox_holder(address, state_dir)
        if saved is not None:
            return _mark_read_with_token(
                address, envelope_id, env, runner, state_dir,
                saved["token"], saved["epoch"])
        try:
            token, epoch = _s2_bind_no_takeover(runner, address)
        except (S2Error, DutymailFaceError, BinaryMissing):
            raise
        try:
            _save_inbox_holder(address, state_dir, epoch, token)
        except OSError as exc:
            # release 結果誠實回報：失敗時 holder 可能殘留 active——token
            # 完整揭露作人工恢復證據，禁宣稱已釋放。
            if _s2_release_best_effort(runner, address, token):
                raise S2Error(
                    f"holder 存檔失敗——已釋放剛取得的 token（不靜默失權；"
                    f"pending 已保留；{exc!r}）") from exc
            raise S2Error(
                "holder 存檔失敗——release 亦失敗——holder 可能殘留 "
                f"active；token＝{token}（保留作人工恢復證據）；pending "
                f"已保留；{exc!r}") from exc
        return _mark_read_with_token(
            address, envelope_id, env, runner, state_dir, token, epoch)


def _mark_read_with_token(address, envelope_id, env, runner, state_dir,
                          token, epoch):
    """持自家 token 的單封消費（prepare 1 → 驗 ID → ACK → 只釋放自家）。
    失敗保留 pending＋evidence（holder 檔僅釋放成功才刪）。"""
    try:
        prepared = receive_prepare(
            runner, address, token, max_count=1)
    except DutymailFaceError as exc:
        if _is_fencing(exc):
            # 自家舊 token 被證 stale（他方已推進）——只清已證 stale 的自家
            # 檔，不猜 ownership、不搶；下一次顯式操作重試。
            try:
                os.remove(inbox_holder_path(address, state_dir))
            except OSError:
                pass
            raise S2Error(
                f"自家 holder 已 stale（{exc.code}）——已清自家狀態、未搶；"
                "pending 已保留，請稍後顯式重試") from exc
        if _s2_release_best_effort(runner, address, token):
            _clear_inbox_holder(address, state_dir)
        raise S2Error(f"prepare 失敗——no-ACK（pending 已保留；{exc}）"
                      ) from exc
    envelopes = prepared.get("envelopes")
    batch_token = prepared.get("batchToken")
    head_id = (
        envelopes[0].get("envelopeId")
        if isinstance(envelopes, list) and envelopes
        and isinstance(envelopes[0], dict) else None
    )
    if (
        not isinstance(envelopes, list) or not envelopes
        or not (isinstance(batch_token, str) and batch_token)
        or head_id != envelope_id
    ):
        if _s2_release_best_effort(runner, address, token):
            _clear_inbox_holder(address, state_dir)
        raise S2Error(
            f"前綴不符——no-ACK/no-skip：pending 頭是 {head_id!r}，本次實際"
            f"讀過的是 {envelope_id!r}；未跳過任何信（pending＋原信保留）"
        )
    try:
        receive_ack(runner, address, token, batch_token)
    except DutymailFaceError as exc:
        if _s2_release_best_effort(runner, address, token):
            _clear_inbox_holder(address, state_dir)
        # ACK 錯誤＝outcome unknown（transport 可能已提交、回應遺失）
        # ——唯讀重查定界，禁宣稱「cursor 未前進」。本段在 consume 短鎖
        # 內，同 repo 無並行消費者可插隊——重查結果可信。
        try:
            recheck = mail_get(runner, address, envelope_id)
            re_item = recheck.get("item")
            if isinstance(re_item, dict) and re_item.get("pending") is False:
                # ACK 已提交（回應遺失）——committed，非錯誤。
                return {"envelope_id": envelope_id, "acked": True,
                        "reread": False, "pending": False,
                        "envelope": env, "ack_outcome": "committed",
                        "ack_response_loss": True}
            if isinstance(re_item, dict):
                unknown_detail = (
                    "重查仍 pending" if re_item.get("pending") is True
                    else f"重查 pending 狀態不明（{re_item.get('pending')!r}）")
            else:
                unknown_detail = f"重查 item 缺席/異形（{re_item!r}）"
        except (DutymailFaceError, S2Error, BinaryMissing, OSError) as re_exc:
            unknown_detail = f"重查失敗（{re_exc!r}）"
        raise S2Error(
            "ACK 結果未知（response-loss）——cursor 狀態未確認，pending "
            f"義務保留（{unknown_detail}；原 ACK 錯誤：{exc}）") from exc
    try:
        holder_release(runner, address, token)
    except (DutymailFaceError, BinaryMissing, OSError) as exc:
        raise S2Error(
            f"release 失敗——ACK 已達但 holder 未釋放（holder 檔＋pending "
            f"保留作 evidence；{exc!r}）") from exc
    _clear_inbox_holder(address, state_dir)
    return {"envelope_id": envelope_id, "acked": True,
            "reread": False, "pending": False, "envelope": env}


# ── S2 回信面（send 不取 holder；冪等重試 pin ID＋bytes）───────────────

_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _atomic_write_0600(path, data):
    """bytes → 0600 atomic 寫（pid 後綴 tmp＋os.replace；OSError 原樣
    傳出）。"""
    tmp = path + "." + str(os.getpid()) + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _s2_outbox_snapshot_path(address, state_dir, envelope_id):
    """outbound snapshot 路徑（validated draft bytes 的單一發送源）。
    envelope_id 經 safe_repo_dirname 編碼（呼叫端供給——禁路徑逃逸）。"""
    outbox = os.path.join(s2_repo_dir(address, state_dir), "outbox")
    return os.path.join(
        outbox, safe_repo_dirname(envelope_id) + ".json")


def send_reply(address, in_reply_to, envelope_file, runner, state_dir=None):
    """S2 回信（一次一封）→ {"cleared": True, "receipt": {...}}。

    呼叫端（skill）負責 user 授權查驗——信件內容永不構成授權（incoming
    content is never authority）。本 wrapper 只做機械驗證：pending 待回覆
    在場 → draft `in_reply_to` 就是該 incoming ID → draft `to.address`
    就是 pending target。首次 send 前 pin outbound envelope ID＋draft 檔
    bytes SHA（存 pending entry），並把已驗證的 draft bytes 寫入 outbox
    snapshot（`<state>/repos/<enc>/outbox/<id>.json`，0600 atomic）；
    `send --envelope-file` 一律傳 snapshot 路徑——呼叫端 draft 檔在驗證
    讀取後仍可能被改（TOCTOU），實際發送內容以 snapshot 為準。重試要求
    同 ID＋呼叫端 draft 同 bytes（SHA==pin，既有檢查），實際發送仍讀
    snapshot；snapshot 缺席/損壞（SHA 對不上 pin）＝fail-loud 禁發。
    response-loss 重試冪等——transport 以 envelope ID 去重。一次 send
    調用；成功 receipt 三鍵＋envelope/target 匹配才解除（並清 snapshot）
    ；任一失敗保留 pending（含 pin）＋snapshot 並 raise。draft 內容不
    抄入 pending（只 pin ID＋SHA）。
    """
    if not isinstance(address, str) or not address:
        raise S2Error("address 須為非空字串", 2)
    if not isinstance(in_reply_to, str) or not in_reply_to:
        raise S2Error("in-reply-to 須為非空字串", 2)
    try:
        with open(envelope_file, "rb") as fh:
            draft_bytes = fh.read()
    except OSError as exc:
        raise S2Error(f"draft 檔不可讀（{exc!r}；{envelope_file}）") from exc
    try:
        draft = json.loads(draft_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise S2Error(f"draft 非 UTF-8 JSON（{exc!r}）") from exc
    if not isinstance(draft, dict):
        raise S2Error("draft 非 JSON object")
    draft_sha = _s2_hashlib.sha256(draft_bytes).hexdigest()
    # 實際 incoming 存在性（mail get；unknown-message 即 fail-loud）。
    incoming = mail_get(runner, address, in_reply_to)
    in_item = incoming.get("item")
    if not isinstance(in_item, dict):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"mail get 缺 item：{in_reply_to}", False, 0,
        )
    if in_item.get("envelopeId") != in_reply_to:
        raise S2Error(
            f"incoming ID 不符（查詢 {in_reply_to!r}≠回 {in_item.get('envelopeId')!r}）"
        )
    with _pending_lock(address, state_dir):
        path = pending_path(address, state_dir)
        doc = load_pending_replies(path)
        if doc is None or not isinstance(
                doc.get("replies", {}).get(in_reply_to), dict):
            raise S2Error(
                f"無待回覆 {in_reply_to}——先 mark-read 記義務再回信")
        entry = doc["replies"][in_reply_to]
        target = entry.get("target")
        if not isinstance(target, str) or not target:
            raise S2Error(f"待回覆 {in_reply_to} 無 reply target——禁發送")
        # draft 欄位驗證（在 pin 比對之後取 ID——changed-bytes 優先報）：
        pinned_id = entry.get("reply_envelope_id")
        pinned_sha = entry.get("reply_sha256")
        if pinned_id is not None or pinned_sha is not None:
            if draft_sha != pinned_sha or not isinstance(pinned_sha, str):
                raise S2Error(
                    "draft bytes 已變更（SHA 不符首次 pin）——重試必須同一"
                    "實物；要換內容請先以新 draft 重新走授權流程")
            draft_id_check = draft.get("envelope_id")
            if draft_id_check != pinned_id:
                raise S2Error(
                    f"draft envelope ID 已變更（{draft_id_check!r}≠pin "
                    f"{pinned_id!r}）——重試必須同一 ID")
        draft_id = draft.get("envelope_id")
        if not isinstance(draft_id, str) or not draft_id:
            raise S2Error("draft 缺 envelope_id（非空字串）")
        if draft.get("in_reply_to") != in_reply_to:
            raise S2Error(
                f"draft in_reply_to（{draft.get('in_reply_to')!r}）≠待回覆 "
                f"{in_reply_to!r}——禁發送")
        to_block = draft.get("to")
        to_addr = to_block.get("address") if isinstance(to_block, dict) else None
        if to_addr != target:
            raise S2Error(
                f"draft 收件（{to_addr!r}）≠待回覆 target（{target!r}）——禁發送")
        snapshot_path = _s2_outbox_snapshot_path(
            address, state_dir, draft_id)
        if pinned_id is None and pinned_sha is None:
            # 首次 send 前 pin（同一臨界段內、send 前）：先寫 snapshot
            # （validated bytes）、後寫 pin——pin 成功蘊含 snapshot 在場
            # （snapshot 寫入失敗＝未發送、未 pin，狀態乾淨可重來）。
            try:
                os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
                _atomic_write_0600(snapshot_path, draft_bytes)
            except OSError as exc:
                raise S2Error(
                    f"outbox snapshot 寫入失敗——未發送、未 pin（{exc!r}）"
                ) from exc
            entry["reply_envelope_id"] = draft_id
            entry["reply_sha256"] = draft_sha
            doc["replies"][in_reply_to] = entry
            try:
                save_pending_replies(path, doc)
            except OSError as exc:
                raise S2Error(
                    f"reply pin 寫入失敗——未發送（{exc!r}）") from exc
        else:
            # 重試：呼叫端 draft 檔已過 SHA==pin 對帳（上）；實際發送
            # 內容以 snapshot 為準——缺席/損壞＝fail-loud 禁發。
            try:
                with open(snapshot_path, "rb") as fh:
                    snap_bytes = fh.read()
            except OSError as exc:
                raise S2Error(
                    "outbox snapshot 缺席/不可讀——禁發（fail-loud；"
                    f"{exc!r}；路徑 {snapshot_path}）") from exc
            if _s2_hashlib.sha256(snap_bytes).hexdigest() != pinned_sha:
                raise S2Error(
                    "outbox snapshot 損壞（SHA 對不上 pin 記錄）——禁發"
                    "（fail-loud）")
        try:
            receipt = _call(
                runner, ["send", "--envelope-file", snapshot_path])
        except (DutymailFaceError, BinaryMissing, OSError) as exc:
            raise S2Error(
                f"send 失敗——pending 保留（含 pin，同 draft 可重試；{exc!r}）"
            ) from exc
        # 成功 receipt 驗證：envelopeId 匹配、acceptanceSeq 正、SHA 形合法。
        # Server SHA 是 canonical-envelope SHA——禁與 draft 檔 pretty-JSON
        # SHA 比對（只驗形狀）。
        if not isinstance(receipt, dict):
            raise S2Error(f"send receipt 非 object——pending 保留（{receipt!r}）")
        if receipt.get("envelopeId") != draft_id:
            raise S2Error(
                f"receipt envelopeId（{receipt.get('envelopeId')!r}）≠draft "
                f"（{draft_id!r}）——pending 保留")
        acc_seq = receipt.get("acceptanceSeq")
        if not _positive_int(acc_seq):
            raise S2Error(
                f"receipt acceptanceSeq 非正整數（{acc_seq!r}）——pending 保留")
        srv_sha = receipt.get("envelopeSha256")
        if not (isinstance(srv_sha, str) and _SHA256_HEX_RE.match(srv_sha)):
            raise S2Error(
                f"receipt envelopeSha256 形非法（{srv_sha!r}）——pending 保留")
        _pending_clear_reply(address, state_dir, in_reply_to)
        try:
            os.remove(snapshot_path)
        except FileNotFoundError:
            pass
        return {"cleared": True, "receipt": receipt}


# ── CLI 面（模組＋CLI；hook 前導為 hooks/duty_receive.py）────────────


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_CONFIG_PATH = os.path.join(
    _repo_root(), "governance", "dutymail-processor.toml"
)


def _load_disposition_sinks(session_id, base_dir=None):
    """AIR-287 接線：以檔案路徑載入 sibling duty_disposition（與 hook
    前導同模式——scripts/ 非 package，CLI 直跑時 sys.path[0]＝scripts/
    但 load_module 測試形態不在，一律顯式路徑載入零歧義）→
    (received sink, resolution sink) 兩 safe callable——received＝
    收信記帳、resolution＝digest 呈現完成邊界推進（auto→handled／
    surface→needs-human；AIR-287 bi 修復必修 1）。載入失敗＝
    (None, None)＋stderr 一行（記帳面故障不擋收信——缺口大聲，信件
    損失 > ledger 缺口）。"""
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_duty_disposition_core",
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "duty_disposition.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return (
            mod.make_received_sink(session_id, base_dir=base_dir),
            mod.make_resolution_sink(session_id, base_dir=base_dir),
        )
    except Exception as exc:
        print(
            f"[{HOOK_TAG}] disposition ledger 載入失敗——本批不記帳"
            f"（{exc!r}）",
            file=sys.stderr,
        )
        return None, None


def _s2_runner(store_root):
    """store 隔離 runner（--store-root 顯式透傳；None＝預設 ~/.dutymail——
    測試恆顯式隔離，禁預設真 store）。"""

    def run(argv):
        if store_root:
            return _default_runner(
                ["--store-root", store_root] + list(argv))
        return _default_runner(list(argv))

    return run


def _resolve_s2_address(requested):
    """S2 身份解析 → canonical alias。requested 省略＝呼叫端身份；給定須
    exact-match（錯址＝S2Error exit 2，呼叫端在任何 side effect 前檢查—
    —含唯讀面）。身份無法判定＝S2Error exit 3。呼叫端 cwd 保持（禁 cd）。
    """
    try:
        canonical = caller_repo_address()
    except ConfigError as exc:
        raise S2Error(f"呼叫端 repo 身份無法判定——不消費（{exc}）", 3)
    if requested is not None and requested != canonical:
        raise S2Error(
            f"address 屬他 repo custody——禁動作：{requested}（本 repo "
            f"canonical＝{canonical}，exact match）", 2)
    return canonical


def _render_inbox_items(alias, box, result):
    """mail list result → stdout 行（全文＋body string 完整＋cursor 保留；
    缺席明示）。"""
    lines = []
    items = result.get("items")
    if not isinstance(items, list):
        raise S2Error(f"mail list 缺 items：{sorted(result)}")
    lines.append(
        f"[duty-inbox] {alias} box={result.get('box', box)} "
        f"items={len(items)} primaryCursor={result.get('primaryCursor')}")
    for item in items:
        if not isinstance(item, dict):
            lines.append("[duty-inbox] item 非 object（明示略過 1 列）")
            continue
        eid = item.get("envelopeId", "unknown")
        env, absence = decode_canonical_item(item)
        if absence is not None:
            lines.append(
                f"[duty-inbox] {eid} acceptanceSeq={item.get('acceptanceSeq')} "
                f"deliverySeq={item.get('deliverySeq')} "
                f"pending={item.get('pending')} {absence}")
            continue
        lines.append(
            f"[duty-inbox] {eid} acceptanceSeq={item.get('acceptanceSeq')} "
            f"deliverySeq={item.get('deliverySeq')} "
            f"pending={item.get('pending')} "
            f"from={json.dumps(env.get('from'), ensure_ascii=False)} "
            f"created_at_us={env.get('created_at_us')}")
        lines.append(f"body: {env.get('body')}")
    nxt = result.get("nextCursor")
    lines.append(
        f"[duty-inbox] nextCursor={nxt if isinstance(nxt, str) and nxt else 'null'}")
    return lines


def _render_show_item(alias, result):
    item = result.get("item")
    if not isinstance(item, dict):
        raise S2Error(f"mail get 缺 item：{sorted(result)}")
    env, absence = decode_canonical_item(item)
    eid = item.get("envelopeId", "unknown")
    if absence is not None:
        return [f"[duty-inbox] {alias} {eid} {absence}"]
    return [
        f"[duty-inbox] {alias} {eid} "
        f"acceptanceSeq={item.get('acceptanceSeq')} "
        f"deliverySeq={item.get('deliverySeq')} pending={item.get('pending')} "
        f"primaryCursor={result.get('primaryCursor')}",
        f"envelope: {json.dumps(env, ensure_ascii=False)}",
        f"body: {env.get('body')}",
    ]


def _cmd_inbox(args):
    try:
        address = _resolve_s2_address(args.address)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    runner = _s2_runner(args.store_root)
    try:
        result = mail_list(
            runner, address, box=args.box, cursor=args.cursor,
            limit=args.limit)
        for line in _render_inbox_items(address, args.box, result):
            print(line)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    except (DutymailFaceError, BinaryMissing) as exc:
        print(f"[duty-inbox] transport 失敗：{exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_show(args):
    try:
        address = _resolve_s2_address(args.address)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    runner = _s2_runner(args.store_root)
    try:
        result = mail_get(runner, address, args.envelope_id)
        for line in _render_show_item(address, result):
            print(line)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    except (DutymailFaceError, BinaryMissing) as exc:
        print(f"[duty-inbox] transport 失敗：{exc}", file=sys.stderr)
        return 1
    return 0


def _cmd_pending_replies(args):
    try:
        address = _resolve_s2_address(args.address)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    try:
        doc = load_pending_replies(pending_path(address, args.state_dir))
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    replies = doc.get("replies", {}) if doc else {}
    if not replies:
        print(f"[duty-inbox] {address}：無待回覆")
        return 0
    print(f"[duty-inbox] {address}：待回覆 {len(replies)} 件")
    for eid in sorted(replies):
        entry = replies[eid] if isinstance(replies[eid], dict) else {}
        print(
            f"[duty-inbox] {eid} note={entry.get('note', '')!r} "
            f"target={entry.get('target', '')!r}")
    return 0


def _cmd_mark_read(args):
    try:
        address = _resolve_s2_address(args.address)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    runner = _s2_runner(args.store_root)
    try:
        out = mark_read(
            address, args.envelope_id, runner, state_dir=args.state_dir,
            note=args.note, target=args.target)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    except (DutymailFaceError, BinaryMissing) as exc:
        print(f"[duty-inbox] transport 失敗——pending 已保留：{exc}",
              file=sys.stderr)
        return 1
    if out["acked"]:
        loss = ("（ACK 回應遺失——唯讀重查確認已提交）"
                if out.get("ack_response_loss") else "")
        print(f"[duty-inbox] {address}：已標已讀 {out['envelope_id']}"
              f"（原信留原處可重看）{loss}")
    elif out.get("pending"):
        print(f"[duty-inbox] {address}：重看 {out['envelope_id']}"
              "（已 ACK 歷史，不再消費；待回覆已記）")
    else:
        print(f"[duty-inbox] {address}：重看 {out['envelope_id']}"
              "（已 ACK 歷史，不再消費）")
    if out.get("released_stale_holder"):
        print(f"[duty-inbox] {address}：已清殘留 holder（前次崩潰遺留）")
    if out.get("stale_holder_note"):
        print(f"[duty-inbox] {address}：{out['stale_holder_note']}",
              file=sys.stderr)
    return 0


def _cmd_reply(args):
    try:
        address = _resolve_s2_address(args.address)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    runner = _s2_runner(args.store_root)
    try:
        out = send_reply(
            address, args.in_reply_to, args.envelope_file, runner,
            state_dir=args.state_dir)
    except S2Error as exc:
        print(f"[duty-inbox] {exc}", file=sys.stderr)
        return exc.exit_code
    except (DutymailFaceError, BinaryMissing) as exc:
        print(f"[duty-inbox] transport 失敗——pending 已保留：{exc}",
              file=sys.stderr)
        return 1
    receipt = out["receipt"]
    print(f"[duty-inbox] {address}：回信已受理 {receipt.get('envelopeId')} "
          f"（acceptanceSeq={receipt.get('acceptanceSeq')}；待回覆已解除）")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail 值星收信處理器（AIR-254.3；模組＋CLI——v1 不觸達"
            " send／replies 面）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    proc = sub.add_parser(
        "process",
        help="單次收信週期：ensure_holder→prepare→triage→ack（digest＋surface 行）",
    )
    proc.add_argument(
        "--address", required=True, metavar="ALIAS",
        help="門牌 alias（exact match canonical repo 身份，例 ai-guide）",
    )
    proc.add_argument(
        "--session-id", required=True, metavar="ID",
        help="holder state 檔 key（per-session；CLI 無 stdin payload 須顯式）",
    )
    proc.add_argument(
        "--config", default=DEFAULT_CONFIG_PATH, metavar="PATH",
        help="分診表路徑（預設 governance/dutymail-processor.toml）",
    )
    proc.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="state 目錄覆寫（預設 XDG state／~/.local/state）",
    )
    proc.add_argument(
        "--disposition-dir", default=None, metavar="DIR",
        help="disposition ledger 根覆寫（AIR-287；預設 XDG state）",
    )
    proc.add_argument(
        "--no-disposition-ledger", action="store_true",
        help="本批不記 disposition 帳（預設記——AIR-287 接線）",
    )
    proc.add_argument(
        "--max-count", type=int, default=DEFAULT_MAX_COUNT, metavar="N",
        help=f"單批上限（預設 {DEFAULT_MAX_COUNT}，bounded）",
    )
    proc.add_argument(
        "--store-root", default=None, metavar="DIR",
        help="dutymail store 根覆寫（預設 ~/.dutymail；測試恆顯式隔離）",
    )
    # ── S2 ordinary inbox（AIR-312 S2：小 CLI 面）──────────────────
    ib = sub.add_parser(
        "inbox",
        help="讀信箱歷史（預設 pending；all/acked＋分頁；全文＋cursor）",
    )
    ib.add_argument("--address", default=None, metavar="ALIAS",
                    help="門牌（省略＝呼叫端 repo 身份；給定須 exact-match）")
    ib.add_argument("--box", default="pending",
                    choices=("pending", "all", "acked"),
                    help="讀寫推導盒（預設 pending）")
    ib.add_argument("--cursor", default=None, metavar="TOKEN",
                    help="分頁 cursor（省略＝首頁；沿用上頁 nextCursor）")
    ib.add_argument("--limit", default=None, type=int, metavar="N",
                    help="頁大小（省略＝server 預設）")
    ib.add_argument("--store-root", default=None, metavar="DIR",
                    help="dutymail store 根覆寫（測試恆顯式隔離）")
    sh = sub.add_parser("show", help="看一封（envelope 全文＋body 完整）")
    sh.add_argument("--envelope-id", required=True, metavar="ID")
    sh.add_argument("--address", default=None, metavar="ALIAS",
                    help="門牌（省略＝呼叫端 repo 身份；給定須 exact-match）")
    sh.add_argument("--store-root", default=None, metavar="DIR")
    pr = sub.add_parser("pending-replies", help="列待回覆（最小 ID/note/target）")
    pr.add_argument("--address", default=None, metavar="ALIAS",
                    help="門牌（省略＝呼叫端 repo 身份；給定須 exact-match）")
    pr.add_argument("--state-dir", default=None, metavar="DIR",
                    help="S2 state 根覆寫（預設 XDG；測試隔離用）")
    mr = sub.add_parser("mark-read", help="標已讀（一次一封；先記義務再 ACK）")
    mr.add_argument("--envelope-id", required=True, metavar="ID")
    mr.add_argument("--note", default=None, metavar="TEXT",
                    help="待回覆記事（與 --target 雙給）")
    mr.add_argument("--target", default=None, metavar="ALIAS",
                    help="回覆目標門牌（與 --note 雙給）")
    mr.add_argument("--address", default=None, metavar="ALIAS",
                    help="門牌（省略＝呼叫端 repo 身份；給定須 exact-match）")
    mr.add_argument("--store-root", default=None, metavar="DIR")
    mr.add_argument("--state-dir", default=None, metavar="DIR",
                    help="S2 state 根覆寫（預設 XDG；測試隔離用）")
    rp = sub.add_parser("reply", help="回信（pending 義務＋持久 draft 冪等）")
    rp.add_argument("--in-reply-to", required=True, metavar="ID",
                    help="待回覆 incoming envelope ID")
    rp.add_argument("--envelope-file", required=True, metavar="PATH",
                    help="持久 outbound draft 檔（pin ID＋bytes 重試）")
    rp.add_argument("--address", default=None, metavar="ALIAS",
                    help="門牌（省略＝呼叫端 repo 身份；給定須 exact-match）")
    rp.add_argument("--store-root", default=None, metavar="DIR")
    rp.add_argument("--state-dir", default=None, metavar="DIR",
                    help="S2 state 根覆寫（預設 XDG；測試隔離用）")
    return parser.parse_args(argv)


def _process_runner(store_root):
    """legacy process 面的 store 隔離 runner（預設行為零變）。"""

    def run(argv):
        if store_root:
            return _default_runner(
                ["--store-root", store_root] + list(argv))
        return _default_runner(list(argv))

    return run


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.command in ("inbox", "show", "pending-replies",
                        "mark-read", "reply"):
        return {
            "inbox": _cmd_inbox, "show": _cmd_show,
            "pending-replies": _cmd_pending_replies,
            "mark-read": _cmd_mark_read, "reply": _cmd_reply,
        }[args.command](args)
    try:
        policy = load_policy(args.config)
    except ConfigError as exc:
        print(f"[{HOOK_TAG}] config fail-loud：{exc}", file=sys.stderr)
        return 3
    # 跨址 custody fence 第一層（AIR-312 repo 身份制）：入口 arg 驗證
    # ——requested address ≠ 呼叫端 repo canonical alias＝他 repo
    # custody，禁消費（第二層＝process_once bind 前核心閘；此處先擋，
    # 零副作用退出。canonical 單一源＝caller_repo_address——見
    # load_policy；非 git cwd／bare／無法判定已在 load_policy 面以
    # ConfigError exit 3 deny-all）。
    if args.address not in policy.consume_addresses:
        print(
            f"[{HOOK_TAG}] address 屬他 repo custody——禁消費："
            f"{args.address}（canonical alias＝呼叫端 repo 身份——git "
            f"common-dir 反推 primary root basename，exact match）",
            file=sys.stderr,
        )
        return 2
    sfile = state_path(args.session_id, args.state_dir)
    recv_sink, res_sink = (
        (None, None) if args.no_disposition_ledger
        else _load_disposition_sinks(
            args.session_id, base_dir=args.disposition_dir
        )
    )
    try:
        lines, commit = process_once(
            args.address, _process_runner(args.store_root), policy, sfile,
            max_count=args.max_count, disposition_sink=recv_sink,
            resolution_sink=res_sink,
        )
    except HolderConflict as exc:
        print(f"[{HOOK_TAG}] {exc}")  # surface 衝突（同 hook 語義）
        return 0
    except DutymailFaceError as exc:
        if exc.is_storage:
            print(
                f"[{HOOK_TAG}] store 缺席（pre-migration）fail-soft"
                f"——{exc}",
                file=sys.stderr,
            )
            return 0
        print(f"[{HOOK_TAG}] dutymail face 失敗：{exc}", file=sys.stderr)
        return 1
    except CustodyFenceError as exc:
        # 深防線（常態不可達——入口已擋）：閘語義恆 exit 2。
        print(f"[{HOOK_TAG}] {exc}", file=sys.stderr)
        return 2
    except BinaryMissing as exc:
        # AIR-274 M1：環境壞 typed 訊息＋exit 1（不再 generic traceback）。
        print(f"[{HOOK_TAG}] binary missing：{exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    if commit is not None:
        try:
            commit()
        except DutymailFaceError as exc:
            print(
                f"[{HOOK_TAG}] ack 失敗——state 保留處置紀錄，下輪先試"
                f" ack（{exc}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
