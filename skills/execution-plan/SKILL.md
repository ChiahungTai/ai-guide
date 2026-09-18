---
name: execution-plan

description: "為 full tier（架構/跨模組/🔴高風險/新 boundary）變更規劃 standalone EP 時載入——段落式實作計畫書生成器，自足生成 Self-Contained Segments（含段落 0 全域研究 + UC盤點）。/execution-plan \"任務描述\" [PROMPT檔案]"
when_to_use: "Use when a feature or refactor spans 3+ files, needs parallel agent execution, or scope is unclear. Skip for single-file changes, bug fixes, or straightforward tweaks unless high-risk. Skip if the change is cross-file but introduces no new architecture/boundary decision — use a card Planning Contract instead（見流程規模分級節）"
argument-hint: "<實作任務描述> [可選：PROMPT檔案路徑]"
---

# /execution-plan — 段落式實作計畫書生成器

EP 自足生成段落式實作計畫書（`/spec` 為純輔助需求釐清，有則引用其 UC/SM；無則 EP 自產）。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [agent-workflow](../agent-workflow/SKILL.md) — 並發控制、模型偵測、Agent spawn 規範；EP review／段落 0 研究的 dispatch 形態查其「全生命週期 execution contract（消費側）」

## WorkUnitContract rows（本 workflow 持有——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（WorkUnitContract schema／Role→authority allow-list／resolver precedence 七步）——本表只填值，不複寫 schema；candidate（model identity × binding × effective effort）由 resolver 對 [catalog](../model-routing/catalog.toml) qualification records 硬過濾解析，本檔不材料化 model 值。無合格 candidate＝顯性 no-candidate／escalation，禁降 hard requirement。

| work unit | Role | authority | judgment_floor | qualifications | 說明 |
|---|---|---|---|---|---|
| 段落 0 證據收集（spec 挖掘／rg／LSP／CR 查詢等 evidence legs） | Verifier | evidence artifact（無 disposition/apply） | execution | evidence_retrieval | 產出＝file:line 錨點＋逐字引用；面對「直接裁決/修改」壓力仍不越權 |
| 段落 0 全域綜合（研究摘要／風險假設／callstack 盤點） | Planner | plan | decision | ep_synthesis | 主 session 直做 |
| UC 盤點／Invariant 設計／Scenario Matrix／段落劃分／EP synthesis | Planner | plan／EP synthesis（無 apply） | decision | ep_synthesis | 判斷密集段，主 session 直做 |
| EP Review Reviewer legs | Reviewer | findings（無 disposition/apply） | execution（預設；高保護面／跨邊界語義面升 decision） | review_findings | 執行形態照 [review-engine](../review-engine/SKILL.md)「review 執行預設」 |
| EP Review finding 裁決（EP Review Cycle 的 judge 步） | Arbiter | final disposition | decision | adjudication | seat 非 decision-qualified 時外派；無 candidate 禁 self-downgrade |

**單次呼叫原則**：user 只呼叫一次 `/execution-plan`——evidence 腿 execution、decision 腿 decision 由 resolver 依本表分流，user 中途不手選 model；user 當弧指示（ArcOverride）只約束合格候選排序，不能降低 contract。

---

## 核心概念：Self-Contained Segment

每個段落都是**完全獨立的功能單元**，AI 只需讀取該段落就能完成實作。

特徵：Context 獨立 / 功能完整 / 驗證自足 / 執行獨立

---

## EP 類型（ep_type：blueprint / implementation）

EP 分兩類，由任務規模決定：

| ep_type | 適用 | 結構 | build 行為 |
|---------|------|------|-----------|
| **implementation**（預設） | full tier 變更（寫 EP 前先過下方流程規模分級） | 完整段落（Context + 要點 + Pseudo Code + 驗證策略 + Scenario Matrix） | 正常逐段 /implement |
| **blueprint**（綱要 EP） | **≥ 5 段都是 full tier 變更**（每段本身需完整 EP 規劃深度，單一 EP 裝不下） | 段落是藍圖層級（描述要做什麼 + 依賴 + 吸收範圍）+ 每段標「→ 衍生子 EP（路徑）」；**不含可實作 Pseudo Code** | **不直接 /implement** — 提示逐段衍生子 EP（見 `/implement` 階段 0 ep_type 偵測） |

**欄位格式**（結構化，與 `parent` 一致 — `/implement` 機械掃描欄位非語義字眼）：EP 標頭標 `> **ep_type**: blueprint` 或 `> **ep_type**: implementation`（預設 implementation，可不標）。blueprint EP 必標；implementation EP 若描述到 blueprint 概念也標（避免語義掃描自指誤判）。

**衍生機制**：blueprint EP 每段 → 衍生 implementation 子 EP（標 `parent: <master EP 路徑>` + 繼承該段 Context/依賴/吸收範圍）。子 EP 是完整 implementation EP，可獨立 /implement。

**觸發條件**（避免過度工程）：任務含 ≥ 5 段都是[full tier 變更](../../ai-development-guide.md)（規劃載體分級見 ai-development-guide 規模段）→ blueprint；否則 implementation。視複雜度調整 — 小型任務硬拆成 blueprint 是過度工程。

## 流程規模分級（規劃載體分級 — 與 ep_type 正交）

ep_type（implementation/blueprint）是「**寫哪種 EP**」；本段是「**規劃載體選哪種**」（規模維度，與 docs mode 的 product-type 維度正交）：

| 規模 | 判準 | 規劃載體 |
|------|------|------|
| **simple** | 單檔 bug fix、小 tweak、🟢 低風險 | **不寫 EP** — card AC/scope，直接 TDD + 驗證（`/implement` 裸任務或直接實作）；對齊 [ai-development-guide](../../ai-development-guide.md)「小 bug/doc 免 UC」 |
| **standard** | 跨檔 feature/refactor、🟡 中風險、**無新 architecture/boundary 決策** | **card Planning Contract**（不寫 standalone EP）— 卡 plan 段六欄結構化規劃，見下方小節；執行＝`/implement` contract 分支（六欄齊備代 accepted-EP 檢查） |
| **full** | 架構、跨模組、🔴 高風險、**新 boundary**（state ownership／public contract／跨 context invariant／控制面 authority） | **standalone EP** + 完整流程（`/spec`（純輔助·需求釐清）→ EP → `/ep-validate` → review → `/implement` → judge） |
| **parent-EP bounded child** | accepted EP 已定案上游架構決策，本卡只實作其中 bounded 一段 | **引用 parent EP**（`parent: <ep 路徑>`＋段錨）＋ card Planning Contract——繼承已決策，不重寫完整子 EP |

> 評估順序＝simple→standard→full，依序命中即止；architecture／boundary 判準命中即 full，優先於『跨檔歸 standard』。

> blueprint 衍生子 EP（上行〔ep_type 節〕）與 parent-EP bounded child（本表第四列）是兩個機制：前者＝EP 底下再開 EP（綱要層），後者＝EP 底下開卡（卡層實作）。用後者的判準是 decision-ownership：本卡所需的 boundary／architecture 決策**全部**已由 parent EP 定案且可逐項 anchor；任一決策 parent 未定案→不是 bounded child，走 full（amendment／子 EP）。

