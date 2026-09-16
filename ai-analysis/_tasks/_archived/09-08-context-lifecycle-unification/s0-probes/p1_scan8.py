"""P1 step8: sample kind=system_reminder synthetic messages — content + timing (read-only)."""

import sqlite3

DB = "file:/Users/ctai/.zcode/cli/db/db.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

print("== system_reminder messages: their text part contents (newest 8) ==")
rows = cur.execute(
    """
    SELECT m.id, m.session_id, m.time_created, p.sequence,
           substr(COALESCE(json_extract(p.data,'$.text'), json_extract(p.data,'$.data')),1,900)
    FROM message m LEFT JOIN part p ON p.message_id = m.id AND json_extract(p.data,'$.type')='text'
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='system_reminder'
    ORDER BY m.time_created DESC LIMIT 8
    """
).fetchall()
for mid, sid, ts, seq, text in rows:
    print("-" * 76)
    print(f"msg={mid} session={sid} ts={ts} part_seq={seq}")
    print(f"text: {(text or '(no text part)')[:850]}".replace("\n", "\\n"))

print()
print("== content classification of ALL 210 system_reminder messages ==")
rows = cur.execute(
    """
    SELECT m.id, m.session_id, m.time_created,
           (SELECT GROUP_CONCAT(COALESCE(json_extract(p.data,'$.text'),''), ' ||| ') FROM part p WHERE p.message_id=m.id)
    FROM message m
    WHERE json_extract(m.data,'$.role')='user'
      AND json_extract(m.data,'$.semantics.kind')='system_reminder'
    ORDER BY m.time_created
    """
).fetchall()
cats = {"memory_related": 0, "file_read_warning": 0, "hook_injection": 0, "other": 0}
samples = {k: [] for k in cats}
sessions_with = set()
time_range = []
for mid, sid, ts, body in rows:
    sessions_with.add(sid)
    time_range.append(ts)
    b = (body or "").lower()
    if "memory" in b and (
        "recall" in b
        or "memories" in b
        or "memory/" in b
        or "memory.md" in b
        or "desc" in b
    ):
        cat = "memory_related"
    elif "warning" in b or "shorter than" in b or "file" in b:
        cat = "file_read_warning"
    elif "hook" in b or "pretooluse" in b or "posttooluse" in b:
        cat = "hook_injection"
    else:
        cat = "other"
    cats[cat] += 1
    if len(samples[cat]) < 3:
        samples[cat].append((mid, sid, ts, (body or "")[:600]))

print(
    f"total system_reminder msgs: {len(rows)}; distinct sessions: {len(sessions_with)}"
)
if time_range:
    import datetime

    lo = datetime.datetime.fromtimestamp(min(time_range) / 1000, tz=datetime.UTC)
    hi = datetime.datetime.fromtimestamp(max(time_range) / 1000, tz=datetime.UTC)
    print(f"time range: {lo} .. {hi}")
for k, v in cats.items():
    print(f"{k}: {v}")
    for mid, sid, ts, s in samples[k]:
        print(f"  sample msg={mid} session={sid}: {s[:480]}".replace("\n", "\\n"))
con.close()
