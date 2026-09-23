#!/usr/bin/env python3
r"""
PreToolUse hook（matcher Edit|Write）: memory 寫入治理（兩層）。

① MEMORY.md 手寫攔截——索引是 _generate_index.py 的機械投影（條目檔
   frontmatter = 單一寫入點），手寫必漂移：索引載入＝200 行或 25,000 字元
   先到為準，超限截斷（附 WARNING，尾端條目不載）→ cluster 查重漏同主題
   → 近重複寫入正回授（2026-08-30 mosaic 56.6KB 實證）。
② 條目檔寫入檢查（2026-09-01 寫入治理）——對應 rules/context-management.md
   寫入五問 Q1/Q2/Q4：
   - frontmatter description >100 chars → 擋（索引行原料＝寫入紀律值，
     name×2 重複已佔索引行 40% 開銷，desc 是主要槓桿）
   - desc 含 hash 兩形態（commit-前綴 09-05 S2/AIR-25＋同日 digit-lookahead 補強；
     bare hash 09-10 擴——mosaic「收案 93715b60a」繞過實證）→ 擋：
     hash 屬 git log 可推導（官方 skip-derivable），desc＝觸發詞＋一句鉤子。
   - desc 含日期 MM-DD／sess_ 形態（09-10 M2 實作——收案群「09-09」流入實證）→ 擋：
     易變快照住 body／卡，desc 只留觸發詞＋鉤子（存量不溯及）。
     邊界：\b 擋 "recommit" 誤傷；複數/大寫 hex 涵蓋；digit-lookahead 排除
     「commit feedback/facade/defaced」類純字母 hex 偽陽性（mosaic 實戰案例）；
     只查 desc 不查 body（body 引 hash 是歷史合法引用，另有 12K 膨脹治理）。
   - 條目檔膨脹 >12,000 chars → 擋（Write 看 content 全長；Edit 只擋
     「變大且超限」方向——收斂型編輯放行，不卡 audit 收縮既有肥檔）。
     超額內容多屬 repo 可推導（EP 進度/git log），該住 EP 檔而非 memory。
③ 放置閘（2026-09-13）——新建條目（檔不存在）非阻斷 stderr 注入六問指針
   （memory-audit skill「hook 擴充」①設計；弧收案慣性 09-11/09-12 兩晚
   project_ 類新流入 87.5% 違 Q1 實證——結案蒸餾掛點攔不到「收案當下新寫」，
   提醒須在寫入瞬間；機械觸發禁語義偵測）。
④ 狀態後綴擋（AIR-100 S-B）——新建條目 stem 命中弧狀態後綴（-pending/
   -inflight/-in-flight/-landed/-done/-closed 六枚舉凍結於 air-90 卡）→ exit 2：
   弧狀態屬卡/report 定義域，非記憶定義域。只擋新建；既有條目收斂編輯與
   改名退役暫時寫入放行。inbox 消費側對等檢查（非機械，轉寫面）＝
   memory-audit skill「Inbox 消費」節。
Self-gating：同目錄無 _generate_index.py 的專案不攔（裝 script 即 opt-in）。
對應 rule: rules/context-management.md「Memory 生命周期規範」。
覆蓋邊界：僅攔 Edit/Write 工具面的 file_path——Bash redirect（echo >>/tee）不攔
（紀律面處理）；**NotebookEdit out-of-scope**（AIR-100 S-C 處置 (a) 移 matcher 字面
——payload 路徑鍵是 notebook_path 非 file_path、池治理場景零 .ipynb 流量；
handler 曾有的 NotebookEdit matcher 字面＝dead-matcher，2026-09-17 移除，
parity assertion＝tests/test_matcher_parity.py 防再生）；**subagent 寫入不觸發本 hook**（ZCode 實證 2026-09-01：subagent
Write 16,154 chars 落地無攔）——治理範圍＝主 session，寫入型 subagent（如
mem-distill）的上限是 prompt 紀律非機械強制。ZCode 端 exit 2 產生 deny 已證
（官方文檔）；stderr 指引送達模型未證（EP A3 deferred）——失敗跡象＝無解釋重試，
回滾按 memory-hooks-rollback.md。
hook crash（非 0 非 2 exit）為非阻斷，工具仍執行。
部署 runtime＝governance-resolved Python 3.12；mixed-session／rollback 窗期保留
Python 3.9 語法相容。
desc 量測近似已知形態（品質洞非完整性洞，不修）：YAML folded scalar（`>-`——
量到摺疊符號本身，超長 desc 放行；generator flat-parse 同不展開，索引不膨脹）。
Write 收斂豁免：content 比既有檔短即放行（與 Edit delta 豁免對稱——部分收斂
結果仍 >12K 但方向正確，不擋）。
"""

