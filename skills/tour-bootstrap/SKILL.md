---
name: tour-bootstrap
description: "Repo Tour Bootstrap——把任意 repo 變成可走讀狀態（場景層 Chain Tour／時間層 Delta Tour；地圖層 Overview Tour 視重複度盤點）的程序 skill，建在 code-reality 工具鏈之上。何時跑：使用者說「bootstrap 這個 repo 的 tour」／新 repo 冷啟動要導覽／要產 overview tour。含 .tour link 語言契約、機械驗證清單、優先序裁定；斷點③已解——callstack 生成走 blueprint-bootstrap。"
when_to_use: "Bootstrapping tour corpus for any repo (user says \"幫我 bootstrap 這個 repo 的 tour\"), authoring an Overview Tour (short isPrimary version), converting callstack docs to chain tours, or validating .tour links/anchors. Prerequisite detection: 有 callstack 文檔→chain＋delta（地圖層視重複度盤點）；無→不產 tour，出 callstack-plan 枚舉清單＋詢問三選（生成 callstack／手作 overview／跳過）。"
argument-hint: "<repo-root>（要 bootstrap 的 repo；省略即 cwd repo）"
allowed-tools: ["Read", "Bash", "Write", "Edit", "Grep", "Glob"]
---

# Repo Tour Bootstrap（repo 導覽建置程序）

一句話：使用者說「**幫我 bootstrap 這個 repo 的 tour**」→ 產出走讀 corpus（地圖層視重複度盤點；場景＋時間層）→ 使用者「**走讀**」它（ai-lifecycle 的 AI Tours 視圖——CodeTour fork player 已被吸收，fork vsix 退役；panel 點開即走）。

**分層**：工具層＝[code-reality](../code-reality/SKILL.md)（chain_tour／delta_tour CLI、repo profile）；本 skill＝程序層（工具的編排、`.tour` 語言契約、驗證、停點設計）。能力命名體系：Repo Tour Bootstrap（能力）／Overview·Chain·Delta Tour（三層產物）／Walkthrough 走讀（消費）。**基數鏈**：一份 callstack md → N 場景 → N 條 tour → 一族（同目錄）——md 與 tour 非一對一，呈現各自獨立（md 給人讀、corpus 受 player 正則約束），唯一耦合是資料流邊（chain_tour 以檔名為錨）。**delta 層不在本程序產出**——由 `delta_tour` CLI 產出（持久版產點＝post-build hook 2 **ask-once**〔demand-driven——user 確認才產，預設略過〕、無 post-build 弧＝implement 階段 6 fallback 同語義；產生入口＝intent-level `code-reality tour materialize <arcId>`；`.tours/delta/` 進 git），bootstrap 只負責其目錄版控契約（步驟 1）。

## manifest provenance 契約（delta materialization——AIR-80）

- **`arcId`＝materialization canonical key**；`cardId` 只是 join 屬性（一卡可多弧——以 arcId 對齊不以卡對齊）。
- **兩階段**：`tour register`（pending row 立即持久化——ask-once 略過路徑）→ `tour materialize`（row 補 `tourPath`）。row 缺席＝消費端無觸發 UI（ask-once 略過仍必須 register 的原因）。
- 每次 materialize 落一列：`{arcId, cardId, base commit, target commit, EP 路徑, quality: full|degraded}`；已 materialize 的 row **保留不刪**——`tourPath` 指向產物，消費端靠 row 尋回已產 tour（同 arcId 重產＝覆蓋同 tourPath，歷史交 git）。**quality＝claims 完整度**（row 有 ep provenance＝full；card-first 弧以卡／TaskRef provenance 計 full（ep 欄缺席合法）；anchor 可用性是另一軸——repo-外 EP 不作 step anchor 但 claims 仍可 full）。
- **替換語義分兩形**：`register`／materialize 註冊形（帶 --base/--target）＝**tool-owned authoritative full replace**（未帶 optional 欄清掉、未知欄不保留）；**row-driven materialize＝cardId 保留、ep 由 provenance 重解析**（ep spec 以 canonical 形持久化——repo 內 repo-relative、repo 外絕對——意圖式重產冪等）。人工策展欄請放 `[tour.*]` row（unknown-key roundtrip 保護只涵蓋該層）。
- 消費端（ai-lifecycle）**容忍式讀取**：欄缺席＝無觸發 UI，不 fail。

