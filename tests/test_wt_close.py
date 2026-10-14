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
    wt = repo.parent / f"repo-{card.replace('/', '-')}"  # slash branch→目錄名攤平
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


def _argv_marker_body(marker: Path, tail: str) -> str:
    """F2/F3 共用 marker 型 stub 機制：stub 先寫 argv 進 marker 檔（檔案副作用不被
    command substitution 吞掉），再跑 tail（echo JSON／exit code）。"""
    return "printf '%s\\n' \"$@\" > \"" + str(marker) + "\"\n" + tail


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
    marker = tmp_path / "cr-invocation.txt"
    stub = _stub_code_reality(
        tmp_path,
        _argv_marker_body(marker, 'echo "SHOULD-NOT-BE-CALLED"; exit 3\n'),
    )

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "graph warm-up skip" in done.stderr
    assert "SHOULD-NOT-BE-CALLED" not in done.stderr  # 身份防護先行——stub 未被呼叫
    assert not marker.exists()  # 獨立證明：外部命令未被呼叫（檔案副作用不被 command substitution 捕捉）
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


def test_freshness_exit2_with_fresh_true_json_receipt_unavailable(tmp_path: Path) -> None:
    """F1 回歸：exit 2＋stdout {"fresh": true}——rc-JSON 不一致不得報 graph-fresh
    （合法 fresh verdict 只配 exit 0；判定 RC 帶入，JSON 不單獨成立）。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 2\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "freshness 快檢不可用" in done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_freshness_exit2_with_fresh_false_json_receipt_unavailable(tmp_path: Path) -> None:
    """F1 回歸：exit 2＋stdout {"fresh": false}——exit 2＝unavailable，不得報
    graph-stale=confirmed（合法 stale verdict 只配 exit 1，照 freshness face 契約）。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": false}'; exit 2\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "freshness 快檢不可用" in done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_freshness_exit0_with_fresh_false_receipt_unavailable(tmp_path: Path) -> None:
    """F1 回歸：rc-JSON 不一致（exit 0＋fresh=false）→ unavailable。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": false}'; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_freshness_exit1_with_fresh_true_receipt_unavailable(tmp_path: Path) -> None:
    """F1 回歸：rc-JSON 不一致（exit 1＋fresh=true）→ unavailable。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 1\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_freshness_non_json_output_receipt_unavailable(tmp_path: Path) -> None:
    """F2：stdout not-json（exit 0）＝解析失敗 → fail-open unavailable，收線 exit 0 不變。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stub = _stub_code_reality(tmp_path, "echo not-json; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "freshness 快檢不可用" in done.stderr
    assert _last_full_result(repo) == "pass;freshness-unavailable"
    assert not wt.exists()


def test_freshness_invocation_form_freshness_repo_json(tmp_path: Path) -> None:
    """F2：freshness 呼叫形態——stub argv 記錄進 marker 檔，斷言含 freshness／--repo／
    primary 實路徑／--json。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    marker = tmp_path / "cr-freshness-argv.txt"
    stub = _stub_code_reality(
        tmp_path,
        _argv_marker_body(marker, "echo '{\"fresh\": true}'; exit 0\n"),
    )

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert marker.exists(), "stub 應被呼叫（MERGE_WT==primary）——marker 檔未落"
    argv = marker.read_text(encoding="utf-8").splitlines()
    assert "freshness" in argv
    assert "--repo" in argv
    assert str(repo) in argv  # primary 實路徑
    assert "--json" in argv


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


# ---------- receipt freshness gate 路徑根契約（root＝arc session 的 owning WT）────
# 寫入端契約：skills/post-build/SKILL.md「寫 .agent-tmp/post-build-receipts/…」與
# 消費端 hooks/post-build-gate.py（repo=cwd=owning WT）都以 owning WT 為根；
# slash branch 檔名編碼 `/`→`__` 單一源＝post-build-gate._branch_key。wt-close 的
# 讀取端必須同根同編碼，否則 card WT 形態下 gate 靜默失效。


def _write_receipt(wt: Path, branch: str, head_sha: str) -> Path:
    """owning WT 根寫 post-build receipt（寫入端契約形；slash branch 走編碼檔名）。"""
    receipt_dir = wt / ".agent-tmp" / "post-build-receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    p = receipt_dir / f"{branch.replace('/', '__')}.json"
    p.write_text(
        json.dumps({"head_sha": head_sha, "completed_at": "2026-10-14T00:00:00+00:00"}),
        encoding="utf-8",
    )
    return p


def _all_full_results(repo: Path) -> list[str]:
    """receipt log 全部 full 行的 result 欄（單次 close 可有多筆 full receipt）。"""
    return [
        ln.split("|")[4]
        for ln in (repo / ".git" / "wt-close.log")
        .read_text(encoding="utf-8")
        .splitlines()
        if "|full|" in ln
    ]


