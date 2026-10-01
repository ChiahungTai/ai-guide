# AIR-52 primed review 帳本
- reviewed revision: air-52 @ 5b0af74
- scope: 4ef2982..HEAD（卡面指定 16 檔；含審查中途平行 session 加入的修正 commit 5b0af74——見下）
- uncommitted identity: `R backlog/tasks/air-59…→air-65…`（staged，他人/平行 session）＋ `?? ai-analysis/reports/2026-09-10-repo-consistency-scan.md`（untracked，範圍外）
- 審查中途 HEAD 前進：審查開始時 HEAD=19974d5，期間平行 post-build 修正 session 提交 5b0af74（fresh-eyes `.review/air-52.md` 六 findings 的修正）。本帳本所有結論以最終 HEAD=5b0af74 為準；與 fresh-eyes 六項的關係：F1/F2/F4/F5/F6 已驗證落地，F3（池條目懸空指針）依其裁決歸弧結案蒸餾。本帳本 finding #1/#2 為 F2 修正**本身引入**的新問題——fresh-eyes 未及見。

## EP 對照

- S1＝**落地於 f9445b7，但 HEAD 回歸**：17 處 hunks 對帳 ✓（audit-test 4／daily-maintain 3／standup 3／maintain 1／skills-CLAUDE 1／kanban-board 1／cr-query 2＋隨掃補 post-build 1／corrections-weekly 1）；驗收① rg 於 f9445b7 全清 ✓——惟 5b0af74（F2）把「mosaic 23:20 report」帶回 daily-maintain:57，驗收①在 HEAD **機械破功**（finding #1）
- S2＝**落地**：c72f5a6 增反查表 A1-A5、e1aecb0 擴欄「新架構職責註記」、5b0af74 F5（更新時點補日期 2026-09-10）/F6（scope 行 A1/A2 記載面例外）。A3/A5 plist 實況、A3 precheck 接線重驗 ✓。A1 新增別名 nightly-thin 無 provenance（finding #2）
- S3＝**落地**：0844380——LaunchAgents 現值＋registry 反查表＋目標 workspace memory 池＋消費端 repo deploy/；standup 誤刪真實案例錨指向 A1 正確 ✓
- S4＝**CronUpdate 無法從 diff 驗證**（排程系統操作）——卡 notes（09-10 04:15）與 memory 記載面（reference_periodic-task-landscape ai-rules workspace 節「09-10 AIR-52 S4 CronUpdate 動態口徑」）雙源一致宣稱 done；口徑前提機械在場（generate_index.py:68-72 GATE_CHARS/GATE_CHARS_B/GATE_BYTES/GATE_LINES）。③cross-verify memory 軸＋commit 2.8 `_inventory.md` 落地於 93496df、F4 補 A/B 形態條件 ✓
- P5＝**落地於 19974d5**：daily-maintain Phase 0 改寫與卡 notes 備援文案逐字一致 ✓——卡 notes 仍稱「P5 仍待」→ 宣稱落後實際（finding #3）

驗收五項對照：①f9445b7 時點 ✓／HEAD ✗（finding #1）②A3/A5 機械對帳 ✓、A1/A2 provenance 標記 ✓（A1 新別名除外，finding #2）③雙源一致、diff 不可驗證（明示）④mosaic 23:20 連兩晚產出＝跨 workspace runtime，**unverified** ⑤「其餘面無需變更」＝自述、diff 無對應變更，**unverified**。

## Findings

