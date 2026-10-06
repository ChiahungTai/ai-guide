---
id: AIR-258
title: B′ 解凍——G3 surface 縮窄（恆人工留 INBOX）＋G4 holderless 改常態
status: To Do
assignee: []
created_date: '2026-10-06 08:27'
labels:
  - dutymail
dependencies: []
ordinal: 249000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
B′ 解凍：SC-305 已上線（SC 能讀 dutymail projection），ai-guide 側兩項跟進落地——G3 收信處理器的 surface 面縮窄＋G4 monitor 的 holderless 語義改常態。

**做什麼**：①G3 surface 縮窄——恆人工項（handoff/patrol/work-order/solicit/未知 class）不再把全文注入 conversation 的 additionalContext，改為 digest 計數行＋「INBOX 查看」指針（人類判讀面＝SC INBOX，B′ 路由分離）；auto 面（inform/receipt 可機械驗證）照舊 digest 吸收。bind/prepare/ack transport 機制完全不動。②G4 monitor——holderless 從「recovery window（異常）」改「常態（pending 在 INBOX 等人）」語義：advisory 文案改、閾值行為保留（session-local 防轟炸）。

**規矩**：default-deny 三層硬底線不動；絕不 flush-ack 不動；v1 零送信不動；roundtrip 文件同步（B′ 語義）。

```mermaid
flowchart LR
    P["prepare 批次"] --> T{"triage"}
    T -->|auto 三底線過| A["digest 吸收（不變）"]
    T -->|恆人工/未知/壞信| D["digest 計數＋INBOX 指針——不再注入全文"]
    A --> K["ack（不變）"]
    D --> K
    M["monitor"] -->|"holderless＝常態"| N["pending N 封在 INBOX（文案改）"]
```
<!-- SECTION:DESCRIPTION:END -->
