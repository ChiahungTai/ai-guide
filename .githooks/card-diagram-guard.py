#!/usr/bin/env python3
# card-description-diagram guard v4——AIR-135.5 協議①機械化＋結案對偶（終態圖契約）
# ＋黑話掃描（v4／AIR-170 amendment：兩閘出處回註 AIR-135.5 開卡協議延伸）。
# 閘一（協議①，v2 既有）：staged 的 backlog/tasks/*.md，managed-set entry（新增/copy/自
# tasks 外移入）或 Description byte delta（對 baseline）時，staged Description 須含
# structurally-valid mermaid fence（獨立開 fence 行＋closing fence＋block 內至少一行非空白）。
#   baseline：tasks→tasks rename 取 HEAD 來源路徑；其他修改取 HEAD 同路徑；drafts→tasks
#   視為 NEW。marker 須恰一 BEGIN/END 且有序——malformed（staged 或 baseline）＝fail loud。
# 閘二（終態圖契約，v3 新增）：staged frontmatter status 為 Done 且非「HEAD 已 Done」
# （即 non-Done→Done transition；entry 卡 birth-Done 同樣要求）且 entry baseline 有 desc
# mermaid 時，Final Summary section 須含有效 mermaid fence（as-built；未實作即結案者畫
# terminal disposition）。HEAD 已 Done 的卡後續修改（typo/notes）不重觸發。entry baseline
# 無圖（legacy 卡）＝豁免——對偶條件：開卡有圖者結案須有終態圖。
# 閘三（黑話掃描，v4／AIR-170 新增）：Description 主體（section markers 內，含 mermaid
# 圖行）不得出現內部代號——D\d{1,2}、C\d{1,2}[ab]?、flash [ABC]、job-mu[a-z0-9-]+ 等
# 只有 AI 自己懂的詞（AIR-168/169 建卡事故 pattern）。觸發面同閘一（entry 或 Description
# delta 對 baseline）——既有卡未動 Description 的修改（Notes/Plan/Final Summary）不追殺
# legacy 黑話，下次改 Description 時順手搬（同閘一遷移語義）。豁免行：含路徑特徵
# （.agent-tmp/、backlog/、skills/、.md、http）＝證據指針行，不掃。命中＝擋 commit，
# 訊息列全檔行號＋命中詞。「說明是否人話」的語義判斷仍歸 user 確認 Description——
# 機械管結構、人管語義（AIR-170 設計邊界）。
# 逃生口（scoped，不關其他閘）：CARD_DIAGRAM_SKIP=1 git commit（須 user 同意並記卡 notes）。
# runtime：系統 python3（3.9）——禁 3.10+ 語法（pre-commit 同款約束）。
import os
import re
import subprocess
import sys

# 內部代號 pattern（AIR-168/169 實例；大小寫敏感——D/C 大寫、flash 小寫）
# F1：單 token 代號用 ASCII-class lookaround 取代 \b——Python re Unicode 模式下
# CJK 屬 \w，「這卡修D4」接鄰時 \b 邊界失效（零命中實證）；lookaround 僅認
# ASCII 字母數字為鄰接（_ 不算鄰接，D4_ 仍命中——identifier 內嵌代號本屬黑話）。
JARGON_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9])D\d{1,2}(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])C\d{1,2}[ab]?(?![A-Za-z0-9])"),
    re.compile(r"\bflash [ABC]\b"),
    re.compile(r"\bjob-mu[a-z0-9-]+"),
]
# 豁免行 token：命中任一＝證據指針行（路徑/連結），不算主體黑話
JARGON_EXEMPT_TOKENS = (".agent-tmp/", "backlog/", "skills/", ".md", "http")
JARGON_REMEDY = (
    "內部代號禁入 Description 主體，改寫為人話（證據指針留結尾）；"
    "改後重 commit；user 明示同意放行時 CARD_DIAGRAM_SKIP=1 git commit"
    "（其他閘照跑）並記卡 notes。"
)


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def extract_section(blob_text, name):
    lines = blob_text.splitlines()
    begins = [i for i, l in enumerate(lines) if f"SECTION:{name}:BEGIN" in l]
    ends = [i for i, l in enumerate(lines) if f"SECTION:{name}:END" in l]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        return (
            False,
            f"SECTION:{name} markers malformed（須恰一 BEGIN／一 END 且 BEGIN 在前）",
        )
    return True, "\n".join(lines[begins[0] + 1 : ends[0]])


def section_of(blob_text):
    return extract_section(blob_text, "DESCRIPTION")


def has_valid_mermaid(section_text):
    lines = section_text.splitlines()
    for i, l in enumerate(lines):
        if l.strip() != "```mermaid":
            continue
        close = None
        for j in range(i + 1, len(lines)):
            if lines[j].strip() == "```":
                close = j
                break
        if close is not None and any(x.strip() for x in lines[i + 1 : close]):
            return True
    return False


def scan_description_jargon(blob_text):
    """閘三：Description 主體黑話掃描——回 [(全檔 1-based 行號, 命中詞串), ...]。

    只掃 SECTION:DESCRIPTION markers 內（含 mermaid 圖行——人話＋一張圖同標準）；
    mermaid 節點 id 同在掃描面（F2 註記——用 D1/D2 當節點 id 會被擋，改節點名即可）。
    含路徑特徵 token 的行＝證據指針行豁免。markers 在呼叫前已由 section_of 驗證，
    此處防禦性再找——malformed 回 []（該路徑已由閘一 fail loud，不重複擋）。
    """
    lines = blob_text.splitlines()
    begins = [i for i, l in enumerate(lines) if "SECTION:DESCRIPTION:BEGIN" in l]
    ends = [i for i, l in enumerate(lines) if "SECTION:DESCRIPTION:END" in l]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        return []
    hits = []
    for i in range(begins[0] + 1, ends[0]):
        line = lines[i]
        if any(tok in line for tok in JARGON_EXEMPT_TOKENS):
            continue
        found = []
        for pat in JARGON_PATTERNS:
            for m in pat.finditer(line):
                if m.group(0) not in found:
                    found.append(m.group(0))
        if found:
            hits.append((i + 1, "、".join(found)))
    return hits


