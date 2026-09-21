---
harness-scope: neutral
---

# 品質約束

## 完整交付標準

方向明確就做到可用：核心功能、相關測試、邊界處理、文檔同步；完成後檢查變更所在與上層 AGENTS.md 的架構/API/職責描述，必要時同步（含 Claude wrapper）。需方案選擇、需求不明或風險裁決時請示。

## 數據完整性優先（Crash-Only Design）

損壞數據比缺失更危險。無效輸入、溢出、轉型/解析失敗立即崩潰，禁吞錯續行或修補損壞輸入；驗非空、必要欄位、NaN、inf。適用量化交易、高頻、實時風控、批次；不適用長會話、複雜 UI 狀態、UX 優先互動。設計方法（狀態外部化/等冪/持久化路徑）與誤用邊界見 validation-strategy skill「crash-only 邊界」。

寫入保障必須至少匹配下游讀取契約：機械依賴的資料欄位，成為 authoritative state 前必須通過 consumer-equivalent 的機械驗證（fail-closed）；LLM 可決定語義值，自由文字格式不得單獨承擔機械契約。寫入權是時間函數：機械讀者上線才收緊對應面；人／LLM-only 記錄面不因此 schema 化（自由度明文保護）。

## 派生產物投影紀律（upstream 追溯）

派生產物（投影殼、生成檔）須可追溯 upstream：manifest 宣告 upstream 清單＋content hash 快照（工具形態＝projection freshness check）。upstream 變更未重驗＝stale，**不得以 current 姿態呈現**。

## 主動揭露錯誤（Fail Loud）

未確認成功、跳過步驟/案例/驗證、migration 跳記錄、未驗邊界都須明列限制，禁報完成/全通過；隔離單元綠燈不代表功能完成。功能須有可執行例，API 實際呼叫，邊界實驗。

### 消費端驗證模式

先定位主要消費者並跑完整流程；測試集範圍不可憑目錄直覺，須機械反查；symbol 命中≠接線被驅動。細則見 **validation-strategy skill**（證據分層見 [acceptance-evidence](acceptance-evidence.md)）。

## 漸進式驗證（DEPTH-MIN→SAMPLE→FULL）

一律 DEPTH-MIN→SAMPLE→FULL；失敗先分析/修正並回 MIN，禁改後直跑 FULL 或失敗盲重跑。風險分級決定最終深度；3–5 案、已知陷阱等細則見 validation-strategy skill。

## 多步驟任務檢查點

跨檔重構、多段或三步以上修改，每個重要步驟回報完成/驗證/剩餘；無法精確描述或不確定前步正確時停下釐清，禁盲續。
