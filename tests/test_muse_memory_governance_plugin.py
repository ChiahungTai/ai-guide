"""Tests for muse-plugins/memory-governance (AIR-79 S1).

Shared core (hooks/muse_memory_governance.sh) with per-repo marker
three-state opt-in: absent -> allow native; protocol==1 (integer) ->
divert into .agents/memory-inbox + deny; anything else -> deny without
landing. Fixtures build tmp repo skeletons and drive the script via
subprocess (no mocks on bash/jq/git — EP verification strategy).
"""

import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "muse-plugins" / "memory-governance"
CORE = PLUGIN_DIR / "hooks" / "muse_memory_governance.sh"

# SM-3/SM-4 value matrix: integer 1 is the only valid protocol; every type
# confusion and every other value denies without landing (EP C10).
INVALID_MARKERS = [
    '{"protocol": 0}',
    '{"protocol": -1}',
    '{"protocol": "1"}',
    '{"protocol": null}',
    '{"protocol": true}',
    '{"protocol": false}',
    "{}",
    "[]",
    "not-json",
    '{"protocol": 2}',
    '{"protocol": 1.5}',
]


# ---------------------------------------------------------------- helpers


def write_marker(repo, value):
    path = repo / ".agents" / "memory-governance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def write_raw_marker(repo, raw):
    path = repo / ".agents" / "memory-governance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw)


def make_repo(tmp_path, *, marker="valid", pool_entry=True):
    """Plugin skeleton: .agents/memory pool + optional governance marker.

    The inbox (.agents/memory-inbox) is intentionally NOT created — its
    ENOENT state must be safe for the hook to build it (SM-12).
    """
    repo = tmp_path / "repo"
    pool = repo / ".agents" / "memory"
    pool.mkdir(parents=True)
    if pool_entry:
        (pool / "note.md").write_text("---\nname: note\n---\n\nbody\n")
    if marker == "valid":
        write_marker(repo, {"protocol": 1})
    elif isinstance(marker, str):
        write_raw_marker(repo, marker)
    elif marker is not None:
        write_marker(repo, marker)
    return repo


def mem_payload(tool="add_memory", path="new-note.md", content="hello inbox"):
    return {
        "tool_name": tool,
        "tool_input": {"scope": "project", "path": path, "content": content},
    }


def scrub_env(extra=None):
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in ("GOVERNANCE_REPO", "GOVERNANCE_ORIGIN", "MUSE_MEMORY_GOVERNANCE_HOME")
    }
    if extra:
        env.update(extra)
    return env


def run_core(
    repo=None, payload=None, *, cwd=None, env_extra=None, stdin_text=None, path_dir=None
):
    """Drive the shared core directly (plugin origin unless env_extra says so)."""
    env = scrub_env(env_extra)
    if repo is not None:
        env["GOVERNANCE_REPO"] = str(repo)
    if path_dir is not None:
        env["PATH"] = str(path_dir)
    if stdin_text is None:
        stdin_text = "" if payload is None else json.dumps(payload)
    return subprocess.run(
        ["/bin/bash", str(CORE)],
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
        env=env,
    )


def inbox_files(repo):
    inbox = repo / ".agents" / "memory-inbox"
    if not inbox.is_dir():
        return []
    return sorted(p for p in inbox.iterdir() if p.suffix == ".json")


def parse_deny(stdout):
    out = json.loads(stdout)
    spec = out["hookSpecificOutput"]
    assert spec["hookEventName"] == "PreToolUse"
    assert spec["permissionDecision"] == "deny"
    assert spec["permissionDecisionReason"].strip() != ""
    return spec


def write_hooks_json(repo, raw_or_obj):
    muse = repo / ".muse"
    muse.mkdir(parents=True, exist_ok=True)
    text = raw_or_obj if isinstance(raw_or_obj, str) else json.dumps(raw_or_obj)
    (muse / "hooks.json").write_text(text)


def hooks_json_for(command, matcher="add_memory|edit_memory"):
    return json.dumps(
        {
            "hooks": {
                "PreToolUse": [
                    {"matcher": matcher, "hooks": [{"command": command}]},
                ]
            }
        }
    )


def foreign_stub(repo):
    stub = repo / "hooks" / "foreign_gate.sh"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text("#!/usr/bin/env bash\nexit 0\n")
    stub.chmod(0o755)
    return stub


