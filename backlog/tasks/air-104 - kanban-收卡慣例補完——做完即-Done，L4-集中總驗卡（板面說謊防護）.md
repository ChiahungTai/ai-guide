---
id: AIR-104
title: kanban 收卡慣例補完——做完即 Done，L4 集中總驗卡（板面說謊防護）
status: Done
assignee: []
created_date: '2026-09-16 01:32'
updated_date: '2026-09-16 01:32'
labels: []
dependencies: []
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
板面曾出現「實作＋judge 已過但卡停 To Do」的說謊狀態（southchariot SC-19/22/26 實例），險些把完成的卡當新工重派。本次把 user 拍板的方案 2 寫進 kanban-board skill：做完即收 Done、L4 驗證集中總驗卡、待驗不是停 To Do 的理由。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 kanban-board SKILL.md 結案段含收 Done 條款與板面說謊警示
- [ ] #2 drift 掃描五個引用檔（execution-plan/implement/post-build/outward-action-consent/metadata-sync）無衝突語義
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
方案 2 條款落盤 skills/kanban-board/SKILL.md 結案兩步段（收 Done 條件＋板面說謊禁止＋SC 實例）；drift 掃描五檔零衝突；skills 為 symlink 部署＝編輯即生效。
<!-- SECTION:FINAL_SUMMARY:END -->
