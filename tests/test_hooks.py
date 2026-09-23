"""攔截型 hooks 的偵測邏輯單元測試（T1-2）。

這些 is_violation() 是行為閘門的核心——regression 直接改變攔截面
（漏抓 = 規則繞道重現；誤傷 = 正常命令被擋）。
"""

import json
import subprocess

import pytest
from conftest import load_module

block_comment = load_module("hooks/block-python-c-comment.py")
block_write = load_module("hooks/block-python-file-write.py")


# ---------------------------------------------------------------------------
# block-python-c-comment：python -c 跨行 # 註解
# ---------------------------------------------------------------------------


def test_c_comment_violation_multiline_hash():
    cmd = "python3 -c 'import json\n# 註解\nprint(1)'"
    assert block_comment.is_violation(cmd)


def test_c_comment_ok_single_line():
    assert not block_comment.is_violation("python3 -c 'print(1)'")


def test_c_comment_ok_multiline_no_hash():
    assert not block_comment.is_violation("python -c 'x = 1\nprint(x)'")


def test_c_comment_ok_not_python():
    assert not block_comment.is_violation("echo 'a\n# b'")


# ---------------------------------------------------------------------------
# block-python-file-write：python heredoc 寫檔繞道（遙測實測 319 次的形態）
# ---------------------------------------------------------------------------


def test_write_violation_pathlib(tmp_path):
    cmd = f"python3 - <<'EOF'\nfrom pathlib import Path\nPath('{tmp_path}/x').write_text('hi')\nEOF"
    assert block_write.is_violation(cmd)


def test_write_violation_open_w():
    cmd = (
        "uv run python - <<EOF\nwith open('out.txt', 'w') as f:\n    f.write('x')\nEOF"
    )
    assert block_write.is_violation(cmd)


def test_write_ok_readonly_heredoc():
    cmd = "python3 - <<'EOF'\nimport json\nprint(json.dumps({'a': 1}))\nEOF"
    assert not block_write.is_violation(cmd)


def test_write_ok_open_read_mode():
    cmd = "python3 - <<EOF\nwith open('in.txt', 'r') as f:\n    print(f.read())\nEOF"
    assert not block_write.is_violation(cmd)


def test_write_ok_no_heredoc():
    # 非 heredoc 的單行 write（少見但非本 hook 標的——write 繞道以 heredoc 為大宗）
    assert not block_write.is_violation("python3 -c \"open('x','w')\"")


def test_write_ok_write_before_heredoc_marker():
    # 寫入 pattern 在 heredoc 標記之前（如把 heredoc 輸出導向檔案的字串巧合）
    cmd = "echo \"w_text(\" && python3 - <<'EOF'\nprint(1)\nEOF"
    assert not block_write.is_violation(cmd)


# Oracle S: accepted EP H4 — literal examples are not write calls.
@pytest.mark.parametrize(
    "body",
    [
        '# Path("x").write_text("example")',
        "print(\".write_bytes(b\\'example\\')\")",
        "example = \"open(\\'x\\', \\'w\\')\"\nprint(example)",
        "'''Documentation: Path(\"x\").write_text(\"example\")'''",
        "print(\"EOF\\n.write_text(\\'example\\')\")",
    ],
)
def test_python_heredoc_literal_and_comment_examples_allowed(body):
    assert not block_write.is_violation("python3 - <<'EOF'\n" + body + "\nEOF")


@pytest.mark.parametrize(
    "body",
    [
        'Path("x").write_text("actual")',
        'Path("x").write_bytes(b"actual")',
        'open(Path("x"), "w")',
        'open("x", mode="a")',
        'open("x", "r+")',
        'Path("x").open("wb")',
        'import io as stream\nstream.open("file", "w")',
        "print(f\"{Path('x').write_text('actual')}\")",
    ],
)
def test_python_heredoc_actual_write_calls_blocked(body):
    assert block_write.is_violation("uv run python - <<'PY'\n" + body + "\nPY")


