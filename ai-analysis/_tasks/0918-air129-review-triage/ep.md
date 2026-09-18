# EP：小修改的分級軌道——static-only 收緊機械化（薄 EP，blueprint）

- **卡**：AIR-129（owning）
- **日期**：2026-09-18　**baseline**：main@0f6035c8（開工前重確認）
- **狀態**：draft v3（muse＋codex ep-review findings 已全數修入）
- **ep_type：blueprint**——S1-S2 開工前各衍生 implementation 級 Planning Contract（引用本 EP）
- **研究依據**：muse I-6（0917 弧實證）＋card Plan 已決策 ①-④＋codex ep-review 關鍵指正（現行條文已有 static-only 豁免——本 EP 是**收緊機械化**不是新增）

## 1. 問題與 delta 錨點

落地前審查閘（AIR-105/106）的現行 static-only 豁免（instruction-writing「豁免：純 typo/link/格式／零語義差——由 diff 自證行為等價」）**已存在但不可機械判定**：「typo」「link」本身需要語義判斷，classifier 自信地誤判時保守 default 救不了（它只處理已被察覺的歧義）。額度緊時 boundary 案 external 腿合法無限期 pending（muse I-6）——防線吃掉吞吐。**與 AIR-125 互補不重疊**：125 修機械閘誤擋，本 EP 修審查儀式的分級與記帳。

**本 EP 真身＝三件事**：①把既有 static-only 豁免**收緊為機械 predicate**（deterministic 白名單，可程式化判定）②把 no-candidate pending 的記帳**標準化為 deferred 回執**（顯式欄位＋SLA）③dogfood 驗證。不是新增 fast-track，不是拆落地閘。

> **〔Amendment 2026-09-18——A1 兩輪 dogfood 裁定後，user 選 B〕**：吞吐痛點主解重定位＝deferred 回執鏈（②，已落地驗證）；fast-track（①）保留已收斂的窄機械 predicate（含 scope 條款），服務面重定位為 whitespace／literal-typo 級——真實控制面編輯幾乎無此形態（d4000e36 錨點 24 hunks 零入場實證），「typo 級修正被全套卡住」的日常痛點由 deferred SLA 承接而非免審。退出後 profile 歸屬發散（ordinary vs boundary）劃回 review-engine 分級層既有性質（判定表有保護分支 fallback，方向 fail-safe），本卡不追。

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
| A1：機械判準對真實歷史 diff 可判定、分類無歧義 | dogfood 兩錨點（存在性已驗）逐 hunk 套 §2-3 表：d4000e36（五處文檔修正）——每 hunk 唯一合法 grade 應皆 static-only；e1aba87a（governance Critical 修復）——應落 boundary 全套。predicate 無法求值的 hunk→boundary 記錄 | **獨立二人（或同人間隔複驗）分類不一致 ≥1 案例**（機械計數） | 判準**收窄**（白名單縮小），不擴表——收窄兩輪後仍不一致 → INVALIDATED fast-track 機械化（保留 deferred 記帳段；既有豁免條文回滾原文） **〔結局 2026-09-18：兩輪後 predicate 層收斂、Type 1 歸屬層 §2-1 不可達；依 user amendment 裁定不 INVALIDATE 不回滾——保留收斂形態（含 scope 條款）、主解重定位 deferred，詳見 §7〕** |

## 4. 工作分段

| 段 | 內容 | 變更檔 | AC 對應 |
|---|---|---|---|
| S1 | 既有 static-only 豁免條文**原位收緊**為 §2-1 機械判準（current→target delta 以現行條文行為唯一修改錨點——instruction-writing 落地閘節豁免行）＋deferred 回執欄位與 N=7 SLA 語義（§2-2） | `skills/instruction-writing/SKILL.md` 落地前審查閘節 | AC#1、#2 |
| S2 | dogfood：§2-3 表四 scenario 全套跑（P1-P4）＋d4000e36/e1aba87a 兩錨點逐 hunk＋**下弧首個真實落地閘案例 live 復核**（歷史 replay 測不到額度緊 pending 動機——live 補位） | 同上（判準措辭如需修） | AC#3、A1 |

## 5. 明示不做

- 不動 `rules/outward-action-consent.md`（card Plan 明示）
- 不拆 boundary baseline／跨家族加腿條款；deferred 不開落地許可（分級≠降級）
- 不與 AIR-131 合併（檔案零交疊、可平行）

## 6. S1 結算（2026-09-18）

- 實作：impl-lite（glm-5.3-flash）card WT 三觸點轉錄；review＝muse xhigh＋codex web/high 雙 cross-family（job-mu6jhk36-j1iewz／job-mu6jhlp0-qt0s0o，verdict 均 needs-fix）→ judge（GLM-5.3）合併 8 findings 全採納落地＋1 conflict note。帳本＝`.review/air-129.md`（lint canonical）。
- 判準收窄（EP §3 A1 授權路徑）：②加 word-level Levenshtein 定義＋封閉負面表；①改義務式＋限 markdown body；codex「EP amendment／correction-pair allowlist」立場不以裁決消滅——S2 dogfood A1 分類不一致觸發時走既有升級路徑。
- 伴隨 drift sync：rules/instruction-writing.md:7 pointer 尾句同步（F1）。
- S2 未開工（待 S1 落地後）。

## 7. S2 dogfood 結算（2026-09-18；A1 kill criteria 實證）

- **Round 1**（判準 v1）：rater A＝GLM-5.3 full fresh、rater B＝muse xhigh（job-mu6k2hvb-ixryvv），純 diff 無錨定 brief。P1-P3 一致；逐 hunk 不一致 8 案例 → A1 觸發。根因二層：Type 2＝scope 缺口（code/config/test hunk 無處置條款，6 案例）；Type 1＝退出後 profile 歸屬（ordinary vs boundary，2 案例）。
- **Round-1 收窄**：第 4 款加「本判準僅適用 instruction 條文（markdown）之 hunk——code／config／test 等其他檔型 hunk 一律不入場，逕依第 1 款分類」；round-2 brief 補 review-engine 判定表三行＋雙腿等量約束（禁讀 repo）。
- **Round 2**：rater A2＝GLM-5.3 full fresh、rater B2＝muse xhigh。P1-P3 一致；Type 2 全收斂 ✓；Type 1 仍不一致 3 案例（AGENTS.md、acceptance-evidence、execution-plan——muse 恒 ordinary、A2 恒 boundary/保護分支）。
- **Judge 判定**：predicate 層（白名單求值／scope／fail-closed／退出決策）兩輪 100% 收斂——機械化工程成立。殘留發散全在 review-engine 分級層（§2-1 收窄不可達；強制 binary collapse 會把真路徑小修全套化，違背卡目的）——收窄路徑實質耗盡，提前進 amendment 裁決（偏離 EP「兩輪」字面，user 在場知情）。
- **服務面發現**：EP canonical 錨點 d4000e36 兩輪 24 hunks 零入場 static-only（實質＝句子級改寫非錯字）——fast-track 真實服務面遠小於 §1 預期；吞吐痛點主解事實上由 deferred 回執鏈（已落地驗證）承擔。
- 待 user 裁決：EP 字面 INVALIDATE（回滾豁免原文）vs amendment（保留已收斂窄 predicate＋吞吐主解重定位 deferred）——arch-thinking 摘要見 session 報告。