| # | 嚴重度 | 信心 | 位置 | 發現 | 建議 |
|---|--------|------|------|------|------|
| 1 | 🔴 | high | skills/daily-maintain/SKILL.md:57（5b0af74 引入） | F2 修正回填時刻 token：`report 主體由 registry 反查表 A1 排程載體（mosaic 23:20 report）組裝`——卡自訂驗收① `rg '23:20\|nightly-sequence\|com\.mosaic' skills/` 全清在 HEAD 機械破功（重跑命中此行；S1 commit f9445b7 曾宣稱「改後 rg…全清」）。卡 AC#1「驗收五項機械驗證通過」因此無法誠實成立。intent-drift：修正做了驗收合約沒豁免的事 | 二擇一、不可靜默：(a) 標籤去時刻，如「（registry 反查表 A1——mosaic 每日 report 載體）」；(b) judge 明示修訂驗收①語義（registry 指針標籤豁免）並記入卡 |
| 2 | 🟡 | med | ai-analysis/schedule-registry.md 反查表 A1 行（5b0af74 引入） | A1 新增別名「（mosaic 側系統名 nightly-thin）」**無 provenance 標記**，違反同表前言自訂規則「跨 workspace 條目（A1/A2）以記載面為準並標 provenance」。且記載面查無此名：`rg nightly-thin .agents/memory/`（含 reference_periodic-task-landscape）零命中；landscape 記 22:57＝`com.mosaic.nightly-sequence`（OP 測試序列）；mosaic repo 歸檔卡名「nightly 排程遷移（22:57 thin＋report 重排）」把 thin 繫於 22:57——別名疑似把 22:57 任務名誤貼到 23:20 載體。同 commit 的 maintain/standup 把 test-regression/BSR 重錨到 A1（23:20），與 landscape 22:57 OP 序列的舊關聯張力未解。registry 是宣告的機械真相源，貼錯名比懸空名更傷 | 查 mosaic workspace CronList 逐字核別名；核得→A1 對帳欄補 provenance（來源＋日期，比照 automationId 不可直驗的標法）；核不得→移除別名或標 unverified。maintain/standup 的 test-regression 重錨一併對照 22:57 條目複核 |
| 3 | 🟡 | med | backlog 卡 notes／AC vs diff | notes（09-10 04:15）宣稱「**P5 仍待**：04:08 查證 air-59 尚未 ff 進 main——merge＋air-52 rebase 後套用上方備援文案」，實際：P5 已於 19974d5 落地（Phase 0 新文案與 notes 備援逐字一致）、HEAD 已含 air-59 內容（53a7487 在 4ef2982..HEAD）。宣稱落後實際；AC#1 未勾屬程序正常（結案兩步未行） | 收尾 session 結案時同步 notes（P5 done、air-59 內容已隨 rebase/merge 在場）；judge 裁決以 diff 為準 |
| 4 | 🟡 | high | skills/cr-query/SKILL.md:23,117；registry A5 | com.code-reality.mcp 解綁後反查鏈斷——skill 端現文「共享 resident（127.0.0.1:8200/mcp，選配——服務由 OS 服務層管理）」，機械三路皆空：`launchctl list` 無 code-reality、`curl 127.0.0.1:8200/mcp`＝000、~/Library/LaunchAgents 與 /Library/Launch{Daemons,Agents} 均無 plist；registry A5（服務型 launchd 行）未收錄 CR resident。解綁前機械柄（launchd 標籤）被移除而「排程系統＋registry」兩側皆未承接＝**孤兒**，違反決策①雙向閉合（skill↔registry）。緩解：cr-query 偵測梯（MCP 在場→用／缺→CLI fallback）使功能自癒，且屬選配——故 🟡 非 🔴。另「服務由 OS 服務層管理」對現況（無服務）是假述 | 三選一：(a) A5 補 CR resident 行（現況＝未部署＋復原柄）；(b) resident 若已退役，cr-query 刪去該提及；(c) 文字改「選配、現未部署，啟用方式見 code-reality repo」。fresh-eyes 六項未涵蓋此處 |
| 5 | 🟢 | high | feac961：backlog/config.yml:13、.gitignore:68-71 | config.yml `check_active_branches: true→false`＋.gitignore `.muse/`/`.playwright-mcp/` 以「前任 CC 遺留三檔收尾」入弧——卡 desc/notes 零記載（intent-drift：diff 做了 EP 沒提）。緩解：commit message 有記錄、5b0af74 F1 後 kanban-board SKILL.md:21 有現值文檔（「ai-rules 現值 false——09-09 起單 WT working copy 單一真相形態」）——文檔面已閉合，僅卡面缺口。check_active_branches 的 CLI 精確行為未查證（unverified），唯變更語義屬 board 防撞掃描開關、單 WT 形態下風險低 | 結案 notes 補一句歸屬說明；judge 知悉即可 |
| 6 | 🟢 | med | skills/acceptance-evidence/SKILL.md:20 | S3 擴充稱「repo 內 `deploy/launchd/` 只是源」——實際 `fd` 顯示 deploy/launchd/ 僅含 `com.ai-rules.backlog-browser.plist`；`com.ai-rules.backlog-cleanup.plist`（A3）無 repo 源、為 ~/Library/LaunchAgents 本地孤本。源面宣稱覆蓋不全（既有債非本弧引入，但本弧把 deploy/ 定為掃描源時未標例外） | A3 對帳欄或 S3 文補「cleanup plist 尚無 repo 源」，或補版控 |
| 7 | 🟢 | low | ai-analysis/schedule-registry.md A4 行 | 職責註記「AIR-14：＋清淤兜底」歸屬 unverified——本 workspace 可查文檔未見 AIR-14 與清淤兜底的直接關聯記載 | 順手核對歸屬；錯則改註記 |

