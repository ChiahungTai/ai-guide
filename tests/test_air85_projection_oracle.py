"""AIR-85 conditional-loading vertical-slice independent contract oracle.

Contract source:
- ai-analysis/_tasks/09-13-conditional-loading-vertical-slice/ep.md:31-61
- ai-analysis/_tasks/09-13-conditional-loading-vertical-slice/ep.md:76-79
- ai-analysis/_tasks/09-13-conditional-loading-vertical-slice/ep.md:93-116

This file intentionally tests observable contracts rather than mirroring the
current deploy_agents.py implementation.
"""

from __future__ import annotations

import os
import pathlib
import sys

import pytest
from conftest import load_module

da = load_module("scripts/deploy_agents.py")


POINTER = (
    "新增或修改 AGENTS.md、rules 或 SKILL.md 等 instruction 檔前（legacy CLAUDE.md 亦然），"
    "先載入 `instruction-writing` skill；frontmatter、載體選擇、引用、"
    "Signal/Noise 與自洽檢查以該 skill 為準。"
)


def _rule(
    directory: pathlib.Path,
    name: str,
    *,
    scope: str = "neutral",
    body: str = "# FULL_BODY\n",
) -> pathlib.Path:
    path = directory / name
    path.write_text(
        f"---\nharness-scope: {scope}\n---\n{body}",
        encoding="utf-8",
    )
    return path


def _pointer_rule(
    directory: pathlib.Path,
    name: str = "instruction-writing.md",
    *,
    target: str = "instruction-writing",
    pointer: str = POINTER,
    body: str = "# ON_DEMAND_BODY_MUST_NOT_SHIP\n",
) -> pathlib.Path:
    path = directory / name
    path.write_text(
        "---\n"
        "harness-scope: neutral\n"
        "paths:\n"
        '  - "**/*.md"\n'
        "bundle-projection: pointer\n"
        f"pointer-target: {target}\n"
        f'bootstrap-pointer: "{pointer}"\n'
        "---\n"
        f"{body}",
        encoding="utf-8",
    )
    return path


def _bad_projection_rule(directory: pathlib.Path) -> pathlib.Path:
    path = directory / "bad-projection.md"
    path.write_text(
        "---\n"
        "harness-scope: neutral\n"
        "bundle-projection: poitner\n"
        "pointer-target: instruction-writing\n"
        'bootstrap-pointer: "x"\n'
        "---\n"
        "# body\n",
        encoding="utf-8",
    )
    return path


def _deploy_targets(home: pathlib.Path) -> list[pathlib.Path]:
    return [target.path for target in da.resolve_targets(home)]


def _patch_env(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    skill_source: bool = True,
    runtime_skill: bool = True,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Create an isolated repo/home without pre-creating deploy target dirs."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")

    skills_dir = tmp_path / "skills"
    home = tmp_path / "home"
    home.mkdir()

    monkeypatch.setattr(da, "RULES_DIR", rules_dir)
    monkeypatch.setattr(da, "GUIDE", guide)
    monkeypatch.setattr(da, "SKILLS_DIR", skills_dir)
    monkeypatch.setattr(da.pathlib.Path, "home", lambda: home)

    if skill_source:
        source = skills_dir / "instruction-writing"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text(
            "---\nname: instruction-writing\ndescription: test skill\n---\n# skill\n",
            encoding="utf-8",
        )

    if runtime_skill:
        runtime = home / ".agents" / "skills" / "instruction-writing"
        runtime.mkdir(parents=True)
        (runtime / "SKILL.md").write_text("runtime skill\n", encoding="utf-8")

    return home, rules_dir


def _section(bundle: str, rule_name: str) -> str:
    """Return only one projected rule section, excluding bundle provenance/sentinel."""
    marker = f"<!-- rules/{rule_name} -->\n"
    assert marker in bundle
    tail = bundle.split(marker, 1)[1]

    if "\n---\n<!-- rules/" in tail:
        tail = tail.split("\n---\n<!-- rules/", 1)[0]
    elif da.BUNDLE_END_SENTINEL in tail:
        tail = tail.split(da.BUNDLE_END_SENTINEL, 1)[0]

    return tail.strip()


# ---------------------------------------------------------------------------
# Projection semantics
# ---------------------------------------------------------------------------


