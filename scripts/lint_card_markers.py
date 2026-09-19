#!/usr/bin/env python3
"""Backlog 卡片結構標記 lint——AC/SECTION 標記配對檢查。

背景（0919 根因）：tri 對照修正批（R7 2d63df4c 斷 air-135.1、R8 e95975c8 斷
parent AIR-135）用 raw Edit 改寫 AC 區塊，new_string 重出 AC 條目時吃掉開頭標記
（parent 連 `## Acceptance Criteria` 標題、135.1 只掉 `<!-- AC:BEGIN -->`）；
`<!-- AC:END -->` 在編輯範圍外存活成孤兒。後果：backlog CLI 對該卡所有編輯
fail-closed 拒寫、AC 機械可投影面（135.2 AC#3 invariant）破損。

檢查項（逐檔）：
1. `<!-- AC:BEGIN -->` 與 `<!-- AC:END -->` 數量配對
2. 有 AC item（`- [ ] #N`）⇒ 必有 `## Acceptance Criteria` 標題
3. 有 item 或標題 ⇒ 必有 AC:BEGIN
4. `<!-- SECTION:<name>:BEGIN/END -->` 逐 name 配對

用法：
  uv run python scripts/lint_card_markers.py [files...]  # 無參＝掃 backlog/tasks/＋archive
exit 0＝乾淨；exit 1＝有損傷（逐檔列 DAMAGE 行）。

掛點：週日治理看照段 3（已掛）；pre-commit backlog fast-path（queued——.githooks
屬控制面，走 air-135 卡 branch 條文收編批）。
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_GLOBS = ["backlog/tasks/*.md", "backlog/archive/tasks/*.md"]
RE_AC_BEGIN = re.compile(r"<!-- AC:BEGIN -->")
RE_AC_END = re.compile(r"<!-- AC:END -->")
RE_AC_HEADING = re.compile(r"^## Acceptance Criteria\s*$", re.MULTILINE)
RE_AC_ITEM = re.compile(r"^- \[ \] #", re.MULTILINE)
RE_SECTION = re.compile(r"<!-- SECTION:(\w+):(BEGIN|END) -->")


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    n_begin = len(RE_AC_BEGIN.findall(text))
    n_end = len(RE_AC_END.findall(text))
    has_heading = bool(RE_AC_HEADING.search(text))
    has_items = bool(RE_AC_ITEM.search(text))
    if n_begin != n_end:
        problems.append(f"AC 標記不配對 BEGIN={n_begin} END={n_end}")
    if has_items and not has_heading:
        problems.append("有 AC item 但缺 '## Acceptance Criteria' 標題")
    if (has_items or has_heading) and n_begin == 0:
        problems.append("AC 內容在場但缺 <!-- AC:BEGIN -->")
    balance: dict[str, int] = {}
    for m in RE_SECTION.finditer(text):
        delta = 1 if m.group(2) == "BEGIN" else -1
        balance[m.group(1)] = balance.get(m.group(1), 0) + delta
    for name, count in sorted(balance.items()):
        if count != 0:
            problems.append(f"SECTION:{name}:BEGIN/END 不配對（balance={count}）")
    return problems


def main() -> int:
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        files = sorted(path for pattern in DEFAULT_GLOBS for path in REPO.glob(pattern))
    damaged = 0
    for f in files:
        try:
            problems = check_file(f)
        except (OSError, UnicodeDecodeError) as exc:
            problems = [f"讀取失敗：{exc}"]
        if problems:
            damaged += 1
            for problem in problems:
                print(f"DAMAGE {f}: {problem}")
    print(f"[lint_card_markers] scanned={len(files)} damaged={damaged}")
    return 1 if damaged else 0


if __name__ == "__main__":
    sys.exit(main())
