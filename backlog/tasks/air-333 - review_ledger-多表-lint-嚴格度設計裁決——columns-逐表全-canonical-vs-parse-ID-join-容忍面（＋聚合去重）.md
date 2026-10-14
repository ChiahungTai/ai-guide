---
id: AIR-333
title: >-
  review_ledger 多表 lint 嚴格度設計裁決——columns 逐表全 canonical vs parse ID-join
  容忍面（＋聚合去重）
status: To Do
assignee: []
created_date: '2026-10-14 04:33'
updated_date: '2026-10-14 08:55'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
裁決（judge＝主 session 座位模型，2026-10-14）：採③ join-aware 分類 lint——muse job-mv7uu9p3-qce8yc 與 codex job-mv7uu9yu-l5i8ya 獨立收斂同案（兩家皆發現工單未明列事實：converged 值域為逐列 pre-join 檢查 review_ledger.py:565，僅修 columns.missing 不足以對齊 parse；muse 實跑 fixture join-last-wins.md 取證）。要點：①第一張 keyed 表＝Finding 定義表（全 canonical 不變）；後表 fid 全∈seen 且含狀態/決策欄＝patch 表（豁免 columns.missing，在場欄位值域/malformed 照查）；含新 fid 或缺條件＝整表按 Finding Record 全檢（混合表整表計不逐列豁免）；零資料列後表＝vacuous patch；不變式＝每 fid 首次出現必經全 canonical 檢查。②converged 值域改 join 後終態檢查，lint/parse 共用 join helper（防 drift——不可兩套 last-wins 實作）。③附帶去重：bad_decision/bad_status/malformed 以 dict.fromkeys 保序去重；columns.missing 不靜默去重（會遮蔽第二壞表）。驗收基準＝codex 九案矩陣＋muse 測試調整案（d5214238 patch 語義測試翻 PASS、FAIL 案以新 fid partial 後表重建、補 patch-pass 與 patch 表缺狀態/決策欄兩案）。落地須同步消費端（single-source drift 掃描）：workflow-review-pattern.md、post-build/judge-review/commit SKILL、腳本 docstring。意見全文：.agent-tmp/air333/{muse,codex}-answer.md。實作另段派工。
<!-- SECTION:NOTES:END -->