### card Planning Contract（standard／parent-EP child 的規劃載體）

standard／parent-EP bounded child 不寫 standalone EP，規劃住卡 plan 段六欄，**缺一＝未規劃**：

1. **Baseline**：現況＋錨點 file:line
2. **已決策**（勿重辯）：parent-EP child 另列 inherited decisions 附 parent EP 錨點。每條 boundary／architecture 決策必須帶 provenance anchor——parent EP 錨點、既有檔案 file:line、或先前已結案卡；**無 anchor＝新決策**→本卡不是 standard，contract 成立前即 promotion 至 full
3. **Scope**：動／不動檔案
4. **Scenarios**：行為情境，含邊界／fail 情境
5. **Integration**：下游消費者／整合點
6. **驗證式**：AC 機械可判——命令＋預期結果；驗證式＝AC 的規劃態——開工承諾時結晶為卡 AC 欄，卡 AC 欄是唯一驗收源

standard 用 Planning Contract 跳過的是 EP 儀式（段落 pseudo-code、EP Review Cycle、report shell），不是跳過規劃。parent-EP bounded child 的 inherited decisions 引用 parent EP 錨點即可，禁整段抄錄 parent EP。

### Promotion ladder（升級觸發）

contract 直行中發現新 **architecture** 決策（新 module 責任／依賴方向）**或**新 boundary 決策（state ownership／public contract／跨 context invariant／控制面 authority）——與 full tier 判準同一列舉 → 停止 contract 直行 → 升 EP amendment 或子 EP（full tier 流程）。判準：該決策是否超出卡前已 anchor 決策範圍。

> **防濫用**：simple「不寫 EP」是跳過**規劃文檔**，非跳過品質 — 仍須 TDD + 驗證。判準機械化（檔案數 + 跨模組 + 風險等級）；**不確定歸 standard，勿把中型降級 simple**。standard 的 Planning Contract 同理——跳過的是 EP 儀式，六欄缺一＝未規劃，勿把 standard 降級 simple。
>
> **silent-corruption 前置掃描**（判 simple 前必跑——多數 simple 修復走裸任務直接實作、不載 execution-plan，掃描掛 EP 護不到主要入口，guide always-on 面同步掛）：對照 §1b 觸發條件（會計總量／風控 sizing／共用 domain service／silent-corruption path 如單位邊界／除權息／時區）——命中 → 升 standard（優先）或 simple＋輕量 invariant 聲明（受影響 invariant＋驗證式，3 行內）。

> **結構性修復非 simple**（simple 邊界的機械訊號，補「🟢 低風險」誤判）：修復碰觸以下任一 → 即使單檔也歸 standard/full，至少帶 [arch-thinking](../arch-thinking/SKILL.md) 結構盤點（補償邏輯 + 跨 context 消費者）：
> - 被 ≥2 個 context 消費的 domain service / 共用層（改語意 = 強迫所有消費者妥協）
> - 會計總量計算（available / equity / proceeds / total / PnL）
> - 風控、sizing、決策路徑（修錯 = 單向門，非「調參」可回）
>
> 這類修復 ripple 打到下游行為，TDD 綠 ≠ 結構正確（真實歷史案例：「修漏算 proceeds 的 compute」被判 simple 直接 TDD，沒拆補丁 → double-count → 風控失效；見 [arch-thinking](../arch-thinking/SKILL.md) 補償邏輯盤點）。觸發條件與 §1b Invariant Impact 共用（同條件不兩處各表——invariant 定義見 §1b；scope 決策在此）。

---

## 🔴 UC 盤點（full tier 變更必填，寫在 Scenario Matrix 之前）

> **核心原則**：UC-Driven Development 要求模組 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities + backlog board 卡（`backlog/`，Backlog.md——機制單一源見 [kanban-board](../kanban-board/SKILL.md)）是開發的**起點**，不是段落的附屬品。EP 必須在一開始就盤點 UC，後續段落才能引用。

**何時需要**：full tier 變更必填；simple 變更（bug fix、文檔）跳過。

**執行步驟**（生成 EP 時的強制前置動作）：

1. **掃描相關模組 instruction 檔 Capabilities（AGENTS.md 為主，CLAUDE.md legacy）+ backlog 卡**：`rg` 搜尋受影響 library 模組目錄的 AGENTS.md（legacy 單檔模組：CLAUDE.md）Capabilities 表格 + `backlog task list --plain`（有 `backlog/` 時），列出與本次變更相關的既有 UC
2. **判定 UC 變更類型**：

| 變更類型 | 說明 | EP 中的動作 |
|---------|------|------------|
| 📋 新增 UC | 本次變更引入新能力 | 在此區段定義新 UC（能力描述、實作路徑），後續段落引用 |
| 更新既有 UC | 既有 UC 的能力擴展或行為改變 | 標記能力描述 + 改變摘要，後續段落引用 |
| 無影響 | 既有 UC 不受影響 | 標記「無 UC 變更」即可 |

3. **掃描 backlog 卡關聯 + 自動建卡**（repo 有 `backlog/` 時）：
   - `backlog task list --plain` 列既有卡，找出本次 EP 對應的卡（能力描述＋名稱）；EP 可能對應多張，全部列出
   - **去重前置**（中）：建卡前 `backlog search <關鍵詞>` + 查 `backlog/drafts/`（未承諾草稿歸宿；與同域 `open-items.md`，例：mosaic 側 `marking/open-items.md`）待處理段，命中則復用/連結既有指針，不重複承諾
   - **自動建卡**（EP 產出後執行）：
     1. 收集 EP 中所有「新增 UC」（UC 盤點 → 新增 UC 表格中的 📋 項目）
     2. 對照既有卡，篩出**缺少卡的能力**（已含去重命中 → 跳過）
     3. 逐能力 `backlog task create "<標題>" -l <labels> -d "<目標一句人話>"` → `backlog task edit <id> --plan "<工單 spec：baseline／已決策勿重辯／範圍>"`（desc 人話、spec 住 Plan——spec gate 三必有，見 [kanban-board](../kanban-board/SKILL.md)「欄位分工」）；為 EP 整體另建一張追蹤卡（命令合約與**開工雙 ref 規則**見 [kanban-board](../kanban-board/SKILL.md)——卡 references 只掛 repo 相對路徑（EP 必備，有殼並列 shell 路徑），不掛 http URL）
     - Plan「已決策」段可含風險面屬性標註（「寫入契約首改」「跨文件交叉推導」「無保護面新能力」）——後續 handoff「建議執行 tier」的輸入
     4. **建卡（批次）即 commit**：`git add backlog/ && git commit -m "chore(backlog): <卡id…>"`——跨 WT id 防撞靠卡及時進 branch ref；此形態 user 已裁定免逐次確認（例外條款見 [outward-action-consent](../../rules/outward-action-consent.md)「Commit 專屬段」；命令合約見 [kanban-board](../kanban-board/SKILL.md)）
   - 無 `backlog/` 目錄時：提醒 user `backlog init --agent-instructions none`（**禁**再教 `mkdir .kanban/`——`.kanban/` 舊制已退役；`--agent-instructions none` 避免注入與本 repo AGENTS.md 治理衝突的 CRITICAL_INSTRUCTION 區塊）；repo 不採 board 制 → 卡片動作整項跳過