def minimal_path(tmp_path, *, with_jq=False, fake_jq=False):
    """PATH dir with only `cat` (+ real or fake jq) for degraded-env tests."""
    bin_dir = tmp_path / "minbin"
    bin_dir.mkdir()
    os.symlink(shutil.which("cat"), bin_dir / "cat")
    if with_jq:
        os.symlink(shutil.which("jq"), bin_dir / "jq")
    if fake_jq:
        fake = bin_dir / "jq"
        fake.write_text("#!/bin/sh\nexit 2\n")
        fake.chmod(0o755)
    return bin_dir


# ------------------------------------------------- SM-1/SM-2/SM-8/SM-13


def test_sm1_governed_diverts_and_denies(tmp_path):
    """SM-1: valid marker -> divert into inbox + deny, legacy-equivalent
    payload/deny schema; inbox ENOENT before the call is safe (SM-12)."""
    repo = make_repo(tmp_path)
    assert not (repo / ".agents" / "memory-inbox").exists()  # ENOENT -> safe
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "已代存 inbox" in spec["permissionDecisionReason"]
    files = inbox_files(repo)
    assert len(files) == 1
    assert files[0].name in spec["permissionDecisionReason"]  # abs path in reason
    saved = json.loads(files[0].read_text())
    assert saved["tool_name"] == "add_memory"
    assert saved["tool_input"]["content"] == "hello inbox"
    assert "_inbox_meta" not in saved  # add class: no CAS base
    assert str(repo) in spec["permissionDecisionReason"]
    assert stat.S_IMODE(files[0].stat().st_mode) == 0o600  # umask 077
    assert not list((repo / ".agents" / "memory-inbox").glob(".tmp-*"))  # atomic


def test_sm2_marker_absent_allows_native(tmp_path):
    """SM-2: ungoverned repo -> allow native (silent exit 0, zero landing)."""
    repo = make_repo(tmp_path, marker=None)
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert inbox_files(repo) == []


def test_sm8_non_memory_tool_self_filter(tmp_path):
    """SM-8: other tool_name -> self-filter early exit even when governed."""
    repo = make_repo(tmp_path)
    r = run_core(repo, mem_payload(tool="read_file"))
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert inbox_files(repo) == []


def test_sm13_empty_stdin_exits_zero():
    """SM-13: empty stdin -> nothing to divert, no landing, no deny."""
    r = run_core(None, None, stdin_text="")
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def test_sm13_non_json_without_memory_features_exits_zero(tmp_path):
    """SM-13: garbage payload without memory-tool features -> silent exit 0."""
    repo = make_repo(tmp_path)
    r = run_core(repo, None, stdin_text="totally not json")
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert inbox_files(repo) == []


# ------------------------------------------------------- SM-3/SM-4 matrix


@pytest.mark.parametrize("raw", INVALID_MARKERS)
def test_marker_matrix_invalid_deny_no_landing(tmp_path, raw):
    """SM-3/SM-4: any non-integer-1 marker denies without landing."""
    repo = make_repo(tmp_path, marker=raw)
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "marker" in spec["permissionDecisionReason"]
    assert str(repo) in spec["permissionDecisionReason"]
    assert inbox_files(repo) == []


# ------------------------------------------------ repo resolution (SM-10/11)


