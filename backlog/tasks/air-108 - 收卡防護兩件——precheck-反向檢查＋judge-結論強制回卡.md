---
id: AIR-108
title: 收卡防護兩件——precheck 反向檢查＋judge 結論強制回卡
status: In Progress
assignee: []
created_date: '2026-09-16 03:17'
updated_date: '2026-09-16 04:00'
labels: []
dependencies: []
references:
  - skills/kanban-board/scripts/backlog_precheck.sh
  - skills/judge-review/SKILL.md
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
UI-SC audit 的兩條流程建議：backlog_precheck 加反向檢查（本線已有實作 commit、卡面卻未翻——抓「做完未收卡」的不一致）；judge／review 結論強制 --append-notes 回卡（findings 不落卡＝下個 session 要考古）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 backlog_precheck.sh 含反向檢查（線上有實作 commit、卡未 Done→擋）
- [ ] #2 review／judge 條文含結論強制回卡條款（--append-notes）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c8acedd〕
〔已決策勿重辯：①反向檢查＝backlog_precheck.sh 增「本線已有實作 commit、卡未 Done→擋」（UI-SC audit 建議）②回卡條款＝review/judge 結論強制 --append-notes 落卡（findings 不落卡＝考古成本）③源＝.agent-tmp/air-101/flash-sc-audit.md 建議 2/3〕
範圍：backlog_precheck.sh＋review-engine／agent-review-cycle 條文。風險分類：ordinary（既有腳本小改＋條文增補）。
<!-- SECTION:PLAN:END -->
