# AIR-52 fresh-eyes review 帳本

- reviewed revision: air-52 @ `19974d5`（`git rev-parse --short HEAD`）
- scope: `4ef2982..HEAD`（16 檔，`git diff --stat` 實數；12 skills + schedule-registry.md + backlog/config.yml + .gitignore + air-52 卡；範圍外 air-57/58/59 卡、usage-ping、memory-audit、cr-audit 報告等未審）
- uncommitted identity: `?? ai-analysis/reports/2026-09-10-repo-consistency-scan.md`（untracked，非本弧項，未審未動）
- draft-3 刪除（弧內）：`backlog/drafts/draft-3 - muse-AGENTS-64KiB截斷——bundle瘦身兩案裁決（專用變體vs全域）.md`（e1aecb0，-66 行）

## Findings

| # | 嚴重度 | 信心 | 位置 | 發現 | 建議 |
|---|--------|------|------|------|------|
| 1 | 🟡 | high（錨點缺失機械驗證；「nightly-thin 是否現役」部分 inferred——mosaic prompt 跨 workspace 不可直驗） | skills/daily-maintain/SKILL.md:57、skills/maintain/SKILL.md:221、skills/standup/SKILL.md:10 | **nightly-thin 系統名解綁殘留且無 registry 錨點，與反查表 A1 「唯一排程載體」宣稱矛盾**。daily-maintain:57「report 主體由 nightly-thin 任務組裝…時刻/載體現況見 ai-rules ai-analysis/schedule-registry.md 反查表」——同句指去反查，但 `rg nightly-thin` 於 schedule-registry.md 與 `.agents/memory/reference_periodic-task-landscape.md` 雙 0 命中（反查鏈斷）。且 registry A1 職責註記稱 23:20 載體為「report 組裝＋三 skill 執行的**唯一**排程載體」，與 skill 端另指 nightly-thin 組裝 report 主體直接矛盾；memory 條目只記 `com.mosaic.nightly-sequence` 22:57＝OP 測試序列（bash「與 AI 無關」），無 nightly-thin。maintain:221 同段不對稱：nightly-thin 點名、23:20 載體泛化成「排程載體」 | 三選一：(a) skill 端 nightly-thin 一併解綁（泛稱＋test-regression 節名即足識別）；(b) 反查表補一列記載 report 組裝/test-regression 節生產者現值；(c) 若 nightly-thin 已隨 08-08 併入退役，skill 三處改為退役口徑。需 mosaic workspace 現值確認後擇一 |
| 2 | 🟡 | high（三池機械搜尋：repo `.agents/memory` 3 檔、CC projects mosaic 路徑無 `memory/`、ZCode memories 池 114 檔檔名＋內容雙搜） | ai-analysis/schedule-registry.md:34（A1 對帳狀態欄）；同源 stale：.agents/memory/reference_periodic-task-landscape.md | **A1 provenance 引用已吸收（不再存在）的 mosaic memory 條目名**。A1 記「mosaic memory `project-weekly-idle-tasks-status`」，但該條目 2026-08-30 已被 12 檔吸收進 `project-nightly-schedule-migration.md`（該檔 `merged_from` 欄逐字列名 weekly-idle-tasks-status）；mosaic ZCode 池 51 個 `project-*` 檔無此名。反查表自我要求「對帳義務：動排程或改消費端接線時同步對應行」，provenance 終點按名反查失敗，未來對帳者需知道 08-30 吸收事件才能定位 | A1 provenance 改指現名 `project-nightly-schedule-migration.md` 或標「已併入該檔（2026-08-30 吸收 12 檔）」；ai-rules 側 memory 條目同句同步（非本弧範圍，登記歸 mosaic/池治理線） |
| 3 | 🟢 | high | commit e1aecb0 message（非檔案缺陷） | **commit message 宣稱未發生的變更**：e1aecb0 稱「corrections-weekly telemetry --pool 示例改指 .agents/memory/ 主體」，但 `git show e1aecb0 --stat` 只有 schedule-registry.md＋draft-3 刪除兩檔；且 `git show 4ef2982:skills/corrections-weekly/SKILL.md` 第 35 行基底就已 是 `--pool /Users/ctai/Github/ai-rules/.agents/memory`——無變更發生（air-54 c57029d 已先行）。檔案現況正確（SKILL.md:35），純 audit trail 不實 | 無需改檔；卡 notes 若仍列此項為已完成順手項，結案蒸餾時標「already-true（air-54 已改）」，避免後人按 message 找 diff |
| 4 | 🟢 | high（文本事實） | ai-analysis/schedule-registry.md:7 vs :34-35 | **header「scope」句與新增 A1/A2 張力**：scope 稱「mosaic 側排程指針→memory reference_periodic-task-landscape」，但反查表 A1/A2 已直接記載 mosaic 側排程事實（雖標 provenance／記載面）——scope 句未隨反查表更新，讀者可能誤以為 mosaic 側只有指針無記載 | scope 句補半句：「反查表 A1/A2 為跨 workspace 記載面（provenance 標注）」 |
| 5 | 🟢 | high | skills/acceptance-evidence/SKILL.md:20（新增句）；既有狀態非本弧造成 | **「repo 內 `deploy/launchd/` 只是源」的覆蓋缺口**：`deploy/launchd/` 實際僅 `com.ai-rules.backlog-browser.plist`；`com.ai-rules.backlog-cleanup` plist 無版控源（fd 全 repo 僅命中腳本）。新句是通則指引非完備性宣稱，不算錯；但照指引盤點者會撞見 cleanup plist 源缺失，live plist 毀損時無法自 repo 重建 | 補 backlog-cleanup plist 源入 `deploy/launchd/`，或句尾註「源覆蓋不含 2026-09-06 後新增 plist」——歸 AIR-54 收尾或 maintenance 順手項 |

