#!/usr/bin/env python3
"""
Unified Project Knowledge Scanner.

Produces three things (no full registries — LLM reads files directly):
1. dep_graph — AST-parsed Python import relationships
2. findings — mechanical cross-validation issues (X-cap-path, X-ep-ready, etc.)
3. fingerprint — lightweight change detection (counts + hashes)

Internal parsing of instruction files (AGENTS.md preferred, CLAUDE.md legacy) and backlog/tasks/ is kept for computing findings,
but registries are NOT included in output.

Designed for the /scan-project skill (on-demand mechanical inventory + findings).

Usage:
    uv run python scan_project.py --project-root . --output .project-snapshot.json
"""

import argparse
import ast
import hashlib
import json
import os
import re
import tomllib
from collections import defaultdict
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS_SCAN = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    "_archive",
    ".claude",
    "build",
    "dist",
    "target",  # Rust/Cargo build artifacts
    "_build",  # Sphinx and similar doc builds
    "ref-docs",  # external harness mirrors — not this repo's instructions
}

# Top-level dirs that may carry __init__.py but are never the importable
# package root. Used only by the _find_package_root fallback to avoid picking
# tests/ (which often has more .py files than the real package).
NON_PACKAGE_DIRS = {"tests", "test", "docs", "examples", "stubs"}

KANBAN_STATUSES = {"To Do", "In Progress", "Done"}

# EP reference in card body (checked by X-ep-ready)
EP_REF_RE = re.compile(r"^- EP:\s*`?([^`*\n]+)`?", re.MULTILINE)

# Capabilities table header detection
CAPABILITIES_HEADER_RE = re.compile(r"^##\s+Capabilities", re.MULTILINE)

# Markdown table row detection: starts and ends with |
TABLE_ROW_START = re.compile(r"^\|.*\|\s*$")

# Note: UC ID pattern removed — Capabilities tables now use 3-column format
# (能力 | 入口 | 狀態) without UC ID numbering.


# ---------------------------------------------------------------------------
# Package root detection (shared by scans + findings)
# ---------------------------------------------------------------------------


def _find_package_root(project_root: Path) -> Path | None:
    """Find the project's main Python package root, deterministically.

    Selection never depends on filesystem iterdir() order. Unsorted iterdir()
    previously caused a regression: adding a dev utility's __init__.py flipped
    the iteration order and resolved package_root to that utility dir instead
    of the real package, which made every path/tag check resolve against the
    wrong base and produced 236 false-positive findings in a single run.

    Priority (each step deterministic):
    1. project_root itself is a package (has __init__.py).
    2. pyproject.toml declaration — [tool.setuptools.packages.find] include /
       [tool.setuptools] packages / [[tool.poetry.packages]] include. This is
       the authoritative source of "what is this project's package".
    3. Dir whose name matches [project] name or the repo dir name
       (PEP 503 normalization: '-' -> '_').
    4. Deterministic fallback: largest candidate by .py file count, excluding
       obvious non-package dirs (tests/ etc.); candidates are pre-sorted by
       name so ties resolve deterministically.

    Limitation: src-layout (packages under src/) is not handled — the scanner's
    scope is top-level packages. Add where=["src"] resolution if ever needed.
    """
    if (project_root / "__init__.py").exists():
        return project_root

    candidates = _sorted_package_candidates(project_root)
    if not candidates:
        return None

    # Same-name collision (e.g. root pkg vs python/<pkg> shell remnant):
    # more .py files wins — a deeper lookalike must not shadow the real package.
    by_name: dict[str, Path] = {}
    for cand in candidates:  # pre-sorted by path: deterministic tie order
        prev = by_name.get(cand.name)
        if prev is None or _count_py_files(cand) > _count_py_files(prev):
            by_name[cand.name] = cand

    # 2. Authoritative: pyproject.toml package declaration
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        for pkg_name in _declared_package_names(pyproject):
            root_name = pkg_name.split(".")[0].rstrip("*")
            if root_name in by_name:
                return by_name[root_name]

    # 3. Name match: [project] name or repo dir name (normalized)
    for proj_name in _project_name_candidates(project_root):
        if proj_name in by_name:
            return by_name[proj_name]

    # 4. Deterministic fallback: largest code candidate; ties -> sorted name
    code_candidates = [c for c in candidates if c.name not in NON_PACKAGE_DIRS]
    pool = code_candidates or candidates
    return max(pool, key=_count_py_files)


