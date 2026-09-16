"""build_shell.py 契約測試（AIR-73）。

三級 gate 對應：
- hard 六項：① ordered semantic leaves 全等＋屬性臂（href/iframe src 有序比對——lossless
  補洞）／②③④ 三硬約束行為面（首屏 active、折疊不重載、aria＋localStorage）／
  ⑤ meta completeness（identity contract＋diagram key-set multiset 鎖死）／
  ⑥ 確定性重跑——golden 重現全綠。
- mutation 七型（防同源自洽）：M1 葉刪除／M2 葉重排／M3 內容竄改／M4 meta 竄改／
  M5 行為面竄改／M6 重跑分歧／M7 屬性竄改——各型必紅。
- 祖父條款：無 builder marker 的既有殼拒絕覆寫；有 marker 可重生；symlink 目標拒絕。

golden 譜系聲明：四組 golden＝mosaic 原殼（tagging-loop／studyarea-lib／factors-cache／
mos80-lot）人工精簡萃取＋人審對照，非 builder 產物——byte-equality 錨的獨立性來源
（tests/fixtures/build_shell/）；mosaic repo 不在場時測試仍自含全綠。
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import load_module

bs = load_module("skills/_common/build_shell.py")

FIXTURES = Path(__file__).parent / "fixtures" / "build_shell"

# 結構差異最大化的四材料：手製 sidebar／單欄無 sidebar／iframe 雙圖／degraded＋fold
GOLDEN_NAMES = [
    "tagging-loop",  # mosaic 09-02-tagging-machine-loop
    "studyarea-lib",  # mosaic 09-03-studyarea-llm-lib
    "factors-cache",  # mosaic 09-04-factors-cache-incremental
    "mos80-lot",  # mosaic 09-09-mos80-volume-lot-single-source
]

MIN_MD = """---
card_id: AIR-73
task_baseline: 9936ce5
title: 最小契約殼
report_type: task-plan
task_type: architecture
diagram_heights:
  arch: 640
---

<!-- section-group: {"id": "s1", "title": "① 概要", "sub": "契約最小樣"} -->
這是**首段**，含 `code` 與 [連結](ep.md)。

- 第一點
- 第二點

| 欄A | 欄B |
|---|---|
| a1 | b1 |
| a2 | b2 |

<!-- fold: appendix -->
### 附錄細節
折疊段內文。

