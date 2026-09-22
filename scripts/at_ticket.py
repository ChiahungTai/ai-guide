#!/usr/bin/env python3
"""at_ticket — /at 排程接續 ticket 狀態機 helper（AIR-157）.

一句話：/at 的排程 ticket 從「只有 identity/pointer 的自由檔」升為帶生命週期
的狀態機 JSON 檔——五主態 SCHEDULED→ARMED→FIRED→RESTORE_PROVEN→SETTLED
＋四異常態 SCHEDULER_REJECTED／MISSED／RESTORE_FAILED／CANCELLED；轉移表
外的轉移一律 raise fail-loud，cleanup 依 resume_at＋state＋grace 機械判準
（淘汰 mtime——排程超過保留期的未到期 ticket 會被 mtime 邏輯誤刪）。

契約面（AIR-157 已決策勿重辯）：
- **禁靜默降級**：scheduler arm 失敗＝SCHEDULER_REJECTED fail-loud（exit 1
  ＋stderr 診斷），禁退背景 sleep 替代（session 死＝保險全滅——三連敗實證），
  禁改用未驗證 scheduler primitive；不自造 scheduler——本 helper 只記帳，
  arm 本體＝harness verified adapter（Claude 端 CronCreate）
- **arm 成功必有 arm receipt**：轉移到 ARMED 需帶非空 receipt dict
  （jobId 等）——禁無憑 ARMED
- **禁復活**：異常態（SCHEDULER_REJECTED／MISSED／RESTORE_FAILED）回主線
  全數非法；重新排程＝開新 ticket，非改舊票
- **cleanup 機械判準**：只有 SETTLED 或 CANCELLED 才可清，且須
  now ≥ resume_at＋grace；mtime 不參與判定；非 terminal 永不清——sweep
  只分類不刪，刪除是讀面 session 對 cleanable 的顯式後續動作
- **MISSED 誠實標記**：ARMED 超過 resume_at＋tolerance 未見 fire 證據＝
  missed-candidate（sweep 大聲回報），處置＝transition --to MISSED 帶
  unsupported window 證據 note；overnight blind window 無 covering trigger
  ＝unsupported window（偵測面：zcode scheduled task POC 為後續卡）

ticket 檔（schema `at-ticket/1`）：`<project>/.agent-tmp/at-tickets/
<ticketId>.json`，atomic 寫（tmp＋fsync＋os.replace）；讀面對損壞／schema
不符 fail-loud（TicketCorrupt——數據完整性優先：損壞比缺失危險，禁靜默當
不存在）。

用法
----
    uv run python scripts/at_ticket.py new --dir .agent-tmp/at-tickets \
        --goal "繼續 EP 段落 3" --resume-at "<ISO 8601 with tz>" \
        [--task-ref ...] [--owner-ref ...] [--project-path ...] [--ticket-id ...]
    uv run python scripts/at_ticket.py transition --ticket <path> --to <STATE> \
        [--arm-receipt-json '<json>'] [--reason "..."] [--note "..."]
    uv run python scripts/at_ticket.py reject --ticket <path> --reason "..."
    uv run python scripts/at_ticket.py classify [--dir .agent-tmp/at-tickets] \
        [--grace-s N] [--missed-after-s N]

exit：0＝成功；1＝fail-loud（IllegalTransition／TicketCorrupt／旗標語義錯
／reject——reject 的記錄已落地但事件本身是失敗，呼叫鏈須停，禁續行降級）；
2＝argparse 旗標錯。classify 對 missed-candidate／past-due 另上 stderr
（大聲回報，不擋 exit 0——分類本身成功）。
"""

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCHEMA = "at-ticket/1"
# ticket 慣例路徑（<project> 相對；與 .agent-tmp 暫存慣例同面——AIR-157）
TICKETS_DIRNAME = Path(".agent-tmp") / "at-tickets"

MAIN_STATES: tuple[str, ...] = (
    "SCHEDULED",
    "ARMED",
    "FIRED",
    "RESTORE_PROVEN",
    "SETTLED",
)
EXCEPTION_STATES: tuple[str, ...] = (
    "SCHEDULER_REJECTED",
    "MISSED",
    "RESTORE_FAILED",
    "CANCELLED",
)
ALL_STATES: frozenset[str] = frozenset(MAIN_STATES + EXCEPTION_STATES)
# 可清＝生命週期走到「好結局」或「明示取消」——其餘狀態禁清（AIR-157 AC#3）
CLEANABLE_STATES: frozenset[str] = frozenset({"SETTLED", "CANCELLED"})

