---
id: AIR-128
title: 文件與目錄的防漂移對帳擴面——model 名、hook 判準、紅線表的單一源查核
status: In Progress
assignee: []
created_date: '2026-09-17 15:08'
updated_date: '2026-09-18 00:32'
labels: []
dependencies: []
references:
  - skills/model-routing/SKILL.md
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
corpus 宣稱多處單一源，但一半有第二副本且無查核：model-routing 正文具名 model 18 處、hook 三判準三檔重寫、紅線枚舉表住在 skill 而 rule 宣稱唯一源。改任一處其他靜默腐爛。這卡補機械對帳 lint＋pointer 化。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 #1 model 詞彙 lint 上線且現存 18 處違規有處置（改寫或 allowlist 附理由）#2 三判準與紅線表單一正典＋他處 pointer 化完成，rg 驗證無全文重抄#3 lint 進 parity gate（--check 面）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：main@f892c344〕〔已決策勿重辯：①跟既有 checker 家族（sync_agents --check／check_single_source 模式）加 lint，不建新框架②(a) model 詞彙 lint：skill prose 內 model token 必須命中 catalog id/token 集合（源=muse I-5，18 處實證）③(b) pointer 化：hook 三判準（I-3，三檔）與 outward 紅線枚舉（I-4，skill 14 處 vs rule 2 處）各留單一正典＋他處縮 pointer；正典歸宿＝memory-audit 統一定義表／outward rule④L1-L6 循環 deferral（A1-F3）已由 0917 審查弧直接修復，不入本卡⑤語義搬移屬 instruction-writing 落地閘面——實作時走審查腿〕範圍——改：skills/model-routing/SKILL.md、skills/instruction-writing/SKILL.md、skills/autonomous-execution/SKILL.md、rules/outward-action-consent.md；新增 lint 掛 sync_agents 或獨立 checker。
<!-- SECTION:PLAN:END -->
