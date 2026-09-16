"""deploy_agents 治理閘門單元測試（T1-2）。

這些閘門管四家 harness 的部署行為——靜默 regression = 全體系失效無人知
（F9：2026-08-30 前本 repo 9 個 .py、0 個測試）。
"""

import dataclasses
import os
import pathlib
import sys

import pytest
from conftest import load_module

da = load_module("scripts/deploy_agents.py")


def _rule(tmp_path, name: str, scope: str | None, body: str = ""):
    front = f"---\nharness-scope: {scope}\n---\n" if scope else ""
    p = tmp_path / name
    p.write_text(front + body, encoding="utf-8")
    return p


def _marker_rule(tmp_path, name: str, scope: str = "neutral", **keys):
    """帶 projection marker 的 rule 檔；keys 以底線傳入轉 hyphen，None＝省略鍵。"""
    lines = ["---", f"harness-scope: {scope}"]
    for key, value in keys.items():
        key = key.replace("_", "-")
        lines.append(f"{key}: {value}" if value is not None else f"{key}:")
    lines.append("---")
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n# body\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# read_scope：frontmatter 解析
# ---------------------------------------------------------------------------


def test_read_scope_default_neutral(tmp_path):
    p = _rule(tmp_path, "bare.md", None, "# no frontmatter\n")
    assert da.read_scope(p) == "neutral"


def test_read_scope_explicit(tmp_path):
    assert da.read_scope(_rule(tmp_path, "a.md", "claude-specific")) == (
        "claude-specific"
    )
    assert da.read_scope(_rule(tmp_path, "b.md", "meta")) == "meta"


