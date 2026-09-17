---
name: ep-review

description: "審查 Execution Plan 合理性（完整性、規範合規、一致性、遺漏風險、場景覆蓋）。/ep-review <EP路徑>"
when_to_use: "Review an Execution Plan for completeness, rules compliance, internal consistency, omission risks, and scenario coverage before implementation begins."
argument-hint: "<Execution Plan 檔案路徑>"
allowed-tools: ["Read", "Grep", "Glob", "Agent", "Workflow", "Write", "Edit"]
---

# /ep-review — Execution Plan 合理性審查

EP 審查員，在實作前審查 Execution Plan，確保計畫書完整、合規、可執行。

> **受眾**：LLM 執行鏈命令（layer 1 獨立 context 自判 / layer 2 跨家族第二意見），產出回寫 EP 餵回產 EP 的 LLM，**不給人看**。EP 的人類 viewport 是 `/illustrate --ep`（layer 3 結構 viewport）；方向確認 = 人讀 EP（Scenario Matrix 情境）+ 本命令機器審查。見 root [AGENTS.md](../../AGENTS.md)（legacy `../CLAUDE.md`）「命令的受眾視角」。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [review-engine](../review-engine/SKILL.md) — 通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/審查模式判定規則/多層驗證）
- [arch-thinking](../arch-thinking/SKILL.md) — 架構視角 + 結構機械（F3 用；視角見 §一、機械見 §二）
- [code-quality profile](../review-engine/code-quality-profile.md) — code 審查方法論

Workflow 執行協調：[workflow-review-pattern.md](../_common/workflow-review-pattern.md)（模式判定見 review-engine；本檔定義「審 EP profile」F1-F5 維度）

---

## 審查模式選擇

配置單一源＝[review-engine](../review-engine/SKILL.md)「審查模式判定規則」（可觀察變更語義 → ordinary／boundary）＋「review 執行預設」—— 本命令**消費 S1 profile 配置，不自建派工數量判準**（不按 effort/max-agents 決定 agent 數量；並發容量＝上限非配額，數值歸 [model-routing](../model-routing/SKILL.md)）；僅定義 EP 特有審查 profile（F1-F5）+ 產出（回寫 EP）。Workflow 載體是執行細節非 effort 門檻；schema/腳本見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md)。

| 風險 profile | context 配置（必需獨立性與視角） | 本命令消費 |
|--------------|------------|-----------|
| **ordinary**（一般 EP） | **單一獨立 context** 順序覆蓋 F1-F5 全維度（top-down：先 F3 結構一致性後 F1/F4/F5 細部——結構錯了正確性審白費）；同一 reviewer 必覆蓋各軸，省略任一軸＝scope 未覆蓋。**單 context 順序覆蓋不是 fresh/primed 雙 context 等價品**（明示語義見 review-engine 執行預設點 4） | 單一 registry `code-reviewer` agent 做所有 5 維度 |
| **boundary**（EP 觸及控制面 authority/gate、public API 契約、跨 context invariant、money/risk/security——按 EP 變更語義判定） | **分離 fresh＋intent**＋必要專項：fresh 腿無錨讀 EP 自身 merits（不餵意圖側材料）；intent 腿餵 UC 盤點／卡 Plan／受影響模組 instruction 檔 | 多腿協調可用 Workflow 載體（見下）；資格升級（judgment_floor→decision）由 WorkUnitContract 承接 |
| 條件不明 | 取更保護分支（boundary） | 同上 |

Reviewer work unit（兩 profile 共用）：qualification=`review_findings`、authority=findings（無 disposition/apply）、judgment_floor 預設 execution／高保護面·跨邊界語義面升 decision（user 09-09 審查層預設）；registry 載體 `code-reviewer`（read-only 契約＋審查 mandate 相容〔lite-verify 禁設計判斷，與 EP review 5 維度矛盾〕；binding 解析照 [model-routing](../model-routing/SKILL.md) resolver＋presets，本檔不材料化 model 值；禁內建 `Explore`——無 pin 繼承主模型，execution 預設落空）。
印出確認：`[EP Review Mode] profile=<ordinary|boundary>, agent=single|fresh+intent`

