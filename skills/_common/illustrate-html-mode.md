# illustrate HTML 模式 — 報告殼（人類 viewport，opt-in）

> /illustrate 的第三輸出模式。Console（即時）與 MD（Mermaid 沉澱，**source of record**）角色不變——HTML 是**按需渲染的展示層**，服務「人類 viewport」：分享 / demo / re-onboard / drift 審查。三模式是受眾分流非取代。舊互動圖渲染產線已退役（AIR-74）——圖載體＝mermaid 與 HTML 塊二擇，殼一律進版控。

## 觸發條件

- **明示**：`/illustrate html <主題或 @dir/@file>`（mode D 主題 → mermaid/HTML 塊；mode B @dir → artifact 概念→載體映射；mode A/C 明示 html → city map 走架構 HTML 塊）；`@ep`／實作報告／`@module`／`@dir` + html 明示報告導讀 → **Report Shell**（見「html 報告殼」段）
- **增益建議**（不自動切換）：mode D 分享情境——互動搜尋 / focus / Present 導覽對位人類 viewport 消費方式時，建議 html 並由 user 決定
- **永不**：Console 語境不 inline 渲染（明示 html = 切換輸出模式，檔案交付＋路徑回報）

## 概念→載體映射（illustrate 概念軸；圖型軸判準在 diagram-selection）

mode B artifact 與 mode A/C city map 共用此映射（概念軸單一源；「sequence/stateDiagram 這類圖型用哪個載體」的判準與量化邊界見 [diagram-selection](../diagram-selection/SKILL.md)——兩軸互補不重疊）：

| illustrate 概念 | 首選載體 | 備註 |
|----------------|---------|------|
| boundary / city map | **HTML 塊**（殼內 div/flex/grid 層次型） | 層次/對照內容零渲染管線、殼原生一體 |
| data-flow | mermaid `flowchart LR`（管線型） | 線性管線一輪可成 |
| sequence | mermaid `sequenceDiagram`（殼內 srcdoc/iframe） | 有通道——成本最低 |
| call graph | mermaid `sequenceDiagram`/`flowchart`（小圖）或 HTML 塊 | 按互動語意選 |
| class slice | **無對應** | 維持 md／表格（diagram-selection 兩層判準），不硬映射 |
| **報告殼（`@任務家/<task>/ep.md`／實作報告／@module／@dir + html）** | 按報告類型選型（見下節變體表） | Report Shell——人類 viewport 通用模式 |

## html 報告殼（Report Shell——人類 viewport 的通用模式）

> 本質：任何「AI 消費為主、人類需要快速理解」的產物（EP 計畫／實作完成報告／codebase 架構／module 現況／目錄導覽／決策 viewport）共用同一模式——**本體層**（markdown source of record）＋**報告殼層**（順序敘事 viewport）——同源雙消費。起源實證：EP「我現在很少看了，太難理解，都給 AI 用的」。

**三層結構（順序性是核心——user 實證：「兩張圖並列搞得好亂、不知道從哪看起、S1 S2 S3 那排不能點」）**：

```
報告殼（自製薄殼 index.html）
  左 sidebar＝章節順序，點章節切主區
  主區＝該章節文字精華＋該章節該看的圖
      ↓ iframe srcdoc（mermaid lazy render）或 HTML 塊直寫
視圖素材層（mermaid 圖引擎——每張圖=一個視圖，diagram-<name>.svg / srcdoc 內嵌）
```

- **殼結構/視覺/互動單一源＝template [`skills/_common/illustrate-report-shell.html`](./illustrate-report-shell.html)，建殼＝複製＋填 slot**（slot：title/badge/meta/nav/section-content/diagram/backlinks/source；首屏 active、sidebar 折疊、hash restore 自帶；主題三態 light-dark token 慣例），入口命名 `index.html`、圖命名 `diagram-<name>.svg`；殼的未來＝AIR-73 `build_shell.py` md→殼 deterministic codegen（落地前為手寫殼 legacy）
- **消費單位是章節不是圖**——多圖並列無導覽＝亂（實證）；每章節只放該章該看的圖
- **首屏 active 與嵌入參數由 template 擁有**（首個含圖章節規則＋AIR-14 實證見 template 檔頭註解三條硬約束）——建殼不重推導、不手改首屏指向
- **殼嵌圖三形態**（同殼可混用，按圖選載體——判準見 [diagram-selection](../diagram-selection/SKILL.md)）：inline SVG（預設產物 **≤1/頁**——mmdc id 碰撞；**帶唯一 `-I <svgId>` 可多張**，見 [mermaid](../mermaid/SKILL.md) 陷阱 5）／iframe＋`diagram-*.svg` 檔（其餘 mermaid）／iframe srcdoc lazy render（mermaid code 內嵌、主題跟隨——blueprint/test-contract 殼先例）／HTML 塊直寫殼內（層次/對照，零渲染管線）；外框統一 frame-wrap（標題列＋zoom/ESC 檢視器）。**無縫一體準則**：同主題（殼 dark → 圖 dark chrome）、透明底、同字體、尺寸自適應——mermaid 配方（mmdc `-t dark -b transparent`／CDN lazy render）見 [mermaid](../mermaid/SKILL.md) 殼內嵌段
- **md 死鏈禁例**：殼連結 `.md` 的 mermaid code block 在 file:// 不渲染＝死內容——未渲染 .md 圖集不進殼，**圖要真的出現在頁面上**（渲染產物嵌殼），不是「原始碼在另一檔」

