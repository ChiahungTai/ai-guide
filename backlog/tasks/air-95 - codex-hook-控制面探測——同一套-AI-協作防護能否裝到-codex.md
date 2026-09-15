---
id: AIR-95
title: codex hook 控制面探測——同一套 AI 協作防護能否裝到 codex
status: To Do
assignee: []
created_date: '2026-09-15 06:12'
updated_date: '2026-09-15 06:13'
labels: []
dependencies: []
ordinal: 81000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
MOS-105 討論中發現 codex 官方文檔有 lifecycle hooks 機制（PreToolUse 等事件，文檔鏡像層證據、未 runtime 驗證）。這卡探測 codex hooks 在現行環境是否可用、契約形狀與 ZCode/muse 是否同構，評估把 MOS-105 的 bash-write-guard 防護移植過去的成本，供 user 決定要不要開移植卡。目前待開工（等 MOS-105 弧收斂後排序）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 codex hooks runtime 可用性判定（available／flagged／unavailable）附機械證據；stdin 契約形狀記錄並與 muse/ZCode 對照；移植成本評估結論（低中高＋理由）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c8bb0d3〕
〔已決策勿重辯：① MOS-105 範圍凍結只做 muse（H1/P2/P3/N2），codex 不入本弧——本卡為後續獨立弧（user 2026-09-15 拍板建卡）② codex lifecycle hooks 現有證據＝官方文檔鏡像層（ref-docs/harness/codex/config-file/config-reference.md:420-501：features.hooks／hooks.json，事件含 PreToolUse/PostToolUse/Stop/PermissionRequest，CC 風格 matcher＋command handler），runtime 可用性未驗證 ③ 探測方法學先例＝MOS-105 POC（fixture plugin／validate／hook test／stdin-dump；材料 .agent-tmp/mos105-advisory/）〕
範圍：只探測＋評估報告；移植實作另卡，不在本卡。
<!-- SECTION:PLAN:END -->
