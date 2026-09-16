---
id: AIR-110
title: 全新機器一鍵安裝 bootstrap——hooks×3 家＋symlink 活視圖＋bundle 部署＋驗證探針
status: To Do
assignee: []
created_date: '2026-09-16 07:25'
updated_date: '2026-09-16 07:26'
labels: []
dependencies: []
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
現在的安裝知識散在 AGENTS.md 各節＋卡片＋調查卷宗，全新電腦要靠讀文檔逐步手動重裝。這卡產出冪等的 bootstrap 腳本＋安裝清單文檔，讓新機器安裝可重現、可驗證。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 bootstrap 腳本冪等可重跑（乾跑或新目錄模擬驗證）
- [ ] #2 安裝清單文檔在場（八面全列＋各面驗證命令）
- [ ] #3 三探針整合（sync-sources／memory-topology／AIR-95 firing 協議）
- [ ] #4 AGENTS.md 註冊安裝節指針
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 47d7571〕
〔已決策勿重辯：①0916 盤點 inventory＝八安裝面：ZCode config.json hooks merge（hooks/zcode-registration.json 範本，禁整檔覆蓋）／Claude settings.json 七事件手動／codex hooks.json＋config.toml trust（程序源自 AIR-95 卷宗 .agent-tmp/air-95/dossier.md，含 trust 注意事項）／git core.hooksPath .githooks per-clone／symlink×5（rules、skills、agents×2、CLAUDE.md→guide）／bundle＝scripts/deploy_agents.py／池拓撲＝hooks/setup-memory-symlinks.sh／muse plugin install+approve ②記憶池拓撲段跟隨 AIR-100 決策（同 AIR-71 約束——本卡只裝機制不決拓撲）③優先 config/腳本層 ④~/.zcode/AGENTS.md 非 symlink＝bundle 部署檔（勿改建成 symlink）〕
範圍：bootstrap 腳本（冪等可重跑）＋安裝清單文檔（八面各附驗證命令）＋既有探針整合（/sync-sources 新鮮度、hooks/verify-memory-topology.sh、AIR-95 firing 協議）。
<!-- SECTION:PLAN:END -->
