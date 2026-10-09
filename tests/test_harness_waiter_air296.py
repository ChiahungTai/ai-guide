"""harness_waiter AIR-296 advisory content face 契約測試.

oracle 分級：
- START_MISSING（spawn+5m 驗活＋2m 複查）＝codex 五級表（卡面權威）
- COMPLETION_SUSPECTED 三條件（可信產物＋活動靜止 ≥15m＋running）＝codex 表
- 不變量：兩 advisory 皆 exit 3 wake——不收割（無 pending receipt／無 harvest
  bundle）、不記帳、不 stop 不重派、不自動宣告完成；frozen T1-T9 主體零變
  （AIR-160 外掛 advisory 先例——狀態機表與 exit code 零變）
- 判定單一源＝scripts/zombie_core.py（本檔驗 waiter 接線，不重驗簽章）

測試全程合成 layout（ZCodeLayout(cli_root=tmp_path)），零真機依賴。
"""

import io
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/harness_waiter.py")

T0 = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)
AGENT = "agent_z1"
TASK = f"sess_subagent_{AGENT}"


def make_layout(tmp_path: Path):
    return _mod.ZCodeLayout(cli_root=tmp_path / "zcode-cli")


def dt(h: int, m: int) -> datetime:
    return datetime(2026, 9, 20, h, m, tzinfo=UTC)


def ts(m: int) -> datetime:
    return dt(11 + m // 60, m % 60)  # 11:xx 起（m≥60 進位）——CREATED（11:00）後輪詢時點


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ns(t: datetime) -> int:
    return int(t.timestamp() * 1_000_000_000)


def write_metadata(
    layout,
    parent: str,
    agent_id: str,
    *,
    status: str = "running",
    created: str = "2026-09-20T11:00:00.000Z",
    output_file: str | None = None,
) -> str:
    task = f"sess_subagent_{agent_id}"
    d = layout.agents_root / parent / agent_id
    d.mkdir(parents=True, exist_ok=True)
    meta = {
        "agentId": agent_id,
        "childSessionId": task,
        "createdAt": created,
        "status": status,
        "parentSessionId": parent,
    }
    if output_file is not None:
        meta["outputFile"] = output_file
    (d / "metadata.json").write_text(json.dumps(meta))
    return task


def touch_face_file(root: Path, name: str, *, mtime: datetime) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    p = root / name
    p.write_bytes(b"y" * 10)
    os.utime(p, ns=(ns(mtime),) * 2)
    return p


def reg_path(tmp_path: Path) -> Path:
    return tmp_path / ".agent-tmp" / "liveness-registry.json"


def write_registry(tmp_path: Path, entries: list) -> Path:
    p = reg_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"entries": entries}))
    return p


def reg_entry_dict(task: str = TASK, created: str = "2026-09-20T11:00:00.000Z", **extra) -> dict:
    d = {
        "taskId": task,
        "attemptId": "att-1",
        "createdAt": created,
        "sink": "out.md",
        "expected": {"anchor": "DONE"},
        "survivingHandles": [],
    }
    d.update(extra)
    return d


def clock(*times: datetime):
    it = iter(times)
    return lambda: next(it)


def run_watcher(tmp_path, entries, layout, *, times, **kw):
    rp = write_registry(tmp_path, entries)
    out, err = io.StringIO(), io.StringIO()
    code = _mod.run_watcher(
        layout,
        rp,
        liveness_root=tmp_path / ".agent-tmp" / "liveness",
        poll_interval_s=600.0,
        now_fn=clock(*times),
        sleep_fn=lambda s: None,
        stdout=out,
        stderr=err,
        **kw,
    )
    return code, out.getvalue(), err.getvalue()


def last_json(stdout: str) -> dict:
    return json.loads(stdout.strip().splitlines()[-1])


# --- START_MISSING（預設＝GLM 校準 60min 型 A；5m 提前版 opt-in）---


