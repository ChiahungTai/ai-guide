---
id: AIR-89
title: >-
  背景 agent liveness 兩項 skill 修正——model-routing heartbeat 事實更新＋agent-workflow
  死亡盲區 doctrine（源：delegate-bridge handoff 09-13）
status: To Do
assignee: []
created_date: '2026-09-13 12:43'
labels: []
dependencies: []
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## 目標一句話
承接 delegate-bridge 跨 repo handoff（backlog/drafts/handoff-agent-liveness-2026-09-13.md，內容經 codex 復議定版 job-mtzs63qz 勿重辯）：①model-routing SKILL.md:227 過期 heartbeat 宣稱改為已交付事實＋正確 flag 名 ②agent-workflow 增補背景 subagent 死亡盲區防禦 doctrine。

## baseline
main @ 開卡 commit。源 repo 證據錨＝delegate-bridge fdc8c47（heartbeat 交付＝d1/2.0.3/39b6964）。

## 已決策（定版勿重辯）
- 防禦階梯：durable dispatch receipt（WAL）→ pre-restart drain → generation watermark reconciliation → exact-process hard-death（dual-signal）→ >20min 多信號 stall advisory → residue recovery → 才 re-dispatch
- watermark＝reconciliation rule 非 active detector；命中後先 residue 再重派；per-agent 分類禁全凍結聚合；process 活＋DB 安靜絕不自動殺
- doctrine 兩句硬話：silence ≠ death；old-generation unresolved ≠ safe-to-retry
- 事故根因：ZCode app 更新重啟殺 child process（09-13 三 flash agents 死亡 47 分鐘無人知）
- 兩項皆 doc fix；probes/WAL 工具等另案建卡（不屬本卡）

## 驗收（handoff 原文）
- rg -n 'stuck-alert|roadmap 需求' skills/ → 0 hit；新句含 --stuck-after 與「已交付」
- agent-workflow 新段落與既有條文無矛盾（liveness ticker 與背景派發預設段特別核）——改前載 instruction-writing skill＋single-source drift 掃
- deploy 流程＋測試 gate（baseline 404 tests）
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 model-routing :227 事實句落地（--stuck-after＋已交付＋舊詞零殘留）
- [ ] #2 agent-workflow doctrine 段落地且與既有條文零矛盾（drift 掃舉證）
- [ ] #3 deploy 全端綠＋404 tests
<!-- AC:END -->
