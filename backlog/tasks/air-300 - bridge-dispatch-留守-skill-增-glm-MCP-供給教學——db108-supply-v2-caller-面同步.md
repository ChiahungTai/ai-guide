---
id: AIR-300
title: bridge-dispatch 留守 skill 增 glm MCP 供給教學——db108 supply v2 caller 面同步（bridge 3.10.0 出貨交辦）
status: Done
assignee: []
created_date: '2026-10-10 19:45'
updated_date: '2026-10-10 20:05'
labels:
  - bridge
dependencies: []
ordinal: 291000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bridge sync 信（arc-close-status-sync-001-1791681000）交付的最後一條教學尾巴：ai-guide 派 glm Rust/TS 結構查詢腿時的 caller 供給教學——`--mcp-supply` 面在 db-108 v2／DB-101（bridge 3.10.0 出貨）後的 caller 契約。落點＝`skills/bridge-dispatch/SKILL.md` 留守面（consumer governance）。教學要點（源＝bridge docs/ep.md db-70/db-108 v2/DB-101 條＋.agent-tmp/db108-supply-v2/ 收斂文件）：①Rust/TS 腿顯式 `--mcp-supply code-reality-lsp-bridge`（graph server `code-reality` 於帶 CR face 的 workspace 預設自動供給、LSP server 恆需顯式）②freshness 三態（fresh 才配裝；stale/no-slot/unknown＝顯式 typed 拒／預設 loud skip；LSP index-free 不受此閘）③`edit_file`＝寫權威面④resume＝exact-supply lineage（換 supply＝新 session）⑤isolated-only（inherit/marshal 帶 supply＝拒）。

```mermaid
flowchart LR
  a["bridge 3.10.0 supply v2 出貨"] --> b["本卡：caller 供給教學入留守 skill"]
  b --> c["glm Rust/TS 腿帶 code-reality-lsp-bridge"]
  b --> d["freshness 三態＋寫權威揭露"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `skills/bridge-dispatch/SKILL.md` 增 caller 供給教學條（五要點——顯式 supply／預設供給與 opt-out／freshness 三態／edit_file 寫權威／resume lineage＋isolated-only），錨點對照 bridge docs/ep.md 原條
- [x] #2 單腿獨立 context 審查（ordinary profile）＋merge 後 live chain probe
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
ephemeral WT → skill 增條（Read→Edit）→單腿 glm 審查→ff merge→probe→ack 信 disposition。
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 單腿審查 approve＋merge
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【來源】arc-close-status-sync-001-1791681000（class sync——bridge 板面清空通知＋過時認知修正＋教學尾巴交辦「歸你方 AIR-294 或後續卡」；AIR-294 已 Done 故開本卡）。
【收口】單腿 glm（job-mv2b0voi）needs-attention——抓到同檔 drift：line 30 既有命令式「dispatch 必帶 mcpSupply」自帶落日條款（db-101 落地則降記載面）未執行，與新增段形成兩規範（failure 語義互異）。收斂 6a3022bc：line 30 依落日條款降為記載面＋failure-policy 差異指針＋as-of 補 3.10.0 delta 註。五點教學錨點經審查逐條對照 ep.md db-70/DB-101 屬實；live chain probe 過。給 bridge 的 upstream 備註（非本側）：MCP bridge_task tool description 仍標 v1 vocabulary，與 CLI db-108 v2 詞彙措辭未對齊。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bridge 3.10.0 supply v2 的 caller 供給教學落地我方 bridge-dispatch 留守 skill：glm Rust/TS 腿顯式 `--mcp-supply code-reality-lsp-bridge`、graph server 預設自動供給（CR face 三形＋opt-out 兩形）、freshness 三態 failure-policy 分流（顯式拒／預設 loud skip）、`edit_file` 寫權威揭露、resume exact-supply lineage、isolated-only。同檔 line 30 既有命令式依自帶落日條款收斂為記載面（drift 單收）。單腿 glm 審查→收口 6a3022bc→live chain probe 過→Done。

```mermaid
flowchart LR
  a["bridge 3.10.0 supply v2 出貨"] --> b["caller 教學入留守 skill"]
  b --> c["glm Rust/TS 腿顯式 lsp supply"]
  b --> d["graph server 預設供給＋freshness 閘"]
  d --> e["line 30 命令式收斂（drift 單收）"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
