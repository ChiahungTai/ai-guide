---
name: review-engine
description: "決定 finding 嚴重度（Critical/Important/Suggestion）、標信心水準（confirmed/evidence-based/inferred）、查證審查宣稱、選審查模式（Workflow/Agent Tool）、理解多層驗證鏈、決定 review 執行預設（force 獨立/風險 profile/必需視角/model/spawn-vs-session）時使用。review 命令家族通用審查邏輯的 domain 真相源 — 審查者自證、LSP 查證方法、Writer-Reviewer 分離、多層驗證設計；ep-review/code-review/audit-test/execution-plan EP Review/implement Agent Review 共用。"
when_to_use: "Fires when deciding review methodology or judging findings — 嚴重度分級（Critical/Important/Suggestion）、信心水準（confirmed/evidence-based/inferred）、審查宣稱查證、審查模式判定（Workflow/Agent Tool）、review 執行預設（force 獨立／風險 profile／必需視角／model／spawn-vs-session）。情境：審查判定規則怎麼定、review 命令家族共用邏輯變更。六軸 what-to-check 屬本 skill 側檔 code-quality-profile；發起審查任務跑 /code-review 等命令——兩者皆不觸發本 skill。"
---

# review-engine — 通用審查邏輯 domain 層

review 命令家族的 **domain 層**：跨 ep-review / code-review / audit-test / execution-plan EP Review / build Agent Review 共用的審查邏輯，**唯一真相源**。各命令是薄 adapter（宣告標的 + profile + 產出，委託本 skill），消除「同一審查動作跨命令重複定義且 drift」。

## 收進判準

一條邏輯收進本 skill 的條件：**所有 review 命令都適用**。只適用部分命令的（如 audit-test 的「偵測器非判官」stance、test 的「套件行為寫 demo」）不收，留該命令。

## 邊界（避免製造新 drift）

| vs | review-engine（本 skill） | 對方 |
|----|--------------------------|------|
| [workflow-review-pattern](../_common/workflow-review-pattern.md) | **方法論 + 判定規則**（嚴重度意義、信心水準、自證、為何分離、審查模式判定規則） | **Workflow 執行**：DimensionVerdict schema、兩階段腳本、Finding Record 持久化（判定規則 → 決定讀哪個 schema，依賴方向非耦合） |
| [agent-review-cycle](../_common/agent-review-cycle.md) | （不重疊） | **Agent Tool 模式執行範本**（3-perspective） |
| [arch-thinking](../arch-thinking/SKILL.md) | **依賴**它（架構審查需要視角/機械） | 提供架構視角/機械能力 |
| audit-test 三層驗證鏈 | 通用 why（各層都可能錯） | **具體 audit→judge→followup 鏈細節**（test 講最細，留 audit-test） |

**不裝**（留各 adapter）：維度定義（各 profile 自訂）、產出動作（回寫 EP / commit message / 報告）、stance（audit「偵測器非判官」）、Workflow schema/腳本（留 workflow-review-pattern）。

> **Correctness 邊界（lens vs checklist）**：③ Correctness **lens**（視角，執行預設 — base perspective）在 domain（點 4 ③，所有 review 共用）；Correctness **checklist**（what to check：null / boundary / error path 細節）屬 profile，留 [code-quality profile](code-quality-profile.md) ### 1。lens 上移、checklist 留 profile —— 符合本行「維度定義留各 adapter」（checklist 是維度定義；lens 是執行預設）。

---

## 嚴重度框架（3 級，唯一定義源）

workflow-review-pattern 的 schema、各命令的輸出分類，皆引用此。

| 嚴重度 | 意義 | 動作 |
|--------|------|------|
| **Critical** | 安全漏洞、資料損壞、功能損壞、邏輯錯誤 | 必須在合併/commit 前處理 |
| **Important** | 架構不一致、可讀性、效能隱患 | 應處理 |
| **Suggestion** | 風格、命名、小優化 | 作者可忽略 |

> **Nit/FYI 不採用**：code-review-and-quality 早期有 5 級（+Nit/FYI），但 workflow-review-pattern 的 DimensionVerdict schema 強制 3 級 enum —— Nit/FYI 在 Workflow 模式下無法表達，是死定義。統一 3 級。

---

## 信心水準

