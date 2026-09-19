---
id: AIR-144
title: ai-guide 專案結構補安裝拓撲指針——skills symlink 母鏈與 rules bundle 裝到哪
status: In Progress
assignee: []
created_date: '2026-09-19 21:46'
updated_date: '2026-09-19 21:46'
labels: []
dependencies: []
references:
  - AGENTS.md
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
<!-- INTENT:BEGIN -->
白話：打開 ai-guide 的人（或 AI）看不出 skills 裝到哪、rules 怎麼部署——在專案結構補一行安裝拓撲指針，指到 governance/manifest.toml（symlink 母鏈）與 deploy bundle 機制。
tier: simple
<!-- INTENT:END -->
<!-- SA:CONTRACT:BEGIN -->
- [C1] ai-guide/AGENTS.md「專案結構」節 skills 條目處補一行安裝拓撲指針：skills 經 governance/manifest.toml〔surfaces.skills〕symlink 母鏈（~/.agents/skills＋~/.claude/skills → repo skills/）送達各 harness；rules 經 scripts/deploy_agents.py bundle（~/.zcode／~/.codex／~/.config/muse 三面）
- [C2] 純導航指針零行為語義——不改任何 decision／authority／gate／authorization／acceptance 條文；審查閘分類記錄＝ordinary（一條獨立 context 腿；分類理由：指針僅新增可發現性，不改變 agent 可觀察行為）
<!-- SA:CONTRACT:END -->
<!-- SA:BOUNDARY:BEGIN -->
- [B1] 不動 model-routing skill 陪審團表條文、不改 governance manifest 本體、不新增檔案、不動 AGENTS.md 其他節
- consumes: 無——standalone 小卡
<!-- SA:BOUNDARY:END -->
<!-- SA:EXPORT:BEGIN -->
- 無（AGENTS.md 為行為面，非卡面消費者）
<!-- SA:EXPORT:END -->
<!-- SA:PENDING:BEGIN -->
- 無
<!-- SA:PENDING:END -->

〔背景（detail，不上圖）〕源＝AIR-142/143 弧附帶發現（user 插問 plugin 安裝面角度；AGENTS.md 專案結構節未載安裝拓撲、plugin 字樣只掛 AIR-116 缺口）。user 0920 對提案原文拍板「OK 開好後直接做」——本卡以該拍板為 acceptance basis（payload 為提案內容的 marker 條文化），receipt 據此記 accepted。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AGENTS.md 專案結構節 skills 條目含安裝拓撲指針：rg "manifest.toml" AGENTS.md 於 skills 安裝語境命中，且 symlink 母鏈（~/.agents/skills＋~/.claude/skills）與 deploy bundle 機制皆在指針內
- [ ] #2 審查閘分類記錄＝ordinary 在卡 notes；fresh 獨立 context 腿回執在場
- [ ] #3 AGENTS.md 其他節零變動（git diff 僅 skills 條目一行）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【authoring receipt】accepted 1ee3f8d94217bdb3 2026-09-20（acceptance basis＝user 0920 對提案原文拍板「OK 開好後直接做」——payload 為提案內容的 marker 條文化）
<!-- SECTION:NOTES:END -->
