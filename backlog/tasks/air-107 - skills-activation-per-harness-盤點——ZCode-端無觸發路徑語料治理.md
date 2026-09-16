---
id: AIR-107
title: skills activation per-harness 盤點——ZCode 端無觸發路徑語料治理
status: Done
assignee: []
created_date: '2026-09-16 03:16'
updated_date: '2026-09-16 05:28'
labels: []
dependencies: []
references:
  - skills/instruction-testing/SKILL.md
ordinal: 92000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-99 A5 實證：ZCode available-skills 只注入 name＋path、desc 不進模型決策面——部分 skill 在 ZCode 端叫不動。這張卡盤點哪些 skill 語料在各 harness 沒有觸發路徑，逐個決定補 rule 錨還是接受明示 invoke，並把 per-harness 判讀基準寫進 instruction-testing。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 盤點表在場（skill×harness 觸發路徑矩陣，機械可驗）
- [ ] #2 每個無觸發路徑 skill 有處置（補錨／接受明示 invoke）並落地
- [ ] #3 instruction-testing 含 per-harness activation 判讀基準（AIR-87 舊 PASS 重解讀）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c8acedd〕
〔已決策勿重辯：①主觸發路徑＝rule 錨＋明示 invoke（AIR-99 judge 裁決，不更名）②AIR-87 舊四 PASS 重解讀＝名字字面命中非 desc 觸發③ZCode available-skills 注入僅 name＋path（activation-results.md 取證）〕
範圍：盤點矩陣（skill×harness 觸發路徑）→逐 skill 處置（補 rule 錨／接受明示 invoke）→instruction-testing 補 per-harness activation 判讀基準。盤點機械段可派 flash。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔0916 實作完成〕AC#1 矩陣（flash 掃描 82 支＋主 session 抽驗吻合＋三噪音錨修正——spec/consistency/implement 字面誤中降級）；AC#2 處置（無觸發路徑六支全數接受明示 invoke——事件驅動工具補錨違反寫入門檻；弱名字 21 支＝5 支 AGENTS.md 錨在場＋16 支 fail-driven 接受現狀）；AC#3 instruction-testing per-harness activation 判讀基準（AIR-87 舊 PASS 重解讀進正典）——commit 於 air-107 branch，等 tri panel 終審。

〔落地回執〕classification=ordinary（盤點產物；instruction-testing 判讀基準屬 acceptance 語義增補——經 tri 全腿審查）。review=flash 機械盤點（主 session 抽驗吻合）＋tri 三腿（codex P1 nt 兩支改補錨→root AGENTS.md 工具鏈行；P2 統計口徑拆兩軸→修；GLM P3 判準同步④→修）。session-freshness=applied。deployment-surfaces=N/A（矩陣＝版控產物；instruction-testing 經 skills symlink live-on-merge healthy）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
82 支 skill 觸發路徑矩陣＋逐群處置（nt 兩支補 root AGENTS.md 錨、四支明示 invoke、16 支 fail-driven）＋instruction-testing per-harness activation 判讀基準（AIR-87 舊 PASS 重解讀進正典）。
<!-- SECTION:FINAL_SUMMARY:END -->
