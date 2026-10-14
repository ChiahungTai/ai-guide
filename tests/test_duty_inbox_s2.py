"""AIR-312 S2 ordinary inbox — fake-runner risk tests (RED first).

Provenance: S (frozen EP ai-analysis/_tasks/air-312-mail-handle/ep.md S2
裁定 + task prompt mark-read/reply algorithms) + H (installed dutymail
3.11.0 stable-face probe shapes for mail list/get, send receipt,
prepare/ack). No legacy five-state/disposition oracle — S2 forbids them.

Scope: mark-read consumption fence + reply idempotency, all via
injectable runner + tmp state dir (zero true store). Real isolated-store
e2e lives in tests/test_duty_inbox_s2_e2e.py.
"""

import hashlib
import json
import os
import threading
import time

import pytest

from conftest import load_module

mod = load_module("scripts/duty_receive.py")

ADDR = "s2probe"


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


def _face_error(code, error_class, message="boom"):
    return mod.DutymailFaceError(
        code=code, error_class=error_class, message=message,
        retryable=False, exit_code=3,
    )


def _seq_runner(steps):
    calls = []

    def run(argv):
        calls.append(list(argv))
        if len(calls) > len(steps):
            raise AssertionError("unexpected call: " + repr(argv))
        step = steps[len(calls) - 1]
        if isinstance(step, Exception):
            raise step
        return step

    run.calls = calls
    return run


def _canon(eid, body="hello plain", seq=1):
    env = {
        "schema_version": 2,
        "message_id": "11111111-1111-4111-8111-111111111111",
        "envelope_id": eid,
        "from": {"session_id": "s1", "name": None, "harness": None},
        "to": {"address": ADDR},
        "delivery": {"mode": "queue", "fallback": None, "intent": "inform",
                     "wake": "none", "fallback_used": False},
        "created_at_us": 1000000,
        "body": body,
    }
    return json.dumps(env, ensure_ascii=False)


def _mail_item(eid, body="hello plain", pending=True, seq=1,
               payload="present", canon=None):
    return {
        "acceptanceSeq": seq, "acceptedAtUs": 2000000,
        "canonicalEnvelope": canon if canon is not None else _canon(eid, body),
        "deliverySeq": seq, "envelopeId": eid, "exportRef": None,
        "payloadState": payload, "pending": pending,
    }


def _mail_get_doc(eid, **kw):
    return _ok({"addressId": "a1", "alias": ADDR, "primaryCursor": 0,
                "item": _mail_item(eid, **kw)})


def _status_doc(epoch=0, bound=False):
    return _ok({"addressId": "a1", "alias": ADDR, "bindingEpoch": epoch,
                "bound": bound, "role": "consume"})


def _bind_doc(epoch=1, token="tok-1"):
    return _ok({"addressId": "a1", "alias": ADDR, "bindingEpoch": epoch,
                "holderToken": token, "role": "consume"})


def _prepare_doc(eid, batch="bt-1"):
    return _ok({"addressId": "a1", "batchToken": batch, "fromSeq": 1,
                "throughSeq": 1, "expiresAtUs": 999,
                "envelopes": [{"envelopeId": eid, "acceptanceSeq": 1,
                               "canonicalEnvelope": _canon(eid)}]})


def _ack_doc():
    return _ok({"addressId": "a1", "receiptId": "r-1", "fromSeq": 1,
                "throughSeq": 1, "ackedAtUs": 999, "replayed": False})


def _release_doc():
    return _ok({"addressId": "a1", "bindingEpoch": 1, "fencedBatches": 0,
                "releasedAtUs": 999, "role": "consume"})


def _send_doc(eid, seq=2, sha="a" * 64):
    return _ok({"acceptanceSeq": seq, "addressId": "a1", "deliverySeq": 2,
                "envelopeId": eid, "envelopeSha256": sha, "replayed": False,
                "storeId": "s1"})


def _write_draft(path, envelope_id="out-1", in_reply_to="env-1",
                 to_addr=ADDR, extra=None):
    doc = {
        "schema_version": 2,
        "message_id": "22222222-2222-4222-8222-222222222222",
        "envelope_id": envelope_id,
        "from": {"session_id": "s9", "name": None, "harness": None},
        "to": {"address": to_addr},
        "delivery": {"mode": "queue", "fallback": None, "intent": "inform",
                     "wake": "none", "fallback_used": False},
        "created_at_us": 3000000,
        "body": "reply body plain",
    }
    if in_reply_to is not None:
        doc["in_reply_to"] = in_reply_to
    if extra:
        doc.update(extra)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    return path


def test_pending_write_failure_consumes_nothing(tmp_path, monkeypatch):
    """Pending persistence fails => zero prepare/ack (no transport cursor)."""
    assert hasattr(mod, "mark_read"), "S2 mark_read API missing (RED)"
    runner = _seq_runner([_mail_get_doc("env-1")])

    def _boom(path, doc):
        raise OSError("disk full (injected)")

    monkeypatch.setattr(mod, "save_pending_replies", _boom)
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-1", runner,
                      state_dir=str(tmp_path), note="reply me",
                      target="peer-x")
    faces = [c[0] for c in runner.calls]
    assert "receive" not in faces
    assert "holder" not in faces


