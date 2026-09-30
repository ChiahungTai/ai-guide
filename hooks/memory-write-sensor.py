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
  registered on BOTH harnesses (CC settings.json +
  governance/registrations/zcode.json template and live config). Payload schema drift
  on the ZCode side is absorbed by this sensor's fail-safe filters (worst
  case: silent no-op; coverage boundary in AIR-56 card).
- Always exits 0: a sensor must never block or fail the tool call.
- Deployed runtime is governance-resolved Python 3.12; keep Python 3.9 syntax
  compatibility during the mixed-session / rollback window.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hook_payload_compat as compat
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
    return value if value in ("claude", "zcode", "grok") else "unknown"


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, OSError):
        return 0
    try:
        if not isinstance(data, dict):
            return 0
        # 容器鍵雙讀（AIR-218）：grok camel 形（toolName/toolInput/sessionId/
        # toolUseId）經 compat 層；search_replace→Edit 映射。agent_id/agent_type
        # 兩欄 grok 合併為單欄 subagentType（值層合併非鍵正規化）——grok 下
        # 兩欄記 None（sensor 容錯面，最壞缺欄非阻斷）。
        if compat.tool_name(data) not in ("Edit", "Write"):
            return 0
        tool_input = compat.tool_input(data) or {}
        canon = is_pool_entry(tool_input.get("file_path", ""))
        if canon is None:
            return 0
        emit(
            {
                "kind": "post_tool_use",
                "source": cli_source(sys.argv),
                "ts": utc_now(),
                "session_id": compat.session_id(data),
                "tool": compat.tool_name(data),
                "file_path": canon,
                "tool_use_id": compat.field(data, "tool_use_id", "toolUseId"),
                "agent_id": data.get("agent_id"),
                "agent_type": data.get("agent_type"),
            }
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
