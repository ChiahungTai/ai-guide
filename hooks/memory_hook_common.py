#!/usr/bin/env python3
"""Shared bits for memory hook sensors (AIR-56 F6 single-source).

Hook runtime is python 3.9 — no 3.10+ syntax in this file. Imported by
memory-write-sensor.py / memory-dirty-sensor.py via sys.path on __file__ dir.

Conventions (defined once here):
- pool entry = absolute .md path whose parent holds MEMORY.md, excluding
  MEMORY.md itself and _* files.
- event timestamps carry microseconds (F2): same-second distinct writes must
  keep order; sensor clock is wall time, ties across channels still possible.
- log path validation (F3): override must be absolute and must not itself be
  a pool entry file (never append JSONL into memory content); violations fall
  back to the default. Fail-closed, caller still exits 0.
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


def log_path():
    override = os.environ.get("MEMORY_HOOK_LOG")
    if override:
        cand = Path(override).expanduser()
        if cand.is_absolute() and is_pool_entry(str(cand)) is None:
            return cand
    return DEFAULT_LOG


def emit(event):
    try:
        lp = log_path()
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
