"""probe_entitlements 契約測試（AIR-98 P1——model 額度探測管線，synthetic 層）。

釘住的 invariant：
- usage-probe allow-list 僅 {codex, glm}；muse 只記 unsupported＋reason，
  禁任何 usage 假造（A4 負向）。
- probe 失敗＝status error＋failure_class＋parsed 顯性 unknown；禁沿用舊值
  冒充新鮮（fail-loud）。
- codex-native 與 chatgpt-web 兩池記錄永不合併（pool 欄分列）。
- webgpt 腿（chatgpt-web 池）＝健康三訊號組合、pool_visibility=none——
  禁造任何用量數字。

Bridge usage 輸出形態 fixture 事實來源：delegate-bridge `usage --json`
live 驗證（2026-09-15，marshal 已核可當 parse fixture）。webgpt healthz
與 browser-turns 形態來自 2026-09-15 本機勘查（healthz 頂層 status 欄與
probe schema 的 status 無關；turns 為 <traceId>/NN-<checkpoint>.json）。

spine_event_line／reminder_log_line 測試＝格式測試；經 ai-guide 側寫回
spine 由消費協議覆蓋（spine patch），不在單測範圍。模組源碼另釘靜態反向
斷言（無 spine 寫入路徑，見 test_module_source_has_no_spine_write_surface）。
"""

import json
import logging
import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Self

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/probe_entitlements.py")

ProbeError = _mod.ProbeError
resolve_bridge_binary = _mod.resolve_bridge_binary
run_bridge_usage = _mod.run_bridge_usage
record_from_bridge_entry = _mod.record_from_bridge_entry
probe_webgpt = _mod.probe_webgpt
fetch_healthz = _mod.fetch_healthz
latest_turn_signal = _mod.latest_turn_signal
write_record = _mod.write_record
record_filename = _mod.record_filename
latest_age_minutes = _mod.latest_age_minutes
aggregate_exit = _mod.aggregate_exit
USAGE_PROBE_ALLOWLIST = _mod.USAGE_PROBE_ALLOWLIST

NOW = datetime(2026, 9, 15, 16, 0, 0, tzinfo=UTC)
NOW_ISO = "2026-09-15T16:00:00Z"

# ---- bridge usage 聚合輸出 fixture（live 形態，2026-09-15）----

GLM_OK_ENTRY: dict[str, Any] = {
    "family": "glm",
    "fetchedAt": "2026-09-15T15:54:29.888Z",
    "planType": "pro",
    "raw": {
        "code": 200,
        "data": {
            "level": "pro",
            "limits": [
                {
                    "type": "TIME_LIMIT",
                    "unit": 5,
                    "percentage": 17,
                    "remaining": 823,
                    "usage": 1000,
                    "currentValue": 177,
                    "nextResetTime": 1791118469998,
                    "usageDetails": [],
                }
            ],
        },
    },
    "status": "ok",
}

CODEX_ERROR_ENTRY: dict[str, Any] = {
    "family": "codex",
    "error": "codex not logged in (run: codex login)",
    "status": "error",
}

MUSE_UNSUPPORTED_ENTRY: dict[str, Any] = {
    "family": "muse",
    "reason": (
        "no structured usage source exposed by this family's runtime "
        "(headless exec stream carries no usage events; no usage "
        "subcommand; no local state file)"
    ),
    "status": "unsupported",
}

HEALTHZ_OK: dict[str, Any] = {
    "status": "ok",
    "service": "codex-chatgpt-web",
    "version": "5.0.6",
    "mode": "full",
    "pid": 3216,
    "port": 17841,
    "uptime": 149174.809,
    "accepting_turns": True,
    "successful_model_catalog_requests": 4684,
    "last_successful_model_catalog_request_at": "2026-09-15T15:59:34.641Z",
    "active_http_turns": 0,
    "active_browser_turns": 0,
}

TURN_COMPLETED: dict[str, Any] = {
    "version": 2,
    "capturedAt": "2026-09-15T15:48:05.710Z",
    "traceId": "00a81443ad9e",
    "checkpoint": "turn-completed",
    "state": {"composer": {"visibleCount": 1}},
}


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, n: int = -1) -> bytes:
        return self._payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _seed_turn_dir(root: Path, checkpoint: str, body: dict[str, Any]) -> Path:
    d = root / "00a81443ad9e-161c344c"
    d.mkdir(parents=True)
    (d / f"20-{checkpoint}.json").write_text(json.dumps(body), encoding="utf-8")
    return d


