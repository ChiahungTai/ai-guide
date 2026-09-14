# mosaic 側排程修復工單（跨 workspace——依紀律由 user 或 mosaic-side session 執行）

> 2026-09-14 ai-rules→ai-guide 改名掃尾。mosaic workspace 的排程**會照常觸發**（workspace 路徑 `/Users/ctai/Github/mosaic_alpha` 未變），但以下兩條 prompt 內嵌 `/Users/ctai/Github/ai-rules/...` 絕對路徑，改名後這些讀取 file-not-found——**2026-09-14 晚起逐步失效**。依 cross-workspace 紀律，ai-guide 側 session 不代改，本檔＝可執行工單。

## 待修排程（mosaic workspace；修法＝CronUpdate prompt，僅路徑替換 `ai-rules`→`ai-guide`，其餘逐字保留）

| automationId | 時刻 | 受影響 prompt 路徑引用（實測自 session db 考古） |
|---|---|---|
| `automation-70e85d4c-2379-4a92-9bab-067a3657ee87` | 每日 23:20 daily-report 組裝＋LLM 節 | `skills/daily-maintain/SKILL.md`、`skills/standup/SKILL.md`＋`skills/standup/scripts/aggregate_sessions.py`、`skills/audit-test/SKILL.md`（週六段）、`skills/memory-audit/scripts/generate_index.py`（cmp 層1）、`scripts/deploy_agents.py`（bundle gate 動態讀） |
| `automation-13dfeb9c-2f03-4cce-add2-c8448ad6f369` | 每晚 23:50 nightly-watch | `skills/memory-audit/scripts/generate_index.py`、`scripts/deploy_agents.py` |

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

**修法（mosaic 側執行）**：
1. 前置檢查陣列兩行改 `/Users/ctai/Github/ai-guide/ai-analysis` 與 `/Users/ctai/Github/ai-guide/report-assets`
2. `--static-dirs` 兩行改 `ai-guide=/Users/ctai/Github/ai-guide/ai-analysis`、`viewer=/Users/ctai/Github/ai-guide/report-assets`
3. 舊 route 名（`ai-rules=`）若保留會讓舊殼連結續命——不建議；舊殼（13 個）已由 ai-guide 側 lint 改雙前綴過渡容納，深連結 404 屬歷史態可接受
4. 驗證：重啟後 `curl -o /dev/null -w '%{http_code}' 'http://127.0.0.1:6421/ai-guide/ai-analysis/blueprint/index.html'`＝200、`http://127.0.0.1:6421/viewer/_md-viewer.html` 任意 `?p=/ai-guide/…` 可渲染