def test_prefix_mismatch_no_ack_no_skip(tmp_path):
    """Prepare head != read ID => no ACK, pending retained, nonzero."""
    runner = _seq_runner([
        _mail_get_doc("env-want"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-other"),
        _release_doc(),
    ])
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-want", runner, state_dir=str(tmp_path))
    assert not any(c[:2] == ["receive", "ack"] for c in runner.calls)
    pend = mod.load_pending_replies(mod.pending_path(ADDR, str(tmp_path)))
    assert pend is not None


def test_active_holder_no_bind_no_steal(tmp_path):
    """Live holder in place => refuse, no bind call, pending retained."""
    assert hasattr(mod, "mark_read"), "S2 mark_read API missing (RED)"
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(3, True),
    ])
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path),
                      note="n", target="t")
    assert not any(c[:2] == ["holder", "bind"] for c in runner.calls)
    assert not any(c[0] == "receive" for c in runner.calls)


def test_prepare_failure_retains_pending_and_releases(tmp_path):
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _face_error("x", "storage"),
        _release_doc(),
    ])
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    assert any(c[:2] == ["holder", "release"] for c in runner.calls)


def test_ack_failure_retains_pending(tmp_path):
    """ACK 錯誤＝outcome unknown（F3/R2-CX03）：release 後唯讀重查——
    仍 pending ⇒ 報「ACK 結果未知（response-loss）」，禁宣稱 cursor
    未前進；pending 義務保留。"""
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _face_error("ack-bad", "storage"),
        _release_doc(),
        _mail_get_doc("env-1", pending=True),
    ])
    with pytest.raises(mod.S2Error, match="ACK 結果未知"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    pend = mod.load_pending_replies(mod.pending_path(ADDR, str(tmp_path)))
    assert pend is not None


def test_release_failure_is_nonzero_and_retains(tmp_path):
    assert hasattr(mod, "mark_read"), "S2 mark_read API missing (RED)"
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _ack_doc(),
        _face_error("rel-bad", "storage"),
    ])
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))


def test_stale_own_token_fenced_clears_without_steal(tmp_path):
    """Persisted own token fenced => clear stale file, no bind, retry later."""
    st = str(tmp_path)
    mod.save_pending_replies(mod.pending_path(ADDR, st),
                             {"address": ADDR, "replies": {}})
    with open(mod.inbox_holder_path(ADDR, st), "w", encoding="utf-8") as fh:
        json.dump({"address": ADDR, "epoch": 1, "token": "tok-old",
                   "bound_at_iso": "2026-01-01T00:00:00+00:00"}, fh)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("holder-token-mismatch", "fencing"),
    ])
    with pytest.raises(Exception):
        mod.mark_read(ADDR, "env-1", runner, state_dir=st)
    assert not os.path.exists(mod.inbox_holder_path(ADDR, st))
    assert not any(c[:2] == ["holder", "bind"] for c in runner.calls)


def test_exported_body_absent_no_consume(tmp_path):
    item = _mail_item("env-1", pending=True, payload="exported", canon=None)
    item["canonicalEnvelope"] = None
    item["exportRef"] = "s3://x"
    runner = _seq_runner([
        _ok({"addressId": "a1", "alias": ADDR, "primaryCursor": 0,
             "item": item}),
    ])
    with pytest.raises(Exception, match="(?i)absent|export"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    assert len(runner.calls) == 1


def test_unslotted_row_no_consume(tmp_path):
    item = _mail_item("env-1", pending=None)
    item["deliverySeq"] = None
    runner = _seq_runner([
        _ok({"addressId": "a1", "alias": ADDR, "primaryCursor": 0,
             "item": item}),
    ])
    with pytest.raises(Exception, match="(?i)unslotted|deliverySeq"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    assert len(runner.calls) == 1


def test_plain_body_survives_intact():
    item = _mail_item("env-1", body="hello plain world — no JSON here")
    env, absence = mod.decode_canonical_item(item)
    assert absence is None
    assert env["body"] == "hello plain world — no JSON here"


def test_long_body_survives_intact():
    long_body = "x" * 20000 + "尾"
    item = _mail_item("env-1", body=long_body)
    env, absence = mod.decode_canonical_item(item)
    assert env["body"] == long_body


def test_cross_repo_state_isolation(tmp_path):
    mod.save_pending_replies(mod.pending_path("repo-a", str(tmp_path)),
                             {"address": "repo-a",
                              "replies": {"e1": {"note": "n", "target": "t"}}})
    got = mod.load_pending_replies(mod.pending_path("repo-b", str(tmp_path)))
    assert got is None or got.get("replies", {}) == {}


def test_mark_read_uses_single_prefix_prepare(tmp_path, monkeypatch):
    """No legacy recovery path: prepare max-count must be exactly 1."""
    if hasattr(mod, "_prepare_with_recovery"):
        monkeypatch.setattr(
            mod, "_prepare_with_recovery",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("legacy recovery must not run")),
        )
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _ack_doc(),
        _release_doc(),
    ])
    mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    preps = [c for c in runner.calls if c[:2] == ["receive", "prepare"]]
    assert len(preps) == 1
    assert "--max-count" in preps[0]
    assert preps[0][preps[0].index("--max-count") + 1] == "1"


