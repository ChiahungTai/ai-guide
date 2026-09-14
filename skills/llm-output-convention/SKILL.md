---
name: llm-output-convention
description: "AI Agent 雙通道輸出細則載體 — print tag 全表（[OK]/[WARN]/[FAIL]/[LOG]/[ACTION]/[progress]）、print 慣例細則（[LOG] 路徑只印一次、何時不該 print）、Logger 慣例（action_name prefix、level 選擇、print↔Logger 閉環）、stdlib logging 與框架 Logger 並存（lastResort 陷阱、遷移非機械替換）、執行自檢清單。always-on 核心（print 當索引 Logger 當資料庫、state transition 定義、Namespace module-path 原則）在 rules/llm-output-convention.md；寫 Python 輸出/log 程式碼、設計 print 格式、診斷 log 找不到輸出時載入。觸發詞：print tag、[OK]、[LOG]、[progress]、Logger prefix、action_name、log level、namespace、module-path、addHandler、lastResort。"
---

# LLM Output Convention — print/Logger 細則

> 本 skill 是 `rules/llm-output-convention.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（雙通道核心原則、state transition 定義、Namespace 原則、慣例摘要）；本檔承載 tag 全表、細則、stdlib 並存、遷移注意與自檢清單。

## print() 慣例

格式：status tag + 精簡摘要——`print(f"[OK] build_features: {n} features, {n_rows} rows")`；需要深挖時附帶 rg 搜尋指引（`[LOG] rg 'train_model' {log_path}`，可用精準 pattern 避噪：`rg 'fit_model.*(start|metric|warn|error)'`）。

| Tag | 含義 |
|-----|------|
| `[OK]` | 成功完成（函式正常返回） |
| `[WARN]` | 異常但可繼續（數值偏低、資料不足） |
| `[FAIL]` | 失敗（拋出異常或無法完成） |
| `[LOG]` | rg 搜尋指引 |
| `[ACTION]` | UI 操作事件（由 ui 元件層 log，app 層不重複——元件擁有互動，元件 log；只有 app 直接操作 UI 框架時才由 app log） |
| `[progress]` | 週期性心跳（長任務定期進度，非 state transition） |

- **不使用 `[INFO]`**（與 Logger level 混淆；`[progress]` 是心跳的明示例外、非 state transition）
- **`[LOG]` 路徑只印一次**：同一 session 內 log 路徑不變，每次都印是浪費 token（class variable 追蹤已印過）
- **何時不該 print**：中間步驟細節（Loading column X / Processing row i/N）→ Logger；重複 Logger 已有摘要；超過一行內容（DataFrame/dict/list）

## Logger 慣例

- **統一 Prefix**：message 以 `action_name: ` 開頭（`logger.info(f"build_features: start, spec={spec_name}, rows={n_rows}")`）——散漫寫法（「開始處理...」「✅ 完成」）rg 無法精準搜
- **Level**：`debug` 中間計算/參數值（重現計算過程）、`info` 狀態轉換 start/done/cache hit（還原流程）、`warning` 異常可續行、`error` 失敗定位
- **閉環規則**：print 的 rg tag 必須在 Logger 中存在（`[OK] build_features` ↔ `build_features:` prefix 的 info 行）；Logger 提供補充細節，不重複 print 摘要

## stdlib `logging` 與框架 Logger 並存

stdlib logger 無 handler 時走 `lastResort`（INFO/DEBUG 靜默丟棄），框架 log 檔找不到其輸出。

- **同進程只用一套 Logger 系統**：框架有內建 Logger → 全用框架 Logger，禁混 stdlib `logging.getLogger`
- 必須用 stdlib（框架無 Logger）→ 顯式 `addHandler`，不依賴 lastResort；依專案 init_logging 配置 file level ≥ DEBUG（供 rg 查），stdout 交 print 控制
- **遷移非純機械替換**：`%s` lazy formatting 在部分框架 Logger 不展開 → 改 f-string；`extra=` kwargs 可能拋 TypeError → 欄位併入 message

## 執行自檢清單

輸出前對照上方慣例段逐項自檢：print 限 state transition＋tag 正確、`[LOG]` 路徑只印一次、Logger `action_name: ` prefix＋module-path name、print↔Logger 閉環、同進程單一 Logger 系統。
