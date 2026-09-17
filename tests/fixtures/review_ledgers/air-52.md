# AIR-52 弧審查 Finding Record（docs-mode——AI 可執行性）

reviewed revision: air-52 @ 19974d5d59a8bde3565c8c1608c0542252b01a19
scope: 4ef2982..HEAD (AIR-52 arc, docs-mode)
reviewer: fresh-eyes independent code-reviewer（唯讀；唯一寫入＝本帳本）

## Finding Record

| ID | severity | confidence | file:line | finding | 建議修法 |
|----|----------|------------|-----------|---------|----------|
| F1 | P1 | high | skills/kanban-board/SKILL.md:21 ↔ backlog/config.yml:13 | skill 權威記載 `check_active_branches: true`（多 WT repo 必開——board 唯讀顯示他 branch 已 commit 卡＋next-id 掃描跨 branch 卡防撞），本弧 feac961 把 config.yml 改為 `false`（commit message：working copy 單一真相）但未同步 skill 的「config.yml 關鍵鍵」記載——文檔面與組態面直接矛盾 | kanban-board SKILL.md:21 補記 ai-rules 現值差異與裁決理由（例：「ai-rules 09-09 起 false——working copy 單一真相；id 防撞靠建卡預掃」），避免未來 session 按「必開」翻轉刻意裁決（mosaic 先例 memory 條目明言「刻意關——重開先回想動機」，本 repo 關閉動機目前只落在 commit message） |
| F2 | P2 | high | skills/daily-maintain/SKILL.md:57；skills/maintain/SKILL.md:221；skills/standup/SKILL.md:10 ↔ ai-analysis/schedule-registry.md（全文 0 命中） | `nightly-thin` 系統名殘留三處，registry 反查表 A1-A5 與 ZCode Cron 表皆無此條目；daily-maintain:57 同句宣稱「時刻/載體現況見 registry 反查表」但該表反查 nightly-thin 落空——S1 解綁契約（時刻/系統名歸排程系統＋registry）對 nightly-thin 未收斂（f9445b7「同類隨掃補 2」漏掃此類）；主體池 reference_periodic-task-landscape 亦僅記 nightly-sequence 22:57（09-08 版），現名對不上 | registry 反查表補 nightly-thin 條目（或併入 A1／跨 repo 指針註記現名與對應）；skill 端三處改「排程載體／report 組裝任務」中性語義，或改指 registry 對應行 |
| F3 | P3 | high | .agents/memory/reference_muse-code-cli-facts.md:21（repo 外主體池，非版控） | e1aecb0 刪除 draft-3 檔後，主體池條目殘留懸空指針「瘦身裁決材料見 ai-rules `backlog/drafts/draft-3`」——材料實質已由 AIR-53 卡＋s3-report 承載，指針過時會誤導檢索 | 池條目指針改指 AIR-53 卡或 ai-analysis/reports/2026-09-08-codex-philosophy-instruction-layering.md（body 歸 owner session／弧結案蒸餾流程承接） |
| F4 | P3 | medium | skills/cross-verify/SKILL.md:22 | memory 軸無條件宣稱「MEMORY.md 僅常駐定額投影、非全量」「檢索入口＝_inventory.md」——依 memory-audit 口徑該形態僅 B 形態（池內有 _resident-set.md）成立；A 形態池 MEMORY.md 即全量投影且可能無 _inventory.md，指引失效。同弧 commit SKILL 2.8 措辭有條件化（「B 形態下」），兩檔新增句口徑不一致 | cross-verify 補形態條件：「B 形態池（有 _inventory.md）：…；A 形態池：MEMORY.md 即全量投影」對齊 commit SKILL 2.8 口徑 |
| F5 | P3 | high | ai-analysis/schedule-registry.md:9 | 更新時點行 AIR-52 條目缺日期前綴（同行 2026-09-06、2026-09-09（AIR-54 S2…）皆帶日期），時序資訊缺失；rebase 並存刻意安排可理解，但補日期不影響並存 | 補「2026-09-10（AIR-52——…）」格式對齊同行慣例 |
| F6 | P3 | high | ai-analysis/schedule-registry.md:7 vs :34-35 | scope 行「mosaic 側排程指針→memory 條目（不進本表）」與反查表 A1/A2 直接記載 mosaic workspace 排程（23:20 report）有輕微張力；表頭已有「跨 workspace 條目以記載面為準」自我說明，scope 行未提反查表例外 | scope 行補一句「反查表 A1/A2 為記載面例外（消費端反查需要）」 |

## 驗證通過項（無 finding）

