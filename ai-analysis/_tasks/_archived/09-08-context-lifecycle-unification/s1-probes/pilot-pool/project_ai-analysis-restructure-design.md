---
name: ai-analysis-restructure-design
description: 任務放置與 backlog 載體線終態——mosaic 三池重構＋任務家探測、Backlog.md kanban 定案、卡即 handoff 契約、放置學教訓群
metadata:
  node_type: memory
  type: project
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
  merged_from: [project_task-flow-restructure-00-tasks, project_mosaic-ai-analysis-directory-review, project_backlog-cards-extension-eval, project_backlog-md-integration-eval]
---

任務放置與 backlog 載體線：00-tasks 放置學→mosaic ai-analysis 三池重構→Backlog.md kanban 定案→卡即 handoff 契約，全收案。EP＝`ai-analysis/_tasks/_archived/09-02-ai-workflow-restructure/ep.md`（已歸檔）。

## 終局形態（user 兩度 push 後定案）

- **`_` 前綴三池**＝`ai-analysis/{_inbox,_projects,_tasks}`（活躍面）；三線進 `_projects/<線>/`（線契約：README＋open-items 一行制＋tasks/＋done/ 任務史巢狀）；00-tasks 整體遷入 `_tasks/`；idle-findings→`_inbox`；`archive/`＝唯一服務歸檔根；放置規則單一源＝`ai-analysis/README.md`
- **被退回的結構層（勿再主動提案）**：`_work/` 傘形、前綴叢集美化、ai-analysis 改名——**AI 主動提案的美化層被退、user 發起的排序需求成立**（勿再主動提案前綴/傘形/改名；user 問排序才給選項）
- **repo 歸屬定案**：線專案家＝mosaic_alpha repo（marking 是 domain，放 ai-rules＝業務內容污染所有部署端 session）；ai-rules＝方法論層（其自用 ai-analysis/ 與 mosaic 同名異物）
- **queue 檔契約**（治「AI 昨天才整理過又亂」）：一行一條；>3 行＝是任務該開任務承載、queue 留指針；狀態唯一源＝ep.md；整理＝比上版短。根因＝append-only 活檔無收斂壓力（同構 memory 84KB 教訓）
- **kanban 縮編**：Backlog=純雜項候選池、In-Progress 廢（任務目錄存在＝進行中）、Done 停囤積；**sprint 否決**（solo+AI 事件驅動不宜 timebox）——替代＝WIP limit＋週末回場升格 weekly triage＋STATE.md 焦點面
- **設計辯證教訓**：「tag+帳冊 vs 物理巢狀」三輪——終局＝物理巢狀＋帳冊刪除（done/ 即任務史）；「結構層 AI 提案被退回、user 自己要的排序手腳卻成立」

## 放置學（00-tasks 九決策，user 拍板勿重開）

- 殼雙掛點（hook 1 EP 定稿／hook 2 post-build 完成／fallback implement 階段 6）＋baseline 跨 session 可從殼讀；spec/ep 同 task 目錄；建卡即 git add；命名 `MM-DD-<task-name>/`（年移除）；持久 delta tour 單一產點＝post-build hook 2
- **根因脈絡**：mosaic 三弧實證弧後產物全滅（掛弧後在 session context 耗盡時必死）——修法＝全掛點搬 commit 前穩定點（同 metadata-sync「結算在 build 不在 commit」先例）
- **任務家探測單一源**＝illustrate-html-mode.md「產物位置分流」：`ai-analysis/_tasks/` 在場→雜項家；session 從線 context 來→`_projects/<線>/tasks/`；否則 repo-root `00-tasks/`（其他 repo 慣例不動）；**結算雙制**（repo 慣例探測：有 Done/ lane→搬入；無→刪卡）
- **歸檔路徑 drift 教訓**：原拍板 `_done/YYYY/` hardcode 與 mosaic 實際 `done/` 慣例漂移——跨專案 skill 改 repo 慣例探測（`done/` 或 `_done/`，皆無建 `done/`；單一源 metadata-sync 歸檔項）
- **T5 成敗指標＝弧中段開全新 session 跑 /post-build 印出 baseline（從殼讀非舊 session 記憶）——靜態層只能證合約存在，跨 session 行為實測才證合約被遵守**

