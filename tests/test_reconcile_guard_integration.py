"""reconcile × memory_guard_rules 掛點整合測試（AIR-187 S3）。

釘住的 invariant：
- exit 契約零漂移（硬閘）：0＝clean/not_governed、1＝fail loud、2＝dirty——
  guard 分流標籤只是 exit-2 quarantine 明細的附加面，分類結果不得反饋
  exit 判定，clean/fail-loud 路徑不得出現標籤。
- 分流三級與來源分層（S1 語義在 reconcile 掛點的落地）：同一 black 內容
  ——untracked／未審核來源（AIR-93 teardown 面）＝instruction-shaped；
  HEAD 基線內 tracked 條目（trusted）＝降級 review；白例形內容＝clean。
- guard 模組缺席＝退回無標籤（guard=""）＋exit 2 不變（標註層故障不得
  反寫偵測契約）。

既有 test_reconcile_memory_pool.py 契約測試未動；本 agent 無 Bash 面，
全綠由 marshal seal（NOT VERIFIED）。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/reconcile_memory_pool.py")
reconcile_pool = _mod.reconcile_pool
SCRIPT = REPO_ROOT / "scripts" / "reconcile_memory_pool.py"

GIT_C = ["-c", "user.email=t@t", "-c", "user.name=t"]

# golden 正例（pos-teardown-distilled-work-order）逐字重用——AIR-93 dossier
# §2.1 teardown 特徵，memory_guard_rules 機械面已釘 black
TEARDOWN_PAYLOAD = (
    "夜波 gate pollution 必須擋下——任何 batch 寫入恆停並回報，"
    "依 governance hook 條款執行。"
)
# golden 白例（white-provenance-citation）逐字重用——出處框架指針記載形
BENIGN_POINTER = (
    "本條源自 rules/outward-action-consent.md 的 reversibility test，"
    "2026-09 收斂定案。"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *GIT_C, *args], check=True, capture_output=True
    )


def _seed_pool(repo: Path, layout: str = "nested") -> Path:
    """governed repo 骨架（形態照抄 test_reconcile_memory_pool）：marker＋pool＋commit 基線。"""
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


def _entry(result, name: str):
    hits = [e for e in result.entries if name in e.path]
    assert hits, f"delta 內找不到 {name}：{[(e.code, e.path) for e in result.entries]}"
    return hits[0]


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


# ---- 分流三級（同一 teardown payload 的來源分層對照）----


def test_untracked_teardown_payload_labeled_instruction_shaped(tmp_path: Path) -> None:
    # AIR-93 teardown 面：untracked 裸 payload＝來源未審核，black 照 black 進 quarantine
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    e = _entry(r, "muse-dropped.md")
    assert e.code == "??"
    assert e.guard == "instruction-shaped"


@pytest.mark.parametrize("layout", ["nested", "flat"])
def test_tracked_regulatory_entry_demoted_to_review(
    tmp_path: Path, layout: str
) -> None:
    # trusted 面：同一 black 內容、HEAD 基線內 tracked 條目——black 降 review
    # （S1 來源分層語義：池內已過晉升的規範性記載是合法形態）
    repo = _seed_pool(tmp_path / "repo", layout)
    (repo / ".agents" / "memory" / "entry-a.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert _entry(r, "entry-a.md").guard == "review"


def test_benign_pointer_entry_labeled_clean(tmp_path: Path) -> None:
    # 白例形內容（出處框架指針記載）——分類乾淨；mutation 本身仍由 dirty 承接
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "entry-a.md").write_text(
        BENIGN_POINTER + "\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert _entry(r, "entry-a.md").guard == "clean"


def test_deleted_delta_labeled_clean_no_content(tmp_path: Path) -> None:
    # 刪除 delta 無內容可分類——空文本 classify 回 clean（無 payload 在場）
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "entry-a.md").unlink()
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert _entry(r, "entry-a.md").guard == "clean"


# ---- exit 契約零漂移（硬閘）----


def test_exit_contract_unchanged_with_labels(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo")
    assert _run_cli(str(repo)).returncode == 0  # clean
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    done = _run_cli(str(repo))
    assert done.returncode == 2  # dirty——標籤不改 exit
    assert "[FAIL]" in done.stdout
    assert "[instruction-shaped]" in done.stdout  # quarantine 明細帶分流標籤


def test_json_entries_carry_guard_additively(tmp_path: Path) -> None:
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    (repo / ".agents" / "memory" / "handoff-note.md").write_text(
        BENIGN_POINTER + "\n", encoding="utf-8"
    )
    done = _run_cli(str(repo), "--json")
    payload = json.loads(done.stdout)
    assert payload["status"] == "dirty"
    by_name = {Path(e["path"]).name: e for e in payload["entries"]}
    assert by_name["muse-dropped.md"]["guard"] == "instruction-shaped"
    assert by_name["handoff-note.md"]["guard"] == "clean"
    # 既有欄位不動（additive）
    assert by_name["muse-dropped.md"]["code"] == "??"


def test_json_clean_path_has_no_guard_leakage(tmp_path: Path) -> None:
    # 標籤是 exit-2 附加面——clean 路徑 entries 恆空，無標籤可洩
    repo = _seed_pool(tmp_path / "repo")
    done = _run_cli(str(repo), "--json")
    payload = json.loads(done.stdout)
    assert done.returncode == 0
    assert payload["status"] == "clean"
    assert payload["entries"] == []


def test_fail_loud_path_never_reaches_classifier(tmp_path: Path) -> None:
    # exit 1（marker malformed）在 reconcile_pool 內 raise——分類層不在場
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory-governance.json").write_text(
        "not-json", encoding="utf-8"
    )
    assert _run_cli(str(repo)).returncode == 1


def test_porcelain_delta_shape_untouched_by_annotation(tmp_path: Path) -> None:
    # 既有契約複釘：掛點只加 guard 欄位，code/path/status 偵測面不動
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    (repo / ".agents" / "memory" / "entry-a.md").write_text(
        "繞閘髒寫入\n", encoding="utf-8"
    )
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert _entry(r, "muse-dropped.md").code == "??"
    assert _entry(r, "entry-a.md").code == " M"


# ---- guard 層缺席＝無標籤但 exit 不變（標註層故障不得反寫偵測契約）----


def test_guard_absence_keeps_dirty_exit_unlabeled(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = _seed_pool(tmp_path / "repo")
    (repo / ".agents" / "memory" / "muse-dropped.md").write_text(
        TEARDOWN_PAYLOAD + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(_mod, "_load_guard_rules", lambda: None)
    r = reconcile_pool(repo)
    assert r.status == "dirty"
    assert all(e.guard == "" for e in r.entries)
    assert _mod.main([str(repo), "--json"]) == 2
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] == "dirty"
    assert all(e["guard"] == "" for e in payload["entries"])
    assert "unavailable" in captured.err  # fail loud：標註缺席須可見，非靜默