def test_send_failure_retains_pending(tmp_path):
    st = str(tmp_path)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": ADDR}}})
    draft = _write_draft(str(tmp_path / "out.json"), in_reply_to="env-1",
                         to_addr=ADDR)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("store-down", "storage"),
    ])
    with pytest.raises(Exception):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert "env-1" in kept["replies"]


def test_mismatched_receipt_retains_pending(tmp_path):
    st = str(tmp_path)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": ADDR}}})
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _send_doc("out-OTHER"),
    ])
    with pytest.raises(Exception):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert "env-1" in kept["replies"]


def test_success_before_clear_retry_same_id_and_bytes(tmp_path, monkeypatch):
    st = str(tmp_path)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": ADDR}}})
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        pinned_sha = hashlib.sha256(fh.read()).hexdigest()
    runner1 = _seq_runner([_mail_get_doc("env-1"), _send_doc("out-1")])
    monkeypatch.setattr(
        mod, "_pending_clear_reply", lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("crash before clear (injected)")))
    with pytest.raises(RuntimeError, match="crash before clear"):
        mod.send_reply(ADDR, "env-1", draft, runner1, state_dir=st)
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert kept["replies"]["env-1"]["reply_envelope_id"] == "out-1"
    assert kept["replies"]["env-1"]["reply_sha256"] == pinned_sha
    monkeypatch.undo()
    runner2 = _seq_runner([_mail_get_doc("env-1"), _send_doc("out-1")])
    out = mod.send_reply(ADDR, "env-1", draft, runner2, state_dir=st)
    assert out["cleared"] is True


def test_changed_draft_bytes_rejected(tmp_path):
    st = str(tmp_path)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        pinned_sha = hashlib.sha256(fh.read()).hexdigest()
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {
            "note": "n", "target": ADDR, "reply_envelope_id": "out-1",
            "reply_sha256": pinned_sha}}})
    with open(draft, "w", encoding="utf-8") as fh:
        fh.write('{"tampered": true}')
    runner = _seq_runner([_mail_get_doc("env-1")])
    with pytest.raises(Exception, match="(?i)changed|bytes|sha"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert len(runner.calls) == 1


def test_already_acked_reread_consumes_nothing(tmp_path):
    runner = _seq_runner([_mail_get_doc("env-1", pending=False)])
    out = mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    assert out["acked"] is False
    assert all(c[0] not in ("receive", "holder") or c[1] in ("status",)
               for c in runner.calls)
    assert not any(c[:2] == ["receive", "prepare"] for c in runner.calls)
    assert not any(c[:2] == ["receive", "ack"] for c in runner.calls)


def test_no_note_read_never_clears_obligation(tmp_path):
    st = str(tmp_path)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": "t"}}})
    runner = _seq_runner([
        _ok({"addressId": "a1", "alias": ADDR, "primaryCursor": 1,
             "item": _mail_item("env-1", pending=False)}),
    ])
    mod.mark_read(ADDR, "env-1", runner, state_dir=st)
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert "env-1" in kept["replies"]


# ── R2 修正（F1–F5、F10——marshal 裁定採納）────────────────────────────


def test_ack_error_requery_committed_response_loss(tmp_path):
    """F3/R2-CX03：ACK 錯誤但唯讀重查 pending=False ⇒ committed
    （acked=True＋response-loss 標記），非錯誤；holder 已清。"""
    st = str(tmp_path)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _face_error("ack-bad", "storage"),
        _release_doc(),
        _mail_get_doc("env-1", pending=False),
    ])
    out = mod.mark_read(ADDR, "env-1", runner, state_dir=st)
    assert out["acked"] is True
    assert out["ack_outcome"] == "committed"
    assert out["ack_response_loss"] is True
    assert not os.path.exists(mod.inbox_holder_path(ADDR, st))


def test_ack_error_requery_itself_fails_reports_unknown(tmp_path):
    """F3：重查本身失敗 ⇒ unknown＋重查錯誤揭露。"""
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _face_error("ack-bad", "storage"),
        _release_doc(),
        _face_error("store-down", "storage"),
    ])
    with pytest.raises(mod.S2Error, match="重查失敗"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))


