---
id: AIR-171
title: CR freshness face 消費接線——ai-guide 誠實降級條款升級（AIR-167 後續）
status: Done
assignee: []
created_date: '2026-09-23 01:46'
updated_date: '2026-09-23 01:57'
labels: []
dependencies: []
references:
  - skills/cr-query/SKILL.md
  - skills/review-engine/SKILL.md
ordinal: 157000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**問題**：code-reality v0.9.3 已落地 source identity freshness face（content-addressed sha256-v1），ai-guide 兩處 instruction face 還寫著「缺口未關前只能證偽 stale、不能宣稱 fresh」的誠實降級條款——缺口已關，條文該升級引用新機制。

**這張卡要做**：更新兩個檔的 freshness 段落——①skills/cr-query/SKILL.md「Stale graph check」②skills/review-engine/SKILL.md「CR freshness preflight」——從「HEAD 對照＋誠實降級」升級為引用 freshness face 消費命令（機器可讀欄位：fresh 布林、stale_reasons、indexed/current identity pair、serves）；保留降級語義給 legacy index（無 identity 戳記時 face 自己會回報 legacy-signals——降級語義不廢，只是換機制面承載）。

**不做**：不改 AIR-135 invariant 條文（判準式 fresh ⇔ indexed == current 不變，機制面已補）；不動 graph 重建慣例；不動 admission guard。

```mermaid
flowchart LR
  IDX["index（identity 戳記）"] --> F["freshness face：indexed vs current"]
  F -->|"相等"| FR["fresh=true 可宣稱新鮮"]
  F -->|"不等或 legacy"| ST["stale＋原因（降級既有語義）"]
```

**驗收**：ai-guide index 已 rebuild 激活 identity pair（fresh=true 實證完成）；兩 face 條文更新後 rg 一致性檢查＋與 AIR-135 判準式零矛盾。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 skills/cr-query/SKILL.md「Stale graph check」升級：引用 freshness face 消費命令與欄位；誠實降級語義保留給 legacy-signals 態
- [x] #2 skills/review-engine/SKILL.md「CR freshness preflight」升級：L2 preflight 消費 freshness face（機械判準取代 HEAD 對照宣稱）；降級路徑保留
- [x] #3 驗收：ai-guide freshness --json fresh=true 實證（已完成）＋兩 face 條文 rg 一致性＋與 AIR-135 invariant 判準式零矛盾
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
**結案（2026-09-23）**：兩 face 各一行升級（cr-query L87／review-engine L188-9）——判準由 freshness face 機械求值（code-reality freshness --repo --json：fresh/stale_reasons/identity pair/identity_algo/serves）；fresh=true 可宣稱新鮮；legacy index 由 face 自回報 legacy-signals＝降級語義保留；WT 即時 delta 仍以 live LSP 為準。judge＝marshal 直審（2 行機械接線，rg 驗證：舊語句清零、判準式逐字保留 2 hits、face 欄位與實跑輸出逐字對齊、drift 掃描 skills/rules/agents 零殘留）。commit 7b4532f5。ai-guide freshness 實證 fresh=true（rebuild 後 identity pair 相等 b74a0650…）。

**結案（2026-09-23）**：兩 face 各一行升級（cr-query L87／review-engine L188-9）——判準由 freshness face 機械求值（code-reality freshness --repo --json：fresh/stale_reasons/identity pair/identity_algo/serves）；fresh=true 可宣稱新鮮；legacy index 由 face 自回報 legacy-signals＝降級語義保留；WT 即時 delta 仍以 live LSP 為準。judge＝marshal 直審（2 行機械接線，rg 驗證：舊語句清零、判準式逐字保留 2 hits、face 欄位與實跑輸出逐字對齊、drift 掃描 skills/rules/agents 零殘留）。commit 7b4532f5。ai-guide freshness 實證 fresh=true（rebuild 後 identity pair 相等 b74a0650…）。

```mermaid
flowchart LR
  OLD["舊：HEAD 對照＋誠實降級 只能證偽 stale"] -->|"AIR-171 置換"| NEW["新：freshness face 機械求值"]
  NEW -->|"fresh=true"| OK["可宣稱新鮮 正常派發"]
  NEW -->|"stale 或 legacy"| DG["既有降級語義 背景 rebuild 或降級收據"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
