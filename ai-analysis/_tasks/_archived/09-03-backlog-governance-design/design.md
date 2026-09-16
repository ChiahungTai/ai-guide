# Backlog.md 治理設計（卡即 handoff）

> **backlog**: AIR-14（中繼站治理設計，兩族合一）  
> **baseline**: `d121837`（2026-09-03，與卡 desc 一致）  
> **EP**: [ep.md](ep.md)（docs mode、4 段）  
> **Task Brief 殼**: [index.html](index.html)（sidebar＋雙 archify 流程圖）  
> **圖 IR**: [card-lifecycle.workflow.json](card-lifecycle.workflow.json)（任務型）／[relay-stations.workflow.json](relay-stations.workflow.json)（檔案型）  
> **相關機制**: [kanban-board skill](../../../skills/kanban-board/SKILL.md)／[self-contained-prompt skill](../../../skills/self-contained-prompt/SKILL.md)／[execution-plan skill](../../../skills/execution-plan/SKILL.md)／[handoff skill](../../../skills/handoff/SKILL.md)／[at skill](../../../skills/at/SKILL.md)／[collaboration-constraints rule](../../../rules/collaboration-constraints.md)  
> **排程真相源**: [schedule-registry.md](../../../ai-analysis/schedule-registry.md)（本卡 S2 建檔）

---

## §0 範圍與已決策（勿重辯）

### 問題與交付物

本設計覆蓋卡 desc 列出的全部 11+ 設計問題（§2、§3、§4 開頭逐項映射標註）。交付物＝本檔 `design.md`（一弧全生命檔案同處，結案隨任務家遷 `done/`）＋[`schedule-registry.md`](../../../ai-analysis/schedule-registry.md) 初版＋本檔 §5 回歸驗證＋§6 文檔化落地清單。**本卡不執行 skills/rules 手術**——手術規格與驗證命令見 §6，執行屬後續卡。

### 已決策六條（user 09-03 裁定，全文不再論證對錯，只落「怎麼執行」）

| # | 決策 | 備註 |
|---|------|------|
| ① | 兩族合一框架：任務型（backlog board——工作意圖的進出口）＋檔案型（repo dot-area——工作產物的暫存區） | 本檔 §1 統一框架以此為脊柱 |
| ② | 討論題即時不建卡——對話即載體，session 斷才落 draft | 對應 §2.4 進口形態一 |
| ③ | `drafts/`＝未承諾／觸發型進口（首例：`drafts/rules-audit`） | 同上 |
| ④ | 退場走 `archive/` 非 `delete`（可復活；AIR-4 先例） | §2.9 出口 |
| ⑤ | `_inbox/` 不採——`drafts/` 即進口（本卡定案收口；理由：進口分裂、solo 無外部湧入、多一治理面） | §2.4 收口 |
| ⑥ | 卡三層分工：`desc`＝決策層／`EP`＝規劃層／`notes`＝留言層 | §2.1 |

---

## §1 統一框架——兩族 × 四問

### 1.1 兩族定義

| 族 | 是什麼 | 承載物 | 進口代表 | 出口代表 |
|---|--------|--------|----------|----------|
| 任務型 | backlog board——「工作意圖」的中繼站 | 卡（To Do／Done） | 對話拍板建卡／`draft` 未承諾池 | Done 欄 → `completed/` 清場；`archive/` 退場 |
| 檔案型 | repo dot-area——「工作產物」的暫存區 | 檔（暫存產物／一次性 context／local finding） | `.agent-tmp/`、`.at-contexts/`、`.review/` | 夜間掃腿 mtime 刪（7／7／30 天緩衝）；有價值先升格 |

兩族共用同一套治理判定：**有進有出才是對的**。任何持續流入的面必須有對應的流出腿；「只進不出」或「進出口沒人知道」即治理缺口。

### 1.2 共同四問（每區必答，作為 §2、§3 各區小節的固定表頭）

1. **誰進來**——哪些來源、什麼形態會流入此區
2. **停多久**——時限語義是**緩衝不是保存承諾**（被續用會 `touch` 刷新 `mtime`，門檻為最後被需要時間）
3. **誰清**——session 自清為第一腿，夜間掃腿為保底
4. **清去哪**——刪除前判「值得保存嗎」：有價值升格進 `EP`／`reports/`／`memory`，不是搬移

