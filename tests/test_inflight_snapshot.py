"""inflight_snapshot 在飛總表機械生成契約測試（AIR-168 AC#3）.

驗證式（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）：
- bridge jobs：jsonl 最後一行 parse，status 非 completed＝在飛（completed
  只計數不進表）；壞 JSONL 行標 parse-error 續跑不炸；無 jobs 目錄＝skip
  非錯。
- scbus：只收 observed_liveness=="live" 且 session_id 以 sess_ 開頭——
  UUID sid、scbus-ext-* 幽靈、非 live 全數排除；欄位 sid 前 13 碼／name／
  workspace 尾段／status／age_min。
- 三路獨立容錯：單路失敗（scbus 缺席／raise）＝該路標 unavailable、其他
  路照常；全源失敗 exit 仍 0（exit 恆 0 契約）。
- 輸出同構：--json 與 markdown 同五區段（bridge jobs／scbus live
  sessions／worktrees／card branches／dirty files）＋生成時間表頭。

oracle＝I 級（impl 衍生——抽取契約單一源即 scripts/inflight_snapshot.py
docstring；真資料源 L4 實跑由 full 複驗）。
"""

import json
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/inflight_snapshot.py")


def _write_job(path: Path, lines: list[dict | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [line if isinstance(line, str) else json.dumps(line) for line in lines]
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _fail_run(cmd: list[str], **kwargs: object) -> str:
    raise FileNotFoundError(f"fake run fail: {cmd[0]}")


def _fake_run_with_scbus_fail(git_outputs: dict[str, str]):
    def run(cmd: list[str], **kwargs: object) -> str:
        joined = " ".join(cmd)
        if cmd[0] == "scbus":
            raise FileNotFoundError("scbus missing")
        for key, out in git_outputs.items():
            if key in joined:
                return out
        raise AssertionError(f"unexpected cmd: {joined}")

    return run


class TestBridgeJobs:
    def test_only_non_completed_reported_as_in_flight(self, tmp_path: Path) -> None:
        jobs = tmp_path / "jobs"
        _write_job(jobs / "job-a.jsonl", [{"status": "running"}])
        _write_job(
            jobs / "job-b.jsonl",
            [{"status": "running"}, {"status": "completed"}],  # 最後一行 wins
        )
        out = _mod.collect_bridge_jobs(jobs)
        assert out["unavailable"] is False
        assert [r["job_id"] for r in out["in_flight"]] == ["job-a"]
        assert out["completed"] == 1
        assert out["total"] == 2

    def test_bad_jsonl_marks_parse_error_and_continues(self, tmp_path: Path) -> None:
        jobs = tmp_path / "jobs"
        _write_job(jobs / "job-bad.jsonl", ["{not json"])
        _write_job(jobs / "job-ok.jsonl", [{"status": "running"}])
        out = _mod.collect_bridge_jobs(jobs)
        statuses = {r["job_id"]: r["status"] for r in out["in_flight"]}
        assert statuses["job-bad"] == "parse-error"
        assert statuses["job-ok"] == "running"
        assert out["parse_errors"] == 1

    def test_missing_dir_is_skip_not_error(self, tmp_path: Path) -> None:
        out = _mod.collect_bridge_jobs(tmp_path / "nope")
        assert out["unavailable"] is False
        assert out["skipped"] is True
        assert out["in_flight"] == []

    def test_unreadable_entry_row_has_full_columns(self, tmp_path: Path) -> None:
        # 目錄冒充 .jsonl → OSError 路：列仍帶全四欄（真資料 L4 揭露的 regression）
        jobs = tmp_path / "jobs"
        (jobs / "job-dir.jsonl").mkdir(parents=True)
        out = _mod.collect_bridge_jobs(jobs)
        row = out["in_flight"][0]
        assert row["status"] == "parse-error"
        assert {"job_id", "status", "model", "timestamp"} <= set(row)

    def test_render_tolerates_missing_optional_keys(self) -> None:
        # render 面 .get 防禦——列缺 model/timestamp 不炸（exit 恆 0 契約）
        lines = _mod._render_bridge_jobs(
            {
                "unavailable": False,
                "in_flight": [{"job_id": "j", "status": "parse-error"}],
                "completed": 0,
                "total": 1,
                "parse_errors": 1,
            }
        )
        assert any("| j |" in ln for ln in lines)


class TestScbusSessions:
    def test_filter_live_sess_prefix_only(self) -> None:
        payload = {
            "count": 4,
            "status": "ok",
            "sessions": [
                {  # 命中：live ＋ sess_ 前綴
                    "session_id": "sess_7716635a-ac9d-404a",
                    "name": "bridge-fixer",
                    "workspace_root": "/Users/ctai/Github/delegate-bridge",
                    "status": "active",
                    "observed_liveness": "live",
                    "age": 900,
                },
                {  # 排除：UUID sid（非 sess_ 前綴）＋假活（ended）
                    "session_id": "064b2c7b-fe00-4709",
                    "name": None,
                    "workspace_root": "/x/y",
                    "status": "ended",
                    "observed_liveness": "live",
                    "age": 60,
                },
                {  # 排除：scbus-ext-* 幽靈（非 sess_ 前綴，前綴過濾自然排除）
                    "session_id": "scbus-ext-ghost-1",
                    "name": "ghost",
                    "workspace_root": "/w",
                    "status": "active",
                    "observed_liveness": "live",
                    "age": 1,
                },
                {  # 排除：非 live
                    "session_id": "sess_dead-1",
                    "name": "dead",
                    "workspace_root": "/w",
                    "status": "ended",
                    "observed_liveness": "ended",
                    "age": 1,
                },
            ],
        }

        def fake_run(cmd: list[str], **kwargs: object) -> str:
            assert cmd[0] == "scbus"
            return json.dumps(payload)

        out = _mod.collect_scbus_sessions(run=fake_run)
        assert out["unavailable"] is False
        assert len(out["rows"]) == 1
        row = out["rows"][0]
        assert row["session"] == "sess_7716635a"  # 前 13 碼
        assert row["name"] == "bridge-fixer"
        assert row["workspace"] == "delegate-bridge"  # 尾段
        assert row["status"] == "active"
        assert row["age_min"] == 15
        assert out["registry_total"] == 4


class TestFaultTolerance:
    def test_single_source_failure_marks_unavailable(self, tmp_path: Path) -> None:
        run = _fake_run_with_scbus_fail(
            {
                "worktree": "worktree /repo\n\nworktree /repo-wt\nbranch refs/heads/air-168\n",
                "branch": "  air-168\n",
                "status": " M a.py\n?? b.txt\n",
            }
        )
        snap = _mod.build_snapshot(tmp_path, run=run)
        assert snap["scbus_sessions"]["unavailable"] is True
        assert "scbus" in snap["scbus_sessions"]["error"]
        # 其他路照常
        assert snap["bridge_jobs"]["skipped"] is True  # tmp 無 jobs 目錄＝skip
        assert snap["worktrees"]["rows"] == [{"path": "/repo-wt", "branch": "air-168"}]
        assert snap["card_branches"]["branches"] == [
            {"name": "air-168", "current": False}
        ]
        assert snap["dirty_files"]["count"] == 2

    def test_card_branches_strip_plus_marker(self) -> None:
        # `+ `＝branch 被其他 worktree checkout（真資料 L4 揭露）——name 剝乾淨、
        # current 只認 `*`（本 WT）
        run = _fake_run_with_scbus_fail({"branch": "+ air-168\n  air-169\n* air-170\n"})
        out = _mod.collect_card_branches(run=run)
        assert out["branches"] == [
            {"name": "air-168", "current": False},
            {"name": "air-169", "current": False},
            {"name": "air-170", "current": True},
        ]

    def test_total_failure_still_exits_zero(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_mod, "_run_cmd", _fail_run)
        assert _mod.main([]) == 0
        out = capsys.readouterr().out
        assert out.count("unavailable") >= 3  # 各源大聲標記，非空白


class TestOutputForms:
    def test_main_json_isomorphic_sections(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        run = _fake_run_with_scbus_fail(
            {
                "worktree": "worktree /repo\n\nworktree /repo-wt\nbranch refs/heads/air-168\n",
                "branch": "  air-168\n",
                "status": " M a.py\n",
            }
        )
        monkeypatch.setattr(_mod, "_run_cmd", run)
        assert _mod.main(["--json"]) == 0
        snap = json.loads(capsys.readouterr().out)
        assert set(snap) == {
            "generated_at",
            "bridge_jobs",
            "scbus_sessions",
            "worktrees",
            "card_branches",
            "dirty_files",
        }
        assert snap["bridge_jobs"]["skipped"] is True
        assert snap["scbus_sessions"]["unavailable"] is True
        assert snap["dirty_files"]["count"] == 1

    def test_main_markdown_header_and_five_sections(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(_mod, "_run_cmd", _fail_run)
        assert _mod.main([]) == 0
        out = capsys.readouterr().out
        assert out.startswith("# 在飛總表")
        for section in (
            "## bridge jobs",
            "## scbus live sessions",
            "## worktrees",
            "## card branches",
            "## dirty files",
        ):
            assert section in out