def test_read_scope_stops_at_closing_fence(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("---\nother: 1\n---\nharness-scope: meta\n", encoding="utf-8")
    assert da.read_scope(p) == "neutral"  # fence 後的不算 frontmatter


# ---------------------------------------------------------------------------
# CLAUDE_NOTE_PATTERN：括號注剝除（ASCII/全形/單層巢狀）
# ---------------------------------------------------------------------------


def test_claude_note_ascii():
    cleaned = da.CLAUDE_NOTE_PATTERN.sub("", "see (Claude: `../skills/x.md`) end")
    assert "../skills/x.md" not in cleaned
    assert "see" in cleaned and "end" in cleaned


def test_claude_note_fullwidth():
    cleaned = da.CLAUDE_NOTE_PATTERN.sub("", "見（Claude：路徑）完")
    assert "路徑" not in cleaned
    assert "見" in cleaned and "完" in cleaned


def test_claude_note_nested_parens():
    cleaned = da.CLAUDE_NOTE_PATTERN.sub("", "a (Claude: [x](../skills/y.md)) b")
    assert "../skills/y.md" not in cleaned
    assert "a" in cleaned and "b" in cleaned


def test_claude_note_requires_colon():
    # 「（Claude 端 ...）」無冒號 → 不是豁免注，不剝
    cleaned = da.CLAUDE_NOTE_PATTERN.sub("", "（Claude 端 rule）")
    assert "Claude 端 rule" in cleaned


# ---------------------------------------------------------------------------
# slim_for_bundle：skip marker
# ---------------------------------------------------------------------------


def test_slim_strips_marked_section():
    content = "a\n<!-- bundle: skip-start -->\nsecret\n<!-- bundle: skip-end -->\nb"
    out = da.slim_for_bundle(content, "r.md")
    assert "secret" not in out
    assert "a" in out and "b" in out


def test_slim_noop_without_markers():
    content = "plain\n"
    assert da.slim_for_bundle(content, "r.md") == content


# ---------------------------------------------------------------------------
# check_broken_refs：neutral→claude-specific 死連結（rules + guide）
# ---------------------------------------------------------------------------


def test_broken_ref_rule_to_claude_specific(tmp_path):
    _rule(tmp_path, "target.md", "claude-specific")
    _rule(tmp_path, "src.md", "neutral", "see [t](target.md)\n")
    broken = da.check_broken_refs(tmp_path)
    assert broken == [("src.md", "target.md", "target")]


def test_broken_ref_exempt_in_claude_note(tmp_path):
    _rule(tmp_path, "target.md", "claude-specific")
    _rule(tmp_path, "src.md", "neutral", "see (Claude: [t](target.md))\n")
    assert da.check_broken_refs(tmp_path) == []


def test_broken_ref_scans_guide(tmp_path, monkeypatch):
    rules = tmp_path / "rules"
    rules.mkdir()
    _rule(rules, "target.md", "claude-specific")
    guide = tmp_path / "guide.md"
    guide.write_text("詳見 `target.md`（範例）\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)
    broken = da.check_broken_refs(rules)
    assert ("guide.md", "target.md", "target") in broken


# ---------------------------------------------------------------------------
# check_neutral_purity：rules/AGENTS.md 機械檢查清單的程式化（F4）
# ---------------------------------------------------------------------------


def test_purity_cross_domain_path(tmp_path):
    _rule(tmp_path, "r.md", "neutral", "見 [s](../skills/x/SKILL.md)\n")
    hits = da.check_neutral_purity(tmp_path)
    assert any(label == "cross-domain-path" for _, label, _ in hits)


def test_purity_cross_domain_exempt_in_claude_note(tmp_path):
    _rule(
        tmp_path,
        "r.md",
        "neutral",
        "見 state-md-write（Claude: `../skills/_common/x.md`）\n",
    )
    assert da.check_neutral_purity(tmp_path) == []


def test_purity_bare_slash_command(tmp_path):
    _rule(tmp_path, "r.md", "neutral", "用 `/sync-sources` 檢查\n")
    assert any(
        label == "bare-slash-command"
        for _, label, _ in da.check_neutral_purity(tmp_path)
    )


def test_purity_at_transclusion(tmp_path):
    _rule(tmp_path, "r.md", "neutral", "載入 @~/x.md 或 @../y.md\n")
    hits = da.check_neutral_purity(tmp_path)
    assert any(label == "at-transclusion" for _, label, _ in hits)


def test_purity_abs_user_path(tmp_path):
    _rule(tmp_path, "r.md", "neutral", "在 ~/Github/ai-guide/ 底下\n")
    assert any(
        label == "abs-user-path" for _, label, _ in da.check_neutral_purity(tmp_path)
    )


def test_purity_claude_wrapper_annotation(tmp_path):
    _rule(tmp_path, "ok.md", "neutral", "CLAUDE.md wrapper（Claude 端才有）\n")
    _rule(tmp_path, "bad.md", "neutral", "記得 CLAUDE.md wrapper 同步\n")
    hits = da.check_neutral_purity(tmp_path)
    assert any(
        label == "claude-wrapper-unannotated" and name == "bad.md"
        for name, label, _ in hits
    )


def test_purity_guide_not_scanned(tmp_path, monkeypatch):
    # guide 合法提及跨 harness 裸 slash（/handoff）——purity 掃描範圍限 rules
    rules = tmp_path / "rules"
    rules.mkdir()
    guide = tmp_path / "guide.md"
    guide.write_text("跨 session：`/handoff`\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)
    assert da.check_neutral_purity(rules) == []


# ---------------------------------------------------------------------------
# _changed_rule_sections：deploy ACTION 的逐 rule 變更名單（AIR-105 codex 審查
# ——刪除 rule 必須入列：刪除正是最需要 freshness 提醒的場景）
# ---------------------------------------------------------------------------


def _section_bundle(sections: dict[str, str]) -> str:
    parts = []
    for name, body in sections.items():
        parts.append(f"\n---\n<!-- rules/{name} -->\n{body}")
    return "".join(parts)


def test_changed_rule_sections_added_changed_removed_nochange():
    old = _section_bundle({"a.md": "A1", "b.md": "B1", "c.md": "C1"})
    new = _section_bundle({"a.md": "A2", "c.md": "C1", "d.md": "D1"})
    # a=changed、b=removed（舊有新無）、d=added、c=no-change
    assert da._changed_rule_sections(old, new) == ["a", "b", "d"]


def test_changed_rule_sections_new_target_reports_all():
    old = None
    new = _section_bundle({"a.md": "A1", "b.md": "B1"})
    assert da._changed_rule_sections(old, new) == ["a", "b"]


def test_changed_rule_sections_identical_reports_none():
    text = _section_bundle({"a.md": "A1"})
    assert da._changed_rule_sections(text, text) == []


# ---------------------------------------------------------------------------
# deploy_all：staged atomic 部署（codex 09-06 審查 I-2——unlink+write_text 非
# 原子，中斷可留截斷檔；逐 target catch 續行可讓三 harness policy split）
# ---------------------------------------------------------------------------


def test_deploy_all_stage_failure_leaves_targets_untouched(tmp_path, monkeypatch):
    t1, t2 = tmp_path / "a.md", tmp_path / "b.md"
    t1.write_text("OLD1", encoding="utf-8")
    t2.write_text("OLD2", encoding="utf-8")
    calls = {"n": 0}
    real_fsync = os.fsync

    def flaky_fsync(fd):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("disk full (injected)")
        real_fsync(fd)

    monkeypatch.setattr(da.os, "fsync", flaky_fsync)
    deployed = da.deploy_all([t1, t2], "NEW")
    assert deployed == []
    assert t1.read_text(encoding="utf-8") == "OLD1"  # staging 失敗＝沒有 target 被動
    assert t2.read_text(encoding="utf-8") == "OLD2"
    assert not list(tmp_path.glob("*.tmp"))  # temp 全清


def test_deploy_all_replace_failure_never_truncates(tmp_path, monkeypatch):
    t1, t2 = tmp_path / "a.md", tmp_path / "b.md"
    t1.write_text("OLD1", encoding="utf-8")
    t2.write_text("OLD2", encoding="utf-8")
    real_replace = os.replace

    def flaky_replace(src, dst):
        if dst == t2:
            raise OSError("replace injected failure")
        real_replace(src, dst)

    monkeypatch.setattr(da.os, "replace", flaky_replace)
    deployed = da.deploy_all([t1, t2], "NEW")
    assert deployed == [t1]
    assert t1.read_text(encoding="utf-8") == "NEW"
    assert t2.read_text(encoding="utf-8") == "OLD2"  # 舊完整版，絕非截斷/partial
    assert not list(tmp_path.glob("*.tmp"))


def test_deploy_all_success_and_backup_of_foreign_file(tmp_path):
    t1 = tmp_path / "a.md"
    t1.write_text("user managed, no marker", encoding="utf-8")
    deployed = da.deploy_all([t1], "Generated by scripts/deploy_agents.py\nNEW")
    assert deployed == [t1]
    assert t1.read_text(encoding="utf-8").endswith("NEW")
    assert (tmp_path / "a.md.bak").read_text(encoding="utf-8") == (
        "user managed, no marker"
    )


# ---------------------------------------------------------------------------
# per-target 配置：所有端保留 neutral 核心，各端獨立 size gate
# ---------------------------------------------------------------------------


def test_targets_keep_neutral_rules_with_independent_size_gates(tmp_path):
    targets = {t.label: t for t in da.resolve_targets(tmp_path)}
    assert set(targets) == {"zcode", "codex", "muse"}
    assert targets["zcode"].exclude == frozenset()
    assert targets["codex"].exclude == frozenset()
    assert targets["muse"].exclude == frozenset()
    # 非 muse 端 gate 不動（既有 90KiB 語義）
    assert targets["zcode"].max_bytes == da.BUNDLE_MAX_BYTES
    assert targets["codex"].max_bytes == da.BUNDLE_MAX_BYTES
    # 留出 project instructions 與 startup 包裝的空間（64KiB 共享線內自限）。
    assert targets["muse"].max_bytes == da.MUSE_USER_BUDGET
    assert da.MUSE_USER_BUDGET == 36 * 1024


def test_muse_bundle_contains_every_neutral_rule(tmp_path):
    # 工單沒有保證補回通用約束，部署給 Muse 的實際內容不可整檔漏載。
    targets = {t.label: t for t in da.resolve_targets(tmp_path)}
    bundle = da.bundle_for(targets["muse"])
    for path in da.discover_rules(da.RULES_DIR, {"neutral"}):
        assert f"<!-- rules/{path.name} -->" in bundle
    assert bundle == da.bundle_for(targets["codex"])


def test_build_bundle_respects_exclude(tmp_path):
    a = _rule(tmp_path, "keep.md", "neutral", "# keep\n")
    b = _rule(tmp_path, "drop.md", "neutral", "# drop\n")
    bundle = da.build_bundle([a, b], "neutral", exclude=frozenset({"drop.md"}))
    assert "# keep" in bundle
    assert "# drop" not in bundle
    assert bundle.rstrip().endswith(da.BUNDLE_END_SENTINEL)


def test_check_size_gate_per_target(tmp_path):
    targets = {t.label: t for t in da.resolve_targets(tmp_path)}
    assert da.check_size_gate(10, targets["muse"]) is None
    over = da.check_size_gate(targets["muse"].max_bytes + 1, targets["muse"])
    assert over is not None and "muse" in over
    # 同一尺寸在 90KiB 端通過
    assert da.check_size_gate(targets["muse"].max_bytes + 1, targets["zcode"]) is None


# ---------------------------------------------------------------------------
# read_rule_meta：projection metadata parser（AIR-85 段 1）
#
# 三軸分離：harness-scope 是 scope 軸、paths: 是 CC runtime 軸（契約一：deploy
# 不解析）、bundle-projection 是 portable bundle 投影軸。四 invariant 解析期
# fail-closed；矛盾組合 hard fail（typo 不得靜默變 deployment semantics）。
# ---------------------------------------------------------------------------


def test_read_rule_meta_full_mode_default(tmp_path):
    meta = da.read_rule_meta(_rule(tmp_path, "plain.md", "neutral", "# body\n"))
    assert meta.scope == "neutral"
    assert meta.projection == "full"  # full body 為預設，不標
    assert meta.pointer_target is None
    assert meta.bootstrap_pointer is None


def test_read_rule_meta_explicit_full_is_legal(tmp_path):
    # full 是已知值：顯式標記不 fail（僅 pointer 語義需要 marker）
    meta = da.read_rule_meta(_marker_rule(tmp_path, "a.md", bundle_projection="full"))
    assert meta.projection == "full"


def test_read_rule_meta_pointer_mode_three_keys(tmp_path):
    meta = da.read_rule_meta(
        _marker_rule(
            tmp_path,
            "iw.md",
            bundle_projection="pointer",
            pointer_target="instruction-writing",
            bootstrap_pointer='"先載入 instruction-writing skill"',
        )
    )
    assert meta.scope == "neutral"
    assert meta.projection == "pointer"
    assert meta.pointer_target == "instruction-writing"
    # YAML 對稱引號剝除後逐字保留（bootstrap-pointer 逐字 materialize）
    assert meta.bootstrap_pointer == "先載入 instruction-writing skill"


def test_read_rule_meta_contract_one_no_paths_field(tmp_path):
    # 契約一：deploy 不解析 paths（CC runtime 軸結構性隔離）——回傳結構無 paths
    p = tmp_path / "iw.md"
    p.write_text(
        '---\nharness-scope: neutral\npaths:\n  - "**/*.md"\n---\n# body\n',
        encoding="utf-8",
    )
    meta = da.read_rule_meta(p)
    assert set(dataclasses.asdict(meta)) == {
        "scope",
        "projection",
        "pointer_target",
        "bootstrap_pointer",
    }
    assert meta.projection == "full"  # paths: 不影響 projection 解析


def test_invariant_pointer_mode_requires_target_and_pointer(tmp_path):
    # invariant 1：pointer mode → target 與 pointer 必須齊備（空值＝缺）
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "no-pointer.md",
                bundle_projection="pointer",
                pointer_target="iw",
            )
        )
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "no-target.md",
                bundle_projection="pointer",
                bootstrap_pointer='"x"',
            )
        )
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "empty-pointer.md",
                bundle_projection="pointer",
                pointer_target="iw",
                bootstrap_pointer="",  # S3：空 bootstrap-pointer＝解析期 fail
            )
        )


