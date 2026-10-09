"""agent_liveness_sweep --zcode-scan 契約測試（AIR-296 第二層——全域 sweeper）.

驗證式（oracle＝I 級 impl 契約＋H 級校準簽章經 zombie_core 單一源；真機
90 例驗證歸 ledger 真跑節）：
- ① --zcode-scan 啟用：text 有 spawn-zombies 節＋表頭計數；JSON 有
  spawn_zombies.events（dedupKey 在場）。
- ② 無 --zcode-scan：既有輸出零變（無 spawn-zombies 節／無 JSON key）。
- ③ 判定單一源：事件分類與 zombie_core.scan_zcode_agents 一致（不重刻）。
- ④ fail-loud：--zcode-root 不存在＝exit 2＋stderr FAIL。
- ⑤ 閾值旗標：--stillbirth-min／--interrupted-min 覆寫生效。
- ⑥ 唯讀：掃描後合成 root 無新增檔案。

fixture＝tmp_path 合成 cli root（agents/artifacts），mtime 以 os.utime 控制。
"""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import load_module

_mod = load_module("scripts/agent_liveness_sweep.py")

T0 = datetime.now(UTC)  # iso() 標記 Z（UTC）——T0 必須同軸；main() 用真實牆鐘造樣本


def ago(**kw) -> str:
    return iso(T0 - timedelta(**kw))


def ns(t: datetime) -> int:
    return int(t.timestamp() * 1_000_000_000)


def iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def make_cli_root(tmp_path: Path) -> Path:
    """合成 ZCode cli root：型 A 死胎＋中斷氣＋型 B＋活體＋損壞 JSON."""
    cli = tmp_path / "zcode-cli"
    cli.mkdir(parents=True, exist_ok=True)
    cli.joinpath("no-journal.md").touch()  # 台帳缺席面——空檔（main 全文掃描用）
    agents = cli / "agents"
    arts = cli / "artifacts"

    def meta(agent, parent, **fields):
        d = agents / parent / agent
        d.mkdir(parents=True, exist_ok=True)
        (d / "metadata.json").write_text(json.dumps(fields))

    # 型 A：running 2h、artifacts 從未建立
    meta("agent_a1", "sess_p1", agentId="agent_a1", status="running",
         createdAt=ago(hours=2), cwd="/w", profileId="p", description="d1")
    # 中斷氣：artifacts 最新檔凍結 4h
    meta("agent_b1", "sess_p1", agentId="agent_b1", status="running",
         createdAt=ago(hours=6))
    adir = arts / "sess_subagent_agent_b1"
    adir.mkdir(parents=True, exist_ok=True)
    f = adir / "call_1-tool-result-x.json"
    f.write_bytes(b"{}")
    stamp = ns(T0 - timedelta(minutes=240))
    os.utime(f, ns=(stamp, stamp))
    # 型 B：output.txt 在場
    out = agents / "sess_p1" / "agent_c1" / "output.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"final report")
    meta("agent_c1", "sess_p1", agentId="agent_c1", status="running",
         createdAt=ago(hours=3), outputFile=str(out))
    # 活體：age 10min、artifacts 缺席（<60min 不得旗標——live 對照）
    meta("agent_d1", "sess_p1", agentId="agent_d1", status="running",
         createdAt=ago(minutes=10))
    # 損壞 JSON（UNKNOWN fail-loud）
    d = agents / "sess_p1" / "agent_e1"
    d.mkdir(parents=True, exist_ok=True)
    (d / "metadata.json").write_text("{broken")
    return cli


def run_sweep(cli: Path, *extra: str):
    argv = [
        "--state-root", str(cli / "state-root"),  # 假 bridge 根（bridge 域空）
        "--journal", str(cli / "no-journal.md"),
        "--zcode-scan", "--zcode-root", str(cli),
        *extra,
    ]
    code = _mod.main(argv)
    return code


def test_zcode_scan_text_has_spawn_section(tmp_path, capsys):
    cli = make_cli_root(tmp_path)
    (cli / "state-root").mkdir()
    code = run_sweep(cli)
    assert code == 0
    out = capsys.readouterr().out
    assert "## spawn-zombies" in out
    assert "START_MISSING" in out and "agent_a1" in out
    assert "SILENCE" in out and "agent_b1" in out
    assert "COMPLETION_SUSPECTED" in out and "agent_c1" in out
    assert "UNKNOWN" in out and "agent_e1" in out
    # live 對照：10min 齡活體不得出現在事件節
    assert "agent_d1" not in out.split("## spawn-zombies")[1].split("##")[0]


def test_zcode_scan_json_events_with_dedup(tmp_path, capsys):
    cli = make_cli_root(tmp_path)
    (cli / "state-root").mkdir()
    run_sweep(cli, "--json")
    payload = json.loads(capsys.readouterr().out)
    sz = payload["spawn_zombies"]
    types = {e["agentId"]: e["alertType"] for e in sz["events"]}
    assert types == {
        "agent_a1": "START_MISSING",
        "agent_b1": "SILENCE",
        "agent_c1": "COMPLETION_SUSPECTED",
        "agent_e1": "UNKNOWN",
    }
    for e in sz["events"]:
        assert e["dedupKey"]
    assert sz["coverage"]["discovered"] == 5
    assert sz["coverage"]["running_fresh"] == 1
    assert sz["counts"]["START_MISSING"] == 1
    # UNKNOWN 去重鍵＝metadata 路徑＋層級（損壞例身份＝檔案位置）
    unk = next(e for e in sz["events"] if e["alertType"] == "UNKNOWN")
    assert unk["dedupKey"].endswith("+UNKNOWN") and unk["dedupKey"].startswith("/")


def test_no_zcode_scan_output_unchanged(tmp_path, capsys):
    cli = make_cli_root(tmp_path)
    (cli / "state-root").mkdir()
    argv = ["--state-root", str(cli / "state-root"), "--json",
            "--journal", str(cli / "no-journal.md")]
    assert _mod.main(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    assert "spawn_zombies" not in payload


def test_zcode_root_missing_fail_loud(tmp_path, capsys):
    (tmp_path / "state-root").mkdir()
    journal = tmp_path / "no-journal.md"
    journal.touch()
    code = _mod.main([
        "--state-root", str(tmp_path / "state-root"),
        "--journal", str(journal),
        "--zcode-scan", "--zcode-root", str(tmp_path / "nope"),
    ])
    assert code == 2
    assert "FAIL" in capsys.readouterr().err


def test_threshold_flags_override(tmp_path, capsys):
    cli = make_cli_root(tmp_path)
    (cli / "state-root").mkdir()
    # 收緊型 A 閾值到 5min——10min 齡活體 agent_d1 也被旗標（閾值生效證明）
    run_sweep(cli, "--json", "--stillbirth-min", "5")
    payload = json.loads(capsys.readouterr().out)
    types = {e["agentId"] for e in payload["spawn_zombies"]["events"]
             if e["alertType"] == "START_MISSING"}
    assert "agent_d1" in types


def test_scan_is_read_only(tmp_path):
    cli = make_cli_root(tmp_path)
    (cli / "state-root").mkdir()
    before = sorted(str(p) for p in cli.rglob("*"))
    run_sweep(cli)
    after = sorted(str(p) for p in cli.rglob("*"))
    assert before == after
