#!/usr/bin/env python3
"""exception forwarding（AIR-287——db-99 裁定信：needs-human→exception
mail（自帶原文＋來源連結）進專用 exception 地址；dutymail 零改動）。

架構位（db99-ruling-aig-001）：正常信留 LLM 地址全消費（digest 吸收）
；處理中判 needs-human 的信——router 判定＝duty_receive.triage 的
surface 分類（needs-human 同義映射，見下）——組 exception envelope v2
送進專用 exception 地址 `ai-guide-exceptions`（人類面板：人類待辦＝
該地址 unresolved exceptions 計數）。本模組是**消費端**；不改 dutymail。

router（單元可測純函式）：`should_forward(disposition)`——
duty_receive.triage 產出的 Disposition.action=="surface" → True
（surface 語義＝需要人判讀：solicit 恆 surface、未列 class 恆 surface、
恆人工 class 恆 surface——default-deny 三底線使「需要人」分類不被
config 放寬，映射安全）；action=="auto"（digest 吸收＝例行事，人類
面板不顯示）→ False；其他值＝LedgerError（分類詞彙漂移 fail-loud）。

exception mail 內容（db-99 裁定兩要素）：
- 自帶原文：body.original_body＝原信 body 字串逐字（禁靜默截斷——
  組合後超 dutymail body 上限 8192 bytes＝BodyLimitExceeded fail-loud，
  交人手動處理）。
- 來源連結：dutymail 無 URL——正典先例（duty_receive render F2「fallback
  指針須可執行」）＝可執行查詢指針 `dutymail events --address <源地址>`
  ＋source_envelope_id（correlation 鍵，replies scoped 查詢可用）。

body machine-header `class: "exception-forward"`＝消費端約定標記
（先例＝handoff_delivery 的 handoff_delivery 標記、proto §5.9 控制信
body 約定）——非 skills/_common/dutymail-roundtrip.md 六值封閉詞彙成員
，不冒用既有值；default-deny 下即使被 duty_receive 處理也恆 surface
（exception 地址本就人類消費、不註冊 duty hook，此為深度防護非依賴）。

dutymail write 面紀律：`forward`＝dutymail send——outward action
（收件方 undo 前可觀察），逐次授權紀律同 skills/handoff「dutymail 直
送＝outward action」；本腳本不自動送——由消費端 session 在 needs-human
判定後顯式呼叫。`init`＝dutymail address create（AIR-287 唯一授權
write 面，author 一次性執行）＋建立記錄入 ledger meta（證據落帳）。

typed contract 單一源：duty_receive._call／DutymailFaceError（stdout
JSON 契約、shape-drift fail-loud）——本檔零複製。acceptance 三鍵
（envelopeId／acceptanceSeq／envelopeSha256）缺一＝shape-drift。

CLI（exit 0 成功／1 typed 錯誤／2 args 誤用；runner／policy_path／
now_us／uuid4／tmp_dir 可注入——測試零真 store 往返）：
    decision --canonical-file PATH [--config PATH]
        只跑 router（dry，零 write）→ stdout JSON {"forward": bool}
    forward  --source-address ALIAS --canonical-file PATH --session-id ID
             [--exception-address ALIAS] [--config PATH] [--force]
        router 閘過→組信→send→stdout acceptance JSON
    init     [--alias ALIAS] [--session-id ID] [--base-dir DIR]
        address create＋ledger meta 記錄（本卡唯一授權 write 面）
"""

import argparse
import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid as _uuid

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)


