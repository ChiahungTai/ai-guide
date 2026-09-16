# mosaic 側排程修復工單（跨 workspace——依紀律由 user 或 mosaic-side session 執行）

> 2026-09-14 ai-rules→ai-guide 改名掃尾。mosaic workspace 的排程**會照常觸發**（workspace 路徑 `/Users/ctai/Github/mosaic_alpha` 未變），但以下兩條 prompt 內嵌 `/Users/ctai/Github/ai-rules/...` 絕對路徑，改名後這些讀取 file-not-found——**2026-09-14 晚起逐步失效**。依 cross-workspace 紀律，ai-guide 側 session 不代改，本檔＝可執行工單。

## 待修排程（mosaic workspace；修法＝CronUpdate prompt，僅路徑替換 `ai-rules`→`ai-guide`，其餘逐字保留）

| automationId | 時刻 | 受影響 prompt 路徑引用（實測自 session db 考古） |
|---|---|---|
| `automation-70e85d4c-2379-4a92-9bab-067a3657ee87` | 每日 23:20 daily-report 組裝＋LLM 節 | `skills/daily-maintain/SKILL.md`、`skills/standup/SKILL.md`＋`skills/standup/scripts/aggregate_sessions.py`、`skills/audit-test/SKILL.md`（週六段）、`skills/memory-audit/scripts/generate_index.py`（cmp 層1）、`scripts/deploy_agents.py`（bundle gate 動態讀） |
| ~~`automation-13dfeb9c-2f03-4cce-add2-c8448ad6f369`~~ 每晚 23:50 nightly-watch——**〔09-14 深夜勘誤：此條已不存在〕**mosaic workspace 現存為 `automation-70e85d4c`（23:20，nightly-watch 收編後）＋`automation-26b39582`（週六 22:10）；照表修復時以 `CronList`（mosaic workspace）現存 id 為準，其 prompt 內 ai-rules 路徑若在場一併替換 | 每晚 23:50 nightly-watch（已收編） | `skills/memory-audit/scripts/generate_index.py`、`scripts/deploy_agents.py` |

修復操作（在 mosaic workspace 開 session）：

1. `CronUpdate` 兩條：prompt 內所有 `/Users/ctai/Github/ai-rules/` → `/Users/ctai/Github/ai-guide/`；prompt 內「ai-rules 以單一 AGENTS.md bundle…」「修復在 ai-rules repo」等自稱同步改 ai-guide；**其餘逐字不動**（codex 裁決紀律：改名修復與行為變更分離）。
2. 完成後 `CronList` 對照本表 automationId 逐字核對。
3. mosaic memory 條目同步（mosaic 側寫入流）：`reference_periodic-task-landscape`、`project-nightly-schedule-migration` 內的 ai-rules 池路徑指針 → ai-guide（`/Users/ctai/Github/ai-guide/.agents/memory/`）。

## 已核不受影響（mosaic 側）——〔09-14 晚勘誤：report-server 原列此節為錯誤宣稱，已移入下方「⚠️ 追加」節待修〕

- `com.mosaic.backlog-cleanup` plist／`com.mosaic.nightly-sequence`：全指 mosaic_alpha 自身路徑，無 ai-rules 引用。
- mosaic 排程 session 的開啟路徑：workspace 未改名，session cwd 照舊——只有上述 prompt 內嵌路徑壞。

## ⚠️ 追加（09-14 judge M3/J1 勘誤）：`run-report-server.sh` 三條 ai-rules 引用

**勘誤**：本工單初版第 20 行宣稱「report-server 全指 mosaic_alpha 自身路徑，無 ai-rules 引用」——**錯誤**。實況（judge 實讀 `mosaic_alpha/deploy/scripts/run-report-server.sh`）：
- 前置檢查陣列含 `/Users/ctai/Github/ai-rules/ai-analysis` 與 `/Users/ctai/Github/ai-rules/report-assets`——**兩路徑已隨改名消失，`[ ! -d ] → 拒起`＝:6421 server 現在整台起不來**
- `--static-dirs` 兩行 mount：`ai-rules=/Users/ctai/Github/ai-rules/ai-analysis`、`viewer=/Users/ctai/Github/ai-rules/report-assets`——同為死路徑

**修法（mosaic 側執行）——〔09-14 深夜 user 裁決縮減：ai-guide 全面退出 :6421，兩條死 mount 直接刪除〕**：
1. 前置檢查陣列：刪 `/Users/ctai/Github/ai-rules/ai-analysis` 與 `/Users/ctai/Github/ai-rules/report-assets` 兩行（保留 main/v2/warrant 三行）
2. `--static-dirs`：刪 `ai-rules=/Users/ctai/Github/ai-rules/ai-analysis` 與 `viewer=/Users/ctai/Github/ai-rules/report-assets` 兩行
3. 依據：ai-guide 卡 refs 已走相對路徑新制（VSCode 內建），**To Do 卡零 :6421 依賴**（air-74/75 為 Done、相對路徑並列兜底）；殘餘 `/viewer/` 引用＝ai-guide 側殼 12（`_tasks/_archived/` 12 個＋`ai-analysis/blueprint/index.html` 1 個；活躍殼 `_tasks/09-08-context-lifecycle-unification/` 3 處 viewer link 已改相對路徑）＋Done 卡 24、mosaic 側殼 2／Done 卡 0——全部歷史態；mosaic 有自己的 viewer 副本（`ai-analysis/_md-viewer.html`，走 main mount）不依賴此 mount。mosaic To-Do 卡三張（mos-22/22.4/22.8，位 mosaic repo）的冗餘 viewer URL 已由 ai-guide session 刪除（相對路徑並列條目保留）
4. 驗證：重啟後 server 應能起（無 missing static dir 拒起）；`curl -o /dev/null -w '%{http_code}' 'http://127.0.0.1:6421/main/_md-viewer.html'`＝200
