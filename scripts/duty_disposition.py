#!/usr/bin/env python3
"""consumer-owned semantic disposition ledger（AIR-287——db-99 ai-guide
消費端份；dutymail 零改動，消費端自持）。

職責：duty hook 鏈收信**處理狀態帳**——received→processing→
handled／needs-human／failed 五態流轉（LLM 消費端自持；非 transport
receipts 軸、非 delivery cursor 軸——三軸獨立，本帳不代理任何 dutymail
權威）。operator 原則服務面：「AI 讀取處理了就不用顯示；人只處理需要
人介入的」——supervisor（scripts/duty_supervisor.py）消費本帳做停滯
觀測。

落點：`$XDG_STATE_HOME`（預設 `~/.local/state`）`/ai-guide/
duty-disposition/<address_alias>/<envelope_id>.json`；每信一檔、
atomic 寫（pid 後綴 tmp＋os.replace）＋0600。寫入序列化＝
per-envelope lockfile（`<eid>.json.lock`——非 .json 不入任何掃描／
integrity gate，空檔留存＝鎖槽位復用）上 fcntl flock：set() 讀改寫
跨進程互斥，競寫不得繞流轉表（AIR-287 bi 修復——GLM F3）。
`<root>/_meta/` 放非 envelope 記錄（例外地址建立記錄等），**不入**
任何 address 掃描。

記錄 schema（凍結六鍵、恰此六鍵——嚴格驗證，多鍵少鍵＝LedgerCorrupt）：
    {"schema_version": 1, "envelope_id": str, "correlation_id": str|None,
     "state": 五態之一, "updated_at_us": 正 int, "session_id": str}
correlation_id＝來源工作關聯鍵（dutymail 語義：in_reply_to 優先、body
machine-header task/card 次之、皆缺＝None）。

五態流轉表（轉移表外一律 IllegalTransition——crash-only，狀態帳不可
靜默漂移）：
    初始建立：僅 received（hook 鏈是唯一 received 寫入者；消費端手動
        補帳走 received 起手——誠實軌跡，禁發明中間歷史）
    received    → processing | handled | needs-human | failed
    processing  → handled | needs-human | failed
    needs-human → processing | handled | failed（人類介入後續工／結案）
    failed      → processing（重試）
    handled     → （終態，禁離開）
    同態重設    → 恆允許＝heartbeat（refresh updated_at_us＋session_id；
        supervisor 停滯判準即「同態太久」，重設就是推進證據）

crash-only 裁定（單檔壞列 vs 整批）：壞 ledger 檔（非 JSON／schema 壞
形）＝LedgerCorrupt typed 錯誤，**get 與 list 皆整批拒用（fail-closed
，拒用範圍＝單 address 目錄）**——284 前例（整源拒用）是 routing 上游
；本帳是自家消費端狀態、權衡不同：降級為「跳過壞檔續掃」＝最需要被
看見的停滯／needs-human 記錄可能正是壞的那筆（silent-corruption 形態
——損壞與異常狀態正相關），故寧拒不跳；範圍最小化到單 address 目錄，
他 address 不受牽連。修復動作明確＝人工檢視／移除該檔（處理狀態證據
，移除須人判斷，本模組不代刪）。

received sink（duty hook 接線消費面）：`make_received_sink(session_id,
base_dir)` 回傳 **safe** callable（address, dispositions, now_us）——
內建 failure containment：任何失敗（含 InvalidIdentifier）只 stderr
`[duty-disposition]` 一行註記、絕不 raise（信件損失 > ledger 缺口；
缺口要大聲）。生產面注入 duty_receive.process_once 時必經此 wrapper。

處理推進（AIR-287 bi 修復必修 1——codex F1「auto 信恆停 received」
；第二 sink 消費面）：`make_resolution_sink(session_id, base_dir)` 回
safe callable，在 **digest 呈現完成邊界**（duty_receive.process_once
的 commit 起點——呼叫端契約＝輸出成功寫出後才 commit，
advance-after-emit）推進：triage action=="auto"（digest 吸收＝例行信
的「處理」本身）→ handled；action=="surface"（摘要已呈報給人，判讀
責任移交人類迴圈）→ needs-human。**推進點選擇裁定（記錄）**：auto
信的工作＝digest 吸收，digest 呈現完成即工作完成——故推進不以
delivery ack 成功為前提（ack 是 transport cursor，bridge 語義
ack≠done；ack 失敗只影響 cursor 重試，digest 已呈現的事實不變）；
也不在 record_received 當下推進（當下 digest 尚未呈現，session 中斷
＝帳面謊報已處理）。surface→needs-human 使人類介入迴圈進入
supervisor 監視面（needs-human 停滯＝session 死於 forward 前的電子
蹤跡）。重呈報（batch-dead ack 後重 prepare）已推進的信：
record_received 逐封吸收 IllegalTransition（stderr 一行、帳面維持已
處理真態、同批其餘信件記帳不中斷）。

CLI（模組＋CLI 三 face；exit 0 成功／1 LedgerError typed 錯誤／
2 args 誤用）：
    set   --address ALIAS --envelope-id ID --state STATE
          --session-id ID [--correlation-id C] [--base-dir DIR]
    get   --address ALIAS --envelope-id ID [--base-dir DIR]
    list  --address ALIAS [--base-dir DIR]   # JSON lines（stdout）

測試形態：base_dir／now_us 全參數可注入——零真實 state 目錄往返。
"""

