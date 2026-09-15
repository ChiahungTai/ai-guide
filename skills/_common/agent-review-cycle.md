# Agent Review Cycle — Agent Tool 審查範本（3-perspective）

> **載入時機**：非 ultracode/xhigh 路徑（effort < xhigh 或 max-agents = 1）。ultracode/xhigh 路徑用 Workflow，見 [workflow-review-pattern.md](./workflow-review-pattern.md)。

Writer/Reviewer 分離的品質閘門 — 用獨立 Agent context 審查，避免主 LLM 審自己的 code。agent 類型一律 `Explore`（read-only by design）。

---

## 核心設計：3-perspective review（固定三 agent）

**觀察**：同樣讀 diff、同樣方法論的多個 agent **共享 writer 的 blind spot** — 都被同一份 context（diff / EP / 維度 checklist）錨定。**三個異質 perspective 的 agent，覆蓋比多個同錨定的 agent 更廣**（多樣性 > 數量）。

| Agent | context | 審什麼 | 補的 blind spot |
|-------|---------|--------|----------------|
| **① clean（Fresh）** | **只有 impl diff，無 UC / 無 EP / 無意圖提示** | 「這 code 自身看哪裡怪 / 冗餘 / 缺 / 可疑 / 過度設計？」 | 作者 rationalize（bias） |
| **② UC-anchored（Intent）** | UC / EP Scenario Matrix + impl diff | 逐 UC 檢驗「impl 滿足嗎？漏了什麼意圖？偏離 EP 嗎？」 | 漏覆蓋 / 偏意圖（coverage） |
| **③ Correctness（邊界正確性）** | impl diff（不錨定意圖，主動質疑邊界） | 「跨日 / 空值 / 溢出 / 空資料 / 邊界案例？邏輯對嗎？測試充分？」 | 邏輯 bugs / 邊界案例 / 測試不足（correctness） |

> **① clean agent 刻意不給任何提示** — 它讀 code 的自身 merits，不被「這應該是做 X」的框架綁住，能挖出 UC-anchored agent 會 rationalize 掉的問題（「UC 說 X，所以這段一定是為 X」）。**新鮮 context 的價值就在無錨定 → 正交發現**。

### 為何同時三個（bias ↔ coverage ↔ correctness 正交）

三 lens 抓的盲點**正交**（錨定方式不同），單跑任一有盲點，同時跑才互補：

- **① clean 抓 bias**（作者 rationalize）—— writer 寫的 code、讀 diff 的 agent 都被「意圖」框住，clean 無 anchor 才能看到合理化掉的問題；但 clean 會**漏「該查的 UC」**（沒給意圖，不知哪些功能該覆蓋）。
- **② UC-anchored 抓 coverage**（漏覆蓋 / 偏意圖）—— 逐 UC 檢驗確保意圖被滿足；但被錨定，**看不到 clean 能挖的合理化**。
- **③ Correctness 抓 correctness**（邏輯 bugs / 邊界案例）—— 主動質疑邊界事實，不靠 code smell；但**漏語意覆蓋 + code smell**（不查 UC、不讀 smell）。

單跑任一有盲點（clean 漏 UC + 邊界；UC 漏合理化 + 邊界；Correctness 漏語意覆蓋 + smell）。三者盲點不重疊（正交），同時跑覆蓋最廣 —— 這是「固定 3 個」的根據（多樣性 > 數量；Correctness 與 clean/UC 錨定方式不同，不適用「共享錨定遞減」，詳 review-engine 點 4 ③）。

### 為什麼固定 3 個（不再 adaptive 多維度 agent）

- **多樣性 > 數量**：舊設計的 4 個 dimension agent（正確性 / 架構 / 測試覆蓋 / EP 合規）共享錨定，邊際覆蓋遞減。3 個異質 perspective（clean + UC-anchored + Correctness）正交覆蓋更廣。
- **機械軸不靠 agent**：測試路徑覆蓋（新參數 `rg "<param>=" tests/`）是 `/implement` 階段 2 硬閘門 + 階段 5c `/audit-test`，不靠 review agent 重複。**正確性由 ③ Correctness lens 顯式覆蓋**（F1 證明 clean 的 smell 視角不主動質疑邊界，漏 `max(fill_dates)` 跨日 bug —— 不再宣稱「clean 自然覆蓋正確性」；詳 review-engine 點 4 ③）；架構由 clean agent 讀 code 自然覆蓋；EP 合規由 UC-anchored agent 覆蓋。

---

## 自適應：max-agents

偵測 effort level 和 max-agents（見 [model-routing 並發表](../model-routing/SKILL.md)）。

| 條件 | 模式 |
|------|------|
| max-agents ≥ 3 | **① clean + ② UC-anchored + ③ Correctness** 三 agent（預設） |
| max-agents = 2 | 兩 agent：保留 **③ Correctness + ① clean**（降級序 Correctness > clean > UC；UC-anchored 降級為 clean-eye 兼查） |
| max-agents = 1 | 單一 agent：**③ Correctness 優先** + 明示「同時 clean-eye + UC-eye」（降級 3-in-1） |

印出確認：`[Review Agent] max=N, mode=3-perspective | 2-agent | single`

