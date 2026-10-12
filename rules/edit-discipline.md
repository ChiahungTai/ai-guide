---
harness-scope: neutral
---

# 編輯紀律

優先改現有檔；測試保護下可重構，品質／正確性／清晰度優先，內部預設不保向後相容。

- library 與 scripts 有入口層級：scripts 不反向侵入 library 內部；可複用邏輯上抽 library，禁 scripts 變第二個 library。
- SOLID：依賴向內、介面隔離、單一改變理由；公開 API 不暴露內部資料／型別。
- 新增 validation／logging／config 前須指出具體問題，禁投機。
- 矛盾寫法禁折衷：選較新或測試較完整者並說明，標另一者待清；即時回報。
- 外部整合／數據流程／部署環境／user 明示才確認相容性；其餘內部修改品質優先。
- 修 bug 只改必要行，重構另段；清自己留下的 dead import／variable，既存 dead code 僅標記不刪；刪除不留 tombstone，歷史查 git log，不動已歸檔歷史文檔。
