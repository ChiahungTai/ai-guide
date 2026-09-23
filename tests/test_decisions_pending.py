"""AIR-151——decisions_pending kind/gate/meta schema 擴充＋--add-improvement＋KPI 記數 測試。

覆蓋（工單任務 3＋任務 4 最小 KPI 測試）：
- nonblocking improvement row 不擋 lint --card；blocking decision row 照擋
- close --obsolete（docstring 宣告的 obsolete 終態——CLI 補實作）
- --add-improvement roundtrip（row＋meta 落帳→解析回讀欄位齊全）
- 舊 7 欄列相容（kind/gate/meta 預設 decision/blocking/空）
- KPI 漏斗 reviewed→opened→settled（add-improvement／promote／close improvement 事件，
  decision row close 不記數）＋improvement_signals.aggregate_kpi per-source 彙總

路徑隔離：monkeypatch 模組級 LEDGER／KPI_FILE 到 pytest tmp_path（repo 測試慣例），
不觸 canonical 台帳。
"""

import json
import sys
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/decisions_pending.py")
_signals = load_module("scripts/improvement_signals.py")


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    ledger = tmp_path / "DECISIONS-PENDING.md"
    kpi = tmp_path / "improvement-kpi.jsonl"
    correction_kpi = tmp_path / "correction-kpi.jsonl"
    monkeypatch.setattr(_mod, "LEDGER", ledger)
    monkeypatch.setattr(_mod, "KPI_FILE", kpi)
    monkeypatch.setattr(_mod, "CORRECTION_KPI_FILE", correction_kpi)
    return ledger, kpi, correction_kpi


def run_cli(*argv: str) -> str:
    """跑 CLI（回傳 stdout）；非零 exit 以 SystemExit 浮出交由個別測試斷言。"""
    monkey_backup = sys.argv
    sys.argv = ["decisions_pending.py", *argv]
    try:
        _mod.main()
    finally:
        sys.argv = monkey_backup
    return ""  # stdout 斷言不必要——行為以台帳/KPI 檔案狀態與 SystemExit 驗證


# ---------- lint 閘：nonblocking 不擋、blocking 照擋 ----------

def test_nonblocking_improvement_does_not_block_lint(env) -> None:
    run_cli(
        "add-improvement", "AIR-151", "bridge 失敗重現候選",
        "--source", "liveness_anomaly", "--evidence-ref", "jobs.json#x",
        "--class", "reliability", "--cost", "S",
    )
    run_cli("lint", "--card", "AIR-151")  # 不 raise＝exit 0——discovery 不阻塞 Settle/Done


def test_blocking_decision_still_blocks_lint(env) -> None:
    run_cli("add", "AIR-151", "A 還是 B？", "A/B")
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--card", "AIR-151")
    assert ei.value.code == 1


def test_global_dash_card_row_original_semantics(env) -> None:
    """原版語義保持：card=- 的列只在 lint --card - 時浮出，不擋其他卡。"""
    run_cli("add", "-", "全域待決")
    run_cli("lint", "--card", "AIR-999")  # - 列不擋其他卡（既有行為不變）
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--card", "-")
    assert ei.value.code == 1


# ---------- close --obsolete ----------

def test_close_obsolete(env) -> None:
    ledger, _, _ckpi = env
    run_cli("add", "AIR-151", "暫緩項")
    run_cli("close", "D-001", "dismiss——TTL 過期", "--obsolete")
    rows = _mod._load(ledger)
    assert rows[0]["status"] == "obsolete"
    run_cli("lint", "--card", "AIR-151")  # obsolete 非開放態——不擋


def test_close_decided_unchanged(env) -> None:
    ledger, _, _ckpi = env
    run_cli("add", "AIR-151", "正常決策")
    run_cli("close", "D-001", "決定 A（見卡 notes）")
    rows = _mod._load(ledger)
    assert rows[0]["status"] == "decided"
    assert rows[0]["note"] == "決定 A（見卡 notes）"


# ---------- --add-improvement roundtrip＋schema 欄位 ----------

def test_add_improvement_roundtrip(env) -> None:
    ledger, _, _ckpi = env
    run_cli(
        "--add-improvement", "AIR-151", "bridge 失敗訊號重現——provision 檢查前置化",
        "--source", "liveness_anomaly",
        "--evidence-ref", ".delegate-bridge/jobs.json#job-x",
        "--class", "reliability",
        "--cost", "S",
    )
    rows = _mod._load(ledger)
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "D-001"
    assert row["kind"] == "improvement"
    assert row["gate"] == "nonblocking"
    assert row["status"] == "open"
    assert row["question"] == "bridge 失敗訊號重現——provision 檢查前置化"
    meta = _mod._parse_meta(row["meta"])
    assert meta["source"] == "liveness_anomaly"
    assert meta["evidence_ref"] == ".delegate-bridge/jobs.json#job-x"
    assert meta["class"] == "reliability"
    assert meta["cost"] == "S"