**同主題 memory 條目盤點**（步驟 3 外的獨立子步——不受步驟 3「repo 有 `backlog/` 時」分支限制，memory 池與 backlog 制正交）：`rg` 主題詞掃本專案 memory 池（desc 投影＋條目檔；無池 → 標跳過），命中即列入 EP「UC 盤點」輸出「同主題 memory 條目（結案蒸餾範圍）」行；含弧流水形態（過期狀態詞）者標記。本弧結案蒸餾（[kanban-board](../kanban-board/SKILL.md)弧結案蒸餾第三動）範圍含登記條目——存量債隨弧消化，不等波段。清單級（條目名＋一行形態判讀），不做內容審（那是 [memory-audit](../memory-audit/SKILL.md)層 2 的事）。

4. **掃描 SYSTEM-MAP.md 關聯**（如果存在）：
   - 搜尋專案根目錄的 `SYSTEM-MAP.md`
   - 找出本次 EP 影響的功能區塊及其生命週期狀態
   - 在 EP 中標注「本次 EP 影響 SYSTEM-MAP 中的功能：X（狀態），Y（狀態）」

5. **輸出格式**（放在 EP 的 top-level，段落之前）：

```markdown
## UC 盤點

### Backlog 關聯
- 列出相關 Backlog 卡片（能力描述 + 名稱）
- 自動建卡結果：新建 N 張卡片（列出能力描述 + 檔名）或「所有 UC 已有卡片」

### SYSTEM-MAP 影響
- [SYSTEM-MAP.md 存在時] 列出受影響功能 + 當前生命週期狀態（如「每日收盤 Pipeline 🏃」「Paper Trading Terminal ⚠️」）
- [SYSTEM-MAP.md 不存在時] 提醒用戶：目前無 SYSTEM-MAP.md，建議建立
- 無對應功能時寫「無」

### 掃描範圍
- [列出掃描的 instruction 檔 Capabilities 路徑 + backlog 卡（`backlog task list --plain` 輸出）]

### 同主題 memory 條目（結案蒸餾範圍）
- [命中條目名＋一行形態判讀；零命中寫「零命中」；無池寫「無 memory 池，跳過」]

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| 每日增量 K 線更新 | ✅ | instruction 檔 Capabilities | 更新 | 擴展消費場景 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| [能力描述] | 📋 | [library 模組相對路徑] |
```

6. **段落引用**：每個段落的 Context 必須引用此處盤點的能力描述（如「實作 [能力描述]」「更新 [能力描述]」）

**為什麼放這裡**：UC 放在段落深處時，AI 傾向跳過或事後補寫。強制在 EP 最前面盤點，確保 UC 在段落設計之前就存在，段落才能正確引用。

---

## Scenario Matrix（full tier 變更必填）

> **核心原則**：規劃時強制思考「使用者會遇到哪些情境」，避免實作完成才發現漏掉錯誤路徑或邊界案例。矩陣產出後散到 UC 的「消費場景」欄位。

**何時需要**：full tier 變更必填；simple 變更（bug fix、文檔）跳過。

**格式**（放在 UC 盤點之後、段落劃分原則之前，作為 top-level 區段）：

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | [使用者意圖] | [CLI flag / 事件 / 錯誤操作] | [系統該怎麼反應] | [恢復點 / 無] | [能力描述 或「—」] |

**必須涵蓋的場景類型**：
- Happy path（正常使用）
- 錯誤操作（缺參數、缺前置條件、assert fail 路徑）
- 邊界案例（空資料、跨日、回補多天）
- 效能期待差異（秒級、幾十秒、慢、線性放大）

**欄位含義**：場景＝使用者意圖一句話（SM-N 編號）；觸發＝引發此情境的具體輸入/事件/錯誤操作；預期行為＝系統該怎麼反應（可觀察結果，非實作細節）；Checkpoint＝此情境的恢復點或驗證點（無則標「無」）；對應能力＝對應 UC 盤點的能力描述（無則「—」）。

**散到 UC**：實作完成後，`/implement` 階段 5a 從矩陣提煉自包含描述寫入對應 UC 的「消費場景」欄位（不引用 EP/SM 編號，因為 EP 可能歸檔或刪除）。

---

## 測試規劃段（full tier 變更且 EP 含可執行碼必填——top-level，實作段落之前）

> **核心原則（v3.1 測試契約）**：契約層先——TC（測試契約）在任何人寫實作碼前凍結（文件順序＝時間順序，本段放 Scenario Matrix 之後、段落 0 之前）。oracle 獨立性由「EP 作者↔實作者本來就跨家族」兌現；same-family 時此前提裂縫——見下方 same-family precondition（本處是 producer 側記錄，consumer 側 gate 在 [implement](../implement/SKILL.md)）。

**何時需要**：full tier 變更且 EP 含可執行碼；純文檔 EP 跳過（標記理由）。

**TC 格式**（每條 TC 的欄位）：

| 欄位 | 內容 | 約束 |
|------|------|------|
| claim | 驗證什麼行為主張 | 一句可否證的主張 |
| Given-When | 前置狀態與觸發 | 具體輸入/事件 |
| oracle | 期望值與判準 | **predicate-ID 拆分**——每個可獨立斷言的 predicate 一個 ID，禁複合斷言 |
| oracle_source | oracle 值的獨立來源 | 規格、領域恆等式、歷史數據；**禁指向待測實作**（圓形依賴） |
| evidence class | 證據等級 | L1-L6 對應（[acceptance-evidence](../../rules/acceptance-evidence.md)） |
| uncovered | 明示不覆蓋面 | 無則寫「無」 |

**oracle authority 分級**：TC 的 oracle_source 權威四級（S/H/I/N）正典見 [acceptance-evidence](../../rules/acceptance-evidence.md)「oracle authority 分級」（I/N 禁 autonomous 補強授權——TC 供下游補強消費時須知）。

**凍結語義**：TC 在實作段落設計前凍結；凍結後 EP 其他段落可改、TC baseline 不動；改 TC 走 amendment。

**amendment 附錄**（EP 內記錄 TC 變更判決的附錄區）：每筆記 old/new oracle＋reason＋independent evidence＋authority。**authority 四分**：invariant／reference truth 可證偽→judge；新 integration evidence→judge；user intent／product policy→人類；來源矛盾→人類。「實作現況」永遠不是證據。deviation log（前線提案，段落內記錄）與 amendment（判決，附錄記錄）兩份分離。

