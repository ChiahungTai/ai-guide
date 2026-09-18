"""consolidation_preflight 契約測試（AIR-127——波前三步機械化，synthetic 層）。

釘住的 invariant（卡片已決策勿重辯①）：腳本唯讀 tri-state——
exit 0＝clean 開波；1＝無法判定停波（fail-closed——基礎設施壞時 dirty
清單不可信，優先於 dirty）；2＝dirty 附清單。寫操作（T4-1 處置／流入
快照 commit／開波初始化）不在此層。

包既有檢查（不加新偵測邏輯）：
- 池 delta gate（AIR-93）：import reconcile_memory_pool 的 reconcile_pool
- wave marker（AIR-49 波前①）：`<pool>/_wave-in-progress` 在場＝上波中斷
  未收斂＝停波待處置
- 活躍 writer mtime（memory-audit 波前散文 age 訊號）：dirty 檔任一
  距今 <30 分鐘＝活躍 writer 在場；全部 ≥30 分鐘＝無活躍 writer 訊號
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "consolidation_preflight.py"

GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return done.stdout


def _seed_pool(repo: Path, layout: str) -> Path:
    """建 governed repo 骨架（照真實池形態）：marker protocol==1 + pool
    （entry + 索引 + 內含訊號檔的 .gitignore）＋commit 基線。

    layout="nested"：pool 自帶 .git（ai-guide 現形）；
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
    # 真實池形態：_wave-in-progress 等訊號檔 gitignored——marker 在場不構成
    # pool delta（否則 marker finding 會與 delta finding 混雜）
    (pool / ".gitignore").write_text(
        "_wave-in-progress\n_pending.md\n", encoding="utf-8"
    )
    git_dir = pool if layout == "nested" else repo
    _git(git_dir, "init")
    _git(git_dir, "add", "-A")
    _git(git_dir, "commit", "-m", "baseline")
    return repo


def _put_wave_marker(repo: Path, layout: str) -> str:
    """放 _wave-in-progress marker（內容記 baseline SHA——照 skill 散文程序）。"""
    git_dir = repo / ".agents" / "memory" if layout == "nested" else repo
    sha = _git(git_dir, "rev-parse", "HEAD").strip()
    (repo / ".agents" / "memory" / "_wave-in-progress").write_text(
        f"baseline: {sha}\n", encoding="utf-8"
    )
    return sha


def _dirty_write(repo: Path, name: str = "stray.md", content: str = "繞閘寫入\n") -> Path:
    target = repo / ".agents" / "memory" / name
    target.write_text(content, encoding="utf-8")
    return target


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_json(repo: Path) -> tuple[subprocess.CompletedProcess, dict]:
    done = _run_cli(str(repo), "--json")
    return done, json.loads(done.stdout)


# ---- tri-state 核心：exit 0 = clean 開波 ----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_clean_pool_exits_zero(tmp_path: Path, layout: str) -> None:
    repo = _seed_pool(tmp_path / "repo", layout)
    done, payload = _run_json(repo)
    assert done.returncode == 0
    assert payload["verdict"] == 0
    assert payload["verdict_name"] == "clean"


def test_not_governed_pool_exits_zero(tmp_path: Path) -> None:
    # skill 散文：exit 0（clean/not_governed）→ 開波初始化後起跑——
    # not_governed＝native 寫入本來合法（無執法面），照 reconciler 語義放行
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (pool / "x.md").write_text("x\n", encoding="utf-8")
    _git(pool, "init")
    done, payload = _run_json(repo)
    assert done.returncode == 0
    assert payload["verdict"] == 0
    assert payload["checks"]["pool_delta"]["status"] == "not_governed"


# ---- tri-state 核心：exit 1 = 無法判定停波（fail-closed）----


def test_malformed_governance_marker_exits_one(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory-governance.json").write_text(
        "not-json", encoding="utf-8"
    )
    done, payload = _run_json(repo)
    assert done.returncode == 1
    assert payload["verdict"] == 1
    assert payload["verdict_name"] == "undetermined"


