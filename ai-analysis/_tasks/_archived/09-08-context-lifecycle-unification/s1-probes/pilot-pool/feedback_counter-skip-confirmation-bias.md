---
name: feedback_counter-skip-confirmation-bias
description: 建議跳過與建議 capture 都先對抗性自查——skip 查推進偏好、capture 查已存在否（雙向自檢）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3da4c7ab-1694-4c4d-831f-723c383929b0
---

推進偏好有兩個出口：建議「**跳過**」某驗證步驟（省事方向）與建議「**capture**」新規則/記錄/覆蓋/列 gap（完整方向）——同一確認偏差的兩面，都必須懷疑建議的觸發源是客觀判定還是偏好。不只對 agent 嚴格，對自己也用同等對抗性。

> merged_from: feedback_counter-capture-completeness-bias.md, 2026-08-31

## A 向：建議「跳過」時懷疑推進偏好

當我建議「跳過某個驗證/審查步驟」（如 ep-validate、code-review、二次 review）時，必須懷疑這個建議的觸發源 —— 是客觀判定，還是「想推進」的確認偏差？

**真實案例**：review-engine EP（純 docs），我在 judge-review 結尾主動說「傾向跳過 ep-validate」。用戶觸發 /ep-validate 後，我讀 skill 找到「何時需要 ❌ 文檔」表格就順勢判定跳過。後設反思發現：我在用戶觸發前就預判跳過，表格只是支持證據，不是觸發源 —— 是確認偏差帶到結論，非嚴謹查證。

**Why**：對話越長，推進偏好越強（潛意識想快點到 build/commit）。這股力量會讓我對「跳過」傾向不夠對抗性 —— 先有結論再找支持證據。

**How to apply**：
- 建議跳過任何步驟前，先問自己「我是在客觀判定，還是想推進？」
- **「out-of-scope 推後」變體**（review-engine build 真實案例）：把該這次做的推到「後續 EP」時，區分「真 out of scope」（pre-existing 設計選擇，如下游語義差異）vs「這次委託的完成」（如委託 review-engine 後 header 條件重述沒清 = drift 溫床）。後者該這次做，不要用「範圍」包裝保守。用戶戳「為何不這次做」時，認真重新評估別固守原判斷 —— 被戳通常代表推後了該做的。
- 做一次**對抗性自查**：逐項問「真的沒有該驗證的假設/風險嗎？」（像 [[settlement-scripts-are-code]] 的宣稱查證原則那樣對自己）
- 一致性原則：我對 agent/review 嚴格（judge-review 不盲從、自我否證），對自己的「跳過」傾向要用**同等對抗性**。對外不盲從、對內也不盲從偏好
- **「live probe 優先」變體**（2026-08-22 案例）：宣稱環境行為前提（「新 agent 檔要重啟才進 registry、所以你先重開」）時引的是前 session 記錄，用戶戳「你確定一定要重開？你現在驗證看看」——一個 spawn（秒級、無副作用）就機械確認 not found。便宜 probe 永遠比引用歷史記錄有說服力；用歷史記錄擋 live test 是把「曾經驗過」錯當「現在也會這樣」
- 結論碰巧對 ≠ 過程可信；確認偏差這次帶到正確結論，下次可能跳過該跑的

## B 向：建議「capture」前先 grounding 是否已存在或已解決（completeness bias 對偶）

建議「capture」任何東西（新增規則、flow-feedback 記錄、補 heuristic、加覆蓋、**列 gap / 強化建議**）前，先 rg / Read grounding **同概念是否已存在或已解決**。completeness bias 會讓我預設「記下來 / 列出去才完整」，但若知識已存在或摩擦已解決，capture = 製造 triplicate drift 或 **false gap**。**已確認 ≥2 instance**：

1. ai-rules session：兩度建議為「framework lifecycle 異常 → 先查 usage contract」教訓建 flow-feedback；rg 發現 nt-query skill 已深度覆蓋（`SKILL.md:58` 字面就是該 daemon-thread 場景）→ Pattern Radar HIGH → 被否決。真 failure 是 trigger miss，非 content gap。
2. **強確認實例**：分析「書→ai-rules→mosaic」時，mosaic-consumer agent 讀了 mosaic `_done/`（**已歸檔=已解決**）flow-feedback 卻報告成 gap，我合成時**沒回頭查實際檔案**就列建議 → 捏造 3 個 false gap（R2 例外路徑驗證、R3 build mypy 對稱、R4 review-pipeline recipe，**全都早已實作**，path:line 齊）+ 1 個 false positive（Memory row 虛構 `memory/` 系統 + MEMORY.md）。用戶當場指出「前期研究不夠」，派 2 個 grounding agent 才校正。

**關鍵 nuance**：`_done/` / `_archive/` 目錄裡的 friction doc = **已解決的歷史摩擦，非現況 gap**。讀到要預設「已解決」並查當前檔案確認，不可直接當 gap 報告。同理 `_done/` EP = 已完成。

**How to apply（B 向）**：
1. 想建議「補規則 / 記 flow-feedback / 加覆蓋 / **列為 gap 或強化建議**」→ 先問「這知識/能力/摩擦是否已存在或已解決？」
2. rg + Read + 必要時 LSP grounding，**附 path:line** 才下結論（找不到要換 pattern/工具，0 hits 不可直判「不存在」—— 自我否證義務）。
3. 讀 `_done/`/`_archive/` friction → 預設「已解決」，查現況確認。
4. 若前期研究已產出未 grounded 的結論 → 派 grounding agent（預設懷疑：先假設已存在，找到 ✅ + path:line，找不到才標 missing）補驗證。寧可少記/少列，不要 triplicate 或 false gap。

關聯：[[settlement-scripts-are-code]]（正向/負向宣稱都需查證）、[[feedback_fix-immediately-not-defer]]（反拖延 vs 合理跳過的邊界 —— 合理才立即修，但「跳過」要反向懷疑）。
