#!/usr/bin/env python3
"""Report Shell provenance lint（ai-analysis 任務家殼的回源完整性）。

殼是 source 的 projection（illustrate-html-mode「投影鎖定與 stale 標記」＋
kanban-board 結案兩步 `--ref` 換 done/ 路徑）——本 lint 把三類已發生的失真
變機械閘門（codex 09-06 全 repo 審查 I-7）：
1. 同殼宣告多個互斥 projection SHA（一殼只能有一個 current identity）；
2. projection SHA 與同目錄 ep.md 的 content SHA 不符（stale projection）；
3. 回源連結失效：`file:///Users/` 絕對路徑（跨 worktree/clone 必斷）、
   `/ai-guide/<task path>` route 指向 repo 內不存在的路徑（歸檔未補 done/）。

掃描範圍：git-tracked `ai-analysis/**/index.html`（渲染產物 diagram-*.html
不進 git，自然排除）；存在性檢查限 .md/.json（svg 等渲染產物可重建，不查）。

Run: uv run python scripts/check_report_shells.py
Exit: 0=clean、1=有 violation、2=無法列舉（git 失敗）。
"""

import hashlib
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_SHA_MENTION = re.compile(r"\b([0-9a-f]{7,64})（EP content SHA")
_FILE_URL = re.compile(r'(?:href|src)="(file:///Users/[^"]+)"')
_ROUTE = re.compile(r"""/(?:ai-rules|ai-guide)/((?:_tasks|_projects)/[^"'<>\s#]+)""")
_RAW_MD_ROUTE = re.compile(r'href="([^"]*/(?:ai-rules|ai-guide)/[^"]*\.md)"')


def lint_shell(shell: Path, repo_root: Path) -> list[str]:
    """對單一殼跑三類檢查，回傳 violation 敘述清單（空＝通過）。"""
    text = shell.read_text(encoding="utf-8")
    issues: list[str] = []
    shas = set(_SHA_MENTION.findall(text))
    if len(shas) > 1:
        issues.append(
            f"同殼宣告多個互斥 projection SHA: {sorted(shas)}（只能有一個 current identity）"
        )
    ep = shell.parent / "ep.md"
    if shas and ep.exists():
        digest = hashlib.sha256(ep.read_bytes()).hexdigest()
        if not any(digest.startswith(s) for s in shas):
            issues.append(
                f"projection SHA {sorted(shas)} 與 ep.md content sha256 前綴不符"
                "（stale projection——重投影或修訂宣告）"
            )
    for url in _FILE_URL.findall(text):
        issues.append(f"file:// 絕對路徑連結（跨 worktree/clone 必斷）: {url}")
    for url in sorted(set(_RAW_MD_ROUTE.findall(text))):
        if url.startswith("file://") or "_md-viewer.html" in url:
            continue  # file:// 另有專屬規則；viewer 形態＝合約合法
        issues.append(
            f"raw .md route 連結（viewer-only 合約——.md 一律 viewer 形態）: {url}"
        )
    for rel in sorted(set(_ROUTE.findall(text))):
        target = repo_root / "ai-analysis" / urllib.parse.unquote(rel)
        if target.suffix in (".md", ".json") and not target.exists():
            issues.append(
                f"route 回源路徑不存在（任務歸檔未補 done/？）: ai-analysis/{rel}"
            )
    return issues


def main() -> int:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "ls-files",
            "--",
            ":(glob)ai-analysis/**/index.html",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"[FAIL] git ls-files: {proc.stderr.strip()}", file=sys.stderr)
        return 2
    findings = 0
    for line in proc.stdout.splitlines():
        shell = REPO_ROOT / line
        if not shell.exists():
            continue
        for issue in lint_shell(shell, REPO_ROOT):
            print(f"[FAIL] {line}: {issue}")
            findings += 1
    if findings:
        print(f"critical: 0  important: {findings}")
        return 1
    print("✅ report shell provenance 全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