# ---- allow-list ----


def test_usage_allowlist_is_codex_glm_only() -> None:
    assert USAGE_PROBE_ALLOWLIST == frozenset({"codex", "glm"})


def test_muse_record_carries_no_usage_fields() -> None:
    rec = record_from_bridge_entry(MUSE_UNSUPPORTED_ENTRY, NOW_ISO)
    assert rec.family == "muse"
    assert rec.status == "unsupported"
    assert rec.parsed["value"] == "unknown"
    assert "reason" in rec.parsed
    usage_keys = {
        "percentage",
        "remaining",
        "usage",
        "currentValue",
        "nextResetTime",
        "limits",
        "plan",
        "planType",
    }
    assert not (set(rec.parsed) & usage_keys)


# ---- bridge usage 三形態 parse ----


def test_parse_glm_ok_entry() -> None:
    rec = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    assert rec.family == "glm"
    assert rec.pool == "glm-native"
    assert rec.status == "ok"
    assert rec.failure_class == "none"
    assert rec.parsed["plan"] == "pro"
    assert rec.parsed["limits"] == GLM_OK_ENTRY["raw"]["data"]["limits"]
    assert rec.raw == GLM_OK_ENTRY["raw"]


def test_parse_codex_error_is_fail_loud() -> None:
    rec = record_from_bridge_entry(CODEX_ERROR_ENTRY, NOW_ISO)
    assert rec.family == "codex"
    assert rec.pool == "codex-native"
    assert rec.status == "error"
    assert rec.failure_class == "upstream_error"
    assert rec.parsed["value"] == "unknown"
    assert "not logged in" in rec.parsed["detail"]


def test_parse_muse_unsupported_entry() -> None:
    rec = record_from_bridge_entry(MUSE_UNSUPPORTED_ENTRY, NOW_ISO)
    assert rec.status == "unsupported"
    assert rec.failure_class == "none"
    assert rec.parsed["value"] == "unknown"
    assert rec.parsed["reason"] == MUSE_UNSUPPORTED_ENTRY["reason"]


def test_bridge_entry_unknown_status_is_parse_error() -> None:
    with pytest.raises(_mod.BridgeParseError):
        record_from_bridge_entry({"family": "glm", "status": "weird"}, NOW_ISO)


# ---- bridge binary resolve ----


def test_resolve_bridge_binary_from_registry(tmp_path: Path) -> None:
    install = tmp_path / "cache" / "delegate" / "2.0.7"
    (install / "bin").mkdir(parents=True)
    binary = install / "bin" / "delegate-bridge"
    binary.write_text("", encoding="utf-8")
    registry = tmp_path / "installed_plugins.json"
    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "plugins": [
                    {"id": "other@x", "installPath": str(tmp_path / "other")},
                    {"id": "delegate@delegate-market", "installPath": str(install)},
                ],
            }
        ),
        encoding="utf-8",
    )
    assert resolve_bridge_binary(registry) == binary


def test_resolve_bridge_binary_missing_registry_fails_loud(tmp_path: Path) -> None:
    with pytest.raises(_mod.BridgeResolveError):
        resolve_bridge_binary(tmp_path / "absent.json")


def test_resolve_bridge_binary_missing_entry_fails_loud(tmp_path: Path) -> None:
    registry = tmp_path / "installed_plugins.json"
    registry.write_text(
        json.dumps({"version": 1, "plugins": [{"id": "other@x"}]}),
        encoding="utf-8",
    )
    with pytest.raises(_mod.BridgeResolveError):
        resolve_bridge_binary(registry)


# ---- bridge subprocess：timeout 與 transport ----


def test_run_bridge_usage_timeout_maps_to_transport_timeout(tmp_path: Path) -> None:
    binary = tmp_path / "bridge"

    def fake_runner(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="bridge", timeout=60)

    with pytest.raises(_mod.TransportTimeout):
        run_bridge_usage(binary, timeout_s=60.0, runner=fake_runner)


