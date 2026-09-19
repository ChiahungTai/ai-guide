#!/usr/bin/env python3
"""agent_liveness_sweep — bridge jobs liveness sweep（唯讀 reporter）.

契約源：AIR-135.7（AC#3 collection contract、AC#6② sweep＝唯讀 reporter——
只標不殺、只報轉移、偵測與處置分離）＋ rules/bridge-dispatch.md
「Dispatch⇄collection 配對」（terminal≠complete；sink 三步＝存在→非空→錨點）。

v1 資料源（bridge ledger 是 per-repo 的——`--state-root` 可多根，預設 ai-guide＋delegate-bridge）：
- 各根 jobs ledger：`<state-root>/jobs/*.jsonl`（事件流，三種形態）
  ＋ `<state-root>/jobs.json`（bridge 自家索引；dispatch 時以 running 寫入、
  終態更新——terminal face 權威；persisted status set 是 OPEN，未知值視 terminal）
- liveness 六欄台帳：session-journal.md 的六欄表（id/carrier/ts/sink/expect/collect）；
  台帳↔bridge 對接鍵＝job id（短形 id 以 faces 前綴正典化）

分類：collected / terminal-unclaimed / running-fresh / zombie-suspect / unledgered。
唯讀保證：除讀檔外無任何寫入／刪除／kill；exit 0（reporter 不以 exit 碼報 finding）。
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_STATE_ROOTS = (
    Path("/Users/ctai/Github/ai-guide/.delegate-bridge"),
    Path("/Users/ctai/Github/delegate-bridge/.delegate-bridge"),
)
DEFAULT_JOURNAL = Path("/Users/ctai/Github/ai-guide/.agent-tmp/session-journal.md")
DEFAULT_SINK_BASE = Path("/Users/ctai/Github/ai-guide")

ZOMBIE_HOURS_DEFAULT = 6.0
WINDOW_HOURS_DEFAULT = 168.0

# bridge 索引（jobs.json）已知狀態集——persisted set 是 OPEN（job.rs is_known_status），
# 此處只用於「是否 terminal」判定，未知名一律視 terminal face（bridge 只在終態寫非 running 值）。
RUNNING = "running"

JOB_ID_RE = re.compile(r"job-[a-z0-9]+(?:-[a-z0-9]+)*")
PATH_RE = re.compile(r"[^\s（）()，,；;|｜]*\/[^\s（）()，,；;|｜]+")
COLLECTED_RE = re.compile(r"已收|已回收|已\s*collect")
ANCHOR_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{3,}")

TERMINAL_RUN_EVENTS = {
    "run.terminal.completed": "completed",
    "run.terminal.failed": "failed",
}
STREAM_TERMINAL_EVENTS = {
    "turn.completed": "completed",
    "turn.failed": "failed",
    "result": "completed",
}


@dataclass
class JobFace:
    """單一 bridge job 的兩面狀態（索引面＋事件流面）合成的 sweep 視圖。"""

    job_id: str
    root: Path  # 所屬 state root（bridge ledger 是 per-repo 的）
    index_status: str | None = None
    index_ts: datetime | None = None
    family: str | None = None
    file_status: str | None = None  # jsonl 事件流推出的 terminal face（無終態標記＝None）
    file_reason: str = ""  # 該 face 的判定依據（事件種類／response 檔／mtime）
    last_activity: datetime | None = None
    response_len: int = 0
    summary: str | None = None

    @property
    def status(self) -> str:
        # 索引 terminal face 權威；索引 running／缺席時，事件流 terminal 標記可推翻 running
        # （bridge finalize 前崩潰的殘留）；兩面皆無 → running。
        if self.index_status and self.index_status != RUNNING:
            return self.index_status
        if self.file_status:
            return self.file_status
        return RUNNING

    @property
    def status_face(self) -> str:
        if self.index_status and self.index_status != RUNNING:
            face = "index"
        elif self.file_status:
            face = "jsonl"
        else:
            face = "running"
        return face


@dataclass
class LedgerRow:
    """session-journal 六欄台帳列（id/carrier/ts/sink/expect/collect）。"""

    cells: list[str]
    line_no: int
    job_ids: set[str] = field(default_factory=set)

    @property
    def collected(self) -> bool:
        return bool(COLLECTED_RE.search(self.cells[5]))

    @property
    def sink(self) -> str:
        return self.cells[3]

    @property
    def expect(self) -> str:
        return self.cells[4]

    @property
    def collect(self) -> str:
        return self.cells[5]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="bridge jobs liveness sweep（唯讀 reporter——只標不殺）"
    )
    parser.add_argument(
        "--state-root",
        type=Path,
        nargs="+",
        default=None,
        metavar="DIR",
        help=(
            "delegate-bridge 狀態根（內含 jobs/*.jsonl 與 jobs.json）；可多值——"
            "bridge ledger 是 per-repo 的。預設＝ai-guide＋delegate-bridge 兩根"
        ),
    )
    parser.add_argument(
        "--journal", type=Path, default=DEFAULT_JOURNAL, help="liveness 六欄台帳（session-journal.md）"
    )
    parser.add_argument(
        "--sink-base",
        type=Path,
        default=DEFAULT_SINK_BASE,
        help="相對 sink 路徑的解析基準（台帳所屬 repo root）",
    )
    parser.add_argument(
        "--stale-hours",
        type=float,
        default=ZOMBIE_HOURS_DEFAULT,
        help="running 但最後活動超過此時數 → zombie-suspect（預設 6）",
    )
    parser.add_argument(
        "--window-hours",
        type=float,
        default=WINDOW_HOURS_DEFAULT,
        help="terminal-unclaimed／unledgered 的回報回看窗（預設 168；0＝不限）",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 輸出報告")
    return parser.parse_args()


def parse_micros(value: object) -> datetime | None:
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value / 1_000_000).astimezone()
    return None


def parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def scan_event_stream(text: str) -> tuple[str | None, datetime | None, str]:
    """掃單一 jsonl 事件流，回（terminal face, 最後活動, 判定依據）。

    涵蓋三種觀察到的 ledger 形態：
    - eventstream：每行 {"schema_version",...,"payload_type":"run.terminal.*","recorded_at":µs}
    - stream-events：每行 {"type":"turn.completed"|...}（無時間戳→mtime）
    - single-pretty-json：整檔單一 response 物件（completed 面）
    """
    stripped = text.strip()
    if not stripped:
        return None, None, "empty"

    face: str | None = None
    last_ts: datetime | None = None
    reason = ""
    per_line = False
    for line in stripped.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        per_line = True
        ts = parse_micros(obj.get("recorded_at"))
        if ts and (last_ts is None or ts > last_ts):
            last_ts = ts
        kind = obj.get("payload_type")
        if kind in TERMINAL_RUN_EVENTS and face is None:
            face = TERMINAL_RUN_EVENTS[kind]
            reason = f"事件流 {kind}"
        stream_type = obj.get("type")
        if stream_type in STREAM_TERMINAL_EVENTS and face is None:
            face = STREAM_TERMINAL_EVENTS[stream_type]
            reason = f"事件流 {stream_type}"
    if per_line:
        return face, last_ts, reason or "事件流無終態標記"

    # 非 per-line JSON：嘗試整檔單一 response 物件形態
    try:
        whole = json.loads(stripped)
    except json.JSONDecodeError:
        return None, None, "unparsable"
    if isinstance(whole, dict) and ("response" in whole or "projection" in whole):
        resp = whole.get("response")
        resp_len = len(resp) if isinstance(resp, str) else 0
        return "completed", None, f"response 檔（{resp_len} chars）"
    return None, None, "unrecognized-json"


def load_index(state_root: Path) -> dict[str, dict[str, object]]:
    index_path = state_root / "jobs.json"
    if not index_path.exists():
        return {}
    try:
        rows = json.loads(index_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[WARN] agent_liveness_sweep: jobs.json 無法解析（{exc}）——僅用事件流面", file=sys.stderr)
        return {}
    if not isinstance(rows, list):
        return {}
    return {str(row["id"]): row for row in rows if isinstance(row, dict) and "id" in row}


def load_job_faces(state_roots: list[Path]) -> dict[str, JobFace]:
    faces: dict[str, JobFace] = {}
    for state_root in state_roots:
        _load_root_faces(state_root, faces)
    # 索引時間戳兜底：無 jsonl 檔（spawn 失敗等）的 job 至少有索引終態寫入時間
    for face in faces.values():
        if face.last_activity is None and face.index_ts is not None:
            face.last_activity = face.index_ts
    return faces


def _load_root_faces(state_root: Path, faces: dict[str, JobFace]) -> None:
    for raw_id, row in load_index(state_root).items():
        faces[str(raw_id)] = JobFace(
            job_id=str(raw_id),
            root=state_root,
            index_status=row.get("status") if isinstance(row.get("status"), str) else None,
            index_ts=parse_iso(row.get("timestamp")),
            family=row.get("family") if isinstance(row.get("family"), str) else None,
            summary=row.get("summary") if isinstance(row.get("summary"), str) else None,
        )

    jobs_dir = state_root / "jobs"
    if jobs_dir.is_dir():
        for path in sorted(jobs_dir.glob("*.jsonl")):
            job_id = path.stem
            face = faces.get(job_id)
            if face is None:
                face = JobFace(job_id=job_id, root=state_root)
                faces[job_id] = face
            try:
                text = path.read_text(errors="replace")
            except OSError as exc:
                face.file_reason = f"read-fail: {exc}"
                continue
            file_face, file_ts, reason = scan_event_stream(text)
            face.file_status = file_face
            if not face.file_reason:
                face.file_reason = reason
            activity = file_ts or datetime.fromtimestamp(path.stat().st_mtime).astimezone()
            if activity and (face.last_activity is None or activity > face.last_activity):
                face.last_activity = activity
            if file_face == "completed" and face.response_len == 0:
                face.response_len = _response_len_hint(text)


def _response_len_hint(text: str) -> int:
    try:
        whole = json.loads(text.strip())
    except json.JSONDecodeError:
        return 0
    resp = whole.get("response") if isinstance(whole, dict) else None
    return len(resp) if isinstance(resp, str) else 0


def canonicalize_job_ids(tokens: set[str], faces: dict[str, JobFace]) -> set[str]:
    """台帳 id → bridge faces 正典 id。

    台帳可能寫短形（job-mu7xpicu）或全形（job-mu7px22a-b1ccwa）；以 faces 前綴對應。
    對不上任何 face 的 token（如路徑詞 job-lifecycle-fixes、已 prune 的歷史 id）丟棄。
    """
    resolved: set[str] = set()
    for token in tokens:
        if token in faces:
            resolved.add(token)
            continue
        matches = [full for full in faces if full.startswith(token + "-")]
        if len(matches) == 1:
            resolved.add(matches[0])
        elif len(matches) > 1:
            # 前綴撞多個 face——保守全收（等價於「台帳提及」語義，collect map 同理）
            resolved.update(matches)
    return resolved


def load_ledger_rows(journal: Path) -> list[LedgerRow]:
    """解析 session-journal 六欄台帳（id 為原始 token，正典化在 faces 載入後做）。"""
    rows: list[LedgerRow] = []
    if not journal.exists():
        return rows
    text = journal.read_text(errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 6:
            continue
        if set(cells[0]) <= {"-", ":", " "} or cells[0] == "id":
            continue  # 分隔列／表頭
        row = LedgerRow(cells=cells[:6], line_no=line_no)
        for cell in cells[:6]:
            row.job_ids.update(JOB_ID_RE.findall(cell))
        rows.append(row)
    return rows


def build_collection_map(rows: list[LedgerRow]) -> tuple[dict[str, LedgerRow], set[str]]:
    """回（已收 id→列, 全部登記於台帳的 id 集）。"""
    collected: dict[str, LedgerRow] = {}
    ledgered: set[str] = set()
    for row in rows:
        ledgered.update(row.job_ids)
        if row.collected:
            for job_id in row.job_ids:
                collected.setdefault(job_id, row)
    return collected, ledgered


def validate_sink(row: LedgerRow, face: JobFace, sink_base: Path) -> str:
    """sink 三步（存在→非空→錨點）的 v1 機驗；receipt-only 以 response 非空代驗。"""
    paths = [token for token in PATH_RE.findall(row.sink) if not token.startswith("http")]
    if not paths:
        # receipt-only：sink＝bridge response 本體——存在＝ledger 有該 job、非空＝response/summary 有內容
        if face.response_len > 0 or (face.summary or "").strip():
            return "receipt-only：response 非空 OK；錨點人工"
        return "receipt-only：FAIL——response/summary 皆空"

    verdicts: list[str] = []
    anchor_tokens = [token for token in ANCHOR_TOKEN_RE.findall(row.expect) if len(token) >= 4]
    for raw in paths:
        path = Path(raw) if raw.startswith("/") else sink_base / raw
        if not path.exists():
            verdicts.append(f"{raw} 缺")
            continue
        try:
            size = path.stat().st_size
        except OSError:
            verdicts.append(f"{raw} stat-fail")
            continue
        if size == 0:
            verdicts.append(f"{raw} 空")
            continue
        if anchor_tokens:
            try:
                content = path.read_text(errors="replace")[:200_000]
            except OSError:
                verdicts.append(f"{raw} read-fail")
                continue
            hits = [token for token in anchor_tokens if token in content]
            if hits:
                verdicts.append(f"{raw} OK（錨點 {hits[0]}）")
            else:
                verdicts.append(f"{raw} 非空但無錨點（{anchor_tokens[:3]}）")
        else:
            verdicts.append(f"{raw} 存在＋非空；錨點人工")
    return "；".join(verdicts)


def age_text(last_activity: datetime | None, now: datetime) -> str:
    if last_activity is None:
        return "活動時間未知"
    delta = now - last_activity
    hours = delta.total_seconds() / 3600
    if hours >= 48:
        return f"{hours / 24:.1f}d 前"
    if hours >= 1:
        return f"{hours:.1f}h 前"
    return f"{delta.total_seconds() / 60:.0f}m 前"


def classify(
    faces: dict[str, JobFace],
    collected: dict[str, LedgerRow],
    journal_ids: set[str],
    now: datetime,
    stale_hours: float,
    window_hours: float,
    sink_base: Path,
) -> dict[str, list[tuple[JobFace, str]]]:
    """五分類；journal_ids＝台帳（全文）提及的所有 bridge job id。"""
    groups: dict[str, list[tuple[JobFace, str]]] = {
        "collected": [],
        "terminal-unclaimed": [],
        "running-fresh": [],
        "zombie-suspect": [],
        "unledgered": [],
    }
    stale_delta = timedelta(hours=stale_hours)
    window_delta = timedelta(hours=window_hours) if window_hours > 0 else None

    for job_id in sorted(faces):
        face = faces[job_id]
        status = face.status
        row = collected.get(job_id)

        if row is not None:
            if status == RUNNING:
                note = f"drift：台帳標已收但 bridge 面 running（{face.file_reason}）"
            else:
                note = f"sink：{validate_sink(row, face, sink_base)}"
            groups["collected"].append((face, note))
            continue

        if status != RUNNING:
            in_window = window_delta is None or face.last_activity is None or (
                now - face.last_activity <= window_delta
            )
            if not in_window:
                continue
            if job_id in journal_ids:
                note = "台帳有登記、無 collect 紀錄——收回 terminal state＋sink 三步驗收"
                groups["terminal-unclaimed"].append((face, note))
            else:
                note = "台帳無登記——補六欄或確認無需回收"
                groups["unledgered"].append((face, note))
            continue

        # running：stale 判定
        is_stale = face.last_activity is None or (now - face.last_activity) > stale_delta
        if is_stale:
            reason = "活動時間未知" if face.last_activity is None else ""
            note = "對帳 carrier 台帳——只標不殺，人裁後處置"
            if reason:
                note = f"{reason}；{note}"
            groups["zombie-suspect"].append((face, note))
        else:
            groups["running-fresh"].append((face, "等 waiter exit 通知；下一檢查點再掃"))
    return groups


def fmt_ts(value: datetime | None) -> str:
    return value.strftime("%m-%d %H:%M") if value else "—"


def render_text(
    groups: dict[str, list[tuple[JobFace, str]]],
    counts: dict[str, int],
    state_roots: list[Path],
    args: argparse.Namespace,
    now: datetime,
) -> str:
    lines: list[str] = []
    multi = len(state_roots) > 1
    roots_txt = "＋".join(str(root) for root in state_roots)
    total = sum(counts.values())
    lines.append(
        f"liveness sweep（唯讀 reporter——只標不殺）@ {roots_txt} | reported={total}"
        f" | collected={counts['collected']} terminal-unclaimed={counts['terminal-unclaimed']}"
        f" running-fresh={counts['running-fresh']} zombie-suspect={counts['zombie-suspect']}"
        f" unledgered(≤{args.window_hours:.0f}h)={counts['unledgered']}"
        f" | stale>{args.stale_hours:.0f}h | {now.strftime('%Y-%m-%d %H:%M')}"
    )
    order = ["zombie-suspect", "terminal-unclaimed", "running-fresh", "unledgered", "collected"]
    for group in order:
        items = groups[group]
        lines.append(f"## {group} ({len(items)})")
        for face, note in items:
            carrier = face.family or "—"
            root_tag = f" @{face.root.parent.name}" if multi else ""
            lines.append(
                f"- {face.job_id} | {carrier} | {face.status}"
                f" [{face.status_face}]{root_tag} | 最後活動 {fmt_ts(face.last_activity)}"
                f"（{age_text(face.last_activity, now)}）| {note}"
            )
    lines.append("[ACTION] 處置分離：本工具不重派／不殺——依 AIR-135.7 契約由 Marshal 主座席裁決")
    return "\n".join(lines)


def render_json(
    groups: dict[str, list[tuple[JobFace, str]]],
    counts: dict[str, int],
    state_roots: list[Path],
    args: argparse.Namespace,
    now: datetime,
) -> str:
    payload = {
        "generated_at": now.isoformat(),
        "state_roots": [str(root) for root in state_roots],
        "journal": str(args.journal),
        "stale_hours": args.stale_hours,
        "window_hours": args.window_hours,
        "counts": counts,
        "read_only": True,
        "groups": {
            group: [
                {
                    "id": face.job_id,
                    "root": str(face.root),
                    "family": face.family,
                    "status": face.status,
                    "status_face": face.status_face,
                    "index_status": face.index_status,
                    "file_status": face.file_status,
                    "file_reason": face.file_reason,
                    "last_activity": face.last_activity.isoformat() if face.last_activity else None,
                    "note": note,
                }
                for face, note in groups[group]
            ]
            for group in groups
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    args = parse_args()
    if args.state_root:
        state_roots = list(args.state_root)
        missing = [root for root in state_roots if not root.is_dir()]
        if missing:
            print(
                f"[FAIL] agent_liveness_sweep: state root 不存在：{missing}",
                file=sys.stderr,
            )
            return 2
    else:
        state_roots = [root for root in DEFAULT_STATE_ROOTS if root.is_dir()]
        if not state_roots:
            print("[FAIL] agent_liveness_sweep: 無可用的預設 state root", file=sys.stderr)
            return 2

    faces = load_job_faces(state_roots)
    rows = load_ledger_rows(args.journal)
    for row in rows:
        row.job_ids = canonicalize_job_ids(row.job_ids, faces)
    mentioned = {job_id for row in rows for job_id in row.job_ids}
    mentioned.update(
        canonicalize_job_ids(set(JOB_ID_RE.findall(args.journal.read_text(errors="replace"))), faces)
    )
    collected, ledgered = build_collection_map(rows)
    now = datetime.now().astimezone()
    groups = classify(
        faces,
        collected,
        mentioned | ledgered,
        now,
        args.stale_hours,
        args.window_hours,
        args.sink_base,
    )
    counts = {group: len(items) for group, items in groups.items()}

    if args.json:
        print(render_json(groups, counts, state_roots, args, now))
    else:
        print(render_text(groups, counts, state_roots, args, now))
    print(
        f"[OK] agent_liveness_sweep: 台帳列 {len(rows)}（提及 job id {len(mentioned)}），"
        f"掃描 {len(faces)} jobs／{len(state_roots)} roots",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
