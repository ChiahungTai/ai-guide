---
name: reference-backlog-md-browser-id-mechanics
description: Backlog.md browser 視野/id 防撞/遮蔽三面體/port fallback——診斷先打 API，跨 WT 靠 commit 紀律
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_763faa95-0187-4383-b88b-5c29becbe573
---

Backlog.md（npm `backlog.md`）browser/id 機制（09-05 對 v1.50.1 查證，源碼 MrLesk/Backlog.md＋09-06 誤診收斂）。治理流程單一源＝kanban-board skill；此檔留機制＋診斷。（09-08 蒸餾）

**browser 視野＝啟動 cwd**：只 serve 該目錄 `backlog/`，board 恆單 worktree 視角。查 board 看哪個 WT：`lsof -iTCP:<port>` 取 PID→`lsof -p <PID> | rg cwd`。**診斷 ground truth＝live API**（`/api/tasks`＝board render 資料）：API 有卡→刷新/排序問題；無卡→未 commit 進 branch ref。易誤點：column 按 ordinal 非卡號；同批建卡同 payload；跨 branch 卡整寬橫幅＋淡出是正常唯讀樣式；「API 有＋fresh load 仍看不到」＝分頁 stale（先 refresh，再查 Milestone 檢視/drafts 路由/搜尋殘留）。

**遮蔽三面體（結構性非 delay）**：同 id 共用卡 commit 進 branch ref 後本地 board 仍恆顯示本地版——等再久不浮現，唯一收斂＝merge/rebase。卡狀態三值分面回答：①owning WT working 檔②branch committed 樹（`git show <branch>:<path>`）③board 本地版。**drafts 天生無跨 branch**（loader 只覆 tasks）。**關鍵限制：掃描只看 committed 樹**——untracked/staged 對他 WT 不可見；撞 id 條件＝某 WT 未 commit＋另一 WT 開卡。

**id 防撞**：同目錄 file lock（不跨目錄）＋跨 branch max-id 掃描（`check_active_branches`，預設 true；mosaic `ffbb87240` 刻意關——重開先回想動機）。**慣例**：建卡即 commit；config 現值以各 repo `backlog/config.yml` 為準（可變組態，依賴前先驗）。config.yml per-branch——statuses 變更只落當前 branch；跑著的 server 會寫回舊 config（改完即 commit＋mtime 複查）。

**port 靜默 fallback**：被佔永不報錯（`--port` 亦跳下一個，exit 0）——起後必 lsof 驗實際 port。避 6421（report server）。**symlink 共用池已否決**（出 repo 邊界＝失 merge 仲裁/歷史/precheck 掃描；原生 cross-branch＋commit 紀律已有）。

**卡渲染契約**：CLI/board 只渲染標準 SECTION 標記區段——bare body 不可見；`draft create` 長標題 ENAMETOOLANG。`--comment` 不存在——掛內容用 `--append-notes`。**套件**：Bun 單檔無自動更新（`npm i -g` 手升；KeepAlive 常駐不換版須手動重啟）。`cleanup` TUI 禁 headless（exit 0 假成功）；headless 用 `task complete` 或 REST（preview＋execute）；Done 清場載體＝每日 launchd＋`run-backlog-cleanup.sh`（單一源 kanban-board skill，殘項見 [[project-backlog-cleanup-vehicle]]）。

方法論印證：binary 讀不了 JS 源——zread 挖官方 repo 機制文件。見 [[feedback_read-tool-source-before-upgrade-proposals]]；治理線見 [[project_ai-analysis-restructure-design]]。