## Backlog.md kanban（機制單一源＝kanban-board skill；本檔留為什麼與陷阱）

- 演化弧全終結：Tasks.md 找回→替代評估（pine/Tasks.md/Signboard）→**Backlog.md 選定**→雙側遷移＋dogfood（prefix=`air`）。舊 `.kanban/` 制退役（**禁再教 `mkdir .kanban/`**）；**卡現況不記**——查 `backlog task list --plain`
- 核心合約：建卡即 git add；開工＝雙 ref（**references 只 linkify http(s)——相對路徑單獨出現＝board 不可點**）；結案兩步＝`-s Done --final-summary` → `--ref` 換 done URL（**`--ref` 整組替換非 append**）
- 工具規律：**檔案制 kanban 皆有專屬格式（無 adapter API）**；**WIP limits 生態一律沒有**（自補）；官方紀律 **CLI-only 寫入**（frontmatter marker 手改易碎）；**draft create 標題即檔名——長標題撞 ENAMETOOLONG**（09-05 兩例），短標題＋細節寫 body；**卡/draft 可見內容只在標準區段**——內容須包在 `## Description`＋`<!-- SECTION:DESCRIPTION:BEGIN/END -->` 標記內才被 `draft view`/board 渲染，bare body（frontmatter 後直接放 markdown）＝隱形、view 顯示 No description（09-05 DRAFT-12 notes 實證）——內容對但區段錯＝接手方看不到＝等於沒寫；pine 教訓＝單作者 v0.x bus factor 1、與 ai-rules 體系全面重疊（採用必 `--skip-agents`）
- **卡即 handoff 契約**：desc 單欄裝不下 handoff（八欄對照實證）→兩層拼裝：**desc 收不變決策（baseline／已決策／驗收）、notes 收接手交代（`--append-notes`）**；handoff 品質衰減兩實例＝CJK 損壞穿過 `task edit -d`、baseline 陳舊（交付前必刷新）
- **中央 md viewer**：canonical `:6421/viewer/_md-viewer.html?p=`；viewer `fetch(?p=)` 同源絕對路徑＝任一份 viewer 可渲染任一 route；**中央掛載版控 assets＝採用；掛整個 `~`＝否決（.ssh/憑證全變同源可 fetch——安全洞）**；重啟驗證陷阱：URL 404 先查檔案是否被平行 session 遷走（404≠server 壞）

## backlog-cards VS Code ext 評估（裁定：好載體但限 VS Code view 面）

唯讀卡瀏覽器（files are truth、寫入一律 CLI）＝board=view not container 的第三個 view、零新容器零契約變更、解雙 ref 相對路徑半不可點痛。**邊界**：VS Code-only——browser 面不受影響，補面非取代；v1 落地走過全場景前勿依賴；保持唯讀定位勿長流程邏輯（治理規則住 ai-rules）。`workspaceContains:**/backlog/config.yml` 單 extension 服務所有 repo。

## 機械手術教訓（S9＋遷移波）

**`git mv` 目標已存在＝嵌套**（mv 語義，逐檔攤平修）；結構驗證 fd 勿限深度（`-d 2` 漏第 3 層）；五軸混層盤點法（型態/主題/版本/狀態/資料分軸）；歸檔慣例多態＝dangling 引用源頭；**research-golden 類資料不動**（程式碼引用面未盤點前）。ai-rules 側手術全落地（任務家措辭全覆蓋＋殘留 0）；user PENDING 項：ZCode GUI 改 3 個 automation prompt 寫入路徑（時限——未改會寫舊路徑）。

關聯：[[gate-severity-solidification-queue]]（AIR 卡清理＋board 治理）、[[session-topology-single-writer]]（實作落點）、[[feedback_project-first-containment]]、[[feedback_full-arc-delivery-vehicle-immediately]]、[[reference_underscore-prefix-sort-cross-tool]]、[[feedback_shell-diagram-quality-bar]]