每個 finding 必須標信心水準，讓下游（judge-review / 用戶）知道哪些需重點查證：

| 信心水準 | 判斷標準 |
|---------|---------|
| **confirmed**（已查證） | 已讀完整 code/body + 比對過具體行/符號 |
| **evidence-based**（有證據） | 有具體 file:line + rg/fd/LSP 結果，但未深入驗證符號語義 |
| **inferred**（推理） | 基於規範/套件行為推理，未實證 |

**規則：Critical 必須 confirmed 或 evidence-based，禁止 inferred**。推理類 finding 必須額外標「⚠️ 未實證，建議實作層跑 demo 確認」並降級為 Suggestion。

---

## 審查者自證 / 誠信

**核心原則**：每個 claim 必須查證，不基於 LLM 訓練資料推測。findings **非定論** — 可被下層（judge-review / 實作查證）推翻，以「可被推翻」的心態輸出。

- **claim 必須查證**：聲稱檔案存在 → Read 它；聲稱命名衝突 → LSP `findReferences` 查 import 鏈；聲稱依賴順序有問題 → LSP `incomingCalls`/`outgoingCalls` 追蹤；聲稱 dead code → LSP `findReferences`（zero hits = 確認）
- **無法查證標 `unverified`**：不得當成事實陳述
- **對外部行為判斷必須實證**（通用原則）：對套件/演算法/數值特性的判斷，不能只靠推理 — 寫最小 demo 跑一次、或引用套件 source（`.venv/lib/...`）具體行號佐證，否則標 inferred + 降級
- **歸因紀律（mixed-tree）**：審查範圍含非本次變更引入的既有問題時，**不報為 diff 新引入**（標 `pre-existing` 或不報；判準＝baseline 態已存在）。finding 訊噪比政策（HIGH SIGNAL／DO-NOT-FLAG 六條）屬 profile 層——單一源見 [code-quality profile](code-quality-profile.md)「HIGH SIGNAL filter」，本 skill 不收（非全命令適用，見「收進判準」）

**不收**（留各命令）：audit-test 的「偵測器非判官 + read-only」stance（只產 findings 不下判）、audit-test「套件行為 → 寫 demo 跑一次」的 test 特化方法。本 skill 只放通用「對外部行為判斷必須實證」原則。

> **對抗性自查義務**：建議「跳過」任何驗證/審查步驟時，懷疑自己的推進偏好（確認偏差）—— 先有結論再找支持證據 ≠ 嚴謹查證得到結論。對 agent 嚴格（不盲從）、對自己也同等對抗性。

---

## LSP 查證方法

符號查證 cr-first（index 在場；缺場退 LSP），文字搜尋用 rg，檔案用 fd。完整決策樹見 [symbol-query-routing](../../rules/symbol-query-routing.md)。

| 查證對象 | 工具 |
|---------|------|
| 符號定義 / 引用 / 型別 / 呼叫鏈 / 介面實作 | LSP（goToDefinition / findReferences / hover / incomingCalls / outgoingCalls / goToImplementation / workspaceSymbol） |
| 註解、字串、config 值、日誌、TODO | rg（LSP 不索引非程式碼） |
| 檔案搜尋 | fd（LSP 不處理檔案系統） |

> **圖譜 facts 後備（code-reality，companion）**：衝擊半徑 / transitive callers / affected flows / community 等**圖譜級**結構事實，在 engine 在場的 repo 用 code-reality（見 [cr-query](../cr-query/SKILL.md)）—— LSP 查單一 symbol（定義/簽名/單點引用），CR 查 transitive impact/flows（review 的 Architecture 軸 ripple、change scoping）。分工 + GATE + anti-over-reliance（graph=structure≠behavior，dynamic dispatch/config 不在圖裡）見 cr-query；engine 缺場 → `[WARN]` + fallback LSP/scan-project（不靜默降級）。

### 自我否證義務

**「找不到」≠「不存在」**。查證 0 hits 時必須：

1. **換工具**：rg 0 hits → LSP `findReferences`（覆蓋動態引用、避免 pattern 失誤）
2. **換 pattern**：`rg "<Class>\("` 失敗 → 試 `rg "<Class>"`（去 `(`，建構方式可能不同）、`workspaceSymbol`
3. **換位置**：以為在某檔 → `workspaceSymbol` 全域查定義位置
4. **標「查證失敗」而非「不存在」**：三工具都 0 hits，仍只能標「查證失敗，無法確認」—— **禁止標「不存在」**（查證者可能是 pattern 失誤，非程式碼不存在）

