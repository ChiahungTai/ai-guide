---
id: AIR-333
title: >-
  review_ledger 多表 lint 嚴格度設計裁決——columns 逐表全 canonical vs parse ID-join
  容忍面（＋聚合去重）
status: Done
assignee: []
created_date: '2026-10-14 04:33'
updated_date: '2026-10-14 12:14'
labels: []
dependencies: []
ordinal: 318000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-332 收線前 bi-panel（muse A1／codex A-02）指出的設計裁決題：多表帳本 lint 逐表要求全 canonical 欄位，但 parse_ledger 的 ID-join last-wins 明示容忍後表 partial（歷史 sanctioned 形態 Apply 記錄表＝ID｜狀態｜apply 落點）——第一表 canonical＋partial 後表的帳本，舊 lint PASS、新 lint FAIL，通過集縮小與 parse 容忍面分歧。

**要做什麼**：marshal/user 裁決 canonical lint 嚴格度——①維持逐表全 canonical（文件聲明嚴格度差異＋補同 ID 跨表狀態覆寫案例）或②columns.missing 僅及 Finding 主表、後表只查值域/malformed（對齊 parse 容忍面）。附帶：跨表聚合 fid 去重（同 fid 兩表皆違規重複列——substring 消費無實害，低優先）。

**裁決來源**：muse job-mv7lj570 A1＋codex job-mv7lj58u A-02（2026-10-14 收線前 bi-panel）；AIR-332 卡 notes 有脈絡。

```mermaid
flowchart LR
  ledger["多表帳本"] --> lint["cmd_lint 現行：逐表全 canonical"]
  lint --> gap["partial Apply 後表誤 FAIL"]
  gap --> rule["裁決嚴格度：全 canonical 或 主表限定"]
  rule --> align["lint 與 parse 容忍面對齊"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 join-aware 分類落地：定義表/patch 表/新 fid 全檢/vacuous patch＋首現不變式（fixture 實跑 discovery OK）
- [x] #2 converged join 後終態＋join_keyed_tables 單一 last-wins 源（parse 行為 byte-equivalent 回歸全過）
- [x] #3 codex 九案矩陣＋muse 測試調整案落 test（patch-pass／新 fid partial FAIL／缺狀態決策欄 FAIL）
- [x] #4 bi-panel findings 修復：多 emoji 恰一（last-wins 兩向釘死）／patch 列完整性按 header 欄數／fid.blank 雙 stage 拒
- [x] #5 marshal 獨立 fixture 複核＋scoped 86／全量 3978 passed＋帳本 converged 未決=0
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 804b425b〕〔已決策勿重辯：①採③ join-aware 分類 lint——定義表全 canonical／patch 表豁免 columns.missing 但在場欄位照查／新 fid或缺條件整表全檢／vacuous patch／每 fid 首現必經全檢②converged 值域改 join 後終態＋lint/parse 共用 join helper③三清單去重、columns.missing 不靜默去重④文件同步 docstring＋workflow-review-pattern＋消費端掃描〕範圍：review_ledger.py＋tests＋workflow-review-pattern.md；驗收＝codex 九案＋muse 測試調整案＋fixture 實跑。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
裁決（judge＝主 session 座位模型，2026-10-14）：採③ join-aware 分類 lint——muse job-mv7uu9p3-qce8yc 與 codex job-mv7uu9yu-l5i8ya 獨立收斂同案（兩家皆發現工單未明列事實：converged 值域為逐列 pre-join 檢查 review_ledger.py:565，僅修 columns.missing 不足以對齊 parse；muse 實跑 fixture join-last-wins.md 取證）。要點：①第一張 keyed 表＝Finding 定義表（全 canonical 不變）；後表 fid 全∈seen 且含狀態/決策欄＝patch 表（豁免 columns.missing，在場欄位值域/malformed 照查）；含新 fid 或缺條件＝整表按 Finding Record 全檢（混合表整表計不逐列豁免）；零資料列後表＝vacuous patch；不變式＝每 fid 首次出現必經全 canonical 檢查。②converged 值域改 join 後終態檢查，lint/parse 共用 join helper（防 drift——不可兩套 last-wins 實作）。③附帶去重：bad_decision/bad_status/malformed 以 dict.fromkeys 保序去重；columns.missing 不靜默去重（會遮蔽第二壞表）。驗收基準＝codex 九案矩陣＋muse 測試調整案（d5214238 patch 語義測試翻 PASS、FAIL 案以新 fid partial 後表重建、補 patch-pass 與 patch 表缺狀態/決策欄兩案）。落地須同步消費端（single-source drift 掃描）：workflow-review-pattern.md、post-build/judge-review/commit SKILL、腳本 docstring。意見全文：.agent-tmp/air333/{muse,codex}-answer.md。實作另段派工。

post-build 收斂落卡（AIR-121）：review_ledger converged parse＝findings 3／✅ 3／verified 3／未決 0。bi-panel 外審：muse job-mv81k0bu-qf461b（1 finding）＋codex job-mv81lr2d-xp31m2（3 findings，cross-hit F-01）——定義表多 emoji 恰一恢復（last-wins 兩向釘死）、patch 列完整性按 header 欄數、fid.blank 獨立 violation 雙 stage 拒。三驗證式 marshal 獨立 fixture 實跑複核過（多emoji FAIL／缺尾欄 malformed／空白fid fid.blank／合法patch＋last-wins覆寫 OK）。scoped 86 passed／全量 3978 passed。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AIR-333 裁決③收線：review_ledger 多表 join-aware 分類 lint 落地——定義表全 canonical／patch 表豁免 columns.missing 但在場欄位照查／新 fid 整表全檢／vacuous patch；converged 值域改 join 後終態（join_keyed_tables 與 parse 單一 last-wins 源）；fid.blank 獨立 violation。bi-panel 4 findings（muse 1＋codex 3）全採納修復、marshal 獨立 fixture 複核、scoped 86／全量 3978 passed、未決=0。

```mermaid
flowchart LR
  D["裁決③ 落卡"] --> I["實作腿 TDD 80 tests"]
  I --> B["bi-panel 4 findings 全採納"]
  B --> F["修正腿 3 項 fail-closed＋86 tests"]
  F --> V["marshal fixture 獨立複核"]
  V --> L["41f66e98 未決=0"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