def test_mark_read_id_echo_mismatch_no_state_change(tmp_path):
    """F10/R2-TEST02：mail get 回應 envelopeId 與查詢不符 ⇒ S2Error、
    零 holder/prepare/ack（與 send_reply incoming 檢查對稱）。"""
    runner = _seq_runner([
        _ok({"addressId": "a1", "alias": ADDR, "primaryCursor": 0,
             "item": _mail_item("env-OTHER", pending=True)}),
    ])
    with pytest.raises(mod.S2Error, match="ID 不符"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    assert len(runner.calls) == 1
    assert not os.path.exists(
        mod.inbox_holder_path(ADDR, str(tmp_path)))


def test_reread_clears_stale_own_holder_without_reconsuming(tmp_path):
    """F4/R2-CX04：ACK 成功＋release 失敗 ⇒ holder 殘留；第二次同 ID
    mark-read（已 ACK 重看）短路前清殘留 holder，不重 ACK/prepare/bind。"""
    st = str(tmp_path)
    runner1 = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _ack_doc(),
        _face_error("rel-bad", "storage"),
    ])
    with pytest.raises(mod.S2Error, match="release 失敗"):
        mod.mark_read(ADDR, "env-1", runner1, state_dir=st)
    assert os.path.exists(mod.inbox_holder_path(ADDR, st))
    runner2 = _seq_runner([
        _mail_get_doc("env-1", pending=False),
        _release_doc(),
    ])
    out = mod.mark_read(ADDR, "env-1", runner2, state_dir=st)
    assert out["acked"] is False
    assert out["reread"] is True
    assert out["released_stale_holder"] is True
    assert not os.path.exists(mod.inbox_holder_path(ADDR, st))
    assert not any(c[:2] == ["receive", "prepare"] for c in runner2.calls)
    assert not any(c[:2] == ["receive", "ack"] for c in runner2.calls)
    assert not any(c[:2] == ["holder", "bind"] for c in runner2.calls)


def test_reread_stale_holder_release_failure_kept_and_disclosed(tmp_path):
    """F4 對照：殘留 holder release 失敗 ⇒ 檔案保留＋訊息揭露，重看
    本身照常成功（唯讀不受殘留牽連）。"""
    st = str(tmp_path)
    mod._save_inbox_holder(ADDR, st, 1, "tok-stale")
    runner = _seq_runner([
        _mail_get_doc("env-1", pending=False),
        _face_error("rel-bad", "storage"),
    ])
    out = mod.mark_read(ADDR, "env-1", runner, state_dir=st)
    assert out["acked"] is False
    assert out["released_stale_holder"] is False
    assert "tok-stale" in out["stale_holder_note"]
    assert os.path.exists(mod.inbox_holder_path(ADDR, st))


def test_holder_save_failure_release_fail_discloses_token(
        tmp_path, monkeypatch):
    """F2/R2-CX02：存 token 失敗且 release 亦失敗 ⇒ 訊息含完整 token
    （人工恢復證據）、不宣稱已釋放。"""

    def _boom(address, state_dir, epoch, token):
        raise OSError("disk full (injected)")

    monkeypatch.setattr(mod, "_save_inbox_holder", _boom)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _face_error("rel-bad", "storage"),
    ])
    with pytest.raises(mod.S2Error) as excinfo:
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))
    msg = str(excinfo.value)
    assert "tok-1" in msg
    assert "release 亦失敗" in msg
    assert "已釋放" not in msg


def test_holder_save_failure_release_ok_keeps_honest_message(
        tmp_path, monkeypatch):
    """F2 對照：release 成功 ⇒ 維持「已釋放」訊息（既有行為回歸）。"""

    def _boom(address, state_dir, epoch, token):
        raise OSError("disk full (injected)")

    monkeypatch.setattr(mod, "_save_inbox_holder", _boom)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _release_doc(),
    ])
    with pytest.raises(mod.S2Error, match="已釋放剛取得的 token"):
        mod.mark_read(ADDR, "env-1", runner, state_dir=str(tmp_path))


