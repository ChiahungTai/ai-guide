"""watcher pairing nag 契約測試（AIR-135 Q8 MVP-2——AIR-152）。

evaluate() 直呼驅動（tmp repo 非 git repo → _git_toplevel 退 cwd，ledger/
liveness/state 全落 tmp）——不碰真 repo 的 .delegate-bridge／.agent-tmp。
block 契約＝reason 字串（main 層包 {"decision":"block"}）；放行＝None；
fail-open 面（malformed payload／缺 ledger）＝None。
"""

import ast
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import REPO_ROOT, load_module

HOOK = REPO_ROOT / "hooks" / "watcher_pairing_nag.py"
NAG = load_module("hooks/watcher_pairing_nag.py")


def _iso(minutes_ago: float) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes_ago)).isoformat()


def _make_repo(tmp_path: Path, rows: list) -> Path:
    repo = tmp_path / "repo"
    (repo / ".delegate-bridge").mkdir(parents=True)
    (repo / ".delegate-bridge" / "jobs.json").write_text(
        json.dumps(rows, ensure_ascii=False), encoding="utf-8"
    )
    return repo


def _payload(repo: Path, session: str = "sess-1") -> dict:
    return {"session_id": session, "cwd": str(repo)}


def _job(
    job_id: str, session: str, minutes_ago: float, status: str = "running"
) -> dict:
    return {
        "id": job_id,
        "status": status,
        "sessionId": session,
        "timestamp": _iso(minutes_ago),
    }


# ---------------------------------------------------------------------------
# mixed-session／rollback Python 3.9 syntax compatibility gate
# ---------------------------------------------------------------------------


def test_hook_parses_as_py39():
    source = HOOK.read_text(encoding="utf-8")
    ast.parse(source, filename=str(HOOK))
    ast.parse(source, filename=str(HOOK), feature_version=(3, 9))


# ---------------------------------------------------------------------------
# 判定矩陣：running＋超寬限＋無 liveness → block；任一不滿足 → None
# ---------------------------------------------------------------------------


def test_unpaired_stale_running_blocks(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    reason = NAG.evaluate(_payload(repo))
    assert reason is not None
    assert "job-a-1" in reason
    assert "bridge_waiter.py" in reason  # arm 命令已內嵌
    assert "uv run python" in reason  # copy-paste 形
    assert "liveness.jsonl" in reason  # 為什麼（無登記）


def test_liveness_registered_no_block(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    liveness = repo / ".agent-tmp" / "liveness.jsonl"
    liveness.parent.mkdir(parents=True)
    liveness.write_text(
        "{bad json line\n" + json.dumps({"event": "armed", "jobId": "job-a-1"}) + "\n",
        encoding="utf-8",
    )
    assert NAG.evaluate(_payload(repo)) is None


def test_fresh_dispatch_within_grace_no_block(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 5.0)])
    assert NAG.evaluate(_payload(repo)) is None


def test_non_running_no_block(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0, status="completed")])
    assert NAG.evaluate(_payload(repo)) is None


def test_null_session_row_not_attributed_no_block(tmp_path):
    """sessionId null（現行 bridge dispatch 常態）不歸屬——不誤報他 session 存量。"""
    row = _job("job-a-1", "sess-1", 15.0)
    row["sessionId"] = None
    repo = _make_repo(tmp_path, [row])
    assert NAG.evaluate(_payload(repo, "sess-1")) is None


def test_other_session_rows_not_attributed(tmp_path):
    repo = _make_repo(
        tmp_path,
        [_job("job-a-1", "sess-other", 15.0), _job("job-a-2", None, 15.0)],
    )
    assert NAG.evaluate(_payload(repo, "sess-1")) is None


