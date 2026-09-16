"""P1 helper: local_setting rows (read-only; rebuilt per PROVENANCE)."""

import sqlite3

con = sqlite3.connect("file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro", uri=True)
rows = con.execute(
    """
    SELECT json_extract(data,'$.semantics.kind') AS k, COUNT(*) AS n,
           group_concat(DISTINCT json_extract(data,'$.localKey'))
    FROM message
    WHERE json_extract(data,'$.semantics.kind') IN ('local_setting','setting_update')
       OR json_extract(data,'$.localKey') IS NOT NULL
    GROUP BY k ORDER BY n DESC
    """
).fetchall()
for k, n, keys in rows:
    print(f"kind={k}: {n}  keys={keys}")
rows = con.execute(
    """
    SELECT session_id, time_created, substr(data, 1, 160)
    FROM message
    WHERE json_extract(data,'$.localKey') IS NOT NULL
       OR json_extract(data,'$.semantics.kind')='local_setting'
    ORDER BY time_created DESC LIMIT 24
    """
).fetchall()
for sid, ts, d in rows:
    print(f"{ts} {sid[:20]} {d}")
