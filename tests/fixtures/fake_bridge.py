#!/usr/bin/env python3
"""假 delegate-bridge CLI stub——bridge_waiter e2e 測試專用，不打真 bridge。

情境由 FAKE_BRIDGE_SCENARIO（JSON 檔）驅動、呼叫計數存 FAKE_BRIDGE_STATE：
- --version → scenario.version（null → exit 2 Unknown subcommand）
- wait ...  → scenario.waits 依序供給 {exit, stdout, stderr}
- show <id> --json → scenario.shows[id]（list 依呼叫次數供給；dict 恆同；
  帶 exit 鍵 → 模擬錯誤面）
"""

import json
import os
import sys
from pathlib import Path


def _load_state(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state))


def main() -> int:
    scenario = json.loads(Path(os.environ["FAKE_BRIDGE_SCENARIO"]).read_text())
    state_path = Path(os.environ["FAKE_BRIDGE_STATE"])
    state = _load_state(state_path)
    args = sys.argv[1:]
    if args[:1] == ["--version"]:
        version = scenario.get("version")
        if version is None:
            sys.stderr.write("Unknown subcommand: --version\n")
            return 2
        sys.stdout.write(f"{version}\n")
        return 0
    cmd = args[0] if args else ""
    if cmd == "wait":
        index = state.get("wait", 0)
        state["wait"] = index + 1
        _save_state(state_path, state)
        steps = scenario["waits"]
        step = steps[index] if index < len(steps) else steps[-1]
        sys.stdout.write(step.get("stdout", ""))
        sys.stderr.write(step.get("stderr", ""))
        return int(step["exit"])
    if cmd == "show":
        job_id = args[1]
        key = f"show:{job_id}"
        index = state.get(key, 0)
        state[key] = index + 1
        _save_state(state_path, state)
        entry = scenario["shows"][job_id]
        if isinstance(entry, list):
            entry = entry[min(index, len(entry) - 1)]
        if entry.get("exit") is not None:
            sys.stderr.write(entry.get("stderr", ""))
            return int(entry["exit"])
        sys.stdout.write(json.dumps(entry))
        return 0
    sys.stderr.write("Unknown subcommand\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
