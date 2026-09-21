"""AIR-151——improvement_signals 四類掃描器契約測試（muse 151-F1：fail-soft 不得
吞掉 miscount——每個掃描分支都要有 fixture 釘住計數行為）。

路徑隔離：全部 fixture 落 pytest tmp_path；churn 掃描用 tmp git repo（git init）。
"""

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest
from conftest import load_module

_sig = load_module("scripts/improvement_signals.py")
NOW = dt.datetime(2026, 9, 22, 12, 0, 0, tzinfo=dt.UTC)


# ---------- ①review 殘留 ----------

def test_review_residue_counts_open_rows_skips_fenced(tmp_path: Path) -> None:
    review = tmp_path / ".review"
    review.mkdir()
    (review / "air-9.md").write_text(
        "| id | 狀態 | 問題 |\n|---|---|---|\n"
        "| U1 | open | 未閉一 |\n"
        "| U2 | resolved | 已閉不算 |\n"
        "```\n| F1 | open | 圍欄內格式範例不算 |\n```\n",
        encoding="utf-8",
    )
    out = _sig.scan_review_residue(tmp_path)
    assert out["count"] == 1
    assert "U1" in out["pointers"][0]


def test_review_residue_legacy_ledger_without_status_col_skipped(tmp_path: Path) -> None:
    """無「狀態」欄的 legacy 帳本＝機械不可分類——跳過不誤計（worker 實跑發現）。"""
    review = tmp_path / ".review"
    review.mkdir()
    (review / "legacy.md").write_text("| id | 內容 |\n|---|---|\n| X1 | 狀態不明 |\n", encoding="utf-8")
    out = _sig.scan_review_residue(tmp_path)
    assert out["count"] == 0 and out["scanned_files"] == 0


def test_review_residue_missing_dir_zero(tmp_path: Path) -> None:
    out = _sig.scan_review_residue(tmp_path)
    assert out["count"] == 0 and "note" in out


# ---------- ②liveness 異常 ----------

def _job(jid: str, status: str, days_ago: float, excerpt: str = "") -> dict:
    ts = NOW - dt.timedelta(days=days_ago)
    row = {"id": jid, "status": status, "timestamp": ts.isoformat()}
    if excerpt:
        row["errorExcerpt"] = excerpt
    return row


def test_liveness_buckets_and_window(tmp_path: Path) -> None:
    (tmp_path / ".delegate-bridge").mkdir()
    (tmp_path / ".delegate-bridge" / "jobs.json").write_text(
        json.dumps([
            _job("j1", "auth-failed", 1),
            _job("j2", "interrupted", 1),
            _job("j3", "failed-or-capped", 1, "429 too many requests"),
            _job("j4", "failed-or-capped", 1, "provider config broken"),
            _job("j5", "completed", 0),
            _job("j6", "auth-failed", 30),  # 窗口外不計
        ]),
        encoding="utf-8",
    )
    out = _sig.scan_liveness(tmp_path, 7, NOW)
    assert out["by_kind"] == {
        "terminal-other": 1, "rate-limited": 1, "auth-failed": 1, "interrupted": 1,
    }
    assert out["count"] == 4


def test_liveness_generic_failure_not_labeled_sink_missing(tmp_path: Path) -> None:
    """未驗 sink 的 generic 終態失敗＝terminal-other（codex 151-C4——禁冒稱 sink-missing）。"""
    (tmp_path / ".delegate-bridge").mkdir()
    (tmp_path / ".delegate-bridge" / "jobs.json").write_text(
        json.dumps([_job("j1", "failed-configuration", 0)]), encoding="utf-8"
    )
    out = _sig.scan_liveness(tmp_path, 7, NOW)
    assert "terminal-sink-missing" not in out["by_kind"]
    assert out["by_kind"]["terminal-other"] == 1


# ---------- ③跨弧重現 ----------

def _git_commit(repo: Path, filename: str, n: int) -> None:
    f = repo / filename
    f.write_text(f"v{n}", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-m", f"c{n}", f"--date={NOW.isoformat()}"],
        check=True, capture_output=True,
    )


def test_recurrence_threshold_join(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    for n in range(3):
        _git_commit(tmp_path, "hot.py", n)
    _git_commit(tmp_path, "cold.py", 99)
    out = _sig.scan_recurrence(tmp_path, 7)
    hot = {p["path"]: p["commits"] for p in out["pointers"]}
    assert hot.get("hot.py") == 3  # 達門檻
    assert "cold.py" not in hot  # 單次是噪音


# ---------- ④預算超支＋cap ----------

def test_budget_keywords_and_cap(tmp_path: Path) -> None:
    journal = tmp_path / ".agent-tmp" / "session-journal.md"
    journal.parent.mkdir(parents=True)
    lines = ["- revert 舊法（掉進 silent rollback）"]
    lines += [f"- L{i} 正常行" for i in range(30)]
    lines.append("- job stall 卡住兩輪")
    journal.write_text("\n".join(lines), encoding="utf-8")
    out = _sig.scan_budget(tmp_path)
    assert out["by_kind"] == {"revert": 1, "stall": 1}
    assert out["count"] == 2


def test_pointers_capped_at_20(tmp_path: Path) -> None:
    journal = tmp_path / ".agent-tmp" / "session-journal.md"
    journal.parent.mkdir(parents=True)
    journal.write_text(
        "\n".join(f"- revert #{i}" for i in range(25)), encoding="utf-8"
    )
    out = _sig.scan_budget(tmp_path)
    assert out["count"] == 25 and len(out["pointers"]) == _sig.CAP  # 計數真實、指針 capped


# ---------- KPI 彙總 ----------

def test_aggregate_kpi_counts_dismissed(tmp_path: Path) -> None:
    kpi = tmp_path / "kpi.jsonl"
    kpi.write_text(
        "\n".join([
            json.dumps({"event": "reviewed", "source": "s1"}),
            json.dumps({"event": "opened", "source": "s1"}),
            json.dumps({"event": "settled", "source": "s1"}),
            json.dumps({"event": "dismissed", "source": "s2"}),
            "not-json",
        ]),
        encoding="utf-8",
    )
    out = _sig.aggregate_kpi(kpi)
    assert out["per_source"]["s1"] == {"reviewed": 1, "opened": 1, "settled": 1, "dismissed": 0}
    assert out["per_source"]["s2"]["dismissed"] == 1
    assert out["total"]["reviewed"] == 1 and out["total"]["dismissed"] == 1
    assert "malformed" in out["note"]
