# EP — 畫圖選型與產線吸收弧（diagram-selection）

> **ep_type**: implementation（docs mode——產物全為 instruction 檔；mermaid seamless POC 為 evidence artifact，列 §S5 顯式執行）
> **baseline**: `a8072ce80355fcf67fa9ee0af675a3f28f6af3e4`

## 實作總覽

把「archify 成本鑑識＋畫圖載體選型」弧的材料（時序鑑識／坑清單／結構分析三軸＋MOS-41／mosaic 避坑／AIR-29 dogfood／MOS-27 四份 handoff＋kchart 線心得＋MOS-42 ①⑤）吸收進 ai-rules 知識體系。user 裁示：**只用 GLM**（全管線不派外部 runtime）；**archify 非必要不用**（選型預設 mermaid／HTML 塊）；**mermaid 在 HTML 下無縫融合一體**（配方定案＋POC 驗證）；可查網路（外部宣稱 grounding 標來源）。

**決策預設（user 授權採推薦傾向；標 ⚖️ 者 user 可否決）**：
- D1(a) 抽統一 skill `diagram-selection`（選型判準＋跨載體共性）；工具配方留原地
- D2 archify 產線 12 條修正整包
- D3 `<主題>.rounds.md` validate 輪 ledger 隨 JSON IR 進 git
- D4(b) hook 1 只建殼骨架（零管線內容可）；渲染管線圖（mermaid/archify）延 hook 2 一次產
- D5 ⚖️ C3 git policy＝「源＋receipt 進 git、渲染產物不進＋一命令再生；per-repo 可覆蓋」（MOS-27 三件套全進不採為單一源）
- ⚖️ C1 class 圖兩層判準（先問是否圖論問題：對照→表格；繼承網→archify）
- C2 locale 定值＝繁中內容省略 `meta.locale`＋回報揭露 Viewer UI fallback English（AIR-29＋MOS-27 兩份一致）

材料全文：`.agent-tmp/2026-09-05-diagram-cost-adjudication.md`（裁定包）、`.agent-tmp/2026-09-05-mosaic-diagram-handoff.md`（MOS-41＋避坑）、`ai-analysis/flow-feedback/2026-09-05-diagram-tool-selection-dogfood.md`（AIR-29）、MOS-27/MOS-42 跨 repo handoff（路徑見裁定包）。

## UC 盤點

### Backlog 關聯
- 既有：AIR-23（殼 template 化，Done——本弧改其產線語義，屬延伸非重開）、AIR-26（Done，殘餘②archify 決策樹槽位→ §S7 處置）
- 自動建卡：**AIR-30**（本弧追蹤卡，EP 產出後建＋commit）

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（元專案，docs mode 正當跳過）

### 掃描範圍
- `backlog task list --plain`（AIR-13~29 全 Done）；`ai-analysis/_inbox/` 目錄不存在（無去重命中）；`skills/CLAUDE.md` 工作流索引；`skills/{illustrate,mermaid,_common/illustrate-html-mode,_common/illustrate-artifact-menu,_common/illustrate-examples,ui-visual-verify,kbar-form-analysis}/`；`agents/roles/archify-gen.md`

### 既有 UC 狀態

| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| illustrate html 模式（archify＋報告殼） | ✅ | skills/illustrate＋_common/illustrate-html-mode | 更新 | 分派表改載體制、hook 時間點、guard 分層 |
| mermaid 圖表生成（theme 無關） | ✅ | skills/mermaid | 更新 | 增 mmdc 管線＋殼內嵌配方＋init 例外 |
| archify-gen 產線 agent | ✅ | agents/roles/archify-gen.md | 更新 | D2 修正＋schema_version per-type |
| UI 視覺驗收編排 | ✅ | skills/ui-visual-verify | 無影響 | 被 diagram-selection pointer 引用，內容不動 |
| K 線形態判讀 pipeline | ✅ | skills/kbar-form-analysis | 無影響 | 同上 |

### 新增 UC

| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| 畫圖載體選型（判準＋對照＋共性慣例） | 📋 | skills/diagram-selection/SKILL.md |
| mermaid 殼內無縫嵌入配方（雙路徑＋陷阱） | 📋 | skills/mermaid/SKILL.md 殼內嵌段 |
| archify 產線止損分層＋rounds ledger | 📋 | agents/roles/archify-gen.md＋illustrate-html-mode.md |
| 殼生命週期時間點（hook 1 骨架／圖延 hook 2） | 📋（更新既有掛點表） | skills/_common/illustrate-html-mode.md |
| vision 判讀標準化（三段式＋分批＋全樣本錨定） | 📋 | skills/diagram-selection/SKILL.md 共性段 |

