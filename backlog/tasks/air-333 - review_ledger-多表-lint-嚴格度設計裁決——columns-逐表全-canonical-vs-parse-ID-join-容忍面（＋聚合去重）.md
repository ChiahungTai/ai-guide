---
id: AIR-333
title: >-
  review_ledger 多表 lint 嚴格度設計裁決——columns 逐表全 canonical vs parse ID-join
  容忍面（＋聚合去重）
status: To Do
assignee: []
updated_date: '2026-10-14 04:40'
created_date: '2026-10-14 04:33'
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
