---
harness-scope: neutral
---

# 修改後必須執行驗證

語法／`ast.parse`／讀碼≠可執行。每個新增／修改的可執行 Python／script／demo／POC／example 須 `uv run python <file>` 真跑：修改→執行→觀察結果／錯誤→修正重跑；逐檔執行，確認轉型／FK、循環 import 等執行期問題。

測試修改後 `uv run pytest <test>`；新增測試先 RED，再實作至綠，並確認測到聲稱行為。

POC 由所屬 EP 段落 build＋commit 承接後清除；正式 test／docstring／EP 結論任一完整固化行為即可刪。量測外界者不強迫轉 test。

僅純文檔／instruction（含不可執行範例）、純註解及 ruff 自動 import 排序可免實跑；配置／可執行碼不屬例外。