@pytest.mark.parametrize(
    "command",
    [
        "python3 - <<EOF\nprint(1)\nEOF\necho \".write_text('example')\"",
        'cat <<TEXT\npython3 - <<PY\nPath("x").write_text("example")\nPY\nTEXT',
        'cat <<TEXT\nopen("x", "w")\nTEXT\npython3 - <<PY\nprint(1)\nPY',
        'python3 - <<PY\nprint(1)\nPY\ncat <<TEXT\n.write_text("example")\nTEXT',
        "python3 - <<-'PY'\n\tprint(\".write_text(example)\")\n\tPY",
    ],
)
def test_heredoc_extent_excludes_other_shell_and_heredocs(command):
    assert not block_write.is_violation(command)


@pytest.mark.parametrize(
    "command",
    [
        'python3 - <<PY\nprint(1)\nPY\npython3 - <<NEXT\nPath("x").write_text("x")\nNEXT',
        'python3 - <<PY\nPath("x").write_text("x")\n PY',
        'python3 - <<PY\nnot valid python .write_text("x")\nPY',
        'python3 - <<PY | cat\nPath("x").write_text("x")\nPY',
        'python3 - <<A <<B\nprint(1)\nA\nPath("x").write_text("x")\nB',
    ],
)
def test_unsupported_or_multiple_heredocs_still_block_real_write(command):
    assert block_write.is_violation(command)


