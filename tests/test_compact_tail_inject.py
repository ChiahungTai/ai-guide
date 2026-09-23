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


def _line(**kw) -> str:
    return json.dumps(kw)


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


def test_fetch_tail_skips_prior_injection_marker(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text(
        _line(
            type="user",
            message={"content": "含 <compact-tail-inject> 上代注入"},
            timestamp="2026-08-30T05:00:00Z",
        )
        + "\n",
        encoding="utf-8",
    )
    assert cti.fetch_tail(str(p)) == ""


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
    [["uv", "run", "python"], ["/usr/bin/python3"]],
    ids=["uv-run-python", "system-python"],
)
@pytest.mark.parametrize("filler", ['"\\\n', "\x01", "繁體🙂"])
def test_entrypoint_escaped_tail_and_state_stay_bounded(tmp_path, runtime, filler):
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
        [*runtime, cti.__file__],
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
