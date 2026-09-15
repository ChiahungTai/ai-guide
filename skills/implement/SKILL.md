---
name: implement

description: "EP 建好後逐段實作（準備、TDD、驗證、提交）。/implement <EP路徑> [段落編號]"
when_to_use: "Implement an Execution Plan segment-by-segment using TDD. Use after /execution-plan (with built-in EP Review). Supports parallel agents with --max-agents."
argument-hint: "<Execution Plan 檔案路徑> [段落編號] [--max-agents N | -a N]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent", "Workflow"]
---

# /implement — 基於 Execution Plan 逐段實作

基於 Execution Plan 進行逐段實作。每個段落都是 Self-Contained Segment，獨立實作、測試、驗證。

> **命名脈絡**：本 skill 原名 `/build`，因 ZCode 對 `build` 名稱的保留名衝突（skill 不可見）改名 `/implement`。文內「build 階段 N」「本 build」「build loop」皆指本 skill 的對應階段/流程。

**自主實作模式**：EP 已經過 EP Review Cycle 充分審查（內建於 `/execution-plan`），實作階段自主執行。自主決策、錯誤自癒遵循 [autonomous-execution](../autonomous-execution/SKILL.md)。

委託 Skills（實作時提供方法論）：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [test-driven-development](../test-driven-development/SKILL.md) — TDD 循環
- [debugging-and-error-recovery](../debugging-and-error-recovery/SKILL.md) — 系統化除錯
- [autonomous-execution](../autonomous-execution/SKILL.md) — 自主決策框架
- [python-type-gap](../python-type-gap/SKILL.md) — 第三方套件 type gap（mypy 失敗時）
- [agent-workflow](../agent-workflow/SKILL.md) — 並發控制、模型偵測、Agent spawn 規範；**各段 dispatch 查表**見其「全生命週期 execution contract（消費側）」（表主體在 agents/AGENTS.md）

Workflow 審查協調：[workflow-review-pattern.md](../_common/workflow-review-pattern.md)（Ultracode 下 Phase 4 使用）

## WorkUnitContract rows（本 workflow 持有——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（WorkUnitContract schema／Role→authority allow-list／resolver precedence 七步）；candidate 由 resolver 對 [catalog](../model-routing/catalog.toml) qualification records 硬過濾，本檔不材料化 model 值；無合格 candidate＝顯性 no-candidate，禁降 hard requirement。

| work unit | Role | authority | judgment_floor | qualifications | 說明 |
|---|---|---|---|---|---|
| 實作主腿（各段落執行） | Implementer | apply（accepted EP 後）／evidence | execution | implement_from_accepted_ep | `implement_from_accepted_ep + execution + apply`——進場受 accepted-EP predicate 約束（階段 0） |
| 機械驗證腿（ruff/mypy/pytest／rg 殘留對帳） | Verifier | evidence artifact（無 disposition/apply） | execution | evidence_retrieval | 組合命令形態；lite 測試＝規格陳述，驗收證據由 full 複驗 |
| Agent Review Reviewer legs（階段 4） | Reviewer | findings（無 disposition/apply） | execution（預設；高保護面／跨邊界語義面升 decision） | review_findings | 執行形態照 [review-engine](../review-engine/SKILL.md)「review 執行預設」 |
| finding 裁決（invoke /judge-review） | Arbiter | final disposition | decision | adjudication | seat 非 decision-qualified 時外派 decision-qualified candidate；無 candidate 禁 self-downgrade |
| decision escalation 腿（觸發時才派） | Arbiter | adjudication | decision | adjudication | 原腿停止＋產 escalation record 後派（見下） |

**escalation 觸發**（命中即停止該腿 → 產 escalation record〔記觸發條件＋已停點〕→ 派 decision work unit 裁決，非靜默降級續行）：

- EP conflict——實作發現與 EP「已決策（勿重辯）」段或 Pseudo Code 具體衝突
- 新 invariant——浮現 EP 未列的 domain invariant／silent-corruption path
- public boundary——對外 API／數據流邊界的契約選擇
- 跨 context 架構選擇——≥2 context 消費的共用層設計決策
- 反覆失敗——連續 3 次失敗（見「EP 專屬約束」錯誤自癒）

---

## 執行流程

### 階段 0：EP 快檢

快速確認 EP 品質，**僅嚴重矛盾才停下**，其餘自行判斷並記錄。

**accepted-EP predicate（進場硬閘門——AIR-91 S3）**：實作腿（execution/apply）進場前四條全要，任一不成立＝**禁止 execution/apply**：

1. EP review ledger（`## EP Review Findings` 表格）每列 status 皆 terminal——`implemented`／`rejected`／`verified`（EP flow 的收斂態；`open`／`adopted` 未回寫／`needs-confirmation` 皆非 terminal）
2. 所有 adopted（✅）修正已回寫 EP 本文
3. 無 `needs-confirmation`／`pending`（⚠️ 未裁決項在場即未 accepted）
4. user 顯式呼叫 implement（本次對話原話）

任一不成立 → 停在決策層：pending findings 交 user／judge 裁決回寫 terminal 後重新檢查，或轉 decision escalation——**不得以「快檢僅嚴重矛盾才停下」繞過**（快檢是品質寬容，predicate 是進場資格）。阻擋時印 `## EP 進場：⛔ 未 accepted（<不成立條件>）`（acceptance predicate receipt，SM-3 checkpoint）。

**強制輸出**：快檢完成後必須印出 `## EP 快檢：✅ 可實作` 或 `## EP 快檢：⚠️ N 項自行補充`。不得靜默跳過。

**前置流程確認**（僅記錄，不因此停下）：`/spec（純輔助·需求釐清，可選）→ /execution-plan（自足，含 EP Review）→ [/ep-validate] → /implement`

