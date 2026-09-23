---
id: AIR-178
title: install.py +917 全量審查——3.12 resolver＋三家 registration 投影（深審腿）
status: To Do
assignee: []
created_date: '2026-09-23 12:02'
labels: []
dependencies: []
ordinal: 164000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**問題**：governance/install.py 在 164c184c 的 +917 行（3.12 resolver＋三家 registration 投影）——兩輪審查都只抽查 resolve_hook_python，其餘約 800 行無人全讀。安裝器是部署要道（全部 hooks 靠它進三面 config）。

**這張卡要做**：單發深審腿（muse/codex READ-ONLY）覆蓋五優先面——①interpreter resolver（input→path 全路徑、缺 uv/缺 3.12/multi-3.12 的 fail-loud、錯誤指引可操作性）②template renderer（token replacement、quoted command/argv parity）③uninstall/rollback（ownership 對稱、不誤刪 user config、殘留 bare python3 掃描）④三家 parity（CC exec-form／ZCode process／Codex quoted）⑤security（路徑注入、不可信 cwd、--no-python-downloads 繞過面）。

```mermaid
flowchart LR
  A["+917 行"] --> B["五優先面深審"]
  B --> C{"Critical/Important?"}
  C -->|是| F["修復歸 air-174 線或小修卡"]
  C -->否| OK["審查通過記錄"]
```

**不做**：不改 install.py（審查卡）；不跑 live 安裝（歸 AIR-179）。

**驗收**：findings 表＋無未處置 Critical/Important＋修復歸屬清單。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 深審腿 findings 表落地（五面覆蓋＋錨點）
- [ ] #2 Critical/Important 全數有處置歸屬
<!-- AC:END -->
