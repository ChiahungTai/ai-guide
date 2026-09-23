---
id: AIR-179
title: AIR-174 deployment 繼任——live acceptance（--marshal 派工執行）
status: To Do
assignee: []
created_date: '2026-09-23 12:02'
labels: []
dependencies: []
ordinal: 165000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**問題**：AIR-174 結案 Done 時 deployment-surfaces=pending——實機安裝與 firing 未驗，無 owning 卡＝半套。本卡為繼任卡。

**這張卡要做**（以 --marshal 派工執行——兼 DB-33 dogfood）：
1. live 安裝：governance/install.py 實跑，三面投影（CC exec-form／ZCode process／Codex quoted）
2. 投影驗證：三面 config 含新 hooks（kanban-skill-gate／黑話掃描 entry）
3. rollback 演練：uninstall 路徑實跑確認可逆清理→再裝回（終態＝已安裝）
4. live firing：zcode 新 session 實測兩閘

**不做**：不改 install.py 本體（審查歸 AIR-178）。

```mermaid
flowchart LR
  I["install.py 實跑（--marshal 派工）"] --> V["三面投影驗證"]
  V --> RB["rollback 演練→裝回"]
  RB --> F["live firing 實測"]
  F --> DONE["AIR-174 pending 解除"]
```

**驗收**：三面投影正確＋rollback 實證＋firing 記錄；authorityMode=marshal stamp 在 ledger（DB-33 dogfood 副產品）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 三面投影驗證（CC/ZCode/Codex config 含新 hooks）
- [ ] #2 rollback 演練實證可逆＋終態已安裝
- [ ] #3 live firing：zcode 新 session 兩閘實測記錄
- [ ] #4 authorityMode=marshal stamp 在 ledger（DB-33 dogfood 副產品）
<!-- AC:END -->
