"""scan_project instruction 檔解析的 regression guard（AIR-291）。

單檔 AGENTS.md 模式（雙檔已廢 AIR-289）：AGENTS.md 為 instruction 檔；
CLAUDE.md 僅 legacy fallback；同目錄共存＝X-legacy-dual-file finding
（原行為 AGENTS 靜默蓋掉 CLAUDE、漏報共存——judge 收口項）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "scan-project" / "scripts"))

import scan_project as sp


def _make(root: Path, dir_name: str, agents: bool, claude: bool) -> Path:
    d = root / dir_name
    d.mkdir()
    if agents:
        (d / "AGENTS.md").write_text(f"# {dir_name} agents\n", encoding="utf-8")
    if claude:
        (d / "CLAUDE.md").write_text(f"# {dir_name} claude legacy\n", encoding="utf-8")
    return d


def test_dual_dir_prefers_agents_md(tmp_path):
    _make(tmp_path, "pkg", agents=True, claude=True)
    files = sp._find_instruction_files(tmp_path)
    assert [f.name for f in files] == ["AGENTS.md"]


def test_legacy_only_dir_falls_back_to_claude_md(tmp_path):
    _make(tmp_path, "legacy", agents=False, claude=True)
    files = sp._find_instruction_files(tmp_path)
    assert [f.name for f in files] == ["CLAUDE.md"]


def test_dual_coexistence_emits_finding(tmp_path):
    """共存不可靜默——逐目錄列 X-legacy-dual-file（原行為漏報）。"""
    _make(tmp_path, "pkg", agents=True, claude=True)
    _make(tmp_path, "clean", agents=True, claude=False)
    findings = sp.run_cross_validation({}, [], [], [], tmp_path)
    dual = [f for f in findings if f["check_id"] == "X-legacy-dual-file"]
    assert len(dual) == 1
    assert dual[0]["directory"] == "pkg"
    assert dual[0]["severity"] == "important"


def test_no_dual_no_finding(tmp_path):
    _make(tmp_path, "clean", agents=True, claude=False)
    _make(tmp_path, "legacy", agents=False, claude=True)
    findings = sp.run_cross_validation({}, [], [], [], tmp_path)
    assert [f for f in findings if f["check_id"] == "X-legacy-dual-file"] == []


def test_lookalike_suffix_is_not_dual_file(tmp_path):
    """反例（judge 必修2）：OLD_CLAUDE.md endswith CLAUDE.md 假陽性——
    同目錄 AGENTS.md＋OLD_CLAUDE.md（無真 CLAUDE.md）不得報 X-legacy-dual-file。"""
    _make(tmp_path, "pkg", agents=True, claude=False)
    (tmp_path / "pkg" / "OLD_CLAUDE.md").write_text("# stale\n", encoding="utf-8")
    findings = sp.run_cross_validation({}, [], [], [], tmp_path)
    assert [f for f in findings if f["check_id"] == "X-legacy-dual-file"] == []


def test_lookalike_only_dir_not_legacy_fallback(tmp_path):
    """反例（judge 必修2）：僅 OLD_CLAUDE.md 的目錄不是 legacy instruction 檔——
    不落入 CLAUDE.md fallback 解析。"""
    d = tmp_path / "stale"
    d.mkdir()
    (d / "OLD_CLAUDE.md").write_text("# stale\n", encoding="utf-8")
    assert sp._find_instruction_files(tmp_path) == []