def test_pointer_projection_is_exact_author_line_only(tmp_path, monkeypatch):
    """〔EP:52,61; S1:97〕作者句逐字 materialize；body/frontmatter 不 ship."""
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)

    rule = _pointer_rule(tmp_path)
    meta = da.read_rule_meta(rule)

    # parse-time symmetric YAML quote stripping is observable here:
    assert meta.bootstrap_pointer == POINTER

    bundle = da.build_bundle([rule], "neutral")
    projected = _section(bundle, rule.name)

    # EP 段 2 contract（09-13 oracle 裁決後明定）：pointer projection =
    # 凍結模板 provenance 註解（逐字，deploy 不得加減一字）＋作者 pointer 行。
    # 模板在此 hard-code（非引用實作常數）——實作改模板即紅。
    annotation = (
        "<!-- pointer projection: on-demand body not shipped in this bundle; "
        "full text -> skill `instruction-writing` (load the skill when triggered) -->"
    )
    assert projected == f"{annotation}\n{POINTER}"

    for forbidden in (
        "---",
        "harness-scope:",
        "paths:",
        "bundle-projection:",
        "pointer-target:",
        "bootstrap-pointer:",
        "ON_DEMAND_BODY_MUST_NOT_SHIP",
    ):
        assert forbidden not in projected


def test_pointer_projection_is_generic_not_instruction_writing_special_case(
    tmp_path, monkeypatch
):
    """〔EP:52; 已決策 #6:114〕第二支 pilot 必須走同一介面，零 filename special case."""
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)

    pointer = "先載入 `llm-output-convention` skill，再處理 Agent output。"
    rule = _pointer_rule(
        tmp_path,
        "llm-output-convention.md",
        target="llm-output-convention",
        pointer=pointer,
    )

    bundle = da.build_bundle([rule], "neutral")
    annotation = (
        "<!-- pointer projection: on-demand body not shipped in this bundle; "
        "full text -> skill `llm-output-convention` (load the skill when triggered) -->"
    )
    assert _section(bundle, rule.name) == f"{annotation}\n{pointer}"


def test_full_projection_preserves_existing_slim_semantics(tmp_path):
    """〔EP:52; S5:101〕無 pointer marker 時不得改既有 full-mode payload."""
    rule = _rule(
        tmp_path,
        "plain.md",
        body=(
            "head\n"
            "<!-- bundle: skip-start -->\n"
            "drop-me\n"
            "<!-- bundle: skip-end -->\n"
            "tail\n"
        ),
    )
    meta = da.read_rule_meta(rule)

    expected = da.slim_for_bundle(rule.read_text(encoding="utf-8"), rule.name)
    assert da.project_rule_for_bundle(rule, meta) == expected


def test_read_scope_wrapper_remains_backward_compatible_with_pointer_rule(tmp_path):
    """〔EP:43,45; 已決策 #6:114〕read_scope() public compatibility surface survives."""
    rule = _pointer_rule(tmp_path)

    assert da.read_scope(rule) == "neutral"
    assert da.read_rule_meta(rule).scope == "neutral"


# ---------------------------------------------------------------------------
# Preflight semantics
# ---------------------------------------------------------------------------


def test_preflight_runtime_contract_is_agents_root_not_zcode_root(tmp_path):
    """〔EP:53-57,111〕runtime reachability contract is ~/.agents/skills exactly."""
    skills = tmp_path / "skills"
    source = skills / "instruction-writing"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("source\n", encoding="utf-8")

    home = tmp_path / "home"

    # Deliberately provide only ~/.zcode/skills. If this passes, the
    # implementation weakened/changed the frozen AIR-85 reachability contract.
    zcode_only = home / ".zcode" / "skills" / "instruction-writing"
    zcode_only.mkdir(parents=True)
    (zcode_only / "SKILL.md").write_text("runtime\n", encoding="utf-8")

    meta = da.RuleMeta(
        scope="neutral",
        projection="pointer",
        pointer_target="instruction-writing",
        bootstrap_pointer=POINTER,
    )
    failures = da.check_pointer_preflight(
        [(pathlib.Path("instruction-writing.md"), meta)],
        skills,
        home,
    )

    assert failures
    assert any(".agents" in failure and "runtime" in failure for failure in failures)


def test_preflight_defensively_rejects_whitespace_pointer_even_if_parser_bypassed(
    tmp_path,
):
    """〔EP:53-57〕preflight repeats non-empty pointer invariant fail-closed."""
    meta = da.RuleMeta(
        scope="neutral",
        projection="pointer",
        pointer_target="instruction-writing",
        bootstrap_pointer="   ",
    )

    failures = da.check_pointer_preflight(
        [(pathlib.Path("instruction-writing.md"), meta)],
        tmp_path / "skills",
        tmp_path / "home",
    )

    assert any("bootstrap-pointer" in failure for failure in failures)