## Scenario Matrix（docs 語境——rg 命中／0 殘留）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 架構全景互動圖 | `/illustrate html` 全景/互動導航需求 | 走 archify（三獨有價值命中才准） | html-mode 分派段 rg | 畫圖載體選型 |
| SM-2 | 時序/狀態/管線/ER 小圖 | 殼補圖或 md 圖 | mermaid 1 輪（mmdc 或 CDN），零 validate 迴圈 | `rg -n "transparent" skills/mermaid/SKILL.md` 命中 | 同上 |
| SM-3 | 層次/對照/分類內容 | 殼補圖 | HTML 塊或表格（零渲染管線） | 同上 | 同上 |
| SM-4 | archify >4 輪不收斂 | validate 連續未收斂 | 停手回報 caller 改 spec（12 輪降級維持為最終出口）；rounds ledger 記錄 | role＋html-mode guard 段 | 止損分層 |
| SM-5 | 殼內嵌 mermaid | hook 2 產圖 | 無縫一體（同主題/透明底/無 iframe 痕跡/尺寸自適應）＋`.mmd` 源進 git | §S5 POC verdict | 無縫嵌入配方 |
| SM-6 | EP 定稿 hook 1 | execution-plan 定稿 | 只建殼骨架＋零管線內容；渲染管線圖槽留 degraded 待裝 | hook 表＋引用掃描 | 殼時間點 |
| SM-7 | vision 批量判讀圖 | 派發 | 三段式契約＋每 agent ≤10-15 張＋抽樣錨定全樣本 | `rg -n "三段式|10-15" skills/diagram-selection/SKILL.md` | vision 標準化 |
| SM-8 | fresh clone 重生殼圖 | 「重生」請求 | archify JSON→deliver；`.mmd`→mmdc 一命令 | html-mode 重生段 | 無縫嵌入配方 |
| SM-9 | class 圖請求 | 型別關係 | 先問是否圖論問題：對照→表格；繼承網→archify | `rg -n "對照→表格" skills/diagram-selection/SKILL.md` | 畫圖載體選型 |
| SM-10 | mmdc 環境缺場 | npx 失敗/逾時 | CDN lazy render fallback，如實記錄 | §S5 | 無縫嵌入配方 |

## 段落 0：全域研究摘要（本弧前置已完成的鑑識）

- **可複用基礎設施**：殼 template `skills/_common/illustrate-report-shell.html`（骨架 hook 1 直接用）；`scripts/sync_agents.py`（role→投影生成器）；mermaid skill 既有 style 規範（seamless 配方的節點顯式配色基底）；ui-visual-verify 三鏈（POC 視覺驗收借用）
- **依賴關係**：落位決策（arch-thinking 三視角）——`diagram-selection`（跨命令 domain 知識：選載體＋共性）← 消費者 illustrate 入口／artifact-menu／html-mode／EP 規劃；工具配方（mermaid/archify-gen/kbar/ui-visual-verify）留原地被 pointer 引用；html-mode 類型映射表主體遷 diagram-selection 成單一源。無 code 符號依賴（docs 變更）；hook 語義 ripple 見 §S6 機械掃描（`rg "hook 1|hook 2" skills/` 命中 11 檔，逐檔判讀殼生命週期語義處）
- **類似實作**：reference skill 分層先例（acceptance-evidence／lsp-navigation——rule 核心＋skill 深層）；kbar-form-analysis 的 vision 契約（共性段的 domain 實例）
- **風險假設**：① mmdc 環境可用（AIR-29 已實證 npx -y 可跑；等級高，§S5 POC 驗證）② mmdc/CDN dark 主題整合手段（init 例外與 `-b transparent` 行為——等級高，POC＋官方文檔 grounding，禁憑記憶寫 CLI 旗標）③ 殼 template 與 iframe 圖高度自適應（等級中，POC 截圖驗）④ 無致命等級（任一路徑失敗都有 fallback：CDN↔mmdc 互補、配方以 POC 實測回寫）

## 段落劃分原則

S1→S2→S3 為知識載體建置（互相引用，S1 先立單一源）；S4 獨立（role＋機械重投影）；S5 驗證回寫 S2/S3；S6 周邊同步掃描（含 hook ripple）；S7 獨立可延。全部段落驗證自足（rg 錨點＋一致性）。

---

## S1 — 新建 `skills/diagram-selection/SKILL.md`＋索引註冊

### Context
- UC 引用：實作「畫圖載體選型」「vision 判讀標準化」
- 依賴：S2/S3/S4 將 pointer 引用本檔（單一源先立）；材料＝裁定包 D1＋四份 handoff＋kchart/MOS-42 共性
- 錨點：`skills/CLAUDE.md` 索引「工具與查詢」組（mermaid 條目旁）；寫作紀律載入 instruction-writing skill（元資訊禁止、pointer 式引用、Signal/Noise）

