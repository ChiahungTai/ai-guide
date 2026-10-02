"""entitlement_window_snapshot 契約測試（AIR-239——planning 證據 evaluator）。

釘住的 invariant（設計契約 tri 定稿，見 .agent-tmp/air-239/journal-impl.md）：
- 衝突序：fresh direct probe/event > spine observation；spine fresh 而 probe
  stale 時 spine 勝；全源 stale → state=unknown（stale 當 available 的
  mutation 必紅——否證測試）。
- muse 誠實條款：probe unsupported → state=unknown、retryable_at 缺席；
  無 anchor 時合成 reset 的 mutation 必紅（否證測試）；帶唯一 provider
  reset 時間戳的 quota-event 例外。
- retryable_at：provider reset 時間戳 only（禁 5h 週期合成）；唯一值才
  生成、歧義或缺席 → None。
- 五鍵輸出契約＋evaluator-not-router（禁 rank/selected/fallback 欄位）。
- fail-loud：--probe-dir 缺席／malformed／未來時間戳 → exit 2。

fixtures 自造（probe 實檔形狀照 ~/.agents/probe-entitlements/
latest-muse-unknown.json 與 latest-glm-glm-native.json；spine 形狀照
availability_snapshot 測試慣例）。quota-event 載體＝probe-dir 內
quota-events.jsonl（raw message intake，parser 邏輯重用
probe_entitlements.capture_quota_event 單一源）。
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from conftest import load_module

snap = load_module("scripts/entitlement_window_snapshot.py")

NOW = datetime(2026, 10, 2, 22, 0, 0, tzinfo=UTC)
NOW_ISO = "2026-10-02T22:00:00Z"
FRESH_TS = "2026-10-02T21:04:21Z"  # ~1h old（< 26h）
STALE_TS = "2026-10-01T12:00:00Z"  # 34h（> 26h）
BOUNDARY_FRESH_TS = "2026-10-01T20:00:00Z"  # 恰 26h——age == 閾值＝fresh
BOUNDARY_STALE_TS = "2026-10-01T19:00:00Z"  # 27h——stale
SPINE_FRESH_AS_OF = "2026-10-02"  # age 0d
SPINE_STALE_AS_OF = "2026-09-26"  # age 6d > 3d
MUSE_RESET_TS = "2026-10-03T00:00:00Z"
GLM_RESET_MS = 1791118469000  # → 2026-10-04T12:54:29Z（秒級 floor）
GLM_RESET_ISO = "2026-10-04T12:54:29Z"
GLM_TOKENS_RESET_MS = 1790975473246  # 相異第二窗（→ 2026-10-02T21:11:13Z）
CODEX_RESET_S = 1791400000  # → 2026-10-07T19:06:40Z

MUSE_RESET_MSG = (
    "muse request failed: HTTP 429 Subscription quota exhausted "
    f"(resets at {MUSE_RESET_TS})"
)
MUSE_AMBIGUOUS_MSG = (
    "muse 429: resets at 2026-10-03T00:00:00Z and resets at "
    "2026-10-03T05:00:00Z"
)

ROW_KEYS = {
    "family",
    "pool",
    "source",
    "observed_at",
    "freshness",
    "state",
    "retryable_at",
}


def seed_probe(
    probe_dir: Path,
    family: str,
    pool: str,
    ts: str,
    *,
    status: str = "ok",
    parsed: dict[str, Any] | None = None,
    raw: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "family": family,
        "pool": pool,
        "probe_ts_utc": ts,
        "source": "delegate-bridge usage --json",
        "status": status,
        "failure_class": "upstream_error" if status == "error" else "none",
        "parsed": parsed if parsed is not None else {"value": "unknown"},
        "raw": raw if raw is not None else {},
        "notes": "",
    }
    (probe_dir / f"latest-{family}-{pool}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def seed_events(probe_dir: Path, lines: list[dict[str, str]]) -> None:
    body = "".join(
        json.dumps(line, ensure_ascii=False) + "\n" for line in lines
    )
    (probe_dir / "quota-events.jsonl").write_text(body, encoding="utf-8")


def seed_spine(path: Path, as_of: str, available_line: str) -> None:
    path.write_text(
        "# model-runtime-entitlements\n\n"
        f"**as-of {as_of}**（test fixture）\n\n"
        f"{available_line}\n",
        encoding="utf-8",
    )


def make_spine(tmp_path: Path, as_of: str, available_line: str) -> Path:
    spine = tmp_path / "spine.md"
    seed_spine(spine, as_of, available_line)
    return spine


def run_json(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> tuple[int, dict[str, Any]]:
    rc = snap.main([*argv, "--json"], now=NOW)
    out = capsys.readouterr().out
    return rc, json.loads(out)


def row_of(rows: list[dict[str, Any]], family: str, pool: str) -> dict[str, Any]:
    hits = [r for r in rows if r["family"] == family and r["pool"] == pool]
    assert len(hits) == 1, f"expected one {family}/{pool} row, got {hits}"
    return hits[0]


# ---- 衝突序三條 ----


def test_fresh_probe_beats_spine_contradiction(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(
        probe_dir,
        "glm",
        "glm-native",
        FRESH_TS,
        parsed={"plan": "pro", "limits": [{"type": "TIME_LIMIT", "nextResetTime": GLM_RESET_MS}]},
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：codex")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "glm", "glm-native")
    assert row["source"] == "probe"
    assert row["state"] == "available"
    assert row["freshness"] == "fresh"
    assert row["observed_at"] == FRESH_TS
    assert row["retryable_at"] == GLM_RESET_ISO


def test_fresh_spine_wins_when_probe_stale(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "glm", "glm-native", STALE_TS)
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：GLM")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "glm", "glm-native")
    assert row["source"] == "spine"
    assert row["state"] == "available"
    assert row["freshness"] == "fresh"
    assert row["observed_at"] == f"{SPINE_FRESH_AS_OF}T00:00:00Z"
    assert row["retryable_at"] is None  # spine 慢事實不供 reset 錨點


def test_all_sources_stale_yields_unknown(tmp_path, capsys) -> None:
    # mutation 否證：stale 證據當 available 的實作必紅
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(
        probe_dir,
        "glm",
        "glm-native",
        STALE_TS,
        parsed={"plan": "pro", "limits": [{"type": "TIME_LIMIT", "nextResetTime": GLM_RESET_MS}]},
    )
    spine = make_spine(tmp_path, SPINE_STALE_AS_OF, "- **可用**：GLM")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "glm", "glm-native")
    assert row["state"] == "unknown"
    assert row["freshness"] == "stale"
    assert row["retryable_at"] is None  # stale 證據不供現值錨點


# ---- muse 誠實條款＋reset 時間戳壓週期推算 ----


def test_muse_unsupported_without_anchor_unknown_no_retryable(
    tmp_path, capsys
) -> None:
    # mutation 否證：無 anchor 時從 5h 週期合成 reset 的實作必紅
    # spine 用 stale——隔離 muse 誠實條款（probe 是唯一 fresh 證據層）
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    spine = make_spine(tmp_path, SPINE_STALE_AS_OF, "- **可用**：muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "muse", "unknown")
    assert row["state"] == "unknown"
    assert row["retryable_at"] is None
    assert row["source"] == "probe"


def test_fresh_spine_available_claim_survives_unsupported_probe(
    tmp_path, capsys
) -> None:
    # D4 has_state：spine fresh 的 available 主張是有資訊量的慢事實，
    # 壓過 unsupported probe 的零資訊 unknown——主張帶 source=spine 溯源，
    # 非合成（合成禁令針對 retryable_at 週期推算，見上測試）
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "muse", "unknown")
    assert row["source"] == "spine"
    assert row["state"] == "available"
    assert row["retryable_at"] is None  # spine 恆不供 reset 錨點


def test_quota_event_unique_reset_pins_literal(tmp_path, capsys) -> None:
    # provider reset 時間戳逐字帶出——週期推算（ts+5h 類）的實作必紅
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    seed_events(
        probe_dir,
        [{"family": "muse", "observed_at_utc": "2026-10-02T21:30:00Z", "message": MUSE_RESET_MSG}],
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "muse", "unknown")
    assert row["source"] == "quota-event"
    assert row["state"] == "unavailable"
    assert row["freshness"] == "fresh"
    assert row["retryable_at"] == MUSE_RESET_TS


def test_event_outranks_unsupported_probe_even_when_older(
    tmp_path, capsys
) -> None:
    # 有 state 主張的證據壓過 unsupported（零資訊量）probe——即使較舊
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    seed_events(
        probe_dir,
        [{"family": "muse", "observed_at_utc": "2026-10-02T12:00:00Z", "message": MUSE_RESET_MSG}],
    )
    spine = make_spine(tmp_path, SPINE_STALE_AS_OF, "- **可用**：muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "muse", "unknown")
    assert row["source"] == "quota-event"
    assert row["state"] == "unavailable"
    assert row["retryable_at"] == MUSE_RESET_TS


def test_quota_event_ambiguous_reset_no_retryable(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    seed_events(
        probe_dir,
        [
            {
                "family": "muse",
                "observed_at_utc": "2026-10-02T21:30:00Z",
                "message": MUSE_AMBIGUOUS_MSG,
            }
        ],
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "muse", "unknown")
    assert row["state"] == "unavailable"
    assert row["retryable_at"] is None  # 歧義→缺，禁揀首個


# ---- retryable_at provider 欄位抽取（唯一值才生成）----


def test_glm_multiple_distinct_provider_resets_yield_none(
    tmp_path, capsys
) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(
        probe_dir,
        "glm",
        "glm-native",
        FRESH_TS,
        parsed={
            "plan": "pro",
            "limits": [
                {"type": "TIME_LIMIT", "nextResetTime": GLM_RESET_MS},
                {"type": "TOKENS_LIMIT", "nextResetTime": GLM_TOKENS_RESET_MS},
            ],
        },
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：GLM")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    row = row_of(payload["rows"], "glm", "glm-native")
    assert row["state"] == "available"
    assert row["retryable_at"] is None  # ≥2 相異值＝歧義→缺（禁揀選）


def test_codex_native_reset_from_primary_window(tmp_path, capsys) -> None:
    # 實檔形狀：reset_at 住 raw.rate_limit.primary_window（secondary=null）
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(
        probe_dir,
        "codex",
        "codex-native",
        FRESH_TS,
        parsed={"plan": "plus", "limits": None},
        raw={
            "rate_limit": {
                "allowed": True,
                "limit_reached": False,
                "primary_window": {
                    "limit_window_seconds": 604800,
                    "reset_after_seconds": 488993,
                    "reset_at": CODEX_RESET_S,
                    "used_percent": 56,
                },
                "secondary_window": None,
            }
        },
    )
    seed_probe(
        probe_dir,
        "codex",
        "chatgpt-web",
        FRESH_TS,
        parsed={"verdict": "healthy", "pool_visibility": "none"},
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：codex")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    native = row_of(payload["rows"], "codex", "codex-native")
    assert native["state"] == "available"
    assert native["retryable_at"] == "2026-10-07T19:06:40Z"
    web = row_of(payload["rows"], "codex", "chatgpt-web")
    assert web["state"] == "available"
    assert web["retryable_at"] is None


def test_codex_native_dual_windows_distinct_resets_yield_none(
    tmp_path, capsys
) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(
        probe_dir,
        "codex",
        "codex-native",
        FRESH_TS,
        parsed={"plan": "plus", "limits": None},
        raw={
            "rate_limit": {
                "primary_window": {"reset_at": CODEX_RESET_S, "used_percent": 56},
                "secondary_window": {"reset_at": 1791464054, "used_percent": 10},
            }
        },
    )
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：codex")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    native = row_of(payload["rows"], "codex", "codex-native")
    assert native["retryable_at"] is None  # ≥2 相異值＝歧義→缺


def test_codex_two_pools_separate_rows(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "codex", "codex-native", FRESH_TS)
    seed_probe(probe_dir, "codex", "chatgpt-web", FRESH_TS)
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：codex")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    pools = sorted(r["pool"] for r in payload["rows"])
    assert pools == ["chatgpt-web", "codex-native"]


# ---- freshness 邊界（age 恰等於閾值＝fresh）----


def test_probe_freshness_boundary_exact_threshold(tmp_path, capsys) -> None:
    for ts, want_freshness, want_state in (
        (BOUNDARY_FRESH_TS, "fresh", "available"),
        (BOUNDARY_STALE_TS, "stale", "unknown"),
    ):
        probe_dir = tmp_path / f"probe-{want_freshness}"
        probe_dir.mkdir()
        seed_probe(probe_dir, "glm", "glm-native", ts)
        spine = make_spine(
            probe_dir, SPINE_STALE_AS_OF, "- **可用**：GLM"
        )
        rc, payload = run_json(
            ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
        )
        assert rc == 0
        row = row_of(payload["rows"], "glm", "glm-native")
        assert row["freshness"] == want_freshness, ts
        assert row["state"] == want_state, ts


# ---- 輸出契約（五鍵＋evaluator-not-router）----


def test_output_contract_exact_keys(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "glm", "glm-native", FRESH_TS)
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS, status="unsupported")
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：GLM＋muse")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    assert set(payload) == {"schema", "generated_at", "rows"}
    assert payload["schema"] == "entitlement-window-snapshot/1"
    assert payload["generated_at"] == NOW_ISO
    assert payload["rows"], "rows 不應為空"
    for row in payload["rows"]:
        assert set(row) == ROW_KEYS
        assert row["state"] in {"available", "unavailable", "unknown"}
        assert row["freshness"] in {"fresh", "stale"}
        assert row["source"] in {"probe", "quota-event", "spine"}


def test_rows_sorted_display_determinism(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS)
    seed_probe(probe_dir, "codex", "chatgpt-web", FRESH_TS)
    seed_probe(probe_dir, "glm", "glm-native", FRESH_TS)
    seed_probe(probe_dir, "codex", "codex-native", FRESH_TS)
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：三家")
    rc, payload = run_json(
        ["--probe-dir", str(probe_dir), "--spine", str(spine)], capsys
    )
    assert rc == 0
    keys = [(r["family"], r["pool"]) for r in payload["rows"]]
    assert keys == sorted(keys)


# ---- fail-loud 輸入契約 ----


def test_probe_dir_missing_exit_2(capsys) -> None:
    rc = snap.main(
        ["--probe-dir", "/nonexistent/probe-dir", "--json"], now=NOW
    )
    assert rc == 2


def test_empty_probe_dir_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    rc = snap.main(["--probe-dir", str(probe_dir), "--json"], now=NOW)
    assert rc == 2


def test_malformed_latest_json_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    (probe_dir / "latest-glm-glm-native.json").write_text("{broken", encoding="utf-8")
    rc = snap.main(["--probe-dir", str(probe_dir), "--json"], now=NOW)
    assert rc == 2


def test_quota_events_malformed_line_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS)
    (probe_dir / "quota-events.jsonl").write_text("{oops\n", encoding="utf-8")
    rc = snap.main(["--probe-dir", str(probe_dir), "--json"], now=NOW)
    assert rc == 2


def test_quota_events_unknown_family_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "muse", "unknown", FRESH_TS)
    seed_events(
        probe_dir,
        [{"family": "grok", "observed_at_utc": FRESH_TS, "message": MUSE_RESET_MSG}],
    )
    rc = snap.main(["--probe-dir", str(probe_dir), "--json"], now=NOW)
    assert rc == 2


def test_future_probe_ts_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "glm", "glm-native", "2026-10-02T23:00:00Z")
    rc = snap.main(["--probe-dir", str(probe_dir), "--json"], now=NOW)
    assert rc == 2


def test_explicit_spine_missing_exit_2(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "glm", "glm-native", FRESH_TS)
    rc = snap.main(
        ["--probe-dir", str(probe_dir), "--spine", str(tmp_path / "absent.md")],
        now=NOW,
    )
    assert rc == 2


def test_flag_without_value_exit_2(tmp_path) -> None:
    rc = snap.main(["--probe-dir"], now=NOW)
    assert rc == 2


# ---- 人話輸出（非 --json）----


def test_human_mode_lists_rows(tmp_path, capsys) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    seed_probe(probe_dir, "glm", "glm-native", FRESH_TS)
    spine = make_spine(tmp_path, SPINE_FRESH_AS_OF, "- **可用**：GLM")
    rc = snap.main(["--probe-dir", str(probe_dir), "--spine", str(spine)], now=NOW)
    out = capsys.readouterr().out
    assert rc == 0
    assert "glm/glm-native" in out
    assert "state=available" in out
