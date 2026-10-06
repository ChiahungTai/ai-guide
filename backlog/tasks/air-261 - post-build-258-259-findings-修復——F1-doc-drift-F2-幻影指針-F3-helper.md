---
id: AIR-261
title: post-build 258/259 findings 修復——F1 doc drift/F2 幻影指針/F3 helper
status: In Progress
assignee: []
created_date: '2026-10-06 08:56'
updated_date: '2026-10-06 08:56'
labels:
  - dutymail
dependencies: []
ordinal: 252000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post-build 階段 1 審查（弧 ade9a195..af1d32dd）三筆 findings 修復：F1 governance 治理文檔殘留已退役的 monitor 文案（drift）；F2 摘要行指針是不可執行的幻影命令（dutymail events 無 envelope-id 過濾參數）；F3 render() class 計數迴圈重複。

**做什麼**：三筆修復＋指針命令形測試斷言（詳 Plan）。

```mermaid
flowchart LR
    A["F1 ownership doc"] -->|"文案同步 B′"| B["governance/scbus-address-ownership.md"]
    C["F2 幻影指針"] -->|"改 events --address 形"| D["scripts/duty_receive.py render"]
    E["F3 重複迴圈"] -->|"_klass_counts helper"| D
    D --> T["指針命令形斷言測試"]
```
<!-- SECTION:DESCRIPTION:END -->
