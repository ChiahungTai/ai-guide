#!/usr/bin/env python
"""receipt_normalize——AIR-135.1 S2 跨家族回執正規化 v0：muse／codex／glm 真實回執 → canonical slice-receipt/1。

邊界（卡面 Plan＋S1 延伸已決策勿重辯）：
- D7：canonical 目標形＝S1 receipt schema（slice-receipt/1，定義源 scripts/arc_spec.py），
  不新造；本檔只做純函式轉換（raw→canonical），禁引擎／守護進程／台帳寫入（D1 畫線同 S1）。
- D8：family/model/ledger 欄語義本 slice 實填——family 進 canonical 欄；model／ledger
  （帳本指針）／usage 以 provenance extras 隨行（validator 容忍額外鍵；是否收編 schema 歸 135.7）。
- N6：dispatch-slice.receipt_sink 選填欄由本 slice 補進 arc_spec.py（回執落點）。

輸入 envelope（normalize 的 raw）——不是家族原生記錄單獨本身，而是「帳本記錄＋plan
回指＋收線面」的組裝信封；逐欄對照＝.agent-tmp/air-135.1/receipt-field-map.md：
- ledger（必填）：bridge jobs.json 該 job 記錄逐字（三家族異質面所在）
- ledger_path（必填）：帳本路徑（帳本指針）
- slice_ref（必填）：plan 回指 {slice_id, card_id, unit_id, plan_version, plan_hash}
  ——帳本無此面，歸 marshal 派工 context。正式派工＝ArcPlan 版本/hash；ad-hoc
  派工（無 ArcPlan——今晚四回執即此形）v0 慣例＝brief 檔 sha256、plan_version=1，
  由 seal 腳本機算密封；normalize 不驗 hash 對應檔案內容（unverified 自述）。
- collection（選填）：waiter CollectionReceipt jobs[] 條目逐字（camelCase；
  normalize 轉 canonical snake：boundedReceiptProjection→bounded_receipt_projection）
- terminal（選填）：家族 jsonl 終端記錄逐字（三家族三形：codex＝item.completed/
  agent_message、muse＝run.terminal.completed、glm＝turn.completed）
- delivery（選填）：caller 親驗的 delivery（manual-anchor 案例）；與 collection
  並存＝雙 authoritative delivery，fail-loud（AC#1 同構）
- status_override（選填）：帳本狀態歧義時的 caller 裁決（canonical terminal 值）
- intent_review（選填 dict）：Intent Review 驗收腿回寫面——原樣透傳進 receipt
  （verdict 枚舉 GO／GO-WITH-FIXES／NO-GO 由下游 arc_spec validator 驗）
- plan_hash_source（選填 str）：被 hash 的來源檔指針——透傳進 receipt 同名欄
  （muse N-2：receipt 只存 hash 不存源；ad-hoc＝brief 檔 path、正式＝ArcPlan 檔 path）
- top_findings／blockers／unverified／pending_human_decision（選填 list[str]）：
  llm-guidance pass-through（語義判定歸 caller；normalize 只加自己可證的條目）

fail-loud（codex multi_agents_common.rs:395-442 文案形，同 S1）：未知 family 列可用值、
缺欄一次列全部、雙 authoritative（family/delivery 衝突）即錯、歧義帳本狀態
（failed-or-capped）禁靜默映射——要 caller 攜 status_override 裁決。

家族狀態映射（v0——今晚真實回執觀察，bridge 狀態詞彙非本檔定義源）：
completed→completed；interrupted→failed（保守映射，blockers 註記原值與 carrier exit）；
running＝非 terminal 拒收；failed-or-capped＝failed 與 budget-limited 歧義，拒收待
status_override。local family 無映射（今晚範圍＝三家族）。
"""

import importlib.util
import re
from pathlib import Path

SCHEMA_RECEIPT = "slice-receipt/1"

_ENVELOPE_REQUIRED = ("ledger", "ledger_path", "slice_ref")
_ENVELOPE_OPTIONAL = (
    "collection",
    "terminal",
    "delivery",
    "status_override",
    "intent_review",
    "plan_hash_source",
    "top_findings",
    "blockers",
    "unverified",
    "pending_human_decision",
)
_SLICE_REF_KEYS = ("slice_id", "card_id", "unit_id", "plan_version", "plan_hash")
_LEDGER_REQUIRED = ("id", "status", "family", "model", "timestamp", "summary")
_HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_EXCERPT_LEN = 280

