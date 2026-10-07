---
id: AIR-276
title: A5 handoff send 遷移——scbus send → dutymail send（db807 B0/P2 前置）
status: In Progress
assignee: []
created_date: '2026-10-07 21:44'
updated_date: '2026-10-07 21:50'
labels:
  - dutymail
dependencies: []
references:
  - skills/handoff/SKILL.md
ordinal: 267000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bridge db807 B0 協調信指名：skills/handoff/SKILL.md:128 仍是 scbus send --to（delivery leg 1）、:95 transport receipt 面、:168/:177 條文同步——遷移到 dutymail send＋receipt 詞形（dutymail-roundtrip.md 契約＝我方自寫）。P2 freeze（bridge 拔舊信箱前置）等此項完成。

**做什麼**：①handoff SKILL.md :128 send 面改 dutymail send（envelope v2、strict grammar——本班今日已實寄 7 封驗證契約）②:95 transport receipt 面改 dutymail receipts 詞形 ③:168/:177 條文同步 ④寄測試信 roundtrip 驗證（handoff → bridge 收訖）。
**不做什麼**：manual paste fallback 不動；dutymail-roundtrip.md 契約本體不動（只消費）；M7 拔 home 不動。

```mermaid
flowchart LR
  h["handoff Phase 5"] --> s["scbus send --to 舊"] --> d["dutymail send envelope v2"]
  d --> r["receipts 面同步"] --> ok["B0/P2 可啟動"]
```
<!-- SECTION:DESCRIPTION:END -->
