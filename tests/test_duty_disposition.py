"""disposition ledger 契約測試（AIR-287——db-99 ai-guide 消費端份）。

涵蓋：
- set/get/list 三 face：建立、roundtrip、排序；_meta 目錄不入掃描。
- 五態流轉表：received 為唯一初始態；received→processing→handled 正鏈；
  needs-human→processing（人類介入後續工）；failed→processing（重試）；
  handled 為終態（禁離開）；同態重設＝heartbeat（refresh updated_at_us）。
- crash-only：壞 JSON／schema 壞形＝LedgerCorrupt typed 錯誤——get 與
  list 皆 fail-closed（**整批拒用裁定**：ledger 是 consumer 唯一 semantic
  處理狀態真相源，跳過壞檔＝最需要被看見的停滯／needs-human 記錄可能
  正是壞的那筆（silent-corruption 形態）；拒用範圍最小化到單 address
  目錄——284 前例（整源拒用）是 routing 上游，這裡是自家消費端狀態，
  權衡不同；修復動作明確＝人工檢視／移除該檔）。
- 識別碼驗證：path traversal／空值／非法字元＝InvalidIdentifier。
- 檔案面：0600、atomic 寫（無 tmp 殘留）、目錄自建。
- 併發面（AIR-287 bi 修復——GLM F3）：set() 讀改寫於 per-envelope
  lockfile（<record>.lock，非 .json 不入掃描）上 fcntl flock 序列化
  ——跨進程互斥實證（持鎖期間他程序 set 阻塞）、風暴後記錄完整。
- CLI 面：set/get/list exit 0；typed 錯誤 exit 1；args 誤用 exit 2。
- received sink（duty hook 接線消費面）：safe wrapper 吸收失敗只
  stderr 註記；correlation_id 抽取（in_reply_to 優先、body task/card
  次之、皆缺 None）。
"""

import fcntl
import json
import os
import stat
import subprocess
import sys
import textwrap
import time

import pytest
from conftest import REPO_ROOT, load_module

mod = load_module("scripts/duty_disposition.py")

ADDR = "ai-guide-marshal"
EID = "018f1234-5678-7abc-9def-0123456789ab"


def _write_raw(base_dir, alias, name, doc):
    d = base_dir / alias
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(
        doc if isinstance(doc, str) else json.dumps(doc),
        encoding="utf-8",
    )


# ── set/get/list 三 face ─────────────────────────────────────────────


def test_set_received_creates_record(tmp_path):
    rec = mod.set(
        ADDR, EID, "received", session_id="sess-1",
        correlation_id="task-9", now_us=1_000, base_dir=str(tmp_path),
    )
    assert rec["schema_version"] == 1
    assert rec["envelope_id"] == EID
    assert rec["correlation_id"] == "task-9"
    assert rec["state"] == "received"
    assert rec["updated_at_us"] == 1_000
    assert rec["session_id"] == "sess-1"
    path = tmp_path / ADDR / f"{EID}.json"
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == rec


