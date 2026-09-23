#!/usr/bin/env python3
"""
PreToolUse hook: 攔截 python heredoc 內的檔案寫入呼叫。

原因：sed 禁令與 Edit-first 紀律的繞道形態——`python3 - <<EOF` +
`pathlib.write_text()` / `open(..., 'w')` 直寫檔案，同時繞過 Edit 工具與
sed 禁令（mosaic 兩週遙測實測 319 次）。改檔一律走 Edit/Write 工具。
對應 rule: rules/tool-discipline.md「檔案修改禁令」。
偵測邏輯見 is_violation()。hook crash（非 0 非 2 exit）為非阻斷，工具仍執行。
"""

import ast
import json
import re
import shlex
import sys

HEREDOC_PATTERN = re.compile(r"<<-?\s*['\"]?\w+")
# `\bpython3?\b` 已涵蓋 uv run python 形態（uv 後仍出現 'python' word）
PYTHON_PATTERN = re.compile(r"\bpython3?\b")
# 不支援的 shell / Python 語法保留舊 heuristic。已知限制：open() 第一參數含
# 巢狀括號（open(Path(d).name, 'w')、open(os.path.join(a,b), 'w')）不攔
# ——[^)]* 不跨巢狀；spike 首版寧漏抓不誤傷，加寬前先收誤傷率數據。
# os.replace/shutil/copy 等先放行。
WRITE_PATTERN = re.compile(
    r"\.write_text\s*\(|\.write_bytes\s*\("
    r"|open\s*\([^)]*['\"][wax][+b]*['\"]"
)
HEREDOC_HEADER = re.compile(
    r"(?P<prefix>[^<>\n]+)<<(?P<tabs>-?)[ \t]*"
    r"(?:'(?P<single>\w+)'|\"(?P<double>\w+)\"|(?P<bare>\w+))"
    r"[ \t]*(?:#.*)?"
)
MAX_AST_BYTES = 100000


def _simple_words(line: str) -> list[str]:
    """只接受獨立單行 simple command；未知 shell 結構退 heuristic。"""
    if any(char in line for char in ("$", "`", "\\")):
        raise ValueError("shell expansion or continuation")
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    words = list(lexer)
    if any(word and all(c in "();<>|&" for c in word) for word in words):
        raise ValueError("shell compound command")
    return words


def _python_bodies(command: str) -> list[str]:
    """辨識獨立 Python / uv run Python 與 cat heredoc，依精確 delimiter 取界。

    cat 的 body 是資料，整段跳過；其他 heredoc receiver 無法判定是否解譯
    shell，故不授予 AST exemption。這是有限 admission heuristic，非 shell sandbox。
    """
    lines = command.split("\n")
    bodies: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        header = HEREDOC_HEADER.fullmatch(line)
        if header is None:
            _simple_words(line)
            continue
        prefix = header["prefix"]
        if "#" in prefix:
            raise ValueError("comment before redirection")
        words = _simple_words(prefix)
        if words[:2] == ["uv", "run"]:
            words = words[2:]
        if not words:
            raise ValueError("missing receiver")
        executable = words[0].rsplit("/", 1)[-1]
        python = executable in ("python", "python3") and words[1:] in ([], ["-"])
        if not python and executable != "cat":
            raise ValueError("unsupported heredoc receiver")
        delimiter = header["single"] or header["double"] or header["bare"]
        body: list[str] = []
        while index < len(lines):
            value = lines[index].lstrip("\t") if header["tabs"] else lines[index]
            index += 1
            if value == delimiter:
                break
            body.append(value)
        else:
            raise ValueError("unterminated heredoc")
        source = "\n".join(body)
        if header["bare"] and ("$" in source or "`" in source or "\\\n" in source):
            raise ValueError("unquoted heredoc expansion")
        if python:
            bodies.append(source)
    return bodies


def _has_write_call(source: str) -> bool:
    if len(source.encode("utf-8")) > MAX_AST_BYTES:
        raise ValueError("AST input budget exceeded")
    tree = ast.parse(source)
    filename_modules = {"io", "builtins"}
    admitted_call = None
    # All filename-open signatures are admitted only for the first direct call
    # after a prefix of known module imports; no state or scope inference.
    for statement in tree.body:
        if isinstance(statement, ast.Import) and all(
            alias.name in ("io", "builtins") for alias in statement.names
        ):
            filename_modules.update(
                alias.asname or alias.name for alias in statement.names
            )
        else:
            if isinstance(statement, ast.Expr) and isinstance(
                statement.value, ast.Call
            ):
                admitted_call = statement.value
            break
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in (
            "write_text",
            "write_bytes",
        ):
            return True
        if isinstance(func, ast.Name) and func.id == "open":
            filename_api = True
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            filename_api = (
                isinstance(func.value, ast.Name) and func.value.id in filename_modules
            )
        elif (isinstance(func, ast.Name) and func.id.endswith("open")) or (
            isinstance(func, ast.Attribute) and func.attr.endswith("open")
        ):
            # The baseline regex matches the open suffix (e.g. os.fdopen).
            raise ValueError("unsupported open callable")
        else:
            continue
        if node is not admitted_call or not filename_api:
            raise ValueError("unsupported open signature")
        if any(isinstance(arg, ast.Starred) for arg in node.args) or any(
            kw.arg is None for kw in node.keywords
        ):
            raise ValueError("unpacked open arguments")
        mode = next((kw.value for kw in node.keywords if kw.arg == "mode"), None)
        if mode is None:
            mode = node.args[1] if len(node.args) > 1 else None
        if mode is None:
            continue
        if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
            raise TypeError("unsupported open mode")
        if any(flag in mode.value for flag in "wax+"):
            return True
    return False


def is_violation(command: str) -> bool:
    """明確 Python heredoc 用 AST；不支援／解析失敗時維持舊 heuristic。"""
    m = HEREDOC_PATTERN.search(command)
    if not m:
        return False
    if not PYTHON_PATTERN.search(command):
        return False
    try:
        return any(_has_write_call(body) for body in _python_bodies(command))
    except (SyntaxError, TypeError, ValueError, RecursionError, MemoryError):
        return bool(WRITE_PATTERN.search(command, m.end()))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        # hook crash = 非阻斷，工具仍執行。記錄但不卡關。
        print(f"[block-python-file-write] stdin parse error: {exc}", file=sys.stderr)
        sys.exit(1)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not command or not is_violation(command):
        sys.exit(0)

    # exit 2 + stderr：harness 將 stderr 回饋給 LLM 作為修正指引
    print(
        "[Hook Blocked] python heredoc 內含檔案寫入呼叫。\n"
        "原因：python - <<EOF + write_text()/open(...,'w') 是 Edit 工具與 sed 禁令的"
        "繞道形態（遙測實測 319 次），不可追溯、無 read-state 保護。\n"
        "修正方式：改檔一律用 Edit/Write 工具；heredoc 僅用於純計算/查詢。",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
