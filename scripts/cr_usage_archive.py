#!/usr/bin/env python3
"""CR 使用率事件持久化（AIR-206 ④）——bridge jobs jsonl 的 code-reality 工具呼叫歸檔。

事件源：$HOME/Github/* 一層各 workspace 的 .delegate-bridge/jobs/*.jsonl（repo 與
card WT 同層皆掃）。抽取 type=tool.updated、toolName 含 "code-reality" 且 kind 為
result 終態的事件（MCP CR 查詢面；一呼叫一事件——scheduled/started 中間態不收，
V2 review F1：三態全收會 3x 高估。Bash 內嵌 CLI 呼叫不計——雜訊面，v2 再評；
.muse-bridge 樹 schema 不同，不涵蓋——muse 面 v2 再評）。
Sink：~/.local/share/cr-usage/events.jsonl（append-only；欄位＝ts〔上游 epoch 毫秒〕/
jobId/tool/callId/ws）。
State：~/.local/share/cr-usage/state.json（per-file 已處理 byte offset，原子寫；
at-least-once——crash 最壞情況＝重複事件，使用率統計可容忍。已知邊界：job jsonl
被 truncate 且縮小時該檔歸零重掃；truncate 後寫更長內容的接縫半行計入 malformed；
檔案終態無尾 newline 時末行不收）。
排程：deploy/cr-usage-archive.plist（每日 08:20；render 後 launchctl bootstrap，
形態照 dispatch-ledger-sweep 先例）。偵測與處置分離：本腳本只歸檔不做分析。
"""

import json
import sys
from pathlib import Path

HOME = Path.home()
ROOT = HOME / "Github"
OUT_DIR = HOME / ".local" / "share" / "cr-usage"
EVENTS = OUT_DIR / "events.jsonl"
STATE = OUT_DIR / "state.json"
NEEDLE = "code-reality"


def main() -> int:
    if not ROOT.is_dir():
        print(f"[FAIL] {ROOT} 不存在", file=sys.stderr)
        return 2
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    state: dict[str, int] = {}
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    new_events: list[dict[str, object]] = []
    scanned = 0
    for jobs_dir in sorted(ROOT.glob("*/.delegate-bridge/jobs")):
        ws = jobs_dir.parents[1].name
        for f in sorted(jobs_dir.glob("*.jsonl")):
            scanned += 1
            key = str(f)
            off = state.get(key, 0)
            size = f.stat().st_size
            if off > size:
                off = 0  # 檔案縮小——歸零重掃該檔
            if size <= off:
                continue
            with f.open("rb") as fh:
                fh.seek(off)
                blob = fh.read()
            cut = blob.rfind(b"\n")
            if cut < 0:
                continue  # 無完整新行——offset 不動，下輪再收（終態無尾 newline 則末行不收）
            for line in blob[: cut + 1].splitlines():
                try:
                    e = json.loads(line)
                except Exception:
                    print(f"[WARN] malformed line skipped: {key}@{off}", file=sys.stderr)
                    continue
                if e.get("type") != "tool.updated":
                    continue
                payload = e.get("payload") or {}
                tool = payload.get("toolName") or ""
                if NEEDLE not in tool:
                    continue
                kind = payload.get("kind") or ""
                if kind not in ("", "result"):
                    continue  # scheduled/started 中間態不收
                new_events.append(
                    {
                        "ts": e.get("timestamp"),
                        "jobId": f.stem,
                        "tool": tool,
                        "callId": payload.get("toolCallId") or "",
                        "ws": ws,
                    }
                )
            state[key] = off + cut + 1
    if new_events:
        with EVENTS.open("a", encoding="utf-8") as out:
            for ev in new_events:
                out.write(json.dumps(ev, ensure_ascii=False) + "\n")
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE)
    print(f"[OK] scanned={scanned} files, new cr events={len(new_events)} -> {EVENTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
