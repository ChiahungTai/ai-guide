# Workflow Review Pattern — 多 Agent 審查協調範本

> **載入時機**: 僅在審查命令的 adapter 選用 Workflow 載體（多 agent 協調）時讀取。載體選擇屬 adapter 執行細節，**不再是 effort／max-agents 門檻**——風險 profile 與 context 配置判定源見 [review-engine](../review-engine/SKILL.md)「審查模式判定規則」（可觀察變更語義 → ordinary／boundary profile）。

---

## 何時使用 Workflow

> 判定規則真相源見 [review-engine](../review-engine/SKILL.md)「審查模式判定規則」；下表為 Workflow 範本的使用時機速查。

| 條件 | 路徑 | 說明 |
|------|------|------|
| 多 context／多軸 profile 協調（boundary 配置分離 fresh＋intent、多維度並行審查、adversarial verify） | ✅ Workflow tool | 確定性協調、schema 輸出、內建進度追蹤 |
| 單一 reviewer context（ordinary profile）或輕量單 agent | ❌ Agent tool / session | 單 context 無需協調層 |

載體選擇不構成獨立性——context 獨立性由風險 profile 配置決定（review-engine），不由工具承載。

Workflow tool 的優勢：
- **確定性協調**：腳本控制流程，非 LLM 逐輪決定
- **Context 保護**：中間結果存在腳本變數，不佔用主 context
- **結構化輸出**：schema 強制 agent 回傳可解析的 JSON
- **可恢復**：同 session 可暫停/恢復
- **進度追蹤**：`/workflows` 內建 view

---

## 兩階段模式

全程自動執行，Workflow 不支援 mid-run 用戶輸入。

### Phase 1: Review — 平行維度審查

- `parallel()` spawn 所有啟用維度的 agents
- 每個 agent 用 `schema` 參數強制結構化輸出
- agent 類型一律 `Explore`（read-only by design）
- agent 看不到主對話歷史、其他 agent 結果 — prompt 是唯一 context 來源

### Phase 2: Verify — 分級驗證

兩級 verify node（分級＝成本對齊風險；錨點屬實性與成立性裁決分離）：

- **第一級：錨點批次驗證（Important+ 全 findings，浮出前）**：合併各維度 findings 後，**單一 lite agent 批次**驗證錨點屬實性（file:line 存在、符號存在、引用原文屬實）——非 per-issue spawn（成本爆炸）。錨點不實的 finding 退回不浮出。**驗證≠裁決**：屬實性（機械/lite）與成立性（judge-review 層）分離
- **第二級：Critical 對抗 quorum**：對錨點屬實的 Critical findings spawn 驗證 agent 嘗試**推翻（refute）**——**3 verifier + ≥2/3 確認** → finding 保留；非 Critical 不跑對抗 verifier（Important 仍須先過第一級錨點閘，通過後直接保留；Suggestion 不進錨點閘；終判交 Main LLM judge-review）
- **compliance vs judgment 分流**：compliance 類維度（機械規則對照，如 instruction 檔合規）是 recall 問題——冗餘 agent 有益；judgment 類維度是 bias 問題——需 context 差異（fresh＋intent 分離配置，dual-context 語義，見 review-engine 執行預設點 6），quorum 對共同盲點無效（[acceptance-evidence](../../rules/acceptance-evidence.md) A/B 軸）。兩者不互斥，按維度性質配

---

## Schema 定義

### DimensionVerdict（Review agent 回傳）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string", "description": "唯一 ID，如 F1, F2" },
          "title": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "important", "suggestion"] },
          "confidence": { "type": "string", "enum": ["confirmed", "evidence-based", "inferred"], "description": "信心水準（見 review-engine）；與 VerifyVerdict.confidence（verify 把握度）不同概念" },
          "file": { "type": "string", "description": "專案相對路徑（Important+ 必填——錨點驗證閘的 join 鍵；Suggestion 可省）" },
          "line": { "type": "number", "description": "同上" },
          "description": { "type": "string" },
          "suggestion": { "type": "string" }
        },
        "required": ["id", "title", "severity", "confidence", "description", "suggestion"]
      }
    },
    "summary": { "type": "string", "description": "該維度的整體評估" }
  },
  "required": ["findings", "summary"]
}
```

### VerifyVerdict（Verify agent 回傳）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "isReal": { "type": "boolean", "description": "finding 是否成立" },
    "reason": { "type": "string", "description": "判斷理由" },
    "confidence": { "type": "string", "enum": ["high", "medium", "low"] }
  },
  "required": ["isReal", "reason", "confidence"]
}
```

