"""exception forwarding 契約測試（AIR-287——db-99 裁定：needs-human→
exception mail（自帶原文＋來源連結）進專用 exception 地址）。

涵蓋：
- router（純函式、單元可測）：triage 分類 surface（＝needs-human 同義
  映射——db-99 裁定）→ forward；auto（digest 吸收）→ 不 forward。
  以真實 governance/dutymail-processor.toml 鎖映射（handoff+solicit
  →forward；usage-liveness+inform→不 forward）。
- envelope 組合：v2 凍結 grammar（schema_version 2／from 三鍵恆在、
  null 是值／delivery queue+solicit+wake none+fallback null）；body
  單行 JSON 自帶原文（original_body 逐字）＋來源連結（可執行查詢
  指針——dutymail 無 URL，正典先例＝duty_receive render F2）＋
  source_envelope_id；body ≤8192 bytes，超限＝BodyLimitExceeded
  fail-loud（禁靜默截斷）。
- send face：dutymail send --envelope-file（typed contract 單一源＝
  duty_receive._call）；acceptance 三鍵（envelopeId／acceptanceSeq／
  envelopeSha256）缺一＝shape-drift typed 錯誤。
- forward 端到端（fake runner）：needs-human 判定→send→acceptance
  回傳；auto 分類且未 force→不 send。
- init face（本卡唯一授權 dutymail write 面）：address create 經
  runner→建立記錄入 ledger meta；face 失敗＝typed 錯誤 exit 1。

測試全走 injectable runner——零真 store 往返（真實 address create＝
author 執行一次，輸出記錄入 ledger meta）。
"""

import json
import os
import stat
import textwrap
import threading
import time
import uuid

import pytest
from conftest import REPO_ROOT, load_module

mod = load_module("scripts/duty_exception_forward.py")
dd = load_module("scripts/duty_disposition.py")
duty_receive = load_module("scripts/duty_receive.py")

REAL_CONFIG = str(REPO_ROOT / "governance" / "dutymail-processor.toml")
SOURCE_ADDR = "ai-guide-marshal"
EXC_ADDR = "ai-guide-exceptions"


def _canonical(eid="018f-aaa", klass="handoff", intent="solicit",
               body=None):
    return {
        "schema_version": 2, "message_id": "m-" + eid, "envelope_id": eid,
        "from": {"session_id": "peer-1", "name": None, "harness": None},
        "to": {"address": SOURCE_ADDR},
        "delivery": {"mode": "queue", "fallback": None, "intent": intent,
                     "wake": "none", "fallback_used": False},
        "created_at_us": 1,
        "body": body if body is not None else json.dumps(
            {"class": klass, "task": "T-9"},
        ),
    }


def _policy():
    return duty_receive.load_policy(REAL_CONFIG)


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


# ── router（triage 映射——單元可測）───────────────────────────────────


def test_surface_maps_to_forward():
    item = {
        "envelopeId": "e-1",
        "canonicalEnvelope": json.dumps(_canonical()),
    }
    d = duty_receive.triage(item, _policy())
    assert d.action == "surface"
    assert mod.should_forward(d) is True


def test_auto_maps_to_no_forward():
    item = {
        "envelopeId": "e-2",
        "canonicalEnvelope": json.dumps(
            _canonical(eid="e-2", klass="usage-liveness", intent="inform")
        ),
    }
    d = duty_receive.triage(item, _policy())
    assert d.action == "auto"
    assert mod.should_forward(d) is False


def test_router_rejects_unknown_action():
    from types import SimpleNamespace

    d = SimpleNamespace(action="bogus", envelope_id="x")
    with pytest.raises(mod.LedgerError):
        mod.should_forward(d)


# ── envelope 組合（v2 grammar＋原文＋來源連結）───────────────────────


def test_compose_exception_envelope_grammar():
    canon = _canonical()
    env = mod.compose_exception_envelope(
        SOURCE_ADDR, canon, session_id="sess-9", now_us=5_000,
        uuid4=lambda: "018f-uuid-1",
    )
    assert env["schema_version"] == 2
    assert env["message_id"] == "018f-uuid-1"
    assert env["envelope_id"] == "018f-uuid-1"
    assert env["from"] == {
        "session_id": "sess-9", "name": None, "harness": None,
    }
    assert env["to"] == {"address": EXC_ADDR}
    assert env["delivery"] == {
        "mode": "queue", "fallback": None, "intent": "solicit",
        "wake": "none", "fallback_used": False,
    }
    assert env["created_at_us"] == 5_000
    assert "in_reply_to" not in env  # 缺席非 null（凍結 grammar）
    body = json.loads(env["body"])
    assert body["class"] == "exception-forward"  # 消費端約定標記
    assert body["source_address"] == SOURCE_ADDR
    assert body["source_envelope_id"] == "018f-aaa"
    # 來源連結＝可執行查詢指針（dutymail 無 URL——render F2 先例）
    assert body["source_query"] == (
        f"dutymail events --address {SOURCE_ADDR}"
    )
    # 自帶原文：original body 逐字
    assert body["original_body"] == canon["body"]
    assert env["body"].count("\n") == 0  # 單行 JSON


