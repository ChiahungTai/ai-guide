# EP：小修改的分級軌道——static-only 收緊機械化（薄 EP，blueprint）

- **卡**：AIR-129（owning）
- **日期**：2026-09-18　**baseline**：main@0f6035c8（開工前重確認）
- **狀態**：draft v3（muse＋codex ep-review findings 已全數修入）
- **ep_type：blueprint**——S1-S2 開工前各衍生 implementation 級 Planning Contract（引用本 EP）
- **研究依據**：muse I-6（0917 弧實證）＋card Plan 已決策 ①-④＋codex ep-review 關鍵指正（現行條文已有 static-only 豁免——本 EP 是**收緊機械化**不是新增）

## 1. 問題與 delta 錨點

落地前審查閘（AIR-105/106）的現行 static-only 豁免（instruction-writing「豁免：純 typo/link/格式／零語義差——由 diff 自證行為等價」）**已存在但不可機械判定**：「typo」「link」本身需要語義判斷，classifier 自信地誤判時保守 default 救不了（它只處理已被察覺的歧義）。額度緊時 boundary 案 external 腿合法無限期 pending（muse I-6）——防線吃掉吞吐。**與 AIR-125 互補不重疊**：125 修機械閘誤擋，本 EP 修審查儀式的分級與記帳。

**本 EP 真身＝三件事**：①把既有 static-only 豁免**收緊為機械 predicate**（deterministic 白名單，可程式化判定）②把 no-candidate pending 的記帳**標準化為 deferred 回執**（顯式欄位＋SLA）③dogfood 驗證。不是新增 fast-track，不是拆落地閘。

## 2. 設計

### 2-1 static-only 機械判準（收緊既有豁免）

入場＝**deterministic 可證行為等價的 transformation 白名單**（可程式化——S1 交付物是 predicate 本身，非散文判準）：
- whitespace／markdown 格式重排（渲染輸出 byte 等價可證）
- 純文字 prose 內錯字修正：限非 code、非 frontmatter key、非路徑/identifier token，且 diff 前後詞彙編輯距離 ≤2（程式化可判）
- **typo 觸及 code token／frontmatter key／路徑／模態詞行 → 一律落 standard／boundary**（無機械 oracle 不入場——codex 指正：confident 誤判是保守 default 蓋不住的）

分類無法求值 → 直接 boundary（fail-closed）。分類有爭議 → 走全套。行數不是判準。

### 2-2 deferred 回執（non-terminal——語義明確化，codex 指正）

`review=deferred` 是**記帳標準化的 pending，不是新的落地許可**：boundary 案 external 腿零容量 → 依現行 no-candidate 帳本記 deferred——**不滿足 landing gate、不得落地**，補審條件＝額度恢復 7 日內補腿（N 凍值，變更走 EP amendment）。與現行 pending 的差別只有兩點：回執欄位顯式化＋SLA 可追蹤。boundary baseline 不變。

### 2-3 Scenario Matrix（gate truth table——驗收即套表）

| # | 輸入 scenario | 預期裁決 | 可判 predicate |
|---|---|---|---|
| P1 | whitespace/format-only diff | static-only | predicate 求值＝true |
| P2 | 條件行內任何改動（含 typo，如 "fresh"→"frsh"） | standard／boundary 全套（fast-track 拒收） | 觸條件行→拒 |
| P3 | 無法求值的分類（新形態 diff） | boundary（fail-closed） | predicate 求值失敗→boundary |
| P4 | boundary 案 external 腿零容量 | deferred（non-terminal，不落地） | 回執欄＋7 日 SLA 行在場 |

## 3. Load-bearing assumption / kill criteria

| Assumption | Probe | Kill observation | Action |
|---|---|---|---|
| A1：機械判準對真實歷史 diff 可判定、分類無歧義 | dogfood 兩錨點（存在性已驗）逐 hunk 套 §2-3 表：d4000e36（五處文檔修正）——每 hunk 唯一合法 grade 應皆 static-only；e1aba87a（governance Critical 修復）——應落 boundary 全套。predicate 無法求值的 hunk→boundary 記錄 | **獨立二人（或同人間隔複驗）分類不一致 ≥1 案例**（機械計數） | 判準**收窄**（白名單縮小），不擴表——收窄兩輪後仍不一致 → INVALIDATED fast-track 機械化（保留 deferred 記帳段；既有豁免條文回滾原文） |

## 4. 工作分段

| 段 | 內容 | 變更檔 | AC 對應 |
|---|---|---|---|
| S1 | 既有 static-only 豁免條文**原位收緊**為 §2-1 機械判準（current→target delta 以現行條文行為唯一修改錨點——instruction-writing 落地閘節豁免行）＋deferred 回執欄位與 N=7 SLA 語義（§2-2） | `skills/instruction-writing/SKILL.md` 落地前審查閘節 | AC#1、#2 |
| S2 | dogfood：§2-3 表四 scenario 全套跑（P1-P4）＋d4000e36/e1aba87a 兩錨點逐 hunk＋**下弧首個真實落地閘案例 live 復核**（歷史 replay 測不到額度緊 pending 動機——live 補位） | 同上（判準措辭如需修） | AC#3、A1 |

## 5. 明示不做

- 不動 `rules/outward-action-consent.md`（card Plan 明示）
- 不拆 boundary baseline／跨家族加腿條款；deferred 不開落地許可（分級≠降級）
- 不與 AIR-131 合併（檔案零交疊、可平行）
