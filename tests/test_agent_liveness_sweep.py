"""agent_liveness_sweep bounded 掃描契約測試（AIR-271 AC#1/#2/#4）.

驗證式（oracle＝I 級——抽取契約單一源即 scripts/agent_liveness_sweep.py
docstring bounded 段＋實作工單定稿；真資料 L4 實跑由 acceptance 複驗）：
- ① full 向後相容：無 cap 全讀、既有分類不變、輸出無 coverage 面（零變）。
- ② cap＋選檔序：index-running 最舊→最新先掃（zombie 不漏）、budget 外不讀。
- ③ hard caps：max-files／max-bytes／並存先達先停，stop_reason 正確。
- ④ fail-visible：極小 budget 下 running=r/R＋unscanned 行在場——不得把
  zombie=0 冒充完整。
- ⑤ coverage parity：text／JSON 兩形數字一致。
- ⑥ unscanned stat-only：被跳過檔塞終態內容仍綠（證明 body 未讀）。

fixture＝tmp_path 雙假根＋jobs.json＋手工 jsonl＋os.utime 控 mtime；
_read_job_text seam monkeypatch 記錄實際 body reads（沿 test_inflight_snapshot 形態）。
"""

import json
import os
import re
import time
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/agent_liveness_sweep.py")


# --- helpers（雙假根＋手工 jsonl＋mtime 控制） ---