<!-- section-group: {"id": "s2", "title": "② 回源", "sub": "殼是展示層"} -->
<!-- diagram-assign: {"id": "arch", "src": "diagram-architecture.html", "title": "架構圖"} -->
回源說明一段。
"""


def _fixture_md(name: str) -> str:
    return (FIXTURES / f"{name}.report.md").read_text(encoding="utf-8")


def _fixture_golden(name: str) -> str:
    return (FIXTURES / f"{name}.golden.html").read_text(encoding="utf-8")


# ── golden 重現：四材料 build→gate 全過＋byte 級 golden＋確定性重跑 ──


@pytest.mark.parametrize("name", GOLDEN_NAMES)
def test_golden_reproduces_and_gate_green(name):
    md = _fixture_md(name)
    html = bs.build(md, source_name=f"{name}.report.md")
    assert html == _fixture_golden(name), f"{name}: 輸出與 golden 不一致"
    assert bs.run_gate(md, html) == []


@pytest.mark.parametrize("name", GOLDEN_NAMES)
def test_golden_deterministic_rerun(name):
    md = _fixture_md(name)
    assert bs.build(md, source_name="x.md") == bs.build(md, source_name="x.md")


# ── hard gate 各項行為 ──


def test_gate_leaves_equality_direct():
    html = bs.build(MIN_MD, source_name="min.md")
    assert bs.md_leaves(MIN_MD) == bs.html_leaves(html)


def test_gate_first_frame_targets_first_frame_section():
    html = bs.build(MIN_MD, source_name="min.md")
    # arch 圖在 s2（唯一 frame）→ canonical init JS 在場且無預設 active class（JS 驅動）
    assert 'document.querySelector(\'main section .frame-wrap\')' in html
    assert 'class="active"' not in html
    # nav href 與 section id 一一對應
    assert 'href="#s1"' in html and 'id="s1"' in html
    assert 'href="#s2"' in html and 'id="s2"' in html


def test_gate_nav_correspondence_broken_flagged():
    html = bs.build(MIN_MD, source_name="min.md")
    bad = html.replace('href="#s2"', 'href="#sX"')
    violations = bs.run_gate(MIN_MD, bad)
    assert any(v.startswith("first-screen:") for v in violations)


def test_meta_completeness_marker_fields():
    html = bs.build(MIN_MD, source_name="min.md")
    assert "card_id=AIR-73" in html
    assert "task_baseline=9936ce5" in html
    assert "mode=lossless" in html
    assert "diagrams=arch" in html


def test_diagram_height_keyset_locked_extra_key_red():
    md = MIN_MD.replace("  arch: 640\n", "  arch: 640\n  ghost: 720\n")
    with pytest.raises(bs.BuildError, match="diagram_heights"):
        bs.build(md, source_name="min.md")


def test_diagram_height_keyset_locked_missing_key_red():
    md = MIN_MD.replace("  arch: 640\n", "  other: 640\n")
    with pytest.raises(bs.BuildError, match="diagram_heights"):
        bs.build(md, source_name="min.md")


def test_diagram_height_applied_to_iframe():
    md = MIN_MD.replace("  arch: 640\n", "  arch: 700\n")
    html = bs.build(md, source_name="min.md")
    assert 'style="height:700px;min-height:0"' in html


# ── 邊界（E 重複 id multiset 語義＋輸入邊界）──


def test_duplicate_diagram_id_red():
    """E：body 出現重複 diagram id → BuildError（multiset 語義，set 去重不得掩蓋）。"""
    md = MIN_MD.replace(
        "回源說明一段。",
        '<!-- diagram-assign: {"id": "arch", "title": "架構圖二"} -->\n回源說明一段。',
    )
    with pytest.raises(bs.BuildError, match="diagram-assign id 重複"):
        bs.build(md, source_name="min.md")


def test_duplicate_section_id_red():
    """E：body 出現重複 section id → BuildError。"""
    md = MIN_MD.replace(
        '<!-- section-group: {"id": "s2", "title": "② 回源", "sub": "殼是展示層"} -->',
        '<!-- section-group: {"id": "s1", "title": "① 概要二", "sub": "撞 id"} -->',
    )
    with pytest.raises(bs.BuildError, match="section-group id 重複"):
        bs.build(md, source_name="min.md")


def test_boundary_heights_non_integer_red():
    md = MIN_MD.replace("  arch: 640\n", "  arch: abc\n")
    with pytest.raises(bs.BuildError, match="整數"):
        bs.build(md, source_name="min.md")


def test_boundary_frontmatter_unclosed_red():
    md = "---\ncard_id: AIR-73\ntask_baseline: 9936ce5\ntitle: t\nreport_type: task-plan\n"
    with pytest.raises(bs.BuildError, match="未閉合"):
        bs.build(md, source_name="min.md")


def test_boundary_empty_md_red():
    with pytest.raises(bs.BuildError, match="frontmatter"):
        bs.build("", source_name="min.md")


# ── 契約 fail loud ──


def test_contract_missing_card_id_red():
    md = MIN_MD.replace("card_id: AIR-73\n", "")
    with pytest.raises(bs.BuildError, match="card_id"):
        bs.build(md, source_name="min.md")


def test_contract_missing_task_baseline_red():
    md = MIN_MD.replace("task_baseline: 9936ce5\n", "")
    with pytest.raises(bs.BuildError, match="task_baseline"):
        bs.build(md, source_name="min.md")


def test_contract_curated_mode_refused():
    md = MIN_MD.replace("report_type: task-plan", "mode: curated\nreport_type: task-plan")
    with pytest.raises(bs.BuildError, match="curated"):
        bs.build(md, source_name="min.md")


def test_unknown_report_type_open_semantics(caplog):
    """未知 report_type → 開放語義：fold 全部預設收合＋warning（非 hard fail）。"""
    md = _fold_probe_md("memo")
    with caplog.at_level(logging.WARNING, logger="skills._common.build_shell"):
        html = bs.build(md, source_name="min.md")
    assert "<details>" in html and "<details open>" not in html
    assert any("report_type" in r.message and "memo" in r.message for r in caplog.records)


def test_fold_cross_mapping_defaults_collapsed_with_warning(caplog):
    """已知 fold group 不在 report_type 折疊映射內 → 預設收合＋warning（非 hard fail）。"""
    md = MIN_MD.replace("<!-- fold: appendix -->", "<!-- fold: evidence -->")
    with caplog.at_level(logging.WARNING, logger="skills._common.build_shell"):
        html = bs.build(md, source_name="min.md")
    assert "<details>" in html and "<details open>" not in html
    assert any("fold" in r.message and "evidence" in r.message for r in caplog.records)


def test_contract_unknown_fold_group_red():
    md = MIN_MD.replace("<!-- fold: appendix -->", "<!-- fold: gossip -->")
    with pytest.raises(bs.BuildError, match="fold"):
        bs.build(md, source_name="min.md")


def test_contract_unknown_task_type_red():
    md = MIN_MD.replace("task_type: architecture", "task_type: vibe")
    with pytest.raises(bs.BuildError, match="task_type"):
        bs.build(md, source_name="min.md")


# ── report-type 折疊預設映射＋task_type 圖預設（09-15 設計輸入②④）──


def _fold_probe_md(report_type: str) -> str:
    return MIN_MD.replace("report_type: task-plan", f"report_type: {report_type}")


def test_fold_default_by_report_type():
    closed = bs.build(_fold_probe_md("task-plan"), source_name="min.md")
    opened = bs.build(_fold_probe_md("study-notes"), source_name="min.md")
    # task-plan：appendix 預設收合（無 open 屬性）；study-notes：appendix 預設展開
    assert "<details>" in closed and "<details open>" not in closed
    assert "<details open>" in opened


def test_task_type_degraded_hint_mapping():
    md = MIN_MD.replace(
        '<!-- diagram-assign: {"id": "arch", "src": "diagram-architecture.html", "title": "架構圖"} -->',
        '<!-- diagram-assign: {"id": "arch", "title": "架構圖"} -->',
    )
    ui_md = md.replace("task_type: architecture", "task_type: ui")
    arch_md = md
    assert "UI mockup 圖" in bs.build(ui_md, source_name="min.md")
    assert "架構圖講解" in bs.build(arch_md, source_name="min.md")
    # 無 src → degraded（無 iframe）；有 src → iframe
    assert "<iframe" not in bs.build(ui_md, source_name="min.md")
    assert "<iframe" in bs.build(MIN_MD, source_name="min.md")


# ── 祖父＋碰觸遷移：overwrite 政策 ──


def _write_md(tmp_path: Path) -> Path:
    p = tmp_path / "report.md"
    p.write_text(MIN_MD, encoding="utf-8")
    return p


def test_overwrite_refuses_legacy_shell(tmp_path, capsys):
    md_path = _write_md(tmp_path)
    out = tmp_path / "index.html"
    out.write_text("<html><body>legacy curated 手填殼</body></html>", encoding="utf-8")
    code = bs.main([str(md_path)])
    assert code == 2
    captured = capsys.readouterr()
    assert "legacy-curated" in captured.out + captured.err
    assert out.read_text(encoding="utf-8").startswith("<html>")  # 未被覆寫


def test_overwrite_allows_builder_marker_file(tmp_path):
    md_path = _write_md(tmp_path)
    out = tmp_path / "index.html"
    first = bs.build(MIN_MD, source_name="report.md")
    out.write_text(first, encoding="utf-8")
    assert bs.main([str(md_path)]) == 0
    assert out.read_text(encoding="utf-8") == first  # 重生成 byte 相同


def test_write_new_target_ok(tmp_path):
    md_path = _write_md(tmp_path)
    assert bs.main([str(md_path)]) == 0
    assert (tmp_path / "index.html").exists()


def test_overwrite_refuses_symlink_target(tmp_path, capsys):
    """F：輸出目標是 symlink → BuildError 拒絕（禁跟隨寫入穿透目標檔）。"""
    md_path = _write_md(tmp_path)
    real = tmp_path / "real.html"
    real.write_text("<html>real</html>", encoding="utf-8")
    out = tmp_path / "index.html"
    out.symlink_to(real)
    assert bs.main([str(md_path)]) == 3
    assert "symlink" in capsys.readouterr().err
    assert real.read_text(encoding="utf-8") == "<html>real</html>"  # 未被穿透
    assert out.is_symlink()  # symlink 本體未被置換


def test_write_is_atomic_no_tmp_leftover(tmp_path):
    """F：寫入走 tmp＋os.replace——成功後不殘留 .tmp（新生與重生兩路徑）。"""
    md_path = _write_md(tmp_path)
    assert bs.main([str(md_path)]) == 0
    out = tmp_path / "index.html"
    first = out.read_text(encoding="utf-8")
    assert first == bs.build(MIN_MD, source_name="report.md")
    assert not list(tmp_path.glob("*.tmp"))
    assert bs.main([str(md_path)]) == 0  # marker 重生路徑
    assert out.read_text(encoding="utf-8") == first
    assert not list(tmp_path.glob("*.tmp"))


# ── mutation 六型（防同源自洽——每型必紅）──


def _gate_keys(violations: list[str]) -> list[str]:
    return [v.split(":", 1)[0] for v in violations]


def test_mutation_m1_leaf_drop_red():
    """M1 葉刪除：抽掉一個 li → leaves 全等紅。"""
    html = bs.build(_fixture_md("tagging-loop"), source_name="x.md")
    mutated = html.replace("<li>首批六 tags＋修飾 tags 全平級；1435 型＝tag 疊加</li>\n", "")
    assert mutated != html
    assert "leaves" in _gate_keys(bs.run_gate(_fixture_md("tagging-loop"), mutated))


def test_mutation_m2_leaf_reorder_red():
    """M2 葉重排：對調兩個純文字 p 區塊 → ordered 全等紅（葉數不變）。"""
    html = bs.build(_fixture_md("studyarea-lib"), source_name="x.md")
    ps = re.findall(r"<p>[^<]*</p>", html)
    assert len(ps) >= 2 and ps[0] != ps[1]
    first, second = ps[0], ps[1]
    mutated = (
        html.replace(first, "@@A@@", 1).replace(second, first, 1).replace("@@A@@", second, 1)
    )
    assert mutated != html
    assert "leaves" in _gate_keys(bs.run_gate(_fixture_md("studyarea-lib"), mutated))


def test_mutation_m3_content_tamper_red():
    """M3 內容竄改：p 葉內文竄改（葉數與順序不變）→ leaves 全等紅。"""
    html = bs.build(_fixture_md("tagging-loop"), source_name="x.md")
    seg = re.search(r"<p>[^<]*</p>", html)
    assert seg is not None
    inner = seg.group(0)[3:-4]
    assert len(inner) > 4
    tampered_seg = f"<p>竄改{inner[2:]}</p>"
    mutated = html.replace(seg.group(0), tampered_seg, 1)
    assert mutated != html
    assert "leaves" in _gate_keys(bs.run_gate(_fixture_md("tagging-loop"), mutated))


def test_mutation_m4_meta_tamper_red():
    """M4 meta 竄改：marker 內 task_baseline 改值（從 build 產物 regex 抽值——不寫死
    fixture 值，fixture 換 baseline 不失明）→ meta completeness 紅。"""
    md = _fixture_md("tagging-loop")
    html = bs.build(md, source_name="x.md")
    m = re.search(r"task_baseline=([\w.]+)", html)
    assert m is not None
    mutated = html.replace(f"task_baseline={m.group(1)}", "task_baseline=deadbeef")
    assert mutated != html
    assert "meta" in _gate_keys(bs.run_gate(md, mutated))


def test_mutation_m5_behavior_tamper_red():
    """M5 行為面竄改：init JS 首屏查詢被改 → 行為面三硬約束紅。"""
    html = bs.build(_fixture_md("factors-cache"), source_name="x.md")
    mutated = html.replace(
        "document.querySelector('main section .frame-wrap')",
        "document.querySelector('main section')",
    )
    assert mutated != html
    keys = _gate_keys(bs.run_gate(_fixture_md("factors-cache"), mutated))
    assert {"first-screen", "collapse", "a11y"} & set(keys)


def test_mutation_m6_rerun_divergence_red():
    """M6 重跑分歧：同 md 兩次產物不一致 → 確定性重跑紅；一致則綠。"""
    md = _fixture_md("mos80-lot")
    html_a = bs.build(md, source_name="x.md")
    html_b = html_a.replace("MOS-80", "MOS-80x", 1)
    keys = _gate_keys(bs.run_gate(md, html_a, prev_html=html_b))
    assert "determinism" in keys
    assert bs.run_gate(md, html_a, prev_html=html_a) == []


def test_mutation_m7_attr_tamper_red():
    """M7 屬性竄改：iframe src／bar href 各竄改一處（葉文不動）→ attrs 有序比對紅。"""
    md = _fixture_md("factors-cache")
    html = bs.build(md, source_name="x.md")
    tampered_src = html.replace("diagram-architecture.html?embed=1", "evil.html?embed=1", 1)
    assert tampered_src != html
    assert "attrs" in _gate_keys(bs.run_gate(md, tampered_src))
    tampered_href = html.replace(
        'href="diagram-workflow.html" target="_blank"',
        'href="evil2.html" target="_blank"',
        1,
    )
    assert tampered_href != html
    assert "attrs" in _gate_keys(bs.run_gate(md, tampered_href))


def test_attrs_gate_covers_links_and_iframe_src():
    """屬性臂綠路徑：sub 連結 href＋diagram src（bar href＋iframe src）有序全等。"""
    md = MIN_MD.replace('"sub": "殼是展示層"', '"sub": "殼是展示層，詳見 [EP](ep.md)"')
    html = bs.build(md, source_name="min.md")
    assert '<a href="ep.md">' in html
    assert bs.run_gate(md, html) == []


# ── 確定性跨 process 證據（C：PYTHONHASHSEED 不同兩次 build byte 相等）──


def test_determinism_cross_process_byte_equal(tmp_path):
    md = _fixture_md("tagging-loop")
    md_path = tmp_path / "report.md"
    md_path.write_text(md, encoding="utf-8")
    script = Path(bs.__file__).resolve()
    outs = []
    for seed in ("0", "12345"):
        proc = subprocess.run(
            [sys.executable, str(script), "--stdout", str(md_path)],
            capture_output=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
            check=True,
        )
        outs.append(proc.stdout)
    assert outs[0] == outs[1], "跨 process（PYTHONHASHSEED 0 vs 12345）輸出分歧"
    assert outs[0] == bs.build(md, source_name="report.md").encode("utf-8")


# ── CLI 面信號（--check / --stdout）──


def test_cli_check_green_and_red(tmp_path, capsys):
    md_path = _write_md(tmp_path)
    out = tmp_path / "index.html"
    out.write_text(bs.build(MIN_MD, source_name="report.md"), encoding="utf-8")
    assert bs.main(["--check", str(md_path), str(out)]) == 0
    tampered = out.read_text(encoding="utf-8").replace("card_id=AIR-73", "card_id=AIR-00", 1)
    out.write_text(tampered, encoding="utf-8")
    assert bs.main(["--check", str(md_path), str(out)]) == 3
    assert "meta" in capsys.readouterr().out


def test_cli_stdout_prints_without_write(tmp_path):
    md_path = _write_md(tmp_path)
    assert bs.main(["--stdout", str(md_path)]) == 0
    assert not (tmp_path / "index.html").exists()


# ── D：讀檔失敗 exit 2（BuildError 族 fail-loud 不變，與契約紅 3 分流）──


def test_cli_non_utf8_input_exit2(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"---\n\xff\xfe\xfd\n")
    assert bs.main([str(bad)]) == 2
    assert "utf-8" in capsys.readouterr().err.lower()


def test_cli_missing_input_exit2(tmp_path):
    assert bs.main([str(tmp_path / "nope.md")]) == 2  # build 路徑 md 缺檔
    md_path = _write_md(tmp_path)
    assert bs.main(["--check", str(md_path), str(tmp_path / "ghost.html")]) == 2  # check 路徑 html 缺檔


# ── 夾具完整性（防 golden 漂移的靜態守門）──


def test_fixtures_present_and_contract_headers():
    for name in GOLDEN_NAMES:
        md = _fixture_md(name)
        assert "card_id:" in md and "task_baseline:" in md and "report_type:" in md
        assert "section-group:" in md
        assert (FIXTURES / f"{name}.golden.html").exists()


def test_section_marker_json_shape():
    """section-group 內容為合法 JSON——機器可解析契約（非自由文字）。"""
    md = _fixture_md("factors-cache")
    markers = [
        line
        for line in md.splitlines()
        if line.startswith("<!-- section-group:")
    ]
    assert len(markers) >= 4
    for m in markers:
        payload = m.removeprefix("<!-- section-group:").removesuffix("-->").strip()
        spec = json.loads(payload)
        assert "id" in spec and "title" in spec