def test_compose_body_limit_fail_loud():
    big = "x" * 9000
    canon = _canonical(body=big)
    with pytest.raises(mod.BodyLimitExceeded):
        mod.compose_exception_envelope(
            SOURCE_ADDR, canon, session_id="s", now_us=1,
            uuid4=lambda: "u1",
        )


def test_compose_rejects_canonical_without_envelope_id():
    canon = _canonical()
    del canon["envelope_id"]
    with pytest.raises(mod.CompositionError):
        mod.compose_exception_envelope(
            SOURCE_ADDR, canon, session_id="s", now_us=1,
            uuid4=lambda: "u1",
        )


def test_compose_rejects_non_string_body():
    canon = _canonical(body={"class": "handoff"})  # body 須為字串（v2）
    with pytest.raises(mod.CompositionError):
        mod.compose_exception_envelope(
            SOURCE_ADDR, canon, session_id="s", now_us=1,
            uuid4=lambda: "u1",
        )


# ── send face（typed contract 單一源＝duty_receive._call）────────────
#
# 暫存檔契約（AIR-287 bi 修復——codex F2/GLM F2）：mkstemp 唯一暫存
# （兩程序同刻 send 不互蓋）＋0600（原文不落共用可讀路徑）＋成功失敗
# 皆清理（送畢零殘留——AIR-286 tmp 殘留教訓）。


def test_send_envelope_via_fake_runner(tmp_path):
    seen = {}

    def runner(argv):
        path = argv[argv.index("--envelope-file") + 1]
        seen["path"] = path
        seen["mode"] = stat.S_IMODE(os.stat(path).st_mode)
        with open(path, "r", encoding="utf-8") as fh:
            seen["sent"] = json.load(fh)
        return _ok({
            "envelopeId": "exc-1", "acceptanceSeq": 3,
            "envelopeSha256": "deadbeef",
        })

    env = mod.compose_exception_envelope(
        SOURCE_ADDR, _canonical(), session_id="s", now_us=1,
        uuid4=lambda: "u1",
    )
    acc = mod.send_envelope(runner, env, tmp_dir=str(tmp_path))
    assert acc == {
        "envelopeId": "exc-1", "acceptanceSeq": 3,
        "envelopeSha256": "deadbeef",
    }
    assert seen["sent"] == env
    # 唯一暫存＋0600：非固定共用名、原文不落群組可讀檔
    assert seen["path"] != str(tmp_path / "exception-envelope.json")
    assert seen["path"].startswith(str(tmp_path))
    assert seen["mode"] == 0o600
    # 成功後清理：暫存檔零殘留
    assert list(tmp_path.iterdir()) == []


def test_send_envelope_cleans_up_on_send_failure(tmp_path):
    def runner(argv):
        raise mod.duty_receive.DutymailFaceError(
            code="storage", error_class="storage", message="store down",
            retryable=True, exit_code=4,
        )

    env = mod.compose_exception_envelope(
        SOURCE_ADDR, _canonical(), session_id="s", now_us=1,
        uuid4=lambda: "u1",
    )
    with pytest.raises(mod.duty_receive.DutymailFaceError):
        mod.send_envelope(runner, env, tmp_dir=str(tmp_path))
    assert list(tmp_path.iterdir()) == []  # 失敗亦清理


