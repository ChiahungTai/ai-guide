# Work Order — AIR-37 EP 審查（read-only 深審，advisory）

## 1. 紅線（違反＝失敗）

- read-only：禁任何寫入（含 repo 外、memory 池、/tmp）；交付＝最終回覆文字
- 禁 git add/commit/push、禁改 backlog 卡狀態
- 中間筆記不留檔

## 2. 目標（一句話）

審查 AIR-37 EP（memory 卡資訊生命週期閘門——commit skill 2.8 對帳腿＋execution-plan UC 盤點登記腿）的設計合理性與引用 drift，產 findings。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- base commit：`3a264e6`
- 並行改動聲明：working tree 有前兩弧（AIR-36 fire-and-forget＋memory-audit 教訓固化）未 commit 變更——非本審查對象，僅 EP 是

## 4. 必讀（scope manifest）

- **core（逐段讀）**：`ai-analysis/_tasks/09-07-memory-card-lifecycle-gate/ep.md`（審查對象）；`skills/commit/SKILL.md` 階段 2.8 段（EP S1 的改寫對象——驗證 EP 描述的現行結構屬實）；`skills/execution-plan/SKILL.md` UC 盤點步驟 3（S2 改寫對象）
- **leaf（機械掃＋異常深讀）**：`skills/kanban-board/SKILL.md`（結案蒸餾第三動條文——EP 宣稱的單一源，驗證條文存在且 EP 引用語義正確）；`skills/memory-audit/SKILL.md`（寫入端紀律段——同上）
- **exclusions**：ref-docs/、backlog/、.muse-bridge/、其他 ai-analysis/

## 5. 已決策（勿重辯）＋矛盾例外

- 蒸餾方法論單一源在 kanban/memory-audit——兩腿只引用不重抄（勿建議把方法論抄進 commit skill）
- 判斷形態＝機械掃描＋LLM 判歸屬（非純 hook）
- 存量債不清（波段出口）——勿建議本弧清 21 條 project_
- 矛盾例外：發現 EP 引用的條文/結構與實際檔案衝突 → 停下舉證（file:line＋逐字引用）

## 6. 範圍限定

動＝零（read-only）；不動＝全部。交付以未產生任何檔案變更自證。

## 7. 工具接線

cat/rg/ls（字串搜尋一律 rg）；禁 code-reality 寫入面；輸出禁寫 repo 外。

## 8. 驗收（查證命令＋預期證據形態）

1. EP 錨點驗證：`rg -n "弧結案蒸餾|第三動" skills/kanban-board/SKILL.md` → 條文在場（EP 依賴錨點）
2. `rg -n "2.8|finalization 對帳" skills/commit/SKILL.md` → 2.8 段結構與 EP 描述一致
3. `rg -n "去重前置|pending-decisions" skills/execution-plan/SKILL.md` → 步驟 3 結構與 EP 描述一致
4. 跨檔詞形預檢：`rg -n "三分歸屬|結案蒸餾範圍" skills/ skills/` → 現況零命中（新詞形，EP 定義）——若已存在則 EP 有撞詞風險

## 9. 證據紀律＋PII 禁令

每 finding 附 file:line＋逐字引用；禁 PII；審查方法論限制段（用了什麼、什麼無法驗證）。

## 10. 交付報告（findings schema）

每 finding：file:line 錨點、嚴重度（High/Medium/Low）、信心水準（0-1）、remedy 三分類（bug＝行為違反意圖且無文檔宣稱刻意／drift＝兩處宣稱或實作不一致／design-reversal＝文檔化刻意設計但設計該反轉——需 user 拍板）、一句修法建議。審查維度：EP 引用 drift（錨點與實際）／設計合理性（閘門形態、單一源分工、SM 矩陣覆蓋）／漏改（本弧變更面是否遺漏——rg 掃 commit/execution-plan 相關引用）／過度工程線（兩腿是否過重）。最後總評一行：可定稿／需修正後定稿。