## 前置偵測（決定 corpus 形態）

| 偵測 | 有 | 無 |
|---|---|---|
| callstack 文檔（場景敘事，`ai-analysis/blueprint/callstack/`——由 [blueprint-bootstrap](../blueprint-bootstrap/SKILL.md) 生成；偵測含歷史版號目錄如 mosaic `callstack-v1/`，其輸出一律無版號） | **chain＋delta**（地圖層視步驟 3 重複度盤點） | **不產 tour**——跑入口枚舉出 callstack-plan 清單（~2% 成本）＋**詢問 user** 三選（生成 callstack：報價＋分批／手作 overview／跳過）；無互動＝無產出（tour 是素材→corpus 轉換器，非內容生成器） |
| `.code-reality/graph.db`（chain_tour 重錨的實際開關） | chain_tour 帶 graph 重錨統計 | 純文檔錨退化（不擋） |
| `.tours/` 既有內容 | 盤點前例（產出形態對照、版控契約現況） | 全新 |

## 程序（五步）

1. **盤點**：`.tours/` 現況、文檔源（root／模組 AGENTS.md 群、架構文檔、SYSTEM-MAP）、`.gitignore` 對 `.tours` 的契約；manifest `generator` 非 `chain_tour`（現值域＝`manual`）rows＝**curated 資產**——重產前逐列提示保留／重寫決策（勿盲目覆蓋；M1 實證）。⚠ **arch 進版控是契約變更**（預設 `.tours/` 常被整目錄排除）——改 `.tours/` → `.tours/delta/`（delta 層**進版控**——弧的行級理解產物非暫態快照，post-build hook 2 ask-once 產出）＋前例補追蹤，`git check-ignore` 雙向驗證，需用戶知情。
2. **場景層**（有 callstack 文檔才做）：`code-reality chain_tour <md> --repo <repo> --out-dir <repo>/.tours/arch/<族名>/`（`--primary` 見「優先序裁定」；<族名>＝**人類標題**——中文／中英混合皆可，panel 標題的職責＝讓人一眼決定要不要進去看；與 md 檔名（英文 slug 供 grep/CLI）解耦，僅 manifest sources 連結——**族名不帶軌別前綴**（軌分類住 README 地圖/plan）、推薦動線族加數字前綴亦見「優先序裁定」）。**收錄語義**：每份 callstack md 落地一族，收錄子集屬策展決策（初稿停點裁定）——M1 實證：全量 16 族 97 條落地、策展核心族 byte-identical 重現。zsh 變數不 word-split——動態 flags 用陣列 `args=(--flag 1); cmd "${args[@]}"`、固定參數直接寫明（通用條目見 tool-discipline rule「zsh 動態 flag 組合」）。驗收：產出檔數＝文檔場景數（場景＝含樹狀幀的 code block）；重錨分佈統計記錄；每條抽樣 ≤5 步 `line`+`pattern` 與源碼 def 對齊。0-step tour（描述殼）保留但勿連入。
3. **地圖層（先做重複度盤點，再判受眾，再選步錨）**：**重複度盤點＝是否做 overview 的前置裁決**——比對潛在 overview 與既有文檔源：模組步是否＝文檔模組導航表的逐步慢讀、文檔錨步邊際值（落地所見 − description 所述）是否≈0、（若已有雙版——audit 時點才可盤）版間錨點重複度；**事後退役同等有效**（mosaic 即先產後盤退役）。高重複（repo 已有強導航文檔群）→ **地圖層退役**：前門改 chain `--primary`＋目錄前綴群序（見「優先序裁定」），省 curated 維護稅；低重複 → 續做，判受眾：受眾＝**冷啟動新手**（clone 即讀）→ 分層步**錨模組 AGENTS.md h1**、description＝職責一句＋file link（文檔是新手的自然入口）；受眾＝**理解程式碼**（含 repo 主人走讀）→ 分層步**錨真實源碼**（入口函式／註冊點／核心機制，`line`+`pattern` 雙錨，講這段程式碼做什麼、上下游是誰），文檔退 file link——**文檔索引對 repo 主人是零價值**。骨架＝開場（contents 步無檔）＋分層 4–6 步＋資料入口 1–2 步（代表檔雙錨）＋場景目錄步（tour link）＋開發工作流步＋收尾；長版可選（30–40 步、`00b - `）。**宣稱紀律：description 每個實質宣稱可追溯到文檔或源碼**（防 AI 造假敘事），不自行發明。
4. **`.tour` 語言契約**（消費端 player 正則決定——現行 player＝ai-lifecycle 吸收的 CodeTour fork，寫錯＝死鏈）：
   - `line` = **1-based**（player 內部 −1）
   - `pattern` = literal-ish regex（`^…$` 行錨定；行漂移時 pattern 最近命中校正，零命中顯性標未驗證）
   - **tour link**＝`[顯示名][匹配鍵#N]`（顯示名可省——單方括號也是合法形式，正是下條誤判的源頭）；markdown `( )` 形式被排除＝死鏈；**匹配鍵**＝title 剝 `^#?\d+\s-` 前綴**且在第一個 ASCII `-` 截斷**（`getTourTitle` 的 `split("-")[1]` quirk——title body 避 ASCII 連字號，撞鍵時 link 落第一條）
   - **file link**＝`[文字](./相對路徑)`——路徑以 `.` 開頭才觸發走讀欄 pinned tab（`./` 為慣例形態）
   - description 內**禁其他裸方括號**（會被誤判為 tour link）
   - **tour 檔名＝`{NN}.tour` 純序號**（user 裁定——族名承載語義、檔名僅穩定鍵，無截斷）；`NN - ` 前綴限系列 tour 且**必須補零**（`01 - `）——非補零 `1 - ` 會被 player 誤判 primary；`isPrimary`＝corpus 前門（冷啟動直達＋panel star 置頂）——有地圖層時＝overview 短版，無地圖層時＝chain_tour `--primary N` 標主題鏈（edu）（見「優先序裁定」）
