"""compact-tail-inject 的 transcript 解析測試（judge F1）。

fetch_tail 是本批最大行為面變更（sqlite → CC transcript JSONL）；
截斷語義（保最新砍最舊）是回歸時最易靜默壞掉的點。
欄位語義已對真實 transcript 驗證（isCompactSummary/isSidechain 在場）。
"""

import json
import subprocess
import sys

import pytest
from conftest import load_module

cti = load_module("hooks/compact-tail-inject.py")
gov = load_module("governance/install.py")


def _managed_hook_python() -> str:
    """Deployed hook interpreter (C3): absolute uv-managed 3.12 via governance
    resolver — never a nested uv-run hook-fire dependency."""
    try:
        return gov.resolve_hook_python()
    except gov.GovernanceError as exc:
        pytest.skip(
            f"uv-managed Python 3.12 unavailable: {exc} — run `uv python install 3.12`"
        )


def _line(**kw) -> str:
    return json.dumps(kw)


def _entrypoint_context(transcript, executable):
    result = subprocess.run(
        [executable, cti.__file__],
        input=json.dumps({"source": "compact", "transcript_path": str(transcript)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout:
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_texts_of_str_and_list_blocks():
    assert cti._texts_of({"content": "hi"}) == ["hi"]
    assert cti._texts_of(
        {"content": [{"type": "text", "text": "a"}, {"type": "tool_use", "text": "b"}]}
    ) == ["a"]
    assert cti._texts_of({}) == []


def test_fetch_tail_filters_and_chronological_order(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text(
        "\n".join(
            [
                _line(
                    type="user",
                    message={"content": "舊訊息"},
                    timestamp="2026-08-30T01:00:00Z",
                ),
                _line(type="summary", message={"content": "skip-type"}),
                _line(
                    type="user",
                    isCompactSummary=True,
                    message={"content": "skip-compact"},
                    timestamp="2026-08-30T02:00:00Z",
                ),
                _line(
                    type="assistant",
                    isSidechain=True,
                    message={"content": "skip-sidechain"},
                    timestamp="2026-08-30T03:00:00Z",
                ),
                _line(
                    type="assistant",
                    message={"content": [{"type": "text", "text": "最新回覆"}]},
                    timestamp="2026-08-30T04:05:06Z",
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = cti.fetch_tail(str(p))
    assert "舊訊息" in out and "最新回覆" in out
    assert "skip-type" not in out and "skip-compact" not in out
    assert "skip-sidechain" not in out
    assert out.index("舊訊息") < out.index("最新回覆")  # 舊在前、新在後
    assert "04:05:06" in out


@pytest.mark.parametrize("runtime", ["managed-312", "system-python"])
@pytest.mark.parametrize("role", ["user", "assistant"])
@pytest.mark.parametrize(
    "text",
    [
        "含 <compact-tail-inject> 的正常討論",
        "<compact-tail-inject> 這個 tag 的用途是什麼？",
        "<compact-tail-inject>\n普通文字\n</compact-tail-inject>",
    ],
)
def test_fetch_tail_preserves_marker_mentions(tmp_path, role, text, runtime):
    """S: F2 retains ordinary mentions, including tag-led text and quoted tag pairs."""
    p = tmp_path / "t.jsonl"
    p.write_text(
        _line(
            type=role,
            message={"content": text},
            timestamp="2026-08-30T05:00:00Z",
        )
        + "\n",
        encoding="utf-8",
    )
    executable = (
        _managed_hook_python() if runtime == "managed-312" else "/usr/bin/python3"
    )
    assert f"\n{text}\n</raw-tail>" in _entrypoint_context(p, executable)


@pytest.mark.parametrize("runtime", ["managed-312", "system-python"])
@pytest.mark.parametrize("role", ["user", "assistant"])
@pytest.mark.parametrize(
    "shape", ["complete", "mixed-blocks", "embedded", "no-prefix", "no-suffix"]
)
def test_producer_envelope_roundtrip(tmp_path, role, shape, runtime):
    """S: F2 filters complete real producer output per text block, preserving mentions."""
    p = tmp_path / "t.jsonl"
    p.write_text(_line(type="user", message={"content": "PRIOR-ONLY-SENTINEL"}))
    executable = (
        _managed_hook_python() if runtime == "managed-312" else "/usr/bin/python3"
    )
    envelope = _entrypoint_context(p, executable)
    assert "PRIOR-ONLY-SENTINEL" in envelope
    if shape == "complete":
        content = " \n" + envelope + "\n "
    elif shape == "mixed-blocks":
        content = [
            {"type": "text", "text": "KEEP-BEFORE"},
            {"type": "text", "text": envelope},
            {"type": "tool_use", "text": "NOT-TEXT"},
            {"type": "text", "text": "KEEP-AFTER"},
        ]
    elif shape == "embedded":
        content = "請檢查這段輸出：\n" + envelope
    elif shape == "no-prefix":
        content = envelope.split("\n", 1)[1]
    else:
        content = envelope.removesuffix("</compact-tail-inject>")
    p.write_text(_line(type=role, message={"content": content}))
    context = _entrypoint_context(p, executable)
    if shape == "complete":
        assert context == ""
        return
    tail = context.split("<raw-tail session=>\n", 1)[1].rsplit("\n</raw-tail>", 1)[0]
    if shape == "mixed-blocks":
        assert tail.endswith("KEEP-BEFORE\nKEEP-AFTER")
        assert "PRIOR-ONLY-SENTINEL" not in tail
        assert "NOT-TEXT" not in tail
    else:
        assert tail.endswith(content.strip())


def test_fetch_tail_budget_drops_oldest_keeps_newest(tmp_path):
    big = "x" * 15000  # TAIL_BUDGET_BYTES=20000：只容得下最新一則
    p = tmp_path / "t.jsonl"
    p.write_text(
        "\n".join(
            [
                _line(
                    type="user",
                    message={"content": big + " OLDEST"},
                    timestamp="2026-08-30T06:00:00Z",
                ),
                _line(
                    type="user",
                    message={"content": big},
                    timestamp="2026-08-30T07:00:00Z",
                ),
                _line(
                    type="user",
                    message={"content": big + " NEWEST"},
                    timestamp="2026-08-30T08:00:00Z",
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = cti.fetch_tail(str(p))
    assert "NEWEST" in out
    assert "OLDEST" not in out


def test_fetch_tail_scan_window_truncates(tmp_path):
    # 65 則小訊息全在預算內：CANDIDATE_ENTRIES=60 → 最舊 5 則被窗口截掉
    p = tmp_path / "t.jsonl"
    p.write_text(
        "\n".join(
            _line(
                type="user",
                message={"content": f"msg-{i:02d}"},
                timestamp=f"2026-08-30T09:{i // 60:02d}:{i % 60:02d}Z",
            )
            for i in range(65)
        )
        + "\n",
        encoding="utf-8",
    )
    out = cti.fetch_tail(str(p))
    assert "msg-64" in out  # 最新保留
    assert "msg-04" not in out  # 窗口外最舊被截
    assert "msg-05" in out  # 窗口邊界內保留


# Oracle S: accepted EP H3 — retain the newest UTF-8 suffix, bounded on the wire.
@pytest.mark.parametrize("filler", ["a", "繁體🙂"])
def test_oversize_newest_retains_utf8_suffix(tmp_path, filler):
    p = tmp_path / "large.jsonl"
    p.write_text(_line(type="user", message={"content": filler * 21000 + "最新指示"}))
    tail = cti.fetch_tail(str(p))
    assert tail.endswith("最新指示")
    assert "[truncated]" in tail
    assert "[user]" in tail
    assert "�" not in tail
    assert len(tail.encode("utf-8")) <= 20000


def test_tail_budget_includes_block_separator(tmp_path):
    p = tmp_path / "boundary.jsonl"
    header = "### [user] 12:34:56\n"
    text = "a" * (10000 - len(header))
    row = _line(
        type="user", timestamp="2000-01-01T12:34:56Z", message={"content": text}
    )
    p.write_text(row + "\n" + row)
    assert len(cti.fetch_tail(str(p)).encode("utf-8")) <= 20000


def test_malformed_records_do_not_hide_valid_latest(tmp_path):
    p = tmp_path / "mixed.jsonl"
    records = [
        "bad json",
        "null",
        "[]",
        "42",
        _line(type="user", message="wrong shape"),
        _line(type="user", message={"content": [{"type": "text", "text": 4}]}),
        _line(type="user", message={"content": "\ud800"}),
        _line(type="user", message={"content": "valid latest"}),
    ]
    p.write_text("\n".join(records))
    assert cti.fetch_tail(str(p)).endswith("valid latest")


@pytest.mark.parametrize(
    "runtime",
    ["managed-312", "system-python"],
)
@pytest.mark.parametrize("filler", ['"\\\n', "\x01", "繁體🙂"])
def test_entrypoint_escaped_tail_and_state_stay_bounded(tmp_path, runtime, filler):
    python = _managed_hook_python() if runtime == "managed-312" else "/usr/bin/python3"
    p = tmp_path / "transcript.jsonl"
    p.write_text(
        _line(type="assistant", message={"content": filler * 22000 + "LATEST-END"})
    )
    (tmp_path / "STATE.md").write_text("STATE-BEGIN" + "\x01" * 4500)
    payload = {
        "source": "compact",
        "transcript_path": str(p),
        "cwd": str(tmp_path),
        "session_id": "s",
    }
    result = subprocess.run(
        [python, cti.__file__],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert 0 < len(result.stdout.encode("utf-8")) <= 30000
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    raw = context.split("<raw-tail session=s>\n", 1)[1].split("\n</raw-tail>", 1)[0]
    assert raw.endswith("LATEST-END")
    assert "[truncated]" in raw
    assert "�" not in raw
    assert "STATE-BEGIN" in context
    assert context.endswith("</compact-tail-inject>")


@pytest.mark.parametrize("source", ["startup", "resume", "clear"])
def test_entrypoint_ordinary_sources_are_noop(tmp_path, source):
    result = subprocess.run(
        [sys.executable, cti.__file__],
        input=json.dumps({"source": source, "cwd": str(tmp_path)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def test_wire_budget_trims_escaping_even_below_raw_budget(tmp_path):
    p = tmp_path / "escaped.jsonl"
    p.write_text(
        _line(type="user", message={"content": "\x01" * 10000 + "TAIL-SENTINEL"})
    )
    result = subprocess.run(
        [sys.executable, cti.__file__],
        input=json.dumps({"source": "compact", "transcript_path": str(p)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert 0 < len(result.stdout.encode("utf-8")) <= 30000
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "[truncated]" in context
    assert "TAIL-SENTINEL\n</raw-tail>" in context


def test_wire_trim_preserves_actual_latest_role_and_timestamp(tmp_path):
    p = tmp_path / "roles.jsonl"
    body = "\x01" * 21000 + "\n### [user] FAKE-TIME\nLATEST-END"
    p.write_text(
        "\n".join(
            [
                _line(type="user", message={"content": "old"}),
                _line(
                    type="assistant",
                    timestamp="2000-01-01T12:34:56Z",
                    message={"content": body},
                ),
            ]
        )
    )
    result = subprocess.run(
        [sys.executable, cti.__file__],
        input=json.dumps({"source": "compact", "transcript_path": str(p)}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.encode("utf-8")) <= 30000
    context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
    raw = context.split("<raw-tail session=>\n", 1)[1].split("\n</raw-tail>", 1)[0]
    assert raw.startswith("### [assistant] 12:34:56\n[truncated]\n")
    assert raw.endswith("### [user] FAKE-TIME\nLATEST-END")


@pytest.mark.parametrize("budget", [0, 1, 11, 12, 13, 14, 15])
def test_bounded_suffix_tiny_budget_is_honored(budget):
    out = cti._bounded_suffix("繁體🙂" * 20, budget)
    assert len(out.encode("utf-8")) <= budget
    assert "�" not in out


def test_bounded_suffix_rejects_negative_budget():
    with pytest.raises(ValueError):
        cti._bounded_suffix("text", -1)


@pytest.mark.parametrize("payload", [None, [], 42, {}, {"source": "compact"}])
def test_malformed_or_missing_hook_input_is_noop(payload):
    result = subprocess.run(
        [sys.executable, cti.__file__],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