- S1 解綁機械驗收：`rg '23:[0-9]{2}' skills/ rules/` → 0 hits；`rg 'com\.mosaic' skills/ rules/` → 0 hits；`rg '定時任務' skills/` → 0 hits；`nightly-sequence` 殘留全在 ai-analysis/ 記載面（archive EP／memory 副本／telemetry JSON），skills/rules 行為契約面乾淨。
- 引用完整性：A3 `deploy/scripts/run-backlog-cleanup.sh`＋`skills/kanban-board/scripts/backlog_precheck.sh` 在場；A5 `run-backlog-browser.sh` 本 repo 在場、`run-report-server.sh` 住 mosaic 三 repo 的 `deploy/scripts/`（「各 repo」措辭成立）；`report-assets/_md-viewer.html` 在場；AIR-54／AIR-53 卡在場；P5 改寫後 daily-maintain Phase 0／when_to_use／§配合三處 registry 指針在場且 A1 記載 daily-maintain 消費（成立條件自我一致）；commit SKILL 引 memory-audit「適用載體」錨點在場；corrections-weekly:35 `--pool` 已指 `.agents/memory` 主體；A2 `f681b71c9` 於主體池 reference_periodic-task-landscape.md 可達。
- 一致性：術語「排程載體」統一（例外見 F2）；commit SKILL 2.8 與 memory-audit B 形態口徑一致（有條件化）。
- 副作用：.gitignore 新行 `.muse/`、`.playwright-mcp/`——兩目錄存在於 disk、`git ls-files` 0 追蹤檔，無破壞；backlog/config.yml `check_active_branches: false` 的文檔矛盾見 F1（id 防撞殘餘靠建卡預掃，風險有限）。
- draft-3 刪除：AIR-53 卡在場＋09-08 EP s3-report「draft-3 結案吸收」記載，承接鏈成立；殘留引用皆歷史記載面（例外見 F3）。

## 無法驗證項（unverified，不當事實陳述）

- S4 CronUpdate（23:40 cron prompt 動態 gate 口徑）＝repo 外 ZCode db 操作，本 repo 無機械證據；registry A4「gate 口徑已動態化（AIR-52 S4）」標 unverified（卡 notes 09-10 04:15 有執行記錄，屬 self-report）。
- mosaic workspace CronList 23:20 automationId（跨 workspace 不可直驗；registry A1 已標 provenance，符合自訂口徑）。
- backlog CLI binary 內部對 `check_active_branches` 的實作（本地安裝為 binary wrapper `backlog.md@1.50.1`，README 無此選項文檔；語義依 kanban-board SKILL 自述＋池條目 reference_backlog-md-browser-id-mechanics 記載，F1 的矛盾本身不受影響——兩行並排逐字驗證）。

## 審查者自證（實際執行命令）

1. `git log 4ef2982..HEAD --oneline` → 13 commits；`git rev-parse HEAD` → 19974d5
2. `rg -n '23:[0-9]{2}' skills/ rules/` → exit 1（0 hits）
3. `rg -n 'com\.mosaic' skills/ rules/` → exit 1（0 hits）
4. `rg -n '定時任務' skills/` → exit 1（0 hits）
5. `rg -n 'nightly-sequence' skills/ rules/ ai-analysis/` → skills/rules 0 hits；ai-analysis hits 皆 archive/memory 副本/JSON 記載面
6. `rg -n 'nightly-thin' ai-analysis/schedule-registry.md` → exit 1；`rg -n 'nightly-thin' skills/` → 3 hits（F2 證據）
7. `ls deploy/scripts/run-backlog-cleanup.sh deploy/scripts/run-backlog-browser.sh`＋`ls skills/kanban-board/scripts/backlog_precheck.sh` → 在場；`fd 'run-report-server' ~/Github --max-depth 4` → mosaic 三 repo 命中
8. `fd -t f 'air-54' backlog/`＋`fd -t f 'air-53' backlog/` → 兩卡在場；`git log --diff-filter=D --name-only` → draft-3 刪於 e1aecb0
9. `rg -n 'draft-3' /Users/ctai/Github/ai-rules/.agents/memory/` → reference_muse-code-cli-facts.md:21 命中（F3 證據）
10. `rg -n 'check_active_branches' skills/kanban-board/SKILL.md backlog/config.yml` → :21 true vs :13 false（F1 證據；初跑誤用 `rg -rn`（-r 為 replace flag）污染輸出，已重跑正確語法）
11. `git ls-files .agents/memory/ | wc -l` → 0（池非版控）；`git ls-files | rg '^\.(muse|playwright-mcp)/'` → exit 1（無追蹤檔）
12. `rg -n '適用載體' skills/memory-audit/SKILL.md` → line 10 在場；`rg -n 'pool' skills/corrections-weekly/SKILL.md` → :35 已指主體
13. `rg -n 'nightly' /Users/ctai/Github/ai-rules/.agents/memory/reference_periodic-task-landscape.md` → 僅 nightly-sequence 22:57／nightly-watch 併入記載（F2 輔證）
14. `rg -n 'f681b71c9' .agents/memory/` → reference_periodic-task-landscape.md 命中（A2 引用可達）
