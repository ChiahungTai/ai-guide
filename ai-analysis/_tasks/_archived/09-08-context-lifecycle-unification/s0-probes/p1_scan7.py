"""P1 step7: enumerate synthetic injection taxonomy via semantics.kind (read-only)."""

import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
SELF = "sess_subagent_agent_b828b2de-6f13-451f-ba0e-402f0de64d00"

print("== user messages: semantics.kind x origin x synthetic ==")
rows = cur.execute(
    """
    SELECT json_extract(data,'$.semantics.kind') AS k,
           json_extract(data,'$.semantics.origin') AS o,
           json_extract(data,'$.synthetic') AS syn,
           COUNT(*) AS n
    FROM message WHERE json_extract(data,'$.role')='user'
    GROUP BY k, o, syn ORDER BY n DESC
    """
).fetchall()
for k, o, syn, n in rows:
    print(f"kind={k} origin={o} synthetic={syn}: {n}")

print("\n== assistant messages: semantics.kind x origin ==")
rows = cur.execute(
    """
    SELECT json_extract(data,'$.semantics.kind') AS k,
           json_extract(data,'$.semantics.origin') AS o, COUNT(*) AS n
    FROM message WHERE json_extract(data,'$.role')='assistant'
    GROUP BY k, o ORDER BY n DESC LIMIT 20
    """
).fetchall()
for k, o, n in rows:
    print(f"kind={k} origin={o}: {n}")

print("\n== sample one message per interesting kind (non-real_user) ==")
rows = cur.execute(
    """
    SELECT json_extract(data,'$.semantics.kind') AS k, COUNT(*) AS n
    FROM message WHERE json_extract(data,'$.role')='user'
      AND json_extract(data,'$.semantics.origin') != 'real_user'
    GROUP BY k ORDER BY n DESC
    """
).fetchall()
for k, _n in rows:
    row = cur.execute(
        """
        SELECT m.id, m.time_created,
               json_extract(m.data,'$.semantics.origin'),
               json_extract(m.data,'$.synthetic'),
               json_extract(m.data,'$.visibility'),
               (SELECT substr(json_extract(p.data,'$.text'),1,400) FROM part p
                 WHERE p.message_id=m.id AND json_extract(p.data,'$.type')='text' LIMIT 1)
        FROM message m
        WHERE json_extract(m.data,'$.role')='user'
          AND json_extract(m.data,'$.semantics.kind') = ?
        ORDER BY m.time_created DESC LIMIT 1
        """,
        (k,),
    ).fetchone()
    mid, ts, origin, syn, vis, text = row
    print("-" * 70)
    print(
        f"kind={k} msg={mid} ts={ts} origin={origin} synthetic={syn} visibility={vis}"
    )
    print(f"text[:400]: {text}")

print()
print(
    "== full body of newest todo_reminder / synthetic non-real messages: text parts =="
)
rows = cur.execute(
    """
    SELECT p.session_id, p.time_created, json_extract(p.data,'$.type'), substr(json_extract(p.data,'$.text'),1,700)
    FROM part p JOIN message m ON m.id=p.message_id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.origin') != 'real_user'
      AND json_extract(p.data,'$.type')='text'
    ORDER BY p.time_created DESC LIMIT 6
    """
).fetchall()
for sid, ts, ptype, text in rows:
    print("-" * 70)
    print(f"session={sid} ts={ts}")
    print(f"text: {text}")
con.close()
