---
id: AIR-136
title: review-engine 歸級發散收斂——退出 static-only 後 ordinary vs boundary 在跨家族 AI 間結構性分歧
status: To Do
assignee: []
created_date: '2026-09-18 08:00'
labels:
  - review-engine
  - dogfood-後續
dependencies: []
ordinal: 118000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-129 S2 兩輪 dogfood 實證（EP：ai-analysis/_tasks/0918-air129-review-triage/ep.md §7）：退出 static-only 豁免後的 review-engine profile 歸屬跨家族結構性分歧——muse 恆判 ordinary、GLM-5.3 恆判 boundary/保護分支（AGENTS.md 作用域例外、acceptance-evidence 單一源指派、execution-plan 產物路徑三案例兩輪同向）。方向恆 fail-safe（判定表保護分支兜底）但審查腿配置不確定，每次落地都要 author 提案/judge 複核。候選處置：①判定表加示例行（控制面 instruction 實質語義編輯→boundary 預設）②條文記載已知發散＋最低複核機制③接受現狀僅歸檔觀察。若動判定表＝gate 面條文變更，走 instruction-writing 落地前審查閘。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 歸級發散的處置裁決完成（bi 討論或 user 拍板，三候選擇一）
- [ ] #2 若選改判定表：條文變更走落地閘全儀式＋dogfood 複驗歸級一致性
- [ ] #3 結論回寫本卡 notes＋（如有）review-engine 條文
<!-- AC:END -->
