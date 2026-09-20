#!/usr/bin/env python3
# card-description-diagram guard v2——AIR-135.5 開卡協議①機械化：「Description 先行（人話＋一張圖）」。
# 判準：staged 的 backlog/tasks/*.md，managed-set entry（新增/copy/自 tasks 外移入）或
# Description byte delta（對 baseline）時，staged Description 須含 structurally-valid mermaid
# fence（獨立開 fence 行＋closing fence＋block 內至少一行非空白）。baseline：tasks→tasks
# rename 取 HEAD 來源路徑；其他修改取 HEAD 同路徑；drafts→tasks 視為 NEW。marker 須恰一
# BEGIN/END 且有序——malformed（staged 或 baseline）＝fail loud，不當 empty。
# 逃生口（scoped，不關其他閘）：CARD_DIAGRAM_SKIP=1 git commit（須 user 同意並記卡 notes）。
# runtime：系統 python3（3.9）——禁 3.10+ 語法（pre-commit 同款約束）。
import os
import subprocess
import sys


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True)


def section_of(blob_text):
    lines = blob_text.splitlines()
    begins = [i for i, l in enumerate(lines) if "SECTION:DESCRIPTION:BEGIN" in l]
    ends = [i for i, l in enumerate(lines) if "SECTION:DESCRIPTION:END" in l]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        return False, "SECTION markers malformed（須恰一 BEGIN／一 END 且 BEGIN 在前）"
    return True, "\n".join(lines[begins[0] + 1 : ends[0]])


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
        ok, staged_desc = section_of(staged_blob)
        if not ok:
            rc = max(rc, fail(dest, "staged " + staged_desc))
            continue
        is_entry = code.startswith("A") or code.startswith("C") or src is None or not src.startswith("backlog/tasks/")
        needs_check = is_entry
        if not needs_check:
            baseline_path = src if (code.startswith("R") and src) else dest
            head_blob = blob_at("HEAD:" + baseline_path)
            if head_blob is None:
                rc = max(rc, fail(dest, "HEAD baseline（%s）讀取失敗——無法證明 Description unchanged" % baseline_path))
                continue
            ok, head_desc = section_of(head_blob)
            if not ok:
                rc = max(rc, fail(dest, "HEAD baseline " + head_desc + "——parser 無法判定 unchanged（fail-closed）"))
                continue
            needs_check = head_desc != staged_desc
        if needs_check and not has_valid_mermaid(staged_desc):
            rc = max(rc, fail(dest, "Description 無有效 mermaid 圖——違反 AIR-135.5 開卡協議①（人話＋一張圖；須獨立 fence 行＋closing fence＋block 內至少一行非空白）。"))
    return rc


def fail(path, msg):
    print("FAIL[card-diagram] " + path, file=sys.stderr)
    print("  " + msg, file=sys.stderr)
    print("  修法：Description 補一張 mermaid 圖後重 commit；user 明示同意免圖時 CARD_DIAGRAM_SKIP=1 git commit（其他閘照跑）並記卡 notes。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
