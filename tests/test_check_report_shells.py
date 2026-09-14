"""check_report_shells 單元測試（codex 09-06 審查 I-7——三類已發生的殼失真）。"""

import hashlib

from conftest import load_module

lint = load_module("scripts/check_report_shells.py")


def _shell(tmp_path, body: str, ep: bytes | None = b"# ep\n") -> tuple:
    """建 fixture 任務家殼；body 中 {SHA} 會代換為 ep.md 實際 content SHA 前綴。"""
    d = tmp_path / "ai-analysis" / "_tasks" / "t"
    d.mkdir(parents=True)
    if ep is not None:
        (d / "ep.md").write_bytes(ep)
        body = body.replace("{SHA}", hashlib.sha256(ep).hexdigest()[:16])
    (d / "index.html").write_text(body, encoding="utf-8")
    return d / "index.html", tmp_path


def test_good_shell_passes(tmp_path):
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/_tasks/t/ep.md">EP</a>',
    )
    assert lint.lint_shell(shell, root) == []


def test_dual_projection_sha_flagged(tmp_path):
    shell, root = _shell(
        tmp_path,
        "header projection {SHA}（EP content SHA）\n"
        "footer projection source：fffffffffffffff（EP content SHA）",
    )
    issues = lint.lint_shell(shell, root)
    assert any("互斥" in i for i in issues)


def test_stale_projection_sha_flagged(tmp_path):
    shell, root = _shell(tmp_path, "projection deadbeefdeadbeef（EP content SHA）")
    issues = lint.lint_shell(shell, root)
    assert any("不符" in i for i in issues)


def test_file_url_flagged(tmp_path):
    shell, root = _shell(
        tmp_path,
        '<a href="file:///Users/ctai/Github/ai-guide/ai-analysis/_tasks/t/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert any("file://" in i for i in issues)


def test_dead_route_flagged(tmp_path):
    shell, root = _shell(
        tmp_path,
        '<a href="http://127.0.0.1:6421/ai-guide/_tasks/ghost-task/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert any("不存在" in i and "ghost-task" in i for i in issues)


def test_raw_md_route_flagged_viewer_form_passes(tmp_path):
    """raw `.md` route 違反 viewer-only 合約；`_md-viewer.html?p=` 形態合法。"""
    shell, root = _shell(
        tmp_path,
        '<a href="http://127.0.0.1:6421/ai-guide/_tasks/t/ep.md">EP</a>\n'
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/_tasks/t/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert sum("raw .md route" in i for i in issues) == 1
