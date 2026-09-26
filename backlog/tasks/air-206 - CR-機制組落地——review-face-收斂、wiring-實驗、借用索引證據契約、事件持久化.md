---
id: AIR-206
title: CR-機制組落地——review-face-收斂、wiring-實驗、借用索引證據契約、事件持久化
status: To Do
assignee: []
created_date: '2026-09-26 00:16'
updated_date: '2026-09-26 00:28'
labels: []
dependencies: []
ordinal: 192000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CR 使用率調查的機制組尾款（近零成本組已由 AIR-205 落地，本卡收其餘）。五項逐個評估：①review 語義派工收斂到 review face 並泛化附掛通道——前置：先做術語對帳（新註記與既有四態命名撞車，歸 review-engine 擁有）；②codex 生成器接線對照實驗——定位外掛已裝但工作面吃不到的斷點；③worktree 借主 checkout 索引的證據契約——先定義借來的索引能支撐哪些結論（禁支撐負向結論），配一次真 worktree 實測；④CR 呼叫事件定期落持久儲存（現行日誌會輪轉，下輪調查將無錨）；⑤事實軸工作腿的提示必帶 repo 根路徑與命令列字串（調查發現的正確修法，非補工具清單）。

```mermaid
graph LR
A[CR 調查報告機制組] --> B[術語對帳前置]
A --> C[接線對照實驗]
A --> D[借用索引證據契約＋實測]
A --> E[事件持久 sink]
A --> F[事實軸 prompt 修正]
B --> G[逐項獨立小卡或併批]
C --> G
D --> G
E --> G
F --> G
```

證據指針：調查報告 .agent-tmp/cr-usage-investigation/report.md（code-reality repo）；共識裁決兩腿 job 帳本（ai-guide workspace bridge show 可查）；AIR-205 Final Summary 節。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
205 reviewer F6 掛帳：crsurface（dispatch preview 拼法）vs cr-surface（bridge receipt/ledger 面拼法）——bridge 側 receipt 欄落地時統一拼法或互相標注等價。
<!-- SECTION:NOTES:END -->
