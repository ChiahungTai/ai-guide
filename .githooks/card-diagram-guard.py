#!/usr/bin/env python3
# card-description-diagram guard v3——AIR-135.5 協議①機械化＋結案對偶（終態圖契約）。
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
# 逃生口（scoped，不關其他閘）：CARD_DIAGRAM_SKIP=1 git commit（須 user 同意並記卡 notes）。
# runtime：系統 python3（3.9）——禁 3.10+ 語法（pre-commit 同款約束）。
import os
import subprocess
import sys


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def extract_section(blob_text, name):
    lines = blob_text.splitlines()
    begins = [i for i, l in enumerate(lines) if f"SECTION:{name}:BEGIN" in l]
    ends = [i for i, l in enumerate(lines) if f"SECTION:{name}:END" in l]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        return False, f"SECTION:{name} markers malformed（須恰一 BEGIN／一 END 且 BEGIN 在前）"
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


def frontmatter_status(blob_text):
    lines = blob_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for l in lines[1:]:
        s = l.strip()
        if s == "---":
            break
        if s.startswith("status:"):
            return s[len("status:"):].strip().strip("'\"")
    return None


def staged_entries():
    r = sh("git", "-c", "core.quotePath=false", "diff", "--cached", "--name-status", "-M", "-C", "--", "backlog/tasks/*.md")
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
        print("[card-diagram] CARD_DIAGRAM_SKIP=1——本 guard 跳過（須 user 同意已記卡 notes；其他閘照跑）")
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
        is_entry = code.startswith(("A", "C")) or (src is not None and not src.startswith("backlog/tasks/"))
        needs_check = is_entry
        head_desc = None
        head_baseline_path = None
        if not needs_check:
            head_baseline_path = src if (code.startswith("R") and src) else dest
            head_blob = blob_at("HEAD:" + head_baseline_path)
            if head_blob is None:
                rc = max(rc, fail(dest, f"HEAD baseline（{head_baseline_path}）讀取失敗——無法證明 Description unchanged"))
                continue
            ok, head_desc = section_of(head_blob)
            if not ok:
                rc = max(rc, fail(dest, "HEAD baseline " + head_desc + "——parser 無法判定 unchanged（fail-closed）"))
                continue
            needs_check = head_desc != staged_desc
        if needs_check and not has_valid_mermaid(staged_desc):
            rc = max(rc, fail(dest, "Description 無有效 mermaid 圖——違反 AIR-135.5 開卡協議①（人話＋一張圖；須獨立 fence 行＋closing fence＋block 內至少一行非空白）。"))
        # 閘二：終態圖契約（non-Done→Done 且 entry baseline 有圖）
        staged_status = frontmatter_status(staged_blob)
        if staged_status == "Done":
            if is_entry:
                baseline_has_diagram = has_valid_mermaid(staged_desc)
                is_done_transition = True  # birth-Done entry 視同須齊
            else:
                head_status = frontmatter_status(blob_at("HEAD:" + head_baseline_path) or "")
                baseline_has_diagram = has_valid_mermaid(head_desc or "")
                is_done_transition = head_status != "Done"
            if is_done_transition and baseline_has_diagram:
                ok_fs, fs_or_err = extract_section(staged_blob, "FINAL_SUMMARY")
                if not ok_fs:
                    rc = max(rc, fail(dest, f"收 Done 缺 Final Summary——{fs_or_err}（終態圖契約：Final Summary 須帶一張 mermaid 終態圖）"))
                elif not has_valid_mermaid(fs_or_err):
                    rc = max(rc, fail(dest, "收 Done 缺終態圖——Final Summary 須帶一張有效 mermaid 圖（實作完成＝as-built；未實作即結案＝terminal disposition；AIR-135.5 協議①結案對偶，單一源＝kanban-board skill「終態圖契約」）。"))
    return rc


def fail(path, msg):
    print("FAIL[card-diagram] " + path, file=sys.stderr)
    print("  " + msg, file=sys.stderr)
    print("  修法：補圖後重 commit；user 明示同意免圖時 CARD_DIAGRAM_SKIP=1 git commit（其他閘照跑）並記卡 notes。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
