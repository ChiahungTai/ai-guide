"""AIR-121——skills/post-build/scripts/review_ledger.py 契約測試。

fixture 全 in-repo（tests/fixtures/review_ledgers/，自 9 份歷史帳本固化）——
禁依賴 gitignored `.review/` 路徑。exit 契約：0 成功／1 解析失敗（fail-closed）／
2 帳本不存在／3 identity stale——四態各有案例斷言 exit code。
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "post-build" / "scripts" / "review_ledger.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "review_ledgers"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_MISSING = 2
EXIT_STALE = 3


def run_cli(
    subcommand: str, target: str | Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), subcommand, str(target), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def fixture(name: str) -> Path:
    return FIXTURES / name


def test_script_exists():
    assert SCRIPT.is_file(), f"缺少交付物：{SCRIPT}"


# ---------- exit 契約四態（lint 與 parse 各自覆蓋） ----------


def test_lint_ok_canonical():
    r = run_cli("lint", fixture("canonical-good.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "[OK]" in r.stdout


def test_parse_ok_canonical():
    r = run_cli("parse", fixture("canonical-good.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr


def test_lint_fail_canonical_violations():
    r = run_cli("lint", fixture("air-91.md"))
    assert r.returncode == EXIT_FAIL, r.stdout + r.stderr
    assert "[FAIL]" in r.stdout
    assert "identity.stale" not in r.stdout  # air-91 有 reviewed revision——非 stale


def test_parse_fail_no_findings_table():
    r = run_cli("parse", fixture("air-86.md"))
    assert r.returncode == EXIT_FAIL, r.stdout + r.stderr
    assert "no_findings_table" in r.stdout


def test_lint_missing_file():
    r = run_cli("lint", FIXTURES / "no-such-ledger.md")
    assert r.returncode == EXIT_MISSING, r.stdout + r.stderr
    assert "[FAIL]" in r.stderr


def test_parse_missing_file():
    r = run_cli("parse", FIXTURES / "no-such-ledger.md")
    assert r.returncode == EXIT_MISSING, r.stdout + r.stderr
    assert "[FAIL]" in r.stderr


def test_lint_identity_stale():
    r = run_cli("lint", fixture("air-66.md"))
    assert r.returncode == EXIT_STALE, r.stdout + r.stderr
    assert "identity.stale" in r.stdout


def test_parse_identity_stale():
    r = run_cli("parse", fixture("air-66.md"))
    assert r.returncode == EXIT_STALE, r.stdout + r.stderr
    assert "identity.stale" in r.stdout


# ---------- lint canonical 細部 ----------


def test_lint_air91_reports_missing_scope_and_columns():
    r = run_cli("lint", fixture("air-91.md"))
    assert r.returncode == EXIT_FAIL
    assert "identity.missing_scope" in r.stdout
    assert "columns.missing" in r.stdout
    assert "status.not_terminal" in r.stdout


def test_lint_air75_strict_identity_stale():
    # air-75 identity 寫「reviewed：」無「reviewed revision」——canonical lint（嚴格）判 stale
    r = run_cli("lint", fixture("air-75.md"))
    assert r.returncode == EXIT_STALE, r.stdout + r.stderr
    assert "identity.stale" in r.stdout


def test_lint_air86_missing_scope_and_table():
    r = run_cli("lint", fixture("air-86.md"))
    assert r.returncode == EXIT_FAIL
    assert "identity.missing_scope" in r.stdout
    assert "table.missing" in r.stdout


# ---------- parse 回歸分類（POC 語義錯誤的修正斷言） ----------


def test_parse_air91_join_last_wins_resolved():
    # POC naive 計數把 air-91 已 resolved 報成未決——ID-join last-wins 後應全 resolved
    r = run_cli("parse", fixture("air-91.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=5" in r.stdout
    assert "resolved=5" in r.stdout
    assert "未決=0" in r.stdout
    assert "tables=2" in r.stdout


def test_parse_air91_prose_negation_trap():
    # 否定句陷阱：air-91 Judge 段「零 ❌、零 ⚠️」禁被 prose 計數；
    # 決策無欄位 → 全 unknown（source=none），禁 prose fallback
    r = run_cli("parse", fixture("air-91.md"))
    assert r.returncode == EXIT_OK
    assert "decisions ✅=0/❌=0/⚠️=0/unknown=5" in r.stdout
    assert "source=none" in r.stdout


def test_parse_air75_free_text_status_not_terminal():
    # air-75 狀態自由文字漂移：implemented 不得計入 terminal——fail-closed 歸 unknown→未決
    r = run_cli("parse", fixture("air-75.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=9" in r.stdout
    assert "verified=1" in r.stdout
    assert "unknown=8" in r.stdout
    assert "未決=8" in r.stdout


def test_parse_air70_partial_decision_from_ruling_column():
    # air-70 部分解析：決策住「裁決」欄（✅3/⚠️1），無狀態欄 → 全 unknown（禁猜 resolved）
    r = run_cli("parse", fixture("air-70.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=4" in r.stdout
    assert "decisions ✅=3/❌=0/⚠️=1/unknown=0" in r.stdout
    assert "source=裁決" in r.stdout
    assert "未決=4" in r.stdout


def test_parse_air52_no_decision_column():
    # air-52 無決策欄：決策/status 全 unknown，禁猜
    r = run_cli("parse", fixture("air-52.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=6" in r.stdout
    assert "decisions ✅=0/❌=0/⚠️=0/unknown=6" in r.stdout
    assert "source=none" in r.stdout
    assert "未決=6" in r.stdout


def test_parse_canonical_good_full_tally():
    r = run_cli("parse", fixture("canonical-good.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=3" in r.stdout
    assert "decisions ✅=2/❌=1/⚠️=0/unknown=0" in r.stdout
    assert "source=決策" in r.stdout
    assert "resolved=1/verified=1/closed=1" in r.stdout
    assert "未決=0" in r.stdout


def test_parse_join_last_wins_fixture():
    # 後表 resolved 覆蓋前表 open（F-01）；前表獨有 open 保留（F-02）；「—」決策＝unknown
    r = run_cli("parse", fixture("join-last-wins.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=2" in r.stdout
    assert "resolved=1" in r.stdout
    assert "open=1" in r.stdout
    assert "未決=1" in r.stdout
    assert "decisions ✅=1/❌=0/⚠️=0/unknown=1" in r.stdout


# ---------- --stage 生命週期閘（F-1/F-2/F-4）：discovery 查結構、converged 全查 ----------


def test_lint_discovery_ok_on_judge_after_state():
    # judge 後態（decision=✅/⚠️、status=adopted/needs-confirmation）——discovery 只查
    # identity 錨＋欄位存在性（decision/status 值域不查）→ 應過（F-1 修復後形態）
    r = run_cli("lint", fixture("judge-after.md"), "--stage", "discovery")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "[OK]" in r.stdout


def test_lint_converged_fails_on_judge_after_state():
    # converged 全查：adopted/needs-confirmation 非 terminal → FAIL
    r = run_cli("lint", fixture("judge-after.md"), "--stage", "converged")
    assert r.returncode == EXIT_FAIL, r.stdout + r.stderr
    assert "status.not_terminal" in r.stdout


def test_lint_default_stage_is_converged():
    # 無 --stage＝converged（現行為不變）：judge 後態必 FAIL——F-1 根因
    # （post-build 階段 2 舊 lint 閘與發現時態帳本互斥）的機械重現
    r = run_cli("lint", fixture("judge-after.md"))
    assert r.returncode == EXIT_FAIL, r.stdout + r.stderr
    assert "status.not_terminal" in r.stdout


def test_lint_discovery_ok_on_followup_after_state():
    r = run_cli("lint", fixture("followup-after.md"), "--stage", "discovery")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr


def test_lint_converged_ok_on_followup_after_state():
    # converged：verified/closed＝canonical terminal、resolved＝容錯 terminal（F-2）→ 應過
    r = run_cli("lint", fixture("followup-after.md"), "--stage", "converged")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr


def test_lint_discovery_still_checks_identity_and_columns():
    # discovery 不等於免檢：identity 錨缺席（air-66）仍 STALE、欄位缺（air-91 缺 scope/
    # 欄位）仍 FAIL——值域才是 discovery 豁免面
    r = run_cli("lint", fixture("air-66.md"), "--stage", "discovery")
    assert r.returncode == EXIT_STALE, r.stdout + r.stderr
    r2 = run_cli("lint", fixture("air-91.md"), "--stage", "discovery")
    assert r2.returncode == EXIT_FAIL, r2.stdout + r2.stderr
    assert "identity.missing_scope" in r2.stdout
    assert "columns.missing" in r2.stdout
    assert "status.not_terminal" not in r2.stdout  # 值域不查


def test_lint_invalid_stage_rejected():
    r = run_cli("lint", fixture("canonical-good.md"), "--stage", "bogus")
    assert r.returncode == EXIT_FAIL, r.stdout + r.stderr
    assert "usage" in r.stderr


def test_parse_judge_after_pending_counts():
    # parse（容錯讀）：needs-confirmation → open、adopted → unknown（自由文字）——皆計未決
    r = run_cli("parse", fixture("judge-after.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=2" in r.stdout
    assert "decisions ✅=1/❌=0/⚠️=1/unknown=0" in r.stdout
    assert "source=決策" in r.stdout
    assert "open=1" in r.stdout
    assert "未決=2" in r.stdout


def test_parse_followup_after_all_terminal():
    # followup 後態：resolved（容錯）/verified/closed 全 terminal——未決=0
    r = run_cli("parse", fixture("followup-after.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=3" in r.stdout
    assert "resolved=1/verified=1/closed=1" in r.stdout
    assert "未決=0" in r.stdout


# ---------- 兩形 identity 錨（F-3）----------


def test_lint_accepts_reviewed_equals_form():
    # canonical 模板（workflow-review-pattern 表格呈現格式）identity 行形＝`reviewed=<hash>`；
    # 舊錨（字面 reviewed revision）會誤判 stale——兩形皆 canonical
    r = run_cli("lint", fixture("judge-after.md"), "--stage", "discovery")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "identity.stale" not in r.stdout


def test_lint_still_rejects_reviewed_colon_form():
    # 「reviewed：」單形仍非 canonical 錨（air-75 回歸；discovery 態複驗）
    r = run_cli("lint", fixture("air-75.md"), "--stage", "discovery")
    assert r.returncode == EXIT_STALE, r.stdout + r.stderr
    assert "identity.stale" in r.stdout


# ---------- code fence 表格跳過（F-6）----------


def test_parse_skips_fenced_example_table():
    # 帳本內嵌格式說明表格（``` 圍欄內、含 ID 欄）禁計數——舊行為會把 X-99 撈進 findings
    r = run_cli("parse", fixture("fenced-example.md"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "findings=2" in r.stdout
    assert "tables=1" in r.stdout
    assert "未決=0" in r.stdout


def test_lint_skips_fenced_example_table():
    # lint 的 Finding Record 表定位同樣跳過 fenced 表（取真表——欄位全、terminal 全）
    r = run_cli("lint", fixture("fenced-example.md"), "--stage", "converged")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr


# ---------- 模組載入煙霧測試（非 package 腳本，importlib 直載） ----------


def test_module_loads_with_exit_contract_constants():
    spec = importlib.util.spec_from_file_location("review_ledger_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (mod.EXIT_OK, mod.EXIT_FAIL, mod.EXIT_MISSING, mod.EXIT_STALE) == (
        0,
        1,
        2,
        3,
    )
