---
name: evidence-over-claims
description: user 對「完成」宣稱要求眼見為憑——「我要看你真的實作長怎樣，誰知道你是不是亂講」；回答配實物（結構 ls/三檔並排對照/live
  命令/open 產物），且交付宣稱須講清與規格的差距
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 09-05（AIR-29 弧）對殼 refresh「完成」的回應：「我要看你真的實作長怎樣，誰知道你是不是亂講」。

**Why**：AI 敘述性完成報告（「殼 refresh 完成」「s6 已掛」）對 user 是不可驗證的宣稱——尤其同一弧內多個 writer（AI 基礎款殼→codex 覆寫→AI 增量）譜系複雜，口頭描述無法分辨誰做了什麼、做到什麼程度。AI 自認 s6 精簡版時也犯了「交付宣稱未講清規格差距」——說「完成」但沒說比 hook 2 規格薄三處。

**How to apply**：
- 報告「完成」時附**實物**：目錄結構 ls、源 vs 產物並排對照（如 roles/ 源 vs 兩 registry 生成檔三欄並排——機制一眼可驗）、live 跑命令＋exit code、`open` 產物（殼/圖）讓 user 自己看
- 「測試跑過了嗎」類質疑：只報 pass 總數會被再追問——配 `pytest --collect-only` **逐檔計數**（哪些測試檔、各幾條）＋逐時點時間線（哪輪編輯後跑的）。09-06 實證：第一次答「151 passed」仍被追問「我是說 tests/ XXX.py 有跑嗎」，對焦答案＝逐檔列舉＋第三次實跑
- 交付若低於規格（精簡版/降級/部分），宣稱中**明說差距**（「這是精簡版，缺 X/Y」），不籠統說「完成」
- user 的質疑是對宣稱不對人——直接給證據是正確回應，防禦或再解釋都會失信

與 [[feedback_relay-claims-verify-current-state]]（接收側驗證）互為鏡像：那是接手宣稱先驗狀態，這是輸出宣稱自帶證據。