**內容篩選通則（user 勘正：「缺漏要看是不是人類真的需要知道」）**：殼裝**判斷材料**（意圖/為什麼動機鏈、風險與降級、取捨決策、驗收判準、當前狀態、實物樣本、回源路徑），**不裝執行細節**（治理規則、AI 流程產物如 UC 盤點表、機械完整性逐項覆蓋）——後者留本體層，殼至多一句指路。**實物樣本要進殼**（人類沒看過實物，機制敘述等於空談）。

**殼生成分工（decision 敘事腿＋vision 驗收腿；registry 對號查 agents/AGENTS.md execution contract 表）**：

1. **篩選敘事（decision——主 session）**：殼的章節篩選與敘事＝判斷密集（「缺漏是不是人類真的需要知道」是判斷題）——不派 execution 腿；mermaid（mmdc 機械 CLI）與 HTML 塊由主 session／execution 腿直接產
2. **vision-review（vision 驗收）**：渲染 PNG 逐張 verdict（圖互 clip／CJK 誤讀／美感底線）——驗收收法見該 agent 定義；契約（三段式/分批上限/全樣本錨定）見 [diagram-selection](../diagram-selection/SKILL.md) 共性段

**機械底稿（數據宣稱唯一來源）**：殼中一切**數據宣稱**（數字、狀態、覆蓋率、時間）只從機械底稿帶入、禁止敘事層自填——底稿＝**delta_tour 輸出／命令輸出原文**（防文檔宣稱漂移——lite 分工律，model-routing skill）。

**報告類型的敘事骨架變體**（殼固定、骨架變）：

| 報告類型 | 敘事骨架 | 圖選型 |
|---------|---------|------------------|
| EP 計畫導讀（任務家 `<task>/ep.md`） | 為什麼（動機鏈）→資產與命運→推進與驗收→各段細節→風險降級→決策記錄 | flowchart（gate/exception）＋HTML 塊（層次） |
| 實作完成報告（implement 完成報告/debrief） | 意圖→做了什麼→**驗證證據**（命令+exit code）→認知誤差點/待確認 | flowchart（流程變更時）＋前後對照 HTML 塊 |
| codebase 架構報告 | 分層地圖→資料流→熱點與風險區 | HTML 塊（分層）＋flowchart LR（資料流） |
| module 現況（`@module`／AGENTS.md 域） | 職責→Capabilities 精華→依賴與邊界 | HTML 塊（局部視圖） |
| 目錄導覽（`@dir`） | 這裡有什麼→入口→慣例 | HTML 塊 |
| 決策 viewport（裁決 report 的圖形投影） | 結論→流程/分工→修改面→證據鏈 | flowchart TB（管線）＋表格（分工/清單）——先例 `ai-analysis/test-contract/` |

**產物位置分流（user 裁決「開心目錄」——一弧一殼、隨生命週期生長；AIR-74 起殼一律進版控）**：

