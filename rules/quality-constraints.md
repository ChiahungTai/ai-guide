---
harness-scope: neutral
---

# 品質約束

## 完整交付

方向明確即完成核心功能、測試、邊界、文檔；必要時同步上層 AGENTS.md 架構／API／職責。方案選擇、需求不明、風險裁決才請示。

## 數據完整性（Crash-Only）

損壞比缺失危險：無效輸入／溢出／轉型／解析失敗立即崩潰，禁吞錯續行或修補壞資料；驗非空、必要欄位、NaN、inf。適用量化／高頻／即時風控／批次；排除長會話、複雜 UI、UX 優先互動。邊界見 validation-strategy skill。

機械依賴欄位成為 authoritative state 前須 consumer-equivalent 機驗（fail-closed；寫入保障≥讀取契約）。LLM 可定語義，自由文字不能獨擔機械契約；機械讀者上線才收緊，人／LLM-only 記錄保留自由。

## 派生產物

manifest 須列 upstream 清單＋content hash 快照；上游變更未重驗即 stale，禁宣稱 current（projection freshness check）。

## Fail Loud 與消費端驗證

未確認成功、跳步驟／案例／驗證、migration 跳記錄、未驗邊界均明列，禁報完成／全通過；隔離綠燈≠功能完成。功能須有可執行例、API 實際呼叫、邊界實驗。

定位主要 consumer 跑完整流程；symbol 命中≠接線被驅動，測試範圍須機械反查。依 DEPTH-MIN→SAMPLE→FULL；失敗分析後回 MIN，禁直接 FULL／盲重跑；詳 validation-strategy skill。

## 多步驟 checkpoint

跨檔重構、多段或至少三步修改，逐重要步驟報完成／驗證／剩餘；無法確認前步正確，停下釐清，禁盲續。
