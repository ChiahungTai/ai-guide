# Agent Review Cycle — Agent Tool 審查範本（3-perspective lens）

> **載入時機**：審查命令的 adapter 選用 Agent Tool 載體時讀取（載體選擇屬 adapter 執行細節，**不再是 effort／max-agents 門檻**）。**context 配置由風險 profile 驅動**——判定源＝[review-engine](../review-engine/SKILL.md)「審查模式判定規則」；Workflow 載體見 [workflow-review-pattern.md](./workflow-review-pattern.md)。

Writer/Reviewer 分離的品質閘門 — 用獨立 Agent context 審查，避免主 LLM 審自己的 code。agent 類型一律 `Explore`（read-only by design）。

---

## 核心設計：3-perspective lens（三正交視角，配置由風險 profile 決定）

**三 lens 定義單一源＝[review-engine](../review-engine/SKILL.md)「review 執行預設」點 4**（正交性與錨定差異論證在彼，此處不重複）——本範本只放 Agent Tool 執行形態：

> 下表為執行形態展開；lens 與 profile 的定義單一源＝review-engine（點 4／『審查模式判定規則』），衝突時以 review-engine 為準。

| lens | context 錨定 | 審什麼 | 補的 blind spot |
|------|---------|--------|----------------|
| **① fresh（clean）** | **只有 impl diff，無 UC / 無 EP / 無意圖提示** | 「這 code 自身看哪裡怪 / 冗餘 / 缺 / 可疑 / 過度設計？」 | 作者 rationalize（bias） |
| **② intent（UC-anchored）** | UC / EP Scenario Matrix + impl diff | 逐 UC 檢驗「impl 滿足嗎？漏了什麼意圖？偏離 EP 嗎？」 | 漏覆蓋 / 偏意圖（coverage） |
| **③ correctness（邊界正確性）** | impl diff（不錨定意圖，主動質疑邊界） | 「跨日 / 空值 / 溢出 / 空資料 / 邊界案例？邏輯對嗎？測試充分？」 | 邏輯 bugs / 邊界案例 / 測試不足（correctness） |

> **① fresh 腿刻意不給任何提示** — 它讀 code 的自身 merits，不被「這應該是做 X」的框架綁住。**新鮮 context 的價值就在無錨定 → 正交發現**。機械軸（測試路徑覆蓋）不靠 review agent——`/implement` 硬閘門＋`/audit-test` 承載；**正確性由 ③ lens 顯式覆蓋**（clean 的 smell 視角不主動質疑邊界——詳 review-engine 點 4 ③）。

### 配置表：風險 profile 驅動（ordinary 單 reviewer 是新預設；固定三 agent／max-agents 降級表已廢除）

> 下表為執行形態展開；lens 與 profile 的定義單一源＝review-engine（點 4／『審查模式判定規則』），衝突時以 review-engine 為準。

| 風險 profile | context 配置 | 本範本執行形態 |
|------|----------|--------------|
| **ordinary**（無邊界觸發的一般變更——**新預設**） | **單一獨立 context**：同一 reviewer 依序覆蓋三 lens——fresh-first：①無錨讀 source/diff → ③正確性與驗證 → ②需求對照；**省略任一軸＝scope 未覆蓋** | 單 agent prompt 明示三段依序執行＋逐軸輸出 findings（下方「Agent Prompt」） |
| **boundary**（public API／跨 context invariant／money/risk/security／控制面 authority-gate） | **分離 fresh＋intent**（各自獨立 context：①fresh 腿不餵意圖、②intent 腿餵 EP/UC——餵料差異見下方 prompt）＋③correctness 或 extras 專項按觸發附加 | 多 agent 各腿依餵料差異分別組 prompt |
| 條件不明／無法判定 | 取更保護分支（boundary） | 同上 |

**extras（特徵觸發，不得被 ordinary 單 context 吞掉）**：整合器／外部整合 → adversarial **且觸發段級 review**；新簽名／注入點 → architecture＋consumer-perspective **且觸發段級 review**；跨模組 → architecture；UC 數 >6 → UC-split。映射框架單一源＝[review-engine](../review-engine/SKILL.md)「review 執行預設」點 5；adapter 接線（消費命令機械信號 → 通用特徵）見各消費命令（如 [implement](../implement/SKILL.md) Agent Review 的觸發映射）。執行範本據此組 prompt。

**明示**：ordinary 單 context 順序覆蓋**不是 fresh/primed 雙 context 的等價品**——只保證 Writer/Reviewer 分離，不宣稱等同多 context 獨立查證。並發容量（[model-routing 並發表](../model-routing/SKILL.md)）是**上限，不是必須派滿的配額**——不得以「cap 有剩」回填 agent；**不以 quota 臨場降級 profile**（恢復時恢復原 profile）。

印出確認：`[Review Agent] profile=<ordinary|boundary>, mode=<single-context | fresh+intent 分離>, extras=<N/A | 列表>`

> review agent candidate＝Reviewer work unit 解析（qualification=`review_findings`／authority=findings——無 disposition/apply；judgment_floor 預設 execution，高保護面／跨邊界語義面升 decision）——binding 照 model-routing resolver（registry default pin 不隨主 session 漂移，AIR-43；CC＝inherit）；見 [review-engine](../review-engine/SKILL.md)「review 執行預設」點 3 與 [model-routing](../model-routing/SKILL.md)。spawn `model` param 填選定 candidate 的 literal。

---

## Agent Prompt

