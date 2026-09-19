---
name: illustrate

description: "圖解技術概念、架構設計或流程 + 結構 viewport（SA/SD artifact menu：call graph/sequence/class slice/data-flow/boundary；city map/drill/drift detection，三時點 pre-EP/post-EP/post-build）。可指定 @目錄或 @檔案讓 AI 先讀再圖解，支援 console（即時）、md（寫檔）和 html（report shell 報告殼＋mermaid——AI 文檔產物〔EP/實作報告/@module/@dir〕的人類 viewport，opt-in）三種輸出模式。"
when_to_use: "Illustrate technical concepts, architecture, or processes. Also structure viewport via SA/SD artifact menu (boundary/data-flow/call-graph/sequence/class-slice) + drift detection at pre-EP / post-EP / post-build. Supports console (ASCII), md (Mermaid), and html (report shell + mermaid — human viewport for EP plan / implementation report / module / dir walkthroughs, opt-in) output. Regenerate diagrams from tracked .mmd sources when asked (shells are authored, not regenerated). Use with @dir or @file for code-based explanations."
---

# /illustrate — 智能圖解系統

> **受眾：layer 3 人類 viewport / B 軸**。產出**供人判讀的結構 artifact**（city map / 心智模型 / 重用枚舉 / 流程圖）—— 人用大原則判讀「結構撐得起嗎、在重造嗎、方向對嗎」。**不產機器 finding**（嚴重度 / file:line，那是 `/code-review` axis 3 的職責）。與 `/code-review` axis 3 共用 [arch-thinking](../arch-thinking/SKILL.md) skill 但**受眾不同**（人 viewport vs 機器 finding）—— skill 刻意中性，受眾由本命令（人）vs code-review（機器）決定。
>
> 受眾模型見 [AGENTS.md](../../AGENTS.md)「命令的受眾視角」（root CLAUDE.md wrapper 經 @AGENTS.md 同載入）；理論（A/B 軸、證據階層）見 [acceptance-evidence](../../rules/acceptance-evidence.md)。

## 輸出模式

輸出給人判讀的章節遵循[結論先行原則](../_common/conclusion-first.md)——先結論後 id／代碼。

| 模式 | 圖表 | 風格 | 適用 |
|------|------|------|------|
| **Console**（預設） | ASCII | 精簡（3-5 章，每章 3-5 點） | 即時討論、快速查詢 |
| **MD** | Mermaid（`skill: "mermaid"`） | 詳盡（多級標題、完整展開） | 深度分析、知識沉澱 |
| **HTML**（opt-in） | 報告殼＋mermaid（委派 [illustrate-html-mode.md](../_common/illustrate-html-mode.md)；殼生成分工〔decision 篩選敘事→vision 驗收〕＋機械底稿規則見該檔「殼生成分工」） | 展示級（報告殼＝sidebar 順序敘事；圖可 zoom/主題跟隨） | 分享 / demo / re-onboard / drift 審查／**報告殼**——AI 文檔產物（EP 計畫、實作完成報告、module 現況、目錄導覽、決策 viewport）的人類 viewport（`@ep`／實作報告／`@module`／`@dir` + html）。殼內圖**按圖選載體**（mermaid／HTML 塊——判準見 [diagram-selection](../diagram-selection/SKILL.md)） |

**執行鐵律**：Console 禁止 Mermaid 語法。MD 禁止 ASCII 圖表。HTML 是**寫檔模式**——僅明示 `html` 或增益判斷時觸發；Console 語境明示 html = 切換輸出模式（檔案交付＋路徑回報），永不 inline 渲染；渲染工具缺場 → 降級 MD Mermaid 並回報（細節見 illustrate-html-mode.md）。違反 = 指令執行失敗。

## 核心：4 mode（從使用者 use case 歸納，非內部能力）

> /illustrate 從**使用者日常開發 use case** 歸納 4 個高層 mode（意圖）。**mode = 意圖，能力 = 手段（跨 mode 共用）** — 能力（city map / 假設驗證 / diff / SA/SD artifact）服務 mode，不是 mode 本身（同一能力可服務多 mode）。