**docs mode 偵測**：掃描 EP 檔頭是否有 docs mode 聲明（變更全為 `.md` 且無新增/修改 `.py` callable 符號）→ 標記本 EP 為 docs mode，後續階段 2/3 依 docs mode 分支跳過 TDD/mypy/pytest，改 rg 殘留 + 一致性（完整對照見 [execution-plan](../execution-plan/SKILL.md) docs mode；「行為控制面」語義判準單一源亦在該段——本段只決定 TDD 跳過，審查深度由 post-build triage 按該判準決定，此處不重定義）。

**EP 品質快掃**：

| 檢查項目 | 通過標準 | 發現問題時 |
|----------|----------|------------|
| 段落結構 | 每段有 Context、Pseudo Code、驗證策略 | 標記缺漏，自行補上 |
| Pseudo Code 可執行性 | 具體到可翻譯為程式碼 | 標記模糊處，自行推斷 |
| 驗證策略具體性 | 有明確測試案例 | 自行補充合理測試 |
| 依賴錨點有效性 | file:line 與實際程式碼一致 | drift 時先更新 EP |
| 兜底宣稱路徑 | EP「X 段暴露/處理 Y」宣稱附 X→Y call chain 證據（path:line） | 路徑未驗證 → flag（計入「⚠️ N 項自行補充」），Y 須獨立調查 |
| EP Review 修正 | 掃描 EP review 區段(`## EP Review Findings` 表格,見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md)),納入實作 | 列入快檢報告 |
| **ep_type 偵測** | **機械掃描** `> **ep_type**:` 欄位（非語義字眼掃描 — 避免描述 blueprint 概念的 implementation EP 自指誤判；預設 implementation） | **blueprint → 不直接 /implement**：提示「逐段衍生子 EP」（列段落 + 建議子 EP 路徑 + build 順序），**不腦補**藍圖段落為實作段落（修段落缺 Pseudo Code 時「自行補上」的腦補災難路徑）；implementation → 正常逐段 |

**平行可行性分析**：
1. 建構段落依賴圖，識別可平行段落
2. 套用 max-agents 限制（預設 3，可透過 `--max-agents N` 或 `-a N` 覆蓋）
3. **有語義約束的段落強制序列**

**整合器段落識別**（驅動階段 2 硬閘門、階段 3 真實邊界的觸發）：掃描 EP 段落，標記同時滿足以下者為整合器型（見 [validation-strategy](../validation-strategy/SKILL.md)「整合器型變更判定」）：

- 主要價值是把 ≥2 個真實外部組件接起來（DB、catalog、SDK、跨進程、跨框架）
- 邊界正確性無法從任一單方文件推導
- 錯了不是調參數而是整天行為全錯

**機械 IO 觸發（三條件的 OR 補充，降 LLM 單點）**：段落 diff 觸及真實 IO 模式（parquet/檔案讀寫、DB 連線、第三方 SDK 呼叫、跨進程/跨框架邊界）→ 即使三條件判「非整合器型」，仍標「**待真實邊界評估**」，交階段 3 確認是否真需要真實邊界。候選撈取 → LLM 裁決兩段式（非硬卡）。排除：純 config/fixture 讀取（非整合器，避免 false positive 稀釋信號）。

整合器型段落標記後，在階段 2/3 對應加嚴（路徑覆蓋硬閘門 + 真實邊界整合測試）。

**complex-change constraint tightening**（與整合器加嚴並列的第二 escalation trigger）：當變更觸及「會被未來目標 rationalize 放寬的約束」（風控 limit / 會計守恆 / single-writer）且 complex / competing-demand 升高時，constraint invariant 審查自動加嚴（不只 IO 邊界觸發加嚴，複雜度-約束也觸發）。asymmetric drift 原則（AI 壓力下傾向破壞 constraint，check 須機械、不可被 lobby）見 [acceptance-evidence skill](../acceptance-evidence/SKILL.md)「Runtime Invariant Assurance」段 —— 本處只加 trigger 機制（IO 邊界 + 複雜度-約束雙 escalation），不重述原則。

### 階段 1：準備

**前置：working tree 乾淨度檢查**：`git status` 確認 working tree 變更都屬於本 EP 範圍。若有**其他功能的 untracked/modified 檔**（與本 EP 無關）→ 提示隔離（`EnterWorktree` / 新 branch / 先 commit 或 stash 舊功能），避免 build/commit 時混入不相關變更（靠 `/commit` 階段 2 git status 兜底，但前置隔離更省事）。

**A/B 分流**：上述隔離僅針對**與本 EP 無關**的改動（另 session in-flight、舊功能殘留）。**與 EP 相關的 ripple / 同 session 發現的順帶修正**（如 instruction 檔同步、metadata 結算）→ 不隔離，在階段 5 自行 fold in 為 working-tree 編輯（不需 `outward-action-consent` rule（commit 場景），見階段 5a「為什麼結算在 build 不在 commit」+ autonomous-execution 🟡 黃線；commit 仍在末端 🔴 紅線 gate）。

**前置：EP baseline 記錄**：EP 整合策略缺 `baseline: <hash>` 時補記當下 `git rev-parse HEAD`（通常＝build 首個 code commit 的 parent；resume 或 EP 後另有 commits 時＝補記當下現狀，git 弧邊界仍以該值為準——快照身份與 baseline 分開記，見下段）——`/post-build`/`/code-review` 任務弧審查的範圍邊界由 EP 攜帶，跨 session 不重新推導（見 [code-review](../code-review/SKILL.md)「任務弧模式」）。

**code_reality baseline snapshot（若 repo 可跑 code_reality——偵測單一真相源見 [code-reality](../code-reality/SKILL.md)）**：有 code diff 就跑（cr-audit R8，不綁「補記 baseline」條件；docs mode EP 免——code edges 不變）：`code-reality snapshot --repo <repo> --label <ep>`——錨定 build 起點 code 結構（HEAD 通常 = EP baseline；resume 或 EP 後另有 commits 時錨 build 起點現狀，git 弧邊界仍由 EP baseline hash 管轄，**snapshot 身份（label/時點）與 EP baseline 分開記**——消費端〔code-review 模式 B〕對照實際存在者，snapshot 晚於 baseline 時明示覆蓋區間），是 delta_tour（EP 宣稱模組 vs 實際變動對照）的 before 基準，階段 6 EP 對照歸納、`/code-review` 模式 B primed（含 `/post-build` 編排；弧模式才產出 delta_tour 對照——時點條件見模式 B）與 `/debrief` 前後差異段消費。docs mode EP 跳過（code edges 不變）；未裝跳過，不阻擋。工具用法真相源：[code-reality](../code-reality/SKILL.md) skill。

