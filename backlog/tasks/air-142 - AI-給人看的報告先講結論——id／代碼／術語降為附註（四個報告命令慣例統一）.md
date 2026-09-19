---
id: AIR-142
title: AI 給人看的報告先講結論——id／代碼／術語降為附註（四個報告命令慣例統一）
status: In Progress
assignee: []
created_date: '2026-09-19 21:15'
updated_date: '2026-09-19 21:19'
labels: []
dependencies: []
references:
  - skills/_common/conclusion-first.md
ordinal: 129000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
<!-- INTENT:BEGIN -->
白話：AI 給人看的報告要先用一句話講「做了什麼、結論是什麼」——卡 id／代碼／術語降為附註。本週三件溝通糾正「要講做啥，不要只有id」「講人話」「不要一堆代碼」的慣例 rewrite。
tier: standard
<!-- INTENT:END -->
<!-- SA:CONTRACT:BEGIN -->
- [C1] 單一源＝skills/_common/conclusion-first.md（新共用子範本）：原則一句「人類可讀產出先結論／先人話，id／代碼／術語降為附註」＋why＋❌/✅ 實例；原則句逐字只住此檔
- [C2] rewrite 非新增：debrief 七段輸出合約（倒金字塔）標記為本原則既有正典實例；illustrate／smell-detector／deep-work 完成報告各補一行指針接上同一原則，不另造第二套輸出規格、禁多檔重刻
- [C3] 適用域＝人類 viewport 產出（debrief／illustrate／smell-detector／deep-work 完成報告）；LLM 執行鏈產出（EP／findings／code）不適用——命令受眾二分不變
- [C4] 落地閘：boundary 歸級（控制面 instruction 語義變更）——fresh＋intent 分離腿＋跨家族加腿；receipt 四欄入卡 notes
<!-- SA:CONTRACT:END -->
<!-- SA:BOUNDARY:BEGIN -->
- [B1] 不碰 harness 系統提示／LLM 執行鏈產物格式；不新增 hook／gate（純條文慣例 rewrite，corrections 週報 Warm 動作「禁 additive」）
- consumes: 無——standalone rewrite 卡
<!-- SA:BOUNDARY:END -->
<!-- SA:EXPORT:BEGIN -->
- 無（四個 SKILL.md 是行為面消費端，非卡面消費者）
<!-- SA:EXPORT:END -->
<!-- SA:PENDING:BEGIN -->
- 無
<!-- SA:PENDING:END -->

〔背景（detail，不上圖）〕證據＝ai-analysis/reports/corrections-2026-09.md:46 Warm 動作②「rewrite 產出慣例：人類面報告先結論後 id（溝通糾正群 3 件，改既有 viewport 慣例）」。debrief 已有倒金字塔但僅該命令；illustrate／smell-detector／deep-work 完成報告無此慣例。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 skills/_common/conclusion-first.md 存在，含原則句「人類可讀產出先結論／先人話」與 id／代碼／術語附註語義＋❌/✅ 實例（rg 驗證）
- [ ] #2 debrief／illustrate／smell-detector／deep-work 四 SKILL.md 各含 conclusion-first.md 指針（rg -c ≥1 且相對路徑可解析）
- [ ] #3 原則句逐字僅住 conclusion-first.md：rg -F「人類可讀產出先結論／先人話，id／代碼／術語降為附註」全 repo 命中=1（禁多檔重刻）
- [ ] #4 審查腿 receipt 四欄（classification/review/session-freshness/deployment-surfaces）入卡 notes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
①baseline：skills/_common/ 無共用輸出慣例檔；debrief SKILL.md:32 已有倒金字塔七段（僅該命令）；illustrate SKILL.md:14 輸出模式無結論先行條；smell-detector SKILL.md:21 兩 mode 分工無輸出慣例；deep-work SKILL.md:151 階段5生成摘要報告無格式約束
②已決策勿重辯：rewrite 非新增（user 0920 prompt＋corrections:46 Warm 動作禁 additive）；單一源落 skills/_common/conclusion-first.md＋四消費端一行指針（payload C1/C2，digest c0087da3f8b59198）；boundary 歸級（review-engine 判定表示例行：skills 條文新增或修改）
③scope：動＝skills/_common/conclusion-first.md（新）＋debrief/illustrate/smell-detector/deep-work 四 SKILL.md 各一行指針；不動＝其他 skills/rules/命令介面；安裝面（governance manifest surfaces.skills symlink 母鏈）零變動
④scenarios：AI 產人類面報告（完成報告/viewport 簡報）→首句先結論、id/代碼為附註；邊界＝LLM 執行鏈產出（EP/findings/code）不適用；fail＝指針路徑斷鏈（rg 攔）
⑤integration：消費端＝四命令輸出段；上游＝corrections 週報 Warm 動作②；安裝面＝~/.agents/skills＋~/.claude/skills symlink 母鏈隨檔送達
⑥驗證式：rg -F "人類可讀產出先結論／先人話" 全 repo 命中=1；四 SKILL.md rg -c "conclusion-first" ≥1；lint_card_markers exit 0；receipt 四欄在卡 notes
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【authoring receipt】accepted c0087da3f8b59198 2026-09-20
<!-- SECTION:NOTES:END -->