| mode | 意圖 | 典型情境 | 主要能力（手段）|
|------|------|---------|---------------|
| **A 設計決策** | 「這樣設計對嗎」 | 討論新功能 / 重構 / pre-EP | city map + 流程 + 重用枚舉（調 [arch-thinking](../arch-thinking/SKILL.md) skill）+ **邊界案例列設計替代** |
| **B 理解既有** | 「這怎麼運作」 | 接手 / 學習套件 / 除錯 | [artifact menu](../_common/illustrate-artifact-menu.md)：call graph / sequence / class slice / data-flow / boundary（default=boundary；非 freehand）|
| **C 審查驗證** | 「對不對 / 好不好」 | code-review 前 / EP 審查 / 重造偵測 / commit 前 | 語義 diff + [假設驗證矩陣](../_common/illustrate-deep-analysis.md) + city map |
| **D 溝通傳達** | 「畫給別人看」 | 文檔 / demo | Mermaid 圖（md 模式）|

use cases + 情境矩陣分析（服務 mode A/C 的**步驟**）見 [illustrate-analysis.md](../_common/illustrate-analysis.md)。結構 viewport 互動（drill）見 [illustrate-structure-viewport.md](../_common/illustrate-structure-viewport.md)。批次檔案分析（`@dir`，≥ 5 Agent 並行）跨 mode 通用。

## 現有程式碼優先原則

> **核心原則**：不管哪種情境，先讀現有程式碼再解釋。不理解現有架構，就無法判斷變更的品質。

| 情境 | 現有程式碼的角色 | 關注點 |
|------|----------------|--------|
| EP 審查（`@任務家/<task>/ep.md`——探測見 html-mode 放置學） | **Ground Truth** — EP 假設對不對？ | 依賴錨點、API 簽名、行號、架構假設逐一比對 |
| 變更審查（明示 diff / post-build drift） | **Baseline** — 改動融入得好不好？ | 語義 diff、架構一致性、下游缺口 |
| 一般圖解 | **Context** — 現有結構是什麼？ | 先理解再解釋 |

## 無參數行為

未提供任何參數時，**委派 [debrief](../debrief/SKILL.md)**（AI 改動理解簡報）——「改完 code 想理解改了啥」是理解意圖而非審查，理解簡報是 debrief 的職責（七段：意圖／行為黑盒子／前後差異／檔案地圖／波及缺口／驗證證據／認知誤差點；diff fallback 鏈兩邊一致，見 debrief input 段）。單一真理源在 debrief，本 skill 不重複展開變更理解的渲染。

## 使用方式

```bash
/illustrate                                    # 無參數 → 委派 /debrief（改動理解簡報）
/illustrate 微服務架構                         # Console 模式
/illustrate md Kubernetes 叢集管理              # MD 模式 → ai-analysis/reports/
/illustrate html @src/components/              # HTML 模式 → 報告殼（mode B 映射）
/illustrate html @ai-analysis/_tasks/<task>/ep.md  # HTML 模式 → 報告殼導讀（Report Shell；@任務家/<task>/ep.md——repo 任務家探測見 html-mode）
/illustrate @src/components/                   # 目錄分析
/illustrate md @src/ @tests/ --output "分析.md" # 自定義輸出
```

更多範例：[illustrate-examples.md](../_common/illustrate-examples.md)

---

## MD 檔案自動儲存

- **預設位置**：`ai-analysis/reports/`
- **自定義**：`--output <路徑>`
- **檔名規則**：單檔案 → `{name}-檔案分析.md`；目錄 → `{dir}-架構分析.md`；主題 → `{topic}-圖解說明.md`
- **備份**：目標檔案存在時加時間戳

---

## 智能並行處理

檔案 ≥ 5 時，Agent tool 並行處理（model 依 [model-routing](../../rules/model-routing.md) WorkUnitContract——平行分組＝execution floor 的 registry agents）：按關聯性分組 → 每組 spawn Agent → 整合結果。

