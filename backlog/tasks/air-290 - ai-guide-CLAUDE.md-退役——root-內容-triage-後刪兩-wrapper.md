---
id: AIR-290
title: ai-guide CLAUDE.md 退役——root 內容 triage 後刪兩 wrapper
status: To Do
assignee: []
created_date: '2026-10-08 22:36'
labels:
  - instruction
dependencies: []
ordinal: 281000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
前置：AIR-289（生成者先改）。①root CLAUDE.md 內容逐段 triage：已由 instruction-writing/memory-audit 定義的原則刪除重複投影；仍有效的 Claude 專屬知識歸入適當 skill；已退役的 CC 註冊路徑（AIR-215 ~/.claude/agents、~/.claude/rules）刪除過時敘述；AGENTS.md 保持 harness-neutral 不收 Claude 專屬內容②skills/CLAUDE.md 純 wrapper 直接刪③AGENTS.md 導航修正（原 wrapper 承載的入口）。驗收：rg -l . --hidden --glob CLAUDE.md --glob !**/.git/** 為空；rg CLAUDE.md skills/ rules/ AGENTS.md 分類殘留（歷史記錄可留；有效雙檔要求／失效錨點／重生 wrapper 指令不得留）。

```mermaid
flowchart LR
  a["CLAUDE.md 全退役——user 裁決"] --> b["本卡：對應段落地"] --> c["驗收：rg 歸零／錨點修／smoke"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 rg CLAUDE.md 全 repo 為空（除 .git）
- [ ] #2 root 有效內容遷移無遺失（triage 對照表）
- [ ] #3 AGENTS 導航完整
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 CC consumer smoke（新 session root/nested 載入實證——獨立於 pytest）
<!-- DOD:END -->