def test_pool_not_under_git_exits_one(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (repo / ".agents" / "memory-governance.json").write_text(
        '{"protocol": 1}\n', encoding="utf-8"
    )
    (pool / "x.md").write_text("x\n", encoding="utf-8")
    done, payload = _run_json(repo)
    assert done.returncode == 1
    assert payload["verdict"] == 1


def test_repo_root_missing_exits_one(tmp_path: Path) -> None:
    # fail-closed：reconciler 對不存在 root 會回 not_governed（=0）——
    # preflight verdict 0 意味開波，拼錯路徑不得換取開波
    done, payload = _run_json(tmp_path / "nonexistent-repo-xyz")
    assert done.returncode == 1
    assert payload["verdict"] == 1


def test_infra_error_wins_over_dirty(tmp_path: Path) -> None:
    # 組合態：pool delta dirty + governance marker malformed——基礎設施壞時
    # dirty 清單不可信，undetermined 蓋過 dirty
    repo = _seed_pool(tmp_path / "repo", "nested")
    _dirty_write(repo)
    (repo / ".agents" / "memory-governance.json").write_text(
        '{"protocol": 0}', encoding="utf-8"
    )
    done, payload = _run_json(repo)
    assert done.returncode == 1
    assert payload["verdict"] == 1


def test_infra_error_wins_over_wave_marker(tmp_path: Path) -> None:
    # 組合態：wave marker 在場 + governance marker malformed → verdict 1，
    # 但 marker 在場事實仍須出現在報告（供人裁對照）
    repo = _seed_pool(tmp_path / "repo", "nested")
    _put_wave_marker(repo, "nested")
    (repo / ".agents" / "memory-governance.json").write_text(
        "not-json", encoding="utf-8"
    )
    done, payload = _run_json(repo)
    assert done.returncode == 1
    assert payload["verdict"] == 1
    assert payload["checks"]["wave_marker"]["present"] is True


# ---- tri-state 核心：exit 2 = dirty 附清單 ----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_dirty_pool_exits_two_with_entries(tmp_path: Path, layout: str) -> None:
    repo = _seed_pool(tmp_path / "repo", layout)
    _dirty_write(repo)
    done, payload = _run_json(repo)
    assert done.returncode == 2
    assert payload["verdict"] == 2
    assert payload["verdict_name"] == "dirty"
    paths = [e["path"] for e in payload["checks"]["pool_delta"]["entries"]]
    assert any("stray.md" in p for p in paths)


def test_wave_marker_present_exits_two(tmp_path: Path) -> None:
    # 波前①：marker 在場＝上波中斷未收斂＝停波；池本身乾淨（marker 已
    # gitignored，不構成 delta）——dirty 來源純為 marker finding
    repo = _seed_pool(tmp_path / "repo", "nested")
    sha = _put_wave_marker(repo, "nested")
    done, payload = _run_json(repo)
    assert done.returncode == 2
    assert payload["verdict"] == 2
    marker = payload["checks"]["wave_marker"]
    assert marker["present"] is True
    assert sha in marker["detail"]  # baseline SHA 入報告（三方對照用）
    assert payload["checks"]["pool_delta"]["status"] == "clean"


def test_wave_marker_plus_dirty_combined_exits_two(tmp_path: Path) -> None:
    # 組合態：marker 在場 + 繞閘 delta——兩 finding 並列於同一報告
    repo = _seed_pool(tmp_path / "repo", "nested")
    _put_wave_marker(repo, "nested")
    _dirty_write(repo)
    done, payload = _run_json(repo)
    assert done.returncode == 2
    assert payload["verdict"] == 2
    assert payload["checks"]["wave_marker"]["present"] is True
    paths = [e["path"] for e in payload["checks"]["pool_delta"]["entries"]]
    assert any("stray.md" in p for p in paths)


# ---- 活躍 writer mtime 訊號（波前散文 age 檢查的機械化）----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_recent_dirty_reported_active_writer(tmp_path: Path, layout: str) -> None:
    # dirty 檔剛寫（<30 分鐘）＝活躍 writer 在場——停波不覆寫
    repo = _seed_pool(tmp_path / "repo", layout)
    _dirty_write(repo)
    done, payload = _run_json(repo)
    assert done.returncode == 2
    active = payload["checks"]["active_writer"]
    assert active["any_active"] is True
    assert active["window_minutes"] == 30
    entry = next(
        e
        for e in payload["checks"]["pool_delta"]["entries"]
        if "stray.md" in e["path"]
    )
    assert entry["age_category"] == "active"
    assert entry["age_minutes"] < 30


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_old_dirty_reported_stale(tmp_path: Path, layout: str) -> None:
    # dirty 檔全部 ≥30 分鐘＝無活躍 writer 訊號——仍 dirty（T4-1 之後才可能
    # 流入快照），但報告分類 stale 讓 skill 端可分支
    repo = _seed_pool(tmp_path / "repo", layout)
    target = _dirty_write(repo)
    old = time.time() - 40 * 60
    os.utime(target, (old, old))
    done, payload = _run_json(repo)
    assert done.returncode == 2
    active = payload["checks"]["active_writer"]
    assert active["any_active"] is False
    entry = next(
        e
        for e in payload["checks"]["pool_delta"]["entries"]
        if "stray.md" in e["path"]
    )
    assert entry["age_category"] == "stale"
    assert entry["age_minutes"] >= 30


def test_deleted_entry_reported_no_file(tmp_path: Path) -> None:
    # deleted delta 無檔可 stat——age 不可得，報告分類 no-file（verdict 不變）
    repo = _seed_pool(tmp_path / "repo", "nested")
    os.remove(repo / ".agents" / "memory" / "entry-a.md")
    done, payload = _run_json(repo)
    assert done.returncode == 2
    entry = next(
        e
        for e in payload["checks"]["pool_delta"]["entries"]
        if "entry-a.md" in e["path"]
    )
    assert entry["age_category"] == "no-file"


# ---- CLI 契約（消費端＝memory-audit 波前，走 exit code＋--json）----


def test_json_shape_and_human_tag(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    clean = _run_cli(str(repo))
    assert clean.returncode == 0
    assert "[OK]" in clean.stdout

    _dirty_write(repo)
    dirty = _run_cli(str(repo), "--json")
    payload = json.loads(dirty.stdout)
    assert set(payload) >= {"verdict", "verdict_name", "repo", "checks"}
    assert set(payload["checks"]) >= {"pool_delta", "wave_marker", "active_writer"}
    assert payload["repo"] == str(repo)

    human = _run_cli(str(repo))
    assert human.returncode == 2
    assert "[FAIL]" in human.stdout  # 停波 verdict 走 fail tag，人可讀


def test_undetermined_human_output(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    (repo / ".agents" / "memory-governance.json").write_text(
        "not-json", encoding="utf-8"
    )
    done = _run_cli(str(repo))
    assert done.returncode == 1
    assert "[FAIL]" in done.stdout


# ---- 唯讀保證：preflight 永不動池（處置權在 consolidation）----


def test_preflight_is_read_only(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo", "nested")
    _put_wave_marker(repo, "nested")
    entry = repo / ".agents" / "memory" / "stray.md"
    entry.write_text("髒寫入\n", encoding="utf-8")
    pool = repo / ".agents" / "memory"
    before_content = entry.read_text(encoding="utf-8")
    before_porcelain = _git(pool, "status", "--porcelain")
    assert _run_cli(str(repo)).returncode == 2
    assert entry.read_text(encoding="utf-8") == before_content
    assert _git(pool, "status", "--porcelain") == before_porcelain
    # marker 不被消費性移除（移除 marker 是波後處置，不是偵測器的事）
    assert (pool / "_wave-in-progress").exists()


# ---- muse review F4：邊角契約補釘 ----


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_dirty_exactly_30_minutes_is_stale(tmp_path: Path, layout: str) -> None:
    # 邊界：恰好 30 分鐘＝stale（<30 才 active）——活躍 writer 窗口閉合釘
    repo = _seed_pool(tmp_path / "repo", layout)
    target = _dirty_write(repo)
    old = time.time() - 30 * 60
    os.utime(target, (old, old))
    done, payload = _run_json(repo)
    assert done.returncode == 2
    assert payload["checks"]["active_writer"]["any_active"] is False
    entry = next(
        e
        for e in payload["checks"]["pool_delta"]["entries"]
        if "stray.md" in e["path"]
    )
    assert entry["age_category"] == "stale"


def test_not_governed_with_marker_still_stops(tmp_path: Path) -> None:
    # 無執法面（not_governed）＋wave marker 在場＝上波中斷未收斂——仍停波（2）
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    (pool / "_wave-in-progress").write_text("baseline: unknown\n", encoding="utf-8")
    done, payload = _run_json(repo)
    assert done.returncode == 2
    assert payload["verdict"] == 2
    assert payload["checks"]["wave_marker"]["present"] is True


def test_pending_md_exempt_passthrough(tmp_path: Path) -> None:
    # _pending.md＝reconciler 唯一豁免檔——preflight 繼承豁免（契約釘）：
    # staged 的 _pending.md 不構成 dirty（否則 reconciler 豁免被靜默破壞可測）
    repo = _seed_pool(tmp_path / "repo", "nested")
    _dirty_write(repo, name="_pending.md", content="in-flight\n")
    _git(repo / ".agents" / "memory", "add", "-f", "_pending.md")
    done, payload = _run_json(repo)
    assert done.returncode == 0
    assert payload["verdict"] == 0


def test_deleted_only_delta_counts_active(tmp_path: Path) -> None:
    # codex finding：deleted delta 無 mtime＝age 未知——保守計入活躍 writer
    # （近期刪除不得被折成「全部 ≥30 分鐘」而收編成合法流入快照）
    repo = _seed_pool(tmp_path / "repo", "nested")
    victim = repo / ".agents" / "memory" / "entry-a.md"
    victim.unlink()
    done, payload = _run_json(repo)
    assert done.returncode == 2
    active = payload["checks"]["active_writer"]
    assert active["any_active"] is True
    entry = next(
        e
        for e in payload["checks"]["pool_delta"]["entries"]
        if e["path"].endswith("entry-a.md")
    )
    assert entry["age_category"] == "no-file"
