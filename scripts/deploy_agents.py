#!/usr/bin/env python3
"""
Deploy bundled AGENTS.md to non-Claude harnesses.

Bundles ai-development-guide.md (guide) + rules with matching harness-scope
frontmatter -> writes to ~/.zcode/AGENTS.md, ~/.codex/AGENTS.md,
~/.config/muse/AGENTS.md (muse machine-wide user rules
path — probe-verified 2026-09-07; loads unconditionally, project AGENTS.md
wins on conflict).

Claude (~/.claude/CLAUDE.md) is NOT touched -- it stays symlink to the
slim guide; Claude gets rules via ~/.claude/rules/ auto-load.

Rule classification is auto-discovered from per-rule frontmatter:
    ---
    harness-scope: neutral
    ---
Scopes: neutral | claude-specific | meta

Bundle projection axis (AIR-85): neutral rules may opt into pointer projection
with `bundle-projection: pointer` + `pointer-target: <skill-id slug>` +
`bootstrap-pointer: "<trigger sentence>"`; parse-time schema violations fail
closed (read_rule_meta). deploy never parses `paths:` -- that is the Claude
runtime axis, structurally isolated from bundle projection.

Pointer rules project to an annotation header + the verbatim bootstrap line
(project_rule_for_bundle); a global preflight (check_pointer_preflight: repo
skill source exists, pointer line present, ~/.agents runtime reachable) runs
once before ANY target write -- dry-run and real deploy share it, and any
failure aborts with exit 1 and zero targets written.

Default bundles 'neutral'. New rules without an explicit harness-scope
default to 'neutral' (generic knowledge defaults to cross-harness). Rules
that are Claude-specific must declare `harness-scope: claude-specific`
explicitly to be excluded from the bundle.

Broken-ref guard: scans every neutral rule's markdown links; if a neutral
rule links to a claude-specific rule, the deploy aborts with an error
listing each broken ref. This forces fixing the ref (or re-scoping the
target) before the bundle ships -- non-Claude readers would otherwise hit
a dead link. Parenthetical Claude notes `(Claude: ...)` are exempt, since
those are Claude-side pointers that non-Claude readers can ignore.

Bundle slimming: rule bodies may mark sections to drop from the bundle with
    <!-- bundle: skip-start --> ... <!-- bundle: skip-end -->
Claude reads the full file via ~/.claude/rules/ symlink; non-Claude bundles
get the slimmed version. No-op for rules without markers.

Size gate: ZCode truncates each instruction file at 102,400 bytes;
Muse delegation startup shares 65,536 bytes across global/project rules
and loader framing. Each target has a global-bundle gate; this does not
replace checking the actual workspace's combined startup context.
Over the target limit -> refuse that deployment with
guidance: slim rules/ (encoder-philosophy) or demote on-demand-grade
content to a reference skill (rule keeps an always-on core + pointer).
Precedents: acceptance-evidence / symbol-query-routing / instruction-writing
rule+skill pairs.

Run after editing rules/ (deploy discipline in rules/AGENTS.md). Idempotent.
"""

import argparse
import dataclasses
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
GUIDE = REPO / "ai-development-guide.md"
RULES_DIR = REPO / "rules"
SKILLS_DIR = REPO / "skills"  # pointer preflight 驗一：repo skill source


@dataclasses.dataclass(frozen=True)
class DeployTarget:
    """單端部署配置：路徑＋scope＋排除＋獨立 size gate。"""

    path: pathlib.Path
    scopes: frozenset
    exclude: frozenset
    max_bytes: int
    label: str


VARIANT_LABEL_SUFFIX = ",filtered"


def scopes_label_for(scopes: frozenset, exclude: frozenset) -> str:
    """scopes → bundle label；exclude 非空＝變體後綴。bundle_for 與 main() 的單一組裝點。"""
    label = ",".join(sorted(scopes))
    if exclude:
        label += VARIANT_LABEL_SUFFIX
    return label