> review agent candidate＝Reviewer work unit 解析（qualification=`review_findings`／authority=findings——無 disposition/apply；judgment_floor 預設 execution，高保護面／跨邊界語義面升 decision）——binding 照 model-routing resolver（registry default pin 不隨主 session 漂移，AIR-43；CC＝inherit）；見 [review-engine](../review-engine/SKILL.md)「review 執行預設」點 3 與 [model-routing](../model-routing/SKILL.md)。spawn `model` param 填選定 candidate 的 literal。

### >3 配置（機械特徵觸發，非語義 opt-in）

extra agent 由**消費命令提供的段落風險特徵**機械觸發（非 LLM 語義判「高風險」）。映射框架（通用風險特徵 → extra agent）定義在 [review-engine](../review-engine/SKILL.md)「review 執行預設」點 5（單一源，此處不重複以免 drift）；base 恆 ① clean + ② UC-anchored + ③ Correctness。build 的 adapter 接線（build 機械信號 → 通用特徵）見 [build.md](../implement/SKILL.md) 階段 4「adaptive 觸發映射」。執行範本據此組 prompt。

---

## Agent Prompt

> subagent prompt 遵循 [self-contained-prompt](../self-contained-prompt/SKILL.md) 原則（本場景 = **同環境・審查型**：subagent 讀得到 repo，給路徑不嵌內容）。

**三 agent 共含**：
- `git diff` 範圍（所有產出的變更）
- 相關檔案路徑（必讀）
- [review-engine](../review-engine/SKILL.md) 通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/模式判定）+ [code-review-and-quality](../code-review-and-quality/SKILL.md) 六軸方法論
- rules-reminder 規則摘要（Agent 看不到 auto-loaded rules）
- **CR 接線查證段（硬性）**：照 [review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」CR 段逐字貼入（Explore＝CLI 形態；trigger-based）——diff 含 callable 新增/修改且命中觸發面（public API/介面、rename/delete、跨模組、negative claim）才必跑 callers；callers 為空 → 互補 rg；engine 缺場 `[WARN]`＋rg fallback；未命中觸發面 → findings summary 註明 N/A

**① clean 額外**：明示「**不給任何 intent 提示，純讀 code 自身評估** — 哪裡怪、冗餘、缺、可疑、過度設計」

**② UC-anchored 額外**：UC / EP 場景清單 + 「逐 UC 檢驗 impl 滿足度，標漏掉的意圖與 EP 偏離」

---

## Authority 輸出契約與視覺證據（review 腿共用——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（Role→authority allow-list／WorkUnitContract independence 欄／resolver precedence 步 7）；此處只列 Agent Tool 模式執行面。

- **artifact recipe（越權＝artifact schema 層阻擋）**：evidence artifact 不含 disposition/apply 欄；findings artifact 不含 apply／final disposition；**只有 Arbiter artifact 有 disposition**——本範本的 ①②③ 皆 review/evidence 腿，終判（✅/❌/⚠️）由 `/judge-review`（Arbiter 腿）落下。Review 腿面對「直接裁決／順手修改」壓力時以**實際輸出／副作用**判分——產出現 disposition/apply 欄即越權（SM-5/SM-6）。
- **independence（跨家族第二意見）**：`kind=different_provider_family`＋`relative_to`（如 writer）＋`required`＋`fallback`——一般高保護面＝**soft-visible**（缺 alternate family 可 `explicit_same_family_degradation` 顯性降級並記錄）；**user 明示跨家族＝required=true，缺場 fail loud**（禁靜默同家族替代，SM-7）。本範本三 lens 的 context 差異（clean／UC／Correctness 錨定方式不同）與 provider-family independence 正交——前者防錨定 bias、後者防家族盲點。
- **視覺證據（review 腿讀圖時）**：source identity/hash＋transport binding＋delivery receipt 由 **dispatcher 產生**（派工方記錄）；`arbiter_viewed_source=true` **只能由 receipt 推導**——收件方自述「已看圖」不算數。無同時 decision-qualified＋native_vision＋image_transport 的單一 candidate 時走 **decomposed** 形態：observer 看原圖產 observation artifact（分 facts/interpretations＋region/coordinates＋uncertainty＋observer model/binding）→ decision 腿 input 無 raw image、只含 observation artifact，verdict 帶 `arbiter_viewed_source=false`＋`decomposed-not-equivalent`（不得宣稱等價單模型原生視覺裁決，SM-9/SM-10）。

---

## 結果交接

三 agent findings 合併 → 主 LLM invoke `/judge-review`（✅ / ❌ / ⚠️）→ apply ✅ 採納清單 → `ruff check --fix && ruff format`。

findings 若需持久化（跨 session / `.review/` / EP 回寫），用 [workflow-review-pattern.md](./workflow-review-pattern.md) 的 Finding Record 格式（跨命令追蹤標準）。

---

## 與 Workflow 路徑的關係

Workflow（ultracode）和 Agent Tool（本檔）**共存**，分支點在 effort level 偵測（判定規則真相源見 [review-engine](../review-engine/SKILL.md)）：

- effort = ultracode/xhigh 且 max-agents > 1 → [Workflow](./workflow-review-pattern.md)（schema + adversarial verify）
- 其餘 → 本檔（3-perspective）

兩路徑 findings 交接一致（同交主 LLM `/judge-review`）。
