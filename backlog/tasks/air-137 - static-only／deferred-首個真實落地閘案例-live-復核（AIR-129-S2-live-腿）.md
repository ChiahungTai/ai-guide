---
id: AIR-137
title: static-only／deferred 首個真實落地閘案例 live 復核（AIR-129 S2 live 腿）
status: To Do
assignee: []
created_date: '2026-09-18 08:00'
labels:
  - instruction-writing
  - dogfood-後續
dependencies: []
ordinal: 119000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-129 的兩輪 dogfood 全是歷史 diff replay，測不到兩件事（EP §4 S2 live 腿規定）：①static-only 判準對真實 staged diff 的求值順暢度——含「作者證明渲染輸出 byte 等價」這個義務的實際操作成本；②deferred 回執在真實 no-candidate 情境的可用性（若下次弧剛好撞額度緊，直接實測 P4）。觸發條件：下次任何控制面 instruction 條文變更弧，實走落地閘時順手復核，結果回寫判準（微調走既有 amendment 路徑；PASS 則記錄即可）。判準現行條文：skills/instruction-writing/SKILL.md 落地前審查閘節第 4/5 款。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 下弧首個真實落地閘案例完成 live 復核（static-only 求值＋deferred 欄位可用性）
- [ ] #2 復核結果回寫：判準微調（走 amendment）或 PASS 記錄落卡 notes
<!-- AC:END -->
