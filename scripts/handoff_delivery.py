#!/usr/bin/env python
"""handoff scbus 直送純邏輯層（AIR-156）——completion 四段分類＋target 分流＋body 組裝。

單一源關係：delivery 條文權威＝skills/handoff/SKILL.md「Delivery——scbus 直送」節；
本檔只承載條文中可純函式化的判定，供 tests/test_handoff_delivery.py 鎖行為——
改條文必同步改這裡與測試。純邏輯零 I/O（CLI 的檔案讀取除外）：呼叫端（session
流程）負責跑 `scbus list`／`scbus send`、餵 dict／檔。

契約錨（card AIR-156 已決策勿重辯）：
- receipt＝queued-visible 非完成（scbus proto §5.7 兩 stage 一次寫成、§5.8
  consume 兩態、無 ack／user-read 第三態）；transport receipt ≠ semantic ACK，
  禁互升格（governance/conventions.md 節一對照表＝審計錨）。
- 已知 session 第一路＝scbus send；未知／歧義／self／ended fail-closed 降
  manual paste fallback。
- scbus 直送＝outward action（AI 發起逐次授權，rules/outward-action-consent）；
  跨 ownership envelope 的 delivery body 必帶 consent.evidence（AUTH 指針）。
- 訊息結構欄對齊 governance/conventions.md 節一 v2（want/card_ref/
  correlation_id/expires_at/artifact_pointers）；msg_type 四值枚舉不涵蓋
  handoff 交接，本檔不發 msg_type 欄（晉升共用 schema 須 conventions amendment）。

CLI exit 契約：0＝ok、非零＝fail loud（2＝contract 錯）。
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

BUS_BODY_MAX_BYTES = 8192  # scbus 凍結面（proto §5.1 body ≤8192）

REPLY_TYPES = frozenset({"accept", "needs-info", "declined", "completed"})
COMPLETED_REQUIRED_FIELDS = ("result_pointer", "evidence")


class DeliveryContractError(Exception):
    """delivery 契約違反（資料序、審計錨不對、consent gate 攔）——fail loud，禁靜默。"""


class CompletionStage(StrEnum):
    """交接完成四段（card AIR-156 已決策）。"""

    PACKET_PRODUCED = "packet-produced"
    QUEUED_VISIBLE = "queued-visible"
    CONSUMED_ACCEPTED = "consumed-accepted"
    OWNERSHIP_RESTORED = "ownership-restored"


class TargetDisposition(StrEnum):
    """target 解析分流：已知 session 直送第一路／其餘降 manual paste。"""

    KNOWN_DIRECT = "known-direct"
    FALLBACK_MANUAL = "fallback-manual"


@dataclass(frozen=True)
class CompletionTrace:
    stage: CompletionStage  # 最高已確認段
    closed: bool  # ownership-restored 達成（交接完成判定）
    consumed: bool  # transport 面：envelope 已被 recv 消費
    note: str | None  # 中間物理態註記（如已消費未回 ACK）
    blocking: str | None  # declined／needs-info——此路被拒，禁原樣重發


@dataclass(frozen=True)
class TargetResolution:
    disposition: TargetDisposition
    reason: str | None  # fallback 時的原因碼；known-direct 時 None
    session_id: str | None
    name: str | None
    harness: str | None
    workspace_root: str | None
    cross_ownership: bool


def _require(value: object, message: str) -> str:
    if not isinstance(value, str) or not value:
        raise DeliveryContractError(message)
    return value


def classify_completion(
    receipt: dict | None, *, consumed: bool, ack: dict | None
) -> CompletionTrace:
    """依 transport receipt＋consume 態＋semantic ACK 分類完成四段。

    receipt 形＝scbus send 的 receipts/<command_id>.json（proto §5.7 凍結
    schema）；ack 形＝conventions.md 節一回覆欄位（reply_type/in_reply_to
    ＋completed 附加 result_pointer/evidence）。任何契約違反 fail loud。
    """
    if receipt is None:
        if consumed or ack is not None:
            raise DeliveryContractError(
                "transport 未發生（無 receipt）時不得有 consumed／ack——資料序違反"
            )
        return CompletionTrace(
            stage=CompletionStage.PACKET_PRODUCED,
            closed=False,
            consumed=False,
            note=None,
            blocking=None,
        )

    _require(receipt.get("command_id"), "receipt 缺 command_id（proto §5.7 凍結欄）")
    message_id = _require(
        receipt.get("message_id"), "receipt 缺 message_id（審計錨鍵）"
    )
    raw_stages = receipt.get("stages")
    if not isinstance(raw_stages, list) or not all(
        isinstance(s, dict) for s in raw_stages
    ):
        raise DeliveryContractError(
            "receipt.stages 須為 stage 物件陣列（proto §5.7 凍結 schema）——malformed shape"
        )
    stages = {s.get("stage") for s in raw_stages}
    if not {"accepted", "visible"} <= stages:
        raise DeliveryContractError(
            "receipt 應一次寫成 accepted＋visible 兩 stage（proto §5.7）——缺 stage＝損壞"
        )

    if ack is not None and not consumed:
        raise DeliveryContractError(
            "semantic ACK 以 consume 為前置（conventions 對照表）——未消費不得有 ack"
        )
    if not consumed:
        return CompletionTrace(
            stage=CompletionStage.QUEUED_VISIBLE,
            closed=False,
            consumed=False,
            note=None,
            blocking=None,
        )

    if ack is None:
        return CompletionTrace(
            stage=CompletionStage.QUEUED_VISIBLE,
            closed=False,
            consumed=True,
            note="envelope 已消費（recv rename）但無 semantic ACK——consumed/accepted 未閉",
            blocking=None,
        )

    reply_type = _require(ack.get("reply_type"), "ack 缺 reply_type（回覆必填欄）")
    if reply_type not in REPLY_TYPES:
        raise DeliveryContractError(f"reply_type 非四值枚舉：{reply_type!r}")
    if (
        _require(ack.get("in_reply_to"), "ack 缺 in_reply_to（機械追線錨）")
        != message_id
    ):
        raise DeliveryContractError(
            "ack.in_reply_to 與 receipt.message_id 不對——審計錨條款：完成宣稱須兩錨同時對上"
        )

    if reply_type == "completed":
        for field in COMPLETED_REQUIRED_FIELDS:
            _require(ack.get(field), f"reply_type=completed 必帶 {field}——禁權威斷言")
        return CompletionTrace(
            stage=CompletionStage.OWNERSHIP_RESTORED,
            closed=True,
            consumed=True,
            note=None,
            blocking=None,
        )
    if reply_type == "accept":
        return CompletionTrace(
            stage=CompletionStage.CONSUMED_ACCEPTED,
            closed=False,
            consumed=True,
            note=None,
            blocking=None,
        )
    # declined／needs-info——transport 已消費但語義被拒；此路不閉。
    return CompletionTrace(
        stage=CompletionStage.QUEUED_VISIBLE,
        closed=False,
        consumed=True,
        note=None,
        blocking=reply_type,
    )


def resolve_target(
    target: str,
    rows: list[dict],
    *,
    own_session_id: str,
    own_workspace_root: str | None,
) -> TargetResolution:
    """把交接目標對 scbus registry rows 解析成已知直送／fallback 分流。

    rows＝`scbus list` 輸出的 sessions 陣列。解析序：session_id 精確→
    claimed name 精確；ended 列不當 target；多列 live＝ambiguous fail-closed
    （與 scbus send 對撞 id fail-closed 同姿）；own ownership 無法確立時
    cross_ownership 恆 True（consent gate fail-closed）。
    """
    if not isinstance(target, str) or not target:
        raise DeliveryContractError("target 不得為空——交接目標須可指認")

    matches = [
        r
        for r in rows
        if r.get("session_id") == target
        or (r.get("name") is not None and r.get("name") == target)
    ]
    live = [r for r in matches if r.get("status") != "ended"]
    if not live:
        reason = "target-ended" if matches else "no-match"
        return TargetResolution(
            disposition=TargetDisposition.FALLBACK_MANUAL,
            reason=reason,
            session_id=None,
            name=None,
            harness=None,
            workspace_root=None,
            cross_ownership=False,
        )
    if len(live) > 1:
        return TargetResolution(
            disposition=TargetDisposition.FALLBACK_MANUAL,
            reason="ambiguous",
            session_id=None,
            name=None,
            harness=None,
            workspace_root=None,
            cross_ownership=False,
        )
    row = live[0]
    if row.get("session_id") == own_session_id:
        return TargetResolution(
            disposition=TargetDisposition.FALLBACK_MANUAL,
            reason="self",
            session_id=None,
            name=None,
            harness=None,
            workspace_root=None,
            cross_ownership=False,
        )
    target_ws = row.get("workspace_root")
    cross_ownership = (
        own_workspace_root is None
        or target_ws is None
        or own_workspace_root != target_ws
    )
    return TargetResolution(
        disposition=TargetDisposition.KNOWN_DIRECT,
        reason=None,
        session_id=row.get("session_id"),
        name=row.get("name"),
        harness=row.get("harness"),
        workspace_root=target_ws,
        cross_ownership=cross_ownership,
    )


def build_delivery_body(
    *,
    summary: str,
    source: str,
    correlation_id: str,
    want: str,
    card_ref: str | None = None,
    expires_at: str | None = None,
    artifact_pointers: list[str] | None = None,
    cross_ownership: bool = False,
    consent_evidence: str | None = None,
) -> str:
    """組 delivery body——單行 UTF-8 JSON，結構欄對齊 conventions.md 節一 v2。

    consent gate：cross_ownership=True 時 consent_evidence 必填（AI 發起
    逐次授權的 AUTH 指針——transport consent ≠ mutation authority，本欄是
    審計註記非對接收端的授權移轉）。超過 bus 凍結面 8192 位元組＝fail loud。
    """
    for name, value in (
        ("summary", summary),
        ("source", source),
        ("correlation_id", correlation_id),
        ("want", want),
    ):
        if not isinstance(value, str) or not value:
            raise DeliveryContractError(f"{name} 為必填結構欄，不得為空")
    if cross_ownership and not (isinstance(consent_evidence, str) and consent_evidence):
        raise DeliveryContractError(
            "跨 ownership envelope 直送必帶 consent.evidence（user 逐次授權的 AUTH 指針）——consent gate"
        )

    body: dict = {
        "handoff_delivery": True,  # 消費端約定標記（先例＝proto §5.9 控制信 body 約定）
        "source": source,
        "correlation_id": correlation_id,
        "want": want,
        "body": summary,
    }
    if card_ref:
        body["card_ref"] = card_ref
    if expires_at:
        body["expires_at"] = expires_at
    if artifact_pointers:
        body["artifact_pointers"] = artifact_pointers
    if cross_ownership:
        body["consent"] = {"granted_by": "user", "evidence": consent_evidence}

    text = json.dumps(body, ensure_ascii=False, sort_keys=True)
    if len(text.encode("utf-8")) > BUS_BODY_MAX_BYTES:
        raise DeliveryContractError(
            f"body 超過 bus 凍結面 {BUS_BODY_MAX_BYTES} 位元組——大材料落 repo 檔案、訊息只派路徑"
        )
    return text


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build-body", help="組單行 JSON delivery body（stdout）")
    p_build.add_argument("--summary", required=True)
    p_build.add_argument("--source", required=True)
    p_build.add_argument("--correlation-id", required=True)
    p_build.add_argument("--want", required=True)
    p_build.add_argument("--card-ref", default=None)
    p_build.add_argument("--expires-at", default=None)
    p_build.add_argument("--artifact-pointers", nargs="*", default=None)
    p_build.add_argument("--cross-ownership", action="store_true")
    p_build.add_argument("--consent-evidence", default=None)

    p_classify = sub.add_parser(
        "classify-completion",
        help="receipt＋consumed＋ack → 完成四段 trace（stdout JSON）",
    )
    p_classify.add_argument("--receipt-file", required=True)
    p_classify.add_argument("--consumed", action="store_true")
    p_classify.add_argument("--ack-file", default=None)

    p_resolve = sub.add_parser(
        "resolve-target",
        help="target＋scbus list rows → 直送/fallback 分流（stdout JSON）",
    )
    p_resolve.add_argument("--target", required=True)
    p_resolve.add_argument("--rows-file", required=True)
    p_resolve.add_argument("--own-session-id", required=True)
    p_resolve.add_argument("--own-workspace-root", default=None)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "build-body":
            print(
                build_delivery_body(
                    summary=args.summary,
                    source=args.source,
                    correlation_id=args.correlation_id,
                    want=args.want,
                    card_ref=args.card_ref,
                    expires_at=args.expires_at,
                    artifact_pointers=args.artifact_pointers,
                    cross_ownership=args.cross_ownership,
                    consent_evidence=args.consent_evidence,
                )
            )
        elif args.cmd == "classify-completion":
            receipt = json.loads(Path(args.receipt_file).read_text())
            ack = json.loads(Path(args.ack_file).read_text()) if args.ack_file else None
            trace = classify_completion(receipt, consumed=args.consumed, ack=ack)
            print(
                json.dumps(
                    {
                        "stage": str(trace.stage),
                        "closed": trace.closed,
                        "consumed": trace.consumed,
                        "note": trace.note,
                        "blocking": trace.blocking,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            loaded = json.loads(Path(args.rows_file).read_text())
            # `scbus list` 原樣輸出＝{"count", "sessions": [...]}；裸 sessions 陣列亦收。
            rows = loaded.get("sessions") if isinstance(loaded, dict) else loaded
            if not isinstance(rows, list):
                raise DeliveryContractError(
                    "rows-file 須為 `scbus list` 輸出（count＋sessions 物件）或 sessions 陣列"
                )
            r = resolve_target(
                args.target,
                rows,
                own_session_id=args.own_session_id,
                own_workspace_root=args.own_workspace_root,
            )
            print(
                json.dumps(
                    {
                        "disposition": str(r.disposition),
                        "reason": r.reason,
                        "session_id": r.session_id,
                        "name": r.name,
                        "harness": r.harness,
                        "workspace_root": r.workspace_root,
                        "cross_ownership": r.cross_ownership,
                    },
                    ensure_ascii=False,
                )
            )
    except DeliveryContractError as exc:
        print(f"contract error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