### 修改要點
1. frontmatter：name `diagram-selection`；description 觸發詞前置——選圖、畫圖工具、圖表選型、何時用 archify、mermaid vs archify、載體選擇、report shell 圖、換形態、vision 判讀契約（精簡——ZCode 端 description 超限**整顆 drop 非截斷**，紅線表述引 skills/CLAUDE.md「description 寫法」單一源，不另寫數字〔F12〕）
2. 判準四問：①邊有無結構化通道（時間軸/管線/狀態/層次柵格——有→mermaid 或結構容器）②交錯度（自由 node-link 無通道）③是否圖論問題（層次/對照/分類→HTML 塊/表格——「不是圖的東西別硬畫圖」）④成本軸（mermaid 宣告式 1 輪；archify LLM 產線高一至兩個數量級——~10 輪量級/圖、單圖十分鐘級、時間絕大多數耗在 LLM 生成〔數量級判準；實測細節錨材料裁定包，統計數字不寫進 skill——F10/F13〕；domain 資料圖機械渲染秒級）
3. 載體對照表：sequence（最強）/stateDiagram（5 狀態 8 邊 label≤20 字餘裕上限）/ER（實體≤6）/flowchart LR 線性=1 輪；TB 自由 ≤8 節點勉強（畫前先問能否改形態）；class 兩層判準（⚖️ C1）；HTML 塊（多分支決策/前後對照/分層——div/flex/grid 零管線）；archify=**最後手段**（user 裁示），獨有價值三條（互動導航 pan/zoom/search、大規模依賴網、無通道大圖的防交錯結構容器＋validate gate）；表格（分類學）；domain 渲染器 pointer（kchart 型——資料綁定圖走機械渲染 lib＋領域薄殼，LLM 只在判讀端）
4. 換形態招：組件→sequence（執行時誰呼叫誰）；自由 flowchart→分層；class→表格；交錯超標第三選項＝刪邊/降文字記載（取捨顯式記錄，事實不丟）
5. 跨載體共性慣例池（三弧同構）：vision 契約三段式（逐張結構化輸出＋誠實段「目視分不出來明說」＋跨案觀察段）；每 agent ≤10-15 張；抽樣錨定全樣本（反倖存者偏差——只看輸家/贏家的 vision 結論會被數字反駁）；**盲判＝Writer/Reviewer 分離**（既有結論不進判讀包；渲染端 `--blind` 撤結論欄是機制化落點——F5）；self-contained 圖（關鍵數值燒進圖題，agent 不回查表）；渲染/判讀分離（機械渲染端確定可批次，LLM 只放消費端）；**git policy 詳 illustrate-html-mode git 段（單一源 pointer，此處不重述條目——F6）**；fail-visible 批次（單案 FAIL 不拖垮、manifest 增量記）；契約 lib 化＋領域薄殼（複用單位=圖形契約非成品圖）；暫存 code「.agent-tmp 先暫存→正式化上抽 repo」生命週期（F5）；人類板設計（正反分頁/worst-first/每卡自帶 gate 數值/iframe lazy）；載體限制顯式登記（避讓缺失/座標裁切等寫進文檔非每次重踩）；文檔 drift 污染下游（判讀預期 code＋文檔雙源核對）
6. 邊界與指針（不重述內容）：mermaid skill（渲染配方）／illustrate-html-mode（殼整合＋guard）／archify-gen role（產線紀律）／ui-visual-verify（UI 驗收編排）／kbar-form-analysis（domain 判讀契約實例）
7. 長度預算 ~130 行；教訓錨引用材料（不內嵌長案例，一句話+材料路徑）

### 驗證策略
- `rg -n "最後手段" skills/diagram-selection/SKILL.md` 定位句在場；rg 指針五目標路徑皆存在（fd 驗證）
- `rg -n "三段式|10-15" skills/diagram-selection/SKILL.md`（vision 標準化錨——F6）＋`rg -n "對照→表格" skills/diagram-selection/SKILL.md`（⚖️ C1 兩層判準錨——F6）
- skills/CLAUDE.md 索引新增條目；`rg -c "diagram-selection" skills/` ≥3 檔命中（S2/S3 完成後交叉引用成立）
- instruction-writing 自檢：無版本號/日期/統計元資訊（數量級表述非統計）

---

## S2 — mermaid skill 擴充：殼內嵌配方（雙路徑＋陷阱＋seamless）

### Context
- UC 引用：實作「mermaid 殼內無縫嵌入配方」；依賴 S1（選型 pointer 回引）；材料＝MOS-41 §五＋AIR-29 ff §渲染教訓＋MOS-27 §三
- 錨點：`skills/mermaid/SKILL.md`（現 50 行，style 規範段之後增段）；外部 CLI 旗標（`-b transparent`、dark 主題手段、`mermaid.run` API 形態）**必須官方文檔 grounding（WebSearch/Context7），禁憑記憶**——S5 POC 實測後回寫定稿

