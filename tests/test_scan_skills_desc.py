"""scan_skills_desc 契約軸回歸測試。

釘住的軸（AIR-87 段落 0 實證）：ZCode drop 閾值＝desc「值」的 chars（非整行、
非 bytes——awk length 給 bytes、CJK 3B/char 是兩次咬人的量測陷阱）。
"""

from pathlib import Path

from conftest import load_module

_scan = load_module("scripts/scan_skills_desc.py")
scan_skill, ScanResult = _scan.scan_skill, _scan.ScanResult
fix_skill = _scan.fix_skill


def _write(tmp_path: Path, frontmatter: str) -> Path:
    d = tmp_path / "fixture-skill"
    d.mkdir()
    p = d / "SKILL.md"
    p.write_text(f"---\n{frontmatter}\n---\n\n# body\n", encoding="utf-8")
    return d


def test_value_chars_axis_cjk_not_bytes(tmp_path: Path) -> None:
    # 700 個 CJK chars = 2,100 bytes——bytes 軸會誤判 >1024，chars 軸正確放行
    val = "觸" * 700
    r = scan_skill(_write(tmp_path, f'name: x\ndescription: "{val}"'))
    assert r.value_chars == 702  # 內容 700＋成對引號 2（as-written 保守計）
    assert not r.is_fail


def test_over_1024_value_chars_fails(tmp_path: Path) -> None:
    val = "a" * 1025
    r = scan_skill(_write(tmp_path, f'name: x\ndescription: "{val}"'))
    assert r.value_chars == 1027
    assert r.is_fail


def test_line_prefix_not_counted(tmp_path: Path) -> None:
    # 整行 1,033 chars（值 1,022）——cr-query 實例：在線上、不可誤報
    val = "a" * 1022
    r = scan_skill(_write(tmp_path, f'name: x\ndescription: "{val}"'))
    assert r.value_chars == 1024
    assert not r.is_fail


def test_bare_unquoted_fails_quote_gate(tmp_path: Path) -> None:
    r = scan_skill(_write(tmp_path, "name: x\ndescription: plain value"))
    assert r.form == "bare"
    assert r.is_fail


def test_quoted_with_hash_is_safe_no_trap(tmp_path: Path) -> None:
    r = scan_skill(_write(tmp_path, 'name: x\ndescription: "use it # now"'))
    assert r.form == "quoted"
    assert not r.hash_trap
    assert not r.is_fail


def test_bare_with_hash_sets_trap(tmp_path: Path) -> None:
    # 完整 YAML 剝 ' #'、ZCode flat parser 不剝——雙解析器長度分歧
    r = scan_skill(_write(tmp_path, "name: x\ndescription: use it # now"))
    assert r.form == "bare"
    assert r.hash_trap
    assert r.is_fail


def test_block_scalar_ok_and_measured_by_content(tmp_path: Path) -> None:
    p = _write(tmp_path, "name: x\ndescription: >\n  line one\n  line two")
    r = scan_skill(p)
    assert r.form == "block"
    assert r.value_chars == len("line one line two")
    assert not r.is_fail


def test_missing_desc_fails(tmp_path: Path) -> None:
    r = scan_skill(_write(tmp_path, "name: x"))
    assert r.form == "missing"
    assert r.is_fail


def test_missing_name_fails(tmp_path: Path) -> None:
    r = scan_skill(_write(tmp_path, 'description: "x"'))
    assert r.is_fail


def test_single_quoted_fails_double_quote_gate(tmp_path: Path) -> None:
    # Fr2/Pr4：形式 gate 只認雙引號——單引號包夾收緊為 fail（form "single"）
    r = scan_skill(_write(tmp_path, "name: x\ndescription: 'plain value'"))
    assert r.form == "single"
    assert r.is_fail


def test_fix_skill_idempotent_bare_to_quoted(tmp_path: Path) -> None:
    # 冪等：bare 第一次引號化回 True，第二次已 quoted 回 False 不再動
    d = _write(tmp_path, "name: x\ndescription: plain value")
    assert fix_skill(d) is True
    assert scan_skill(d).form == "quoted"
    assert fix_skill(d) is False


def test_fix_skill_skips_inner_double_quote(tmp_path: Path) -> None:
    # 內含雙引號值 → 回 False 不動（跳過留人工，防嵌套錯引號）
    d = _write(tmp_path, 'name: x\ndescription: say "hello" now')
    before = (d / "SKILL.md").read_text()
    assert fix_skill(d) is False
    assert (d / "SKILL.md").read_text() == before
