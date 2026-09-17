---
name: code-review

description: "深層思考代碼審查。/code-review [branch] [base]；<hash> 通盤審任務弧（逐段 commit 後整弧）"
when_to_use: "Review uncommitted changes, a feature branch, or a task arc (baseline-hash..HEAD after per-segment commits) using multi-axis methodology and deep-thinking (first-principles + second-level consequence tracing)."
argument-hint: "無參數審查 uncommitted / branch 名稱審查該 branch / baseline hash 通盤審任務弧"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Agent", "Workflow"]
---

# /code-review — 深層思考代碼審查

基於深層思考審查尚未 commit 的 code。不只是看改了什麼，更要讀相關程式碼確認**為什麼這樣改**。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [review-engine](../review-engine/SKILL.md) — 通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/審查模式判定規則/多層驗證）
- [code-quality profile](../review-engine/code-quality-profile.md) — code 六軸審查方法論（what to check；Security/Performance 軸的 checklist 亦在該檔，細節判斷屬 LLM 原生能力）

Workflow 執行協調：[workflow-review-pattern.md](../_common/workflow-review-pattern.md)（模式判定見 review-engine；多軸並行時的協調載體——載體由風險 profile 與協調需求決定，非 effort 門檻）

---

## 審查範圍

| 用法 | 實際執行 | 場景 |
|------|---------|------|
| `/code-review` | `git diff` + `git diff --cached` + `git ls-files --others --exclude-standard` | 審查 uncommitted（預設，含 untracked files；空/trivial 時見下方任務弧模式——**禁靜默以空範圍通過**） |
| `/code-review feat/xxx` | `git diff HEAD...feat/xxx` | 審查 feature branch |
| `/code-review feat/xxx main` | `git diff main...feat/xxx` | 審查 branch（指定 base） |
| `/code-review <hash>` | `git diff <hash>..HEAD` + uncommitted | **任務弧**：逐段 commit 後的整弧通盤審查（hash = EP baseline commit） |

**任務弧模式（逐段 commit 後的整弧審查）**：implement 的逐段檢查點（＋isolated worktree 弧的 pre-flight commit——共享樹不預先 commit，見 implement 平行模式）會讓變更在 build 中途落地，無參調用只剩尾段殘留甚至空 diff——逐 commit 或只看 uncommitted 都會漏跨段互動（大規模刪除段只有對照抽取段才看得出是遷移不是丟失）。

- **觸發**：① 明確傳 baseline hash；② 無參且 context EP／卡 Plan 記有 baseline（或殼頭可讀）→ 自動切弧模式（印 `[Code Review] mode=arc baseline=<hash>`）；無任務 baseline → uncommitted 模式；uncommitted 亦空 → 印 `[WARN] no diff（弧模式需任務 baseline）` 終止（fail-loud，同 post-build）
- **baseline 來源**：EP 整合策略的 `baseline: <hash>`（記錄：execution-plan 建 EP 時；implement 階段 1 補記）或卡 Plan 所記（無 EP standalone 弧）——優於 merge-base 推導：同 branch 可能混入他任務 commits，拓撲邊界 ≠ 任務邊界；跨 session context 無 EP 記憶 → 從 Report Shell 殼頭部讀（任務家 `*/index.html`——探測見 [illustrate html-mode](../_common/illustrate-html-mode.md)；聲明 EP 路徑＋baseline hash——hook 1 起攜帶，機制見 [post-build](../post-build/SKILL.md) 階段 0）
- **非本任務 commits 註明**：`<hash>..HEAD` 範圍內不屬本 EP 的 commits 列進 reviewer prompt（避免誤判 scope；diff 連續仍涵蓋它們）
- dual-context 兩側吃同一份 diff——範圍錯則兩側同瞎，範圍判定先於 spawn

**Untracked files 處理**：新檔案沒有「變更前/後」可比對，審查時以完整檔案內容為對象（等同 diff against `/dev/null`），重點檢查架構一致性、命名慣例、與既有程式碼的整合點。

---

## Lint 預檢

對 modified files 執行 `ruff check --select F401,PLC0415`，結果併入審查報告。