1. 讀取 Execution Plan（慣例路徑＝任務家 `<task>/ep.md`——探測：`ai-analysis/_tasks/`／`ai-analysis/_projects/<線>/tasks/`／否則 repo-root `00-tasks/`，單一源見 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」；與 Report Shell 同 task 目錄——一弧全生命檔案同處；舊 `ai-analysis/execution-plans/` 慣例退役），識別段落結構、依賴關係
2. **backlog 卡狀態更新**（repo 有 `backlog/` 時）：EP 對應卡翻進行中——`backlog task edit <id> -s "In Progress"`（＋開工雙 ref，合約見 [kanban-board](../kanban-board/SKILL.md)）；無 `backlog/` → 容錯跳過（進行中由任務目錄存在性表達；結算在階段 5a）
3. **深度查證現有程式碼**（不同於階段 0 的 drift 快掃，此處是理解程式碼上下文與設計意圖）。LSP `goToDefinition` 驗證 dependency anchors 的定義端，`findReferences` 驗證消費端，`hover` 確認關鍵參數型別——三者對不同 anchor 獨立，同 block 併發（[tool-discipline](../../rules/tool-discipline.md) 批次化）
4. **POC + demo 盤點**：掃描 `poc/**/*.py`、`demo_*.py`、`scripts/demo_*.py`、`notebooks/*.ipynb`，建立 `{module} → [poc/demo paths]` 映射表
5. 檢查清單：Kanban InProgress ✓ | POC/demo 映射表 ✓ | 測試檔案 ✓ | instruction 檔同步 ✓ | 依賴完整 ✓

### 階段 2：逐段實作

**EP 段落元素 → TDD 步驟**：

| EP 元素 | TDD 步驟 | 說明 |
|---------|---------|------|
| Context | 開始前讀取 | 理解背景 |
| §1b Invariant Impact（條件 — 段有此元素時） | RED 強化 | §1b「驗證對齊」映射的 invariant test 須在 RED 寫入、GREEN 後通過——producer 在 EP 宣告「動到哪些 invariant + 用哪個 test 守」，builder 機械確認該 test 存在且通過（producer 自證 → builder 驗收，非留 reviewer 推） |
| 驗證策略 | RED | 讀 EP 測試類型 → 分類情境 → 寫對應測試（測試類型選擇紀律見 [validation-strategy](../validation-strategy/SKILL.md)：e2e 優先 / 交易 replay >>> live / 放 scripts/ / 不重驗 pkg；詳 TDD skill EP Integration）；**每情境二擇一顯式結算**——入庫測試或記錄跳過理由（EP 段記錄），段落收斂時逐情境核對：「寫了測試」≠「每情境有去處」（post-build 側 lite-verify 終端對帳） |
| Pseudo Code | GREEN | 照設計實作 |
| 核心要點 | REFACTOR | 對 EP 完成檢查逐項驗證 |

**POC → RED 測試銜接**：若本段有對應的 POC（檔頭 `EP 段落:` 標注本段），優先將其「提煉改寫」成該段 RED 測試，非另起爐灶 —— POC 先於 impl、獨立產生（時間獨立性），改寫保留其驗證意圖。「提煉改寫」= 提煉 POC 的驗證意圖（斷言什麼行為）→ 寫成 pytest test function，assert 的對象（被測函數）尚未實作 → 確保 RED 狀態；**非把 POC 整段貼進 test file**（POC 已跑通非 fail）。

#### 平行模式

**Pre-flight**：先判 execution environment——Agent 直接寫主 worktree（共享樹，本段步驟 2）→ uncommitted 變更對 Agent 可見，**不需先 commit**（未經授權 commit 禁止，見執行約束）；isolated worktree spawn（worktree 看不到 uncommitted，見 [agent-workflow](../agent-workflow/SKILL.md) Worktree 隔離）→ dependency transfer（已授權 commit 或明確快照）；branch 不正確 → 先 checkout

**max-agents > 1 且有可平行段落**時：
1. 依賴圖分層為 waves
2. 同 wave 平行 Agent（上限 max-agents；Agent 直接寫入主 worktree，產出即 working tree 變更）
3. **Agent 產出機械驗證 = Claim→Evidence→Trust 校驗**（原則見 [acceptance-evidence](../../rules/acceptance-evidence.md)「證據獨立性 + Claim→Evidence→Trust」—— agent 自述是 L2 同義反覆風險、`git diff` 是 L1 機械證據）。**此模式適用所有 no-impact claim**（agent / producer 宣稱「沒影響 X」：accounting / risk / invariant）：claim 須獨立機械證據反證，否則退化為 self-report：
   - `git diff --name-only` 列實際變更檔（機械事實）
   - 比對各 Agent 自述「改了哪些檔 / 幾處」vs git 實際 → flag mismatch（**稱「零修改」但 git 顯示有改**最危險，曾釀 scope-creep 近乎 ship）
   - scope-creep：diff 檔是否超出該 Agent prompt 指定 scope → flag 超出（附 prompt scope 引用）
   - mismatch / scope-creep → 列為 finding 進階段 4 Agent Review，**不靜默採信自述**
4. Agent 全部完成後統一 `uv run ruff check --fix && uv run ruff format`

**Agent Context 邊界**：Agent 看不到主對話歷史、其他 Agent 結果、EP 準備結論。**主 LLM 的 prompt 是 Agent 理解任務的唯一來源。**