def test_run_bridge_usage_exit_one_with_valid_aggregate_is_consumed(
    tmp_path: Path,
) -> None:
    """bridge 契約：聚合內含 family error → exit 1，stdout 仍是完整報告。

    fail-loud 切面在 per-family status（upstream_error），非整體 exit。
    """
    binary = tmp_path / "bridge"
    aggregate = json.dumps({"families": [CODEX_ERROR_ENTRY, GLM_OK_ENTRY]})
    done = subprocess.CompletedProcess(
        args=["bridge"], returncode=1, stdout=aggregate, stderr=""
    )
    report = run_bridge_usage(binary, timeout_s=60.0, runner=lambda *a, **k: done)
    assert {e["family"] for e in report["families"]} == {"codex", "glm"}


def test_run_bridge_usage_nonzero_exit_maps_to_transport_error(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "bridge"
    done = subprocess.CompletedProcess(
        args=["bridge"], returncode=2, stdout="boom", stderr=""
    )
    with pytest.raises(_mod.BridgeTransportError):
        run_bridge_usage(binary, timeout_s=60.0, runner=lambda *a, **k: done)


def test_run_bridge_usage_exit_one_bad_json_maps_to_parse_error(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "bridge"
    done = subprocess.CompletedProcess(
        args=["bridge"], returncode=1, stdout="boom", stderr=""
    )
    with pytest.raises(_mod.BridgeParseError):
        run_bridge_usage(binary, timeout_s=60.0, runner=lambda *a, **k: done)


def test_run_bridge_usage_report_missing_families_is_parse_error(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "bridge"
    done = subprocess.CompletedProcess(
        args=["bridge"], returncode=0, stdout=json.dumps({"other": 1}), stderr=""
    )
    with pytest.raises(_mod.BridgeParseError):
        run_bridge_usage(binary, timeout_s=60.0, runner=lambda *a, **k: done)


def test_run_bridge_usage_bad_json_maps_to_parse_error(tmp_path: Path) -> None:
    binary = tmp_path / "bridge"
    done = subprocess.CompletedProcess(
        args=["bridge"], returncode=0, stdout="not json", stderr=""
    )
    with pytest.raises(_mod.BridgeParseError):
        run_bridge_usage(binary, timeout_s=60.0, runner=lambda *a, **k: done)


# ---- CODEX_HOME 注入（bridge 2.0.23 codex.rs default-branch bug workaround）----


def _capture_env_runner(captured: dict[str, Any]) -> Any:
    def fake_runner(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout=json.dumps({"families": [GLM_OK_ENTRY]}),
            stderr="",
        )

    return fake_runner


def test_run_bridge_usage_injects_codex_home_when_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """呼叫環境未設 CODEX_HOME → 注入 CODEX_HOME=<home>/.codex。

    bridge codex.rs:566-570 default branch 讀 $HOME/auth.json（缺
    .join(".codex")）恆報 not logged in——probe 端 env 注入暫解，
    bridge 2.0.24 修復後本 workaround 可移除。
    """
    captured: dict[str, Any] = {}
    monkeypatch.delenv("CODEX_HOME", raising=False)
    run_bridge_usage(
        tmp_path / "bridge", timeout_s=60.0, runner=_capture_env_runner(captured)
    )
    env = captured["env"]
    assert env is not None
    assert env["CODEX_HOME"] == str(Path.home() / ".codex")


def test_run_bridge_usage_preserves_existing_codex_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """呼叫環境已設 CODEX_HOME → 原值透傳，禁覆蓋。"""
    captured: dict[str, Any] = {}
    monkeypatch.setenv("CODEX_HOME", "/custom/codex-home")
    run_bridge_usage(
        tmp_path / "bridge", timeout_s=60.0, runner=_capture_env_runner(captured)
    )
    env = captured["env"]
    assert env is not None
    assert env["CODEX_HOME"] == "/custom/codex-home"


# ---- webgpt 兩訊號 ----


def test_webgpt_healthy_verdict(tmp_path: Path) -> None:
    _seed_turn_dir(tmp_path, "turn-completed", TURN_COMPLETED)
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=lambda url, timeout: _FakeResponse(json.dumps(HEALTHZ_OK).encode()),
    )
    assert rec.family == "codex"
    assert rec.pool == "chatgpt-web"
    assert rec.status == "ok"
    assert rec.failure_class == "none"
    assert rec.parsed["verdict"] == "healthy"
    assert rec.parsed["pool_visibility"] == "none"
    assert rec.parsed["accepting_turns"] is True
    assert rec.parsed["turn"]["checkpoint"] == "turn-completed"


def test_webgpt_rate_limited_turn_degrades(tmp_path: Path) -> None:
    failed = {
        **TURN_COMPLETED,
        "checkpoint": "turn-failed",
        "error": "rate limit exceeded, retry after backoff",
    }
    _seed_turn_dir(tmp_path, "turn-failed", failed)
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=lambda url, timeout: _FakeResponse(json.dumps(HEALTHZ_OK).encode()),
    )
    assert rec.status == "ok"
    assert rec.parsed["verdict"] == "degraded"
    assert rec.parsed["turn"]["rate_limited"] is True


def test_webgpt_unreachable_is_error(tmp_path: Path) -> None:
    import urllib.error

    def refuse(url: str, timeout: float) -> object:
        raise urllib.error.URLError("connection refused")

    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=refuse,
    )
    assert rec.status == "error"
    assert rec.failure_class == "transport_error"
    assert rec.parsed["value"] == "unknown"
    assert rec.parsed["verdict"] == "unreachable"


