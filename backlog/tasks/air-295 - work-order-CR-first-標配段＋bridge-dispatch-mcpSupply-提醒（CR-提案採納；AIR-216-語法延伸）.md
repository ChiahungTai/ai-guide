---
id: AIR-295
title: work-order CR-first 標配段＋bridge-dispatch mcpSupply 提醒（CR 提案採納；AIR-216 語法延伸）
status: Done
assignee: []
created_date: '2026-10-09 01:52'
updated_date: '2026-10-09 02:46'
labels:
  - instruction
dependencies: []
ordinal: 286000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CR repo 提案採納（cr-workorder-cr-first-proposal-001；實證＝GLM plan tier 腿 3144 Read＋0 CR 查詢——brief 給了 verified anchors 但缺工具分工，腿在無 CR face 下逐檔 Read 重建結構事實＝AIR-216 禁止形態）：①skills/_common/work-order.md——bridge 委派 glm 腿模板增配「CR-first 工具分工」標配段：結構事實（refs/callers/closure/impact radius）恆走 code-reality（MCP supply 或唯讀 CLI），Read/Grep 僅在結構範圍縮小後做語義判讀（分工語義單一源＝cr-query skill）②skills/bridge-dispatch/SKILL.md——glm isolated 腿 workspace CR 面在場時（.code-reality/graph.db／.code-reality.toml 任一）必帶 mcpSupply=[code-reality] 提醒一行（bridge db-101 預設化落地則降為記載面（提案信 db-71 為過期號——bridge grok 卡佔用順延））。

```mermaid
flowchart LR
  a["GLM 腿 3144 Read＋0 CR——缺工具分工"] --> b["work-order 標配 CR-first 段"] --> c["bridge-dispatch 補 mcpSupply 提醒"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 work-order.md CR-first 標配段落地
- [x] #2 bridge-dispatch mcpSupply 提醒一行
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 老規矩審查鏈（codex＋5.3＋judge）
<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
```mermaid
flowchart LR
  a["GLM 腿 3144 Read＋0 CR"] --> b["work-order CR-first 標配段"] --> c["bi 合議：三形態＋非結構可選收窄"] --> d["merge 9d00be3b Done"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