def frontmatter_status(blob_text):
    lines = blob_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for l in lines[1:]:
        s = l.strip()
        if s == "---":
            break
        if s.startswith("status:"):
            return s[len("status:") :].strip().strip("'\"")
    return None


def staged_entries():
    r = sh(
        "git",
        "-c",
        "core.quotePath=false",
        "diff",
        "--cached",
        "--name-status",
        "-M",
        "-C",
        "--",
        "backlog/tasks/*.md",
    )
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            src = parts[1] if len(parts) > 2 else None
            out.append((parts[0], parts[-1], src))
    return out


def blob_at(ref_and_path):
    r = sh("git", "show", ref_and_path)
    return r.stdout if r.returncode == 0 else None


def main():
    if os.environ.get("CARD_DIAGRAM_SKIP") == "1":
        print(
            "[card-diagram] CARD_DIAGRAM_SKIP=1——本 guard 跳過（須 user 同意已記卡 notes；其他閘照跑）"
        )
        return 0
    rc = 0
    for code, dest, src in staged_entries():
        if code.startswith("D"):
            continue  # 刪卡不需圖；rename 未達相似度時拆成 D+A，A 側照 gate
        staged_blob = blob_at(":" + dest)
        if staged_blob is None:
            rc = max(rc, fail(dest, "staged blob 讀取失敗（index 不一致）"))
            continue
        # 閘一：Description 圖（協議①）
        ok, staged_desc = section_of(staged_blob)
        if not ok:
            rc = max(rc, fail(dest, "staged " + staged_desc))
            continue
        # entry＝A/C 新增，或 rename 源在 tasks 外（drafts→tasks）；純 M 修改＝非 entry
        # （v2 潛伏 bug 修正：`src is None` 曾把 M 也判 entry，靠「全卡都有圖」掩蓋）
        is_entry = code.startswith(("A", "C")) or (
            src is not None and not src.startswith("backlog/tasks/")
        )
        needs_check = is_entry
        head_desc = None
        head_baseline_path = None
        if not needs_check:
            head_baseline_path = src if (code.startswith("R") and src) else dest
            head_blob = blob_at("HEAD:" + head_baseline_path)
            if head_blob is None:
                rc = max(
                    rc,
                    fail(
                        dest,
                        f"HEAD baseline（{head_baseline_path}）讀取失敗——無法證明 Description unchanged",
                    ),
                )
                continue
            ok, head_desc = section_of(head_blob)
            if not ok:
                rc = max(
                    rc,
                    fail(
                        dest,
                        "HEAD baseline "
                        + head_desc
                        + "——parser 無法判定 unchanged（fail-closed）",
                    ),
                )
                continue
            needs_check = head_desc != staged_desc
        if needs_check:
            if not has_valid_mermaid(staged_desc):
                rc = max(
                    rc,
                    fail(
                        dest,
                        "Description 無有效 mermaid 圖——違反 AIR-135.5 開卡協議①（人話＋一張圖；須獨立 fence 行＋closing fence＋block 內至少一行非空白）。",
                    ),
                )
            # 閘三：黑話掃描（AIR-170 v4）——與閘一同觸發面（entry／desc delta）
            jargon = scan_description_jargon(staged_blob)
            if jargon:
                detail = "\n".join(f"    line {ln}: {words}" for ln, words in jargon)
                rc = max(
                    rc,
                    fail(
                        dest,
                        "Description 黑話命中——內部代號禁入 Description 主體，改寫為人話（證據指針留結尾）：\n"
                        + detail,
                        JARGON_REMEDY,
                    ),
                )
        # 閘二：終態圖契約（non-Done→Done 且 entry baseline 有圖）
        staged_status = frontmatter_status(staged_blob)
        if staged_status == "Done":
            if is_entry:
                baseline_has_diagram = has_valid_mermaid(staged_desc)
                is_done_transition = True  # birth-Done entry 視同須齊
            else:
                head_status = frontmatter_status(
                    blob_at("HEAD:" + head_baseline_path) or ""
                )
                baseline_has_diagram = has_valid_mermaid(head_desc or "")
                is_done_transition = head_status != "Done"
            if is_done_transition and baseline_has_diagram:
                ok_fs, fs_or_err = extract_section(staged_blob, "FINAL_SUMMARY")
                if not ok_fs:
                    rc = max(
                        rc,
                        fail(
                            dest,
                            f"收 Done 缺 Final Summary——{fs_or_err}（終態圖契約：Final Summary 須帶一張 mermaid 終態圖）",
                        ),
                    )
                elif not has_valid_mermaid(fs_or_err):
                    rc = max(
                        rc,
                        fail(
                            dest,
                            "收 Done 缺終態圖——Final Summary 須帶一張有效 mermaid 圖（實作完成＝as-built；未實作即結案＝terminal disposition；AIR-135.5 協議①結案對偶，單一源＝kanban-board skill「終態圖契約」）。",
                        ),
                    )
    return rc


def fail(path, msg, remedy=None):
    print("FAIL[card-diagram] " + path, file=sys.stderr)
    print("  " + msg, file=sys.stderr)
    if remedy is None:
        remedy = "補圖後重 commit；user 明示同意免圖時 CARD_DIAGRAM_SKIP=1 git commit（其他閘照跑）並記卡 notes。"
    print("  修法：" + remedy, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
