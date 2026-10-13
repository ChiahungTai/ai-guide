# Guide 歷史對話 dry run

Flash 檢索四個歷史情境，Terra gpt-5.6-terra/high 逐案 fresh context 應用現行 WT guide，Marshal 依輸出前凍結 oracle 判讀：三案 PASS、一案 FAIL。這是四個 diagnostic samples，不是統計可靠性、前後因果比較或全 guide 驗收。

材料為只讀 ZCode SQLite export，保留 session、part、timestamp、截斷旗標。worker 只做模擬選擇，未執行歷史中的授權或真實派工／收信。Source 是含 AIR-327 的隔離 WT，非宣稱已部署現況。

| 案例 | 結果 | 可觀察行為 |
|---|---|---|
| H1 Marshal 角色 | PASS | 保留原 writer，派唯讀調查後交獨立意見，自己裁決，不自行改 code/rules；被指控 session 缺證據明列未知 |
| H2 native/WebGPT 分池 | PASS | 不把 native 負面額度推成 WebGPT 不可用，先按池查證現值；不擅換 family/API |
| H3 mail watcher 接續 | FAIL | 正確 status-first／無 cron，但 missing/stale 分支直接要求再次 start，未核對既有 watch 意圖／opt-in；且將 per-repo fresh 外推成 caller 可被通知 |
| H4 單純問進度／MCP 可用性 | PASS | 查目前 scope/receipt、live tool inventory、一次唯讀 probe；未擴成建卡、部署或派工 |

H3 是相對預先凍結接續判準的失敗；具體哪段 guide 造成它尚無因果驗證。歷史 worker 是否真的沒啟動亦未知，不能由沒報狀態推斷。此次回放顯示應補「既有啟動意圖／status／observer／delivery」的區分，不支援新增永久監控 daemon。

Flash 報告中的三個外推已否決：沒有 always-on Marshal 規則（實際在 ai-development-guide.md:36-38）；沒回報哨等於沒啟 worker；歷史 user 說 WebGPT 可用等於當下必可用。接受其逐字引用與 provenance，不接受這些結論。

H4 初次 job 因 Selected model is at capacity 失敗、零覆蓋；終態與空結果核對後，間隔一次同模型 retry 成功。未靜默換模型。

## Evidence

保全路徑根＝`/Users/ctai/Github/ai-guide/.agent-tmp/air327-retained/`（收線前由 owning WT 複製；原 job 證據另由 wt-close drain 保全）：

- `air327-history-oracles.md`：輸出前判準。
- `air327-history-flash-result.md`：Flash job `job-mv6dk0cp-953564` 原始檢索。
- `history-case-0.json` 至 `history-case-3.json`：個案刺激，互相隔離。
- `history-terra-0-result.md`：H1 `job-mv6dl96i-2db8pj`。
- `history-terra-1-result.md`：H2 `job-mv6dl9e3-o9gvvv`。
- `history-terra-2-result.md`：H3 `job-mv6dqhs1-ri4btt`。
- `history-terra-3-result.md`：H4成功 `job-mv6dwnxk-1bo8vt`；初次失敗 `job-mv6dswdr-5q072p`。
- `history-adjudication.md`：逐案裁決。

歷史原始 export 位於 primary `.agent-tmp/air327-history-context.json`；不足部分明列，沒有重建缺失對話。所有背景腿已回收，transport completed 與本報告 PASS 分開判。