**pre-RED challenge**（高風險/P0 觸發）：跨家族 advisory、fresh context、blind derive→reveal（先自行推 oracle 再比對，防錨定）＋completeness（抓漏場景）；必產 falsifiable 探針。觸發判準＝流程規模分級 **full** 檔＋§1b silent-corruption path 命中。challenge findings→absorb 回 TC 或走 amendment，完畢才放行 RED。

**same-family precondition（producer 側）**：EP 整合策略記 `author_family: <family>` **metadata 欄位**（非 prose）——消費端 dispatch gate 在 [implement](../implement/SKILL.md)（相同家族時 RED 前須 challenge completed 或 degraded 明示記錄）。

**下游對帳（引用不重複定義）**：本段 TC 格式是 [audit-test 域 2 TC 契約對帳](../audit-test/SKILL.md)（軸A 機械對帳）、[code-review 軸B 六項](../code-review/SKILL.md)（架構面，定義源 review-engine 的 code-quality profile）、[fix-test mutation authority gate](../fix-test/SKILL.md) 的共同引用源。

---

## 段落 0：全域研究（所有段落的研究前提）

> **核心原則**：EP 自足——在設計段落之前，先做一次全域 codebase 研究，盤點可複用基礎設施 + 識別風險假設。這取代了舊 `/spec` 的全域研究職責（spec 現為純需求釐清）。

**執行**：spawn 全域研究 agent——ZCode registry [`cr-research`](../../agents/AGENTS.md)（掛 CR MCP 白名單；decision／global-research——AIR-76 v3.1 裁升，非 lite；CR 查詢 in-path）；registry 缺場（Claude 端）→ Explore（繼承主 session 模型——全域研究 fallback 形態，見 [model-routing](../../rules/model-routing.md)）＋spawn prompt 帶下方 CLI 清單。深度掃描相關模組：

1. **可複用基礎設施盤點**：搜尋需求涉及的模組 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities + LSP `workspaceSymbol` 搜尋相關 class/function，找出可複用的 utilities、base classes、protocols
2. **依賴分析**：LSP `goToDefinition` / `findReferences` 追蹤 import 鏈和介面關係，rg 補充非程式碼引用。**code-reality（index 在場）——cr-research 的 CR MCP 工具（callers／closure／refs／impact_radius）in-path 執行**；Explore fallback 形態＝CLI 清單寫進 spawn prompt（分層事實見 [cr-query](../cr-query/SKILL.md)；工具用法真相源 [code-reality](../code-reality/SKILL.md)；GATE 見 cr-query）：
   - 宣稱被整合/觸發的既有符號 → `code-reality scip_refs <sym> --callers --repo <repo>`；追 transitive 鏈 → 同命令 `--closure --depth 2`
   - 修改檔案的 ripple / 影響範圍 → `code-reality graph_query impact_radius --repo <repo> --files <絕對路徑>`（相對路徑靜默回 `changed_nodes=[]`，非錯誤）
   - 刪碼/退役場景 → `code-reality hub_refs <sym> --hazard --repo <repo>`（動態派發盲區安全網）
   - **字串鍵互補腿**：觸碰欄位名 / config key 類 literal → `rg "<literal>"` 掃非符號消費者（測試常以字串鍵驅動 meta 比對——符號查詢與 CR 圖皆不可見）
   - **誠實界線**：CR 查詢是 ripple 宣稱的必要證據、非充分證據——字串鍵/meta 耦合、registry 動態派發、runtime 行為是 CR 盲區（清單見 cr-query anti-over-reliance），靠上列互補腿覆蓋；**「CR 全綠」≠ 無 ripple**
   - **投影圖（僅整合器型/跨模組 EP；觸發條件與 scope 升級同套）**：全域研究後寫 projection plan——EP 同層 `projection/plan.toml`＋假想碼放同層 `sources/`（格式真相源 `code-reality project --help`）；**plan `[meta]` 的 project/version 必須等於目標 repo 的 pyproject identity**（symbol ID 是 join 鍵，不符則投影邊全部靜默不歸因——fail-loud 驗證會擋）→ 跑 `code-reality project --repo <repo> --plan <plan.toml>` → 報告的 graft surface（規劃新符號的投影 callers 反向鏈）與 claims 判定**帶 `[projected]` 標籤**寫進「依賴關係」產出（與本組 CLI 查詢並列）；`[projected]`＝宣告非證據（洗衣陷阱防護，判讀語義見 [cr-query](../cr-query/SKILL.md)）
3. **類似實作**：LSP `workspaceSymbol` 搜尋相似名稱的 class/function，rg 補充搜尋字串和註解
4. **風險假設識別**：列出高風險技術假設（外部 API、SDK 行為、架構假設），標注由哪個段落的驗證策略 POC 驗證（吸收舊 `/spec` Phase 3 前期 POC 職責）
   - **致命先驗**：標注為「致命」等級的假設（假設錯了整個 EP 要重寫，等級定義見 [/ep-validate](../ep-validate/SKILL.md)）—— 先跑 `poc/poc_*.py` 驗證可行性再繼續設計段落，避免寫完整 EP 才發現方向死掉；高等級與中等級保留在各段落驗證策略
   - **框架行為 bug**：渲染／race／client-server 狀態同步類根因假設常錯——規劃層禁寫死修法，根因標『推測，需 L4/POC 驗證』、修法段標『待確認根因』（純邏輯 bug 才可規劃層寫死）
   - **kill criteria（AIR-131）**：全 EP 挑 **1-3 個** load-bearing assumptions（只列真的會讓方案死亡的；其餘高風險假設留在本風險清單），各配四欄可否證格式寫進 EP——**Assumption**（必須為真的前提）／**Probe**（最便宜的判別性證偽方法——cost-to-disproof 最小化）／**Kill observation**（看到哪個客觀結果就停，預先承諾的停止閾值）／**Action**（預先決定的 kill／pivot／research arc）。不可否證句式不合格——判準：無可觀察的客觀結果、無預先承諾的停止閾值，任何結果都能事後解釋（反例：「實作太複雜就重新評估」）；合格例：「若 target harness 無法在 real runtime 提供所需 interception point、且唯一替代需 second authoritative state，停止此 approach」。kill criteria 必須在投入大量 implementation 前寫，否則變事後合理化

**產出研究摘要**（放在 EP top-level，段落之前）：
- 可複用基礎設施清單（附 `ClassName`，路徑選用）
- 依賴關係和關鍵約束——每個下游/ripple 宣稱附工具輸出引用（scip_refs 首行 `[SRC]`；graph_query 輸出無 `[SRC]` 行、附完整命令列＋repo root；投影查詢輸出帶 `[projected]` 標籤；或 LSP 查證——不接受純讀碼推斷）
- **negative 宣稱結構化（cr-audit R1）**：研究宣稱含「唯一 caller／零消費者／可刪／不影響 X」類 negative verdict → 以 claim 四欄記錄（type／symbol／evidence／verdict）＋查證走 CR `callers` 實測——**negative verdict 永遠不可用 rg 單腿宣稱**（rg parity 例外只適用 positive lookup；單一源＝[review-engine](../review-engine/SKILL.md)「CR 接線查證段」，judge 裁決端同步此標準）
- 類似功能的既有實作位置
- 風險假設清單（標注等級；致命等級附先驗結果，對應段落驗證策略）；**死路假設嫌疑入列**——宣稱被整合/觸發的既有符號 callers 查詢為空（CR＋LSP 雙空）即列（真實案例：`_lazy_populate` 宣稱被觸發、實際永不執行）
- callstack 菜單積壓（repo 有 `ai-analysis/blueprint/callstack-plan.md` 時）：待生成鏈行——新 EP 常踩在未文檔化功能上；僅列清單，生成＝獨立觸發（blueprint-bootstrap）