### 修改要點
1. **雙路徑**：(A) mmdc 預渲染——`npx -y @mermaid-js/mermaid-cli -i x.mmd -o x.svg -b transparent`（主題整合手段以 POC 實測+文檔為準）；(B) CDN runtime lazy render——`startOnLoad:false`＋nav 切換後 `mermaid.run({querySelector:'<目標節>.show pre.mermaid:not(:has(svg))'})` 逐節補渲染
2. **陷阱六條**（MOS-41 §五全收——F2）：`display:none` 容器 flowchart 崩潰（getBBox 量測 0→假 Syntax error；sequence 線性免疫）；單次 guard 陷阱（`_mmRendered` flag 只渲染第一節——`:has(svg)` 排除已渲染者是關鍵）；parse 除錯（DOM textContent 已被 error SVG 污染——從原始檔正則抽乾淨源碼反證）；特殊字元易誤歸因（保守 label 仍值得但非首要嫌疑）；mmdc `id="my-svg"` 碰撞（同頁多張 inline 互污染——**inline ≤1/頁**，其餘存檔＋iframe/img 隔離；mmdc `-I <svgId>` 官方旗標可自訂 id，是否連 style selector 一起改寫由 §S5 POC 驗證）；**驗收閉環**（截圖→vision 判讀→修→複驗；`mermaid.parse` OK ≠ 渲染 OK ≠ 佈局可讀——三層各有失敗面，vision 是後兩層唯一防線）
3. **無縫融合一體準則**：同主題（殼 dark→圖 dark chrome）、透明底、同字體、尺寸自適應、無 iframe 痕跡（border 0/scrollbar/白底不出現）
4. **init 例外（bounded）**：mermaid SKILL.md :14 核心原則句加「MD 語境」限定詞（原句全稱否定會與新段逐字矛盾——F10）；MD 語境維持禁 `%%{init}%%`＋顯式 fill+color；**殼語境允許** `mermaid.initialize`（theme/themeVariables 驗 chrome 色）——API 形態已官方 grounding（v10 `startOnLoad:false`＋`mermaid.run({querySelector})`；`initialize` 是唯一配置通道）；節點顯式 fill+color 兩語境都保留（可讀性不依賴主題）
5. `.mmd` 源進 git 慣例 pointer（詳 S3 html-mode git 段）

### 驗證策略
- rg 新段關鍵詞（`-b transparent`、`:has(svg)`、`id="my-svg"`、init 例外句）命中
- 與 S5 POC 結論對帳：POC 推翻的旗標/API 形態即改寫（S5 完成後複查本段）

---

## S3 — `illustrate-html-mode.md` 改版：分派、嵌圖形態、hook 時間點、guard 分層

### Context
- UC 引用：更新「illustrate html 模式」＋「殼生命週期時間點」＋「止損分層」
- 依賴：S1（分派表單一源）；材料＝裁定包 D2/D3/D4/D5＋MOS-27 NEW-1/2/5＋AIR-29 ff
- 錨點：`skills/_common/illustrate-html-mode.md` 各段（類型映射 :23-34／殼生成分工 :57-63／掛點表 :83-92／輪數 guard :112-118／產物生命週期 :120-125／重生 :127-138／教訓 :147-157）

### 修改要點
1. **類型映射表→「illustrate 概念→載體」映射（語義修訂、不遷移——F1 兩軸分層）**：diagram-selection 擁**圖型軸**判準（sequence/stateDiagram/…→載體）；本檔擁**illustrate 概念軸**映射（boundary/data-flow/call graph/class slice→mermaid 圖型或 archify 圖型或 HTML 塊），段名改「概念→載體映射」，artifact-menu 指向維持本檔不變。明訂：**archify 是最後手段**（user 裁示「非必要不用」，判準源 S1——就地重申屬消費端 gate 強調）——命中三獨有價值才走 archify-gen；mermaid/HTML 塊為殼補圖預設
2. **殼嵌圖四形態**（AIR-29 ff §5）：inline SVG（≤1/頁）／iframe+`.svg` 檔（其餘 mermaid）／iframe+`?embed=1`（archify）／HTML 塊直寫殼內（層次/對照）；外框統一 frame-wrap（標題列＋↗ 全屏連結）；**無縫一體準則**引用 S2；md 檔 mermaid code block 連結＝死內容禁例重申（未渲染 .md 不進殼）
3. **git 慣例擴 mermaid 線（⚖️ C3 單一源）**：`.mmd` 源進 git——任務家與 `arch-report/<主題>/` 兩場景皆與 JSON IR 對位同存；`diagram-*.svg` 渲染產物不進（任務家既有 gitignore 覆蓋；arch-report 場景 §S6 補 `arch-report/**/*.svg` 條目——F3）；「源進 git、產物不進、一命令再生」原則明文覆蓋兩載體
4. **輪數 guard 分層（D2①/D3——本段為止損閾值與 rounds ledger 規格單一源，S4 role 側 pointer 引用——F5）**：新增「**>4 輪不收斂＝caller spec 過重**——停手回報 caller 改 spec（減 lanes/去堆疊/砍 sublabel/次要事實沉 cards）重跑，非 agent 不努力」；12 輪降級＋18 session 預算維持；**rounds ledger**：archify-gen 每輪 validate 摘要（輪次/checks/errors/變更處）append `<主題>.rounds.md` 與 candidate 同目錄、隨 JSON IR 進 git，並列入機械底稿源清單（html-mode:63——F15）
5. **caller 端事實清單義務（D2⑥⑦，殼生成分工段落地——F1/F9）**：archify 委派前事實清單自帶**幾何分類**（主線/分支/消費＋標註哪些邊跨圖、哪些垂直相鄰）＋起手規格一句（3 lanes 起手×零堆疊×5-6 節點/lane、短 sublabel、fromCol/toCol 按 phase 帶切乾淨禁重疊）——事前預防，非只靠 >4 輪止損
6. **掛點表 D4(b)**：hook 1＝建殼骨架＋章節敘事（零管線內容——HTML 塊/表格可），**渲染管線圖（mermaid/archify）不於 hook 1 產**，diagram 槽留 degraded 待裝（殼頭標「圖待 hook 2 裝」；hook 1 `open` 提前預覽行為**維持**——F14 裁定）；hook 2＝產圖一次＋實作章節＋delta tour；修訂重投影僅大方向級變更
7. **殼生成分工補 mermaid/HTML 塊路徑**：三 tier 中 archify-gen 只接 archify 圖；mermaid（mmdc 機械 CLI）與 HTML 塊由主 session/lite 產；vision 驗收不變（label 級唯一防線）
8. **containment/readability 分離（MOS-27 NEW-2）**：交付標準＝validate showcase 全綠＋readability（最小投影字 ≥6px）；containment overflowY 如實並列回報（縱向組成超一屏是組成事實，iframe 可捲場景非致命）；**禁為 containment 壓字級**
9. **重生程序擴步**：`.mmd` → mmdc → `diagram-*.svg`（與 archify JSON→deliver 並列）
10. 刪邊顯式記錄慣例（MOS-27 NEW-1）入 authoring 段

