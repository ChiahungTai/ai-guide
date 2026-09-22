---
name: agent-workflow
description: "Guides Agent spawning, worktree isolation, concurrency control, parallel execution, and delegation. Use when spawning agents, using worktrees, running parallel tasks, delegating to agents, handling scope-external discoveries, invoking /implement with --max-agents, or setting up Writer/Reviewer patterns. Triggers on: agent, worktree, spawn, parallel, delegation, side-discovery, scope redirect, manager-delegate, isolation, subagent, background task, auto mode. Boundary: how to spawn safely lives here; when to dispatch in conversation (主動派工/討論座席) = conversation-dispatch skill."
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
---

# Agent 與平行執行規範

Claude Code 提供多種平行模式，依任務規模和協調需求選擇。

## 平行模式選擇

Claude Code 官方四個**首類並行方法**（[官方比較](https://code.claude.com/docs/zh-TW/agents)），依「誰協調 / worker 是否互通 / 是否編輯同檔」選擇。**執行細節落在執行層命令**（`/deep-work` substrate、`/implement` Phase 4），本 skill 是選擇參考。

| 方法 | 它是什麼 | 何時用 | 執行落點 |
|------|---------|--------|---------|
| **Subagents**（Agent tool + worktree） | 一個 session 內委派 worker，獨立 context 回摘要 | 側任務會用搜尋/日誌/檔案內容淹沒主對話 | 本 skill 主要涵蓋；`/implement` Agent Review |
| **Agent view**（`claude agents` / `--bg`） | 一個螢幕調度 + 監控背景 session（supervisor 接管、survive terminal 關閉） | 多個獨立任務、user-away 可 peek/attach 監控 | **`/deep-work`** substrate layer（研究預覽 v2.1.139+） |
| **Agent teams** | 多個協調 session，共享任務清單 + 互傳訊息（leader 管理；實驗性，預設禁用） | 要 Claude 自己分派 + 保持 worker 同步 | Claude Code 內建（見官方文檔） |
| **Dynamic workflows**（Workflow tool / `ultracode`） | JS 腳本協調數十~數百 subagent，可對抗驗證 / 多角度起草 / loop 收斂 | 任務太大、需交叉驗證、大規模遷移/審計 | **`/implement` Phase 4** Workflow 模式；[workflow-review-pattern](../_common/workflow-review-pattern.md) |

**其他相關（非並行方法，與上面正交）**：

- **Writer/Reviewer 雙 session**：開新 terminal 審查避免 bias（pattern，非 surface）
- **Auto mode**（`claude --permission-mode auto -p`）：無人值守的**權限模式**（autonomy enabler），非並行方法 —— 詳見下方「Auto Mode」
- **Worktrees**：給並行 session 各自 git checkout，避免編輯同檔（搭配上述方法用；agent-view bg session 自動 worktree）

---

## 全生命週期 execution contract（消費側）

> 表主體單一源：[agents/AGENTS.md](../../agents/AGENTS.md)「全生命週期 execution contract」（每段一行，欄位 schema 以該表為準）。本節是**怎麼查表 dispatch** 的消費規範；各生命週期命令（deep-work／execution-plan／implement／post-build／commit）的一行形態註記指向本節，不重抄表。

1. **開段先查表**：當前 stage 的執行主體＝「主 session 直做」→ 不 spawn（判斷密集段——EP 規劃／judge 裁決／post-build 編排／commit consent，AIR-24 分工律）；spawn 類 → 取 registry name＋tier 欄。**implementation work unit 判定 role-based**：改變 behavior-bearing artifact 或其驗證物者一律 spawn（一行也算；purely editorial＋Marshal 本職豁免；「小範圍／單檔」不是豁免條件）——定義源＝[agents/AGENTS.md](../../agents/AGENTS.md)「全生命週期 execution contract」註 b
2. **spawn 形態按 harness**：ZCode＝registry spawn（生成檔 pins 生效）；CC＝named agent（`--agent <name>`／Workflow `agentType`）——全 role 名在 claude/ registry 生成在場（未知名稱仍立即退出）；model/effort 解析＝DispatchPlan（WorkUnitContract → model-routing resolver 七步 → candidate 四元組，[model-routing](../model-routing/SKILL.md)——catalog/presets 供給事實，不在此材料化值）；**lite／機械角色任務 spawn 型別必須是 registry 角色**——harness 內建 `general-purpose`／`Explore` 無 pin、繼承主 session 模型，lite 任務用內建型別＝旗艦燒機械段；唯讀探察／EP Review 形態用內建 Explore 承接（繼承主 session 旗艦＝正確）
3. **failure fallback 照表走**：重試 ≤2（classifier unavailable／1302）→ 顯式降級記錄（見下「spawn 失敗階梯」）；commit consent 行的 fallback 恆為「等用戶」，不可降級繞過
4. **模型歸因抽查**（tier 欄落地驗證）：registry pin 是否真達 wire 用 per-message modelID 對帳（ZCode db.sqlite），不信 session 自述（[model-routing](../model-routing/SKILL.md) 歸因紀律）
5. **DispatchPlan→carrier 三路**（換載體規則，語義單一源＝[model-routing](../model-routing/SKILL.md) DispatchPlan 條）：selected binding 等於 named preset default → registry spawn；harness 支援 spawn override → 同 WorkUnitContract／ExecutionPreset 只換 binding（動態升級不被固定 pin 吞掉）；否則 main-or-bridge 換載體，並把 Role／authority／surface 與**禁止再委派**完整裝入 work order（[work-order.md](../_common/work-order.md)；批次工單——單次 dispatch 承載多 unit 引用——照同檔「批次 envelope」：review units 不共 worker context、跨 authority／required 獨立 lens 不合併、逐 unit PASS/FAIL/未做收回）
6. **dispatch preview（consequential dispatch 前列印）**：`[Dispatch] unit=<work unit> role=<Role>/<authority> qual=<qualifications> judgment=<judgment_floor> caps=<capabilities> candidate=<model identity×binding> effort=<requested→effective> carrier=<registry|override|bridge> override=<echo|none> indep=<kind/relative_to/required> fallback=<decomposition|none> job/attempts=<jobId＋attempt 史>`——欄位至少涵蓋 work unit／Role-authority／qualification／judgment-capabilities／candidate model-binding／requested-effective effort／carrier／override／independence／fallback-decomposition／jobId-attempts（AIR-91 S3 契約；與既有 `[Agent] model=…` spawn 確認並存——後者是 carrier 執行面回報，前者是派工前 preview）
7. **failure handback（quota／runtime fallback）**：carrier failure 記入 work-unit-local **DispatchTrace**（欄位＝contract hash／candidate-binding／failure family／retryable-at／attempt disposition——[model-routing](../model-routing/SKILL.md) AvailabilitySnapshot 段）；**1308 candidate 在 retryable-at 前排除**（窗口制，重派無效）；**429 走既有 bounded backoff／降並發**（下方 spawn 失敗階梯）；候選耗盡＝**no-candidate report 停止**（列缺失條件），禁 loop、禁降 hard requirement

---

## Agent Tool + Worktree（互動式）

### 並發控制：自適應模型偵測

**Step 1**：從系統提示詞的 model 資訊判斷當前模型的 tier 歸屬（雙詞彙面——CC＝sonnet/haiku/opus、ZCode/GLM＝原生名）：

| 系統提示詞中的模型 ID | tier 歸屬 |
|---------------------|---------|
| `claude-opus-*` | opus（full） |
| `claude-sonnet-*` / `claude-haiku-*` | sonnet／haiku（lite） |
| `glm-5.3`（無 `-flash` 後綴） | 旗艦（full） |
| `glm-5.3-flash` | lite |

> CC 詞彙面的背後接線＝machine-local（user 維護，訂閱變更自換）——本表只記詞彙面→tier 歸屬，接線變更不需同步本表；GLM 原生名即 ZCode 實載 model id（非接線細節）。

**Step 2**：查「rate limit 與並發上限」表得**並發上限**——以**將 spawn 的 agent 所在 tier** 為準（spawn 模型詞彙對應列——sonnet/haiku/opus 查「haiku / sonnet / opus」列；與主 session 同 tier 的 spawn 才用 Step 1 偵測結果）（單一源 — 本檔不自帶數字，避免 provider 改限額時這裡 drift；表在 [model-routing skill](../model-routing/SKILL.md)）。

**spawn Agent 前必須印出確認**：`[Agent] model=<依 model-routing 角色 tier>, max=N, current=M`

### 調查型 fan-out（N-flash＋主 session 統合）

考古／稽核／掃描／分類調查→開 N 個 flash 平行拆樣（**一次三個為上限**，user 裁定）＋**主 session 統合複查**（主 session 的義務，不外包給 agent）。

### Spawn 預設背景（ZCode spawn 原生預設前台——規則補上）

ZCode 的 Agent tool **預設前台**（阻塞主對話）——前台 spawn 期間使用者無法插話，steering 訊息只能中斷、連帶殺掉 agent。因此：

- **spawn 帶 `run_in_background: true`**（Claude 2.1.198+ 已預設背景免動作）；spawn 後主對話回報「進行中」即結束 turn，agent 完成的通知會自動接手
- **背景 gate（ZCode 已上線）**：省略或 `run_in_background != true` 的 Agent 派發被 PreToolUse hook 以 allow＋updatedInput 自動補成背景（rewrite 式零浪費，fail-open）——**省略參數不再等於前景**；真要前景（含 <30s 短 probe 例外）須 prompt 前 200 字帶 `[fg]` 機械子串。機制細節（audit log、per-session 啟動快照限制）見 `hooks/AGENTS.md`「Agent 背景 gate」
- 例外（前台）：結果是當前步驟立即依賴且預期 <30s 的短 probe，**且 prompt 帶 `[fg]`**
- 為什麼（兩面）：前台 = 對話卡死 + 使用者 steer 即殺 agent；背景 = 使用者可繼續對話、steer 不影響 agent、通知後無縫接手——token 帳等價（接手時 context 重送都一次、cache TTL 看壁鐘與 turn 結構無關）
- pytest 與預期 >10 分鐘命令預設背景跑；短測試可併機械驗證。spawn agent 不能拿來繞 Bash timeout——真實案例：誤以為 Bash 只能 600s 而加 bridge wrapper，實際 `run_in_background` 從頭可用，代價是 agent 開銷、間接層與收斂路徑變長。
- 先做可獨立的前台工作；沒有就回報進行中並結束 turn 等通知。禁背景阻塞長等（各 harness 機制名不同；主對話被中斷時 agent 會連帶 killed、產出遺失）；前台短等待只限結果立即依賴的 <30s probe。
- **背景 agent liveness（死亡盲區防禦——真實案例：ZCode app 更新重啟殺掉多個背景 agents、長時間無人知）**：通知是被動喚醒——可以等通知，但**一旦被喚醒（completion／user message／resume）、準備依賴舊 agents 結果前，先過 generation/reconciliation checkpoint**：確認承載 process generation 未變（ZCode app-owned Agent-tool 背景 agents：app 重啟＝舊代全死、零歧義；delegate-bridge external runtime 背景 worker 跨 session 存活，依其 jobs 狀態判定）。generation 命中後**先收 residue 再重派**（DB＋transcript＋worktree 殘留——完成未送達者盲重派＝duplicate side effects）；per-agent 判定禁「全凍結才報」聚合；**silence ≠ death；old-generation unresolved ≠ safe-to-retry**。驗屍法（watcher 不可用時的手工 fallback）：db.sqlite `MAX(time_created)`（Python `sqlite3`＋`file:...?mode=ro`——CLI 有 silent-empty 坑）＋`ps`＋transcript mtime＋`git status` 殘留＋`TaskOutput` registry 查無。防禦階梯其餘項（WAL receipt／generation watermark reconciliation／exact-process hard-death dual-signal；stall advisory——in-harness 域已由上條工具化承接，bridge 域維持 advisory-only）維持另案。
- **in-harness 子 agent 凍結偵測工具化（主 session 持有 watcher＝`scripts/harness_waiter.py`：registry 註冊→輪詢→凍結收割→喚醒；AIR-149）**：dispatch 註冊一行（spawn 拿到 taskId 同 step）——`uv run python scripts/harness_waiter.py .agent-tmp/liveness-registry.json --register <taskId> --attempt-id <id> --sink <path> [--expected <json>] [--surviving-handle <h> ...] [--silence-budget-min <min>] [--expected-heartbeat --heartbeat-file <path>]`（末組旗標＝heartbeat pilot——impl-lite／cr-research 兩 role 照抄範例即啟用；接線四環＝下節「Worker supervision contract」；register 假設序列呼叫——主 session dispatch 同 step 一行，並發無鎖）；註冊後啟動輪詢：`uv run python scripts/harness_waiter.py .agent-tmp/liveness-registry.json`（背景常駐 run_in_background——凍結/hard-death/stale 時 exit 喚醒）；in-harness brief 禁未登記 long-lived/daemonized child——要 server 須記 ownership handle 進 `--surviving-handle`。**凍結處置協議（user 裁決：全面靜默 20m＝bug 處理——不判死，先收割後砍）**：全面靜默 20m→收割→喚醒→主 session TaskStop→STOP verification（metadata terminal＋cursors grace 靜止＝STOP_CONFIRMED；否則 STOP_INCOMPLETE 禁重派）；**quarantine 期恢復活動記 `resumed_during_quarantine=true` 仍照砍**——禁 kill 前重檢 silence（恢復一行逃過處置＝liveness inference 回滲）。重派前過 **RETRY_SAFE gate 三問**：surviving handles 全 collect？outward side effect 盤點？deliverable 已存在先 collect？——任一不明＝禁重派。**偵測與處置分離**：watcher 永不 stop／重派（TaskStop 與重派決策＝主 session）；bridge 域背景工維持 advisory-only watcher（AIR-146），不隨本工具化改。
- **subagent 自持背景命令完成後的自動續跑不可依賴（死亡盲區同族——真實案例：09-14 AIR-87，ZCode 實證背景 exec 已完成而 subagent 停留 completed 狀態、續跑未發生）**：防禦＝主 session 持有 watcher（`scripts/harness_waiter.py`，見上 liveness 工具化條）／輪詢敲醒，或背景命令由主 session 自持——禁假設「subagent 會被自己背景命令的完成通知喚醒續跑」。bridge 域（delegate-bridge 背景 job）同構防禦＝派工同 step 自動 arm `scripts/bridge_waiter.py`（一顆背景 shell；exit 124 內部消化、terminal 輸出 CollectionReceipt、stalled＝exit 3 advisory——自動 arm 規約單一源＝bridge-dispatch skill「Dispatch⇄collection 配對——完整模式」段）。
- **collection-owner invariant（0921 雙模型調查收斂；0922 AIR-160 收緊——invariant 與 mechanism 分離，mechanism 可演化 invariant 不綁 script）**：**背景＋有限工 dispatch ⇒ register 義務——dispatch 尚未完成，直到 collection owner（watch handle／registry entry）已建立**。形態分類：①bridge 背景 job（N 顆／長工／須活過重啟）＝強制 arm ②Task tool 背景 subagent＝**一律強制 register**（寫檔／長工／無人在場／互動皆然——互動短腿豁免已刪，AIR-160：三起無聲死亡的事故破口）③前景 <30s probe＝豁免（前景本身即 ownership；限結果立即依賴且 <30s 且 prompt 帶 `[fg]`）④daemon／長駐 child＝不套 terminal watcher，**已登記 ownership handle**（`--surviving-handle`）豁免取代。誤報有聲且廉（advisory wake）、漏報靜默且貴（殭屍燒 quota——歷史殘留數十具實證），不對稱支持強制。

## Worker supervision contract（派工監督契約——AIR-160 凍結）

> 本節是 supervision contract 的**凍結定義源**（三出口語義、偽造禁令、heartbeat 協議）——機制面（registry/watcher/sidecar）可演化、契約不綁 script，改本節走卡面 amendment。機制真相源：`scripts/harness_waiter.py`（ZCode in-harness supervisor）、`scripts/child_heartbeat.py`（child 端 sidecar helper）。

**invariant（勿重辯裁決）**：背景＋有限工 dispatch ⇒ register 義務——**dispatch 尚未完成，直到 collection owner（registry entry／watch handle）已建立**。豁免僅兩項：前景 <30s probe（前景本身即 ownership）＋已登記 ownership handle 的 daemon／長駐 child（`--surviving-handle` 取代 terminal watcher）。

**三出口**（每個 registered worker 只能到達其中之一；**UNKNOWN 不是出口**）：

| 出口 | 判準 | 處置 |
|------|------|------|
| **TERMINAL** | metadata terminal transition（唯一權威狀態訊號） | parent collect 銷帳 |
| **HARD_DEATH_EVIDENCE** | 死亡證據（generation mismatch／registry entry 異動） | 立即喚醒 parent，禁 retry |
| **TIMEBOX_EXPIRED** | 牆鐘 timebox 到期（時間盒事實） | 先收割後喚醒——advisory，不 stop 不重派 |
| UNKNOWN（升級面） | 錨點缺失／JSON 不可解析／schema 不符＝無法判定 | **fail-loud 升級主 session，禁列結案態** |

silence 可觀測、death 不可——**禁逾時宣稱死亡**（timebox 到期只宣稱逾時，禁宣稱 worker 已死）。

**偵測與處置分離**：watcher／heartbeat 只偵測與喚醒（advisory）；TaskStop、重派、collect 銷帳＝主 session／deepwork 授權鏈。**ownership 歸 parent**：registration 與 collected 都是 parent 專屬動作。

**偵測語義（分級證據——禁推活死）**：

- **output.txt 缺席／transcript mtime／一般檔案活動＝D 級遙測**——只證明有活動過，禁推活死（實證：impl-lite flash 完成前不 materialize output.txt）
- **ping 失敗＝不在冊（NOT_ADDRESSABLE），禁推死亡**——凍結矩陣未跑前 ping 僅 reachability
- **working tree 活動歸因必須綁 attempt 身分窗**（`registry.createdAt ≤ mtime ≤ now`）——窗外增長標 `attribution_ambiguous` 升 needs_human（0922 同 WT 雙 worker 併發事故的條文化）

**wake early, declare death late**：B/C/D 級證據可喚醒 controller；只有 A 級（terminal metadata／generation mismatch）可產生 `HARD_DEATH_EVIDENCE`；重派前必須 fresh probe＋scope fence。

**heartbeat 協議（pilot：impl-lite＋cr-research 兩 role；其他 role 缺席合法）**：child 依注入週期寫**自己的** sidecar（`scripts/child_heartbeat.py`——JSONL append-only：seq 自動遞增、`emittedAt`/`intervalSecs` 由 helper 機械寫、半截行丟棄；**heartbeat 週期預設 60s**（`--interval-secs` 旗標，值寫進 sidecar row 供 watcher 對帳）；**harness_waiter stale 門檻＝2×週期**（預設 120s）；sidecar 路徑/taskId/attemptId/週期/timebox 由 spawn prompt 注入，role 檔不硬編）。watcher 每輪 join 讀 sidecar，三分支：

- **fresh**（最新記錄 age ≤ 2×週期）→ 壓 advisory（recent-checkin／recent execution 續等——heartbeat 只證明 T 時刻執行過 emitter，不證明現在活著）——**禁延 timebox**（heartbeat 永不覆蓋 timebox／terminal）
- **stale**（記錄存在但斷訊超 2×週期）→ `STALE_ADVISORY` 提前喚醒——advisory，**stale 不判死**
- **缺席**（無記錄／child 未實施 heartbeat）→ `heartbeat_missing` telemetry L0——**缺席合法**，禁失敗禁喚醒

**接線四環（照做即啟用 pilot——spawn prompt 注入 → child 寫 sidecar → register 帶旗標 → sweep join 讀，一次讀完能照做）**：

1. **注入**：spawn prompt 給 sidecar 路徑（`.agent-tmp/heartbeats/<taskId>.jsonl`）＋taskId＋attemptId＋週期（預設 60s）＋timebox
2. **child 回報**：working 期間每週期跑 `uv run python scripts/child_heartbeat.py --file <sidecar 路徑> --task-id <taskId> --attempt-id <attemptId> --state working`；完工改 `--state done`
3. **register**：dispatch 同 step 的註冊行帶成對旗標 `--expected-heartbeat --heartbeat-file <同 1 的 sidecar 路徑>`（範例＝上節 liveness 工具化條）
4. **sweep**：watcher 每輪 join 讀 sidecar（record contract 全欄位驗證、torn tail 丟棄）跑三分支——stale 提前醒，不收割不記帳

**偽造禁令**：fresh 不延 timebox、stale 不判死、**child 禁自報 collected**（child 只寫自己的 sidecar；`done` 是 child 自述，collected 由 parent 對帳銷帳）。**台帳分家**：bridge liveness.jsonl 不動；child 寫自己的 sidecar；worker-supervision/1 投影按需。hooks＝reconciliation trigger 非 detector。SendMessage ping contract 未凍結——留空分支（凍結前禁接線）。

### Subagent 產出格式：schema 嚴格度（raw material vs deliverable）

spawn agent 時，依「agent 產出是**原料**還是**直接交付**」選 schema 嚴格度：

| 產出性質 | schema | 為什麼 |
|---|---|---|
| **原料**（給主 session 組裝/parse，如 §HR 深審內容、findings 清單） | **free-text 或極簡 schema**（單層、少 required） | agent 價值在分析；strict schema 是約束不是助力 |
| **直接交付**（agent 產出即最終結構，如 rename edit list、verdict 物件） | StructuredOutput schema OK | 結構本身是 deliverable，值得強制 |

**🔴 anti-pattern：complex nested StructuredOutput + 多 required 用於「原料」產出** → **retry-exhausted**（agent 做完真實分析但無法 fit 進 nested schema，反覆重試全廢）。實證：`/codebase-sweep`（現 smell-detector baseline mode）indicators/ rollout 用 6-agent workflow（nested io_contracts/test_map schema）→ 6/6 retry-exhausted（224 tool uses 白費）；改直接執行（單 session）一次成。

**恢復路徑**（遭遇 retry-exhausted）：
1. **直接執行**（單 session，主 LLM 自己做）— 目錄/任務規模 fit 一個 session 時首選
2. 或 **free-text schema** + 主 session 從 free-text parse 結構
3. 禁：重跑同一 strict schema（必然再 retry-exhaust）

判準自問：「agent 回傳的東西，我是直接用，還是要再組裝/parse？」要再組裝 → free-text。

### 委派框架（Delegation Philosophy）

agent-workflow 偏控制導向（scope fence / git diff 驗產出 / classifier / gate），但放手碎片零散未連貫（[autonomous-execution](../autonomous-execution/SKILL.md)「不交半成品」、[build.md](../implement/SKILL.md)「裁量權」+ context handoff、scope fence「創造性例外」）。連貫化為 **delegate(goal + tools + context) → let go(within guardrails) → verify(outcome)** 模型。

**連貫模型**：

- **goal**：EP segment / 任務目標（清晰可驗收）
- **tools**：delegation 前配工具集——依任務領域匹配 skill description 觸發詞（任務含「測試」→ TDD skill、含「錯誤」→ debugging skill）；[build.md](../implement/SKILL.md) Agent Prompt 已有完整 skill invoke 實作清單（rules-reminder / test-driven-development / autonomous-execution），此處概念化引用不重列
- **context**：[build.md](../implement/SKILL.md) context handoff 已是最完整實作——引用不重述
- **let go**：實作層裁量權（build.md「EP 為收斂方向，實作層有發現真相的責任」）；放手底線 = [autonomous-execution](../autonomous-execution/SKILL.md) 紅線/黃線
- **verify**：[build.md](../implement/SKILL.md) git diff + Agent Review——引用不重述

**平衡（delegate + verify，非 delegate + trust）**：

- **防過度放手**：verify 是委派的**共同體**非事後補丁——純放手無驗證 = scope-creep 近乎 ship 重演。**強度上限**：delegate+verify 假設 verifier（主 LLM）可靠；deep-work 長 session 的 verifier 退化（context fatigue）是已知上限，由 build.md batch ceiling 部分緩解但不完全覆蓋。
- **防過度控制**：創造性任務（設計/實作）**不加 fence**（scope fence 已排除創造性）。委派光譜：機械任務 = tight delegation（fence）；創造性任務 = loose delegation（goal+tools+放手）；混合型（部分機械 + 部分判斷，如重構提升可讀性）= medium delegation（goal + 精簡 fence，只 fence 不可碰區域 + 放手判斷空間）。
- **fence vs 委派非矛盾**：兩者適用**不同任務類型**（同光譜兩端）——fence 是委派的特殊形態（目標極明確時的 tight delegation），委派框架是 scope fence 的上層框架。

**delegate→verify loop（與 Recovery 段互補）**：委派（本段）上游 → 降低 false-done；[autonomous-execution](../autonomous-execution/SKILL.md)「Session 級 Recovery」completeness validation（false-done 偵測）下游 → 捕捉殘餘。兩者形成 loop，**互補非重複**。**邊界**：verify 的 git diff 半邊（scope/claim 校驗）與 Recovery 段 completeness 互補不重疊；Agent Review 半邊關注**單段 code 正確性**（段落級），Recovery 段 completeness 關注**跨段落 EP 完成度**（EP 級）——builder 寫 verify 時引用 build.md Agent Review（段落級），不重述 Recovery 段的 EP 級 completeness。

**委派時 side-discovery**：agent 發現 scope 外 → Side-Discovery 段（scope-fence 負空間 redirect）是委派框架的 redirect 應用。

> **docs-mode 強度上限**：委派是**判斷框架**非機械閘門（無 server-side enforcement）；其 verify 半邊的機械性來自 build.md git diff（已存在）。理論支撐：ref-docs Ch19 AI Contract 四 pillar（Formalized Contract / Dynamic Negotiation / Quality-Focused Iterative Execution / Hierarchical Subcontracts）+ Ch6 Planning「does the how need to be discovered, or is it already known?」判準（控制 vs 放手）——外部靈感來源；核心論證用內部已查證引用（build.md 裁量權 / 紅線）承載。

### Worktree 隔離

**Worktree 基於 committed state 建立，看不到 uncommitted changes。**

Pre-flight 檢查：
1. **Uncommitted dependency**：Agent 需要看到 uncommitted changes？→ **先 commit**，再 spawn
2. **Branch check**：當前 branch 是否正確 base？不是 → 先 checkout
3. **多 Agent 協作**：先把前置工作 commit 到 feature branch，再從該 branch spawn

**Prompt 路徑紀律**：Agent 在 worktree 中 CWD 是 worktree 目錄。**用相對路徑**，不要用主 worktree 絕對路徑。

**安全不變量**（path-in-root / symlink-escape 偵測 / 優先 EnterWorktree）定義見 [autonomous-execution](../autonomous-execution/SKILL.md)「機械空間不變量」段；此處僅為 worktree 用法，不重述安全不變量定義（single-source）。

何時用 `isolation: "worktree"`：PoC 驗證、平行實作、風險操作。
何時不用：純研究（background Agent 即可）。（isolation 取捨與 execution ownership 正交——implementation work unit 一律 spawn、單檔小改不是豁免，契約單一源＝[agents/AGENTS.md](../../agents/AGENTS.md) execution contract 註 b）

### PoC → Implement 流程

1. Agent 跑 PoC（worktree）→ 失敗自動清理 / 成功讀取結果
2. **審查 Agent 產出**（不要假設正確）→ 跑測試、code-review、修正設計瑕疵
3. 確認方向後實作 → implementation work unit spawn Agent（範圍大小不改變 ownership——「小範圍主 session 做」已退役，契約單一源＝[agents/AGENTS.md](../../agents/AGENTS.md) execution contract 註 b）

**品質預期**：核心邏輯 ~80% 正確，細節（邊界條件、錯誤處理、命名）常需修正。

### Scope Fence（機械任務 prompt 模板 — negative-space）

機械任務（rename / 補 log / format / 批次替換）的 Agent prompt 只有「做什麼」不夠，必須加 **negative-space scope fence** —— 否則 Agent 易「順手重構」scope 外區塊（實證：4 個補-Logger agent 各自找到已有 Logger 的區塊順手改 severity / 合併 / 丟 callback 名，需 4 處 pure-revert）。模板三要素：

- **DO NOT** modify blocks that already contain `<pattern>`（例：`Logger.` 已存在的 except 塊 —— 別動）
- 只 touch 符合 `<criteria>` 的區塊（例：silent `except: pass` 或 print-only 塊）
- 完成後自驗：`rg <pattern> <edited_file>` 確認沒碰不該碰的

**適用判準**：機械任務（pattern 明確、意圖單一）強制；設計 / 實作任務（需創造性判斷）不強制。與 build 階段 2「Agent 產出機械驗證」攻守 —— fence 事前預防、git diff 事後驗證。

### Side-Discovery（scope-fence 負空間 redirect）

Scope Fence（上）擋機械任務 agent「順手重構」scope 外區塊，但 fence 是**死路**——擋擴大卻無 redirect，發現的 scope 外改進被丟棄。Side-discovery 補 **redirect 通道**：agent 發現 scope 外 meaningful 改進 → 建 Backlog 卡（非擴大 scope、非丟棄）。fence 說「不擴大」、side-discovery 說「scope 外工作去哪」——兩者共置（single-source），否則 fence 負空間是死路（擋擴大 + 無 redirect = 工作遺失）。

**觸發**：agent 審查/實作時發現 **scope 外 meaningful 改進**（非當前任務目標，但值得做）。

**triage 決策**：

- **defer**（default）：建 Backlog 卡供日後排程
- **accept**：擴大 scope——**需用戶/EP 確認，非自主擴大**（與 scope fence「不擴大」一致）；**自主模式（deep-work 半夜跑）用戶不可得 → accept 預設降級為 defer**（建 Backlog 卡 + completion report 標記待用戶確認，對齊 [autonomous-execution](../autonomous-execution/SKILL.md) 紅線 git commit 自主處置）
- **decline**：明確不值得，丟棄（記錄原因，避免重複發現）

**建卡**（defer 時）：用 [kanban-board](../kanban-board/SKILL.md) 卡片模板（建卡欄位＝標題／目標一句／驗收條件——欄位名對齊該模板，不在此重複定義；開工時依 kanban 起手式用 `--ref` 補 references）。依賴關係在「備註」欄標 `[blocked-by: <當前任務>]`（備註行約定；kanban 模板無此標準欄）。

**防氾濫三層**：

- **threshold**：「meaningful」= 獨立發現時會 warrant 一張卡/EP 的改進（非 trivial 觀察）
- **batch**：side-discovery 先記錄到 completion report，**段落/任務結束時統一建卡**（非執行中斷流程）；研究 agent（Explore 等）不產 completion report → 記錄於 spawn prompt 回覆，由 spawner 代建卡
- **人類 triage**：kanban 每週回顧（kanban-board）清理低價值卡

### `/implement` 整合

`/implement --max-agents N` 的 N 是**並發上限 cap**（非 review 配額；上限值單一源＝[model-routing](../model-routing/SKILL.md) 並發表）——review agent 配置由風險 profile 推導（單一源＝[review-engine](../review-engine/SKILL.md)「審查模式判定規則」：ordinary 單獨立 context、boundary fresh＋intent 分離），不按 N 預設派滿（舊「預設 3 agent」固定語義已廢除）。

---

## Writer/Reviewer 雙 Session

新鮮 context 提升審查品質（同 LLM 自審有 bias）——原則與流程見全域 guide「Solo + AI 開發工作流」的 Writer/Reviewer 分離段（always-loaded，此處不重述）。

---

## Auto Mode

無人值守自主執行。classifier model 在命令執行前審查，阻擋 scope 升級、未知基礎設施、和惡意內容驅動的操作。

```bash
claude --permission-mode auto -p "fix all lint errors"
```

**注意**：非互動式 `-p` 模式下，如果 classifier **反覆阻擋**操作（主動擋 scope 升級 / 惡意），auto mode 中止（沒有用戶可回退）。

**classifier unavailable ≠ 阻擋**（服務端間歇故障，非主動擋）：spawn Agent 收 classifier unavailable note（只回警告、無 findings）→ **先重試 spawn（≤ 2 次，間歇常成功）**；仍 unavailable 才降級主 LLM 自審 + **顯式標記 fallback**（警示獨立 review 丟失，非靜默降級）。GLM / 非 Claude harness 的 classifier 間歇 unavailable 是已知風險，重試是正解非異常（[model-routing](../model-routing/SKILL.md) classifier 段）。

---

## spawn 失敗階梯（general，所有 spawn 共用）

spawn 失敗處理依失敗類型分階梯 —— classifier unavailable retry 見上方「Auto Mode」；本段涵蓋 **429 / 持續失敗**（所有 spawn 命令共用的 general 階梯）：

```
429 單次 → backoff retry（同 spawn 重試）
429 持續 → 降並發（N → N/2 → … 最深 = serialization，concurrency=1，一次一個循序）
              • deep-work（無人、無時間壓力）停在此 — 用時間換獨立性，保所有 lens
非 429 失敗（crash / timeout）→ retry ≤ 2（同 classifier 模式）
全失敗（serialization 仍 429，少見）→ 降級主 LLM 自審 + 顯式標記 fallback（警示獨立 review 丟失，非靜默）
```

**usage limit（1308）不是降並發信號**（user 09-05 裁定）：1308 是窗口制——能用＝窗口已重置，並發數量與之無關；處置只有「等 reset 再派原並發」（窗口時間戳在錯誤訊息內，見 model-routing spawn 失敗態表）；AIR-91 S3 起該 candidate 記入 DispatchTrace 並在 retryable-at 前排除（見上方消費側點 7——重選即 loop 違規）。**只有 429 持續才降並發**，且降並發時 dual-context（fresh＋primed）不砍成單側——複雜任務的審查結構用序列化保（一次跑一個但兩側都跑），不用降低 lens 數換速度。

**關鍵區分**：serialization 是**降並發的一步，不是降級**。降級（丟獨立性）只在 concurrency=1 還持續 429 才發生。deep-work（無人、無時間壓力）甚至可**預設低並發** —— 不急，何必冒 429 平行；用時間換獨立性，保所有 lens。

---

## Rule Freshness（spawn 時注入）

Rules 檔在 session 啟動時載入，但**更新不會傳播到已 spawn 的 agent 或執行中的任務**——agent 帶著 spawn 當下的 context 跑完全程。「它在 rules 裡」不等於「agent 會遵守」。**兩面分工**：main session 自身的 freshness（redeploy/slimming 後續作）歸 [context-management](../../rules/context-management.md)「Session freshness」——refresh 或 reset＋恢復主題材料；本節管 spawned-agent snapshot 面：

- 高頻被違反的規則（mock patterns、property patching）→ **spawn prompt 直接注入該規則摘錄**，不假設 agent 會自己讀 rules 檔
- 高風險 rule 更新後 → 下一個依賴該規則的任務前先 reset context（`/clear` 或重新載入 rule）
- 熱點規則值得在關鍵流程點（audit 角度、agent prompt 模板）重複出現，而非只靠單次載入

---

## 自檢清單

### Agent tool spawn 前

- [ ] 已查「並發上限」表確認——以將 spawn 的 agent 所在 tier 為準（[model-routing](../model-routing/SKILL.md) 並發表）；Agent **model 依角色 tier**
- [ ] **lite／機械角色任務 spawn 型別＝registry 角色**（內建 `general-purpose`／`Explore` 無 pin、繼承主 session 模型——lite 任務用內建型別＝旗艦跑機械段；唯讀探察／review 形態用內建 Explore 承接＝rule research/explore 列）
- [ ] 已印出 `[Agent] model=X, max=N, current=M`
- [ ] consequential dispatch 前已印出 `[Dispatch] unit=…` 完整 preview 行（派工前契約揭露；`[Agent]`/`[Bridge]` 是執行面回報，不可替代）
- [ ] 當前 Agent 數量未超過上限
- [ ] spawn 帶 `run_in_background: true`（前台僅限 <30s 短 probe **且 prompt 帶 `[fg]`**——見上「Spawn 預設背景」；省略參數已被 gate 自動轉背景）
- [ ] Prompt 包含足夠 context + 相對路徑 + rules-reminder 規則摘要（Agent 看不到 auto-loaded rules，必須在 prompt 開頭明確寫入：多行 `python -c` 禁 `#` 註解、`rg`/`fd` 取代 `grep`/`find`、`uv run` 前綴 Python、禁止 `sed` 修改 `.py/.md`、禁止 `$` shell 展開、輸出繁體中文、獨立工具呼叫同 block 批次發、改檔前先 Read）
- [ ] **寫檔類 agent** prompt 必注入三條：①禁 /tmp，產出留當前 repo/worktree；②寫不進指定路徑就回報「環境限制：我寫不進 X」，不可退 /tmp；③暫存集中 `.agent-tmp/`（post-build 清；夜掃兜底 `.agent-tmp/`/`.at-contexts/` 7d、`.review/` 30d）
- [ ] **🚫 spawned agent 禁寫記憶池面**（`.agents/memory*`——含 pool／inbox／memory-auto staging）——發現類內容以最終回報交回主 session，由主 session 走 consolidation（AIR-100 S-D）
- [ ] **若任務涉及 mock / PropertyMock / fixture**：prompt 主動注入專案 `tests/AGENTS.md`（legacy `tests/CLAUDE.md`）的 mock 規範段落摘要（agent 不會自己讀專案 instruction 檔，必須主動注入；見上方「Rule Freshness」）
- [ ] Uncommitted changes：需要 → 先 commit；Branch：不正確 → 先 checkout
- [ ] 失敗 Agent 的 worktrees 已清理（`git worktree list`）
- [ ] Agent 產出 commit 前需用戶確認（[outward-action-consent](../../rules/outward-action-consent.md)）

### 選擇平行模式時

- [ ] 互動式平行實作 → Agent tool + worktree
- [ ] 無偏差審查 → Writer/Reviewer 雙 session（開新 terminal）
- [ ] 無人值守 → Auto mode（`--permission-mode auto`）