import json
import re
import sys
from pathlib import Path

GENERATOR_NAME = "_generate_index.py"
DESC_LIMIT = 100  # frontmatter description 硬上限（＝寫入紀律值；09-03 P1 對齊）
BODY_LIMIT = 12_000  # 條目檔總長上限（chars）
NEW_ENTRY_LIMIT = (
    3_000  # 新建條目上限——寫入當下即蒸後形（cur=0 時 12K 膨脹治理無約束力，此閘補真空）
)
HASH_RE = re.compile(
    r"\bcommit[s]?\s+(?=[0-9a-fA-F]*[0-9])[0-9a-fA-F]{7,}"
    r"|\b(?=[0-9a-fA-F]*[0-9])(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{7,}\b"
)  # desc 禁 hash 兩形態（09-05 S2 commit-前綴；09-10 擴 bare hash——mosaic 收案群
#   desc「收案 93715b60a」無前綴流入兩晚實證）：bare 分支要求 7+ hex 且同時含數字
#   與 a-f 字母——純數字 7+ 串（緊湊日期 20260909／長編號）放行（漏全數字真 hash
#   ~2-4%，與 digit-lookahead 漏全字母 hash 同構，歸掃尾）；digit-lookdown 排除
#   純字母 hex 形態——實戰偽陽性「commit feedback」〔feedbac 恰 7 hex〕，真 hash
#   7+ 碼全字母機率≈0.01%。殘餘：hex 字母詞＋數字（如 decade12）在 desc 語彙罕見
#   （MOS-78／EP／kebab 名含 - 斷 run／版號用點號），誤傷成本＝一次改寫重試。
DATE_RE = re.compile(
    r"\b\d{2}-\d{2}\b"
)  # desc 禁日期流水 MM-DD（09-10 M2 實作——收案群「09-09」流入實證；全日期
#   經 MM-DD 子串命中）。合法碰撞面：版號用點號／範圍用 ~／時刻用冒號／比例用
#   斜線；字母前綴數字（S1-S4）因 \b 不中。純數字 8 位（20260909）不中，歸掃尾。
SESS_RE = re.compile(
    r"\bsess_[0-9A-Za-z]{3,}"
)  # desc 禁 session id（09-10 M2 實作；sess_ 前綴高特異，碰撞≈零）
STEM_SUFFIX_RE = re.compile(
    r"-(pending|inflight|in-flight|landed|done|closed)$", re.IGNORECASE
)  # 新建條目 stem 禁弧狀態後綴（AIR-100 S-B——air-90 決策 P3 承接，TC-4 凍結枚舉）；
#   IGNORECASE（F-6）——`-DONE`/`-Inflight` 變體同屬弧狀態語義，大小寫不變葉不構成繞道。
#   邊界：全形連字號（U+FF0D）不匹配——同既有三 pattern 歸夜間掃尾（F-7）。
#   弧狀態屬卡/report 定義域，非記憶定義域（air-100 Plan ④清洗標的——帶後綴條目
#   是弧收案慣性流入的主要形態）。**只擋新建**（cur_len==0）：既有條目收斂編輯
#   與改名退役流程的暫時寫入放行——存量處置（S-D）不被迫走 --no-verify 逃生口。
#   parity：Edit 無法改檔名、新建後綴實務只在 Write 出現——檢查置 tool 分支前
#   （tool-agnostic 於「檔不存在」條件，Edit 對不存在路徑本就在 harness 面失敗）。
# 共同邊界（三 pattern 同界）：CJK 緊貼（`案93715…` 無空白）因 \b／Unicode \w
# 含 CJK 而漏——歸夜間掃尾，不擴邊界。
PLACEMENT_REMINDER = (
    "[放置閘] 新條目——先過寫入六問 Q1：任務終態→卡/report（不進池）；"
    "repo 可推導→不寫；確定的跨 session user/專案事實才進池。"
    "六問＋載體統一定義表＝memory-audit skill「寫入端紀律」。（提醒不判斷）"
)  # ③ 放置閘（memory-audit skill「hook 擴充」①設計）：新建條目 stderr 注入六問
#   指針，非阻斷。動機＝弧收案 session 慣性實證（09-11/09-12 兩晚 project_ 類
#   新流入 87.5% 違 Q1——收案當下新寫，結案蒸餾掛點攔不到，提醒須在寫入瞬間）。
#   機械觸發＝檔不存在（與 NEW_ENTRY_LIMIT 同判準），禁語義偵測「收案語境」。


def is_index_violation(file_path: str, has_generator: bool) -> bool:
    """寫入目標名為 MEMORY.md 或 _inventory.md（B 形態全量投影），且同目錄裝有 generator（opt-in 條件）。"""
    return Path(file_path).name in ("MEMORY.md", "_inventory.md") and has_generator


