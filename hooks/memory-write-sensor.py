#!/usr/bin/env python3
"""CC PostToolUse sensor (AIR-56): memory pool write evidence, zero friction.

Fires after Edit|Write succeeds (PostToolUse = post-success, unlike PreToolUse
which also fires on denied/failed calls). Emits one JSONL line per pool write
for the telemetry collector (`--hook-events`) to normalize.

Scope contract (fail-loud, not fake coverage):
- Only Edit|Write whose file_path resolves inside a memory pool (shared
  `memory_hook_common.is_pool_entry`).
- Bash redirects / external processes are INVISIBLE here (see
  memory-dirty-sensor.py FileChanged + the hash leg in `attribution`).
- ZCode 3.7.7 events DO include PostToolUse (04-report measured subset);
  registered on BOTH harnesses since 2026-09-09 (CC settings.json +
  zcode-registration.json template and live config). Payload schema drift
  on the ZCode side is absorbed by this sensor's fail-safe filters (worst
  case: silent no-op; coverage boundary in AIR-56 card).
- Always exits 0: a sensor must never block or fail the tool call.
- Hook runtime is python 3.9 — no 3.10+ syntax in this file.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memory_hook_common import emit, is_pool_entry, utc_now


def cli_source(argv):
    """--source <name> from the registering harness, validated against an
    allowlist. Unknown/missing values emit "unknown" (visible in telemetry)
    instead of silently relabeling as claude — silent mislabeling is exactly
    the drift class this sensor exists to expose (2026-09-17 audit: 76% of
    events were mislabeled before --source existed).

    Manual argv scan (not argparse) keeps the always-exit-0 contract —
    argparse would exit 2 on malformed args.
    """
    value = None
    for i, arg in enumerate(argv):
        if arg == "--source" and i + 1 < len(argv):
            value = argv[i + 1]
            break
    return value if value in ("claude", "zcode") else "unknown"


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return 0
    try:
        if not isinstance(data, dict):
            return 0
        if data.get("tool_name") not in ("Edit", "Write"):
            return 0
        tool_input = data.get("tool_input") or {}
        canon = is_pool_entry(tool_input.get("file_path", ""))
        if canon is None:
            return 0
        emit(
            {
                "kind": "post_tool_use",
                "source": cli_source(sys.argv),
                "ts": utc_now(),
                "session_id": data.get("session_id"),
                "tool": data.get("tool_name"),
                "file_path": canon,
                "tool_use_id": data.get("tool_use_id"),
                "agent_id": data.get("agent_id"),
                "agent_type": data.get("agent_type"),
            }
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
