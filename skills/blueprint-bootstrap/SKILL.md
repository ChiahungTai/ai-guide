---
name: blueprint-bootstrap
description: "Blueprint 知識庫建置程序——人讀合成視角的骨架＋半滿＋🤖/👤 狀態標記（誘導人類-LLM 協同完成），含 callstack 場景敘事生成（斷點③解法——graph/code 結構→AI 草擬→人審；產出即 tour-bootstrap chain 層輸入）。既有 blueprint 走 audit 模式（drift 盤點不重建）。"
when_to_use: "使用者說「幫這個 repo 立 blueprint 骨架」、新 repo 冷啟動要人類 onboarding 視角（instruction-init 之後）、要產 callstack 場景敘事文檔、或既有 blueprint 要 drift 覆核時。"
argument-hint: "<repo-root>（要建置的 repo；省略即 cwd repo）"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]
---

# Blueprint Bootstrap（blueprint 知識庫建置程序）

一句話：使用者說「**幫這個 repo 立 blueprint 骨架**」→ 產出半滿 blueprint 知識庫（骨架＋狀態標記＋誘導問題）＋（指定時）callstack 場景敘事系列 → 使用者策展演化；callstack 產出＝[tour-bootstrap](../tour-bootstrap/SKILL.md) 場景層的輸入。

**定位**：軌道②人類 viewport 的 **scaffold**（工作區非成品）——骨架不偽裝完成。與機器導航分工：[instruction-init](../instruction-init/SKILL.md) 產 AGENTS.md 群（blueprint 的真相源輸入之一）；與 tour 分工：blueprint 先成熟 → tour 後消費（callstack 文檔餵 chain_tour，每份 md → `.tours/arch/<族名>/` 一族）。**不併 tour-bootstrap**——載體契約（治理文檔 vs `.tour` corpus）、生命週期（消化重編人類策展 vs 工具重產禁手改）、工具層三切面異質。

## 前置偵測（決定模式）

| 偵測 | 有 | 無 |
|---|---|---|
| `<repo>/ai-analysis/blueprint/` 實質內容 | **audit 模式**（見下——不重建） | fresh（本程序） |
| AGENTS.md 群（instruction-init 產物） | 半滿草擬的真相源輸入 | 建議先跑 instruction-init |
| `.tours/` corpus | 盤點形態（前門／族結構）；既有輸入文檔用 pointer 收攏不搬移 | — |

## Fresh 程序（五步）

1. **盤點（機械）**：AGENTS.md 群／SYSTEM-MAP／dependency-graph／架構文檔／既有 ai-analysis 產物。結構性列舉以 `ls`/fd 對齊，subagent 報告只是理解素材非列舉來源。
2. **骨架生成**：目錄結構＋`README.md`（區塊導航＝**問題→入口**＋讀者路徑：onboarding 5 分鐘／開新設計先盤 UC／排研究工作）＋治理 `AGENTS.md`——**真相源映射表**（檔案×真相源×drift 速度×更新時機）、更新紀律（消化重編非機械 patch、單一真相不重複、退役制 `_done/`、狀態宣稱帶出處）、對齊覆核流程（arc 收尾錨定 git log 觸發，**含 callstack-plan 差異盤點**——UC-B→UC-A 回填鉤子，細則見生成章「新功能回填」）。區塊分類參考：架構／UC 矩陣／營運地圖／研究循環／策略方法論／領域哲學（哲學類用 symlink 指向單一真相，不複製）。模板從 mosaic `ai-analysis/blueprint/` 抽象。
3. **半滿草擬（🤖 標記）**：AI 立即填可推導部分——架構結構段（from code-reality graph（index 在場時）／既有 dependency-graph／snapshot（若有））、營運 UC 骨架（from Capabilities 掃描）。**空清單誘導力弱、半滿文檔誘導力強**（人傾向補完非開頭）。
4. **👤 標記＋誘導問題預埋**：需人類意圖的 section（核心假說、需求全集缺口、策略方法論、領域哲學）標 👤＋預埋具體誘導問題（例：「核心假說是什麼？沒有它會怎樣？」「需求全集的分層與缺口？」）。**成功判據＝正確留白，不是重現內容**——fresh run 若「補出」洞察層內容即失敗（編造非意圖）。
5. **更新鉤子接線＋停點**：鉤子掛既有流程（build 5a 結算→營運地圖、arc 收尾→對齊覆核＋callstack-plan 差異盤點（見生成章「新功能回填」）、開新設計→UC 盤點）——誘導靠流程被動觸發不靠人想起，此為防骨架淪為永久空清單的唯一可靠機制。初稿即**停**：blueprint 是人類 viewport，AI 不代終審。

## callstack 場景敘事生成（斷點③解法——tour-bootstrap 場景層上游）