> subagent prompt 遵循 [self-contained-prompt](../self-contained-prompt/SKILL.md) 原則（本場景 = **同環境・審查型**：subagent 讀得到 repo，給路徑不嵌內容）。

**各 reviewer 腿共含**（boundary 分離腿與 ordinary 單 context 皆適用）：
- `git diff` 範圍（所有產出的變更）
- 相關檔案路徑（必讀）
- [review-engine](../review-engine/SKILL.md) 通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/模式判定）+ [code-review-and-quality](../code-review-and-quality/SKILL.md) 六軸方法論
- rules-reminder 規則摘要（Agent 看不到 auto-loaded rules）
- **CR 接線查證段（硬性）**：照 [review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」CR 段逐字貼入（Explore＝CLI 形態；trigger-based）——diff 含 callable 新增/修改且命中觸發面（public API/介面、rename/delete、跨模組、negative claim）才必跑 callers；callers 為空 → 互補 rg；engine 缺場 `[WARN]`＋rg fallback；未命中觸發面 → findings summary 註明 N/A

**ordinary 單 context 額外**：明示「同一 context 依序覆蓋三 lens——先無錨讀 source/diff（①），再正確性與驗證（③），最後需求對照（②）；逐軸輸出 findings，省略任一軸＝scope 未覆蓋」

**① fresh 腿額外**：明示「**不給任何 intent 提示，純讀 code 自身評估** — 哪裡怪、冗餘、缺、可疑、過度設計」

**② intent 腿額外**：UC / EP 場景清單 + 「逐 UC 檢驗 impl 滿足度，標漏掉的意圖與 EP 偏離」

---

## Authority 輸出契約與視覺證據（review 腿共用——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（Role→authority allow-list／WorkUnitContract independence 欄／resolver precedence 步 7）；此處只列 Agent Tool 模式執行面。

- **artifact recipe（越權＝artifact schema 層阻擋）**：evidence artifact 不含 disposition/apply 欄；findings artifact 不含 apply／final disposition；**只有 Arbiter artifact 有 disposition**——本範本的 ①②③ 皆 review/evidence 腿，終判（✅/❌/⚠️）由 `/judge-review`（Arbiter 腿）落下。Review 腿面對「直接裁決／順手修改」壓力時以**實際輸出／副作用**判分——產出現 disposition/apply 欄即越權（SM-5/SM-6）。
- **independence（跨家族第二意見）**：`kind=different_provider_family`＋`relative_to`（如 writer）＋`required`＋`fallback`——一般高保護面＝**soft-visible**（缺 alternate family 可 `explicit_same_family_degradation` 顯性降級並記錄）；**user 明示跨家族＝required=true，缺場 fail loud**（禁靜默同家族替代，SM-7）。本範本三 lens 的 context 差異（clean／UC／Correctness 錨定方式不同）與 provider-family independence 正交——前者防錨定 bias、後者防家族盲點。
- **視覺證據（review 腿讀圖時）**：source identity/hash＋transport binding＋delivery receipt 由 **dispatcher 產生**（派工方記錄）；`arbiter_viewed_source=true` **只能由 receipt 推導**——收件方自述「已看圖」不算數。無同時 decision-qualified＋native_vision＋image_transport 的單一 candidate 時走 **decomposed** 形態：observer 看原圖產 observation artifact（分 facts/interpretations＋region/coordinates＋uncertainty＋observer model/binding）→ decision 腿 input 無 raw image、只含 observation artifact，verdict 帶 `arbiter_viewed_source=false`＋`decomposed-not-equivalent`（不得宣稱等價單模型原生視覺裁決，SM-9/SM-10）。

---

## 結果交接

各腿 findings 合併（boundary 多腿按 profile 合併規則——單一源＝[workflow-review-pattern](./workflow-review-pattern.md)「findings 去重與復用判準」；ordinary 單 context 即單份三軸 findings）→ 主 LLM invoke `/judge-review`（✅ / ❌ / ⚠️）→ apply ✅ 採納清單 → `ruff check --fix && ruff format`。

findings 若需持久化（跨 session / `.review/` / EP 回寫），用 [workflow-review-pattern.md](./workflow-review-pattern.md) 的 Finding Record 格式（跨命令追蹤標準）。

**結論回卡（強制——AIR-108）**：各腿回收當下以一行 `backlog task edit <卡id> --append-notes "<腿名＋verdict＋evidence ref/jobId>"` 落卡——詳細 findings 留工單輸出檔、卡面帶指針，禁逐腿全文散寫（噪音防護）；無卡弧 → 落 EP／report 並記錄去向。Arbiter 裁決的回卡契約單一源＝[judge-review](../judge-review/SKILL.md)「寫入持久化」第 6 點。

---

## 與 Workflow 路徑的關係

Workflow（多 agent 協調腳本）和 Agent Tool（本檔）**共存**——載體選擇屬 adapter 執行細節，**不再是 effort level 偵測或 max-agents 門檻**（判定規則真相源見 [review-engine](../review-engine/SKILL.md)「審查模式判定規則」；載體使用時機速查見 [workflow-review-pattern](./workflow-review-pattern.md)「何時使用 Workflow」）：

- 多 context／多軸 profile 協調（boundary 分離 fresh＋intent、多維度並行、adversarial verify）→ [Workflow](./workflow-review-pattern.md)（schema + adversarial verify）
- 單一 reviewer context（ordinary profile）或輕量單 agent → 本檔（3-perspective lens）

兩路徑 findings 交接一致（同交主 LLM `/judge-review`）。