## 審查者自證（實跑命令＋結果）

1. `git rev-parse --short HEAD` → `19974d5`；`git status --porcelain` → 僅 untracked 報告檔；`git log --oneline 4ef2982..HEAD` → 15 commits
2. `git diff 4ef2982..HEAD -- <scope 16 檔>` → 全量逐行讀畢（30.7KB persisted log 全讀）
3. drift 掃描：`rg -n '23:[0-9]{2}|nightly-sequence|com\.mosaic|com\.code-reality|com\.user\.crg-mcp' skills/ rules/ AGENTS.md agents/` → **0 hits**（exit 1）；追加 `rg '定時任務'` 同面 → **0 hits**（exit 1，無 pipe 掩蓋重跑）
4. 術語掃描：`rg -n '排程任務|排程載體' skills/` → 13 檔命中，逐條讀語義；skills/at/SKILL.md:61「排程任務」指 at job 語境、post-build:23 泛指背景寫入者——非解綁對象，恰當
5. registry 外部依賴存在性：`ls ~/Library/LaunchAgents/com.*` → A3/A5 所指 5 枚 plist 全在場；`plutil -p` 驗證 cleanup 雙 plist `Hour=23 / Minute=50|55` 與 launchd 表一致
6. 腳本接線：`deploy/scripts/run-backlog-cleanup.sh:15` `PRECHECK=.../skills/kanban-board/scripts/backlog_precheck.sh` 在場（A3「已核」屬實）；`run-report-server.sh` 在 `~/Github/mosaic_alpha/deploy/scripts/`（A5 屬實）；`report-assets/_md-viewer.html` 版控本 repo 在場
7. registry 內部：A4「上表 #1-3」與 ZCode Cron 表 #1-3 編號逐行核對一致；#3 corrections-weekly 對應 cron 表第 3 列；A1/A2 的 23:20 report／nightly-watch 併入（f681b71c9）在 `reference_periodic-task-landscape.md:32,35` 有獨立記載
8. nightly-thin 反查：`rg -n 'nightly-thin' skills/ schedule-registry.md rules/ AGENTS.md` → 僅 3 個 skill 檔命中、registry/memory 條目 0 命中（Finding 1 機械證據）
9. mosaic 池三路搜尋（Finding 2）：`ls mosaic_alpha/.agents/memory/`（3 檔）、`ls ~/.claude/projects/-Users-ctai-Github-mosaic-alpha/`（無 memory/ 子目錄；rg 遞迴僅 session transcript 命中）、`ls ~/.zcode/cli/memories/projects/mosaic_alpha-91db1aef2f9baec8/memory/`（114 檔；`rg -li 'weekly-idle-tasks-status'` 僅命中 project-nightly-schedule-migration.md 的 merged_from 欄）——條目檔名不存在為機械事實；「無其他池位」無法窮盡證明，已照 self-否定義務標註
10. draft-3：`git log --diff-filter=D` → e1aecb0 刪 drafts/ 檔殼；`ls backlog/tasks | rg air-53` → AIR-53 卡在場且主題（Muse bundle 超限治理）吻合「已承接」宣稱；殘留引用僅歷史記載（air-45 卡 desc、done/ EP、check_single_source.py:355 註解）——符合「刪除不留 tombstone」紀律，無 finding
11. backlog/config.yml `check_active_branches true→false`：skills/kanban-board/SKILL.md:21 既有記載「**ai-rules 現值 false**——09-09 起單 WT working copy 單一真相形態」——本弧 commit 是把 config 對齊既有文檔記載的一致性修復，無矛盾
12. daily-maintain Phase 0 改寫：套用文字與卡 notes 備援文案逐字吻合；與 when_to_use（SKILL.md:5）、§配合（SKILL.md:55-57）一致——三處皆「排程載體＋registry 指針」、無時刻/系統名綁定
13. instruction-writing 五維抽查：反查表無元資訊/統計/版號（「更新時點」日期行為該檔既有慣例，豁免）；無 >5 行範例；acceptance-evidence「真實案例：standup 誤刪」為規範允許的真實案例標記
14. memory-B 形態承接：`.agents/memory/_inventory.md` 在場（cross-verify memory 軸、commit 2.8 新檢索語義有所指）；`reference_periodic-task-landscape.md` 在場

**無法驗證項（不腦補）**：mosaic workspace 23:20 cron prompt 現值與 automationId（跨 workspace，A1 已自我標注）；nightly-thin 是否現役任務（Finding 1 之 (c) 選項需 mosaic 側確認）；`project-weekly-idle-tasks-status` 是否存在於本機未探及的其他池位。

## 結論

排程解綁主體乾淨（時間/系統名機械掃描全清、plist/腳本/條目存在性全數對帳通過、registry 內部表間一致）；兩個 🟡 均為「反查鏈端點」問題（nightly-thin 無錨點、A1 provenance 指向已吸收條目名），不影響行為契約，建議結案前順手補。
