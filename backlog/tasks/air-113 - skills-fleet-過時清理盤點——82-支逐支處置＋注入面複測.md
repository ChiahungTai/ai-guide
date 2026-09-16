---
id: AIR-113
title: skills fleet 過時清理盤點——82 支逐支處置＋注入面複測
status: To Do
assignee: []
created_date: '2026-09-16 13:51'
labels: []
dependencies: []
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
0916 互動弧遺留：user 判 skill fleet『有點太肥、有些可能過時』。ZCode 單根化後注入面＝82 條目（~6K chars/session），真成本在維護面（82 個 instruction surface 各需 consistency review）。盤點地基已備：AIR-107 觸發路徑矩陣（ai-analysis/_tasks/09-16-air107-skills-activation-matrix/matrix.md）。隨卡處理 instruction-testing:56 歸因張力（本弧 bi panel deferred 項——本卡 fleet 增減正是使其條件化的變數，縮進 metadataBudget 預算內即 desc 注入啟動）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 82 支逐支處置表附 usage 證據（AIR-107 矩陣錨位：31 rule 錨／24 語義自明／21 弱名〔5 錨＋16 fail-driven〕／6 零路徑）
- [ ] #2 專案特定六支外移評估落卡（nt-query／nt-v1-query／upgrade-nt／upgrade-sj／swing-analysis／kbar-form-analysis——locality vs 跨 repo 可用性取捨）
- [ ] #3 處置後注入面複測（headless rollout 條目數＋預算溢出態判定）
- [ ] #4 instruction-testing:56 歸因張力修正（絕對句→條件化＋PASS 歸因紀律補 desc channel）——acceptance 語義面，隨卡 tri 腿審查，本卡審查級別含 tri
- [ ] #5 .agent-tmp 遺留清掃（probe 證據 air-107-budget-probe／air-107-docsync＋journal 收斂）
<!-- AC:END -->
