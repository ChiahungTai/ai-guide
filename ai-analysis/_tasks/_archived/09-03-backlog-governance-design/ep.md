# EP：Backlog.md 治理設計（卡即 handoff）

> **ep_type**: implementation（**docs mode**——全變更為 `.md`，無 `.py` callable 符號）
> **backlog**: AIR-14（本 EP 追蹤卡；卡 desc＋notes＝self-contained handoff）
> **baseline**: `d121837`（2026-09-03，與卡 desc baseline 一致）
> **審查狀態**: EP Review pending（本 EP 定稿前跑）

## 實作總覽

**目標**：產出中繼站治理設計文件（兩族合一：任務型 backlog board＋檔案型 dot-area）——核心是「卡即 handoff」契約；交付物＝設計文件（`design.md`，本任務家內）＋排程 registry 初版＋回歸驗證節＋文檔化落地清單。**本 EP 不執行 skill/rule 手術**（kanban-board/handoff/execution-plan/collaboration-constraints 手術＝落地清單文檔化，執行屬後續卡）。

**已決策（user 09-03 裁定，勿重辯）**：①兩族合一框架（任務型＋檔案型）②討論題即時不建卡——對話即載體，session 斷才落 draft ③drafts＝未承諾/觸發型進口（rules-audit draft 首例）④退場走 archive 非 delete（可復活；AIR-4 先例）⑤`_inbox` 不採——drafts 即進口（本 EP 定案收口）⑥卡三層分工 desc＝決策層／EP＝規劃層／notes＝留言層。

**產物與放置**：設計文件＝本任務家 `design.md`（一弧全生命檔案同處；結案隨家遷 `done/`）；排程 registry＝`ai-analysis/schedule-registry.md`（跨任務活文檔——不隨任務家歸檔，落 ai-analysis/ 根活文檔區）。

## EP Review Findings（09-03 獨立 Explore agent，judge-review 8/8 ✅ 採納）

| ID | 嚴重度 | EP 段落 | 問題 | 處置 | 狀態 |
|----|--------|---------|------|------|------|
| R-1 | 🟡 | 段落 0 | 五個機制檔相對連結深度錯（`../../../../` 4 層解析出 repo 外；正確 `../../../` 3 層） | 連結全改 `../../../`；S1/S2 驗證策略加設計文件相對連結導航檢查 | implemented |
| R-2 | 🟡 | 實作總覽 | registry 放置慣例錨虛指（bundle-watch-state.json 尚不存在——週日 cron 首跑才寫入） | 改直接陳述放置理由（跨任務活文檔、不隨任務家歸檔） | implemented |
| R-3 | 🟡 | 段落 0 | report URL 形態記載歧義（字面保留 `ai-analysis/` 前綴實測 404；正確＝相對於 ai-analysis/ 的路徑） | 改寫形態語義＋附 200 實例；S2 驗證策略加 registry URL 抽 curl | implemented |
| R-4 | 🟡 | S3 | AIR-16「兩次 desc 漂移修正」證據源分歧（AIR-14 notes 記＝AIR-16 desc 一次＋AIR-15 標題一次；memory 記 AIR-16 兩次；卡 artifact 僅見一次） | S3 規格改以卡 artifact 為準：AIR-16＝desc 如實化一次；AIR-15＝標題改名（標題層漂移修正） | implemented |
| R-5 | 🟡 | S2 §4/L7 | memory 條目名內部不一致（`reference_periodic_task_landscape` vs 實名 `reference_periodic-task-landscape`） | 兩處統一實名；design.md/registry 引用 memory 條目一律逐字全名 | implemented |
| R-6 | ℹ️ | S2 §3.1 | .agent-tmp 殘留數卡記 36、EP 記 37（實測 37，快照漂移常態） | design.md 照錄時點標註 | noted |
| R-7 | ℹ️ | S4 L4 | 「三部署檔 cmp」出處未驗（rules/AGENTS.md 無 cmp 步驟） | L4 改「cmp 兩兩比對——出處＝週日治理 cron 段 1 同款檢查」 | implemented |
| R-8 | ℹ️ | S2 | registry 第三條 cron automationId 未在卡/EP 出現（不可自足取得） | EP 直接嵌三條全名（本 session CronList 實錄） | implemented |

## 段落 0：全域研究摘要（09-03 本 session 已完成）

**可複用基礎設施**（設計的直接輸入）：
- [kanban-board skill](../../../skills/kanban-board/SKILL.md)——board 機制單一源（命令合約/ref 規則/結案兩步/容錯）；落地手術對象 L1
- [self-contained-prompt skill](../../../skills/self-contained-prompt/SKILL.md)「標準 schema」——handoff 八欄（任務一句話/baseline/來源 EP/已完成/已決策/下一步/驗收/承接不重做）；卡即 handoff 契約的映射源
- [execution-plan skill](../../../skills/execution-plan/SKILL.md)「流程規模分級」（simple/standard/full）——兩層判定（small 卡即 handoff vs standard+ 卡＋EP）的對齊對象，**不新造判定**
- [collaboration-constraints rule](../../../rules/collaboration-constraints.md)「Agent 檔案寫入紀律」——三個 dot-area 慣例現址（.agent-tmp 禁 /tmp、寫不進回報、暫時產物集中區）；落地手術對象 L4
- [at skill](../../../skills/at/SKILL.md)——`.at-contexts/` ephemeral lifecycle 已定義（排程時建立→resume 後刪）；handoff `--save` 同區但**無消費後刪除機制**（殘留實證：09-01 檔仍在）
- 夜間 23:40 收斂 cron（automation-751ecce2，ai-rules memory 池寫手）——檔案型清淤腿掛點（卡 notes 明示「可考慮掛它」）；週日 23:00 治理 cron（fed036ff）＝審計角色（advisory 不動手，prompt 有審計獨立註記）——**不掛清淤腿於審計**

**依賴關係與關鍵約束**：
- references 只對 http(s) linkify（kanban-board 合約）；ai-rules report route 實測 `http://127.0.0.1:6421/ai-rules/<相對於 ai-analysis/ 的路徑>`——route root 即 ai-analysis 內容，URL **不含** `ai-analysis/` 段（例 `ai-rules/_tasks/09-03-backlog-governance-design/ep.md` 實測 200；保留前綴形態實測 404；`_md-viewer.html` 僅在 mosaic route，ai-rules 直連 raw md）
- memory 條目 `backlog-md-integration-eval`「卡即 handoff 契約雛形」段＝本設計直系前置（desc 三必有 gate 雛形、八欄對照、品質衰減兩實例——CJK 損壞穿過 CLI、baseline 陳舊）
- Backlog.md CLI 事實：`--append-notes` 追加、`-d` 全量替換 desc、`--ref` 整組替換 references、drafts promote

**類似實作（回歸樣本）**：MOS-14 卡＋EP（mosaic；self-contained handoff 正面樣本＋desc 同步缺失樣本）、AIR-13~17 卡群（09-03 開卡全過程實踐）、drafts/rules-audit（觸發型 draft 格式樣本）。

**風險假設**（等級/防護）：
1. **設計覆蓋度**（中）——卡 desc 列 11+ 設計問題，漏項＝驗收失敗。防護：EP 段落↔desc 問題清單逐項映射（S1/S2/S3 各段開頭列覆蓋項）；EP Review 查漏維度。
2. **registry 同步義務無機械執法**（中）——本卡只交付設計＋初版；比對腿（週日 cron）屬落地清單。防護：設計內明示「registry 是職責總覽非機械真相源」（機械真相源＝CronList），drift 後果限縮為認知過時而非行為錯誤。
3. **mosaic 原稿七問不可自足取得**（低）——卡 notes「用戶可提供」。防護：desc 蒸餾版（共同問法四問）為設計準據；設計文件標註原稿指針留白。
4. **夜間掃腿誤刪**（中）——.agent-tmp 檔案可能仍被續用。防護：mtime 門檻（7d）＋「時限是緩衝不是保存承諾」原則（被續用檔案會 touch 刷新）＋首跑 AIR-17 式驗證＋報告列明細（可從報告復原判斷）。

**死路假設**：無（純文檔變更）。

## UC 盤點（docs mode：受影響文檔清單）

### Backlog 關聯
- **AIR-14**＝本 EP 追蹤卡（已 In Progress；EP 建立後掛雙 ref）；無自動建卡（設計任務，落地手術另卡——落地清單即後續卡的規格輸入）

### SYSTEM-MAP 影響
- 無（ai-rules 無 SYSTEM-MAP.md；元專案正當跳過）

### 掃描範圍
- `backlog task list --plain`（To Do: AIR-13；In Progress: AIR-14/AIR-17；Done: AIR-15/16）
- 受影響文檔＝新建二檔（`_tasks/09-03-backlog-governance-design/design.md`、`ai-analysis/schedule-registry.md`）＋卡本身收尾；skill/rule 四檔為**落地清單手術對象（本 EP 不動）**

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| backlog board 任務追蹤 | ✅ | kanban-board skill | 無 | 本 EP 只消費不合修改 |
| 設計文件交付 | 📋 | 本 EP | 新增 | 中繼站治理設計（一次性交付，非持續能力） |

## Scenario Matrix（文檔語境）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應段落 |
|---|------|------|---------|------------|---------|
| SM-1 | 接手 session 說「做 AIR-N」 | 卡 To Do、desc 過 gate | 起手式五步依 desc＋notes 接手，不重辯已決策 | 設計文件 §2 起手式＋§5 樣本對照 | S1 |
| SM-2 | desc 缺 baseline/已決策/驗收 | 開卡時 | gate 三必有補齊才建卡（session 內即辦卡豁免） | 設計文件 §2 gate 段 | S1 |
| SM-3 | desc 快照過時 | baseline 後 repo 前進／並行 commit 搶走項目 | 起手式新鮮度核對（`git log <baseline>..HEAD`）；如實化記錄（AIR-16 樣本） | 同上 | S1 |
| SM-4 | EP review 校準 scope/驗收 | F-1 型 finding | desc 同步義務觸發——決策層變更回寫卡 desc | 設計文件 §2 同步義務段 | S1 |
| SM-5 | .agent-tmp 殘留累積 | 每日 agent 暫存（09-03 實測 37 項跨 3 天） | `post-build` 列清單預設刪（LLM 判後續還用則保留）+ 夜間掃腿 mtime>7d 兜底 | 設計文件 §3＋落地清單 L5（*本 EP 原寫夜掃，09-03 討論補 `post-build 預設清`） | S2 |
| SM-6 | 新暫存需求出現 | 想開新 dot-area | 門檻四條：語義最近區→四問有答→規則承載→掃腿覆蓋 | 設計文件 §3 門檻段 | S2 |
| SM-7 | 排程認知過時 | session 查「現有排程」 | 查 registry 檔（職責總覽）；機械操作仍走 CronList | 設計文件 §4＋落地 L7/L8 | S2 |
| SM-8 | 卡結案 | 驗收達成 | 結案兩步＋final-summary；notes 不蒸餾（durable lesson 走正規歸宿） | 設計文件 §2 出口段 | S1 |
| SM-9 | 多 session 並行搶同一卡 | Sessions A/B 同時 `edit -s In Progress` | 第一動可見 + `backlog_precheck.sh` 擋併發清板；後到者見 `In Progress` 退讓 | 設計文件 §2 起手式＋kanban-board 前置去重 | S1 |
| SM-10 | 多 WT 同 repo | WT-1 已 `In Progress AIR-14` 時 WT-2 誤開同名任務 | 依 `backlog → 執行家` 單向 + `owning-WT` 約束攔截，不在 `ai-analysis/_tasks` 另建獨立承諾 | 設計文件 §2＋README 三池紀律 | S1 |
| SM-11 | 跨 repo 指針與卡重複 | mosaic `_inbox/pending-decisions` 已有一行指針時誤 `task create` | `backlog search` + 查 `pending-decisions`/`open-items.md` 命中復用指針，不重複承諾 | 設計文件 §2 去重前置＋§3 三池 | S1/S2 |
| SM-12 | review/handoff 落點 | `judge/followup` 的交接落 `handoff --save` 檔 | 不寫 `.at-contexts/handoff-*.md`，改 `backlog task edit --comment` 掛卡 `comments` 段，隨卡歸檔 | 設計文件 §2 notes 治理（含 `handoff --save` 退場） | S1 |
| SM-13 | 想法未細拆先丟 draft | 有需求直覺、未 UC 盤點/成本細拆 | `backlog draft create` 不經 `/execution-plan`，僅記一句話+範圍草案 | 設計文件 §2.4 想法捕獲 | S1 |

## 段落劃分原則

依賴序：**S1（設計文件：框架＋任務型）→ S2（設計文件：檔案型＋排程＋registry 建檔）→ S3（回歸驗證節，依 S1/S2 定案）→ S4（落地清單＋sync-sources 掃描，依 S1-S3）**；每段獨立可驗證、可分 session 接續（段落自足）。S1/S2 平行可做（設計域獨立）；S3/S4 必須後置。

---

## S1：設計文件——統一框架＋任務型治理（卡即 handoff 契約）

**Context**：卡即 handoff 的核心張力——handoff 八欄裝不進 desc 單欄（AIR-14 開卡 session 實證；補法＝desc 收不變決策＋驗收、notes 收接手交代）。本段定案該拼裝模式。覆蓋卡 desc 設計問題：卡即 handoff 契約（desc 何時夠格）、drafts 進口慣例、升卡流程、notes 治理、兩層判定、「做 AIR-N」起手式、EP 修訂時 desc 同步義務。

**基礎設施盤點**：self-contained-prompt「標準 schema」八欄（映射源）；execution-plan「流程規模分級」（兩層判定對齊）；kanban-board 命令合約（起手式載體）；memory `backlog-md-integration-eval` 卡即 handoff 雛形段；MOS-14 卡＋AIR-13~17 卡群（樣本）。

**修改要點**（design.md §0-§2 內容規格）：

1. **§0 範圍與已決策**：六條已決策照錄（⑤收口：`_inbox` 不採——drafts 即進口；理由＝進口分裂、solo 無外部湧入、多一層多一治理面）。
2. **§1 統一框架**：兩族定義（任務型＝backlog board——「工作意圖」的進出口；檔案型＝repo dot-area——「工作產物」的暫存區）；**共同四問**（誰進來/停多久/誰清/清去哪——有進有出，user 治理原則）；治理判定＝每區四問有答案＋出口腿真存在。
3. **§2 任務型治理**（卡即 handoff）：
   - **2.1 三層分工**（已決策⑥）：desc＝決策層（baseline/已決策/範圍/驗收——不變的）；EP＝規劃層（怎麼做：段落/錨點/驗證策略）；notes＝留言層（接手交代/實踐記錄/漂移修正/指針）。
   - **2.2 卡即 handoff 契約**＝desc＋notes＋references＋EP 四件拼裝，八欄映射表：任務一句話→title＋desc 首句；baseline→desc 標記；來源 EP→references；已完成→EP 段落進度或 notes；**已決策→desc「已決策勿重辯」段（最關鍵——決策脈絡不交就重辯）**；下一步→notes 接手指針；驗收→desc；承接不重做→desc baseline＋notes。**desc gate 三必有**（baseline/已決策勿重辯/驗收）——適用時機＝**開卡狀態 To Do 且預期跨 session 執行**；session 內即辦記錄卡（開卡即做即結，AIR-15 樣本）豁免；gate 是內容 gate 非格式 gate（語義標記自由：〔〕或 **bold**）；不做 hook（desc 完備性是語義判斷→LLM 流程；載體決策樹三者條件不滿）；附 rg 軟自查（`rg -c "baseline|已決策|驗收" <卡檔>`）。
   - **2.3 兩層判定**：對齊 execution-plan 流程規模分級（simple/standard/full），不新造——small（≈simple）＝不建 EP、卡即 handoff（desc＋notes 自足直行）；standard+（standard/full）＝寫 EP、卡為追蹤錨（references 指向 EP）＋EP 為 handoff 主體。**判定時點＝承諾時**（升卡/建卡前的 `/execution-plan` 分級——與 2.4 分界線同一站）；執行端不分岔——起手式讀卡即知形態（references 有無 EP），執行中 scope 遠超 desc → 先升 EP 再動工（逃逸口，非分岔）。
   - **2.4 drafts 進口**（已決策②③⑤）：三形——①**想法捕獲**（有需求直覺、**還沒開 `/execution-plan`**→`backlog draft create` 丟池，不 UC 盤點；熬到 `scope 定+跨 session+可驗收` 三條齊才升為 `task`）、②**觸發型**（`rules-audit` 樣本：目標/觸發條件/範圍草案→條件到才 `promote`）、③**session 斷結晶**（對話要丟前結晶落 draft 不建卡）；**區分線＝有沒有開 `/execution-plan`：未開＝`draft 未承諾池`，已開 UC 盤點＝`task` 承諾池**；出口統一：`promote`（升卡時蒸餾 `desc` 過 gate）或刪。
   - **2.5 升卡流程**：對話拍板→跑 `/execution-plan`（規模判定＋UC 盤點）→simple 直接建卡（過 gate，不建 EP）／standard+ 寫 EP 後建卡（雙 ref 掛 EP）；draft→promote 時同站判定；執行中 scope 漲→升 EP（§2.3 逃逸口）。
   - **2.6 notes 治理**：與 EP 邊界＝規劃性內容（怎麼做）住 EP、notes 只收接手當下需知（EP 已有不重複）；長度＝無硬限，**機械信號＝notes 開始像 EP（段落結構/pseudo code/驗證策略出現）→ 該升 EP**；**結案蒸餾＝不做**——durable lesson 走正規歸宿（memory 四問/skill/rule），notes 隨卡歸檔為考古材料（過程留言不沉澱、沉澱走正規歸宿）。
   - **2.7 「做 AIR-N」起手式**（五步）：①`task edit <id> -s "In Progress"`（第一動——平行 session 可見）②讀卡三層（frontmatter→desc→notes→references）③讀卡知形態（references 有無 EP——形態承諾時已定 §2.3，此步不重判；scope 遠超 desc → 先升 EP 再動工）④**新鮮度核對**——desc baseline vs `git log --oneline <baseline>..HEAD` 非空→對照 desc 範圍確認；notes relay 宣稱→機械驗證當前狀態（relay 快照落後實證）⑤開工雙 ref。
   - **2.8 EP 修訂 desc 同步義務**：**決策層變更才同步**（scope 擴張收縮/驗收校準/已決策翻案〔須 user〕→回寫 desc）；規劃層調整（段落重排/錨點修正）不動 desc；機械觸發＝ep-review findings 含 F-1 型（scope/驗收校準）→ apply 時同步。反證樣本：MOS-14 F-1 驗收 110→80-100 區間校準寫進 EP 未回寫 desc（desc 仍寫 ~75-80）＝同步缺失實證。
   - **2.9 出口**：結案兩步→Done 欄留板；completed/ 清場（maintain 週期）；archive＝退場可復活（AIR-4 先例）；品質衰減防護（CJK 損壞 rg 驗證；baseline 交付前刷新）。

**驗證策略**（docs mode）：設計文件 rg 自查——§2 各小節標題對應卡 desc 設計問題清單逐項（卡即 handoff/drafts/升卡/notes/兩層判定/起手式/desc 同步七項全命中）；八欄映射表八行齊；六條已決策照錄可數；設計文件內相對連結導航檢查（`../../../` 深度——R-1）。

---

## S2：設計文件——檔案型中繼站治理＋排程單一真相源＋registry 建檔

**Context**：檔案型＝repo dot-area 暫存區（collaboration-constraints 已有慣例但無出口執行率——.agent-tmp 37 項殘留實證）；排程真相源＝cron 職責散在 automation prompt 無總覽（兩次認知過時實證：週日 23:30→23:00 改動靠 AIR-17 notes 才知、usage-ping completed 殘留誤認運行中）。覆蓋卡 desc 設計問題：.agent-tmp 清淤、新 dot-area 門檻、夜間 cron 掃殘留腿、.at-contexts 退場、.review 健康形態參照、共同問法、排程清單單一真相源需求。

**基礎設施盤點**：collaboration-constraints「Agent 檔案寫入紀律」（三區慣例現址）；at skill（.at-contexts lifecycle）；judge-review/followup-review（.review 定位：決策落點首選 EP review 區段、.review 僅 local-only）；夜間 23:40 cron（automation-751ecce2 挂點）；CronList（機械真相源）；09-03 三區實測（.agent-tmp 37 項/.at-contexts 1 檔/.review 空）。

**修改要點**：

1. **design.md §3 檔案型治理**：
   - **3.1 現況盤點**（09-03 實測照錄＋時點標註——快照漂移常態，卡 desc 記 36、本 EP 實測 37〔Sep1:21＋Sep2:2＋Sep3:16〕，R-6）。
   - **3.2 三區治理表**（每區四問＋健康形態）：`.agent-tmp`——進＝agent 暫時產物；停＝session＋7 天緩衝；清＝**兩腿**（第一腿 post-build 預設清：收尾列清單→LLM 判「後續還用嗎」→用則保留不用當場刪〔09-03 午後 user 裁定〕；兜底＝夜間掃）；去＝刪（有價值先升格進 EP/reports/memory——判「值得保存」非搬）；健康＝post-build 後應近空。`.at-contexts`——進＝at 一次性 context（**handoff --save 已退場**：交接改 `backlog --comment` 掛卡 comments 段，SM-12）；停＝一次性（at：resume 後刪已定義）＋7 天緩衝兜底；健康＝空或 pending 中。`.review`——進＝judge/followup local-only finding（**arch 評：solo 可退場**，多 WT 並行才留）；停＝branch 活躍期＋30 天緩衝；清＝decision 落點首選 EP review 區段（tracked）；健康＝空（決策都在 EP）——**本區即「健康形態參照」樣本：local-only fallback＋tracked 首選的語義**。
   - **3.3 出口兩腿**：第一腿＝post-build 預設清（「單一 session 產物單一 session 清」；落地＝post-build skill 收尾段）；兜底腿＝夜間掃殘留掛 23:40 收斂 cron（寫手角色每夜動手；週日 23:00 是審計 advisory 不動手——不混角色）；掃描表＝.agent-tmp 7d/.at-contexts 7d/.review 30d（mtime＝「最後被需要」代理——被續用會 touch 刷新；時限是緩衝不是保存承諾）；動作＝報告列明細＋刪；首跑 AIR-17 式驗證。落地＝cron prompt 手術（L5，本 EP 不動）。
   - **3.4 新 dot-area 門檻**（四條全過才開）：①語義最近既有區裝得下嗎（三區已覆蓋暫存語義空間）②四問有答案③規則承載（寫進 collaboration-constraints＋.gitignore）④掃腿覆蓋（進場即有出口）。
2. **design.md §4 排程單一真相源**：問題（散在 prompt 無總覽＋兩次過時實證）；設計＝`ai-analysis/schedule-registry.md`——**registry 是人/AI 可讀職責總覽，機械真相源仍是 CronList**（registry drift 後果限縮為認知過時）；欄位＝automationId/cron/職責一句/對象範圍/紅線注記；scope＝ai-rules workspace（ZCode cron 3 條＋ai-rules 相關 plist；mosaic 側指針→memory `reference_periodic-task-landscape`——條目名逐字全名）；同步義務＝動排程的 session 順手同步；驗證腿＝週日治理 cron 加 CronList vs registry 比對（落地 L8）。
3. **registry 初版建檔**（本段唯一新建檔）：三條 ZCode cron——`automation-751ecce2-a79c-4309-a79c-08486e2ee893`（每晚 23:40 memory 收斂，ai-rules 池寫手）／`automation-fed036ff-17bf-4cf0-a50e-3216a7de6665`（週日 23:00 治理看照，advisory 審計）／`automation-370fafc5-a050-479e-b62f-9c7988d23521`（週六 23:10 糾正週報＋CR 健檢）——automationId 全名照錄（本 session CronList 實錄；R-8）＋backlog-browser plist 注記＋維護規則頭註（同步義務+機械真相源宣告）。

**驗證策略**：registry 三條 automationId 與 CronList 輸出逐字比對；registry 內 URL 抽 curl（`ai-rules/<相對於 ai-analysis/ 的路徑>` 形態，R-3）；設計文件 §3 三區×四問表 12 格齊＋門檻四條；§4 兩次過時實證照錄。

---

## S3：設計文件——回歸驗證節（MOS-14＋AIR-13~17 樣本對照）

**Context**：卡驗收明定「以 MOS-14 卡/EP 與本卡群為回歸樣本」。依賴 S1/S2 設計定案（對照的基準）。

**基礎設施盤點**：MOS-14 卡＋EP（mosaic 絕對路徑在 AIR-14 notes）；AIR-13~17 五卡（本 repo backlog/tasks/）；本 session 接手 AIR-14 的一手實測（卡即 handoff 的活樣本——我就是接手 session）。

**修改要點**（design.md §5 樣本對照表，每樣本：卡形態→設計命中→設計反饋）：
- **MOS-14**（standard+ 正面樣本）：desc 過 gate 三必有/雙 ref/EP 規劃層完整/notes 空（EP 承載）＝三層分工實證；**F-1 驗收校準未回寫 desc＝2.8 同步義務的反證輸入**。
- **AIR-14 本卡**（desc＋notes 拼裝樣本＋接手實測）：接手實測報告——夠用處（已決策清單直接防重辯/設計問題清單即大綱/驗收即完成線）；缺口處（mosaic 七問不可自足取得——desc 蒸餾版夠用、標註留白；「排程真相源」只述痛點未附材料——需 CronList 自查；「dual-family 審查首發」參考價值模糊）；結論＝拼裝成立。
- **AIR-15**（session 內即辦記錄卡）：desc 無 baseline/已決策標記＝gate 豁免樣本（支持 2.2 適用時機設計）；標題舊 scope→改名＝卡 artifact 漂移修正（標題層）實證（R-4：以卡 artifact 為準）。
- **AIR-16**（如實化樣本）：desc 如實化一次（並行 commit 搶走 .gitignore 項→desc 記實況；卡 artifact 為準，R-4）＝desc 快照過時＋如實化慣例實證。
- **AIR-17**（In Progress 驗證型卡）：notes 記排程整併過程＝排程認知過時實證材料（支持 §4）；「首跑驗證」＝排程也有進出口的驗收模式。
- **AIR-13**（To Do 等待型）：desc 裝裁決＋批次清單、規劃層薄＝small 卡即 handoff 樣本（支持 2.3）。
- 對照結論行：設計是否被全樣本支持／樣本暴露的修正項（如有）。

**驗證策略**：對照表七行齊（MOS-14＋六卡）；每行有「設計命中」與「反饋」兩欄非空；MOS-14 F-1 反證有 EP 內證據引用（`09-03-memory-pool-slim/ep.md` findings 表）。

