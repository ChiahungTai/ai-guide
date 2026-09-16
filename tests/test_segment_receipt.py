"""segment_receipt 契約測試（AIR-60 段③＝AIR-62 併入——synthetic 層）。

釘住的 invariant（archived AIR-62 已決策勿重辯）：
- 欄位分級——git 可推導欄全部機械生成（零 LLM 手寫），判斷欄不住 receipt。
- freshness 鏈式版本（parent receipt identity）——resume 判「世界是否已分叉」。
- receipt 是 transcript cache 的 validity token，不是第二真相源——完成度真相
  仍是 Git＋EP re-derive。

exit 契約（對齊 reconcile_memory_pool 慣例）：verify 0＝FRESH、1＝DRIFTED、
2＝contract/infra 錯。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import load_module

_mod = load_module("scripts/segment_receipt.py")

GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", *GIT_C, *args], cwd=repo, capture_output=True, text=True, check=False
    )
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "app.py").write_text("x = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "init")
    return repo


def _write_ep(repo: Path, baseline: str) -> Path:
    """寫入 EP 並 commit（真實弧中 EP 是已入庫檔；baseline 指向更早的 commit）。"""
    ep = repo / "ep.md"
    ep.write_text(f"# EP\n\n> **baseline**: {baseline}\n")
    _git(repo, "add", "ep.md")
    _git(repo, "commit", "-qm", "ep")
    return ep


def test_generate_mechanical_columns_and_verify_fresh(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    (git_repo / "app.py").write_text("x = 2\n")  # uncommitted tracked change

    out = git_repo / ".agent-tmp" / "segment-receipts"
    path = _mod.generate_receipt(
        repo=git_repo, segment="S1", ep=ep, out_dir=out
    )
    text = path.read_text()
    data = json.loads(text.split("```json")[1].split("```")[0])

    assert data["schema"] == "segment-receipt/1"
    assert data["segment"] == "S1"
    assert data["baseline_head"] == baseline
    assert data["head"] != baseline  # EP commit 使 HEAD 前進、baseline 不變
    assert data["tracked_diff_hash"] not in ("", "clean")  # 有 uncommitted diff
    assert data["untracked"]["count"] == 0
    assert data["parent"] is None
    assert data["pytest"] is None  # 未要求即不承載——不假造測試欄

    fresh, keys = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is True
    assert keys == []


def test_verify_drift_on_tracked_and_untracked_change(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    (git_repo / "app.py").write_text("x = 2\n")
    path = _mod.generate_receipt(
        repo=git_repo, segment="S2", ep=ep,
        out_dir=git_repo / ".agent-tmp" / "segment-receipts",
    )

    (git_repo / "app.py").write_text("x = 3\n")  # tracked drift
    fresh, keys = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is False
    assert "tracked_diff_hash" in keys

    (git_repo / "extra.txt").write_text("new\n")  # untracked 出現也算內容變更
    fresh, keys = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is False
    assert "untracked" in keys


def test_verify_drift_on_ep_baseline_tamper(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    path = _mod.generate_receipt(
        repo=git_repo, segment="S6", ep=ep,
        out_dir=git_repo / ".agent-tmp" / "segment-receipts",
    )
    fresh, _ = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is True

    ep.write_text(f"# EP\n\n> **baseline**: {'0' * 40}\n")  # EP baseline 竄改
    fresh, keys = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is False
    assert "baseline_head" in keys


def test_parent_chain_and_tamper_detection(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    out = git_repo / ".agent-tmp" / "segment-receipts"

    a = _mod.generate_receipt(repo=git_repo, segment="S1", ep=ep, out_dir=out)
    (git_repo / "app.py").write_text("x = 2\n")
    b = _mod.generate_receipt(
        repo=git_repo, segment="S2", ep=ep, parent=a, out_dir=out
    )
    bdata = json.loads(b.read_text().split("```json")[1].split("```")[0])
    adata = json.loads(a.read_text().split("```json")[1].split("```")[0])
    assert bdata["parent"]["identity_digest"] == adata["identity_digest"]

    fresh, keys = _mod.verify_receipt(receipt=b, repo=git_repo)
    assert fresh is True  # B 對當前 tree fresh、parent 未被換

    # parent receipt 被換/漂移 → 鏈上孩子驗證失敗
    adata["identity_digest"] = "0" * 64
    a.write_text(a.read_text().split("```json")[0] + "```json\n"
                 + json.dumps(adata, ensure_ascii=False, indent=2) + "\n```\n")
    fresh, keys = _mod.verify_receipt(receipt=b, repo=git_repo)
    assert fresh is False
    assert any("parent" in k for k in keys)


def test_pytest_capture_column(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    tests = git_repo / "test_ok.py"
    tests.write_text("def test_ok():\n    assert True\n")

    path = _mod.generate_receipt(
        repo=git_repo, segment="S3", ep=ep,
        pytest_cmd=f"{sys.executable} -m pytest",
        pytest_args=["-q", str(tests)],
        out_dir=git_repo / ".agent-tmp" / "segment-receipts",
    )
    data = json.loads(path.read_text().split("```json")[1].split("```")[0])
    assert data["pytest"] is not None
    assert data["pytest"]["exit"] == 0
    assert "passed" in data["pytest"]["summary"]


def test_verify_missing_ep_and_missing_receipt(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    path = _mod.generate_receipt(
        repo=git_repo, segment="S4", ep=ep,
        out_dir=git_repo / ".agent-tmp" / "segment-receipts",
    )
    ep.unlink()  # EP 失聯——baseline 比對鍵不可達＝drift（fail-closed）
    fresh, keys = _mod.verify_receipt(receipt=path, repo=git_repo)
    assert fresh is False
    assert any("ep" in k for k in keys)

    with pytest.raises(_mod.ReceiptError):
        _mod.verify_receipt(receipt=git_repo / "nope.md", repo=git_repo)


def test_cli_exit_contract(git_repo: Path) -> None:
    baseline = _git(git_repo, "rev-parse", "HEAD")
    ep = _write_ep(git_repo, baseline)
    out = git_repo / ".agent-tmp" / "segment-receipts"
    path = _mod.generate_receipt(repo=git_repo, segment="S5", ep=ep, out_dir=out)

    assert _mod.main(["--verify", str(path), "--repo", str(git_repo)]) == 0
    (git_repo / "app.py").write_text("x = 9\n")
    assert _mod.main(["--verify", str(path), "--repo", str(git_repo)]) == 1
    assert _mod.main(["--verify", str(git_repo / "nope.md"),
                      "--repo", str(git_repo)]) == 2
