---
id: AIR-157
title: 排程接續狀態機——at skill 的排程回執與禁靜默降級
status: To Do
assignee: []
created_date: '2026-09-22 01:53'
labels:
  - session-lifecycle
dependencies: []
ordinal: 143000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**這卡解什麼**：/at 排程接續現況不可靠——CronCreate 被拒後即興退到背景 sleep（綁 session 存活，session 死＝保險全滅，昨夜三連敗實證）；ticket 只有 identity/pointer 沒有生命週期；「到點了沒做完」靠新 session 讀 prose 判斷；cleanup 用 mtime>7d 會誤刪未到期 ticket。

**改成什麼**：ticket 升狀態機 SCHEDULED→ARMED→FIRED→RESTORE_PROVEN→SETTLED＋SCHEDULER_REJECTED／MISSED／RESTORE_FAILED／CANCELLED；scheduler arm 成功必有 arm receipt、失敗 fail-loud SCHEDULER_REJECTED——禁靜默降級 sleep；fire 後「做完沒」＝機械判準（ticket 狀態＋registry 組合查，非讀 prose）；cleanup 依 resume_at＋state＋grace（淘汰 mtime）；notification adapter 化（say 語音 headless 必敗，降可選）。

**開工必答**：MISSED 的 covering 觸發——overnight blind window 沒有 Marshal entry／SessionStart，誰來掃（host 啟動？launchd？）或誠實標 unsupported window。

**不做什麼**：接續優先序自動化（判斷面）、自造 scheduler primitive（只消費 harness verified adapter，沒有就標 unsupported）。

```mermaid
flowchart LR
  S["SCHEDULED"] -->|"arm receipt"| A2["ARMED"]
  A2 --> F["FIRED"]
  F --> R["RESTORE_PROVEN"]
  R --> T["SETTLED"]
  S -.->|"fail-loud"| X["SCHEDULER_REJECTED"]
  A2 -.-> M["MISSED"]
  F -.-> RF["RESTORE_FAILED"]
```

〔已決策勿重辯〕tri 裁決 2：禁 failure-class collapse（CronCreate 被拒≠session 內 sleep 苟活——兩個 failure domain 不可互為 fallback；替代 adapter 須獨立 failure domain＋經驗證雙條件）；scbus 續接登記定位＝reconcile 路徑非降級；開卡序在 B（air-155）／C（air-156）之後——scheduler capability 是真問題非文檔重寫。溯源同 AIR-155。開工時依 card Planning Contract 補 AC/Plan。
<!-- SECTION:DESCRIPTION:END -->
