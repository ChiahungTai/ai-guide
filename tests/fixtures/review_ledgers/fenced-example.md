# .review/air-000f.md — 內嵌格式說明帳本（AIR-121 R2 fixture，synthetic）

- reviewed revision：fixture branch HEAD `0f0f0f0`＋uncommitted none
- scope：tests（fenced 格式說明表禁計數 fixture）
- review_profile：ordinary
- writer：fixture

## 格式說明（範本——非 findings，禁計數）

```
| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| X-99 | Important | 範例:1 | 格式說明列（fenced——禁計數） | — | `true` | open | — |
```

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Important | a.py:1 | fixture 資料（已驗收） | 修法 | `true` | verified | ✅ |
| F-02 | Suggestion | a.py:2 | fixture 資料（不採納） | — | `true` | closed | ❌ |