---

## Authority／independence／artifact schema（review 腿共用——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（Role→authority allow-list／WorkUnitContract independence 欄）；此處只列 Workflow 消費面。

- **artifact recipe（越權＝artifact schema 層阻擋）**：evidence artifact（Verifier 腿）無 disposition/apply 欄；findings artifact（Review 腿，含 DimensionVerdict→Finding Record）無 apply／final disposition；**Arbiter artifact 才有 disposition**——Workflow 的 Review/Verify phase 產出皆屬前兩類，終判（✅/❌/⚠️）由 Main LLM judge-review（Arbiter 腿）落下。Review/Verify agent 面對「直接裁決」壓力時以實際輸出判分。
- **independence 欄（dual-context／跨家族腿）**：`kind=different_provider_family`＋`relative_to`＋`required`＋`fallback`——soft-visible 缺場可 `explicit_same_family_degradation` 顯性降級並記錄；user 明示跨家族 required=true 缺場 **fail loud**。Verify phase 的 3-verifier quorum 是同家族 context 差異（對共同盲點無效，見 [acceptance-evidence](../../rules/acceptance-evidence.md) A/B 軸），與 provider-family independence 正交。
- **dispatch 掛鉤**：Workflow `agent()` 呼叫即 DispatchPlan 消費點——selected candidate 走 carrier adapter 三路（[model-routing](../model-routing/SKILL.md) DispatchPlan 條）；quota/runtime 失敗記 work-unit-local DispatchTrace（1308 於 retryable-at 前排除、429 bounded backoff），候選耗盡＝no-candidate report 停止，禁 loop。

---

## Finding Record（跨命令持久化標準）

> **核心原則**：審查發現(finding)的對話對象主要是另一個 LLM(`/implement` 內串接、`/copy` 給外部 LLM)。**跨命令自動化場景**（接 `/judge-review`/`/followup-review`）finding 須持久化、結構化、跨命令可追蹤；**人主導工作流**（review session 對話 + `/copy` 搬運）finding 留對話由人對照 diff 判讀，不強制持久化（見下方「持久化位置（optional）」）。

### Finding Record = DimensionVerdict + 追蹤欄

Review agent 回傳的 `DimensionVerdict.findings[]` 是**發現時**狀態。持久化時擴充為 Finding Record,加入生命週期追蹤欄:

| 欄位 | 來源 | 用途 |
|------|------|------|
| `id` / `title` / `severity` / `file` / `line` / `description` / `suggestion` | DimensionVerdict 沿用 | 發現本體 |
| `驗證式` | 追蹤 | 可機械複驗命令（rg 命令／pytest case——**Important+ 必附**；judge 裁決與 followup 驗收共用同一驗證基準） |
| `status` | 追蹤 | 生命週期見下(跨命令 join key) |
| `source` | 追蹤 | 產生命令(由表格標題 `## <命令> Findings` 編碼,不單獨成欄) |
| `decision` | 追蹤 | judge-review 的 ✅ / ❌ / ⚠️ |

### 帳本 header identity（resume 與重複審比對鍵）

帳本檔頭帶 identity 區塊（header 級、非逐條）——跨 session resume 與「implement 已審 vs post-build 再審」的去重比對都靠它：

