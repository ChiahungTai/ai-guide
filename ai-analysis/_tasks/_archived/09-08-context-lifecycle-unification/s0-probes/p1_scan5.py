"""P1 step5: tool-part samples with wrapper + other recall markers + session_input/entry tables (read-only)."""

import json
import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
SELF = "sess_subagent_agent_b828b2de-6f13-451f-ba0e-402f0de64d00"

print("== tool parts with literal wrapper: tool name + head snippet ==")
rows = cur.execute(
    """
    SELECT p.session_id, p.time_created, substr(p.data, 1, 3000)
    FROM part p
    WHERE p.data LIKE '%<system-reminder>%'
      AND p.session_id != ?
      AND json_extract(p.data, '$.type') = 'tool'
    ORDER BY p.time_created DESC LIMIT 8
    """,
    (SELF,),
).fetchall()
for sid, ts, data in rows:
    try:
        j = json.loads(data)
    except Exception:
        j = {}
    tool = j.get("tool") or j.get("state", {}).get("tool") or j.get("name") or "?"
    keys = list(j.keys())
    raw = json.dumps(j, ensure_ascii=False)
    idx = raw.find("<system-reminder>")
    print("-" * 70)
    print(f"session={sid} ts={ts} tool={tool} json_keys={keys}")
    print(f"around wrapper: {raw[max(0, idx - 120) : idx + 260]}")

print()
print("== user-role text parts scanned for recall-marker alternatives ==")
markers = [
    "recalled",
    "Recalled",
    "memory context",
    "Relevant memories",
    "relevant memories",
    "<memory",
    "memories>",
    "memory context block",
    "auto-injected",
    "automatically injected",
]
for mk in markers:
    n = cur.execute(
        "SELECT COUNT(*) FROM part p JOIN message m ON m.id=p.message_id WHERE json_extract(m.data,'$.role')='user' AND json_extract(p.data,'$.type')='text' AND p.data LIKE ? AND p.session_id != ?",
        (f"%{mk}%", SELF),
    ).fetchone()[0]
    print(f"user-text parts LIKE '%{mk}%': {n}")

print()
print("== any-part scan for 'recalled' variants ==")
for mk in ["%recalled memor%", "%Recalled memor%", "%recall%memory%"]:
    n = cur.execute(
        "SELECT COUNT(*) FROM part WHERE data LIKE ? AND session_id != ?", (mk, SELF)
    ).fetchone()[0]
    print(f"parts LIKE {mk}: {n}")

print()
print("== session_input kinds ==")
for k, n in cur.execute(
    "SELECT kind, COUNT(*) FROM session_input GROUP BY kind"
).fetchall():
    print(f"{k}: {n}")
print("\n== session_input payload sample (1 row, truncated) ==")
row = cur.execute(
    "SELECT kind, payload FROM session_input ORDER BY time_created DESC LIMIT 1"
).fetchone()
if row:
    print(f"kind={row[0]} payload_head={row[1][:500]}")

print()
print("== session_entry types ==")
for k, n in cur.execute(
    "SELECT type, COUNT(*) FROM session_entry GROUP BY type"
).fetchall():
    print(f"{k}: {n}")
print("\n== session_entry data keys sample ==")
row = cur.execute(
    "SELECT type, substr(data,1,300) FROM session_entry ORDER BY time_created DESC LIMIT 5"
).fetchall()
for t, d in row:
    print(f"type={t}: {d}")
con.close()