## 審查者自證（正向確認，機械證據）

- S1 17 hunks 數對帳 ✓（git diff 逐 hunk 點名）；驗收① 於 f9445b7 時點重演 ✓、寬掃 `23:[0-9]{2}` 於 f9445b7 時點全清 ✓（HEAD 上因 finding #1 命中一處）
- A3 對帳重驗 ✓：`deploy/scripts/run-backlog-cleanup.sh:15` `PRECHECK="$REPO_ROOT/skills/kanban-board/scripts/backlog_precheck.sh"`；A3/A5 六個 plist 皆在 `~/Library/LaunchAgents/` ✓
- 五個未入反查表的 mosaic plist（nightly-sequence／night-update／daily-workflow／market-open／disposition-weekly）`rg 'ai-rules'` 零命中——消費端不在本 repo，F6「記載面例外」scope 成立、**無孤兒**
- 記載面三向閉合 ✓：reference_periodic-task-landscape 已記 S1-S3 落地（:37）與 S4 CronUpdate（ai-rules workspace 節）——S4 宣稱有卡 notes 以外的獨立第二源
- S4 口徑前提 ✓：generate_index.py:68-72 `GATE_CHARS=22_500/GATE_CHARS_B=6_000/GATE_BYTES=24_000/GATE_LINES=190`（cron prompt 動態讀取目標真實在場）
- cross-verify／commit 2.8 的 `_inventory.md` 前提 ✓：.agents/memory/_inventory.md 35KB 在場；F4 補 A 形態池條件（MEMORY.md 即全量、可無 _inventory.md）——B 形態預設不再過度泛化 ✓
- S3 錨點 ✓：acceptance-evidence 真實案例「standup 誤刪」指向反查表 A1，A1 行存在且語義相符
- P5 文案 ✓：diff `+` 行與卡 notes 備援文案逐字一致（19974d5）

## 治理規範對照（AGENTS.md 寫作治理／受眾視角）

- 載體選擇 ✓：反查表住 registry（機械對帳 ledger）而非 rule/skill——符合「機械查詢由工具/registry 承擔」；A1-A5 對帳欄 fail-loud（A1/A2 標「不可直驗／未逐字驗證」）符合主動揭露
- 真實案例標記 ✓：acceptance-evidence「真實案例：standup 誤刪」符合「真實失敗案例例外，須標真實案例」
- 長度預算：skill 端解綁皆單行指針化 ✓；acceptance-evidence 擴充句偏長但屬 on-demand skill、資訊密度可接受
- 受眾 ✓：registry 與 skill 改動均為軌道①（LLM 執行鏈機械對帳），無人類 viewport 混裝

## unverified 清單（明示）

- 驗收③（23:40 prompt 無硬編數字）：CronUpdate 為排程系統操作，diff 不可驗證；notes＋landscape 雙源一致宣稱 done
- 驗收④（mosaic 23:20 連兩晚產出、昨日活動節在場）：跨 workspace runtime，本 repo 無法驗證
- 驗收⑤（memory 審查其餘面跟上）：自述性質，diff 無對應變更
- A1 別名 nightly-thin 於 mosaic workspace CronList 的真偽：跨 workspace（finding #2 本體）
- check_active_branches 的 backlog CLI 精確行為（finding #5 附註）
