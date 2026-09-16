"""P1 step4: literal <system-reminder> wrapper scan + role/content classification (read-only)."""

import re
import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
SELF = "sess_subagent_agent_b828b2de-6f13-451f-ba0e-402f0de64d00"

print("== literal '<system-reminder>' counts ==")
n = cur.execute(
    "SELECT COUNT(*) FROM part WHERE data LIKE '%<system-reminder>%'"
).fetchone()[0]
print(f"parts with literal '<system-reminder>': {n}")
q = "SELECT COUNT(DISTINCT session_id) FROM part WHERE data LIKE '%<system-reminder>%'"
print(f"distinct sessions: {cur.execute(q).fetchone()[0]}")

print("\n== breakdown by part type x parent role ==")
rows = cur.execute(
    """
    SELECT json_extract(p.data, '$.type') AS ptype,
           json_extract(m.data, '$.role') AS role,
           COUNT(*) AS n
    FROM part p JOIN message m ON m.id = p.message_id
    WHERE p.data LIKE '%<system-reminder>%' AND p.session_id != ?
    GROUP BY ptype, role ORDER BY n DESC
    """,
    (SELF,),
).fetchall()
for ptype, role, n in rows:
    print(f"type={ptype} role={role}: {n}")

print(
    "\n== memory-recall signatures inside <system-reminder> blocks (user-role text parts) =="
)
rows = cur.execute(
    """
    SELECT p.session_id, p.message_id, m.sequence, p.time_created,
           json_extract(p.data, '$.text') AS ptext
    FROM part p JOIN message m ON m.id = p.message_id
    WHERE p.data LIKE '%<system-reminder>%'
      AND p.session_id != ?
      AND json_extract(m.data, '$.role') = 'user'
      AND json_extract(p.data, '$.type') = 'text'
    ORDER BY p.time_created DESC
    LIMIT 200
    """,
    (SELF,),
).fetchall()

sigs = {
    "recalled memories": lambda b: "recalled" in b.lower() or "recall" in b.lower(),
    "memory entry body (--- frontmatter + desc:)": lambda b: (
        bool(re.search(r"desc\s*:", b)) and "---" in b
    ),
    "MEMORY.md mention": lambda b: "MEMORY.md" in b,
    "memory/ path": lambda b: "memory/" in b,
    "task-notification": lambda b: "task-notification" in b,
    "plan/mode": lambda b: "plan mode" in b.lower() or "plan_mode" in b.lower(),
    "todos": lambda b: "todo" in b.lower(),
}
counts = {k: 0 for k in sigs}
example = {k: None for k in sigs}
block_samples = []
for sid, mid, seq, ts, text in rows:
    if not text:
        continue
    for bm in re.finditer(r"<system-reminder>(.*?)</system-reminder>", text, re.DOTALL):
        block = bm.group(1)
        block_samples.append((sid, mid, seq, ts, block))
        for k, fn in sigs.items():
            if fn(block):
                counts[k] += 1
                if example[k] is None:
                    example[k] = (sid, mid, seq, ts, block[:500])

print(
    f"user-role text parts scanned: {len(rows)}; total <system-reminder> blocks: {len(block_samples)}"
)
for k, v in counts.items():
    print(f"{k}: {v}")

print("\n== sample blocks (first 6, any signature) ==")
for sid, mid, seq, ts, block in block_samples[:6]:
    print("-" * 80)
    print(f"session={sid} msg={mid} msg_seq={seq} ts={ts} block_len={len(block)}")
    print(f"block head: {block[:600].replace(chr(10), chr(92) + 'n')}")
con.close()