def test_receipt_fresh_at_wt_root_passes(tmp_path: Path) -> None:
    """(a) receipt 寫在 owning WT 根且 head_sha==branch HEAD → 放行（receipt-fresh）。"""
    repo = _seed_repo(tmp_path)
    wt, tip = _card_wt_with_work(repo)
    _write_receipt(wt, "air-1", tip)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "receipt stale" not in done.stderr
    assert any(
        r.startswith("receipt-fresh(sha=") for r in _all_full_results(repo)
    ), _all_full_results(repo)
    assert not wt.exists()  # 正常收線


def test_receipt_stale_at_wt_root_dies(tmp_path: Path) -> None:
    """(b) 同位置但 head_sha≠branch HEAD → die（receipt stale，rebase 後未重驗）。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    stale_sha = "0" * 40
    _write_receipt(wt, "air-1", stale_sha)

    done = _close(wt)

    assert done.returncode == 3, done.stderr  # die＝exit 3
    assert "receipt stale" in done.stderr
    assert stale_sha in done.stderr
    assert wt.exists()  # die 保現場——WT 未被移除


def test_receipt_only_at_primary_root_not_misjudged_stale(tmp_path: Path) -> None:
    """(c) 只有 PRIMARY 根殘留 stale receipt、owning WT 根沒有 → 不得誤判 stale
    （讀取端根錯誤會把「WT 根無 receipt」讀成 PRIMARY 的 stale → 假擋收線）。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    primary_receipts = repo / ".agent-tmp" / "post-build-receipts"
    primary_receipts.mkdir(parents=True)  # .agent-tmp/ 已 gitignored（_seed_repo）
    (primary_receipts / "air-1.json").write_text(
        json.dumps({"head_sha": "0" * 40}), encoding="utf-8"
    )
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "receipt stale" not in done.stderr
    assert "receipt 缺席" in done.stderr  # 正確讀 owning WT 根 → 缺席 warn（不擋）
    assert any(r == "receipt-absent" for r in _all_full_results(repo))
    assert not wt.exists()


def test_receipt_empty_json_object_dies(tmp_path: Path) -> None:
    """(e) receipt 存在但 JSON={}（缺 head_sha）→ die（fail-closed）——空 sha 跳過
    stale 判斷＝gate 有洞（A-01：損壞比缺失危險，對齊 post-build-gate missing 語義）。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    receipt_dir = wt / ".agent-tmp" / "post-build-receipts"
    receipt_dir.mkdir(parents=True)
    receipt_file = receipt_dir / "air-1.json"
    receipt_file.write_text("{}", encoding="utf-8")

    done = _close(wt)

    assert done.returncode == 3, done.stderr  # die＝exit 3
    assert "receipt 解析失敗或缺 head_sha" in done.stderr
    assert str(receipt_file) in done.stderr  # 訊息含 receipt 路徑
    assert wt.exists()  # die 保現場——WT 未被移除


def test_receipt_bad_json_dies(tmp_path: Path) -> None:
    """(f) receipt 存在但非 JSON 文本（解析失敗）→ die（fail-closed），不得靜默照收。"""
    repo = _seed_repo(tmp_path)
    wt, _tip = _card_wt_with_work(repo)
    receipt_dir = wt / ".agent-tmp" / "post-build-receipts"
    receipt_dir.mkdir(parents=True)
    receipt_file = receipt_dir / "air-1.json"
    receipt_file.write_text("not-json{{", encoding="utf-8")

    done = _close(wt)

    assert done.returncode == 3, done.stderr  # die＝exit 3
    assert "receipt 解析失敗或缺 head_sha" in done.stderr
    assert str(receipt_file) in done.stderr  # 訊息含 receipt 路徑
    assert wt.exists()  # die 保現場——WT 未被移除


def test_receipt_slash_branch_encoded_key_at_wt_root(tmp_path: Path) -> None:
    """(d) slash branch：receipt 落 owning WT 根編碼檔名（/→__，對齊
    post-build-gate._branch_key）→ receipt-fresh（讀取端須同編碼才讀得到）。"""
    repo = _seed_repo(tmp_path)
    card = "feat/sub"
    wt = _open_card_wt(repo, card)
    (wt / "w.txt").write_text("y\n", encoding="utf-8")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "(feat/sub) work")
    tip = _git(wt, "rev-parse", "HEAD")
    _write_receipt(wt, card, tip)
    stub = _stub_code_reality(tmp_path, "echo '{\"fresh\": true}'; exit 0\n")

    done = _close(wt, path=f"{stub}:{os.environ['PATH']}")

    assert done.returncode == 0, done.stderr
    assert "receipt stale" not in done.stderr
    assert any(
        r.startswith("receipt-fresh(sha=") for r in _all_full_results(repo)
    ), _all_full_results(repo)
    assert not wt.exists()
