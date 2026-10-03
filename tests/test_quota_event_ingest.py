"""quota_event_ingest 契約測試（AIR-244——quota-event ingress closure）。

釘住的 invariant（codex 審核 §B 項目 2——reader 有、writer 無的 contract hole）：
- production entry：synthetic 簽名一律經 CLI main()（ingest-event／ingest
  ledger sweep），非 helper 直呼——真實 dispatch failure 面（bridge ledger
  jobs.json 的 errorExcerpt 欄）與測試走同一入口。
- 恰一筆：單一事件 → 恰一 JSONL row（{family, message, observed_at_utc}
  三鍵 verbatim）；同事件重跑冪等不重複。
- unknown signature 禁偽造 → 0 筆、事件檔不建（檔案缺席＝零事件，reader
  D2 契約）。
- malformed family／observed-at → fail-loud exit 2、零寫入（all-or-nothing
  ——sweep 途中有 malformed row 即整批不落盤）。
- ledger sweep：errorExcerpt 持有原始 provider failure message＝
  authoritative failure surface；whitelist-外 family（grok）skip 非偽造；
  1302 rate-path 非額度簽名 → 0 筆。
- 閉環：producer 寫出的 row 被 entitlement_window_snapshot 重 parse →
  state=unavailable＋retryable_at 帶值（既有 reader 零改動）。
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from conftest import load_module

ing = load_module("scripts/quota_event_ingest.py")
snap = load_module("scripts/entitlement_window_snapshot.py")

NOW = datetime(2026, 10, 2, 22, 0, 0, tzinfo=UTC)
NOW_ISO = "2026-10-02T22:00:00Z"
FRESH_PROBE_TS = "2026-10-02T21:04:21Z"  # ~1h old（< 26h）
GLM_RESET_TS = "2026-10-03T03:00:00Z"

# 三簽名 synthetic（形狀照真實 failure surface——bridge ledger errorExcerpt
# 實錄／model-routing spawn 失敗態表；reset 時間戳用 ISO T 格式釘
# retryable_at 帶值路徑。真實 GLM 1308 的空格格式時間戳 → parser
# retryable=unknown 屬 parser 單一源既有行為，本卡不動 probe 檔）。
GLM_1308_MSG = (
    "ProviderBusinessError: [1308][Usage limit reached for 5 hour. "
    f"Your limit will reset at {GLM_RESET_TS}][20261002154822025db723cefa4fc5]"
)
CODEX_USAGE_MSG = (
    "You've hit your usage limit. Please try again at 2026-10-03T08:00:00Z"
)
RATE_429_MSG = "HTTP 429 too many requests (resets at 2026-10-02T23:30:00Z)"
GLM_1302_MSG = (
    "ProviderBusinessError: [1302][Rate limit reached for requests]"
    "[202609220541266263f44c16ac4135]"
)


def read_events(probe_dir: Path) -> list[dict[str, str]]:
    path = probe_dir / "quota-events.jsonl"
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_ingest_event(
    probe_dir: Path,
    family: str,
    message: str,
    capsys: pytest.CaptureFixture[str],
    observed_at: str = NOW_ISO,
) -> int:
    rc = ing.main(
        [
            "ingest-event",
            "--family",
            family,
            "--message",
            message,
            "--observed-at",
            observed_at,
            "--probe-dir",
            str(probe_dir),
        ]
    )
    capsys.readouterr()
    return rc


# ---- ingest-event：三簽名經 production entry → 恰一筆 ----


@pytest.mark.parametrize(
    "family,message",
    [
        ("glm", GLM_1308_MSG),
        ("codex", CODEX_USAGE_MSG),
        ("muse", RATE_429_MSG),
    ],
)
def test_quota_event_ingest_three_signatures_exactly_one_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], family: str, message: str
) -> None:
    probe_dir = tmp_path / "probe"
    rc = run_ingest_event(probe_dir, family, message, capsys)
    assert rc == 0
    events = read_events(probe_dir)
    assert len(events) == 1
    assert set(events[0]) == {"family", "message", "observed_at_utc"}
    assert events[0] == {
        "family": family,
        "message": message,
        "observed_at_utc": NOW_ISO,
    }


def test_quota_event_ingest_rerun_same_event_stays_one_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    probe_dir = tmp_path / "probe"
    assert run_ingest_event(probe_dir, "glm", GLM_1308_MSG, capsys) == 0
    assert run_ingest_event(probe_dir, "glm", GLM_1308_MSG, capsys) == 0
    assert len(read_events(probe_dir)) == 1


# ---- unknown signature 禁偽造／malformed fail-loud ----


def test_quota_event_ingest_unknown_signature_writes_zero_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    probe_dir = tmp_path / "probe"
    rc = run_ingest_event(probe_dir, "glm", "ordinary upstream failure", capsys)
    assert rc == 0
    assert read_events(probe_dir) == []
    assert not (probe_dir / "quota-events.jsonl").exists()


def test_quota_event_ingest_malformed_family_fails_loud(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    probe_dir = tmp_path / "probe"
    rc = run_ingest_event(probe_dir, "openai", GLM_1308_MSG, capsys)
    assert rc == 2
    assert read_events(probe_dir) == []


def test_quota_event_ingest_malformed_observed_at_fails_loud(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    probe_dir = tmp_path / "probe"
    rc = run_ingest_event(
        probe_dir, "glm", GLM_1308_MSG, capsys, observed_at="2026/09/15 16:00"
    )
    assert rc == 2
    assert read_events(probe_dir) == []


# ---- ingest：ledger sweep——authoritative failure surface 接線 ----


def seed_ledger(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def test_quota_event_ingest_ledger_sweep_writes_signature_hits_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = tmp_path / "jobs.json"
    seed_ledger(
        ledger,
        [
            {  # 簽名命中（真實 ledger 形狀：failed-usage＋errorExcerpt）
                "id": "job-glm-1308",
                "status": "failed-usage",
                "family": "glm",
                "timestamp": "2026-10-02T15:48:22.025Z",
                "errorExcerpt": GLM_1308_MSG,
            },
            {  # 簽名命中（native usage limit）
                "id": "job-codex-usage",
                "status": "failed-usage",
                "family": "codex",
                "timestamp": "2026-10-02T16:30:00.000Z",
                "errorExcerpt": CODEX_USAGE_MSG,
            },
            {  # 1302 rate-path 非額度簽名 → 0 筆
                "id": "job-glm-1302",
                "status": "rate-limited",
                "family": "glm",
                "timestamp": "2026-10-02T17:00:00.000Z",
                "errorExcerpt": GLM_1302_MSG,
            },
            {  # whitelist-外 family → skip（非偽造）
                "id": "job-grok-x",
                "status": "failed-usage",
                "family": "grok",
                "timestamp": "2026-10-02T17:30:00.000Z",
                "errorExcerpt": GLM_1308_MSG,
            },
            {  # 無 errorExcerpt（completed）→ 非 candidate
                "id": "job-glm-ok",
                "status": "completed",
                "family": "glm",
                "timestamp": "2026-10-02T18:00:00.000Z",
            },
        ],
    )
    probe_dir = tmp_path / "probe"
    rc = ing.main(
        [
            "ingest",
            "--ledger",
            str(ledger),
            "--probe-dir",
            str(probe_dir),
        ]
    )
    capsys.readouterr()
    assert rc == 0
    events = read_events(probe_dir)
    assert [e["family"] for e in events] == ["glm", "codex"]
    assert events[0]["message"] == GLM_1308_MSG
    assert events[0]["observed_at_utc"] == "2026-10-02T15:48:22.025Z"
    assert events[1]["message"] == CODEX_USAGE_MSG


def test_quota_event_ingest_ledger_sweep_idempotent_rerun(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = tmp_path / "jobs.json"
    seed_ledger(
        ledger,
        [
            {
                "id": "job-glm-1308",
                "status": "failed-usage",
                "family": "glm",
                "timestamp": "2026-10-02T15:48:22.025Z",
                "errorExcerpt": GLM_1308_MSG,
            }
        ],
    )
    probe_dir = tmp_path / "probe"
    argv = ["ingest", "--ledger", str(ledger), "--probe-dir", str(probe_dir)]
    assert ing.main(argv) == 0
    assert ing.main(argv) == 0
    capsys.readouterr()
    assert len(read_events(probe_dir)) == 1


def test_quota_event_ingest_ledger_malformed_timestamp_fails_loud_all_or_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ledger = tmp_path / "jobs.json"
    seed_ledger(
        ledger,
        [
            {
                "id": "job-glm-1308-ok-ts",
                "status": "failed-usage",
                "family": "glm",
                "timestamp": "2026-10-02T15:48:22.025Z",
                "errorExcerpt": GLM_1308_MSG,
            },
            {  # 契約內 row 的 malformed timestamp → 整批 fail-loud 零寫入
                "id": "job-codex-bad-ts",
                "status": "failed-usage",
                "family": "codex",
                "timestamp": "09/28/2026 17:00",
                "errorExcerpt": CODEX_USAGE_MSG,
            },
        ],
    )
    probe_dir = tmp_path / "probe"
    rc = ing.main(["ingest", "--ledger", str(ledger), "--probe-dir", str(probe_dir)])
    capsys.readouterr()
    assert rc == 2
    assert read_events(probe_dir) == []


# ---- 閉環：producer row → 既有 reader 重 parse ----


def test_quota_event_ingest_closure_reader_reparses_producer_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    probe_dir = tmp_path / "probe"
    probe_dir.mkdir()
    # reader rows 以 probe latest-*.json 為底（family/pool 集）——seed 一筆
    # fresh ok probe（形狀照 test_entitlement_window_snapshot.seed_probe）
    latest = {
        "schema_version": 1,
        "family": "glm",
        "pool": "glm-native",
        "probe_ts_utc": FRESH_PROBE_TS,
        "source": "delegate-bridge usage --json",
        "status": "ok",
        "failure_class": "none",
        "parsed": {"value": "unknown"},
        "raw": {},
        "notes": "",
    }
    (probe_dir / "latest-glm-glm-native.json").write_text(
        json.dumps(latest, ensure_ascii=False), encoding="utf-8"
    )
    spine = tmp_path / "spine.md"
    spine.write_text(
        "# model-runtime-entitlements\n\n"
        "**as-of 2026-10-02**（test fixture）\n\n"
        "可用池（as-of 2026-10-02）：muse/unknown\n",
        encoding="utf-8",
    )

    # production writer 寫出事件（1308＋ISO reset 時間戳）
    rc = run_ingest_event(probe_dir, "glm", GLM_1308_MSG, capsys)
    assert rc == 0

    # 既有 reader（零改動）重 parse → glm row state=unavailable＋retryable 帶值
    rc = snap.main(
        ["--probe-dir", str(probe_dir), "--spine", str(spine), "--json"],
        now=NOW,
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "entitlement-window-snapshot/1"
    glm_rows = [r for r in payload["rows"] if r["family"] == "glm"]
    assert len(glm_rows) == 1
    row = glm_rows[0]
    assert row["source"] == "quota-event"
    assert row["freshness"] == "fresh"
    assert row["state"] == "unavailable"
    assert row["retryable_at"] == GLM_RESET_TS
