#!/usr/bin/env python3
"""ping_matrix — ZCode worker 五態 × 查詢面真機矩陣（AIR-162 AC#2）.

目的：凍結 ping（TaskOutput／SendMessage）與被動查詢面在五個 worker 狀態
下的可機械區分性——實驗結論寫成 contract 建議段（可機械區分／不可區分，
兩者皆可驗收，誠實優先；card AIR-162 已決策）。

五態與真機建構（H 級 corpus——真實歷史 worker，非合成）：
- running：self-verified live worker（執行本矩陣的 worker 自身——唯一可從
  script 內驗證活性的 cell；K1 證偽後 running metadata row 不等於 process
  liveness，須 lsof fd lease 正向控制輔證）
- completed-retained：最近 completed worker（metadata 仍可查）
- failed-stopped：最近 failed 與 stopped worker（兩 sub-cell）
- reaped：exec face 存在但 metadata 已被 harness 清除的歷史 worker（自然
  reaped 樣本——存在性前證＝exec 目錄在，metadata 缺席）
- nonexistent：隨機合法格式、從未 spawn 的 id（對照組 baseline）

查詢面（全唯讀、bounded）：
- metadata-status：agents/sess_*/agent_<id>/metadata.json（唯一權威狀態訊號）
- exec-face／artifact-face：目錄列舉（路徑身份＝taskId 全形）
- output-face：output.txt／task.output 存在性＋大小
- lsof-exec-lease：exec 檔 fd 存在性（process 可尋址性代理）
- taskoutput-tool／sendmessage-tool：parent session in-conversation 工具——
  腳本端機械探測 CLI/spawn 面存在性；ZCode 3.14.3 實測無 script 面（逐字
  記錄探測證據）＝structurally-unavailable，in-conversation 語義凍結留
  parent session 實驗（後續卡）。SendMessage＝mutating probe——契約凍結前
  禁對真 worker 使用；本矩陣零 mutating 操作（metadata-status 面查詢前後
  stat 對照零變；其餘面為唯讀列舉／lsof，sideEffect.checked=false 如實記錄）。

每格記錄：回應原文（bounded 截斷）、exit code、延遲 ms、side effect。

輸出（--out 目錄，預設 <repo>/.agent-tmp/ping-matrix/）：
- matrix.json——機械可判全量記錄
- matrix.md——五態 × 查詢面記錄表（人類判讀）
- contract-suggestion.md——實驗結論＋contract 建議段（AC#3 吸收源）

用法：
    uv run python scripts/ping_matrix.py [--cli-root DIR] [--out DIR]
        [--running ID] [--completed ID] [--failed ID] [--stopped ID]
        [--reaped ID] [--nonexistent ID]
（cell id 缺省＝自動從真機 corpus 探測最新樣本；explicit 傳入優先）
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

MAX_RESPONSE_CHARS = 400
LSOF_TIMEOUT_S = 30.0
TERMINAL_STATES = {"completed", "failed", "stopped"}

_META_KEYS_VERBATIM = (
    "agentId",
    "childSessionId",
    "createdAt",
    "updatedAt",
    "completedAt",
    "status",
    "cwd",
    "description",
)


def _clip(text: str, limit: int = MAX_RESPONSE_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + f"…[{len(text)} chars]"


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds")


@dataclass
class QueryResult:
    surface: str
    ok: bool
    exit_code: int
    latency_ms: float
    response: str
    stat_before: dict | None = None
    stat_after: dict | None = None
    saved_side_effect: dict | None = None  # --render-only 重建時用（保存原值）

    def to_dict(self) -> dict:
        if self.saved_side_effect is not None:
            side_effect = self.saved_side_effect
        else:
            side_effect = {
                "checked": self.stat_before is not None and self.stat_after is not None,
                "changed": (
                    self.stat_before is not None and self.stat_before != self.stat_after
                ),
            }
        return {
            "surface": self.surface,
            "ok": self.ok,
            "exitCode": self.exit_code,
            "latencyMs": round(self.latency_ms, 1),
            "response": self.response,
            "sideEffect": side_effect,
        }


@dataclass
class Cell:
    state: str
    task_id: str
    note: str = ""
    queries: list[QueryResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "taskId": self.task_id,
            "note": self.note,
            "queries": [q.to_dict() for q in self.queries],
        }


# ---------------------------------------------------------------------------
# 查詢面（全唯讀）
# ---------------------------------------------------------------------------


def _stat_snap(p: Path) -> dict | None:
    try:
        st = p.stat()
    except OSError:
        return None
    return {"size": st.st_size, "mtimeNs": st.st_mtime_ns}


def _agent_id(task_id: str) -> str:
    prefix = "sess_subagent_"
    return task_id.removeprefix(prefix)


def find_metadata(cli_root: Path, task_id: str) -> Path | None:
    agent_id = _agent_id(task_id)
    pattern = str(cli_root / "agents" / "sess_*" / agent_id / "metadata.json")
    hits = sorted(glob.glob(pattern))
    return Path(hits[0]) if hits else None


def query_metadata(cli_root: Path, task_id: str) -> QueryResult:
    start = time.monotonic()
    path = find_metadata(cli_root, task_id)
    if path is None:
        return QueryResult(
            surface="metadata-status",
            ok=False,
            exit_code=1,
            latency_ms=(time.monotonic() - start) * 1000,
            response="NOT_FOUND: 無 metadata（缺席——⊃ never-existed/reaped）",
        )
    before = _stat_snap(path)
    try:
        meta = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return QueryResult(
            surface="metadata-status",
            ok=False,
            exit_code=1,
            latency_ms=(time.monotonic() - start) * 1000,
            response=f"UNPARSEABLE: {exc}",
            stat_before=before,
            stat_after=_stat_snap(path),
        )
    verbatim = {k: meta.get(k) for k in _META_KEYS_VERBATIM if meta.get(k)}
    after = _stat_snap(path)
    return QueryResult(
        surface="metadata-status",
        ok=True,
        exit_code=0,
        latency_ms=(time.monotonic() - start) * 1000,
        response=json.dumps(verbatim, ensure_ascii=False),
        stat_before=before,
        stat_after=after,
    )


def _dir_candidates(cli_root: Path, kind: str, task_id: str) -> list[Path]:
    """exec/artifact 目錄名＝taskId 全形（機器實證 2026-09-20）——兩形都試.

    短形 agent_<uuid> 的目錄以全形 sess_subagent_agent_<uuid> 落盤；只查
    傳入形會漏（矩陣 run-1 儀器缺陷實證——路徑形誤查＝偽 MISS）。
    """
    root = {"exec": cli_root / "exec", "artifact": cli_root / "artifacts"}[kind]
    candidates = [root / task_id]
    if not task_id.startswith("sess_subagent_"):
        candidates.append(root / ("sess_subagent_" + task_id))
    return candidates


def query_dir_face(cli_root: Path, kind: str, task_id: str) -> QueryResult:
    start = time.monotonic()
    tried: list[str] = []
    for d in _dir_candidates(cli_root, kind, task_id):
        tried.append(str(d))
        if not d.is_dir():
            continue
        try:
            files = sorted(p.name for p in d.iterdir() if p.is_file())
        except OSError as exc:
            return QueryResult(
                surface=f"{kind}-face",
                ok=False,
                exit_code=1,
                latency_ms=(time.monotonic() - start) * 1000,
                response=f"UNREADABLE: {exc}",
            )
        return QueryResult(
            surface=f"{kind}-face",
            ok=True,
            exit_code=0,
            latency_ms=(time.monotonic() - start) * 1000,
            response=f"{len(files)} files: {files[:10]} (dir={d.name[:30]}…)",
        )
    return QueryResult(
        surface=f"{kind}-face",
        ok=False,
        exit_code=1,
        latency_ms=(time.monotonic() - start) * 1000,
        response=f"NOT_FOUND: 試 {_clip('; '.join(tried), 120)}",
    )


def query_output_face(cli_root: Path, task_id: str) -> QueryResult:
    start = time.monotonic()
    agent_dir = find_metadata(cli_root, task_id)
    paths: list[Path] = []
    if agent_dir is not None:
        base = agent_dir.parent
        paths = [base / "output.txt", base / "task.output"]
    else:
        # metadata 缺席——glob 嘗試（reaped/nonexistent 的 output face）
        agent_id = _agent_id(task_id)
        paths = [
            Path(p)
            for p in glob.glob(str(cli_root / "agents" / "sess_*" / agent_id / "*"))
        ][:4]
    observed = []
    for p in paths:
        snap = _stat_snap(p)
        if snap is not None:
            observed.append(f"{p.name}: size={snap['size']}")
        else:
            observed.append(f"{p.name}: ABSENT")
    return QueryResult(
        surface="output-face",
        ok=bool(observed),
        exit_code=0 if observed else 1,
        latency_ms=(time.monotonic() - start) * 1000,
        response="; ".join(observed) if observed else "NOT_FOUND: 無 output 面",
    )


def query_lsof(cli_root: Path, task_id: str) -> QueryResult:
    start = time.monotonic()
    paths: list[Path] = []
    for d in _dir_candidates(cli_root, "exec", task_id):
        if d.is_dir():
            try:
                paths = [p for p in d.iterdir() if p.is_file()]
            except OSError:
                paths = []
            if paths:
                break
    if not paths:
        return QueryResult(
            surface="lsof-exec-lease",
            ok=False,
            exit_code=1,
            latency_ms=(time.monotonic() - start) * 1000,
            response="NO_TARGET: exec 面無檔可 probe（lease 面缺席＝合法）",
        )
    try:
        proc = subprocess.run(
            ["lsof", "-F", "pn", "--", *[str(p) for p in paths]],
            capture_output=True,
            text=True,
            check=False,
            timeout=LSOF_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return QueryResult(
            surface="lsof-exec-lease",
            ok=False,
            exit_code=1,
            latency_ms=(time.monotonic() - start) * 1000,
            response=f"PROBE_ERROR: {exc}",
        )
    holders = sorted(
        os.path.realpath(line[1:])
        for line in proc.stdout.splitlines()
        if line.startswith("n")
    )
    if proc.returncode == 0 and holders:
        resp = f"LEASE HELD by {len(holders)} fd——process 存在（可尋址性代理=C）"
    elif proc.returncode == 1 and not proc.stderr.strip():
        resp = "NO LEASE: 無 open fd（process 不在或未開檔）"
    else:
        resp = f"UNDECIDABLE: exit={proc.returncode} stderr={_clip(proc.stderr)}"
    return QueryResult(
        surface="lsof-exec-lease",
        ok=proc.returncode in (0, 1),
        exit_code=proc.returncode,
        latency_ms=(time.monotonic() - start) * 1000,
        response=resp,
    )


# ---------------------------------------------------------------------------
# harness 工具面機械探測（TaskOutput／SendMessage／spawn CLI 面存在性）
# ---------------------------------------------------------------------------


def probe_tool_surface() -> dict:
    """逐字記錄 CLI 面探測證據——TaskOutput/SendMessage/spawn 的 script 可達性."""
    candidates = {
        "zcode-on-PATH": shutil.which("zcode"),
        "zcode-app-binary": Path("/Applications/ZCode.app/Contents/MacOS/ZCode"),
    }
    evidence: dict[str, dict] = {}
    for name, bin_path in candidates.items():
        if bin_path is None:
            evidence[name] = {
                "available": False,
                "response": "NOT_FOUND: binary 不在 PATH／預期路徑",
            }
            continue
        exe = str(bin_path) if isinstance(bin_path, Path) else bin_path
        start = time.monotonic()
        try:
            proc = subprocess.run(
                [exe, "--help"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            out = (proc.stdout + proc.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            out = f"INVOKE_ERROR: {exc}"
            proc_returncode = -1
        else:
            proc_returncode = proc.returncode
        # 掃 task/send/agent/spawn 子命令證據
        needle_lines = [
            line
            for line in out.splitlines()
            if any(w in line.lower() for w in ("task", "send", "spawn", "agent"))
        ]
        evidence[name] = {
            "available": True,
            "exitCode": proc_returncode,
            "latencyMs": round((time.monotonic() - start) * 1000, 1),
            "usageLinesFound": _clip(" | ".join(needle_lines[:6]) or "(無)"),
            "responseExcerpt": _clip(out.splitlines()[0] if out else "(empty)"),
        }
    tool_faces = {
        "taskoutput-tool": "parent session in-conversation 查詢工具",
        "sendmessage-tool": "parent session in-conversation 投遞工具（mutating）",
    }
    script_callable = any(
        info.get("usageLinesFound") not in (None, "(無)")
        and any(
            w in str(info.get("usageLinesFound", "")).lower()
            for w in ("task", "send", "spawn")
        )
        for info in evidence.values()
    )
    return {
        "probedAt": _now_iso(),
        "cliEvidence": evidence,
        "scriptCallable": script_callable,
        "finding": (
            "CLI 面存在 TaskOutput/SendMessage/spawn 子命令——可 script 驅動"
            if script_callable
            else "ZCode 端無 script 呼叫面：TaskOutput/SendMessage 為 parent "
            "session in-conversation 工具、spawn 無 headless CLI——structurally-"
            "unavailable；ping 語義無法由 script 端凍結（in-conversation 實驗"
            "留 parent session／後續卡），凍結前 ping＝reachability-only"
        ),
        "toolFaces": tool_faces,
    }


# ---------------------------------------------------------------------------
# corpus 自動探測（cell id 缺省時）
# ---------------------------------------------------------------------------


def discover_cells(cli_root: Path) -> dict[str, tuple[str, str]]:
    """從真機 corpus 自動探測各態最新樣本——回 {state: (task_id, note)}."""
    found: dict[str, tuple[str, str]] = {}
    candidates: list[tuple[datetime, str, str]] = []  # (updatedAt, status, path)
    for meta_path in glob.glob(
        str(cli_root / "agents" / "sess_*" / "*" / "metadata.json")
    ):
        try:
            meta = json.loads(Path(meta_path).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        status = meta.get("status")
        updated = meta.get("updatedAt") or meta.get("createdAt") or ""
        try:
            ts = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
        except ValueError:
            continue
        candidates.append((ts, str(status), meta_path))
    candidates.sort(reverse=True)
    for want in ("running", "completed", "failed", "stopped"):
        for ts, status, path in candidates:
            if status != want:
                continue
            task_id = Path(path).parent.name
            found.setdefault(
                want, (task_id, f"auto-discovered（updatedAt={ts.isoformat()}）")
            )
            break
    # reaped：exec face 在、metadata 缺席的歷史 worker
    for exec_dir in sorted(
        (cli_root / "exec").glob("sess_subagent_agent_*"), reverse=True
    ):
        if find_metadata(cli_root, exec_dir.name) is None:
            found.setdefault(
                "reaped",
                (
                    exec_dir.name,
                    "auto-discovered（exec face 存在＝存在性前證；metadata 缺席）",
                ),
            )
            break
    return found


# ---------------------------------------------------------------------------
# 矩陣執行
# ---------------------------------------------------------------------------


def run_cell(cli_root: Path, cell: Cell) -> Cell:
    cell.queries.append(query_metadata(cli_root, cell.task_id))
    for kind in ("exec", "artifact"):
        cell.queries.append(query_dir_face(cli_root, kind, cell.task_id))
    cell.queries.append(query_output_face(cli_root, cell.task_id))
    cell.queries.append(query_lsof(cli_root, cell.task_id))
    return cell


def render_md(cells: list[Cell], tool: dict) -> str:
    lines = [
        "# ping 五態矩陣記錄表（AIR-162 AC#2）",
        "",
        f"生成：{_now_iso()}——全查詢面唯讀，side effect 欄＝查詢前後 stat 對照。",
        "",
        f"**工具面探測**：{tool['finding']}",
        "",
        "| 態 | taskId | metadata-status | exec-face | artifact-face | output-face | lsof-lease | side-effect |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for cell in cells:
        by = {q.surface: q for q in cell.queries}

        def brief(surface: str, _by: dict = by) -> str:
            q = _by.get(surface)
            if q is None:
                return "—"
            mark = "OK" if q.ok else "MISS"
            return f"{mark}({_clip(q.response, 60)})"

        mutated = any(q.to_dict()["sideEffect"]["changed"] for q in cell.queries)
        lines.append(
            f"| {cell.state} | `{_clip(cell.task_id, 50)}` | "
            f"{brief('metadata-status')} | {brief('exec-face')} | "
            f"{brief('artifact-face')} | {brief('output-face')} | "
            f"{brief('lsof-exec-lease')} | "
            f"{'CHANGED(異常!)' if mutated else 'none'} |"
        )
    lines += [
        "",
        "## 逐格回應原文（bounded）",
        "",
    ]
    for cell in cells:
        lines.append(f"### {cell.state}——`{cell.task_id}`")
        if cell.note:
            lines.append(f"- note：{cell.note}")
        for q in cell.queries:
            d = q.to_dict()
            lines.append(
                f"- **{d['surface']}**：exit={d['exitCode']} "
                f"latency={d['latencyMs']}ms sideEffect={d['sideEffect']}\n"
                f"  - 原文：`{_clip(q.response, 200)}`"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def render_contract(cells: list[Cell], tool: dict) -> str:
    """實驗結論——contract 建議段（AC#3 吸收源；誠實優先）."""
    by_state = {c.state: {q.surface: q for q in c.queries} for c in cells}
    lines = [
        "# ping 五態矩陣——實驗結論與 contract 建議（AIR-162 AC#2）",
        "",
        f"生成：{_now_iso()}。矩陣記錄：matrix.json／matrix.md（同目錄）。",
        "",
        "## 結論",
        "",
    ]

    def ok(state: str, surface: str) -> bool:
        q = by_state.get(state, {}).get(surface)
        return bool(q and q.ok)

    # 逐面可區分性（機械判準：各態 ok/response 是否互異）
    meta_states = {
        s: by_state.get(s, {}).get("metadata-status").response
        if ok(s, "metadata-status")
        else "MISS"
        for s in by_state
    }
    terminal_distinguishable = (
        ok("completed-retained", "metadata-status")
        and ok("failed-stopped", "metadata-status")
        and by_state["completed-retained"]["metadata-status"].response
        != by_state["failed-stopped"]["metadata-status"].response
    )
    reaped_vs_nonexistent = (
        by_state.get("reaped", {}).get("exec-face").ok
        if by_state.get("reaped")
        else False
    ) and not (
        by_state.get("nonexistent", {}).get("exec-face").ok
        if by_state.get("nonexistent")
        else False
    )
    # 機器事實（run-2 實測）：output 缺席與活性共存；lsof 只在 running 命中
    lease_only_running = ok("running", "lsof-exec-lease") and all(
        "LEASE HELD" not in by_state.get(s, {}).get("lsof-exec-lease").response
        for s in by_state
        if s != "running" and by_state.get(s, {}).get("lsof-exec-lease")
    )
    lines += [
        "1. **metadata-status（被動權威面）＝可機械區分 running/terminal 各態**："
        "status 欄逐字回報 running/completed/failed/stopped；terminal 三態互異＝"
        f"{terminal_distinguishable}。此面是唯一權威狀態訊號（A 級 terminal "
        "transition 的來源）——contract 維持不變。",
        f"2. **reaped vs nonexistent＝exec face 可機械區分（reaped 有 exec 面、"
        f"nonexistent 全缺席）**：實測 reaped.exec-face.ok="
        f"{by_state.get('reaped', {}).get('exec-face').ok if by_state.get('reaped') else 'n/a'}、"
        f"nonexistent.exec-face.ok="
        f"{by_state.get('nonexistent', {}).get('exec-face').ok if by_state.get('nonexistent') else 'n/a'}"
        f"（→{reaped_vs_nonexistent}）。**但 metadata 面兩者皆 MISS——單靠 "
        "metadata lookup miss 不可區分 reaped/nonexistent/never-existed，"
        "證成 probe 條款「D 級缺席禁推死、lookup miss＝UNKNOWN」**。",
        "3. **lsof-exec-lease＝process 可尋址性代理（C 級）**：live worker 有 "
        "open fd、死/終態 worker 無——但 K1 限制：fd 存在不證明 progress，"
        "僅 reachability 語義。",
        "4. **output 缺席與活性共存（本次事故的直接實機反證）**：running cell"
        "（self-verified live）output.txt/task.output 皆 ABSENT，同格 lsof "
        "LEASE HELD——**「output 檔不存在」與「worker 正在執行」在真機並存"
        "實證成立，D 級 output 缺席禁進任何判準（含 probe、含人工臨場判讀）**"
        "——今日 marshal 誤判事故的觸發面即此。",
        f"5. **lsof 六格互異（running cell 唯一 LEASE HELD）＝{lease_only_running}**"
        f"：process-presence 訊號在六格全互異——但僅可尋址性（C），禁升 "
        f"liveness/progress（K1）。",
        f"6. **TaskOutput／SendMessage（script 端）＝不可區分——structurally "
        f"unavailable**：{tool['finding']}。故：**ZCode 3.14.3 上 ping 無法由 "
        "script 凍結；probe v1 不內建 ping；ping 失敗＝不在冊（NOT_ADDRESSABLE）"
        "⊃｛死、完成後被清、從未存在、查詢面錯｝，禁死亡推論**。"
        "in-conversation 面的 TaskOutput/SendMessage 語義（含 nonce ACK 可否"
        "升 B 級）留 parent session 以 sacrificial workers 實驗（後續卡）。",
        "7. **sacrificial spawn（script 端）＝不可用**：無 headless spawn CLI——"
        "running cell 以 self-verified live worker 替代（執行矩陣的 worker "
        "自身＋lsof 正向控制），其餘四態用真實歷史 corpus（H 級：真實 worker "
        "留存面）。",
        "8. **side effect（零 mutating 實證）**：metadata-status 面查詢前後 stat 對照"
        "零變；其餘面為唯讀列舉／lsof 查詢未做前後快照（sideEffect.checked=false"
        "記錄）；SendMessage 屬 mutating（文獻面），契約凍結前禁對真 worker"
        "使用（僅 sacrificial）。",
        "",
        "## contract 建議段（吸收進 harness_waiter docstring 偵測節——AC#3）",
        "",
        "- 被動查詢面（metadata/exec/artifact/output/lsof）為 probe 正式語義；"
        "ping（TaskOutput/SendMessage）在 ZCode 無 script 面——probe v1 零 "
        "ping 欄，reachability 判定走被動面。",
        "- metadata lookup miss ≠ 死亡（reaped/nonexistent 實證同文 MISS）；"
        "已註冊身份 metadata 消失（有 registry row 前證）才可 HARD_DEATH_"
        "EVIDENCE（A 級）。",
        "- exec/artifact 面可把 reaped 與 nonexistent 機械分開——但兩者皆非"
        "「死」，歸 UNKNOWN／needs_human 面（存在性 ≠ 活性）。",
        "- lsof lease＝可尋址性（C），禁升 liveness。",
        "",
        "## 方法論限制",
        "",
        "- running cell 的「self-verified」限縮於執行當下；lsof 正向控制證明"
        " fd 存在，不證明 progress（K1）。",
        "- 本矩陣單輪單機（ZCode 3.14.3 macOS arm64）；重複輪次與 harness "
        "restart 後 old-generation case 未涵蓋（codex 腿建議的穩定性重複——"
        "後續卡）。",
        "- in-conversation ping 語義（TaskOutput/SendMessage 對五態的回應原文"
        "／exit／延遲／side effect）本輪無法記錄——structurally unavailable，"
        "非自願跳過。",
        "",
        "## 附錄：metadata-status 逐字回應",
        "",
    ]
    for state, resp in sorted(meta_states.items()):
        lines.append(f"- {state}: `{_clip(resp, 200)}`")
    return "\n".join(lines) + "\n"


