#!/usr/bin/env python
"""skills corpus desc 契約機械掃（AIR-87 AC#1）。

契約源＝ZCode 官方（zcode-guide/diagnosing-skills）＋AIR-87 段落 0 實證：
- drop 軸＝desc「值」>1024 **chars**（非整行、非 bytes；name/description 缺失同 drop）
- 形式 gate＝雙引號單行或 block scalar（bare unquoted 有 ' #' 雙解析器分歧風險）
- 觸發呈現截 desc 前 ~250 chars——前 250 無觸發語義屬 AC#2 人工改寫面，本掃只提示

已知限制（量法近似）：
- block scalar 量法＝space-fold 近似（非完整 YAML 折疊語義）
- frontmatter 跨多個 block key 的連續行會混收（本 corpus 僅 maintain/scan-project
  兩支單鍵 block，實害零）

用法：uv run python scripts/scan_skills_desc.py [--root <skills 根]
exit 0＝全綠；exit 1＝有 FAIL。
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

LIMIT = 1024
# 形式 gate 只認雙引號（Fr2/Pr4）——單引號包夾不算 quoted-form，收緊為 form "single" fail
QUOTE_FORMS = ('"',)


BLOCK_MARKERS = {">", "|", ">-", "|-", ">+", "|+"}


@dataclass
class ScanResult:
    skill: str
    form: str  # quoted / single / bare / block / missing
    value_chars: int
    hash_trap: bool  # bare 值含 ' #'——完整 YAML 剝註解、flat parser 不剝
    quoted_hash: bool  # quoted 值含 ' #'——安全但追蹤
    missing_name: bool

    @property
    def failures(self) -> list[str]:
        out = []
        if self.form == "missing":
            out.append("desc missing (skill dropped)")
        if self.missing_name:
            out.append("name missing (skill dropped)")
        if self.value_chars > LIMIT:
            out.append(f"value {self.value_chars} chars > {LIMIT} (skill dropped)")
        if self.form == "bare":
            out.append("bare unquoted desc (quote gate)")
        if self.form == "single":
            out.append("single-quoted desc (double-quote gate)")
        if self.hash_trap:
            out.append("' #' in bare desc (dual-parser divergence)")
        return out

    @property
    def is_fail(self) -> bool:
        return bool(self.failures)


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """flat key:value 解析＋block scalar 連續行折疊（回傳值與原始連續行）。"""
    meta: dict[str, str] = {}
    block_lines: list[str] = []
    in_fm = False
    block_key: str | None = None
    for line in lines:
        if not in_fm:
            if line.strip() == "---":
                in_fm = True
            continue
        if line.strip() == "---":
            break
        if block_key is not None:
            if line.startswith((" ", "\t")):
                block_lines.append(line.strip())
                continue
            block_key = None
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            meta[key] = val
            if val in BLOCK_MARKERS:
                block_key = key
    return meta, block_lines


def scan_skill(skill_dir: Path) -> ScanResult:
    path = skill_dir / "SKILL.md"
    # utf-8-sig：剝 BOM（Fr9）
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    meta, block_lines = _parse_frontmatter(lines)
    desc = meta.get("description", "")
    missing_name = "name" not in meta or not meta["name"]
    if not desc:
        return ScanResult(skill_dir.name, "missing", 0, False, False, missing_name)
    if desc in BLOCK_MARKERS and block_lines:
        return ScanResult(
            skill_dir.name,
            "block",
            len(" ".join(block_lines)),
            False,
            False,
            missing_name,
        )
    if len(desc) >= 2 and desc[0] in QUOTE_FORMS and desc[-1] == desc[0]:
        inner_hash = " #" in desc[1:-1]
        return ScanResult(
            skill_dir.name, "quoted", len(desc), False, inner_hash, missing_name
        )
    if len(desc) >= 2 and desc[0] == "'" and desc[-1] == "'":
        return ScanResult(
            skill_dir.name, "single", len(desc), False, False, missing_name
        )
    return ScanResult(
        skill_dir.name, "bare", len(desc), " #" in desc, False, missing_name
    )


def fix_skill(skill_dir: Path) -> bool:
    """bare desc 引號化（僅 frontmatter description 行；含內部雙引號者跳過留人工）。"""
    path = skill_dir / "SKILL.md"
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    in_fm = False
    for i, line in enumerate(lines):
        s = line.rstrip("\n")
        if not in_fm:
            if s.strip() == "---":
                in_fm = True
            continue
        if s.strip() == "---":
            break
        if s.startswith("description:"):
            r = scan_skill(skill_dir)
            if r.form == "bare" and '"' not in line[len("description:") :]:
                val = line[len("description:") :].strip()
                lines[i] = f'description: "{val}"\n'
                path.write_text("".join(lines), encoding="utf-8")
                return True
            return False
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="skills", help="skills 根目錄（預設 ./skills）")
    ap.add_argument(
        "--headroom", type=int, default=0, help="FAIL 門檻再降 N chars（餘裕檢查用）"
    )
    ap.add_argument("--fix", action="store_true", help="bare desc 引號化後重掃")
    args = ap.parse_args(argv)

    root = Path(args.root)
    dirs = sorted(d for d in root.iterdir() if (d / "SKILL.md").is_file())
    if args.fix:
        fixed = [d.name for d in dirs if fix_skill(d)]
        print(
            f"--- fix: quoted {len(fixed)} bare descs: {', '.join(fixed) or '(none)'}"
        )
        dirs = sorted(d for d in root.iterdir() if (d / "SKILL.md").is_file())
    fail_n = warn_n = 0
    print(f"{'skill':30} {'form':8} {'chars':>6}  notes")
    for d in dirs:
        r = scan_skill(d)
        notes: list[str] = []
        if args.headroom and r.value_chars > LIMIT - args.headroom:
            notes.append(f"within {args.headroom} of limit")
        if r.quoted_hash:
            notes.append("quoted ' #' tracked")
        notes += r.failures
        if r.is_fail:
            fail_n += 1
            notes.append("<FAIL>")
        elif notes:
            warn_n += 1
            notes.append("<WARN>")
        print(f"{r.skill:30} {r.form:8} {r.value_chars:>6}  {'; '.join(notes)}")
    print(f"--- {len(dirs)} skills; FAIL={fail_n} WARN={warn_n}")
    return 1 if fail_n else 0


if __name__ == "__main__":
    sys.exit(main())
