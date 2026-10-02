#!/usr/bin/env python3
"""entitlement_window_snapshot——planning 證據 evaluator（AIR-239）。

輸入三源 → per family/pool `{source, observed_at, freshness, state,
retryable_at}` planning 證據（--json）。消費者＝ArcPlan temporal schema
編譯面（AIR-240 child-2）；**非 dispatch gate**——派工當下 live authority
仍是 skills/model-routing/scripts/availability_snapshot.py（AIR-123）。

evaluator-not-router：輸出只有 per-row 證據欄位——禁任何揀選／排序／代換建
議欄位（禁 selected/rank/fallback/recommend）；判斷腿仍歸 model-routing
resolver instruction protocol。

設計決策（D1–D7 詳 .agent-tmp/air-239/journal-impl.md；tri 定稿契約＝卡
AIR-239 Description）：
- D1 平行新檔（不擴 availability_snapshot.py——dispatch exit 閘語義與
  planning exit 0-with-unknowns 契約互斥）；spine 解析重用
  availability_snapshot.parse_spine（禁第二份 spine parser）。
- D2 quota-event 載體＝`<probe-dir>/quota-events.jsonl`（raw message
  intake：{"family","observed_at_utc","message"}），parser 重用
  probe_entitlements.capture_quota_event 單一源——檔案缺席＝零事件；
  malformed line／白名單外 family＝exit 2 fail-loud。
- D3 freshness 雙時鐘：probe/event 秒級 age vs --probe-stale-hours（預設
  26h，hourly cadence 容忍一次整日缺口）；spine UTC 日級 vs
  --spine-stale-days（預設 3，與 availability_snapshot 同形）。**age 恰
  等於閾值＝fresh，＞才 stale**；未來時間戳＝exit 2（未來非新，沿 F4）。
- D4 衝突序（勝者 rank key 由高到低＝fresh → has_state → tier →
  observed_at → 平手 tiebreak）：fresh 壓 stale；有 state 主張壓 unknown
  主張（probe unsupported/error 對現值零資訊量）；direct（probe/event）
  壓 spine；較新 observed_at 勝；全等時 event＞probe＞spine（保守：耗盡
  訊號壓過探測快照）。**勝者 stale → state=unknown＋retryable_at=None**
  （stale 證據的 reset 錨點屬考古，禁當現值）。
- D5 retryable_at＝provider reset 時間戳 only、**禁 5h 週期合成**（全檔無
  週期推算路徑）：probe 勝者讀 glm-native parsed.limits[].nextResetTime
  （epoch ms）與 codex-native raw.rate_limit.reset_at（epoch s）——相異值
  恰一個才生成 ISO Z，0 或 ≥2 個＝None（歧義→缺，揀選即 ranking）；event
  勝者用 parser retryable_at_utc（"unknown"→None）；spine 勝者恆 None。
  retryable_at 不是 availability 主張（retryable-at ≠ available 正典）。
- D6 rows＝probe latest-*.json 的 (family, pool) 集（muse pool 字面
  "unknown" 逐字保留）；spine-only family 不造 row；codex 兩池分列；
  quota-event 為 family 級、套用該 family 全部 pools（pool 級歸因屬
  AIR-150 地形，已知限制）。輸出
  {"schema": "entitlement-window-snapshot/1", "generated_at", "rows"}，
  rows 按 (family, pool) 字母序（display determinism——非候選排序）。
- D7 exit 契約：0＝snapshot 產出（rows 可全 unknown——planning evidence
  的 unknown 是值不是失敗）；2＝輸入缺席或不合法（probe dir 缺／空、
  latest malformed、quota-events line malformed／白名單外、未來時間戳、
  flag 帶無值、顯式 --spine 檔缺）。預設 spine 檔缺＝該層缺席（WARN
  續行——spine 是慢事實補充源非閘）。

用法：uv run python scripts/entitlement_window_snapshot.py
      --probe-dir ~/.agents/probe-entitlements [--spine PATH] [--json]
"""

import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBE_DIR = Path.home() / ".agents/probe-entitlements"
DEFAULT_SPINE = (
    Path.home() / ".agents/memory-spine/reference_model-runtime-entitlements.md"
)
PROBE_STALE_HOURS_DEFAULT = 26
SPINE_STALE_DAYS_DEFAULT = 3

SCHEMA = "entitlement-window-snapshot/1"
ROW_KEYS = ("family", "pool", "source", "observed_at", "freshness", "state", "retryable_at")
STATES = ("available", "unavailable", "unknown")
SOURCES = ("probe", "quota-event", "spine")
FRESH = "fresh"
STALE = "stale"
DIRECT_TIER = 1  # probe／event＝fast facts
SPINE_TIER = 0  # spine＝slow fact
# 平手 tiebreak（observed_at 全等時）：event＞probe＞spine——耗盡訊號保守壓過快照
TIEBREAK = {"quota-event": 2, "probe": 1, "spine": 0}


