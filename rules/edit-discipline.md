---
harness-scope: neutral
---

# 編輯紀律

優先編輯現有檔案；測試保護下可大幅重構，品質、正確性、清晰度優先，預設不保留向後相容。

- 依賴遵循 library 與 scripts 入口層級，scripts 不反向侵入 library 內部；可複用邏輯上抽 library，勿讓 scripts 成第二個 library。
- 遵循 SOLID：依賴向內、介面隔離、單一改變理由；公開介面不暴露內部資料/型別。
- 每個新增 validation/logging/config 必能回答解決什麼具體問題，禁投機。
- 矛盾寫法不各取一半：選較新或測試完整者、說明理由、標另一者待清，發現即回報，禁默默混合。
- 影響外部整合、數據流程、部署環境或 user 明確要求時才確認向後相容，其他內部改動預設品質優先。
- 修 bug 只改必要行，架構重構另段完成；清自己造成的 dead import/variable，既存 dead code 只標不刪；刪除不留 tombstone，歷史交 git log，歸檔歷史文檔不動。