def test_webgpt_missing_turns_dir_is_not_unhealthy(tmp_path: Path) -> None:
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path / "browser-turns",
        opener=lambda url, timeout: _FakeResponse(json.dumps(HEALTHZ_OK).encode()),
    )
    assert rec.parsed["verdict"] == "healthy"
    assert rec.parsed["turn"]["signal"] == "absent"


def test_webgpt_accepting_turns_false_degrades(tmp_path: Path) -> None:
    healthz = {**HEALTHZ_OK, "accepting_turns": False}
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=lambda url, timeout: _FakeResponse(json.dumps(healthz).encode()),
    )
    assert rec.parsed["verdict"] == "degraded"


def test_webgpt_stale_catalog_degrades(tmp_path: Path) -> None:
    stale = {
        **HEALTHZ_OK,
        "last_successful_model_catalog_request_at": "2026-09-14T03:00:00.000Z",
    }
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=lambda url, timeout: _FakeResponse(json.dumps(stale).encode()),
    )
    assert rec.parsed["verdict"] == "degraded"


def test_webgpt_record_has_no_usage_numbers(tmp_path: Path) -> None:
    _seed_turn_dir(tmp_path, "turn-completed", TURN_COMPLETED)
    rec = probe_webgpt(
        NOW,
        healthz_url="http://127.0.0.1:17841/healthz",
        turns_root=tmp_path,
        opener=lambda url, timeout: _FakeResponse(json.dumps(HEALTHZ_OK).encode()),
    )
    forbidden = {"percentage", "remaining", "usage", "limits", "plan"}
    assert not (set(rec.parsed) & forbidden)


# ---- 落地檔：檔名／原子寫／latest 指針 ----


def test_record_filename_schema() -> None:
    rec = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    assert record_filename(rec) == "20260915T160000Z-glm-glm-native.json"


def test_write_record_atomic_with_latest_pointer(tmp_path: Path) -> None:
    rec = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    path, latest = write_record(tmp_path, rec)
    assert path == tmp_path / "20260915T160000Z-glm-glm-native.json"
    assert latest == tmp_path / "latest-glm-glm-native.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == 1
    assert loaded["family"] == "glm"
    assert loaded["pool"] == "glm-native"
    assert loaded["probe_ts_utc"] == NOW_ISO
    assert loaded["status"] == "ok"
    assert loaded["failure_class"] == "none"
    assert {"source", "parsed", "raw", "notes"} <= set(loaded)
    assert json.loads(latest.read_text(encoding="utf-8")) == loaded
    # 原子寫：無 tmp 殘留
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "20260915T160000Z-glm-glm-native.json",
        "latest-glm-glm-native.json",
    ]


def test_latest_age_minutes(tmp_path: Path) -> None:
    rec = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    write_record(tmp_path, rec)
    age = latest_age_minutes(tmp_path, "glm", "glm-native", NOW)
    assert age is not None and age < 1
    assert latest_age_minutes(tmp_path, "codex", "codex-native", NOW) is None


def test_min_interval_guard_blocks_fresh_probe(tmp_path: Path) -> None:
    rec = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    write_record(tmp_path, rec)
    reason = _mod.min_interval_skip_reason(
        tmp_path, rec.family, rec.pool, min_interval_min=30, now=NOW
    )
    assert reason is not None and "glm-native" in reason
    old = NOW - timedelta(hours=1)
    old_rec = record_from_bridge_entry(
        GLM_OK_ENTRY, old.isoformat().replace("+00:00", "Z")
    )
    write_record(tmp_path, old_rec)
    reason = _mod.min_interval_skip_reason(
        tmp_path, rec.family, rec.pool, min_interval_min=30, now=NOW
    )
    assert reason is None


