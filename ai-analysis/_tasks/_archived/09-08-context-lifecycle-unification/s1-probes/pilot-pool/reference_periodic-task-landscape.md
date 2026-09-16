---
name: periodic-task-landscape
description: ai-rules 排程現值→ai-analysis/schedule-registry.md；mosaic plist→ls ~/Library/LaunchAgents/
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_9fe48e77-45f3-49d1-a89b-961e7c0cda65
---

# 週期任務全景（2026-08-30 user 要求整理定案＋同日兩輪 user 指正修正）

## 三個排程表面

**① launchd（~/Library/LaunchAgents/）——mosaic 交易資料管線，bash 腳本，與 AI 無關**

| plist | 時間 | 腳本 repo |
|---|---|---|
| com.mosaic.night-update | 每天 05:30 | mosaic_alpha |
| com.mosaic.market-open | 每天 08:30 | mosaic_alpha |
| com.mosaic.daily-workflow | 每天 15:30 | mosaic_alpha |
| com.mosaic.nightly-sequence | 每天 22:57 | mosaic_alpha（OP 測試序列） |
| com.mosaic.tdcc-weekly | 週六 09:00 | mosaic_alpha |
| com.mosaic.disposition-weekly | 週六 09:30 | **mosaic_alpha（08-30 user 指正後修正**——原指 offline_backtesting；兩邊腳本 byte-identical 且腳本內部本來就 `cd` offline_backtesting 執行＝零行為變更；plist 改徑＋bootout/bootstrap 重載＋launchctl print 驗證新參數） |

（com.user.ollama 另計）

另有服務型 plist（com.mosaic.report-server、com.mosaic.backlog-browser、com.ai-rules.backlog-browser——常駐服務非週期管線，09-03 audit 補記）；**數量與增刪不記**，現值查 `ls ~/Library/LaunchAgents/com.*`。

**② ZCode cron（CronCreate/CronUpdate）——唯一活著的免設定 AI 排程通道（計費、workspace-scoped）**

- **mosaic workspace**（ai-rules workspace 的 CronList 看不到；08-28 user 收斂定案，記錄在 mosaic memory `project-weekly-idle-tasks-status.md`）：
  - 每日 23:20 report 節
  - **automation `26b39582`「22:10 週期大活」`10 22 * * 0,3,6` 星期分流**——週日 test-findings／週三 doc-sync／週六 research-scan（這就是 user 記憶中的「週末晚上一週維護」）
  - weekly-standup 週日 21:00 cron 已刪（08-28 user 裁決——每日 report 涵蓋匯報職責）
  - **每晚 23:50 nightly-watch——含 memory 面治理（09-03 深夜 user 勘正，推翻本檔原「memory 面＝無」記載）**：scope＝memory-audit lite＋arch 看照＋現況＋instruction bundle 大小；**自動 commit**（ai-rules 週日治理 cron 的 lite 配方即抄自此段）。開放項＝advisory-only vs 會動手修未定——決定 mosaic 是否缺寫手腿：advisory-only → 縮編成 nightly-watch 加收斂一節（勿新開排程）；會修 → 全覆蓋免建。09-03 曾誤判無治理並出「23:35 收斂 cron 移植稿」——**稿 ON HOLD 待此確認**（誤判根因：引用他池記錄只見任務面、memory 面未現場驗）
- **ai-rules workspace**（ZCode cron 現值→`ai-analysis/schedule-registry.md`——僅指針，三條 active 職責/時段見該檔；歷史趨勢：三軌定版〔23:40 收斂寫手/23:00 治理審計/23:10 糾正週報〕詳 [[project_gate-severity-solidification-queue]]；mosaic plist 現值→`ls ~/Library/LaunchAgents/`）

- 其餘皆已完成/停用的一次性舊物（usage-ping rungs、at 接續、量測）——**completed 記錄仍鎖 20-cap 名額**（09-03 實證處置：usage-ping 9/3 completed 殘留已 CronDelete 釋放，匹配 [[at-skill-zcode-cron-gaps]]「pending/completed 皆鎖」）

**③ ZCode 閒時任務（idle-time task，免費通道）——已死，但功能未無主**
- user coding plan **不支援**（user 2026-08-30 明示「應該要刪除了」）→ 通道停用
- `mosaic-idle-tasks` skill 早已退休（commit `1cf8eee`，08-28 user 授權）；settings.json 最後殘留 dead allowlist 行已清（08-30）
- **「四範本無主」為誤判**（我 08-30 首輪結論，被 mosaic memory 推翻）：08-28 遷移已完成——三張活在 26b39582 星期分流、weekly-standup 職責由每日 23:20 report 涵蓋、research-scan 曾暫緩後納入分流

## 查證教訓（user「不要偷懶」）

User 引用既有設施（「我本來就有 X」）時**全表面搜尋**才可下結論：CronList → launchd plists（`ls ~/Library/LaunchAgents/`＋`plutil -p`）→ 遙測 db（part 表 LIKE 關鍵詞）→ **目標 workspace 的 memory 檔**→ skills 目錄。**CronList 是 workspace-scoped**——ai-rules workspace 看不到 mosaic workspace 的排程（08-30 實例：我只查本 workspace CronList 就斷言「週末維護不存在」，user 指正後在 mosaic memory `project-weekly-idle-tasks-status.md` 找到 26b39582 全套定義）；idle-time 任務不在 CronList 也不在 launchd（存在 ZCode app 層，config.json/db 均無蹤）。單一表面查不到 ≠ 不存在。

## Pending（08-30）

- **themes 任務查證 handoff 已交付 user**（貼 mosaic session；跨 repo self-contained）：mosaic 端 CronList 全量盤點＋找 user 記憶中「每週會更新 themes」的任務定義＋對照 08-28 最終態找缺口＋回報（hub-relay；ai-rules 側 'themes' 直搜只得到噪音、815 個 'theme' 命中多為 mermaid theme）
- T3-1 維持獨立排程已定案（週六 23:10，不併 26b39582——user 08-30 末輪裁定）

Related: [[gate-severity-solidification-queue]]（corrections-weekly 段） [[at-skill-zcode-cron-gaps]] [[slash-command-existence-verification]]
