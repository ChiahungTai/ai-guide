# .review/air-224-tc4c.md — legacy-exempt 無效章 fixture（synthetic：缺 cutoff 引用＝FAIL）

- reviewed revision：fixture branch HEAD `0005678`＋uncommitted none
- scope：tests/fixtures/review_ledgers（exempt 章缺 cutoff 引用＝機械錨不符）
- review_profile：ordinary
- legacy-exempt——無 cutoff 引用的章不合格（禁自由豁免）
- writer：fixture

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | fixture 資料（無效豁免章） | 修法 | `true` | verified | ✅ |