def bundle_for(target: DeployTarget) -> str:
    """該 target 的預期 bundle（label 語義與 main() 一致；freshness check 消費）。"""
    return build_bundle(
        discover_rules(RULES_DIR, target.scopes),
        scopes_label_for(target.scopes, target.exclude),
        target.exclude,
    )


def expected_bundle_for(target_path) -> bytes:
    """部署路徑 → 預期 bytes；未知路徑 KeyError。供 check_single_source 消費。"""
    for target in resolve_targets(pathlib.Path.home()):
        if target.path == pathlib.Path(target_path):
            return bundle_for(target).encode("utf-8")
    raise KeyError(f"unknown deploy target: {target_path}")


def resolve_targets(home: pathlib.Path) -> list[DeployTarget]:
    """三端皆保留 neutral 核心；Muse 為 project instructions 留出空間。"""
    return [
        DeployTarget(
            home / ".zcode" / "AGENTS.md",
            frozenset({"neutral"}),
            frozenset(),
            BUNDLE_MAX_BYTES,
            "zcode",
        ),
        DeployTarget(
            home / ".codex" / "AGENTS.md",
            frozenset({"neutral"}),
            frozenset(),
            BUNDLE_MAX_BYTES,
            "codex",
        ),
        DeployTarget(
            home / ".config" / "muse" / "AGENTS.md",
            frozenset({"neutral"}),
            frozenset(),
            MUSE_USER_BUDGET,  # user 層自限；合併專案指令仍須驗 64KiB startup limit。
            "muse",
        ),
    ]


# ZCode truncates a single instruction file at 100KiB (102,400 bytes,
# hardcoded; Codex limit covered by project_doc_max_bytes knob, set to
# 102400 on 2026-09-08). Keep the bundle under 90KiB
# so tail rules never land in the silent-truncation zone.
BUNDLE_MAX_BYTES = 90 * 1024

# Muse startup shares 64KiB across global+project rules and loader framing;
# the global bundle self-limits to 36KiB so a project layer (mosaic: ~24.1KiB)
# + framing (~0.8KiB) stays under the shared line with ~3KiB buffer.
# Broke once at 40,092B (2026-09-09, tail rules silently truncated) before
# this budget existed.
MUSE_USER_BUDGET = 36 * 1024

# Early-warning threshold (fraction of BUNDLE_MAX_BYTES). Deploy-time visibility
# only -- the weekly bundle-watch advisory owns per-rule composition analysis
# and slimming candidates; this WARN just prevents "gate abort" being the
# first signal.
BUNDLE_WARN_RATIO = 0.85

# Appended as the bundle's last line; a deployed file whose tail lacks it was
# cut short (or hand-edited) -- load-time truncation is proven by size gate.
BUNDLE_END_SENTINEL = "<!-- bundle-end -->"

TARGETS = [t.path for t in resolve_targets(pathlib.Path.home())]

# Matches <!-- bundle: skip-start --> ... <!-- bundle: skip-end --> (incl. the
# trailing newline) so adjacent sections join cleanly. Non-greedy + DOTALL.
SKIP_PATTERN = re.compile(
    r"<!-- bundle: skip-start -->.*?<!-- bundle: skip-end -->\n?",
    flags=re.DOTALL,
)

HEADER = (
    "<!-- Generated by scripts/deploy_agents.py -- do not edit directly.\n"
    "     Source: ai-guide/ai-development-guide.md + rules/<scope: {scopes}>\n"
    "     Regenerate: uv run python scripts/deploy_agents.py -->\n\n"
)


def read_scope(path: pathlib.Path) -> str:
    """Compatibility wrapper：harness-scope 軸（既有 caller/tests API 不變）。"""
    return read_rule_meta(path).scope


# --- projection metadata（AIR-85 三軸分離）--------------------------------
#
# harness-scope 是 scope 軸；paths: 是 CC runtime 軸（契約一：deploy 不解析）；
# bundle-projection 是 portable bundle 投影軸——作者顯式 opt-in 的 marker，
# deploy 只機械投影＋fail-closed（投影：project_rule_for_bundle；全域
# preflight：check_pointer_preflight）。