def test_sm10_cwd_subdir_resolves_repo_root_via_git(tmp_path):
    """SM-10: cwd in a repo subdir -> upward git resolution finds the root."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True)
    sub = repo / "sub"
    sub.mkdir()
    r = run_core(None, mem_payload(), cwd=sub)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    files = inbox_files(repo)
    assert len(files) == 1
    saved = json.loads(files[0].read_text())
    assert saved["tool_input"]["path"] == "new-note.md"


def test_stdin_workspace_field_resolves_repo(tmp_path):
    """P-WS frozen (live 2026-09-14): stdin workspace is a backward-compat
    fallback — resolves the repo when the authoritative cwd field is absent
    (no GOVERNANCE_REPO or $PWD dependence). R4 hardening: the field is
    honored only when it is itself a git root."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    payload = mem_payload()
    payload["workspace"] = str(repo)
    r = run_core(None, payload, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_stdin_cwd_field_resolves_repo(tmp_path):
    """P-WS frozen (live 2026-09-14): muse live stdin carries `cwd`
    (workspace root) and no `workspace`/`host_workspace` field — stdin cwd
    alone resolves the repo without GOVERNANCE_REPO or $PWD dependence."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    payload = mem_payload()
    payload["cwd"] = str(repo)
    r = run_core(None, payload, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_stdin_cwd_takes_priority_over_workspace(tmp_path):
    """P-WS frozen order (.cwd // .workspace // .host_workspace): with both
    fields present and $PWD outside any repo, the divert lands in the
    cwd-named repo — cwd is authoritative, workspace is a legacy fallback."""
    repo_cwd = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo_cwd)], check=True)
    repo_ws = tmp_path / "repo-ws"
    (repo_ws / ".agents" / "memory").mkdir(parents=True)
    write_marker(repo_ws, {"protocol": 1})
    subprocess.run(["git", "init", "-q", str(repo_ws)], check=True)
    payload = mem_payload()
    payload["workspace"] = str(repo_ws)
    payload["cwd"] = str(repo_cwd)
    r = run_core(None, payload, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo_cwd)) == 1
    assert inbox_files(repo_ws) == []


def test_stdin_repo_fields_null_fall_back_to_pwd(tmp_path):
    """P-WS frozen: null cwd/workspace/host_workspace fields 與欄位缺席同待遇
    （防禦性 pin；live 實證僅 transcript_path=null 與 workspace/host_workspace
    缺席）— the jq chain yields empty and $PWD upward resolution is unchanged
    (SM-10 pin)."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    sub = repo / "sub"
    sub.mkdir()
    payload = mem_payload()
    payload["cwd"] = None
    payload["workspace"] = None
    payload["host_workspace"] = None
    r = run_core(None, payload, cwd=sub)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm11_not_a_git_repo_allows_native(tmp_path):
    """SM-11: git present but cwd is not a repo -> explicit not-a-repo
    branch -> allow native (distinct from git-binary-missing branch)."""
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run_core(None, mem_payload(), cwd=plain)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def test_git_binary_missing_allows_native(tmp_path):
    """EP ⑦: git binary missing -> repo unresolvable, marker unobservable ->
    allow (separate arrival path from explicit not-a-repo; pinned separately)."""
    repo = make_repo(tmp_path)  # governed — still unreachable without git
    bin_dir = minimal_path(tmp_path, with_jq=True)
    r = run_core(None, mem_payload(), cwd=tmp_path, path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert inbox_files(repo) == []


# ------------------------------------------------------------ SM-12 safety


@pytest.mark.parametrize("segment", ["inbox", "agents", "repo-root"])
def test_sm12_symlink_segment_denies_no_landing(tmp_path, segment):
    """SM-12/A7: any existing symlink component on the inbox path denies
    without landing; ENOENT segments are safe (covered by SM-1)."""
    outside = tmp_path / "outside"
    outside.mkdir()
    repo = make_repo(tmp_path)
    if segment == "inbox":
        (repo / ".agents" / "memory-inbox").symlink_to(outside)
    elif segment == "agents":
        shutil.rmtree(repo / ".agents")
        (repo / ".agents").symlink_to(outside)
        write_marker(repo, {"protocol": 1})  # resolves through the symlink
    else:
        real = tmp_path / "repo-real"
        repo.rename(real)
        repo.symlink_to(real)
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "symlink" in spec["permissionDecisionReason"].lower()
    # nothing lands anywhere; the agents-segment case legitimately holds the
    # marker (written through the symlink during setup), exclude it
    landed = [p for p in outside.iterdir() if p.name != "memory-governance.json"]
    assert landed == []
    real_repo = tmp_path / "repo-real"
    if real_repo.exists():
        assert inbox_files(real_repo) == []


# --------------------------------------------- SM-5 legacy-owner surrender


def test_sm5_working_legacy_owner_plugin_origin_noop(tmp_path):
    """SM-5: working legacy owner (matcher covers both tools, command exists
    + executable + realpath != self) -> plugin-origin call is a no-op."""
    repo = make_repo(tmp_path)
    stub = foreign_stub(repo)
    write_hooks_json(repo, hooks_json_for(str(stub)))
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""
    assert inbox_files(repo) == []


def test_sm5_dual_origin_contrast(tmp_path):
    """EP C1: same repo, working legacy owner — plugin-origin no-op vs
    registered-origin (launcher env) deny+land."""
    repo = make_repo(tmp_path)
    stub = foreign_stub(repo)
    write_hooks_json(repo, hooks_json_for(str(stub)))
    payload = mem_payload()

    plugin_leg = run_core(repo, payload)
    assert plugin_leg.returncode == 0, plugin_leg.stderr
    assert plugin_leg.stdout == ""
    assert inbox_files(repo) == []

    registered_leg = run_core(
        repo, payload, env_extra={"GOVERNANCE_ORIGIN": "registered"}
    )
    assert registered_leg.returncode == 0, registered_leg.stderr
    parse_deny(registered_leg.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm5_negative_malformed_hooks_json_keeps_gating(tmp_path):
    repo = make_repo(tmp_path)
    write_hooks_json(repo, "{oops not json")
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm5_negative_stale_command_keeps_gating(tmp_path):
    repo = make_repo(tmp_path)
    write_hooks_json(repo, hooks_json_for(str(repo / "hooks" / "ghost.sh")))
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm5_negative_non_executable_command_keeps_gating(tmp_path):
    repo = make_repo(tmp_path)
    stub = foreign_stub(repo)
    stub.chmod(0o644)
    write_hooks_json(repo, hooks_json_for(str(stub)))
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm5_negative_partial_matcher_keeps_gating(tmp_path):
    repo = make_repo(tmp_path)
    stub = foreign_stub(repo)
    write_hooks_json(repo, hooks_json_for(str(stub), matcher="add_memory"))
    r = run_core(repo, mem_payload(tool="edit_memory"))
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_sm5_self_registration_is_not_an_owner(tmp_path):
    """EP C1 regression pin: hooks.json registering THIS shared script must
    not make the plugin surrender to itself (self-exclusion via realpath)."""
    repo = make_repo(tmp_path)
    write_hooks_json(repo, hooks_json_for(str(CORE)))
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


# --------------------------------------------------- degraded jq (jq-free)


def test_jq_missing_crude_hit_degraded_deny(tmp_path):
    """EP ⑦/C3: jq unavailable + crude memory-tool hit -> static jq-free
    deny with repair guidance (declared governance must not fail open)."""
    repo = make_repo(tmp_path)
    bin_dir = minimal_path(tmp_path)  # no jq at all
    r = run_core(repo, mem_payload(), path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)  # deny JSON itself must be jq-free
    reason = spec["permissionDecisionReason"].lower()
    assert "degraded" in reason
    assert "jq" in reason
    assert inbox_files(repo) == []


def test_jq_missing_non_memory_tool_exits_zero(tmp_path):
    bin_dir = minimal_path(tmp_path)  # no jq
    r = run_core(None, mem_payload(tool="read_file"), path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    assert r.stdout == ""


def test_broken_jq_governed_deny_fail_closed(tmp_path):
    """EP verification list: governed repo + internal jq failure -> deny."""
    repo = make_repo(tmp_path)
    bin_dir = minimal_path(tmp_path, fake_jq=True)
    r = run_core(repo, mem_payload(), path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "degraded" in spec["permissionDecisionReason"].lower()
    assert inbox_files(repo) == []


# --------------------------------------------------- CAS / lexical gates (⑥)


def test_cas_edit_existing_attaches_base_sha256(tmp_path):
    repo = make_repo(tmp_path)
    raw = (repo / ".agents" / "memory" / "note.md").read_bytes()
    r = run_core(
        repo, mem_payload(tool="edit_memory", path="note.md", content="new body")
    )
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    files = inbox_files(repo)
    assert len(files) == 1
    meta = json.loads(files[0].read_text())["_inbox_meta"]
    assert meta["base_path"] == "note.md"
    assert meta["base_sha256"] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    ("path", "setup"),
    [
        ("absolute", "absolute"),
        ("nested", "nested"),
        ("symlink", "symlink"),
        ("../memory-inbox/x.md", "sentinel"),
    ],
    ids=["absolute", "nested", "symlink", "traversal"],
)
def test_cas_lexical_gates_skip_enrichment(tmp_path, path, setup):
    """T3-1/T4-2 inheritance: unverified/unsafe P skips CAS enrichment while
    deny+land still happens."""
    repo = make_repo(tmp_path, pool_entry=(setup != "sentinel"))
    if setup == "sentinel":
        (repo / ".agents" / "memory-inbox").mkdir(parents=True)
        (repo / ".agents" / "memory-inbox" / "x.md").write_text("sentinel")
    elif setup == "nested":
        sub = repo / ".agents" / "memory" / "sub"
        sub.mkdir()
        (sub / "note.md").write_text("---\nname: n\n---\n\nb\n")
        path = "sub/note.md"
    elif setup == "symlink":
        pool = repo / ".agents" / "memory"
        (pool / "real.md").write_text("body\n")
        (pool / "alias.md").symlink_to("real.md")
        path = "alias.md"
    else:
        path = str(repo / ".agents" / "memory" / "note.md")
    r = run_core(repo, mem_payload(tool="edit_memory", path=path, content="x"))
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    files = inbox_files(repo)
    assert len(files) == 1
    assert "_inbox_meta" not in json.loads(files[0].read_text())


# ---------------------------------- review round findings (R1-R7/C-C1-C-C5)


@pytest.mark.parametrize(
    "matcher",
    ["xadd_memory|xedit_memory", "add_memory_backup|edit_memory_backup"],
)
def test_legacy_owner_decoy_matcher_keeps_gating(tmp_path, matcher):
    """C-C1: matcher coverage must match whole tool-name tokens — substring
    decoys ("xadd_memory"-style) are NOT a working legacy owner."""
    repo = make_repo(tmp_path)
    stub = foreign_stub(repo)
    write_hooks_json(repo, hooks_json_for(str(stub), matcher=matcher))
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)  # this hook keeps gating (no surrender)
    assert len(inbox_files(repo)) == 1


def test_deny_schema_valid_with_newline_in_repo_path(tmp_path):
    """R1/C-C2: a repo path containing a newline must still yield a
    schema-valid deny — parse_deny (json.loads) fails on raw control bytes,
    so merely parsing IS the regression proof."""
    repo = tmp_path / "we\nird"
    (repo / ".agents" / "memory").mkdir(parents=True)
    write_marker(repo, {"protocol": 1})
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "已代存 inbox" in spec["permissionDecisionReason"]
    assert len(inbox_files(repo)) == 1


def test_git_execution_error_denies_fail_closed(tmp_path):
    """C-C3: git present but rev-parse failing with a non-'not a git
    repository' error denies (workspace state undeterminable) — distinct
    from the determined non-repo lane which allows native."""
    repo = make_repo(tmp_path)
    bin_dir = minimal_path(tmp_path, with_jq=True)
    fake_git = bin_dir / "git"
    fake_git.write_text("#!/bin/sh\necho 'fatal: unknown failure' >&2\nexit 128\n")
    fake_git.chmod(0o755)
    r = run_core(repo=None, payload=mem_payload(), cwd=repo, path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "rev-parse failed" in spec["permissionDecisionReason"]


@pytest.mark.parametrize("raw", ['{"protocol": 1.0}', '{"protocol": 1e0}'])
def test_marker_numeric_one_lexical_forms_valid(tmp_path, raw):
    """C-C4/R5 contract ruling: any JSON number equal to 1 is valid —
    lexical 1.0/1e0 are the same number and divert."""
    repo = make_repo(tmp_path, marker=raw)
    r = run_core(repo, mem_payload())
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_stdin_workspace_bogus_falls_back_to_cwd(tmp_path):
    """R4 seam hardening (P-WS frozen order): an stdin workspace value that
    is not itself a git root is ignored — with no cwd field either,
    resolution falls back to $PWD (cwd-in-repo)."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    payload = mem_payload()
    payload["workspace"] = str(tmp_path / "nonexistent-bogus")
    r = run_core(repo=None, payload=payload, cwd=repo)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_stdin_bogus_workspace_with_cwd_resolves_cwd(tmp_path):
    """P-WS frozen: a bogus (non-git-root) workspace alongside a valid cwd
    still resolves the cwd-named repo — a stale workspace fallback must not
    mask cwd authority ($PWD outside every repo)."""
    repo = make_repo(tmp_path)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    payload = mem_payload()
    payload["workspace"] = str(tmp_path / "nonexistent-bogus")
    payload["cwd"] = str(repo)
    r = run_core(None, payload, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    assert len(inbox_files(repo)) == 1


def test_no_jq_innocent_mention_denies_degraded(tmp_path):
    """R6 spec pin: degraded tooling (no jq) + stdin merely mentioning the
    tool names in a NON-memory tool call conservatively denies."""
    repo = make_repo(tmp_path, marker=None)
    bin_dir = minimal_path(tmp_path)  # no jq
    payload = {
        "tool_name": "Edit",
        "tool_input": {"path": "doc.md", "content": "see add_memory docs"},
    }
    r = run_core(repo, payload, path_dir=bin_dir)
    assert r.returncode == 0, r.stderr
    spec = parse_deny(r.stdout)
    assert "degraded" in spec["permissionDecisionReason"].lower()
    assert inbox_files(repo) == []


def test_non_md_pool_path_skips_cas_enrichment(tmp_path):
    """R7b: lexical gate — a non-.md pool-relative path never gains CAS
    meta (deny+land still happens)."""
    repo = make_repo(tmp_path)
    (repo / ".agents" / "memory" / "notes.txt").write_text("x")
    r = run_core(repo, mem_payload(tool="edit_memory", path="notes.txt", content="y"))
    assert r.returncode == 0, r.stderr
    parse_deny(r.stdout)
    files = inbox_files(repo)
    assert len(files) == 1
    assert "_inbox_meta" not in json.loads(files[0].read_text())
