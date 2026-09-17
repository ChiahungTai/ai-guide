"""projection_freshness 單元測試——manifest 宣告的投影 upstream hash gate（AIR-122）。

exit 契約：0=全 fresh、1=drift（列哪條投影的哪個 upstream 變了）、
2=fatal（manifest/upstream 缺席、快照不完整、section 錨不命中）。
"""

import subprocess
from pathlib import Path

from conftest import load_module

freshness = load_module("scripts/projection_freshness.py")

SECTION = "命令的受眾視角"

ROOT_AGENTS = (
    f"# Repo\n\n## {SECTION}\n\n受眾節內容甲。\n\n## 專案結構\n\n結構節內容。\n"
)

MANIFEST_NO_HASH = """\
[[projection]]
artifact = "proj/index.html"

[[projection.upstream]]
path = "docs/guide.md"

[[projection.upstream]]
path = "AGENTS.md"
section = "命令的受眾視角"
"""


def _mini_repo(tmp_path: Path) -> tuple[Path, Path]:
    """建最小投影 repo：root AGENTS.md（雙節）＋一 upstream 檔＋投影殼＋無快照 manifest。"""
    (tmp_path / "AGENTS.md").write_text(ROOT_AGENTS, encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\n\n導覽文字。\n", encoding="utf-8"
    )
    (tmp_path / "proj").mkdir()
    (tmp_path / "proj" / "index.html").write_text("<html>殼</html>", encoding="utf-8")
    manifest = tmp_path / "proj" / "projection-manifest.toml"
    manifest.write_text(MANIFEST_NO_HASH, encoding="utf-8")
    return manifest, tmp_path


def _run(manifest: Path, root: Path, capsys, *flags: str) -> tuple[int, str, str]:
    code = freshness.main(
        ["--manifest", str(manifest), "--repo-root", str(root), *flags]
    )
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_check_without_snapshot_is_fatal(tmp_path, capsys):
    """check 遇無 sha1 快照的 manifest＝fatal 2（先 --update 建快照，非 drift）。"""
    manifest, root = _mini_repo(tmp_path)
    code, _, err = _run(manifest, root, capsys)
    assert code == 2
    assert "sha1" in err


def test_update_builds_snapshot_then_fresh(tmp_path, capsys):
    """--update 寫回 hash 快照；之後 check exit 0 並列 fresh 投影。"""
    manifest, root = _mini_repo(tmp_path)
    code, _, _ = _run(manifest, root, capsys, "--update")
    assert code == 0
    assert manifest.read_text(encoding="utf-8").count("sha1 = ") == 2
    code, out, _ = _run(manifest, root, capsys)
    assert code == 0
    assert "proj/index.html" in out
    assert "fresh" in out


def test_upstream_change_drifts(tmp_path, capsys):
    """整檔 upstream 內容變 → exit 1，輸出列明投影與 upstream。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    (root / "docs" / "guide.md").write_text(
        "# Guide\n\n導覽文字改。\n", encoding="utf-8"
    )
    code, out, _ = _run(manifest, root, capsys)
    assert code == 1
    assert "proj/index.html" in out
    assert "docs/guide.md" in out


def test_section_inside_change_drifts(tmp_path, capsys):
    """section 錨＝只 hash 該節：節內文字變 → drift。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    changed = ROOT_AGENTS.replace("受眾節內容甲。", "受眾節內容乙。")
    (root / "AGENTS.md").write_text(changed, encoding="utf-8")
    code, out, _ = _run(manifest, root, capsys)
    assert code == 1
    assert "AGENTS.md" in out


def test_section_outside_change_stays_fresh(tmp_path, capsys):
    """section 錨：節外（同檔另一節）文字變 → 仍 fresh（防無關改動噪音閘）。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    changed = ROOT_AGENTS.replace("結構節內容。", "結構節內容改。")
    (root / "AGENTS.md").write_text(changed, encoding="utf-8")
    code, _, _ = _run(manifest, root, capsys)
    assert code == 0


def test_update_converges_and_idempotent(tmp_path, capsys):
    """drift → --update 收斂（check 轉 0）且重寫冪等（內容不變）。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    (root / "docs" / "guide.md").write_text(
        "# Guide\n\n導覽文字二改。\n", encoding="utf-8"
    )
    assert _run(manifest, root, capsys)[0] == 1
    code, _, _ = _run(manifest, root, capsys, "--update")
    assert code == 0
    snapshot = manifest.read_text(encoding="utf-8")
    assert _run(manifest, root, capsys)[0] == 0
    _run(manifest, root, capsys, "--update")
    assert manifest.read_text(encoding="utf-8") == snapshot


def test_missing_upstream_file_is_fatal(tmp_path, capsys):
    """upstream 檔缺席（刪除/改名）＝追丟源 → exit 2 非 drift。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    (root / "docs" / "guide.md").unlink()
    code, _, err = _run(manifest, root, capsys)
    assert code == 2
    assert "docs/guide.md" in err


def test_missing_manifest_is_fatal(tmp_path, capsys):
    """manifest 檔缺席 → exit 2。"""
    code, _, _ = _run(tmp_path / "nope.toml", tmp_path, capsys)
    assert code == 2


def test_missing_section_anchor_is_fatal(tmp_path, capsys):
    """upstream 在但 section 錨不命中（節改名/刪除）＝無法計算 → exit 2。"""
    manifest, root = _mini_repo(tmp_path)
    _run(manifest, root, capsys, "--update")
    changed = ROOT_AGENTS.replace(f"## {SECTION}", "## 受眾視角（改名）")
    (root / "AGENTS.md").write_text(changed, encoding="utf-8")
    code, _, err = _run(manifest, root, capsys)
    assert code == 2
    assert SECTION in err


def test_malformed_manifest_is_fatal(tmp_path, capsys):
    """manifest TOML 語法錯誤 → exit 2。"""
    manifest, root = _mini_repo(tmp_path)
    manifest.write_text("[[projection]\nbroken", encoding="utf-8")
    code, _, _ = _run(manifest, root, capsys)
    assert code == 2


def test_file_hash_matches_git_hash_object(tmp_path):
    """整檔 hash 與 git hash-object 等價（sha1 of blob）。"""
    f = tmp_path / "blob.txt"
    f.write_bytes("hello 投影\n".encode())
    expected = subprocess.run(
        ["git", "hash-object", str(f)], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert freshness.hash_file(f) == expected


def test_section_hash_tracks_slice_only(tmp_path):
    """section hash 隨節文字變、不隨節外內容變（直接驗證 slice 語義）。"""

    def variant(name: str, old: str, new: str) -> Path:
        p = tmp_path / name
        p.write_text(ROOT_AGENTS.replace(old, new), encoding="utf-8")
        return p

    agents = variant("AGENTS.md", "無此字串", "無此字串")
    base = freshness.hash_section(agents, SECTION)
    inside = freshness.hash_section(
        variant("inside.md", "受眾節內容甲。", "受眾節內容乙。"), SECTION
    )
    outside = freshness.hash_section(
        variant("outside.md", "結構節內容。", "結構節內容改。"), SECTION
    )
    assert inside != base
    assert outside == base