| Rule | 抓什麼 | 唯一合理例外 |
|------|--------|-------------|
| F401 | unused import（LLM 重構後殘留） | `__all__` 用途、optional dependency try/except |
| PLC0415 | import 不在檔案頂部（LLM 偷懶） | circular import avoidance |

---

## 審查模式選擇

review 執行預設（force 獨立 / model 預設）見 [review-engine](../review-engine/SKILL.md)「review 執行預設」—— code-review **預設 spawn 獨立 agent**（與其他 review 命令一致，force 獨立；取消 Main LLM 自審 — 實證：獨立 agent 抓自審盲點）。**派發形態由風險 profile 決定**（[review-engine](../review-engine/SKILL.md)「審查模式判定規則」——本命令消費 S1 配置，不重建派工數量判準；並發容量〔[model-routing](../model-routing/SKILL.md) 並發表〕是上限非配額）。下方為本命令的六軸啟用配置（C 已廢除，見下方 C 段）：

**派發前觸發檢查（各形態共用）**：主審先讀 [arch-thinking §二觸發表](../arch-thinking/SKILL.md)，按 diff 判定命中項，將命中配方與檢查責任放入下列 reviewer 的必讀／檢查清單。不因未達檔數門檻丟棄檢查；沒有命中才按一般啟用軸門檻。

| 已選派發形態 | 命中檢查的承接者 |
|---|---|
| 單一 fresh-eyes（ordinary） | 該 fresh-eyes reviewer |
| fresh＋intent（boundary） | fresh-eyes 與 primed 的 prompt 都含命中配方；意圖材料仍依 B 段分開餵 |
| Workflow | Architecture 軸；超出並發上限時合併至既有 agent，保留檢查責任 |

派發形態依 review-engine 風險 profile 判定（ordinary→單一 fresh-eyes context；boundary→分離 fresh＋intent，見 B 段配置表）；觸發表只增加檢查責任，不另改派發模式。

**A. Workflow 載體**（boundary 多軸並行的協調選項，非 effort 門檻）：

使用 Workflow tool，參照 [workflow-review-pattern.md](../_common/workflow-review-pattern.md) 腳本骨架。

| Workflow Phase | 說明 | Agent 數量 |
|----------------|------|-----------|
| Review | 平行 spawn 軸 agents（啟用軸見下表） | 由 profile 配置與並發容量決定（上限非配額） |
| Verify | 分級 verify node：Important+ 錨點批次（單一 lite agent）→ Critical 3 verifier + ≥2/3 quorum（配置單一源見 [workflow-review-pattern](../_common/workflow-review-pattern.md)） | 1 批 + 3 × critical |

**啟用軸**：

| 軸 Agent | 審查項目 | 啟用條件 | 優先級 |
|----------|---------|---------|--------|
| Correctness | 邏輯 bugs、邊界案例、測試充分性 | **always** | P0 |
| Readability & Simplicity | 命名、控制流、避免過早抽象 | **always** | P0 |
| Architecture（axis 3，調用 arch-thinking skill） | 設計模式、模組邊界、重用、dep weight；**diff 含 test files 時加掛測試架構六項**（定義源 [code-quality profile](../review-engine/code-quality-profile.md) ### 3「測試架構六項」） | 變更 ≥ 3 files 或 arch-thinking 觸發表命中；**diff 含 test files** | P1 |
| Security | 輸入驗證、權限檢查 | diff 含 HTTP/auth/credential | P1 |
| Performance | N+1、無界操作 | 變更 ≥ 5 files | P2 |
| Capability Coverage | Capabilities 行為覆蓋 | full／standard 變更 | P2 |

啟用軸數超過並發容量 → 從低優先級（P2 起）合併至前一個 agent（不丟棄任何軸——合併是容量約束下的分工手段，非固定派滿）。

**docs mode（純文檔變更）**：Security / Performance 軸 N/A（文檔不涉及 HTTP/auth/credential、無 N+1/無界操作），跳過此二軸避免噪音；Correctness / Readability & Simplicity / Architecture / Capability Coverage 仍適用（文檔正確性、可讀、結構、行為覆蓋）。docs mode 觸發判準見 [execution-plan.md](../execution-plan/SKILL.md) docs mode 段。

