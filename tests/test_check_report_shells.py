"""check_report_shells 單元測試（codex 09-06 審查 I-7＋09-14 viewer 形態退役反轉）。"""

import hashlib

from conftest import load_module

lint = load_module("scripts/check_report_shells.py")


def _shell(
    tmp_path, body: str, ep: bytes | None = b"# ep\n", sub: str = "_tasks/9999-test"
) -> tuple:
    """建 fixture 任務家殼；body 中 {SHA} 會代換為 ep.md 實際 content SHA 前綴。

    sub 控制殼在 repo 內的相對位置——歷史位置（如 `_tasks/_archived/…`）走 lint 豁免。
    """
    d = tmp_path / "ai-analysis" / sub
    d.mkdir(parents=True)
    if ep is not None:
        (d / "ep.md").write_bytes(ep)
        body = body.replace("{SHA}", hashlib.sha256(ep).hexdigest()[:16])
    (d / "index.html").write_text(body, encoding="utf-8")
    return d / "index.html", tmp_path


def test_good_shell_passes(tmp_path):
    """相對路徑制合約：repo 相對 .md href（VSCode 直接開檔）不觸任何 violation。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="ep.md">EP</a>',
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


def test_viewer_url_active_shell_flagged(tmp_path):
    """viewer URL 在活躍殼＝violation（09-14 ai-guide 退出 :6421，viewer 形態退役）。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/_tasks/9999-test/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert sum("viewer URL 形態已退役" in i for i in issues) == 1


def test_viewer_url_historical_shell_exempt(tmp_path):
    """viewer URL 在歷史位置（_archived/）豁免——歷史殼留歷史態不動。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/_tasks/_archived/9999-test/ep.md">EP</a>',
        sub="_tasks/_archived/9999-test",
    )
    assert lint.lint_shell(shell, root) == []


def test_viewer_url_month_layer_shell_not_exempt(tmp_path):
    """viewer URL 在月份層（_tasks/YYYY-MM/）不豁免——月份層是活躍位置。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/_tasks/2026-09/9999-test/ep.md">EP</a>',
        sub="_tasks/2026-09/9999-test",
    )
    issues = lint.lint_shell(shell, root)
    assert sum("viewer URL 形態已退役" in i for i in issues) == 1


def test_viewer_url_historical_reports_exempt(tmp_path):
    """viewer URL 在歷史位置（reports/）豁免。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://localhost:6421/viewer/_md-viewer.html?p=/ai-guide/reports/2026-09-10-x.md">EP</a>',
        sub="reports/9999-test",
    )
    assert lint.lint_shell(shell, root) == []


def test_viewer_url_historical_blueprint_exempt(tmp_path):
    """viewer URL 在歷史位置（blueprint/）豁免。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-guide/blueprint/architecture.md">EP</a>',
        sub="blueprint/9999-test",
    )
    assert lint.lint_shell(shell, root) == []


def test_localhost_viewer_url_active_shell_flagged(tmp_path):
    """localhost:6421 同義 host 形態在活躍殼同樣觸旗（judge r3 題 1）。"""
    shell, root = _shell(
        tmp_path,
        "meta projection {SHA}（EP content SHA）\n"
        '<a href="http://localhost:6421/ai-guide/_tasks/9999-test/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert sum("viewer URL 形態已退役" in i for i in issues) == 1


def test_raw_md_on_6421_dedup_single_violation(tmp_path):
    """6421 host 上的 raw .md：活躍殼由 viewer 規則統一承接，恰好 1 條（dedup，judge r3 題 3）。"""
    shell, root = _shell(
        tmp_path,
        '<a href="http://127.0.0.1:6421/ai-guide/_tasks/9999-test/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert len(issues) == 1
    assert "viewer URL 形態已退役" in issues[0]


def test_raw_md_http_flagged_with_new_contract_message(tmp_path):
    """raw http .md（非 6421 host、非 viewer 形態）仍是 violation，訊息教新合約＝repo 相對路徑。"""
    shell, root = _shell(
        tmp_path,
        '<a href="https://example.com/ai-guide/_tasks/9999-test/ep.md">EP</a>',
    )
    issues = lint.lint_shell(shell, root)
    assert len(issues) == 1
    assert "raw .md http 連結" in issues[0] and "repo 相對路徑" in issues[0]