def test_concurrent_mark_read_serialized_under_pending_lock(tmp_path):
    """F1/R2-CX01：同 repo 兩執行緒 mark_read——holder/prepare/ack 消費
    段在 `_pending_lock` 內序列化（每 thread 的 transport 呼叫成連續塊、
    token 不交錯）。fcntl flock 跨執行緒（各自 os.open fd）互斥。"""
    st = str(tmp_path)

    class _FakeStore:
        """狀態型 fake store：bind 遞增 epoch／token、release 清 bound
        ；status/prepare 各帶 sleep 擴大交錯窗口（驗證序列化用）。"""

        def __init__(self):
            self.lock = threading.Lock()
            self.epoch = 0
            self.bound = False
            self.tokens = {}
            self.calls = []

        def run(self, argv):
            key = tuple(argv[:2])
            if key == ("holder", "status"):
                time.sleep(0.05)
                with self.lock:
                    self.calls.append((threading.get_ident(), list(argv)))
                    doc = {"addressId": "a1", "alias": ADDR,
                           "bindingEpoch": self.epoch,
                           "bound": self.bound, "role": "consume"}
                return _ok(doc)
            with self.lock:
                self.calls.append((threading.get_ident(), list(argv)))
            if key == ("holder", "bind"):
                with self.lock:
                    self.epoch += 1
                    self.bound = True
                    token = f"tok-{self.epoch}"
                    self.tokens[threading.get_ident()] = token
                    epoch = self.epoch
                return _ok({"addressId": "a1", "alias": ADDR,
                            "bindingEpoch": epoch, "holderToken": token,
                            "role": "consume"})
            if key == ("receive", "prepare"):
                time.sleep(0.12)
                return _prepare_doc("env-1")
            if key == ("receive", "ack"):
                return _ack_doc()
            if key == ("holder", "release"):
                with self.lock:
                    self.bound = False
                return _release_doc()
            if key == ("mail", "get"):
                return _mail_get_doc("env-1")
            raise AssertionError("unexpected: " + repr(argv))

    store = _FakeStore()
    errs = []

    def _work():
        try:
            mod.mark_read(ADDR, "env-1", store.run, state_dir=st)
        except Exception as exc:  # 測試收集面——兩執行緒皆須成功
            errs.append(exc)

    threads = [threading.Thread(target=_work) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert errs == [], f"並行 mark_read 失敗：{errs!r}"

    # 消費段（status/bind/prepare/ack/release）必須成兩個連續 per-thread
    # 塊（mail get 在鎖外，排除後看序列）。
    tail = [tid for tid, argv in store.calls
            if tuple(argv[:2]) != ("mail", "get")]
    blocks = 1 + sum(
        1 for i in range(1, len(tail)) if tail[i] != tail[i - 1])
    assert blocks == 2, f"消費段交錯：{tail!r}"
    # token 不交錯：每 thread 恰一 bind／一 prepare，prepare token＝
    # 自己 bind 的 token。
    for tid in {tid for tid, _ in store.calls}:
        mine = [argv for t, argv in store.calls if t == tid]
        binds = [a for a in mine if a[:2] == ["holder", "bind"]]
        preps = [a for a in mine if a[:2] == ["receive", "prepare"]]
        assert len(binds) == 1, f"bind 數異常：{mine!r}"
        assert len(preps) == 1, f"prepare 數異常：{mine!r}"
        assert preps[0][preps[0].index("--token") + 1] == store.tokens[tid]


def _snapshot_path(st, envelope_id="out-1"):
    return os.path.join(
        st, "repos", mod.safe_repo_dirname(ADDR), "outbox",
        mod.safe_repo_dirname(envelope_id) + ".json")


def test_send_uses_validated_snapshot_not_mutable_draft(tmp_path):
    """F5/R2-RP01：send 一律以 validated snapshot 發送——驗證後呼叫端
    draft 檔被改（TOCTOU）不影響送出內容；成功清 pending＋snapshot。"""
    st = str(tmp_path / "state")
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        original = fh.read()
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": ADDR}}})

    seen = {}

    def runner(argv):
        if argv[:2] == ["mail", "get"]:
            return _mail_get_doc("env-1")
        assert argv[0] == "send"
        # 攔截：送達 runner 時篡改呼叫端 draft 檔（模擬驗證後 TOCTOU）
        with open(draft, "w", encoding="utf-8") as fh:
            fh.write('{"tampered": true}')
        seen["path"] = argv[2]
        with open(argv[2], "rb") as fh:
            seen["bytes"] = fh.read()
        return _send_doc("out-1")

    out = mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert out["cleared"] is True
    assert seen["path"] != draft
    assert seen["bytes"] == original
    assert not os.path.exists(_snapshot_path(st)), "成功後 snapshot 應清除"
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert kept is None or "env-1" not in kept.get("replies", {})


def test_send_retry_after_transport_failure_sends_snapshot(tmp_path):
    """F5：首次 send transport 失敗 ⇒ pin＋snapshot 保留；重試以同
    draft 發送，實際送出內容讀 snapshot（原 validated bytes）。"""
    st = str(tmp_path / "state")
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        original = fh.read()
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {"note": "n", "target": ADDR}}})

    def runner_fail(argv):
        if argv[:2] == ["mail", "get"]:
            return _mail_get_doc("env-1")
        raise _face_error("store-down", "storage")

    with pytest.raises(mod.S2Error):
        mod.send_reply(ADDR, "env-1", draft, runner_fail, state_dir=st)
    snap = _snapshot_path(st)
    assert os.path.exists(snap)
    with open(snap, "rb") as fh:
        assert fh.read() == original
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert kept["replies"]["env-1"]["reply_sha256"] == hashlib.sha256(
        original).hexdigest()

    seen = {}

    def runner_ok(argv):
        if argv[:2] == ["mail", "get"]:
            return _mail_get_doc("env-1")
        with open(argv[2], "rb") as fh:
            seen["bytes"] = fh.read()
        return _send_doc("out-1")

    out = mod.send_reply(ADDR, "env-1", draft, runner_ok, state_dir=st)
    assert out["cleared"] is True
    assert seen["bytes"] == original
    assert not os.path.exists(snap)


