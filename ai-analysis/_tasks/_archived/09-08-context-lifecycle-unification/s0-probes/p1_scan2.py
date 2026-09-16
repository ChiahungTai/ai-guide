"""P1 step2: sample system-reminder parts, classify content + timing (read-only)."""

import json
import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

rows = cur.execute(
    """
    SELECT p.session_id, p.message_id, p.sequence, p.time_created, substr(p.data, 1, 4000)
    FROM part p
    WHERE p.data LIKE '%system-reminder%' AND p.data LIKE '%MEMORY.md%'
    ORDER BY p.time_created DESC
    LIMIT 12
    """
).fetchall()

print(f"== {len(rows)} newest samples (system-reminder AND MEMORY.md) ==")
for sid, mid, seq, ts, data in rows:
    try:
        j = json.loads(data)
    except Exception:
        j = {}
    ptype = j.get("type", "?")
    text = j.get("text", "") or json.dumps(j, ensure_ascii=False)
    idx = text.find("system-reminder")
    start = max(0, idx - 100)
    snippet = text[start : idx + 500].replace("\n", "\\n")
    print("-" * 80)
    print(
        f"session={sid} msg={mid} part_seq={seq} time={ts} part_type={ptype} text_len={len(text)}"
    )
    print(f"snippet: {snippet}")

print()
print("== position-in-session statistics for all reminder+MEMORY.md parts ==")
rows = cur.execute(
    """
    SELECT p.session_id,
           COUNT(*) AS n_parts,
           MIN(p.time_created) AS first_ts,
           MAX(p.time_created) AS last_ts,
           (SELECT MIN(m2.sequence) FROM message m2 WHERE m2.session_id = p.session_id AND json_extract(m2.data, '$.role') = 'user') AS first_user_seq,
           (SELECT MAX(m2.sequence) FROM message m2 WHERE m2.session_id = p.session_id) AS max_seq
    FROM part p
    WHERE p.data LIKE '%system-reminder%' AND p.data LIKE '%MEMORY.md%'
    GROUP BY p.session_id
    """
).fetchall()
early = mid = late = 0
for sid, n_parts, first_ts, last_ts, first_user_seq, max_seq in rows:
    span = max(1, (last_ts - first_ts))
    if span < 60_000 and n_parts <= 2:
        early += 1
    elif n_parts <= 2:
        mid += 1
    else:
        late += 1
print(f"sessions with reminder+MEMORY.md parts: {len(rows)}")
print(
    f"  single-burst early (span<60s, <=2 parts, likely session-start injection): {early}"
)
print(f"  single-burst later (<=2 parts): {mid}")
print(f"  repeated injections (>2 parts in session): {late}")

print()
print("== per-session detail (first 15 sessions) ==")
for sid, n_parts, first_ts, last_ts, first_user_seq, max_seq in rows[:15]:
    t = cur.execute(
        "SELECT time_created, sequence FROM message WHERE id = (SELECT message_id FROM part WHERE session_id = ? AND data LIKE '%system-reminder%' AND data LIKE '%MEMORY.md%' LIMIT 1)",
        (sid,),
    ).fetchone()
    print(
        f"session={sid} n_reminder_parts={n_parts} msg_seq={t[1] if t else '?'} first_user_seq={first_user_seq} session_max_seq={max_seq}"
    )
con.close()