5. **機械驗證**（初稿產出時＋策展定稿後各一次）：全檔 JSON parse／tour link 匹配鍵逐字對齊＋步號存在（用上述剝前綴演算法算鍵，非肉眼）／file link 路徑存在／自有步 line+pattern 與源碼行對齊。

## 優先序裁定（條件式——多族 corpus）

**觸發**：chain ≥ 2 族或 ≥ 10 條（或地圖層經重複度盤點退役）；單族小 corpus 跳過。**產出形狀＝推薦動線（≤6 條）＋按任務查族，不產全序**——corpus 內 0-step 殼與 1-step 條目使全序成假精確。

三輸入（盤點而來，AI 不發明）：

- **機械統計**——chain_tour 輸出（每條步數、0-step 殼、族幀數）
- **族角色**——SYSTEM-MAP 狀態標記（🏃＝生產運行）＋plan 軌別（入口 ops／機制 mech／主題 edu——blueprint 三軌）
- **覆蓋廣度**——鏈橫跨的架構層數（callstack 幀目錄可判）

裁決規則：① 前門＝主題鏈（edu）中「橫跨層最多 × 步數中等」者（殼與 1-step 不入動線——步驟 2「勿連入」擴為「不入動線」）；② 動線＝主題（edu）→入口（ops）→機制（mech）按任務；③ 殼族標「深讀走 callstack md 本身，不走 tour」。落地＝`chain_tour --primary N`（唯一有效前門機制——player fallback 只認未補零 `1 - `，補零 corpus 永不命中；**重產帶前門的族必須再帶 `--primary`，漏帶則旗標靜默掉落**）＋目錄數字前綴（**補零兩位**如 `01-`——panel 群組 alphabetical 排序，前綴讓群序＝優先序——**panel 即動線**；族名＝人類標題（中文／中英不拘，決定進場用）**不含軌別**——生產者分類（edu/mech/ops）洩入走讀介面是呈現錯置，軌分類住 README 地圖與 plan）＋repo 入口文檔一行（AGENTS.md 觸發器表自述前門與群序語義）。停點：初稿產出即停，用戶策展。

