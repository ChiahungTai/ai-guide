"""P1 step6: sample 'recalled memor' parts + user message JSON structure + user-role near-hits (read-only)."""

import json
import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
SELF = "sess_subagent_agent_b828b2de-6f13-451f-ba0e-402f0de64d00"

print("== parts LIKE '%recalled memor%' — type/role/session breakdown ==")
rows = cur.execute(
    """
    SELECT p.session_id, json_extract(p.data,'$.type') AS ptype,
           json_extract(m.data,'$.role') AS role, COUNT(*) AS n
    FROM part p JOIN message m ON m.id=p.message_id
    WHERE p.data LIKE '%recalled memor%' AND p.session_id != ?
    GROUP BY ptype, role ORDER BY n DESC
    """,
    (SELF,),
).fetchall()
for sid0, ptype, role, n in rows:
    print(f"type={ptype} role={role}: {n}")

print("\n== sample 'recalled memor' contents (up to 5, head 400 chars around hit) ==")
rows = cur.execute(
    """
    SELECT p.session_id, p.time_created, json_extract(p.data,'$.type'),
           json_extract(p.data,'$.text')
    FROM part p
    WHERE p.data LIKE '%recalled memor%' AND p.session_id != ?
    ORDER BY p.time_created DESC LIMIT 6
    """,
    (SELF,),
).fetchall()
for sid, ts, ptype, text in rows:
    if not text:
        print(f"session={sid} type={ptype} (no text field)")
        continue
    idx = text.lower().find("recalled memor")
    print("-" * 70)
    print(f"session={sid} ts={ts} type={ptype} text_len={len(text)}")
    print(f"around hit: {text[max(0, idx - 200) : idx + 400]}".replace("\n", "\\n"))

print()
print("== user-role near-hits: 'memory context' (1) and '<memory' (3) ==")
rows = cur.execute(
    """
    SELECT p.session_id, p.time_created, json_extract(p.data,'$.text')
    FROM part p JOIN message m ON m.id=p.message_id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(p.data,'$.type')='text'
      AND (p.data LIKE '%memory context%' OR p.data LIKE '%<memory%')
      AND p.session_id != ?
    ORDER BY p.time_created DESC LIMIT 5
    """,
    (SELF,),
).fetchall()
for sid, ts, text in rows:
    if not text:
        continue
    for mk in ["memory context", "<memory"]:
        idx = text.find(mk)
        if idx >= 0:
            print("-" * 70)
            print(f"session={sid} ts={ts} marker={mk} text_len={len(text)}")
            print(
                f"around hit: {text[max(0, idx - 150) : idx + 350]}".replace(
                    "\n", "\\n"
                )
            )

print()
print("== user message data JSON structure (full keys, 3 newest user messages) ==")
rows = cur.execute(
    """
    SELECT m.id, m.data FROM message m
    WHERE json_extract(m.data,'$.role')='user' AND m.session_id != ?
    ORDER BY m.time_created DESC LIMIT 3
    """,
    (SELF,),
).fetchall()
for mid, data in rows:
    j = json.loads(data)
    print("-" * 70)
    print(f"msg={mid} keys={list(j.keys())}")
    for k, v in j.items():
        s = json.dumps(v, ensure_ascii=False)
        print(f"  {k}: {s[:200]}")
con.close()