def is_entry_file(file_path: str, has_generator: bool) -> bool:
    """寫入目標是治理池內的條目檔（.md、非 MEMORY.md、非底線系統檔）。"""
    p = Path(file_path)
    return (
        has_generator
        and p.suffix == ".md"
        and p.name != "MEMORY.md"
        and not p.name.startswith("_")
    )


def extract_desc(text: str) -> str:
    """取 generator 實際投影的 description，不擴成通用 YAML parser。

    對齊 skills/memory-audit/scripts/generate_index.py 的 parse_frontmatter
    與 main 的 read_text：universal newlines、首行／終界、頂層 key trim、
    最後同名 key 勝出、值去引號與空白。
    縮排行是巢狀 key，不是 description 的續行。
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    if end < 0:
        return ""
    desc = ""
    for line in text[4:end].splitlines():
        if (
            not line.strip()
            or line.lstrip().startswith("#")
            or line.startswith((" ", "\t"))
        ):
            continue
        key, _, value = line.partition(":")
        if key.strip() == "description":
            desc = value.strip().strip("'\"")
    return " ".join(desc.split())


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[block-memory-index-write] stdin parse error: {exc}", file=sys.stderr)
        sys.exit(1)

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    gen = Path(file_path).parent / GENERATOR_NAME
    has_generator = gen.exists()

    # ① 索引手寫攔截（原有行為；AIR-48 P3 擴 _inventory.md——B 形態全量投影同禁手寫）
    if is_index_violation(file_path, has_generator):
        print(
            "[Hook Blocked] MEMORY.md／_inventory.md 是 generator 投影，禁手寫。\n"
            "原因：索引由條目檔 frontmatter 機械投影；手寫必漂移"
            "（載入截斷 → 查重漏 → 近重複寫入）。\n"
            "修正方式：改條目檔（frontmatter name/description/type）後執行:\n"
            f"  python3 {gen}（Stop hook 也會自動重生成）",
            file=sys.stderr,
        )
        sys.exit(2)

    # ② 條目檔寫入檢查（寫入治理）
    if not is_entry_file(file_path, has_generator):
        sys.exit(0)
    target = Path(file_path)
    cur_text = target.read_text(encoding="utf-8") if target.exists() else ""
    cur_len = len(cur_text)
    # ④ 狀態後綴擋（AIR-100 S-B——插在 desc 檢查前，更上游；air-90 決策 P3 落地）
    if cur_len == 0 and STEM_SUFFIX_RE.search(target.stem):
        print(
            "[Hook Blocked] 新建條目檔名含弧狀態後綴（-pending/-inflight/-in-flight/"
            "-landed/-done/-closed）。\n"
            "弧狀態屬卡/report 定義域，非記憶定義域——inflight/landed 是弧生命週期，"
            "不是跨 session 事實。\n"
            "修正方式：重命名去掉狀態後綴再寫；弧進度與收案狀態歸卡/EP，"
            "內容歸屬見六問 Q1。",
            file=sys.stderr,
        )
        sys.exit(2)
    # ③ 放置閘（非阻斷提醒——不 exit 2，寫入照常進行）
    if cur_len == 0:
        print(PLACEMENT_REMINDER, file=sys.stderr)
    if tool == "Write":
        content = tool_input.get("content", "") or ""
        desc = extract_desc(content)
        if len(desc) > DESC_LIMIT:
            print(
                f"[Hook Blocked] 條目 description {len(desc)} chars > {DESC_LIMIT}。\n"
                "description 是索引行的投影原料（索引行 = name×2 重複 + desc，desc 佔一半 chars）。\n"
                "修正方式：精簡到主題＋一個鉤子（紀律 ≤100 chars），細節寫進 body。",
                file=sys.stderr,
            )
            sys.exit(2)
        if HASH_RE.search(desc):
            print(
                "[Hook Blocked] 條目 description 含 hash（commit／bare 形態）——desc＝觸發詞＋一句鉤子。\n"
                "hash 屬 git log 可推導（官方 skip-derivable），不進索引行。\n"
                "修正方式：desc 去掉 hash（收案錨點留 body 或指向 repo 檔案）。",
                file=sys.stderr,
            )
            sys.exit(2)
        if DATE_RE.search(desc):
            print(
                "[Hook Blocked] 條目 description 含日期（MM-DD）——desc 不放易變快照。\n"
                "日期／進度狀態住 body 或卡，desc 只留觸發詞＋一句鉤子。",
                file=sys.stderr,
            )
            sys.exit(2)
        if SESS_RE.search(desc):
            print(
                "[Hook Blocked] 條目 description 含 session id——sess_ 屬 DB 可推導。\n"
                "修正方式：desc 去掉 session id（接續錨點留 body）。",
                file=sys.stderr,
            )
            sys.exit(2)
        cur = cur_len
        if cur == 0 and len(content) > NEW_ENTRY_LIMIT:
            print(
                f"[Hook Blocked] 新建條目 {len(content):,} chars > {NEW_ENTRY_LIMIT:,}——寫入當下就該是蒸後形。\n"
                "新條目直寫敘事流水（timeline 過程/commit 清單/findings 計數）是池膨脹主入口——\n"
                "超額內容住 EP/卡/repo，不是「先寫再等 audit 壓」（09-06 user 拍板）。\n"
                "修正方式：lesson-first 一行一事實（教訓＋實證錨一行），壓縮後重寫；\n"
                "既有條目覆寫（cluster merge 收斂）不受此閘，走 12K 膨脹治理。",
                file=sys.stderr,
            )
            sys.exit(2)
        if len(content) > BODY_LIMIT and len(content) >= cur:
            print(
                f"[Hook Blocked] 條目檔 {len(content):,} chars > {BODY_LIMIT:,}。\n"
                "超大條目多屬 repo 可推導內容（EP 進度/git log/弧線流水）——該住 EP 檔，memory 收教訓。\n"
                "修正方式：只留決策與教訓（收案後一次性蒸餾），現況細節回 EP 檔。",
                file=sys.stderr,
            )
            sys.exit(2)
    elif tool == "Edit":
        new_string = tool_input.get("new_string")
        old_string = tool_input.get("old_string")
        replace_all = tool_input.get("replace_all", False)
        if (
            not isinstance(old_string, str)
            or not old_string
            or not isinstance(new_string, str)
            or not isinstance(replace_all, bool)
            or old_string not in cur_text
        ):
            print(
                "[Hook Blocked] Edit 無法重建候選內容：請重新讀取條目，提供可匹配的"
                " old_string、字串 new_string 與 boolean replace_all。",
                file=sys.stderr,
            )
            sys.exit(2)
        candidate = cur_text.replace(old_string, new_string, -1 if replace_all else 1)
        previous_desc = extract_desc(cur_text)
        desc = extract_desc(candidate)
        if not replace_all and cur_text.count(old_string) > 1:
            # Body-only ambiguity stays with the tool's uniqueness gate, as
            # before (including shrink allowance). A description-changing
            # ambiguous edit cannot be validated as a unique candidate.
            all_desc = extract_desc(cur_text.replace(old_string, new_string))
            if desc != previous_desc or all_desc != previous_desc:
                print(
                    "[Hook Blocked] Edit old_string 有多處匹配且可能改變 description；"
                    "請提供唯一匹配或明確設定 replace_all。",
                    file=sys.stderr,
                )
                sys.exit(2)
        if desc == previous_desc:
            desc = ""  # 存量不溯及：body-only 或攜帶未變 desc 的編輯仍可收斂。
        if len(desc) > DESC_LIMIT:
            print(
                f"[Hook Blocked] 新 description {len(desc)} chars > {DESC_LIMIT}。\n"
                "修正方式：精簡到主題＋一個鉤子（紀律 ≤100 chars），細節寫進 body。",
                file=sys.stderr,
            )
            sys.exit(2)
        if desc and HASH_RE.search(desc):
            print(
                "[Hook Blocked] 新 description 含 hash（commit／bare 形態）——desc＝觸發詞＋一句鉤子，\n"
                "hash 屬 git log 可推導。修正方式：desc 去掉 hash。",
                file=sys.stderr,
            )
            sys.exit(2)
        if desc and DATE_RE.search(desc):
            print(
                "[Hook Blocked] 新 description 含日期（MM-DD）——desc 不放易變快照，\n"
                "日期住 body 或卡。",
                file=sys.stderr,
            )
            sys.exit(2)
        if desc and SESS_RE.search(desc):
            print(
                "[Hook Blocked] 新 description 含 session id——sess_ 屬 DB 可推導，\n"
                "接續錨點留 body。",
                file=sys.stderr,
            )
            sys.exit(2)
        if len(candidate) > cur_len and len(candidate) > BODY_LIMIT:
            print(
                f"[Hook Blocked] 條目檔將膨脹到 {len(candidate):,} chars > {BODY_LIMIT:,}。\n"
                "膨脹主因＝進行中弧線每 session 追加（實證：單檔 98 次 Edit 養到 84KB）。\n"
                "修正方式：弧線進度住 EP 檔；此檔收案後一次性蒸餾。收斂方向（縮小）的編輯不受限。",
                file=sys.stderr,
            )
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
