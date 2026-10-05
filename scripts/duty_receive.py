#!/usr/bin/env python3
"""dutymail 值星收信處理器核心（AIR-254.3 S1——模組＋CLI）。

職責：在 SessionStart／UserPromptSubmit 邊界（值星在場時），以
epoch-fenced holder 身分對 per-repo mailbox（alias＝exact alias，如
ai-guide-marshal）執行一個完整收信週期——`holder` 面取權威 →
`receive prepare` 取 bounded 批次 → 逐封 triage → 全部處置完才
`receive ack`。輸出＝digest 行＋surface 項（hook 層包成
hookSpecificOutput.additionalContext；CLI 層印純文字行）。

核心不變量（EP invariant 對應）：
- ack 是唯一 cursor 前進邊，只在本批每一封都有 disposition 紀錄後
  下達——絕不 flush-ack（處置中斷＝ack 呼叫不到達；未完成批次以
  `--invalidate` 顯式作廢，信不動，下輪重 prepare，寧重不漏）。
- 自動處理 default-deny：`triage` 需 class×action 表（config）允許＋
  intent 機械驗證全過；三條代碼層底線 config 無法放寪——solicit 恆
  surface、未列 class 恆 surface、恆人工名單 class（handoff／patrol／
  work-order）恆 surface。auto 處理＝digest 吸收（計數行），
  輸出語義「例行已處理」，絕不宣稱 work accepted。
- holder 權威經 `holder bind` consent CAS 取得，絕不繞過；live holder
  在場＝不搶（換代正當路徑＝lease 到期後 rebind）；rebind CAS 失敗＝
  HolderConflict（surface 衝突訊息、單次嘗試、不重試轟炸）。
- holder state（bearer token）存 per-session 檔 0600、atomic 寫、
  路徑可注入（測試 fake state，不碰真 store）。
- v1 絕不主動送信：本檔不觸達 send／replies 面（回信＝outward，須
  逐次 AUTH，非本處理器範圍）。

dutymail typed contract（3.1.0 凍結）：每命令恰一個 JSON；成功＝
stdout `{"schemaVersion":1,"ok":true,"result":{...}}`；typed failure＝
stderr `{"schemaVersion":1,"ok":false,"error":{code,class,message,
retryable}}`＋空 stdout，exit class 2 usage／3 admission／4 storage／
5 fencing／6 wait-timeout。binary 解析順序：env DUTYMAIL_BIN →
PATH `dutymail` → plugin cache 版本最新（禁手 pin 版化路徑）。

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
SURFACE_FULL_TEXT_LIMIT = 3  # 每邊界全文呈報上限（防 context 洪水）
DUTYMAIL_TIMEOUT_SECONDS = 30
RUNNER_ENV = "DUTYMAIL_BIN"
PLUGIN_CACHE_BASE = "~/.zcode/cli/plugins/cache/delegate-market/delegate"
PLUGIN_BIN_PATTERN = os.path.join(
    "*", "bin", "aarch64-apple-darwin", "dutymail"
)

# renew/prepare 撞上的 fencing 家族（class 5）——觸發 status→rebind
FENCING_CODES = frozenset(
    {"stale-epoch", "holder-token-mismatch", "lease-expired"}
)
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


class HolderConflict(RuntimeError):
    """holder 衝突——surface 訊息、單次嘗試、不重試轟炸（唯一
    consuming authority 裁決）。兩觸發：live holder 在場（另一 session
    持有消費權威——不搶，待 lease 到期）；rebind consent CAS 失敗
    （status 與 bind 之間 race window 内他方先 bind——epoch 已前進）。"""


# ── binary 解析（DUTYMAIL_BIN → PATH → plugin cache 版本最新）────────


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
    base = os.path.expanduser(PLUGIN_CACHE_BASE)
    candidates = glob.glob(os.path.join(base, PLUGIN_BIN_PATTERN))
    if not candidates:
        raise RuntimeError(
            "dutymail binary not found（" + RUNNER_ENV
            + " / PATH / plugin cache 皆缺席）"
        )
    return max(candidates, key=_version_key)


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


def holder_bind(runner, address, expected_epoch):
    return _call(
        runner,
        ["holder", "bind", "--address", address,
         "--expected-epoch", str(expected_epoch)],
    )


def holder_renew(runner, address, token):
    return _call(
        runner, ["holder", "renew", "--address", address, "--token", token]
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
    """單封處置紀錄。action＝auto（digest 吸收）｜surface（全文呈報）。"""

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


# ── 輸出渲染（digest-first；全文上限 3）──────────────────────────────


def render(address, dispositions, now_us):
    """dispositions → 輸出行（digest 行＋surface 項）。auto 由 digest
    吸收（「例行已處理」——絕不宣稱 work accepted）；surface 前 3 筆
    全文（canonical envelope 原文），超出者一行 header 摘要。"""
    if not dispositions:
        return []
    surf = [d for d in dispositions if d.action == "surface"]
    n_auto = len(dispositions) - len(surf)
    counts: dict[str, int] = {}
    for d in dispositions:
        label = d.klass if d.klass else "unknown"
        counts[label] = counts.get(label, 0) + 1
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
    for i, d in enumerate(surf, 1):
        if i <= SURFACE_FULL_TEXT_LIMIT:
            lines.append(
                f"[{HOOK_TAG}] 待你處置（{i}/{len(surf)}）：{d.canonical}"
            )
        else:
            lines.append(
                f"[{HOOK_TAG}] 待你處置（{i}/{len(surf)}，摘要）"
                f"from={d.from_session or 'unknown'} "
                f"class={d.klass or 'unknown'} "
                f"intent={d.intent or 'unknown'} "
                f"envelope_id={d.envelope_id or 'unknown'}"
            )
    return lines


# ── ensure_holder：fresh bind／renew／rebind-on-fencing 三分流────────


def ensure_holder(address, runner, state_file):
    """取得／續約 holder 權威 → 有效 state dict。

    無 token → status（觀察 epoch＋live）→ live holder 在場＝不搶
    （HolderConflict surface）；live=False 才 bind（consent CAS）。
    有 token → renew（heartbeat）；renew 撞 fencing 家族（stale-epoch
    ／token mismatch／lease-expired）→ status→rebind（同樣過 live 閘——
    他方 live＝不搶）。rebind CAS 失敗（epoch-conflict，race window
    内他方先 bind）＝HolderConflict。storage 錯誤原樣傳出（上層
    fail-soft pre-migration）。
    """
    st = load_state(state_file)
    if _valid_holder_state(st, address):
        try:
            holder_renew(runner, address, st["token"])
            return st
        except DutymailFaceError as exc:
            if exc.is_storage or exc.code not in FENCING_CODES:
                raise
            # fencing 家族 → rebind（落到 _bind_fresh）
    return _bind_fresh(address, runner, state_file)


def _bind_fresh(address, runner, state_file):
    observed = holder_status(runner, address)
    epoch = observed.get("bindingEpoch")
    # observed epoch 驗證＝非負整數：fresh address（從未 bind）的合法值
    # 就是 0（unbound e=0）——首次 bind 的 consent CAS 觀察值正是
    # `--expected-epoch 0`（S3 真實 store 實測：bindingEpoch=0＋live=
    # False＋leaseExpiresAtUs=None）。bind 後的 epoch 恆 ≥1（下方
    # result 面維持正整數驗證）。
    if not _non_negative_int(epoch):
        raise DutymailFaceError(
            "shape-drift", "unknown",
            f"holder status bindingEpoch 非非負整數：{observed!r}",
            False, 0,
        )
    # holder 搶奪防護（S3 finding #2）：live holder 在場＝另一 session
    # 正持有消費權威——**不 bind 不搶**（並行 session／卡 WT spawned
    # agents 的 ping-pong 防護）；值星換代正當路徑＝lease 到期
    # （live=False）後 rebind。CAS（epoch-conflict）保留為 status 與
    # bind 之間 race window 的最後防線。「live=True 且 epoch==我 state
    # epoch」（我方 token 失效邊角）經此同一規則落衝突不搶——租約到期
    # 自癒，信不丟（prepare 不消耗）。
    if observed.get("live") is True:
        raise HolderConflict(
            f"{address}：另一 session holding（epoch {epoch}）——本"
            " session 不搶，待 lease 到期；處理面照舊由現 holder 承擔"
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
            if exc.code in BATCH_DEAD_CODES or exc.code in FENCING_CODES:
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
    重試一次；fencing 家族（epoch/token 中途失效）→ status→rebind→
    以新 token 重試一次（舊批隨 rebind 自動 fenced）。"""
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
        if exc.code in FENCING_CODES:
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
                 max_count=DEFAULT_MAX_COUNT, now_us=None):
    """完整收信週期 → (lines, commit | None)。

    流程：ensure_holder → 遺留批次收斂 → prepare（bounded）→ state
    記 batch_token（undisposed——crash window 防線）→ 逐封 triage（
    全純計算；任一 raise＝ack 不被呼叫——絕不 flush-ack）→ render。
    commit＝ack＋state 收斂，由呼叫端在輸出寫出成功後執行（
    advance-after-emit：先呈報後 ack）。空批次（正典形＝envelopes==[]
    且 batchToken==None）＝([], None) 零輸出；其他非正典形 shape-drift
    raise（fail-loud，交上層 fail-soft）。
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
    lines = render(address, dispositions, now)
    token = st["token"]

    def commit():
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
    try:
        lines, commit = process_once(
            args.address, _default_runner, policy, sfile,
            max_count=args.max_count,
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
