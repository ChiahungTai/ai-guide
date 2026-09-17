# 測試帳本——雙表 ID-join last-wins（AIR-121 fixture，synthetic）

- reviewed revision：test branch HEAD `abcdef0`＋uncommitted none
- scope：tests/fixtures/review_ledgers（本檔為 join 語義測試 fixture）
- review_profile：ordinary

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | 發現時態（fixture 資料） | 修法 | `true` | open | — |
| F-02 | Important | a.py:2 | 發現時態（fixture 資料） | 修法 | `true` | open | ✅ |

## Apply 記錄

| ID | 狀態 | apply 落點 |
|---|---|---|
| F-01 | resolved | fixture 欄（示範後表覆蓋前表） |