def test_record_file_mode_0600_and_no_tmp_leftover(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    path = tmp_path / ADDR / f"{EID}.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert list((tmp_path / ADDR).glob("*.tmp")) == []


# ── 併發面（AIR-287 bi 修復——GLM F3：set 讀改寫跨進程鎖）──────────────


def test_set_creates_lockfile_0600_next_to_record(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    lock = tmp_path / ADDR / f"{EID}.json.lock"
    assert lock.exists()
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600


def test_lockfile_not_in_scan_or_gate(tmp_path):
    """lockfile（非 .json）不入 list／get integrity gate——鎖槽位
    留存是復用非記錄殘留（supervisor 掃描同規則，見該檔測試）。"""
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    assert [r["envelope_id"] for r in
            mod.list_records(ADDR, base_dir=str(tmp_path))] == [EID]
    assert mod.get(ADDR, EID, base_dir=str(tmp_path))["state"] == "received"


_LOCK_CHILD_DRIVER = textwrap.dedent("""
    import importlib.util, sys, time
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "_dd_lock_child",
        str(Path(sys.argv[1]) / "scripts" / "duty_disposition.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    t0 = time.monotonic()
    mod.set(sys.argv[2], sys.argv[3], "processing", "child", now_us=2,
            base_dir=sys.argv[4])
    print(time.monotonic() - t0)
""")


def test_set_blocks_while_lockfile_flocked(tmp_path):
    """跨進程互斥實證：他程序持 lockfile flock 期間，set() 阻塞至釋
    鎖（讀改寫臨界區序列化——競寫不得繞流轉表）。"""
    mod.set(ADDR, EID, "received", session_id="parent", now_us=1,
            base_dir=str(tmp_path))
    lock_path = str(tmp_path / ADDR / f"{EID}.json.lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        driver = tmp_path / "_lock_child.py"
        driver.write_text(_LOCK_CHILD_DRIVER, encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(driver), str(REPO_ROOT), ADDR, EID,
             str(tmp_path)],
            stdout=subprocess.PIPE, text=True,
        )
        time.sleep(0.8)  # 持鎖窗口——子程序應全程阻塞
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
    elapsed = float(proc.communicate()[0].strip())
    assert proc.returncode == 0
    assert elapsed >= 0.5  # 阻塞至釋鎖（無鎖實作隨即返回）
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "processing"


def test_set_storm_keeps_record_intact(tmp_path):
    """多程序同刻 heartbeat 風暴——鎖序列化下記錄恆完整（JSON 可解
    析、凍結六鍵、掃描面恰好一筆）。"""
    mod.set(ADDR, EID, "received", session_id="seed", now_us=1,
            base_dir=str(tmp_path))
    driver = tmp_path / "_storm_child.py"
    driver.write_text(
        textwrap.dedent("""
            import importlib.util, sys
            from pathlib import Path
            spec = importlib.util.spec_from_file_location(
                "_dd_storm_child",
                str(Path(sys.argv[1]) / "scripts"
                    / "duty_disposition.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for i in range(20):
                mod.set(sys.argv[2], sys.argv[3], "received",
                        f"p{sys.argv[5]}-{i}", now_us=10 + i,
                        base_dir=sys.argv[4])
        """),
        encoding="utf-8",
    )
    procs = [
        subprocess.Popen(
            [sys.executable, str(driver), str(REPO_ROOT), ADDR, EID,
             str(tmp_path), k],
            stderr=subprocess.PIPE, text=True,
        )
        for k in ("a", "b", "c")
    ]
    for p in procs:
        _out, err = p.communicate()
        assert p.returncode == 0, err
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "received"
    assert len(rec) == 6  # 凍結六鍵
    assert [r["envelope_id"] for r in
            mod.list_records(ADDR, base_dir=str(tmp_path))] == [EID]


def test_get_roundtrip_all_fields(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s1",
            correlation_id="card-1", now_us=100, base_dir=str(tmp_path))
    mod.set(ADDR, EID, "processing", session_id="s1", now_us=200,
            base_dir=str(tmp_path))
    got = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert got["state"] == "processing"
    assert got["updated_at_us"] == 200
    assert got["correlation_id"] == "card-1"  # 後續 set 未傳＝保留原值


def test_get_missing_raises_unknown_record(tmp_path):
    with pytest.raises(mod.UnknownRecord):
        mod.get(ADDR, "nope-none", base_dir=str(tmp_path))


def test_get_refuses_when_any_sibling_corrupt(tmp_path):
    """get 與 list 同 address integrity gate（AIR-287 bi 修復——codex
    F4）：同目錄任一壞 JSON→get 亦 LedgerCorrupt 整批拒用（模組
    docstring 裁定本為如此——實作自此對齊）。"""
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    (tmp_path / ADDR / "bad.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(mod.LedgerCorrupt):
        mod.get(ADDR, EID, base_dir=str(tmp_path))


def test_get_unaffected_by_non_json_and_meta(tmp_path):
    """integrity gate 只看 .json 記錄檔——.lock／_meta／其他副檔名
    不入 gate（與 list 同語義）。"""
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    (tmp_path / ADDR / f"{EID}.json.lock").write_text("", encoding="utf-8")
    meta = tmp_path / "_meta"
    meta.mkdir()
    (meta / "junk.json").write_text("{bad", encoding="utf-8")
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "received"


def test_list_sorted_and_skips_meta(tmp_path):
    for eid, ts in ((EID, 300), ("aaa", 100), ("zzz", 200)):
        mod.set(ADDR, eid, "received", session_id="s", now_us=ts,
                base_dir=str(tmp_path))
    meta = tmp_path / "_meta"
    meta.mkdir()
    (meta / "exception-address.json").write_text("{}", encoding="utf-8")
    rows = mod.list_records(ADDR, base_dir=str(tmp_path))
    assert [r["envelope_id"] for r in rows] == ["aaa", "zzz", EID]


def test_list_empty_dir_returns_empty(tmp_path):
    assert mod.list_records(ADDR, base_dir=str(tmp_path)) == []


# ── 五態流轉表 ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("received", "processing"),
        ("received", "handled"),
        ("received", "needs-human"),
        ("received", "failed"),
        ("processing", "handled"),
        ("processing", "needs-human"),
        ("processing", "failed"),
        ("needs-human", "processing"),
        ("needs-human", "handled"),
        ("needs-human", "failed"),
        ("failed", "processing"),
    ],
)
def test_legal_transitions(tmp_path, first, second):
    mod.set(ADDR, EID, "received", session_id="s", now_us=0 + 1,
            base_dir=str(tmp_path))
    mod.set(ADDR, EID, first, session_id="s", now_us=2,
            base_dir=str(tmp_path))
    rec = mod.set(ADDR, EID, second, session_id="s", now_us=3,
                  base_dir=str(tmp_path))
    assert rec["state"] == second


def test_initial_state_must_be_received(tmp_path):
    with pytest.raises(mod.IllegalTransition):
        mod.set(ADDR, EID, "processing", session_id="s", now_us=1,
                base_dir=str(tmp_path))


def test_handled_is_terminal(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    mod.set(ADDR, EID, "handled", session_id="s", now_us=2,
            base_dir=str(tmp_path))
    with pytest.raises(mod.IllegalTransition):
        mod.set(ADDR, EID, "processing", session_id="s", now_us=3,
                base_dir=str(tmp_path))


def test_same_state_set_is_heartbeat_refresh(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s0", now_us=1,
            base_dir=str(tmp_path))
    mod.set(ADDR, EID, "processing", session_id="s1", now_us=2,
            base_dir=str(tmp_path))
    rec = mod.set(ADDR, EID, "processing", session_id="s2", now_us=99,
                  base_dir=str(tmp_path))
    assert rec["state"] == "processing"
    assert rec["updated_at_us"] == 99
    assert rec["session_id"] == "s2"


def test_unknown_state_rejected(tmp_path):
    with pytest.raises(mod.LedgerError):
        mod.set(ADDR, EID, "done", session_id="s", now_us=1,
                base_dir=str(tmp_path))


# ── 識別碼驗證（crash-only：path traversal 禁）────────────────────────


@pytest.mark.parametrize(
    "bad", ["", "../evil", "a/b", "a b", ".", "..", "x" * 129],
)
def test_invalid_envelope_id(tmp_path, bad):
    with pytest.raises(mod.InvalidIdentifier):
        mod.set(ADDR, bad, "received", session_id="s", now_us=1,
                base_dir=str(tmp_path))


@pytest.mark.parametrize(
    "bad", ["", "../evil", "a/b", ".", ".."],
)
def test_invalid_address_alias(tmp_path, bad):
    with pytest.raises(mod.InvalidIdentifier):
        mod.get(bad, EID, base_dir=str(tmp_path))


# ── crash-only：壞檔 typed 錯誤（整批拒用裁定——見模組 docstring）──────


def test_get_corrupt_json_raises_typed(tmp_path):
    _write_raw(tmp_path, ADDR, f"{EID}.json", "not-json{")
    with pytest.raises(mod.LedgerCorrupt):
        mod.get(ADDR, EID, base_dir=str(tmp_path))


def test_get_schema_violation_raises_typed(tmp_path):
    _write_raw(tmp_path, ADDR, f"{EID}.json", {
        "schema_version": 2,  # 版本壞
        "envelope_id": EID,
        "correlation_id": None,
        "state": "received",
        "updated_at_us": 1,
        "session_id": "s",
    })
    with pytest.raises(mod.LedgerCorrupt):
        mod.get(ADDR, EID, base_dir=str(tmp_path))


def test_list_one_corrupt_file_refuses_whole_address(tmp_path):
    mod.set(ADDR, "good-one", "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    _write_raw(tmp_path, ADDR, "bad-one.json", "{nope")
    with pytest.raises(mod.LedgerCorrupt) as ei:
        mod.list_records(ADDR, base_dir=str(tmp_path))
    assert "bad-one" in str(ei.value)  # 檔名隨行——修復動作明確
    # 拒用範圍＝單 address 目錄：他 address 不受牽連
    mod.set("other-addr", EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    assert len(mod.list_records("other-addr", base_dir=str(tmp_path))) == 1


# ── received sink（duty hook 接線消費面）─────────────────────────────


def _make_disp(action, envelope_id, canonical):
    """組 duty_receive.Disposition 同形物件（避免跨模組 import）。"""
    from types import SimpleNamespace

    return SimpleNamespace(
        action=action, reason="r", klass="handoff", intent="solicit",
        envelope_id=envelope_id, from_session="peer-1",
        created_at_us=1, canonical=canonical,
    )


CANONICAL = json.dumps({
    "schema_version": 2, "message_id": "m1", "envelope_id": EID,
    "from": {"session_id": "peer-1", "name": None, "harness": None},
    "to": {"address": ADDR},
    "delivery": {"mode": "queue", "fallback": None, "intent": "solicit",
                 "wake": "none", "fallback_used": False},
    "created_at_us": 1,
    "body": json.dumps({"class": "handoff", "task": "task-77"}),
})


def test_received_sink_writes_received_records(tmp_path):
    sink = mod.make_received_sink("sess-9", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("surface", EID, CANONICAL)], 5_000)
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "received"
    assert rec["session_id"] == "sess-9"
    assert rec["correlation_id"] == "task-77"  # body task 鍵抽取
    assert rec["updated_at_us"] == 5_000


def test_received_sink_in_reply_to_priority(tmp_path):
    canon = json.loads(CANONICAL)
    canon["in_reply_to"] = "parent-1"
    sink = mod.make_received_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("auto", EID, json.dumps(canon))], 5_000)
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["correlation_id"] == "parent-1"  # in_reply_to 優先於 body task


def test_received_sink_correlation_none_when_absent(tmp_path):
    canon = json.loads(CANONICAL)
    canon["body"] = json.dumps({"class": "handoff"})
    sink = mod.make_received_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("surface", EID, json.dumps(canon))], 5_000)
    assert mod.get(ADDR, EID, base_dir=str(tmp_path))[
        "correlation_id"
    ] is None