平行處理架構：[illustrate-parallel-architecture.md](../_common/illustrate-parallel-architecture.md)

---

## pre-EP checkpoint（彈性、軟 gate）

> **核心理念**：illustrate 是討論到一定程度時的**結構催化劑**，不是固定流程節點。結構確認前移到寫 EP **之前** —— Clean Architecture 核心順序「先定 use case + 邊界，再寫細節」。

**非線性流程**（非剛性 spec→illustrate→ep）：

```
對話討論新功能 →〔提醒〕/illustrate 結構化提案 → 人判讀（撐得起嗎、在重造嗎）→ 直接 EP 或先 spec
```

- **EP 必備、spec 可選**：EP 是實作起點（必備，自足）；spec 是純輔助需求釐清（需求不明時前置，可選）
- **軟 gate（不硬擋）**：pre-EP 是**標註 + 提醒**，不強制擋流程。前移價值靠提醒（「結構還沒確認，建議先 illustrate」）而非硬性 gate —— 避免流程摩擦，保留前移價值
- **視角來源**：調用 [arch-thinking](../arch-thinking/SKILL.md)（分層/bounded context/use case 視角 §一 + 結構資料 §二）

**結構 viewport 三時點**（同一載體，三觸發點）：pre-EP（本段，軟 gate）/ post-EP（EP 審查模式渲染提案結構撐得起嗎，見決策流程）/ post-build（懷疑結構漂移或重造既有時，重畫 city map 比對）。

**drift spine**（post-EP / post-build 核心，回應「程式碼失控」恐懼）：SEED `git diff`（機械恆可用）→ GENERATE change-scoped graph facts（調 arch-thinking §二）→ BASELINE degradation ladder（① EP-claimed optional gold → ② last commit 機械主幹 → ③ HEAD~1 → ④ current-only）→ DIFF 5 signal class → RENDER overlay（**no-severity**：僅「this moved; you judge direction」，非 finding）。完整 spec見 [illustrate-artifact-menu.md](../_common/illustrate-artifact-menu.md)「Drift Overlay Spec」。

---

## 決策流程（mode 驅動）

> 從使用者 **use case 判斷 mode**（非內部能力觸發）。輸入（@ep / 無參數 / 主題 / @dir）是 mode 判斷**線索**（客觀輸入，非相容保留 — ai-guide 預設不考慮向後相容，演化性重構）。

```
用戶輸入 → 判斷 use case → mode?
  A 設計決策（討論新功能 / pre-EP / 重構 / 架構取捨）
    → 讀 code → city map + 流程 + 重用枚舉（調 skill）→ 邊界案例列 2-3 設計替代 + tradeoff → 渲染 → 人判讀
  B 理解既有（@模組 / 概念 / 除錯 / 學習套件）
    → 讀 code → 依方向問題從 artifact menu 選 artifact（default boundary）→ grounded 渲染 → 人理解
    → html：artifact 選型後走概念→載體映射（class slice 除外，見 illustrate-html-mode.md；載體判準見 diagram-selection）
  C 審查驗證（@ep / 重造偵測 / commit 前）
    → 讀 code → 語義 diff / 假設驗證矩陣 / city map → 渲染 → 人判讀
  D 溝通傳達（文檔 / demo / 主題）
    → 主題 → Mermaid（md 沉澱；分享情境建議 html——增益判斷：互動搜尋/focus/Present）→ 可分享

輸入判斷線索：無參數→委派 debrief；@ep→C（假設驗證）；@module／概念→B；主題+md→D；主題+html→D（mermaid/HTML 塊）；@dir+html→B（映射）；@ep／實作報告／@module／@dir + html 明示報告導讀→**Report Shell**（見 illustrate-html-mode.md 變體表）；架構/邊界討論→A
```

### 邊界案例的行動路徑分流（mode A 輸出指引）

mode A flag 邊界 / smell 時，給兩條行動路徑 + 取捨，**不替 user 預設**：