**Agent Prompt 必須包含**：
- EP 段落完整內容（Context + Pseudo Code + 驗證策略 + 核心要點）
- 準備階段結論（現有程式碼狀態、架構決策）
- 語義約束
- POC/demo 映射（Agent 回報前必須執行至少一個 demo 驗證）
- 相關檔案路徑（必讀 / 可修改 / 禁止修改）
- Skills invoke 指示（rules-reminder, test-driven-development, autonomous-execution）

#### EP 專屬約束

> **EP 是收斂方向，不是合約**。EP 是規劃層對需求理解的最佳猜測，有預見極限（見 [acceptance-evidence skill](../acceptance-evidence/SKILL.md)「認知誤差與 EP 的預見極限」）— 實作落差、設計本身錯，都只能在實作呈現時發現。前線實作 LLM 有裁量權根據實作發現調整；死守 EP 會實作「忠實但錯誤」的東西，反而妨礙人類在呈現時發現認知誤差。

- **EP 為收斂方向，實作層有裁量權**：照 EP 為主軸，但實作時發現 EP 預見極限外的真相（邊界、副作用、組件互動、需求落差）可調整 — 這是「發現真相的責任」而非「偷懶不照 EP」
- 記錄偏差：與 Pseudo Code 有出入時記錄原因（偏差是發現認知誤差的線索，不是違規）
- 記錄疑慮不中斷：先選最合理方案繼續，最後統一讓用戶確認
- 錯誤自癒：連續 3 次失敗 → 該腿停止＋escalation record＋轉 decision work unit（AIR-91 S3 起—— escalation 觸發清單見 WorkUnitContract rows；完成報告同段標 ⚠️ 揭露殘留）
- **batch ceiling**：累積多段未經人類判讀 → 建議暫停跑 session-boundary review（防 context 累積漂移;session-boundary review 原則見 [acceptance-evidence](../../rules/acceptance-evidence.md) B 軸人類驗收層）—— 單段重試上限（連續 3 次）vs batch ceiling（累積段落上限），雙 ceiling
- **依賴錨點 drift check**：實作每段前驗證錨點，drift 時先更新 EP

#### 驗證

每段完成後：**整合路徑覆蓋檢查**（rg）與機械驗證**組合命令**同 block 併發（一次 call 取代逐條，見 [tool-discipline](../../rules/tool-discipline.md)「獨立呼叫批次化」）：`mkdir -p .agent-tmp; uv run ruff check --fix . > .agent-tmp/v.out 2>&1 || echo "ruff:FAIL"; uv run ruff format . >> .agent-tmp/v.out 2>&1 || echo "fmt:FAIL"; uv run mypy . > .agent-tmp/m.out 2>&1 || echo "mypy:FAIL"; uv run pytest <test> -v > .agent-tmp/p.out 2>&1 || echo "pytest:FAIL"`——無 FAIL 行 = 全綠，輸出重導檔案再 Read（段級短測試隨組合跑；全量背景跑在階段 3）。LSP diagnostics 被動推送不耗 request。之後 POC/demo 驗證

> ⚠️ **mypy/pytest 閘門禁 `| tail/grep`**（exit code 被遮蔽 → 誤判通過，見 [bash-hard-rules](../../rules/bash-hard-rules.md)）；看 output 重導檔案再 Read。

> **docs mode**：跳過 TDD（RED/GREEN/REFACTOR）、mypy/ruff/pytest、整合路徑覆蓋；改執行「修改 → rg 殘留 → 跨檔一致性 → `/consistency`」。

**整合路徑覆蓋檢查**（機械式硬閘門，見 [acceptance-evidence](../../rules/acceptance-evidence.md) L3 + [quality-constraints](../../rules/quality-constraints.md) 符號 vs 路徑覆蓋）：本段是否新增/修改 callable 簽名（新參數、新 keyword）或新增注入點（constructor 接受新依賴）？

- 否 → 跳過
- 是 → 對每個新參數/注入點 `rg "<param>=" tests/`
  - **0 hits → 該段不得 pass**，必須先補消費端整合測試（驅動真實消費端流程 + 新參數組合路徑，非僅符號 import）
  - 有 hits → 確認 hits 是「驅動消費端流程」的測試，而非僅符號 import

> 受影響測試集列舉走機械反查、禁目錄直覺（配方見 cr-query skill）。

### 階段 3：整合驗證

> **scope 邊界（階段 2 vs 階段 3）**：階段 2 抓「新參數/注入點的接線路徑」（機械 rg 初篩）；階段 3 抓「既有接線的行為正確性」（需真實邊界跑）。**鐵律：階段 2 rg 有 hits ≠ 階段 3 真實邊界已滿足** — 符號出現在 tests（如被測單元自己的單元測試）≠ 消費端驅動該符號的路徑被覆蓋。例（真實歷史案例）：`rg "<符號>=" tests/` 有 hits 但全在被測單元自己的測試，消費端 integration 路徑不存在 — 符號有測 ≠ 消費路徑有測，bug 漏到補 integration test 才抓到。

全量 Lint + mypy + **全量測試**（背景跑）+ POC/demo 全量驗證。**全量測試 exit 0 是完成閘門**（regression gate）：green ≠ 驗證充分（primary evidence 是該段 targeted + integration test），但**必須 green** —— 未跑 / 未過不得宣稱 build 完成。**優先用專案的全量測試命令**（查 root AGENTS.md / Makefile，如 `make test`）；**無專案命令的小專案**（無 Makefile）bare `uv run pytest`（背景跑）即可 —— bare serial 的「資源上限 + cross-module pollution」警告是**大專案**情境（exit code 看 background task 結果，禁 `| tail`）。

> **docs mode**：跳過全量 mypy/pytest，改全量 rg 殘留 + `/consistency`。

**整合器型段落必須有真實邊界整合測試**（見 [validation-strategy](../validation-strategy/SKILL.md)「整合器型變更判定」＋「兩層整合測試」）：主要價值是接 ≥2 個真實外部組件的段落，完成定義必須含接線 guard（`unit_tests/`）+ 真實邊界（`integration_tests/`），不能只靠 mock — mock 循環論證會讓 mock 假設即 bug 來源。