- **task baseline**：本弧任務 baseline hash（卡 Plan 或 EP 整合策略所記）
- **reviewed**：審查當下 HEAD hash
- **uncommitted identity**：本弧 tracked diff hash＋untracked 路徑清單＋content hash（與 [work-order](work-order.md) §3 dirty identity 契約同詞）——只有 rev 會讓「untracked-only WIP 改變」場景（HEAD 未變、新檔內容變）假吻合跳審
- **scope**：本弧 review 範圍——包含／排除檔案與 UC/invariant 清單（復用判準第 3 條的比對鍵）
- **review_profile**：風險 profile identifier＋定義內容 identity（定義源＝[review-engine](../review-engine/SKILL.md)「審查模式判定規則」；identifier＋該 profile 定義內容的 hash／版次標記——復用判準第 4 條的比對鍵）。正典寫法＝`review-engine@<sha>`，sha 取 `git hash-object -- skills/review-engine/SKILL.md` 輸出前 12 碼（content-bound，非 HEAD）；帳本身份行照寫此值。
- **coverage**：各軸（profile 必需視角／extras）完成／未驗狀態＋evidence ref（指向 findings／驗證證據所在；**缺證據≠PASS**——未驗軸不得標完成）
- **writer**：產生本清單的命令/session

### findings 去重與復用判準（complete coverage 宣稱的必要條件）

**去重規則**：同位置（file:line）**且同一 claim** 才合併；矛盾 findings **並列**（標 `conflict`，兩方觀點並列）交 Arbiter 裁決層（Workflow 鏈＝judge-review；EP 鏈＝主 session Arbiter），**不以投票或「先回者」裁決**。

**可復用判準（五條，缺一即不得宣稱 complete coverage／不得據以跳審）**：

1. **同任務基線**：task baseline 與目前任務相同
2. **相同實物內容**：tracked diff hash＋untracked 路徑與 content hash 與當前一致（untracked-only 變更也算內容變更）
3. **scope 覆蓋目前要求**：header `scope` 包含目前所需的檔案與 UC/invariant
4. **profile 相容**：header `review_profile` 與目前所需 profile identifier 相同、定義內容 identity 未變，且該 profile 的獨立性配置滿足目前要求
5. **證據可讀且未失效**：`coverage` 所指 evidence ref 可達、內容可核對

**不變項**：revision 或 profile 變更**不能復用舊結論**——對 delta 重審；複用 findings **不等於**複用測試——環境／config／input 改變時驗證證據另行失效。Reviewer≠Arbiter（disposition 僅 Arbiter artifact，見上方 artifact recipe）；缺證據≠PASS。

**status 生命週期**——decision 映射與狀態流轉是**兩條獨立的軸**(同名互斥是定義錯誤:`adopted` 是決策後中繼態、非 terminal):

- **decision 映射軸**(judge-review 落帳):✅ → `adopted`、❌ → `rejected`、⚠️ → `needs-confirmation`——`adopted`/`rejected`/`needs-confirmation` 皆非 terminal
- **狀態生命週期軸**:**Code review flow**(經 judge-review):`open` →(`adopted` / `rejected` / `needs-confirmation`)→ `implemented` → `verified` → `closed`。**rejected 不經 implemented**,直接 `closed`(不實作)。**EP flow**(ep-review/ep-validate,無 judge-review):`open` → `implemented`(修正入 EP)/ `verified`(POC 通過)
- **terminal 值域**(機械契約,單一源＝`review_ledger.py` TERMINAL_STATUSES):canonical ＝`verified|closed`(生命週期終點);`resolved`＝容錯 terminal(歷史帳本方言——parse 視同 terminal、lint converged 接受;新寫入用 verified/closed)
- commit 階段 2.6（optional）列出殘留 `open` finding 提醒（不阻擋；status 靠 LLM 更新會漏，僅作提醒線索非機械閘門，最終把關靠人對照 diff）

> **status 寫入責任（AIR-121）**：帳本 header identity／`decision`／terminal `status`（canonical `verified|closed`＋容錯 `resolved`）是實際被 parse/join/count 的機械契約欄位——落盤須通過 consumer-equivalent 機械驗證（`skills/post-build/scripts/review_ledger.py` lint/parse，fail-closed）；寫入保障必須至少匹配下游讀取契約，準則單一源＝[quality-constraints](../../rules/quality-constraints.md)「數據完整性優先」寫入保障段，分類軸（機械／記錄／混合面）＝[memory-audit](../memory-audit/SKILL.md)「載體統一定義表」寫入權軸。

