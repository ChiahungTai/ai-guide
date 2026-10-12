---
id: AIR-317
title: muse/grok 治理 bundle 瘦身——三家族版本競稿＋整合
status: Done
assignee: []
created_date: '2026-10-12 10:13'
updated_date: '2026-10-12 12:49'
labels: []
dependencies: []
references:
  - AIR-317
ordinal: 302000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
治理 bundle（guide＋17 條 neutral rules）在 muse/grok 面已達 30KiB 預算的 99%——每次加條文都貼著 gate，該正式瘦身了。

**這卡做什麼**
- 三家族（GLM-5.3-Flash／muse／codex）各自獨立出一版瘦身方案（同素材同約束，唯讀競稿）
- Marshal 整合出終版：目標 muse/grok 面留出實質餘裕（≤28KiB），核心紀律語義零損失
- 走落地前審查閘（boundary）＋四端部署驗證

**不做什麼**
- 不砍掉 always-on 核心（首個有後果決策前必須在場的規則面）
- 不用行數/字數當判準（instruction-writing 禁元資訊）

```mermaid
flowchart LR
  M[實測組成 30430B] --> G[三家族競稿 x3]
  G --> J[Marshal 整合終版]
  J --> L[Flash 落地]
  L --> V[muse grok 面 <=28KiB 實測]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 三家族競稿回收（muse/codex 全文＋glm 關鍵判斷早收斂——整合記錄 .agent-tmp/air317-integration.md）
- [x] #2 Marshal 整合終版有逐項裁定表（採納/否決＋理由）
- [x] #3 落地後 muse/grok 面 bundle ≤28KiB（部署實測 26,895B/87%）；zcode/codex 面 90KiB gate 不變綠
- [x] #4 核心紀律語義零損失：確認腿逐 rule 勾稽表（sink）
- [x] #5 boundary 審查閘四欄回執＋四端部署驗證
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide db24b2b9〕〔已決策勿重辯：①三家族競稿（user 裁定：5.3/muse/codex 各出一版、5.3 整理終版）②瘦身槓桿限三形——reference 分層下沉（rule 留最小核心＋pointer，深層住 skill，既有先例：acceptance-evidence/symbol-query-routing）、per-lane scope 差異化（deploy target exclude 機制）、prose 收緊/冗餘移除③always-on 核心語義零損失（首個有後果決策前必須在場）④禁元資訊〕範圍：guide＋17 neutral rules 的瘦身方案（唯讀競稿×3→Marshal 整合終版→Flash 落地→boundary 審查閘→merge→deploy 驗證≤28KiB）。素材：bundle 實測組成（guide 6663B／outward-action-consent 4217B／context-management 2589B／collaboration 2469B／quality 2103B／design-thinking 1626B／tool-discipline 1589B／acceptance-evidence 1354B／bridge-dispatch 1138B／其餘<1.1K）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
收線：三稿競稿（muse/codex 全文＋glm 關鍵判斷）→整合裁定（exclude 否決）→Flash 落地 8 檔→muse 確認腿 accept（語義零損失機械比對確認、裁定三條全守、Marshal 數值覆驗屬實；F-1 可選微修記錄）；merge e14cabbb；四端部署 26,895B+carve-out（88%）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
治理 bundle 瘦身：三稿競稿（muse/codex 全文＋glm 判斷）整合——codex 六 rule 收緊＋muse 兩項（tool-discipline/acceptance-evidence pointer）；exclude 否決（muse 可為派工端反例）。30,430→26,895B（gate 99%→87%）。確認腿 accept。

```mermaid
flowchart LR
  M[muse 全文] --> J[整合裁定]
  C[codex 全文] --> J
  G[glm 判斷 exclude 否決] --> J
  J --> F[Flash 8 檔]
  F --> V[26895B 87 percent]
```
<!-- SECTION:FINAL_SUMMARY:END -->