_MAPPED_FAMILIES = ("muse", "codex", "glm")

# bridge 帳本狀態 → canonical terminal（TERMINALS 定義源＝arc_spec.py）
_LEDGER_STATUS_MAP = {"completed": "completed", "interrupted": "failed"}


class NormalizeError(Exception):
    """envelope／帳本記錄契約錯——收集式訊息一次報全部（同 arc_spec 慣例），fail loud。"""


def _load_arc_spec():
    path = Path(__file__).resolve().with_name("arc_spec.py")
    spec = importlib.util.spec_from_file_location("_air1351_arc_spec", path)
    if spec is None or spec.loader is None:
        raise NormalizeError(f"cannot load arc_spec module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_arc = _load_arc_spec()
FAMILIES: tuple[str, ...] = tuple(_arc.FAMILIES)
TERMINALS: tuple[str, ...] = tuple(_arc.TERMINALS)


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------


def _excerpt(text: str) -> str:
    text = text.strip()
    if len(text) <= _EXCERPT_LEN:
        return text
    return text[:_EXCERPT_LEN] + f"…（截斷 {_EXCERPT_LEN} 字元，全文見 jsonl）"


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _terminal_text(family: str, terminal: dict, errors: list[str]) -> str | None:
    """家族 jsonl 終端記錄 → 最終文字（三家族三形；形不合列期望形，codex 文案形）。"""
    if not isinstance(terminal, dict):
        errors.append(
            f"`terminal` must be an object for family `{family}`, "
            f"got {type(terminal).__name__}"
        )
        return None
    if family == "codex":
        item = terminal.get("item")
        ok = (
            terminal.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        )
        if not ok:
            errors.append(
                f"Malformed codex terminal record for receipt_normalize — "
                f'expected {{"type": "item.completed", "item": {{"type": "agent_message", '
                f'"text": …}}}}, got type=`{terminal.get("type")}`. '
                f"codex jsonl 終端文字住最後一個 item.completed/agent_message"
            )
            return None
        return str(item["text"])
    if family == "muse":
        payload = terminal.get("payload")
        ok = (
            terminal.get("payload_type") == "run.terminal.completed"
            and isinstance(payload, dict)
            and isinstance(payload.get("text"), str)
        )
        if not ok:
            errors.append(
                f"Malformed muse terminal record for receipt_normalize — "
                f'expected {{"payload_type": "run.terminal.completed", "payload": '
                f'{{"terminal": …, "text": …}}}}, got payload_type=`{terminal.get("payload_type")}`. '
                f"muse jsonl 終端文字住 run.terminal.completed 的 payload.text"
            )
            return None
        terminal_value = payload.get("terminal")
        if terminal_value != "completed":
            errors.append(
                f"Unknown muse terminal value `{terminal_value}` for receipt_normalize. "
                f"Known muse terminal values: completed"
            )
            return None
        return str(payload["text"])
    if family == "glm":
        payload = terminal.get("payload")
        ok = (
            terminal.get("type") == "turn.completed"
            and isinstance(payload, dict)
            and isinstance(payload.get("response"), str)
        )
        if not ok:
            errors.append(
                f"Malformed glm terminal record for receipt_normalize — "
                f'expected {{"type": "turn.completed", "payload": {{"response": …}}}}, '
                f'got type=`{terminal.get("type")}`. '
                f"glm jsonl 終端文字住 turn.completed 的 payload.response"
            )
            return None
        return str(payload["response"])
    errors.append(
        f"Family `{family}` has no terminal record mapping in receipt_normalize v0. "
        f"Mapped families: {', '.join(_MAPPED_FAMILIES)}"
    )
    return None


def _usage_extra(family: str, ledger: dict) -> tuple[dict | None, list[str]]:
    """家族帳本 usage 面 → canonical usage extras（無面者回 (None, [])——缺席非 0）。

    回傳 (usage, unmapped_keys)——未映射鍵原樣保留進 usage（鍵名不轉換）並由
    呼叫端記 unverified（muse NB-2：禁靜默丟棄計量面）。
    """
    if family == "codex":
        usage = ledger.get("carrierUsage")
        if usage is not None and not isinstance(usage, dict):
            raise NormalizeError(
                f"`carrierUsage` must be an object for codex usage face, "
                f"got {type(usage).__name__}（計量面損壞禁靜默缺席——J-2）"
            )
        if isinstance(usage, dict):
            return dict(usage), []
        return None, []
    if family == "glm":
        usage = ledger.get("resultUsage")
        if usage is not None and not isinstance(usage, dict):
            raise NormalizeError(
                f"`resultUsage` must be an object for glm usage face, "
                f"got {type(usage).__name__}（計量面損壞禁靜默缺席——J-2）"
            )
        if isinstance(usage, dict):
            mapped: dict = {}
            key_map = {
                "inputTokens": "input_tokens",
                "outputTokens": "output_tokens",
                "totalTokens": "total_tokens",
                "cacheReadTokens": "cache_read_tokens",
                "modelRequestCount": "model_request_count",
                "source": "source",
            }
            for src, dst in key_map.items():
                if src in usage:
                    mapped[dst] = usage[src]
            unmapped = sorted(k for k in usage if k not in key_map)
            for k in unmapped:
                mapped[k] = usage[k]
            return mapped, unmapped
        return None, []
    return None, []  # muse：帳本無 usage 面（今晚實證）——由呼叫端記 unverified


# ---------------------------------------------------------------------------
# 子面組裝
# ---------------------------------------------------------------------------


def _slice_ref_fields(slice_ref: object, errors: list[str]) -> dict:
    if not isinstance(slice_ref, dict):
        errors.append(
            f"`slice_ref` must be an object for receipt_normalize, "
            f"got {type(slice_ref).__name__}. "
            f"Required slice_ref keys: {', '.join(_SLICE_REF_KEYS)}"
        )
        return {}
    missing = [k for k in _SLICE_REF_KEYS if k not in slice_ref]
    if missing:
        errors.append(
            f"Missing slice_ref key(s) {', '.join(missing)} for receipt_normalize. "
            f"Required slice_ref keys: {', '.join(_SLICE_REF_KEYS)}"
        )
    blank = [
        k
        for k in _SLICE_REF_KEYS
        if isinstance(slice_ref.get(k), str) and not str(slice_ref.get(k)).strip()
    ]
    if blank:
        errors.append(
            f"Blank slice_ref key(s) {', '.join(blank)} for receipt_normalize — "
            f"空白值視同缺欄（fail-loud）"
        )
    unknown = [k for k in slice_ref if k not in _SLICE_REF_KEYS]
    if unknown:
        errors.append(
            f"Unknown slice_ref key(s) {', '.join(unknown)} for receipt_normalize. "
            f"Known slice_ref keys: {', '.join(_SLICE_REF_KEYS)}"
        )
    plan_version = slice_ref.get("plan_version")
    if "plan_version" in slice_ref and not _is_positive_int(plan_version):
        errors.append(
            f"Invalid slice_ref.plan_version `{plan_version}` for receipt_normalize — "
            f"需正整數（回指 ArcPlan 版本；ad-hoc 派工慣例＝1）"
        )
    plan_hash = slice_ref.get("plan_hash")
    if "plan_hash" in slice_ref and not (
        isinstance(plan_hash, str) and _HEX64_RE.match(plan_hash)
    ):
        errors.append(
            f"Invalid slice_ref.plan_hash `{plan_hash}` for receipt_normalize — "
            f"需 hex 64 位（正式派工＝ArcPlan content hash；ad-hoc 慣例＝brief 檔 sha256）"
        )
    fields: dict = {}
    for key in _SLICE_REF_KEYS:
        value = slice_ref.get(key)
        if isinstance(value, str) and value.strip():
            fields[key] = value
        elif value is not None:
            fields[key] = value
    return fields


def _canonical_status(ledger: dict, envelope: dict, job_id: str, errors: list[str]) -> str:
    ledger_status = ledger.get("status")
    override = envelope.get("status_override")
    if ledger_status in _LEDGER_STATUS_MAP and override is not None:
        errors.append(
            f"Conflicting status authority for job `{job_id}`: ledger status "
            f"`{ledger_status}` 本可直接映射，卻另攜 status_override=`{override}` — "
            f"雙 authoritative status（fail-loud；override 留給歧義狀態）"
        )
        return ""
    if ledger_status in _LEDGER_STATUS_MAP:
        return _LEDGER_STATUS_MAP[ledger_status]
    if ledger_status == "failed-or-capped":
        if override is None:
            errors.append(
                f"Ambiguous ledger status `failed-or-capped` for job `{job_id}` — "
                f"failed 與 budget-limited 二義，禁靜默映射。攜 envelope "
                f"`status_override` 裁決（caller 依 failurePhase/errorExcerpt 判別）. "
                f"Available terminal overrides: {', '.join(TERMINALS)}"
            )
        elif override in TERMINALS:
            return str(override)
        else:
            errors.append(
                f"Unknown status_override `{override}` for job `{job_id}`. "
                f"Available terminals: {', '.join(TERMINALS)}"
            )
        return ""
    if ledger_status == "running":
        errors.append(
            f"Non-terminal ledger status `running` for job `{job_id}` — "
            f"receipt 語義限 terminal job（等收線再正規化）. "
            f"Mappable ledger statuses: {', '.join(sorted(_LEDGER_STATUS_MAP))}, "
            f"failed-or-capped（須 status_override）"
        )
        return ""
    errors.append(
        f"Unknown ledger status `{ledger_status}` for job `{job_id}` in receipt_normalize. "
        f"Known ledger statuses: completed, interrupted, failed-or-capped, running"
    )
    return ""


def _delivery(
    envelope: dict,
    collection: dict | None,
    final_text: str | None,
    ledger: dict,
    job_id: str,
    errors: list[str],
) -> dict:
    if collection is not None and envelope.get("delivery") is not None:
        errors.append(
            f"Conflicting authoritative delivery for job `{job_id}`: envelope `collection` "
            f"（waiter 機驗）與 `delivery`（caller 親驗）並存 — 雙 authoritative delivery（fail-loud）"
        )
    if collection is not None:
        delivery = collection.get("delivery")
        if not isinstance(delivery, dict) or not delivery:
            errors.append(
                f"Missing `delivery` in collection entry for job `{job_id}` — "
                f"waiter CollectionReceipt jobs[] 條目須帶 delivery 面"
            )
            delivery = {}
        proj = collection.get("boundedReceiptProjection")
        projection: dict = {}
        if isinstance(proj, dict) and "finalTextNonEmpty" in proj:
            projection["final_text_non_empty"] = bool(proj["finalTextNonEmpty"])
            if "note" in proj:
                projection["note"] = proj["note"]
        elif isinstance(proj, dict):
            errors.append(
                f"Malformed boundedReceiptProjection for job `{job_id}` — "
                f"缺 finalTextNonEmpty（waiter camelCase 慣例）"
            )
        else:
            # 舊形 waiter 條目缺投影面——改由 terminal／summary 推導（推導源註記）
            source = final_text if final_text is not None else str(ledger.get("summary") or "")
            projection["final_text_non_empty"] = bool(source.strip())
            projection["note"] = "finalTextNonEmpty 由 terminal／帳本 summary 推導（collection 條目缺投影面）"
        return delivery, projection
    if "delivery" in envelope and envelope.get("delivery") is not None:
        if not isinstance(envelope["delivery"], dict):
            errors.append(
                f"`delivery` must be an object for receipt_normalize, "
                f"got {type(envelope['delivery']).__name__}"
            )
            return {}, {}
        delivery = envelope["delivery"]
        projection: dict = {}
        if final_text is not None:
            projection["final_text_non_empty"] = bool(final_text.strip())
        elif isinstance(ledger.get("summary"), str):
            projection["final_text_non_empty"] = bool(ledger["summary"].strip())
            projection["note"] = "final_text 判定源＝帳本 summary（bridge 組裝摘要），非全文"
        return delivery, projection
    # 兩收線面皆缺——receipt-only 保守形：verdict=not-assessed；status=completed 時
    # 會被 arc_spec validator 擋（terminal≠complete）——那是設計行為，不是缺口。
    l1 = bool(final_text.strip()) if final_text is not None else bool(
        str(ledger.get("summary") or "").strip()
    )
    return (
        {
            "mode": "receipt-only",
            "l1_present": l1,
            "l2_anchor": False,
            "anchor_hits": [],
            "verdict": "not-assessed",
        },
        {"final_text_non_empty": l1},
    )


# ---------------------------------------------------------------------------
# normalize 主體
# ---------------------------------------------------------------------------


def normalize(family: str, raw: dict) -> dict:
    """家族真實回執 envelope → canonical slice-receipt/1 dict（純函式；契約錯 raise NormalizeError）。"""
    errors: list[str] = []

    if family not in FAMILIES:
        raise NormalizeError(
            f"Unknown family `{family}` for receipt_normalize. "
            f"Available families: {', '.join(FAMILIES)}"
        )
    if family == "local":
        raise NormalizeError(
            f"Family `local` has no receipt mapping in receipt_normalize v0. "
            f"Mapped families: {', '.join(_MAPPED_FAMILIES)}（今晚範圍＝muse／codex／glm）"
        )
    if not isinstance(raw, dict):
        raise NormalizeError(
            f"raw must be an object for receipt_normalize, got {type(raw).__name__}"
        )

    for key in _ENVELOPE_REQUIRED:
        if key not in raw or raw[key] is None:
            errors.append(
                f"Missing envelope key `{key}` for receipt_normalize. "
                f"Required envelope keys: {', '.join(_ENVELOPE_REQUIRED)}"
            )
    unknown_keys = [k for k in raw if k not in _ENVELOPE_REQUIRED + _ENVELOPE_OPTIONAL]
    if unknown_keys:
        errors.append(
            f"Unknown envelope key(s) {', '.join(unknown_keys)} for receipt_normalize. "
            f"Known envelope keys: {', '.join(_ENVELOPE_REQUIRED + _ENVELOPE_OPTIONAL)}"
        )
    if errors:
        raise NormalizeError("\n".join(errors))

    ledger = raw["ledger"]
    if not isinstance(ledger, dict):
        raise NormalizeError(
            f"`ledger` must be an object for receipt_normalize, got {type(ledger).__name__}"
        )
    job_id = ledger.get("id")
    missing_ledger = [
        k
        for k in _LEDGER_REQUIRED
        if k not in ledger
        or ledger[k] is None
        or (isinstance(ledger[k], str) and not ledger[k].strip())
    ]
    if missing_ledger:
        errors.append(
            f"Missing ledger field(s) {', '.join(missing_ledger)} for family `{family}` "
            f"job `{job_id}` in receipt_normalize. "
            f"Required ledger fields: {', '.join(_LEDGER_REQUIRED)}"
        )
    ledger_family = ledger.get("family")
    if ledger_family is not None and ledger_family != family:
        errors.append(
            f"Conflicting family for job `{job_id}`: family arg=`{family}`, "
            f"ledger.family=`{ledger_family}` — 雙 authoritative family（fail-loud）"
        )

    slice_fields = _slice_ref_fields(raw.get("slice_ref"), errors)

    status = _canonical_status(ledger, raw, str(job_id), errors)

    terminal = raw.get("terminal")
    final_text: str | None = None
    if terminal is not None:
        final_text = _terminal_text(family, terminal, errors)

    collection = raw.get("collection")
    if collection is not None:
        if not isinstance(collection, dict):
            errors.append(
                f"`collection` must be an object for receipt_normalize, "
                f"got {type(collection).__name__}"
            )
            collection = None
        else:
            col_job = collection.get("jobId")
            if col_job is not None and col_job != job_id:
                errors.append(
                    f"Conflicting job id for receipt_normalize: ledger.id=`{job_id}`, "
                    f"collection.jobId=`{col_job}` — 雙 authoritative job id（fail-loud）"
                )
            col_family = collection.get("family")
            if col_family is not None and col_family != family:
                errors.append(
                    f"Conflicting family for job `{job_id}`: family arg=`{family}`, "
                    f"collection.family=`{col_family}` — 雙 authoritative family（fail-loud）"
                )

    delivery, projection = _delivery(raw, collection, final_text, ledger, str(job_id), errors)

    if errors:
        raise NormalizeError("\n".join(errors))

    # --- 組裝 canonical（過此線＝契約面已全綠） ---
    usage, usage_unmapped = _usage_extra(family, ledger)

    receipt: dict = {"schema": SCHEMA_RECEIPT, **slice_fields}
    receipt["job_id"] = job_id
    receipt["family"] = family
    receipt["status"] = status
    receipt["delivery"] = delivery
    receipt["bounded_receipt_projection"] = projection

    # llm-guidance pass-through（caller 語義）＋normalize 自證條目
    def _merge_list(key: str, extra: str | None = None) -> None:
        value = raw.get(key)
        if value is not None and not isinstance(value, list):
            raise NormalizeError(
                f"`{key}` must be a list for caller pass-through, "
                f"got {type(value).__name__}"
            )
        items = [str(x) for x in value or []]
        if extra:
            items.append(extra)
        if items:
            receipt[key] = items

    blockers_extra: str | None = None
    if status == "failed" and ledger.get("status") == "interrupted":
        carrier = ledger.get("carrierExit")
        blockers_extra = (
            f"帳本狀態 interrupted（carrierExit={carrier}）——canonical failed 為保守映射；"
            f"非 completed 亦非 budget-limited"
        )
    _merge_list("blockers", blockers_extra)
    _merge_list("top_findings")
    _merge_list("pending_human_decision")
    unverified_raw = raw.get("unverified")
    if unverified_raw is not None and not isinstance(unverified_raw, list):
        raise NormalizeError(
            f"`unverified` must be a list for caller pass-through, "
            f"got {type(unverified_raw).__name__}"
        )
    unverified_caller = [str(x) for x in unverified_raw or []]
    unverified_caller.append(
        "plan_hash 回指面由 caller 提供（正式＝ArcPlan content hash；ad-hoc 慣例＝"
        "brief 檔 sha256）——normalize 不驗 hash 對應檔案內容"
    )
    if final_text is None:
        if projection.get("final_text_non_empty"):
            unverified_caller.append(
                "final_text 判定源＝帳本 summary（bridge 組裝摘要），非 jsonl 全文"
            )
    if family == "muse" and usage is None:
        unverified_caller.append(
            "muse 帳本無 usage 欄——計量面缺席（非 0；今晚 job-mufn1cw6-f4fmzx 實證）"
        )
    if usage_unmapped:
        unverified_caller.append(
            f"usage 未映射鍵原樣保留（{', '.join(usage_unmapped)}）——canonical 無對應欄，"
            f"值未丟棄但語義未轉換（muse NB-2 修正）"
        )
    receipt["unverified"] = unverified_caller

    # provenance extras（D8：model/ledger 實填；validator 容忍額外鍵，收編歸 135.7）
    receipt["model"] = ledger.get("model")
    ledger_pointer: dict = {
        "path": raw.get("ledger_path"),
        "job_id": job_id,
        "ledger_status": ledger.get("status"),
    }
    if ledger.get("jsonlPath"):
        ledger_pointer["jsonl"] = ledger.get("jsonlPath")
    if "exitCode" in ledger:
        ledger_pointer["exit_code"] = ledger.get("exitCode")
    elif "carrierExit" in ledger:
        ledger_pointer["exit_code"] = ledger.get("carrierExit")
    receipt["ledger"] = ledger_pointer

    if usage is not None:
        receipt["usage"] = usage
    if final_text is not None:
        receipt["final_text_excerpt"] = _excerpt(final_text)

    # 改版批次擴鍵（machine-invariant 選填，缺席＝不寫 key——現行 None 慣例）
    intent_review = raw.get("intent_review")
    if intent_review is not None:
        if not isinstance(intent_review, dict):
            raise NormalizeError(
                f"`intent_review` must be an object for receipt_normalize, "
                f"got {type(intent_review).__name__}"
            )
        receipt["intent_review"] = intent_review
    plan_hash_source = raw.get("plan_hash_source")
    if plan_hash_source is not None:
        if not isinstance(plan_hash_source, str):
            raise NormalizeError(
                f"`plan_hash_source` must be a string for receipt_normalize, "
                f"got {type(plan_hash_source).__name__}"
            )
        receipt["plan_hash_source"] = plan_hash_source

    return receipt


def validate_normalized(receipt: dict, stage: str = "dispatch") -> list[str]:
    """正規化產物過 S1 validator（DONE-WHEN #3 的 in-process 面；CLI 等價 arc_spec validate）。"""
    return list(_arc.validate("receipt", receipt, stage=stage))


# ---------------------------------------------------------------------------
# 合成視圖（人類可讀：誰／做了什麼／交付了什麼／狀態／帳本指針）
# ---------------------------------------------------------------------------


def render_merged_view(receipts: list[dict], *, title: str, note: str = "") -> str:
    """canonical receipts → 單一 markdown 視圖（純渲染；不改資料）。"""
    lines: list[str] = [f"# {title}", ""]
    if note:
        for note_line in note.splitlines():
            lines.append(f"> {note_line}")
        lines.append("")

    lines += [
        "## 總表",
        "",
        "| # | job | family／model | slice | 狀態 | 交付 verdict | sink |",
        "|---|-----|---------------|-------|------|--------------|------|",
    ]
    for i, r in enumerate(receipts, start=1):
        delivery = r.get("delivery") or {}
        lines.append(
            f"| {i} | `{r.get('job_id')}` | {r.get('family')}／{r.get('model')} "
            f"| `{r.get('slice_id')}` | {r.get('status')} "
            f"| {delivery.get('verdict')} | `{delivery.get('sink', '（receipt-only）')}` |"
        )
    lines.append("")

    for i, r in enumerate(receipts, start=1):
        delivery = r.get("delivery") or {}
        pointer = r.get("ledger") or {}
        usage = r.get("usage")
        lines += [
            f"## {i}. `{r.get('job_id')}`（{r.get('family')}——{r.get('slice_id')}）",
            "",
            f"- **誰**：family=`{r.get('family')}` model=`{r.get('model')}` job=`{r.get('job_id')}`",
        ]
        if r.get("final_text_excerpt"):
            lines.append(f"- **做了什麼**：{r['final_text_excerpt']}")
        sink = delivery.get("sink")
        anchor = delivery.get("anchor_hits") or []
        lines.append(
            f"- **交付了什麼**：mode=`{delivery.get('mode')}` sink=`{sink or '（receipt-only）'}` "
            f"anchor={anchor} verdict=**{delivery.get('verdict')}**"
        )
        status_extra = f"（帳本狀態：{pointer.get('ledger_status')}；exit={pointer.get('exit_code')}）"
        lines.append(f"- **狀態**：{r.get('status')}{status_extra}")
        jsonl = pointer.get("jsonl")
        jsonl_note = f"（jsonl: `{jsonl}`）" if jsonl else ""
        lines.append(
            f"- **帳本指針**：`{pointer.get('path')}#{r.get('job_id')}`{jsonl_note}"
        )
        lines.append(
            f"- **plan 回指**：v{r.get('plan_version')}／`{str(r.get('plan_hash'))[:12]}…`"
            f"（slice=`{r.get('slice_id')}` unit=`{r.get('unit_id')}` card=`{r.get('card_id')}`）"
        )
        if usage:
            rendered = "、".join(f"{k}={usage[k]}" for k in sorted(usage))
            lines.append(f"- **usage**：{rendered}")
        else:
            lines.append("- **usage**：（帳本無此面——缺席非 0）")
        for key, label in (
            ("top_findings", "top findings"),
            ("blockers", "blockers"),
            ("unverified", "unverified"),
            ("pending_human_decision", "pending human decision"),
        ):
            items = r.get(key) or []
            if items:
                joined = "；".join(items)
                lines.append(f"- **{label}**：{joined}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI（開發自檢用；正式收線走 s2_seal_and_validate.sh）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print(
        "receipt_normalize 是純函式庫——呼叫 normalize(family, raw)；"
        "端到端驗證跑 bash .agent-tmp/air-135.1/s2_seal_and_validate.sh",
        file=sys.stderr,
    )
    raise SystemExit(2)