# ---- exit 語義 ----


def test_aggregate_exit_any_ok_is_zero() -> None:
    ok = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    err = record_from_bridge_entry(CODEX_ERROR_ENTRY, NOW_ISO)
    unsup = record_from_bridge_entry(MUSE_UNSUPPORTED_ENTRY, NOW_ISO)
    assert aggregate_exit([ok, err, unsup]) == 0
    assert aggregate_exit([unsup]) == 1
    assert aggregate_exit([err, err]) == 1
    assert aggregate_exit([]) == 0  # 全 skip／全過濾＝非失敗


# ---- main：min-interval 全 skip → exit 0 且不落地新檔 ----


def test_main_all_skipped_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_dir = tmp_path / "probe-entitlements"
    fresh = record_from_bridge_entry(GLM_OK_ENTRY, NOW_ISO)
    write_record(out_dir, fresh)
    for family, pool in [
        ("glm", "glm-native"),
        ("codex", "codex-native"),
        ("codex", "chatgpt-web"),
        ("muse", "unknown"),
    ]:
        r = record_from_bridge_entry(
            GLM_OK_ENTRY if family == "glm" else MUSE_UNSUPPORTED_ENTRY, NOW_ISO
        )
        if family == "codex" or family == "muse":
            r = _mod.ProbeRecord(
                family=family,
                pool=pool,
                probe_ts_utc=NOW_ISO,
                source="test",
                status="unsupported",
                failure_class="none",
                parsed={"value": "unknown"},
                raw={},
                notes="",
            )
        write_record(out_dir, r)

    monkeypatch.setattr(_mod, "DEFAULT_OUT_DIR", out_dir)
    rc = _mod.main(["--min-interval", "30"])
    assert rc == 0


