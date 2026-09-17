# .review/air-000.md — canonical 範本帳本（AIR-121 測試 fixture，synthetic）

## Header identity

- reviewed revision：air-000 branch HEAD `0000000`＋uncommitted none
- scope：skills/post-build/SKILL.md（本檔為 canonical 格式範本 fixture，非真實審查）
- review_profile：ordinary
- writer：fixture

## Finding Record

| ID | 嚴重度 | 位置 | 問題 | 建議 | 驗證式 | 狀態 | 決策 |
|---|---|---|---|---|---|---|---|
| F-01 | Suggestion | skills/post-build/SKILL.md:1 | 範例 finding（fixture 資料，非真實審查） | 範例修法 | `rg -n "canonical" skills/post-build/SKILL.md` | resolved | ✅ |
| F-02 | Important | skills/post-build/SKILL.md:2 | 範例 finding 二（fixture 資料） | 範例修法二 | `rg -n "identity" skills/post-build/SKILL.md` | verified | ✅ |
| F-03 | Suggestion | skills/post-build/SKILL.md:3 | 範例 finding 三（fixture 資料） | 不採納（成本＞收益，fixture 示範 ❌ 值） | `rg -n "review_profile" skills/post-build/SKILL.md` | closed | ❌ |