import argparse
import fcntl
import json
import os
import re
import sys

SCHEMA_VERSION = 1
STATES = ("received", "processing", "handled", "needs-human", "failed")
INITIAL_STATE = "received"
TRANSITIONS = {
    "received": frozenset({"processing", "handled", "needs-human",
                           "failed"}),
    "processing": frozenset({"handled", "needs-human", "failed"}),
    "needs-human": frozenset({"processing", "handled", "failed"}),
    "failed": frozenset({"processing"}),
    "handled": frozenset(),  # 終態
}
RECORD_KEYS = frozenset(
    {"schema_version", "envelope_id", "correlation_id", "state",
     "updated_at_us", "session_id"}
)
# 識別碼（alias／envelope_id）＝檔名面：strict 白名單——path traversal
# （..／／）與任意字元 crash-only 拒絕。
_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

TAG = "duty-disposition"


class LedgerError(RuntimeError):
    """ledger typed 錯誤基類（CLI 面統一 exit 1）。"""


class InvalidIdentifier(LedgerError):
    """alias／envelope_id 含非法字元或形（path traversal 禁）。"""


class UnknownRecord(LedgerError):
    """查詢的記錄不存在（list 空目錄≠錯；get 缺檔＝typed）。"""


class LedgerCorrupt(LedgerError):
    """壞 ledger 檔（非 JSON／schema 壞形）——fail-closed，見模組
    docstring 整批拒用裁定。"""


class IllegalTransition(LedgerError):
    """五態流轉表外轉移（含非 received 初始態）。"""


def _validate_identifier(value, label):
    if (
        not isinstance(value, str)
        or not _ID_RE.match(value)
        or value in (".", "..")
    ):
        raise InvalidIdentifier(f"{label} 非法：{value!r}")
    return value


def _default_base_dir():
    """ledger 根目錄預設解析（base_dir 參數缺席時——XDG state 慣例）。"""
    root = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(root, "ai-guide", "duty-disposition")


def record_path(address, envelope_id, base_dir_override=None):
    _validate_identifier(address, "address alias")
    _validate_identifier(envelope_id, "envelope_id")
    root = (
        base_dir_override
        if base_dir_override is not None
        else _default_base_dir()
    )
    return os.path.join(root, address, envelope_id + ".json")


