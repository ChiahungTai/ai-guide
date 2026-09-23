#!/usr/bin/env python3
"""Shared bits for memory hook sensors (AIR-56 F6 single-source).

Hook runtime is python 3.9 — no 3.10+ syntax in this file. Imported by
memory-write-sensor.py / memory-dirty-sensor.py via sys.path on __file__ dir.

Conventions (defined once here):
- pool entry = absolute .md path whose parent holds MEMORY.md, excluding
  MEMORY.md itself and _* files.
- event timestamps carry microseconds (F2): same-second distinct writes must
  keep order; sensor clock is wall time, ties across channels still possible.
- log destinations and rotation siblings must be outside every pool ancestor,
  including lexical and symlink paths. Unsafe overrides use the validated
  default; if neither is safe, skip telemetry. Caller still exits 0.
- size-bounded append (F4): single-generation rotation at 2 MiB.
"""

import json
import os
import time
from pathlib import Path

DEFAULT_LOG = Path.home() / ".local" / "share" / "ai-guide" / "memory-hook-events.jsonl"
POOL_INDEX = "MEMORY.md"
MAX_LOG_BYTES = 2 * 1024 * 1024


def utc_now():
    t = time.time()
    tt = time.gmtime(t)
    usec = int((t - int(t)) * 1000000)
    return (
        f"{tt.tm_year:04d}-{tt.tm_mon:02d}-{tt.tm_mday:02d}"
        f"T{tt.tm_hour:02d}:{tt.tm_min:02d}:{tt.tm_sec:02d}.{usec:06d}+00:00"
    )


def is_pool_entry(file_path):
    try:
        p = Path(file_path).expanduser() if isinstance(file_path, str) else None
        if p is None or not p.is_absolute() or p.suffix != ".md":
            return None
        if p.name == POOL_INDEX or p.name.startswith("_"):
            return None
        if (p.parent / POOL_INDEX).is_file():
            return str(p.resolve())
    except OSError:
        return None
    return None


def _outside_pool(path):
    """Containment is independent of the narrower event attribution filter."""
    if not path.is_absolute():
        return False
    # Resolve every lexical ancestor too: alias/pool/outbound-symlink must
    # remain protected even when the final resolved target is outside pool.
    for lexical in (path,) + tuple(path.parents):
        resolved = lexical.resolve()
        for ancestor in (lexical, resolved) + tuple(resolved.parents):
            if (ancestor / POOL_INDEX).is_file():
                return False
    return True


def log_path():
    for raw in (os.environ.get("MEMORY_HOOK_LOG"), DEFAULT_LOG):
        if not raw:
            continue
        try:
            cand = Path(raw).expanduser()
            resolved = cand.resolve()
            # emit rotates next to the canonical append path; validate both
            # spellings so neither an alias nor its sibling bypasses policy.
            paths = (
                cand,
                resolved,
                cand.with_suffix(cand.suffix + ".prev"),
                resolved.with_suffix(resolved.suffix + ".prev"),
            )
            if all(_outside_pool(path) for path in paths):
                return resolved
        except (OSError, RuntimeError, ValueError):
            continue
    return None


def emit(event):
    try:
        lp = log_path()
        if lp is None:
            return
        lp.parent.mkdir(parents=True, exist_ok=True)
        if lp.is_file() and lp.stat().st_size > MAX_LOG_BYTES:
            prev = lp.with_suffix(lp.suffix + ".prev")
            try:
                if prev.is_file():
                    prev.unlink()
            except OSError:
                pass
            try:
                lp.rename(prev)
            except OSError:
                pass
        with open(lp, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass
