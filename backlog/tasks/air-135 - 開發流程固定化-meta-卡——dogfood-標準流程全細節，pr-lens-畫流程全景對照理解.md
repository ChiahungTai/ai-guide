---
id: AIR-135
title: 開發流程固定化 meta 卡——dogfood 標準流程全細節，pr-lens 畫流程全景對照理解
status: To Do
assignee: []
created_date: '2026-09-18 07:14'
updated_date: '2026-09-18 07:15'
labels: []
dependencies: []
ordinal: 117000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把這次討論的「開發流程固定化」本身當第一個 dogfood 對象：照標準流程每個細節走一遍，第一產物＝用 pr-lens 把標準開發流程畫成全景圖，給 user 對照 AI 的理解與 user 的想法是否一致。對齊後才固化條文（下游：AIR-134 編譯器、DRAFT-12 EP/卡邊界）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ①graph document 過 npx validate（零錯誤）②render SVG user 可直接開（light/dark）③user 對照後的差異清單已收斂成文件④S1 圖中的每個節點在 ai-guide skills/條文有對應出處（抽查可溯源）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide main（開工時重確認）〕

〔源（user 0918 逐字）：「我在想 開個 meta card，然後 dogfood 這次的問題，然後先直接用看看 pr lens，呈現你的理解跟我的想法是否符合，這樣如何，要從完整的開發流程開始，先從標準的流程，要有每個細節」〕

〔已決策勿重辯：①方向>>品質——viewport 先驗方向，圖醜不擋結論②第一產物暫存 .agent-tmp/air-135/、看完即棄（照 AIR-134 收斂的 fast-path 原則：要看再產、不入版控）③靜態地圖 delta 全 unchanged（誠實語義），非 canon 的新東西用 badge 標④手作 graph document（slice-0 形態零基建）→ npx validate → npx render，不走 producer⑤本卡後續條文固化工作觸控制面＝persistent card WT（wt-open）〕

範圍：S1＝標準開發流程 graph document（規劃／開卡開工／實作審查／收尾結案／跨 session／viewport 六 lane，每個細節）＋validate＋render 交 user 對照；S2＝依對照差異清單修圖或修理解，收斂後產出差異清單文件；S3＝收斂版餵下游（AIR-134 S1 contract、DRAFT-12 promote 的條文工作另走各卡）。
<!-- SECTION:PLAN:END -->