def test_start_missing_wake_after_recheck(tmp_path):
    # 預設校準閾值：長弧條目（silenceBudget 240）60min 無開工證據→candidate；
    # 複查窗 2m 仍缺→advisory wake
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=created)
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(70), ts(73)],  # 12:10／12:13——age 70min ≥60；candidate 3min ≥2
        max_cycles=3,
    )
    assert code == 3
    tail = last_json(out)
    assert tail["state"] == "start-missing"
    assert tail["advisoryOnly"] is True
    assert tail["taskId"] == TASK
    assert tail["attemptId"] == "att-1"
    assert tail["evidence"]["artifactsFiles"] == 0
    assert tail["evidence"]["execFiles"] == 0
    assert tail["evidence"]["ageMin"] >= 60
    # advisory 不收割不記帳：無 pending receipt、無 harvest bundle
    liveness = tmp_path / ".agent-tmp" / "liveness"
    assert not (liveness / "pending").exists() or not any((liveness / "pending").iterdir())
    assert not (liveness / "harvest").exists() or not any((liveness / "harvest").iterdir())


def test_start_missing_early_mode_opt_in_five_min(tmp_path):
    # codex 五級表 spawn+5m 提前驗活＝顯式 opt-in（GLM 實證 5m 對慢啟動活體
    # 誤旗約半數——首檔 p50=12min——故不作預設）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict()],
        layout,
        times=[ts(6), ts(9)],
        max_cycles=3,
        start_missing_min=5.0,
        start_missing_recheck_min=2.0,
    )
    assert code == 3
    tail = last_json(out)
    assert tail["state"] == "start-missing"
    assert tail["evidence"]["ageMin"] >= 5


def test_start_missing_first_flag_is_candidate_not_wake(tmp_path):
    # 首查（60m）只記 candidate——複查窗 2m 內不得 wake
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=created)
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(70), ts(71)],  # candidate 1min < 2m
        max_cycles=2,
    )
    assert code == 1  # max-cycles 內部收場，非 wake
    assert '"state":"start-missing"' not in out
    assert "start-missing-candidate" in out  # telemetry 行在場


def test_start_evidence_present_suppresses_wake(tmp_path):
    # artifacts 心跳在場＝開工證據——60min 後仍不得 START_MISSING wake
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=created)
    touch_face_file(
        layout.artifact_dir(TASK), "call_1-tool-result-x.json", mtime=dt(10, 50)
    )
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(70), ts(73)],
        max_cycles=2,
    )
    assert code == 1
    assert '"state":"start-missing"' not in out


def test_exec_face_files_count_as_start_evidence(tmp_path):
    # 開工證據＝artifacts 或 exec 任一面有檔（exec 目錄存在≠證據——type A 零檔實證）
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=created)
    touch_face_file(layout.exec_dir(TASK), "call_1-stdout.log", mtime=dt(10, 50))
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(70), ts(73)],
        max_cycles=2,
    )
    assert code == 1
    assert '"state":"start-missing"' not in out


def test_young_entry_below_calibrated_min_no_wake(tmp_path):
    # 標準 20m timebox 條目 age <60min——零 candidate 零 wake（T3 零喚醒不變；
    # 慢啟動活體〔首檔 p50=12min〕不得誤旗——GLM 校準）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT)
    code, out, _err = run_watcher(
        tmp_path, [reg_entry_dict()], layout, times=[ts(6), ts(15)], max_cycles=2
    )
    assert code == 1
    assert "start-missing-candidate" not in out


def test_metadata_gone_is_hard_death_not_start_missing(tmp_path):
    # metadata 消失＝T5 權威路徑（exit 2）——advisory face 不得攔截
    layout = make_layout(tmp_path)  # 不寫 metadata
    code, out, _err = run_watcher(
        tmp_path, [reg_entry_dict()], layout, times=[ts(6), ts(9)]
    )
    assert code == 2
    assert last_json(out)["state"] == "hard-death-wake"


# --- COMPLETION_SUSPECTED：產物在場＋活動靜止 ≥15m＋running→advisory wake ---


