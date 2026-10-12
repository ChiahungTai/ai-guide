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
    runner = _seq_runner([
        _mail_get_doc("env-1"),
        _status_doc(0, False),
        _bind_doc(1, "tok-1"),
        _prepare_doc("env-1"),
        _face_error("ack-bad", "storage"),
        _release_doc(),
    ])
    with pytest.raises(Exception):
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