def _load_core(rel_name, module_key):
    """以檔案路徑載入 repo 內腳本（scripts/ 非 package——CLI 直跑與
    load_module 測試形態下 sys.path 不可依賴，一律顯式路徑載入）。"""
    spec = importlib.util.spec_from_file_location(
        module_key, os.path.join(_HERE, rel_name)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


duty_receive = _load_core("duty_receive.py", "_duty_receive_fwd_core")
dd = _load_core("duty_disposition.py", "_duty_disposition_fwd_core")

DEFAULT_CONFIG_PATH = duty_receive.DEFAULT_CONFIG_PATH
EXCEPTION_ADDRESS = "ai-guide-exceptions"
BODY_LIMIT_BYTES = 8192  # envelope v2 凍結 grammar：body UTF-8 ≤8192
EXCEPTION_CLASS = "exception-forward"  # 消費端約定標記（見 docstring）
TAG = "duty-exception-forward"


class CompositionError(RuntimeError):
    """exception envelope 組合前提不成立（canonical 缺 envelope_id／
    body 非字串——v2 凍結 grammar 違反，fail-loud 禁靜默降級）。"""


class BodyLimitExceeded(CompositionError):
    """組合後 body 超 dutymail 上限——禁靜默截斷（自帶原文是裁定
    要素，截斷＝資料損失），交人手動處理。"""


class LedgerError(RuntimeError):
    """router 分類詞彙漂移（Disposition.action 非 surface|auto）。"""


# ── router（純函式——單元可測）───────────────────────────────────────


def should_forward(disposition):
    """triage Disposition → 是否轉 exception 地址。

    surface（＝needs-human 同義映射）→ True；auto（digest 吸收）→
    False；其他＝LedgerError（分類詞彙漂移 fail-loud）。
    """
    action = getattr(disposition, "action", None)
    if action == "surface":
        return True
    if action == "auto":
        return False
    raise LedgerError(
        f"Disposition.action 非法：{action!r}（得 surface|auto）"
    )


# ── envelope 組合（v2 凍結 grammar；測試注入 uuid4／now_us）──────────


def compose_exception_envelope(
    source_address, canonical_env, session_id, exception_address=None,
    now_us=None, uuid4=None,
):
    """canonical envelope dict → exception envelope v2 dict。

    前提（CompositionError fail-loud）：canonical_env 為 dict、帶非空
    字串 envelope_id、body 為字串（v2 grammar：body＝字串）。
    """
    if not isinstance(canonical_env, dict):
        raise CompositionError(
            f"canonical envelope 非 dict：{type(canonical_env)}"
        )
    source_envelope_id = canonical_env.get("envelope_id")
    if not isinstance(source_envelope_id, str) or not source_envelope_id:
        raise CompositionError(
            f"canonical envelope 缺 envelope_id：{sorted(canonical_env)}"
        )
    original_body = canonical_env.get("body")
    if not isinstance(original_body, str):
        raise CompositionError(
            f"canonical envelope body 非字串：{type(original_body)}"
        )
    exc_addr = (
        exception_address
        if exception_address is not None
        else EXCEPTION_ADDRESS
    )
    body_doc = {
        "class": EXCEPTION_CLASS,
        "source_address": source_address,
        "source_envelope_id": source_envelope_id,
        # 來源連結＝可執行查詢指針（duty_receive render F2 先例）
        "source_query": f"dutymail events --address {source_address}",
        "original_body": original_body,
        "forwarded_by": session_id,
    }
    body = json.dumps(body_doc, ensure_ascii=False, sort_keys=True)
    size = len(body.encode("utf-8"))
    if size > BODY_LIMIT_BYTES:
        raise BodyLimitExceeded(
            f"exception body {size} bytes > 上限 {BODY_LIMIT_BYTES}"
            f"（源信 {source_envelope_id}）——禁靜默截斷，人工處理"
        )
    return {
        "schema_version": 2,
        "message_id": str((uuid4 or _uuid.uuid4)()),
        "envelope_id": str((uuid4 or _uuid.uuid4)()),
        "from": {"session_id": session_id, "name": None, "harness": None},
        "to": {"address": exc_addr},
        "delivery": {
            "mode": "queue",
            "fallback": None,
            "intent": "solicit",  # 需要人判讀——solicit 語義正確
            "wake": "none",
            "fallback_used": False,
        },
        "created_at_us": (
            now_us if now_us is not None else time.time_ns() // 1000
        ),
        "body": body,
    }


# ── send face（typed contract 單一源＝duty_receive._call）────────────


def send_envelope(runner, envelope, tmp_dir=None):
    """dutymail send（--envelope-file 檔案面）→ acceptance result dict。

    acceptance 三鍵（envelopeId／acceptanceSeq／envelopeSha256）＝
    queued-visible 證據（handoff skill 審計錨條款同源）；缺一＝
    shape-drift DutymailFaceError。測試注入 runner 零真 store 往返。
    """
    parent = tmp_dir if tmp_dir is not None else tempfile.gettempdir()
    os.makedirs(parent, exist_ok=True)
    path = os.path.join(parent, "exception-envelope.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(envelope, fh, ensure_ascii=False, sort_keys=True)
    result = duty_receive._call(
        runner, ["send", "--envelope-file", path],
    )
    missing = [
        k for k in ("envelopeId", "acceptanceSeq", "envelopeSha256")
        if k not in result
    ]
    if missing:
        raise duty_receive.DutymailFaceError(
            "shape-drift", "unknown",
            f"send acceptance 缺鍵 {missing}：{sorted(result)}",
            False, 0,
        )
    return result


# ── forward（router 閘→組信→send；零自動——由消費端顯式呼叫）────────


def forward(
    source_address, canonical_env, session_id, runner, policy,
    exception_address=None, now_us=None, uuid4=None, force=False,
    tmp_dir=None,
):
    """needs-human 判定 → exception mail → (decision, acceptance|None)。

    decision＝force 或 should_forward(triage(canonical, policy))；
    decision False＝不 send（auto 分類信留 LLM 地址全消費——db-99
    裁定，人類面板不顯示）。
    """
    item = {
        "envelopeId": canonical_env.get("envelope_id"),
        "canonicalEnvelope": json.dumps(
            canonical_env, ensure_ascii=False, sort_keys=True
        ),
    }
    disposition = duty_receive.triage(item, policy)
    decision = bool(force) or should_forward(disposition)
    if not decision:
        return False, None
    envelope = compose_exception_envelope(
        source_address, canonical_env, session_id,
        exception_address=exception_address, now_us=now_us, uuid4=uuid4,
    )
    return True, send_envelope(runner, envelope, tmp_dir=tmp_dir)


# ── init face（本卡唯一授權 dutymail write 面）───────────────────────


def init_exception_address(alias, session_id, runner, base_dir=None,
                           now_us=None):
    """dutymail address create＋建立記錄入 ledger meta（證據落帳——
    建立記錄失敗＝fail-loud raise，禁「建了沒記」）。"""
    result = duty_receive._call(
        runner, ["address", "create", "--alias", alias],
    )
    dd.write_exception_address_record(
        alias, result, session_id,
        now_us if now_us is not None else time.time_ns() // 1000,
        base_dir=base_dir,
    )
    return result


# ── CLI 面 ───────────────────────────────────────────────────────────


def _read_canonical(path):
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict):
        raise CompositionError(f"canonical file 非 JSON object：{path}")
    return doc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "exception forwarding（AIR-287；needs-human→exception mail"
            "——dutymail 零改動；send＝outward 逐次授權）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dec = sub.add_parser(
        "decision", help="只跑 router（dry，零 write）",
    )
    p_dec.add_argument("--canonical-file", required=True, metavar="PATH")
    p_dec.add_argument("--config", default=DEFAULT_CONFIG_PATH,
                       metavar="PATH")

    p_fwd = sub.add_parser(
        "forward", help="router 閘→組信→dutymail send（outward）",
    )
    p_fwd.add_argument("--source-address", required=True, metavar="ALIAS")
    p_fwd.add_argument("--canonical-file", required=True, metavar="PATH")
    p_fwd.add_argument("--session-id", required=True, metavar="ID")
    p_fwd.add_argument("--exception-address", default=EXCEPTION_ADDRESS,
                       metavar="ALIAS")
    p_fwd.add_argument("--config", default=DEFAULT_CONFIG_PATH,
                       metavar="PATH")
    p_fwd.add_argument("--force", action="store_true",
                       help="auto 分類也強制轉（消費端已判 needs-human）")
    p_fwd.add_argument("--base-dir", default=None, metavar="DIR",
                       help="tmp envelope 檔目錄覆寫（預設系統 temp）")

    p_init = sub.add_parser(
        "init", help="address create＋建立記錄入 ledger meta（授權面）",
    )
    p_init.add_argument("--alias", default=EXCEPTION_ADDRESS,
                        metavar="ALIAS")
    p_init.add_argument("--session-id", required=True, metavar="ID")
    p_init.add_argument("--base-dir", default=None, metavar="DIR",
                        help="ledger 根覆寫（預設 XDG state）")
    return parser.parse_args(argv)


