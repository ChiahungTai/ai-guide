"""Tests for hooks/setup-memory-symlinks.sh + hooks/verify-memory-topology.sh.

Both scripts derive REPO from their own location and HOME from the
environment, so fixtures build a tmp skeleton (tmp/HOME + tmp/repo) and
copy the scripts in. Never touch the live home dirs or the live pool.
"""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"


def make_skeleton(tmp_path, with_pool=True, with_cc_memory=True):
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    (repo / "hooks").mkdir(parents=True)
    for name in ("setup-memory-symlinks.sh", "verify-memory-topology.sh"):
        shutil.copy(HOOKS / name, repo / "hooks" / name)
    env = dict(os.environ, HOME=str(home))
    pool = repo / ".agents" / "memory"
    if with_pool:
        pool.mkdir(parents=True)
        (pool / "MEMORY.md").write_text("# index\n")
        (pool / "_generate_index.py").write_text("import sys\nsys.exit(0)\n")
    cc_mem = home / ".claude" / "projects" / str(repo).replace("/", "-") / "memory"
    if with_cc_memory:
        cc_mem.mkdir(parents=True)
        (cc_mem / "old-note.md").write_text("stale\n")
    return home, repo, pool, env


def repo_encoded(repo):
    return str(repo).replace("/", "-")


def test_symlinks_dry_run_changes_nothing(tmp_path):
    """Default is dry-run: plan printed, tree untouched."""
    _, repo, _, env = make_skeleton(tmp_path)
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "setup-memory-symlinks.sh")],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "dry-run" in r.stdout
    cc_mem = Path(env["HOME"]) / ".claude" / "projects" / repo_encoded(repo) / "memory"
    assert (cc_mem / "old-note.md").is_file()  # untouched, no backup made
    assert not list(cc_mem.parent.glob("memory.bak-*"))


def test_symlinks_apply_backs_up_and_links(tmp_path):
    """--apply: existing entries moved to .bak-<ts>, symlinks land."""
    home, repo, pool, env = make_skeleton(tmp_path)
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "setup-memory-symlinks.sh"), "--apply"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    cc_mem = home / ".claude" / "projects" / repo_encoded(repo) / "memory"
    assert cc_mem.is_symlink() and os.readlink(cc_mem) == str(pool)
    baks = list(cc_mem.parent.glob("memory.bak-*"))
    assert len(baks) == 1 and (baks[0] / "old-note.md").is_file()
    zc = list((home / ".zcode" / "cli" / "memories" / "projects").glob("repo-*/memory"))
    assert len(zc) == 1 and os.readlink(zc[0]) == str(pool)


def test_symlinks_apply_idempotent(tmp_path):
    """Second --apply is a no-op (OK lines, no new backups)."""
    _, repo, _, env = make_skeleton(tmp_path)
    s = str(repo / "hooks" / "setup-memory-symlinks.sh")
    assert (
        subprocess.run(
            ["bash", s, "--apply"], env=env, capture_output=True, check=False
        ).returncode
        == 0
    )
    r = subprocess.run(
        ["bash", s, "--apply"], capture_output=True, text=True, env=env, check=False
    )
    assert r.returncode == 0, r.stderr
    assert "already points at target" in r.stdout


def test_symlinks_missing_pool_fails_loud(tmp_path):
    """No pool -> fail with transfer instructions, exit != 0."""
    _, repo, _, env = make_skeleton(tmp_path, with_pool=False)
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "setup-memory-symlinks.sh"), "--apply"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode != 0
    assert "transfer" in r.stderr


def test_symlinks_apply_without_cc_dir_links_zcode_direct(tmp_path):
    """CC-less skeleton (no ~/.claude/projects): --apply exit 0, ZCode -> pool.

    AIR-223: the CC alias is optional compat; its absence must not block
    the required ZCode leg (direct-anchor topology).
    """
    home, repo, pool, env = make_skeleton(tmp_path, with_cc_memory=False)
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "setup-memory-symlinks.sh"), "--apply"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stderr
    assert "SKIP CC alias (optional; project dir absent)" in r.stdout
    cc_mem = home / ".claude" / "projects" / repo_encoded(repo) / "memory"
    assert not cc_mem.exists() and not cc_mem.is_symlink()
    h = hashlib.sha256(str(repo).encode()).hexdigest()[:16]
    zc_mem = (
        home / ".zcode" / "cli" / "memories" / "projects" / f"repo-{h}" / "memory"
    )
    assert zc_mem.is_symlink() and os.readlink(zc_mem) == str(pool)


def test_verify_green_without_cc_dir(tmp_path):
    """CC-less skeleton: verify exit 0; CC leg printed as SKIP, not FAIL."""
    _, repo, _, env = make_skeleton(tmp_path, with_cc_memory=False)
    setup = str(repo / "hooks" / "setup-memory-symlinks.sh")
    assert (
        subprocess.run(
            ["bash", setup, "--apply"], env=env, capture_output=True, check=False
        ).returncode
        == 0
    )
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "verify-memory-topology.sh")],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SKIP CC alias" in r.stdout
    assert "0 failed" in r.stdout


def test_verify_topology_green_on_good_tree(tmp_path):
    """Verify script passes on a correctly linked skeleton."""
    home, repo, pool, env = make_skeleton(tmp_path, with_cc_memory=False)
    cc_mem = home / ".claude" / "projects" / repo_encoded(repo) / "memory"
    cc_mem.parent.mkdir(parents=True)
    cc_mem.symlink_to(pool)

    h = hashlib.sha256(str(repo).encode()).hexdigest()[:16]
    zc_mem = home / ".zcode" / "cli" / "memories" / "projects" / f"repo-{h}" / "memory"
    zc_mem.parent.mkdir(parents=True)
    zc_mem.symlink_to(pool)
    muse_dir = repo / ".muse"
    muse_dir.mkdir()
    fake_hook = repo / "hooks" / "fake-hook.sh"
    fake_hook.write_text("#!/bin/sh\nexit 0\n")
    fake_hook.chmod(0o755)
    (muse_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "x", "hooks": [{"command": str(fake_hook)}]}
                    ]
                }
            }
        )
    )
    r = subprocess.run(
        ["bash", str(repo / "hooks" / "verify-memory-topology.sh")],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 failed" in r.stdout
