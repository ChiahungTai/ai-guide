---
id: AIR-291
title: 消費端與治理收斂——deploy_agents／scan-project／metadata-sync／CC smoke
status: To Do
assignee: []
created_date: '2026-10-08 22:36'
labels:
  - instruction
dependencies: []
ordinal: 282000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
前置：AIR-289/290。①deploy_agents.py：L13-14/L48/L866 stale 文字（宣稱已不存在的 Claude 部署面）＋L427-452 neutral purity guard（檢查 CLAUDE.md wrapper）＋test_deploy_agents.py:179 同步②test_air85_projection_oracle.py（instruction-writing bootstrap 逐字比對）同步③scan-project：scan_project.py 文件/parser 命名＋check_single_source.py:60 audience_self_declare source:CLAUDE.md 錨點失效修正④metadata-sync/SKILL.md 範例⑤CC smoke：claude --version→新 session→/config Project instructions→/context root AGENTS.md→Read 子模組驗 nested 載入（獨立於 pytest）。

```mermaid
flowchart LR
  a["CLAUDE.md 全退役——user 裁決"] --> b["本卡：對應段落地"] --> c["驗收：rg 歸零／錨點修／smoke"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 deploy_agents stale 文字＋purity guard＋測試同步
- [ ] #2 scan-project/check_single_source 錨點修
- [ ] #3 CC smoke root/nested 實證通過
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈（codex＋5.3＋judge）
<!-- DOD:END -->