def test_main_family_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out_dir = tmp_path / "probe-entitlements"
    out_dir.mkdir()
    bin_dir = tmp_path / "delegate" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "delegate-bridge").write_text("", encoding="utf-8")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "version": 1,
                "plugins": [
                    {
                        "id": "delegate@delegate-market",
                        "installPath": str(bin_dir.parent),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def fake_runner(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=0,
            stdout=json.dumps(
                {
                    "families": [
                        MUSE_UNSUPPORTED_ENTRY,
                        CODEX_ERROR_ENTRY,
                        GLM_OK_ENTRY,
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(_mod, "DEFAULT_OUT_DIR", out_dir)
    monkeypatch.setattr(_mod, "DEFAULT_REGISTRY", registry)
    monkeypatch.setattr(_mod, "TURNS_ROOT", tmp_path / "turns")
    monkeypatch.setattr(_mod.subprocess, "run", fake_runner)
    rc = _mod.main(["--family", "glm"])
    assert rc == 0
    assert (out_dir / "latest-glm-glm-native.json").exists()
    assert not (out_dir / "latest-codex-chatgpt-web.json").exists()


# ---- P3：額度事件入帳（合成注入，禁真呼叫探測）----

capture_quota_event = _mod.capture_quota_event
spine_event_line = _mod.spine_event_line
reminder_log_line = _mod.reminder_log_line

# 三種簽名的合成 fixture——合成非真實報文樣本（單元測試輸入，未經 provider
# live 驗證；真實 native 報文多為人類可讀本地時間如 "try again at 3:30pm"，
# 解析器對非 ISO reset 一律 unknown——形態契約釘在解析器，首次 live 命中再校準）
NATIVE_429_MESSAGE = "codex-native request failed: HTTP 429 rate limit exceeded"
NATIVE_429_WITH_RESET_MESSAGE = (
    "codex-native request failed: HTTP 429 rate limit exceeded, "
    "resets at 2026-09-15T20:00:00Z"
)
GLM_1308_MESSAGE = (
    "GLM API error 1308: usage limit reached for current window, "
    "resets at 2026-09-15T18:00:00Z"
)
AMBIGUOUS_1308_MESSAGE = (
    "GLM API error 1308: usage limit reached, "
    "window started 2026-09-15T15:00:00Z, next window 2026-09-15T18:00:00Z"
)
DUAL_SIGNATURE_MESSAGE = (
    "GLM API error 1308: you've hit your usage limit, "
    "resets at 2026-09-15T18:00:00Z"
)
NATIVE_USAGE_LIMIT_MESSAGE = (
    "You've hit your usage limit for this plan, "
    "try again at 2026-09-15T19:30:00Z"
)
NATIVE_USAGE_LIMIT_NON_ISO_MESSAGE = (
    "You've hit your usage limit for this plan, try again at 3:30pm"
)


def test_capture_native_429_signature() -> None:
    event = capture_quota_event("codex", NATIVE_429_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.family == "codex"
    assert event.failure_class == "rate_limit_429"
    # 原生 429 訊息無重置時間戳 → retryable-at 顯性 unknown（禁推度）
    assert event.retryable_at_utc == "unknown"
    assert event.as_of_utc == NOW_ISO


def test_capture_native_429_with_reset_context_adopts_timestamp() -> None:
    """原生 429 若訊息含明確 reset 語境時間戳亦採用（docstring 與實作對齊）。"""
    event = capture_quota_event("codex", NATIVE_429_WITH_RESET_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "rate_limit_429"
    assert event.retryable_at_utc == "2026-09-15T20:00:00Z"


def test_capture_glm_1308_parses_reset_timestamp() -> None:
    event = capture_quota_event("glm", GLM_1308_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "usage_limit_1308"
    assert event.retryable_at_utc == "2026-09-15T18:00:00Z"


def test_capture_native_usage_limit_parses_retry_time() -> None:
    event = capture_quota_event("codex", NATIVE_USAGE_LIMIT_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "usage_limit_native"
    assert event.retryable_at_utc == "2026-09-15T19:30:00Z"


def test_capture_non_quota_message_returns_none() -> None:
    # None＝未識別，非無事件（簽名覆蓋窄——變體如 "quota exceeded" 不在表內）
    assert capture_quota_event("glm", "ordinary upstream failure", NOW_ISO) is None


def test_capture_input_validation_fails_loud() -> None:
    """family 白名單＋observed_at ISO 校驗——非法輸入 ValueError（禁透傳污染）。"""
    with pytest.raises(ValueError, match="family"):
        capture_quota_event("openai", NATIVE_429_MESSAGE, NOW_ISO)
    with pytest.raises(ValueError, match="observed_at"):
        capture_quota_event("glm", NATIVE_429_MESSAGE, "2026/09/15 16:00")


def test_capture_dual_signature_priority_is_1308() -> None:
    """雙簽名共存：優先序 1308＞usage limit＞429（確定性釘死，禁飄移）。"""
    event = capture_quota_event("glm", DUAL_SIGNATURE_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "usage_limit_1308"
    assert event.retryable_at_utc == "2026-09-15T18:00:00Z"


def test_capture_multi_timestamp_ambiguous_is_unknown_with_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """訊息含多個 ISO 時間戳且無法判定 reset 語境 → unknown＋log 原文（禁取首個）。"""
    with caplog.at_level(logging.WARNING, logger="scripts.probe_entitlements"):
        event = capture_quota_event("glm", AMBIGUOUS_1308_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "usage_limit_1308"
    assert event.retryable_at_utc == "unknown"
    assert "capture_quota_event:" in caplog.text
    assert "1308" in caplog.text  # 原文入 log


def test_capture_non_iso_reset_time_is_unknown() -> None:
    """非 ISO reset（人類可讀本地時間）→ unknown，禁把本地時間偽裝成 ISO。"""
    event = capture_quota_event("codex", NATIVE_USAGE_LIMIT_NON_ISO_MESSAGE, NOW_ISO)
    assert event is not None
    assert event.failure_class == "usage_limit_native"
    assert event.retryable_at_utc == "unknown"


def test_spine_event_line_has_four_fields() -> None:
    """spine 格式事件行＝as-of＋family＋failure_class＋retryable-at。"""
    event = capture_quota_event("glm", GLM_1308_MESSAGE, NOW_ISO)
    assert spine_event_line(event) == (
        "quota-event as_of=2026-09-15T16:00:00Z family=glm "
        "failure_class=usage_limit_1308 retryable_at=2026-09-15T18:00:00Z"
    )


def test_spine_event_line_unknown_retryable_kept_explicit() -> None:
    event = capture_quota_event("codex", NATIVE_429_MESSAGE, NOW_ISO)
    line = spine_event_line(event)
    assert "as_of=2026-09-15T16:00:00Z" in line
    assert "family=codex" in line
    assert "failure_class=rate_limit_429" in line
    assert "retryable_at=unknown" in line


def test_reminder_log_line_is_reminder_not_auto_write() -> None:
    """提醒式不自動寫：log 行指明由處置 session 校驗後更新 spine 事件行。"""
    event = capture_quota_event("glm", GLM_1308_MESSAGE, NOW_ISO)
    line = reminder_log_line(event)
    assert "[quota-event reminder]" in line
    assert "glm" in line
    assert "usage_limit_1308" in line
    assert "2026-09-15T18:00:00Z" in line
    assert "不自動寫" in line


# ---- P4：capability matrix（unsupported 顯性化）----

CAPABILITY_MATRIX = _mod.CAPABILITY_MATRIX
CAPABILITY_PROVENANCE_MUSE = _mod.CAPABILITY_PROVENANCE_MUSE

_USAGE_KEYS = {
    "percentage",
    "remaining",
    "usage",
    "currentValue",
    "nextResetTime",
    "limits",
    "plan",
    "planType",
}


def test_capability_matrix_values() -> None:
    assert CAPABILITY_MATRIX == {
        "codex": "supported",
        "glm": "supported",
        "muse": "unsupported",
    }


def test_matrix_unsupported_family_probe_yields_no_usage() -> None:
    """matrix unsupported family → probe 行為面：record 回 unsupported＋parsed 無任何用量鍵。

    行為面斷言（非 allow-list↔matrix 自指比對）——unsupported 是 capability
    事實，probe 路徑結構上不可能產生用量數字。
    """
    unsupported = [f for f, v in CAPABILITY_MATRIX.items() if v == "unsupported"]
    assert unsupported
    for family in unsupported:
        entry = {
            "family": family,
            "reason": "no structured usage source",
            "status": "unsupported",
        }
        rec = record_from_bridge_entry(entry, NOW_ISO)
        assert rec.status == "unsupported"
        assert not (set(rec.parsed) & _USAGE_KEYS)
        assert CAPABILITY_PROVENANCE_MUSE in rec.notes


def test_capability_matrix_muse_provenance_is_event_only() -> None:
    """muse 現值 provenance 結構 gate：常數被 notes 消費（非孤立字串）＋無用量鍵。"""
    rec = record_from_bridge_entry(MUSE_UNSUPPORTED_ENTRY, NOW_ISO)
    assert rec.status == "unsupported"
    assert CAPABILITY_PROVENANCE_MUSE in rec.notes
    assert not (set(rec.parsed) & _USAGE_KEYS)
    assert rec.raw == {}
    src = (REPO_ROOT / "scripts" / "probe_entitlements.py").read_text(
        encoding="utf-8"
    )
    # 常數非孤立：定義＋至少一處消費（provenance 是結構事實，非文案）
    assert src.count("CAPABILITY_PROVENANCE_MUSE") >= 2


# ---- 靜態反向斷言（A3 負向：模組無 spine 寫入路徑）----


def test_module_source_has_no_spine_write_surface() -> None:
    """rg 模組源碼：無 spine 寫入符號——單一寫者＝ai-guide session（AIR-98 決策②）。

    「提醒式不自動寫」的機械反向斷言：模組不知道 spine 路徑（零引用），
    寫入面唯一（_atomic_write_json 的 tmp 檔＋os.replace 原子換名），
    無 open() 寫模式呼叫。
    """
    src = (REPO_ROOT / "scripts" / "probe_entitlements.py").read_text(
        encoding="utf-8"
    )
    # spine 位置零引用：不知路徑即不可能寫入 ~/.agents/memory-spine
    assert "memory-spine" not in src
    assert "memory_spine" not in src
    # 寫入面唯一：唯一 .write_text/.write_bytes/.write 呼叫＝原子寫的 tmp 檔
    write_calls = re.findall(r"\.write_text\(|\.write_bytes\(|\.write\(", src)
    assert len(write_calls) == 1
    assert "os.replace(tmp, path)" in src
    # 無 open(...) 寫模式（w/a/x）
    assert not re.search(r"\bopen\([^)]*['\"][wax][+b]?'", src)