### 1.3 治理判定

一個區治理合格 ⇔ 四問有答案 **且** 出口腿真存在（能跑、有人掛、首跑驗證過）。新 dot-area 准入門檻（§3.4）即此判定的實例化。

---

## §2 任務型治理——卡即 handoff 契約

> 覆蓋卡 desc 設計問題：卡即 handoff 契約（desc 何時夠格）、drafts 進口慣例、升卡流程、notes 治理、兩層判定、「做 AIR-N」起手式、EP 修訂時 desc 同步義務。

![任務型卡生命週期](diagram-workflow-card.html)

*圖：任務型卡生命週期——卡即 handoff（archify workflow，上為 Board 承諾池、下為 Session 執行；亮暗切換、pan/zoom）*

### 2.1 三層分工（已決策⑥）

| 層 | 欄位 | 放什麼（只放這個） | 不放什麼 |
|---|------|---------------------|----------|
| `desc` | 決策層 | baseline／已決策勿重辯／範圍／驗收——**不變的、跨 session 需共識的** | 怎麼做、過程記錄、指針 |
| `EP` | 規劃層 | 怎麼做：段落／錨點／驗證策略／依賴與風險 | 決策本身（決策在 desc） |
| `notes` | 留言層 | 接手當下需知的交代：實踐記錄、漂移修正、指針、session 間留言 | 規劃性內容（那是 EP 的事；重複即該升 EP 的信號） |

三層各有歸宿：`desc` 隨卡入 `archive/` 或 `completed/` 可復活；`EP` 隨任務家遷 `done/` 永久保存；`notes` 隨卡歸檔為考古材料（過程留言不沉澱，沉澱走正規歸宿——`memory`／`skill`／`rule`）。

### 2.2 卡即 handoff 契約與 desc gate

**定義**：一張 To Do 卡的 `desc`＋`notes`＋`references`＋`EP`（若有）**四件拼裝**，承接 [self-contained-prompt skill](../../../skills/self-contained-prompt/SKILL.md) 的 handoff 標準八欄。接手 session 說「做 AIR-N」，憑卡即能接手，不重辯已定之事。

**八欄映射表**（以 AIR-14 為實例）：

| handoff 八欄 | 卡拼裝承載 | AIR-14 實例 |
|--------------|------------|-------------|
| 任務一句話 | `title`＋`desc` 首句 | Backlog.md 治理設計（卡即 handoff）＋「中繼站治理設計（兩族合一，2026-09-03 開卡）」 |
| baseline | `desc` 標記 `〔baseline：ai-rules d121837〕` | `d121837` |
| 來源 EP | `references` 第二項 `ai-analysis/_tasks/.../ep.md` | `ep.md`（AI 消費源；人類消費源為 `index.html`） |
| 已完成 | `EP` 段落進度或 `notes` 記錄 | EP §0 已完成的研究；S1-S2 進度 |
| 已決策 | `desc`〔已決策勿重辯〕段 | ①-⑥ 六條 |
| 下一步 | `notes` 接手指針 | 接手指針 ①-⑤ |
| 驗收 | `desc` 末尾〔驗收：...〕 | 「設計文件覆蓋上述全部＋以 MOS-14 與本卡群為回歸樣本；文檔化落地清單含 sync-sources 檢查」 |
| 承接不重做 | `desc` baseline＋`notes` 記錄 | baseline 錨＋「兩次 desc 漂移修正」記錄 |

**desc gate 三必有**（適用時機＝**卡狀態 To Do 且預期跨 session 執行**）：

1. `baseline`——`〔baseline：<repo> <short-hash>〕`
2. `已決策勿重辯`——`〔已決策勿重辯：①...〕`
3. `驗收`——`〔驗收：...〕` 或 `<!-- SECTION:ACCEPTANCE -->` 等價

豁免：session 內即辦即結的記錄卡（如 AIR-15，開卡即做即結，To Do 生命以小時計）無需過 gate。gate 是**內容 gate 非格式 gate**——語義標記自由（`〔〕`、`**bold**`、`### 驗收` 皆可），只要求三要素**語義在場**。

不做 hook：`desc` 完備性是語義判斷（「已決策」是否真列出關鍵決策不是字串有無），不滿足 [載體決策樹](../../../AGENTS.md) 的「純機械＋單一入口＋無語義例外」三者條件。改以慣例＋軟自查：

```bash
rg -c "baseline|已決策|驗收" backlog/tasks/<卡檔>.md  # 應 ≥3（豁免卡除外）
```

### 2.3 兩層判定（不新造，對齊既有規模分級）

對齊 [execution-plan skill](../../../skills/execution-plan/SKILL.md) 的流程規模分級（`simple`／`standard`／`full`——判準＝檔案數＋跨模組＋風險）——**本設計不新造判定**：

| 層 | 對應分級 | 卡形態 | handoff 主體 | 判定時點 |
|----|----------|--------|--------------|----------|
| small | `≈simple` | 不建 EP——卡即 handoff，卡自足直行 | 卡 `desc`＋`notes` | **承諾時**（升卡/建卡前的 `/execution-plan` 分級——與 §2.4 分界線同一站） |
| standard+ | `standard`／`full` | 寫 EP——卡為追蹤錨（`references` 指向 EP）＋EP 為 handoff 主體 | `EP` | 同上 |

**執行端不分岔**：起手式（§2.6）讀卡即知形態（`references` 有無 EP），不做第二次規模判定；執行中 scope 遠超 `desc` → 先升 EP 再動工（逃逸口，非分岔——與 §2.5「notes 像EP」信號同源）。

AIR-13（To Do 等待型，desc 裝裁決＋批次清單、規劃層薄）為 small 自洽實例；MOS-14 與本卡 AIR-14 為 standard+ 實例。

### 2.4 drafts 進口慣例（已決策②③⑤）

**區分線＝有沒有開 `/execution-plan`**：未開＝`draft` 未承諾池；已開（規模判定＋UC 盤點過）＝`task` 承諾池。draft 三形：

| 形態 | 觸發 | 格式 | 出口 |
|------|------|------|------|
| 想法捕獲 | 有需求直覺、還沒開 `/execution-plan` 細拆——想到要做先記，不佔承諾池 | `backlog draft create "<想法>"`（一句話＋範圍草案） | 熬到 `scope 定＋跨 session＋可驗收` 三條齊 → promote |
| 觸發型 draft | 條件到才做（如 `drafts/rules-audit`：目標／觸發條件／範圍草案） | `backlog/drafts/<topic>.md`（標題＋觸發條件＋草擬範圍） | 條件滿足→`backlog draft promote <id>` 升卡（升卡時蒸餾 `desc` 過 gate）；條件永久失效→刪 |
| session 斷結晶 | 討論題尚未拍板但 session 將斷、對話即將丟失 | 同上，內容為對話結晶摘要 | 同上；或在對話中拍板→直接走升卡流程（不經 draft） |

**收口**：`_inbox/` 不另設進口——`drafts/` 即進口（已決策⑤）。理由：進口分裂增加一治理面，solo 場景無外部批量湧入，`drafts/` 已覆蓋「未承諾／觸發型」語義。

**升卡流程**：對話拍板 → 跑 `/execution-plan`（規模判定＋UC 盤點）→ `simple` 直接 `task create`（過 gate，不建 EP）／`standard+` 寫 EP 後建卡（雙 ref 掛 EP）；`draft`→`promote` 時同站判定；執行中 scope 漲 → 升 EP（§2.3 逃逸口）。

### 2.5 notes 治理

- **與 EP 邊界**：規劃性內容（怎麼做）住 `EP`，`notes` 只收接手當下需知（`EP` 已有不重複）。重複即治理缺口。
- **長度**：無硬限。**機械信號**＝`notes` 開始像 `EP`（出現段落結構／pseudo code／驗證策略）→ 該升 `EP`。
- **結案蒸餾＝不做**。durable lesson 走正規歸宿（`memory` 四問／`skill`／`rule`），`notes` 隨卡歸檔為考古材料。過程留言不沉澱，沉澱走正規歸宿——這是本治理與「結案把 notes 提煉回 desc」的顯式分歧。

### 2.6 「做 AIR-N」起手式五步

任意要動某卡的 session，第一個動作必須是：