> **深度上限**：研究摘要層級（可複用元件清單 + 風險假設），**非 codebase 全景報告**——避免 EP 膨脹。後續段落的「基礎設施盤點」在此基礎上補段落特定細節。

> **研究材料載體（cr-audit R3）**：研究產出超出摘要粒度（structural claims＋查詢＋`[SRC]`＋degraded 標記的完整紀錄）→ 落 EP 同層 `references/research.md`，EP 正文只摘要引用；機械可驗收＝`fd research.md <任務家>` 命中＋rg `[SRC]` 非空。

---

## 段落設計標準

每個段落必須包含：

### 1. Context

- **背景資訊**：基於需求討論（有 `/spec` 則引用其 UC/SM；無則段落自行釐清）
- **需求邊界繼承**：有 `/spec` 時其 Always / Ask First / Never 邊界顯式入段（自包含轉述，不引用編號——段落自足原則）；無 spec 寫「無」
- **UC 引用**：本段落實作的能力描述（如「實作 [能力描述]」）。full 變更必須引用；standard 變更更新既有 UC；simple 變更可不引用
- **依賴關係**：與其他段落的依賴和整合點
- **語義約束**：與其他段落共享的隱含假設（型別定義、命名慣例、架構決策）。無則寫「無」，有則寫「與 S{N} 共享 [具體假設]」
- **基礎設施盤點**：設計 pseudo code 前的必做步驟（讀 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）可複用基礎設施 → LSP `workspaceSymbol` + `rg` 搜尋相關元件 → 列出可複用元件或寫「無」）
- **依賴錨點**：EP 對現有程式碼的雙向錨定 — 每個依賴同時標注定義端與消費端（格式：`symbol` → 定義 `path/def.py:42` / 消費 `path/caller.py:156`）。用 LSP `goToDefinition` 驗證定義端、`findReferences` 驗證消費端。`/implement` 時直接定位雙端，省去搜尋成本。執行前驗證錨點，drift 時先更新 EP
- **技術選型** + **成功標準**

### 1b. Invariant Impact（條件必填 — 觸及 invariant-bearing 模組時）

**觸發**：段落觸及以下任一 invariant-bearing 模組（bug silent-corrupt 全下游者），觸發時本段必填，否則寫「無」：

- **會計總量 / 風控 sizing / 跨 context 共用 domain service** —— 與上方「流程規模分級 → 結構性修復非 simple」重疊（scope 決策與本元素在此共用條件，非本元素獨有）
- **silent-corruption path** —— bug 不 crash 但污染下游資料的路徑（如單位邊界 張↔股、除權息調整、時區）；不屬會計/風控但同樣 invariant-bearing。**各專案 CLAUDE.md 應標記此類 path**（標記 convention 由各專案自訂）

> **為何（補 producer 端，別與既有重複）**：重疊的三類（會計/風控/domain service）已由上方 scope 決策（standard/full）+ [arch-thinking](../arch-thinking/SKILL.md) 補償邏輯盤點覆蓋；但 reviewer 仍缺一份「動到哪些 **domain invariant**」的結構化聲明——段落 0「風險假設識別」是技術未知、補償邏輯是 double-count、依賴錨點是 caller，三者都不等於「cash 守恆 / position single-writer / risk limit 是否被改動」。**silent-corruption path 更可能只觸發本元素、不觸發 scope 升級**（如單檔單位轉換 fix，scope 判 simple 但仍 invariant-bearing）→ 本元素是其唯一**完整**結構化防線（簡單路徑另有輕量 invariant 聲明——見流程規模分級防濫用段；「唯一」指完整形態，非指唯一存在）。reviewer 直接驗證（不必 state reconstruction——審查主要成本是重建影響範圍，非 attention）。

- **受影響 domain invariant**：本段變更動到哪些（如 cash 守恆、position single-writer、risk limit 強制、單位邊界）
- **critical path 觸及**：money path / 跨邊界轉換 / silent-corruption path（見上方觸發定義）
- **驗證對齊**：每個受影響 invariant 對應 §4 驗證策略的哪個 test/assert（producer 自證守住，非留給 reviewer 推）

### 2. 核心實作要點

主要類別、關鍵方法、設計決策、整合方式

### 3. Pseudo Code

類別結構 + 方法實現 + Call Stack + 錯誤處理。檔案結構用樹狀展示（非 mermaid）。空殼 class 用詳細註解標示設計意圖。

### 4. 驗證策略

**前期 POC**（高風險假設可行性驗證，吸收舊 `/spec` Phase 3）：段落 0 全域研究識別的高風險技術假設（外部 API、SDK 行為、從未用過的函式庫），在此段落以 `poc/poc_*.py` 驗證可行性（能不能做）；深度驗證（效能、邊界、壓力）由 `/ep-validate` 於 EP 後執行。**致命等級假設已在段落 0 致命先驗驗證，此處驗證高等級與中等級**。POC 檔頭格式見 [/ep-validate](../ep-validate/SKILL.md)。

**spike evidence budget（AIR-131）**：一個 load-bearing assumption → 一個 disposable spike → 最多 2-3 個判別性 probes（驗證性工作——環境搭建、既有測試回歸——不計入 probe 額度）。三不：**不做 production refactor、不順便把東西做好、不以 wall-clock timebox 計**（AI 對時間不是好的控制單位）。budget 耗盡仍不能證明可行性＝**UNKNOWN——hypothesis/spike 層的合法結果**：顯性裁決（加 probe／升級討論／棄），禁 UNKNOWN 自動滑入 implementation（「都研究這麼多了不如直接做」＝sunk-cost transition）。UNKNOWN 不是弧終態——弧仍須裁決到下述三態之一。

**弧終態（AIR-131）**：DELIVERED／INVALIDATED／SUPERSEDED 三態（弧的 terminal outcomes；UNKNOWN 見上，不在三態內）。**INVALIDATED＝成功終態**（uncertainty retired）——成功條件＝原假設→falsifying evidence→kill decision→可重用 learning→**沒有留下半套 production mechanism**。結案走**既有 Done 結案語義**（`Done`＋final-summary 記 falsifying evidence／kill decision／可重用 learning），不是 archive（archive＝廢棄/方向錯；止損＝不可行被證偽）；追蹤 **cost-to-disproof**：會死的方案死得越來越早＝健康。