def test_improvement_gate_is_always_nonblocking(env) -> None:
    """卡規格：improvement kind 必帶 nonblocking——CLI 無旗標可覆寫（hardcode）。"""
    ledger, _, _ckpi = env
    run_cli(
        "add-improvement", "AIR-151", "別名拼法候選", "--source", "review_residue",
        "--evidence-ref", ".review/air-9.md::U1", "--class", "friction", "--cost", "M",
    )
    row = _mod._load(ledger)[0]
    assert row["kind"] == "improvement" and row["gate"] == "nonblocking"


def test_add_improvement_rejects_missing_provenance(env, capsys) -> None:
    """四欄必填（codex 151-C2）——缺任一即拒收（防污染 source-segmented KPI）。"""
    ledger, kpi, _ckpi = env
    with pytest.raises(SystemExit) as ei:
        run_cli("add-improvement", "AIR-151", "缺 evidence", "--source", "review_residue")
    assert ei.value.code == 2
    with pytest.raises(SystemExit):
        run_cli(
            "add-improvement", "AIR-151", "缺 cost", "--source", "review_residue",
            "--evidence-ref", "x", "--class", "friction",
        )
    assert not ledger.exists() and not kpi.exists()  # 拒收＝零落帳


def test_add_improvement_rejects_unknown_source(env) -> None:
    """source 為四值 enum——自由文字 typo 會製造 KPI 假分桶（codex 151-C2）。"""
    with pytest.raises(SystemExit) as ei:
        run_cli(
            "add-improvement", "AIR-151", "自由文字源", "--source", "我看到的問題",
            "--evidence-ref", "x", "--class", "friction", "--cost", "S",
        )
    assert ei.value.code == 2


def test_row_date_is_local_calendar_date(env) -> None:
    """row 日期＝本機日曆日（codex 151-C5：UTC 日期在 Taipei 00:00–08:00 慢一天，
    TTL 計齊跟著錯）。"""
    import datetime
    ledger, _, _ckpi = env
    run_cli("add", "AIR-151", "日期面")
    row = _mod._load(ledger)[0]
    assert row["date"] == datetime.datetime.now().astimezone().date().isoformat()


def test_legacy_seven_column_row_defaults(env) -> None:
    """舊 7 欄列相容：kind/gate/meta 缺欄預設 decision/blocking/空——既有行為不變。"""
    ledger, _, _ckpi = env
    ledger.write_text(
        "# Pending decisions\n\n"
        "| id | 日期 | 卡 | 問題 | 選項 | 狀態 | 備註 |\n"
        "|----|------|----|------|------|------|------|\n"
        "| D-001 | 2026-09-19 | AIR-135.2 | 舊形問題 | A/B | open | 舊備註 |\n",
        encoding="utf-8",
    )
    rows = _mod._load(ledger)
    assert rows[0]["kind"] == "decision"
    assert rows[0]["gate"] == "blocking"
    assert rows[0]["meta"] == ""
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--card", "AIR-135.2")
    assert ei.value.code == 1  # 舊形 open decision 照樣擋——既有行為不變


def test_empty_cells_parse_after_roundtrip(env) -> None:
    """空 cell（無 options／無 meta）roundtrip——+ 量詞吃 padding space 的 latent bug 回歸測試。"""
    ledger, _, _ckpi = env
    run_cli("add", "AIR-151", "無 options 的決策")
    rows = _mod._load(ledger)
    assert len(rows) == 1 and rows[0]["question"] == "無 options 的決策"
    assert rows[0]["gate"] == "blocking"


# ---------- promote ----------

def test_promote_improvement_row(env) -> None:
    ledger, _, _ckpi = env
    run_cli(
        "add-improvement", "AIR-151", "候選", "--source", "budget_overspend",
        "--evidence-ref", "journal#L1", "--class", "efficiency", "--cost", "L",
    )
    run_cli("promote", "D-001", "AIR-160")
    row = _mod._load(ledger)[0]
    assert row["status"] == "decided"
    assert "AIR-160" in row["note"]


def test_promote_rejects_decision_row(env) -> None:
    run_cli("add", "AIR-151", "普通決策")
    with pytest.raises(SystemExit) as ei:
        run_cli("promote", "D-001", "AIR-160")
    assert ei.value.code == 1