# 合法轉移表（狀態契約單一源；表外 raise IllegalTransition）。
# 主線：SCHEDULED→ARMED（arm receipt）→FIRED→RESTORE_PROVEN→SETTLED。
# 異常：arm 被拒（SCHEDULED）、fire 沒來（ARMED→MISSED）、恢復失敗
# （FIRED→RESTORE_FAILED）；異常態唯一出口＝CANCELLED（明示處置）。
TRANSITIONS: dict[str, frozenset[str]] = {
    "SCHEDULED": frozenset({"ARMED", "SCHEDULER_REJECTED", "CANCELLED"}),
    "ARMED": frozenset({"FIRED", "MISSED", "CANCELLED"}),
    "FIRED": frozenset({"RESTORE_PROVEN", "RESTORE_FAILED"}),
    "RESTORE_PROVEN": frozenset({"SETTLED"}),
    "SETTLED": frozenset(),
    "SCHEDULER_REJECTED": frozenset({"CANCELLED"}),
    "MISSED": frozenset({"CANCELLED"}),
    "RESTORE_FAILED": frozenset({"CANCELLED"}),
    "CANCELLED": frozenset(),
}

# cleanup grace：terminal 後自 resume_at 起的保留期（證據留存；
# dogfood 複核點——air-157 結案後依實際清淤節奏複核此常數）
CLEANUP_GRACE_S = 7 * 86400
# MISSED tolerance：ARMED 超過 resume_at 此秒數仍無 fire 證據＝標記候選
# （時鐘誤差窗；dogfood 複核點——同上，依 sweep 實際命中複核）
MISSED_AFTER_S = 3600


class TicketCorrupt(ValueError):
    """ticket 檔損壞／schema 不符——fail-loud，禁靜默當不存在."""