```
① backlog task edit <id> -s "In Progress"   # 第一動——平行 session 可見（kanban-board 機制單一源 §開工）
② 讀卡三層：frontmatter → desc → notes → references  # 了解決策與接手指針
③ 讀卡知形態（references 有無 EP——形態承諾時已定 §2.3，此步不重判；scope 遠超 desc → 先升 EP 再動工）
④ 新鮮度核對——
     desc baseline vs `git log --oneline <baseline>..HEAD` 非空→對照 desc 範圍確認；
     notes relay 宣稱（如「排程真相源」材料）→機械驗證當前狀態（relay 快照落後實證）
⑤ 開工雙 ref（kanban-board 雙 ref 內建合約）：
     backlog task edit <id> --ref "<http URL>,<repo 相對路徑>"
     # http URL＝board 可點連結（ai-rules 形態見下）；相對路徑＝AI/VSCode 消費
```

ai-rules report URL 形態（實測 2026-09-03；晚間二次修訂）：`http://127.0.0.1:6421/ai-rules/<相對於 ai-analysis/ 的路徑>`——route root 即 `ai-analysis/` 內容，URL **不含** `ai-analysis/` 段。例：`ai-rules/_tasks/09-03-backlog-governance-design/ep.md` 實測 200；保留 `ai-analysis/` 前綴形態實測 404。md preview＝**中央掛載**（2026-09-03 晚定案，選項②）：viewer 單一源版控於 `report-assets/_md-viewer.html`、report server 掛 `viewer=` route——preview URL 形態 `http://127.0.0.1:6421/viewer/_md-viewer.html?p=/<route>/<相對於該 route root 的路徑>`（viewer `fetch(?p=)` 同源絕對路徑，可渲染任一 route 的 md；per-route 副本不新增）。卡的 http ref 過渡形態用此 viewer URL，殼建好後換殼 URL。

### 2.7 EP 修訂的 desc 同步義務

**決策層變更才同步**：

| 變更類型 | 是否回寫 desc | 例子 |
|----------|---------------|------|
| scope 擴張／收縮、驗收校準、已決策翻案（須 user） | ✅ 回寫 | MOS-14 F-1：驗收 110→80-100 區間校準屬決策層，應回寫 desc |
| 規劃層調整（段落重排、錨點修正、驗證策略調整） | ❌ 不動 desc | 純 EP 內部重排 |

機械觸發：`ep-review` findings 含 F-1 型（scope／驗收校準）→ apply 時同步執行（執行者負責 `--description` 全量替換）。

反證樣本：MOS-14 的 F-1 校準寫進 EP 未回寫 desc（desc 仍寫「~75-80」）＝同步缺失實證（見 §5）。

### 2.8 出口

- 結案兩步→Done 欄留板（`task edit <id> -s Done --final-summary "<一句>"` → `--ref "<done/ 新URL>,<相對路徑>"`）；`task complete <id>`（搬 `completed/`）是清場動作，延後到 maintain 週期（見 [kanban-board skill](../../../skills/kanban-board/SKILL.md) 清理前跨線掃描）。
- `archive/`＝退場可復活（AIR-4 先例）；品質衰減防護：CJK 損壞 `rg` 驗證、baseline 交付前刷新。

---

## §3 檔案型中繼站治理

> 覆蓋卡 desc 設計問題：.agent-tmp 清淤、新 dot-area 門檻、夜間 cron 掃殘留腿、.at-contexts 退場、.review 健康形態參照、共同四問。

![檔案型三區與夜間掃腿](diagram-workflow-relay.html)

*圖：檔案型三區與夜間掃腿（archify workflow，上為三區、下為出口；夜間掃腿掛 23:40 收斂 cron）*

### 3.1 現況盤點（09-03 實測，時點標註——快照漂移常態）