### closure lens 分工（修正驗證雙腿——AIR-61 標準化）

> 修正驗收的 lens 配置規則；執行面接線（同 session 續接形態、cost 判準、守衛處置）單一源＝[followup-review](../followup-review/SKILL.md)「muse reviewer 續接驗收」＋[model-routing](../model-routing/SKILL.md)「session 定向接續」，本節不重抄。

- **closure 腿（同 session 續接 followup——原 reviewer 帶 findings context）只做逐 finding closure**（逐項通過/未通過＋驗證式機械複跑），**不當 final acceptance**——原 reviewer 對自己 findings 的修正驗證有保真度優勢（MOS-74 實證），對修正引入的新問題卻有共同盲點。**例外條款**：finding 級 closure 附驗證式且機械複跑通過者，可為**該 finding** 的終驗（粒度＝單一 finding，非整弧覆蓋）
- **regression 腿（優先跨家族）補派觸發（兩者其一即派）**：①**修正越出 finding scope**——修正 diff 觸及 findings 未覆蓋的檔面/invariant；②**新問題密度高**——修正輪帶回的新增 findings 密度達編排者裁量之顯著水準（heuristic，由編排者當弧判）。任務＝抓 fix-induced regression 與 scope drift；觸發判定由主鏈編排者做（post-build 階段 3／implement 修正迴圈），觸發①（越出 finding scope）走既有新 scope 重分級路徑（review-engine 風險 profile 重判定）；觸發②為本節新增密度 heuristic
- **量測獨立性**：closure 腿的 closure accuracy 與 regression 腿的 drift-detection rate **分開記錄**——closure 全綠**不得**推斷無 drift；兩 lens 輸出差異的裁決不得同家族單審（independence 語義見本檔「Authority／independence／artifact schema」節）

### 持久化位置（optional）

> **人主導工作流**（finding 在 review session 對話、`/copy` 搬運）：不需持久化，finding 處置由人對照 diff 判讀。以下持久化僅給**跨命令自動化場景**（接 `/judge-review` / `/followup-review`）。

| 情境 | 位置 |
|------|------|
| **工作鏈**（post-build 編排、standalone code-review→judge→followup） | `.review/<branch>.md`（工作帳本，代表一次變更的 finding 清單；**caller 指定可覆寫**） |
| **規劃期**（EP Review Cycle——ep-review/ep-validate，EP 未歸檔） | EP review 區段（EP 5a 歸檔後結構性不可用——工作鏈一律走 `.review`） |
| **規劃期無 EP**（card-first 弧——計畫載體＝card Planning Contract） | owning 卡 notes／`.review/` |

`.review/` 為 ephemeral 工作產物,須加入 `.gitignore`;**`/commit` 階段 6 成功後清除**（commit 結算點，同 POC 生命週期）。`status` 機制靠 LLM 更新會漏，僅作提醒線索，非可靠閘門 —— 最終把關靠人（commit 確認對照 diff）。

### Markdown 表格呈現格式(持久化與 /copy 載體)

人類可讀 + 機器可解析。所有命令的持久化 finding 統一用此格式:

```
## <命令> Findings — <branch 或 EP 段落>

> identity: baseline=<任務 baseline hash> · reviewed=<HEAD hash>（或 `reviewed revision：`——兩形皆 canonical，lint 錨同受） · uncommitted=<tracked diff hash>＋untracked <路徑清單＋content hash>（clean 標 none）· scope=<包含檔案/UC/invariant；排除項> · review_profile=<identifier＋definition identity> · coverage=<各軸完成/未驗＋evidence ref> · writer=<命令/session>

| ID | 嚴重度 | 檔案:行 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|----|--------|---------|------|------|--------|------|------|
| F1 | 🔴 critical | src/foo.py:42 | ... | ... | `rg "..." tests/` | open | — |
| F2 | 🟡 important | src/bar.py:10 | ... | ... | `pytest tests/test_bar.py::test_x` | adopted | ✅ |
```

