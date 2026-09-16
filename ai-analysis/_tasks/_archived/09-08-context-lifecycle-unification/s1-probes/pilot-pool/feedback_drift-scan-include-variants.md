---
name: feedback_drift-scan-include-variants
description: 假 CLEAN 掃描家族——殘留掃描必含拼寫變體與配對鏡像語句；刪除行核對必看完整 diff 禁 rg 過濾管道（過濾器輸出≠完整輸入）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

drift 殘留掃描（改名/退休/術語翻轉後的「清乾淨了」驗證）只掃一種拼寫形態＝產出**假陰性 CLEAN**。真實案例（2026-08-28）：`rg 'lsp_harvest'`（底線）回零 → 我宣稱「zero-residue」寫進 commit message；ep-review 抓出 `LSP-harvest`（連字號）4 位點殘留（rules/lsp-navigation.md:26＋crg-query :3/:44/:55，含已部署 bundle 新舊並存）——宣稱不實，當場修 4 位點＋重 deploy。

> merged_from: feedback_deleted-line-review-full-diff.md, 2026-08-31

**Why**：同一概念在語料中天然多拼法（底線/連字號/空格/大小寫、中英標點差）；掃描 pattern 是人為選擇，選了哪個變體就只驗證那個變體——「我掃不到」≠「不存在」。審查者獨立掃描能抓，但別依赖下游抓。

**How to apply**：殘留掃描用容差 pattern（`rg -in 'term.variant'`——點號同時吃底線/連字號、`-i` 大小寫）或顯式列舉全部已知變體；「zero/CLEAN」宣稱必須由此類掃描背書後才寫進文檔/commit message。同族陷阱：過濾管道吞行（見下方同族段）、acceptance-evidence 的 head 截斷計數。

**第二實例類（2026-08-28 P1 翻轉）：鏡像陳述漏翻**——rule 定義源翻了 3 位點，但 `skills/lsp-navigation:85` 的「**LSP 保留面不變**」鏡像 blockquote 沒跟（寫翻轉的 CR session 漏、ai-rules 審查抓，同批修入 d9cf2d0）。定義翻轉的掃描除術語變體外必含**配對鏡像語句**（rule↔skill 同主題複述句）——「X 保留面**不變**」「Y 恆」這類明示恆常句是重災區：翻轉後第一個變謊的就是它們。

**第三實例類（2026-08-31）：重編號後跨檔編號引用**——post-build 階段重編號（收尾報告 5→6、新 5=殼 refresh，commit 1c9ea1e）後，`code-review:186` junk tag 說明仍指舊「階段 5」（`smell=` 欄已移至階段 6）——當場靜態驗證示範 `rg "post-build 階段" skills/ --glob '!post-build/*'` 跨檔掃抓出，修入 9cf7201。**How to apply**：任何章節/階段重編號後必掃跨檔「〈檔名/命令〉＋編號」引用；修法偏好**名稱錨**（「收尾報告」）取代編號錨——編號是位置引用，重排即漂，名稱錨免疫再編號。

**第四實例類（2026-09-02）：清單 pattern ≠ 驗收 pattern**——handoff/第三方給的殘留清單，其掃描 pattern 與自查必須不同：Backlog.md 手術 handoff 用 `rg '\.kanban' --hidden -g '!archive' -g '!*done*'` 產出 13 檔清單，驗收自查改 `rg -c '\.kanban' skills/ rules/ ai-development-guide.md` 抓到**清單外 6 檔漏網**（acceptance-evidence/state-md-write/sync-implementation-steps/cr-query/code-review-and-quality/maintain——`290d4e5` 補修）。**How to apply**：消費任何「已清乾淨」清單時，用自己的 pattern（不同 glob/路徑範圍）重掃對帳——清單是輸入不是驗收。

