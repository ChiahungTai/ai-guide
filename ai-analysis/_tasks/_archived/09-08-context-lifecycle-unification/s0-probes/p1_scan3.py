"""P1 step3: clean sampling of memory system-reminders, excluding self-echo (read-only)."""

import re
import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# exclude: my own live session + subagent sessions of today's task + tool-part echoes
SELF = "sess_subagent_agent_b828b2de-6f13-451f-ba0e-402f0de64d00"

rows = cur.execute(
    """
    SELECT p.session_id, p.message_id, p.time_created,
           json_extract(p.data, '$.type') AS ptype,
           json_extract(p.data, '$.text') AS ptext
    FROM part p
    WHERE p.data LIKE '%system-reminder%'
      AND p.data LIKE '%MEMORY.md%'
      AND p.session_id != ?
      AND json_extract(p.data, '$.type') IN ('text', 'file')
    ORDER BY p.time_created DESC
    LIMIT 40
    """,
    (SELF,),
).fetchall()

print(
    f"== {len(rows)} newest text/file parts with system-reminder+MEMORY.md (self session excluded) =="
)
shown = 0
for sid, mid, ts, ptype, text in rows:
    if not text:
        continue
    low = text.lower()
    if "p1_scan" in low or "sqlite_master" in low:  # forensic echo of my own probes
        continue
    idx = text.find("system-reminder")
    if idx < 0:
        continue
    start = max(0, idx - 150)
    snippet = text[start : idx + 700].replace("\n", "\\n")
    print("-" * 80)
    print(f"session={sid} msg={mid} time={ts} type={ptype} text_len={len(text)}")
    print(f"snippet: {snippet}")
    shown += 1
    if shown >= 8:
        break

print()
print(
    "== classify reminder content shapes (all non-self text parts, no sample limit) =="
)
rows = cur.execute(
    """
    SELECT p.session_id, p.message_id, p.time_created, p.sequence,
           json_extract(p.data, '$.type') AS ptype,
           json_extract(p.data, '$.text') AS ptext
    FROM part p
    WHERE p.data LIKE '%system-reminder%'
      AND p.session_id != ?
      AND json_extract(p.data, '$.type') = 'text'
    """,
    (SELF,),
).fetchall()

cats = {
    "index_projection (MEMORY.md title list)": 0,
    "entry_body (frontmatter desc/rank/body)": 0,
    "read tool reminder (instruction quote)": 0,
    "other": 0,
}
samples_by_cat = {k: [] for k in cats}
seen_text_hashes = set()
unique_texts = 0
for sid, mid, ts, seq, ptype, text in rows:
    if not text:
        continue
    low = text.lower()
    if "p1_scan" in low or "sqlite_master" in low:
        continue
    h = hash(text[:2000])
    if h not in seen_text_hashes:
        seen_text_hashes.add(h)
        unique_texts += 1
    # find the reminder block
    m = re.search(r"<system-reminder>(.{0,1200})", text, re.DOTALL) or re.search(
        r"system-reminder[:\s]*(.{0,1200})", text, re.DOTALL
    )
    block = m.group(1) if m else text[:1200]
    has_index = "MEMORY.md" in block and (
        "|" in block or "- [" in block or "read_memory" in block
    )
    has_entry = bool(re.search(r"(desc\s*:|rank\s*:|---)", block)) and (
        "memory/" in block or "[[" in block
    )
    is_read = (
        "read_memory" in block
        or "memory-audit" in block.lower()
        and "hook" in block.lower()
    )
    if has_entry and not has_index:
        cat = "entry_body (frontmatter desc/rank/body)"
    elif has_index:
        cat = "index_projection (MEMORY.md title list)"
    elif "read_memory" in block:
        cat = "read tool reminder (instruction quote)"
    else:
        cat = "other"
    cats[cat] += 1
    if len(samples_by_cat[cat]) < 2:
        samples_by_cat[cat].append(
            (sid, mid, ts, seq, block[:400].replace("\n", "\\n"))
        )

print(
    f"total non-self text parts with 'system-reminder': {len(rows)}; unique by first-2KB hash: {unique_texts}"
)
for k, v in cats.items():
    print(f"{k}: {v}")
    for sid, mid, ts, seq, s in samples_by_cat[k]:
        print(f"   sample session={sid} msg={mid} seq={seq} ts={ts}: {s[:360]}")
con.close()