class SnapshotInputError(Exception):
    """輸入缺席或不合法——exit 2 fail-loud（損壞比缺失危險）。"""


def _load_repo_module(rel: str, name: str):
    """importlib 載入 repo 內非 package 腳本（重用單一源，禁自刻第二份）。"""
    path = REPO_ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SnapshotInputError(f"module load failed: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_iso_z(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SnapshotInputError(message)


# ---- 輸入三源 ----


def load_probe_records(probe_dir: Path) -> list[dict]:
    """probe latest-*.json 載入（fail-loud：dir 缺／空／malformed／欄缺）。"""
    if not probe_dir.is_dir():
        raise SnapshotInputError(f"probe dir 缺席：{probe_dir}——fail-loud（exit 2）")
    latests = sorted(probe_dir.glob("latest-*.json"))
    if not latests:
        raise SnapshotInputError(
            f"probe dir 內零 latest-*.json：{probe_dir}"
            "——探測管線未運行，fail-loud（exit 2）"
        )
    records: list[dict] = []
    for path in latests:
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SnapshotInputError(f"probe latest malformed：{path}（{exc}）") from exc
        _require(
            isinstance(rec, dict)
            and isinstance(rec.get("family"), str)
            and isinstance(rec.get("pool"), str)
            and rec.get("status") in {"ok", "unsupported", "error"},
            f"probe record 欄位不合法：{path}（family/pool/status）",
        )
        ts = _parse_iso_z(rec.get("probe_ts_utc"))
        _require(ts is not None, f"probe_ts_utc 非 ISO：{path}")
        assert ts is not None
        _require(
            ts <= datetime.now(tz=UTC),
            f"probe_ts_utc 為未來時間戳：{path}（{rec.get('probe_ts_utc')}）——輸入不合法",
        )
        records.append(rec)
    return records


def load_quota_events(probe_dir: Path) -> list[dict]:
    """quota-events.jsonl → capture_quota_event 重解析（parser 單一源）。

    檔案缺席＝零事件；parser 回 None＝簽名未命中（「未識別，非無事件」）
    ——該行不產生 state 證據、不報錯。
    """
    path = probe_dir / "quota-events.jsonl"
    if not path.is_file():
        return []
    probe_mod = _load_repo_module("scripts/probe_entitlements.py", "probe_entitlements")
    events: list[dict] = []
    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        try:
            line = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise SnapshotInputError(
                f"quota-events.jsonl line {line_no} malformed：{exc}"
            ) from exc
        _require(
            isinstance(line, dict)
            and isinstance(line.get("family"), str)
            and isinstance(line.get("message"), str)
            and _parse_iso_z(line.get("observed_at_utc")) is not None,
            f"quota-events.jsonl line {line_no} 欄位不合法"
            "（family/message/observed_at_utc）",
        )
        try:
            event = probe_mod.capture_quota_event(
                line["family"], line["message"], line["observed_at_utc"]
            )
        except ValueError as exc:
            raise SnapshotInputError(
                f"quota-events.jsonl line {line_no} 不合法：{exc}"
            ) from exc
        observed_at = _parse_iso_z(line["observed_at_utc"])
        _require(
            observed_at is not None and observed_at <= datetime.now(tz=UTC),
            f"quota-events.jsonl line {line_no} observed_at_utc 為未來時間戳"
            "——輸入不合法",
        )
        if event is None:
            continue
        events.append({"event": event, "observed_at": observed_at, "line_no": line_no})
    return events


def load_spine_state(spine_path: Path, families: list[str], *, explicit: bool):
    """spine 慢事實載入（availability_snapshot.parse_spine 單一源重用）。

    顯式 --spine 檔缺＝exit 2；預設路徑檔缺＝該層缺席（None，WARN 線索交
    human 輸出）。
    """
    if not spine_path.is_file():
        if explicit:
            raise SnapshotInputError(f"--spine 檔缺席：{spine_path}——exit 2")
        return None
    avail_mod = _load_repo_module(
        "skills/model-routing/scripts/availability_snapshot.py",
        "availability_snapshot",
    )
    text = spine_path.read_text(encoding="utf-8")
    state = avail_mod.parse_spine(text, families)
    _require(
        state.as_of is not None,
        f"spine as-of 缺席：{spine_path}——fail-loud（exit 2）",
    )
    assert state.as_of is not None
    as_of_date = datetime.fromisoformat(state.as_of).date()
    _require(
        as_of_date <= datetime.now(tz=UTC).date(),
        f"spine as-of {state.as_of} 為未來日期——輸入不合法（exit 2）",
    )
    return state


# ---- 證據層與勝者選擇（D4）----


@dataclass
class Evidence:
    source: str
    observed_at: datetime
    fresh: bool
    has_state: bool
    state: str
    retryable: str | None


def _winner(evidences: list[Evidence]) -> Evidence:
    return max(
        evidences,
        key=lambda e: (
            1 if e.fresh else 0,
            1 if e.has_state else 0,
            DIRECT_TIER if e.source in {"probe", "quota-event"} else SPINE_TIER,
            e.observed_at,
            TIEBREAK[e.source],
        ),
    )


def _epoch_to_iso(seconds: float) -> str:
    return _iso_z(datetime.fromtimestamp(seconds, tz=UTC))


def _probe_retryable(rec: dict) -> str | None:
    """provider 結構化 reset 欄抽取（D5）——相異值恰一個才生成。

    實檔形狀（~/.agents/probe-entitlements/latest-*.json，2026-10-02）：
    glm-native＝parsed.limits[].nextResetTime（epoch ms）；codex-native＝
    raw.rate_limit.primary_window/secondary_window.reset_at（epoch s）。
    """
    stamps: set[int] = set()
    parsed = rec.get("parsed")
    if isinstance(parsed, dict) and isinstance(parsed.get("limits"), list):
        for limit in parsed["limits"]:
            if isinstance(limit, dict) and isinstance(
                limit.get("nextResetTime"), (int, float)
            ):
                stamps.add(int(limit["nextResetTime"] // 1000))
    raw = rec.get("raw")
    if isinstance(raw, dict) and isinstance(raw.get("rate_limit"), dict):
        for window in ("primary_window", "secondary_window"):
            win = raw["rate_limit"].get(window)
            if isinstance(win, dict) and isinstance(win.get("reset_at"), (int, float)):
                stamps.add(int(win["reset_at"]))
    if len(stamps) != 1:
        return None  # 0 或 ≥2 相異值＝歧義→缺（禁揀選）
    return _epoch_to_iso(stamps.pop())


def _probe_evidence(rec: dict, now: datetime, stale_hours: float) -> Evidence:
    ts = _parse_iso_z(rec["probe_ts_utc"])
    assert ts is not None
    fresh = (now - ts).total_seconds() / 3600 <= stale_hours
    if rec["status"] == "ok":
        # retryable 抽取限 ok 態（unsupported/error 不供任何現值錨點）
        return Evidence(
            source="probe",
            observed_at=ts,
            fresh=fresh,
            has_state=True,
            state="available",
            retryable=_probe_retryable(rec) if fresh else None,
        )
    # muse 誠實條款：unsupported 是 capability 事實；error 是 probe 失敗
    # ——皆非 unavailable 主張，state=unknown（has_state=False）
    return Evidence(
        source="probe",
        observed_at=ts,
        fresh=fresh,
        has_state=False,
        state="unknown",
        retryable=None,
    )


def _event_evidence(item: dict, now: datetime, stale_hours: float) -> Evidence:
    event = item["event"]
    observed_at: datetime = item["observed_at"]
    fresh = (now - observed_at).total_seconds() / 3600 <= stale_hours
    retryable = event.retryable_at_utc
    return Evidence(
        source="quota-event",
        observed_at=observed_at,
        fresh=fresh,
        has_state=True,
        state="unavailable",  # capture_quota_event 簽名命中＝額度限制事件
        retryable=retryable if (fresh and retryable != "unknown") else None,
    )


def _spine_evidence(
    spine_state, family: str, now: datetime, stale_days: int
) -> Evidence | None:
    if spine_state is None:
        return None
    as_of_date = datetime.fromisoformat(spine_state.as_of).date()
    age_days = (now.date() - as_of_date).days
    fresh = age_days <= stale_days
    observed_at = datetime(as_of_date.year, as_of_date.month, as_of_date.day, tzinfo=UTC)
    return Evidence(
        source="spine",
        observed_at=observed_at,
        fresh=fresh,
        has_state=True,
        state="available" if family in spine_state.available else "unavailable",
        retryable=None,  # spine 慢事實不供 reset 錨點（D5）
    )


# ---- row 組裝 ----


def build_rows(
    probe_dir: Path,
    spine_path: Path,
    now: datetime,
    *,
    probe_stale_hours: float,
    spine_stale_days: int,
    spine_explicit: bool,
) -> tuple[list[dict], list[str]]:
    records = load_probe_records(probe_dir)
    events = load_quota_events(probe_dir)
    families = sorted({r["family"] for r in records})
    spine_state = load_spine_state(
        spine_path, families, explicit=spine_explicit
    )
    warnings: list[str] = []
    if spine_state is None:
        warnings.append(f"spine 缺席（{spine_path}）——慢事實層缺席，僅 probe/event 評估")
    rows: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()
    for rec in records:
        pair = (rec["family"], rec["pool"])
        if pair in seen_pairs:
            warnings.append(
                f"重複 latest probe {pair[0]}/{pair[1]}——後者忽略（latest 指針契約一對一）"
            )
            continue
        seen_pairs.add(pair)
        evidences = [_probe_evidence(rec, now, probe_stale_hours)]
        for item in events:
            if item["event"].family == rec["family"]:
                evidences.append(_event_evidence(item, now, probe_stale_hours))
        spine_ev = _spine_evidence(
            spine_state, rec["family"], now, spine_stale_days
        )
        if spine_ev is not None:
            evidences.append(spine_ev)
        winner = _winner(evidences)
        state = winner.state if (winner.fresh and winner.has_state) else "unknown"
        rows.append(
            {
                "family": rec["family"],
                "pool": rec["pool"],
                "source": winner.source,
                "observed_at": _iso_z(winner.observed_at),
                "freshness": FRESH if winner.fresh else STALE,
                "state": state,
                "retryable_at": winner.retryable if winner.fresh else None,
            }
        )
    orphan_events = {
        item["event"].family for item in events
    } - {r["family"] for r in rows}
    for family in sorted(orphan_events):
        warnings.append(
            f"quota-event family={family} 無對應 probe row——事件擱置（禁造 row）"
        )
    rows.sort(key=lambda r: (r["family"], r["pool"]))
    return rows, warnings


# ---- CLI ----


def _parse_args(argv: list[str]) -> dict:
    opts: dict = {
        "probe_dir": DEFAULT_PROBE_DIR,
        "spine": DEFAULT_SPINE,
        "probe_stale_hours": float(PROBE_STALE_HOURS_DEFAULT),
        "spine_stale_days": SPINE_STALE_DAYS_DEFAULT,
        "json": False,
        "spine_explicit": False,
    }
    value_flags = ("--probe-dir", "--spine", "--probe-stale-hours", "--spine-stale-days")
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            opts["json"] = True
            i += 1
            continue
        if arg in value_flags:
            _require(i + 1 < len(argv), f"{arg} 帶 flag 無值——輸入不合法（exit 2）")
            value = argv[i + 1]
            if arg == "--probe-dir":
                opts["probe_dir"] = Path(value).expanduser()
            elif arg == "--spine":
                opts["spine"] = Path(value).expanduser()
                opts["spine_explicit"] = True
            elif arg == "--probe-stale-hours":
                try:
                    hours = float(value)
                except ValueError as exc:
                    raise SnapshotInputError(
                        f"--probe-stale-hours 需數值參數：{value!r}"
                    ) from exc
                _require(hours >= 0, "--probe-stale-hours 不可為負")
                opts["probe_stale_hours"] = hours
            else:
                try:
                    days = int(value)
                except ValueError as exc:
                    raise SnapshotInputError(
                        f"--spine-stale-days 需整數參數：{value!r}"
                    ) from exc
                _require(days >= 0, "--spine-stale-days 不可為負")
                opts["spine_stale_days"] = days
            i += 2
            continue
        raise SnapshotInputError(f"未知參數：{arg}——輸入不合法（exit 2）")
    return opts


def main(argv: list[str] | None = None, *, now: datetime | None = None) -> int:
    now = now or datetime.now(tz=UTC)
    try:
        opts = _parse_args(list(sys.argv[1:] if argv is None else argv))
        rows, warnings = build_rows(
            opts["probe_dir"],
            opts["spine"],
            now,
            probe_stale_hours=opts["probe_stale_hours"],
            spine_stale_days=opts["spine_stale_days"],
            spine_explicit=opts["spine_explicit"],
        )
    except SnapshotInputError as exc:
        print(f"[FAIL] {exc}")
        return 2
    payload = {"schema": SCHEMA, "generated_at": _iso_z(now), "rows": rows}
    if opts["json"]:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        for w in warnings:
            print(f"[WARN] {w}", file=sys.stderr)
        return 0
    print(
        f"[EntitlementWindowSnapshot] probe-dir={opts['probe_dir']}"
        f" spine={opts['spine']} generated_at={_iso_z(now)}"
        f" rows={len(rows)}"
    )
    for w in warnings:
        print(f"[WARN] {w}")
    for r in rows:
        print(
            f"{r['family']}/{r['pool']} source={r['source']}"
            f" observed_at={r['observed_at']} freshness={r['freshness']}"
            f" state={r['state']} retryable_at={r['retryable_at']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