def test_received_sink_safe_absorbs_failure(tmp_path, capsys):
    """safe wrapper：ledger 寫入失敗只 stderr 一行——絕不中斷收信處理
    （信件損失 > ledger 缺口；缺口要大聲）。"""
    calls = []

    def boom(addr, disps, now_us):
        calls.append(addr)
        raise OSError("disk full")

    safe = mod.make_safe_sink(boom)
    safe(ADDR, [], 1)  # 不 raise
    assert calls == [ADDR]
    err = capsys.readouterr().err
    assert "duty-disposition" in err


def test_received_sink_skips_non_forwarding_actions(tmp_path):
    """action=auto 也記 received（處理狀態帳記「收到了」；auto 分類
    是消化語義，非 ledger 排除條件——supervisor 靠它觀測 backlog）。"""
    sink = mod.make_received_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("auto", EID, CANONICAL)], 5_000)
    assert mod.get(ADDR, EID, base_dir=str(tmp_path))["state"] == "received"


def test_received_sink_bad_envelope_id_noted_not_raised(tmp_path, capsys):
    sink = mod.make_received_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("surface", "../bad", CANONICAL)], 5_000)
    assert "duty-disposition" in capsys.readouterr().err
    assert mod.list_records(ADDR, base_dir=str(tmp_path)) == []


