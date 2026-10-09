---
id: AIR-298
title: holder/lease 語義改革——INBOX 章與消費章分離＋AIR-225 慣例修正（bridge sess_1f2a2cda 荒繆狀況）
status: In Progress
assignee: []
created_date: '2026-10-09 12:44'
updated_date: '2026-10-09 12:47'
labels:
  - dutymail
dependencies: []
ordinal: 289000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bridge repo sess_1f2a2cda 遇到：holder 章長持導致下個 session 無法 consume（荒繆狀況——排班值星退場後新形態下 holder 歸屬更模糊）。user 提出兩方向：①dutymail 面（bridge repo 份額）：章分級——INBOX 章（ext 長持、只服務 viewport 顯示）vs 消費章（AI session 短持、prepare/ack 用）分開；或恢復某種 idle-lease（AIR-288 拔掉的時鐘只對「AI 消費者持有」的章有意義）②AIR-225 慣例面（ai-guide repo 份額）：修正慣例文字——ext 長持只及 escalation／人類 viewport 地址；marshal 地址章歸「當時的值星 session」，session 死後進 death-evidence 接管（不用等 24h——AI session 的心跳可判）。兩 repo 各有份額，相互寄信討論。

```mermaid
flowchart LR
  a["holder 章長持——下班 session 綁死收信"] --> b["ai-guide：慣例修正 ext 語義＋death-evidence 接管"]
  a --> c["bridge：INBOX 章 vs 消費章分離提案"]
  b --> d["雙 repo 寄信討論→各自落地"]
  c --> d
```
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
①ai-guide 慣例修正（本卡主體）②寄信 bridge＋SC 提案章分級③互相討論後各自落地
<!-- SECTION:PLAN:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ai-guide 慣例修正落地（ext 長持語義＋death-evidence 接管）
- [ ] #2 bridge 側章分級提案回執（相互討論閉環）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈
<!-- DOD:END -->