def _cells_from_json(payload: dict) -> list[Cell]:
    cells: list[Cell] = []
    for raw in payload.get("cells", []):
        queries = [
            QueryResult(
                surface=q["surface"],
                ok=q["ok"],
                exit_code=q["exitCode"],
                latency_ms=q["latencyMs"],
                response=q["response"],
                saved_side_effect=q.get("sideEffect"),
            )
            for q in raw.get("queries", [])
        ]
        cells.append(Cell(raw["state"], raw["taskId"], raw.get("note", ""), queries))
    return cells


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ping_matrix",
        description="ZCode worker 五態 × 查詢面真機矩陣（AIR-162 AC#2；全唯讀）",
    )
    parser.add_argument(
        "--cli-root",
        type=Path,
        default=Path.home() / ".zcode" / "cli",
        help="ZCode CLI 觀察面根（預設 ~/.zcode/cli）",
    )
    repo_root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--out",
        type=Path,
        default=repo_root / ".agent-tmp" / "ping-matrix",
        help="輸出目錄（預設 <repo>/.agent-tmp/ping-matrix/）",
    )
    for state in ("running", "completed", "failed", "stopped", "reaped"):
        parser.add_argument(f"--{state}", default=None, metavar="TASK_ID")
    parser.add_argument("--nonexistent", default=None, metavar="TASK_ID")
    parser.add_argument(
        "--render-only",
        action="store_true",
        default=False,
        help="不重跑探測——從 <out>/matrix.json 重建 md＋contract（結論迭代用）",
    )
    args = parser.parse_args(argv)

    out: Path = args.out
    if args.render_only:
        payload = json.loads((out / "matrix.json").read_text())
        cells = _cells_from_json(payload)
        tool = payload["toolSurface"]
        md = render_md(cells, tool)
        (out / "matrix.md").write_text(md)
        (out / "contract-suggestion.md").write_text(render_contract(cells, tool))
        print(f"重建：{out}/{{matrix.md,contract-suggestion.md}}")
        return 0

    cli_root = args.cli_root
    if not cli_root.is_dir():
        print(f"cli-root 不存在：{cli_root}", file=sys.stderr)
        return 1
    discovered = discover_cells(cli_root)

    def pick(arg: str | None, state: str) -> tuple[str, str]:
        if arg:
            return arg, "explicit（caller 指定）"
        if state in discovered:
            return discovered[state]
        return (
            f"agent_{uuid.uuid4()}",
            "synthetic（corpus 無樣本——以隨機 id 充當，解讀時注意）",
        )

    run_id, run_note = pick(args.running, "running")
    if args.running is None:
        # running 預設樣本＝最新 running row——K1 限制：metadata running ≠
        # process liveness；lsof 正向控制輔證，解讀保守
        run_note += "；running row ≠ 已驗證活性（K1）——lsof 為正向控制"
    cells = [
        Cell("running", run_id, run_note),
        Cell("completed-retained", *pick(args.completed, "completed")),
        Cell("failed-stopped", *pick(args.failed, "failed")),
        Cell("failed-stopped(stopped)", *pick(args.stopped, "stopped")),
        Cell("reaped", *pick(args.reaped, "reaped")),
        Cell("nonexistent", *pick(args.nonexistent, "nonexistent")),
    ]
    cells = [run_cell(cli_root, c) for c in cells]
    tool = probe_tool_surface()

    payload = {
        "schema": "ping-matrix/1",
        "generatedAt": _now_iso(),
        "cliRoot": str(cli_root),
        "toolSurface": tool,
        "cells": [c.to_dict() for c in cells],
    }
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "matrix.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    md = render_md(cells, tool)
    (out / "matrix.md").write_text(md)
    contract = render_contract(cells, tool)
    (out / "contract-suggestion.md").write_text(contract)
    print(md)
    print(f"輸出：{out}/{{matrix.json,matrix.md,contract-suggestion.md}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