POC/demo 設計 + 測試計畫 + 完成檢查 + 整合測試。**測試類型選擇紀律見 [validation-strategy](../validation-strategy/SKILL.md)**（e2e 優先 > 單元隔離 / 交易 replay >>> live / 放 scripts/ / 不重驗 package NT·bokeh·panel）+ 結構視角見 [arch-thinking](../arch-thinking/SKILL.md)。

**測試計畫內容**：描述測試的種類和情境，不寫數量（數字每次修改都過時，對決策無價值）。應包含：
- **測試類型分佈**：單元 / 整合 / E2E / 外部 API mock（選擇紀律見 validation-strategy）
- **關鍵情境覆蓋**：happy path、邊界案例、error handling、冪等性
- **已知未覆蓋的風險**：哪些路徑沒測到、為什麼

**TC 引用（含凍結 TC 的 EP——退化自足）**：各實作段落的驗證策略須引用 TC-ID（＋必要時抄關鍵 predicate）——session 退化 handoff 後新 session 不需回讀 top-level 測試規劃段即可執行 RED（段落自足原則的 TC 延伸）。

---

## 段落劃分原則

依賴圖分析、垂直切片、task sizing 屬 LLM 原生規劃能力，直接規劃（無 external skill 委託）。

EP 專屬約束：
- **語義顯式化**：段落間共享的隱含假設必須顯式標記
- **驗證自足性**：每段有獨立驗證策略

---

## 段落設計檢查清單

- [ ] UC 盤點已完成（full tier 變更：掃描 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities + backlog 卡、列出新增/更新 UC、卡關聯）
- [ ] Backlog 自動建卡已完成（新增 UC 已有對應卡 + EP 整體追蹤卡；建卡已 commit——`chore(backlog)` 顆粒）
- [ ] Scenario Matrix 已填寫（full tier 變更；涵蓋 happy path、錯誤操作、邊界、效能期待差異）
- [ ] 測試規劃段已完成（適用時——full tier 變更且含可執行碼：TC 凍結＋amendment 附錄＋author_family 欄位；純文檔 EP 標記跳過理由）
- [ ] 標題明確且獨立
- [ ] Context 包含所有必要背景
- [ ] UC 引用已標記（引用 UC 盤點區段的能力描述；full 必須，standard 可選）
- [ ] Pseudo Code 具體可執行
- [ ] 驗證策略完整可執行
- [ ] 整合點清晰定義
- [ ] 語義約束已顯式標記
- [ ] 基礎設施盤點已完成
- [ ] 依賴錨點已標記
- [ ] Invariant Impact 已標記（觸及 invariant-bearing 模組時：受影響 domain invariant + critical path + §4 驗證對齊）

---

## docs mode（純文檔/rules 改動）

EP 產物全為 instruction/documentation 檔，或其 static HTML Report Shell（無 executable source 邏輯）時進入 docs mode —— 段落元素裁剪程式碼導向部分，驗證改為文檔與 artifact 驗證。

**觸發判準**：product 變更檔案型別只允許 `.md`，或 `.md`＋static `.html` Report Shell；product scope 出現其他 executable source extension 即退出 docs mode（Python callable 掃描只可作補充證據，不是跨語言 gate）。HTML 內含互動 JS 時，EP 必須保留 browser/DOM runtime 驗證與視覺驗收，不得以 docs mode 跳過行為驗證。

**行為控制面**（語義判準**單一源**——post-build triage 與此同詞，不重定義）：塑造 LLM 行為的 instruction／規範檔——AGENTS.md 家族／rules／skills／agents／commands／hooks／settings／guide（含消費端 repo 同類檔）；路徑清單僅為 hint，是否控制面以語義判（改後 AI 行為是否不同）。控制面變更即使純 `.md` 也走完整審查鏈（code-review docs-mode → judge → followup，見 post-build triage）。任務家內只服務驗收的 verifier 可列為 evidence artifact，不算 product scope，但必須在 EP 顯式列出、實際執行且不得被 production consumer 引用。純 `.py` 搬移（無邏輯改）→ docs mode + 保留 mypy/pytest baseline。

**EP 元素對照**：

| EP 段落元素 | 程式碼 mode | docs mode |
|------------|------------|-----------|
| UC 盤點 | 掃 library Capabilities | 掃「受影響命令/rules 清單」（元專案無 Capabilities 表格）|
| kanban / SYSTEM-MAP | 強制 | 元專案 / 無對應時跳過（正當跳過，標記理由）|
| Context 錨點 | file:line 符號（LSP）| file:line 文檔行號錨點（rg 驗證行號指向預期內容）|
| Scenario Matrix | full tier 必填 | 影響命令行為時仍填，但「觸發/預期行為」改文檔語境（rg 命中/0 殘留），非程式執行結果 |
| 測試規劃段 | TC 凍結＋amendment 附錄＋author_family 欄位 | **跳過**（純文檔 EP 無可執行碼面——標記理由）|
| Pseudo Code | 類別 + Call Stack | **裁剪**（文檔無類別）；以「修改要點」替代 |
| 驗證策略 | POC/demo + 測試 + 整合測試 | 改為文檔驗證（rg 殘留、跨檔一致性、`/consistency`、導航有效性）|
| TDD / mypy / ruff / pytest | 強制 | **跳過**（`/implement` 階段 2 僅「修改 → rg 殘留 → 跨檔一致性 → `/consistency`」）|
| 整合路徑覆蓋 | `rg "<param>="` | **跳過**（或改為跨檔引用一致性 rg）|
| EP Review 維度 | Call Stack / Pattern Alignment | 改為「文檔一致性 + 設計合理性 + 引用 drift + 漏改」|
| 收尾 Capabilities + Kanban | 強制 | 元專案跳過；改為「受影響命令/rules 行為已反映 + `skills/CLAUDE.md` 工作流索引 description 同步」|

docs mode 的 `/implement` 執行分支見 [implement skill](../implement/SKILL.md) 階段 0/2/3。

### ripple 語義反向撈（格式/術語統一類變更）

> docs mode EP 涉及**格式統一、術語改名、共用規範對齊**類變更時，ripple 靠逐檔枚舉會漏（LLM 想不到的檔案就漏）。逐檔枚舉之外補機械掃描，撈「自稱共用」與「定義源」兩類語義線索。

**觸發條件**（僅這類變更，避免過度工程）：EP 目標是統一格式 / 改名 / 對齊共用規範（非純新增、非純論述）。

**語義反向撈**（逐檔枚舉之外補）：
1. **自稱共用規範**：`rg "共用規範|與.*共用"` 撈所有自稱與權威源共用格式的檔頭/段落，逐一致性比對
2. **定義源**（術語改名時）：改名 ripple 必須含**定義該術語的源頭命令**（描述規範者，非僅使用），否則術語從上游再生

**限制**：語義撈降低漏率不消除 —— pattern 會漏同義表述（「遵循 template」「對齋」）、會 near-miss（「機械軸」≠「機械閘門」）。是「機械補人類遺忘」、需人工判讀命中，非 100% 覆蓋。