def _make_root(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name / ".delegate-bridge"
    (root / "jobs").mkdir(parents=True)
    return root


def _write_index(root: Path, rows: list[dict]) -> None:
    (root / "jobs.json").write_text(json.dumps(rows), encoding="utf-8")


def _write_jsonl(root: Path, job_id: str, lines: list[dict]) -> Path:
    path = root / "jobs" / f"{job_id}.jsonl"
    path.write_text(
        "\n".join(json.dumps(ln) for ln in lines) + "\n", encoding="utf-8"
    )
    return path


def _write_raw(root: Path, job_id: str, size: int) -> Path:
    """非 JSON 內容（scan_event_stream→unparsable，face 維持 running）＋精確 size。"""
    path = root / "jobs" / f"{job_id}.jsonl"
    path.write_bytes(b"x" * size)
    return path


def _hours_ago(path: Path, hours: float) -> None:
    ts = time.time() - hours * 3600
    os.utime(path, (ts, ts))


def _run(
    monkeypatch,
    capsys,
    tmp_path: Path,
    roots: list[Path],
    extra: list[str] | None = None,
    track_reads: list[str] | None = None,
) -> tuple[int, str]:
    journal = tmp_path / "journal.md"
    if not journal.exists():
        journal.write_text("", encoding="utf-8")
    original = _mod._read_job_text

    if track_reads is not None:

        def seam(path: Path) -> str:
            track_reads.append(path.name)
            return original(path)

        monkeypatch.setattr(_mod, "_read_job_text", seam)

    argv: list[str] = ["--state-root"] + [str(root) for root in roots]
    argv += ["--journal", str(journal), "--sink-base", str(tmp_path)]
    argv += extra or []
    code = _mod.main(argv)
    return code, capsys.readouterr().out


# --- ① full 向後相容 ---


class TestFullBackwardCompat:
    def test_no_cap_reads_all_classification_unchanged(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        b = _make_root(tmp_path, "b")
        _write_index(
            a,
            [
                {"id": "job-oldrun", "status": "running", "family": "glm"},
                {"id": "job-done", "status": "completed", "family": "muse"},
            ],
        )
        oldrun = _write_jsonl(a, "job-oldrun", [{"type": "message", "text": "hi"}])
        _hours_ago(oldrun, 30)  # running＋舊 mtime → zombie
        done = _write_jsonl(a, "job-done", [{"type": "turn.completed"}])
        _hours_ago(done, 2)  # index terminal＋台帳無登記 → unledgered
        ghost = _write_jsonl(b, "job-ghost", [{"type": "message"}])
        _hours_ago(ghost, 1)  # 無 index＋jsonl 無終態 → running-fresh
        resp = b / "jobs" / "job-resp.jsonl"  # 多行 response 檔 → completed face
        resp.write_text(json.dumps({"response": "x" * 50}, indent=2), encoding="utf-8")
        _hours_ago(resp, 3)

        reads: list[str] = []
        code, out = _run(monkeypatch, capsys, tmp_path, [a, b], track_reads=reads)
        assert code == 0
        assert sorted(reads) == [
            "job-done.jsonl",
            "job-ghost.jsonl",
            "job-oldrun.jsonl",
            "job-resp.jsonl",
        ]
        # 既有分類不變
        assert "zombie-suspect=1" in out
        assert "running-fresh=1" in out
        assert "unledgered(≤168h)=2" in out
        assert "- job-oldrun" in out
        assert "- job-ghost" in out
        # 零變：full 模式無 coverage 面
        assert not any(ln.startswith("scan=") for ln in out.splitlines())
        assert "coverage:" not in out
        assert "unscanned:" not in out

    def test_full_json_has_no_coverage_key(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        raw = _write_raw(a, "job-r1", 40)
        _hours_ago(raw, 7)
        code, out = _run(monkeypatch, capsys, tmp_path, [a], extra=["--json"])
        assert code == 0
        payload = json.loads(out)
        assert "coverage" not in payload
        assert payload["counts"]["zombie-suspect"] == 1


# --- ② cap＋選檔序 ---


class TestCapPriorityOrder:
    def test_running_oldest_first_zombie_not_missed(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        b = _make_root(tmp_path, "b")
        _write_index(
            a,
            [
                {"id": "job-zold", "status": "running"},
                {"id": "job-znew", "status": "running"},
                {"id": "job-term", "status": "completed"},
            ],
        )
        zold = _write_jsonl(a, "job-zold", [{"type": "message"}])
        _hours_ago(zold, 30)  # 舊 running＝zombie 候選（最優先掃）
        znew = _write_jsonl(a, "job-znew", [{"type": "message"}])
        _hours_ago(znew, 1)
        term = _write_jsonl(a, "job-term", [{"type": "turn.completed"}])
        _hours_ago(term, 0.5)  # index-terminal——body I/O 最後
        fresh = _write_jsonl(b, "job-fresh", [{"type": "message"}])
        _hours_ago(fresh, 0.2)  # 無 index 新→舊，中間 tier

        reads: list[str] = []
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a, b], extra=["--max-files", "2"], track_reads=reads
        )
        assert code == 0
        # 選檔序：tier1 index-running 最舊→最新；cap 到即停，term/fresh 未讀
        assert reads == ["job-zold.jsonl", "job-znew.jsonl"]
        assert "scan=2/4 files (bounded: max-files=2)" in out
        assert "stop=max-files" in out
        # zombie 不漏：最舊 running 被讀且分類 zombie-suspect
        assert "## zombie-suspect (1)" in out
        assert "- job-zold" in out
        assert "## running-fresh (1)" in out
        assert "- job-znew" in out
        # 未掃分流：term＝terminal 排除；fresh＝候選
        assert "running=2/3" in out
        assert "skipped=2" in out
        assert "候選（running/無 index）=1 files" in out
        assert "index-terminal 安全排除=1 files" in out
        # budget 外檔不出現在 body 分類列——term 靠 index face 權威分類（安全排除語義）
        assert "- job-fresh" not in out
        assert "- job-term | — | completed [index]" in out


# --- ③ hard caps ---


class TestHardCaps:
    def _four_raw(self, tmp_path: Path) -> Path:
        a = _make_root(tmp_path, "a")
        for i in range(1, 5):
            raw = _write_raw(a, f"job-f{i}", 100)
            _hours_ago(raw, 20 - i)  # f4 最新（16h）→ 無 index 新→舊序 f4,f3,f2,f1
        return a

    def test_max_files_stops_and_reports(self, tmp_path: Path, monkeypatch, capsys) -> None:
        a = self._four_raw(tmp_path)
        reads: list[str] = []
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-files", "2"], track_reads=reads
        )
        assert code == 0
        assert reads == ["job-f4.jsonl", "job-f3.jsonl"]  # 新→舊
        assert "scan=2/4 files" in out
        assert "stop=max-files" in out
        assert "## zombie-suspect (2)" in out  # 16h/17h > stale 6h

    def test_max_bytes_stops_before_overflow(self, tmp_path: Path, monkeypatch, capsys) -> None:
        a = self._four_raw(tmp_path)
        reads: list[str] = []
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-bytes", "150"], track_reads=reads
        )
        assert code == 0
        assert reads == ["job-f4.jsonl"]  # 第二顆會到 200 > 150 → 先停
        assert "scan=1/4 files" in out
        assert "stop=max-bytes" in out

    def test_both_caps_stop_whichever_first(self, tmp_path: Path, monkeypatch, capsys) -> None:
        a = self._four_raw(tmp_path)
        reads: list[str] = []
        code, out = _run(
            monkeypatch,
            capsys,
            tmp_path,
            [a],
            extra=["--max-files", "1", "--max-bytes", "1000000"],
            track_reads=reads,
        )
        assert code == 0
        assert reads == ["job-f4.jsonl"]
        assert "stop=max-files" in out  # files 先達

    def test_budget_out_files_never_read(self, tmp_path: Path, monkeypatch, capsys) -> None:
        a = self._four_raw(tmp_path)

        def guard_seam(path: Path) -> str:
            if path.name in {"job-f1.jsonl", "job-f2.jsonl"}:
                raise AssertionError(f"budget 外檔被讀 body：{path.name}")
            return path.read_text(errors="replace")

        monkeypatch.setattr(_mod, "_read_job_text", guard_seam)
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-files", "2"]
        )
        assert code == 0
        assert "unscanned: 2 files / 0.0 MiB" in out