`/copy` 場景:用戶貼此表格給外部 LLM,回饋以同格式 append 回寫。

cell 內出現 pipe(`|`)一律寫轉義形 `\|`(驗證式欄 rg pattern 常見)——`review_ledger.py` lint/parse 容錯讀取轉義形,未轉義裸 pipe 會拆壞欄位。

---

## 腳本骨架

各命令提供具體的 `dimensions` 陣列（維度名稱、prompt、啟用條件）。骨架定義通用協調邏輯：

```javascript
export const meta = {
  name: '[command]-review',
  description: '[command] multi-agent review with adversarial verification',
  phases: [
    { title: 'Review', detail: '平行維度審查' },
    { title: 'Verify', detail: 'Adversarial 驗證' }
  ]
}

const REVIEW_SCHEMA = { /* DimensionVerdict schema */ }
const VERIFY_SCHEMA = { /* VerifyVerdict schema */ }
// review command agent = Reviewer work unit（qualification=review_findings、authority=findings 無 disposition/apply；judgment_floor 預設 execution——user 09-09 拍板 findings 生產層已實證，高保護面/跨邊界語義面升 decision）；binding 經 model-routing resolver（catalog/presets 供給，此處不材料化 model 值）；judge 層恆為 decision work unit（AIR-24）。見 model-routing skill + review-engine「review 執行預設」點 3
// author 時依當前 session 填選定 candidate 的 literal（下為 CC 詞彙面範例 → inherit）
const REVIEW_MODEL = 'sonnet'

// --- 各命令定義自己的 dimensions ---
// const dimensions = [
//   { key: 'completeness', prompt: '...', enabled: true },
//   ...
// ]
// const enabledDimensions = dimensions.filter(d => d.enabled)

// Phase 1: Review
phase('Review')
const reviews = await parallel(
  enabledDimensions.map(d => () =>
    agent(d.prompt, {
      label: `review:${d.key}`,
      phase: 'Review',
      schema: REVIEW_SCHEMA,
      agentType: 'Explore',
      model: REVIEW_MODEL
    })
  )
)

// Phase 2: Verify (only Critical findings)
// ⚠️ 可自訂：各命令可調整 verifier 數量和 quorum 門檻
//   預設：Critical → 3 verifier + 2/3 quorum
//   輕量（如 /ep-review）：important（輕量別名 must-fix）→ 1 verifier/finding
//   在此修改 verifier 數量：Array.from({length: N}, ...)
// Phase 2a: 錨點批次驗證（Important+ 浮出前；單一 lite agent，非 per-issue）
phase('Verify')
// 全域唯一鍵：各 dimension agent 各自回 F1/F2…，flatten 後以 `${dimension}:${id}` join（防同名 id 錯配）
const allFindings = reviews.flatMap((r, di) =>
  (r?.findings ?? []).map(f => ({ ...f, key: `${(dimensions[di] && dimensions[di].key) || 'd' + di}:${f.id}` }))
)
const suggestions = allFindings.filter(f => f.severity === 'suggestion') // 不進錨點閘，直接保留（schema 允許無 file/line）
const importantPlus = allFindings.filter(f => f.severity !== 'suggestion')
const anchorable = importantPlus.filter(f => f.file != null && f.line != null) // 缺錨點＝閘未過，退回不浮出
const ANCHOR_MODEL = 'sonnet' // lite 地板（user 09-05：haiku/luna 基本不用，最低 sonnet/terra 級；CC 詞彙——dispatch 不綁 backend id，背後接線 machine-local）
const ANCHOR_SCHEMA = { /* { results: [{ key, anchorReal: boolean, evidence }] } */ }
const anchorReport = await agent(
  `批次驗證下列 findings 的錨點屬實性（file:line 存在、符號存在、引用原文屬實）。逐項附機械證據，不判斷成立性。\n` +
  anchorable.map(f => `${f.key}: ${f.file}:${f.line} — ${f.title}\n  主張：${f.description}`).join('\n'),
  { label: 'verify:anchor-batch', phase: 'Verify', schema: ANCHOR_SCHEMA, agentType: 'Explore', model: ANCHOR_MODEL }
)
const anchored = anchorable.filter(f => {
  const r = anchorReport?.results?.find(x => x.key === f.key)
  return r?.anchorReal === true
})

// Phase 2b: Critical 對抗 quorum（僅錨點屬實的 Critical）
const criticalFindings = anchored.filter(f => f.severity === 'critical')
const normalFindings = anchored.filter(f => f.severity !== 'critical')

// Critical → 3 verifier + 2/3 quorum
const verified = await parallel(
  criticalFindings.map(f => () =>
    parallel(Array.from({length: 3}, () =>
      agent(
        `Adversarially verify this finding. Try to REFUTE it. Check against actual code.
         Finding: ${f.title} — ${f.description}
         File: ${f.file}:${f.line}
         Default to isReal=false if uncertain.`,
        { label: `verify:${f.id}`, phase: 'Verify', schema: VERIFY_SCHEMA, agentType: 'Explore', model: REVIEW_MODEL }
      )
    ))
  )
)

// 2/3 quorum
const confirmedCritical = criticalFindings.filter((f, i) => {
  const votes = verified[i].filter(Boolean)
  return votes.filter(v => v.isReal).length >= 2
})

return {
  confirmed: [...suggestions, ...normalFindings, ...confirmedCritical], // suggestion 不進錨點閘但也不得丟失
  stats: {
    total: allFindings.length,
    suggestions: suggestions.length,
    anchorFailed: importantPlus.length - anchored.length, // 缺錨點或錨點不實＝退回不浮出
    confirmed: suggestions.length + normalFindings.length + confirmedCritical.length
  }
}
```

