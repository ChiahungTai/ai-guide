---
id: AIR-180
title: >-
  marshal mode work-order amendment——blanket no-commit 改接 conditional
  delegation（DB-33 後續）
status: To Do
assignee: []
created_date: '2026-09-23 12:02'
labels: []
dependencies: []
ordinal: 166000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**問題**：DB-33 落地（--marshal 上線）但我方 work-order 範本還有 blanket no-commit 圍欄——能力落地了，caller 工單會把它綁死。

**這張卡要做**：work-order.md 加 marshal mode 條款——--marshal 派工的 writer 工單不帶 blanket no-commit fence，改為「commit 授權依 caller 的 conditional commit delegation（active arc＋有效 post-build receipt＋judge 收斂＋revision 未變）」。不動：correctness guards（slash 防護、model pin）、reviewer READ-ONLY fence（role 語義）。依據：bridge 評估「commit 治理不進 bridge，正確位置是 caller governance」。

**不做**：install.py 審查（AIR-178）；live acceptance（AIR-179）。

```mermaid
flowchart LR
  M["--marshal 派工"] --> WO["work-order 無 blanket no-commit"]
  WO --> CD["commit 授權＝conditional delegation"]
  G["slash 防護＋model pin"] -.->|保留| M
```

**驗收**：work-order.md marshal 條款在場；bridge-dispatch 相關句無矛盾；rg 一致性。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 work-order.md marshal mode 條款在場（no-commit fence 解除改 conditional delegation 指針）——rg 可查
- [ ] #2 bridge-dispatch 相關句零矛盾（slash 防護/model pin/reviewer fence 保留聲明）
- [ ] #3 dogfood：--marshal 派工實測記錄（ledger stamp＋寫入 parity＋guards 保留）——併 AIR-179 執行
<!-- AC:END -->