def test_missing_ledger_no_block(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    assert NAG.evaluate(_payload(repo)) is None


def test_malformed_ledger_no_block(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".delegate-bridge").mkdir(parents=True)
    (repo / ".delegate-bridge" / "jobs.json").write_text("[broken", encoding="utf-8")
    assert NAG.evaluate(_payload(repo)) is None


def test_missing_session_id_no_block(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    assert NAG.evaluate({"cwd": str(repo)}) is None
    assert NAG.evaluate({}) is None


def test_naive_timestamp_no_block(tmp_path):
    """naive 時間戳不可計齊 → 不催告（fail-safe 方向，post-build-gate 同哲學）。"""
    row = _job("job-a-1", "sess-1", 15.0)
    row["timestamp"] = datetime(2026, 9, 21, 12, 0, 0).isoformat()  # noqa: DTZ001 -- intentionally naive rejection fixture.
    repo = _make_repo(tmp_path, [row])
    assert NAG.evaluate(_payload(repo)) is None


# ---------------------------------------------------------------------------
# budget 2／session＋每 jobId 至多一次＋超預算只記 audit 不擋
# ---------------------------------------------------------------------------


def test_same_job_not_reblocked(tmp_path):
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    first = NAG.evaluate(_payload(repo))
    assert first is not None
    assert NAG.evaluate(_payload(repo)) is None  # 已催告過＝不重報存量


def test_budget_two_then_audit_only(tmp_path):
    """逐 job 派工：前兩次 block 消耗預算；第三次超預算→只記 audit 行不擋。"""
    repo = tmp_path / "repo"
    (repo / ".delegate-bridge").mkdir(parents=True)

    def dispatch(job_id: str) -> None:
        (repo / ".delegate-bridge" / "jobs.json").write_text(
            json.dumps([_job(job_id, "sess-1", 15.0)], ensure_ascii=False),
            encoding="utf-8",
        )

    dispatch("job-a")
    assert NAG.evaluate(_payload(repo)) is not None  # #1
    dispatch("job-b")
    assert NAG.evaluate(_payload(repo)) is not None  # #2
    dispatch("job-c")
    assert NAG.evaluate(_payload(repo)) is None  # 預算耗盡——只記 audit 不擋
    audit = repo / ".agent-tmp" / "watcher-pairing-nag-audit.jsonl"
    assert audit.exists()
    line = json.loads(audit.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert line["event"] == "budget-exhausted"


def test_single_block_covers_all_due_jobs_at_once(tmp_path):
    """同一時點多個未配對 job→一次 block 併報（預算計一次）。"""
    rows = [_job("job-a", "sess-1", 15.0), _job("job-b", "sess-1", 15.0)]
    repo = _make_repo(tmp_path, rows)
    reason = NAG.evaluate(_payload(repo))
    assert reason is not None
    assert "job-a" in reason and "job-b" in reason


def test_budget_is_per_session(tmp_path):
    repo = _make_repo(
        tmp_path, [_job("job-a", "sess-1", 15.0), _job("job-b", "sess-2", 15.0)]
    )
    assert NAG.evaluate(_payload(repo, "sess-1")) is not None
    assert NAG.evaluate(_payload(repo, "sess-2")) is not None  # 另 session 自有預算


# ---------- 回歸（codex 152-C4/C5 審查修復釘） ----------


def test_liveness_exact_jobid_no_substring_false_match(tmp_path):
    """job-a 的登記查詢不得被子串命中 job-a-1 的記錄（152-C4）。"""
    repo = _make_repo(tmp_path, [_job("job-a", "sess-1", 15.0)])
    liveness = repo / ".agent-tmp" / "liveness.jsonl"
    liveness.parent.mkdir(parents=True)
    liveness.write_text(
        json.dumps({"event": "armed", "jobId": "job-a-1"}) + "\n", encoding="utf-8"
    )
    reason = NAG.evaluate(_payload(repo))
    assert reason is not None  # job-a 無己身登記——照樣催告


def test_liveness_malformed_text_line_is_not_registration(tmp_path):
    """壞行即使文字含 jobId 也不算登記（152-C4：docstring 與實作對齊）。"""
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    liveness = repo / ".agent-tmp" / "liveness.jsonl"
    liveness.parent.mkdir(parents=True)
    liveness.write_text(
        "watcher armed for job-a-1 manually（非 JSON——舊手寫殘留）\n", encoding="utf-8"
    )
    reason = NAG.evaluate(_payload(repo))
    assert reason is not None


def test_state_write_failure_fails_open(tmp_path, monkeypatch):
    """state 寫不入＝預算/去重無法承諾——不攔（152-C5 fail-open 契約）。"""
    repo = _make_repo(tmp_path, [_job("job-a-1", "sess-1", 15.0)])
    monkeypatch.setattr(NAG, "_save_state", lambda path, state: False)
    assert NAG.evaluate(_payload(repo)) is None