# ---------- KPI 漏斗（任務 4 最小測試） ----------

def test_kpi_funnel_reviewed_opened_settled_and_dismissed(env) -> None:
    """漏斗（codex 151-C3 修後語義）：reviewed→opened→settled 可達（promoted row 的
    close）；未 promote 即 close＝dismissed（與 opened 互斥的終態，非 settled）。"""
    _ledger, kpi, _ckpi = env
    run_cli(
        "add-improvement", "AIR-151", "候選A", "--source", "liveness_anomaly",
        "--evidence-ref", "j#1", "--class", "reliability", "--cost", "S",
    )
    run_cli("promote", "D-001", "AIR-160")
    run_cli("close", "D-001", "AIR-160 Settle 收線")  # promoted→settled 終段
    run_cli(
        "add-improvement", "AIR-151", "候選B", "--source", "review_residue",
        "--evidence-ref", ".review/x.md::U1", "--class", "friction", "--cost", "M",
    )
    run_cli("close", "D-002", "dismiss", "--obsolete")  # 未 promote→dismissed
    events = [json.loads(line) for line in kpi.read_text(encoding="utf-8").splitlines()]
    assert [(e["event"], e["id"]) for e in events] == [
        ("reviewed", "D-001"),
        ("opened", "D-001"),
        ("settled", "D-001"),
        ("reviewed", "D-002"),
        ("dismissed", "D-002"),
    ]
    assert events[0]["source"] == "liveness_anomaly"
    assert events[0]["cost_bucket"] == "S"
    agg = _signals.aggregate_kpi(kpi)
    assert agg["total"]["reviewed"] == 2 and agg["total"]["opened"] == 1
    assert agg["total"]["settled"] == 1
    rows = _mod._load(_ledger)
    assert rows[0]["status"] == "obsolete" and rows[0]["note"].startswith("settled")


def test_update_improvement_bumps_recurrence(env) -> None:
    """重現訊號走 update 不建新 row（dedupe 機械面——codex 151-C1）。"""
    ledger, _, _ckpi = env
    run_cli(
        "add-improvement", "AIR-151", "重現候選", "--source", "cross_arc_recurrence",
        "--evidence-ref", "old#1", "--class", "friction", "--cost", "S",
    )
    run_cli("update", "D-001", "--evidence-ref", "new#2")
    row = _mod._load(ledger)[0]
    meta = _mod._parse_meta(row["meta"])
    assert meta["evidence_ref"] == "new#2"
    assert meta["recurrence"] == "2"
    assert meta["lastSeen"] == _mod._today()
    assert len(_mod._load(ledger)) == 1  # 不建新 row


def test_ls_stale_days_filters_old_open_improvements(env) -> None:
    """TTL 面：--stale-days 只列超齡 open improvement（codex 151-C1）。"""
    ledger, _, _ckpi = env
    run_cli(
        "add-improvement", "AIR-151", "舊候選", "--source", "review_residue",
        "--evidence-ref", "x", "--class", "friction", "--cost", "S",
    )
    rows = _mod._load(ledger)
    rows[0]["date"] = "2026-08-01"  # 人造 50 天前
    _mod._save(rows, ledger)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_cli("ls", "--open", "--stale-days", "14")
    assert "D-001" in buf.getvalue()  # 超齡→浮出
    run_cli(
        "add-improvement", "AIR-151", "新候選", "--source", "review_residue",
        "--evidence-ref", "y", "--class", "friction", "--cost", "M",
    )
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        run_cli("ls", "--open", "--stale-days", "14")
    assert "D-001" in buf2.getvalue() and "D-002" not in buf2.getvalue()  # 新候選不列


def test_kpi_not_written_for_decision_rows(env) -> None:
    _ledger, kpi, _ckpi = env
    run_cli("add", "AIR-151", "普通決策")
    run_cli("close", "D-001", "決定 A")
    assert not kpi.exists()  # decision kind 不入 improvement 漏斗


# ---------- AIR-135.8：correction kind＋lint --dispatch＋correction KPI ----------

def test_add_correction_row_roundtrip(env) -> None:
    """correction kind row 解析：add --kind correction 落帳 kind=correction gate=blocking。"""
    ledger, _, _ckpi = env
    run_cli("add", "AIR-135.8", "commit 委任語義再教一次", "--kind", "correction")
    row = _mod._load(ledger)[0]
    assert row["id"] == "D-001"
    assert row["kind"] == "correction"
    assert row["gate"] == "blocking"
    assert row["status"] == "open"
    assert row["card"] == "AIR-135.8"