def test_completion_suspected_wake(tmp_path):
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    out_txt = layout.agents_root / "sess_p1" / AGENT / "output.txt"
    write_metadata(
        layout, "sess_p1", AGENT, created=created, output_file=str(out_txt)
    )
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_bytes(b"final report body")
    os.utime(out_txt, ns=(ns(dt(10, 50)),) * 2)  # 靜止 30min（poll 11:20）
    touch_face_file(
        layout.artifact_dir(TASK), "call_1-tool-result-x.json", mtime=dt(10, 50)
    )
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],  # 壓 timebox——隔離 advisory face
        layout,
        times=[ts(80)],
        max_cycles=2,
    )
    assert code == 3
    tail = last_json(out)
    assert tail["state"] == "completion-suspected"
    assert tail["advisoryOnly"] is True
    assert tail["evidence"]["outputSize"] == len(b"final report body")
    assert tail["evidence"]["quiesceMin"] >= 15
    # 不自動宣告完成：無收割、無 pending receipt
    liveness = tmp_path / ".agent-tmp" / "liveness"
    assert not (liveness / "pending").exists() or not any((liveness / "pending").iterdir())
    assert not (liveness / "harvest").exists() or not any((liveness / "harvest").iterdir())


def test_completion_suspected_requires_quiesce_window(tmp_path):
    # 產物在場但活動靜止僅 5min（<15m）——completion face 不 wake（等窗滿；
    # START_MISSING 亦被產物在場壓制——工作明顯已發生）
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    out_txt = layout.agents_root / "sess_p1" / AGENT / "output.txt"
    write_metadata(
        layout, "sess_p1", AGENT, created=created, output_file=str(out_txt)
    )
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_bytes(b"fresh report")
    os.utime(out_txt, ns=(ns(dt(11, 15)),) * 2)  # poll 11:20——靜止 5min
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(20)],
        max_cycles=1,
    )
    assert code == 1
    assert '"state":"completion-suspected"' not in out
    assert "start-missing-candidate" not in out


def test_completion_suspected_not_flagged_without_output(tmp_path):
    # 無 output.txt＝型 B 面不成立——即便 artifacts 凍結也不走 completion face
    # （凍結面歸 SILENCE／timebox 域）
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    write_metadata(layout, "sess_p1", AGENT, created=created)
    touch_face_file(
        layout.artifact_dir(TASK), "call_1-tool-result-x.json", mtime=dt(10, 50)
    )
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(80)],
        max_cycles=1,
    )
    assert code == 1
    assert '"state":"completion-suspected"' not in out


# --- 優先序與主體零變 ---


def test_all_terminal_receipt_unaffected(tmp_path):
    # T2 主體零變：全 terminal＝CollectionReceipt exit 0（advisory face 不攔）
    layout = make_layout(tmp_path)
    write_metadata(layout, "sess_p1", AGENT, status="completed")
    (tmp_path / "out.md").write_text("report body\nDONE\n")
    code, out, _err = run_watcher(
        tmp_path, [reg_entry_dict()], layout, times=[ts(6), ts(9)]
    )
    assert code == 0
    assert last_json(out)["exitState"] == "all-terminal"


def test_completion_suspected_outranks_start_missing(tmp_path):
    # 同輪兩訊號：正向產物證據（completion-suspected）優先於缺席證據
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    out_txt = layout.agents_root / "sess_p1" / AGENT / "output.txt"
    write_metadata(
        layout, "sess_p1", AGENT, created=created, output_file=str(out_txt)
    )
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_bytes(b"done")
    os.utime(out_txt, ns=(ns(dt(10, 40)),) * 2)  # 靜止 40min
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(80)],  # age 80min >5m——START_MISSING 條件亦成立
        max_cycles=2,
    )
    assert code == 3
    assert last_json(out)["state"] == "completion-suspected"


def test_terminal_between_reads_skips_advisory(tmp_path):
    # advisory 二讀見 terminal（T2 race）——靜默交 T2，不發 advisory
    layout = make_layout(tmp_path)
    created = "2026-09-20T10:00:00.000Z"
    out_txt = layout.agents_root / "sess_p1" / AGENT / "output.txt"
    write_metadata(
        layout, "sess_p1", AGENT, created=created, output_file=str(out_txt),
        status="completed",
    )
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_bytes(b"done")
    code, out, _err = run_watcher(
        tmp_path,
        [reg_entry_dict(created=created, silenceBudget=240)],
        layout,
        times=[ts(80)],
    )
    assert code == 0
    assert last_json(out)["exitState"] == "all-terminal"