> 真實案例：審查者 rg 稱「`<ExecutorClass>` 無建構點」→ 不採納 finding。獨立查證：LSP `findReferences` 立刻列出 import 行 + 建構行。審查者 rg pattern 失誤，把「自己沒查到」誤判為「程式碼不存在」。

> 審查 EP/計畫文件時同理：宣稱「文件內容有誤」的 finding，必須**逐欄引用文件原文**（含決策欄，非只問題欄），並標出與結論矛盾的證據 —— 否則易產生 false positive（讀漏決策欄、虛構 guard 內容）。

---

## 審查模式判定規則

**本段職責 = 判定規則**（domain：可觀察變更語義 → 風險 profile 與必需視角）；**派發到 adapter 範本是命令層職責**（use-case）—— 判定為某 profile 後，各命令自取執行範本（Workflow → [workflow-review-pattern](../_common/workflow-review-pattern.md)；Agent Tool → [agent-review-cycle](../_common/agent-review-cycle.md)）。不強求消除導覽連結（docs 互指可容忍），重點是 domain 不內嵌派發。

**風險 profile 判定**（取代舊 effort/max-agents 門檻——審查儀式由**可觀察變更語義**決定，不按 effort 大小加碼；載體選擇（Workflow tool / Agent Tool / session）屬 adapter 執行細節，不再是 effort 門檻）：

| 可觀察變更語義 | 風險 profile | context 配置（必需獨立性與視角） |
|------|----------|-------------------|
| 無邊界觸發的一般變更（typo、樣式、一般跨檔 feature） | **ordinary** | **一個獨立 context**：依序 source/diff → 正確性與驗證 → 需求對照；同一 reviewer 必覆蓋 profile 各軸（見執行預設點 4）。**這不是 fresh/primed 雙 context 的等價品**——單 context 只保證 Writer/Reviewer 分離，不宣稱等同多 context |
| 邊界變更：**public API、跨 context invariant、money/risk/security、控制面 authority/gate** 改動 | **boundary** | **分離 fresh＋intent 視角**（各自獨立 context，錨定差異見點 4/6）＋必要專項（correctness 或點 5 extras 視角）；資格升級由各 workflow WorkUnitContract 承接 |
| 條件不明／無法判定變更語義 | **取更保護分支** | 按 boundary 配置 |

判定結果決定讀哪個執行範本的 schema/腳本 —— 這是**依賴方向**（判定 → schema），不是耦合。本 skill 只放判定規則，**不重複** schema/腳本（在 workflow-review-pattern）。

> 各命令的覆蓋宣告見各自檔案（命令層可**升級**保護面——加專項、加腿；**不可降級**本表必需項與點 2 的 user scope／hard independence 保護）。

### 為何 Writer/Reviewer 分離

用獨立 Agent context 審查，避免主 LLM 審自己寫的 code/EP。理論基礎：[acceptance-evidence](../../rules/acceptance-evidence.md) 證據獨立性 — AI 同寫 impl + test 時獨立性塌縮，審查同理（同 LLM 審自己的計畫/實作 = 零獨立性 = 證據強度低）。獨立 context 提升證據獨立性——fresh reviewer（同 session 不同 context 的 spawn）抓 **anchoring／局部 reasoning failure**；**systematic bias 是升級軸**：同家族 reviewer 共享家族偏誤，quorum 對共同盲點無效 → 升**跨家族第二意見**（`different_provider_family`，見點 7；跨家族非萬能，終極獨立性是人類 viewport — 見 acceptance-evidence A/B 軸）。

### 為何多層驗證

review finding 可經多層驗證，**各層都可能錯**：

| 層 | 抓什麼錯 |
|----|---------|
| review（偵測/審查） | 品質問題（主要產出 findings） |
| [judge-review](../judge-review/SKILL.md)（評估） | review 的 false positive / 過度陳述 |
| [followup-review](../followup-review/SKILL.md)（驗收） | 實作是否正確套用採納的 finding |

