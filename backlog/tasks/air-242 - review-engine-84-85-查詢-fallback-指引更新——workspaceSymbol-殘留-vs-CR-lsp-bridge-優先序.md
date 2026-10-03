---
id: AIR-242
title: 'review-engine:84-85 查詢 fallback 指引更新——workspaceSymbol 殘留 vs CR/lsp-bridge 優先序'
status: In Progress
assignee: []
created_date: '2026-10-02 22:48'
updated_date: '2026-10-03 03:07'
labels: []
dependencies: []
ordinal: 233000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
skills/review-engine/SKILL.md:84-85 觀察（AIR-227 弧標記另卡）：「換 pattern／換位置→workspaceSymbol」兩行查詢 fallback 指引早於 AIR-227 lsp-bridge 接線與 CR 主面——指引詞需更新（CR refs/callers 優先、lsp-bridge hover/check_file 次之、workspaceSymbol 標 CC-native 邊界），政策條文走審查閘。詳見卡面。

舊 workspaceSymbol fallback 指引（84-85 兩行）早於 AIR-227 接線，需更新查詢優先序。

```mermaid
flowchart LR
    O['review 查詢 fallback<br/>84-85 兩行舊指引'] --> P['AIR-227 後新序<br/>CR refs callers 優先<br/>lsp-bridge hover 次之']
    P --> Q['workspaceSymbol 標 CC-native 邊界<br/>跨 harness 不在場']
```
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
user 確認照建議新序（1003 晨）：84-85 兩行改寫為 CR refs/callers 優先→lsp-bridge hover/check_file 次之→workspaceSymbol 標 CC-native 邊界；與 symbol-query-routing 單一源對齊指針。單 impl unit＋fresh 腿輕閘（指引詞更新非語義變更）。
<!-- SECTION:PLAN:END -->

## Acceptance Criteria

- [ ] #1 兩行改寫新序在場（CC-native 邊界標註） `rg -c "CC-native" skills/review-engine/SKILL.md` → ≥1
- [ ] #2 symbol-query-routing 單一源指針 `rg -c "symbol-query-routing" skills/review-engine/SKILL.md` → ≥1
- [ ] #3 drift 掃描執行並記 journal（workspaceSymbol 殘留面盤點） `rg -n "workspaceSymbol" skills/review-engine/SKILL.md` → exit 0
- [ ] #4 single-source 面不破 `uv run pytest tests/test_sync_agents.py` → exit 0
