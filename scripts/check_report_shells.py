#!/usr/bin/env python3
"""Report Shell provenance lint（ai-analysis 任務家殼的回源完整性）。

殼是 source 的 projection（illustrate-html-mode「投影鎖定與 stale 標記」＋
kanban-board 開工 refs 出生即寫——AIR-77 起任務目錄永不搬，結案不換路徑）——
本 lint 把三類已發生的失真變機械閘門（codex 09-06 全 repo 審查 I-7）：
1. 同殼宣告多個互斥 projection SHA（一殼只能有一個 current identity）；
2. projection SHA 與同目錄 ep.md 的 content SHA 不符（stale projection）；
3. 回源連結失效：`file:///Users/` 絕對路徑（跨 worktree/clone 必斷）、
   `/ai-guide/<task path>` route 指向 repo 內不存在的路徑（歸檔/月份層未同步）；
4. 連結合約（09-14 裁決：ai-guide 退出 :6421 report server）：殼內 .md 連結
   採 repo 相對路徑（VSCode 直接開檔）——viewer URL 形態（127.0.0.1:6421、
   /viewer/_md-viewer.html）在活躍殼即 violation；歷史位置（_tasks/_archived/、
   reports/、blueprint/）殼留歷史態豁免，不回改。

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
# viewer URL 形態（09-14 退役）：活躍殼即 violation，歷史位置殼豁免
_VIEWER_URL = re.compile(r"""(?:127\.0\.0\.1:6421|localhost:6421|/viewer/_md-viewer\.html)""")
_HISTORICAL_PREFIXES = (
    "ai-analysis/_tasks/_archived/",
    "ai-analysis/reports/",
    "ai-analysis/blueprint/",
)


def _is_historical(shell: Path, repo_root: Path) -> bool:
    """殼位於歷史位置（_archived/＋reports/＋blueprint/）→ 留歷史態，豁免 viewer 檢查。"""
    rel = shell.relative_to(repo_root).as_posix()
    return rel.startswith(_HISTORICAL_PREFIXES)


def lint_shell(shell: Path, repo_root: Path) -> list[str]:
    """對單一殼跑各類檢查，回傳 violation 敘述清單（空＝通過）。"""
    text = shell.read_text(encoding="utf-8")
    issues: list[str] = []
    historical = _is_historical(shell, repo_root)
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
    viewer_hits = sorted(set(_VIEWER_URL.findall(text)))
    if viewer_hits and not historical:
        issues.append(
            "viewer URL 形態已退役（09-14 ai-guide 退出 :6421——改 repo 相對路徑，"
            f"歷史位置豁免）: {viewer_hits}"
        )
    for url in sorted(set(_RAW_MD_ROUTE.findall(text))):
        if url.startswith("file://"):
            continue  # file:// 另有專屬規則
        if "_md-viewer.html" in url:
            # viewer 形態：歷史殼豁免；活躍殼由上方 _VIEWER_URL 檢查統一承接——
            # 此處一律跳過，避免同一 viewer 連結被重複計數
            continue
        if _VIEWER_URL.search(url) and not historical:
            # 6421 host 上的 raw .md：活躍殼已由 viewer 規則承接（dedup，避免一物兩報）；
            # 歷史殼不跳過——raw 檢查維持原行為，避免豁免被誤鬆
            continue
        issues.append(
            f"raw .md http 連結（合約＝repo 相對路徑，VSCode 直接開檔）: {url}"
        )
    for rel in sorted(set(_ROUTE.findall(text))):
        target = repo_root / "ai-analysis" / urllib.parse.unquote(rel)
        if target.suffix in (".md", ".json") and not target.exists():
            issues.append(
                f"route 回源路徑不存在（任務歸檔/月份層未同步？）: ai-analysis/{rel}"
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
