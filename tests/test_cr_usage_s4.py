"""AIR-224 muse-F12——cr_usage.py 源4 S4 掃描函數 golden test。

`scan_receipt_ledgers`／`scan_brief_routes`／`scan_crsurface` 鎖七分項計數口徑
（eligible／declared／receipt／degraded／n-a／closure／silent fallback）——
monkeypatch 模組常數（GITHUB／DB）指向 tmp_path 合成樹，不觸真實 home 目錄。
函數面 advisory-only（只計數不驗收），golden 值＝已知輸入的手算口徑。
"""

import importlib.util
import json
import sqlite3
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "corrections-weekly" / "scripts" / "cr_usage.py"


@pytest.fixture()
def cr_usage():
    spec = importlib.util.spec_from_file_location("cr_usage_s4", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


WINDOW_S = time.time() - 3600  # 窗口起點（過去）——合成檔 mtime 恆在窗內


def test_scan_receipt_ledgers_golden(cr_usage, tmp_path, monkeypatch):
    """七分項手算口徑：三本合成帳本——
    full.md：legs 2 trigger＋1 n/a；receipt live-cr:MCP＋degraded；n/a receipt；
            closure 1 → eligible=2／receipts=2／degraded=1／na=1／closure=1／silent=0
    ephemeral.md：1 trigger＋bridge 形 ref receipt → eligible+1／receipts+1／ephemeral=1
    silent.md：1 trigger 無 receipt → eligible+1／silent=1
    合計：eligible=4／receipts=3／degraded=1／na=1／closure=1／silent=1
    """
    review = tmp_path / "repoA" / ".review"
    review.mkdir(parents=True)
    (review / "full.md").write_text(
        "# .review/full.md — golden fixture\n"
        "- legs：L1 job-a trigger；L2 job-b trigger；L3 job-c n/a\n"
        "- L1: cr(route=live-cr:MCP, evidence=docs/provenance.md)\n"
        "- L2: cr(route=degraded, reason=no-cr-query-face)\n"
        "- L3: cr: n/a（reason=無結構查證 trigger）\n"
        "- cr-closure：L1 checked\n",
        encoding="utf-8",
    )
    (review / "ephemeral.md").write_text(
        "# .review/ephemeral.md — golden fixture\n"
        "- legs：L9 job-x trigger\n"
        "- L9: cr(route=live-cr:CLI, evidence=.delegate-bridge/jobs/j1.jsonl)\n",
        encoding="utf-8",
    )
    (review / "silent.md").write_text(
        "# .review/silent.md — golden fixture\n- legs：L7 job-y trigger\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(cr_usage, "GITHUB", tmp_path)
    out = cr_usage.scan_receipt_ledgers(WINDOW_S)
    assert out["ledgers"] == 3
    assert out["eligible"] == 4
    assert out["receipts"] == 3
    assert out["degraded"] == 1
    assert out["na_receipts"] == 1
    assert out["closures"] == 1
    assert out["silent_fallback"] == 1
    assert out["ephemeral_refs"] == 1


def test_scan_brief_routes_golden(cr_usage, tmp_path, monkeypatch):
    """declared 分項：payload_type=turn.input.user 的 prompt 內 route 宣告才計——
    bare `live-cr`（producer 宣告面）與 `live-cr:MCP` 各一；非 user payload 不計。"""
    jobs = tmp_path / "repoA" / ".delegate-bridge" / "jobs"
    jobs.mkdir(parents=True)
    rows = [
        (
            "job1.jsonl",
            {"payload_type": "turn.input.user", "payload": {"prompt": "前置 route：live-cr:MCP 後續"}},
        ),
        (
            "job2.jsonl",
            {"payload_type": "turn.input.user", "payload": {"prompt": "route：live-cr（bare 宣告面）"}},
        ),
        ("job3.jsonl", {"payload_type": "item.completed", "payload": {"prompt": "route：degraded"}}),
    ]
    for name, row in rows:
        (jobs / name).write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setattr(cr_usage, "GITHUB", tmp_path)
    out = cr_usage.scan_brief_routes(WINDOW_S)
    assert out["jobs"] == 3
    assert out["declared_jobs"] == 2
    assert out["values"] == {"live-cr:MCP": 1, "live-cr": 1}


def test_scan_crsurface_golden(cr_usage, tmp_path, monkeypatch):
    """crsurface 分布：只計 part 文字內 `crsurface=<face>` 出現次數。"""
    db_path = tmp_path / "db.sqlite"
    db = sqlite3.connect(db_path)
    try:
        db.execute("CREATE TABLE part (data TEXT, time_created INTEGER)")
        now_ms = int(time.time() * 1000)
        for text in (
            "宣告 crsurface=mcp 投影",
            "第二筆 crsurface=absent 降級",
            "無 crsurface 的 part",
        ):
            db.execute(
                "INSERT INTO part VALUES (?, ?)",
                (json.dumps({"text": text}), now_ms),
            )
        db.commit()
    finally:
        db.close()
    monkeypatch.setattr(cr_usage, "DB", db_path)
    values = cr_usage.scan_crsurface(0)
    assert values == {"mcp": 1, "absent": 1}