- **流程性 brief（EP 計畫導讀＋實作完成結果）→ 任務家（task home）下 `MM-DD-<task-name>/`**（目錄名**無年份、無 ep-/impl- 前綴**——活躍弧停留短；完結弧 task 目錄**整目錄**搬同家歸檔層——repo 慣例探測 `done/` 扁平或 `_done/<YYYY>/` 年分層，皆無建 `done/`；年份僅由年分層形態承接；歸檔目錄判定單一源見 [metadata-sync](../metadata-sync/SKILL.md) EP 歸檔項）。**任務家探測（2026-09-02 三池重構定案，各 skill 放置規則共用本源）**：`<repo>/ai-analysis/_tasks/` 在場 → 雜項任務家＝它（**線任務另居 `ai-analysis/_projects/<線>/tasks/`**——session 從線 context 來時；完成→同線 `done/`）；否則 repo-root `00-tasks/`（`00-` 前綴 VSCode/`ls` 排最前）。spec（`spec.md`）與 EP 本體（`ep.md`）同 task 目錄——一弧全生命檔案同處。與 debrief（文字簡報）/delta tour（行級走讀）三層互補：殼=high-level 圖形、debrief=模組/檔案文字、tour=行級；殼實作章節吸收日常判斷材料，debrief 為深度選配
- **按需性視覺產物（codebase 架構/module 現況/目錄導覽）與決策 viewport → `ai-analysis/<域>/`**（與裁決 report 同域——先例：`blueprint/`、`test-contract/`）；**殼 `index.html` 進 git**（authored 殼不可再生——AIR-74 定案；舊 repo-root 渲染目錄慣例已退役）
- git 慣例**同一原則、條目隨任務家**：`.mmd` 源＋殼 `index.html`＋mermaid 渲染（svg）全進 git（AIR-74——舊「渲染產物不進」慣例已取消）；殼 `index.html` 一律進（排過寬 `**/*.html` 會連殼一起 ignore——規格↔實作分歧實證：殼蒸發死鏈）

**殼生命週期掛點（自動產生雙掛點＋fallback）**——修「掛弧後（commit 後）的產物在 session context 耗盡時必死」：掛點全落在 commit **前**的穩定點。**backlog 卡同步與主動顯示隨掛點聯動**（命令合約＝[kanban-board](../kanban-board/SKILL.md)；「顯示」走 `open <殼絕對路徑>`——內建瀏覽器 file: 直開；:6421 report server 已與 ai-guide 無關〔09-14 退出，mosaic 自家承載〕，殼一律 file: 直開）。

| 掛點 | 時機 | 殼 | backlog 卡同步 | 主動顯示 |
|------|------|-----|---------------|---------|
| **hook 1** | EP 定稿（[execution-plan](../execution-plan/SKILL.md) 定稿交付） | **建殼骨架**＋計畫章節，badge 📋——骨架＝零渲染管線內容（HTML 塊/表格可），**渲染管線圖（mermaid）不於 hook 1 產**，diagram 槽留 degraded 待裝＋殼頭標「圖待 hook 2 裝」（砍掉 hook 1 計畫圖在 hook 2 實作大改後的重投影成本）；殼頭部聲明 EP 路徑＋task integration baseline＋projection source（未 commit 用本體 content SHA；post-build/code-review 弧模式跨 session 可從殼讀） | `task edit <id> --ref "<EP 相對路徑>,<殼相對路徑>"`（**開工雙 ref 合約**——建殼後並列殼路徑；殼未建單掛 EP 路徑，不寫 viewer 過渡 URL） | **`open <殼絕對路徑>`**——殼建好即彈出（提前預覽骨架） |
| **badge 推進** | [implement](../implement/SKILL.md) 階段 5a 結算 | 情境 A（Built 結算）→ 🟡（✅ 升級掛 hook 2 結案）；情境 B（中間段）→ 🟡 | 卡不動（仍 In Progress） | 不主動開——board portal 隨時點同一殼路徑 |
| **hook 2** | **post-build 完成**（commit 前最後穩定點；程序載體＝[post-build](../post-build/SKILL.md) 階段 5） | 同一殼長**實作章節**：做了什麼／驗證證據／delta 前後對照／認知誤差點＋回源連結——反映修正迴圈後**最終態**；**並產圖一次**——依 [diagram-selection](../diagram-selection/SKILL.md) 選型補 degraded 槽；badge ✅；**持久版 delta tour＝ask-once**（收尾報告待確認清單、預設略過——demand-driven；已產時殼實作章節連結 `.tours/delta/<arcId>.tour`，走讀＝ai-lifecycle AI Tours 視圖） | **結案兩步＋弧結案蒸餾第三動**：`-s Done --final-summary` → `--ref` 換 `done/` 新路徑（任務目錄遷 done/ 後；卡留 Done 欄；已產 delta tour 時 refs 並附 `.tours/delta/<arcId>.tour`）；本弧 memory 條目蒸餾終態 facts | **`open <殼絕對路徑>`**——終態殼彈出 |
| **fallback** | 無 post-build 弧（user 直接 `/commit`、弧終止）→ implement 階段 6 | hook 2 同款產出由 implement 階段 6 承接 | 同 hook 2 | 同 hook 2 |