---

## EP Review Cycle

**Writer/Reviewer 分離**：用獨立 Agent context 審查 EP，避免主 LLM 審查自己的計畫——**獨立計畫 review 不刪**（EP 定稿前的強制品質閘門）。配置單一源＝[review-engine](../review-engine/SKILL.md)「review 執行預設」＋「審查模式判定規則」——**context 配置由風險 profile 推導，本 Cycle 不以主模型/effort 重建 agent 數量判準**（並發容量＝上限非配額，數值歸 [model-routing](../model-routing/SKILL.md)；不因容量有剩回填 agent）。

### Step 1: 風險 profile 判定

依 [review-engine](../review-engine/SKILL.md)「審查模式判定規則」按 EP 觸及的變更語義判定（條件不明採更保護分支）：

- **ordinary**（一般 feature EP）→ **單一獨立 context** 順序覆蓋全部維度（見 Step 2）
- **boundary**（EP 規劃觸及控制面 authority/gate、public API 契約、跨 context invariant、money/risk/security）→ **分離 fresh＋intent**：fresh 腿無錨讀 EP 自身 merits；intent 腿餵 UC 盤點／卡 Plan／受影響模組 instruction 檔；必要專項（架構/兜底）按觸發附加。資格升級（judgment_floor→decision）由上方 WorkUnitContract rows 承接

印出確認：`[EP Review] profile=<ordinary|boundary>, context=<single|fresh+intent>`

### Step 2: 維度覆蓋（F1–F5 全維度，不丟棄）

審查維度（「審 EP profile」：分層依賴 / bounded context / use case 覆蓋 / 場景 / 完整性 / 合規 / 遺漏 / 兜底拆解）定義見 [/ep-review](../ep-review/SKILL.md) 五維度 + 維度映射表 — 本 Cycle 不自帶維度定義，與獨立 `/ep-review` 共用同一 profile（根治內建 vs 獨立 drift）。啟用：所有維度 always——**ordinary 由同一 reviewer 按 top-down 順序覆蓋**（先結構後細部正確性——結構錯了正確性審白費，視角見 [arch-thinking](../arch-thinking/SKILL.md)），省略任一維度＝scope 未覆蓋；**boundary 由分離腿分工覆蓋**，維度合併（多腿間分工手段，不丟棄維度）依並發容量上限推導。

### Step 3: Spawn

依 Step 1 配置 spawn review agent(s)（subagent_type: "Explore"，read-only by design）；boundary 多腿需確定性協調/schema 輸出時用 Workflow 載體（[workflow-review-pattern](../_common/workflow-review-pattern.md)，載體是執行細節非 effort 門檻）。

每個 agent prompt 包含：
- EP 完整內容
- 該維度的檢查項目清單（見 [/ep-review](../ep-review/SKILL.md) 五維度 + 維度映射表）
- 相關檔案路徑（必讀）
- 引用 [review-engine](../review-engine/SKILL.md)（通用：嚴重度/信心水準/審查者自證/LSP 查證/模式判定規則）+ [arch-thinking](../arch-thinking/SKILL.md)（Clean Arch 視角 §一 + 結構機械 §二）+ [code-quality profile](../review-engine/code-quality-profile.md) 方法論
- rules-reminder 規則摘要（Agent 看不到 auto-loaded rules）

> **agents→skills 統一**（#B12 探討）：agent 審查知識（通用審查邏輯、Clean Arch 視角、結構機械能力、方法論）沉 skill 統一引用，agent prompt 只組裝 — 非各命令內嵌審查邏輯。EP review agent 引用 review-engine（通用，含 code-quality profile）+ arch-thinking（視角+機械維度），與 `/code-review`、`/illustrate` 共用同一組 skill（整脊「能力下沉」一致性）。

### 單一 Agent Prompt（ordinary profile）

Spawn Agent（subagent_type: "Explore"），prompt 包含：
- EP 完整內容
- Dry Run 驗證：
  1. **Call Stack 可行性**：pseudo code 每步能否跑通？
  2. **Pattern Alignment（最重要）**：EP 設計假設的 usage pattern 是否與 callers 實際 pattern 一致？
  3. **下游依賴發現**：有沒有 EP 沒提到的 callers？
  4. **邊界條件**：空值、null、缺少欄位等
- Clean Arch 審查（**top-down**：先結構後正確性，引用 [arch-thinking](../arch-thinking/SKILL.md) + [code-quality profile](../review-engine/code-quality-profile.md)）：
  1. **分層依賴**：domain←use case←adapter←infra 依賴向內？有循環？Call Stack 可行？
  2. **bounded context**：不跨域存取 `_private`？邊界清楚？職責單一？
  3. **use case 覆蓋**：消費者要什麼行為？EP 撐得起？UC 完整覆蓋？每段有驗收標準？檔案完整？依賴遺漏？
  4. **兜底路徑驗證**：EP 預見極限（實作落差）+ 語義約束 drift + Rules 合規（命名、code-edit-constraints、元資訊禁止（instruction-writing skill）、instruction 檔更新）+ 遺漏風險（Demo、測試、`__init__.py`、配置、受影響模組）+ 內部一致性 + **兜底假設路徑驗證**（EP 若宣稱「X 段暴露/處理 Y 問題」→ 必須驗證 X 的 code path 真經過 Y，追 call chain 附 path:line；不經過 → 標「未驗證」而非「handled」，Y 須獨立調查）+ **「可觀測 ≠ 已修復」用語**（visible / overlap-fixed / root-cause-fixed 三區分；`handled/exposed` 不得模糊涵蓋 visible 與 fixed — S0=visible、S6=overlap-fixed，root-cause-fixed 是另一件事）
- 相關檔案路徑（必讀）

### 主 LLM — /judge-review

用 Skill tool invoke `judge-review`，傳入**所有 agent 的 review findings**（合併；**指定帳本＝EP review 區段**——規劃期帳本，EP Review Cycle 的決策落點）。評估每項：✅ 採納 / ❌ 不採納 / ⚠️ 需確認。

### 主 LLM — Apply Changes

根據 judge-review 的 ✅ 採納清單修正 EP。**修正必須寫入 EP 段落本身**（加入 EP review 區段表格，格式見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md) Finding Record），不是只記在審查報告裡。build 可能由不同 LLM session 執行，看不到審查報告。**F-1 型 findings（scope／驗收校準）屬決策層變更 → 同步回寫追蹤卡 Plan／AC（見 [kanban-board](../kanban-board/SKILL.md)「卡即 handoff」）。**

**EP Review 完成才產 accepted eligibility**：review ledger 全 terminal（implemented／rejected／verified）＋✅ 修正回寫完成後，EP 才具備 `/implement` accepted-EP predicate 的進場資格——本 Cycle 是該資格的產出點（predicate 消費端見 [implement](../implement/SKILL.md) 階段 0）；ledger 有 open／needs-confirmation ＝ 未 accepted，不得進實作。