def _atomic_write(path, doc):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    tmp = path + "." + str(os.getpid()) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _load_valid(path):
    """讀單檔 → 記錄 dict；缺檔＝None；壞檔＝LedgerCorrupt（檔名隨行
    ——修復動作明確）。schema 嚴格：恰六鍵、型別與值域全驗。"""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise LedgerCorrupt(f"ledger 檔不可解析：{path}（{exc!r}）") from exc
    if not isinstance(doc, dict) or doc.keys() != RECORD_KEYS:
        raise LedgerCorrupt(
            f"ledger schema 鍵集不符：{path}"
            f"（得 {sorted(doc) if isinstance(doc, dict) else type(doc)}，"
            f"應 {sorted(RECORD_KEYS)}）"
        )
    if doc["schema_version"] != SCHEMA_VERSION:
        raise LedgerCorrupt(
            f"ledger schema_version 不符：{path}"
            f"（{doc['schema_version']!r}）"
        )
    if doc["state"] not in STATES:
        raise LedgerCorrupt(
            f"ledger state 非法：{path}（{doc['state']!r}）"
        )
    if not _positive_int(doc["updated_at_us"]):
        raise LedgerCorrupt(
            f"ledger updated_at_us 非正整數：{path}"
            f"（{doc['updated_at_us']!r}）"
        )
    if not isinstance(doc["envelope_id"], str) or not doc["envelope_id"]:
        raise LedgerCorrupt(f"ledger envelope_id 壞形：{path}")
    if not isinstance(doc["session_id"], str) or not doc["session_id"]:
        raise LedgerCorrupt(f"ledger session_id 壞形：{path}")
    corr = doc["correlation_id"]
    if corr is not None and not isinstance(corr, str):
        raise LedgerCorrupt(f"ledger correlation_id 壞形：{path}")
    return doc


def _positive_int(value):
    return (
        isinstance(value, int) and not isinstance(value, bool) and value > 0
    )


# ── 三 face（模組 API）───────────────────────────────────────────────