### 驗證策略
- rg：`>4 輪|rounds.md|最後手段|.mmd|containment` 各命中且語義就位；舊「hook 1 建殼＋計畫章節」句已改骨架語義
- 跨檔一致性：S6 hook 引用掃描後 0 殘留（詳 S6 驗證）

---

## S4 — `agents/roles/archify-gen.md` 修正＋sync_agents 重投影

### Context
- UC 引用：更新「archify-gen 產線」；材料＝裁定包 D2 role 側 12 條中的 agent 面＋AIR-29 ff §五-5＋MOS-41 避坑階段 3
- 錨點：`agents/roles/archify-gen.md`（做法 1-5＋紀律段）；`scripts/sync_agents.py`（投影生成器——AIR-29 剛落地）

### 修改要點（role 新增/修訂條目，保持 role 檔緊湊）
1. 做法 2 補：`schema_version` **per-type**（architecture=1、workflow=2——現只標 workflow 2 是誤套源）；`meta.locale` 繁中內容**省略**＋回報揭露「Viewer UI fallback English」（C2 定值，勿填 zh-CN 假裝）；schema 靜態坑清單（避坑階段 2——F4：`sources` 是 `{path,line,label}` object 陣列且 path 須存在於 pinned revision；component `type` 固定六種、語意自由映射別要求對位；workflow node schema 無 `sources` 欄；`visual_preset` enum 四值）
2. 新紀律：**validate 診斷建議值直接抄**（labelAt/座標——自選被攔時 deliver 附建議照抄一發過；禁自發明座標，盲猜是 12 輪 dataflow 的主因）
3. 新紀律：repair 輪 **context 節制**——只 Read candidate 檔＋最新 `--json` 診斷輸出；禁重讀 SKILL/範例/大檔（實測單 run 6.5M+ input 主因之一）
4. 新紀律：**每次修一類、同類全修**（防擠牙膏——R2-R5 每輪 1 error 形態）；修復順序固定 routing（crossing/corridor）→label（clearance/labelAt）→rhythm/readability
5. author 期幾何前移**七條**（AIR-29 ff 五條＋避坑階段 3 兩條——F3）：邊分級（跨 >2 node 欄寬或中隔 container→必給 via/channelX/Y 走邊緣通道；垂直相鄰→釘 fromSide/toSide）；稠密區 label 先佔位（labelAt/labelSegment 指長段）；viewBox 寬×字級連動（桌面投影 ≥6px，寧窄勿寬）；節點離 container 邊框留距（貼邊→border run）；meta 欄位先查 schema enum 再填；**對角交叉根治＝對調組件位置**（左下↔右上交錯必交叉，微調 via 只引發穿組件新錯）；同 lane 同 col 節點顯式 `yOffset`（慣例值 88/176，否則 node-overlap）
6. 止損：**>4 輪未收斂→停手回報「建議 caller 改 spec」**；每輪 validate 摘要 append rounds ledger——**閾值與 ledger 規格以 illustrate-html-mode 輪數 guard 段為單一源**（本 role 不重述數字與格式，pointer 引用——F5）
7. 圖語義：刪邊取捨顯式記錄（圖備註/cards，事實不丟）；containment fail ≠ 圖壞——readability 是底線，如實並列回報不宣稱視覺全過

### 驗證策略
- `uv run python scripts/sync_agents.py` exit 0；`diff agents/zcode/archify-gen.md agents/roles/archify-gen.md` 僅 frontmatter 差異（生成註記＋pins）；`diff agents/claude/archify-gen.md agents/roles/archify-gen.md` 同原則（F8）；冪等重跑 `git diff --stat agents/` 為空
- rg role 新關鍵詞（`schema_version`、建議值、rounds）命中；description 準確反映（lite 定位不變）