| 區 | 實測 | 備註 |
|---|------|------|
| `.agent-tmp/` | **38 項**（09-03 14:xx 實測；卡 desc 記 36、EP 記 37——快照漂移，新增 1 檔 `mos14-append.md` 等） | Sep 1: ~21、Sep 2-3: 累積；三天跨度，印證「session 結束列清單」有慣例無出口執行率 |
| `.at-contexts/` | 1 檔 `handoff-20260901-postbuild-distill.md`——**09-03 午後裁定：`handoff --save` 退場**（SM-12：交接改 `backlog task edit --comment` 掛卡 `comments` 段，隨卡歸檔），本區只剩 `at` 的 `at-context-*`（resume 後刪已定義） | `at` 排程 09-01 建、消費後未刪的殘留即退場前的遺證 |
| `.review/` | 空目錄 | 決策落點首選 `EP` review 區段（tracked），本區僅 local-only fallback——**09-03 /arch-thinking 評：solo 場景可退場（EP 全承載），多 WT 並行 review 時才留作不干擾主線的暫存板** |

> 數字漂移屬常態（09-03 內從 36→37→38），設計取「時點標註＋趨勢判斷」而非精確計數。

### 3.2 三區治理表（每區四問＋健康形態）

| 區 | 誰進來 | 停多久 | 誰清（第一腿→保底） | 清去哪 | 健康形態 |
|---|--------|--------|---------------------|--------|----------|
| `.agent-tmp/` | agent 暫時產物：中間分析／草稿／POC／探測腳本輸出 | session 生命＋**7 天緩衝**（`mtime>7d`） | **post-build 預設清**（收尾列清單→LLM 判「後續還用嗎」→用則保留、不用當場刪＋報清單——09-03 午後 user 裁定）→ 夜間掃腿兜底（併發線混入的漏網） | 刪；有價值先升格進 `EP`／`reports/`／`memory`——判「值得保存」非搬移 | **post-build 後應近空**（非 38 檔全量常駐） |
| `.at-contexts/` | `at` 一次性 context（`at-context-*`）——**`handoff --save` 已退場**：交接改 `backlog task edit --comment` 掛卡 `comments` 段（SM-12，隨卡歸檔） | 一次性：`at` 定義 `resume` 後刪；夜間掃 **7 天緩衝**兜底 | 消費 session 刪＋夜間掃腿 | 刪（一次性語義——消費後無保留價值） | 空或 pending 中 |
| `.review/` | `judge-review`／`followup-review` 的 local-only finding | branch 活躍期；**30 天緩衝**（finding 生命週期長於一次性 context） | decision 落點首選 `EP` review 區段（tracked，隨任務家遷 `done/` 永久保存）→ branch 完結即死檔 → 夜間掃腿。**arch-thinking 評（09-03）：solo 場景可退場**（EP 全承載），多 WT 並行 review 才留 | 刪（落點已在 `EP`，本區為未落點的草稿） | **空**——決策都在 `EP` 即健康（本區即「健康形態參照」樣本：local-only fallback＋tracked 首選的語義） |

**共同原則**：時限是緩衝不是保存承諾——被續用的檔案會 `touch` 刷新 `mtime`；門檻以「最後被需要」為代理。

### 3.3 出口兩腿：post-build 預設清＋夜間掃殘留腿

- **第一腿 post-build 預設清**（09-03 午後 user 裁定）：`/post-build` 收尾階段列 `.agent-tmp/` 清單→逐項 LLM 判「後續還用嗎」→用則保留（可 `touch` 保活）、不用當場刪＋報清單——「單一 session 產物單一 session 清」；**夜掃定位降為兜底**（併發線混入、session 意外中斷的漏網）。
- **兜底腿掛點**：每晚 **23:40** 收斂 cron（`automation-751ecce2-a79c-4309-a79c-08486e2ee893`，ai-rules 池寫手）——寫手角色每夜動手；**不掛週日 23:00** 治理看照（`automation-fed036ff-17bf-4cf0-a50e-3216a7de6665`，advisory 審計——不動手，角色不混）。
- **掃描表**：`.agent-tmp/` 7d／`.at-contexts/` 7d／`.review/` 30d（`mtime` 判準）。
- **動作**：報告列明細（可復原判斷的證據）＋刪；有價值先升格（判「值得保存」）。
- **首跑驗證**：比照 AIR-17 模式——隔日產物驗證（報告是否產出、明細是否可復原判斷、`_audit-state` 是否更新），通過即關卡。部署≠生效，生效要產物驗證。
- **落地**：post-build skill 收尾段（L 列）＋cron prompt 手術（L5，本卡不動，見 §6）。

### 3.4 新 dot-area 門檻（四條全過才開）

新暫存需求出現時，按序回答：

1. 語義最近的既有區裝得下嗎（三區已覆蓋「暫存」語義空間——中間產物／一次性 context／review 草稿）
2. 四問有答案（誰進來／停多久／誰清／清去哪）
3. 規則承載——寫進 [collaboration-constraints rule](../../../rules/collaboration-constraints.md)＋`.gitignore`
4. 掃腿覆蓋——進場即有出口（進 `L5` 清淤腿掃描表）

四條全過才開新 dot-area；否則復用既有區。

---

## §4 排程單一真相源

### 問題

cron 職責散在各 `automation` prompt 內，無總覽——同一週內兩次認知過時實證：

- 以為週日治理在 23:30（實已改 23:00，靠 AIR-17 notes 才知）
- 以為 `usage-ping` 還在跑（實為 `completed` 殘留記錄，`CronList` 見 `lifecycleStatus` 才知）

### 設計

`ai-analysis/schedule-registry.md`——**人／AI 可讀的職責總覽；機械真相源仍是 `CronList`**。`registry` drift 的後果限縮為認知過時，不是行為錯誤。

| 欄位 | 內容 |
|------|------|
| `automationId` | 全名逐字（`CronList` 輸出 `automationId`，非前綴） |
| `cron` | `cronExpr` 原樣 |
| `職責一句` | 一句話職責 |
| `對象範圍` | 作用對象（ai-rules 池／repo／workspace） |
| `紅線` | 禁止事項或角色注記 |

**scope**：ai-rules workspace（ZCode cron 3 條＋本 repo `backlog-browser` plist；mosaic 側指針→memory `reference_periodic-task-landscape`——條目名逐字全名，見 [schedule-registry.md](../../../ai-analysis/schedule-registry.md)）。

**同步義務**：動排程的 session（`CronCreate`／`CronUpdate`／`CronDelete`）順手同步 `registry`——慣例層，比對腿兜底。

**驗證腿**：週日 23:00 治理看照加 `CronList` vs `registry` 比對（drift 報告），落地 L8（見 §6）。

---

## §5 回歸驗證——MOS-14＋AIR-13~17 樣本對照

> 卡驗收明定「以 MOS-14 卡／EP 與本卡群為回歸樣本」。本節依 S1／S2 定案為基準，逐樣本：卡形態→設計命中→設計反饋。

| # | 樣本 | 卡形態 | 設計命中 | 設計反饋 |
|---|------|--------|----------|----------|
| 1 | **MOS-14**（mosaic，standard+ 正面樣本） | `desc` 過 gate 三必有（baseline／已決策／驗收 75-80 區間）、雙 ref、EP 規劃層完整、`notes` 空（EP 承載） | 三層分工自洽；兩層判定（standard+ 建 EP）實證；起手式五步可套用 | **F-1 驗收校準未回寫 desc＝§2.7 同步義務的反證輸入**：EP 內將驗收 110→80-100 校準，但 `desc` 仍寫 ~75-80 未同步——設計新增「決策層變更才同步」與機械觸發（F-1 型 findings）即為此反證的修正 |
| 2 | **AIR-14 本卡**（desc＋notes 拼裝樣本＋接手實測） | `desc` 三必有齊、`notes` 五條接手指針、`references` 雙 ref、`EP` docs mode 四段 | 拼裝成立：一手接手實測——夠用處（已決策清單直接防重辯／設計問題清單即大綱／驗收即完成線）；`notes` 與 `EP` 邊界清晰 | 缺口處：`mosaic 原稿七問` 不可自足取得——`desc` 蒸餾版（共同四問）夠用，設計標註原稿指針留白；「排程真相源」痛點未附 CronList 材料——需起手式機械自查；「dual-family 審查首發」參考價值模糊——不入設計 |
| 3 | **AIR-15**（Done，session 內即辦記錄卡） | `desc` 無 baseline／已決策標記；`status: Done`（開卡 09-03 04:31→04:56 即結） | **gate 豁免樣本**：支持 §2.2「適用時機＝To Do 且預期跨 session」設計——session 內即辦卡豁免非缺口 | 標題舊 scope→改名（標題層漂移修正，見 R-4）：卡 artifact 為準，支持「漂移修正」慣例（標題亦需如實化） |
| 4 | **AIR-16**（Done，如實化樣本） | `desc` 如實化一次：`.muse-bridge/` 已由並行 commit `5e6e9cb` 先行滿足→本批無 diff，如實記錄（卡 artifact 為準，R-4） | **desc 快照過時＋如實化慣例**實證：並行 commit 搶走項目→`desc` 記實況；支持 §2.6 新鮮度核對與 §2.7「並行搶走→如實化」 | memory 記「AIR-16 兩次」與卡 artifact 一次的分歧——設計採卡 artifact 為準（R-4 處置） |
| 5 | **AIR-17**（In Progress，驗證型卡） | `notes` 記排程整併過程（`automation-13dfeb9c` 23:50 mosaic 側、單池定版過程、readlink 覆核） | 排程認知過時實證材料（支持 §4）；**「首跑驗證」＝排程也有進出口的驗收模式**（支持 §3.3 首跑比照） | 方法論補一條判定紀律：多路徑涉及 memory 池先 `readlink`（`cmp identical` 在 symlink 同實體下是 tautology）——已補進 MOS-14 補充塊 |
| 6 | **AIR-13**（To Do，等待型） | `desc` 裝裁決（D1-D3）＋批次清單、規劃層薄 | **small 卡即 handoff 自洽樣本**：支持 §2.3（small 卡不建 EP 直行） | 無反饋——等待裁決落地，卡形態已自洽 |
| 7 | **對照結論** | 七樣本覆蓋 small／standard+／豁免／如實化／驗證型全形態 | 設計被全樣本支持：三層分工、兩層判定、gate 適用時機、notes 邊界、漂移修正、首跑驗證皆有正／反實證 | 僅 MOS-14 F-1 一處反證已轉為 §2.7 修正項；其餘樣本無新修正 |

---

## §6 落地清單與 sync-sources 掃描

> 卡驗收明定「文檔化落地清單（kanban-board／handoff／execution-plan／collaboration-constraints 手術）含 sync-sources 檢查」。本段只文檔化規格＋掃描，**不動四檔本體**——手術執行屬後續卡。

### L1-L9 落地清單

| # | 載體 | 手術內容 | 對應設計節 | 驗證命令 |
|---|------|----------|------------|----------|
| L1 | [kanban-board skill](../../../skills/kanban-board/SKILL.md) | 「開工」段改寫為起手式五步（§2.6）；「建卡」段加 desc gate 三必有（§2.2，適用時機與豁免）；新增「卡即 handoff」小節（三層分工／兩層判定／desc 同步義務，引用 execution-plan 規模分級不新造） | §2.2／§2.3／§2.6／§2.7 | `rg "已決策\|baseline\|起手式" skills/kanban-board/SKILL.md` 行齊 |
| L2 | [handoff skill](../../../skills/handoff/SKILL.md) | 邊界注記：有卡任務交接優先「卡即 handoff」；**`--save` 退場**（SM-12：不寫 `.at-contexts/handoff-*.md`，交接內容改 `backlog task edit --comment` 掛卡 `comments` 段隨卡歸檔；原 handoff 八欄 schema 不變，卡拼裝映射回指 self-contained-prompt） | §2.2／§3.2 | `rg "comment" skills/handoff/SKILL.md` 且 `rg -c "at-contexts/handoff" skills/handoff/SKILL.md`=0 |
| L3 | [execution-plan skill](../../../skills/execution-plan/SKILL.md) | UC 盤點建卡段——建卡時 desc 過 gate（蒸餾自 EP 總覽：baseline／已決策／驗收）；EP review apply 段——F-1 型 findings 觸發卡 desc 同步義務（§2.7） | §2.2／§2.7 | `rg "desc gate\|F-1.*同步" skills/execution-plan/SKILL.md` |
| L4 | [collaboration-constraints rule](../../../rules/collaboration-constraints.md) | 「Agent 檔案寫入紀律」段補 dot-area 治理（三區清單＋出口兩腿——post-build 預設清第一腿＋時限表＋新區門檻四條＋兜底掃注記）；**動 rule → `scripts/deploy_agents.py` 重跑＋三部署檔 cmp 兩兩比對一致**（cmp 出處＝週日治理 cron 段 1 同款檢查，R-7） | §3.2／§3.3／§3.4 | `deploy_agents.py` 後 `cmp ~/.zcode/AGENTS.md ~/.config/opencode/AGENTS.md && cmp ~/.config/opencode/AGENTS.md ~/.codex/AGENTS.md` |
| L5 | 夜間 23:40 cron prompt（`automation-751ecce2-a79c-4309-a79c-08486e2ee893`） | 加檔案型清淤兜底腿：三區 `mtime` 掃（7／7／30 天）＋報告列明細＋刪（§3.3 兜底腿）——`CronUpdate` | §3.3 | `CronList` prompt 含 `mtime.*7d.*30d` 且 `report.*明細` |
| L6 | [at skill](../../../skills/at/SKILL.md) | `.at-contexts/` 段注記：**只剩 `at-context-*`**（`handoff --save` 已退場改 `--comment`，見 L2）；`at-context-*` resume 後刪既有紀律維持，夜掃 7 天兜底 | §3.2 | `rg "at-context-\*" skills/at/SKILL.md` 且 prompt 注記含兜底 |
| L7 | [schedule-registry.md](../../../ai-analysis/schedule-registry.md) | S2 已建初版；memory `reference_periodic-task-landscape` 壓指針（現值清單→指針，memory 治理紀律——僅指針可跨 workspace 通用） | §4 | `rg "reference_periodic-task-landscape" ai-analysis/schedule-registry.md` |
| L8 | 週日 23:00 治理 cron prompt（`automation-fed036ff-17bf-4cf0-a50e-3216a7de6665`） | 加 `CronList` vs `registry` 比對腿：`rg automationId` 抽兩側，drift 列報告（§4 驗證腿） | §4 | `CronList` prompt 含 `schedule-registry.*比對\|registry.*drift` |
| L9 | [post-build skill](../../../skills/post-build/SKILL.md) | 收尾段加 `.agent-tmp/` 預設清：列清單→LLM 判「後續還用嗎」→用則保留、不用當場刪＋報清單（§3.3 第一腿——「單一 session 產物單一 session 清」） | §3.3 | `rg "agent-tmp" skills/post-build/SKILL.md` |

