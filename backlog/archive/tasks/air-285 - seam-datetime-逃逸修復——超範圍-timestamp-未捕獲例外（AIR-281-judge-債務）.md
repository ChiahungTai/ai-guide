---
id: AIR-285
title: seam datetime 逃逸修復——超範圍 timestamp 未捕獲例外（AIR-281 judge 債務）
status: To Do
assignee: []
created_date: '2026-10-08 12:50'
labels:
  - dutymail
dependencies: []
ordinal: 276000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
session_discovery.py 的 _last_seen_iso（:320 datetime.fromtimestamp）無範圍防護——store 列含超範圍 last_seen_us 時拋 ValueError/OverflowError，逃出 main() 的 except DiscoveryError，exit 3 typed envelope 保證破洞（codex job-muyyjjzb F1 marshal 親驗成立；judge job-muzezky5 裁決本卡不改 seam——修復屬新契約決策另開卡）。本卡要決：列值損壞時 row-skip（跳過該列續掃）還是整源 source_malformed（typed 拒絕）——參照 quality-constraints crash-only（損壞比缺失危險）。修後 handoff SKILL.md「罕見未捕獲例外」註記可收回。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 契約決策落卡（row-skip vs source_malformed）＋RED→GREEN 修復
- [ ] #2 SKILL.md 罕見例外註記收回
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈（codex＋5.3＋judge）
<!-- DOD:END -->