---

## S4：設計文件——落地清單＋sync-sources 掃描

**Context**：卡驗收明定「文檔化落地清單（kanban-board/handoff/execution-plan/collaboration-constraints 手術）含 sync-sources 檢查」。依賴 S1-S3 全部定案。**本段只文檔化手術規格＋執行掃描檢查，不動四檔**。

**基礎設施盤點**：sync-sources skill（機械新鮮度檢查）；rules/AGENTS.md「部署紀律」（collaboration-constraints 動→deploy_agents.py 重跑＋三部署檔 cmp）。

**修改要點**（design.md §6 落地清單表：#／載體／手術內容／對應設計節／驗證命令）：
- **L1 kanban-board skill**：「開工」段改寫為起手式五步；「建卡」段加 desc gate 三必有；新增「卡即 handoff」小節（三層分工/兩層判定/desc 同步義務引用 execution-plan 規模分級不新造）。
- **L2 handoff skill**：邊界注記——有卡任務交接優先「卡即 handoff」；/handoff 用於無卡一次性交接；八欄 schema 不變（卡拼裝映射回指 self-contained-prompt）。
- **L3 execution-plan skill**：UC 盤點建卡段——建卡時 desc 過 gate（蒸餾自 EP 總覽：baseline/已決策/驗收）；EP review apply 段——F-1 型 findings 觸發卡 desc 同步義務。
- **L4 collaboration-constraints rule**：「Agent 檔案寫入紀律」段補 dot-area 治理（三區清單＋時限表＋新區門檻四條＋夜間掃注記）；**動 rule → `deploy_agents.py` 重跑＋三部署檔 cmp 兩兩比對一致**（cmp 出處＝週日治理 cron 段 1 同款檢查，R-7）。
- **L5 夜間 23:40 cron prompt**：加檔案型清淤腿（三區 mtime 掃＋報告＋刪）——CronUpdate。
- **L6 at skill**：.at-contexts 出口補 handoff --save 檔的夜間清注記。
- **L7 schedule-registry.md**：S2 已建初版；memory `reference_periodic-task-landscape` 壓指針（現值清單→指針，memory 治理紀律）。
- **L8 週日治理 cron prompt**：加 CronList vs registry 比對腿（drift 報告）。
- **sync-sources 檢查規格**（落地 session 執行）：手術對象互引掃描（`rg "kanban-board" skills/`——execution-plan/metadata-sync 等引用面；`rg "collaboration-constraints" rules/ skills/`）；L4 動 rule 的 bundle 部署驗證；術語漂移掃（「起手式」「desc gate」新詞的定義源唯一性）。

**驗證策略**：落地清單 L1-L9 行齊且含四點名檔案；每行有驗證命令欄；sync-sources 段有三類掃描（互引/部署/術語）。

---

## 整合策略

- 全部變更 working tree 隨 docs commit 一次帶走（design.md＋registry＋卡收尾）；無程式碼風險。
- 不碰：skills/rules 四檔本體（落地清單對象）、既有 cron prompt（L5/L8 落地項）、memory 條目（L7 落地項）。
- 手術（L1-L9）執行＝後續卡（建卡建議：落地清單表即規格，可一卡一批或分批）。

## 收尾步驟（implement 階段 5）

- 元專案跳過 Capabilities/SYSTEM-MAP（docs mode）；`skills/CLAUDE.md` 工作流索引無新命令不動
- **AIR-14 結案兩步**：`task edit AIR-14 -s Done --final-summary "<一句>"` → `--ref "<done/ 新URL>,<相對路徑>"`（任務家遷 `ai-analysis/_tasks/_archived/09-03-backlog-governance-design/`；URL 形態 `http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-03-backlog-governance-design/design.md`）
- 卡 notes 補接手記錄一條（設計產出指針＋EP review 結論）——`--append-notes`
- audit-test 跳過（無測試變更——docs mode 正當跳過）
