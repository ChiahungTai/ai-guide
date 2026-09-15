"""reconcile_memory_pool 契約測試（AIR-93——池 state 對帳網，synthetic 層）。

釘住的 invariant：池的任何變動必須能證明來自 approved consolidation。
合法流程下池 HEAD＝已審核基線；繞閘寫入（muse teardown／shell 直寫／未來
新 writer）只會出現在 working tree delta——porcelain 非空即 flag。

對帳網是唯讀偵測器：永不自動回復 canonical（CAS/consolidation 互斥語義
不在此層），處置權在 consolidation 補審。

Marker 語義與 governance hook 同源：absent → not_governed（native 寫入
本來合法，無可執法面）；malformed → fail loud（declared state 不得 fail
open）。exit 契約：0＝clean/not_governed、1＝infra/contract 錯（fail
loud）、2＝dirty（flag）。

Fixture 覆蓋兩種真實 layout：pool 為 nested 獨立 git repo（ai-guide/mosaic
現形）與 pool 在 outer repo git 內。
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/reconcile_memory_pool.py")
reconcile_pool, ReconcileError, PoolDelta = (
    _mod.reconcile_pool,
    _mod.ReconcileError,
    _mod.PoolDelta,
)
SCRIPT = REPO_ROOT / "scripts" / "reconcile_memory_pool.py"

GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args], check=True, capture_output=True
    )


def _seed_pool(repo: Path, layout: str) -> Path:
    """建 governed repo 骨架：marker protocol==1 + pool（entry + 索引）＋commit 基線。

    layout="nested"：pool 自帶 .git（ai-guide/mosaic 現形）；
    layout="flat"：outer repo 是 git、pool 在其內。
    """
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (repo / ".agents" / "memory-governance.json").write_text(
        '{"protocol": 1}\n', encoding="utf-8"
    )
    (pool / "MEMORY.md").write_text("# index\n- [[entry-a]]\n", encoding="utf-8")
    (pool / "entry-a.md").write_text(
        "---\nname: entry-a\n---\nbody\n", encoding="utf-8"
    )
    git_dir = pool if layout == "nested" else repo
    _git(git_dir, "init")
    _git(git_dir, "add", "-A")
    _git(git_dir, "commit", "-m", "baseline")
    return repo


# ---- 核心判準：delta 即 flag ----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_clean_pool_exits_zero(tmp_path: Path, layout: str) -> None:
    r = reconcile_pool(_seed_pool(tmp_path / "repo", layout))
    assert r.status == "clean"
    assert r.entries == []


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_modified_entry_flagged(tmp_path: Path, layout: str) -> None:
    repo = _seed_pool(tmp_path / "repo", layout)
    (repo / ".agents" / "memory" / "entry-a.md").write_text(
        "繞閘髒寫入\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    paths = " ".join(e.path for e in r.entries)
    assert "entry-a.md" in paths


def test_untracked_new_file_flagged(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        "teardown 學習\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert any("muse-dropped.md" in e.path for e in r.entries)


def test_deleted_entry_flagged(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    os.remove(repo / ".agents" / "memory" / "entry-a.md")
    assert reconcile_pool(repo).status == "dirty"


def test_index_modification_flagged(tmp_path: Path) -> None:
    # R3：索引（MEMORY.md/_inventory.md）被改寫＝影響後續所有 recall 的污染面，不得漏
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory" / "MEMORY.md").write_text(
        "# index\n- [[evil]]\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert any("MEMORY.md" in e.path for e in r.entries)


def test_gitignored_file_not_flagged(tmp_path: Path) -> None:
    # 忽略規則跟 git 走（consolidation commit 同規則）——ignored scratch 非 delta
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory" / ".gitignore").exists() or (
        (repo / ".agents" / "memory" / ".gitignore").write_text(
            "*.tmp\n", encoding="utf-8"
        )
    )
    git_root = repo / ".agents" / "memory"
    _git(git_root, "add", "-A")
    _git(git_dir := git_root, "commit", "-m", "gitignore")
    (git_dir / "scratch.tmp").write_text("ignored\n", encoding="utf-8")
    assert reconcile_pool(repo).status == "clean"


def test_dirty_outside_pool_scope_not_flagged(tmp_path: Path) -> None:
    # 執法面＝.agents/memory；inbox 等池外髒狀態不歸對帳網管
    repo = _seed_pool(tmp_path / "repo", "flat")
    inbox = repo / ".agents" / "memory-inbox"
    inbox.mkdir()
    (inbox / "stray.json").write_text("{}\n", encoding="utf-8")
    assert reconcile_pool(repo).status == "clean"


# ---- marker 三態（與 governance hook 同源語義）----


def test_marker_absent_not_governed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (pool / "x.md").write_text("x\n", encoding="utf-8")
    _git(pool, "init")
    r = reconcile_pool(repo)
    assert r.status == "not_governed"


@pytest.mark.parametrize(
    "raw",
    [
        '{"protocol": 0}',
        '{"protocol": "1"}',
        '{"protocol": true}',
        '{"protocol": 1.5}',
        "{}",
        "not-json",
    ],
)
def test_malformed_marker_fails_loud(tmp_path: Path, raw: str) -> None:
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (repo / ".agents" / "memory-governance.json").write_text(raw, encoding="utf-8")
    with pytest.raises(ReconcileError):
        reconcile_pool(repo)


# ---- fail-closed：無法建立基線＝loud，禁靜默當 clean ----


def test_pool_not_under_git_fails_loud(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (repo / ".agents" / "memory-governance.json").write_text(
        '{"protocol": 1}\n', encoding="utf-8"
    )
    (pool / "x.md").write_text("x\n", encoding="utf-8")
    with pytest.raises(ReconcileError):
        reconcile_pool(repo)


def test_git_binary_missing_fails_loud(tmp_path: Path, monkeypatch) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    monkeypatch.setenv("PATH", str(fake_bin))
    with pytest.raises(ReconcileError):
        reconcile_pool(repo)


# ---- 唯讀保證：偵測器永不動池（CAS/consolidation 互斥語義不在此層）----


def test_reconciler_is_read_only(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    entry = repo / ".agents" / "memory" / "entry-a.md"
    entry.write_text("髒寫入\n", encoding="utf-8")
    before = entry.read_text(encoding="utf-8")
    git_root = repo / ".agents" / "memory"
    status_before = subprocess.run(
        ["git", "-C", str(git_root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert entry.read_text(encoding="utf-8") == before
    status_after = subprocess.run(
        ["git", "-C", str(git_root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert status_after == status_before


# ---- CLI 契約（消費端＝consolidation 開頭／memory-audit，走 exit code）----


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_exit_codes(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    assert _run_cli(str(repo)).returncode == 0
    (repo / ".agents" / "memory" / "dirty.md").write_text("x\n", encoding="utf-8")
    done = _run_cli(str(repo))
    assert done.returncode == 2
    assert "[FAIL]" in done.stdout  # flag 走 fail tag，人可讀


def test_cli_json_shape(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory" / "new.md").write_text("x\n", encoding="utf-8")
    done = _run_cli(str(repo), "--json")
    payload = json.loads(done.stdout)
    assert payload["status"] == "dirty"
    assert payload["repo"] == str(repo)
    assert any("new.md" in e["path"] for e in payload["entries"])


# ---- F6 六釘（codex review＋5.3 judge 裁決的回歸 pins）----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_config_hidden_untracked_still_flagged(tmp_path: Path, layout: str) -> None:
    # 釘 F1：status.showUntrackedFiles=no config 不得讓 teardown 新增檔隱形
    repo = _seed_pool(tmp_path / "repo", layout)
    git_dir = repo / ".agents" / "memory" if layout == "nested" else repo
    _git(git_dir, "config", "status.showUntrackedFiles", "no")
    (repo / ".agents" / "memory" / "teardown.md").write_text("髒\n", encoding="utf-8")
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert any("teardown.md" in e.path for e in r.entries)


def test_broken_symlink_marker_fails_loud(tmp_path: Path) -> None:
    # 釘 F2：broken symlink marker＝declared-but-broken（hook -e/-L 同源語義），
    # 不得誤判 not_governed 放行
    repo = _seed_pool(tmp_path / "repo", "nested")
    marker = repo / ".agents" / "memory-governance.json"
    marker.unlink()
    marker.symlink_to("/nonexistent-target-xyz")
    with pytest.raises(ReconcileError):
        reconcile_pool(repo)
    assert _run_cli(str(repo)).returncode == 1


@pytest.mark.parametrize("raw", ['{"protocol": 1.0}', '{"protocol": 1e0}'])
def test_protocol_numeric_equality_accepted(tmp_path: Path, raw: str) -> None:
    # 釘 F3：JSON number semantic equality（與 hook jq 同源）——1.0/1e0 是合法
    # protocol 1；bool/字串/其他數值仍拒絕（見 malformed parametrize，1.5 保留）
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (repo / ".agents" / "memory-governance.json").write_text(raw, encoding="utf-8")
    (pool / "entry-a.md").write_text("x\n", encoding="utf-8")
    _git(pool, "init")
    _git(pool, "add", "-A")
    _git(pool, "commit", "-m", "baseline")
    assert reconcile_pool(repo).status == "clean"


def test_parse_porcelain_worktree_rename_pairing() -> None:
    # 釘 F4：Y 欄 R/C 也有來源 token 配對——XY 兩欄皆查，" R" 的來源不會被
    # 當下一筆 record；CJK＋空格路徑同批 pin（codex 驗證式原文形態）
    raw = " R 新 檔.md\0C來源.md\0?? 後續.md\0"
    entries = _mod._parse_porcelain(raw)
    assert [(e.code, e.path) for e in entries] == [
        (" R", "新 檔.md"),
        ("??", "後續.md"),
    ]


def test_parse_porcelain_malformed_token_fails_loud() -> None:
    with pytest.raises(ReconcileError):
        _mod._parse_porcelain("??\0next.md\0")


def test_staged_rename_roundtrip_flagged(tmp_path: Path) -> None:
    # 真實 git 路徑的 rename pairing：staged rename 顯示 R<space>，entries 不錯位
    repo = _seed_pool(tmp_path / "repo", "nested")
    pool = repo / ".agents" / "memory"
    (pool / "entry-a.md").rename(pool / "entry-b.md")
    _git(pool, "add", "-A")
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert any("entry-b.md" in e.path for e in r.entries)


def test_flat_pool_directory_deleted_flagged(tmp_path: Path) -> None:
    # 釘 F7：flat layout 下 pool 目錄整刪是最大級 mutation——outer git 的
    # D delta 必須接住，禁早退 clean
    repo = _seed_pool(tmp_path / "repo", "flat")
    import shutil

    shutil.rmtree(repo / ".agents" / "memory")
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert all(e.code.strip().startswith("D") or "D" in e.code for e in r.entries)


def test_nested_pool_directory_deleted_fails_loud(tmp_path: Path) -> None:
    # F7 裁決的殘留極限釘：nested 刪光（.git 同滅）且 outer 無 git＝無基準
    # → fail loud，不得報 clean（「無法證明乾淨≠乾淨」）
    repo = tmp_path / "repo"
    _seed_pool(repo, "nested")
    import shutil

    shutil.rmtree(repo / ".agents" / "memory")
    with pytest.raises(ReconcileError):
        reconcile_pool(repo)


# ---- AIR-63 S3：_pending.md 豁免（pending 生成器合法自產物，T4-1 訊號③）----


def test_pending_view_self_produced_not_flagged(tmp_path: Path) -> None:
    # _pending.md refresh（手動／夜波 Phase0）是合法自產——porcelain 不得告警
    repo = _seed_pool(tmp_path / "repo", "nested")
    pool = repo / ".agents" / "memory"
    (pool / "_pending.md").write_text("pending view\n", encoding="utf-8")
    assert reconcile_pool(repo).status == "clean"


def test_pending_view_exempt_but_sibling_dirty_still_flagged(tmp_path: Path) -> None:
    # 豁免只涵蓋 _pending.md 本身——同批其他繞閘 delta 照樣 flag（豁免非整池放行）
    repo = _seed_pool(tmp_path / "repo", "nested")
    pool = repo / ".agents" / "memory"
    (pool / "_pending.md").write_text("pending view\n", encoding="utf-8")
    (pool / "stray.md").write_text("x\n", encoding="utf-8")
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert any("stray.md" in e.path for e in r.entries)
    assert not any("_pending.md" in e.path for e in r.entries)