def test_send_corrupt_snapshot_refuses_retry(tmp_path):
    """F5：snapshot 損壞（SHA 對不上 pin）＝fail-loud 禁發（零 send
    呼叫）。"""
    st = str(tmp_path / "state")
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        pinned_sha = hashlib.sha256(fh.read()).hexdigest()
    os.makedirs(os.path.dirname(_snapshot_path(st)), exist_ok=True)
    with open(_snapshot_path(st), "wb") as fh:
        fh.write(b'{"corrupted": true}')
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {
            "note": "n", "target": ADDR,
            "reply_envelope_id": "out-1", "reply_sha256": pinned_sha}}})
    runner = _seq_runner([_mail_get_doc("env-1")])
    with pytest.raises(mod.S2Error, match="snapshot 損壞"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert not any(c[0] == "send" for c in runner.calls)


def test_send_missing_snapshot_refuses_retry(tmp_path):
    """F5：snapshot 缺席（如修前 pin 的遺留）＝fail-loud 禁發。"""
    st = str(tmp_path / "state")
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1", to_addr=ADDR)
    with open(draft, "rb") as fh:
        pinned_sha = hashlib.sha256(fh.read()).hexdigest()
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {"env-1": {
            "note": "n", "target": ADDR,
            "reply_envelope_id": "out-1", "reply_sha256": pinned_sha}}})
    runner = _seq_runner([_mail_get_doc("env-1")])
    with pytest.raises(mod.S2Error, match="snapshot 缺席"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert not any(c[0] == "send" for c in runner.calls)


# ── AIR-336：確定性 envelope schema 拒收解 pin（codex §6 測試矩陣）────
#
# Producer typed contract（真 binary probe 實證 2026-10-14）：缺
# message_id 的 envelope → stderr JSON {"code": "invalid-envelope",
# "class": "usage", "retryable": false}、exit 2、store 零受理
# （parse_strict 在 store acceptance 前）。


def _seed_pending(st, incoming="env-1", pinned_id=None, pinned_sha=None):
    entry = {"note": "n", "target": ADDR}
    if pinned_id is not None:
        entry["reply_envelope_id"] = pinned_id
    if pinned_sha is not None:
        entry["reply_sha256"] = pinned_sha
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {incoming: entry}})


def _entry(st, incoming="env-1"):
    doc = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert doc is not None, "pending 檔不該缺席"
    return doc["replies"][incoming]


def _draft_without_message_id(path, **kw):
    """_write_draft 建合法 envelope 後移除 message_id——producer
    parse_strict 必拒（invalid-envelope: missing field）。wrapper 端
    欄位驗證（envelope_id/in_reply_to/to.address）不含 message_id，
    恰好模擬「wrapper 放行、store schema 拒收」的真實死鎖輸入。"""
    _write_draft(path, **kw)
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    doc.pop("message_id")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    return path


def _file_sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_t1_schema_refusal_clears_pin_keeps_pending(tmp_path):
    """T1：draft 缺 message_id，send 回 invalid-envelope(usage) ⇒
    pending 存在、兩 pin 為 null、snapshot 清除。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _draft_without_message_id(
        str(tmp_path / "out.json"), envelope_id="out-1", in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error, match="schema 拒收") as ei:
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert "修正 draft 後可重新授權寄送" in str(ei.value)
    entry = _entry(st)
    assert entry["reply_envelope_id"] is None
    assert entry["reply_sha256"] is None
    assert entry["note"] == "n" and entry["target"] == ADDR
    assert not os.path.exists(_snapshot_path(st)), "snapshot 應已清除"


def test_t2_fixed_draft_resend_full_flow_no_state_surgery(tmp_path):
    """T2（核心 regression，T1→T2 完整鏈）：修正 draft 後同一 incoming
    重新 send_reply ⇒ 成功寄送、receipt 合法、pending 解除——全程僅
    呼叫 send_reply，零 state 檔手術。"""
    st = str(tmp_path)
    _seed_pending(st)
    bad_draft = _draft_without_message_id(
        str(tmp_path / "out.json"), envelope_id="out-1", in_reply_to="env-1")
    runner1 = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error, match="schema 拒收"):
        mod.send_reply(ADDR, "env-1", bad_draft, runner1, state_dir=st)
    # 修正 draft：補回 message_id（_write_draft 整檔重寫＝合法 envelope）。
    good_draft = _write_draft(
        bad_draft, envelope_id="out-1", in_reply_to="env-1")
    runner2 = _seq_runner([_mail_get_doc("env-1"), _send_doc("out-1")])
    out = mod.send_reply(ADDR, "env-1", good_draft, runner2, state_dir=st)
    assert out["cleared"] is True
    assert out["receipt"]["envelopeId"] == "out-1"
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert kept is None or "env-1" not in kept.get("replies", {})
    assert not os.path.exists(_snapshot_path(st))


def test_t3_unsupported_schema_refusal_also_clears_pin(tmp_path):
    """T3：unsupported-envelope-schema(usage) 與 T1 同樣解除 pin。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _draft_without_message_id(
        str(tmp_path / "out.json"), envelope_id="out-1", in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("unsupported-envelope-schema", "usage"),
    ])
    with pytest.raises(mod.S2Error, match="schema 拒收"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] is None
    assert entry["reply_sha256"] is None
    assert not os.path.exists(_snapshot_path(st))


def test_t4_storage_error_retains_pin_and_snapshot(tmp_path):
    """T4：store-down(storage) ⇒ pin/snapshot 完整保留（outcome 未確認
    保守路徑）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("store-down", "storage"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)
    with open(_snapshot_path(st), "rb") as fh, open(draft, "rb") as fh2:
        assert fh.read() == fh2.read()


def test_t5_after_storage_error_changed_draft_sha_rejected_zero_send(
        tmp_path):
    """T5：T4 後修改 draft ⇒ SHA 拒絕、零 send 呼叫。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner1 = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("store-down", "storage"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner1, state_dir=st)
    with open(draft, "w", encoding="utf-8") as fh:
        json.dump({"envelope_id": "out-1", "in_reply_to": "env-1",
                   "tampered": True}, fh)
    runner2 = _seq_runner([_mail_get_doc("env-1")])
    with pytest.raises(mod.S2Error, match="bytes 已變更|SHA 不符"):
        mod.send_reply(ADDR, "env-1", draft, runner2, state_dir=st)
    assert not any(c[0] == "send" for c in runner2.calls)