**boundary 多腿時的 Workflow 載體**（可選——協調需求決定，非門檻）：使用 Workflow tool，參照 [workflow-review-pattern.md](../_common/workflow-review-pattern.md) 腳本骨架。

| Workflow Phase | 說明 | Agent 數量 |
|----------------|------|-----------|
| Review | 平行 spawn profile 分離腿（fresh／intent／專項） | 由 profile 配置決定（並發容量為上限） |
| Verify | must-fix findings → 1 verifier/finding | findings 數 |

**啟用維度（F1-F5 全維度——兩 profile 皆須覆蓋，不丟棄）**：

| 維度 | 審查項目 | 優先級 |
|-----------|---------|--------|
| F1 完整性 | 驗收標準、檔案清單、依賴項、邊界情況 | P0 |
| F2 合規 | 命名、code-edit-constraints、instruction 檔 | P0 |
| F3 一致性 | 段落依賴順序、檔案修改矛盾、語義約束 | P1 |
| F4 遺漏 | Demo、測試、__all__、配置、受影響模組 | P2 |
| F5 場景覆蓋 | Scenario Matrix 是否涵蓋 happy path、錯誤操作、邊界、效能期待差異 | P2 |

維度合併＝多腿間的分工手段（不丟棄任何維度），依 profile 配置與並發容量上限推導，非固定派滿。

每個 Review agent prompt 包含：
- EP 完整內容（boundary fresh 腿例外——無錨配置不餵意圖側材料，見上表）
- 該維度的檢查項目清單（F1-F5 各自定義）
- 計畫書提到的檔案路徑（必讀）
- 方法論引用（code-quality profile）
- rules-reminder 規則摘要（Agent 看不到 auto-loaded rules）
- schema: DimensionVerdict（定義在 workflow-review-pattern.md）

Workflow 完成後回傳 `{confirmed, stats}` → Main LLM 合成 5 個 DimensionVerdict → 執行回寫（回寫原則見下方）。

---

## 五維度審查

### F1: 完整性檢查

每段是否有驗收標準？檔案是否完整列出？依賴項是否遺漏？邊界情況是否考量？Use LSP goToDefinition to verify file paths mentioned in EP actually contain the referenced symbols.

**§1b Invariant Impact（觸發時才檢查）**：若段落觸及 invariant-bearing 模組（見 [execution-plan](../execution-plan/SKILL.md) §1b 觸發定義），檢查 §1b 是否含：① 受影響 domain invariant、② §4 驗證對齊。**關鍵：驗證對齊的 test 是否真覆蓋該 invariant 行為**（非僅符號存在——同 acceptance-evidence L3 符號 vs 路徑覆蓋）。producer 宣告的完整性由本維度把關（build 只機械確認 test 存在通過，不判斷 producer 是否漏列 invariant——漏列的 invariant 無人查，§1b 退化為 self-report）—— 此即 Claim→Evidence→Trust 缺口（原則見 [acceptance-evidence](../../rules/acceptance-evidence.md)「Claim→Evidence→Trust」：producer 宣告「沒動 X invariant」= no-impact claim，須獨立證據反證，不接受自述）。

### F2: Rules 合規檢查

命名是否符合 `python-standards`？是否遵守 `code-edit-constraints`？是否有違反元資訊禁止（[instruction-writing](../instruction-writing/SKILL.md)）的內容？是否需要更新 instruction 檔（AGENTS.md 為主，legacy CLAUDE.md）？

### F3: 一致性 + 架構視角檢查（承接 execution-plan 維度①②④）