def test_missing_skill_source_aborts_before_any_target_path_is_created(
    tmp_path, monkeypatch, capsys
):
    """〔EP:49,53-57,61; S2:98〕preflight fail => all three targets literally absent."""
    home, rules_dir = _patch_env(
        tmp_path,
        monkeypatch,
        skill_source=False,
        runtime_skill=True,
    )
    _pointer_rule(rules_dir)

    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() != 0

    for target in _deploy_targets(home):
        assert not target.exists()
        assert not target.parent.exists()

    # No staged/backup deployment artifacts either.
    assert not list(home.rglob("AGENTS.md"))
    assert not list(home.rglob("AGENTS.md.tmp"))
    assert not list(home.rglob("AGENTS.md.bak"))

    err = capsys.readouterr().err
    assert "[FAIL]" in err
    assert "preflight" in err.lower()


def test_missing_runtime_preflight_does_not_touch_preexisting_targets(
    tmp_path, monkeypatch
):
    """〔EP:49,53-57〕global preflight protects existing targets as well as absent ones."""
    home, rules_dir = _patch_env(
        tmp_path,
        monkeypatch,
        skill_source=True,
        runtime_skill=False,
    )
    _pointer_rule(rules_dir)

    expected: dict[pathlib.Path, tuple[str, int]] = {}
    frozen_mtime = 1_700_000_000_000_000_000

    for index, target in enumerate(_deploy_targets(home)):
        target.parent.mkdir(parents=True, exist_ok=True)
        content = f"OLD-{index}\n"
        target.write_text(content, encoding="utf-8")
        os.utime(target, ns=(frozen_mtime, frozen_mtime))
        expected[target] = (content, target.stat().st_mtime_ns)

    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() != 0

    for target, (content, mtime_ns) in expected.items():
        assert target.read_text(encoding="utf-8") == content
        assert target.stat().st_mtime_ns == mtime_ns
        assert not target.with_name(target.name + ".tmp").exists()


def test_dry_run_and_real_run_share_identical_invalid_preflight(
    tmp_path, monkeypatch, capsys
):
    """〔EP:53,61; S7:103〕dry-run cannot green an input that real deploy rejects."""
    home, rules_dir = _patch_env(
        tmp_path,
        monkeypatch,
        skill_source=False,
        runtime_skill=False,
    )
    _pointer_rule(rules_dir)

    for argv in (
        ["deploy_agents.py", "--dry-run"],
        ["deploy_agents.py"],
    ):
        monkeypatch.setattr(sys, "argv", argv)
        assert da.main() != 0

        for target in _deploy_targets(home):
            assert not target.exists()
            assert not target.parent.exists()

        err = capsys.readouterr().err
        assert "[FAIL]" in err
        assert "preflight" in err.lower()


def test_preflight_failure_occurs_before_any_size_gate_evaluation(
    tmp_path, monkeypatch
):
    """〔EP:49,58〕ordering oracle: global preflight precedes per-target build/gate work."""
    _home, rules_dir = _patch_env(
        tmp_path,
        monkeypatch,
        skill_source=True,
        runtime_skill=False,
    )
    _pointer_rule(rules_dir, body="x" * (da.BUNDLE_MAX_BYTES * 2))

    gate_calls: list[tuple[int, str]] = []

    def should_not_run(bundle_bytes, target):
        gate_calls.append((bundle_bytes, target.label))

    monkeypatch.setattr(da, "check_size_gate", should_not_run)
    monkeypatch.setattr(sys, "argv", ["deploy_agents.py", "--dry-run"])

    assert da.main() != 0
    assert gate_calls == []


# ---------------------------------------------------------------------------
# Size-gate timing and deploy idempotency
# ---------------------------------------------------------------------------


