# Schedule Registry（排程職責總覽）

> **定位**：人／AI 可讀的**職責總覽**；**機械真相源仍是 `CronList`**（`registry` drift 的後果限縮為認知過時，不是行為錯誤）。
>
> **維護規則**：動排程的 session（`CronCreate`／`CronUpdate`／`CronDelete`）順手同步本檔——慣例層；比對腿兜底見週日 23:00 治理看照（[design.md §4](_tasks/done/09-03-backlog-governance-design/design.md#§4-排程單一真相源)）。
>
> **scope**：ai-guide workspace（ZCode cron 3 條 active＋本 repo `backlog-cleanup` plist）；mosaic 側排程指針→memory `reference_periodic-task-landscape`（條目名逐字）——反查表 A1/A2/A6 為 mosaic 排程的記載面例外（消費端在本 repo）。
>
> **更新時點**：2026-09-14（改名修復弧——三 cron 因 repo 改名 workspace key 失效：每晚 23:40 已重建＝automation-c9eb6495、週日／週六待建〔spec 版控於 _tasks/done/09-14-ai-guide-rename/〕；launchd label/path/log 改 com.ai-guide.backlog-cleanup；~/.codex/hooks.json 三 hook 路徑同步修復）。2026-09-06（新增 `backlog-cleanup` plist——Done 欄清場自動腿，ai-rules＋mosaic 雙 repo）。2026-09-09（AIR-54 S2——池主體遷 `/Users/ctai/Github/ai-rules/.agents/memory/`，條 1 對象路徑與跨 repo 指針同步；CronList 兩 prompt 同步換址）。2026-09-10（AIR-52——新增「外部依賴反查表」A1-A5；S1 skill 端排程解綁的對側載體）（AIR-54 收尾——首波驗證一次性 cron `automation-d64fd994` 已於本日晨由 CC 提前手動執行完畢：六判據全綠→`memory.bak` 刪除→cron 收除；行 4 重放劇本作廢不落表，記此存查）。2026-09-10（AIR-54 P5 定案——watchdog 雙檢查併入條 2 週日看照：lite-verify 觀測 mosaic 23:20 載體六晚 report 零 Phase 0 輸出＝**無 Phase 0 執行正證據**〔健康靜默相容；23:20 prompt 段規格跨 workspace 未驗〕，A1 僅載 Phase 1-3；user 拍板先(a)後(b)→退(b)；A1 記載源 stale 指針同步修正；CronUpdate fed036ff 增段 4，升級語義＝age 訊號連續兩排程週期命中→🔴）。2026-09-14（AIR-93——條 1 補波前池 delta gate、條 2 補對帳網唯讀 report：方法論源＝memory-audit skill「夜間收斂」節已接線，cron prompt 不變——引用 skill 即生效；mosaic 池 v1 不接 ai-rules 寫手腿，唯讀 report 歸條 2）。2026-09-14（改名掃尾——條 2 週日治理看照重建完成＝`automation-23c773b9-52a0-46ba-a1f5-777a6f3261bf`，首發 2026-09-20 23:00：prompt 依 db 考古〔fed036ff 最後 CronUpdate payload ts 1788997150600〕ai-rules→ai-guide 全替換 13 處、字面反斜線序列逐字保留；同 session 試建條 3 被 harness 拒——限一 session 一排程實證仍有效，條 3 仍待建）。2026-09-14（改名掃尾續——user 委託收除三條休眠舊排程：CronDelete 工具 workspace-scoped 不可達，直接對 `~/.zcode/v2/tasks-index.sqlite` automations 表精準 DELETE〔id＋workspace_key 雙重條件〕，三列全欄備份＝`.agent-tmp/automations-backup-20260914.json`〔gitignored，約 7 日後隨 nightly 清淤消失〕；`automation_runs` 歷史 2/2/11 筆留存未動；刪後立即＋15s 雙複查 0 殘留、mosaic 兩條與 ai-guide 新兩條未受影響）。2026-09-14（改名掃尾終——條 3 週六糾正週報重建完成＝`automation-c52d4574-bf92-4f45-bb2a-81783d2f0379`，首發 2026-09-19 23:10：prompt＝我方 spec 原文原樣重建——**三條全數重建完成，registry 回歸 3 條 active**）。2026-09-15（AIR-98 P1——新增 `com.ai-guide.entitlements-probe` launchd 註冊（launchd 表）：每小時 `scripts/probe_entitlements.py` 額度探測 glm/codex/muse＋chatgpt-web 池健康，落地 `~/.agents/probe-entitlements/`；**plist 內容已備、需 user 安裝**＝`.agent-tmp/air-98/entitlements-probe.plist`（09-16 移版控 `deploy/entitlements-probe.plist`）；probe/runtime/cron 永不直寫 spine，spine 寫手＝ai-guide session）。

## ZCode Cron（3 條 active，ai-guide workspace；09-14 改名重建完成）

| # | automationId | cron | 職責一句 | 對象範圍 | 角色／紅線 |
|---|--------------|------|----------|----------|------------|
| 1 | `automation-c9eb6495-2301-4fb7-bf18-81e244b135a9` | `40 23 * * *`（每晚 23:40） | ai-guide memory 池收斂（輕掃／弧線預警／波段收斂＋regen）＋**步驟 0 inbox 消費**（AIR-54 muse 寫入流 consolidation：path contract/CAS/六問→done/rejected receipt）＋**波前池 delta gate**（AIR-93：`reconcile_memory_pool.py --json` 波前第一機械步驟——exit 2→T4-1 分類、exit 1 停波；方法論源＝memory-audit skill「夜間收斂」節）＋**波尾 repo 外 bundle**（`~/.agents/memory-bundles/` 輪替 7 份，G2-11）＋**檔案型清淤兜底腿已上線**（`.agent-tmp`/`.at-contexts` `mtime>7d`、`.review` `>30d`；AIR-14 L5，2026-09-03 起） | 僅 ai-guide 記憶主體 `/Users/ctai/Github/ai-guide/.agents/memory/`（AIR-54 遷移；CC/ZCode 舊徑 symlink 指此）＋`.agents/memory-inbox/`（步驟 0）＋repo 三 dot-area | 寫手（每夜動手）；紅線：不碰 mosaic 池、不 commit、不改 DB schema、不刪 shared；09-14 改名後於 ai-guide workspace 原樣重建（僅路徑替換）——舊 `automation-751ecce2` 已刪（2026-09-14，全欄備份＝`.agent-tmp/automations-backup-20260914.json`） |
| 2 | `automation-23c773b9-52a0-46ba-a1f5-777a6f3261bf` | `0 23 * * 0`（週日 23:00） | 治理看照：bundle 組成看照（`deploy_agents.py` 三部署檔 cmp）＋memory lite 稽核＋**registry/卡 ref 一致性比對已上線**（`CronList` vs 本表 drift＋raw `.md` 直連卡 ref lint；AIR-14 L8，2026-09-03 起）＋**watchdog 雙檢查**（AIR-54 P5 定案 2026-09-10 併入：雙池 inbox age＋porcelain-vs-receipt；升級＝age 訊號連續兩排程週期命中→🔴、processing 殘留/直寫立即🔴）＋**池對帳網唯讀 report**（AIR-93：雙池 `reconcile_memory_pool.py --json`——偵測＋報告而已，禁修復動作） | ai-guide repo＋memory 池＋mosaic 池（唯讀） | 審計（advisory 不動手）；禁止改 rules／memory 條目（戳記除外）；09-14 改名後於 ai-guide workspace 原樣重建（僅路徑替換；prompt 考古過程見 spec 檔）——舊 `automation-fed036ff` 已刪（2026-09-14，全欄備份＝`.agent-tmp/automations-backup-20260914.json`） |
| 3 | `automation-c52d4574-bf92-4f45-bb2a-81783d2f0379` | `10 23 * * 6`（週六 23:10） | 糾正模式週報＋CR 使用健檢（`corrections-weekly` skill；CR 健檢主形態已轉事件觸發＝post-build 階段 4「CR wiring telemetry checkpoint」，AIR-67 弧B——本 cron 腿僅週期健康診斷） | ai-guide workspace | 報告；DB 唯讀、一頁、腳本失敗 2 次即止；09-14 改名後於 ai-guide workspace 原樣重建（我方 spec 原文，首發 2026-09-19 23:10）——舊 `automation-370fafc5` 已刪（2026-09-14，全欄備份＝`.agent-tmp/automations-backup-20260914.json`） |

> 全名照錄 `CronList` 輸出 `automationId`（非前綴），逐字比對通過。

## 本 repo 相關 launchd（服務＋排程）

| 服務 | 形態 | 說明 |
|------|------|------|
| `com.ai-guide.backlog-cleanup` | `launchd` plist（`~/Library/LaunchAgents/com.ai-guide.backlog-cleanup.plist`） | `deploy/scripts/run-backlog-cleanup.sh`（`StartCalendarInterval` 每日 23:50）——Done 欄清場批次：`Done` 且 `updated_date`>30d 的卡逐卡 `backlog_precheck.sh` → `backlog task complete` → commit（`BACKLOG_CLEANUP_AGE_DAYS` 可覆寫；跨 worktree 全展開）。twin＝mosaic `com.mosaic.backlog-cleanup`（23:55，`mosaic_alpha/deploy/scripts/` 同邏輯副本） |
| `com.ai-guide.entitlements-probe`（**待安裝**——plist 版控於 `deploy/entitlements-probe.plist`，需 user 安裝） | `launchd` plist（目標 `~/Library/LaunchAgents/com.ai-guide.entitlements-probe.plist`） | `uv run python scripts/probe_entitlements.py`（`StartInterval` 每小時 3600s；`--min-interval 30` 內建防重疊 skip）——AIR-98 P1 額度探測：glm/codex/muse 經 delegate-bridge `usage --json`（allow-list＝codex/glm；muse 只記 unsupported）＋codex chatgpt-web 池健康三訊號（非 usage、pool_visibility=none），落地 `~/.agents/probe-entitlements/latest-*.json`（fail-loud：失敗落 failure_class、全腿非 ok exit 1） | ai-guide repo `scripts/probe_entitlements.py`＋`~/.agents/probe-entitlements/`＋delegate-bridge＋localhost healthz | 探測（runtime 面）；紅線：**永不直寫 memory spine**——消費協議＝ai-guide session 讀 latest 校驗後寫 spine（as-of＋per-family 現值）、憑證零經手、codex-native 與 chatgpt-web 兩池記錄永不合併 |

（board browser 常駐服務已退役 09-11——ai-rules/mosaic 雙 plist 移除；board UI 走 VSCode extension／TUI／`backlog browser` on-demand，kanban SKILL「UI 入口」單一源。）

## 外部依賴反查表（排程側 → skill/腳本消費端）

> S1 解綁（AIR-52）的對側：skill 端只寫行為契約（去時刻/系統名），排程事實由排程系統＋本表承載——「誰在跑 X」從本表反查。**對帳義務**：動排程或改消費端接線時同步對應行；跨 workspace 條目（A1/A2/A6）以記載面為準並標 provenance。

| # | 排程側 | 消費端 | 契約一句 | 對帳狀態 | 新架構職責註記（AIR-54 後） |
|---|--------|--------|----------|----------|---------------------------|
| A1 | mosaic workspace ZCode cron「每日 23:20 report」 | daily-maintain（Phase 1-3）／standup（昨日活動節）／audit-test（週六條件段 Daily Scan） | 排程任務讀 skill 檔依規範執行、report 節由任務 append | 記載：memory `reference_periodic-task-landscape`＋mosaic memory `project-nightly-schedule-migration`（2026-08-30 吸收 weekly-idle-tasks-status——原指針 stale 已修）；23:20 automationId 在 mosaic workspace CronList（本 workspace 不可見） | 不變；保留——人類活動層 report 節＋三 skill 執行的唯一排程載體（機器狀態層＝A6）；**Phase 0 watchdog 承載移至 ai-guide 條 2 週日看照（AIR-54 P5 定案）——本載體六晚 report 零 Phase 0 輸出＝無執行正證據（健康靜默相容；prompt 段規格跨 workspace 未驗）** |
| A2 | 同 23:20 report「🌃 夜間看照」節（原 23:50 nightly-watch 併入） | memory-audit lite 配方／arch 看照／bundle 大小看照 | 治理面隨每日 report；含自動 commit | 併入記載於 memory（f681b71c9）；prompt 本體未逐字驗證（跨 workspace） | 保留；配方引用的池路徑隨 AIR-54 主體同步（`.agents/memory/`） |
| A3 | launchd `com.ai-guide.backlog-cleanup`＋twin `com.mosaic.backlog-cleanup` | kanban-board 清理段——`deploy/scripts/run-backlog-cleanup.sh` → 逐卡 `skills/kanban-board/scripts/backlog_precheck.sh` → `task complete` → commit | Done>30d 清場自動腿；precheck 紅燈跳過該卡 | plist 在場＋腳本 precheck 接線已核；時刻見上表 | 不變；保留——Done 卡清場唯一自動腿 |
| A4 | ai-guide workspace 三 ZCode cron（上表 #1-3） | #1→memory-audit（收斂＋Inbox 消費）；#2→治理看照（自含步驟）；#3→corrections-weekly | cron prompt 引用 skill 為方法論源 | CronList 已核（automationId 見上表） | #1 職責擴充（AIR-54：＋inbox 消費＋波尾 bundle；AIR-14：＋清淤兜底）、gate 口徑已動態化（AIR-52 S4）；保留——唯一寫手腿，與 #2 審計／#3 報告角色分離 |
| A5 | 服務型 launchd（常駐非週期）：`com.mosaic.report-server`（RunAtLoad＋KeepAlive＝登入自啟＋自動重拉；board browser 常駐已退役 09-11——雙 plist 移除，board UI 走 VSCode extension／on-demand） | mosaic 自家 report 殼與卡（main/v2/warrant mount）——**ai-guide 已退出 :6421**（09-14 裁決：卡 refs 相對路徑制、歷史殼 viewer link 留歷史態；死 mount ai-rules=/viewer= 待 mosaic 側刪除，工單＝`_tasks/done/09-14-ai-guide-rename/mosaic-side-ticket.md`） | report URL（:6421）的服務承載（mosaic 自家） | plist 在場已核；服務現值 `ls ~/Library/LaunchAgents/com.*` | mosaic 所有權；ai-guide 零依賴——殼一律 file: 直開 |
| A6 | launchd `com.mosaic.nightly-sequence`（22:57；任務別名 nightly-thin——skill 端稱 report 組裝任務） | daily-report 機器狀態層組裝（test-regression/BSR 節）＋maintain foreign-section 契約＋daily-maintain §配合（report 主體組裝者） | 機器狀態層 append、不產人類活動層（人類層＝A1） | plist 在場（`~/Library/LaunchAgents/com.mosaic.nightly-sequence.plist`→mosaic_alpha）＋memory landscape（OP 測試序列） | 不變；保留——report 機器狀態層唯一組裝者，與 A1 人類活動層互補 |

## 跨 repo 指針

- mosaic 側排程風景（含 `nightly-watch` 23:50 等）→ memory 條目 `reference_periodic-task-landscape`（主體：`/Users/ctai/Github/ai-guide/.agents/memory/`——CC/ZCode 舊徑皆 symlink 指此；不在則以 mosaic repo 的 `CronList` 為準）。

## 同步義務

- 動排程的 session 順手 `rg automationId` 抽 `CronList` 與本表，更新本表對應行與本節「更新時點」；操作後跑 `CronList` 再 `cat` 本表逐字核對。
- 週日治理看照（09-14 改名後重建＝automation-23c773b9；原 automation-fed036ff 已刪）含 `CronList` vs 本表比對腿＋卡 ref lint——drift 列報告，不自動改（AIR-14 L8 已上線，2026-09-03）。

---

*機械真相源：`CronList`；本表為職責總覽。*