**共通必備**：狀態 badge（📋 計畫／🟡 進行中／✅ 完成——與全域 UC 狀態標記同符號語義）；計畫 vs 既有顯式區分（計畫物 tag「S<N> 計畫中」——並列無區分＝誤導）；回源連結（本體檔案路徑＋baseline commit）；**board 反向連結已取消**（board 無 HTTP 位址——09-11 常駐退役；殼頭部可標「← backlog board（VSCode Backlog Cards）」提示文字、不帶 URL）；**EP（.md）連結形態**（09-14 退役 viewer 形態——:6421 report server 與 ai-guide 無關，殼內 EP 連結一律 **repo 相對路徑**（VSCode 一點即編輯器／preview），禁掛 `/viewer/_md-viewer.html?p=/…` http URL；歷史殼的舊 viewer 連結留原樣＝歷史態）——卡 refs 相對路徑制見 kanban-board 雙 ref 合約行；狀態隨本體結算更新、本體歸檔殼隨之（殼服務本體生命期）。

**雙向一致性（html ↔ md——user 勘正：「同一個 md 每個人理解都不一樣，AI 跟人有理解差異正常，但是大方向不要錯」）**：

- **分級而非逐字**——零差異不可能也不追求；分兩級：
  - **大方向（硬，不可錯）**：目的與動機、範圍邊界（做什麼/不做什麼）、段落劃分與順序、驗收判準的語義（gate 過關條件）、風險的有無與等級、關鍵數字的數量級——判準句：「**拿殼給人看形成的大方向預期，vs 拿本體給 AI 實作產出的結果——兩者對得上嗎**」；對不上＝投影失真（這才是 bug）
  - **細節（軟，容忍理解差異）**：語氣/詳略/例子選擇/口語化改寫——不逐字逐句核對
- **殼是投影非平行創作**——殼想說本體沒有的東西 → **先改本體再投影**（發現順序顛倒是警訊：本體缺該內容）；禁止殼內出現本體沒有的**大方向級主張**（新決策/新範圍/新風險等級）
- **投影鎖定與 stale 標記**：殼頭部將 task integration baseline 與 projection source **分欄聲明**；projection source 已 commit 時用包含本體的 revision，未 commit 時用本體 content SHA（不可拿早於本體的 integration baseline 冒充）。本體修訂（review 修訂/段落結算/狀態變化）→ 殼**同步重投影**並只更新 projection source（大方向級變更必同步；純文字潤飾可不動）。同步義務與「測試斷言變更→驗收規格同步」「code 變更→Capabilities 同步」同一模式（single source of truth 的投影紀律）
- **提煉篩選≠語義漂移**：篩選通則（判斷材料 vs 執行細節）授權「刪」不授權「改」——刪掉的內容一個指路連結回本體即可

## 產物生命週期

- **輸出位置**：任務家（流程 brief）或 `ai-analysis/<域>/`（按需視覺/決策 viewport）——見「產物位置分流」；入口 HTML 命名 **`index.html`**、mermaid 源 `diagram-<name>.mmd`、渲染產物 `diagram-<name>.svg`；`--output <path>` 自訂路徑尊崇（track 與否使用者決定）
- **目錄即索引**：不建 index——kebab 檔名自描述；手維護 index 是 drift-prone 清單（同 skills/CLAUDE.md 索引教訓），量大再考慮機械投影生成（YAGNI）
- **git 分工（⚖️ 源＋殼＋svg 渲染全進 git——單一源，per-repo 可覆蓋）**：**`.mmd` 源＋殼 `index.html`＋mermaid 渲染（svg）＋visual-check receipt 全進 git**（AIR-74）；`.mmd` 仍可重渲染 svg，但輸出 tracked——「可重渲染」≠「不追蹤」
- **html→md 雙輸出**：同主題先 html 後要 md 沉澱 → 從同一 grounding 事實再渲染 Mermaid；md 是 source of record

## 重生（regeneration）

**觸發**：user 說「**重生報告殼**」（全量）或「重生 `<主題>`」（單目錄）；svg 損毀／工具版本變更後的修復性重渲染（svg 已 tracked：fresh clone 自帶、`git clean -Xf` 清不掉）。

**程序**（對每個含 `.mmd` 源的殼目錄——任務家 `*/` 與 `ai-analysis/<域>/`）：

1. mermaid 圖 = `diagram-<name>.mmd` 源；`npx -y @mermaid-js/mermaid-cli -i diagram-<name>.mmd -o diagram-<name>.svg -t dark -b transparent`
2. 殼本體＝手寫 authored 殼（在 git，無需重生）；AIR-73 codegen 落地後殼＝md 投影、重跑 `build_shell.py` 即得
3. 驗收態（可選）：`visual-check`（需要 Chrome；產 receipt＋截圖）
4. 確定性保證：同源 → 相同產物；重生後對不上 = 源或工具版本變了，如實回報