class IllegalTransition(ValueError):
    """轉移表外的狀態轉移——fail-loud（禁復活禁跳級）."""


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _sanitize(component: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", component)
    return cleaned or "unnamed"


def new_ticket(
    *,
    ticket_id: str,
    goal: str,
    resume_at: datetime,
    scheduled_at: datetime | None = None,
    task_ref: str = "ad-hoc",
    owner_ref: str = "none",
    project_path: str = "",
    now: datetime | None = None,
) -> dict:
    """建立 SCHEDULED ticket（in-memory dict；落地走 write_ticket）.

    `resume_at` 須 tz-aware（naive＝ValueError——時區不明確的排程禁入帳）；
    `now` 僅測試注入面。ticket 只承載任務身份與指針（taskRef/ownerRef），
    規格與 read-set 住 durable owner——禁抄進 ticket（checkpoint-first）。
    """
    if not isinstance(resume_at, datetime) or resume_at.tzinfo is None:
        raise ValueError(f"resume_at 需 tz-aware datetime：{resume_at!r}")
    if not goal.strip():
        raise ValueError("goal 需非空（任務目標一行）")
    created = now or datetime.now(tz=UTC)
    return {
        "schema": SCHEMA,
        "ticketId": ticket_id,
        "state": "SCHEDULED",
        "goal": goal,
        "scheduledAt": _iso(scheduled_at or created),
        "resumeAt": _iso(resume_at),
        "taskRef": task_ref,
        "ownerRef": owner_ref,
        "projectPath": project_path,
        "history": [
            {
                "at": _iso(created),
                "from": None,
                "to": "SCHEDULED",
                "note": "created",
            }
        ],
        "updatedAt": _iso(created),
    }


def _validate(ticket: object) -> list[str]:
    """schema `at-ticket/1` 驗證——回問題清單（空＝合法）."""
    if not isinstance(ticket, dict):
        return ["非 JSON object"]
    problems: list[str] = []
    if ticket.get("schema") != SCHEMA:
        problems.append(f"schema 需 {SCHEMA}：{ticket.get('schema')!r}")
    if not isinstance(ticket.get("ticketId"), str) or not ticket["ticketId"]:
        problems.append("ticketId 需非空字串")
    if ticket.get("state") not in ALL_STATES:
        problems.append(f"state 非法：{ticket.get('state')!r}")
    if not isinstance(ticket.get("goal"), str) or not ticket["goal"]:
        problems.append("goal 需非空字串")
    for key in ("scheduledAt", "resumeAt"):
        if _parse_iso(ticket.get(key, "")) is None:
            problems.append(f"{key} 需 tz-aware ISO 時間：{ticket.get(key)!r}")
    for key in ("taskRef", "ownerRef", "projectPath", "updatedAt"):
        if not isinstance(ticket.get(key), str):
            problems.append(f"{key} 需字串")
    history = ticket.get("history")
    if not isinstance(history, list) or not all(
        isinstance(h, dict) and h.get("to") in ALL_STATES for h in history
    ):
        problems.append("history 需非空 list[dict]（每列 to 為合法狀態）")
    return problems


def read_ticket(path: Path) -> dict:
    """讀 ticket——缺失自然 FileNotFoundError；損壞／schema 不符＝TicketCorrupt."""
    try:
        raw = path.read_text()
    except FileNotFoundError:
        raise  # 缺席＝自然缺席（呼叫端自帶路徑）；損壞才是 TicketCorrupt 面
    except OSError as exc:
        raise TicketCorrupt(f"{path} 不可讀：{exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TicketCorrupt(f"{path} 不可解析：{exc}") from exc
    problems = _validate(payload)
    if problems:
        raise TicketCorrupt(f"{path} schema 不符：{'；'.join(problems)}")
    return payload


def write_ticket(path: Path, ticket: dict) -> None:
    """atomic 寫：schema 驗證→tmp 檔＋fsync→os.replace（禁半寫、異常清 .tmp 殘留）."""
    problems = _validate(ticket)
    if problems:
        raise TicketCorrupt(f"拒寫 schema 不符 ticket：{'；'.join(problems)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = (json.dumps(ticket, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        tmp.unlink(missing_ok=True)  # 寫入失敗禁殘留 .tmp（暫存集中紀律）
        raise
    finally:
        os.close(fd)
    os.replace(tmp, path)


def apply_transition(
    ticket: dict,
    target: str,
    *,
    now: datetime,
    note: str | None = None,
    arm_receipt: dict | None = None,
    reason: str | None = None,
) -> dict:
    """合法轉移（表外 raise IllegalTransition）；原地更新並落 history row.

    憑證要求：ARMED 需非空 `arm_receipt` dict（arm 成功必有回執）；
    SCHEDULER_REJECTED／RESTORE_FAILED 需 `reason`（arm 失敗／恢復失敗
    診斷——禁靜默）；MISSED 需 `note`（unsupported window 證據——誠實
    標記）。`now` 由呼叫端注入（CLI＝牆鐘；測試面注入）。
    """
    if target not in ALL_STATES:
        raise ValueError(f"未知狀態：{target!r}（合法集：{sorted(ALL_STATES)}）")
    current = ticket["state"]
    allowed = TRANSITIONS.get(current)
    if allowed is None:
        # 轉移表外的 current state＝檔損壞面——顯式 TicketCorrupt 禁裸 KeyError
        raise TicketCorrupt(
            f"ticket state 非法（轉移表無此狀態）：{current!r}——檔損壞，禁轉移"
        )
    if target not in allowed:
        raise IllegalTransition(
            f"非法轉移 {current} → {target}"
            f"（合法：{sorted(allowed) or '無——terminal'}）；"
            "狀態機禁復活禁跳級（重新排程＝開新 ticket）"
        )
    if target == "ARMED" and not (isinstance(arm_receipt, dict) and arm_receipt):
        raise ValueError("ARMED 需 arm receipt（非空 dict）——arm 成功必有回執")
    if target == "SCHEDULER_REJECTED" and not (
        isinstance(reason, str) and reason.strip()
    ):
        raise ValueError("SCHEDULER_REJECTED 需 reason——arm 失敗診斷禁靜默")
    if target == "RESTORE_FAILED" and not (isinstance(reason, str) and reason.strip()):
        raise ValueError("RESTORE_FAILED 需 reason——恢復失敗診斷禁靜默")
    if target == "MISSED" and not (isinstance(note, str) and note.strip()):
        raise ValueError("MISSED 需 note——unsupported window 證據（誠實標記）")
    row: dict = {
        "at": _iso(now),
        "from": current,
        "to": target,
        "note": note,
    }
    if target == "ARMED":
        row["armReceipt"] = arm_receipt
    if target in {"SCHEDULER_REJECTED", "RESTORE_FAILED"}:
        row["reason"] = reason
    ticket["state"] = target
    ticket["updatedAt"] = _iso(now)
    ticket["history"].append(row)
    return ticket


def _resume_of(ticket: dict) -> datetime:
    resume = _parse_iso(ticket.get("resumeAt", ""))
    if resume is None:
        raise TicketCorrupt(f"resumeAt 不可解析：{ticket.get('resumeAt')!r}")
    return resume


def cleanable(ticket: dict, *, now: datetime, grace_s: int = CLEANUP_GRACE_S) -> bool:
    """AC#3 判準：SETTLED/CANCELLED 才可清，且 now ≥ resume_at＋grace.

    mtime 不參與（舊 mtime>7d 邏輯會誤刪長程排程的未到期 ticket——AIR-157
    淘汰標的）；非 terminal 永遠回 False。
    """
    if ticket["state"] not in CLEANABLE_STATES:
        return False
    return now >= _resume_of(ticket) + timedelta(seconds=grace_s)


def classify(
    ticket: dict,
    *,
    now: datetime,
    grace_s: int = CLEANUP_GRACE_S,
    missed_after_s: int = MISSED_AFTER_S,
) -> dict:
    """單票分類（sweep 只分類不刪——刪除＝session 對 cleanable 的顯式後續）.

    bucket：cleanable（terminal＋grace 已過）／missed-candidate（ARMED 過
    resume_at 超過 tolerance 未 fire——MISSED 誠實標記候選）／past-due（排
    程時刻已過且生命週期未完——禁清，需處置）／hold（進行中或 terminal 保
    留期未滿）。
    """
    state = ticket["state"]
    resume = _resume_of(ticket)
    base = {
        "ticketId": ticket["ticketId"],
        "state": state,
        "resumeAt": ticket["resumeAt"],
    }
    if cleanable(ticket, now=now, grace_s=grace_s):
        return {**base, "bucket": "cleanable", "reason": f"{state}＋grace 已過"}
    overdue_s = (now - resume).total_seconds()
    if state == "ARMED" and overdue_s >= missed_after_s:
        return {
            **base,
            "bucket": "missed-candidate",
            "reason": "ARMED 過期未 fire——MISSED 誠實標記候選"
            "（查證 unsupported window 後 transition --to MISSED 帶 note）",
        }
    if state not in CLEANABLE_STATES and overdue_s >= missed_after_s:
        return {
            **base,
            "bucket": "past-due",
            "reason": "排程時刻已過且生命週期未完——禁清，需處置"
            "（arm/reject/cancel/settle 擇一收尾）",
        }
    return {**base, "bucket": "hold", "reason": "進行中或 terminal 保留期未滿"}


def sweep_dir(
    tickets_dir: Path,
    *,
    now: datetime,
    grace_s: int = CLEANUP_GRACE_S,
    missed_after_s: int = MISSED_AFTER_S,
) -> list[dict]:
    """掃 ticket 目錄逐票分類（*.json；損壞票 fail-loud 禁靜默跳過）."""
    if not tickets_dir.is_dir():
        return []
    return [
        classify(
            read_ticket(path),
            now=now,
            grace_s=grace_s,
            missed_after_s=missed_after_s,
        )
        for path in sorted(tickets_dir.glob("*.json"))
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_reject_diagnosis(reason: str) -> None:
    print(
        "[at_ticket] SCHEDULER_REJECTED——排程 arm 失敗，已落票記錄\n"
        f"  reason: {reason}\n"
        "  禁靜默降級：禁退背景 sleep 替代（session 死＝保險全滅），"
        "禁改用未驗證 scheduler primitive\n"
        "  處置：向 user 回報 arm 失敗，或 transition --to CANCELLED 結案；\n"
        "  本 ticket 非 terminal 禁清——sweep 會持續大聲回報 past-due",
        file=sys.stderr,
    )


def _cmd_new(args: argparse.Namespace) -> int:
    resume_at = _parse_iso(args.resume_at)
    if resume_at is None:
        raise ValueError(f"--resume-at 需 tz-aware ISO 時間：{args.resume_at!r}")
    scheduled_at: datetime | None = None
    if args.scheduled_at:
        scheduled_at = _parse_iso(args.scheduled_at)
        if scheduled_at is None:
            raise ValueError(
                f"--scheduled-at 需 tz-aware ISO 時間：{args.scheduled_at!r}"
            )
    ticket_id = args.ticket_id or f"at-{resume_at:%Y%m%d-%H%M}"
    path = args.dir / f"{_sanitize(ticket_id)}.json"
    if path.exists():
        raise ValueError(f"ticket 已存在，禁靜默覆蓋：{path}（新任務請換 id）")
    ticket = new_ticket(
        ticket_id=ticket_id,
        goal=args.goal,
        resume_at=resume_at,
        scheduled_at=scheduled_at,
        task_ref=args.task_ref,
        owner_ref=args.owner_ref,
        project_path=args.project_path,
    )
    write_ticket(path, ticket)
    print(
        json.dumps(
            {
                "ticketId": ticket_id,
                "path": str(path),
                "state": "SCHEDULED",
                "resumeAt": ticket["resumeAt"],
            },
            ensure_ascii=False,
        )
    )
    return 0


def _cmd_transition(args: argparse.Namespace) -> int:
    ticket = read_ticket(args.ticket)
    arm_receipt = json.loads(args.arm_receipt_json) if args.arm_receipt_json else None
    apply_transition(
        ticket,
        args.target,
        now=datetime.now(tz=UTC),
        note=args.note,
        arm_receipt=arm_receipt,
        reason=args.reason,
    )
    write_ticket(args.ticket, ticket)
    print(
        json.dumps(
            {"ticket": str(args.ticket), "state": ticket["state"]},
            ensure_ascii=False,
        )
    )
    if ticket["state"] == "SCHEDULER_REJECTED":
        _print_reject_diagnosis(args.reason or "")
        return 1  # 記錄已落地但事件＝fail-loud——呼叫鏈禁續行降級
    return 0


def _cmd_reject(args: argparse.Namespace) -> int:
    ticket = read_ticket(args.ticket)
    apply_transition(
        ticket,
        "SCHEDULER_REJECTED",
        now=datetime.now(tz=UTC),
        reason=args.reason,
    )
    write_ticket(args.ticket, ticket)
    _print_reject_diagnosis(args.reason)
    return 1  # fail-loud：呼叫鏈（/at session）見非零即停，禁退背景 sleep


def _cmd_classify(args: argparse.Namespace) -> int:
    rows = sweep_dir(
        args.dir,
        now=datetime.now(tz=UTC),
        grace_s=args.grace_s,
        missed_after_s=args.missed_after_s,
    )
    print(json.dumps(rows, ensure_ascii=False))
    for row in rows:
        if row["bucket"] in {"missed-candidate", "past-due"}:
            # 大聲回報不擋 exit 0——分類本身成功，處置歸 session
            print(
                f"[at_ticket] {row['bucket']}: {row['ticketId']}"
                f"（{row['state']}）——{row['reason']}",
                file=sys.stderr,
            )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="at_ticket",
        description="/at ticket 狀態機 helper（AIR-157）——轉移表外 raise "
        "fail-loud；cleanup 依 resume_at＋state＋grace（淘汰 mtime）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="建立 SCHEDULED ticket（atomic 寫）")
    p_new.add_argument("--dir", type=Path, default=TICKETS_DIRNAME)
    p_new.add_argument("--goal", required=True, help="任務目標一行")
    p_new.add_argument(
        "--resume-at",
        dest="resume_at",
        required=True,
        help="觸發時刻（ISO 8601 帶 tz）",
    )
    p_new.add_argument("--scheduled-at", dest="scheduled_at", default=None)
    p_new.add_argument("--task-ref", dest="task_ref", default="ad-hoc")
    p_new.add_argument("--owner-ref", dest="owner_ref", default="none")
    p_new.add_argument("--project-path", dest="project_path", default="")
    p_new.add_argument(
        "--ticket-id",
        dest="ticket_id",
        default=None,
        help="缺省＝at-{resume_at %%Y%%m%%d-%%H%%M}",
    )

    p_tr = sub.add_parser("transition", help="合法轉移（表外 fail-loud）")
    p_tr.add_argument("--ticket", type=Path, required=True)
    p_tr.add_argument("--to", dest="target", required=True, metavar="STATE")
    p_tr.add_argument(
        "--arm-receipt-json",
        dest="arm_receipt_json",
        default=None,
        help="轉移 ARMED 必帶（非空 JSON object——arm 回執）",
    )
    p_tr.add_argument(
        "--reason",
        default=None,
        help="轉移 SCHEDULER_REJECTED／RESTORE_FAILED 必帶（失敗診斷禁靜默）",
    )
    p_tr.add_argument("--note", default=None, help="轉移 MISSED 必帶")

    p_rej = sub.add_parser(
        "reject",
        help="arm 失敗專用——SCHEDULER_REJECTED fail-loud（exit 1；禁靜默降級）",
    )
    p_rej.add_argument("--ticket", type=Path, required=True)
    p_rej.add_argument("--reason", required=True)

    p_cls = sub.add_parser(
        "classify", help="清淤分類（resume_at＋state＋grace；只分類不刪）"
    )
    p_cls.add_argument("--dir", type=Path, default=TICKETS_DIRNAME)
    p_cls.add_argument("--grace-s", type=int, default=CLEANUP_GRACE_S)
    p_cls.add_argument("--missed-after-s", type=int, default=MISSED_AFTER_S)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    handlers = {
        "new": _cmd_new,
        "transition": _cmd_transition,
        "reject": _cmd_reject,
        "classify": _cmd_classify,
    }
    try:
        return handlers[args.command](args)
    except (TicketCorrupt, IllegalTransition, ValueError, OSError) as exc:
        print(f"[at_ticket] fail-loud: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