def test_invariant_unknown_projection_value_fails(tmp_path):
    # invariant 2：未知值（含 typo）fail——不得靜默變 deployment semantics
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "typo.md",
                bundle_projection="poitner",  # S8 typo
                pointer_target="iw",
                bootstrap_pointer='"x"',
            )
        )


def test_invariant_orphan_projection_keys_without_mode_fails(tmp_path):
    # invariant 3：無 mode 卻帶 target/pointer 孤兒鍵 → fail
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(tmp_path, "orphan-target.md", pointer_target="iw")
        )
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(tmp_path, "orphan-pointer.md", bootstrap_pointer='"x"')
        )


def test_invariant_orphan_keys_under_full_mode_fails(tmp_path):
    # invariant 3 延伸：孤兒鍵在非 pointer mode（含顯式 full）下同樣 fail——
    # full mode 不消費 target/pointer，殘留即 schema 錯誤
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "full-orphan.md",
                bundle_projection="full",
                pointer_target="iw",
                bootstrap_pointer='"x"',
            )
        )


def test_invariant_pointer_target_must_be_skill_slug(tmp_path):
    # invariant 4：target 限 skill-id slug（禁 ../ 與路徑字元）
    for i, bad in enumerate(
        [
            "../skills/instruction-writing",
            "instruction-writing/SKILL.md",
            "has space",
            "Upper-Case",
        ]
    ):
        with pytest.raises(da.RuleMetaError):
            da.read_rule_meta(
                _marker_rule(
                    tmp_path,
                    f"bad{i}.md",
                    bundle_projection="pointer",
                    pointer_target=bad,
                    bootstrap_pointer='"x"',
                )
            )
    ok = da.read_rule_meta(
        _marker_rule(
            tmp_path,
            "ok.md",
            bundle_projection="pointer",
            pointer_target="instruction-writing",
            bootstrap_pointer='"x"',
        )
    )
    assert ok.pointer_target == "instruction-writing"


