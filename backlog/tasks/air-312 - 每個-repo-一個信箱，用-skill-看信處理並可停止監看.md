---
id: AIR-312
title: 每個 repo 一個信箱，用 skill 看信處理並可停止監看
status: In Progress
assignee: []
created_date: '2026-10-11 23:14'
updated_date: '2026-10-11 23:14'
labels: []
dependencies: []
ordinal: 297000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把跨 repo 信件處理收斂為一 repo 一信箱，名稱就是 repo name。呼叫 skill 才看信處理，可持續監看，也可停止；保留防重複處理與不漏信的交易保證。

```mermaid
flowchart LR
  A["呼叫處理信 skill"] --> B["本 repo 信箱"]
  B --> C["判讀並處理"]
  C --> D["記錄結果後回執"]
  C --> E["需要裁決則呈報"]
  A --> F["監看新信"]
  F --> C
  G["停止"] --> F
```

依已拍板設計實作與審查；舊信箱逐一對帳後退役，其他 repo 的遷移由其 owner 承接。
<!-- SECTION:DESCRIPTION:END -->
