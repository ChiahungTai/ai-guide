---
id: AIR-331
title: review_ledger 零 findings 帳本誤報 FAIL——header-only 表豁免（D-009）
status: In Progress
assignee: []
created_date: '2026-10-14 00:36'
updated_date: '2026-10-14 00:36'
labels: []
dependencies: []
references:
  - skills/post-build/scripts/review_ledger.py
ordinal: 316000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
mosaic 端透過 dutymail 回報的修復請求（D-009）：review_ledger.py 把「合法零 findings 帳本」誤報為 FAIL——兩處 `if len(t) > 1` 表格過濾在 ID 欄偵測前就把 header-only 表丟掉，導致 `table.missing` 誤報。雙家族討論（codex job-mv7dioh7＋GLM-5.3 job-mv7dips7）收斂修法②：interpreter 層修正讀取語義（header-only 表＝合法零 findings），格式不動、凍結 grammar 不動、fail-closed 底線不動。

```mermaid
flowchart LR
    A["帳本 lint/parse"] --> B{"含 ID 欄表頭?"}
    B -- "無" --> X["FAIL 真缺表 不變"]
    B -- "有" --> C{"有資料列?"}
    C -- "零列" --> Y["合法零 findings tally 全 0"]
    C -- "有列" --> Z["既有逐列語義 不變"]
```
<!-- SECTION:DESCRIPTION:END -->