def test_send_envelope_concurrent_no_clobber(tmp_path):
    """兩執行緒同刻 send（barrier 對齊＋runner 讀檔前停注）——各腿
    acceptance 必對應自己內容（唯一暫存＝不互蓋）、送畢零殘留。"""
    marker_body = {m: json.dumps({"marker": m}) for m in ("m1", "m2")}
    results = {}
    barrier = threading.Barrier(2)

    def leg(marker):
        def runner(argv):
            path = argv[argv.index("--envelope-file") + 1]
            barrier.wait()  # 兩腿同刻抵達 send 窗口
            time.sleep(0.05)  # 拉長重叠窗口——固定路徑必被對方覆蓋
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            return _ok({
                "envelopeId": doc["envelope_id"], "acceptanceSeq": 1,
                "envelopeSha256": doc["body"],
            })

        env = mod.compose_exception_envelope(
            SOURCE_ADDR,
            _canonical(eid=marker, body=marker_body[marker]),
            session_id=marker, now_us=1, uuid4=lambda: "u-" + marker,
        )
        results[marker] = mod.send_envelope(
            runner, env, tmp_dir=str(tmp_path)
        )

    threads = [threading.Thread(target=leg, args=(m,)) for m in ("m1", "m2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for m in ("m1", "m2"):
        # 各腿讀到的暫存檔＝自己內容（無跨腿互蓋）——acceptance sha 欄
        # 帶回 runner 讀到的 body；原文 marker 在組合 body 的內層。
        doc = json.loads(results[m]["envelopeSha256"])
        assert json.loads(doc["original_body"])["marker"] == m
        assert results[m]["envelopeId"] == "u-" + m
    assert list(tmp_path.iterdir()) == []


def test_send_envelope_two_processes_no_clobber(tmp_path):
    """兩程序同刻 forward 不互蓋（subprocess 驅動——mkstemp 唯一性是
    process-safe 性質，不止執行緒面）；父層斷言各程序 acceptance 全數
    對應自己 marker＋共享目錄送畢零殘留。"""
    import subprocess
    import sys

    driver = tmp_path / "_fwd_driver.py"
    driver.write_text(
        textwrap.dedent(
            """
            import importlib.util, json, sys, time
            from pathlib import Path
            spec = importlib.util.spec_from_file_location(
                "_fwd_driver",
                str(Path(sys.argv[1]) / "scripts"
                    / "duty_exception_forward.py"),
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            marker, shared = sys.argv[2], sys.argv[3]
            body = json.dumps({"marker": marker})
            env = {
                "schema_version": 2, "message_id": marker,
                "envelope_id": marker,
                "from": {"session_id": marker, "name": None,
                         "harness": None},
                "to": {"address": "ai-guide-exceptions"},
                "delivery": {"mode": "queue", "fallback": None,
                             "intent": "solicit", "wake": "none",
                             "fallback_used": False},
                "created_at_us": 1, "body": body,
            }
            seen = []

            def runner(argv):
                time.sleep(0.05)
                with open(argv[argv.index("--envelope-file") + 1],
                          encoding="utf-8") as fh:
                    seen.append(json.load(fh))
                return json.dumps({
                    "schemaVersion": 1, "ok": True,
                    "result": {"envelopeId": marker, "acceptanceSeq": 1,
                               "envelopeSha256": seen[-1]["body"]},
                })

            for _ in range(4):
                mod.send_envelope(runner, env, tmp_dir=shared)
            print(json.dumps({"marker": marker, "read_markers": [
                json.loads(s["body"])["marker"] for s in seen]}))
            """
        ),
        encoding="utf-8",
    )
    shared = tmp_path / "shared"
    shared.mkdir()
    procs = [
        subprocess.Popen(
            [sys.executable, str(driver), str(REPO_ROOT), m, str(shared)],
            stdout=subprocess.PIPE, text=True,
        )
        for m in ("pa", "pb")
    ]
    outs = [p.communicate()[0] for p in procs]
    assert all(p.returncode == 0 for p in procs)
    for line in outs:
        doc = json.loads(line)
        assert doc["read_markers"] == [doc["marker"]] * 4  # 全讀到自己
    assert list(shared.iterdir()) == []  # 兩程序送畢零殘留


def test_send_acceptance_shape_drift_typed(tmp_path):
    def runner(argv):
        return _ok({"unexpected": 1})  # acceptance 三鍵缺席

    env = mod.compose_exception_envelope(
        SOURCE_ADDR, _canonical(), session_id="s", now_us=1,
        uuid4=lambda: "u1",
    )
    # typed 類別須取 mod.duty_receive 實例（同檔案不同 instance——
    # except 面看後者；house 慣例同 test_duty_receive._hook_err）。
    with pytest.raises(mod.duty_receive.DutymailFaceError):
        mod.send_envelope(runner, env, tmp_dir=str(tmp_path))


# ── forward 端到端（fake runner；router 閘）──────────────────────────


def test_forward_sends_for_needs_human(tmp_path):
    def runner(argv):
        return _ok({
            "envelopeId": "exc-1", "acceptanceSeq": 1,
            "envelopeSha256": "aa",
        })

    decision, acc = mod.forward(
        SOURCE_ADDR, _canonical(), session_id="sess-9", runner=runner,
        policy=_policy(), now_us=1, tmp_dir=str(tmp_path),
        uuid4=lambda: "u1",
    )
    assert decision is True
    assert acc["envelopeId"] == "exc-1"


def test_forward_skips_auto_without_force(tmp_path):
    def runner(argv):  # 禁呼叫——auto 不 send
        raise AssertionError("send must not be called")

    decision, acc = mod.forward(
        SOURCE_ADDR,
        _canonical(eid="e-2", klass="usage-liveness", intent="inform"),
        session_id="s", runner=runner, policy=_policy(), now_us=1,
        tmp_dir=str(tmp_path), uuid4=lambda: "u1",
    )
    assert decision is False and acc is None


def test_forward_force_overrides_auto(tmp_path):
    def runner(argv):
        return _ok({
            "envelopeId": "exc-2", "acceptanceSeq": 1,
            "envelopeSha256": "bb",
        })

    decision, acc = mod.forward(
        SOURCE_ADDR,
        _canonical(eid="e-2", klass="usage-liveness", intent="inform"),
        session_id="s", runner=runner, policy=_policy(), now_us=1,
        force=True, tmp_dir=str(tmp_path), uuid4=lambda: "u1",
    )
    assert decision is True and acc["envelopeId"] == "exc-2"


# ── init face（本卡唯一授權 dutymail write 面）───────────────────────


def test_init_creates_address_and_records_meta(tmp_path):
    calls = []

    def runner(argv):
        calls.append(list(argv))
        return _ok({"alias": EXC_ADDR, "addressId": "a-9"})

    rc = mod.main([
        "init", "--alias", EXC_ADDR, "--session-id", "air-287",
        "--base-dir", str(tmp_path),
    ], runner=runner)
    assert rc == 0
    assert calls[0] == ["address", "create", "--alias", EXC_ADDR]
    doc = json.loads(
        (tmp_path / "_meta" / "exception-address.json").read_text(
            encoding="utf-8"
        )
    )
    assert doc["kind"] == "exception-address-create"
    assert doc["result"]["addressId"] == "a-9"


def test_init_face_failure_typed_exit_1(tmp_path, capsys):
    def runner(argv):
        raise mod.duty_receive.DutymailFaceError(
            code="alias-conflict", error_class="admission",
            message="alias exists", retryable=False, exit_code=3,
        )

    rc = mod.main([
        "init", "--alias", EXC_ADDR, "--session-id", "s",
        "--base-dir", str(tmp_path),
    ], runner=runner)
    assert rc == 1
    assert "alias-conflict" in capsys.readouterr().err


def test_init_meta_record_failure_fail_loud(tmp_path):
    """建立記錄入 ledger 失敗＝fail-loud exit 1（建立證據不可丟）。"""
    def runner(argv):
        return _ok({"alias": EXC_ADDR, "addressId": "a-9"})

    # base-dir 指到檔案上——meta 寫入必敗
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    rc = mod.main([
        "init", "--alias", EXC_ADDR, "--session-id", "s",
        "--base-dir", str(blocker),
    ], runner=runner)
    assert rc == 1


# ── CLI decision／forward 面 ─────────────────────────────────────────


def test_cli_decision_face(tmp_path, capsys):
    canon_file = tmp_path / "canonical.json"
    canon_file.write_text(json.dumps(_canonical()), encoding="utf-8")
    rc = mod.main([
        "decision", "--canonical-file", str(canon_file),
    ], policy_path=REAL_CONFIG)
    assert rc == 0
    out = capsys.readouterr().out
    assert '"forward": true' in out or '"forward":true' in out


def test_cli_forward_face_end_to_end(tmp_path, capsys):
    canon_file = tmp_path / "canonical.json"
    canon_file.write_text(json.dumps(_canonical()), encoding="utf-8")

    def runner(argv):
        return _ok({
            "envelopeId": "exc-9", "acceptanceSeq": 1,
            "envelopeSha256": "cc",
        })

    rc = mod.main([
        "forward", "--source-address", SOURCE_ADDR,
        "--canonical-file", str(canon_file),
        "--session-id", "sess-x",
        "--base-dir", str(tmp_path),  # 僅供 tmp 檔案面——非真 store
    ], runner=runner, policy_path=REAL_CONFIG)
    assert rc == 0
    assert "exc-9" in capsys.readouterr().out


def test_cli_args_misuse_exit_2():
    with pytest.raises(SystemExit) as exc:
        mod.main(["forward"])
    assert exc.value.code == 2


def test_uuid_injection_defaults_real():
    """預設 uuid4／now_us 為真值注入（非測試專用 stub）。"""
    env = mod.compose_exception_envelope(
        SOURCE_ADDR, _canonical(), session_id="s", now_us=None,
    )
    assert env["envelope_id"] == str(uuid.UUID(env["envelope_id"]))
    assert env["created_at_us"] > 0
