# .review/air-224-tc1.md — TC-1 fixture（synthetic：命中 trigger 腿缺 cr receipt）

- reviewed revision：fixture branch HEAD `22400t1`＋uncommitted none
- scope：tests/fixtures/review_ledgers（TC-1——trigger 腿缺 receipt，lint 須定位該腿）
- review_profile：ordinary
- legs：L1 fixture-job-tc1 trigger；L2 fixture-job-tc1b n/a
- L2: cr: n/a（reason=無結構查證 trigger；trigger 事實 ref=fixture synthetic docs-only diff）
- writer：fixture

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | fixture 資料（TC-1） | 修法 | `true` | verified | ✅ |