**第五實例類（2026-09-03）：type/glob 過濾漏檔**——定義源（截斷語義）修正時 drift 掃描用了 `rg --type md`，`.py` 的 `hooks/block-memory-index-write.py` 檔頭舊敘述漏網——fresh-eyes 審查 agent 全域掃才抓到（F3）。**How to apply**：術語/定義翻轉的殘留掃描預設**不加副檔名過濾**（定義會出現在註解/docstring/config 任何載體）；要限縮先問「該術語可能出現在哪些檔案型別」再顯式列舉，不用單一 `--type`。

**第六實例類（2026-09-06）：link 名稱的合法前綴形態**——memory cluster merge 前的 backref 掃描只掃 `[[name]]` 無前綴形態，漏 `[[project_name]]` 帶前綴 7 處（終掃兩形態 `(project_)?name` 才清零）。**How to apply**：掃描 reference/link 類目標時，列舉**全部合法引用形態**（前綴有無、路徑長短、絕對相對）——連結語法天然多形態，單形態掃描對 link 類目標是結構性假 CLEAN。

**第七實例類（2026-09-06）：引用端 characterization 引述**——rule 例外結構翻轉（單例外→雙例外）後，引用端掃描用 rule 現有詞（「唯一例外｜建卡｜style」）回零判 CLEAN；consistency gate 抓到 `autonomous-execution/SKILL.md` 兩處引述該 rule 為「無例外」——該詞已不在 rule 裡，掃 rule 詞對它結構性免疫。**How to apply**：改定義源後掃引用端，pattern 除新關鍵詞外必含引用端的**絕對化 characterization**（「無例外」「恆」「永遠是」）——與第二實例類恆常句同根源，載體是跨檔引述。

**第八實例類（2026-09-07）：「歸零」判準反向必敗——同詞異義誤殺**——AIR-38 EP 驗證句寫 `rg "隨意" 產品面歸零`（tier 標籤四處改「一般」後應零殘留），但 `flow-review:33`「降**隨意**性」是日常中文詞非 tier 標籤——四處改完歸零**永不成立**，執行者被迫改無辜檔或謊報通過（muse review F1 抓出）。**How to apply**：寫「X 歸零」驗證判準前，先 `rg X` 掃現況全命中並逐個判型——命中超出預期標的（日常詞/成語/子字串）時**限縮判準形態**（僅計標的位點、排除清單明列）而非全 repo 歸零；與前七類同根源的鏡像：前者漏掃變體（假 CLEAN），此者掃到異義（假 FAIL）——判準兩端都要對現況。

## 同族：刪除行核對禁 rg 過濾管道（deleted-line-review-full-diff 併入）

壓縮/重構類任務的「刪除行逐行核對」（判準：無誤刪承重論證）必須**直接看完整 git diff**，禁用 rg 過濾管道抽取刪除行。

**Why**：2026-08-24 bundle 減量 EP S4 核對四檔刪除行，`git diff <4檔> | rg '^-[^-]' | rg -v "^-### |^-## |^-> "` 只顯示 2 檔的刪除行（acceptance-evidence 與 llm-output-convention 消失）——過濾管道吞行（與 git add 部分 stage 行為交互後更難察覺，見 [[feedback_verify-wt-before-commit]]）。若未追查直接簽核 = 兩檔未核對。這是 rules/modern-cli-preference「pattern coverage blind spot」家族的新載體（同 head 截斷、toplevel-only import）：**過濾器輸出 ≠ 完整輸入**，而「掃了什麼就被當成完整」——與本文主線（單一拼法掃描產出假 zero-residue）同屬「假 CLEAN」家族。

**How to apply**：
- 刪除行核對：`git diff <files>` 直接讀（或輸出重導檔案再 Read），不疊 rg 過濾
- 已用過濾器時：過濾結果的檔案覆蓋數 vs 預期檔案數機械對帳（4 檔 diff 只見 2 檔的行 = 紅燈）
- 展示用途過濾可以；**簽核用途（驗證聲稱完整看過）禁過濾**