def test_contradiction_scoped_rule_with_projection_fails(tmp_path):
    # 矛盾組合 hard fail（S4）：claude-specific / meta 帶任一 projection 鍵
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(
                tmp_path,
                "cs.md",
                scope="claude-specific",
                bundle_projection="pointer",
                pointer_target="iw",
                bootstrap_pointer='"x"',
            )
        )
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(tmp_path, "meta.md", scope="meta", bundle_projection="full")
        )
    # 孤兒鍵也屬 projection 軸——scoped 檔同樣禁帶
    with pytest.raises(da.RuleMetaError):
        da.read_rule_meta(
            _marker_rule(tmp_path, "meta-orphan.md", scope="meta", pointer_target="iw")
        )


def test_existing_rules_without_marker_parse_unchanged(tmp_path):
    # 無 marker 既有 rule：全預設、read_scope 行為不變（S5 解析面回歸）
    p = tmp_path / "legacy.md"
    p.write_text("# no frontmatter\nbody\n", encoding="utf-8")
    meta = da.read_rule_meta(p)
    assert meta.scope == "neutral"
    assert meta.projection == "full"
    assert meta.pointer_target is None
    assert meta.bootstrap_pointer is None
    assert da.read_scope(p) == "neutral"


def test_read_scope_wrapper_delegates_with_marker(tmp_path):
    # compatibility wrapper：帶 marker 檔的 scope 軸照常回傳（既有 caller API 不變）
    p = _marker_rule(
        tmp_path,
        "iw.md",
        bundle_projection="pointer",
        pointer_target="instruction-writing",
        bootstrap_pointer='"x"',
    )
    assert da.read_scope(p) == "neutral"


