---
id: AIR-108
title: 收卡防護兩件——precheck 反向檢查＋judge 結論強制回卡
status: Done
assignee: []
created_date: '2026-09-16 03:17'
updated_date: '2026-09-16 05:28'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 實作完成〕AC#1 反向檢查（To Do 卡本線實作 commit→需裁決擋；-i 補大小寫盲點；結案序列先翻 Done）＋AC#2 結論回卡條款（judge-review 單一源＋agent-review-cycle 腿級）——commit 於 air-108 branch，等 tri panel 終審。

〔落地回執〕classification=ordinary（既有腳本小改＋條文增補——Plan 分類）。review=tri 終審三腿 muse（P1 actor 刻界→dc86f20 修）＋GLM-5.3 full（P2 allowed-tools→f7f6464 修；P3 grep 邊界→修）＋codex（P1 Workflow 路徑漏接→workflow-review-pattern 補 adapter-neutral 契約；P0×2 卡檔衝突→預統一，merge-tree 六對全 0）＋5 測＋實機煙霧。session-freshness=applied。deployment-surfaces=healthy（skills symlink 活視圖——merge 即生效形態，無殘餘對帳面）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
precheck 反向檢查（做完未收卡→擋）＋結論回卡條款（judge-review／agent-review-cycle／workflow-review-pattern 三處 adapter-neutral）；5 測＋tri 修復閉環。
<!-- SECTION:FINAL_SUMMARY:END -->