# ── resolution sink（digest 呈現完成邊界的處理推進——AIR-287 bi 修復
#    必修 1：codex F1「auto 信恆停 received」）─────────────────────────


def test_resolution_sink_auto_advances_handled(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s",
            correlation_id="task-77", now_us=1, base_dir=str(tmp_path))
    sink = mod.make_resolution_sink("sess-2", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("auto", EID, CANONICAL)], 5_000)
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "handled"
    assert rec["session_id"] == "sess-2"
    assert rec["correlation_id"] == "task-77"  # 未帶＝保留原關聯鍵
    assert rec["updated_at_us"] == 5_000


def test_resolution_sink_surface_advances_needs_human(tmp_path):
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    sink = mod.make_resolution_sink("s2", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("surface", EID, CANONICAL)], 5_000)
    assert mod.get(ADDR, EID, base_dir=str(tmp_path))["state"] == (
        "needs-human"
    )


def test_resolution_sink_same_state_is_heartbeat(tmp_path):
    """重呈報已推進信（handled→handled）＝heartbeat——時間戳刷新、
    不 raise。"""
    mod.set(ADDR, EID, "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    mod.set(ADDR, EID, "handled", session_id="s", now_us=2,
            base_dir=str(tmp_path))
    sink = mod.make_resolution_sink("s2", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("auto", EID, CANONICAL)], 9_000)
    rec = mod.get(ADDR, EID, base_dir=str(tmp_path))
    assert rec["state"] == "handled"
    assert rec["updated_at_us"] == 9_000


def test_resolution_sink_unknown_action_skipped(tmp_path):
    """未知 action 不發明狀態（router 面 fail-loud 是 forward 模組
    職責；sink 對未知值保守跳過）。"""
    sink = mod.make_resolution_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("bogus", EID, CANONICAL)], 5_000)
    assert mod.list_records(ADDR, base_dir=str(tmp_path)) == []


