---
id: AIR-147
title: >-
  collection integration——bridge-dispatch／agent-workflow watcher 自動 arm
  規約＋doctrine 接線
status: To Do
assignee: []
created_date: '2026-09-20 08:12'
labels: []
dependencies:
  - AIR-146
ordinal: 134000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-146 watcher 落地後的 doctrine 整線（digest §3 D1-D5）：rules/bridge-dispatch.md Dispatch⇄collection 配對句改寫（waiter 主路徑、裸 wait 降 fallback）；skills/bridge-dispatch/SKILL.md 完整模式段＋frontmatter desc 觸發詞＋完整模式指針補 CollectionReceipt 落點；agent-workflow watcher 工具化指涉（:84 主 session 持有 watcher 可指名工具形態）；stalled-advisory 處置 doctrine；fan-in 消費者測試。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 bridge-dispatch rule＋skill 改寫落地（waiter 主路徑、裸 wait fallback 保留、124 語句行為主體更新為 watcher 內部）
- [ ] #2 skill desc 觸發詞涵蓋新形態（bridge_waiter／CollectionReceipt／stalled-advisory；desc 機驗 ≤1024 chars）
- [ ] #3 fan-in 消費者測試（多 job 情境）通過
- [ ] #4 stalled-advisory 處置句進 doctrine（喚醒不處置；stop 恆為主 session 判斷）
<!-- AC:END -->