| 路徑 | 性質 | 適用 |
|------|------|------|
| **文件化契約** | 保守、快速、低風險 | 結構合理，只是契約隱性（把不變量 / 設計原則寫進 AGENTS.md）|
| **重構修正** | 根本、風險高 | 結構本身有 smell（繼承 / strategy / 重寫）|

兩條都擺出來讓 user 選——user 可能直覺朝重構想（要根本解），但文件化通常成本較低，可作為先手。

## 能力 survey 與下沉

> 能力位置 + 下沉標準（**跨命令共用才沉**；illustrate 特有留本體/supporting，避免過度下沉）。

| 能力 | 位置 | 下沉? |
|------|------|-------|
| city map / dep weight / 重用枚舉 / LSP 查證 | `arch-thinking` skill | ✅ 已沉（跨 illustrate/code-review/ep-review 共用）|
| 假設驗證矩陣（EP 審查）| `illustrate-deep-analysis.md` | ❌ 留（illustrate 特有）|
| 語義 diff / 缺口（無參數改動理解） | `debrief`（無參數委派，單一源在 debrief）| ✅ 已沉 |
| use cases + 情境矩陣分析 | `illustrate-analysis.md` | ❌ 留（分析步驟，特有）|
| drill / Phase 2 互動 | `illustrate-structure-viewport.md` | ❌ 留（mode A 互動）|
| call graph（函數級）資料生成 | `arch-thinking` skill §二 | ✅ 已沉（跨 illustrate/code-review/ep-review）|
| type structure（contract slice）資料生成 | `arch-thinking` skill §二 | ✅ 已沉（跨命令）|
| data-flow（靜態骨架）資料生成 | `arch-thinking` skill §二 | ✅ 已沉（跨命令）|
| artifact menu（5 artifact + drift overlay spec）| `illustrate-artifact-menu.md` | ❌ 留（illustrate 特有渲染）|
| drift diff（5 signal class）| `illustrate-artifact-menu.md` | ❌ 留（viewport framing）|
| drift rendering（Console/MD overlay + HTML compare）| `illustrate-structure-viewport.md` | ❌ 留（viewport 渲染）|

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [arch-thinking](../arch-thinking/SKILL.md) — 結構 viewport 能力來源（city map 資料/dep weight/Pattern Radar/LSP 查證/call graph（函數級）/type structure（contract slice）/data-flow（靜態骨架）；視角 §一、機械 §二；本命令渲染給人判讀）

---

## Supporting Files

| 檔案 | 何時讀取 |
|------|---------|
| [illustrate-parallel-architecture.md](../_common/illustrate-parallel-architecture.md) | 檔案 ≥ 5 需並行處理時 |
| [illustrate-deep-analysis.md](../_common/illustrate-deep-analysis.md) | 分析特定類型內容時（含 EP 審查框架） |
| [illustrate-analysis.md](../_common/illustrate-analysis.md) | use cases / 情境矩陣分析時（mode A/C 組合步驟） |
| [illustrate-examples.md](../_common/illustrate-examples.md) | 需理解各模式實際輸出時 |
| [illustrate-structure-viewport.md](../_common/illustrate-structure-viewport.md) | 結構 viewport / drill / pre-EP checkpoint 時 |
| [illustrate-artifact-menu.md](../_common/illustrate-artifact-menu.md) | mode B code 解釋 / drift checkpoint（5 SA/SD artifact + drift overlay spec）|
| [illustrate-html-mode.md](../_common/illustrate-html-mode.md) | html 模式觸發 / mode D 增益判斷 / **殼重生**（概念→載體映射、產物生命週期＋重生程序）|
| [diagram-selection](../diagram-selection/SKILL.md) | 畫圖前選載體（判準四問＋對照表＋跨載體共性——vision 契約/渲染判讀分離）時 |
| [illustrate-report-shell.html](../_common/illustrate-report-shell.html) | 建報告殼時複製＋填 slot（殼結構/視覺/互動單一源；slot 填法與三條硬約束見檔頭註解）|