每一層都是獨立查證機會，不假定上層正確。**具體 audit→judge→followup 三層鏈的細節**（各層盲點、偵測器 stance）見 [audit-test](../audit-test/SKILL.md) — test 場景講最細；本 skill 只放通用的「各層都可能錯」原則。

---

## review 執行預設（單一源 — 各 review 命令引用）

> 各 review 命令（ep-review / code-review / audit-test / execution-plan EP Review / build Agent Review）的**執行層預設**集中於此 —— 消除「預設行為跨命令重複定義且 drift」。各命令保留自己的 profile（維度）+ 產出動作，執行預設（force 獨立 / 風險 profile 配置 / model / 視角 / spawn-vs-session）引用本段。

> 審查類命令 spawn agent 預設背景跑（細則見 rules/tool-discipline 背景執行段）

1. **不 auto-detect，force 獨立 agent（預設）**：review 命令預設 spawn 獨立 agent（Workflow / Agent Tool），**不接受 LLM 在裁量點偷懶退 Main LLM 自審**（實證：auto-detect 時 LLM 偷懶 / 搞錯退 Main LLM）。**所有 review 命令含 code-review 都 force 獨立**（取消 Main LLM 自審例外 — 實證:獨立 agent 抓自審盲點）。spawn 失敗降級（顯式標記 fallback，見 [agent-workflow](../agent-workflow/SKILL.md)「spawn 失敗階梯」）除外。

2. **context 配置由風險 profile 推導，不固定填滿**：ordinary＝一個獨立 context；boundary＝分離 fresh＋intent（＋必要專項）——判定表見上「審查模式判定規則」。並發容量（[model-routing](../model-routing/SKILL.md) 並發表；**數值歸 model-routing 擁有，本 skill 不寫數值**）是**上限，不是必須派滿的配額**——不得以「cap 有剩」回填 agent。**explicit user review scope 或 hard independence 不能被較省配置覆蓋**；條件不明採更保護分支（boundary）。回復（resume／弧恢復）時恢復原 profile，**不以 quota 臨場降級**。

3. **agent candidate＝Reviewer work unit 解析（非裸 model 名）**：qualification=`review_findings`＋authority=findings（無 disposition/apply——輸出契約見 [model-routing](../model-routing/SKILL.md) Role→authority allow-list）；judgment_floor 預設 **execution**（user 09-09 審查層預設——findings 生產層跨家族/跨層品質已實證），高保護面／跨邊界語義面升 **decision**（同一 Reviewer Role 保持 findings authority，只有 binding 換——SM-6）。binding/candidate 照 model-routing resolver（catalog qualification 硬過濾→presets/registry default→availability→override→policy）；registry default pin 不隨主 session 漂移（AIR-43）、CC 端 inherit。非 review command 的輕量 agent（verify／anchor 批次／research／explore）＝execution 腿（qualifications 依 workload，值查 catalog）。

4. **必需視角＝三 lens 正交（3-perspective 詞彙：① fresh + ② intent + ③ correctness），配置由風險 profile 決定**（非固定 3 agent）：
   - **① fresh（clean，無 anchor）** 抓作者 rationalize〔bias〕—— 無 anchor 讀 source/diff 自身 merits（**code smell 視角**），不被「該做 X」綁住
   - **② intent（UC-anchored）** 抓漏覆蓋 / 偏意圖〔coverage〕—— 逐 UC 檢驗 impl 滿足度、EP 偏離
   - **③ correctness（邊界正確性）** 抓邏輯 bugs / 邊界案例（跨日 / 空值 / 溢出 / 空資料）/ 測試充分性〔correctness〕—— **主動質疑邊界事實**，不錨定意圖、不靠 code smell
   - **三者錨定方式不同 → 正交**（故不適用「共享錨定遞減」移除理由）：① 無錨讀 smell / ② 錨 EP / ③ 質疑邊界事實
   - **ordinary（單一獨立 context）順序**：fresh-first——先無錨讀 source/diff（① 軸），再正確性與驗證（③ 軸），最後需求對照（② 軸）；**同一 reviewer 必覆蓋 profile 各軸**，省略任一軸＝scope 未覆蓋。**明示：單 context 順序覆蓋不是 fresh/primed 雙 context 的等價品**——只保證 writer context 分離，不宣稱等同多個 context 的獨立查證（boundary 場景仍分離，見下一行）。
   - **boundary（分離配置）**：① 與 ② 各自獨立 context（fresh 腿不餵意圖、intent 腿餵 EP/UC——餵料差異見點 6），③ correctness 或點 5 專項視角按觸發附加。
   - **為何 ③ 同 session 有效**（F1 證偽 agent-review-cycle 舊論述「clean 自然覆蓋正確性」）：clean 是 smell 視角，不主動質疑邊界 → `max(fill_dates)` 跨日 bug 看起來不怪 → 漏。③ correctness 主動質疑邊界事實，**不共享 writer 意圖假設** → 對**非系統性偏誤**邊界 bug，同 session fresh reviewer 可抓。**例外**：系統性偏誤（LLM 普遍弱項，如某類邊界推理）同家族也漏 → **跨家族第二意見**（`kind=different_provider_family`——systematic bias 的升級軸，見點 7；同家族 fresh context 仍抓 stochastic／局部 failure，對家族共享 systematic bias 無效；跨家族亦非萬能，終極獨立性是人類 viewport——見 acceptance-evidence「A/B 軸限制」節：同家族模型仍可能共享偏誤）
   - 執行範本見 [agent-review-cycle](../_common/agent-review-cycle.md)；code-review 六軸、ep-review F1-F5 等以**維度 profile** 分配 context（見各命令 + 上方 profile 判定表），非此 fresh/intent/correctness lens 詞彙本體。

