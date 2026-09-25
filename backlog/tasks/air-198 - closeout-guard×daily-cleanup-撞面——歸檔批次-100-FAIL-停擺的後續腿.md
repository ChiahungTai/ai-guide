---
id: AIR-198
title: closeout-guard×daily-cleanup-撞面——歸檔批次-100-FAIL-停擺的後續腿
status: To Do
assignee: []
created_date: '2026-09-25 00:26'
labels: []
dependencies: []
ordinal: 184000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
來源＝AIR-193 切片二雙腿 review 腿二 F2（confirmed，機械重現）：結案結構 predicate 上線後（0925），deploy/scripts/run-backlog-cleanup.sh 的每日歸檔批次（tasks→completed，R code、is_entry=False、status 仍 Done）照跑結構 predicate——全板 125 張 Done 卡 100 張 FAIL（AC 殘留 63／AC 缺段無 fallback 標題 34／FS marker 缺 16／DESCRIPTION 缺 1／malformed 4），cleanup 批次 commit 逐卡被 pre-commit 擋：腳本 loud fail 但無補齊腿，每晚重複失敗噪音＋清理實質停擺。

需求釐清：①存量 100 張是補格式（批量補段）還是觀察期豁免 ②cleanup 腳本要不要對 struct-fail 有機械處置（跳過＋計數入 log？觸發補段清單？）③選項互斥或組合。裁定面＝載體三判準（cleanup 是 hook 消費端，guard 是正典判定——禁二刻，cleanup 端只消費 exit code）。

```mermaid
flowchart LR
  A[193 guard 地板抬高] --> B[存量 Done 卡 100/125 不合五段]
  B --> C[daily cleanup 歸檔 commit]
  C --> D[pre-commit 擋<br/>每晚失敗噪音]
  D --> E{後續腿裁決}
  E --> F[批量補段 runbook]
  E --> G[cleanup 對 struct-fail 處置<br/>跳過計數或觸發補段]
  E --> H[FS/AC 缺失觀察期降級]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 裁定三選一（或組合）記卡 notes（補段 runbook／cleanup 處置／觀察期降級）
- [ ] #2 實作落地＋cleanup 批次連續三晚綠燈（或顯式豁免清單機制）
- [ ] #3 存量 100 張清零或歸檔面隔離（判準記 notes）
<!-- AC:END -->