# --- ④ running=r/R fail-visible ---


class TestRunningVisibility:
    def test_tiny_budget_does_not_masquerade_complete(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        for i in range(3):
            raw = _write_raw(a, f"job-old{i}", 50)
            _hours_ago(raw, 30 + i)  # 若被讀皆為 zombie 候選
        reads: list[str] = []
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-bytes", "10"], track_reads=reads
        )
        assert code == 0
        assert reads == []  # 0 檔在 budget 內
        # 報告面 zombie=0，但 coverage 如實暴露不完整——禁冒充完整
        assert "zombie-suspect=0" in out
        assert "scan=0/3 files" in out
        assert "running=0/3" in out
        assert "unscanned: 3 files" in out
        assert "候選（running/無 index）=3 files" in out
        assert "stop=max-bytes" in out


# --- ⑤ coverage parity（text/JSON 兩形一致） ---


class TestCoverageParity:
    def _scenario(self, tmp_path: Path) -> list[Path]:
        a = _make_root(tmp_path, "a")
        b = _make_root(tmp_path, "b")
        _write_index(a, [{"id": "job-r1", "status": "running"}])
        _write_index(b, [{"id": "job-t1", "status": "completed"}])
        r1 = _write_jsonl(a, "job-r1", [{"type": "message"}])
        _hours_ago(r1, 30)  # tier1 最舊→最先掃
        t1 = _write_jsonl(b, "job-t1", [{"type": "turn.completed"}])
        _hours_ago(t1, 3)  # tier3
        n1 = _write_raw(a, "job-n1", 200)
        _hours_ago(n1, 1)  # tier2 新→舊：n1 先
        n2 = _write_raw(b, "job-n2", 300)
        _hours_ago(n2, 2)
        return [a, b]

    def test_text_and_json_numbers_agree(self, tmp_path: Path, monkeypatch, capsys) -> None:
        roots = self._scenario(tmp_path)
        _, text_out = _run(
            monkeypatch,
            capsys,
            tmp_path,
            roots,
            extra=["--max-files", "2", "--max-bytes", "100000"],
        )
        _, json_out = _run(
            monkeypatch,
            capsys,
            tmp_path,
            roots,
            extra=["--max-files", "2", "--max-bytes", "100000", "--json"],
        )
        cov = json.loads(json_out)["coverage"]

        scan_m = re.search(r"^scan=(\d+)/(\d+) files", text_out, re.MULTILINE)
        assert scan_m
        assert (int(scan_m.group(1)), int(scan_m.group(2))) == (
            cov["content_scanned_files"],
            cov["discovered_files"],
        )
        cov_m = re.search(
            r"running=(\d+)/(\d+) \| roots=(\S+) (\d+)/(\d+), (\S+) (\d+)/(\d+)"
            r" \| skipped=(\d+) \| stop=(\S+)",
            text_out,
        )
        assert cov_m
        assert (int(cov_m.group(1)), int(cov_m.group(2))) == (
            cov["running_scanned"],
            cov["running_candidates"],
        )
        def _root_counts(name: str) -> dict:
            return next(
                v for k, v in cov["per_root"].items() if k.endswith(f"/{name}/.delegate-bridge")
            )

        assert (int(cov_m.group(4)), int(cov_m.group(5))) == (
            _root_counts(cov_m.group(3))["scanned"],
            _root_counts(cov_m.group(3))["discovered"],
        )
        assert (int(cov_m.group(7)), int(cov_m.group(8))) == (
            _root_counts(cov_m.group(6))["scanned"],
            _root_counts(cov_m.group(6))["discovered"],
        )
        assert int(cov_m.group(9)) == cov["discovered_files"] - cov["content_scanned_files"]
        assert cov_m.group(10) == (cov["stop_reason"] or "none")
        # 場景期望：r1（30h tier1）＋n1（1h tier2 最先）被掃；t1 排除、n2 候選
        assert cov["content_scanned_files"] == 2
        assert cov["running_scanned"] == 2 and cov["running_candidates"] == 3
        assert cov["stop_reason"] == "max-files"
        assert cov["bytes"] == _stat_size(roots[0], "job-r1") + _stat_size(roots[0], "job-n1")
        unscanned_m = re.search(r"候選（running/無 index）=(\d+) files", text_out)
        term_m = re.search(r"index-terminal 安全排除=(\d+) files", text_out)
        assert unscanned_m and int(unscanned_m.group(1)) == 1
        assert term_m and int(term_m.group(1)) == 1
        # F4（複核）：JSON unscanned 分流與 text 拆分一致
        assert cov["unscanned_by_face"]["candidates"] == int(unscanned_m.group(1))
        assert cov["unscanned_by_face"]["terminal_excluded"] == int(term_m.group(1))
        assert cov["read_failed"] == 0


