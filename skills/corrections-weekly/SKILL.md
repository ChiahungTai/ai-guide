---
name: corrections-weekly
description: "糾正模式週報＋CR 使用健檢＋memory 寫入歸因——三職週報：①挖掘本週用戶對 AI 的糾正訊息、分類計數、累積月檔；②量測 code-reality 消費指標（主形態＝事件觸發：CR wiring 變更弧收尾時跑 cr_usage、數字附卡——cr-audit R5；週期 cron 降 optional，KPI 換 negative-claim CR 覆蓋率等、penetration 只當健康診斷），advisory 趨勢對比；③memory 成功寫入歸因（AIR-40 telemetry——actor×entry 排行、copies/errors 分列、index baseline 對比；流量非品質，違規抽驗留 LLM）。腳本撈候選（ZCode db.sqlite 面）、LLM 只做判讀分類。排程載體自動跑（ai-guide workspace；時刻見 ai-analysis/schedule-registry.md）或手動觸發。產出供治理決策。"
when_to_use: "週期排程到點；或用戶要求糾正模式分析/月報/趨勢對比時手動載入。不適用：單一 session 的即時糾正處理（那是當下對話的事）。"
allowed-tools: ["Read", "Bash", "Write", "Edit"]
---

# corrections-weekly — 糾正模式週報＋CR 使用健檢

> 背景：兩週遙測實證（2026-08-29 brainstorm §2.4）——~30 糾正/2週（方向錯＞重複勞動＞遺漏），散在 1/4 sessions，隨 session 消失。本 skill 把它變成可累積的治理訊號。方法經 Agent A 驗證；機械面沉腳本（冷 context 安全），判讀面留 LLM。
> 雙職（2026-09-03 user 裁定）：本 skill 是唯一讀遙測對話面（ZCode db.sqlite）的週期班次——CR 使用健檢的資料源在這裡，故併入（advisory；升級① cr-research 落地後的常態驗收迴路）。

## 步驟

1. **跑腳本撈糾正候選**（機械面——勿手打 SQL）：

   ```bash
   uv run python /Users/ctai/Github/ai-guide/skills/corrections-weekly/scripts/mine_corrections.py --days 7
   ```

   輸出：候選清單（時間／session 短 id／摘錄）＋計數。腳本已排除 subagent sessions、task-notification 注入、compact 摘要。

2. **跑 CR 使用量腳本**（機械面）：

   ```bash
   uv run python /Users/ctai/Github/ai-guide/skills/corrections-weekly/scripts/cr_usage.py --days 7
   ```

   輸出三源三證據類：源1 ZCode db——CR skill 調用（cr-query＋code-reality，distinct sessions＋總計）、CR MCP 工具呼叫（per-tool distinct sessions）、對照 Bash rg part 數；源2 bridge jobs——**call 證據只認 `item.completed`＋`command_execution` 的 command 欄位 match CR CLI**（文字面提及≠呼叫——條文引用與呼叫混淆是誤報主體），寫入面 subcommand 另計，`[SRC]`／未 index 驗證／degraded marker＝evidence-bearing jobs（非 CR calls）；源3 agent 產出（`output.txt` 無工具結構，一律計 evidence 不計 call）。**判讀語義（cr-audit R5 換軌）**：滲透計數只是健康診斷（agent 在不需 CR 的任務亂 call 也達標，不作 KPI）；KPI 主軸＝**negative-claim CR 覆蓋率**（本週弧 negative claims 中附 `[SRC]`／CR 證據的比例）、**rename-delete preflight 覆蓋率**、**query not-found→retry 成功率**、**silent fallback 數**——分母取材本週弧 findings/卡面（LLM 判讀面，腳本只供工具呼叫面）。事件觸發主形態：CR wiring 變更弧收尾時必跑本腳本＋數字附卡（**runtime hook＝post-build 階段 4「CR wiring telemetry checkpoint」，detector 清單單一源在彼**）；週期 cron 跑到時若該週無 wiring 變更，CR 段寫「事件觸發制——本週無 wiring 變更，KPI 段略」。

