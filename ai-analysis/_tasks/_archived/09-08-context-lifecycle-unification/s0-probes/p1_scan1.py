"""P1 step1: part type distribution + system-reminder hit counts (read-only, SQL-side scan)."""

import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

print("== part.data JSON type distribution ==")
for t, n in cur.execute(
    "SELECT json_extract(data, '$.type') AS t, COUNT(*) FROM part GROUP BY t ORDER BY COUNT(*) DESC"
).fetchall():
    print(f"{t}: {n}")

print("\n== message.data JSON role distribution ==")
for t, n in cur.execute(
    "SELECT json_extract(data, '$.role') AS r, COUNT(*) FROM message GROUP BY r ORDER BY COUNT(*) DESC"
).fetchall():
    print(f"{t}: {n}")

print("\n== parts containing 'system-reminder' ==")
n = cur.execute(
    "SELECT COUNT(*) FROM part WHERE data LIKE '%system-reminder%'"
).fetchone()[0]
print(f"parts with 'system-reminder': {n}")
q = "SELECT COUNT(DISTINCT session_id) FROM part WHERE data LIKE '%system-reminder%'"
print(f"distinct sessions: {cur.execute(q).fetchone()[0]}")

print("\n== memory-feature co-occurrence among those parts ==")
feats = {
    "MEMORY.md": "data LIKE '%MEMORY.md%'",
    "memories/projects path": "data LIKE '%memories/projects%'",
    "memory/ path": "data LIKE '%memory/%'",
    "wiki [[ link": "data LIKE '%[[%'",
    "desc: frontmatter": "data LIKE '%desc:%'",
    "rank:": "data LIKE '%rank:%'",
}
for label, cond in feats.items():
    n = cur.execute(
        f"SELECT COUNT(*) FROM part WHERE data LIKE '%system-reminder%' AND {cond}"
    ).fetchone()[0]
    print(f"system-reminder AND {label}: {n}")

print("\n== bare memory-feature scan (no system-reminder filter), for comparison ==")
for label, cond in feats.items():
    n = cur.execute(f"SELECT COUNT(*) FROM part WHERE {cond}").fetchone()[0]
    print(f"{label}: {n}")
con.close()
