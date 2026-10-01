# .review/air-224-tc4b.md — legacy-exempt fixture（synthetic：凍結前舊檔形態＋有效豁免章＝PASS）

- reviewed revision：fixture branch HEAD `0001234`＋uncommitted none
- scope：tests/fixtures/review_ledgers（legacy-exempt 放行——凍結 cutoff 前帳本）
- review_profile：ordinary
- legacy-exempt（cutoff=b41b4ed1）——AIR-224 receipt 語義凍結前帳本，無 legs 名冊/cr receipt
- writer：fixture

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | fixture 資料（legacy-exempt 放行） | 修法 | `true` | verified | ✅ |
