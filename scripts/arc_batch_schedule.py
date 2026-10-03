#!/usr/bin/env python
"""arc_batch_schedule——AIR-246：ArcPlan temporal_allocation 的第一個真正
temporal consumer（deterministic batch scheduling）。

語義（codex §D 契約——勿重辯）：

- 時間閘：`planned_not_before` 未來（> now）的 arc 不進 eligible set；時間到
  （now >= planned_not_before，邊界含）才進。`now` 一律顯式注入（禁裸
  datetime.now——signature 釘死 keyword-only 無預設，測試機驗；AIR-239 R2
  單一時鐘姿態：時鐘一律注入）。naive（無時區）now／planned_not_before＝
  不合法（禁與 aware 值混比，arc_spec._parse_iso_utc 同姿態）。
- 排序（非新 priority engine）：priority 為主鍵（呼叫端既有 priority 語義，
  本模組不發明 priority 也不讀第二來源）；同 priority 內 temporal 只做
  tiebreak——無 planned_not_before（無時間下界＝隨時可開工）先於有界者、
  有界者早窗先；鍵全同者保持輸入順序（queue stable order）。推論：全體無
  temporal 意圖的輸入，輸出＝純 priority 穩定排序（既有語義完全不動）。
- authority 邊界（C checker 不被繞）：preferred_family／fallback_families 屬
  advisory planning evidence——只能影響排程/排序；dispatch 與否由 resolver
  live AvailabilitySnapshot 決定（AIR-240 模型-routing 契約面、AIR-245
  resolver_decision_check hard invariants 為閘）。本模組輸出僅排程面
  （eligible/deferred），不含 dispatch 決策欄——planning evidence 再 fresh
  也不在此產生 dispatch 義務。

消費面：ArcPlan dict（`entry_from_plan`——讀頂層 temporal_allocation，arc 級
排程單位；unit 級細化屬 slice join 面，歸 arc_spec.validate-link）或直接構造
`ArcEntry`。CLI 無入口（純 library module——排程語義由排程呼叫端組裝）。

exit／錯誤契約：輸入不合法一律 fail-loud（crash-only：靜默排程損壞比拒絕更
危險）——型別錯誤 TypeError（priority 非 int、plan 非 dict）；值錯誤
ValueError（naive 時間、重複 arc_id、空 id、壞 ISO 格式）。
"""

import json
from dataclasses import dataclass
from datetime import datetime

ARC_BATCH_SCHEDULE_SCHEMA = "arc-batch-schedule/1"
DEFERRED_REASON = "planned_not_before"


def _parse_iso_utc(value: object) -> datetime | None:
    """ISO 8601 tz-aware 解析——naive（無時區）＝不合法（鏡射
    arc_spec._parse_iso_utc 同姿態；腳本間自含解析為本目錄既有慣例）。"""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt


@dataclass(frozen=True)
class ArcEntry:
    """批次排程單位——一個 arc（ArcPlan）的排程投影。

    priority＝呼叫端既有 priority 語義（本模組不發明）；preferred_family 屬
    advisory planning evidence（只影響排程/排序——dispatch authority 歸
    resolver live AvailabilitySnapshot）。
    """

    arc_id: str
    priority: int = 0
    planned_not_before: datetime | None = None
    preferred_family: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.arc_id, str) or not self.arc_id.strip():
            raise ValueError(
                f"ArcEntry.arc_id 須為非空字串, got {self.arc_id!r} — "
                f"排程身分歧義即拒絕（fail-loud）"
            )
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise TypeError(
                f"ArcEntry.priority 須為 int, got {self.priority!r} — "
                f"priority 是排序主鍵（既有語義），非數即歧義（fail-loud）"
            )
        if self.planned_not_before is not None and (
            not isinstance(self.planned_not_before, datetime)
            or self.planned_not_before.tzinfo is None
        ):
            raise ValueError(
                f"ArcEntry.planned_not_before 須為 tz-aware datetime, got "
                f"{self.planned_not_before!r} — naive 值禁與 aware 值混比"
                f"（fail-loud）"
            )
        if self.preferred_family is not None and (
            not isinstance(self.preferred_family, str)
            or not self.preferred_family.strip()
        ):
            raise ValueError(
                f"ArcEntry.preferred_family 須為非空字串或 None, got "
                f"{self.preferred_family!r}（fail-loud）"
            )

    def to_row(self) -> dict:
        """JSON-safe 排程列（correctness receipt 形）。"""
        return {
            "arc_id": self.arc_id,
            "priority": self.priority,
            "planned_not_before": (
                self.planned_not_before.isoformat()
                if self.planned_not_before is not None
                else None
            ),
            "preferred_family": self.preferred_family,
        }