**何時**：**獨立觸發**（「幫這個 repo 生成 callstack」）——本章高成本（agent 群 ~150M token、牆鐘 ~2h——單 session 可能超出當日 token 上限），骨架流程走到此處＝**停點報價**（兩模式並列），不自動跑。輸出目錄 `ai-analysis/blueprint/callstack/`——**一律無版號**：世代交替＝舊版退役 `_done/`（標籤帶世代）、新版原地寫回 `callstack/`；版號並行目錄僅當新舊 code 並存跑且兩份地圖同時活消費（罕見）。mosaic 既有 `callstack-v1/` 屬歷史遺留——其 v2 cutover 也是退役路線，**不是** `callstack-v2/`。骨架的 callstack 區塊狀態四態：📋 未枚舉→📋 已枚舉（plan 在）→🤖 逐鏈生成中（分批）→✅。

**新功能回填（UC-B→UC-A 交接）＝盤點入 plan、生成仍獨立觸發**：功能 arc 收尾時盤點本 UC 對素材的影響——①新機制/入口/流程→plan 加一行；②實質改動既有鏈→標待重生成；③參數調整/內部重構/bug fix→不動（bug 知識歸 delta 與既有鏈⑥不變量段；步驟 0 邊際值與三軌過濾照套）。提示掛人必經流程點、**報庫存不催行動、附量級報價**：post-build 收尾報告列「菜單積壓」（機械＝plan **成鏈行數**（①-③ 軌行；④索引行不計）− `callstack/` 既有 md 數）；EP 段落 0 全域研究列待生成行。

**格式契約（chain_tour 機械解析——寫錯＝場景落空）**：
- 場景＝**含樹狀幀行（`├`/`└`）的 code block＋最近前置標題**（標題即場景名/tour title）
- 幀行＝函式名＋`path:line` 錨＋`  # ` 職責附註——**`#` 前須雙空格**（parse_frames 的 partition 條件 `"  # "`；單空格或無 `#` 會讓職責併入 ident 判定、污染 graph 重錨——M2 實證：單空格形態致 not-in-graph 偏高）；幀 ident 一律 call-shaped `fn()`——ident 擇取偏呼叫狀、其次 longest-wins，裸 `Type::method` 會被更長的 struct 名搶走、錨到 struct 定義行（NT 實證 moved 1→19，補 `()` 歸零）；depth 由樹狀縮排推導；幀 DFS 序＝步序
- 錨副檔＝`.py`／`.rs`（`.pyi` stub 是宣告層不入錨——跨縫幀走 boundary 第二錨，見生成程序步驟 2）；無錨幀（launchd/shell／外部路徑／撞名）會被跳過並記原因分佈——屬設計非錯誤

**每份文檔模板**（callstack-v1 實證七段完整形態——按鏈型態裁剪，如純資料鏈無入口總表；audit 盤點不以七段齊全為 drift 基準）：①檔頭 blockquote（讀者／定位／行號快照宣告／交叉引用）②入口總表（launchd／CLI／test 誰觸發＋**環境前提與警語**——本機前置／feature gate／fallback 鏈；NT 實證：madsim 開關、雙 venv、feature 靜默縮減、RPC fallback panic 為 ops 鏈最有價值段落）③主 call stack 樹（**場景分棵**）④分層敘事（關鍵函式／錯誤路徑／IO·state 副作用）⑤資料轉換邊界表（時區／單位／編碼在鏈上哪點變換）⑥不變量與陷阱（docstring 教訓）⑦符號速查表（symbol→連結按層分組）。

**檔名**：每篇＝英文 kebab slug（grep/CLI 友善）；corpus 族名與檔名**解耦**（族名＝人類標題，規範在 [tour-bootstrap](../tour-bootstrap/SKILL.md) 步驟 2）——兩者僅經 manifest sources 連結。

