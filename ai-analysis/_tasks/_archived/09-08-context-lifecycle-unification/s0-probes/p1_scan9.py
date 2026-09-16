"""P1 step9 (final): adjacency of synthetic msgs + session-start MEMORY.md auto-read + recall absence (read-only)."""

import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

print("== A. system_reminder adjacency: previous message kind ==")
rows = cur.execute(
    """
    SELECT m.id, m.session_id, m.sequence, json_extract(m.data,'$.semantics.kind') AS k
    FROM message m
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind') IN ('system_reminder','fork_notice','subagent_notification')
    LIMIT 400
    """
).fetchall()
adj = {}
for mid, sid, seq, k in rows:
    if seq is None:
        prev = "(no seq)"
    else:
        r = cur.execute(
            """
            SELECT json_extract(data,'$.semantics.kind'), json_extract(data,'$.role')
            FROM message WHERE session_id=? AND sequence<? ORDER BY sequence DESC LIMIT 1
            """,
            (sid, seq),
        ).fetchone()
        prev = f"{r[0]}/{r[1]}" if r else "(session start)"
    key = (k, prev)
    adj[key] = adj.get(key, 0) + 1
for (k, prev), n in sorted(adj.items(), key=lambda x: -x[1]):
    print(f"{k} after {prev}: {n}")

print()
print("== B. sessions with system_reminder AND time_compacting set ==")
n = cur.execute(
    """
    SELECT COUNT(DISTINCT m.session_id)
    FROM message m JOIN session s ON s.id=m.session_id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='system_reminder'
      AND s.time_compacting IS NOT NULL
    """
).fetchone()[0]
tot = cur.execute(
    """
    SELECT COUNT(DISTINCT m.session_id)
    FROM message m
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='system_reminder'
    """
).fetchone()[0]
print(f"system_reminder sessions: {tot}; of which with time_compacting: {n}")

print()
print("== C. session-start auto Read of MEMORY.md (static index preload evidence) ==")
rows = cur.execute(
    """
    SELECT p.session_id, MIN(m.sequence) AS first_seq
    FROM part p JOIN message m ON m.id=p.message_id
    WHERE json_extract(p.data,'$.type')='tool'
      AND p.data LIKE '%MEMORY.md%'
      AND json_extract(m.data,'$.role')='assistant'
    GROUP BY p.session_id
    HAVING first_seq <= 6
    LIMIT 12
    """
).fetchall()
print(
    f"sessions whose MEMORY.md tool mention occurs at assistant message seq<=6 (n shown, first 12): {len(rows)}"
)
for sid, seq in rows:
    # confirm it is a Read tool call with MEMORY.md path in input
    r = cur.execute(
        """
        SELECT substr(p.data,1,700)
        FROM part p JOIN message m ON m.id=p.message_id
        WHERE p.session_id=? AND json_extract(p.data,'$.type')='tool'
          AND p.data LIKE '%MEMORY.md%'
          AND m.sequence=?
        ORDER BY p.time_created LIMIT 1
        """,
        (sid, seq),
    ).fetchone()
    blob = r[0] if r else ""
    is_read = '"tool":"Read"' in blob or '"tool": "Read"' in blob
    has_mem_path = "memories/projects" in blob or "MEMORY.md" in blob
    print(
        f"session={sid} first_seq={seq} isRead={is_read} memPath={has_mem_path} head={blob[:180]}"
    )

n_all = cur.execute(
    """
    SELECT COUNT(DISTINCT p.session_id)
    FROM part p
    WHERE json_extract(p.data,'$.type')='tool' AND p.data LIKE '%MEMORY.md%'
    """
).fetchone()[0]
print(f"(for scale) sessions with ANY tool part mentioning MEMORY.md: {n_all}")

print()
print(
    "== D. desc-matching recall absence check: synthetic msgs quoting entry 'description:' fields =="
)
rows = cur.execute(
    """
    SELECT json_extract(m.data,'$.semantics.kind') AS k, COUNT(*) AS n
    FROM message m JOIN part p ON p.message_id=m.id
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.origin')='agent_runtime'
      AND json_extract(p.data,'$.type')='text'
      AND json_extract(p.data,'$.text') LIKE '%description:%'
      AND json_extract(p.data,'$.text') LIKE '%memory%'
      AND json_extract(m.data,'$.semantics.kind') != 'system_reminder'
    """
).fetchone()
print(f"non-system_reminder synthetic msgs w/ description:+memory: {rows}")
con.close()
