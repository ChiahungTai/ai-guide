---
name: cjk-char-corruption-rg-verify
description: Edit/Write 失誤兩形態——CJK 字元損壞（形似異體字肉眼難辨）與標題錨替換（插入未接回標題、段落孤兒化）；改完必機械 rg 驗證
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 16b8d8ba-41b8-40e0-85f8-4507a96004b2
---

我的 Edit/Write 在產出 CJK（中文）內容時，偶發寫入「視覺相似但不同的字元」—— rg 抓得到、肉眼難辨。這是 Edit 失誤的形態一；形態二（結構面：標題錨被替換掉）見下方段——兩個形態共同的紀律是**改後機械驗證**。

> merged_from: feedback_edit-insert-heading-preservation.md, 2026-08-31

**實證（本 session EP-A/B/C build）**：
- `脈絡` → 寫成 `脀絡`（U+8108 → U+8100）—— 我自己 rg 驗證抓到
- `判讀層` → 寫成 `判讂層` —— 跨 session code-review（ai2）抓到
- （非 CJK 但同類：`enforcement` overclaim 用詞，自審漏、ai1 抓到）

**再證（2026-08-17 metadata-sync 改寫）**：`偵測` → 寫成 `偵渵`（測/渵）——寫完自覺可疑 rg 驗證抓到。頻率非一次性，每次寫中文都要驗。

**再證（2026-09-01）**：`load-bearing` → 寫成 `load-loading`（英文複合詞滑筆，Edit 複製舊文改一詞時混入）——下一動自覺即改；同「複製舊文＋改一詞」高風險場景，英文長字也要 rg 驗。

**再證（2026-09-03，Edit old_string 連續 4 次失敗）**：memory 條目「不○ per-task branch」的否定動詞字（形似異體家族）我連打 4 次都與檔內字元不同——連「從 Read 輸出複製 old_string」都失敗（複製動作再次寫錯同一字）。排查定式：`rg -c "<最短錨>"` 先驗存在 → 短錨命中但 Edit 連續失敗＝字元碼位問題非匹配問題 → `python3 -c "c=open(f).read(); i=c.find('<片段>'); print(repr(c[i-5:i+40]))"` 直接看 repr 定位差異點，以 repr 揭露的字面重構 old_string。

**再證（2026-09-03 第二形，CLI 載體）**：backlog 卡 desc 經 `backlog task edit AIR-14 -d "<長文>"` 寫入後，「結案蒸餾」變「結案蒸 District」——CJK 語詞中段被替換成無關英文單字（非視覺相似異體，是滑入整個錯詞）。載體擴展：**不限 Edit/Write tool，CLI 參數傳長 CJK 文同樣損壞**——`backlog task edit` 類 CLI 寫入後同樣要 rg 驗證關鍵詞（本次 `rg -c "蒸餾"` 抓到）。

**再證（2026-09-05，潛伏既有損壞——非本次寫入造成）**：Edit deep-work SKILL.md 時 old_string not-found，repr 檢查肉眼看正常——升級 **codepoint 級比對**（python `ord()` 逐字迴圈）才定案：檔內既有字 `規`U+898F 被寫成 `覄`U+8984（形似異體、潛伏的既有損壞非本 session 寫入）。定式擴充：Edit old_string 連續 not-found 且 repr「看似正常」→ **不要信肉眼，跑 codepoint 比對**（`[hex(ord(c))+':'+c for c in 候選段]`）；修復後以 `rg $'\u8984'` 按碼位掃全 repo 殘留（按字面搜其他形態會漏）。

**Why**：Edit/Write 的字元可靠性在 CJK 區段比 ASCII 差；視覺渲染下 `脀/脈`、`讂/讀` 幾乎無法分辨，但語意/字典完全不同。同 LLM 自審與作答共享盲點（acceptance-evidence 證據獨立性）—— 我自己讀不出錯。

**How to apply（形態一：字元損壞）**：
- 改完含 CJK 的 instruction 檔後，**機械 rg 驗證關鍵詞的精確字元**（不只確認「存在」，要確認是對的字）—— 尤其自己整檔重寫的行（複製舊文+改一詞時最易混入異體）。
- 高風險字：視覺相似異體（脀/脈、讂/讀、己/已/巳、未/末...）、罕用技術字。
- 獨立 review（跨 session /consistency、/code-review）是必要兜底，不只靠自審。

## 形態二：Edit 在標題前插入未接回標題（edit-insert-heading-preservation 併入）

2026-08-30 同一 session 兩次同型失誤：在報告插入新小節（side chat 結算補記、T3-2 結案段）時，old_string 選了既有標題「### T1 落地記錄…」、new_string 只含新段落未接回標題——標題被刪除，既有段落內容孤兒化掛在新小節下（語義污染非資料遺失，兩次都是下一動 rg 發現立即補回）。

**Why**：Edit 是字串替換不是插入；拿「錨點標題」當 old_string 時，錨點本身就是被替換掉的內容之一。

**How to apply（形態二：標題錨替換）**：在既有標題前插入內容 → new_string 結尾必須原樣接回該標題全文（或改用標題以外的唯一相鄰文字當錨）；插入後 rg 該標題確認存活。

## 形態三：刪除型 Edit 的 new_string 重寫目標（2026-09-03）

意圖刪 `scan_project.py` 整函式 `_find_valid_tag_names`，Edit 的 new_string 卻把函式全文重寫一遍（只差尾空行）——函式沒刪成，還吃掉尾換行造成 `return valid_tagsdef run_cross_validation(` 語法黏連；ruff check 8 個語法錯立刻現形（exit 1），重發正確 Edit（new_string 只含保留邊界 `def run_cross_validation(`）收斂。

**Why**：刪除意圖下把「目標內容」寫進 new_string＝複製貼上慣性；Edit 是字串替換，old/new 高度重疊時語義上只是微調不是刪除，且尾端換行數差異會把銜接行黏上。

**How to apply（形態三）**：刪整段/整函式 → new_string 只含**保留邊界**（前後銜接行），發出前自檢「new_string 裡是否還出現我打算刪的內容」；.py 改後 ruff check 是廉價防線（黏連類語法錯機械現形）。

關聯：[[feedback_counter-skip-confirmation-bias]]（建議跳過驗證時懷疑推進偏好）、[[settlement-scripts-are-code]]（AI 審查宣稱同等查證）。
