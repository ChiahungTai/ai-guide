#!/usr/bin/env python3
"""CC FileChanged sensor (AIR-56): memory pool mutation dirty-bit, evidence only.

FileChanged fires on watched-file disk change (Edit/Write/Bash/external —
mirror docs). It CANNOT attribute: the session_id in its input is the WATCHER,
not the writer. So this sensor emits dirty evidence only; the collector
attaches it per entry (`dirty_after_tracked`) and the hash leg decides.

Scope contract (fail-loud):
- Same shared pool filter (`memory_hook_common.is_pool_entry`).
- Wiring (landed 2026-09-09): FileChanged matcher SEEDS are cwd-scoped
  literal filenames, so a pool outside any repo cwd cannot be seed-watched;
  the pool is watched instead via memory-watch-seed.py (SessionStart returns
  `watchPaths`, per CC mirror docs) with this group on an omitted matcher.
  Live firing is verified from the next session's hook log; until then the
  hash leg remains the external-write backstop.
- Always exits 0. Deployed runtime is governance-resolved Python 3.12; keep
  Python 3.9 syntax compatibility during the mixed-session / rollback window.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_hook_common import emit, is_pool_entry, utc_now


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return 0
    try:
        if not isinstance(data, dict):
            return 0
        # FileChanged input carries the changed path under file_path (CC
        # mirror); fall back to tool_input.file_path defensively.
        tool_input = data.get("tool_input") or {}
        raw_path = data.get("file_path") or tool_input.get("file_path", "")
        canon = is_pool_entry(raw_path)
        if canon is None:
            return 0
        emit(
            {
                "kind": "file_changed",
                "source": "claude",
                "ts": utc_now(),
                "watcher_session": data.get("session_id"),
                "file_path": canon,
            }
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
