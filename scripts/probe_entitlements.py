#!/usr/bin/env python3
"""AIR-98 P1——model 額度探測管線（runtime probe pipeline）。

探測四腿、每腿落地一份 JSON 到 `~/.agents/probe-entitlements/`：
- glm（pool=glm-native）：delegate-bridge `usage --json`（ok 態帶 plan＋limits）。
- codex（pool=codex-native）：同一聚合輸出；error（如未登入）＝fail-loud 示範。
  （bridge 2.0.24 b913b41 已修復 codex.rs default branch；probe 端
  CODEX_HOME 注入 workaround 0921 撤除——AIR-150。）
- muse（pool=unknown）：bridge 聚合自帶 unsupported＋reason——usage-probe
  allow-list 僅 {codex, glm}，muse 禁任何 usage 假造（A4）；現值
  provenance 只能是 event/429（P3 後）。
- codex（pool=chatgpt-web）：健康三訊號組合（web 池 usage 盲區，禁造用量
  數字、pool_visibility=none）——訊號1 localhost healthz
  （accepting_turns＋last_successful_model_catalog_request_at）、訊號2
  browser-turns 最新 trace 結局 checkpoint；訊號3（doctor --json）本輪
  不做（TODO）。verdict＝healthy/degraded/unreachable；全綠只證 process 活。

契約：
- schema：{"schema_version":1,"family","pool","probe_ts_utc","source",
  "status":"ok|unsupported|error","failure_class","parsed","raw","notes"}；
  原子寫（tmp+rename）；另維護 `latest-<family>-<pool>.json` 指針。
- fail-loud：probe 失敗＝status error＋failure_class＋parsed 顯性 unknown；
  禁沿用舊值冒充新鮮；跑過的腿全非 ok → exit 1，否則 0（全 skip＝0）。
- codex-native 與 chatgpt-web 兩池記錄永不合併（pool 欄分列）。
- 憑證零經手（bridge 內部處理，本 script 只消費 stdout）；webgpt 只讀
  本機檔與 localhost；bridge 呼叫 bounded timeout（60s 保守值）。
- 排程重疊防護：--min-interval N（分鐘，預設 30）內 latest 指針過新即
  skip（exit 0）；單次執行無 daemon。
- 本 script 永不直寫 memory spine——消費協議＝ai-guide session 讀
  latest-*.json 校驗後寫 spine（as-of＋per-family 現值）。

用法：uv run python scripts/probe_entitlements.py [--min-interval 30]
      [--family codex|glm|muse] [--out-dir DIR]
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

# ---- 常數（路徑契約：本機探測面；測試經參數/monkeypatch 注入 tmp 路徑）----

DEFAULT_REGISTRY = Path.home() / ".zcode/cli/plugins/installed_plugins.json"
DEFAULT_OUT_DIR = Path.home() / ".agents/probe-entitlements"
HEALTHZ_URL = "http://127.0.0.1:17841/healthz"
TURNS_ROOT = Path.home() / ".codex-chatgpt-web/diagnostics/browser-turns"
BRIDGE_TIMEOUT_S = 60.0  # bridge 內部 usage 自帶 15s timeout；外部取保守值
HEALTHZ_TIMEOUT_S = 5.0
CATALOG_STALE_S = 6 * 3600  # catalog 時間戳超齡＝ChatGPT 端回應存疑（heuristic，可調）

SCHEMA_VERSION = 1
_logger = logging.getLogger("scripts.probe_entitlements")
# P4 capability matrix（unsupported 顯性化）：usage 探測能力 per-family 事實；
# USAGE_PROBE_ALLOWLIST 是本表 supported 投影（行為面一致性釘在測試）。
CAPABILITY_MATRIX: dict[str, Literal["supported", "unsupported"]] = {
    "codex": "supported",
    "glm": "supported",
    "muse": "unsupported",
}
# muse 現值 provenance 唯一合法來源＝event/429（P3 quota event capture）——
# usage probe unsupported 是 capability 事實，禁任何 muse usage 值假造（A4）。
CAPABILITY_PROVENANCE_MUSE = "event/429"
USAGE_PROBE_ALLOWLIST = frozenset(
    f for f, v in CAPABILITY_MATRIX.items() if v == "supported"
)

FAMILY_POOL: dict[str, str] = {
    "glm": "glm-native",
    "codex": "codex-native",  # bridge usage 只見原生訂閱池
    "muse": "unknown",
}

RATE_LIMIT_MARKERS = ("rate limit", "rate_limit", "ratelimit")


# ---- 錯誤家族（failure_class 單一源）----


class ProbeError(Exception):
    """probe 失敗家族基底；failure_class 供落地記錄 fail-loud。"""

    failure_class = "probe_error"


class BridgeResolveError(ProbeError):
    failure_class = "missing_binary"


class BridgeTransportError(ProbeError):
    failure_class = "transport_error"


class TransportTimeout(ProbeError):
    failure_class = "transport_timeout"


class BridgeParseError(ProbeError):
    failure_class = "parse_error"


class HealthSignalError(ProbeError):
    failure_class = "health_signal_error"


# ---- bridge 腿 ----


def resolve_bridge_binary(registry: Path) -> Path:
    """由 installed_plugins.json 解析 delegate-bridge binary（禁手拼 cache 路徑）。"""
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BridgeResolveError(f"registry unreadable: {registry}: {exc}") from exc
    for plugin in data.get("plugins", []):
        if plugin.get("id") == "delegate@delegate-market":
            install = plugin.get("installPath")
            if not install:
                raise BridgeResolveError("delegate plugin missing installPath")
            binary = Path(install) / "bin" / "delegate-bridge"
            if not binary.is_file():
                raise BridgeResolveError(f"bridge binary absent: {binary}")
            return binary
    raise BridgeResolveError(f"delegate@delegate-market not in {registry}")


def run_bridge_usage(
    binary: Path,
    timeout_s: float = BRIDGE_TIMEOUT_S,
    *,
    runner: Any = None,
) -> dict[str, Any]:
    """跑 `usage --json`（憑證零經手：只消費 stdout）。"""
    run = runner if runner is not None else subprocess.run
    try:
        done = run(
            [str(binary), "usage", "--json"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise TransportTimeout(f"bridge usage timed out after {timeout_s}s") from exc
    except OSError as exc:
        raise BridgeTransportError(f"bridge spawn failed: {exc}") from exc
    # exit map（bridge 契約）：ok/unsupported→0、聚合內任一 family error→1；
    # per-family status 才是 fail-loud 真相源（upstream_error 於 parse 層映射），
    # 故 0/1 皆嘗試消費 stdout；其餘 exit＝transport 層失敗。
    if done.returncode not in (0, 1):
        raise BridgeTransportError(
            f"bridge usage exited {done.returncode}: {done.stderr.strip()[:200]}"
        )
    try:
        report = json.loads(done.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeParseError(f"bridge stdout not JSON: {exc}") from exc
    if not isinstance(report, dict) or "families" not in report:
        raise BridgeParseError("bridge report missing families key")
    return report


def _unknown_parsed(detail: str) -> dict[str, Any]:
    return {"value": "unknown", "detail": detail}


def record_from_bridge_entry(entry: dict[str, Any], probe_ts: str) -> Any:
    """bridge 聚合輸出單 family entry → ProbeRecord。

    status 映射沿用 bridge（ok/unsupported/error）；ok 態 parsed 只做最小
    提取（plan＋limits 原樣），窗口語義正典屬 P2、此處不造語義。
    """
    family = entry.get("family")
    status = entry.get("status")
    raw = entry.get("raw")
    if family not in FAMILY_POOL or status not in {"ok", "unsupported", "error"}:
        raise BridgeParseError(f"bridge entry shape unrecognized: keys={sorted(entry)}")

    if status == "ok":
        data = (raw or {}).get("data") if isinstance(raw, dict) else None
        parsed: dict[str, Any] = {
            "plan": entry.get("planType") or (data or {}).get("level"),
            "limits": (data or {}).get("limits"),
        }
        failure_class = "none"
    elif status == "unsupported":
        parsed = {"value": "unknown", "reason": entry.get("reason", "")}
        failure_class = "none"
    else:
        parsed = _unknown_parsed(str(entry.get("error", "")))
        failure_class = "upstream_error"

    return ProbeRecord(
        family=family,
        pool=FAMILY_POOL[family],
        probe_ts_utc=probe_ts,
        source="delegate-bridge usage --json",
        status=status,
        failure_class=failure_class,
        parsed=parsed,
        raw=raw if isinstance(raw, dict) else {},
        notes=(
            "usage-probe allow-list: "
            + ",".join(sorted(USAGE_PROBE_ALLOWLIST))
            + (
                "; muse unsupported 是 capability 事實，現值 provenance "
                f"只能是 {CAPABILITY_PROVENANCE_MUSE}（AIR-98 A4）"
                if status == "unsupported"
                else ""
            )
        ),
    )


# ---- webgpt 腿（chatgpt-web 池：健康三訊號，非 usage）----


def fetch_healthz(url: str, timeout_s: float, *, opener: Any) -> dict[str, Any]:
    """訊號1：localhost healthz JSON（本機唯讀）。"""
    try:
        with opener(url, timeout=timeout_s) as resp:
            return json.loads(resp.read())
    except json.JSONDecodeError as exc:
        raise HealthSignalError(f"healthz not JSON: {exc}") from exc
    except urllib.error.URLError as exc:
        raise BridgeTransportError(f"healthz unreachable: {exc}") from exc
    except TimeoutError as exc:
        raise TransportTimeout(f"healthz timed out after {timeout_s}s") from exc


def latest_turn_signal(turns_root: Path) -> dict[str, Any]:
    """訊號2：最新 trace 目錄的結局 checkpoint（無目錄≠不健康）。"""
    if not turns_root.is_dir():
        return {"signal": "absent"}
    try:
        newest_dir = max(
            (p for p in turns_root.iterdir() if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
        )
    except ValueError:
        return {"signal": "absent"}
    files = sorted(newest_dir.glob("*.json"))
    if not files:
        return {"signal": "absent"}
    try:
        body = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HealthSignalError(f"turn file unreadable: {files[-1]}: {exc}") from exc
    serialized = json.dumps(body).lower()
    return {
        "signal": "present",
        "checkpoint": body.get("checkpoint", files[-1].stem),
        "capturedAt": body.get("capturedAt"),
        "traceId": body.get("traceId"),
        "rate_limited": any(m in serialized for m in RATE_LIMIT_MARKERS),
    }


def _parse_iso_z(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def probe_webgpt(
    now: datetime,
    *,
    healthz_url: str,
    turns_root: Path,
    opener: Any = urllib.request.urlopen,
) -> Any:
    """健康三訊號組合 → ProbeRecord（pool=chatgpt-web、pool_visibility=none）。"""
    try:
        healthz = fetch_healthz(healthz_url, HEALTHZ_TIMEOUT_S, opener=opener)
    except ProbeError as exc:
        return ProbeRecord(
            family="codex",
            pool="chatgpt-web",
            probe_ts_utc=_iso_z(now),
            source="local healthz+browser-turns",
            status="error",
            failure_class=exc.failure_class,
            parsed={"value": "unknown", "verdict": "unreachable", "detail": str(exc)},
            raw={},
            notes="web 池 usage 盲區：本記錄無任何用量數字（pool_visibility=none）",
        )

    turn = latest_turn_signal(turns_root)
    degraded_reasons: list[str] = []
    if healthz.get("accepting_turns") is not True:
        degraded_reasons.append("accepting_turns is not true")
    catalog_at = _parse_iso_z(healthz.get("last_successful_model_catalog_request_at"))
    if catalog_at is None:
        degraded_reasons.append("catalog timestamp missing/unparseable")
    elif (now - catalog_at).total_seconds() > CATALOG_STALE_S:
        degraded_reasons.append(f"catalog ts older than {CATALOG_STALE_S // 3600}h")
    if turn.get("signal") == "present" and "failed" in str(turn.get("checkpoint")):
        degraded_reasons.append(
            "latest turn failed" + (" (rate limit)" if turn.get("rate_limited") else "")
        )
    verdict = "degraded" if degraded_reasons else "healthy"
    return ProbeRecord(
        family="codex",
        pool="chatgpt-web",
        probe_ts_utc=_iso_z(now),
        source="local healthz+browser-turns",
        status="ok",
        failure_class="none",
        parsed={
            "verdict": verdict,
            "degraded_reasons": degraded_reasons,
            "pool_visibility": "none",
            "accepting_turns": healthz.get("accepting_turns"),
            "catalog_request_at": healthz.get(
                "last_successful_model_catalog_request_at"
            ),
            "turn": turn,
        },
        raw={"healthz": healthz, "latest_turn": turn},
        notes=(
            "健康三訊號組合，全綠只證 process 活；訊號3（doctor --json）"
            "本輪未接（TODO，含 2s live 探測）；無目錄≠不健康"
        ),
    )


# ---- 落地（schema／原子寫／latest 指針）----


class ProbeRecord:
    """probe 落地記錄（schema v1 欄位）。"""

    def __init__(
        self,
        family: str,
        pool: str,
        probe_ts_utc: str,
        source: str,
        status: str,
        failure_class: str,
        parsed: dict[str, Any],
        raw: dict[str, Any],
        notes: str,
    ) -> None:
        self.family = family
        self.pool = pool
        self.probe_ts_utc = probe_ts_utc
        self.source = source
        self.status = status
        self.failure_class = failure_class
        self.parsed = parsed
        self.raw = raw
        self.notes = notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "family": self.family,
            "pool": self.pool,
            "probe_ts_utc": self.probe_ts_utc,
            "source": self.source,
            "status": self.status,
            "failure_class": self.failure_class,
            "parsed": self.parsed,
            "raw": self.raw,
            "notes": self.notes,
        }


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _basic_z(iso: str) -> str:
    dt = _parse_iso_z(iso)
    if dt is None:
        raise BridgeParseError(f"bad probe timestamp: {iso}")
    return dt.strftime("%Y%m%dT%H%M%SZ")


def record_filename(rec: ProbeRecord) -> str:
    return f"{_basic_z(rec.probe_ts_utc)}-{rec.family}-{rec.pool}.json"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{os.getpid()}.tmp"
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)  # 原子換名：讀者永遠看到完整檔


def write_record(out_dir: Path, rec: ProbeRecord) -> tuple[Path, Path]:
    """落地時間戳檔＋更新 latest 指針（兩者同一內容）。"""
    payload = rec.to_dict()
    path = out_dir / record_filename(rec)
    latest = out_dir / f"latest-{rec.family}-{rec.pool}.json"
    _atomic_write_json(path, payload)
    _atomic_write_json(latest, payload)
    return path, latest


def _read_latest(out_dir: Path, family: str, pool: str) -> dict[str, Any] | None:
    latest = out_dir / f"latest-{family}-{pool}.json"
    if not latest.is_file():
        return None
    try:
        return json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None  # 指針壞＝當無指針重探（fail-loud 方向：不沿用舊值）


def latest_age_minutes(
    out_dir: Path, family: str, pool: str, now: datetime
) -> float | None:
    data = _read_latest(out_dir, family, pool)
    if data is None:
        return None
    ts = _parse_iso_z(data.get("probe_ts_utc"))
    if ts is None:
        return None
    return max((now - ts).total_seconds() / 60, 0.0)


def min_interval_skip_reason(
    out_dir: Path, family: str, pool: str, *, min_interval_min: int, now: datetime
) -> str | None:
    """latest 指針過新 → skip 原因字串；否則 None。"""
    age = latest_age_minutes(out_dir, family, pool, now)
    if age is None or age >= min_interval_min:
        return None
    return (
        f"skip {family}/{pool}: latest probe {age:.1f}min ago "
        f"is newer than --min-interval {min_interval_min}min"
    )


def aggregate_exit(records: list[Any]) -> int:
    """跑過的腿全非 ok → 1；空集合（全 skip／過濾）＝非失敗 → 0。"""
    if not records:
        return 0
    return 0 if any(r.status == "ok" for r in records) else 1


# ---- 額度事件入帳（P3：合成注入測試；提醒式不自動寫）----


@dataclass
class QuotaEvent:
    """dispatch 撞額度事件的機械訊號（P3）。

    retryable_at_utc＝ISO 8601 或字面 "unknown"——只採 reset 語境（resets at
    ／try again at／重置…）緊鄰的 ISO 時間戳；無 reset 語境、非 ISO 時間、
    多時間戳無法判定時顯性 unknown，禁從訊息歷史或週期表推度現值。
    """

    as_of_utc: str
    family: str
    failure_class: str
    retryable_at_utc: str
    source_message: str


_ISO_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?")
# reset 語境詞——時間戳須緊鄰其後才可作 retryable-at（裸 ISO 時間戳如呼叫
# 時間不入帳，禁取首個）；非 ISO 時間（"try again at 3:30pm"）一律不採。
_RESET_CONTEXT_RE = re.compile(
    r"(?:resets?\s+at|reset\s+at|try\s+again\s+at|retry\s+after|重置(?:於|時間)?|恢復(?:於|時間)?)"
    r"\s*[:：]?\s*("
    + _ISO_TS_RE.pattern
    + r")",
    re.IGNORECASE,
)
_SIG_1308 = re.compile(r"\b1308\b")
_SIG_429 = re.compile(r"\b429\b")
# usage limit 簽名＝native 訂閱池訊號（codex CLI exec-approval 層查 native
# 訂閱額度，非 web edge——0921 歸因修訂 AIR-150/F1，同 model-routing webgpt
# 失敗態表第 6 類）。
_SIG_NATIVE_USAGE = re.compile(r"you've hit your usage limit")
# 額度事件 family 白名單（typo/偽造 family 禁透傳進事件行）
QUOTA_EVENT_FAMILIES = frozenset(CAPABILITY_MATRIX)


def capture_quota_event(
    family: str, message: str, observed_at_utc: str
) -> QuotaEvent | None:
    """辨識額度事件簽名 → QuotaEvent；回 None＝未識別，非無事件。

    三簽名（AIR-98 A3，優先序 1308＞usage limit＞429 釘死在測試）：
    ①原生 429——訊息含明確 reset 語境時間戳（resets at／try again at／重置…
    緊鄰其後）亦採用，無 reset 語境時間戳 → retryable-at=unknown
    ②GLM 1308（錯誤含重置時間戳，解析之）③usage limit（"You've hit your
    usage limit ... try again at <time>"，解析 <time>）——歸因＝native 訂閱池
    （usage limit 訊號＝native 訂閱池耗盡，非 web edge；
    failure_class=usage_limit_native，同 model-routing webgpt 失敗態表
    第 6 類歸因修訂）。

    retryable-at 擷取限定 reset 語境：時間戳須緊鄰 reset 語境詞；訊息含多個
    ISO 時間戳且無法判定（reset 語境零命中或多個互斥）→ retryable-at=
    unknown＋log 原文（warning），禁取首個時間戳冒充重置點。非 ISO 時間
    （如 "try again at 3:30pm"）不採，一律 unknown——禁把本地時間偽裝成 ISO。

    None 語義：簽名未命中＝「未識別，非無事件」——簽名表覆蓋窄（變體如
    "quota exceeded" 未列），調用方禁把 None 當「無額度事件」入帳依據。

    輸入校驗 fail-loud：family 非白名單（codex/glm/muse）、observed_at_utc
    非 ISO 8601 → ValueError，禁透傳污染事件行。

    輸出只有提醒 log 行＋spine 格式事件行（reminder_log_line／
    spine_event_line）——寫回 spine 由 ai-guide session 校驗後執行，本模組
    不含任何 spine 寫入路徑；合成注入測試，禁真呼叫探測。
    """
    if family not in QUOTA_EVENT_FAMILIES:
        raise ValueError(
            f"capture_quota_event: unknown family {family!r} "
            f"(expected one of {sorted(QUOTA_EVENT_FAMILIES)})"
        )
    if _parse_iso_z(observed_at_utc) is None:
        raise ValueError(
            f"capture_quota_event: observed_at_utc is not ISO 8601: "
            f"{observed_at_utc!r}"
        )
    lowered = message.lower()
    if _SIG_1308.search(lowered):
        failure_class = "usage_limit_1308"
    elif _SIG_NATIVE_USAGE.search(lowered):
        failure_class = "usage_limit_native"
    elif _SIG_429.search(lowered):
        failure_class = "rate_limit_429"
    else:
        return None
    reset_ctx_ts = sorted(set(_RESET_CONTEXT_RE.findall(message)))
    if len(reset_ctx_ts) == 1:
        retryable_at = reset_ctx_ts[0]
    else:
        retryable_at = "unknown"
        # 多個 ISO 時間戳無法判定 → 顯性 log 原文（禁靜默丟棄；原文另存
        # source_message 欄供消費端覆核）
        if len(_ISO_TS_RE.findall(message)) > 1:
            _logger.warning(
                "capture_quota_event: ambiguous reset timestamps "
                "(%d ISO ts, no unique reset-context match), "
                "retryable_at=unknown, raw message: %s",
                len(_ISO_TS_RE.findall(message)),
                message,
            )
    return QuotaEvent(
        as_of_utc=observed_at_utc,
        family=family,
        failure_class=failure_class,
        retryable_at_utc=retryable_at,
        source_message=message,
    )


def spine_event_line(event: QuotaEvent) -> str:
    """spine 格式事件行（as-of＋family＋failure_class＋retryable-at）。

    文字產物：由處置 session 校驗後併入 spine 條目「近期事件」（本模組不
    寫任何檔到 spine 位置——單一寫者不變，AIR-98 決策②）。
    """
    return (
        f"quota-event as_of={event.as_of_utc} family={event.family} "
        f"failure_class={event.failure_class} "
        f"retryable_at={event.retryable_at_utc}"
    )


def reminder_log_line(event: QuotaEvent) -> str:
    """提醒 log 行——提醒式不自動寫：處置 session 校驗後更新 spine 事件行。"""
    return (
        f"[quota-event reminder] {event.as_of_utc} {event.family} "
        f"{event.failure_class} retryable_at={event.retryable_at_utc}"
        "——提醒處置 session 校驗後更新 spine 事件行（不自動寫）"
    )


# ---- main ----


def _bridge_leg_pools(families: set[str]) -> list[tuple[str, str]]:
    return [(f, FAMILY_POOL[f]) for f in sorted(families)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--min-interval",
        type=int,
        default=30,
        help="latest 指針過新即 skip 的分鐘數（排程重疊防護；預設 30）",
    )
    parser.add_argument(
        "--family",
        choices=sorted({"codex", "glm", "muse"}),
        help="只跑指定 family（codex 含 codex-native＋chatgpt-web 兩池）",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    out_dir = args.out_dir or DEFAULT_OUT_DIR
    now = datetime.now(UTC)
    want: set[str] = {args.family} if args.family else {"codex", "glm", "muse"}

    records: list[Any] = []
    for line in (
        min_interval_skip_reason(
            out_dir, f, p, min_interval_min=args.min_interval, now=now
        )
        for f, p in _bridge_leg_pools(want)
    ):
        if line is not None:
            print(line)
    bridge_pools = [
        (f, p)
        for f, p in _bridge_leg_pools(want)
        if min_interval_skip_reason(
            out_dir, f, p, min_interval_min=args.min_interval, now=now
        )
        is None
    ]
    webgpt_skip = (
        min_interval_skip_reason(
            out_dir, "codex", "chatgpt-web", min_interval_min=args.min_interval, now=now
        )
        if "codex" in want
        else "filtered"
    )
    if webgpt_skip is not None and webgpt_skip != "filtered":
        print(webgpt_skip)

    # bridge 聚合腿（glm/codex/muse）
    if bridge_pools:
        try:
            binary = resolve_bridge_binary(DEFAULT_REGISTRY)
            report = run_bridge_usage(binary, BRIDGE_TIMEOUT_S)
            entries = {e.get("family"): e for e in report.get("families", [])}
            probe_ts = _iso_z(now)
            for family, _pool in bridge_pools:
                if family not in entries:
                    records.append(
                        ProbeRecord(
                            family=family,
                            pool=FAMILY_POOL[family],
                            probe_ts_utc=probe_ts,
                            source="delegate-bridge usage --json",
                            status="error",
                            failure_class="parse_error",
                            parsed=_unknown_parsed("family missing from bridge report"),
                            raw={},
                            notes="bridge 聚合輸出缺此 family——fail-loud",
                        )
                    )
                    continue
                records.append(record_from_bridge_entry(entries[family], probe_ts))
        except ProbeError as exc:
            # bridge 面失敗 → 所有 bridge 依賴腿落同名 error（禁沿用舊值）
            probe_ts = _iso_z(now)
            for family, _pool in bridge_pools:
                records.append(
                    ProbeRecord(
                        family=family,
                        pool=FAMILY_POOL[family],
                        probe_ts_utc=probe_ts,
                        source="delegate-bridge usage --json",
                        status="error",
                        failure_class=exc.failure_class,
                        parsed=_unknown_parsed(str(exc)),
                        raw={},
                        notes="bridge 呼叫失敗——fail-loud，不沿用舊值",
                    )
                )

    # webgpt 腿（chatgpt-web 池）
    if "codex" in want and webgpt_skip is None:
        records.append(
            probe_webgpt(now, healthz_url=HEALTHZ_URL, turns_root=TURNS_ROOT)
        )

    for rec in records:
        write_record(out_dir, rec)
        print(
            f"probed {rec.family}/{rec.pool} status={rec.status} "
            f"failure_class={rec.failure_class} -> {record_filename(rec)}"
        )
    return aggregate_exit(records)


if __name__ == "__main__":
    sys.exit(main())