### Agent Prompt 必須包含

每個 Review agent prompt 必須包含：
1. 審查範圍（git diff 範圍、EP 路徑、檔案清單）
2. 該維度的檢查項目清單
3. 相關檔案路徑（必讀）
4. 方法論引用（review-engine 的 code-quality profile / 對應 skill）
5. rules-reminder 規則摘要（agent 看不到 auto-loaded rules）
6. CR 接線查證段（硬性——diff 含 callable 變更時；逐字照 [review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」CR 段貼入，Explore＝CLI 形態）

---

## 結果交接

Workflow 完成後回傳 `{confirmed, stats}`，由 Main LLM 接手後續處理：

| 命令 | 後續處理 |
|------|---------|
| `/implement` Phase 4 | invoke judge-review skill → evaluate ✅/❌/⚠️ → apply ✅ findings |
| `/ep-review` | 合成 4 個 DimensionVerdict → EP write-back（回寫修正） |
| `/code-review` | 合成 results → 分三級（Critical/Important/Suggestion）→ commit message |

**結論回卡（adapter-neutral——AIR-108，與 Agent Tool 載體同契約）**：有卡弧時，caller／board-control 在每腿回收後以一行 `backlog task edit <卡id> --append-notes "<腿名＋verdict＋evidence ref>"` 落卡——`.review/<branch>.md` 隨 commit 清除、卡面是跨 session durable 驗證狀態源；spawned worker 禁直寫卡 metadata（verdict 隨回報交 board-control 代落，同 single-writer 分工）。契約細節單一源＝[agent-review-cycle](./agent-review-cycle.md)「結果交接」節。

---

## 與 Agent Tool Fallback 的關係

Workflow 路徑和 Agent tool 路徑**共存不互斥**：

- 命令文件中 Agent tool 指令標記為「Agent Tool 模式（Fallback）」
- Workflow 指令標記為「Workflow 模式（Ultracode）」
- 分支點在風險 profile（判定源＝review-engine『審查模式判定規則』）；載體選擇（Workflow／Agent Tool）屬 adapter 執行細節，非判定門檻。
- Agent Tool Fallback 的完整邏輯（3-perspective review）見 [agent-review-cycle.md](./agent-review-cycle.md)