def _stat_size(root: Path, job_id: str) -> int:
    return (root / "jobs" / f"{job_id}.jsonl").stat().st_size


# --- ⑥ unscanned stat-only ---


class TestUnscannedStatOnly:
    def test_skipped_file_with_terminal_content_stays_unread(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        _write_index(a, [{"id": "job-oldterm", "status": "completed"}])
        _write_jsonl(a, "job-oldterm", [{"type": "turn.completed"}])  # tier3（index 權威）
        trap = a / "jobs" / "job-trap.jsonl"  # 無 index；若被讀 → terminal face
        trap.write_text('{"type": "turn.completed"}\n', encoding="utf-8")
        _hours_ago(trap, 30)
        ok = _write_jsonl(a, "job-ok", [{"type": "message"}])
        _hours_ago(ok, 1)
        # budget 只夠 job-ok（25B）——trap 30h 較舊排後、超限被跳
        reads: list[str] = []
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-bytes", "30"], track_reads=reads
        )
        assert code == 0
        assert reads == ["job-ok.jsonl"]
        # trap 未讀→無 face→不出現在任何分類列（若被讀會變 terminal 進 unledgered）
        assert "job-trap" not in out
        # oldterm 靠 index face 權威分類（無需 body）——正是「安全排除」語義
        assert "## unledgered (1)" in out
        assert "- job-oldterm" in out
        assert "候選（running/無 index）=1 files" in out  # trap
        assert "index-terminal 安全排除=1 files" in out  # oldterm

    def test_same_scenario_full_mode_flips_trap_terminal(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        """對照組：同場景無 cap——trap 被讀→terminal face 入 unledgered（證明 ⑥ 未讀）。"""
        a = _make_root(tmp_path, "a")
        _write_index(a, [{"id": "job-oldterm", "status": "completed"}])
        _write_jsonl(a, "job-oldterm", [{"type": "turn.completed"}])
        trap = a / "jobs" / "job-trap.jsonl"
        trap.write_text('{"type": "turn.completed"}\n', encoding="utf-8")
        _hours_ago(trap, 30)
        ok = _write_jsonl(a, "job-ok", [{"type": "message"}])
        _hours_ago(ok, 1)
        code, out = _run(monkeypatch, capsys, tmp_path, [a])
        assert code == 0
        assert "unledgered(≤168h)=2" in out  # trap（jsonl terminal）＋oldterm（index terminal）
        assert "- job-trap" in out


# --- F1（複核）：read-fail 不得偽造完整 coverage ---


class TestReadFailCoverage:
    def test_read_fail_not_counted_and_marks_incomplete(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        a = _make_root(tmp_path, "a")
        raw = _write_raw(a, "job-xf", 50)
        _hours_ago(raw, 30)  # running 候選——被偽造計入就會假裝掃過

        def boom(path: Path) -> str:
            raise OSError("disk on fire")

        monkeypatch.setattr(_mod, "_read_job_text", boom)
        code, out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--json", "--max-files", "5"]
        )
        assert code == 0
        cov = json.loads(out)["coverage"]
        assert cov["discovered_files"] == 1
        assert cov["content_scanned_files"] == 0  # 讀取失敗不是 content scan
        assert cov["running_scanned"] == 0  # running 候選未掃——r 不得遞增
        assert cov["read_failed"] == 1  # 獨立計數＝coverage incomplete
        assert cov["bytes"] == 0  # 失敗檔不計 bytes
        # text 面 fail-visible：read-failed 段在場
        code2, text_out = _run(
            monkeypatch, capsys, tmp_path, [a], extra=["--max-files", "5"]
        )
        assert code2 == 0
        assert "read-failed=1" in text_out
        assert "running=0/1" in text_out


# --- F5（複核）：同-tier 雙 root round-robin regression ---


class TestDualRootRoundRobin:
    def test_index_running_tier_interleaves_oldest_first(self, tmp_path: Path) -> None:
        a = _make_root(tmp_path, "a")
        b = _make_root(tmp_path, "b")
        _write_index(a, [{"id": "job-a1", "status": "running"}, {"id": "job-a2", "status": "running"}])
        _write_index(b, [{"id": "job-b1", "status": "running"}, {"id": "job-b2", "status": "running"}])
        faces: dict = {}
        _mod._load_root_index(a, faces)
        _mod._load_root_index(b, faces)
        fa1 = _write_jsonl(a, "job-a1", [{"type": "message"}])
        _hours_ago(fa1, 10)
        fa2 = _write_jsonl(a, "job-a2", [{"type": "message"}])
        _hours_ago(fa2, 8)
        fb1 = _write_jsonl(b, "job-b1", [{"type": "message"}])
        _hours_ago(fb1, 9)
        fb2 = _write_jsonl(b, "job-b2", [{"type": "message"}])
        _hours_ago(fb2, 7)
        files = [_mod._discover_job_files(a, faces), _mod._discover_job_files(b, faces)]
        order = [jf.job_id for jf in _mod._priority_order(files)]
        # tier1 oldest-first 交錯：a1(10h), b1(9h), a2(8h), b2(7h)
        assert order == ["job-a1", "job-b1", "job-a2", "job-b2"]

    def test_no_index_tier_interleaves_newest_first(self, tmp_path: Path) -> None:
        a = _make_root(tmp_path, "a")
        b = _make_root(tmp_path, "b")
        na1 = _write_raw(a, "job-na1", 10)
        _hours_ago(na1, 10)
        na2 = _write_raw(a, "job-na2", 10)
        _hours_ago(na2, 8)
        nb1 = _write_raw(b, "job-nb1", 10)
        _hours_ago(nb1, 9)
        nb2 = _write_raw(b, "job-nb2", 10)
        _hours_ago(nb2, 7)
        files = [_mod._discover_job_files(a, {}), _mod._discover_job_files(b, {})]
        order = [jf.job_id for jf in _mod._priority_order(files)]
        # tier2 newest-first 交錯：na2(8h), nb2(7h), na1(10h), nb1(9h)
        assert order == ["job-na2", "job-nb2", "job-na1", "job-nb1"]