PROJECTION_MODES = ("full", "pointer")

# skill-id slug：小寫開頭＋小寫/數字/hyphen——禁 `../`、路徑字元、空白。
SKILL_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")

# Frontmatter 只消費 flat `key: value` 純量；list item／縮排續行（如 paths: 的
# `- "**/*.md"`）不是 flat 純量，不匹配即略過。
_FLAT_FRONTMATTER_KEY = re.compile(r"^([a-z][a-z0-9_-]*):(.*)$")


class RuleMetaError(ValueError):
    """rule frontmatter projection metadata 違反 schema invariant（解析期 fail-closed）。"""


@dataclasses.dataclass(frozen=True)
class RuleMeta:
    """單一 rule 的 deploy 可視 metadata（scope 軸＋projection 軸）。

    契約一：無 paths 欄位——paths: 是 CC runtime 軸，deploy 結構上不解析。
    """

    scope: str
    projection: str = "full"  # PROJECTION_MODES 之一；full body 為預設不標
    pointer_target: str | None = None
    bootstrap_pointer: str | None = None


def _frontmatter_fields(path: pathlib.Path) -> dict[str, str]:
    """Opening `---` fence 內的 flat `key: value` 純量（fence 外不算）。

    解析語義與舊 read_scope 一致：無 fence、fence 內無該鍵、或鍵值為空，
    皆由呼叫端以預設值兜底。
    """
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    fields: dict[str, str] = {}
    for line in content.split("\n")[1:]:
        if line.strip() == "---":
            break
        match = _FLAT_FRONTMATTER_KEY.match(line.strip())
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def _unquote(value: str) -> str:
    """剝除一對對稱 YAML 引號（bootstrap-pointer 逐字 materialize 的前置）。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def read_rule_meta(path: pathlib.Path) -> RuleMeta:
    """解析 harness-scope＋projection metadata；invariant 違反即 raise RuleMetaError。

    Schema（flat keys）::

        bundle-projection: pointer   # 唯一 projection 語義值；full 為預設不標
        pointer-target: <skill-id slug>
        bootstrap-pointer: "<作者明寫 trigger 句>"

    四 invariant（解析期 fail-closed）：
        1. pointer mode → target/pointer 必須齊備且非空
        2. 未知 projection 值 → fail
        3. 非 pointer mode 卻帶 target/pointer 孤兒鍵 → fail
        4. pointer-target 非 skill-id slug → fail
    矛盾組合 hard fail：claude-specific / meta 帶任一 projection 鍵——
    typo 不得靜默變 deployment semantics。
    """
    fields = _frontmatter_fields(path)
    scope = fields.get("harness-scope", "") or "neutral"

    mode_value = fields.get("bundle-projection")
    target_value = fields.get("pointer-target")
    pointer_value = fields.get("bootstrap-pointer")
    has_orphan = target_value is not None or pointer_value is not None

    if scope in ("claude-specific", "meta") and (mode_value is not None or has_orphan):
        raise RuleMetaError(
            f"{path.name}: harness-scope {scope!r} must not carry projection "
            "metadata (bundle-projection/pointer-target/bootstrap-pointer)"
        )

    mode = _unquote(mode_value) if mode_value is not None else "full"
    if mode not in PROJECTION_MODES:
        raise RuleMetaError(
            f"{path.name}: unknown bundle-projection value {mode_value!r} "
            f"(expected one of {list(PROJECTION_MODES)})"
        )

    if mode != "pointer":
        if has_orphan:
            raise RuleMetaError(
                f"{path.name}: pointer-target/bootstrap-pointer are orphans "
                f"under {mode!r} projection (only pointer mode consumes them)"
            )
        return RuleMeta(scope=scope, projection=mode)

    target = _unquote(target_value or "")
    pointer = _unquote(pointer_value or "")
    if not target or not pointer:
        raise RuleMetaError(
            f"{path.name}: bundle-projection pointer requires non-empty "
            "pointer-target and bootstrap-pointer"
        )
    if not SKILL_SLUG_PATTERN.match(target):
        raise RuleMetaError(
            f"{path.name}: pointer-target {target_value!r} is not a skill-id "
            "slug (lowercase [a-z0-9-], no path characters)"
        )
    return RuleMeta(
        scope=scope,
        projection="pointer",
        pointer_target=target,
        bootstrap_pointer=pointer,
    )


def discover_rules(
    rules_dir: pathlib.Path, target_scopes: set[str]
) -> list[pathlib.Path]:
    """Scan rules/*.md, return those whose harness-scope is in target_scopes."""
    rules = []
    for path in sorted(rules_dir.glob("*.md")):
        if read_scope(path) in target_scopes:
            rules.append(path)
    return rules


# Match `(Claude: ...)` parenthetical notes, supporting both ASCII `()`
# and full-width `（）` parens (CJK convention). Refs inside these are
# Claude-side pointers non-Claude readers can ignore, so they're stripped
# before scanning. Allows a single level of nested ASCII parens.
_OPEN = r"[\(（]"
_CLOSE = r"[\)）]"
_NOT_PAREN = r"[^()（）]"
CLAUDE_NOTE_PATTERN = re.compile(
    _OPEN
    + r"Claude[:：]"
    + _NOT_PAREN
    + r"*"
    + r"(?:\([^()]*\)"
    + _NOT_PAREN
    + r"*)*"
    + _CLOSE
)

# Markdown link `[text](target.md)` — capture target path.
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")

# Backtick-quoted bare rule ref like `` `rule-name.md` ``.
BACKTICK_REF_PATTERN = re.compile(r"`([a-z][a-z0-9_-]*\.md)`")


def scan_sources(rules_dir: pathlib.Path, include_guide: bool) -> list[tuple[str, str]]:
    """Bundle sources as (name, content) pairs, Claude notes stripped.

    Neutral rules always (purity scope per rules/AGENTS.md 機械檢查清單:
    rules/*.md only -- the guide legitimately mentions cross-harness bare
    slash commands like `/handoff`, so it must NOT enter the purity scan).
    Guide included only for broken-ref scanning (it ships in the bundle too).
    rules/AGENTS.md itself is meta-scoped and never enters the neutral set,
    so its self-referential examples cannot false-positive either scan.
    """
    sources = [
        (p.name, p.read_text(encoding="utf-8"))
        for p in discover_rules(rules_dir, {"neutral"})
    ]
    if include_guide and GUIDE.exists():
        sources.append((GUIDE.name, GUIDE.read_text(encoding="utf-8")))
    return [(name, CLAUDE_NOTE_PATTERN.sub("", content)) for name, content in sources]


def check_broken_refs(
    rules_dir: pathlib.Path,
) -> list[tuple[str, str, str]]:
    """Find bundle sources (neutral rules + guide) linking to claude-specific rules.

    Returns a list of (source_name, link_target, target_rule_name) tuples.
    Parenthetical Claude notes `(Claude: ...)` are exempt: their contents are
    stripped before scanning, so refs inside them don't count as broken.

    The scan scope is a global invariant -- it always checks neutral sources
    against claude-specific targets, regardless of what deploy is bundling.
    The guide is scanned since build_bundle ships it verbatim (a guide-side
    ref to a claude-specific file is just as dead for non-Claude readers).
    """
    claude_stems = {p.stem for p in discover_rules(rules_dir, {"claude-specific"})}

    broken: list[tuple[str, str, str]] = []
    for src_name, cleaned in scan_sources(rules_dir, include_guide=True):
        # Markdown links `[text](target.md)`.
        for _, link_target in LINK_PATTERN.findall(cleaned):
            stem = pathlib.Path(link_target).stem
            if stem in claude_stems:
                broken.append((src_name, link_target, stem))
        # Bare backtick refs `` `rule-name.md` ``.
        for match in BACKTICK_REF_PATTERN.finditer(cleaned):
            ref = match.group(1)
            stem = ref[:-3]  # strip ".md"
            if stem in claude_stems:
                broken.append((src_name, ref, stem))
    return broken


# Neutral-purity patterns -- the programmatic form of rules/AGENTS.md's
# 機械檢查清單 (which until 2026-08-30 existed only as prose commands nobody
# ran; two live violations had shipped to all three deployed bundles).
# 已知限制：(1) 掃描面 = 全文，build_bundle 的 slim skip 段不 ship 但仍被掃
# （repo 現無 marker；首個 skip marker 出現時重訪此差異）。(2) bare-slash
# pattern 與 checklist 的 rg 原文逐字等價（僅攔 backtick 形態）。(3)
# claude-wrapper 的豁免詞「Claude 端」為列舉制——寫「Claude Code」等其他
# 措辭會誤抓，屬可接受的 heuristic。
PURITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("bare-slash-command", re.compile(r"`/[a-z][a-z-]+[ `]")),
    ("at-transclusion", re.compile(r"@~/|@\.\./|@/[a-z]")),
    ("cross-domain-path", re.compile(r"\.\./(commands|skills)/")),
    ("abs-user-path", re.compile(r"~/Github/ai-guide/")),
]
CLAUDE_WRAPPER_PATTERN = re.compile(r"CLAUDE\.md wrapper")


def check_neutral_purity(rules_dir: pathlib.Path) -> list[tuple[str, str, str]]:
    """Find neutral-rule purity violations (rules/AGENTS.md 機械檢查清單).

    Returns a list of (rule_name, check_label, matched_text) tuples. Input is
    Claude-note-stripped, matching the checklist's 括號注 exemption.
    """
    violations: list[tuple[str, str, str]] = []
    for rule_name, cleaned in scan_sources(rules_dir, include_guide=False):
        for label, pattern in PURITY_PATTERNS:
            for match in pattern.finditer(cleaned):
                violations.append((rule_name, label, match.group(0)))
        for line in cleaned.splitlines():
            if CLAUDE_WRAPPER_PATTERN.search(line) and "Claude 端" not in line:
                violations.append(
                    (rule_name, "claude-wrapper-unannotated", line.strip()[:80])
                )
    return violations


def slim_for_bundle(content: str, rule_name: str = "") -> str:
    """Drop bundle-skip marker sections. No-op when no markers present.

    Warns on unbalanced markers (start without end or vice versa) so future
    edits that drop a marker don't silently skip the slimming.
    """
    starts = content.count("<!-- bundle: skip-start -->")
    ends = content.count("<!-- bundle: skip-end -->")
    if starts != ends:
        loc = f" in {rule_name}" if rule_name else ""
        print(
            f"[WARN] unbalanced bundle markers{loc}: {starts} start vs {ends} end",
            file=sys.stderr,
        )
    return SKIP_PATTERN.sub("", content)


# Pointer 投影的 bundle 註解標頭：指名 skill 來源，on-demand body 不 ship。
POINTER_ANNOTATION = (
    "<!-- pointer projection: on-demand body not shipped in this bundle; "
    "full text -> skill `{target}` (load the skill when triggered) -->"
)


def project_rule_for_bundle(path: pathlib.Path, meta: RuleMeta) -> str:
    """單一 rule 的 bundle 投影：純函數（內容只由 path 內容＋meta 決定）。

    full mode → 既有 slim_for_bundle()（無 marker 時 byte-identical）；
    pointer mode → 投影註解標頭＋bootstrap-pointer 逐字（無 frontmatter／
    body 殘留）。之後的 rule 走同一介面（第二支 pilot：llm-output），
    零 special-case filename。
    """
    content = path.read_text(encoding="utf-8")
    if meta.projection != "pointer":
        return slim_for_bundle(content, path.name)
    assert meta.pointer_target is not None and meta.bootstrap_pointer is not None, (
        "pointer mode meta must carry target and pointer (parse-time invariant)"
    )
    annotation = POINTER_ANNOTATION.format(target=meta.pointer_target)
    return f"{annotation}\n{meta.bootstrap_pointer}"


def check_pointer_preflight(
    rules: list[tuple[pathlib.Path, RuleMeta]],
    skills_dir: pathlib.Path,
    home: pathlib.Path,
) -> list[str]:
    """全域 preflight 三驗（契約二）：在任何 target write 之前對全部 pointer rule 跑完。

        1. target skill source 存在（repo skills/<target>/SKILL.md）
        2. pointer 行在場（bootstrap-pointer 非空；解析期已擋一次，此為防禦層）
        3. runtime 可達（~/.agents/skills/<target>/SKILL.md——non-CC 三家
           canonical portable root）

    回傳失敗訊息清單（空＝全過）。呼叫端（main 的 deploy 與 --dry-run 共用）
    必須以此 exit≠0 且不寫出任何 target——發現在 per-target loop 後段＝
    partial deploy 已發生，禁止。
    """
    failures: list[str] = []
    for path, meta in rules:
        if meta.projection != "pointer":
            continue
        target = meta.pointer_target or ""
        if not (meta.bootstrap_pointer or "").strip():
            failures.append(
                f"{path.name}: bootstrap-pointer empty (pointer line missing)"
            )
        source = skills_dir / target / "SKILL.md"
        if not source.is_file():
            failures.append(
                f"{path.name}: pointer target skill source missing: {source}"
            )
        runtime = home / ".agents" / "skills" / target / "SKILL.md"
        if not runtime.is_file():
            failures.append(
                f"{path.name}: pointer target skill not reachable at runtime: {runtime}"
            )
    return failures


def build_bundle(
    rule_paths: list[pathlib.Path],
    scopes_label: str,
    exclude: frozenset = frozenset(),
) -> str:
    parts = [HEADER.format(scopes=scopes_label)]
    parts.append(GUIDE.read_text(encoding="utf-8").strip())
    parts.append("")
    for rule_path in rule_paths:
        if rule_path.name in exclude:
            continue
        parts.append(f"\n---\n<!-- rules/{rule_path.name} -->\n")
        # 投影先於 bytes／size gate（S9）：bundle 內容即投影後內容。
        parts.append(
            project_rule_for_bundle(rule_path, read_rule_meta(rule_path)).strip()
        )
        parts.append("")
    parts.append(BUNDLE_END_SENTINEL)
    return "\n".join(parts)


def check_size_gate(bundle_bytes: int, target: DeployTarget) -> str | None:
    """該端超 gate 即回報訊息；通過回 None。"""
    if bundle_bytes <= target.max_bytes:
        return None
    return (
        f"[{target.label}] bundle {bundle_bytes:,} bytes exceeds "
        f"{target.max_bytes:,} bytes ({target.max_bytes // 1024}KiB)"
    )


def deploy_all(targets: list[pathlib.Path], bundle: str) -> list[pathlib.Path]:
    """Stage-then-commit 部署，回傳成功就位的 targets（含 identical 跳過者）。

    被寫入的是 always-on agent policy：單檔用同目錄 temp＋fsync＋os.replace
    保證原子（target 永不出現截斷/partial）；全部 temp 寫完才開始 replace，
    把跨 harness split 窗口壓到 replace 循環內。staging 任一失敗＝全部回滾
    temp、不動任何 target；replace 失敗＝回報該 target、其餘照常（殘餘 split
    由 check_single_source 的 freshness gate 兜底偵測）。

    冪等零寫入（AIR-85 EP:78）：target 已存在、非 symlink 且 bytes 與新
    bundle 完全一致 → 跳過 stage/replace（零寫入、mtime 不變、不留 .tmp），
    仍計入回傳清單（就位＝成功）。symlink 或內容不同 → 照舊 stage＋replace。
    """
    staged: list[tuple[pathlib.Path, pathlib.Path]] = []
    skipped: list[pathlib.Path] = []
    new_bytes = bundle.encode("utf-8")
    try:
        for target in targets:
            if (
                target.exists()
                and not target.is_symlink()
                and target.read_bytes() == new_bytes
            ):
                print(f"  [SKIP] {target} (identical)")
                skipped.append(target)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not target.is_symlink():
                existing = target.read_text(encoding="utf-8")
                if "Generated by scripts/deploy_agents.py" not in existing:
                    backup = target.with_suffix(".md.bak")
                    backup.write_text(existing, encoding="utf-8")
                    print(f"  [WARN] backed up {target} -> {backup}")
            tmp = target.with_name(target.name + ".tmp")
            staged.append(
                (tmp, target)
            )  # 先登記再寫——寫入/fsync 失敗時 cleanup 涵蓋本 temp
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(bundle)
                fh.flush()
                os.fsync(fh.fileno())
    except Exception as exc:
        for tmp, _target in staged:
            tmp.unlink(missing_ok=True)
        print(f"  [FAIL] staging: {exc}", file=sys.stderr)
        return []
    deployed: list[pathlib.Path] = list(skipped)
    for tmp, target in staged:
        try:
            os.replace(tmp, target)
            deployed.append(target)
            print(f"  -> {target}")
        except Exception as exc:
            tmp.unlink(missing_ok=True)
            print(f"  [FAIL] replace {target}: {exc}", file=sys.stderr)
    return deployed


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deploy bundled AGENTS.md to non-Claude harnesses."
    )
    ap.add_argument(
        "--scope",
        default="neutral",
        help="comma-separated harness-scopes to bundle (default: neutral)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="preview bundle stats without writing (stats only; use `cat` on a deployed target or import build_bundle to inspect content)",
    )
    args = ap.parse_args()
    try:
        return _deploy(args)
    except RuleMetaError as exc:
        # RuleMetaError＝rule frontmatter schema 解析期全域 fail-closed：
        # 以可判讀 [FAIL] 收場，不讓裸 traceback 直接噴給操作者。
        print(f"[FAIL] rule frontmatter schema: {exc}", file=sys.stderr)
        print(
            "     deploy aborted (fail-closed); fix the rule frontmatter and rerun.",
            file=sys.stderr,
        )
        return 1


def _deploy(args: argparse.Namespace) -> int:
    scope_override = (
        {s.strip() for s in args.scope.split(",")} if args.scope != "neutral" else None
    )

    if not GUIDE.exists():
        print(f"[FAIL] Guide not found: {GUIDE}", file=sys.stderr)
        return 1

    broken = check_broken_refs(RULES_DIR)
    if broken:
        print(
            f"[FAIL] {len(broken)} broken ref(s): bundle sources linking to claude-specific rules:",
            file=sys.stderr,
        )
        for src, target, name in broken:
            print(f"  {src} -> {target} ({name} is claude-specific)", file=sys.stderr)
        print("Fix the ref, or re-scope the target to neutral.", file=sys.stderr)
        return 1

    impure = check_neutral_purity(RULES_DIR)
    if impure:
        print(
            f"[FAIL] {len(impure)} neutral-purity violation(s) "
            "(rules/AGENTS.md 機械檢查清單):",
            file=sys.stderr,
        )
        for rule_name, label, hit in impure:
            print(f"  {rule_name}: [{label}] {hit}", file=sys.stderr)
        print(
            "Neutralize it: move into a (Claude: ...) note, describe the skill "
            "by name, or generalize the path away.",
            file=sys.stderr,
        )
        return 1

    # 全域 preflight（契約二）：pointer 三驗在任何 target write 之前一次跑完，
    # --dry-run 與真跑共用（S7——根除「dry-run 綠、真跑 fail」的假驗收）；
    # 發現在 per-target loop 中後段＝partial deploy 已發生，禁止。
    home = pathlib.Path.home()
    targets = resolve_targets(home)
    if scope_override is not None:
        preflight_scopes: set[str] = set(scope_override)
    else:
        preflight_scopes = set().union(*(set(t.scopes) for t in targets))
    preflight_failures = check_pointer_preflight(
        [(p, read_rule_meta(p)) for p in discover_rules(RULES_DIR, preflight_scopes)],
        SKILLS_DIR,
        home,
    )
    if preflight_failures:
        print(
            f"[FAIL] {len(preflight_failures)} pointer preflight failure(s) "
            "(aborted before ANY target write):",
            file=sys.stderr,
        )
        for msg in preflight_failures:
            print(f"  {msg}", file=sys.stderr)
        print(
            "     pointer rule needs repo skills/<target>/SKILL.md and "
            "~/.agents/skills/<target>/SKILL.md (non-CC canonical portable root).",
            file=sys.stderr,
        )
        return 1
    # partial-deploy 語義（有意）：各端獨立 build＋gate，一端失敗只跳過該端，
    # 其餘端照樣部署；exit code 仍為 1 告警（F4 聲明）。
    ready: list[tuple[DeployTarget, str]] = []
    failed = False
    for target in targets:
        # 自訂 --scope 只改 scope；target 的排除與尺寸契約不變。
        scopes = scope_override or target.scopes
        scopes_label = scopes_label_for(scopes, target.exclude)
        rule_paths = discover_rules(RULES_DIR, scopes)
        if not rule_paths:
            print(f"[FAIL] No rules with scope in {scopes}", file=sys.stderr)
            failed = True
            continue
        bundle = build_bundle(rule_paths, scopes_label, target.exclude)
        # Sentinel integrity is the load-time truncation proof; guard it every run.
        assert bundle.count(BUNDLE_END_SENTINEL) == 1
        assert bundle.rstrip().endswith(BUNDLE_END_SENTINEL)
        bundle_lines = bundle.count("\n") + 1
        bundle_bytes = len(bundle.encode("utf-8"))
        tok_est = bundle_bytes // 3200

        rule_names = [p.name for p in rule_paths if p.name not in target.exclude]
        print(
            f"[OK] [{target.label}] bundle: {len(rule_names)} rules "
            f"(scope={scopes_label}) + guide"
        )
        print(f"     rules: {', '.join(rule_names)}")
        print(
            f"     size: {bundle_lines} lines, {bundle_bytes:,} bytes "
            f"(~{tok_est}K tokens est, "
            f"{bundle_bytes * 100 // target.max_bytes}% of "
            f"{target.max_bytes // 1024}KiB gate)"
        )

        if bundle_bytes >= target.max_bytes * BUNDLE_WARN_RATIO:
            print(
                f"[WARN] [{target.label}] bundle at "
                f"{bundle_bytes * 100 // target.max_bytes}% of "
                f"size gate ({target.max_bytes // 1024}KiB) -- deploy still OK, "
                "but slimming should happen before the gate, not at it "
                "(see rules/AGENTS.md size-gate note)",
                file=sys.stderr,
            )

        gate_msg = check_size_gate(bundle_bytes, target)
        if gate_msg is not None:
            print(f"[FAIL] {gate_msg}", file=sys.stderr)
            print(
                "     Harness lanes truncate (ZCode: 102,400B hard line; "
                "muse: 64KiB shared with project layer). Slim rules/ per "
                "encoder-philosophy, or demote on-demand content to a "
                "reference skill (rule keeps always-on core + pointer; "
                "see rules/AGENTS.md size-gate note).",
                file=sys.stderr,
            )
            failed = True
            continue
        ready.append((target, bundle))

    if args.dry_run:
        print("[DRY-RUN] skipping deploy")
        return 1 if failed else 0

    deployed = 0
    for target, bundle in ready:
        if deploy_all([target.path], bundle) == [target.path]:
            deployed += 1
    if deployed == len(ready) and not failed:
        print(f"[OK] deployed to {deployed}/{len(targets)} non-Claude harnesses")
    else:
        print(
            f"[FAIL] deployed to {deployed}/{len(targets)} non-Claude harnesses",
            file=sys.stderr,
        )
    print(
        "     Claude (~/.claude/CLAUDE.md) untouched -- rules via ~/.claude/rules/ auto-load"
    )
    return 0 if deployed == len(targets) and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
