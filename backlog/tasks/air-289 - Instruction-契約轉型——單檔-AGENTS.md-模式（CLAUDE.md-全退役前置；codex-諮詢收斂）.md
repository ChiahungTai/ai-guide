---
id: AIR-289
title: Instruction 契約轉型——單檔 AGENTS.md 模式（CLAUDE.md 全退役前置；codex 諮詢收斂）
status: To Do
assignee: []
created_date: '2026-10-08 22:36'
labels:
  - instruction
dependencies: []
ordinal: 280000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC 2.1.277+ 原生支援 AGENTS.md（no CLAUDE.md 即讀；/config Project instructions 可調；諮詢全文 .agent-tmp/cl-md-consult-codex.md）。本卡＝生成者先行（退役前置）：①instruction-writing/SKILL.md 大改——廢雙檔規範、:38「Claude 不 native 讀 AGENTS.md」錯誤事實修正、:64 @ 規範精確化（新版 CC 能展開 AGENTS.md imports 但跨 harness 不應依賴 CC 專屬 transclusion）、CC discovery／載入表重寫②instruction-init/SKILL.md——root/模組只生成 AGENTS.md、停止生成 wrapper、保留 legacy CLAUDE.md 唯讀辨識（禁誤判缺 AGENTS）③instruction-clean/instruction-sync 中改（AGENTS.md 為正式同步對象）④rules/instruction-writing.md 雙檔定義源改⑤skills/_common/ 範本同步。

```mermaid
flowchart LR
  a["CLAUDE.md 全退役——user 裁決"] --> b["本卡：對應段落地"] --> c["驗收：rg 歸零／錨點修／smoke"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instruction-writing 雙檔規範廢除＋CC discovery 重寫
- [ ] #2 instruction-init 停止生成 wrapper＋legacy 唯讀辨識
- [ ] #3 clean/sync/rules/_common 同步
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈（codex＋5.3＋judge）
<!-- DOD:END -->