---

## S5 — mermaid seamless POC（evidence artifact）

### Context
- UC 引用：驗證「mermaid 殼內無縫嵌入配方」；依賴 S2/S3 配方草稿；位置 `.agent-tmp/poc-mermaid-seamless/`（不進 product scope、不被 production 引用）
- 環境：mmdc 已有 AIR-29 實證；playwright 依 ui-visual-verify 慣例

### 執行要點
1. 深色殼頁（借 illustrate-report-shell.html 配距）兩章節 nav 切換：圖一 sequence、圖二 flowchart LR（label 帶 CJK 驗字體）
2. 路徑 A：mmdc 預渲染（`-b transparent`＋dark 主題手段——官方文檔 grounding 後下旗標）→ inline×1＋iframe/`<img>`×1 兩嵌法對照
3. 路徑 B：CDN lazy render（startOnLoad:false＋逐節 `mermaid.run` `:has(svg)`）——含 display:none 章節切換後補渲染
4. playwright 截圖（殼整頁＋逐章節）→ spawn vision-review agent（背景）以無縫準則判讀（主題一致/透明底/無框痕跡/字可讀/CJK）
5. 結論回寫：POC 推翻的旗標/嵌法即改 S2/S3；**加驗 `-I <svgId>`**（兩張不同 `-I` 渲染後檢查 style selector 是否隨 id 改寫——改寫→id 碰撞有官方解法可註記鬆綁條件；不改寫→維持 inline ≤1/頁）；時間盒——mmdc npx 下載 >3min 視同缺場→只驗路徑 B 如實記錄（SM-10；F11）

### 驗證策略
- 截圖在場＋vision verdict 文字回報（PASS/FAIL 逐項）；配方與實測對帳結論寫進本段完成記錄；POC 產物隨 post-build 清理（.agent-tmp 生命週期）

### S5 完成記錄（verdict 落盤——UF1 補）

- 機械驗證（shoot.py stdout）：iframe autofit height=**304px**（svg viewBox 高 303.06 → ceil）；s3 runtime-rendered svgs=**2/2**（nav 切換後 `:has(svg)` 逐節補渲染成功——display:none 陷阱處理正確）；console errors/warnings＝**零**
- `-I <svgId>` 加驗：`diagram-b.svg` root id／marker id／style selector **全部**隨 `-I diagram-b-svg` 改寫（`#diagram-b-svg`×5、marker 前綴改寫）、`my-svg` **零殘留**——id 碰撞有官方完整解方，S2 陷阱 5 已回寫鬆綁（帶唯一 `-I` 可多張 inline）
- vision-review verdict（逐張）：`s1-inline.png` **PASS**（sequence 完整、中文標籤可讀、participant 深底淺字、透明底與殼一體）；`s2-iframe.png` **PASS**（三 styled 節點齊、無捲動條/白底/多餘邊框、高度緊收）；`s3-cdn-lazy.png` **PASS**（兩圖 runtime 渲染完成非原始碼/錯誤 bomb；底緣屬 viewport 裁切非渲染缺陷——vision 標註）。跨張：三形態主題同系、零外部嵌入感斷裂、emoji 全彩無 tofu
- 回寫閉環：S2 配方與實測對帳一致（無推翻項——mmdc 21.6s 首渲染在 3min 時間盒內、兩路徑全通）

---

## S6 — 周邊同步掃描（hook ripple＋artifact-menu＋gitignore＋memory）

### Context
- UC 引用：貫穿；錨點：`rg -n "hook 1|hook 2" skills/` 命中 11 檔（CLAUDE/kanban-board/tour-bootstrap/corpus-recall/debrief/commit/post-build/execution-plan/illustrate-html-mode/code-review/implement）

