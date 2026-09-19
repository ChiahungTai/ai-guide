---
id: AIR-144
title: ai-guide 專案結構補安裝拓撲指針——skills symlink 母鏈與 rules bundle 裝到哪
status: Done
assignee: []
created_date: '2026-09-19 21:46'
updated_date: '2026-09-19 21:59'
labels: []
dependencies: []
references:
  - AGENTS.md
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
打開 ai-guide 的人（或 AI）看不出 skills 裝到哪、rules 怎麼部署——在專案結構補一行安裝拓撲指針：skills 經 governance/manifest.toml〔surfaces.skills〕symlink 母鏈（~/.agents/skills＋~/.claude/skills → repo skills/）送達各 harness；rules 經 scripts/deploy_agents.py bundle（~/.zcode／~/.codex／~/.config/muse 三面）。純導航指針零行為語義（審查閘分類＝ordinary：僅新增可發現性，不改變 agent 可觀察行為）；不動 model-routing skill 條文、不改 governance manifest 本體、不新增檔案。

源＝AIR-142/143 弧附帶發現（user 插問 plugin 安裝面角度）；user 0920 對提案原文拍板「OK 開好後直接做」。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 AGENTS.md 專案結構節 skills 條目含安裝拓撲指針：rg "manifest.toml" AGENTS.md 於 skills 安裝語境命中，且 symlink 母鏈（~/.agents/skills＋~/.claude/skills）與 deploy bundle 機制皆在指針內
- [x] #2 審查閘分類記錄＝ordinary 在卡 notes；fresh 獨立 context 腿回執在場
- [x] #3 AGENTS.md 其他節零變動（git diff 僅 skills 條目一行）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【authoring receipt】accepted 1ee3f8d94217bdb3 2026-09-20（acceptance basis＝user 0920 對提案原文拍板「OK 開好後直接做」——payload 為提案內容的 marker 條文化）

【review receipt】classification=ordinary（純導航指針零行為語義——分類理由在 payload C2）／review=fresh 獨立 context 腿 PASS（零 Critical/Important；F1 採納已修＝rules 子句補 CC 端 ~/.claude/rules auto-load；F2 維持現狀）／session-freshness=fresh／deployment-surfaces=healthy（AGENTS.md 為 workspace 面，隨 merge cbcd5b7f 生效）
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AGENTS.md 專案結構補安裝拓撲指針（symlink 母鏈＋deploy bundle＋CC rules 面＋plugin 邊界）；ordinary fresh 腿 PASS；merge cbcd5b7f
<!-- SECTION:FINAL_SUMMARY:END -->
