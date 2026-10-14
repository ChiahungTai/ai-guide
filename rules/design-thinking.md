---
harness-scope: neutral
---

# 設計思考紀律

## 決策與後果

先釐清使用者行為／成功條件／約束，分清事實／假設；比較含「不做／刪除現有」，追蹤變更→直接行為／責任→間接消費者／invariant。

改判未知：低成本、隔離可逆、無 outward 者先 POC 再交付（deep-thinking 判準、must-execute-before-complete 清理）；需授權／缺證者列未知、查證依賴並請示。間接影響不明只標已查範圍，禁捏造；跨 context／共用契約／state／外部副作用／改判未知須深入，局部可簡報；停止條件見 deep-thinking skill。

專案／套件行為宣稱須查源附位置；可信材料可引用；未驗證的改判關鍵不得作行動依據。

## 可逆性與架構

單向門查失敗／回復條件，雙向門查間接影響；code 可回滾≠資料／外部動作可逆。語義用 LLM，機械確定性工作用程式。

Clean Architecture＋DDD 三 lens（見 arch-thinking）：不強制模板／過度分層、不憑目錄或 `_private` 判邊界；涉及依賴、重用、共用契約、state、修復／刪除／重構時載其觸發表。適用架構/選型/性能/重構/AI 建議/資訊架構；股票分析另載 trading-analysis skill。