### sync-sources 檢查規格（落地 session 執行）

三類掃描，落地時各跑一次（`[sync-sources skill](../../../skills/sync-sources/SKILL.md)` 機械新鮮度檢查為載體）：

| 類 | 命令 | 判定 |
|---|------|------|
| 互引 | `rg "kanban-board" skills/`——`execution-plan`／`metadata-sync` 等引用面是否指回更新後的 kanban-board 語義 | 引用語義一致，無舊語義殘留 |
| 部署 | `scripts/deploy_agents.py` 重跑＋三部署檔 `cmp`（見 L4）＋`wc -c` 量測（bundle 門檻） | 三份一致且均 < gate |
| 術語 | `rg "起手式\|desc gate" skills/ rules/`——新詞「起手式」「desc gate」定義源唯一（僅 kanban-board 與 execution-plan 二處），無三處以上漂移 | 定義源 ≤2 處 |

---

## 附：驗證清單（本卡交付自檢）

- [ ] §2 各小節標題對應卡 desc 設計問題清單逐項（卡即 handoff／drafts／升卡／notes／兩層判定／起手式／desc 同步七項全命中）
- [ ] 八欄映射表八行齊（§2.2）
- [ ] 六條已決策照錄可數（§0）
- [ ] 三區×四問表 12 格齊＋門檻四條（§3.2／§3.4）
- [ ] §4 兩次過時實證照錄
- [ ] 對照表七行齊、每行有命中＋反饋兩欄（§5）
- [ ] L1-L9 行齊（含四點名檔案）、每行有驗證命令（§6）
- [ ] 設計文件內相對連結 `../../../` 深度可導航（R-1）
- [ ] 報告 URL 形態 `http://127.0.0.1:6421/ai-rules/<相對於 ai-analysis/ 的路徑>` 實測 200（R-3）
- [ ] `schedule-registry.md` 三條 `automationId` 與 `CronList` 逐字一致（R-8）

---

*baseline `d121837`（2026-09-03）——下游審查弧以此為範圍邊界；設計文件隨任務家遷 `done/` 永久保存。*