# ---------------------------------------------------------------------------
# project_rule_for_bundle / check_pointer_preflight / build_bundle 投影＋
# main() 全域 preflight（AIR-85 段 2：投影機制＋全域 preflight）
#
# 契約二：projection validation 是全域 preflight——現行 main() 是 per-target
# 獨立 build/deploy（partial deploy 是既有設計）；pointer 三驗必須在任何
# target write 之前全域跑完，dry-run 與真跑共用（否則假驗收）。
# ---------------------------------------------------------------------------


def _pointer_rule(
    tmp_path,
    name: str = "iw.md",
    target: str = "instruction-writing",
    pointer: str = '"先載入 instruction-writing skill"',
):
    return _marker_rule(
        tmp_path,
        name,
        bundle_projection="pointer",
        pointer_target=target,
        bootstrap_pointer=pointer,
    )


def _meta(projection="full", target=None, pointer=None):
    """手建 RuleMeta（繞過解析；供 preflight 防禦層單元測試）。"""
    return da.RuleMeta(
        scope="neutral",
        projection=projection,
        pointer_target=target,
        bootstrap_pointer=pointer,
    )


def _patch_deploy_env(
    tmp_path, monkeypatch, skill_source: bool = True, runtime: bool = True
):
    """隔離部署環境：tmp rules／tmp repo skills／tmp home（~/.agents runtime）。"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "RULES_DIR", rules_dir)
    monkeypatch.setattr(da, "GUIDE", guide)
    monkeypatch.setattr(da, "SKILLS_DIR", tmp_path / "skills")
    home = tmp_path / "home"
    home.mkdir()
    if skill_source:
        d = tmp_path / "skills" / "instruction-writing"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("skill source\n", encoding="utf-8")
    if runtime:
        d = home / ".agents" / "skills" / "instruction-writing"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("runtime skill\n", encoding="utf-8")
    monkeypatch.setattr(da.pathlib.Path, "home", lambda: home)
    return home, rules_dir


def _iw_pointer_rule(rules_dir):
    p = rules_dir / "iw.md"
    p.write_text(
        "---\nharness-scope: neutral\n"
        "bundle-projection: pointer\n"
        "pointer-target: instruction-writing\n"
        'bootstrap-pointer: "先載入 instruction-writing skill"\n---\n'
        "# on-demand body\n",
        encoding="utf-8",
    )
    return p


# --- project_rule_for_bundle：單一 rule 的 bundle 投影（純函數）-------------


def test_project_rule_full_mode_equals_slim_for_bundle(tmp_path):
    # full mode → 既有 slim_for_bundle() 行為（含 skip marker 處理）；輸入＝
    # 全檔內容（frontmatter 照舊原樣 ship——與既有 bundle 行為 byte-identical）
    p = _rule(
        tmp_path,
        "plain.md",
        "neutral",
        "a\n<!-- bundle: skip-start -->\nsecret\n<!-- bundle: skip-end -->\nb\n",
    )
    meta = da.read_rule_meta(p)
    assert da.project_rule_for_bundle(p, meta) == da.slim_for_bundle(
        p.read_text(encoding="utf-8"), "plain.md"
    )


def test_project_rule_pointer_mode_annotation_and_verbatim_pointer(tmp_path):
    # pointer mode → 投影註解標頭＋bootstrap-pointer 逐字；無 frontmatter/body 殘留
    p = _pointer_rule(tmp_path)
    meta = da.read_rule_meta(p)
    out = da.project_rule_for_bundle(p, meta)
    assert meta.bootstrap_pointer in out.splitlines()  # 逐字、獨立一行
    assert f"skill `{meta.pointer_target}`" in out  # 註解標頭指名 skill
    assert "harness-scope" not in out  # 無 frontmatter 殘留
    assert "pointer-target" not in out
    assert "bundle-projection" not in out
    assert "---" not in out  # 無 frontmatter fence
    assert "# body" not in out  # 無 body 殘留


# --- check_pointer_preflight：三驗（source／pointer 行／runtime 可達）-------


def test_preflight_pass_when_source_and_runtime_present(tmp_path):
    skills = tmp_path / "repo-skills"
    (skills / "instruction-writing").mkdir(parents=True)
    (skills / "instruction-writing" / "SKILL.md").write_text("s", encoding="utf-8")
    home = tmp_path / "home"
    (home / ".agents" / "skills" / "instruction-writing").mkdir(parents=True)
    (home / ".agents" / "skills" / "instruction-writing" / "SKILL.md").write_text(
        "r", encoding="utf-8"
    )
    rules = [
        (
            pathlib.Path("iw.md"),
            _meta("pointer", "instruction-writing", "先載入 instruction-writing skill"),
        )
    ]
    assert da.check_pointer_preflight(rules, skills, home) == []


def test_preflight_fails_missing_repo_skill_source(tmp_path):
    # 驗一：repo skills/<target>/SKILL.md 不存在 → fail（runtime 在場仍 fail）
    home = tmp_path / "home"
    (home / ".agents" / "skills" / "iw").mkdir(parents=True)
    (home / ".agents" / "skills" / "iw" / "SKILL.md").write_text("r", encoding="utf-8")
    rules = [(pathlib.Path("iw.md"), _meta("pointer", "iw", "p"))]
    failures = da.check_pointer_preflight(rules, tmp_path / "repo-skills", home)
    assert len(failures) == 1
    assert "iw.md" in failures[0]
    assert "source" in failures[0]


def test_preflight_fails_missing_runtime_skill(tmp_path):
    # 驗三：~/.agents/skills/<target>/SKILL.md（non-CC canonical root）不可達 → fail
    skills = tmp_path / "repo-skills"
    (skills / "iw").mkdir(parents=True)
    (skills / "iw" / "SKILL.md").write_text("s", encoding="utf-8")
    rules = [(pathlib.Path("iw.md"), _meta("pointer", "iw", "p"))]
    failures = da.check_pointer_preflight(rules, skills, tmp_path / "home")
    assert len(failures) == 1
    assert "runtime" in failures[0]


def test_preflight_fails_empty_pointer_line(tmp_path):
    # 驗二：pointer 行在場（bootstrap-pointer 非空）——解析期已擋一次（S3），
    # 此為 preflight 防禦層：手建空 pointer meta 直接驗
    rules = [(pathlib.Path("iw.md"), _meta("pointer", "iw", ""))]
    failures = da.check_pointer_preflight(rules, tmp_path, tmp_path)
    assert any("bootstrap-pointer" in f for f in failures)


def test_preflight_ignores_full_mode_rules(tmp_path):
    # preflight 只管 pointer rule；full mode rule 不觸發任何存在性要求
    rules = [(pathlib.Path("plain.md"), _meta())]
    assert da.check_pointer_preflight(
        rules, tmp_path / "none", tmp_path / "nohome"
    ) == ([])


# --- build_bundle：投影先發生、再計 bytes（S9）；無 marker byte-identical（S5）


def test_build_bundle_projects_pointer_rule(tmp_path, monkeypatch):
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)
    p = _pointer_rule(tmp_path)
    meta = da.read_rule_meta(p)
    bundle = da.build_bundle([p], "neutral")
    assert f"<!-- rules/{p.name} -->" in bundle  # 章節分隔不變
    assert meta.bootstrap_pointer in bundle.splitlines()  # pointer 句逐字
    assert f"skill `{meta.pointer_target}`" in bundle  # 投影註解標頭
    assert "harness-scope" not in bundle  # 無 frontmatter 殘留
    assert "# body" not in bundle  # 無 body 殘留
    assert bundle.count(da.BUNDLE_END_SENTINEL) == 1


def test_build_bundle_without_marker_byte_identical(tmp_path, monkeypatch):
    # S5：無 marker rule 的 bundle 與舊演算法（slim_for_bundle 展開）逐 byte 相同
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)
    a = _rule(tmp_path, "a.md", "neutral", "# a\n")
    b = _rule(
        tmp_path,
        "b.md",
        "neutral",
        "head\n<!-- bundle: skip-start -->\nsecret\n<!-- bundle: skip-end -->\ntail\n",
    )
    got = da.build_bundle([a, b], "neutral")
    parts = [
        da.HEADER.format(scopes="neutral"),
        guide.read_text(encoding="utf-8").strip(),
        "",
    ]
    for p in (a, b):
        parts.append(f"\n---\n<!-- rules/{p.name} -->\n")
        parts.append(da.slim_for_bundle(p.read_text(encoding="utf-8"), p.name).strip())
        parts.append("")
    parts.append(da.BUNDLE_END_SENTINEL)
    assert got == "\n".join(parts)


def test_size_gate_consumes_projected_bytes(tmp_path, monkeypatch):
    # S9：projection 先發生、再計 bundle bytes/size gate——巨量 body 經 pointer
    # 投影後遠低於 muse gate（若 gate 吃投影前 bytes 此測試必 fail）
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)
    p = tmp_path / "iw.md"
    p.write_text(
        "---\nharness-scope: neutral\n"
        "bundle-projection: pointer\npointer-target: iw\n"
        'bootstrap-pointer: "先載入 iw skill"\n---\n'
        + "x" * (da.MUSE_USER_BUDGET * 2)
        + "\n",
        encoding="utf-8",
    )
    bundle = da.build_bundle([p], "neutral")
    bundle_bytes = len(bundle.encode("utf-8"))
    assert bundle_bytes < da.MUSE_USER_BUDGET  # 投影後才進 gate
    muse = {t.label: t for t in da.resolve_targets(tmp_path)}["muse"]
    assert da.check_size_gate(bundle_bytes, muse) is None


# --- main()：全域 preflight 接線（任何 target write 前；dry-run 共用）-------


def test_main_deploys_pointer_projection_all_targets(tmp_path, monkeypatch):
    # S1 整合：合法 pointer rule → 三端寫出投影內容（header＋pointer、無殘留）
    home, rules_dir = _patch_deploy_env(tmp_path, monkeypatch)
    _iw_pointer_rule(rules_dir)
    _rule(rules_dir, "plain.md", "neutral", "# plain rule\n")
    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() == 0
    for rel in (".zcode/AGENTS.md", ".codex/AGENTS.md", ".config/muse/AGENTS.md"):
        assert (home / rel).exists(), rel
    bundle = (home / ".zcode" / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- rules/iw.md -->" in bundle
    # 殘留斷言限縮在 pointer rule 的投影區段（同 bundle 的 full-mode rule
    # frontmatter 照舊原樣 ship，屬既有行為）
    section = bundle.split("<!-- rules/iw.md -->\n", 1)[1].split("\n---\n", 1)[0]
    assert "先載入 instruction-writing skill" in section.splitlines()  # 逐字 pointer 行
    assert "harness-scope" not in section
    assert "# on-demand body" not in section
    assert "# plain rule" in bundle  # 無 marker rule 照常 full
    assert bundle.rstrip().endswith(da.BUNDLE_END_SENTINEL)


def test_main_preflight_failure_zero_target_writes(tmp_path, monkeypatch, capsys):
    # S2：target skill source 不存在 → 整體 exit≠0，任何端都未寫出
    home, rules_dir = _patch_deploy_env(tmp_path, monkeypatch, skill_source=False)
    _iw_pointer_rule(rules_dir)
    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() == 1
    for rel in (".zcode", ".codex", ".config"):
        assert not (home / rel).exists(), rel
    assert not list(home.rglob("AGENTS.md*"))
    err = capsys.readouterr().err
    assert "[FAIL]" in err and "preflight" in err


def test_dry_run_and_real_run_share_preflight(tmp_path, monkeypatch, capsys):
    # S7：同一 invalid marker，--dry-run 與真跑同 exit≠0（共用 preflight，
    # 不存在 dry-run 綠真跑 fail 的假驗收）；兩者皆零 target 寫出
    home, rules_dir = _patch_deploy_env(
        tmp_path, monkeypatch, skill_source=False, runtime=False
    )
    _iw_pointer_rule(rules_dir)
    for argv in (["deploy_agents.py", "--dry-run"], ["deploy_agents.py"]):
        monkeypatch.setattr(sys, "argv", argv)
        assert da.main() == 1, argv
        for rel in (".zcode", ".codex", ".config"):
            assert not (home / rel).exists(), (argv, rel)
        assert "preflight" in capsys.readouterr().err


def test_main_rule_meta_error_readable_not_traceback(tmp_path, monkeypatch, capsys):
    # discover_rules 冒泡 RuleMetaError（schema typo）→ 可判讀 [FAIL]，非裸 traceback
    home, rules_dir = _patch_deploy_env(tmp_path, monkeypatch)
    _marker_rule(
        rules_dir,
        "bad.md",
        bundle_projection="poitner",
        pointer_target="iw",
        bootstrap_pointer='"x"',
    )
    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() == 1
    err = capsys.readouterr().err
    assert "bad.md" in err
    assert "unknown bundle-projection" in err
    assert "Traceback" not in err
    assert not (home / ".zcode").exists()  # fail 在任何 target write 之前
