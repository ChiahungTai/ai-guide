---
id: AIR-236
title: >-
  mosaic cr-audit (1)(2) re-route——reviewer spawn prompt CR 段＋rules-reminder
  routing 行盤點（ai-guide instruction 主權；信 46fb84ab）
status: To Do
assignee: []
created_date: '2026-10-02 13:20'
labels: []
dependencies: []
ordinal: 227000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
delegate-bridge duty session relay（msg ee65474f；本體存 sess_8e15d9db 信箱 new/1790904263207）：mosaic session 6a7b8240（GLM-5.3-Flash seat）CR-audit 提案信 46fb84ab（cr-audit-suggestion-20261001，原文存 fixture 信箱 `01a0f427…/cur/1790822637785-cr-audit-suggestion-20261001.json`）四建議——(3) 外部 reviewer CR 降級義務＝duty session 裁「我方 review WO 契約已編碼（bridge-attached bounded CR evidence／unverified-by-graph 標記／四態標記，例 .review/db-74.md）」、(4) bridge job 紀錄 durable＝DB-76 在途——兩點本卡不接。(1)(2) 屬 ai-guide instruction deployment 主權，本卡盤點：

- **(1) reviewer spawn prompt CR 段**：code-review/reviewer spawn prompt 模板（_common review-cycle 或 work-order）應帶「symbol/呼叫鏈/錨點 freshness 查證用 cr-query（repo 有 .code-reality/graph.db）」——接線從規範在場變 prompt 在場。盤點現狀：AIR-224（crsurface→route 投影＋per-leg receipt）／AIR-227（roles 白名單 lsp-bridge）／AIR-232（宣稱—證據綁定表）之後的殘差為何——work-order「Review/advisory variant」節與 workflow-review-pattern 是否已實質滿足，或仍缺一行預設 CR 檢查段。
- **(2) rules-reminder 摘要納 symbol-query-routing 一行**：盤點 skills/rules-reminder 是否已含 routing 指針；缺則一行補丁。
- 產出：兩點各一行 verdict（covered-by ＜檔案錨點＞ 或 patch-needed）；patch-needed 項當弧直接補或開後續卡。
- 邊界：純盤點＋最小補丁；禁重開 CR 機制卡（224/227/232/234 已承載機制面）。

```mermaid
flowchart LR
    L['mosaic 信 46fb84ab<br/>CR-audit 四建議'] --> D['duty session 裁決']
    D -->|3 已編碼| X0['不接（WO 契約已含）']
    D -->|4 = DB-76| X1['delegate-bridge 在途']
    D -->|1＋2 re-route| C['本卡盤點<br/>AIR-236']
    C --> V1['(1) reviewer prompt CR 段<br/>covered-by 或 patch']
    C --> V2['(2) rules-reminder routing 行<br/>covered-by 或 patch']
    V1 --> F['followup 卡或直補']
    V2 --> F
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

- [ ] #1 兩點 verdict 行記本卡 notes（covered-by＜錨點＞ 或 patch-needed） `rg -c "covered-by|patch-needed" "backlog/tasks/air-236 - mosaic-cr-audit-12-re-route——reviewer-spawn-prompt-CR-段＋rules-reminder-routing-行盤點（ai-guide-instruction-主權；信-46fb84ab）.md"` → ≥2
- [ ] #2 patch-needed 項各有下場（本弧 patch commit sha 或 followup 卡 id；全 covered 時顯式 waiver 行） `rg -c "followup:|patch-commit:|waiver:" "backlog/tasks/air-236 - mosaic-cr-audit-12-re-route——reviewer-spawn-prompt-CR-段＋rules-reminder-routing-行盤點（ai-guide-instruction-主權；信-46fb84ab）.md"` → ≥1

