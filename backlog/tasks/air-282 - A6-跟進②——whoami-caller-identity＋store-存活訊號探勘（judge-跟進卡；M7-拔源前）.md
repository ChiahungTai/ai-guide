---
id: AIR-282
title: A6 跟進②——whoami caller-identity＋store 存活訊號探勘（judge 跟進卡；M7 拔源前）
status: To Do
assignee: []
created_date: '2026-10-07 23:10'
labels:
  - dutymail
dependencies: []
ordinal: 273000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-277 judge 跟進卡（codex F1/F2 根治面，不阻擋 A6）：探勘兩事——①ZCode runtime 是否有 session API/env 注入面可接真呼叫者身份（有→whoami 換真身份源；無→將 workspace 對照語義固化為正式宣稱——現 docstring caveat 為過渡）②zcode store 是否有真存活訊號可升級 live 語義（無則維持「未封存≠存活」宣稱）。紅線：禁 mtime 啟發式（猜測違禁猜精神）。可與跟進①併弧或另弧。

```mermaid
flowchart LR
  a["AIR-277 caveat 過渡態"] --> b{"ZCode 有 session/identity API？"}
  b -->|有| c["whoami 接真身份源＋live 升級"]
  b -->|無| d["workspace 對照語義固化為正式宣稱"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 探勘結論落卡（有源→接線；無源→宣稱固化）
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 探勘證據附 file:line
- [ ] #2 老規矩審查鏈
<!-- DOD:END -->