### 修改要點
1. hook 語義掃描：逐檔判讀命中行——**殼生命週期語義**（hook 1 建殼產圖相關）同步為骨架語義；zcode hooks/其他語義不動。改點**雙向**（F9/F11）：①hook 1 舊語義清理——execution-plan「定稿生 Report Shell〔hook 1〕」與「+ 可選 archify 圖」句、html-mode「建殼＋計畫章節」、CLAUDE.md 拓撲圖；②**hook 2 增產圖職責**——post-build 階段 5 職責清單（:70-79）、implement 階段 6 fallback（:291）、CLAUDE.md:50 各補「產圖一次（依 diagram-selection 選型）」（只清舊句不增職責＝弧末 degraded 槽永遠無人裝）
2. `skills/illustrate/SKILL.md`：輸出模式表 HTML row 提四載體＋選型 pointer；Supporting Files 表增 diagram-selection
3. `skills/_common/illustrate-artifact-menu.md`：「HTML 圖型映射」行**維持指向 html-mode**（概念軸映射屬主——F1 兩軸分層裁定），僅核對文字與新段名一致；`_common/illustrate-examples.md`「類型映射」詞同步（F2）
4. `.gitignore` 檢查：任務家 `diagram-*.svg` 排除現況確認；**補 `arch-report/**/*.svg`**（arch-report 場景 mermaid 產物同原則不進 git——F3）；`.mmd` 不被誤吞——`git check-ignore ai-analysis/_tasks/09-06-diagram-selection-absorption/diagram-x.mmd` 期望 exit 1（F7）
5. memory 同步：`~/.zcode/cli/memories/projects/ai-rules-01610fbb20315a8b/memory/`——**ai-rules 側判例池繼承者＝`project_archify-illustrate-html-mode-eval.md`＋`project_archify-cost-review-0905.md`**（材料引用的 `reference-archify-illustrate-html` 是 mosaic 側 pool 條目名，本 pool 不存在——F8）補本弧終態（diagram-selection 單一源 pointer）；`project_air-23-illustrate-shell-template` 陳述矛盾修正（「archify 缺場」句→clone 在場事實）；`feedback_shell-diagram-quality-bar` 選型口徑蒸餾對齊裁定包（「mermaid 僅循序型」舊口徑→「sequence/stateDiagram/ER/LR=1 輪、TB 自由勉強、層次=HTML 塊」——F16）；`MEMORY.md` 索引 generator 重跑
6. `agents/AGENTS.md`：execution contract 表 :74「殼／圖渲染→spawn archify-gen」需求行——載體分流後語義需限定 archify 線（mermaid/HTML 塊不派 archify-gen；「主 session/lite 產」的執行者歸屬核對表行——F17）

### 驗證策略
- 舊語義清光（舊句清單逐項）：`rg -n "建殼＋計畫章節|可選 archify 圖" skills/` 0 殘留；`rg -n "類型映射" skills/` 0 殘留（段名改「概念→載體映射」後 5 處引用全清——F2/F9）
- hook 2 職責新增可驗：`rg -n "產圖一次" skills/post-build/SKILL.md skills/implement/SKILL.md skills/CLAUDE.md` ≥3 命中（F11）
- `git check-ignore ai-analysis/_tasks/09-06-diagram-selection-absorption/diagram-x.mmd` exit 1（源不被吞——F7）
- 跨檔 pointer 一致性：`rg -c "diagram-selection" skills/` ≥4（S1/S2/S3/S6 點）

---

## S7 — AIR-26 殘餘處置（可延段落）

### Context
- UC 引用：無新 UC（AIR-26 卡殘餘②清償）；錨點 `ai-analysis/_tasks/_archived/09-05-external-runtime-push-collection/index.html` degraded 槽＋`skills/model-routing/SKILL.md` push 收法決策樹事實源

### 修改要點
1. 讀 model-routing push 收法段→萃取決策樹事實（背景 Bash exit 喚醒/timeout 訊號家系/ETA-gate fallback）
2. **應用 S1 選型判準**選載體（決策樹型預期 mermaid；僅互動導航需求才 archify）
3. 產圖＋換裝 degraded 槽位（frame-wrap 形態對齊既有殼）；`.mmd`/JSON 源進 git、產物不進
4. **時間盒**：事實萃取＋產圖合計 >30min 或阻塞 → defer 並在完成報告列未決項（不阻斷主弧——F11）

### 驗證策略
- 殼 index.html 無 `class="frame-wrap degraded"` 使用點殘留（rg——掃使用點非 CSS 定義）；圖源檔在 git 追蹤清單（`.mmd` tracked、`diagram-*.svg` ignored）

---

## 整合策略

- 段落順序：S1→S2→S3（知識鏈）→S4（role＋機械）→S5（POC 回寫）→S6（掃描收斂）→S7（獨立）；S5 發現配方問題→回改 S2/S3 再複查
- baseline `a8072ce`：下游 code-review/post-build 以此為範圍邊界

## EP Review Findings — 09-06-diagram-selection-absorption（雙維度平行審＋主 LLM judge）

> 審查形態：結構維度＋完整性維度各一 Explore agent（lite/GLM，read-only）；judge 由主 LLM 執行。F 編號 = EP 內文修訂標記對應。