def test_t6_after_storage_error_same_bytes_retry_sends_snapshot(tmp_path):
    """T6：T4 後原 bytes 重試 ⇒ 使用原 snapshot 發送並清 pending。"""
    st = str(tmp_path / "state")
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    with open(draft, "rb") as fh:
        original = fh.read()
    runner1 = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("store-down", "storage"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner1, state_dir=st)
    seen = {}

    def runner_ok(argv):
        if argv[:2] == ["mail", "get"]:
            return _mail_get_doc("env-1")
        seen["path"] = argv[2]
        with open(argv[2], "rb") as fh:
            seen["bytes"] = fh.read()
        return _send_doc("out-1")

    out = mod.send_reply(ADDR, "env-1", draft, runner_ok, state_dir=st)
    assert out["cleared"] is True
    assert seen["path"] != draft
    assert seen["bytes"] == original
    assert not os.path.exists(_snapshot_path(st))


def test_t7_unknown_address_admission_retains_pin(tmp_path):
    """T7：unknown-address(admission) ⇒ pin 保留。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("unknown-address", "admission"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)


def test_t8_idempotency_conflict_admission_retains_pin(tmp_path):
    """T8：idempotency-conflict(admission) ⇒ pin 保留（不可重試≠確定
    未受理——解 pin 換 ID 會增加重複發信風險）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("idempotency-conflict", "admission"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)


def test_t9_other_usage_or_unknown_errors_retain_pin(tmp_path):
    """T9：其他 usage code（非 schema 二碼）或未知錯誤 ⇒ pin 保留
    （error_class 單獨不構成解 pin 條件）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("usage", "usage"),
        _mail_get_doc("env-1"),
        _face_error("unknown", "unknown"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)


def test_t10_invalid_envelope_retryable_true_retains_pin(tmp_path):
    """T10：invalid-envelope 但 retryable=True ⇒ pin 保留（predicate
    要求 retryable is False）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    retryable_exc = mod.DutymailFaceError(
        code="invalid-envelope", error_class="usage", message="boom",
        retryable=True, exit_code=2)
    runner = _seq_runner([_mail_get_doc("env-1"), retryable_exc])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)


def test_t11_pin_clear_save_oserror_keeps_old_pin_and_snapshot(
        tmp_path, monkeypatch):
    """T11：解 pin 的 save_pending OSError ⇒ fail-loud；原 pin＋
    snapshot 保留（持久化失敗＝狀態不動）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    real_save = mod.save_pending_replies
    calls = {"n": 0}

    def _flaky_save(path, doc):
        calls["n"] += 1
        if calls["n"] >= 2:  # 第 1 次＝send 前 pin 寫入；第 2 次＝解 pin
            raise OSError("disk full (injected)")
        return real_save(path, doc)

    monkeypatch.setattr(mod, "save_pending_replies", _flaky_save)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error, match="持久化失敗"):
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert calls["n"] == 2
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)
    assert os.path.exists(_snapshot_path(st))


def test_t12_snapshot_removal_oserror_pins_cleared_orphan_disclosed(
        tmp_path, monkeypatch):
    """T12：解 pin 成功後刪 snapshot OSError ⇒ pending 保留（pin 已
    null）、揭露 orphan snapshot（禁宣稱完整清理）。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    snap = _snapshot_path(st)
    real_remove = os.remove

    def _boom_remove(p, *args, **kwargs):
        if os.path.abspath(p) == os.path.abspath(snap):
            raise OSError("disk full (injected)")
        return real_remove(p, *args, **kwargs)

    monkeypatch.setattr(mod.os, "remove", _boom_remove)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error, match="schema 拒收") as ei:
        mod.send_reply(ADDR, "env-1", draft, runner, state_dir=st)
    assert "殘留 snapshot 清理失敗" in str(ei.value)
    entry = _entry(st)
    assert entry["reply_envelope_id"] is None
    assert entry["reply_sha256"] is None
    assert os.path.exists(snap), "orphan snapshot 應保留並揭露"


def test_t13_acked_reread_note_update_keeps_pin_zero_send(tmp_path):
    """T13：已 ACK mark-read 重看、更新 note ⇒ 原 pin 不變、零 send
    （reread setdefault 保守語義——response-loss 去重保障）。"""
    st = str(tmp_path)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    sha = _file_sha(draft)
    _seed_pending(st, pinned_id="out-1", pinned_sha=sha)
    runner = _seq_runner([_mail_get_doc("env-1", pending=False)])
    out = mod.mark_read(ADDR, "env-1", runner, state_dir=st,
                        note="updated", target=ADDR)
    assert out["acked"] is False and out["reread"] is True
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == sha
    assert entry["note"] == "updated"
    assert not any(c[0] == "send" for c in runner.calls)