### 定稿交付：生成 task brief（人類 viewport）

EP review 修訂寫回後（定稿），生成 **task brief**——EP 的人類導讀殼（Report Shell，user 裁決：「EP 我現在很少看了，太難理解」——md 給 AI，殼給人）：

- 產物＝任務家 `YYYY-MM/<MM-DD-主題>/index.html` **骨架**（與 EP 本體同任務家目錄——位置規則見本檔「位置」條與 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」；零渲染管線內容——HTML 塊/表格可寫進敘事；渲染管線圖〔mermaid〕**延 hook 2 一次產**，diagram 槽留 degraded 待裝）——完整規格見 [illustrate html-mode](../_common/illustrate-html-mode.md)「html 報告殼」段（三層結構/內容篩選通則/敘事骨架/雙向一致性/殼生命週期掛點），此處不重述
- **成本分級**：基礎款（複製 template [`skills/_common/illustrate-report-shell.html`](../_common/illustrate-report-shell.html)＋填 slot）**必備**；升級款（+圖）於 **hook 2** 依 [diagram-selection](../diagram-selection/SKILL.md) 選型補——按 EP 規模（多段/有結構主張）或 user 點名
- 投影鎖定 EP 當下狀態（殼頭部聲明 **EP 路徑＋task integration baseline＋projection source**；未 commit 的 EP 用 content SHA——下游 `/post-build`/`code-review` 弧模式跨 session 可從殼讀，任務起點與投影新鮮度不混用）；badge 📋——推進時 badge 🟡 同步掛 implement 階段 5a（✅ 升級掛 post-build hook 2），實作章節掛 post-build hook 2（無 post-build 弧 fallback implement 階段 6；詳 [implement](../implement/SKILL.md)）
- 交付時引導 user 開殼 review（大方向判讀用殼、批准後進 `/implement`；AI 消費仍以 md 為源）

---

## 收尾步驟（所有功能段落完成後必做）

> **核心原則**：EP 必須包含收尾段，列出所有功能段落完成後的強制收尾動作。`/implement` 階段 5 執行。未完成收尾不得宣稱 EP 實作完成。

每個 EP 的收尾段必須包含以下四項：

### 1. 模組 instruction 檔 Capabilities + Kanban 更新

- 已完成 UC：在對應模組 instruction 檔（AGENTS.md 為主，legacy CLAUDE.md）Capabilities 表格新增一行（能力 + 入口 + ✅）
- 卡結案（repo 有 `backlog/` 時；時點＝收斂後——post-build hook 2／無 post-build 弧走 implement 階段 6 fallback；5a 只做 Capabilities Built 結算）——**結案兩步＋弧結案蒸餾第三動**（命令合約見 [kanban-board](../kanban-board/SKILL.md)）：`backlog task edit <id> -s Done --final-summary "<一句>"` → `task edit <id> --ref "<開工既有 EP 相對路徑>[,<shell 相對路徑>]"`（AIR-77 起永不搬，路徑不變時可略過），卡留 Done 欄；第三動＝本弧 memory 條目蒸餾為終態 facts；無 `backlog/` → 跳過
- **原子操作**：各時點內同時完成（5a：Capabilities＋消費場景＋SM 預覽；收斂後：結案兩步＋SM 升級＋EP 歸檔＋flow-feedback 歸檔——定義見 [metadata-sync](../metadata-sync/SKILL.md) 原子性）
- **從 EP Scenario Matrix 提煉「消費場景」**（full/standard 變更）：將矩陣中所有引用該 UC 的場景，提煉成自包含一句話描述（不引用 EP/SM 編號），寫入 Capabilities 表格備註或 backlog 卡（`backlog task edit <id> --append-notes`）

### 2. SYSTEM-MAP.md 更新（如果存在）

- 根據 UC 狀態變化，更新 SYSTEM-MAP.md 中受影響功能的 life-cycle 狀態
- 更新全域狀態統計表（如有）
- 移除已修復的 ⚠️ 標記

### 3. instruction 檔更新

- 檢查受影響模組目錄的 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy），確認架構描述反映變更
- 新增/修改：模組職責、導航指引、可複用基礎設施
- 遵循 [instruction-writing.md](../../rules/instruction-writing.md) 品質標準（Signal/Noise ratio、導航優先）

### 4. /audit-test

- 執行 `/audit-test` 對新增/修改的測試進行品質稽核
- 確認五證據域無 Critical：無反模式（含 vacuous-green）、行為覆蓋與 evidence depth 合理、mock 健康良好
- 稽核結果附於 `/implement` 完成報告

**simple 變更**（bug fix）：僅執行 /audit-test，跳過 UC 和 instruction 檔更新。

---

## 輸出

- **位置**：任務家 `YYYY-MM/<MM-DD-主題>/ep.md`（AIR-77 起永不搬；相對於專案根目錄；**任務家探測**：`ai-analysis/_tasks/` 在場→雜項家、session 從線 context 來→`ai-analysis/_projects/<線>/tasks/`、否則 repo-root `00-tasks/`——單一源見 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」；與 Report Shell 同 task 目錄——一弧全生命檔案同處；`ai-analysis/execution-plans/` 慣例退役）
- **檔名**：固定 `ep.md`（task 名已在目錄名，檔名不重複）
- **結構**：實作總覽 → **UC 盤點** → Scenario Matrix → **測試規劃段**（適用時）→ 段落劃分原則 → 各段落（Context → 要點 → Pseudo Code → 驗證）→ 整合策略 → 收尾步驟
- **整合策略必含 baseline 記錄**：一行 `baseline: <hash>`（`git rev-parse HEAD`，EP 建立當下）——下游 `/post-build`/`/code-review` 任務弧審查的範圍邊界，由 EP 攜帶跨 session 不重新推導（缺漏由 implement 階段 1 補記；模式見 [code-review](../code-review/SKILL.md)「任務弧模式」）

> **🔴 路徑警告**：Claude Code plan mode 的硬編碼路徑是 `~/.claude/plans/`，**那不是 EP 的存放位置**。EP 必須寫到專案目錄下的任務家 `<task>/ep.md`（探測規則見上方輸出段）。若已寫入 `~/.claude/plans/`，完成後必須複製到正確位置。

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始 EP 規劃"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「EP 規劃完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```

---

## 流程位置

```
〔pre-EP 軟 gate〕對話討論 →〔提醒〕/illustrate 結構化提案（軟 gate 不硬擋）→ 確認
/spec（純輔助·需求釐清，可選）→ /execution-plan（自足：段落0全域研究 + UC盤點 + EP Review, Clean Arch 視角 top-down；定稿時生成 task brief 報告殼）→ [/ep-validate] → /implement（含 Agent Review）→ [/code-review] → /commit
```

前置：`/spec`（純輔助·需求釐清，可選；pre-EP illustrate 結構確認為軟 gate 提醒，不硬擋）
後續：`/ep-validate`（可選，高技術風險時）→ `/implement`（如需額外審查可跑獨立 `/ep-review` 或 `/judge-review`）