@pytest.mark.parametrize(
    "runtime",
    [["uv", "run", "python"], ["/usr/bin/python3"]],
    ids=["uv-run-python", "system-python"],
)
@pytest.mark.parametrize(
    "body, expected",
    [
        ("print(\"open(\\'x\\', \\'w\\')\")", 0),
        ('Path("x").write_text("actual")', 2),
    ],
)
def test_write_entrypoint_runtime_contract(tmp_path, runtime, body, expected):
    result = subprocess.run(
        [*runtime, block_write.__file__],
        cwd=tmp_path,
        input=json.dumps(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "python3 - <<'PY'\n" + body + "\nPY",
                },
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected, result.stderr
    assert result.stdout == ""
    assert ("[Hook Blocked]" in result.stderr) == (expected == 2)
    assert not (tmp_path / "x").exists()


@pytest.mark.parametrize(
    "body",
    [
        'open("x", "r")',
        'open(Path("w"), mode="rb")',
        'io.open("a", "rb")',
        'import io as stream\nstream.open("x", "r")',
        'builtins.open("x", "r")',
        'Path("x").open("r")',
        "text = \"open('x', 'w')\"\nprint(text)",
    ],
)
def test_python_heredoc_readonly_modes_and_exact_literal_allowed(body):
    assert not block_write.is_violation("python3 - <<'PY'\n" + body + "\nPY")


@pytest.mark.parametrize(
    "command",
    [
        'python3 - <<PY\nprint("$(echo .write_text(example))")\nPY',
        'bash <<SH\npython3 - <<PY\nPath("x").write_text("x")\nPY\nSH',
        "python3 - <<PY\n" + "# padding\n" * 12000 + 'Path("x").write_text("x")\nPY',
    ],
)
def test_shell_expansion_shell_receiver_and_ast_budget_use_fallback(command):
    assert block_write.is_violation(command)


# Oracle S: final-review F1/F2 contract — unsupported forms retain the heuristic;
# default reads must not interpret a filename as a Path.open mode.
@pytest.mark.parametrize(
    "runtime",
    [["uv", "run", "python"], ["/usr/bin/python3"]],
    ids=["uv-run-python", "system-python"],
)
@pytest.mark.parametrize(
    "body, expected",
    [
        ('open("out.bin", "w" + "b")', 2),
        ('open("out.txt", "w" if True else "r")', 2),
        ('open(file="out.bin", mode="w" + "b")', 2),
        ('open(file="out.txt", mode="w" if True else "r")', 2),
        ('open("data.txt", "r" + "b")', 0),
        ('open("data.txt", "r" if True else "rb")', 0),
        ('open(file="data.txt")', 0),
        ('open("out.txt", "w")', 2),
        ('open("data.txt", "r")', 0),
        ('import io as stream\nstream.open("data.txt")', 0),
        ('import builtins as stream\nstream.open("data.txt")', 0),
        ('import io as stream\nstream.open(file="data.txt")', 0),
        ('import builtins as stream\nstream.open(file="data.txt")', 0),
        ('import io as stream\nstream.open("out.txt", "w")', 2),
        ('import builtins as stream\nstream.open(file="out.txt", mode="w")', 2),
        ('import io as stream\nstream.open(file="data.txt", mode="rb")', 0),
        ('import builtins as stream\nstream.open("out.bin", "w" + "b")', 2),
        ('Path("out.bin").open("wb")', 2),
        # Unknown Path.open retains the baseline regex's r+ limitation.
        ('Path("out.txt").open(mode="r+")', 0),
        ('io.open(file="data.txt")', 0),
        (
            "import io as stream\nfrom pathlib import Path\n"
            'stream = Path("out.txt")\nstream.open("w")',
            2,
        ),
        (
            "import builtins as stream\n"
            'stream = __import__("pathlib").Path("out.txt")\nstream.open("w")',
            2,
        ),
        (
            "import io as stream\n"
            'def write(stream):\n    stream.open("w")\n'
            'write(__import__("pathlib").Path("out.txt"))',
            2,
        ),
        (
            "import io as stream\n"
            '(lambda stream: stream.open("w"))(__import__("pathlib").Path("out.txt"))',
            2,
        ),
        (
            'import io as stream\nstream.open("data.txt")\n'
            'stream = __import__("pathlib").Path("out.txt")\nstream.open("w")',
            2,
        ),
        (
            "import io as stream\nfrom pathlib import Path\n"
            'stream = Path("data.txt")\nstream.open("r")',
            0,
        ),
        ('io = __import__("pathlib").Path("out.txt")\nio.open("w")', 2),
        ('builtins = __import__("pathlib").Path("out.txt")\nbuiltins.open("w")', 2),
        ('open = __import__("pathlib").Path("out.txt").open\nopen("w")', 2),
        (
            'def write(io):\n    io.open("w")\n'
            'write(__import__("pathlib").Path("out.txt"))',
            2,
        ),
        ('io = __import__("pathlib").Path("data.txt")\nio.open("r")', 0),
        ('open = __import__("pathlib").Path("data.txt").open\nopen("r")', 0),
        (
            'import io\nio.open = __import__("pathlib").Path("out.txt").open\n'
            'io.open("w")',
            2,
        ),
        (
            "import builtins\n"
            'builtins.open = __import__("pathlib").Path("out.txt").open\nopen("w")',
            2,
        ),
        ('open("out.txt", **{"mode": "w"})', 2),
        ('open(*["out.txt", "w"])', 2),
        (
            'import io\nio.open = __import__("pathlib").Path("data.txt").open\n'
            'io.open("r")',
            0,
        ),
        (
            "import builtins\n"
            'builtins.open = __import__("pathlib").Path("data.txt").open\nopen("r")',
            0,
        ),
        ('open("data.txt", **{"mode": "r"})', 0),
        ('open(*["data.txt", "r"])', 0),
        ('os.fdopen(f, "w")', 2),
        ('os.fdopen(f, "r")', 0),
    ],
)
def test_h4_followup_mode_and_receiver_contract(tmp_path, runtime, body, expected):
    command = "python3 - <<'PY'\n" + body + "\nPY"
    result = subprocess.run(
        [*runtime, block_write.__file__],
        cwd=tmp_path,
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected, result.stderr
    assert result.stdout == ""
    assert ("[Hook Blocked]" in result.stderr) == (expected == 2)
    assert block_write.is_violation(command) == (expected == 2)
    assert not any(tmp_path.iterdir())
