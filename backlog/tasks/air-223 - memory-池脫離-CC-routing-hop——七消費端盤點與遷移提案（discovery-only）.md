---
id: AIR-223
title: memory-池脫離-CC-routing-hop——七消費端盤點與遷移提案（discovery-only）
status: To Do
assignee: []
created_date: '2026-10-01 01:46'
updated_date: '2026-10-01 01:46'
labels: []
dependencies: []
ordinal: 209000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**做什麼**：只調查不動手——memory 池的讀寫路由現在把 CC 目錄當中繼站（CC 休眠後這依賴主權尷尬，且新機器建池要先開一次 CC session 才能建鏈）。盤點所有消費端、分兩類（池路由面 vs Claude 歷史遙測面）、產出單一遷移拓撲提案＋新機器負向案例證明＋回滾次序。完成後再決定開不開實作卡。

**不做什麼**：不改任何 symlink/hook/池位元組；corrections-weekly 與 standup 的 CC 路徑是歷史遙測面（非池路由）——只分類不盲改。

**等 user 什麼**：提案完成後拍板開不開實作（trigger＝discovery 證明 direct-anchor 方案＋fresh-machine 負向案例＋rollback 三者成立）。

```mermaid
flowchart LR
    INV["七消費端盤點<br/>池路由面 vs 遙測面"] --> TOP["單一遷移拓撲提案<br/>direct-anchor 候選"]
    TOP --> NEG["fresh-machine 負向案例<br/>（從未建 CC 目錄仍可建池）"]
    NEG --> RB["migration/rollback 次序"]
    RB --> GATE["user 拍板 → 實作卡？"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 active consumer 全枚舉分類表（每行：行為需求＋候選改法＋驗證式——池路由面 vs 遙測面二分）
- [ ] #2 單一 proposed topology＋fresh-machine 負向案例證明（從未建 ~/.claude/projects 條件下 pool routing 可建立/驗證）＋migration/rollback 次序＋consumer-equivalent probes 清單
- [ ] #3 零代碼改動舉證（git status --porcelain 乾淨）＋telemetry 面保留/停用建議與理由（coverage 決策移交 user）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔Planning Contract——AIR-223 Tier C discovery（唯讀調查弧；codex 重定義採納——池已在 repo/.agents/memory，問題＝CC routing hop 非池位置）〕
**Baseline**：main @ f7850c10＋AIR-215 調查面 4＋批次討論 verdicts（.agent-tmp/backlog-batch/）。
**已決策（勿重辯）**：①discovery-only 零代碼改動②消費者二分：池路由面（setup-memory-symlinks.sh:19/:33、verify-memory-topology.sh:15/:23、memory-index-regen.py:42-45、instruction-init 池探測、root AGENTS.md 觀察池路由）vs Claude transcript/telemetry 面（corrections-weekly --cc-root、standup ~/.claude/projects——不屬 re-anchor，coverage 決策另議）③候選終態評估 ZC_MEM→<repo>/.agents/memory 直接鏈優先；CC path 僅可為 optional compat alias 不得為 prerequisite（setup:61 要求先開 CC session 已是 trigger）④禁先寫目標「搬 ~/.agents/」——repo 池已實體，防第二 authority⑤實作 trigger＝discovery 證明 direct-anchor＋fresh-machine 負向＋rollback 三者成立。
**Scope**：動＝無（唯讀＋提案文落 .agent-tmp/air-223/proposal.md）。不動＝一切 runtime/symlink/scbus/agents 投影。
**Scenarios**：fresh-machine（從未建 ~/.claude/projects）負向案例；夜波/晨波/reconcile/telemetry/standup/instruction-init 六面行為對照。
**Integration**：下游＝user 拍板→實作卡（trigger＝direct-anchor＋fresh-machine 負向＋rollback 三者成立）。
**驗證式**：AC 三項。
<!-- SECTION:PLAN:END -->
