"""Tests for hooks/memory-write-sensor.py + hooks/memory-dirty-sensor.py (AIR-56).

Sensors read CC hook JSON on stdin, append pool-scoped events to
$MEMORY_HOOK_LOG (overridden to tmp in tests). Never touch the live pool:
fixtures build a fake pool (dir + MEMORY.md) under tmp_path.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
WRITE_SENSOR = HOOKS / "memory-write-sensor.py"
DIRTY_SENSOR = HOOKS / "memory-dirty-sensor.py"


def make_pool(tmp_path):
    pool = tmp_path / "pool"
    pool.mkdir()
    (pool / "MEMORY.md").write_text("# index\n")
    entry = pool / "note.md"
    entry.write_text("---\nname: note.md\n---\n\nbody\n")
    return pool, entry


def run_sensor(script, payload, tmp_path):
    import os

    log = tmp_path / "hook-events.jsonl"
    env = dict(os.environ, MEMORY_HOOK_LOG=str(log))
    inp = payload if isinstance(payload, str) else json.dumps(payload)
    r = subprocess.run(
        [sys.executable, str(script)],
        input=inp,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    lines = []
    if log.is_file():
        lines = [json.loads(ln) for ln in log.read_text().splitlines() if ln.strip()]
    return r, lines


def test_write_sensor_records_pool_edit(tmp_path):
    """AIR-56: PostToolUse Edit on pool entry emits actor evidence."""
    _, entry = make_pool(tmp_path)
    payload = {
        "session_id": "sess_1",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(entry)},
        "tool_use_id": "tu_1",
        "agent_id": "ag_9",
        "agent_type": "Task",
    }
    r, lines = run_sensor(WRITE_SENSOR, payload, tmp_path)
    assert r.returncode == 0, r.stderr
    assert len(lines) == 1
    ev = lines[0]
    assert ev["kind"] == "post_tool_use"
    assert ev["file_path"] == str(entry.resolve())
    assert (ev["session_id"], ev["tool_use_id"]) == ("sess_1", "tu_1")
    assert ev["agent_id"] == "ag_9"


def test_write_sensor_ignores_non_pool_and_other_tools(tmp_path):
    """AIR-56: non-pool paths / non-Edit-Write tools / MEMORY.md emit nothing."""
    pool, entry = make_pool(tmp_path)
    other = tmp_path / "other.md"
    other.write_text("x")
    cases = [
        {
            "session_id": "s",
            "tool_name": "Read",
            "tool_input": {"file_path": str(entry)},
        },
        {
            "session_id": "s",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(other)},
        },
        {
            "session_id": "s",
            "tool_name": "Write",
            "tool_input": {"file_path": str(pool / "MEMORY.md")},
        },
        {"session_id": "s", "tool_name": "Edit", "tool_input": {}},
    ]
    for payload in cases:
        r, lines = run_sensor(WRITE_SENSOR, payload, tmp_path)
        assert r.returncode == 0
        assert lines == []


def test_sensors_malformed_stdin_still_exit_zero(tmp_path):
    """AIR-56: a sensor must never fail the tool call (exit 0 on garbage)."""
    for script in (WRITE_SENSOR, DIRTY_SENSOR):
        for bad in ("", "not json{", "[1,2]"):
            r, lines = run_sensor(script, bad, tmp_path)
            assert r.returncode == 0, (script, bad)
            assert lines == []


def test_dirty_sensor_records_watcher_not_writer(tmp_path):
    """AIR-56: FileChanged emits dirty evidence with watcher session only."""
    _, entry = make_pool(tmp_path)
    payload = {"session_id": "watcher_A", "file_path": str(entry)}
    r, lines = run_sensor(DIRTY_SENSOR, payload, tmp_path)
    assert r.returncode == 0, r.stderr
    assert len(lines) == 1
    ev = lines[0]
    assert ev["kind"] == "file_changed"
    assert ev["watcher_session"] == "watcher_A"
    assert "session_id" not in ev  # never pose as the writer
    assert ev["file_path"] == str(entry.resolve())


def test_log_override_falls_back_when_relative_or_pool_file(tmp_path):
    """AIR-56 F3: relative override or pool-entry target falls back safely."""
    import os

    _, entry = make_pool(tmp_path)
    payload = {
        "session_id": "s",
        "tool_name": "Write",
        "tool_input": {"file_path": str(entry)},
        "tool_use_id": "t1",
    }
    # relative override -> default log, not cwd (HOME isolated: never touch
    # the real default log from tests)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    env = dict(os.environ, MEMORY_HOOK_LOG="rel-log.jsonl", HOME=str(fake_home))
    r = subprocess.run(
        [sys.executable, str(WRITE_SENSOR)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env=env,
        cwd=str(tmp_path),
    )
    assert r.returncode == 0
    assert not (tmp_path / "rel-log.jsonl").is_file()
    # override pointing at a pool entry file -> refused, entry untouched
    before = entry.read_text()
    env = dict(os.environ, MEMORY_HOOK_LOG=str(entry), HOME=str(fake_home))
    r = subprocess.run(
        [sys.executable, str(WRITE_SENSOR)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert r.returncode == 0
    assert entry.read_text() == before


def test_log_rotation_single_generation(tmp_path):
    """F4: >2 MiB log rotates to .prev (old content) and new log holds only the new line."""
    _, entry = make_pool(tmp_path)
    log = tmp_path / "hook-events.jsonl"
    filler_line = json.dumps({"kind": "old", "pad": "x" * 512}) + "\n"
    lines_needed = (2 * 1024 * 1024 // len(filler_line)) + 10
    log.write_text(filler_line * lines_needed)
    assert log.stat().st_size > 2 * 1024 * 1024
    payload = {
        "session_id": "sess_rot",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(entry)},
        "tool_use_id": "tu_rot",
    }
    r, lines = run_sensor(WRITE_SENSOR, payload, tmp_path)
    assert r.returncode == 0, r.stderr
    prev = tmp_path / "hook-events.jsonl.prev"
    assert prev.is_file(), "old generation must survive as .prev"
    assert "old" in prev.read_text()[:200]
    assert len(lines) == 1
    assert lines[0]["session_id"] == "sess_rot"


def test_underscore_prefixed_pool_file_excluded(tmp_path):
    """Pool maintenance files (_inventory.md etc.) are not entries: no event."""
    pool, _ = make_pool(tmp_path)
    underscore = pool / "_inventory.md"
    underscore.write_text("# projection\n")
    payload = {
        "session_id": "sess_u",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(underscore)},
        "tool_use_id": "tu_u",
    }
    r, lines = run_sensor(WRITE_SENSOR, payload, tmp_path)
    assert r.returncode == 0, r.stderr
    assert lines == []


def test_watch_seed_outputs_pool_entry_watch_paths():
    """SessionStart seed lists pool entries (excl MEMORY.md/_-prefix) as watchPaths; exits 0."""
    import sys as _sys

    r = subprocess.run(
        [_sys.executable, str(HOOKS / "memory-watch-seed.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "SessionStart"
    paths = hso["watchPaths"]
    assert isinstance(paths, list)
    if paths:  # live pool present on this machine
        assert all(p.endswith(".md") for p in paths)
        assert not any(p.endswith("MEMORY.md") or "/_" in p for p in paths)


@pytest.mark.parametrize("script", [WRITE_SENSOR, DIRTY_SENSOR])
@pytest.mark.parametrize(
    "destination",
    [
        "MEMORY.md",
        "_inventory.md",
        "_generate_index.py",
        "nested/log.jsonl",
        "file-alias",
        "directory-alias",
        "outbound-alias",
        "nested-outbound-alias",
    ],
)
def test_log_destination_protects_entire_pool(tmp_path, script, destination):
    """S: accepted H1 forbids append/rotation anywhere in a pool, including aliases."""
    pool, entry = make_pool(tmp_path)
    target = pool / destination
    if destination == "file-alias":
        target = tmp_path / "external.jsonl"
        target.symlink_to(pool / "MEMORY.md")
    elif destination == "directory-alias":
        alias = tmp_path / "alias"
        alias.symlink_to(pool, target_is_directory=True)
        target = alias / "nested" / "log.jsonl"
    elif destination in ("outbound-alias", "nested-outbound-alias"):
        outside = tmp_path / "outside"
        outside.mkdir()
        (pool / "out").symlink_to(outside, target_is_directory=True)
        target = pool / "out" / "log.jsonl"
        if destination == "nested-outbound-alias":
            alias = tmp_path / "alias"
            alias.symlink_to(pool, target_is_directory=True)
            target = alias / "out" / "log.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("protected\n")
    before = target.read_bytes()
    home = tmp_path / "home"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(entry)},
        "file_path": str(entry),
    }
    result = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ, HOME=str(home), MEMORY_HOOK_LOG=str(target)),
    )
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == before
    assert not target.with_suffix(target.suffix + ".prev").exists()
    fallback = home / ".local/share/ai-guide/memory-hook-events.jsonl"
    assert len(fallback.read_text().splitlines()) == 1


@pytest.mark.parametrize("mode", ["ancestor", "file-alias", "rotation-alias"])
def test_unsafe_default_log_is_not_written(tmp_path, mode):
    """S: H1 requires default and rotation destination validation, with no unsafe fallback."""
    pool, entry = make_pool(tmp_path)
    home = tmp_path / "home"
    log = home / ".local/share/ai-guide/memory-hook-events.jsonl"
    log.parent.mkdir(parents=True)
    protected = pool / "MEMORY.md"
    if mode == "ancestor":
        (home / "MEMORY.md").write_text("# home is a pool\n")
    elif mode == "file-alias":
        log.symlink_to(protected)
    else:
        log.write_text("x" * (2 * 1024 * 1024 + 1))
        log.with_suffix(".jsonl.prev").symlink_to(protected)
    before = protected.read_bytes()
    log_before = log.read_bytes() if log.exists() else None
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(entry)}}
    result = subprocess.run(
        [sys.executable, str(WRITE_SENSOR)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ, HOME=str(home), MEMORY_HOOK_LOG="relative.jsonl"),
    )
    assert result.returncode == 0, result.stderr
    assert protected.read_bytes() == before
    assert (log.read_bytes() if log.exists() else None) == log_before
    if mode == "rotation-alias":
        assert log.with_suffix(".jsonl.prev").is_symlink()


def test_log_rotation_alias_falls_back_without_touching_pool(tmp_path):
    """S: H1 protects a pool-targeting rotation sibling as well as the append path."""
    pool, entry = make_pool(tmp_path)
    log = tmp_path / "events.jsonl"
    old = "x" * (2 * 1024 * 1024 + 1)
    log.write_text(old)
    prev = log.with_suffix(".jsonl.prev")
    prev.symlink_to(pool / "MEMORY.md")
    before = (pool / "MEMORY.md").read_bytes()
    home = tmp_path / "home"
    result = subprocess.run(
        [sys.executable, str(WRITE_SENSOR)],
        input=json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": str(entry)}}
        ),
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ, HOME=str(home), MEMORY_HOOK_LOG=str(log)),
    )
    assert result.returncode == 0, result.stderr
    assert prev.is_symlink()
    assert log.read_text() == old
    assert (pool / "MEMORY.md").read_bytes() == before
    assert (home / ".local/share/ai-guide/memory-hook-events.jsonl").is_file()
