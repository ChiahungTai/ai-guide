---
name: ui-collab
description: "UI-LLM 協作模式。當使用者啟動互動式 UI（Bokeh/Panel 等）並希望 LLM 觀察操作、提供上下文感知的協助時觸發。適用於任何有 [ACTION] 操作日誌的 UI 協作場景。"
---

# UI-LLM 協作模式

LLM 作為觀察者角色，透過監控 UI 操作日誌理解使用者行為，在被動回應時提供上下文感知的協助。

## 背景執行模式

UI 必須在背景執行，讓 LLM 能同時啟動 Monitor 監控。

- **`python -u`**：背景執行時 Python stdout 會 buffer，不加 `-u` 則 `[ACTION]` 不會即時 flush，Monitor 完全捕捉不到事件
- **`run_in_background: true`**：讓 Bash 在背景執行，立即取得 output file path
- **就緒等待**：`until grep -q "就緒信號" <output_path> 2>/dev/null; do sleep 1; done && echo "UI Ready"`——grep 目標須為 **process 級就緒行**（main 層 serve 前即印，如 `[OK] ... serve: port=N`）
- **就緒信號生命週期（隱性 stdout 契約）**：啟動即印的 stdout line 是 Monitor／ops 腳本消費的**隱性 API**——serve 形態重構（singleton `pn.serve(app.render())` → factory session callback）會把 session 級 readiness **靜默 deferred 到第一個瀏覽器連線**：不開瀏覽器永不印，Monitor until-grep 無限卡等且無錯誤訊號（像 hang、不像 fail）。對策：app 端 main 層 serve 前印 process 級 readiness（per-session 詳情留在 session callback）；啟動路徑重構時盤點就緒行消費端；serve 形態以 AST 釘測固定。真實案例：mosaic viewer／annotate／backtest_dashboard singleton→factory（`8e92d957`／`69257c01`，Monitor 卡等到補償行落地）
- **重啟流程**：先用 `TaskStop` 停掉舊的背景任務和 Monitor，再重新啟動

## Monitor 監控模式

使用 Monitor tool 監控 stdout 的 `[ACTION]` 行：

```bash
tail -f <背景任務output路徑> | grep --line-buffered "\[ACTION\]\|\[FAIL\]\|\[WARN\]"
```

- `<背景任務output路徑>` 是 `run_in_background` 回傳的 output file path
- `--line-buffered` 確保每行立即 flush（不加則 pipe buffer 會延遲事件）
- 過濾目標：`[ACTION]`（操作事件）+ `[FAIL]`/`[WARN]`（異常信號）

## 協作哲學

觀察 → 讀取 → 等待 → 上下文感知 → 記錄

1. **觀察**：透過 `[ACTION]` 日誌理解使用者正在做什麼
2. **讀取**：收到 `[LOG]` 路徑後主動讀取分析檔案，不等使用者提示
3. **等待**：使用者提問時再回應，不主動打擾
4. **上下文感知**：回答前先讀 action log + 相關分析檔案
5. **記錄**：討論結束後寫入 `llm-discussions/`

## 領域感知

當 UI 涉及股票分析（Trajectory Viewer、K 線圖等），載入 `trading-analysis` skill（三層框架：經典 TA → 量化 → 第二層思考整合），分析必含「各理論共識/歧異對照」表格。

未經 Layer 1（經典 TA）直接跳到 Layer 2 數值判斷（如「RSI=75 所以超買」）是錯誤的分析流程。

## 討論記錄

討論結束後（使用者明確結束或 session 結束前），將結論寫入：

```
llm-discussions/{category}/YYYY-MM-DD_{script-name}_{topic-slug}.md
```

- `{category}`: 至少一層分類目錄（如 instrument、project）
- `{script-name}`: 執行的腳本名稱
- `{topic-slug}`: 討論主題
- 同一天多次討論可用序號: `YYYY-MM-DD_01_topic.md`

## Action Table 慣例

每個 UI command 應提供專屬的操作對照表：

| 欄位 | 說明 |
|------|------|
| `[ACTION]` 名稱 | 操作識別碼 |
| 觸發時機 | 什麼操作觸發此事件 |
| LLM 應理解的上下文 | 使用者意圖推斷 |
| 伴隨輸出 | `[LOG]` 路徑或其他輸出，LLM 應主動讀取 |
