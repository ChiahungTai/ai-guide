"""P1 probe: dump sqlite schema of ~/.zcode/cli/db/db.sqlite (read-only)."""

import sqlite3

DB = "file:" + "/Users/ctai/.zcode/cli/db/db.sqlite" + "?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

rows = cur.execute(
    "SELECT name, type FROM sqlite_master WHERE type IN ('table','index') ORDER BY type, name"
).fetchall()
print("== sqlite_master objects ==")
for name, typ in rows:
    print(f"{typ}: {name}")

print("\n== table DDL ==")
for (sql,) in cur.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
).fetchall():
    print(sql)
    print("---")

print("\n== row counts (may be slow on big tables) ==")
for (name,) in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
).fetchall():
    try:
        n = cur.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        print(f"{name}: {n}")
    except Exception as e:
        print(f"{name}: ERR {e}")
con.close()
