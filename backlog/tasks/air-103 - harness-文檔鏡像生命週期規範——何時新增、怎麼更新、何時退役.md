---
id: AIR-103
title: harness 文檔鏡像生命週期規範——何時新增、怎麼更新、何時退役
status: In Progress
assignee: []
created_date: '2026-09-16 00:41'
updated_date: '2026-09-16 03:48'
labels: []
dependencies: []
references:
  - ref-docs/harness/LIFECYCLE.md
ordinal: 88000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
這卡把 ref-docs/harness 官方文檔鏡像的新增／更新／退役判準寫成文檔：opencode 鏡像退役時（AIR-102）全靠當場判斷，沒有成文流程。產出 LIFECYCLE.md＋AGENTS.md 指針，Wave-1 收線後開工。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ref-docs/harness/LIFECYCLE.md 在場，涵蓋新增／更新／退役三態的判準與操作流程
- [ ] #2 AGENTS.md ref-docs 條目含 LIFECYCLE.md 指針
- [ ] #3 退役流程含 AIR-102 案例的四處連動清單與殘留掃描驗證步驟（可機械執行）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c741a14（Wave-1 收線後開工時重新對時 main tip）〕
〔已決策勿重辯：①載體＝ref-docs/harness/LIFECYCLE.md 獨立檔（user 09-16 拍板「可以」）②AGENTS.md ref-docs 條目補 LIFECYCLE.md 指針③時點＝Wave-1 收線後開工④退役流程以 AIR-102 決策 7 四處連動（鏡像目錄／manifest.json 條目／crawl.py source／AGENTS.md 引用面）為首例素材〕
範圍：新增判準（消費面存在＋值得離線鏡像的條件）、更新節奏（既有 crawl.py refresh 機制指針，不重寫）、退役判準（harness 退出個人工具棧／鏡像零消費者的 rg 實掃）與退役流程（四處連動清單＋README 同步＋殘留掃描驗證）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 實作完成〕LIFECYCLE.md 三態判準＋退役五處連動＋殘留掃描驗證；AGENTS.md ref-docs 指針——commit 於 air-103 branch，等 tri panel 終審。
<!-- SECTION:NOTES:END -->