### 階段 4：Agent Review Cycle

**Writer/Reviewer 分離**：用獨立 Agent context 做品質閘門，避免主 LLM 審查自己的 code。
review 執行預設（force 獨立 / max-agents 預設 3 / model 預設 / 3-perspective）見 [review-engine](../review-engine/SKILL.md)「review 執行預設」—— 本段僅定義 build 特有流程。**3-perspective**（① clean + ② UC-anchored + ③ Correctness，多樣性 > 數量）完整設計見 [agent-review-cycle.md](../_common/agent-review-cycle.md)。

> **code-reality（若在場）**：Agent Review 的 wiring 驗證（新/改 symbol 的消費端接對沒）用 callers 查詢；段 impact 驗證用 `impact_radius`；「沒影響 X」的 claim 機械反證用 code-reality（graph 是 L1 機械證據，補強 Claim→Evidence→Trust，見階段 3 整合路徑檢查）。**review agent spawn prompt 必含 CR 接線查證段（硬性——單一源 [review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」；build review agents＝`Explore` 無 CR MCP 白名單 → CLI 形態）**；主 session 自行查詢 **MCP 優先**（MCP `callers`／`impact_radius`；資料面 `build`／`snapshot`／`delta_tour`／`project` MCP face 同在）。分工 + GATE 見 [cr-query](../cr-query/SKILL.md)。

#### Step 1: 確認 max-agents

`--max-agents N` 或 `-a N` 參數控制平行 Agent 數量（預設 3，見 review-engine review 執行預設）。用戶可手動調整。
印出確認：`[Review Agent] max=N`

> **classifier unavailable**（spawn 收 note、無 findings）→ **重試 spawn ≤ 2 次**（間歇常成功），非直接降級主 LLM 自審（會丟失獨立 review）；仍失敗才降級 + 顯式標記 fallback。完整處置見 [agent-workflow](../agent-workflow/SKILL.md)「Auto Mode」+「spawn 失敗階梯」（429 / continuous）。

#### Step 2: 選擇審查模式

審查模式判定規則（effort/max-agents → Workflow/Agent Tool）見 [review-engine](../review-engine/SKILL.md)。偵測 effort level，印出確認：`[Review Mode] effort=ultracode, workflow=true, max=N` 或 `[Review Mode] effort=standard, workflow=false, max=N`

**A. Workflow 模式**（判定條件見 [review-engine](../review-engine/SKILL.md)）：

用 Workflow tool 協調 3-perspective（① clean + ② UC-anchored + ③ Correctness；perspective 定義 + prompt 見 [agent-review-cycle.md](../_common/agent-review-cycle.md)）；腳本骨架、DimensionVerdict schema、adversarial verify 見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md)。

| Workflow Phase | 說明 | Agent 數量 |
|----------------|------|-----------|
| Review | 平行 spawn 3 perspective agents（max-agents<3 時依 [agent-review-cycle](../_common/agent-review-cycle.md) 降級序：Correctness > clean > UC） | ≤ max-agents |
| Verify | 分級 verify node：Important+ 錨點批次（單一 lite agent）→ Critical 3 verifier + ≥2/3 quorum（配置單一源見 [workflow-review-pattern](../_common/workflow-review-pattern.md)） | 1 批 + 3 × critical findings |

Workflow 完成後回傳 `{confirmed, stats}` → Main LLM 進入「/judge-review」步驟（現有流程不變）。

##### Workflow 執行行為（官方文檔對齊）

