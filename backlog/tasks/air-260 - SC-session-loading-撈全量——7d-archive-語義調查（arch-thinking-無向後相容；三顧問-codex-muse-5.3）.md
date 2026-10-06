---
id: AIR-260
title: >-
  SC session loading 撈全量——7d archive 語義調查（arch-thinking 無向後相容；三顧問
  codex/muse/5.3）
status: To Do
assignee: []
created_date: '2026-10-06 08:53'
updated_date: '2026-10-06 08:53'
labels:
  - sc-crossover
  - correction
dependencies: []
ordinal: 251000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
user 糾正（2026-10-06 12:34，於 SC session）：SC session loading 機制有問題——撈到全量歷史；zcode 有 7 天 archived 設置可借；arch-thinking 面不用向後相容，看怎樣做比較好；派 codex/muse/5.3 好好調查分析討論後收斂。

**做什麼**：三顧問獨立調查（事實先備：SC 側 loading 代碼路徑＋現況行為＋zcode 7d archive 語義）→ 收斂設計建議 → user 拍板 → SC 側卡承接（southchariot repo）。

**不做**：不改 SC repo（對方主權——產出設計建議與討論收斂，落地歸 SC 卡）。

```mermaid
flowchart LR
    L["SC session loading"] -->|"現況：撈全量"| P["效能/記憶體負擔"]
    A["zcode 7d archived 設置"] --> D["設計輸入"]
    T["arch-thinking（無向後相容）"] --> D
    D --> C["三顧問獨立調查（codex/muse/5.3）"]
    C --> S["收斂設計建議"]
    S --> U["user 拍板"]
    U --> SC["SC 側卡落地"]
```
<!-- SECTION:DESCRIPTION:END -->
