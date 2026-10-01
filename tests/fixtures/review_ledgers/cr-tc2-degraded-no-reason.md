# .review/air-224-tc2a.md — TC-2 fixture（synthetic：degraded receipt 無 reason）

- reviewed revision：fixture branch HEAD `22400t2`＋uncommitted none
- scope：tests/fixtures/review_ledgers（TC-2——degraded 無 reason＝FAIL）
- review_profile：ordinary
- legs：L1 fixture-job-tc2a trigger
- L1: cr(route=degraded, evidence=fixture-artifact.out)
- writer：fixture

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | fixture 資料（TC-2a） | 修法 | `true` | verified | ✅ |
