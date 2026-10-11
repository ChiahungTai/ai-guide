"""card_validate 單元測試（AIR-309 P1）——四層檢查逐層 case＋DB-109 原始樣本
regression＋CLI 三模式（file／--all／--staged）exit code 契約。

harness：subprocess 直跑腳本（sys.executable）。pytest 專案環境無 pyyaml——每次
呼叫都實測「缺 import → uv run --no-project --with pyyaml 自癒 re-exec」路徑
（yaml 在場的環境則直跑，兩態皆須過）。--all／--staged 於 tmp repo 進行，不觸
本板 working tree（板上有 session 在飛卡，live 全板掃描屬工單驗證步驟非單元測試）。
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "card_validate.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "card_validate"


def run_cli(*args, cwd=REPO_ROOT, script=None):
    return subprocess.run(
        [sys.executable, str(script or SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )


def fixture(name):
    return str(FIXTURES / name)


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


def _seed_repo(tmp_path):
    """tmp git repo：seed commit 完成，backlog/tasks/ 待 staging。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "user.email", "t@t")
    (repo / "README.md").write_text("seed\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _copy_script(root):
    """--all 以腳本所在 repo 為根——tmp 板測試須把腳本複製進 tmp repo 同構。"""
    (root / "scripts").mkdir(exist_ok=True)
    shutil.copy2(SCRIPT, root / "scripts" / "card_validate.py")


# ── 層① delimiter ────────────────────────────────────────────────
def test_layer1_missing_closing_delimiter():
    r = run_cli(fixture("broken_delimiter.md"))
    assert r.returncode == 1
    assert "FAIL" in r.stdout
    assert "[delimiter]" in r.stdout
    assert "closing" in r.stdout  # 未閉合型訊號


def test_layer1_missing_opening_delimiter(tmp_path):
    p = tmp_path / "no_open.md"
    p.write_text("id: AIR-9000\n---\n", encoding="utf-8")
    r = run_cli(str(p))
    assert r.returncode == 1
    assert "[delimiter]" in r.stdout
    assert "opening" in r.stdout


# ── 層② YAML strict ──────────────────────────────────────────────
def test_layer2_db109_regression():
    """DB-109 原始 malformed frontmatter（delegate-bridge a4446ea 原文）——
    plain scalar 內 `a: b` 須被 pyyaml 擋下，事故訊號逐字在場。"""
    r = run_cli(fixture("db109_original_malformed.md"))
    assert r.returncode == 1
    assert "[yaml]" in r.stdout
    assert "mapping values are not allowed" in r.stdout


def test_layer2_date_string_contract_no_automatic_cast():
    """日期禁自動轉型（文件契約以字串為準）——未引用日期須 PASS；若 timestamp
    constructor 覆寫泄漏（轉成 datetime/date），層④會誤報「須為非空字串」。"""
    r = run_cli(fixture("date_string_contract.md"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


# ── 層③ top-level mapping ────────────────────────────────────────
def test_layer3_non_mapping():
    r = run_cli(fixture("non_mapping.md"))
    assert r.returncode == 1
    assert "[mapping]" in r.stdout
    assert "list" in r.stdout  # 實得型別回報


# ── 層④ 必填欄位契約 ─────────────────────────────────────────────
def test_layer4_missing_fields():
    r = run_cli(fixture("missing_fields.md"))
    assert r.returncode == 1
    for f in (
        "status",
        "assignee",
        "created_date",
        "updated_date",
        "labels",
        "dependencies",
        "ordinal",
    ):
        assert f"缺必填欄位 {f}" in r.stdout
    assert "缺必填欄位 id" not in r.stdout  # 在場欄不誤報
    assert "缺必填欄位 title" not in r.stdout


def test_layer4_wrong_types():
    r = run_cli(fixture("wrong_type.md"))
    assert r.returncode == 1
    assert r.stdout.count("須為清單") == 4  # assignee／labels／dependencies／references
    assert "ordinal 須為整數" in r.stdout
    assert "缺必填欄位" not in r.stdout  # 型別樣本欄位全在場——只有型別違約


# ── 正向對照組 ────────────────────────────────────────────────────
def test_valid_card_passes():
    r = run_cli(fixture("valid_card.md"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS" in r.stdout


# ── CLI 模式契約 ──────────────────────────────────────────────────
def test_cli_multiple_files_mixed_verdicts():
    r = run_cli(fixture("valid_card.md"), fixture("non_mapping.md"))
    assert r.returncode == 1
    assert r.stdout.count("PASS") == 1
    assert r.stdout.count("FAIL") == 1
    assert "1/2 檔違規" in r.stdout


def test_cli_missing_file_is_violation_not_crash():
    r = run_cli(str(FIXTURES / "no_such_file.md"))
    assert r.returncode == 1
    assert "[read]" in r.stdout
    assert "不存在" in r.stdout


def test_cli_no_mode_is_usage_error():
    r = run_cli()
    assert r.returncode == 2  # argparse 用法錯＝環境／用法軸，非驗證 verdict


def test_cli_all_mode(tmp_path):
    """--all 掃腳本所在 repo 的 backlog/tasks/——tmp 同構板驗 exit code 與輸出。"""
    good = (FIXTURES / "valid_card.md").read_text(encoding="utf-8")
    bad = (FIXTURES / "non_mapping.md").read_text(encoding="utf-8")
    root = tmp_path / "board"
    board = root / "backlog" / "tasks"
    board.mkdir(parents=True)
    (board / "a.md").write_text(good, encoding="utf-8")
    (board / "b.md").write_text(bad, encoding="utf-8")
    _copy_script(root)
    r = run_cli("--all", cwd=root, script=root / "scripts" / "card_validate.py")
    assert r.returncode == 1
    assert "PASS backlog/tasks/a.md" in r.stdout
    assert "FAIL backlog/tasks/b.md" in r.stdout
    assert "1/2 檔違規" in r.stdout
    # 全綠板＝exit 0
    root_ok = tmp_path / "board_ok"
    board_ok = root_ok / "backlog" / "tasks"
    board_ok.mkdir(parents=True)
    (board_ok / "a.md").write_text(good, encoding="utf-8")
    _copy_script(root_ok)
    r2 = run_cli("--all", cwd=root_ok, script=root_ok / "scripts" / "card_validate.py")
    assert r2.returncode == 0
    assert "2 檔全過" not in r2.stdout  # 單檔板——彙總計數正確
    assert "1 檔全過" in r2.stdout


def test_cli_staged_mode_hook_path(tmp_path):
    """--staged 讀 staged blob（非 working tree）——pre-commit hook 契約：
    FAIL 列 repo 相對路徑、通過時靜默、修復後重跑收斂。"""
    repo = _seed_repo(tmp_path)
    board = repo / "backlog" / "tasks"
    board.mkdir(parents=True)
    (board / "good.md").write_text(
        (FIXTURES / "valid_card.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (board / "bad.md").write_text(
        (FIXTURES / "db109_original_malformed.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _git(repo, "add", "backlog/")
    r = run_cli("--staged", cwd=repo)
    assert r.returncode == 1
    assert "FAIL backlog/tasks/bad.md" in r.stdout
    assert "mapping values are not allowed" in r.stdout
    assert "good.md" not in r.stdout  # hook 模式通過時靜默
    # 自修迴圈：修復後重跑＝exit 0
    (board / "bad.md").write_text(
        (FIXTURES / "valid_card.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    _git(repo, "add", "backlog/tasks/bad.md")
    r2 = run_cli("--staged", cwd=repo)
    assert r2.returncode == 0
    # 刪卡（D）不驗
    _git(repo, "rm", "-q", "-f", "backlog/tasks/bad.md")
    r3 = run_cli("--staged", cwd=repo)
    assert r3.returncode == 0
