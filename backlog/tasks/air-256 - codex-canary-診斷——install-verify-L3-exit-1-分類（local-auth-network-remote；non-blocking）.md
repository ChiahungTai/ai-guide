---
id: AIR-256
title: >-
  codex canary 診斷——install --verify L3 exit 1
  分類（local/auth/network/remote；non-blocking）
status: To Do
assignee: []
created_date: '2026-10-05 22:38'
updated_date: '2026-10-05 22:39'
labels:
  - diagnostics
dependencies: []
ordinal: 247000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
install --verify 的 L3 codex canary FAIL（codex exec exit 1）——目前歸因只是假設（auth/網路），exit 1 本身不提供 attribution。本卡防止 red-gate normalization（verifier 習慣性被忽略＝失去 gate 價值）。

**做什麼**：分類先行——保存 exit 1 的 stderr/phase 原樣輸出，區分 local installation defect／credential-auth unavailable／network-provider unavailable／remote runtime regression；若是環境類，評估 install --verify 的 L3 是否該加 ENV-BLOCKED 第三態（local verify 與 external-readiness 分面）。下次實際 codex 派工失敗即升級。

**不做**：不阻塞任何既有弧；不預先歸因。

```mermaid
flowchart LR
    E["L3 canary exit 1"] --> C{"分類"}
    C -->|local| F["修 installer/config"]
    C -->|auth 或 network| B["標 ENV-BLOCKED（候選新態）"]
    C -->|remote regression| U["上游回報"]
```
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide b8026cc0〕〔Already-decided, do not re-argue: classification-first (local defect / auth / network / remote regression) —— exit 1 itself carries no attribution, existing auth/network suspicions are hypothesis and must not be written as conclusions; evaluate L3 adding ENV-BLOCKED state; escalate to diagnosis on next actual codex dispatch failure〕Scope: diagnosis + install.py --verify L3 tri-state evaluation; do not block existing arcs.
<!-- SECTION:PLAN:END -->
