"""inflight_snapshot 在飛總表機械生成契約測試（AIR-168 AC#3）.

驗證式（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）：
- bridge jobs：jsonl 最後一行 parse，status 非 completed＝在飛（completed
  只計數不進表）；壞 JSONL 行標 parse-error 續跑不炸；無 jobs 目錄＝skip
  非錯。
- session 腿（seam `collect_scbus_sessions`——名隨 frozen script 符號）：
  只收 liveness=="live" 且 session_id 以 sess_ 開頭——UUID sid、幽靈、
  非 live 全數排除；欄位 sid 前 13 碼／name（＝seam label，sidecar 優先）
  ／workspace 尾段／status／age_min。fixture＝monkeypatch seam 模組
  `DEFAULT_DB` 指 tmp fake store（AIR-277 換源後注入面＝store 路徑非
  runner——script 的 `run` 參數位置相容保留、被 seam 忽略）。
- 三路獨立容錯：單路失敗（session store 缺席／git raise）＝該路標
  unavailable、其他路照常；全源失敗 exit 仍 0（exit 恆 0 契約）。
- 輸出同構：--json 與 markdown 同五區段（bridge jobs／live sessions／
  worktrees／card branches／dirty files）＋生成時間表頭。

oracle＝I 級（impl 衍生——抽取契約單一源即 scripts/inflight_snapshot.py
docstring；真資料源 L4 實跑由 full 複驗）。
"""

import json
import sqlite3
import sys
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/inflight_snapshot.py")

_MS = 1_700_000_000_000  # ms epoch（session store 時間單位）


def _seam():
    """inflight 內 `from session_discovery import collect_rows` 綁定的 seam
    模組實例（sys.modules——非 load_module 新實例，patch 它才生效）。"""
    return sys.modules["session_discovery"]


def _seed_store(tmp_path: Path, *rows: tuple) -> Path:
    """tmp fake session store（與 test_session_discovery 同最小表形）。"""
    db = tmp_path / "store.sqlite"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE session ("
        "id TEXT, directory TEXT, title TEXT, time_created INTEGER,"
        " time_updated INTEGER, time_archived INTEGER, task_type TEXT)"
    )
    con.executemany("INSERT INTO session VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()
    return db


def _patch_default_db(monkeypatch, db: Path) -> None:
    monkeypatch.setattr(_seam(), "DEFAULT_DB", db)


def _write_job(path: Path, lines: list[dict | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [line if isinstance(line, str) else json.dumps(line) for line in lines]
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _fail_run(cmd: list[str], **kwargs: object) -> str:
    raise FileNotFoundError(f"fake run fail: {cmd[0]}")


def _fake_run_git_only(git_outputs: dict[str, str]):
    """git 腿 fake（session 腿已不經 runner——AIR-277 後源直讀 store）。"""
    def run(cmd: list[str], **kwargs: object) -> str:
        joined = " ".join(cmd)
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
    def test_filter_live_sess_prefix_only(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import time

        db = _seed_store(
            tmp_path,
            (  # 命中：live ＋ sess_ 前綴
                "sess_7716635a-ac9d-404a",
                "/Users/ctai/Github/delegate-bridge",
                "bridge-fixer",
                _MS,
                (time.time() - 900) * 1_000,
                None,
                "interactive",
            ),
            (  # 排除：UUID sid（非 sess_ 前綴）
                "064b2c7b-fe00-4709", "/x/y", "uuid-row", _MS, _MS, None,
                "interactive",
            ),
            (  # 排除：幽靈（非 sess_ 前綴，前綴過濾自然排除）
                "ext-ghost-1", "/w", "ghost", _MS, _MS, None, "interactive",
            ),
            (  # 排除：非 live（已封存）
                "sess_dead-1", "/w", "dead", _MS, _MS, _MS + 9_000,
                "interactive",
            ),
        )
        _patch_default_db(monkeypatch, db)

        out = _mod.collect_scbus_sessions()
        assert out["unavailable"] is False
        assert len(out["rows"]) == 1
        row = out["rows"][0]
        assert row["session"] == "sess_7716635a"  # 前 13 碼
        assert row["name"] == "bridge-fixer"
        assert row["workspace"] == "delegate-bridge"  # 尾段
        assert row["status"] == "active"
        assert row["age_min"] == 15
        assert out["registry_total"] == 4  # 掃描總數（subagent 排除由 seam 測試釘住）

    def test_name_column_reflects_seam_sidecar_label(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """路 2 吃 session_discovery seam（AIR-254.1）——name 欄＝seam label.

        seam label 合併 sidecar 優先：sidecar 有值時 name 欄顯示 sidecar
        label（非 store title）——證明 rows 來自 seam 正規化層非本檔直查。
        """
        seam = _seam()
        db = _seed_store(
            tmp_path,
            (
                "sess_sidecar-1",
                "/Users/ctai/Github/ai-guide",
                "store-name",
                _MS,
                _MS + 60_000,
                None,
                "interactive",
            ),
        )
        _patch_default_db(monkeypatch, db)
        sidecar = tmp_path / "labels.json"
        seam.set_label("sess_sidecar-1", "seam-tag", sidecar=sidecar)

        out = _mod.collect_scbus_sessions(sidecar=sidecar)
        assert out["rows"][0]["name"] == "seam-tag"


class TestFaultTolerance:
    def test_single_source_failure_marks_unavailable(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        run = _fake_run_git_only(
            {
                "worktree": "worktree /repo\n\nworktree /repo-wt\nbranch refs/heads/air-168\n",
                "branch": "  air-168\n",
                "status": " M a.py\n?? b.txt\n",
            }
        )
        _patch_default_db(monkeypatch, tmp_path / "missing.sqlite")  # store 缺席
        snap = _mod.build_snapshot(tmp_path, run=run)
        assert snap["scbus_sessions"]["unavailable"] is True
        assert "store" in snap["scbus_sessions"]["error"]
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
        run = _fake_run_git_only({"branch": "+ air-168\n  air-169\n* air-170\n"})
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
        _patch_default_db(monkeypatch, tmp_path / "missing.sqlite")  # store 缺席
        assert _mod.main([]) == 0
        out = capsys.readouterr().out
        assert out.count("unavailable") >= 3  # 各源大聲標記，非空白


class TestOutputForms:
    def test_main_json_isomorphic_sections(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        monkeypatch.chdir(tmp_path)
        run = _fake_run_git_only(
            {
                "worktree": "worktree /repo\n\nworktree /repo-wt\nbranch refs/heads/air-168\n",
                "branch": "  air-168\n",
                "status": " M a.py\n",
            }
        )
        monkeypatch.setattr(_mod, "_run_cmd", run)
        _patch_default_db(monkeypatch, tmp_path / "missing.sqlite")  # store 缺席
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
