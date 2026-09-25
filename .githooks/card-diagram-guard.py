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
# 結案結構 predicate 群（v5／AIR-193 切片二）：staged frontmatter status==Done 時加驗——
#   a. AC 殘留：<!-- AC:BEGIN/END --> 區塊內 `- [ ]` 計數>0＝擋；未勾行同行帶豁免標註
#      （AC_EXEMPT_MARKERS：歸 AIR-／移交／拆卡／總驗）不計，全帶標註＝不擋
#      （AIR-181 破口：結案漏 tick 七格零 catcher）。
#   b. status 軌跡：HEAD 非 In Progress（To Do／無 HEAD 版本＝birth-Done／其他值）而
#      staged=Done＝擋；HEAD 已 Done 的後續編輯非軌跡事件不重觸發（AIR-135.3 破口：
#      To Do 直達 Done；軌跡合法形＝In Progress→Done）。
#   c. 五段 marker：DESCRIPTION/AC/NOTES/PLAN/FINAL_SUMMARY 各恰一組 BEGIN/END 且有序，
#      缺失或雙包裹＝擋（kanban「卡即 handoff」五段組成；雙包裹真實案例＝kanban
#      「卡編輯前查驗」）。AC 段為 <!-- AC:BEGIN/END --> 專屬 marker，餘四段 SECTION:*。
#   d. refs 落地對照（警告級，不擋）：frontmatter references 逐筆 git ls-files 查無＝
#      stderr 警告。TODO：warning 面收窄為擋的觀察期——MOS-28（refs 指向未 commit 路徑）。
# skip 語義分離（AIR-193）：CARD_DIAGRAM_SKIP=1 由「一鍵關全 guard」收窄為只豁免圖在場／
# 黑話檢查（閘一 desc 圖／閘二終態圖／閘三黑話）；結構 predicate a-c fail-closed 不受其
# 豁免——逃生口另設 CARDCLOSE_STRUCT_SKIP=1（stderr 大聲標注，須 user 同意並記卡 notes）。
# hooksPath 探針（AIR-193）：core.hooksPath 未指向本 repo .githooks＝閘未上線的 fail-open
# 面——stderr 顯性警告一行，探針性質不擋。
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


# ── 結案結構 predicate 群（v5／AIR-193 切片二）────────────────────────────
# 純函式契約：讀卡檔字串 → 人話違規清單（空＝過）。scripts/closeout_check.py
# （複查腿 CLI）import 這些函式消費——判定邏輯單一源，禁二刻。
AC_BEGIN = "<!-- AC:BEGIN -->"
AC_END = "<!-- AC:END -->"
# 豁免標註（工作序候選集）：未勾行同行含任一＝顯性拆卡/移交/總驗標註，不計殘留
AC_EXEMPT_MARKERS = ("歸 AIR-", "移交", "拆卡", "總驗")
# 卡面五段（kanban「卡即 handoff」：desc＋plan＋AC＋notes＋references 拼裝即 handoff，
# 結案加 Final Summary）；AC 段用專屬 marker，其餘四段 SECTION:* 形
CARD_SECTIONS = ("DESCRIPTION", "AC", "NOTES", "PLAN", "FINAL_SUMMARY")
STRUCT_REMEDY = (
    "結案結構 predicate（AIR-193）：補齊後重 commit；本類 fail-closed，CARD_DIAGRAM_SKIP "
    "豁免不到——user 明示同意放行時 CARDCLOSE_STRUCT_SKIP=1 git commit 並記卡 notes。"
)


def section_marker_violations(blob_text):
    """predicate c：五段各恰一組 BEGIN/END 且有序——回人話違規清單（空＝過）。

    缺失（0/0）與 malformed（重複／缺一／逆序）分列；AC 段用 <!-- AC:* --> 專屬
    marker，其餘四段 SECTION:*。
    存量相容（marshal seal 裁定 0925）：AC 缺失以 markdown 標題 `## Acceptance
    Criteria` fallback（Backlog CLI 建卡 AC 落 DESCRIPTION 區內無 marker——實證
    air-194/196）；PLAN/NOTES 缺失降 warning（section_marker_warnings），不擋。
    """
    lines = blob_text.splitlines()
    out = []
    for name in CARD_SECTIONS:
        if name == "AC":
            b_lit, e_lit = AC_BEGIN, AC_END
            has_fallback = "## Acceptance Criteria" in blob_text
        else:
            b_lit = f"SECTION:{name}:BEGIN"
            e_lit = f"SECTION:{name}:END"
            has_fallback = False
        bs = [i for i, l in enumerate(lines) if b_lit in l]
        es = [i for i, l in enumerate(lines) if e_lit in l]
        if not bs and not es:
            if name in ("PLAN", "NOTES"):
                continue  # 降 warning——歸 section_marker_warnings
            if has_fallback:
                continue  # AC 標題 fallback 在場＝段在場
            out.append(
                f"{name} section 缺失（{b_lit}／{e_lit} 皆無）——"
                "收 Done 卡須五段齊（kanban「卡即 handoff」）"
            )
        elif len(bs) != 1 or len(es) != 1 or bs[0] >= es[0]:
            out.append(
                f"{name} markers malformed（BEGIN×{len(bs)}／END×{len(es)}，"
                "須恰一組且 BEGIN 在前）——雙包裹真實案例見 kanban「卡編輯前查驗」"
            )
    return out