5. **特徵 extras（機械特徵觸發，非 LLM 語義判「高風險」）**：由**消費命令提供的變更特徵**觸發，附加於任一 profile——**不得被 ordinary 單 context 吞掉**：`外部整合`（整合器／外部整合段）→ adversarial **且觸發段級 review**、`公開簽名變更`（新簽名／注入點）→ architecture+consumer-perspective **且觸發段級 review**、`跨模組` → architecture、`UC 數 >6` → UC-split（拿 UC 子集做分拆深度審查，保留適用 scope 的分拆；唯一給 intent 開專項的情境）。`跨模組` 映射目前無 adapter 接線，保留供未來消費命令。**特徵偵測由消費命令提供**（adapter）；review-engine 只定義映射框架（domain），**不列消費命令特有名詞**（DIP — domain 不被 adapter 污染）。容量不足需截斷時依 **architecture（axis 3）> adversarial / edge > consumer-perspective** 取最高，截斷其餘並顯式提示；**絕不** 2nd fresh / 2nd **同一** lens —— 複製 lens 同家族共享盲點，邊際覆蓋 ≈0（UC-split 是不同子集做深度，非複製；多樣性 > 數量）。

6. **fresh＋intent 分離編排（boundary profile 用；dual-context 語義的新錨）**：點 4 的 ①fresh + ②intent 錨定二分法在邊界變更場景的分離配置 —— fresh 腿（如 `code-reviewer`，只餵 diff/source）+ intent 腿（如 `code-reviewer-primed`，餵 diff + EP + Capabilities + dependency-graph（若有）＋消費命令的條件式附加項，如 code-review「B. Agent 載體」的 delta_tour 對照——定義在各消費命令；意圖對齊 / 架構契合 / 測試精簡度 / 完整度光譜）。**context 差異在 spawn prompt 餵料，非 agent 定義**（subagent 自動注入 AGENTS.md，「空 context」靠不餵意圖文件達成）。**由風險 profile 觸發（邊界變更即分離），不按檔案數或 effort 切換**（舊「≥3 files 才 dual」門檻廢除——可觀察變更語義決定）。**findings 合併規則（單一源＝[workflow-review-pattern](../_common/workflow-review-pattern.md)「findings 去重與復用判準」）**：同位置**且同一 claim** 才合併；**矛盾不裁決** —— 合併端自行裁決 = 球員兼裁判，標 `conflict` 欄（兩方觀點並列）交 Arbiter 裁決層，不以投票或「先回者」裁決。多樣性 > 數量：絕不 spawn 第二個同 context 的 fresh 腿（共享盲點，邊際覆蓋 ≈0，同點 5 原則）。