**docs mode 必跑：前瞻 phantom 偵測** — 文檔 diff 不只回溯查「既有路徑還在嗎」（刪了 module 後 doc 是否仍引用 = 回溯），更要**前瞻查「這次編輯有沒有新增指向虛無的引用」**：diff 中每個**新增**的 symbol/path/link，用 rg/LSP 驗證目標存在。真實案例：清理日一個「修 phantom doc」的 commit 反而**新增** phantom（寫了不存在的 routing 機制）——只回溯查會漏掉這種前瞻引入；教訓通用（phantom 偵測須雙向：回溯 + 前瞻）。回溯查是 `/doc-health` 的 X-cap-path，前瞻查是本處。

每個 Review agent prompt 包含：
- `git diff` 範圍
- 該軸的檢查項目清單（如上表）
- 相關檔案路徑（必讀）
- 方法論引用（code-quality profile；Architecture 軸引用 arch-thinking（視角+機械））
- rules-reminder 規則摘要（Agent 看不到 auto-loaded rules）
- CR 接線查證段（硬性；[review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」——Explore＝CLI 形態）
- schema: DimensionVerdict（定義在 workflow-review-pattern.md）

Workflow 完成後回傳 `{confirmed, stats}` → Main LLM 合成 results → 分三級（Critical/Important/Suggestion）→ 消費端影響檢查 → label-vs-diff 驗證 → commit message 產生。

印出確認：`[Code Review Mode] profile=<ordinary|boundary>, carrier=workflow, legs=N`

**B. Agent 載體**（**預設 force 獨立**；判定條件見 [review-engine](../review-engine/SKILL.md)）：

**context 配置由風險 profile 決定（舊「變更 ≥ 3 files」檔數門檻廢除——可觀察變更語義決定，單一源 [review-engine](../review-engine/SKILL.md)「審查模式判定規則」）**：

| 風險 profile | 配置 |
|--------------|------|
| **ordinary**（無邊界觸發的一般變更，含小型 diff） | **單一 fresh-eyes agent**——fresh-first 順序覆蓋：diff/source 自身 merits（smell）→ 正確性與驗證 → 需求對照；**單 context 順序覆蓋不是 fresh/primed 雙 context 等價品**（明示語義見 review-engine 執行預設點 4） |
| **boundary**（public API、跨 context invariant、money/risk/security、控制面 authority/gate 變更；條件不明同此） | **Dual-context 雙審查者**：平行 spawn 兩個**信念環境不同**的 agent（互補盲點，非 quorum 印證——quorum 對共同盲點無效，刻意讓兩 agent 前提不同）： |

| Agent | 定義 | context（spawn prompt 餵） | 抓什麼 |
|-------|------|---------------------------|--------|
| fresh-eyes | `agents/roles/code-reviewer.md` | **只餵 diff**，不給任何意圖文件 | 實作層真相：邏輯錯、邊界、silent regression、幻覺 API（不被作者意圖合理化） |
| primed | `agents/roles/code-reviewer-primed.md` | diff + EP + delta_tour 對照（若有，見下）+ 模組 AGENTS.md Capabilities + `dependency-graph.md`（若有） | Type A intent drift：意圖對齊、架構契合、測試精簡且完整、YAGNI↔過度工程光譜 |

- **context 差異在 spawn prompt，非 agent 定義**（ZCode subagent 自動注入 AGENTS.md，「空 context」不可能全空；可控制的是不餵 EP/架構文檔）
- **spawn prompt 必含 CR 接線查證段（硬性）**：fresh-eyes 與 primed 皆含（registry agents＝MCP 形態；逐字照 [review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」CR 段）
- **測試架構六項注入（v3.1——diff 含 test files 時）**：fresh-eyes 與 primed 兩側 spawn prompt 均注入六項（拓撲 vs blast radius／層級平衡／符號≠路徑／evidence fidelity／shared dependency／耦合面——定義源 [code-quality profile](../review-engine/code-quality-profile.md) ### 3「測試架構六項」，本處只 wiring 不重複定義）；primed 額外拿 EP 凍結 TC（測試規劃段）作 context。**排除面**：翻譯忠實度（test↔TC 逐條對帳）不歸軸B——歸 [audit-test](../audit-test/SKILL.md) TC 契約對帳（域 2 第一 gate；軸A 機械對帳）
- **delta_tour 對照（若 repo 可跑 code_reality——偵測單一真相源見 [code-reality](../code-reality/SKILL.md)）**：**僅弧模式（code 已 commit、HEAD 越過 EP baseline）產出**——spawn primed 前對當下 HEAD 跑 `code-reality snapshot --repo <repo>`（呼叫形態：`code-reality <tool> --repo <repo>`），與 EP baseline snapshot（implement 階段 1 落下；定位＝EP baseline hash8 → `<repo>-<sha8>.json`，`--label` 僅入 `_meta`；**snapshot 身份與 EP baseline 分開記**——消費實際存在者，snapshot 晚於 baseline〔resume 形態〕時明示對照只覆蓋該區間）對跑 `code-reality delta_tour <a> <b> --ep <ep.md> --repo <repo> --out-dir .agent-tmp/`（**臨時自產不持久**——不寫 `.tours/delta/`：持久版產點＝post-build hook 2 ask-once〔demand-driven，user 確認才產〕、無 post-build 弧＝implement 階段 6 fallback 同語義；`.tours/delta/` 進 git），其 `.tour` description（宣稱對照三態＋實際變動模組＋退化/跨面 pair 自動警示；json 中間產物不落盤）併入 primed 餵料——intent drift（Type A）從 LLM 推導升級為機械底稿（宣稱抽取只認特定模組路徑前綴，宣稱欄 NONE ≠ EP 無宣稱——範圍見真相源）。**HEAD == baseline（uncommitted 審查）→ 不跑**：同 sha 對跑＝零差異假陰性，且此時對 baseline sha 跑 graph 刷新＋snapshot 會以 working-tree 修改覆寫 baseline sidecar；印 `[WARN]` 退回純 LLM 對照。snapshot 報 stale WARN → 視同缺報告跳過（stale snapshot 照寫、基於舊原料）。缺 baseline snapshot 或未裝 → 跳過不阻擋。工具用法真相源：[code-reality](../code-reality/SKILL.md) skill
- **無 EP 時降級規則**（dual 情境）：EP 是 primed 側的意圖合約核心；無 EP（跨 session resume、非 build 場景）→ 降級單 fresh-eyes agent 並印 `[WARN] no EP for primed context`（primed 缺 EP 仍跑 = 架構契合/完整度光譜可審、意圖對齊空轉，findings 噪音可能多於信號）
- **findings 合併**：同 file:line 去重；**矛盾不裁決**——標 `conflict` 欄（兩方意點並列）交 `/judge-review` 裁決層；合併/衝突規則真相源見 [review-engine](../review-engine/SKILL.md)「fresh＋intent 分離編排」（單一源＝[workflow-review-pattern](../_common/workflow-review-pattern.md)「findings 去重與復用判準」）
- **Important+ 錨點驗證（浮出前）**：合併後的 Important+ findings 先交 lite-verify **批次**錨點驗證（file:line 存在、符號存在、引用原文屬實——清單式一次 spawn，非 per-issue）；錨點不實的 finding 退回不浮出。**驗證≠裁決**：屬實性（機械/lite）與成立性裁決（judge-review/full）分離——本載體（B 段）不 spawn per-issue 對抗 verifier（成本爆炸；Workflow 載體的 Critical quorum 走 [workflow-review-pattern](../_common/workflow-review-pattern.md) 分級 verify node）
- **primed instruction 檔適用範圍**：primed 側審 instruction 檔合規時，某檔只適用**同路徑或祖先路徑**的 instruction 檔（AGENTS.md 為主）；**最近者優先、子層覆寫上層**（本弧新決策——源方法論無此語義，與既有 per-layer instruction 階層慣例對齊）——防拿上層泛用規則審下層已覆寫慣例的系統性誤報

印出確認：`[Code Review Mode] profile=<ordinary|boundary>, carrier=agent, legs=single|dual`

**C. Main LLM 模式 — 已廢除**：取消（force 獨立 — 與其他 review 命令一致）。理由：[acceptance-evidence](../../rules/acceptance-evidence.md)「同 LLM 審自己 = 零獨立性」；實證獨立 agent 抓 changeset 作者漏的 drift（本 session dogfood：fresh-eyes agent 抓 3 reference 層錯、code-review agent 抓 5 跨檔 drift — changeset 作者自審漏的，獨立 agent 抓到）。

---

## 六軸審查 + 深層思考

> **六軸定義**（Correctness / Readability & Simplicity / Architecture / Security / Performance / Capability Coverage）見 [code-quality profile](../review-engine/code-quality-profile.md) — **單一真相源**（完整定義沉 skill）。本命令：上方啟用軸表的「審查項目」是 agent-prompt 啟用條件 + 摘要（agent 看的），非定義重複；另定義執行方式（top-down、axis 3 接線、Capability Coverage 審查細節、深層思考）。
>
> **Correctness 三層**（消歧）：**lens**（base perspective，所有 review 共用視角）見 [review-engine](../review-engine/SKILL.md) 點 4 ③；**checklist**（what to check 細節）見 [code-quality profile](../review-engine/code-quality-profile.md) ### 1；本命令上方啟用軸表是 **agent-prompt 摘要**（非定義）。

**top-down 審查順序**：axis 3（Architecture，結構）先於細部正確性（Correctness 等）— 結構錯了正確性審白費。

### axis 3：Architecture — 調用 [arch-thinking](../arch-thinking/SKILL.md) skill
- **機器產 finding（A 軸）**：city map / dep weight / 重用枚舉 / LSP 查證 / call graph（函數級）/ type structure（contract slice）/ data-flow（靜態骨架），調用 skill 取結構資料 → 產 finding（變更融入既有結構？在重造？）
  - **code-reality（若在場）**：axis 3 的 impact radius / 跨檔 callers / affected flows 用 `impact_radius` / `callers` / `affected_flows` 機械產（取代手動 LSP 逐層追蹤）；change scoping 用 `detect_changes` + `get_minimal_context`（只讀 impacted nodes）。**CR 查詢分層**：主 session 與 spawned registry agents（code-reviewer 族——CR MCP 白名單已掛）**MCP 優先**（MCP `callers`／`impact_radius`／`affected_flows`／`detect_changes`／`get_minimal_context`）；spawn generic agent（無白名單）的 CLI 形態與硬性必含規則＝[review-engine](../review-engine/SKILL.md)「spawn prompt 工具紀律」CR 段（單一源）。分工 + GATE 見 [cr-query](../cr-query/SKILL.md)。
- **條件機制 activation**：先依 [arch-thinking §二](../arch-thinking/SKILL.md) 觸發表選配方；刪除整檔／class／method、修缺陷或 refactor 遷移邏輯要查補償關係；涉及 mutable state／invariant 或 ownership 變更再加寫入路徑盤點。此義務不受變更檔數門檻豁免；沒有 state 的變更不硬造 writer。
- **受眾明文**：axis 3 與 `/illustrate` 用同一 skill，但 axis 3 產**機器 finding**（A 軸）、illustrate **渲染給人判讀**（B 軸）

### Capability Coverage — 滿足 Capabilities 描述嗎？

**checklist 單一真相源在 [code-quality profile](../review-engine/code-quality-profile.md) ### 6**（涵蓋行為、diff 對應、入口指向 library 非 scripts/、simple 變更跳過）。本命令僅定義執行時機：full／standard 變更時審查，simple 變更（bug fix）跳過；審查題材為模組 instruction 檔（AGENTS.md 為主，legacy CLAUDE.md）Capabilities 表格 + EP 段落引用 + 「消費場景」情境（happy path、錯誤操作、邊界、效能期待差異）。

### 深層思考（決策證據與後果）
- **讀相關程式碼**：不只看 diff，讀取被修改檔案引用的其他模組
- **確認實作合理性**：為什麼這樣寫？有沒有更簡單的方式？
- **驗證假設**：修改是否基於對現有程式碼的正確理解？
- **追蹤後果**：這個修改的下游影響是什麼？依賴模組是否受影響？
- **審查者自證**：提出問題前必須查證宣稱（LSP 查證方法 + 自我否證義務：找不到 ≠ 不存在）— 完整方法見 [review-engine](../review-engine/SKILL.md)

決策方法見 [deep-thinking](../deep-thinking/SKILL.md)；摘要內容併入 findings／證據欄位，不另加固定分析模板。

---

## 消費端影響檢查（API 變更 + 刪除）

不向後相容原則下，API 變更或**刪除**必須同步更新所有消費端。**刪除是最高風險**——「零 caller」是 no-impact self-claim，須獨立全消費端驗證，不採信 commit/EP 自述（見 [acceptance-evidence](../../rules/acceptance-evidence.md) Claim→Evidence→Trust「刪除/死碼自述同理」）。

**全消費端列舉的 what-to-check 真相源在 [code-quality profile](../review-engine/code-quality-profile.md)「Dead Code Hygiene」**（LSP findReferences + rg scripts/lab/configs + 動態派發 + import 測試）——本節是 Main LLM post-flow 步驟的執行點，不重抄清單（避免 single-source drift）。切記消費端**不只 demo/poc**：**scripts/、lab/、saved config** 是清理日 over-deletion 的典型盲區。

---

## 架構文檔 ripple 提醒（結構變更 → 文檔）

> 補盲區：消費端影響檢查看 **code consumer**（API/刪除 → scripts/lab/config）；本節看 **arch doc consumer**（結構變更 → 架構文檔）。code-review 只 **flag 提醒**，不做 sync。

偵測 structural signal（新/移/改名 module、跨模組 import edge 變、觸及 hub/ripple component、新抽象層；非 file-count）→ 產 finding 提醒檢查架構文檔（`dependency-graph.md`（若有） / 模組 AGENTS.md 架構段 / `SYSTEM-MAP.md`），**每個 finding 指向其 owner tool**（what-to-check 真相源在 [code-quality profile](../review-engine/code-quality-profile.md)「Architecture Doc Drift Reminder」，不重抄——single-source drift 防護）。

**為什麼獨立成節**：`dependency-graph.md`（per-repo opt-in）無 build-time owner（人工策展，同 `architecture.md`），是架構文檔最易 silent drift 的；axis 3 被「≥3 files」gate 擋住，會漏 1-file 高 ripple 改動（如改 hub module 的單檔），故獨立、signal-triggered 接住。

---

## 輸出格式

問題分三級（Critical/Important/Suggestion 的定義 + 信心水準標註）見 [review-engine](../review-engine/SKILL.md) 嚴重度框架。

每個發現包含：`檔案:行號`、問題描述、修正建議、信心水準（confirmed/evidence-based/inferred）。

---

## Finding 呈現

finding 預設留在審查報告/對話，供用戶 `/copy` 搬到實作 LLM（**人主導工作流**，不靠持久化追蹤）。**跨命令自動化場景**（接 `/judge-review`/`/followup-review`）才寫 `.review/<branch>.md`（Finding Record 表格，欄位見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md)，header identity 含 scope／review_profile／coverage 三欄）—— code-review 立場 optional（接 `/judge-review`→`/followup-review` 鏈才寫）；一旦進入該鏈，judge-review/followup-review 預設讀寫持久化（它們即此「跨命令自動化場景」，故二者步驟內固定讀寫、非再條件判斷）。寫入時 **Important+ 每條附驗證式**（可機械複驗的 rg 命令／pytest case——judge 裁決與 followup 驗收共用同一驗證基準）。`/commit` 階段 6 成功後清除。

```
## Code Review Findings — <branch>

| ID | 嚴重度 | 檔案:行 | 問題 | 建議 | 狀態 | 決策 |
|----|--------|---------|------|------|------|------|
| F1 | 🔴 critical | src/foo.py:42 | ... | ... | open | — |
```

Suggestion 級留在報告即可,不持久化(避免噪音)。

**junk tag**：finding 屬「疑似 AI 亂加／junk／scope creep」類（無對應 UC 的加料、防禦性冗餘、越權 scope）→ 問題欄前綴 `[junk]`——這是 post-build 收尾報告 `smell=` triage 欄的訊號源（消費端語義在 post-build；此處只標記不展開）。

---

## Commit Message 產生

審查完成後，基於已分析的 diff 直接產生 commit message。**格式 / 語言規範見 [commit.md](../commit/SKILL.md) 階段 4 — 單一真相源**（task #10：避免雙重定義 drift）。**跨命令自動化場景（post-build 編排）略過本段**——apply 後 message 即過期，最終命名屬 `/commit`；standalone code-review 保留（便利用途）。

**settings.json permission 同步檢查**（收尾步驟，AIR-42.1 遷入）：本次審查/修正新建或改名了 skill 時，檢查 `settings.json` allow-list 是否同步新增對應 skill permission——allow-list 同步是高頻漏步（skill 定義與 permission 在不同檔、無自動關聯）；機械防線＝順手跑 `/sync-sources` 的 `skill_allowlist_coverage` invariant（集合比對抓漏，2026-08-24 實例抓到 5 個漏加）。

**type 對應審查結論**（code-review 特有，映射審查發現 → type）：

| 審查判斷 | type | 說明 |
|----------|------|------|
| 新功能、新模組 | `feat` | 新增能力 |
| 修正邏輯錯誤、安全問題 | `fix` | 修正既有問題 |
| 架構調整、模式統一 | `refactor` | 不改行為的結構改善 |
| 效能改善 | `perf` | 回應 Performance 軸發現 |
| 測試補充 | `test` | 回應 Correctness 軸發現 |
| 文檔、instruction 檔 | `docs` | 文檔同步 |

**Label-vs-diff 一致性驗證**（產生後必跑 — message 是 claim 非 output）：commit message 的 type 與「無行為變更」/「行為變更」宣稱必須與 diff 語意一致。message 不只是從 diff 產出的 artifact，也是一個要被驗證的 claim。不一致 → flag 並重新產生：

- **「無行為變更」/`refactor` 但 diff 含行為變更**：control-flow / error-path / 值 / validation / 預設參數改動，**不是**「無行為變更」（真實案例：清理日 commit 標「無行為變更」但實新增 CHARTING 欄位 + 改 validation；另一 commit 把 crash 改 silent skip 也標「無行為變更」——自述反映「低風險」意圖，非事實）。
- **`fix` 但實為 tuning**：`fix` = 修正違反 spec 的缺陷；調整 spec 內的參數（預設值、週期、閾值）是 tuning，不是 fix（真實案例：參數 25→10 標「fix 對齊 spec」，但 spec 也是 25，實為 tuning 決策；教訓通用：別把 tuning 包裝成 fix）。
- **`refactor` 夾帶 correctness fix**：主體是 refactor 但 diff 含真實 bug fix → 拆 commit 或改 type（避免 fix 被埋在 refactor 型 commit，未來 git bisect 漏）。

**產生時機**：審查結論為「無 Critical 問題」或「用戶確認 Critical 可接受」時才產生。有未解決 Critical 問題 → 只輸出審查報告，不產生 commit message。

---

## 流程位置

> **canonical review flow（詳細）以本檔為單一源** —— 其他命令畫 flow 須引用此處、不重畫（防 flow drift；機械追蹤見 [/sync-sources](../sync-sources/SKILL.md)）。skills/CLAUDE.md 的 review-pipeline recipe 是高層概觀，非重畫。

```
/spec（純輔助·需求釐清，可選）→ /execution-plan（含 EP Review；定稿生 Report Shell〔hook 1〕＋EP 落任務家 <task>/ep.md）→ [/ep-validate] → /implement（含 Agent Review）→ /post-build（收尾鏈編排：/code-review（六軸含 axis 3 結構 = arch 吸收，top-down，含 commit message）→ /judge-review（一次）→ 修正迴圈 → consistency → metadata-sync → 殼 refresh〔hook 2〕；可拆開單跑）→ /commit
```

後續：用戶確認 commit message → `/commit` 捷徑（跳過階段 2 Git 狀態分析；保留 2.7 POC/Demo 處置閘門＋2.8 Finalization 對帳閘門；見 [commit](../commit/SKILL.md) 捷徑模式）

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始程式碼審查"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「審查完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```
