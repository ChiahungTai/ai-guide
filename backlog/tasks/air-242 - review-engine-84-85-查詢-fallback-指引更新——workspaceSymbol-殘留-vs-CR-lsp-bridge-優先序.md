---
id: AIR-242
title: 'review-engine:84-85 查詢 fallback 指引更新——workspaceSymbol 殘留 vs CR/lsp-bridge 優先序'
status: Done
assignee: []
created_date: '2026-10-02 22:48'
updated_date: '2026-10-03 03:32'
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

- [x] #1 兩行改寫新序在場（CC-native 邊界標註） `rg -c "CC-native" skills/review-engine/SKILL.md` → ≥1
- [x] #2 symbol-query-routing 單一源指針 `rg -c "symbol-query-routing" skills/review-engine/SKILL.md` → ≥1
- [x] #3 drift 掃描執行並記 journal（workspaceSymbol 殘留面盤點） `rg -n "workspaceSymbol" skills/review-engine/SKILL.md` → exit 0
- [x] #4 single-source 面不破 `uv run pytest tests/test_sync_agents.py` → exit 0

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
**四數量測（settle 結算）**：first_handback_complete＝TRUE（impl 首收 join 4/4）；repair_rounds＝0（fresh 腿 GO 零必修——三條綠建議不擋合併）；marshal_direct_impl_violation＝0；settle_wait＝t_dispatch 1790982000 前後 → t_landed 1790991000 前後約 150min（多弧並行佔資源；本弧自身工作 15 分鐘級）。

**結案複核附記（fresh 腿三綠建議，皆不擋）**：一、journal drift 計數 9 檔實為 8 檔 17 處（題頭含改寫前 L85）——結論零同步需求不變；二、「CR workspace 級查詢」用語非 face 詞彙——未來觸碰此行改 face 名（refs 全域範圍查詢）；三、歸級口径：本變更＝對齊既有單一源的 drift 修復加 user 逐項裁決新序已記 PLAN，緩解 boundary 面分腿要求（fresh 腿已執行）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
**as-built 終態**（main 5d1375e2）：review-engine 84-85 兩行查詢 fallback 改寫新序——CR refs/callers（結構查證主面）→ lsp-bridge hover/check_file（簽名/即時）→ workspaceSymbol（CC-native face 邊界標註）＋symbol-query-routing 單一源指針。與 symbol-query-routing doctrine 三點全同向（CR-first／lsp-bridge 限 hover-check_file／CC-native 邊界）；全域 workspaceSymbol 殘留盤點 8 檔 17 處判讀零同步需求（execution-plan/judge-review 已帶 carrier 限定同向）。

```mermaid
flowchart LR
    O['舊指引：換 pattern 換位置<br/>→workspaceSymbol'] --> N['新序：CR refs callers<br/>→lsp-bridge hover<br/>→workspaceSymbol CC-native 邊界']
    N --> D['全域殘留盤點<br/>8 檔 17 處零同步需求']
```
<!-- SECTION:FINAL_SUMMARY:END -->
__zcode_status=$?
if [ "$__zcode_status" -eq 0 ]; then pwd -P > '/var/folders/h8/q6jpct1x4d1g4xt_7g2r06080000gp/T/zcode-552b706e-96f5-485d-8400-a33681abbee9-cwd'; fi
exit "$__zcode_status"
