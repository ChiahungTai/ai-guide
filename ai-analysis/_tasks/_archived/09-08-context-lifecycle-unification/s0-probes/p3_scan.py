"""P3: muse sessions 09/07-08 forensics — rules_file text_bytes per workspace (streaming, read-only)."""

import json
import os
import re
from collections import Counter

BASE = os.path.expanduser("~/.local/share/muse/sessions/2026/09")
DAYS = ["07", "08"]

DIAG = re.compile(
    r'\\"kind\\":\\"context_block_diagnostic\\",\\"block_id\\":\\"([^"\\]+)\\"'
)
WORKSPACE_PATH = re.compile(r"/Users/ctai/Github/([A-Za-z0-9_.-]+)")


def scan_file(path):
    """Stream one session.jsonl; return (rules_file_bytes_list, all_blocks Counter, workspace_guess, payload_types)."""
    rules_bytes = []
    blocks = Counter()
    ws_counter = Counter()
    diag_records = []  # (sequence, recorded_at, block_id, text_bytes, max_bytes, lifecycle)
    ptypes = Counter()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            # cheap pre-filter before any json parsing
            if (
                "context_block_diagnostic" not in line
                and "/Users/ctai/Github/" not in line
            ):
                continue
            # workspace guess: count repo-name occurrences on the raw line
            for m in WORKSPACE_PATH.finditer(line):
                ws_counter[m.group(1)] += 1
            if "context_block_diagnostic" not in line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            children = frame.get("children")
            if children is None:
                children = [
                    {
                        "child_index": 0,
                        "record_json": json.dumps(frame, ensure_ascii=False),
                    }
                ]
            for child in children:
                try:
                    rec = json.loads(child.get("record_json", ""))
                except json.JSONDecodeError:
                    continue
                pt = rec.get("payload_type", "")
                if "context_block" not in line and "workspace" not in pt:
                    continue
                ptypes[pt] += 1
                payload = rec.get("payload", {})
                ev = payload.get("event") if isinstance(payload, dict) else None
                if (
                    isinstance(ev, dict)
                    and ev.get("kind") == "context_block_diagnostic"
                ):
                    bid = ev.get("block_id")
                    tb = ev.get("text_bytes")
                    mb = ev.get("max_bytes")
                    blocks[bid] += 1
                    if bid == "rules_file":
                        rules_bytes.append(tb)
                        diag_records.append(
                            (
                                rec.get("sequence"),
                                rec.get("recorded_at"),
                                bid,
                                tb,
                                mb,
                                ev.get("lifecycle"),
                            )
                        )
    ws = ws_counter.most_common(1)[0][0] if ws_counter else "?"
    return rules_bytes, blocks, ws, ptypes, diag_records


results = []
for day in DAYS:
    day_dir = os.path.join(BASE, day)
    if not os.path.isdir(day_dir):
        continue
    for sid in sorted(os.listdir(day_dir)):
        path = os.path.join(day_dir, sid, "session.jsonl")
        if not os.path.isfile(path):
            continue
        try:
            rb, blocks, ws, ptypes, diags = scan_file(path)
        except Exception as e:
            print(f"ERROR {sid}: {e}")
            continue
        results.append((day, sid, ws, rb, blocks, diags))

print(f"scanned {len(results)} sessions")
print()
print(
    "== per-session: day | session | workspace | rules_file text_bytes (all observations) =="
)
for day, sid, ws, rb, blocks, diags in results:
    if not rb:
        print(f"{day} {sid[:13]} ws={ws} rules_file: (none)")
        continue
    print(f"{day} {sid[:13]} ws={ws} rules_file text_bytes={rb} n_obs={len(rb)}")

print()
print("== aggregate by workspace ==")
by_ws = {}
for day, sid, ws, rb, blocks, diags in results:
    if rb:
        by_ws.setdefault(ws, []).append((day, sid[:13], rb[0], rb[-1]))
for ws, rows in sorted(by_ws.items()):
    print(f"{ws}: {len(rows)} sessions with rules_file obs")
    for day, sid, first, last in rows:
        print(f"   {day} {sid} first={first} last={last}")

print()
print("== all block ids seen (aggregate) ==")
allblocks = Counter()
for _, _, _, _, blocks, _ in results:
    allblocks.update(blocks)
for b, n in allblocks.most_common():
    print(f"{b}: {n}")