def main(argv=None, runner=None, policy_path=None) -> int:
    args = parse_args(argv)
    real_runner = runner if runner is not None else (
        duty_receive._default_runner
    )
    try:
        if args.command == "decision":
            policy = duty_receive.load_policy(
                policy_path if policy_path is not None else args.config
            )
            item = {
                "envelopeId": None,
                "canonicalEnvelope": json.dumps(
                    _read_canonical(args.canonical_file),
                    ensure_ascii=False,
                ),
            }
            decision = should_forward(duty_receive.triage(item, policy))
            print(json.dumps({"forward": decision}, ensure_ascii=False))
        elif args.command == "forward":
            policy = duty_receive.load_policy(
                policy_path if policy_path is not None else args.config
            )
            decision, acceptance = forward(
                args.source_address, _read_canonical(args.canonical_file),
                args.session_id, real_runner, policy,
                exception_address=args.exception_address, force=args.force,
                tmp_dir=args.base_dir,
            )
            if not decision:
                print(json.dumps(
                    {"forward": False, "reason": "auto-classified"
                     "（digest 吸收——人類面板不顯示）"},
                    ensure_ascii=False,
                ))
                return 0
            print(json.dumps(
                {"forward": True, "acceptance": acceptance},
                ensure_ascii=False, sort_keys=True,
            ))
        else:  # init
            init_exception_address(
                args.alias, args.session_id, real_runner,
                base_dir=args.base_dir,
            )
            print(f"[{TAG}] {args.alias} 建立記錄已入 ledger meta")
    except (
        duty_receive.DutymailFaceError,
        duty_receive.BinaryMissing,
        duty_receive.ConfigError,
        CompositionError,
        LedgerError,
        OSError,
        ValueError,
    ) as exc:
        print(f"[{TAG}] typed failure：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