- **段落一致性**：段落間依賴順序合理？對同一檔案的修改矛盾？技術方案一致？
- **語義約束**（共享型別、命名慣例、架構假設）是否標記？drift 檢查
- **依賴錨點 drift**：EP 對現有 code 的雙向錨定（定義端 + 消費端）是否 drift — 用 LSP `goToDefinition`/`findReferences` 驗證
- **投影 claims 判讀**（EP 段落 0 有跑 `code-reality project` 時）：報告的 `[projected][HOLE]`／`[projected][MISSING]` 進 Findings 表（前綴保留）——**HOLE**＝宣稱整合的符號有 DEF 但零呼叫邊（**未驗證假設非 bug**——回作者接線或撤宣稱）；**MISSING**＝宣稱符號不存在（EP 錨點錯）；WIRED＝邊已鑄（通過）；`[projected]` 一律＝宣告非證據（overlay 是 producer 假設——落地後以真實 index 重驗；洗衣陷阱措辭，工具語義見 [cr-query](../cr-query/SKILL.md)）
- **分層依賴**（承接 execution-plan ①）：domain←use case←adapter←infra 依賴向內？有循環？— 視角與結構資料見 [arch-thinking](../arch-thinking/SKILL.md)（視角 §一、機械 §二）
- **bounded context**（承接 ②）：跨域存取 `_private`？邊界清楚？職責單一？

### F4: 遺漏風險檢查

Demo 檔案有規劃？測試有規劃？`__init__.py` 的 `__all__` 需要更新？配置檔案需修改？受影響的其他模組已列出？

### F5: 場景覆蓾度檢查

full tier 變更必須有 Scenario Matrix。檢查：
- 場景是否涵蓋 happy path、錯誤操作、邊界案例、效能期待差異？
- 每個場景的「觸發 → 預期行為」是否具體可驗證？
- Checkpoint 語義是否與程式碼中的實際 checkpoint 對齊（snapshot / catalog / 無）？
- 矩陣中的「對應 UC」是否與 EP 段落的 UC 引用一致？
- 是否遺漏明顯的使用者情境（如回補多天、跨日、缺前置條件）？

simple 變更（bug fix）跳過此維度。

### 「審 EP profile」維度映射表（與 execution-plan EP Review 共用，零失落）

execution-plan EP Review Cycle 的四維度 ↔ 本命令 F1-F5 對應（execution-plan 引用此 profile，不再自帶維度 — 見 S6）：

| execution-plan 維度 | 本命令歸屬 |
|---------------------|-----------|
| ①分層依賴（domain←use case←adapter←infra 向內？循環？） | F3 |
| ②bounded context（跨域 `_private`？） | F3 |
| ③use case 覆蓋（EP 撐得起 use case？） | F5 場景覆蓋 |
| ④兜底路徑驗證（複合） | 拆解 → 實作落差預見（深層思考）+ 語義約束 drift（F3）+ 依賴錨點 drift（F3）+ **兜底假設路徑驗證**（F3：EP 宣稱「X 段暴露/處理 Y」→ 驗證 X 的 code path 真經過 Y，追 call chain 附 path:line；不經過標「未驗證」非「handled」，Y 另開調查）+ Rules 合規（F2）+ 遺漏（F4）+ 內部一致性（F3） |

### 深層思考（決策證據與後果）

F1-F5 檢查「有沒有漏」，深層思考檢查「方向對不對」。
- **本質需求追問**：每段的核心目的？是否有更簡單的實現路徑？
- **技術方案驗證**：EP 選擇的方案是否基於對現有程式碼的正確理解？讀取相關檔案確認
- **實作落差預見**（承接 execution-plan 兜底④）：EP pseudo code 看起來對，接起來才發現的邊界/副作用/組件互動 — EP 預見極限，標記給 build 注意
- **連鎖後果追蹤**：追直接行為／責任與間接消費者／invariant；關鍵因果附依據。在已查範圍未識別間接影響時標明範圍，不為湊層數編造後果
- **如果錯了**：最壞情境？可以逆轉嗎？逆轉成本？

決策方法見 [deep-thinking](../deep-thinking/SKILL.md)；摘要內容併入既有審查欄位。

---

## 回寫原則

