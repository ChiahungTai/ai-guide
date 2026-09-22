---
id: AIR-156
title: 跨 session 交接直送——handoff 接 scbus 送達證明與授權閘
status: To Do
assignee: []
created_date: '2026-09-22 01:52'
labels:
  - session-lifecycle
dependencies: []
ordinal: 142000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**這卡解什麼**：/handoff 現況＝產 prompt、user 手動貼到目標 session——無送達證明（mosaic/southchariot 收編就是人肉攜帶實證）。本卡讓 handoff 走 scbus 直送：已知 session 第一路＝scbus send（receipt＝queued-visible，不擴 ack protocol）；完成判定分四段（packet-produced→queued-visible→consumed/accepted→ownership-restored），「prompt 產完」不再冒充「對方收到」；manual paste 降為 unavailable fallback。

**要做的新設計——consent gate**：user 親手貼原本是隱式授權載體，直送後 AI 可直達另一 session mailbox——授權面必須重新設計（消費 outward-action-consent：AI 發起逐次授權；跨 ownership envelope 補 consent 欄），不能為機械化拆安全閘。

**不做什麼**：ack protocol amendment（correlated upper-layer reply 先行，多弧實證不足才准重提）、同 repo 預設路徑本輪刪除（方向納入、刪除後置——等 Marshal continuation 路徑 dogfood 後）、新 bus 類型。

```mermaid
flowchart LR
  A["現況：user 當郵差"] --> B["本卡：scbus 直送"]
  B --> C1["produced"]
  C1 --> C2["queued-visible"]
  C2 --> C3["consumed accepted"]
  C3 --> C4["ownership-restored"]
  B --> G["consent gate 設計"]
  A -.->|"fallback"| P["manual paste"]
```

〔已決策勿重辯〕tri 裁決 4：同 repo 意圖遷 Marshal 但本輪不斷路；consent gate 必設（muse 缺口 1）；receipt 語義＝queued-visible 非完成（scbus protocol 明文無 ack／user-read 第三態）。溯源同 AIR-155 合併檔。開工時依 card Planning Contract 補 AC/Plan。
<!-- SECTION:DESCRIPTION:END -->
