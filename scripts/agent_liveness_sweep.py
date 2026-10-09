#!/usr/bin/env python3
"""agent_liveness_sweep — bridge jobs liveness sweep（唯讀 reporter）.

契約源：AIR-135.7（AC#3 collection contract、AC#6② sweep＝唯讀 reporter——
只標不殺、只報轉移、偵測與處置分離）＋ rules/bridge-dispatch.md
「Dispatch⇄collection 配對」（terminal≠complete；sink 三步＝存在→非空→錨點）。

收編盤點（AIR-152）：`--enrollment-root <dir>` 掃該目錄**下一層** git repos，
以 guard 本體 load_profile（三態單一源）列「未收編」（無 marker）與
marker-malformed 清單——一行一 repo，只報存量不處置（V8 可見面腿）。

v1 資料源（bridge ledger 是 per-repo 的——`--state-root` 可多根，預設 ai-guide＋delegate-bridge）：
- 各根 jobs ledger：`<state-root>/jobs/*.jsonl`（事件流，三種形態）
  ＋ `<state-root>/jobs.json`（bridge 自家索引；dispatch 時以 running 寫入、
  終態更新——terminal face 權威；persisted status set 是 OPEN，未知值視 terminal）
- liveness 六欄台帳：session-journal.md 的六欄表（id/carrier/ts/sink/expect/collect）；
  台帳↔bridge 對接鍵＝job id（短形 id 以 faces 前綴正典化）

bounded 掃描（AIR-271）：`--max-files`／`--max-bytes` 限定 jsonl body 讀取預算——
jobs.json 索引恆全量讀（小檔、不受 bound）；jsonl 走語義選檔序（①index-running
最舊→最新先掃 zombie 候選 ②無 index 新→舊 ③index-terminal 新→舊——body I/O
最後），兩 cap 並存先達先停。截斷丟的是排序尾端——tier1 較新 running 候選與
tier2 較舊無 index 檔（兩者仍是 zombie 候選面）——防護＝覆蓋率如實聲明（首行
scan=N/M＋coverage 行 running=r/R＋unscanned 候選行 stat-only）——zombie=0 而
r<R 時不得當完整；read-fail 不計 scanned（read_failed>0＝coverage incomplete）。
無 bounded flag＝既有全量行為零變。

分類：collected / terminal-unclaimed / running-fresh / zombie-suspect / unledgered。
唯讀保證：除讀檔外無任何寫入／刪除／kill；exit 0（reporter 不以 exit 碼報 finding）。

spawn 僵屍掃描（AIR-296 第二層；`--zcode-scan`）
--------------------------------------------------------
ZCode 原生 subagent 域：掃 `<zcode-root>/agents/sess_*/agent_*/metadata.json`
全庫，套 GLM 90 樣本校準三簽章（型 A stillbirth＝running∧artifacts 缺/空
∧age>60min；中斷氣＝artifacts 最新檔凍結>180min；型 B silent-completion＝
running∧output.txt 存在即報）＋UNKNOWN（JSON 損壞 fail-loud 列報，禁自動
結案）。判定單一源＝scripts/zombie_core.py（本檔不重刻簽章）；輸出結構化
事件台帳（attempt_id+alert_type 去重鍵隨事件，sweeper 唯讀——去重由消費端
執行）。HARD_DEATH 不由本掃描產生（無 registry join——缺席非證據）；
session-local 的 waiter T5 為其唯一 producer。掛載＝夜 cron
（deploy/zombie-sweep.plist）＋/sitrep 按需。
"""

import argparse
import importlib.util
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent)
)  # scripts/ 非 package——同目錄 seam import（AIR-254.1 先例）

import zombie_core  # AIR-296：spawn 僵屍判定核心（三簽章／五級單一源）

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
class _JobFile:
    """jobs/*.jsonl 的 stat 面（body 未讀）——bounded 選檔序的排序單元。"""

    path: Path
    root: Path
    job_id: str
    size: int
    mtime: float
    tier: int  # 1=index-running（最舊→最新）2=無 index（新→舊）3=index-terminal（新→舊）