def entry_from_plan(plan: dict, *, priority: int = 0) -> ArcEntry:
    """ArcPlan dict → 排程 entry（讀頂層 temporal_allocation；缺席＝untimed）。

    planned_not_before 解析失敗（naive／壞格式）＝ValueError fail-loud——
    plan compile stage 已驗形，此處防禦直接 dict 呼叫端（crash-only）。
    """
    if not isinstance(plan, dict):
        raise TypeError(
            f"plan 須為 dict（ArcPlan payload）, got {type(plan).__name__}"
        )
    arc_id = plan.get("card_id")
    if not isinstance(arc_id, str) or not arc_id.strip():
        raise ValueError(
            f"plan.card_id 須為非空字串（排程身分錨點）, got {arc_id!r}"
        )
    temporal = plan.get("temporal_allocation")
    planned: datetime | None = None
    preferred: str | None = None
    if isinstance(temporal, dict):
        raw = temporal.get("planned_not_before")
        if raw is not None:
            planned = _parse_iso_utc(raw)
            if planned is None:
                raise ValueError(
                    f"plan.card_id=`{arc_id}` temporal_allocation."
                    f"planned_not_before 須為 ISO 8601 且帶時區, got {raw!r} "
                    f"（naive ISO＝不合法，fail-loud）"
                )
        preferred = temporal.get("preferred_family")
        if preferred is not None and not isinstance(preferred, str):
            raise ValueError(
                f"plan.card_id=`{arc_id}` temporal_allocation."
                f"preferred_family 須為字串, got {preferred!r}（fail-loud）"
            )
    return ArcEntry(
        arc_id=arc_id,
        priority=priority,
        planned_not_before=planned,
        preferred_family=preferred,
    )


def entries_from_plans(plans: list[dict], *, priority: int = 0) -> list[ArcEntry]:
    """ArcPlan 列表 → entry 列表（multi-arc dogfood／批次消費面）。"""
    return [entry_from_plan(p, priority=priority) for p in plans]


def schedule(entries: list[ArcEntry], *, now: datetime) -> dict:
    """deterministic batch scheduling——時間閘＋穩定排序。

    回 {"eligible": [...排程列...], "deferred": [...]}：
    - eligible：過時間閘者依 (-priority, temporal tiebreak, 輸入序) 排序
    - deferred：future planned_not_before 者保持輸入順序，附 reason

    now 須 tz-aware（naive＝ValueError）；預設無——時鐘一律注入（禁裸
    datetime.now）。
    """
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError(
            f"now 須為 tz-aware datetime（時鐘一律注入——禁裸 datetime.now）, "
            f"got {now!r}"
        )
    ids = [e.arc_id for e in entries]
    dupes = sorted({a for a in ids if ids.count(a) > 1})
    if dupes:
        raise ValueError(
            f"duplicate arc_id {dupes} in batch entries — 排程身分歧義即拒絕"
            f"（fail-loud）"
        )
    ranked: list[tuple[tuple, int, ArcEntry]] = []
    deferred: list[dict] = []
    for i, entry in enumerate(entries):
        planned = entry.planned_not_before
        if planned is not None and planned > now:
            deferred.append(
                {
                    "arc_id": entry.arc_id,
                    "planned_not_before": planned.isoformat(),
                    "reason": DEFERRED_REASON,
                }
            )
            continue
        temporal_key: tuple = (0,) if planned is None else (1, planned)
        ranked.append(((-entry.priority, temporal_key), i, entry))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return {
        "eligible": [entry.to_row() for _, _, entry in ranked],
        "deferred": deferred,
    }


def render_receipt(result: dict) -> str:
    """排程 correctness receipt（一行 JSON——arc_behavior_audit 慣例）。"""
    return json.dumps(
        {"schema": ARC_BATCH_SCHEDULE_SCHEMA, **result},
        ensure_ascii=False,
        sort_keys=True,
    )


if __name__ == "__main__":
    raise SystemExit(
        "arc_batch_schedule 是 library module（排程語義由排程呼叫端組裝；"
        "now 必須由呼叫端注入）——無 CLI 入口"
    )
