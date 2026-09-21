---
id: AIR-153
title: Rate limit 與 usage limit 概念分流——spawn 失敗態辨識條文澄清
status: To Do
assignee: []
created_date: '2026-09-21 23:02'
labels: []
dependencies: []
ordinal: 140000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
spawn agent 撞到限制時，有兩種性質相反的失敗：**rate limit**（請求頻率被打回——backoff／降並發就能解）和 **usage limit**（訂閱額度窗口耗盡——只能等重置）。現行 model-routing skill 的失敗態表隱含這個差異，但沒有概念層的分流條文，誤判會白等或白撞。

**做什麼**：在 model-routing skill「spawn 失敗態辨識」表格前加一條概念分流 blockquote，含三家對應（GLM 1308/429 兩碼分流、codex native 429 structured body 分類、codex web 冷凍 dialog＝retryable rate signal）；順手對齊 1302 行的 rate 用語。

**不做什麼**：不重刻窗口數字（正典＝「窗口語義」節）、不改 429 處置正典（agent-workflow）、不動 memory-audit／audit-test 的既有鬆散用語（記為後續收斂候選）。

**狀態**：bi 審查（codex＋muse）已 PASS-with-fixes、修正全數採納；spine glossary 快查投影已先行落地（記憶層，repo 外）。

```mermaid
flowchart LR
    A["spawn agent 失敗"] --> B{"哪種 limit？"}
    B -->|"429 頻率節流"| C["rate path：backoff，持續 429 才降並發"]
    B -->|"1308 額度窗口"| D["usage path：只能等重置，降並發無效"]
    C --> E["codex native：structured body 三態分類"]
    C --> F["codex web：Too many requests dialog＝暫時冷凍"]
    D --> G["GLM 1308 錯誤內含重置時間戳"]
```
<!-- SECTION:DESCRIPTION:END -->