- **可恢復**：workflow 被中斷（user stop / 429 序列化）可同 session resume —— 已完成 agent 回快取結果、其餘 live 重跑（`/workflows` → 選執行 → `p`）。under `/deep-work` 多階段 loop 中，每階段 workflow 各自可 resume。
- **監控**：review workflow 背景跑時用 `/workflows` 看階段 / agent 計數 / 令牌。under `/deep-work` 雙視角：`claude agents`（session 層）+ `/workflows`（workflow 層）。
- **acceptEdits-always**：workflow 生成的 subagent **始終在 acceptEdits 執行，無視 session mode**（[官方 workflows 文檔](https://code.claude.com/docs/zh-TW/workflows)）。目前 review agent 全 `Explore`（read-only）無風險；若未來 build 經 workflow spawn impl agent，**edit 會繞過 session 權限自動准** —— 自主路徑（`/deep-work` + auto-mode）下，classifier + acceptEdits 是唯一防線，須知會。

**B. Agent Tool 模式**（Fallback，非 Workflow 條件 = max-agents=1 或非 ultracode）：build 的 Agent Review force 獨立 agent、不走 Main LLM（review 執行預設 + 刻意覆蓋通用判定，見 [review-engine](../review-engine/SKILL.md)）。3-perspective（① clean + ② UC-anchored + ③ Correctness）完整流程見 [agent-review-cycle.md](../_common/agent-review-cycle.md)。

#### adaptive 觸發映射（extra agent 機械觸發）

base ① clean + ② UC-anchored + ③ Correctness 之外，extra agent 由**段落風險特徵機械觸發**（非 LLM 語義判「高風險」）。映射框架定義見 [review-engine](../review-engine/SKILL.md)「review 執行預設」點 5；build 提供 adapter 信號翻譯成通用特徵：

| build 既有信號 | review-engine 通用特徵 | 觸發 extra agent |
|------------------|----------------------|-----------------|
| 階段 0 整合器標記（機械 IO 觸發） | `外部整合` | adversarial |
| 階段 2 路徑覆蓋觸發（新簽名/注入點） | `公開簽名變更` | architecture + consumer-perspective |
| EP UC 盤點計數 >6（半機械：LLM 數 EP UC 清單，非純 diff） | `UC 數 >6` | UC-split |

**範圍（只接線既有信號，不新造偵測）**：build adapter 只翻譯上表兩個既有機械信號（IO + 簽名）+ EP UC 計數。**無特徵命中 → 僅 base ①+②，不開 extra**（機械避免浪費，非 LLM 判）。**跨模組特徵在 build 無 adapter**（無既有偵測，不新造；跨模組 ripple 交階段 6 layer 旗標導向 layer 2，不在 build 段落自檢 — 同 session 看不全跨模組 ripple）。

**依賴方向（DIP）**：build 是 adapter（提供特徵偵測 + 翻譯成通用特徵名）；review-engine 是 domain（定義特徵→agent 映射）。build 引用 review-engine 通用特徵名，review-engine 不列 build 特有名詞。

**cap + 優先序**：extra 受 max-agents cap + 優先序（見 review-engine 點 5：architecture > adversarial/edge > consumer-perspective）；多特徵命中 + cap 不足時依序取最高，截斷其餘並輸出截斷提示：

> ⚠️ cap 截斷：max-agents=N，base 佔 3，僅 (N-3) extra 額度。命中 [特徵清單]，取 [最高優先 agent]，其餘 [被截斷 agent] 截斷 — 建議提高 `--max-agents` 或跑 `/code-review` 補截斷軸。

#### 主 LLM — /judge-review

用 Skill tool invoke `judge-review`，傳入**所有 agent 的 review findings**（合併；**指定帳本＝`.review/<branch>.md` 工作帳本**——findings 與 judge 決策落盤〔含 header identity〕，供 post-build 證據身份比對與跨 session resume 消費；findings 只走 context 不落盤＝比對鍵缺席，post-build 將 fallback 全審）。評估每項：✅ 採納 / ❌ 不採納 / ⚠️ 需確認。

#### 主 LLM — Apply Changes

根據 judge-review 的 ✅ 採納清單修改 code——**先規劃整批、再批次套用**：逐項定位修改點與改法（目標檔先 Read，見 tool-discipline「檔案修改禁令」Read 紀律），多個 Edit 同 block 一次發出：跨檔獨立、同檔不同位置（old_string 不重疊）皆可；同檔鄰近一行式小修合併為單一較大 Edit。只有真依賴（先改簽名看結果再改 caller）才序列。修改完跑 `uv run ruff check --fix && uv run ruff format`。

#### loop 迭代收斂（Loop engineering — apply 後 re-review）

apply 後**不是一輪結束**，而是 loop 迭代收斂（self-correcting）：apply 修正可能引入新問題或舊 finding 未修對 → re-review 確認。

1. **re-review**（同 base 3-perspective）審 apply 後的 diff
2. **pass 判定**：re-review findings **再 invoke /judge-review**（非主 LLM 自判，保 Writer/Reviewer 分離）
3. judge-review 有新 ✅ 採納 → 再 apply → re-review（迭代）
4. **收斂條件**：judge-review 無新 ✅ 採納（pass）或**達迭代上限 3 輪**（純防無限 loop，**與 base 3-perspective 的「3」無關**——兩個獨立的 3）

**達上限硬性處置**（loop 未收斂）：標 ⚠️「loop 未收斂（達 3 輪上限，仍有未修 finding）」+ **阻止 Capabilities/Kanban 升級**（階段 5a 結算條件加「loop 須收斂」）+ **layer 旗標導向 layer 2**（階段 6 layer 旗標條件加「loop 未收斂」）。

> **Loop engineering 邊界**：build 內 loop（base 3-perspective 補 Correctness lens 後）收斂「視角覆蓋內」的錯（邏輯邊界、語意、結構）；**同 session 盲點類**（設計假設、系統性偏誤）loop 結構性抓不到 → 階段 6 layer 旗標導向 layer 2（loop 外部收斂）。不假裝 build loop 全閉環。

### 階段 5：收尾步驟（EP 強制）

**執行 EP 收尾段定義的三項動作。未完成不得宣稱實作完成。**

**讀取 EP 收尾段**：EP 結構末段的「收尾步驟」定義了本 EP 的具體收尾範圍。讀取後按以下三項執行：

#### 5a. metadata-sync 結算（依情境；大型/中型變更）

**委派** [metadata-sync](../metadata-sync/SKILL.md) skill（build mode）—— 依「結算情境矩陣」（見 skill）決定本 build 的結算範圍：

| 情境 | 結算 |
|------|------|
| **情境 A** EP 最後段、UC 全完成 | **Built 結算（5a）**：Capabilities ✅ 行寫入（導航職責——正式 ✅ 完成宣稱時點仍是收斂後結案兩步，此處語義＝Built 🟡）＋ 消費場景寫入 ＋ SYSTEM-MAP 預覽（Built）；**final 結案（收斂後——post-build hook 2／無 post-build 弧走階段 6 fallback）**：backlog 結案兩步＋弧結案蒸餾第三動（`-s Done --final-summary` → `--ref` 換 `done/` 新 URL，卡留 Done 欄；本弧 memory 條目蒸餾終態 facts；見 [kanban-board](../kanban-board/SKILL.md)）＋ SYSTEM-MAP 升級 ＋ EP 歸檔 ＋ flow-feedback 歸檔 |
| **情境 B** EP 中間段 | **預覽 only**：SYSTEM-MAP `📋→✅ Built`（不寫 ✅、不升 Verified）；loop 未收斂（達 3 輪上限）→ 阻止升級 + ⚠️ |
| **情境 C** 小型變更（bug fix／單檔小 tweak，無新 UC） | **跳過** Capabilities／Kanban 結算（純 refactor 不自動歸此——依規模，見下方小型變更段） |
| **情境 D** docs-mode EP（無 .py UC，EP 完成） | **EP 歸檔 only** |

> **為什麼結算在 build 不在 commit**：finalization 是 working tree 編輯（改 instruction 檔 / mv EP / 搬 Kanban），不需 `outward-action-consent` rule（commit 場景）；commit 退回純 git 提交（一次帶走 code + finalization）。舊設計（commit 階段 3 內嵌）對 LLM 是建議性、會漏跑（實證：commit 歷史多個「補漏」單獨 commit）。working tree 編輯沒 commit 就不永久，跟 code 一起 stash/checkout。Kanban 搬 In-Progress/（暫時狀態）已在階段 1 完成；消費場景提煉隨 Capabilities 寫入一併落地（原「暫存供 commit 寫入」取消）。

**Report Shell badge 同步**：本 EP 對應殼（任務家 `<task>/index.html`，execution-plan 定稿 hook 1 所建）存在時隨結算同步——情境 A（Built 結算）→ badge 🟡；收斂後 final 結案（post-build hook 2／階段 6 fallback）→ badge ✅；情境 B（中間段）→ 🟡；無殼（hook 1 未跑）跳過不阻擋。殼掛點全貌（hook 1/2、fallback、持久 delta tour）見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」。

#### 5b. 模組 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）+ architecture.md 更新（大型/中型變更）

> **為什麼兩份一起**：AGENTS.md（what / where，雙檔模式內容來源）與 architecture.md（why / whole-picture）同為導航文檔（見 [ai-development-guide](../../ai-development-guide.md) 文檔體系）。涉及設計變更時兩份都要看，避免 architecture.md 漂移成 LLM 讀不到現狀設計。純 feature（不改設計）只更 AGENTS.md。

1. **識別受影響模組**：從 git diff 中找出變更檔案所在目錄及上層目錄的 instruction 檔（AGENTS.md 為主，legacy 單檔模組為 CLAUDE.md）
2. **檢查更新需求**：變更是否影響 AGENTS.md 中描述的架構、模組職責、導航指引、可複用基礎設施
3. **更新 AGENTS.md**：新增/修改受影響段落，遵循 [instruction-writing.md](../../rules/instruction-writing.md) 品質標準（Signal/Noise ratio、導航優先、禁止元資訊）
4. **更新 architecture.md（若專案有此檔）**：本次變更若涉及**設計決策 / 設計原則 / 模組結構 / 新抽象層**，同步更新對應段落（新增原則、調整 data flow、模組職責表）。純 feature 實作（不改設計）跳過。

#### 5c. /audit-test（所有變更）

執行 `/audit-test` 對新增/修改的測試進行品質稽核（階段 2 已逐段檢查整合路徑覆蓋，此處複驗整體 + 其他角度如反模式、mock 健康度、測試必要性）。稽核結果附於完成報告。

**小型變更**（bug fix／單檔小 tweak＝情境 C）：跳過 5a Capabilities／Kanban 結算；僅執行 5c（/audit-test）+ 5b／5d（若動過導航文檔）。**純 refactor 不以「無新 UC」判小型**——跨檔／跨模組／改架構描述的 refactor 達大型／中型規模即走 5a／5b 照跑（恰是最需架構同步的變更；規模判準見 [ai-development-guide](../../ai-development-guide.md) 變更規模分級）。

#### 5d. 導航文檔 /consistency 品質閘門（大型/中型變更）

> **核心原則**：導航文檔（AGENTS.md / CLAUDE.md / architecture.md / SYSTEM-MAP.md，見 [ai-development-guide](../../ai-development-guide.md) 文檔體系）任一份內部 drift 都誤導 LLM。本次修改過的導航文檔必須通過單檔自洽閘門。

1. 對 5a 結算（AGENTS.md Capabilities 行 + SYSTEM-MAP 預覽）、5b（AGENTS.md / architecture.md）**本次修改過**的文檔，逐一執行 `/consistency <doc>`（單檔內部自洽：術語 / 章節 / 引用 / 邏輯 / 格式）。5a 新增的 Capabilities ✅ 行在此複驗。
2. 🔴 / 🟡 inconsistency → 修正後才算 build 收尾（不把不一致文檔留給 `/commit`）
3. **scope 邊界**：/consistency 是單檔內部自洽，**非跨檔**。跨文檔一致性（三份互相矛盾）由 `/doc-health`（maintain Phase 3）處理，非本步驟

### 階段 6：完成報告

> **誠實盤點**：效能／成本宣稱分列『上界估計』vs『現行實測』（沒跑過的路徑不得當現況宣稱）；工具／流程投資附退役地圖（取代了什麼、哪些變便宜）；『無優勢』也是要報的結果。

輸出：實作結果（新增/修改檔案）+ 架構決策記錄 + 待確認清單 + 未解決問題 + Agent 統計（平行模式）+ Agent Review 結果摘要 + **EP 對照（宣稱 vs 實際差異歸納，見下段）** + 能力狀態變更摘要 + SYSTEM-MAP 功能狀態變更 + architecture.md 設計變更（若有）+ /consistency 導航文檔結果 + /audit-test 稽核結果 + **全量測試結果（命令 + exit code + 通過計數；階段 3 完成閘門，必填）**

**EP 對照（宣稱 vs 實際差異歸納——主歸納點在此，post-build 只再提醒）**：build 現場是差異最清楚的時點（post-build/debrief 只能事後推導），兩個來源缺一不可——① **偏差記錄歸納（why）**：階段 2「EP 專屬約束」逐段累積的偏差（與 Pseudo Code 出入、疑慮、自癒 ⚠️）統一歸納，差異原因只在 build session 記得；② **機械對照（what）**：弧條件成立（HEAD 越過 EP baseline）時跑 `code-reality delta_tour`（呼叫形態與時點條件真相源見 [code-review](../code-review/SKILL.md) 模式 B；未裝/條件不符 → 標明降級）——session 歸納是 self-report，機械對照反證之（Claim→Evidence→Trust，見 [acceptance-evidence](../../rules/acceptance-evidence.md)）。**rename gate 觸發源（cr-audit R8）**：delta_tour 機械改名清單（renamed symbols）非零 → 該弧 rename 須附 CR callers 證據（被 diff 逼問而非自覺）。歸納供 `/post-build` 收尾報告帶入與人類直接判讀；深度渲染（邊集差異+行為 delta）屬 `/debrief`。

**Report Shell 實作章節 fallback（hook 2 由本階段承接——僅無 post-build 弧時）**：本弧不會跑 `/post-build`（user 直接 `/commit`、或弧在此終止）→ 實作章節＋**產圖一次**（依 [diagram-selection](../diagram-selection/SKILL.md) 選型補 degraded 槽）＋badge ✅＋**持久版 delta tour＝ask-once**（完成報告「⚠️ 待確認」列「delta tour：產生／略過」、預設略過＋inputs 保留——語義單一源＝[post-build](../post-build/SKILL.md) hook 2 點 4）在本階段套用，內容與掛點規格見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」；會跑 post-build → 跳過（hook 2 掛 post-build 完成點——實作章節須反映修正迴圈後**最終態**，本階段早於修正迴圈）。**觸發條件（收緊）**：僅 user 明示不跑 post-build 或弧在此終止才走——session 不得自行預測「本弧不跑 post-build」提前發布（預測即 PB3 換位復活）。**收斂檢查**：發布結案前按帳本完整狀態生命週期處置——`open`／`adopted` 未實作／`implemented` 未 verified 皆屬未收斂（**不得以 `open=0` 宣稱收斂**）；`needs-confirmation` 彙整報告不阻塞。**發布去重**：核對任務身份與實際結案狀態（卡已 Done／hook 2 已執行 → 跳過不重做）。**缺帳本**（`.review` 不存在）→ fail-loud 標示＋以 git／卡狀態推導，不以空集合冒充驗收通過。**並列主路徑**：fallback 與 post-build hook 2 同為結案主路徑（ZCode 弧常不跑 post-build——非降級）。**結案 gate 一律是 skill 流程步驟，禁掛 SessionEnd hook**（SessionEnd 不在 ZCode hooks 事件子集——contracts.md 定案，靜默 no-op；子集實測見 04 報告 §207）。**結案內容**（呼應 hook 2）：invoke [metadata-sync](../metadata-sync/SKILL.md) 結案段（backlog 結案兩步＋SYSTEM-MAP 升級＋EP 歸檔＋flow-feedback 歸檔）＋badge ✅。

**layer 旗標（硬性 — commit 前方向提示）**：偵測本 EP 變更是否觸及**跨模組**（`git diff --name-only` top-level 模組目錄計數 ≥2；模組目錄 = 專案 bounded context 根目錄，各專案自訂）、**公開簽名變更**（階段 2 路徑覆蓋觸發）、**整合器段落**（階段 0 標記）、或 **build loop 未收斂**（階段 4 達 3 輪上限）。命中 → 完成報告必含：

> ⚠️ 本 build 僅 layer 1（AI 自洽天花板）。此變更觸及 [跨模組/公開簽名/外部整合]，**建議跑跨 session `/code-review`（layer 2）** 抓全貌漣漪 / 同 session 盲點（段落自檢 + Agent Review 都是 layer 1，看不全跨模組 ripple）。

layer 旗標（本段）與檔尾「與其他命令的協作」段的軟提醒（涵蓋 debrief/illustrate/code-review）並存——前者是觸發條件命中時的硬性提示，後者是常規協作導覽。

> **終點聲明**：implement 止於本完成報告——commit 屬 `/commit`（人類確認硬規則，見 [post-build](../post-build/SKILL.md)），不由本 skill 觸發。

---

## 執行約束

### 強制

1. 必須先 EP 快檢
2. 必須完整讀取計畫書
3. 每段必須 TDD（RED → GREEN → REFACTOR）—— docs mode EP 除外
4. 每段必須獨立驗證（ruff + mypy + pytest）—— docs mode EP 除外（改 rg 殘留 + 跨檔一致性 + `/consistency`）
5. 禁止 `from __future__ import annotations`
6. 必須執行收尾步驟（階段 5）：大型/中型 → metadata-sync 依情境結算（5a：情境 A Built 結算 / B 預覽 / D EP 歸檔；收斂後 final 結案見階段 6 fallback；含 Report Shell badge 同步）+ instruction 檔 / architecture.md 內容同步（5b）+ /audit-test（5c）+ /consistency 導航文檔閘門（5d，含 Capabilities 行複驗）；小型（情境 C）→ /audit-test（5c）

### 禁止

- ❌ 跳過測試直接實作
- ❌ 使用 `sed` 修改程式碼
- ❌ 段落範圍外修改
- ❌ 中間狀態提交破損程式碼
- ❌ 未經用戶明確指示執行 git commit / push——implement 止於階段 6 完成報告，commit 屬 `/commit`（人類確認；見 [post-build](../post-build/SKILL.md) 止步硬規則）。EP 內的 commit 分組描述是規劃語境、並行 session 的 commit 行為，皆不構成授權
- ❌ 跳過收尾步驟宣稱完成

---

## 與其他命令的協作

```
/spec（純輔助·需求釐清，可選）→ /execution-plan（含 EP Review；定稿生 Report Shell〔hook 1〕＋EP 落任務家 <task>/ep.md）→ [/ep-validate] → post-EP: 方向確認 = 人讀 Report Shell（任務家殼）+ /ep-review → /implement（含 Agent Review + /audit-test, LLM 鏈；階段 5a 殼 badge 同步）→ post-build（看狀況呼叫，不硬定先後）: /illustrate（layer 3 結構 viewport）/ /debrief（深度選配：模組/檔案級深挖——日常判斷材料由殼實作章節吸收）→ /post-build（收尾鏈編排：code-review [dual-context] → judge-review → 修正迴圈 → consistency → metadata-sync → 殼 refresh〔hook 2〕；可拆開單跑）→ /commit
```

**搭配 `/goal`**：啟動後設定 `all segments implemented, uv run pytest exits 0, ruff clean, mypy clean, all demos run` 搭配 auto mode 效果最佳。

> **Agent Review Cycle（LLM 鏈, layer 1）已完成。** 機器自驗天花板 = AI 自洽,commit 前建議跑 `/debrief`（layer 3 改動理解簡報：驗證證據+認知誤差點）跨越認知誤差、`/illustrate`（layer 3 結構 viewport）跨越重造盲點;如需 LLM 第二意見可跑獨立 `/code-review`（layer 1/2）。

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始實作 EP"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「實作完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```
