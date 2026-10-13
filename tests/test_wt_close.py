"""wt-close.sh TRUNK_ADVANCED 條件分支契約測試（AIR-166 F2 起底——AIR-329 升級三態快檢）。

釘住的 invariant（scripts/wt-close.sh：merge 前 merge-base --is-ancestor 捕捉、
收線尾 CR freshness 三態快檢 receipt result 欄）：

- full 收斂且 trunk 實際前進（merge 前 card branch 未含於 trunk）時：
  - MERGE_WT≠primary（merge 落於暫時/trunk WT）→ stderr skip note，receipt
    pass;graph-warmup-skipped，不跑 freshness（identity 錯配防護）。
  - MERGE_WT==primary → code-reality freshness --repo <primary> --json：
    fresh=false → receipt pass;graph-stale=confirmed＋stderr 附確切重建命令；
    fresh=true → pass;graph-fresh；binary 缺席／exit 2／解析失敗 →
    pass;freshness-unavailable（fail-open——不改 exit code、不擋收線、
    腳本不自動 build）。
- 零 commit close（card branch == trunk tip，trunk 未被推動）→ receipt 純
  pass，不進快檢。

Fixture：tmp git repo＋手工 identity contract（模擬 wt-open 產物，手法同
test_wt_sweep.py）。full 模式會真的 ff merge 進 main（primary worktree 清潔
由 seed 保證）；close 成功後卡 WT 與 branch 皆應移除。code-reality 行為以
stubbin 目錄 PATH 前插 stub 控制（shell 腳本印指定 JSON 後回指定 exit code）；
缺席面用受限 PATH（/usr/bin:/bin——實體 code-reality 住 ~/.cargo/bin 不在內）。
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from conftest import REPO_ROOT

CLOSE_SCRIPT = REPO_ROOT / "scripts" / "wt-close.sh"
GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]
ISOLATED_PATH = "/usr/bin:/bin"  # code-reality 缺席面（macOS 系統目錄，無 ~/.cargo/bin）


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def _seed_repo(base: Path) -> Path:
    """tmp 消費端 repo：main 基線＋.agent-tmp ignore（identity contract 不構成 dirty）。"""
    repo = base / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".agent-tmp/\n")
    (repo / "f.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _open_card_wt(repo: Path, card: str = "air-1") -> Path:
    """模擬 wt-open：worktree add＋手工 identity contract（owning 線＝main）。"""
    wt = repo.parent / f"repo-{card}"
    _git(repo, "worktree", "add", "-b", card, str(wt))
    ident_dir = wt / ".agent-tmp"
    ident_dir.mkdir()
    (ident_dir / "wt-identity.json").write_text(
        json.dumps(
            {
                "v": 1,
                "mode": "card",
                "task": card,
                "owning_line": "main",
                "base_ref": "main",
                "base_hash": _git(repo, "rev-parse", "main"),
                "branch": card,
                "wt_path": str(wt),
                "opened_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return wt


def _stub_code_reality(base: Path, body: str) -> Path:
    """stubbin 目錄放一支 code-reality stub（body＝shell 腳本片段），回傳其目錄供 PATH 前插。"""
    stub_bin = base / "stubbin"
    stub_bin.mkdir(exist_ok=True)
    stub = stub_bin / "code-reality"
    stub.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    stub.chmod(0o755)
    return stub_bin


def _close(wt: Path, *, path: str | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if path is not None:
        env["PATH"] = path
    return subprocess.run(
        ["bash", str(CLOSE_SCRIPT), "--wt", str(wt)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _last_full_result(repo: Path) -> str:
    """receipt log（.git/wt-close.log，格式 timestamp|mode|wt|branch|result）最後一筆 full 行的 result 欄。"""
    lines = [
        ln
        for ln in (repo / ".git" / "wt-close.log")
        .read_text(encoding="utf-8")
        .splitlines()
        if "|full|" in ln
    ]
    assert lines, "預期至少一筆 full receipt"
    return lines[-1].split("|")[4]


def _card_wt_with_work(repo: Path) -> tuple[Path, str]:
    """開卡 WT＋一顆卡 commit（trunk 將實際前進）；回傳（wt, commit hash）。"""
    wt = _open_card_wt(repo)
    (wt / "w.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(air-1) work")
    return wt, _git(wt, "rev-parse", "HEAD")


def test_trunk_advanced_stale_confirmed_receipt_rebuild_command(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt, tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": false}'; exit 1\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "confirmed-stale" in done.stderr  # stderr warn 面
    assert "code-reality build --repo" in done.stderr  # 確切重建命令附上
    assert _last_full_result(repo) == "pass;graph-stale=confirmed"  # receipt 面
    assert tip in _git(repo, "rev-list", "main")  # trunk 實際前進（吸收 card commit）
    assert not wt.exists()  # 正常收線：WT 已移除
    assert _git(repo, "branch", "--list", "air-1") == ""  # branch 已刪（-d 非 -D）


def test_trunk_advanced_fresh_receipt_graph_fresh(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "graph fresh" in done.stderr
    assert _last_full_result(repo) == "pass;graph-fresh"
    assert not wt.exists()


def test_merge_wt_not_primary_skips_warmup(tmp_path: Path) -> None:
    """main 由第二個 WT 持有（wave 形態）→ MERGE_WT≠primary，skip 不跑 freshness。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    _git(repo, "checkout", "-b", "side")  # primary 讓出 main
    trunk_wt = repo.parent / "repo-trunk"
    _git(repo, "worktree", "add", str(trunk_wt), "main")
    stub = _stub_code_reality(tmp_path, 'echo "SHOULD-NOT-BE-CALLED"; exit 3\n')

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "graph warm-up skip" in done.stderr
    assert "SHOULD-NOT-BE-CALLED" not in done.stderr  # 身份防護先行——stub 未被呼叫
    assert _last_full_result(repo) == "pass;graph-warmup-skipped"
    assert not wt.exists()


def test_freshness_exit2_fail_open_receipt_unavailable(tmp_path: Path) -> None:
    """freshness exit 2（no-slot/unavailable）→ fail-open：不擋收線、exit 0 不變。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"error\": \"no-slot\"}'; exit 2\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "freshness 快檢不可用" in done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_code_reality_absent_fail_open_receipt_unavailable(tmp_path: Path) -> None:
    """binary 缺席（受限 PATH 排除 ~/.cargo/bin）→ fail-open：不擋收線、exit 0 不變。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)

    done = _close(wt, path=ISOLATED_PATH)

    assert done.returncode == 0, done.stderr
    assert "code-reality 缺席" in done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_zero_commit_close_receipt_plain_pass(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    main_tip = _git(repo, "rev-parse", "main")
    wt = _open_card_wt(repo)  # 零 commit：branch == trunk tip

    done = _close(wt)

    assert done.returncode == 0, done.stderr
    assert "CR freshness" not in done.stderr
    assert _last_full_result(repo) == "pass"  # 純 pass，不進快檢
    assert _git(repo, "rev-parse", "main") == main_tip  # trunk 未被推動
    assert not wt.exists()