## 停點設計

初稿產出即**停**——AI 不代終審（敘事品質是使用者策展職責）；使用者走讀邊看邊改（ai-lifecycle AI Tours 視圖）；策展定稿後重跑機械驗證（編輯會引入壞 link／壞 JSON，走查只暴露走到的步）。收尾**預設不產 `.tours/README.md`**——panel 群序＋manifest 清單＋本 skill（契約／CLI）已承擔其全部內容，使用者不讀；僅當有 panel 外的 repo 專屬 gotcha 才立檔。

## 重跑語義（三模式——repo 已有 corpus 時）

| 模式 | 觸發 | 行為 |
|---|---|---|
| **fresh** | 無 corpus／用戶明示重建 | 走五步程序 |
| **audit** | 有 corpus（**預設**） | 跑 `tour_validate --manifest` 產報告，**不改任何檔**（bootstrap/audit 恆唯讀——FAIL 修復閉環程序單一源＝[post-build](../post-build/SKILL.md)「Tour corpus gate」節） |
| **migrate** | 格式舊（line-only 錨／純文字 cross-ref） | `tour_upgrade --dry-run` 先看報告，用戶點頭才 `--apply` |

判定：`.tours/` 無 tour→fresh；有 corpus 無 manifest→audit（提示 migrate 若格式舊）；有 manifest→audit 為預設。

**兩條鐵律**：① **corpus 變更一律經工具**（generator／tour_upgrade／tour_manifest CLI）——LLM 不直接手改 `.tour`（bootstrap 期 overview 手工初稿與人類策展編輯除外）；② **curated 不可盲目覆蓋**——derived tour 重產 diff 非空＝已被人改過，升級為 curated（manifest generator 改 `manual`）只報 diff 不覆蓋。

**檔名格式過渡（D-f 後）**：out_dir 殘留舊格式 `chain-*.tour` 時 chain_tour 印 `[WARN]`——新舊同 title 並存會使 player 撞鍵靜默落第一條（corpus 靜默雙份）；全 corpus 改名重錨＝雙步清理：`rm <族目錄>/chain-*.tour` ＋ 刪 manifest.toml 讓重產重建。

## 斷點③（已解——上游為獨立服務）

**AI 輔助生成 callchain 文檔**——生成程序固化於 [blueprint-bootstrap](../blueprint-bootstrap/SKILL.md)「callstack 場景敘事生成」章節（高成本＝獨立觸發＋報價＋按 callstack-plan 分批挑鏈）。本程序偵測無場景敘事 → **不代跑、不自動退化**：先跑入口枚舉出 plan 清單，**詢問 user** 三選——高成本操作是決策停點，不是流程步驟。

## 已驗證案例

- **mosaic**（chain 前門型——地圖層經重複度盤點退役：雙版間 10/12 錨點逐字重複；前門＝chain_tour `--primary`＋目錄數字前綴群序）：規格源 EP（**歷史溯源**——原路徑 `~/Github/mosaic_alpha_offline_backtesting/ai-analysis/execution-plans/` 已於 2026-09-01 清除、WT 於 2026-09-18 退役；spec 內容以 dogfood 退役裁決 ab63887c 為準）；M1 fresh 重產驗證（mosaic b10e4a95）：策展族 byte-identical 重現、全量 16 族 97 條、validate 0 fails
- **codetour**（overview-only 最小形態）：`~/Github/codetour/.tours/00 - codetour 總覽.tour`