def _iter_files(root: Path, suffix: str) -> Iterator[Path]:
    """Yield files whose name ends with suffix, pruning noise dirs, deterministic order.

    os.walk with in-place dir pruning (SKIP_DIRS_SCAN + dot-dirs) — unlike
    rglob this never descends into build artifacts (target/, .venv/, ...).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS_SCAN and not d.startswith(".")
        )
        for name in sorted(filenames):
            if name.endswith(suffix):
                yield Path(dirpath) / name


def _sorted_package_candidates(project_root: Path) -> list[Path]:
    """Deterministic list of package-top candidates.

    A package top = dir with __init__.py whose PARENT lacks __init__.py.
    Search depth ≤ 3 so python/<pkg> workspace layouts resolve; deeper
    nesting is rare and intentionally out of scope. Non-package dirs
    (tests/ etc.), hidden and skip dirs are excluded. Sorted by path so
    selection never depends on filesystem iteration order.
    """
    result: list[Path] = []
    for init in _iter_files(project_root, "__init__.py"):
        parts = init.relative_to(project_root).parts
        if len(parts) > 4:  # depth-3 dir + __init__.py
            continue
        if init.parent.name in NON_PACKAGE_DIRS:
            continue
        if (init.parent.parent / "__init__.py").exists():
            continue  # nested subpackage, not a package top
        result.append(init.parent)
    return sorted(set(result), key=lambda p: str(p))


def _declared_package_names(pyproject: Path) -> list[str]:
    """Extract declared package names from pyproject.toml (setuptools/poetry).

    Names may be glob patterns ("my_package*") or dotted paths
    ("pkg.sub"); callers take the first dot segment and strip the glob star.
    """
    try:
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return []

    tool = data.get("tool", {})
    names: list[str] = []

    # setuptools packages field is overloaded:
    #   [tool.setuptools] packages = ["pkg_a", "pkg_b"]   -> list
    #   [tool.setuptools.packages.find] include = [...]   -> dict with .find
    packages_field = tool.get("setuptools", {}).get("packages", {})
    if isinstance(packages_field, list):
        names.extend(packages_field)
    elif isinstance(packages_field, dict):
        find_cfg = packages_field.get("find", {})
        names.extend(find_cfg.get("include", []))

    # poetry: [[tool.poetry.packages]] include = "..."
    for pkg in tool.get("poetry", {}).get("packages", []):
        if isinstance(pkg, dict) and "include" in pkg:
            names.append(pkg["include"])

    return names


def _project_name_candidates(project_root: Path) -> list[str]:
    """Candidate project names (normalized '-' -> '_') for dir matching."""
    names: list[str] = []
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
            proj_name = data.get("project", {}).get("name")
            if proj_name:
                names.append(proj_name.replace("-", "_"))
        except (OSError, tomllib.TOMLDecodeError):
            pass
    # Repo dir name (commonly matches the package name)
    names.append(project_root.name.replace("-", "_"))
    return names


def _count_py_files(path: Path) -> int:
    """Count .py files in a directory tree (fallback sizing signal only)."""
    try:
        return sum(1 for _ in path.rglob("*.py"))
    except OSError:
        return 0


# ---------------------------------------------------------------------------
# Instruction-file parsing (AGENTS.md preferred, CLAUDE.md legacy)
# ---------------------------------------------------------------------------


def _find_instruction_files(project_root: Path) -> list[Path]:
    """Find each directory's instruction-content file (dual-file aware).

    Per instruction-writing.md dual-file mode: content lives in AGENTS.md
    (CLAUDE.md is a thin @AGENTS.md wrapper for Claude). Prefer AGENTS.md;
    fall back to CLAUDE.md for legacy single-file repos. Returns one file
    per directory. Uses pruned walk (_iter_files) — never descends into
    build artifacts.
    """
    by_dir: dict[Path, Path] = {}
    for path in _iter_files(project_root, "CLAUDE.md"):
        by_dir[path.parent] = path
    for path in _iter_files(project_root, "AGENTS.md"):
        by_dir[path.parent] = path  # AGENTS.md preferred (overwrites CLAUDE.md)
    return sorted(by_dir.values())


def parse_claude_md_registry(
    project_root: Path,
) -> tuple[list[dict], list[dict]]:
    """Parse all CLAUDE.md files.

    Returns (claude_md_registry, capabilities_registry).
    """
    claude_md_registry = []
    capabilities_registry = []
    for md_file in _find_instruction_files(project_root):
        md_entry, caps_entries = _parse_single_claude_md(md_file, project_root)
        claude_md_registry.append(md_entry)
        capabilities_registry.extend(caps_entries)
    return claude_md_registry, capabilities_registry


def _parse_capabilities_table(
    content: str, source_claude_md: str, module: str
) -> list[dict]:
    """Parse Capabilities table from instruction-file content.

    Expected table format (3 columns, no UC ID):
        | 能力 | 入口 | 狀態 |
    """
    entries: list[dict] = []

    header_match = CAPABILITIES_HEADER_RE.search(content)
    if not header_match:
        return entries

    # Get text after the header until next ## heading
    start = header_match.end()
    next_section = re.search(r"\n## ", content[start:])
    section_text = (
        content[start : start + next_section.start()]
        if next_section
        else content[start:]
    )

    for line in section_text.splitlines():
        # Parse table row using split-by-| instead of regex.
        # This handles | inside backtick content (e.g. CLI `sync [revenue|income|all]`)
        # by taking col1 from the left and status from the right, then
        # reconstructing entry_point from the middle fragments.
        if not TABLE_ROW_START.match(line):
            continue
        parts = line.split("|")
        # parts: ['', col1, col2, ..., colN, ''] (leading/trailing |)
        if len(parts) < 5:  # need at least: '' capability entry_point status ''
            continue
        col1 = parts[1].strip()  # capability/能力 (never contains |)
        col_last = parts[-2].strip()  # status/狀態 (never contains |)
        # Reconstruct entry_point by rejoining fragments — restores | inside backticks
        entry_point = "|".join(parts[2:-2]).strip()

        # Skip separator rows (---)
        if all(set(c.strip()) <= {"-", ":"} for c in parts[1:-1]):
            continue
        # Skip header rows
        if col1 in ("能力", "Capability"):
            continue

        # Skip empty rows
        if not col1:
            continue

        # Extract status emoji
        status = ""
        for ch in col_last:
            if ch in "✅📋🔧❌🟡🟢":
                status = ch
                break
        if not status:
            status = "✅"  # Default for Capabilities table entries

        entries.append(
            {
                "module": module,
                "capability": col1,
                "entry_point": entry_point,
                "status": status,
                "source_claude_md": source_claude_md,
            }
        )

    return entries


def _parse_single_claude_md(
    md_file: Path, project_root: Path
) -> tuple[dict, list[dict]]:
    """Parse a single CLAUDE.md file.

    Returns (metadata_dict, capabilities_entries).
    """
    content = md_file.read_text(encoding="utf-8")
    path_rel = str(md_file.relative_to(project_root))

    parent = md_file.parent
    module = parent.name if parent != project_root else "(root)"

    has_boundaries = bool(
        re.search(r"Module Boundaries|模組邊界|Does NOT depend on", content)
    )

    has_capabilities = bool(CAPABILITIES_HEADER_RE.search(content))

    not_depend_on = []
    for m in re.finditer(r"Does NOT depend on[：:]*\s*(.+?)(?:\n|$)", content):
        for mod_match in re.finditer(r"\b([a-z][a-z0-9_]*)\b", m.group(1)):
            not_depend_on.append(mod_match.group(1))

    # Parse Capabilities table
    capabilities_entries = _parse_capabilities_table(content, path_rel, module)

    md_entry = {
        "path": path_rel,
        "module": module,
        "exists": True,
        "has_module_boundaries": has_boundaries,
        "has_capabilities_table": has_capabilities,
        "capabilities_count": len(capabilities_entries),
        "declared_not_depend_on": sorted(set(not_depend_on)),
    }

    return md_entry, capabilities_entries


# ---------------------------------------------------------------------------
# backlog/tasks/ card parsing (frontmatter identity)
# ---------------------------------------------------------------------------


def parse_kanban_registry(project_root: Path) -> list[dict]:
    """Parse all backlog/tasks/ cards (Backlog.md frontmatter format)."""
    tasks_dir = project_root / "backlog" / "tasks"
    if not tasks_dir.is_dir():
        return []

    registry = []
    for card_file in sorted(tasks_dir.glob("*.md")):
        entry = _parse_kanban_card(card_file, project_root)
        if entry.get("lane") in KANBAN_STATUSES:
            registry.append(entry)
    return registry


def _parse_kanban_card(card_file: Path, project_root: Path) -> dict:
    """Parse a single Backlog.md task card.

    Card identity: frontmatter id + title; lane = frontmatter status
    (To Do / In Progress / Done — Backlog.md three-column workflow).
    """
    content = card_file.read_text(encoding="utf-8")
    source_rel = str(card_file.relative_to(project_root))

    # Frontmatter (id/title/status) — plain regex parse, no yaml dependency
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    fm = fm_match.group(1) if fm_match else ""

    def _fm_value(key: str) -> str:
        m = re.search(rf"^{key}: (.+)$", fm, re.MULTILINE)
        return m.group(1).strip() if m else ""

    card_id = _fm_value("id")
    title = _fm_value("title") or card_file.stem
    lane = _fm_value("status")

    # EP reference from body (`- EP: path` convention, checked by X-ep-ready)
    ep_match = EP_REF_RE.search(content)
    ep_ref = ""
    has_ep = False
    if ep_match:
        ep_ref = ep_match.group(1).strip()
        has_ep = ep_ref not in ("待定", "")

    has_spec = bool(re.search(r"spec[：:]", content, re.IGNORECASE))

    return {
        "id": card_id,
        "title": title,
        "lane": lane,
        "has_ep": has_ep,
        "ep_ref": ep_ref,
        "has_spec": has_spec,
        "source_file": source_rel,
    }


# ---------------------------------------------------------------------------
# Cross-validation (mechanical checks)
# ---------------------------------------------------------------------------


def run_cross_validation(
    modules: dict,
    capabilities_registry: list[dict],
    kanban_registry: list[dict],
    claude_md_registry: list[dict],
    project_root: Path,
) -> list[dict]:
    """Run mechanical cross-validation checks."""
    findings = []

    claude_md_modules = {e["module"] for e in claude_md_registry}

    # --- Capabilities checks ---

    # X-cap-path: Capabilities entry_point path does not exist
    # Entry paths may be relative to: project root, package root, or
    # the CLAUDE.md's own directory.  Check all three before reporting.
    pkg_root = _find_package_root(project_root)
    for e in capabilities_registry:
        entry = e.get("entry_point", "")
        if not entry:
            continue
        # Extract first path-like segment (before any description)
        # e.g. "CLI `mycli data daily-close`" → skip (CLI commands)
        # e.g. "`indicators/engine.py:apply_indicators()`" → extract path
        path_match = re.search(r"`?([a-z_][a-z0-9_./]+\.pyi?)", entry)
        if path_match:
            rel_path = path_match.group(1).split(":")[0]
            # Candidate locations to check
            candidates = [
                project_root / rel_path,  # absolute from project root
            ]
            if pkg_root:
                candidates.append(pkg_root / rel_path)  # under package root
            # Relative to the CLAUDE.md's own directory
            claude_md_dir = (
                project_root / e["source_claude_md"].rsplit("/", 1)[0]
                if "/" in e["source_claude_md"]
                else project_root
            )
            candidates.append(claude_md_dir / rel_path)
            if not any(p.exists() for p in candidates):
                findings.append(
                    {
                        "check_id": "X-cap-path",
                        "severity": "important",
                        "detail": (
                            f"Capabilities entry path '{rel_path}' "
                            f"does not exist (in {e['source_claude_md']})"
                        ),
                        "capability": e["capability"],
                        "source_claude_md": e["source_claude_md"],
                    }
                )

    # X6: Module in dep-graph but no instruction file (AGENTS.md/CLAUDE.md)
    # Module dirs may live at project root OR under the package root
    # (python/<pkg>/<mod> layouts) — check both before reporting.
    for mod_name, mod_data in modules.items():
        if mod_name in claude_md_modules or mod_name == "(root)":
            continue
        file_count = mod_data.get("file_count", 0)
        if file_count < 3:
            continue
        candidate_dirs = [
            d
            for d in (
                project_root / mod_name,
                pkg_root / mod_name if pkg_root else None,
            )
            if d is not None and d.is_dir()
        ]
        if not candidate_dirs:
            continue
        if any(
            (d / "CLAUDE.md").exists() or (d / "AGENTS.md").exists()
            for d in candidate_dirs
        ):
            continue
        findings.append(
            {
                "check_id": "X6",
                "severity": "important",
                "detail": (
                    f"Module '{mod_name}' has {file_count} files but no instruction file (AGENTS.md/CLAUDE.md)"
                ),
                "module": mod_name,
            }
        )

    # --- Kanban checks ---

    # X-ep-ready: To Do/In Progress card has EP ref but file missing
    for e in kanban_registry:
        if e["lane"] not in ("To Do", "In Progress"):
            continue
        if not e.get("has_ep") or not e.get("ep_ref"):
            continue
        ep_ref = e["ep_ref"]
        # Task-home conventions: ai-analysis/_tasks/, line projects, 00-tasks/
        # (probe mirrors metadata-sync EP archiving; AIR-77: new arcs live
        # under _tasks/YYYY-MM/ and never move, history is frozen _archived/)
        tasks_home = project_root / "ai-analysis" / "_tasks"
        ep_candidates = [
            tasks_home / ep_ref,
            tasks_home / "_archived" / ep_ref,
            project_root / "00-tasks" / ep_ref,
            project_root / ep_ref,
        ]
        if tasks_home.is_dir():
            ep_candidates.extend(
                month_dir / ep_ref
                for month_dir in sorted(
                    tasks_home.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]")
                )
                if month_dir.is_dir()
            )
        projects_dir = project_root / "ai-analysis" / "_projects"
        if projects_dir.is_dir():
            for line_dir in sorted(projects_dir.iterdir()):
                if line_dir.is_dir():
                    ep_candidates.append(line_dir / "tasks" / ep_ref)
                    ep_candidates.append(line_dir / "done" / ep_ref)
        ep_exists = any(p.exists() for p in ep_candidates)
        if not ep_exists:
            findings.append(
                {
                    "check_id": "X-ep-ready",
                    "severity": "important",
                    "detail": (
                        f"Card '{e['title']}' in {e['lane']} references "
                        f"EP '{ep_ref}' but file not found"
                    ),
                    "kanban_source": e["source_file"],
                }
            )

    return findings


# ---------------------------------------------------------------------------
# Built-in scans (no target-project tooling required)
# ---------------------------------------------------------------------------


def _builtin_import_scan(project_root: Path) -> dict | None:
    """Built-in AST import scan over the project's package root.

    AST-parses all .py files under the package root and reduces imports to
    module-level edges (module = first directory under the package root).
    Relative imports are resolved against the importing file's location.
    Import paths falling into a non-package directory (e.g. a bindings shim
    without __init__.py) are skipped rather than misattributed.
    """
    pkg_root = _find_package_root(project_root)
    if pkg_root is None:
        return None
    pkg_name = pkg_root.name
    module_dirs = {
        d.name
        for d in pkg_root.iterdir()
        if d.is_dir() and (d / "__init__.py").exists() and not d.name.startswith(".")
    }

    modules: dict[str, dict] = {}

    def _entry(owner: str) -> dict:
        return modules.setdefault(
            owner,
            {
                "file_count": 0,
                "internal_deps": {},
                "external_deps": {},
                "imported_by": [],
                "fan_out": 0,
            },
        )

    hotspot_importers: dict[str, set] = {}

    for py_file in _iter_files(pkg_root, ".py"):
        rel_parts = py_file.relative_to(pkg_root).parts
        owner = rel_parts[0] if len(rel_parts) > 1 else "(root)"
        entry = _entry(owner)
        entry["file_count"] += 1
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [(alias.name, 0) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [(node.module or "", node.level)]
            else:
                continue
            for name, level in imports:
                if level == 0:
                    parts = tuple(name.split(".")) if name else ()
                else:
                    base = list(rel_parts[:-1])
                    cut = level - 1
                    if cut > len(base):
                        continue
                    resolved = base[: len(base) - cut] + (
                        name.split(".") if name else []
                    )
                    parts = tuple(resolved)
                if not parts:
                    continue
                first_party = level > 0 or parts[0] == pkg_name
                if first_party:
                    if len(parts) <= 1 or parts[1] not in module_dirs:
                        continue
                    target = parts[1]
                    if target != owner:
                        paths = entry["internal_deps"].setdefault(target, [])
                        import_path = ".".join(parts[:2])
                        if import_path not in paths:
                            paths.append(import_path)
                        hotspot_importers.setdefault(import_path, set()).add(owner)
                else:
                    ext = parts[0]
                    paths = entry["external_deps"].setdefault(ext, [])
                    if name not in paths and len(paths) < 3:
                        paths.append(name)

    edges = []
    for source in sorted(modules):
        entry = modules[source]
        entry["fan_out"] = len(entry["internal_deps"])
        for target in sorted(entry["internal_deps"]):
            paths = entry["internal_deps"][target]
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "weight": len(paths),
                    "imports": paths[:5],
                }
            )
            tgt = modules.get(target)
            if tgt is not None and source not in tgt["imported_by"]:
                tgt["imported_by"].append(source)

    hotspots = [
        {"import_path": p, "imported_by": sorted(owners), "fan_out": len(owners)}
        for p, owners in sorted(hotspot_importers.items(), key=lambda kv: -len(kv[1]))[
            :10
        ]
    ]

    return {
        "project": pkg_name,
        "modules": modules,
        "edges": edges,
        "hotspots": hotspots,
    }


def _scan_rust_workspace(project_root: Path) -> dict | None:
    """Parse the shallowest Cargo workspace: members + internal crate deps.

    Internal dep = a [dependencies] key naming another workspace member.
    has_python_bindings marks crates with src/python/ (PyO3 binding layer) —
    the truth↔shell signal for Rust-core + binding-shell repos.
    """
    manifests = sorted(
        _iter_files(project_root, "Cargo.toml"),
        key=lambda p: (len(p.relative_to(project_root).parts), str(p)),
    )
    workspace_manifest = None
    workspace_data = None
    for manifest in manifests:
        try:
            with manifest.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            continue
        if "workspace" in data:
            workspace_manifest = manifest
            workspace_data = data
            break
    if workspace_manifest is None:
        return None
    ws_root = workspace_manifest.parent

    member_dirs: set[Path] = set()
    for pattern in workspace_data.get("workspace", {}).get("members", []):
        for d in ws_root.glob(pattern):
            if d.is_dir() and (d / "Cargo.toml").exists():
                member_dirs.add(d)
    if "package" in workspace_data:
        member_dirs.add(ws_root)

    crate_by_dir: dict[Path, tuple[str, dict]] = {}
    for d in sorted(member_dirs, key=str):
        try:
            with (d / "Cargo.toml").open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            continue
        name = data.get("package", {}).get("name")
        if name:
            crate_by_dir[d] = (name, data)

    member_names = {name for name, _ in crate_by_dir.values()}
    crates = []
    for d, (name, data) in sorted(crate_by_dir.items(), key=lambda kv: kv[1][0]):
        deps_table = data.get("dependencies", {})
        internal = sorted(
            dep
            for dep in (deps_table if isinstance(deps_table, dict) else {})
            if dep in member_names and dep != name
        )
        crates.append(
            {
                "name": name,
                "dir": str(d.relative_to(project_root)),
                "internal_deps": internal,
                "has_python_bindings": (d / "src" / "python").is_dir(),
            }
        )
    return {"root": str(ws_root.relative_to(project_root)), "crates": crates}


def _dir_inventory(project_root: Path, max_depth: int = 4, cap: int = 800) -> dict:
    """Mechanical directory inventory (bounded) — the enumeration ground truth.

    Structural listings consumed by instruction-init / doc flows must come
    from mechanical output, not from LLM prose summaries. File NAMES are
    included only for dirs with ≤60 direct files (larger dirs get counts
    only) to keep the snapshot bounded. Depth 4 covers the AIR-77 month
    layer (ai-analysis/_tasks/YYYY-MM/<arc>/).
    """
    dirs_out: list[dict] = []
    truncated = False
    for dirpath, dirnames, filenames in os.walk(project_root):
        current = Path(dirpath)
        depth = len(current.relative_to(project_root).parts)
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS_SCAN and not d.startswith(".")
        )
        subdirs = sorted(dirnames)
        if depth >= max_depth:
            dirnames[:] = []  # stop descent; subdirs above still reports children
        if depth == 0:
            continue
        if len(dirs_out) >= cap:
            truncated = True
            break
        ext_counts: dict[str, int] = {}
        for fn in sorted(filenames):
            ext = Path(fn).suffix.lstrip(".").lower() or "(noext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        entry = {
            "path": str(current.relative_to(project_root)),
            "depth": depth,
            "subdirs": subdirs,
            "files_total": len(filenames),
            "file_exts": dict(sorted(ext_counts.items(), key=lambda kv: -kv[1])[:6]),
        }
        if len(filenames) <= 60:
            entry["files"] = sorted(filenames)
        dirs_out.append(entry)
    return {"max_depth": max_depth, "truncated": truncated, "dirs": dirs_out}


# ---------------------------------------------------------------------------
# Main scan function
# ---------------------------------------------------------------------------


def _compute_fingerprint(
    capabilities_registry: list[dict],
    kanban_registry: list[dict],
    claude_md_registry: list[dict],
) -> dict:
    """Compute lightweight fingerprint for change detection.

    LLM reads CLAUDE.md and backlog/tasks/ directly when it needs details.
    The fingerprint only answers: "did something change since last scan?"
    """

    # Capabilities hash: sorted capability + module + status
    cap_keys = sorted(
        f"{e['capability']}:{e['module']}:{e['status']}" for e in capabilities_registry
    )
    cap_hash = hashlib.md5("|".join(cap_keys).encode()).hexdigest()[:12]

    # Kanban hash: sorted id + title + lane
    kanban_keys = sorted(f"{e['id']}:{e['title']}:{e['lane']}" for e in kanban_registry)
    kanban_hash = hashlib.md5("|".join(kanban_keys).encode()).hexdigest()[:12]

    # Kanban by lane
    kanban_by_lane: dict[str, int] = defaultdict(int)
    for e in kanban_registry:
        kanban_by_lane[e["lane"]] += 1

    return {
        "capabilities_total": len(capabilities_registry),
        "capabilities_hash": cap_hash,
        "kanban_total": len(kanban_registry),
        "kanban_by_lane": dict(kanban_by_lane),
        "kanban_hash": kanban_hash,
        "instruction_file_total": len(claude_md_registry),
    }


def scan_project(project_root: Path) -> dict:
    """Run the full unified scan.

    Produces three things:
    1. dep_graph — AST-parsed import relationships (LLM can't do this)
    2. findings — mechanical cross-validation issues (LLM can but expensive)
    3. fingerprint — lightweight change detection (counts + hashes)

    Internal parsing (registries) is kept for computing findings,
    but NOT included in output. LLM reads CLAUDE.md and backlog/tasks/
    directly when it needs details.
    """
    project_root = project_root.resolve()

    # Phase 1: Import scan — built-in AST scan of the package root
    import_data = _builtin_import_scan(project_root)
    import_source = "builtin" if import_data else "none"
    if import_data:
        modules = import_data.get("modules", {})
        edges = import_data.get("edges", [])
        hotspots = import_data.get("hotspots", [])
        project_name = import_data.get("project", project_root.name)
    else:
        modules = {}
        edges = []
        hotspots = []
        project_name = project_root.name

    # Phase 1b: Rust workspace + mechanical directory inventory (no project tooling needed)
    rust_workspace = _scan_rust_workspace(project_root)
    dir_inventory = _dir_inventory(project_root)

    # Phase 2: Parse CLAUDE.md files (internal — not in output)
    claude_md_registry, capabilities_registry = parse_claude_md_registry(project_root)

    # Phase 3: Parse backlog/tasks/ cards (internal — not in output)
    kanban_registry = parse_kanban_registry(project_root)

    # Phase 4: Run mechanical cross-validation → findings
    findings = run_cross_validation(
        modules,
        capabilities_registry,
        kanban_registry,
        claude_md_registry,
        project_root,
    )

    # Phase 5: Compute fingerprint for change detection
    fingerprint = _compute_fingerprint(
        capabilities_registry, kanban_registry, claude_md_registry
    )

    return {
        "project": project_name,
        "scan_timestamp": datetime.now(tz=UTC).isoformat(),
        "schema_version": 6,
        "dep_graph": {
            "source": import_source,
            "modules": modules,
            "edges": edges,
            "hotspots": hotspots,
        },
        "rust_workspace": rust_workspace,
        "dir_inventory": dir_inventory,
        "instruction_files": [
            {
                "path": e["path"],
                "module": e["module"],
                "has_module_boundaries": e["has_module_boundaries"],
                "has_capabilities_table": e["has_capabilities_table"],
            }
            for e in claude_md_registry
        ],
        "findings": findings,
        "fingerprint": fingerprint,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Unified project knowledge scanner")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to the project root (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    result = scan_project(project_root)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        args.output.write_text(output_json, encoding="utf-8")
        fp = result["fingerprint"]
        findings_count = len(result["findings"])
        dep = result["dep_graph"]
        dep_modules = len(dep["modules"])
        rust_crates = len((result.get("rust_workspace") or {}).get("crates", []))
        inv_dirs = len(result.get("dir_inventory", {}).get("dirs", []))
        print(
            f"[OK] Written to {args.output} "
            f"(dep_graph[{dep.get('source', 'builtin')}]: {dep_modules} modules, "
            f"rust: {rust_crates} crates, "
            f"inventory: {inv_dirs} dirs, "
            f"instruction_files: {fp['instruction_file_total']}, "
            f"findings: {findings_count}, "
            f"fingerprint: {fp['capabilities_total']} caps / "
            f"{fp['kanban_total']} cards)"
        )
    else:
        print(output_json)


if __name__ == "__main__":
    main()