def test_resolution_sink_missing_envelope_id_skipped(tmp_path):
    sink = mod.make_resolution_sink("s", base_dir=str(tmp_path))
    sink(ADDR, [_make_disp("auto", None, CANONICAL)], 5_000)
    assert mod.list_records(ADDR, base_dir=str(tmp_path)) == []


def test_received_survives_already_advanced_envelope(tmp_path, capsys):
    """重呈報（batch-dead ack 後重 prepare）的信可能已被推進
    handled／needs-human——received→現態 IllegalTransition 逐封吸收
    （stderr 大聲、帳面維持已處理真態），同批其餘信件記帳不中斷。"""
    mod.set(ADDR, "old-1", "received", session_id="s", now_us=1,
            base_dir=str(tmp_path))
    mod.set(ADDR, "old-1", "handled", session_id="s", now_us=2,
            base_dir=str(tmp_path))
    sink = mod.make_received_sink("s2", base_dir=str(tmp_path))
    sink(ADDR, [
        _make_disp("auto", "old-1", CANONICAL),
        _make_disp("surface", "fresh-2", CANONICAL),
    ], 5_000)
    err = capsys.readouterr().err
    assert "duty-disposition" in err and "old-1" in err
    assert mod.get(ADDR, "old-1", base_dir=str(tmp_path))[
        "state"
    ] == "handled"  # 維持真態，不被 received 蓋寫
    assert mod.get(ADDR, "fresh-2", base_dir=str(tmp_path))[
        "state"
    ] == "received"  # 同批他信記帳不中斷


# ── meta record（例外地址建立記錄落點）───────────────────────────────


def test_write_exception_address_record(tmp_path):
    mod.write_exception_address_record(
        "ai-guide-exceptions",
        {"alias": "ai-guide-exceptions", "addressId": "a9"},
        session_id="air-287", now_us=7, base_dir=str(tmp_path),
    )
    doc = json.loads(
        (tmp_path / "_meta" / "exception-address.json").read_text(
            encoding="utf-8"
        )
    )
    assert doc["kind"] == "exception-address-create"
    assert doc["alias"] == "ai-guide-exceptions"
    assert doc["result"]["addressId"] == "a9"
    assert doc["session_id"] == "air-287"
    # meta 不入任何 address 掃描
    assert mod.list_records("ai-guide-exceptions",
                            base_dir=str(tmp_path)) == []


# ── CLI 面 ───────────────────────────────────────────────────────────


def test_cli_set_get_list_exit_codes(tmp_path, capsys):
    base = str(tmp_path)
    assert mod.main([
        "set", "--address", ADDR, "--envelope-id", EID,
        "--state", "received", "--session-id", "s1",
        "--base-dir", base,
    ]) == 0
    assert mod.main([
        "get", "--address", ADDR, "--envelope-id", EID,
        "--base-dir", base,
    ]) == 0
    out = capsys.readouterr().out
    assert '"state": "received"' in out or '"state":"received"' in out
    assert mod.main([
        "list", "--address", ADDR, "--base-dir", base,
    ]) == 0
    assert EID in capsys.readouterr().out


def test_cli_typed_error_exit_1(tmp_path):
    assert mod.main([
        "get", "--address", ADDR, "--envelope-id", "missing",
        "--base-dir", str(tmp_path),
    ]) == 1


def test_cli_transition_violation_exit_1(tmp_path):
    base = str(tmp_path)
    mod.main([
        "set", "--address", ADDR, "--envelope-id", EID,
        "--state", "received", "--session-id", "s", "--base-dir", base,
    ])
    mod.main([
        "set", "--address", ADDR, "--envelope-id", EID,
        "--state", "handled", "--session-id", "s", "--base-dir", base,
    ])
    # handled 為終態——流轉表外轉移過 argparse、落 typed exit 1
    assert mod.main([
        "set", "--address", ADDR, "--envelope-id", EID,
        "--state", "processing", "--session-id", "s", "--base-dir", base,
    ]) == 1


def test_cli_unknown_state_exit_2_argparse():
    """state 選項 argparse choices 把關——misuse exit 2（house 慣例）。"""
    import pytest as _pytest

    with _pytest.raises(SystemExit) as exc:
        mod.main([
            "set", "--address", ADDR, "--envelope-id", EID,
            "--state", "bogus", "--session-id", "s",
        ])
    assert exc.value.code == 2


def test_cli_missing_required_arg_exit_2():
    with pytest.raises(SystemExit) as exc:
        mod.main(["set"])
    assert exc.value.code == 2