> **核心原則**：EP 是 `/implement` 的唯一真相來源。審查發現不在 EP 裡 = 不存在。

> **適用範圍**：回寫由主 LLM 執行（非 review agent）。`/execution-plan` 流程由主 LLM 自動完成；獨立 `/ep-review` 由主 session LLM 回寫 EP（spawn 模式下 standalone 與內建一致 — 舊 `context: fork` 時 standalone 無 Write 權僅能輸出供手動套用，已隨 spawn 改版對齊）。

build 可能由不同 LLM session 執行，無法存取審查報告。因此：

- **🔴 必須修正** → 審查結論前必須回寫 EP（修正段落內容或新增約束）
- **🟡 建議討論且被採納** → 回寫 EP（作為段落補充說明或新段落）
- **🟡 建議討論但未確認** → 回寫 EP（標記 `⚠️ 待確認：[說明]`），不留在報告裡等 build 自己看
- **禁止「build 再改」**：任何需要 build 執行的變更，必須寫入 EP 的對應段落。審查報告只記錄「已回寫什麼」，不代替 EP 承載實作指令

### 回寫格式

在 EP 開頭(研究摘要之後、UC 盤點之前)加 review 區段,用 Finding Record 表格(欄位定義見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md))。EP 場景「檔案:行」欄填「EP 段落」(如 S2):

```
## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| 1 | 🔴 必須修正 | S2 | ... | ... | implemented |
| 2 | 🟡 建議 | S3 | ... | ... | needs-confirmation |
```

回寫後:🔴 / 🟡-採納 → `implemented`(修正已入 EP);🟡-未確認 → `needs-confirmation`。

### 回寫驗證

回寫完成後，重新讀取 EP 確認修正已入檔。未回寫的發現不得標記為「已處理」。

---

## 技術約束

- **基於實際程式碼**：必須讀取計畫書提到的檔案確認存在
- **五維度覆蓋**：必須覆蓋 F1-F5
- **審查者自證**：提出問題前必須用 Read/Grep 查證宣稱。聲稱檔案存在 → 讀它；聲稱命名衝突 → 查 import 鏈；聲稱依賴順序有問題 → 追蹤執行順序。無法查證的宣稱標注「未驗證」
- **不實作**：審查階段不自動開始實作
- **read-only 審查**：review agent 為 registry `code-reviewer`（read-only 契約保證無 Edit/Write）— 審查階段 review agent 不修改 EP；主 session 僅於審查完成後執行回寫（見回寫原則）

---

## 邊界

- **Always**：完整讀取 EP、查證現有程式碼、覆蓋五維度、輸出結構化報告
- **Ask First**：重大架構問題時是否停止審查、格式不符標準時是否要求修正
- **Never**：不自動實作、不基於推測、不跳過維度

---

## 審查報告格式

```markdown
## 🔍 Execution Plan 審查報告

**檔案**: [計畫書路徑]
**段落數**: [N] 個

### ⚠️ 需要確認的問題

**🔴 必須修正**：[問題 + 修正方式]
**🟡 建議討論**：[問題 + 替代方案]
**ℹ️ 提醒事項**：[已處理項目說明]

### 📝 EP 回寫紀錄

列出已回寫至 EP 的修正（段落 + 修正摘要），供用戶快速確認。

### 審查結論
[可直接執行 / 有條件執行 / 需修正後重新審查]
```

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始 EP 審查"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「EP 審查完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```

---

## 流程位置

> **內建整合**：EP Review Cycle 已整合至 `/execution-plan`。獨立使用適用於手動修改 EP 後重新審查。

```
/spec（純輔助·需求釐清，可選）→ /execution-plan（含 EP Review）→ [/ep-validate] → /implement（含 Agent Review）→ /code-review
```

前置：`/execution-plan`
後續：`/implement`（→ `/post-build`（編排 `/code-review` → `/judge-review` → docs 鏈）→ `/commit`；canonical review flow 見 [code-review.md](../code-review/SKILL.md)）
