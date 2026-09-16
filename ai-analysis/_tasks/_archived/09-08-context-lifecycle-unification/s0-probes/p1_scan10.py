"""P1 step10: sample the 7 background_notification msgs w/ description+memory (read-only)."""

import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

rows = cur.execute(
    """
    SELECT m.id, m.session_id, m.time_created,
           substr(COALESCE(json_extract(p.data,'$.text'),''),1,1200)
    FROM message m JOIN part p ON p.message_id=m.id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='background_notification'
      AND json_extract(p.data,'$.type')='text'
      AND json_extract(p.data,'$.text') LIKE '%description:%'
      AND json_extract(p.data,'$.text') LIKE '%memory%'
    ORDER BY m.time_created DESC LIMIT 10
    """
).fetchall()
print(f"hits: {len(rows)}")
for mid, sid, ts, text in rows:
    print("-" * 76)
    print(f"msg={mid} session={sid} ts={ts}")
    print(f"text: {text}".replace("\n", "\\n"))

print()
print("== generic background_notification shape (2 newest) ==")
rows = cur.execute(
    """
    SELECT m.id, substr(COALESCE(json_extract(p.data,'$.text'),''),1,400)
    FROM message m JOIN part p ON p.message_id=m.id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='background_notification'
      AND json_extract(p.data,'$.type')='text'
    ORDER BY m.time_created DESC LIMIT 2
    """
).fetchall()
for mid, text in rows:
    print("-" * 76)
    print(f"msg={mid}: {text}".replace("\n", "\\n"))
con.close()
