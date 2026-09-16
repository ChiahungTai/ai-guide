"""Read-only memory telemetry collector (AIR-40 S1: events + coverage).

Drives normalized write/read events out of ZCode db.sqlite part rows and
Claude transcript JSONL without touching sources. Scope is S1 only:
event/identity/coverage JSON. Ranking projection is S2 and consumes this
output. See ai-analysis/_tasks/_archived/09-07-memory-governance/write-attribution/ep.md.
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCHEMA = 1
TOOLS = ("Read", "Write", "Edit")


@dataclass
class Event:
    source: str  # zcode | claude | hook (hook-synthesized, AIR-56)
    id: str
    session: str
    parent: str | None
    task_type: str | None
    tool: str
    status: str  # completed | error | unmatched | unknown
    operation_start: str | None
    operation_end: str | None
    record_time: str
    time_source: str  # operation | record_fallback
    raw_path: str
    canonical_path: str | None
    entry: str
    payload_chars: int
    input_sha256: str
    call_id: str | None
    prior_known: bool = False
    net_delta: int | None = None
    copy_of: str | None = None
    actor: str = "unknown"
    source_ref: dict = field(default_factory=dict)
    read_range: dict | None = None


@dataclass
class Coverage:
    zcode: dict = field(default_factory=dict)
    claude: dict = field(default_factory=dict)
    pools: list = field(default_factory=list)


def parse_ts(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, UTC)
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    # date-only / naive ISO strings（SKILL 呼叫慣例形態）一律視為 UTC——
    # naive 與 epoch 解析出的 aware 比較會 TypeError（09-09 回測實證）
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def iso(dt):
    return dt.astimezone(UTC).isoformat() if dt else None


def in_window(dt, since, until):
    return dt is not None and since <= dt < until


def resolve_pool_entry(pools, raw, cwd=None):
    """Return (canonical_path, entry) or (None, None) when outside pools."""
    if not raw:
        return None, None
    p = Path(raw).expanduser()
    if not p.is_absolute():
        if not cwd:
            return None, None
        p = Path(cwd) / p
    try:
        rp = p.resolve()
    except OSError:
        return None, None
    for pool in pools:
        try:
            if (
                rp.parent == pool
                and rp.name != "MEMORY.md"
                and not rp.name.startswith("_")
            ):
                return str(rp), rp.name
        except OSError:
            continue
    return None, None


def read_zcode(db_path, pools, since, until):
    events, coverage = [], {"readable": False}
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        coverage.update(readable=False, error=str(exc))
        return events, coverage
    try:
        con.execute("BEGIN")
        bounds = con.execute(
            "select min(time_created), max(time_created), count(*) from part"
        ).fetchone()
        coverage["bounds"] = {
            "first": iso(parse_ts(bounds[0])),
            "last": iso(parse_ts(bounds[1])),
            "global_parts": bounds[2],
        }
        sessions = {
            r[0]: (r[1], r[2])
            for r in con.execute("select id, parent_id, task_type from session")
        }
        rows = con.execute(
            """select p.id, p.session_id, p.time_created, p.data
            from part p
            where json_extract(p.data, '$.type') = 'tool'
              and (
                (
                  json_extract(p.data, '$.state.time.start') is not null
                  and datetime(json_extract(p.data, '$.state.time.start')) is not null
                  and datetime(json_extract(p.data, '$.state.time.start')) >= datetime(?)
                  and datetime(json_extract(p.data, '$.state.time.start')) <= datetime(?)
                )
                or (
                  json_extract(p.data, '$.state.time.start') is null
                  and p.time_created >= ? and p.time_created < ?
                )
                or (
                  json_extract(p.data, '$.state.time.start') is not null
                  and datetime(json_extract(p.data, '$.state.time.start')) is null
                )
              )
            order by p.time_created, p.id""",
            # selection mirrors the event contract: operation time is
            # authoritative when present (parseable), record time only when
            # the operation clock is absent or unparseable by SQLite (the
            # Python layer re-judges those rows) — no fixed margin can
            # guarantee completeness (F1). The op-window bounds use >=/<= on
            # purpose: datetime() truncates subseconds, so a same-second
            # inclusive fetch keeps SQL a strict superset of the precise
            # half-open window the Python layer applies (N1).
            (
                iso(since),
                iso(until),
                int(since.timestamp() * 1000),
                int(until.timestamp() * 1000),
            ),
        ).fetchall()
    finally:
        con.close()
    coverage["readable"] = True
    coverage["rows_scanned"] = len(rows)
    coverage["unknown_shapes"] = 0
    for pid, sid, ts_ms, raw in rows:
        try:
            d = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            coverage["unknown_shapes"] += 1
            continue
        if not isinstance(d, dict) or d.get("tool") not in TOOLS:
            coverage["unknown_shapes"] += 1
            continue
        state = d.get("state") or {}
        if not isinstance(state, dict):
            coverage["unknown_shapes"] += 1
            continue
        inp = state.get("input") or {}
        canon, entry = resolve_pool_entry(pools, inp.get("file_path"))
        if canon is None:
            continue
        op = state.get("time") or {}
        op_start = parse_ts(op.get("start")) if isinstance(op, dict) else None
        op_end = parse_ts(op.get("end")) if isinstance(op, dict) else None
        record = parse_ts(ts_ms)
        if op_start is not None:
            # operation time is authoritative when present: outside window
            # means excluded — no record fallback (R2)
            if not in_window(op_start, since, until):
                continue
            flag = "operation"
        elif in_window(record, since, until):
            flag = "record_fallback"
        else:
            continue  # no operation time and record clock outside window
        status = state.get("status")
        status = status if status in ("completed", "error") else "unknown"
        parent, task = sessions.get(sid, (None, None))
        payload = inp.get("content", inp.get("new_string", ""))
        events.append(
            Event(
                source="zcode",
                id=pid,
                session=sid,
                parent=parent,
                task_type=task,
                tool=d["tool"],
                status=status,
                operation_start=iso(op_start),
                operation_end=iso(op_end),
                record_time=iso(record),
                time_source=flag,
                raw_path=str(inp.get("file_path")),
                canonical_path=canon,
                entry=entry,
                payload_chars=len(payload) if isinstance(payload, str) else 0,
                input_sha256=hashlib.sha256(
                    json.dumps(inp, sort_keys=True).encode()
                ).hexdigest(),
                call_id=d.get("callID"),
                actor=sid if sid in sessions else "unknown",
                source_ref={"db": str(db_path), "row": pid},
                read_range=(
                    {k: inp[k] for k in ("offset", "limit") if k in inp} or None
                )
                if d["tool"] == "Read"
                else None,
            )
        )
    return events, coverage


def read_claude(roots, pools, since, until):
    events = []
    coverage = {
        "requested": True,
        "readable": True,
        "files": 0,
        "malformed": 0,
        "bounds": {"first": None, "last": None},
        "scope": "explicit --cc-root only; removed worktree dirs not enumerated unless passed",
    }
    seen_ts = []
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            coverage["readable"] = False
            coverage.setdefault("missing", []).append(str(root))
            continue
        for path in sorted(root.rglob("*.jsonl")):
            coverage["files"] += 1
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                coverage.setdefault("unreadable", []).append(str(path))
                continue
            pending, results = {}, {}
            for line_no, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    coverage["malformed"] += 1
                    continue
                if not isinstance(d, dict):
                    coverage["malformed"] += 1
                    continue
                ts = parse_ts(d.get("timestamp"))
                if ts is not None:
                    seen_ts.append(ts)
                blocks = (d.get("message") or {}).get("content", [])
                if not isinstance(blocks, list):
                    continue
                sid = d.get("sessionId", path.stem)
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result" and block.get("tool_use_id"):
                        results[(str(path), sid, block["tool_use_id"])] = (
                            "error" if block.get("is_error") else "completed"
                        )
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in TOOLS:
                        continue
                    inp = block.get("input") or {}
                    canon, entry = resolve_pool_entry(
                        pools, inp.get("file_path"), d.get("cwd")
                    )
                    if canon is None or ts is None or not in_window(ts, since, until):
                        continue
                    payload = inp.get("content", inp.get("new_string", ""))
                    pending[(str(path), sid, block.get("id"))] = Event(
                        source="claude",
                        id=str(block.get("id")),
                        session=sid,
                        parent=None,
                        task_type=None,
                        tool=block["name"],
                        status="unmatched",
                        operation_start=iso(ts),
                        operation_end=iso(ts),
                        record_time=iso(ts),
                        time_source="operation",
                        raw_path=str(inp.get("file_path")),
                        canonical_path=canon,
                        entry=entry,
                        payload_chars=len(payload) if isinstance(payload, str) else 0,
                        input_sha256=hashlib.sha256(
                            json.dumps(inp, sort_keys=True).encode()
                        ).hexdigest(),
                        call_id=str(block.get("id")),
                        source_ref={
                            "file": str(path),
                            "line": line_no,
                            # prompt/turn join key when the transcript carries
                            # one (messageId/uuid); absent -> omitted, never
                            # fabricated (writer_record reads .get only)
                            **(
                                {"message_id": str(d.get("messageId") or d.get("uuid"))}
                                if (d.get("messageId") or d.get("uuid"))
                                else {}
                            ),
                        },
                        read_range=(
                            {k: inp[k] for k in ("offset", "limit") if k in inp} or None
                        )
                        if block["name"] == "Read"
                        else None,
                    )
            for key, event in pending.items():
                event.status = results.get(key, "unmatched")
                events.append(event)
    if seen_ts:
        coverage["bounds"] = {"first": iso(min(seen_ts)), "last": iso(max(seen_ts))}
    return events, coverage


def resolve_lineage(events, sessions):
    """Fold fork/side-chat copies. Returns (canonical, aliases, ambiguous)."""

    def ancestors(sid):
        chain, seen = [], set()
        while sid and sid not in seen:
            seen.add(sid)
            parent, _ = sessions.get(sid, (None, None))
            if not parent:
                break
            chain.append(parent)
            sid = parent
        return set(chain)

    groups = {}
    for e in events:
        if e.tool not in ("Write", "Edit") or e.status != "completed":
            continue
        key = (
            e.tool,
            e.canonical_path,
            e.input_sha256,
            e.operation_start,
            e.operation_end,
        )
        groups.setdefault(key, []).append(e)
    aliases, ambiguous = [], []
    for members in groups.values():
        by_session = {m.session for m in members}
        if len(by_session) < 2:
            continue
        folded = False
        missing_time = False
        for m in members:
            older = [
                o for o in members if o is not m and o.session in ancestors(m.session)
            ]
            if older:
                first = min(older, key=lambda o: (o.record_time, o.id))
                # a confirmed copy needs complete time evidence on both
                # sides; None==None in the group key is "no evidence", not
                # "same time" — surface as ambiguity instead of folding (F3)
                if m.operation_start is None or first.operation_start is None:
                    missing_time = True
                    continue
                m.copy_of = first.id
                aliases.append(
                    {"copy": m.id, "canonical": first.id, "basis": "lineage+time+hash"}
                )
                folded = True
        if not folded:
            ambiguous.append(
                {
                    "members": [m.id for m in members],
                    "reason": (
                        "lineage+hash but missing operation time evidence"
                        if missing_time
                        else "multi-session same content without ancestor link"
                    ),
                }
            )
    canonical = [e for e in events if e.copy_of is None]
    return canonical, aliases, ambiguous


def generator_identity(pool: Path) -> str:
    g = pool / "_generate_index.py"
    if not g.is_file():
        return "absent"
    return hashlib.sha256(g.read_bytes()).hexdigest()[:12]


def snapshot_index(pools) -> dict:
    snaps = {}
    for pool in pools:
        mem = pool / "MEMORY.md"
        text = mem.read_text(encoding="utf-8") if mem.is_file() else ""
        entry_names = sorted(
            p.name
            for p in pool.glob("*.md")
            if p.name != "MEMORY.md" and not p.name.startswith("_")
        )
        snaps[str(pool)] = {
            "generator_schema": generator_identity(pool),
            "index_chars": len(text),
            "index_lines": text.count("\n"),
            "entry_count": len(entry_names),
            "entries": entry_names,
        }
    return snaps


def index_delta_with_baseline(pools, baseline_dir: Path):
    if baseline_dir is None:
        return {
            "value": None,
            "reason": "index baseline disabled (pass --baseline-dir to enable)",
            "baseline_written": [],
            "incomparable": None,
        }
    written, reasons, pool_deltas, incomparable = [], [], {}, []
    now = snapshot_index(pools)
    for pool_key, snap in now.items():
        key = pool_key.replace("/", "_")
        bfile = baseline_dir / f"{key}.json"
        if not bfile.is_file():
            reasons.append(f"no prior baseline for {pool_key}; baseline created")
        else:
            try:
                prev = json.loads(bfile.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                reasons.append(f"unreadable baseline for {pool_key}")
                incomparable.append(pool_key)
                prev = None
            if prev is not None:
                if prev.get("generator_schema") != snap["generator_schema"]:
                    reasons.append(f"incomparable generator identity for {pool_key}")
                    incomparable.append(pool_key)
                else:
                    pool_deltas[pool_key] = {
                        k: snap[k] - prev.get(k, 0)
                        for k in ("index_chars", "index_lines", "entry_count")
                    }
        baseline_dir.mkdir(parents=True, exist_ok=True)
        bfile.write_text(
            json.dumps(snap, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        written.append(str(bfile))
    # partial semantics: with multiple pools, value sums only comparable pools
    # — consumers must check "partial" before reading it as a total.
    if pool_deltas:
        value = {
            k: sum(d[k] for d in pool_deltas.values())
            for k in ("index_chars", "index_lines", "entry_count")
        }
        value["pools"] = pool_deltas
        value["partial"] = len(pool_deltas) < len(now)
    else:
        value = None
    return {
        "value": value,
        "reason": "; ".join(reasons) or None,
        "baseline_written": written,
        "incomparable": incomparable or None,
    }


def project_writes(canonical, aliases, ambiguous, pools, baseline_dir):
    successful = [
        e for e in canonical if e.status == "completed" and e.tool in ("Write", "Edit")
    ]
    # errors share the Write/Edit scope with successful; CC unmatched pairs are
    # in-flight, not failures — counted separately, never as write errors.
    errors = [
        e for e in canonical if e.status == "error" and e.tool in ("Write", "Edit")
    ]
    unmatched = [
        e for e in canonical if e.status == "unmatched" and e.tool in ("Write", "Edit")
    ]
    by_entry, by_actor = {}, {}
    for e in successful:
        ent = by_entry.setdefault(
            e.entry, {"entry": e.entry, "successful_writes": 0, "payload_chars": 0}
        )
        ent["successful_writes"] += 1
        ent["payload_chars"] += e.payload_chars
        act = by_actor.setdefault(
            e.actor, {"actor": e.actor, "successful_writes": 0, "payload_chars": 0}
        )
        act["successful_writes"] += 1
        act["payload_chars"] += e.payload_chars
    top_entries = sorted(
        by_entry.values(), key=lambda r: (-r["payload_chars"], r["entry"])
    )
    top_actors = sorted(
        by_actor.values(), key=lambda r: (-r["payload_chars"], r["actor"])
    )
    snaps = snapshot_index(pools)
    inventory_entries = [
        {"entry": name, "pool": pk}
        for pk, snap in snaps.items()
        for name in snap["entries"]
    ]
    return {
        "schema": SCHEMA,
        "inventory_timestamp": max(
            (e.record_time for e in successful if e.record_time),
            default=None,
        ),
        "counts": {
            "events_total": len(canonical),
            "successful": len(successful),
            "errors": len(errors),
            "unmatched": len(unmatched),
            "copies_folded": len(aliases),
            "ambiguous": len(ambiguous),
        },
        "top_actors": top_actors,
        "top_entries": top_entries,
        "net_file_delta": {
            "value": None,
            "reason": (
                "no proven before-image for Write/Edit; payload_chars is flow, "
                "not stock"
            ),
        },
        "index_delta": index_delta_with_baseline(pools, baseline_dir),
        "current_inventory": {"entries": inventory_entries},
    }


RANKS = ("hot", "core", "cold")


def read_exemptions(rank, mtime, until):
    """F2 (AIR-49 P2) single source of the zero-read exemption criterion:
    layer-2 no_body_read and the decay projection must judge identically —
    rank=hot or mtime within 30 days of the window end is mechanically
    exempt (until-anchored, deterministic; not a wall-clock judgment)."""
    cutoff = until - timedelta(days=30)
    return {
        "hot": rank == "hot",
        "recent_30d": mtime is not None and mtime >= cutoff,
    }


def _frontmatter_rank(text):
    """Behavioral mirror of the pool generator's parse_frontmatter+parse_rank.

    Equivalence contract (pinned by test_i1/test_i1b): requires a leading
    '---' fence, the frontmatter block ends at the first closing '\\n---'
    (body fences never leak in), only 'metadata:' indented children (not
    other parents) feed the nested placement, a top-level rank with a value
    wins over metadata.rank. Normalization mirrors the generator's two
    layers: parse_frontmatter unquotes TOP-LEVEL values only, then
    parse_rank strips+unquotes+lowercases once — so a quoted top-level
    ' hot ' ends up hot (double-pass) while the same nested value stays
    core (single-pass leaves inner whitespace). Invalid or missing -> core.
    The per-pool generator hash rides along as generator_schema (report
    "generators" map), so consumers can detect mirror drift.
    """
    if not text.startswith(("---\n", "---\r\n")):
        return "core"
    end = text.find("\n---", 4)
    if end < 0:
        return "core"
    top = meta = None
    parent = None
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            k, _, v = line.strip().partition(":")
            if parent == "metadata" and k.strip() == "rank" and v.strip():
                meta = v.strip()  # generator keeps nested values raw
            continue
        k, _, v = line.partition(":")
        parent = k.strip() if not v.strip() else None
        if k.strip() == "rank" and v.strip():
            top = v.strip().strip("'\"")  # generator unquotes top-level
    raw = top or meta
    val = str(raw).strip().strip("'\"").lower() if raw is not None else ""
    return val if val in RANKS else "core"


def snapshot_entries(pools):
    """Inventory with content hash / rank / mtime (AIR-41 S1)."""
    inv = []
    for pool in pools:
        for p in sorted(pool.glob("*.md")):
            if p.name == "MEMORY.md" or p.name.startswith("_"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            inv.append(
                {
                    "entry": p.name,
                    "pool": str(pool),
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "rank": _frontmatter_rank(text),
                    "mtime": iso(datetime.fromtimestamp(p.stat().st_mtime, tz=UTC)),
                }
            )
    return inv


def project_reads(canonical, inventory, coverages, since, until):
    """AIR-41 S1/S2: body-Read observation + coverage-limited candidates."""
    reads_by_entry = {}
    read_errors = 0
    unpaired = 0
    for e in canonical:
        if e.tool != "Read":
            continue
        if e.status == "error":
            read_errors += 1
            continue
        if e.entry == "MEMORY.md":
            continue  # index file, not an entry (EP S1)
        # unmatched (CC result missing) / unknown (zcode state absent) Reads
        # still count as contact — dropping them would flip genuinely read
        # entries into zero-body-read candidates (directional error).
        if e.status != "completed":
            unpaired += 1
        reads_by_entry.setdefault(e.entry, []).append(
            {
                "source": e.source,
                "session": e.session,
                "actor": e.actor,
                "ts": e.operation_start or e.record_time,
                "status": e.status,
                "partial": e.read_range is not None,
                "range": e.read_range,
                "source_ref": e.source_ref,
            }
        )
    observations, no_body = [], []
    for item in inventory:
        name = item["entry"]
        body = reads_by_entry.get(name, [])
        mtime = parse_ts(item["mtime"])
        exemptions = read_exemptions(item["rank"], mtime, until)
        observations.append(
            {
                "entry": name,
                "body_reads": body,
                "zero_body_read": not body,
            }
        )
        if not body:
            no_body.append(
                {
                    "entry": name,
                    "rank": item["rank"],
                    "mtime": item["mtime"],
                    "exemptions": exemptions,
                }
            )
    inventory_names = {item["entry"] for item in inventory}
    reads_without_entry = sorted(set(reads_by_entry) - inventory_names)
    firsts = []
    for db_cov in coverages.get("zcode_dbs", []):
        if db_cov.get("readable"):
            first = parse_ts((db_cov.get("bounds") or {}).get("first"))
            if first:
                firsts.append(first)
    cc_first = parse_ts((coverages.get("claude", {}).get("bounds") or {}).get("first"))
    if cc_first:
        firsts.append(cc_first)
    # window_shortfall: a source whose earliest record post-dates --since
    # cannot testify about the start of the window — zero-read conclusions
    # there are coverage-limited, not evidence of disuse.
    coverages["window_shortfall"] = any(first > since for first in firsts)
    coverages["unpaired_reads"] = unpaired
    c_cov = coverages.get("claude", {})
    partial = (
        not (coverages.get("zcode", {}).get("readable") and c_cov.get("requested"))
        or coverages["window_shortfall"]
        # unreadable files / malformed lines mean part of the source was
        # never parsed — coverage is limited, never "fully observed" (R3)
        or bool(c_cov.get("unreadable"))
        or bool(c_cov.get("malformed"))
    )
    coverages["partial"] = partial
    coverages["read_errors"] = read_errors
    coverages["instrumented"] = [
        s
        for s in ("zcode", "claude")
        if coverages.get(s, {}).get("readable") or coverages.get(s, {}).get("requested")
    ]
    # static manifest — not probed at runtime; extend only when a harness
    # gains a readable telemetry source
    coverages["uninstrumented"] = ["codex", "muse", "bash-rg"]
    return {
        "inventory": inventory,
        "observations": observations,
        "candidates": {
            "no_body_read": no_body,
            "coverage_limited": partial,
            # reads of entries absent from inventory: rename/delete identity
            # clue (EP R6) — HOLD material for LLM adjudication, never
            # auto-merged. maintenance-only / purpose classification stays
            # LLM-side (skill); the collector emits no fake empty slot.
            "reads_without_entry": reads_without_entry,
        },
    }


ATTRIBUTION_SCHEMA = 2


def migrate_prior_writer(prev_writer):
    """Backfill schema-2 provenance keys onto a carried v1 writer.

    Fail-closed migration (never a confidence upgrade):
    - identity: hook source forces "unmatched" (a writer_record never
      emits hook+exact, so the combo is tampered — F3); otherwise an
      existing v2 value passes through, and a missing one is
      RECONSTRUCTED by allowlist — only "zcode"/"claude" yield "exact"
      (F2: "", garbage, or missing source -> unmatched, never silent
      exact).
    - root_complete is True only for a verifiably chain-free record:
      root == session AND (hook source — the hook branch never walks
      chains — or a leaf kind). A carried root != session claims a
      chain nobody can re-walk -> False; a non-hook "subagent" with
      root == session is a v1 cycle/self-parent fallback (classify_actor
      returns session on corruption), NOT a proven leaf -> False (F1).
    - ts_basis is "unknown": old ts provenance is unknowable, and
      carried writers never re-enter winner competition (carry runs
      only with zero window events), so no ordering risk.
    Dirty "unordered" needs no backfill: dirty_events are recomputed
    from the current window every run and never carried — absence of
    the key means ordered, regardless of what any old version emitted.
    """
    w = dict(prev_writer)
    if w.get("source") == "hook":
        w["identity"] = "unmatched"
    elif w.get("identity") not in ("exact", "unmatched"):
        w["identity"] = (
            "exact" if w.get("source") in ("zcode", "claude") else "unmatched"
        )
    w.setdefault(
        "root_complete",
        w.get("root") == w.get("session")
        and (
            w.get("source") == "hook"
            or w.get("kind")
            in ("interactive", "harness", "automation", "external_unknown")
        ),
    )
    w.setdefault("ts_basis", "unknown")
    return w


# actor kind single source (AIR-55/P5): evidence -> kind, never guessed.
# - interactive: zcode task_type interactive, no parent
# - subagent: parented session or subagent-ish task_type (or hook-merged
#   agent_id on a transcript event)
# - harness: claude/hook-channel session with no leaf evidence
# - external_unknown: zcode event whose session is absent from the session
#   table (join miss). Hash-mismatch / dirty legs emit writer None, never a
#   classified kind — absence of attribution, not a kind.
# - automation: task_type in AUTOMATION_TASKS (empty-match today; extension
#   point — cron sessions have no distinct task_type in current db evidence)
AUTOMATION_TASKS = ("cron", "scheduled", "launchd")
SUBAGENT_TASKS = ("subagent_child", "selection_side_chat", "fork")


def classify_actor(event, sessions):
    """Return (kind, root, root_complete).

    Root is the outermost-KNOWN actor/session id, not a proven traversal:
    root_complete=False when the chain is truncated (a parent id absent from
    the session map — window/deleted ancestry) or cyclic (corrupt data; root
    falls back to the event session, the only verified containment). A
    cyclic node is never silently elected as root.
    """
    parent, task = sessions.get(event.session, (None, None))
    if event.source == "hook":
        # CC PostToolUse sensor: agent_id present = subagent leaf, else the
        # harness session itself acted (channel known, leaf unknown).
        ref = event.source_ref or {}
        kind = "subagent" if ref.get("agent_id") else "harness"
        return kind, event.session, True
    # + hook-merged agent_id on a transcript event: a known leaf beats the
    # channel-default harness rule below (root stays the session: CC carries
    # no parent chain).
    if (
        parent is not None
        or task in SUBAGENT_TASKS
        or (event.source == "claude" and (event.source_ref or {}).get("agent_id"))
    ):
        root, seen, complete = event.session, {event.session}, True
        while parent:
            if parent in seen:
                complete, root = False, event.session
                break
            seen.add(parent)
            root = parent
            if parent not in sessions:
                complete = False
                break
            parent, _ = sessions.get(parent)
        return "subagent", root, complete
    if task == "interactive":
        return "interactive", event.session, True
    if task in AUTOMATION_TASKS:
        return "automation", event.session, True
    if event.source == "claude":
        return "harness", event.session, True
    return "external_unknown", event.session, True


def _event_ts(event):
    return event.operation_end or event.record_time


def build_attribution(canonical, sessions, inventory, prior, dirty=None):
    """AIR-55/P5: per-entry last-tracked-writer projection.

    Contract (projection says who was last SEEN, never how much to trust):
    - strictly-latest completed Write/Edit -> consistent (+current hash stored)
    - top tie (same ts, differing session or input) -> ambiguous + candidates
    - mixed time_source among competitors -> ambiguous, reason
      "mixed-time-bases" (cross-channel clocks have no total order)
    - unmatched-hook winner vs exact-identity competitors -> ambiguous,
      reason "unmatched-hook-vs-exact" (hook-vs-hook keeps ts order)
    Downgrade priority: timestamp-tie is judged first; mixed-time-bases
    second; unmatched-hook-vs-exact last (all ambiguous — reason only
    routes triage, never changes the verdict).
    - no window event + prior hash match -> consistent (carried writer)
    - no window event + prior hash mismatch -> unattributed_external
    - no window event + no prior -> stale (writer null, never fabricated)
    dirty: [{entry, ts}] file_changed evidence (watcher != writer) — sets
    dirty_after_tracked when a dirty ts postdates the last tracked write
    (same-content-rewrite suspect flag; status enum unchanged). Unparseable
    dirty ts is retained as {"unordered": True} and forces the flag
    (fail-closed: unorderable mutation, never dropped).
    Single-pool semantics: entry keys are bare pool filenames; main() REFUSES
    multiple --pool args outright (see pools guard) precisely because basename
    keying cannot prevent cross-pool evidence blending. One pool per report.
    """
    current = {item["entry"]: item["sha256"] for item in inventory}
    writes_by_entry = {}
    for e in canonical:
        if e.tool not in ("Write", "Edit") or e.status != "completed":
            continue
        if e.entry == "MEMORY.md":
            continue
        writes_by_entry.setdefault(e.entry, []).append(e)
    prior_entries = {}
    prior_note = None
    if prior is not None:
        if isinstance(prior, dict) and isinstance(prior.get("entries"), dict):
            prior_entries = prior["entries"]
        else:
            prior_note = "prior sidecar unreadable or wrong shape; treated as absent"
    entries = {}
    names = sorted(set(current) | set(writes_by_entry) | set(prior_entries))
    for name in names:
        sha_now = current.get(name)
        evs = writes_by_entry.get(name, [])
        # dedupe same session+content retries; order by ts, id for determinism
        seen, uniq = set(), []
        for e in sorted(evs, key=lambda x: (_event_ts(x) or "", x.id)):
            key = (e.session, e.input_sha256, _event_ts(e))
            if key not in seen:
                seen.add(key)
                uniq.append(e)
        count = len(uniq)
        if uniq:
            top_ts = _event_ts(uniq[-1])
            tied = [e for e in uniq if _event_ts(e) == top_ts]
            contested = any(
                (e.session, e.input_sha256) != (tied[0].session, tied[0].input_sha256)
                for e in tied[1:]
            )
            if contested:
                entries[name] = {
                    "status": "ambiguous",
                    "last_tracked_writer": None,
                    "tracked_content_hash": sha_now,
                    "current_sha256": sha_now,
                    "write_count_window": count,
                    "candidates": [writer_record(e, sessions) for e in tied],
                    "reason": "timestamp-tie",
                }
                continue
            winner = uniq[-1]
            # B: operation-vs-record clocks across channels have no total
            # order — mixed bases among competitors mean ordering_uncertain,
            # never a confident winner (no fabricated skew margin can fix
            # cross-harness clocks; same-basis keeps its order).
            if len({e.time_source for e in uniq}) > 1:
                entries[name] = {
                    "status": "ambiguous",
                    "last_tracked_writer": None,
                    "tracked_content_hash": sha_now,
                    "current_sha256": sha_now,
                    "write_count_window": count,
                    "candidates": [writer_record(e, sessions) for e in uniq],
                    "reason": "mixed-time-bases",
                }
                continue
            # C: an unmatched hook observation (sentinel hash, no transcript
            # counterpart) must not outrank exact-identity events on ts
            # alone. Hook-vs-hook keeps ts order (same identity grade).
            if winner.source == "hook" and any(e.source != "hook" for e in uniq):
                entries[name] = {
                    "status": "ambiguous",
                    "last_tracked_writer": None,
                    "tracked_content_hash": sha_now,
                    "current_sha256": sha_now,
                    "write_count_window": count,
                    "candidates": [writer_record(e, sessions) for e in uniq],
                    "reason": "unmatched-hook-vs-exact",
                }
                continue
            entries[name] = {
                "status": "consistent",
                "last_tracked_writer": writer_record(winner, sessions),
                "tracked_content_hash": sha_now,
                "current_sha256": sha_now,
                "write_count_window": count,
                "candidates": [],
            }
            continue
        prev = (
            prior_entries.get(name, {})
            if isinstance(prior_entries.get(name), dict)
            else {}
        )
        prev_hash = prev.get("tracked_content_hash")
        prev_writer = prev.get("last_tracked_writer")
        # F9: prior is untrusted input — carry only a well-formed writer
        # (session str); anything else is treated as no prior (fail-closed,
        # writer null rather than propagated garbage).
        if not isinstance(prev_writer, dict) or not isinstance(
            prev_writer.get("session"), str
        ):
            prev_hash, prev_writer = None, None
        else:
            # schema-2 migration: v1 writers lack ts_basis/identity/
            # root_complete — backfill fail-closed, never upgrade.
            prev_writer = migrate_prior_writer(prev_writer)
        if sha_now is None:
            # F1: entry absent from pool with no window writes — not a live
            # external mutation; keep the carried writer for forensics.
            entries[name] = {
                "status": "absent",
                "last_tracked_writer": prev_writer,
                "tracked_content_hash": prev_hash,
                "current_sha256": None,
                "write_count_window": 0,
                "candidates": [],
            }
            continue
        if prev_hash is not None and isinstance(prev_writer, dict):
            if sha_now is not None and sha_now == prev_hash:
                entries[name] = {
                    "status": "consistent",
                    "last_tracked_writer": prev_writer,
                    "tracked_content_hash": sha_now,
                    "current_sha256": sha_now,
                    "write_count_window": 0,
                    "candidates": [],
                    "carried_from_prior": True,
                }
                continue
            entries[name] = {
                "status": "unattributed_external",
                "last_tracked_writer": None,
                "tracked_content_hash": sha_now,
                "current_sha256": sha_now,
                "write_count_window": 0,
                "candidates": [],
            }
            continue
        entries[name] = {
            "status": "stale",
            "last_tracked_writer": None,
            "tracked_content_hash": sha_now,
            "current_sha256": sha_now,
            "write_count_window": 0,
            "candidates": [],
        }
    for rec in entries.values():
        rec.setdefault("present", rec.get("current_sha256") is not None)
    dirty_by_entry = {}
    for d in dirty or []:
        # unparseable ts -> (None, d): retained as an unorderable mutation,
        # never dropped (fail-closed).
        dirty_by_entry.setdefault(d.get("entry"), []).append((parse_ts(d.get("ts")), d))
    for name, rec in entries.items():
        devs = dirty_by_entry.get(name, [])
        wts = parse_ts((rec["last_tracked_writer"] or {}).get("ts"))
        unordered = any(dts is None for dts, _ in devs)
        rec["dirty_after_tracked"] = unordered or any(
            wts is None or dts > wts for dts, _ in devs if dts is not None
        )
        rec["dirty_events"] = [
            (
                {"ts": d.get("ts"), "watcher": d.get("watcher"), "unordered": True}
                if dts is None
                else {"ts": d.get("ts"), "watcher": d.get("watcher")}
            )
            for dts, d in devs
        ]
    return entries, prior_note


def normalize_hook_events(paths, pools, since, until, canonical):
    """AIR-56: merge CC hook sensor JSONL into canonical + dirty evidence.

    - post_tool_use matching an existing event (session + call_id) enriches
      it (agent ids) instead of duplicating; unmatched becomes a new tracked
      write (source hook, sentinel input hash — never folds copies).
    - file_changed is dirty evidence only (watcher != writer): returned
      separately, never as a write event.
    """
    dirty = []
    coverage = {
        "requested": bool(paths),
        "files": 0,
        "malformed": 0,
        "merged": 0,
        "added": 0,
    }
    if not paths:
        return dirty, coverage
    by_key = {
        (e.session, e.call_id, e.canonical_path): e
        for e in canonical
        if e.call_id and e.canonical_path
    }
    for raw in paths:
        p = Path(str(raw)).expanduser()
        if not p.is_file():
            coverage.setdefault("missing", []).append(str(raw))
            continue
        coverage["files"] += 1
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            coverage.setdefault("unreadable", []).append(str(raw))
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                coverage["malformed"] += 1
                continue
            if not isinstance(d, dict):
                coverage["malformed"] += 1
                continue
            kind = d.get("kind")
            ts = parse_ts(d.get("ts"))
            if kind == "file_changed":
                canon, entry = resolve_pool_entry(pools, d.get("file_path"))
                if canon is None or entry is None:
                    coverage["skipped_pool"] = coverage.get("skipped_pool", 0) + 1
                    continue
                if ts is None:
                    # fail-closed: a mutation was seen but carries no
                    # orderable clock — retain the raw ts; the projection
                    # marks the entry dirty-unordered (never silently
                    # dropped, never counted as skipped).
                    dirty.append(
                        {
                            "entry": entry,
                            "pool": canon,
                            "ts": d.get("ts"),
                            "watcher": d.get("watcher_session"),
                        }
                    )
                elif in_window(ts, since, until):
                    dirty.append(
                        {
                            "entry": entry,
                            "pool": canon,
                            "ts": iso(ts),
                            "watcher": d.get("watcher_session"),
                        }
                    )
                else:
                    coverage["skipped_window"] = coverage.get("skipped_window", 0) + 1
                continue
            if kind != "post_tool_use":
                coverage["malformed"] += 1
                continue
            canon, entry = resolve_pool_entry(pools, d.get("file_path"))
            if canon is None or entry is None:
                coverage["skipped_pool"] = coverage.get("skipped_pool", 0) + 1
                continue
            if ts is None or not in_window(ts, since, until):
                coverage["skipped_window"] = coverage.get("skipped_window", 0) + 1
                continue
            call_id = d.get("tool_use_id")
            key = (d.get("session_id"), call_id, canon)
            if call_id and key in by_key:
                ref = by_key[key].source_ref or {}
                for k in ("agent_id", "agent_type"):
                    if d.get(k) and k not in ref:
                        ref[k] = d[k]
                by_key[key].source_ref = ref
                coverage["merged"] += 1
                continue
            canonical.append(
                Event(
                    source="hook",
                    id=f"hook-{coverage['files']}-{line_no}",
                    session=d.get("session_id") or "unknown",
                    parent=None,
                    task_type=None,
                    tool=d.get("tool")
                    if d.get("tool") in ("Write", "Edit")
                    else "Write",
                    status="completed",
                    operation_start=iso(ts),
                    operation_end=iso(ts),
                    record_time=iso(ts),
                    time_source="operation",
                    raw_path=str(d.get("file_path")),
                    canonical_path=canon,
                    entry=entry,
                    payload_chars=0,
                    input_sha256="hook:" + str(call_id or f"{p}:{line_no}"),
                    call_id=str(call_id) if call_id else None,
                    source_ref={
                        "hook_log": str(p),
                        "line": line_no,
                        "agent_id": d.get("agent_id"),
                        "agent_type": d.get("agent_type"),
                    },
                )
            )
            coverage["added"] += 1
    return dirty, coverage


def writer_record(event, sessions):
    kind, root, root_complete = classify_actor(event, sessions)
    return {
        "ts": _event_ts(event),
        # ts_basis: which clock the ts came from — consumers must not
        # total-order across differing bases (see build_attribution B).
        "ts_basis": event.time_source,
        "source": event.source,
        "session": event.session,
        "root": root,
        # root_complete=False: outermost-KNOWN id, not a verified root
        # (truncated chain or cycle — see classify_actor).
        "root_complete": root_complete,
        "kind": kind,
        # identity: hook sentinels never merged to a transcript event are
        # observations, not exact-identity writes (see C).
        "identity": "exact" if event.source != "hook" else "unmatched",
        "prompt": (event.source_ref or {}).get("message_id"),
        "tool": event.tool,
        "call_id": event.call_id,
    }


def project_decay(projection, until, max_unused_days=30, promotion_min_reads=3):
    """AIR-49 P2: aggregate the reads projection into decay candidates.

    Rules (spec, candidates only — never verdicts, never auto-delete):
    1) zero in-window body reads and not exempted -> unused; exempted
    zero-read entries are noted separately (same criterion as layer-2
    no_body_read, via read_exemptions). 2) everything else sorts by
    reads_count asc then last_read asc (decay order). 3) last_read older
    than max_unused_days before the window end marks a decaying candidate.
    Cold entries with heavy in-window reads surface as rank-promotion
    candidates (human-adjudication input; automation leg left open).
    """
    cutoff = until - timedelta(days=max_unused_days)
    inv = {i["entry"]: i for i in projection["inventory"]}
    no_body = {c["entry"]: c for c in projection["candidates"]["no_body_read"]}
    unused, exempted_zero, active = [], [], []
    for obs in projection["observations"]:
        name = obs["entry"]
        item = inv[name]
        body = obs["body_reads"]
        count = len(body)
        last = max((r["ts"] for r in body if r["ts"]), default=None)
        exemptions = (
            no_body[name]["exemptions"]
            if count == 0
            else read_exemptions(item["rank"], parse_ts(item["mtime"]), until)
        )
        rec = {
            "entry": name,
            "rank": item["rank"],
            "mtime": item["mtime"],
            "reads_count": count,
            "last_read_ts": last,
            "exempted": exemptions["hot"] or exemptions["recent_30d"],
            "exemptions": exemptions,
        }
        if count == 0:
            (exempted_zero if rec["exempted"] else unused).append(rec)
        else:
            active.append(rec)
    # rule 2: usage asc, then last_read asc (parse_ts key——ISO 字串序在混合時區偏移下≠時序；
    # None fallback＝tz-aware 下界，避免 None/aware datetime 混排 TypeError)
    active.sort(
        key=lambda r: (
            r["reads_count"],
            parse_ts(r["last_read_ts"]) or datetime.min.replace(tzinfo=UTC),
        )
    )
    decaying, healthy = [], []
    for rec in active:
        last = parse_ts(rec["last_read_ts"]) if rec["last_read_ts"] else None
        (decaying if last is not None and last < cutoff else healthy).append(rec)
    promotion = sorted(
        (
            rec
            for rec in active
            if rec["rank"] == "cold" and rec["reads_count"] >= promotion_min_reads
        ),
        key=lambda r: (-r["reads_count"], r["entry"]),
    )
    return {
        "unused": unused,
        "exempted_zero_read": exempted_zero,
        "decaying": decaying,
        "healthy": healthy,
        "rank_promotion": promotion,
    }


def render_decay_md(report):
    """Human-readable four-section view: 1 unused (+exempt notes) / 2 decaying
    / 3 rank promotion / 4 coverage statement. Candidates are never verdicts
    — a human adjudicates, nothing is deleted automatically."""
    cand = report["candidates"]
    counts = report["counts"]
    win = report["window"]
    params = report["parameters"]
    cov = report["coverage"]
    display = {"zcode": "ZCode", "claude": "CC"}
    channels = [display.get(s, s) for s in cov.get("instrumented", [])]
    lines = [
        f"# Decay 候選清單（{report['pool']}）",
        "",
        (
            f"> 窗：{win['start']} → {win['end']}"
            f"｜max_unused_days={params['max_unused_days']}"
            f"｜promotion_min_reads={params['promotion_min_reads']}"
        ),
        (
            "> **候選非判決——人裁不自動刪**（decay 只產候選；"
            "由 memory-audit 層 3 夜波①併入報告人裁消費）"
        ),
        "",
        "## 1. Unused 候選（窗內零 body reads、未豁免）",
        "",
    ]
    if cand["unused"]:
        lines += ["| entry | rank | mtime |", "|---|---|---|"]
        lines += [
            f"| {r['entry']} | {r['rank']} | {r['mtime']} |" for r in cand["unused"]
        ]
    else:
        lines.append("（無）")
    lines += ["", "### 豁免註記（零讀但機械豁免——僅記錄，不入候選）", ""]
    if cand["exempted_zero_read"]:
        lines += ["| entry | rank | mtime | exemptions |", "|---|---|---|---|"]
        for r in cand["exempted_zero_read"]:
            reasons = ",".join(k for k, v in r["exemptions"].items() if v) or "none"
            lines += [f"| {r['entry']} | {r['rank']} | {r['mtime']} | {reasons} |"]
    else:
        lines.append("（無）")
    lines += [
        "",
        f"## 2. 衰減候選（有 reads，last_read 距窗尾 > {params['max_unused_days']} 日）",
        "",
    ]
    if cand["decaying"]:
        lines += ["| entry | rank | reads | last_read |", "|---|---|---|---|"]
        lines += [
            f"| {r['entry']} | {r['rank']} | {r['reads_count']} | {r['last_read_ts']} |"
            for r in cand["decaying"]
        ]
    else:
        lines.append("（無）")
    lines += [
        "",
        "## 3. Rank 升級候選（窗內高讀取且 rank=cold——人裁輸入；自動化腿遺留標記）",
        "",
    ]
    if cand["rank_promotion"]:
        lines += ["| entry | reads | last_read |", "|---|---|---|"]
        lines += [
            f"| {r['entry']} | {r['reads_count']} | {r['last_read_ts']} |"
            for r in cand["rank_promotion"]
        ]
    else:
        lines.append("（無）")
    lines += [
        "",
        "## 4. Coverage 聲明",
        "",
        (
            f"- 通道覆蓋：{'＋'.join(channels) if channels else '無（未提供 telemetry 來源）'}"
            " 兩主通道觀測；未覆蓋通道："
            + "、".join(cov.get("uninstrumented", ["codex", "muse", "bash-rg"]))
            + "（其 reads 不入 db/transcript＝盲區，不假裝覆蓋）"
        ),
        (
            f"- partial={cov.get('partial')}"
            f"｜window_shortfall={cov.get('window_shortfall')}"
            f"｜read_errors={cov.get('read_errors', 0)}"
            f"｜unpaired_reads={cov.get('unpaired_reads', 0)}"
        ),
        (
            f"- 統計：entries={counts['entries']}"
            f"｜unused={counts['unused']}"
            f"｜豁免={counts['exempted_zero_read']}"
            f"｜衰減={counts['decaying']}"
            f"｜healthy={counts['healthy']}"
            f"｜rank 升級候選={counts['rank_promotion']}"
        ),
        "",
    ]
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Read-only memory telemetry (AIR-40 S1)"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("writes", help="emit normalized events + coverage JSON")
    w.add_argument("--pool", action="append", required=True)
    w.add_argument("--zcode-db", action="append", default=[])
    w.add_argument("--cc-root", action="append", default=[])
    w.add_argument("--since", default=None)
    w.add_argument("--until", default=None)
    w.add_argument("--output", required=True)
    w.add_argument(
        "--baseline-dir",
        default=None,
        help="enable index-delta snapshots in this directory (default: disabled)",
    )
    rd = sub.add_parser("reads", help="body-Read observation (AIR-41)")
    rd.add_argument("--pool", action="append", required=True)
    rd.add_argument("--zcode-db", action="append", default=[])
    rd.add_argument("--cc-root", action="append", default=[])
    rd.add_argument("--since", default=None)
    rd.add_argument("--until", default=None)
    rd.add_argument("--output", required=True)
    at = sub.add_parser(
        "attribution", help="per-entry last-tracked-writer sidecar (AIR-55/P5)"
    )
    at.add_argument("--pool", action="append", required=True)
    at.add_argument("--zcode-db", action="append", default=[])
    at.add_argument("--cc-root", action="append", default=[])
    at.add_argument("--since", default=None)
    at.add_argument("--until", default=None)
    at.add_argument("--output", required=True)
    at.add_argument(
        "--prior-sidecar",
        default=None,
        help="previous attribution output: hash continuity leg (carry vs "
        "unattributed_external); corrupt/missing treated as absent (noted)",
    )
    at.add_argument(
        "--hook-events",
        action="append",
        default=[],
        help="hook sensor JSONL (post_tool_use merged/enriched, file_changed "
        "as dirty evidence; AIR-56)",
    )
    dc = sub.add_parser(
        "decay", help="usage-driven decay candidates (AIR-49 P2; candidates only)"
    )
    dc.add_argument("--pool", action="append", required=True)
    dc.add_argument("--zcode-db", action="append", default=[])
    dc.add_argument("--cc-root", action="append", default=[])
    dc.add_argument("--since", default=None)
    dc.add_argument("--until", default=None)
    dc.add_argument(
        "--max-unused-days",
        type=int,
        default=30,
        help=(
            "last_read older than this many days before the window end "
            "marks a decaying candidate (default: 30)"
        ),
    )
    dc.add_argument(
        "--promotion-min-reads",
        type=int,
        default=3,
        help=(
            "cold entries with at least this many in-window reads surface "
            "as rank-promotion candidates (default: 3)"
        ),
    )
    return parser.parse_args(argv)


def fail(message, code=2):
    sys.stderr.write(json.dumps({"schema": SCHEMA, "error": message}) + "\n")
    return code


def main(argv=None):
    args = parse_args(argv)
    pools = []
    for raw in args.pool:
        p = Path(raw).expanduser()
        if not p.is_dir():
            return fail(f"pool not a directory: {raw}")
        p = p.resolve()
        if p not in pools:
            pools.append(p)
    if len(pools) > 1:
        # projections key by entry basename and history contains deleted
        # entries — guarding on current files cannot prevent cross-pool
        # evidence blending, so the contract is one pool per report (F2)
        return fail(
            "multiple pools refused: projections key by basename and history "
            "may collide — run one pool per report (aliases are deduplicated)"
        )
    if args.command == "decay":
        # F3 (AIR-49 P2): decay writes the fixed _decay-candidates.{json,md}
        # pair inside the pool by design — there is no --output flag, so the
        # generic output-inside-sources guard below does not apply. The
        # source-side half of that guard still applies and runs below (F4).
        out_resolved = None
    else:
        out = Path(args.output).expanduser()
        try:
            out_resolved = out.resolve()
        except OSError:
            out_resolved = out.absolute()

    def _resolved(raw):
        try:
            return Path(raw).expanduser().resolve()
        except OSError:
            return Path(raw).expanduser().absolute()

    # sources must be canonicalized the same way as the output, otherwise a
    # relative path or symlink alias defeats the equality check (R1)
    source_paths = [_resolved(p) for p in args.zcode_db + args.cc_root]
    if args.command == "decay":
        # F4 (AIR-49): a pool alias resolving inside a source tree (db dir or
        # transcript root) puts the fixed decay outputs inside the sources —
        # writing them would clobber the input. R1 canonical-path semantics,
        # scoped to sources only (pool-internal output is by design).
        # R3: a symlinked fixed output (e.g. pointing at a pool entry) evades
        # the resolved-path source check — write_text follows it and clobbers
        # the target. Refuse symlinks outright.
        for out in (
            pools[0] / "_decay-candidates.json",
            pools[0] / "_decay-candidates.md",
        ):
            if out.is_symlink():
                return fail(f"decay fixed output is a symlink, refused: {out}")
            out_r = _resolved(out)
            for protected in source_paths:
                if out_r == protected or protected in out_r.parents:
                    return fail(f"decay fixed output inside sources refused: {out}")
    if out_resolved is not None:
        for protected in pools + source_paths:
            try:
                if out_resolved == protected or protected in out_resolved.parents:
                    return fail(f"output inside sources refused: {args.output}")
            except OSError:
                continue
        if getattr(args, "baseline_dir", None):
            baseline_resolved = _resolved(args.baseline_dir)
            for protected in pools + source_paths:
                if (
                    baseline_resolved == protected
                    or protected in baseline_resolved.parents
                ):
                    return fail(
                        f"baseline dir inside sources refused: {args.baseline_dir}"
                    )
    until = (
        parse_ts(args.until) if args.until else datetime.now(UTC).replace(microsecond=0)
    )
    default_days = 90 if args.command in ("reads", "decay") else 7
    since = parse_ts(args.since) if args.since else until - timedelta(days=default_days)
    if since is None or until is None or since >= until:
        return fail("invalid --since/--until window")
    if out_resolved is not None:
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return fail(f"cannot create output dir: {exc}")
    events, coverages, sessions = [], {}, {}
    if args.zcode_db:
        for db_path in args.zcode_db:
            if not Path(db_path).is_file():
                return fail(f"zcode db unreadable: {db_path}")
        for db_path in args.zcode_db:
            z_events, z_cov = read_zcode(db_path, pools, since, until)
            events.extend(z_events)
            coverages.setdefault("zcode_dbs", []).append(
                {"path": str(db_path), **z_cov}
            )
    else:
        coverages["zcode_dbs"] = [{"requested": False}]
    zcovs = [c for c in coverages.get("zcode_dbs", []) if c.get("readable")]
    coverages["zcode"] = {
        "readable": bool(zcovs) if args.zcode_db else False,
        "rows_scanned": sum(c.get("rows_scanned", 0) for c in zcovs),
        "unknown_shapes": sum(c.get("unknown_shapes", 0) for c in zcovs),
    }
    if args.cc_root:
        c_events, c_cov = read_claude(args.cc_root, pools, since, until)
        events.extend(c_events)
        coverages["claude"] = c_cov
        if c_cov.get("missing"):
            return fail(f"cc roots missing: {c_cov['missing']}")
    else:
        coverages["claude"] = {"requested": False}
    coverages["pools"] = [str(p) for p in pools]
    for db_path in args.zcode_db:
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            for sid, parent, task in con.execute(
                "select id, parent_id, task_type from session"
            ):
                sessions[sid] = (parent, task)
            con.close()
        except sqlite3.Error:
            pass
    canonical, aliases, ambiguous = resolve_lineage(events, sessions)
    unknown = sorted(
        {e.session for e in events if e.actor == "unknown" and e.session != "unknown"}
    )
    events.sort(key=lambda e: (e.record_time or "", e.id))
    if args.command == "decay":
        inventory = snapshot_entries(pools)
        projection = project_reads(canonical, inventory, coverages, since, until)
        candidates = project_decay(
            projection, until, args.max_unused_days, args.promotion_min_reads
        )
        report = {
            "schema": SCHEMA,
            "type": "decay_candidates",
            "window": {"start": iso(since), "end": iso(until)},
            "pool": str(pools[0]),
            "parameters": {
                "max_unused_days": args.max_unused_days,
                "promotion_min_reads": args.promotion_min_reads,
            },
            "coverage": coverages,
            "generators": {str(p): generator_identity(p) for p in pools},
            "counts": {
                "entries": len(inventory),
                **{k: len(v) for k, v in candidates.items()},
            },
            "candidates": candidates,
        }
        json_path = pools[0] / "_decay-candidates.json"
        md_path = pools[0] / "_decay-candidates.md"
        json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        md_path.write_text(render_decay_md(report), encoding="utf-8")
        c = report["counts"]
        print(
            f"[OK] entries={c['entries']} unused={c['unused']} "
            f"exempted_zero_read={c['exempted_zero_read']} "
            f"decaying={c['decaying']} healthy={c['healthy']} "
            f"rank_promotion={c['rank_promotion']} "
            f"partial={coverages.get('partial')} out={json_path}"
        )
        return 0
    if args.command == "reads":
        inventory = snapshot_entries(pools)
        projection = project_reads(canonical, inventory, coverages, since, until)
        report = {
            "schema": SCHEMA,
            "window": {"start": iso(since), "end": iso(until)},
            "coverage": coverages,
            # the rank mirror above is a behavioral copy of the per-pool
            # generator; its hash rides along so consumers can detect drift
            "generators": {str(p): generator_identity(p) for p in pools},
            "aliases": aliases,
            "ambiguous": ambiguous,
            "unknown": unknown,
            **projection,
        }
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        obs = projection["observations"]
        zero = len(projection["candidates"]["no_body_read"])
        print(
            f"[OK] entries={len(inventory)} body_read_entries="
            f"{sum(1 for o in obs if o['body_reads'])} zero_body_read={zero} "
            f"read_errors={coverages.get('read_errors', 0)} "
            f"unpaired_reads={coverages.get('unpaired_reads', 0)} "
            f"window_shortfall={coverages.get('window_shortfall')} "
            f"partial={coverages.get('partial')}"
        )
        return 0
    if args.command == "attribution":
        hook_dirty, hook_cov = normalize_hook_events(
            getattr(args, "hook_events", []), pools, since, until, canonical
        )
        coverages["hooks"] = hook_cov
        inventory = snapshot_entries(pools)
        prior, prior_status = None, "absent"
        prior_path = getattr(args, "prior_sidecar", None)
        if prior_path:
            try:
                prior = json.loads(
                    Path(prior_path).expanduser().read_text(encoding="utf-8")
                )
                prior_status = "loaded"
            except (ValueError, OSError) as exc:
                prior_status = f"unreadable ({exc}); treated as absent"
        entries, prior_note = build_attribution(
            canonical, sessions, inventory, prior, hook_dirty
        )
        if prior_note:
            prior_status = prior_note
        by_status: dict = {}
        for rec in entries.values():
            by_status[rec["status"]] = by_status.get(rec["status"], 0) + 1
        report = {
            "attribution_schema": ATTRIBUTION_SCHEMA,
            "pool": str(pools[0]),
            "window": {"start": iso(since), "end": iso(until)},
            "built_at": iso(datetime.now(UTC).replace(microsecond=0)),
            "coverage": coverages,
            "prior": {"requested": bool(prior_path), "status": prior_status},
            "counts": {"entries": len(entries), **by_status},
            "entries": entries,
        }
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(
            f"[OK] entries={len(entries)} "
            + " ".join(f"{k}={v}" for k, v in sorted(by_status.items()))
        )
        return 0
    baseline_dir = Path(args.baseline_dir).expanduser() if args.baseline_dir else None
    projection = project_writes(canonical, aliases, ambiguous, pools, baseline_dir)
    report = {
        "schema": SCHEMA,
        "window": {"start": iso(since), "end": iso(until)},
        "coverage": coverages,
        "events": [asdict(e) for e in canonical]
        + [{**asdict(e), "folded": True} for e in events if e.copy_of is not None],
        "aliases": aliases,
        "ambiguous": ambiguous,
        "unknown": unknown,
        "report": projection,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        f"[OK] events={len(report['events'])} aliases={len(aliases)} "
        f"ambiguous={len(ambiguous)} unknown_actors={len(unknown)} "
        f"successful={projection['counts']['successful']} "
        f"errors={projection['counts']['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