2b. **跑 memory 寫入歸因腳本**（機械面——AIR-40；池＝本 repo 對應 CC 池）：

   ```bash
   uv run python /Users/ctai/Github/ai-guide/skills/memory-audit/scripts/memory_telemetry.py writes \
     --pool /Users/ctai/Github/ai-guide/.agents/memory \
     --zcode-db ~/.zcode/cli/db/db.sqlite \
     --cc-root ~/.claude/projects/-Users-ctai-Github-ai-guide \
     --output ai-analysis/memory-telemetry/weekly-<YYYYMMDD>.json \
     --baseline-dir ai-analysis/memory-telemetry/baselines
   ```

   > 輸出與 baseline 住常態目錄 `ai-analysis/memory-telemetry/`（不隨任務家歸檔移動——R6 教訓：baseline 指向已歸檔任務家會斷承接）。既有 baseline 已自 `done/09-07-memory-governance/evidence/baselines/` 遷入。

   輸出 report：counts（successful／errors／copies_folded）、top_actors／top_entries（寫入次數×payload chars）、index_delta（baseline 對比；首輪建 baseline）。判讀：top 寫入者（subagent session 大戶＝抽驗線索——追 source_ref 到原始事件看上下文）；errors>0 如實報（失敗不冒充無寫入）；**寫入量是流量非品質/存量**——違規判斷留 LLM 抽驗，不按 chars 自動判。路徑陷阱：ZCode db＝`~/.zcode/cli/db/db.sqlite`（`~/.zcode/cli/db.sqlite` 頂層 0-byte 殘檔勿用）。

3. **逐則判讀分類**（LLM 面）：對每個糾正候選判斷是否真糾正（關鍵詞有假陽性——技術討論中的「不需要」可能不是糾正），分類：**方向錯／重複勞動（whole-picture blind spot）／遺漏／修了仍壞／過度工程／驗證責任推給用戶／其他**。邊界案例標「疑似」不硬歸。

4. **append 月檔**：`ai-analysis/reports/corrections-<YYYY-MM>.md`（每月一檔累積）。每週一節：

   ```markdown
   ## <起訖日> 週報
   - 計數：方向錯 N／重複 N／遺漏 N／修了仍壞 N／過度工程 N／驗推用戶 N（候選 X、真糾正 Y）
   - Top 引述（≤3，session id＋200 字內摘錄）
   - vs 前週：一句趨勢（哪類升降）
   - 訊號：有無新湧現模式（如新規則繞道形態）——有則明列，無則寫「無新形態」
   ### CR 使用（R5 換軌後形態）
   - 健康診斷：CR skill（cr-query＋code-reality）N sessions（總計）；CR MCP top 3 工具各 N sessions；對照 Bash rg：N
   - KPI（有 negative-claim/rename-delete 弧的週才填）：negative-claim CR 覆蓋 N/M；rename-delete preflight 覆蓋 N/M；retry 成功率；silent fallback 數
   - 事件觸發註記：本週 CR wiring 變更（卡號）＋附卡數字；無則寫「無 wiring 變更」
   ### Memory 寫入（AIR-40）
   - successful N（errors N／unmatched N／folded N／ambiguous N）；top actors ≤3（session 短 id＋次數×chars）；top entries ≤3；index_delta（vs 前輪 baseline，首輪標 baseline 已建；partial 標記多 pool 部分和）；unknown actor sessions；evidence 路徑一行
   ```

5. **判讀產出**（報告尾一行）：本月累積趨勢是否支持「某規則在衰減、該修」或「negative-claim/rename preflight 覆蓋率下滑、該接線」的具體建議——沒有就寫「無需動作」（不硬擠結論）。

## 紀律

- DB 唯讀（腳本 mode=ro）；報告一頁內；腳本失敗 2 次即止（印 `[FAIL]` 收工，勿重試迴圈燒 usage——冷 context 教訓）
- 不動 repo 其他檔案；corrections 月檔未 commit 由用戶決定去留
- 排程語境（冷 context）：本 skill 自足——腳本路徑絕對、分類定義內嵌、不依賴其他 skill

## 邊界

- 只挖掘 ZCode 面（CC 側糾正不在 db.sqlite——如需雙面再擴，YAGNI 現不建）
- CR 健檢計全 workspace（全域單一 DB——mosaic 端 CR 用量可見，一併計入）
- 常態化裁決沿革（用戶 08-30 定案週六排程；CR 段 09-03 併入；**R5 換軌 2026-09-10**：CR 量測主形態＝事件觸發（wiring 變更附卡），週期 cron 降 optional）；月檔累積 4 週後可做月度趨勢總結（屆時手動）
