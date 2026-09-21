"""bridge_waiter 機器登記腿測試（AIR-146 frozen spec amendment——AIR-152）。

armed（T1）／collected（T5/T6）append liveness.jsonl；輔助腿容錯（寫入失敗
不影響 frozen spec exit 契約）；run_watcher 不傳 liveness_path＝停用。
"""

import io
import json
from datetime import UTC, datetime
from pathlib import Path

from conftest import REPO_ROOT, load_module

_mod = load_module("scripts/bridge_waiter.py")
SCRIPT = REPO_ROOT / "scripts" / "bridge_waiter.py"

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _payload(status: str, final_text: str = "done") -> dict:
    return {
        "job": {
            "id": "job-a",
            "status": status,
            "family": "codex",
            "sessionId": "s1",
            "timestamp": "2026-09-21T11:55:00.000Z",
            "extra": {},
        },
        "finalText": final_text,
    }


class FakeClient:
    """version/wait/show 最小面（wait 即刻全 terminal）。"""

    bin_path = "/fake/delegate/2.0.22/bin/delegate-bridge"

    def __init__(self, shows: dict) -> None:
        self._shows = shows

    def version(self) -> str:
        return "2.0.22"

    def wait(
        self,
        job_ids: list[str],
        timeout_ms: int,
        stuck_after_ms: int,
        *,
        wake_on_stuck: bool = False,
        wake_axis: str = "runtime",
    ) -> tuple[int, str, str]:
        return 0, "", ""

    def show(self, job_id: str) -> dict:
        entry = self._shows[job_id]
        if isinstance(entry, list):
            return entry.pop(0)
        return entry


def _run(liveness_path, tmp_path: Path):
    out, err = io.StringIO(), io.StringIO()
    client = FakeClient(
        {"job-a": [_payload("running"), _payload("completed")]}
    )
    code = _mod.run_watcher(
        client,
        ["job-a"],
        now=lambda: NOW,
        stdout=out,
        stderr=err,
        liveness_path=liveness_path,
    )
    return code, out.getvalue(), err.getvalue()


def _lines(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_armed_and_collected_appended(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    code, out, _ = _run(path, tmp_path)
    assert code == 0
    events = _lines(path)
    armed = [e for e in events if e["event"] == "armed"]
    collected = [e for e in events if e["event"] == "collected"]
    assert len(armed) == len(collected) == 1
    assert armed[0]["jobId"] == "job-a"
    assert armed[0]["pid"] > 0
    assert armed[0]["armedAt"]
    assert collected[0]["jobId"] == "job-a"
    assert collected[0]["exitState"] == "completed"


def test_append_only_across_runs(tmp_path):
    path = tmp_path / ".agent-tmp" / "liveness.jsonl"
    _run(path, tmp_path)
    _run(path, tmp_path)
    events = _lines(path)
    assert sum(1 for e in events if e["event"] == "armed") == 2  # 不覆寫歷史行


def test_liveness_disabled_by_default(tmp_path):
    """run_watcher 不傳 liveness_path＝登記腿停用（既有調用面零影響）。"""
    code, _out, _err = _run(None, tmp_path)
    assert code == 0
    assert not (tmp_path / ".agent-tmp").exists()


def test_write_failure_tolerated(tmp_path):
    """輔助腿容錯：路徑不可寫（父為檔案）→ stderr 診斷、exit 契約不變。"""
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    path = blocker / "liveness.jsonl"
    code, out, err = _run(path, tmp_path)
    assert code == 0  # frozen spec exit 契約不變
    assert '"schema":"collection-receipt/1"' in out
    assert "liveness 登記失敗" in err


def test_docstring_amendment_note_present():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AIR-146 frozen spec amendment" in source
    assert "AIR-152" in source