def test_main_size_gate_receives_projected_not_source_bytes(tmp_path, monkeypatch):
    """〔EP:58,61; S9:105〕prove timing at main wiring, not only pure build_bundle."""
    _home, rules_dir = _patch_env(tmp_path, monkeypatch)

    huge_body = "X" * (da.BUNDLE_MAX_BYTES * 3)
    rule = _pointer_rule(rules_dir, body=huge_body)
    raw_rule_bytes = len(rule.read_bytes())
    assert raw_rule_bytes > da.BUNDLE_MAX_BYTES

    real_gate = da.check_size_gate
    observed: list[tuple[str, int]] = []

    def recording_gate(bundle_bytes, target):
        observed.append((target.label, bundle_bytes))
        return real_gate(bundle_bytes, target)

    monkeypatch.setattr(da, "check_size_gate", recording_gate)
    monkeypatch.setattr(sys, "argv", ["deploy_agents.py", "--dry-run"])

    # If the gate sees raw/full source bytes this must fail, especially Muse.
    assert da.main() == 0

    assert {label for label, _ in observed} == {"zcode", "codex", "muse", "grok"}
    budgets = {t.label: t.max_bytes for t in da.resolve_targets(tmp_path)}
    assert all(bundle_bytes <= budgets[label] for label, bundle_bytes in observed)
    assert all(bundle_bytes < raw_rule_bytes for _, bundle_bytes in observed)


def test_second_identical_deploy_performs_zero_target_replacements_and_preserves_mtime(
    tmp_path, monkeypatch
):
    """〔EP:78〕idempotent rerun = same content + same mtime + zero target rewrite."""
    home, rules_dir = _patch_env(tmp_path, monkeypatch)
    _pointer_rule(rules_dir)
    _rule(rules_dir, "plain.md", body="# plain\n")

    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() == 0

    targets = _deploy_targets(home)
    frozen_mtime = 1_700_000_000_000_000_000
    expected: dict[pathlib.Path, tuple[str, int]] = {}

    for target in targets:
        content = target.read_text(encoding="utf-8")
        os.utime(target, ns=(frozen_mtime, frozen_mtime))
        expected[target] = (content, target.stat().st_mtime_ns)

    real_replace = da.os.replace
    replacements: list[tuple[pathlib.Path, pathlib.Path]] = []

    def recording_replace(src, dst):
        replacements.append((pathlib.Path(src), pathlib.Path(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(da.os, "replace", recording_replace)

    assert da.main() == 0

    # "Idempotent" here is the stronger EP:78 contract, not merely same bytes
    # after rewriting.
    assert replacements == []

    for target, (content, mtime_ns) in expected.items():
        assert target.read_text(encoding="utf-8") == content
        assert target.stat().st_mtime_ns == mtime_ns
        assert not target.with_name(target.name + ".tmp").exists()


# ---------------------------------------------------------------------------
# Operator-facing failure semantics
# ---------------------------------------------------------------------------


def test_rule_meta_error_is_operator_readable_without_traceback_or_writes(
    tmp_path, monkeypatch, capsys
):
    """〔EP:41-45; S8:104〕schema error is a readable fail-closed CLI result."""
    home, rules_dir = _patch_env(tmp_path, monkeypatch)
    _bad_projection_rule(rules_dir)

    monkeypatch.setattr(sys, "argv", ["deploy_agents.py"])
    assert da.main() != 0

    captured = capsys.readouterr()
    combined = captured.out + captured.err

    assert "[FAIL]" in combined
    assert "bad-projection.md" in combined
    assert "bundle-projection" in combined
    assert "poitner" in combined
    assert "Traceback" not in combined

    for target in _deploy_targets(home):
        assert not target.exists()
        assert not target.parent.exists()


def test_no_marker_bundle_is_byte_identical_to_pre_air85_assembly(
    tmp_path, monkeypatch
):
    """〔EP:61; S5:101〕projection feature is a strict no-op for legacy full rules."""
    guide = tmp_path / "guide.md"
    guide.write_text("GUIDE\n", encoding="utf-8")
    monkeypatch.setattr(da, "GUIDE", guide)

    rules = [
        _rule(tmp_path, "a.md", body="# A\n"),
        _rule(
            tmp_path,
            "b.md",
            body=(
                "before\n"
                "<!-- bundle: skip-start -->\n"
                "hidden\n"
                "<!-- bundle: skip-end -->\n"
                "after\n"
            ),
        ),
    ]

    got = da.build_bundle(rules, "neutral")

    # Reconstruct the old pre-projection assembly directly from the frozen
    # legacy operations, rather than calling project_rule_for_bundle().
    parts = [
        da.HEADER.format(scopes="neutral"),
        guide.read_text(encoding="utf-8").strip(),
        "",
    ]
    for rule in rules:
        parts.append(f"\n---\n<!-- rules/{rule.name} -->\n")
        parts.append(
            da.slim_for_bundle(
                rule.read_text(encoding="utf-8"),
                rule.name,
            ).strip()
        )
        parts.append("")
    parts.append(da.BUNDLE_END_SENTINEL)

    assert got == "\n".join(parts)
