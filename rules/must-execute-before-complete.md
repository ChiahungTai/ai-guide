---
harness-scope: neutral
---

# 修改後必須執行驗證

## 核心原則

語法正確不代表邏輯正確；建立/修改每個可執行 Python/script/demo/POC/example 後，必須 uv run python <file> 實跑，不能只讀碼、ast.parse 或說理論可行就報完成——轉型/FK、循環 import 等錯誤需實跑揭露。

## 強制規則

修改→立即執行→觀察成功/失敗與錯誤→調整重跑；多個可執行檔都須跑。測試改後 uv run pytest <test>；新增測試先 RED 再實作，綠後確認確實測到聲稱行為。

POC 到所屬 EP 段落 build＋commit 承接後清除；驗證行為以正式 test、docstring 或 EP 結論任一完整固化即可刪，量測外部世界者不強迫轉 test。

### 例外（可跳過執行）

純文檔/instruction（rules/skills md、Claude 端 wrapper；內含不可執行範例仍是文檔）、純註解、ruff 自動 import 排序；配置與可執行碼不屬純文檔。