**生成程序**（callstack-v1 反推——16 篇／24 模組實證）：
0. **重複度盤點（前置裁決——燒錢的是生成非枚舉）**：比對 repo 既有文檔群（docs／concepts／how_to）×既有 corpus 與將生成鏈——**edu 軸須證明邊際值**（文檔極完善 repo 直接生成流程鏈＝同源重複——NT dogfood：docs 極完善＋corpus 又是 docs 鏡像 → edu 全降 P3 邊際值≈0），結論反映進 callstack-plan 優先序。原則同 [tour-bootstrap](../tour-bootstrap/SKILL.md) 步驟 3 重複度盤點（overview 前置的同型裁決）
1. **鏈枚舉（問題錨定三軌——獨立可跑，成本 ~2% 於生成）**：準則＝「這條鏈回答什麼**使用者問題**」（非程式從哪進來/長在哪層）——①**入口鏈**（ops「這入口失敗去哪查」）：機械掃入口（launchd／CLI／UI app）＋常青篩選（會再跑才成鏈；同體多入口併一鏈），本軌機械收斂可驗；②**機制鏈**（debug／重構「為什麼擋單／改這模組誰受影響」）：錨共用模組影響域／critical path（候選＝code-reality graph 熱點〔`hub_nodes`〕、hub 影響域），過濾＝cross-cutting 且活著（dormant 不成鏈）；③**流程主題鏈**（onboarding／研究「這流程端到端」）：一篇一縱貫流程，教育裁定（人決動線）；④scripts／probe／一次性——**plan 索引一行，不成鏈**（無對應使用者場景）。產出 `ai-analysis/blueprint/callstack-plan.md`（每行＝**軌**×鏈名×錨點×一句職責×優先序）——分批菜單按軌分批；驗收分軌（入口軌機械收斂／機制軌數據支持／主題軌人裁定）。README 地圖按三軌分組、目錄維持平面；入口鏈↔機制鏈交叉引用開放（「本鏈止於 X、深潛見 Y」邊界宣告）
2. **每鏈深挖**：入口→逐幀抽取，**每一幀 Read／rg／LSP 實證、禁止臆測**；行號用 def 實讀非估算；跨縫幀（python 面↔Rust 真身，pyo3 形態 repo）以 `boundary` 查詢補第二錨（`code-reality boundary <symbol>`、`--rs` 反向；sidecar 無則先 `boundary_build` 產）——graph 對縫兩側無邊（NT 實證：Python↔Rust 邊＝0、.pyi 節點＝0）
3. **coverage 稽核**：檔案級覆蓋率＋省略原則（registry 同構 leaf 群由引擎篇涵蓋、thin wrapper＝CLI 等價入口不另錨、UI 呈現內容切綱外但資料餵入子鏈屬執行面、dev tools 不入盤點）
4. **補強輪**：真缺口清零（省略原則豁免項外逐檔對賬）
5. **findings 彙整**：跨系列 🔴／🟡／🟢 優先序（深挖副產品＝code review 輸入）
6. **UC 映射表**：任務／UC × 鏈（「查某 UC 的 how 從這進」）

**人審停點**：每份文檔初稿即停——敘事品質（幀職責一行是否講對重點）是使用者策展職責；系列收尾跑機械驗證（下段）。**維護紀律**：行號 drift 不逐行修（符號名優先、LSP `workspaceSymbol` 重錨後重寫該幀）；整條鏈大改→整份重生成（原地）或退役 `_done/`——平行版本需求才開版號目錄。**執行模式與效率**：①單 session 逐鏈（原版實證：16 篇／24 模組／約一日滿載 session）②agent 群並行（跑批實證：29 篇／~2.5k 幀／牆鐘 ~2h／token ~150M——超出單 session 負荷，但每篇自帶錨定機械驗證、可並行；token 量級是模式抉擇的輸入）——**並行上限 ≤3**（全強度模型實證：mosaic 六並行掛 2；NT 13 agents 併 ≤3 零失敗——lite tier 並發上限較寬，見 [model-routing](../model-routing/SKILL.md) 並發表）＋失敗者**序列重試一次一個**，勿立即重 spawn。agent 群模式**共用 context 打包**：枚舉產物（鏈清單＋每鏈入口細節＋相關 AGENTS.md 段）直接嵌入每篇 agent prompt——冷啟重讀是重複成本主因，打包入口細節實證有效。品質基準：工具實測錨定率（>90%）＋`  # ` 附註率（~100%）。

## audit 模式（既有 blueprint——預設防護）

不重建不覆蓋：①現況 vs 治理 `AGENTS.md` 契約 drift 盤點（真相源連結失效／宣稱過時／孤兒檔）②缺塊只報清單＋可補骨架（如無治理檔）③既有內容是人類策展資產——**AI 只報缺口不代寫**；內容重編走該 repo 既有對齊覆核流程（消化重編、人在環）。

## 已驗證案例

- **mosaic**（blueprint 演化源＋callstack-v1 golden sample——骨架模板與生成程序的反推來源）：`~/Github/mosaic_alpha/ai-analysis/blueprint/`（2026-09-18 mosaic 兩線 WT offline_backtesting／trading_lab 退役後，blueprint 現居主 repo）。skill 程序本身未經完整 fresh-run 執行——首個 dogfood＝mosaic audit run

## 機械驗證（產出時）

README／治理檔交叉引用路徑存在；callstack 文檔跑 `code-reality chain_tour <md> --repo <repo> --out-dir <repo>/.agent-tmp/chain-dry/` 暫存自測——**場景數＝文檔場景數、重錨統計合理、無錨幀分佈記錄**，生成端當場驗，不等到 tour-bootstrap 才發現格式落空（out-dir 在 `.tours/` 外＝工具自動跳 manifest，暫存零副作用；驗完即棄）。