def test_add_default_kind_stays_decision(env) -> None:
    """--days 式既有行為不變的對應面：add 不帶 --kind 仍落 decision。"""
    ledger, _, _ckpi = env
    run_cli("add", "AIR-135.8", "普通待決")
    assert _mod._load(ledger)[0]["kind"] == "decision"


def test_lint_dispatch_blocks_open_correction(env) -> None:
    """Dispatch-gate：目標卡 open＋kind=correction＋gate=blocking → exit 1（禁派工先收編）。"""
    run_cli("add", "AIR-135.8", "main-seat 預設又教一次", "--kind", "correction")
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--dispatch", "AIR-135.8")
    assert ei.value.code == 1


def test_lint_dispatch_passes_after_close(env) -> None:
    """close（收編）後 dispatch gate 放行。"""
    ledger, _, _ = env
    run_cli("add", "AIR-135.8", "講人話再教一次", "--kind", "correction")
    run_cli("close", "D-001", "已收編進 post-build checkpoint（見收尾報告指針）")
    run_cli("lint", "--dispatch", "AIR-135.8")  # 不 raise＝exit 0
    assert _mod._load(ledger)[0]["status"] == "decided"


def test_lint_dispatch_scoped_to_card(env) -> None:
    """D-d：按卡關聯擋，非全域擋——他卡 correction 不擋本卡 dispatch。"""
    run_cli("add", "AIR-999", "他卡的 correction", "--kind", "correction")
    run_cli("lint", "--dispatch", "AIR-135.8")  # 不 raise＝exit 0


def test_lint_dispatch_ignores_decision_and_improvement_rows(env) -> None:
    """dispatch gate 只看 correction——同卡 open decision/improvement 不擋 dispatch
   （decision 照舊由 lint --card 擋 Done）。"""
    run_cli("add", "AIR-135.8", "普通決策 open")
    run_cli(
        "add-improvement", "AIR-135.8", "improvement 候選", "--source", "review_residue",
        "--evidence-ref", "x", "--class", "friction", "--cost", "S",
    )
    run_cli("lint", "--dispatch", "AIR-135.8")  # 不 raise＝exit 0
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--card", "AIR-135.8")  # decision 照舊擋 Done-gate
    assert ei.value.code == 1


def test_correction_row_also_blocks_card_done_gate(env) -> None:
    """open correction gate=blocking 也擋 lint --card（未收編不結卡——同一 row 進兩個 gate）。"""
    run_cli("add", "AIR-135.8", "未收編 correction", "--kind", "correction")
    with pytest.raises(SystemExit) as ei:
        run_cli("lint", "--card", "AIR-135.8")
    assert ei.value.code == 1


def test_correction_kpi_detected_and_incorporated(env) -> None:
    """correction KPI 漏斗：add --kind correction 記 detected；close decided 記 incorporated
    （欄位＝ts／id／event 三欄；檔路徑錨定 .agents/correction-kpi.jsonl）。"""
    _ledger, _, _ = env
    ckpi = _mod.CORRECTION_KPI_FILE
    run_cli("add", "AIR-135.8", "plugin 授權語義再教", "--kind", "correction")
    run_cli("close", "D-001", "已收編進 rules/outward-action-consent.md（commit 段）")
    events = [json.loads(line) for line in ckpi.read_text(encoding="utf-8").splitlines()]
    assert [(e["event"], e["id"]) for e in events] == [
        ("detected", "D-001"),
        ("incorporated", "D-001"),
    ]
    assert set(events[0].keys()) == {"ts", "id", "event"}


def test_correction_obsolete_close_records_no_extra_kpi(env) -> None:
    """--obsolete 收 correction 不記新 KPI 事件——enum 無 dismissed 值，禁冒充 restated。"""
    _ledger, _, ckpi = env
    run_cli("add", "AIR-135.8", "撤回的 correction", "--kind", "correction")
    run_cli("close", "D-001", "誤報撤回", "--obsolete")
    events = [json.loads(line) for line in ckpi.read_text(encoding="utf-8").splitlines()]
    assert [e["event"] for e in events] == ["detected"]


def test_correction_kpi_isolated_from_improvement_kpi(env) -> None:
    """correction KPI 走獨立檔（correction-kpi.jsonl）——decision close 兩檔都不寫。"""
    _ledger, kpi, ckpi = env
    run_cli("add", "AIR-135.8", "普通決策")
    run_cli("close", "D-001", "決定 B")
    assert not ckpi.exists() and not kpi.exists()