def section_marker_warnings(blob_text):
    """predicate c 警告腿：PLAN/NOTES section 缺失（存量相容——不擋，stderr 提示補段）。"""
    lines = blob_text.splitlines()
    out = []
    for name in ("PLAN", "NOTES"):
        b_lit = f"SECTION:{name}:BEGIN"
        e_lit = f"SECTION:{name}:END"
        if not any(b_lit in l or e_lit in l for l in lines):
            out.append(f"{name} section 缺失（存量卡相容）——補段以合「卡即 handoff」五段齊")
    return out


def ac_residue_violations(blob_text):
    """predicate a：AC 區塊內 `- [ ]` 殘留——未勾行同行帶豁免標註者不計（AIR-181 破口）。

    全部未勾行都帶標註＝不擋。AC markers 缺損時 fallback 掃 `## Acceptance Criteria`
    標題區塊（到下一個 `## ` 標題為止——Backlog CLI 建卡 AC 在 DESCRIPTION 區內無
    marker 的實證格式，air-194/196；fallback 亦無＝回 [] 歸 predicate c 擋）。
    """
    lines = blob_text.splitlines()
    begins = [i for i, l in enumerate(lines) if AC_BEGIN in l]
    ends = [i for i, l in enumerate(lines) if AC_END in l]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        heads = [i for i, l in enumerate(lines) if l.strip() == "## Acceptance Criteria"]
        if not heads:
            return []
        tail = next((j for j in range(heads[0] + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
        begins, ends = [heads[0]], [tail]
    residue = []
    for i in range(begins[0] + 1, ends[0]):
        line = lines[i]
        if "- [ ]" not in line:
            continue
        if any(m in line for m in AC_EXEMPT_MARKERS):
            continue
        residue.append((i + 1, line.strip()))
    if not residue:
        return []
    detail = "\n".join(f"      line {ln}: {txt[:100]}" for ln, txt in residue)
    return [
        f"AC 殘留 {len(residue)} 格未勾（豁免標註：{'／'.join(AC_EXEMPT_MARKERS)}）：\n{detail}"
    ]


def status_trajectory_violation(head_status, staged_status):
    """predicate b：進入 Done 的軌跡——回人話違規（None＝過）。

    合法：In Progress→Done；HEAD 已 Done（後續編輯非軌跡事件，同閘二不重觸發語義）。
    擋：To Do／無 HEAD 版本（birth-Done）／其他值 → Done（AIR-135.3 破口：To Do 直達
    Done；receipt-gate 只驗 commit 時點，本 predicate 補 HEAD vs staged diff 腿）。
    """
    if staged_status != "Done":
        return None
    if head_status in ("Done", "In Progress"):
        return None
    shown = head_status or "（無 HEAD 版本——birth-Done 或 baseline 無 status）"
    return (
        f"status 軌跡非法：HEAD={shown} → staged=Done——"
        "進入 Done 須自 In Progress（AIR-135.3 破口：To Do 直達 Done）"
    )


def frontmatter_references(blob_text):
    """frontmatter references 清單（原樣；http／空由消費端過濾）。"""
    lines = blob_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    in_refs = False
    for l in lines[1:]:
        s = l.strip()
        if s == "---":
            break
        if s.startswith("references:"):
            val = s[len("references:"):].strip()
            if val and val != "[]":
                out.append(val.strip("'\""))
            in_refs = True
            continue
        if in_refs:
            if s.startswith("- "):
                out.append(s[2:].strip().strip("'\""))
            elif s:
                in_refs = False
    return out


def missing_ref_paths(blob_text, is_tracked):
    """predicate d（警告級）：references 逐筆對 is_tracked——回未落地路徑清單。

    is_tracked: callable(path)->bool（git ls-files 存取在呼叫端——判定源單一、
    git 存取留外，CLI 複查腿同一函式消費）。http(s) 與空值略過。
    """
    return [
        p
        for p in frontmatter_references(blob_text)
        if p and not p.startswith(("http://", "https://")) and not is_tracked(p)
    ]


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


def warn(path, msg):
    print("WARN[card-diagram] " + path, file=sys.stderr)
    print("  " + msg, file=sys.stderr)


def hooks_path_warning():
    """AIR-193 #2：hooksPath 未指向本 repo .githooks＝閘未上線的 fail-open 面——顯性警告，不擋。"""
    root = sh("git", "rev-parse", "--show-toplevel")
    if root.returncode != 0:
        return  # 非 repo 等——探針自身不添亂
    cfg = sh("git", "config", "core.hooksPath")
    # unset（returncode!=0、stdout 空）＝「未設」非「無法判定」——兩者分流（探針死碼修正）
    configured = cfg.stdout.strip() if cfg.returncode == 0 else ""
    toplevel = os.path.abspath(root.stdout.strip())
    if not configured:
        print(
            "WARN[card-diagram] core.hooksPath 未設——本 guard 等治理閘在此 clone 未上線"
            "（fail-open 面）；上線：git config core.hooksPath .githooks",
            file=sys.stderr,
        )
        return
    resolved = os.path.normpath(os.path.join(toplevel, os.path.expanduser(configured)))
    if resolved != os.path.normpath(os.path.join(toplevel, ".githooks")):
        print(
            f"WARN[card-diagram] core.hooksPath={configured} 非本 repo .githooks——"
            "本 guard 可能不在 commit 路徑上（fail-open 面）",
            file=sys.stderr,
        )


def _is_tracked(path):
    return bool(sh("git", "ls-files", "--", path).stdout.strip())


def main():
    rc = 0
    skip_diagram = os.environ.get("CARD_DIAGRAM_SKIP") == "1"
    skip_struct = os.environ.get("CARDCLOSE_STRUCT_SKIP") == "1"
    if skip_diagram:
        print(
            "[card-diagram] CARD_DIAGRAM_SKIP=1——僅豁免圖在場／黑話檢查（閘一 desc 圖／"
            "閘二終態圖／閘三黑話）；結案結構 predicate（AC 殘留／status 軌跡／五段 marker）"
            "屬 fail-closed 照跑。須 user 同意並記卡 notes。",
            file=sys.stderr,
        )
    if skip_struct:
        print(
            "[card-diagram] CARDCLOSE_STRUCT_SKIP=1——結案結構 predicate（AC 殘留／"
            "status 軌跡／五段 marker）本輪跳過！fail-closed 逃生口，須 user 同意並記卡 notes。",
            file=sys.stderr,
        )
    hooks_path_warning()
    for code, dest, src in staged_entries():
        if code.startswith("D"):
            continue  # 刪卡不需圖；rename 未達相似度時拆成 D+A，A 側照 gate
        staged_blob = blob_at(":" + dest)
        if staged_blob is None:
            rc = max(rc, fail(dest, "staged blob 讀取失敗（index 不一致）"))
            continue
        staged_status = frontmatter_status(staged_blob)
        # entry＝A/C 新增，或 rename 源在 tasks 外（drafts→tasks）；純 M 修改＝非 entry
        # （v2 潛伏 bug 修正：`src is None` 曾把 M 也判 entry，靠「全卡都有圖」掩蓋）
        is_entry = code.startswith(("A", "C")) or (
            src is not None and not src.startswith("backlog/tasks/")
        )
        head_baseline_path = (
            None if is_entry else (src if (code.startswith("R") and src) else dest)
        )
        # 結案結構 predicate 群（AIR-193 v5）：staged Done 觸發；fail-closed——
        # CARD_DIAGRAM_SKIP 豁免不到，逃生口＝CARDCLOSE_STRUCT_SKIP（見檔頭）。
        if staged_status == "Done" and not skip_struct:
            for v in section_marker_violations(staged_blob):
                rc = max(rc, fail(dest, v, STRUCT_REMEDY))
            for v in section_marker_warnings(staged_blob):
                warn(dest, v)
            for v in ac_residue_violations(staged_blob):
                rc = max(rc, fail(dest, v, STRUCT_REMEDY))
            head_status = None
            if not is_entry:
                head_status = frontmatter_status(
                    blob_at("HEAD:" + head_baseline_path) or ""
                )
            v = status_trajectory_violation(head_status, staged_status)
            if v:
                rc = max(rc, fail(dest, v, STRUCT_REMEDY))
        # predicate d（警告級，不擋——豁免鍵影響不到警告面）
        if staged_status == "Done":
            for p in missing_ref_paths(staged_blob, _is_tracked):
                warn(dest, f"refs 路徑 git 查無（未落地？MOS-28 型）：{p}")
        # 閘一：Description 圖（協議①）
        ok, staged_desc = section_of(staged_blob)
        if not ok:
            rc = max(rc, fail(dest, "staged " + staged_desc))
            continue
        needs_check = is_entry
        head_desc = None
        if not needs_check:
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
        if needs_check and not skip_diagram:
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
        # 閘二：終態圖契約（non-Done→Done 且 entry baseline 有圖）——CARD_DIAGRAM_SKIP 豁免面
        if staged_status == "Done" and not skip_diagram:
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