| ID | 嚴重度 | 檔案:行 | 問題 | 決策 | 狀態 |
|----|--------|---------|------|------|------|
| CF1 | 🔴 | ep 裁定包:52 | D2⑦ caller 事實清單幾何分類漏收（宣稱整包實漏 1） | ✅ | implemented（S3-5 caller 義務條） |
| CF2 | 🟡 | MOS-41 §五-5 | vision 驗收閉環（parse OK ≠ 渲染 OK ≠ 可讀）無落點 | ✅ | implemented（S2 陷阱第六條） |
| CF3 | 🟡 | 避坑階段 3 | 佈局鐵律漏 2 條（對角交叉對調/yOffset） | ✅ | implemented（S4-5 前移七條） |
| CF4 | 🟡 | 避坑階段 2 | schema 靜態坑大半漏 | ✅ | implemented（S4-1 清單） |
| CF5 | 🟡 | 裁定包:45 | kchart delta 漏 2 條（--blind 盲判/上抽生命週期） | ✅ | implemented（S1-5 池） |
| CF6 | 🟡 | ep SM 表 | 多條 SM checkpoint 缺機械 rg 錨 | ✅ | implemented（SM-2/7/9＋S1 驗證） |
| CF7 | 🔴 | ep S6:200 | `git check-ignore` 用 .agent-tmp 路徑（整目錄被 ignore）驗證必敗 | ✅ | implemented（改任務家形態＋exit 1 期望） |
| CF8 | 🟢 | ep S4 驗證 | claude/ 投影驗證無具體命令 | ✅ | implemented（diff＋冪等重跑） |
| CF9 | 🟢 | 避坑階段 1 | 起手規格無落點 | ✅ | implemented（併 S3-5） |
| CF10 | 🟡 | ep S1:90 | 成本軸統計數字 vs 統計元資訊禁令矛盾 | ✅ | implemented（數量級化＋材料錨） |
| CF11 | 🟢 | ep S5/S7 | defer 時間盒未量化 | ✅ | implemented（3min/30min） |
| SF1 | 🟡 | S3-1/S6-3 | 概念軸 vs 圖型軸分層矛盾（artifact-menu pointer 改向錯誤） | ✅ | implemented（兩軸分層寫死，映射不遷移） |
| SF2 | 🟡 | rg 類型映射×5 | 段名改名殘留面 EP 只覆蓋 1/5 | ✅ | implemented（0 殘留驗證＋examples.md 入掃描） |
| SF3 | 🟡 | .gitignore | arch-report 場景 svg 不被排除＋.mmd 放置未定義 | ✅ | implemented（補 glob＋兩場景放置） |
| SF4 | 🟢 | S1↔S2 | 檔案層互指成環 | ❌ | closed（符合 repo 互指慣例，記錄不修） |
| SF5 | 🟡 | S3-4/S4-6 | >4 輪閾值與 ledger 格式兩處全述（drift 種子） | ✅ | implemented（role 側 pointer 化，單一源 html-mode） |
| SF6 | 🟡 | S1-5/S3-3 | git policy 原則句兩處 | ✅ | implemented（S1 改 pointer） |
| SF7 | 🟢 | S1-3/S3-1 | archify 定位句兩處重述 | ⚠️ | needs-confirmation（消費端 gate 就地強調可辯護；已標注判準源 S1——user 可否決刪其一） |
| SF8 | 🟡 | ep S6-5 | memory 條目 `reference-archify-illustrate-html` 不存在（mosaic pool 條目名誤植） | ✅ | implemented（改現存 project_archify-* 兩條目） |
| SF9 | 🟡 | ep S6 驗證 | `hook 1.*圖` 正則恆真（0 命中），舊語義檢出力零 | ✅ | implemented（舊句清單逐項列舉） |
| SF10 | 🟡 | mermaid SKILL:14 | init 例外與核心原則絕對句逐字矛盾 | ✅ | implemented（:14 加 MD 語境限定） |
| SF11 | 🟡 | post-build:70-79 等 | hook 2 消費檔缺「產圖」職責（degraded 槽將無人裝） | ✅ | implemented（S6-1 明列三檔增職責） |
| SF12 | 🟡 | ep S1-1 | 「1024 字元」數字無 repo 依據（違自訂 grounding 紀律） | ✅ | implemented（引 CLAUDE.md 單一源表述） |
| SF13 | 🟡 | ep S1-3 | 統計寫入要求 vs instruction-writing 紅線（同 CF10） | ✅ | implemented（同 CF10） |
| SF14 | 🟢 | html-mode:87 | hook 1 open 行為（骨架殼彈出）去留未定 | ✅ | implemented（維持 open＋殼頭標待裝） |
| SF15 | 🟢 | html-mode:63 | rounds.md 未納機械底稿源清單 | ✅ | implemented（S3-4 附註） |
| SF16 | 🟡 | MEMORY.md:68 | `feedback_shell-diagram-quality-bar` 選型口徑與裁定包衝突 | ✅ | implemented（S6-5 補蒸餾） |
| SF17 | 🟢 | agents/AGENTS.md:74 | 「殼／圖渲染→archify-gen」行載體分流後語義變寬 | ✅ | implemented（S6-6 明確檢查項） |

**附加 grounding 收穫**（本弧執行中實測）：mmdc `-I, --svgId` 官方旗標存在（id 碰撞潛在官方解方——S5 加驗）；`-t dark -b transparent` 官方 README 實錄；mermaid v10 `run({querySelector})`＋`startOnLoad:false` API 形態確認。

## 收尾步驟（docs mode）

1. 受影響命令行為已反映＋`skills/CLAUDE.md` 工作流索引同步（S1/S6 內完成，收尾複查）
2. AIR-30 結案兩步＋弧結案蒸餾第三動（`-s Done --final-summary` → `--ref` 換 done/ URL；memory 條目蒸餾終態 facts——S6 已預寫，結案時對帳）
3. 從 Scenario Matrix 提煉消費場景寫入 AIR-30 卡 notes（`--append-notes`）
4. post-build 收尾鏈（consistency→metadata-sync→殼 hook 2）止步 commit 前；.agent-tmp POC 清理