7. **獨立性階梯（A 軸）：同家族 fresh-context spawn → 跨家族第二意見 → 人類 viewport**（spawn 為預設路徑；manual new session 非獨立性層級——同家族新 session 買不到額外獨立性、不構成升級軸；跨 context transport 需求由持久化鏈承接，見下）:
   - **spawn**（命令內、即時、fresh 獨立 context）—— 預設路徑；fresh reviewer 抓 **anchoring／局部 reasoning failure**（writer 意圖假設、作者 rationalize）
   - **跨家族第二意見**（`kind=different_provider_family`，經 delegate-bridge `--family muse|codex`）—— **systematic bias 的升級軸**：同家族 reviewer（spawn 或 manual new session 皆然）共享家族偏誤，quorum 對共同盲點無效；跨家族抓家族共享盲點。**跨家族非萬能**——不同家族仍可能共享普遍弱項，終極獨立性是人類 viewport（層 3）
   - **單家族顯性降級**：無 alternate family 可用（或額度撞牆）→ `explicit_same_family_degradation` 顯性降級＋記錄（詞彙與欄位見 [agent-review-cycle](../_common/agent-review-cycle.md) independence 欄），或依點 8 記 **no-candidate** 入既有帳本（規劃期＝EP Review 節；實作期＝`.review/<branch>.md`）；**user 明示跨家族＝required，缺場 fail loud**（禁靜默同家族替代）
   - **manual new session＝窄義 escape clause（meta-review 對照組）**：僅當 **reviewer orchestration 本身被審查**（懷疑審查機制自身）或 **spawn isolation 不可信**（spawn 基建被污染）時，作 escape/control mechanism——**非常設獨立性層級、非高風險常設補審**
   - **持久化鏈（durability 基建——與 session 邊界脫鉤）**：`review` 寫 finding → `judge-review` 寫決策（✅ / ❌ / ⚠️）→ apply（主 agent / impl LLM 改）→ `followup-review` 讀持久化逐項驗收（verified / closed / open）——persistence 串起每步、不靠對話記憶（防 compact／context 死亡；跨 context 接續與跨家族 findings 貼回消費同一鏈）。findings 交接格式見 [workflow-review-pattern](../_common/workflow-review-pattern.md) Finding Record。
   - **spawn prompt 餵料衛生（高風險 review）**：fresh 腿**最小餵料**——只餵 diff／source，**禁塞 implementer 解讀與 dispatcher 自身結論摘要**（退化 dispatcher 污染面：dispatcher 把判讀塞進 fresh prompt＝fresh 腿被錨定，獨立性假象）；意圖材料只進 intent 腿（餵料差異見點 6）

8. **no-candidate＝顯性 pending，入既有帳本**：缺合格 candidate 時由該 workflow 編排者在**既有帳本**記 open 阻擋項（規劃期＝EP Review 節；實作期＝`.review/<branch>.md`），欄位：scope/profile、原因、owner、DispatchTrace、下次查 availability 的重查條件。完成報告與 post-build triage 必列出；有已授權排程才排 re-arm，否則保留明確接續動作，**不暗建 automation**。再次 dispatch 前先查有無活 job——**不把無候選和 worker timeout 混同**；不以主模型裸自審取代缺口的獨立性（本條與 SM-13 對應；「缺 candidate 顯性 pending」不可被省配置跳過）。

### spawn prompt 工具紀律（review agent 通用）

spawn review agent 時，prompt 內的工具使用紀律（源方法論「token 紀律」的**限縮吸收**——原版「All tools are functional and will work without error」宣稱與本 repo 的 degraded contract 衝突，不吸收該宣稱）：