@dataclass
class ScanCoverage:
    """單次掃描的覆蓋率聲明（AIR-271）——只報未掃，不假裝完整。"""

    mode: str  # "bounded" | "full"
    discovered_files: int = 0
    content_scanned_files: int = 0
    bytes_scanned: int = 0
    running_candidates: int = 0  # tier1（index-running）＋tier2（無 index）＝潛在 running
    running_scanned: int = 0  # 候選中實際讀了 body 的數
    read_failed: int = 0  # body 讀取失敗（OSError）——>0 即 coverage incomplete
    per_root: dict[str, dict[str, int]] = field(default_factory=dict)  # root → {discovered, scanned}
    stop_reason: str | None = None  # "max-files" | "max-bytes" | None（掃完／full）
    unscanned_candidates: int = 0  # 未掃的 zombie 候選（index-running／無 index）
    unscanned_candidates_bytes: int = 0
    unscanned_terminal_excluded: int = 0  # index-terminal 安全排除（index face 權威，不需 body）
    unscanned_terminal_excluded_bytes: int = 0

    @property
    def skipped(self) -> int:
        return self.discovered_files - self.content_scanned_files

    @property
    def unscanned_bytes(self) -> int:
        return self.unscanned_candidates_bytes + self.unscanned_terminal_excluded_bytes


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