def _envelope_lock(path):
    """per-envelope 寫鎖（AIR-287 bi 修復——GLM F3）：lockfile＝
    `<record>.lock`（非 .json——不入任何掃描／integrity gate；空檔
    留存＝鎖槽位復用，非記錄殘留）上 fcntl flock LOCK_EX，set() 的
    讀改寫臨界區全程持有——兩消費端同 envelope_id 競寫序列化，禁繞
    流轉表。回傳 fd；呼叫端 finally flock UN＋close。開檔／flock 失
    敗＝LedgerError fail-loud（禁無鎖續寫）。"""
    lock_path = path + ".lock"
    parent = os.path.dirname(lock_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as exc:
        raise LedgerError(
            f"lockfile 開啟失敗：{lock_path}（{exc!r}）"
        ) from exc
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except OSError as exc:
        os.close(fd)
        raise LedgerError(
            f"lockfile flock 失敗：{lock_path}（{exc!r}）"
        ) from exc
    return fd


def set(
    address, envelope_id, state, session_id, correlation_id=None,
    now_us=None, base_dir=None,
):
    """寫入（含流轉表驗證）→ 落盤記錄 dict。

    correlation_id 傳 None 且記錄已存在＝保留原值（後續態轉移不必重
    帶關聯鍵）；首次建立 correlation_id=None 即 None。
    讀改寫於 per-envelope lockfile flock 下進行（GLM F3——跨進程
    序列化；lockfile 契約見 _envelope_lock）。
    """
    _validate_identifier(address, "address alias")
    _validate_identifier(envelope_id, "envelope_id")
    if state not in STATES:
        raise IllegalTransition(f"未知 state：{state!r}")
    if not _positive_int(now_us):
        raise LedgerError(f"now_us 須正整數，得 {now_us!r}")
    if not isinstance(session_id, str) or not session_id:
        raise LedgerError("session_id 須非空字串")
    path = record_path(address, envelope_id, base_dir)
    lock_fd = _envelope_lock(path)
    try:
        try:
            existing = _load_valid(path)
            if existing is None:
                if state != INITIAL_STATE:
                    raise IllegalTransition(
                        f"初始建立僅 {INITIAL_STATE}（得 {state!r}）——"
                        "消費端補帳走 received 起手，禁發明中間歷史"
                    )
                corr = correlation_id
            else:
                if (
                    state != existing["state"]
                    and state not in TRANSITIONS[existing["state"]]
                ):
                    raise IllegalTransition(
                        f"{address}/{envelope_id}："
                        f"{existing['state']}→{state} 不在流轉表"
                    )
                corr = (
                    correlation_id
                    if correlation_id is not None
                    else existing["correlation_id"]
                )
            doc = {
                "schema_version": SCHEMA_VERSION,
                "envelope_id": envelope_id,
                "correlation_id": corr,
                "state": state,
                "updated_at_us": now_us,
                "session_id": session_id,
            }
            _atomic_write(path, doc)
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
    finally:
        os.close(lock_fd)
    return doc


def get(address, envelope_id, base_dir=None):
    """讀單記錄 → dict；缺檔＝UnknownRecord；同 address 任一檔壞＝
    LedgerCorrupt（整批拒用與 list 統一——AIR-287 bi 修復 codex F4：
    實作經同一 address 掃描面，模組 docstring「get 與 list 皆整批拒
    用」裁定自此為真；284 前例＝整源拒用，本帳範圍最小化到單
    address）。以記錄內 envelope_id 配對（非檔名）——錯置檔名不冒
    配。"""
    _validate_identifier(address, "address alias")
    _validate_identifier(envelope_id, "envelope_id")
    for doc in list_records(address, base_dir=base_dir):
        if doc["envelope_id"] == envelope_id:
            return doc
    raise UnknownRecord(f"{address}/{envelope_id}：無記錄")


def list_records(address, base_dir=None):
    """列 address 目錄全部記錄 → 按（updated_at_us, envelope_id）排序。

    目錄缺席／空＝[]（合法冷啟動）；目錄內任一檔壞＝LedgerCorrupt
    （整批拒用裁定——見模組 docstring）。_meta 與非 .json 檔不入。
    """
    _validate_identifier(address, "address alias")
    d = os.path.join(
        base_dir if base_dir is not None else _default_base_dir(), address
    )
    try:
        names = sorted(os.listdir(d))
    except FileNotFoundError:
        return []
    records = []
    for name in names:
        if not name.endswith(".json"):
            continue
        path = os.path.join(d, name)
        doc = _load_valid(path)
        if doc is None:
            raise LedgerCorrupt(f"ledger 檔失蹤（race）：{path}")
        records.append(doc)
    records.sort(key=lambda r: (r["updated_at_us"], r["envelope_id"]))
    return records


# ── meta face（非 envelope 記錄；不入 address 掃描）──────────────────


def write_exception_address_record(
    alias, create_result, session_id, now_us, base_dir=None,
):
    """例外地址建立記錄 → `<root>/_meta/exception-address.json`。

   AIR-287 唯一 dutymail write 面（address create）的證據落帳；形：
    {kind, alias, result, session_id, created_at_us}。
    """
    _validate_identifier(alias, "address alias")
    root = os.path.join(
        base_dir if base_dir is not None else _default_base_dir(), "_meta"
    )
    os.makedirs(root, exist_ok=True)
    doc = {
        "kind": "exception-address-create",
        "alias": alias,
        "result": create_result,
        "session_id": session_id,
        "created_at_us": now_us,
    }
    _atomic_write(os.path.join(root, "exception-address.json"), doc)
    return doc


# ── received sink（duty hook 接線消費面；safe by construction）───────


def _correlation_from_canonical(canonical):
    """canonical envelope 字串 → correlation_id（in_reply_to 優先、
    body task/card 次之、皆缺／不可解析＝None——記帳面禁因解析失敗
    raise，解析失敗≠信件壞）。"""
    try:
        env = json.loads(canonical)
        if not isinstance(env, dict):
            return None
    except (ValueError, TypeError):
        return None
    irt = env.get("in_reply_to")
    if isinstance(irt, str) and irt:
        return irt
    body = env.get("body")
    if isinstance(body, str):
        try:
            body_doc = json.loads(body)
        except ValueError:
            body_doc = None
        if isinstance(body_doc, dict):
            for key in ("task", "card"):
                value = body_doc.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def record_received(
    address, dispositions, session_id, now_us, base_dir=None,
):
    """triage dispositions → 逐封 set received（本 face 允許 raise
    ——failure containment 在 make_safe_sink）。

    已推進信（handled／needs-human／processing——重呈報案例）逐封
    吸收 IllegalTransition：stderr 一行（大聲非靜默）、帳面維持已處
    理真態、同批其餘信件記帳不中斷（received→已處理態不在流轉表，
    蓋寫才是 silent-corruption）。"""
    for d in dispositions:
        if not getattr(d, "envelope_id", None):
            continue  # triage 已標 unknown id——無記帳鍵，跳過（raw
            # bad-envelope 案例的 envelope_id=None；ledger 不發明 id）
        try:
            set(
                address, d.envelope_id, INITIAL_STATE, session_id,
                correlation_id=_correlation_from_canonical(d.canonical),
                now_us=now_us, base_dir=base_dir,
            )
        except IllegalTransition as exc:
            print(
                f"[{TAG}] {exc}（重呈報已處理信——維持現態）",
                file=sys.stderr,
            )


def record_resolution(
    address, dispositions, session_id, now_us, base_dir=None,
):
    """digest 呈現完成邊界的處理推進（本 face 允許 raise——failure
    containment 在 make_safe_sink）：action=="auto"→ handled（digest
    吸收＝工作完成——推進點裁定見模組 docstring）；action==
    "surface"→ needs-human（判讀責任移交人類迴圈）。未知 action 不
    發明狀態（保守跳過——router 面 fail-loud 是 forward 模組職責）；
    correlation_id 恆保留原值。"""
    for d in dispositions:
        if not getattr(d, "envelope_id", None):
            continue
        action = getattr(d, "action", None)
        if action == "auto":
            target = "handled"
        elif action == "surface":
            target = "needs-human"
        else:
            continue
        set(
            address, d.envelope_id, target, session_id,
            now_us=now_us, base_dir=base_dir,
        )


def make_safe_sink(inner):
    """包裝任意 sink → safe callable：任何例外只 stderr 一行
    `[duty-disposition]`——絕不 raise（信件損失 > ledger 缺口；缺口
    要大聲。生產面注入 process_once 必經此 wrapper）。"""
    def safe(address, dispositions, now_us):
        try:
            inner(address, dispositions, now_us)
        except Exception as exc:
            print(
                f"[{TAG}] disposition 記帳失敗（照常收信）——{exc!r}",
                file=sys.stderr,
            )
    return safe


def make_received_sink(session_id, base_dir=None):
    """生產面 sink 工廠：session 綁定＋safe wrapper 一體。"""
    return make_safe_sink(
        lambda address, dispositions, now_us: record_received(
            address, dispositions, session_id, now_us, base_dir,
        )
    )


def make_resolution_sink(session_id, base_dir=None):
    """生產面 resolution sink 工廠（AIR-287 bi 必修 1）：session 綁定
    ＋safe wrapper 一體——digest 呈現完成邊界推進（auto→handled／
    surface→needs-human；推進點裁定見模組 docstring）。"""
    return make_safe_sink(
        lambda address, dispositions, now_us: record_resolution(
            address, dispositions, session_id, now_us, base_dir,
        )
    )


# ── CLI 面 ───────────────────────────────────────────────────────────


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "consumer disposition ledger（AIR-287；set/get/list 三 face"
            "——dutymail 零改動，消費端自持狀態帳）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _common(p):
        p.add_argument(
            "--base-dir", default=None, metavar="DIR",
            help="ledger 根覆寫（預設 XDG state／~/.local/state）",
        )

    p_set = sub.add_parser("set", help="寫入／流轉狀態（流轉表驗證）")
    p_set.add_argument("--address", required=True, metavar="ALIAS")
    p_set.add_argument("--envelope-id", required=True, metavar="ID")
    p_set.add_argument("--state", required=True, choices=STATES)
    p_set.add_argument("--session-id", required=True, metavar="ID")
    p_set.add_argument("--correlation-id", default=None, metavar="C")
    _common(p_set)

    p_get = sub.add_parser("get", help="讀單記錄（stdout JSON）")
    p_get.add_argument("--address", required=True, metavar="ALIAS")
    p_get.add_argument("--envelope-id", required=True, metavar="ID")
    _common(p_get)

    p_list = sub.add_parser("list", help="列 address 全記錄（JSON lines）")
    p_list.add_argument("--address", required=True, metavar="ALIAS")
    _common(p_list)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "set":
            doc = set(
                args.address, args.envelope_id, args.state,
                args.session_id, correlation_id=args.correlation_id,
                now_us=_now_us(), base_dir=args.base_dir,
            )
            print(json.dumps(doc, ensure_ascii=False, sort_keys=True))
        elif args.command == "get":
            doc = get(args.address, args.envelope_id, base_dir=args.base_dir)
            print(json.dumps(doc, ensure_ascii=False, sort_keys=True))
        else:
            for doc in list_records(args.address, base_dir=args.base_dir):
                print(json.dumps(doc, ensure_ascii=False, sort_keys=True))
    except LedgerError as exc:
        print(f"[{TAG}] typed failure：{exc}", file=sys.stderr)
        return 1
    return 0


def _now_us():
    import time

    return time.time_ns() // 1000


if __name__ == "__main__":
    raise SystemExit(main())