- **不做無目的 capability probe**：每個 tool call 有明確證據目的（查什麼、佐證哪條 finding／claim）
- **工具實際失敗走既有 `[WARN]`＋fallback 路徑**（degraded contract）——**不把「工具皆可用」當 runtime fact** 寫進 prompt，也不要求 agent 先測試工具可用性
- **CR 接線查證段（硬性必含；本段＝單一源，各審查範本引用此處、不重抄命令；trigger-based——cr-audit R8，2026-09-10 起「每 callable callers 一次」降觸發面）**：diff 含 callable 新增/修改且**命中觸發面**——public API/介面變更、rename/delete、跨模組、negative claim（唯一 caller／零消費者／不影響 X）——spawn prompt 必含接線查證指令：registry agents（code-reviewer 族，MCP 白名單）寫「對觸發面 callable 跑 MCP `callers`（帶 `repo_root`）；跨模組變更加 `impact_radius`」；generic／Explore（無白名單）寫 CLI 形態「`code-reality scip_refs <sym> --callers --repo <repo-root>`；跨模組加 `code-reality graph_query impact_radius --repo <repo-root> --files <絕對路徑>`」。私有/內部小改不逐 callable 必跑（符號名全域唯一時 rg 等效）；**negative verdict（零消費者/唯一 caller/可刪）永遠不可用 rg 宣稱**。**callers 為空是嫌疑不是乾淨**——prompt 同時要求互補腿 `rg` 字串引用（anti-over-reliance 見 [cr-query](../cr-query/SKILL.md)）；engine 缺場 → prompt 內建 `[WARN]`＋rg fallback（cr-query GATE，不靜默降級）。diff 無 callable 變更或未命中觸發面 → 跳過並要求 findings summary 註明「CR 接線查證 N/A（無觸發面 callable）」
  > 為什麼在 spawn prompt 層不在 agent 定義層：實測（2026-09-04～06）registry 定義檔已寫 MCP-first 指引，spawn prompt 未明示時 reviewer 幾乎不觸發（rg-only）；spawn prompt 明示 CR 步驟的 agent（cr-research）則穩定重度使用——**prompt 明示是唯一被實證的觸發形態**
- **Finding 驗證式段（硬性必含；欄位定義單一源＝[workflow-review-pattern](../_common/workflow-review-pattern.md)，此處不重定義）**：spawn prompt 必含「Important+ 每條 finding 附驗證式（可機械複驗的 rg 命令／pytest case——judge 裁決與 followup 驗收共用同一驗證基準）」——無驗證式的 finding 不可直接進 judge 鏈

> **quorum／verify node 配置單一源**：verify 階段的分級（lite 錨點批次 vs Critical 3-verifier quorum）與 compliance/judgment 分流在 [workflow-review-pattern](../_common/workflow-review-pattern.md)「兩階段模式」（Workflow 模式）與 [code-review](../code-review/SKILL.md)「B. Agent 載體」錨點驗證——本 skill 無 quorum 配置節，只有「quorum 對共同盲點無效」原則（見 [acceptance-evidence](../../rules/acceptance-evidence.md) A/B 軸）。

---

## 與各 review 命令的關係

各命令是薄 adapter，引用本 skill 取通用邏輯，自帶 profile（維度）+ 產出動作：

| 命令 | 標的 | profile（維度）來源 | 產出動作 |
|------|------|-------------------|---------|
| [ep-review](../ep-review/SKILL.md) | EP | 自訂（架構 + 完整性 + 場景 + 兜底拆解） | 回寫 EP |
| [code-review](../code-review/SKILL.md) | git diff | [code-quality profile](code-quality-profile.md) 六軸 | findings + commit message |
| [audit-test](../audit-test/SKILL.md) | test files | 自訂六角度 | 偵測報告 + 健康度（read-only） |
| execution-plan EP Review / build Agent Review | EP / code | 各自 profile | 回寫 EP / apply |

**模式使用**（審查模式判定規則見上「審查模式判定規則」段；此處說明各命令實際用哪些）：
- **code-review**：兩模式（Workflow / Agent Tool）— 可選審查，**force 獨立**（無 Main LLM 自審例外；實證：獨立 agent 抓自審盲點）
- **ep-review / execution-plan EP Review / build Agent Review**：總用獨立 agent（Workflow / Agent Tool），**刻意不走 Main LLM** —— 內建流程的強制品質閘門（Writer/Reviewer 分離）
- **audit-test**：不經模式判定（read-only 單一 agent 偵測，不做平行審查）

維度知識（架構視角/機械）依賴 arch-thinking，非本 skill 包含。

> **`/smell-detector` baseline mode（非 review 命令家族，但複用本 skill 的 severity/confidence 框架標其 §zoom findings）**：baseline per-directory sweep，產 `codebase-review/<dir>/` 4 檔；**非** change-driven（不審 diff、不 spawn review agents）→ **不適用本段執行預設**（force 獨立/風險 profile 配置/3-perspective 是 change review 的）；自有 baseline 流程（廣到精細 + 受眾分離，見 [smell-detector baseline](../smell-detector/baseline.md)）。
