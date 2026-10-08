#!/usr/bin/env python3
"""dutymail 值星收信處理器核心（AIR-254.3 S1——模組＋CLI）。

職責：在 SessionStart／UserPromptSubmit 邊界（值星在場時），以
epoch-fenced holder 身分對 per-repo mailbox（alias＝exact alias，如
ai-guide-marshal）執行一個完整收信週期——`holder` 面取權威 →
`receive prepare` 取 bounded 批次 → 逐封 triage → 全部處置完才
`receive ack`。輸出＝digest 行＋surface 一行摘要（hook 層包成
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
  active（3.8.0 bound／3.7.0 live）在場＝不搶（換代正當路徑＝對方釋
  放後 rebind）；rebind CAS 失敗＝HolderConflict（surface 衝突訊息、
  單次嘗試、不重試轟炸）。AIR-288：3.8.0 renew 面拔除（authority 無
  時鐘）——token 有效至被 fence，fencing 交 prepare 既有 rebind 路徑。
- holder state（bearer token）存 per-session 檔 0600、atomic 寫、
  路徑可注入（測試 fake state，不碰真 store）。
- v1 絕不主動送信：本檔不觸達 send／replies 面（回信＝outward，須
  逐次 AUTH，非本處理器範圍）。

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
FENCING_CODES = frozenset({"stale-epoch", "holder-token-mismatch"})
RETIRED_FENCING_CODES = frozenset({"lease-expired"})
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
    rebind 路徑。消費面限 prepare/ack 錯誤：`epoch-conflict`（同屬
    class 5）只在 bind CAS 面出現，由 `_bind_fresh` 攔下轉
    HolderConflict，不到這裡。"""
    return exc.error_class == "fencing"


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


def _resolve_binary():
    env_bin = os.environ.get(RUNNER_ENV)
    if env_bin:
        return env_bin
    on_path = shutil.which("dutymail")
    if on_path:
        return on_path
    # cache rungs 依序（zcode 先、claude 後——既有優先序零變，AIR-273
    # 第四 rung 只在 candidates 追加）；每 rung 內取版本最新。
    for base in (PLUGIN_CACHE_BASE, CLAUDE_PLUGIN_CACHE_BASE):
        candidates = glob.glob(
            os.path.join(os.path.expanduser(base), PLUGIN_BIN_PATTERN)
        )
        if candidates:
            return max(candidates, key=_version_key)
    raise BinaryMissing(
        "dutymail binary not found（" + RUNNER_ENV
        + " / PATH / zcode・claude plugin cache 皆缺席）"
    )


def _default_runner(argv):
    """真實 dutymail 呼叫（無 shell）；非零 exit＝解析 stderr typed
    failure 成 DutymailFaceError raise（fail-soft 由上層吸收）。"""
    proc = subprocess.run(
        [_resolve_binary()] + list(argv),
        capture_output=True,
        text=True,
        timeout=DUTYMAIL_TIMEOUT_SECONDS,
        check=False,
    )
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
    窗口 binary 是哪版都同判定）。雙缺席＝False（同既有 `live` 缺席
    容忍面——bind CAS 為最後防線）；值非 `True`（None 等）不誤判。"""
    return status.get("bound", status.get("live")) is True


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
    恒 deny；列為 auto 需 intent 在該 class 的 auto_intent 內。"""

    def __init__(self, rules):
        self._rules = rules  # class -> (action, frozenset(auto_intent))

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


def load_policy(path):
    """載入分診表 → Policy。缺席／TOML 壞形／未知鍵／壞值一律
    ConfigError（呼叫端 fail-loud exit 3——不靜默全 surface）。"""
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
            f"分診表未知頂層鍵：{sorted(extra)}（僅允許 class_rule）"
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
    return Policy(rules)


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
    rebind、同樣過 active 閘）。rebind CAS 失敗（epoch-conflict，race
    window 内他方先 bind）＝HolderConflict。storage 錯誤原樣傳出（上層
    fail-soft pre-migration）。
    """
    st = load_state(state_file)
    if _valid_holder_state(st, address):
        return st
    return _bind_fresh(address, runner, state_file)


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
    # 正當路徑＝對方釋放（3.8.0：binding 變更；3.7.0：lease 到期）後
    # rebind。CAS（epoch-conflict）保留為 status 與 bind 之間 race
    # window 的最後防線。「active=True 且 epoch==我 state epoch」（我方
    # token 失效邊角）經此同一規則落衝突不搶——對方釋放後自癒，信不丟
    # （prepare 不消耗）。
    if holder_active(observed):
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
    回原 receipt）；批次已死（expired/fenced/invalidated）或 token 已
    fenced → 清記錄落 fresh prepare；storage 等其他失敗 → 保留紀錄
    （prepare 稍後自然失敗，交上層 fail-soft）。未處置 → 不代 ack，
    回 invalidate_next=True（寧重不漏：prepare --invalidate 重 prepare）。
    """
    batch_token = st.get("batch_token")
    if not isinstance(batch_token, str) or not batch_token:
        return st, False
    if st.get("batch_disposed") is True:
        try:
            receive_ack(runner, address, st["token"], batch_token)
        except DutymailFaceError as exc:
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
    → status→rebind→以新 token 重試一次（舊批隨 rebind 自動 fenced）。"""
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
    """
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
        help="門牌 alias（exact match，例 ai-guide-marshal）",
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
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        policy = load_policy(args.config)
    except ConfigError as exc:
        print(f"[{HOOK_TAG}] config fail-loud：{exc}", file=sys.stderr)
        return 3
    sfile = state_path(args.session_id, args.state_dir)
    recv_sink, res_sink = (
        (None, None) if args.no_disposition_ledger
        else _load_disposition_sinks(
            args.session_id, base_dir=args.disposition_dir
        )
    )
    try:
        lines, commit = process_once(
            args.address, _default_runner, policy, sfile,
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