def test_t14_response_loss_retains_pin_same_id_bytes_retry_succeeds(
        tmp_path):
    """T14：成功送達但 receipt 遺失（消費端可見面＝非 schema 錯誤、
    outcome 未確認）⇒ 原 pin 保留；同 bytes、同 ID 重試成功。"""
    st = str(tmp_path)
    _seed_pending(st)
    draft = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                         in_reply_to="env-1")
    runner1 = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("unknown", "wait-timeout"),
    ])
    with pytest.raises(mod.S2Error, match="結果未確認"):
        mod.send_reply(ADDR, "env-1", draft, runner1, state_dir=st)
    entry = _entry(st)
    assert entry["reply_envelope_id"] == "out-1"
    assert entry["reply_sha256"] == _file_sha(draft)
    runner2 = _seq_runner([_mail_get_doc("env-1"), _send_doc("out-1")])
    out = mod.send_reply(ADDR, "env-1", draft, runner2, state_dir=st)
    assert out["cleared"] is True
    assert out["receipt"]["envelopeId"] == "out-1"
    kept = mod.load_pending_replies(mod.pending_path(ADDR, st))
    assert kept is None or "env-1" not in kept.get("replies", {})


# ── AIR-336 修正迴圈（flash 外審 F-1）：shared snapshot 護衛分支補測───
#
# 守衛（duty_receive.py send_reply schema 拒收清理段）：他筆 pending
# 義務 pin 同一 outbound envelope ID 時禁刪 snapshot（誤刪砸掉他筆
# 的重試發送源）——保留＋揭露；無共用才刪。


def test_t15_schema_refusal_shared_snapshot_kept_and_disclosed(tmp_path):
    """T15（F-1）：兩筆 pending 義務（不同 in_reply_to）pin 同一
    outbound envelope ID＋共用 snapshot ⇒ 對第一筆 schema 拒收解 pin
    後，snapshot 仍被第二筆引用——禁刪＋訊息揭露保留原因；第一筆
    pin 已解、第二筆 pin 不受影響。"""
    st = str(tmp_path)
    draft1 = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                          in_reply_to="env-1")
    sha = _file_sha(draft1)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {
            "env-1": {"note": "n", "target": ADDR,
                      "reply_envelope_id": "out-1", "reply_sha256": sha},
            "env-2": {"note": "m", "target": ADDR,
                      "reply_envelope_id": "out-1", "reply_sha256": sha}}})
    snap = _snapshot_path(st)
    os.makedirs(os.path.dirname(snap), exist_ok=True)
    with open(draft1, "rb") as fh:
        snap_bytes = fh.read()
    with open(snap, "wb") as fh:
        fh.write(snap_bytes)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error) as ei:
        mod.send_reply(ADDR, "env-1", draft1, runner, state_dir=st)
    msg = str(ei.value)
    assert "schema 拒收" in msg
    assert "snapshot 保留" in msg and "out-1" in msg, msg
    assert "殘留 snapshot 清理失敗" not in msg
    assert os.path.exists(snap), "snapshot 仍被 env-2 引用——不該刪"
    with open(snap, "rb") as fh:
        assert fh.read() == snap_bytes
    entry1 = _entry(st, "env-1")
    assert entry1["reply_envelope_id"] is None
    assert entry1["reply_sha256"] is None
    entry2 = _entry(st, "env-2")
    assert entry2["reply_envelope_id"] == "out-1"
    assert entry2["reply_sha256"] == sha


def test_t16_schema_refusal_unshared_snapshot_removed(tmp_path):
    """T16（F-1 反向）：第二筆 pending pin 不同 envelope ID（無共用）
    ⇒ 對第一筆 schema 拒收解 pin 後，snapshot 正常刪除、無保留揭露；
    第二筆 pin 不受影響。"""
    st = str(tmp_path)
    draft1 = _write_draft(str(tmp_path / "out.json"), envelope_id="out-1",
                          in_reply_to="env-1")
    sha1 = _file_sha(draft1)
    mod.save_pending_replies(
        mod.pending_path(ADDR, st),
        {"address": ADDR, "replies": {
            "env-1": {"note": "n", "target": ADDR,
                      "reply_envelope_id": "out-1", "reply_sha256": sha1},
            "env-2": {"note": "m", "target": ADDR,
                      "reply_envelope_id": "out-2", "reply_sha256": sha1}}})
    snap = _snapshot_path(st)
    os.makedirs(os.path.dirname(snap), exist_ok=True)
    with open(draft1, "rb") as fh:
        snap_bytes = fh.read()
    with open(snap, "wb") as fh:
        fh.write(snap_bytes)
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _face_error("invalid-envelope", "usage"),
    ])
    with pytest.raises(mod.S2Error) as ei:
        mod.send_reply(ADDR, "env-1", draft1, runner, state_dir=st)
    msg = str(ei.value)
    assert "schema 拒收" in msg
    assert "snapshot 保留" not in msg, msg
    assert not os.path.exists(snap), "無共用——snapshot 應正常刪除"
    entry1 = _entry(st, "env-1")
    assert entry1["reply_envelope_id"] is None
    assert entry1["reply_sha256"] is None
    entry2 = _entry(st, "env-2")
    assert entry2["reply_envelope_id"] == "out-2"
    assert entry2["reply_sha256"] == sha1
