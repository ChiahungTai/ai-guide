"""AIR-312 S2 isolated-store end-to-end (real installed dutymail, real CLI).

Provenance: H (installed dutymail 3.11.0 --help: --store-root flag is the
only isolation face; STORE_ROOT env ignored; store dir must be 0700).

Every dutymail touch carries explicit --store-root under .agent-tmp (never
default ~/.dutymail); every CLI runs from a disposable consumer git repo
whose basename IS the mailbox address (skill command shape:
`uv run python $AI_GUIDE/scripts/duty_receive.py ...` with caller cwd
preserved). No real mailboxes, no network.
"""

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from conftest import REPO_ROOT

SCRIPT = str(REPO_ROOT / "scripts" / "duty_receive.py")
WAITER = str(REPO_ROOT / "scripts" / "mail_waiter.py")
BIN = os.path.expanduser(
    "~/.local/lib/delegate-bridge/runtime/current/dutymail")

E2E_ROOT = REPO_ROOT / ".agent-tmp" / "air312-s2-e2e-tmp"


def _run_cli(cwd, *argv):
    proc = subprocess.run(
        ["uv", "run", "python", SCRIPT, *argv],
        capture_output=True, text=True, cwd=cwd, timeout=120,
    )
    return proc


def _dutymail(store, *argv):
    proc = subprocess.run(
        [BIN, "--store-root", str(store), *argv],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["result"]


def _git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.email=t@t", "-c",
         "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"],
        check=True,
    )
    return path


def _envelope(mid, eid, to_addr, body, in_reply_to=None):
    doc = {
        "schema_version": 2, "message_id": mid, "envelope_id": eid,
        "from": {"session_id": "e2e", "name": None, "harness": None},
        "to": {"address": to_addr},
        "delivery": {"mode": "queue", "fallback": None, "intent": "inform",
                     "wake": "none", "fallback_used": False},
        "created_at_us": 1000000, "body": body,
    }
    if in_reply_to is not None:
        doc["in_reply_to"] = in_reply_to
    return doc


@pytest.mark.skipif(not os.path.isfile(BIN), reason="no installed dutymail")
def test_s2_ordinary_inbox_end_to_end():
    pid = os.getpid()
    root = E2E_ROOT / f"run-{pid}"
    if root.exists():
        shutil.rmtree(root)
    store = root / "store"
    state = root / "state"
    store.mkdir(parents=True)
    os.chmod(store, 0o700)
    consumer = _git_repo(root / "repos" / f"s2e2c{pid}")
    peer = _git_repo(root / "repos" / f"s2e2p{pid}")
    caddr, paddr = consumer.name, peer.name
    try:
        _dutymail(store, "store", "init")
        _dutymail(store, "address", "create", "--alias", caddr)
        _dutymail(store, "address", "create", "--alias", paddr)
        long_plain = "plain-body-no-json " * 400 + "尾"
        env_id = "e2e-env-1"
        src = root / "incoming.json"
        src.write_text(json.dumps(
            _envelope(str(uuid.uuid4()), env_id, caddr, long_plain),
            ensure_ascii=False), encoding="utf-8")
        rcpt = _dutymail(store, "send", "--envelope-file", str(src))
        assert rcpt["envelopeId"] == env_id

        # inbox default pending shows the full plain body intact.
        p = _run_cli(str(consumer), "inbox", "--store-root", str(store))
        assert p.returncode == 0, p.stderr
        assert env_id in p.stdout
        assert "plain-body-no-json" in p.stdout and "尾" in p.stdout
        assert long_plain in p.stdout  # no truncation

        # show by envelope id: complete body intact.
        p = _run_cli(str(consumer), "show", "--envelope-id", env_id,
                     "--store-root", str(store))
        assert p.returncode == 0, p.stderr
        assert long_plain in p.stdout

        # no pending replies yet.
        p = _run_cli(str(consumer), "pending-replies",
                     "--state-dir", str(state))
        assert p.returncode == 0, p.stderr
        assert "無待回覆" in p.stdout

        # mark-read with note/target (reply needed).
        p = _run_cli(str(consumer), "mark-read", "--envelope-id", env_id,
                     "--note", "need reply", "--target", paddr,
                     "--store-root", str(store), "--state-dir", str(state))
        assert p.returncode == 0, p.stderr
        assert "已標已讀" in p.stdout

        # original stays readable in history: pending empty, acked keeps it.
        p = _run_cli(str(consumer), "inbox", "--box", "pending",
                     "--store-root", str(store))
        assert p.returncode == 0, p.stderr
        assert env_id not in p.stdout
        p = _run_cli(str(consumer), "inbox", "--box", "acked",
                     "--store-root", str(store))
        assert p.returncode == 0, p.stderr
        assert env_id in p.stdout and long_plain in p.stdout

        # fresh process sees the pending reply.
        p = _run_cli(str(consumer), "pending-replies",
                     "--state-dir", str(state))
        assert p.returncode == 0, p.stderr
        assert env_id in p.stdout and paddr in p.stdout

        # waiter stop leaves pending intact.
        wstate = root / "waiter"
        p = subprocess.run(
            ["uv", "run", "python", WAITER, "stop",
             "--state-dir", str(wstate)],
            capture_output=True, text=True, cwd=str(consumer), timeout=120,
        )
        assert p.returncode == 0, p.stderr
        p = _run_cli(str(consumer), "pending-replies",
                     "--state-dir", str(state))
        assert p.returncode == 0, p.stderr
        assert env_id in p.stdout

        # failed reply (broken store) retains pending.
        draft = root / "reply-draft.json"
        draft.write_text(json.dumps(
            _envelope(str(uuid.uuid4()), "e2e-reply-1", paddr,
                      "reply plain", in_reply_to=env_id),
            ensure_ascii=False), encoding="utf-8")
        broken = root / "broken-store"
        broken.mkdir()
        os.chmod(broken, 0o700)
        p = _run_cli(str(consumer), "reply", "--in-reply-to", env_id,
                     "--envelope-file", str(draft),
                     "--store-root", str(broken), "--state-dir", str(state))
        assert p.returncode != 0
        p = _run_cli(str(consumer), "pending-replies",
                     "--state-dir", str(state))
        assert env_id in p.stdout

        # successful reply clears; peer sees it from its own repo cwd.
        p = _run_cli(str(consumer), "reply", "--in-reply-to", env_id,
                     "--envelope-file", str(draft),
                     "--store-root", str(store), "--state-dir", str(state))
        assert p.returncode == 0, p.stderr
        assert "e2e-reply-1" in p.stdout
        p = _run_cli(str(consumer), "pending-replies",
                     "--state-dir", str(state))
        assert "無待回覆" in p.stdout
        p = _run_cli(str(peer), "inbox", "--store-root", str(store))
        assert p.returncode == 0, p.stderr
        assert "e2e-reply-1" in p.stdout and "reply plain" in p.stdout

        # foreign fence: consumer cwd asking for peer address refuses.
        p = _run_cli(str(consumer), "inbox", "--address", paddr,
                     "--store-root", str(store))
        assert p.returncode == 2
    finally:
        shutil.rmtree(root, ignore_errors=True)