def _positive_int(value: str) -> int:
    num = int(value)
    if not (num > 0):
        raise argparse.ArgumentTypeError(f"須為正整數：{value}")
    return num


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
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
    parser.add_argument(
        "--max-files",
        type=_positive_int,
        default=None,
        metavar="N",
        help=(
            "bounded 掃描（AIR-271）：最多讀 N 個 jsonl body——選檔序＝index-running"
            " 最舊先（zombie 候選優先）；與 --max-bytes 並存＝先達先停"
        ),
    )
    parser.add_argument(
        "--max-bytes",
        type=_positive_int,
        default=None,
        metavar="B",
        help="bounded 掃描（AIR-271）：body 讀取累計 bytes 上限；先達先停",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 輸出報告")
    parser.add_argument(
        "--enrollment-root",
        type=Path,
        default=None,
        metavar="DIR",
        help="收編盤點根（AIR-152）：掃下一層 git repos，列未收編／marker 壞清單"
        "（唯讀可見面）",
    )
    parser.add_argument(
        "--zcode-scan",
        action="store_true",
        help=(
            "spawn 僵屍掃描（AIR-296 第二層）：掃 ZCode 原生 subagent metadata"
            "全庫，套 GLM 90 樣本校準三簽章（型 A stillbirth／中斷氣／型 B "
            "silent-completion）＋UNKNOWN fail-loud——唯讀、事件台帳帶 "
            "attempt_id+alert_type 去重鍵；判定單一源＝scripts/zombie_core.py"
        ),
    )
    parser.add_argument(
        "--zcode-root",
        type=Path,
        default=Path.home() / ".zcode" / "cli",
        metavar="DIR",
        help="--zcode-scan 的 ZCode CLI 根（內含 agents/ 與 artifacts/；測試注入用）",
    )
    parser.add_argument(
        "--stillbirth-min",
        type=float,
        default=zombie_core.STILLBIRTH_AGE_MIN_DEFAULT,
        metavar="MIN",
        help=(
            "型 A 閾值：running∧artifacts 缺/空∧age 超此分鐘→START_MISSING"
            "（預設 60＝GLM 校準＞首檔 max 48min）"
        ),
    )
    parser.add_argument(
        "--interrupted-min",
        type=float,
        default=zombie_core.INTERRUPTED_FROZEN_MIN_DEFAULT,
        metavar="MIN",
        help=(
            "中斷氣閾值：artifacts 最新檔凍結超此分鐘→SILENCE"
            "（預設 180＝≈1.7×間距 max 106min）"
        ),
    )
    return parser.parse_args(argv)


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


def _read_job_text(path: Path) -> str:
    """body 讀取 seam（AIR-271）——測試經 monkeypatch 記錄實際 body reads。"""
    return path.read_text(errors="replace")


def load_job_faces(
    state_roots: list[Path],
    max_files: int | None = None,
    max_bytes: int | None = None,
) -> tuple[dict[str, JobFace], ScanCoverage]:
    """兩面載入：jobs.json 索引恆全量讀（小檔、不受 bound）；jsonl body 依
    bounded 預算走選檔序（無 cap＝全量，行為不變）。回（faces, 覆蓋率聲明）。"""
    faces: dict[str, JobFace] = {}
    coverage = ScanCoverage(
        mode="bounded" if (max_files is not None or max_bytes is not None) else "full"
    )
    per_root_files: list[list[_JobFile]] = []
    for state_root in state_roots:
        _load_root_index(state_root, faces)
        files = _discover_job_files(state_root, faces)
        per_root_files.append(files)
        coverage.per_root[str(state_root)] = {"discovered": len(files), "scanned": 0}
        coverage.discovered_files += len(files)
        coverage.running_candidates += sum(1 for jf in files if jf.tier in (1, 2))

    ordered = _priority_order(per_root_files)
    for jf in ordered:
        if max_files is not None and coverage.content_scanned_files >= max_files:
            coverage.stop_reason = "max-files"
            break
        if max_bytes is not None and coverage.bytes_scanned + jf.size > max_bytes:
            coverage.stop_reason = "max-bytes"
            break
        if not _scan_job_file(faces, jf):
            # read-fail：不是 content scan——不計 scanned／bytes／running_scanned，
            # 只計獨立 read_failed（coverage 語義隨之 incomplete）
            coverage.read_failed += 1
            continue
        coverage.content_scanned_files += 1
        coverage.bytes_scanned += jf.size
        coverage.per_root[str(jf.root)]["scanned"] += 1
        if jf.tier in (1, 2):
            coverage.running_scanned += 1

    # 未掃部分按 index face 分流：terminal 安全排除；running／無 index＝zombie 候選
    for jf in ordered[coverage.content_scanned_files :]:
        if jf.tier == 3:
            coverage.unscanned_terminal_excluded += 1
            coverage.unscanned_terminal_excluded_bytes += jf.size
        else:
            coverage.unscanned_candidates += 1
            coverage.unscanned_candidates_bytes += jf.size

    # 索引時間戳兜底：無 jsonl 檔（spawn 失敗等）的 job 至少有索引終態寫入時間
    for face in faces.values():
        if face.last_activity is None and face.index_ts is not None:
            face.last_activity = face.index_ts
    return faces, coverage


def _load_root_index(state_root: Path, faces: dict[str, JobFace]) -> None:
    for raw_id, row in load_index(state_root).items():
        faces[str(raw_id)] = JobFace(
            job_id=str(raw_id),
            root=state_root,
            index_status=row.get("status") if isinstance(row.get("status"), str) else None,
            index_ts=parse_iso(row.get("timestamp")),
            family=row.get("family") if isinstance(row.get("family"), str) else None,
            summary=row.get("summary") if isinstance(row.get("summary"), str) else None,
        )


def _discover_job_files(state_root: Path, faces: dict[str, JobFace]) -> list[_JobFile]:
    """stat 面 discovery（千檔毫秒級，只 stat 不讀 body）＋依 index face 分 tier。"""
    jobs_dir = state_root / "jobs"
    if not jobs_dir.is_dir():
        return []
    files: list[_JobFile] = []
    for path in sorted(jobs_dir.glob("*.jsonl")):
        face = faces.get(path.stem)
        index_status = face.index_status if face is not None else None
        if index_status is None:
            tier = 2  # 無 index／index 無 status——face 未知，視為潛在 running 候選
        elif index_status == RUNNING:
            tier = 1
        else:
            tier = 3
        try:
            stat = path.stat()
            size, mtime = stat.st_size, stat.st_mtime
        except OSError:
            size, mtime = 0, 0.0  # read 時照原路徑標 read-fail
        files.append(
            _JobFile(
                path=path, root=state_root, job_id=path.stem, size=size, mtime=mtime, tier=tier
            )
        )
    return files


def _priority_order(per_root_files: list[list[_JobFile]]) -> list[_JobFile]:
    """選檔序（替換檔名序）：①index-running 最舊→最新（先抓 zombie 候選）
    ②無 index 新→舊 ③index-terminal 新→舊（body I/O 最後）；各 tier 內雙 root
    round-robin。截斷丟的是排序尾端——tier1 較新 running 候選與 tier2 較舊檔
    （皆屬 zombie 候選面）——防護＝coverage 的 running=r/R＋unscanned 候選行；
    tier 3 被截斷屬安全排除（index face 權威）。"""
    ordered: list[_JobFile] = []
    for tier in (1, 2, 3):
        buckets: list[list[_JobFile]] = []
        for files in per_root_files:
            subset = [jf for jf in files if jf.tier == tier]
            subset.sort(key=lambda jf: (jf.mtime, jf.path.name), reverse=(tier != 1))
            if subset:
                buckets.append(subset)
        iterators: list[Iterator[_JobFile]] = [iter(bucket) for bucket in buckets]
        while iterators:
            exhausted: list[Iterator[_JobFile]] = []
            for it in iterators:
                item = next(it, None)
                if item is None:
                    exhausted.append(it)
                else:
                    ordered.append(item)
            for it in exhausted:
                iterators.remove(it)
    return ordered


def _scan_job_file(faces: dict[str, JobFace], jf: _JobFile) -> bool:
    """讀單一 jsonl body 並合成 face（原有逐檔語義，分類不變）。

    回傳 body 是否成功讀取——read-fail 不是 content scan：caller 不得把
    失敗檔計入 coverage 的 scanned／running_scanned，否則 read-fail 會
    偽造完整 coverage（F1，AIR-271 複核）。
    """
    face = faces.get(jf.job_id)
    if face is None:
        face = JobFace(job_id=jf.job_id, root=jf.root)
        faces[jf.job_id] = face
    try:
        text = _read_job_text(jf.path)
    except OSError as exc:
        face.file_reason = f"read-fail: {exc}"
        return False
    file_face, file_ts, reason = scan_event_stream(text)
    face.file_status = file_face
    if not face.file_reason:
        face.file_reason = reason
    activity = file_ts or datetime.fromtimestamp(jf.mtime).astimezone()
    if activity and (face.last_activity is None or activity > face.last_activity):
        face.last_activity = activity
    if file_face == "completed" and face.response_len == 0:
        face.response_len = _response_len_hint(text)
    return True


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


def _guard_schema():
    """載 guard 本體——load_profile 三態判定單一源（收編盤點與執行面同 schema）。"""
    guard = (
        Path(__file__).resolve().parents[1] / "hooks" / "marshal_admission_guard.py"
    )
    spec = importlib.util.spec_from_file_location("_marshal_guard_schema", guard)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scan_enrollment(root: Path) -> dict:
    """收編盤點（AIR-152）：root 下一層 git repos，唯讀、只報存量不處置。"""
    guard = _guard_schema()
    repos = sorted(
        child
        for child in root.iterdir()
        if child.is_dir() and (child / ".git").exists()
    )
    enrolled: list[str] = []
    unenrolled: list[str] = []
    malformed: list[str] = []
    for repo in repos:
        # marker 權威面＝canonical PRIMARY（guard runtime 同錨——codex 152-C1 同源：
        # linked WT 上 worktree 根的 marker 不被 guard 讀，盤點錨錯＝假收編）
        primary = repo
        try:
            common = guard._git_common_dir(str(repo))
            primary = Path(common).parent
        except Exception:
            pass  # 非 standard 佈局退 repo 根（盤點唯讀——判讀誤差可容忍）
        status, _profile = guard.load_profile(str(primary))
        if status == "ok":
            enrolled.append(str(repo))
        elif status == "malformed":
            malformed.append(str(repo))
        else:
            unenrolled.append(str(repo))
    return {
        "root": str(root),
        "scanned": len(repos),
        "enrolled": enrolled,
        "unenrolled": unenrolled,
        "malformed": malformed,
    }


def render_enrollment(scan: dict) -> list[str]:
    lines = [
        "## enrollment (%d scanned | enrolled=%d unenrolled=%d marker-malformed=%d)"
        % (
            scan["scanned"],
            len(scan["enrolled"]),
            len(scan["unenrolled"]),
            len(scan["malformed"]),
        )
    ]
    for repo in scan["unenrolled"]:
        lines.append(
            f"- {repo} | 未收編（無 .agents/marshal-governance.json）——"
            f"收編：uv run python scripts/enroll_repo.py --repo {repo}"
        )
    for repo in scan["malformed"]:
        lines.append(f"- {repo} | marker-malformed——修復或刪除該 marker")
    return lines


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


def _mib(num_bytes: int) -> str:
    return f"{num_bytes / 1048576:.1f}"


def _render_coverage_lines(coverage: ScanCoverage) -> list[str]:
    """coverage 行＋unscanned 行（bounded 時；全部 stat 面數字，不讀內容）。"""
    stop_txt = coverage.stop_reason or "none"
    per_root_txt = ", ".join(
        f"{Path(root).parent.name} {counts['scanned']}/{counts['discovered']}"
        for root, counts in coverage.per_root.items()
    )
    read_fail_txt = (
        f" | read-failed={coverage.read_failed}" if coverage.read_failed else ""
    )
    lines = [
        f"coverage: running={coverage.running_scanned}/{coverage.running_candidates}"
        f" | roots={per_root_txt} | skipped={coverage.skipped} | stop={stop_txt}"
        f"{read_fail_txt}"
    ]
    if coverage.skipped:
        lines.append(
            f"unscanned: {coverage.skipped} files / {_mib(coverage.unscanned_bytes)} MiB"
            f" | 候選（running/無 index）={coverage.unscanned_candidates} files /"
            f" {_mib(coverage.unscanned_candidates_bytes)} MiB"
            f" | index-terminal 安全排除={coverage.unscanned_terminal_excluded} files /"
            f" {_mib(coverage.unscanned_terminal_excluded_bytes)} MiB"
            f" | reason=stop={stop_txt}{read_fail_txt}"
        )
    return lines


def spawn_zombie_counts(zcode: dict) -> dict:
    """事件層級計數（五級——sweeper 掃描面產生四種；HARD_DEATH 歸 waiter T5）."""
    counts = {
        zombie_core.ALERT_START_MISSING: 0,
        zombie_core.ALERT_SILENCE: 0,
        zombie_core.ALERT_COMPLETION_SUSPECTED: 0,
        zombie_core.ALERT_HARD_DEATH: 0,
        zombie_core.ALERT_UNKNOWN: 0,
    }
    for event in zcode["events"]:
        counts[event.alert_type] = counts.get(event.alert_type, 0) + 1
    return counts


def render_spawn_zombies(zcode: dict, counts: dict, now: datetime) -> list[str]:
    """spawn-zombies 節（唯讀事件台帳——去重鍵隨事件，消費端去重；禁自動結案：
    UNKNOWN＝fail-loud 列報，處置恆人裁 AIR-135.7）."""
    cov = zcode["coverage"]
    lines = [f"## spawn-zombies ({len(zcode['events'])})"]
    for event in zcode["events"]:
        ev = event.evidence
        newest_txt = (
            f"{ev['newestArtifactAgeMin']}min 前"
            if ev.get("newestArtifactAgeMin") is not None
            else "無心跳檔"
        )
        lines.append(
            f"- {event.agent_id} | {event.alert_type} | dedup={event.dedup_key}"
            f" | age={ev.get('ageMin')}min | artifacts={ev.get('artifactsFiles')}"
            f" | 最新活動 {newest_txt}"
            f" | output={ev.get('outputPath') or '—'}"
            f" | {event.parent_session_id} | {event.cwd or '—'}"
            f" | {(event.description or '')[:60]}"
        )
    lines.append(
        f"coverage: discovered={cov['discovered']} running={cov['running']}"
        f" terminal={cov['terminal']} terminal-other={cov['terminal_other']}"
        f" running-fresh={cov['running_fresh']} clock-anomaly={cov['clock_anomaly']}"
        f" | 閾值 START_MISSING>{zcode['thresholds']['stillbirth_min']:.0f}min"
        f" SILENCE>{zcode['thresholds']['interrupted_min']:.0f}min"
        f" | 掃描 {now.strftime('%Y-%m-%d %H:%M')}"
    )
    lines.append(
        "[ACTION] spawn 僵屍：只報不殺——處置（TaskStop/重派/寫 completed）恆人裁"
        "（AIR-135.7）；存量清掃以本節為輸入清單"
    )
    return lines


def render_text(
    groups: dict[str, list[tuple[JobFace, str]]],
    counts: dict[str, int],
    state_roots: list[Path],
    args: argparse.Namespace,
    now: datetime,
    enrollment: dict | None = None,
    coverage: ScanCoverage | None = None,
    zcode: dict | None = None,
) -> str:
    lines: list[str] = []
    if coverage is not None and coverage.mode == "bounded":
        caps = []
        if args.max_files is not None:
            caps.append(f"max-files={args.max_files}")
        if args.max_bytes is not None:
            caps.append(f"max-bytes={args.max_bytes}")
        lines.append(
            f"scan={coverage.content_scanned_files}/{coverage.discovered_files}"
            f" files (bounded: {', '.join(caps)})"
        )
    multi = len(state_roots) > 1
    roots_txt = "＋".join(str(root) for root in state_roots)
    total = sum(counts.values())
    zc_txt = ""
    if zcode is not None:
        zc = spawn_zombie_counts(zcode)
        zc_txt = (
            f" | spawn-zombies={len(zcode['events'])}"
            f"({zombie_core.ALERT_START_MISSING}={zc[zombie_core.ALERT_START_MISSING]}"
            f" {zombie_core.ALERT_SILENCE}={zc[zombie_core.ALERT_SILENCE]}"
            f" {zombie_core.ALERT_COMPLETION_SUSPECTED}={zc[zombie_core.ALERT_COMPLETION_SUSPECTED]}"
            f" {zombie_core.ALERT_UNKNOWN}={zc[zombie_core.ALERT_UNKNOWN]})"
        )
    lines.append(
        f"liveness sweep（唯讀 reporter——只標不殺）@ {roots_txt} | reported={total}"
        f" | collected={counts['collected']} terminal-unclaimed={counts['terminal-unclaimed']}"
        f" running-fresh={counts['running-fresh']} zombie-suspect={counts['zombie-suspect']}"
        f" unledgered(≤{args.window_hours:.0f}h)={counts['unledgered']}"
        f"{zc_txt}"
        f" | stale>{args.stale_hours:.0f}h | {now.strftime('%Y-%m-%d %H:%M')}"
    )
    if zcode is not None:
        lines.extend(render_spawn_zombies(zcode, spawn_zombie_counts(zcode), now))
    if coverage is not None and coverage.mode == "bounded":
        lines.extend(_render_coverage_lines(coverage))
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
    if enrollment is not None:
        lines.extend(render_enrollment(enrollment))
    lines.append("[ACTION] 處置分離：本工具不重派／不殺——依 AIR-135.7 契約由 Marshal 主座席裁決")
    return "\n".join(lines)


def render_json(
    groups: dict[str, list[tuple[JobFace, str]]],
    counts: dict[str, int],
    state_roots: list[Path],
    args: argparse.Namespace,
    now: datetime,
    enrollment: dict | None = None,
    coverage: ScanCoverage | None = None,
    zcode: dict | None = None,
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
    if zcode is not None:
        payload["spawn_zombies"] = {
            "zcode_root": str(args.zcode_root),
            "counts": spawn_zombie_counts(zcode),
            "events": [event.to_dict() for event in zcode["events"]],
            "coverage": zcode["coverage"],
            "thresholds": zcode["thresholds"],
            "read_only": True,
        }
    if coverage is not None and coverage.mode == "bounded":
        payload["coverage"] = {
            "mode": coverage.mode,
            "discovered_files": coverage.discovered_files,
            "content_scanned_files": coverage.content_scanned_files,
            "bytes": coverage.bytes_scanned,
            "running_candidates": coverage.running_candidates,
            "running_scanned": coverage.running_scanned,
            "read_failed": coverage.read_failed,
            "unscanned_by_face": {
                "candidates": coverage.unscanned_candidates,
                "candidates_bytes": coverage.unscanned_candidates_bytes,
                "terminal_excluded": coverage.unscanned_terminal_excluded,
                "terminal_excluded_bytes": coverage.unscanned_terminal_excluded_bytes,
            },
            "per_root": coverage.per_root,
            "stop_reason": coverage.stop_reason,
        }
    if enrollment is not None:
        payload["enrollment"] = enrollment
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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

    faces, coverage = load_job_faces(
        state_roots, max_files=args.max_files, max_bytes=args.max_bytes
    )
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

    enrollment = None
    if args.enrollment_root is not None:
        if not args.enrollment_root.is_dir():
            print(
                f"[FAIL] agent_liveness_sweep: enrollment root 不存在："
                f"{args.enrollment_root}",
                file=sys.stderr,
            )
            return 2
        enrollment = scan_enrollment(args.enrollment_root)

    zcode = None
    if args.zcode_scan:
        # AIR-296 第二層：ZCode 原生 subagent 全庫掃描（唯讀；判定單一源
        # ＝zombie_core）。fail-loud 與 state-root 同款——根不存在 exit 2
        if not args.zcode_root.is_dir():
            print(
                f"[FAIL] agent_liveness_sweep: zcode root 不存在：{args.zcode_root}",
                file=sys.stderr,
            )
            return 2
        # 資料源完整性（judge F2）：缺 agents/／artifacts/ 任一源不得靜默——
        # 缺 agents/＝glob 空集合 discovered=0 exit 0（假陰性）；缺
        # artifacts/＝face_snapshot 全空使 running 母體集體誤判
        # START_MISSING（誤報）。與根同款 exit 2：缺失必須可見，掃描擋在分類前
        for sub in ("agents", "artifacts"):
            sub_dir = args.zcode_root / sub
            if not sub_dir.is_dir():
                print(
                    f"[FAIL] agent_liveness_sweep: zcode root 缺 {sub}/："
                    f"{sub_dir}",
                    file=sys.stderr,
                )
                return 2
        zcode = zombie_core.scan_zcode_agents(
            args.zcode_root / "agents",
            args.zcode_root / "artifacts",
            now,
            stillbirth_age_min=args.stillbirth_min,
            interrupted_frozen_min=args.interrupted_min,
        )
        zcode["thresholds"] = {
            "stillbirth_min": args.stillbirth_min,
            "interrupted_min": args.interrupted_min,
        }

    if args.json:
        print(render_json(groups, counts, state_roots, args, now, enrollment, coverage, zcode))
    else:
        print(render_text(groups, counts, state_roots, args, now, enrollment, coverage, zcode))
    scanned_note = (
        f"（body {coverage.content_scanned_files}/{coverage.discovered_files}）"
        if coverage.mode == "bounded"
        else ""
    )
    print(
        f"[OK] agent_liveness_sweep: 台帳列 {len(rows)}（提及 job id {len(mentioned)}），"
        f"掃描 {len(faces)} jobs／{len(state_roots)} roots{scanned_note}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
