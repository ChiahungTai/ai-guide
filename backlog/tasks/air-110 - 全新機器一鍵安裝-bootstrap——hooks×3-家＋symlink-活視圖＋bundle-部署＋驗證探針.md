---
id: AIR-110
title: 全新機器一鍵安裝 bootstrap——hooks×3 家＋symlink 活視圖＋bundle 部署＋驗證探針
status: To Do
assignee: []
created_date: '2026-09-16 07:25'
updated_date: '2026-09-17 13:40'
labels: []
dependencies: []
ordinal: 95000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
0916 開卡時安裝知識散落；0917 AIR-116 落地 governance installer（五面＋monitor＋verify/check）後地貌已變：installer 面內的安裝已有單一權威入口與穩定 CLI 契約。本卡 re-scope 為：產出冪等的 bootstrap 編排器（前置步→installer→手動 approve 暫停點→驗證探針→面外清單輸出），不重造安裝動作（installer 是唯一安裝入口）；補齊 installer 邊界外的缺口面（CC settings.json 前置鏈〔secrets＋symlink〕、四條 home symlink、hooksPath per-clone、monitor plist 路徑參數化、backlog-cleanup plist 版控化）；並以真機執行完成實機驗證（含 muse 腿，AIR-116 移交）。等 user 開工拍板（含四項決策：secrets 手動拷／primary 副機角色／G2 symlink 歸屬／approve 恆手動邊界）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 bootstrap 腳本冪等可重跑（乾跑或新目錄模擬驗證）
- [ ] #2 安裝清單文檔在場（八面全列＋各面驗證命令）
- [ ] #3 三探針整合（sync-sources／memory-topology／AIR-95 firing 協議）
- [ ] #4 AGENTS.md 註冊安裝節指針
- [ ] #5 bootstrap 編排器冪等可重跑（前置探針→install→驗證全鏈；重跑全 noop 有證據），以 installer 穩定 CLI 契約（manifest.toml [bootstrap_cli]）為唯一安裝入口，不下手工 config
- [ ] #6 面外安裝面補齊：CC settings.json 前置鏈（secrets 拷貝引導 fail-loud＋symlink 建立，順序在 installer 前）、四條 home symlink（歸屬依 plan 決議：擴 manifest skills 面 or bootstrap 建）、git config core.hooksPath .githooks、monitor plist 路徑參數化（跨機器零手改）、backlog-cleanup plist 版控化
- [ ] #7 驗證階段編排既有探針：installer --verify＋--check --surface all（五面綠）、hooks/verify-memory-topology.sh、/sync-sources（AIR-120 收斂後）、hooksPath 輸出探針、spine degraded 檢查；muse 腿真機 PASS
- [ ] #8 新機器全裝總覽文檔在場（擴充 hooks/MULTI-MACHINE.md；installer 面指針指 governance/README bootstrap 節，不重抄）＋專案 AGENTS.md 註冊安裝節指針
- [ ] #9 真機（或 HOME-shim 沙箱）完整跑一輪：全綠收尾報告，含手動 approve 步驟（CC /hooks、codex trust、ZCode 重開 session）完成確認
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 47d7571〕
〔已決策勿重辯：①0916 盤點 inventory＝八安裝面：ZCode config.json hooks merge（hooks/zcode-registration.json 範本，禁整檔覆蓋）／Claude settings.json 七事件手動／codex config.toml inline [[hooks.*]]＋trust approve（2026-09-16 單一 representation 收斂——hooks.json 已退役，註冊與 trust 同檔；trust 注意事項源自 AIR-95 卷宗 .agent-tmp/air-95/dossier.md）／git core.hooksPath .githooks per-clone／symlink×5（rules、skills、agents×2、CLAUDE.md→guide）／bundle＝scripts/deploy_agents.py／池拓撲＝hooks/setup-memory-symlinks.sh／muse plugin install+approve ②記憶池拓撲段跟隨 AIR-100 決策（同 AIR-71 約束——本卡只裝機制不決拓撲）③優先 config/腳本層 ④~/.zcode/AGENTS.md 非 symlink＝bundle 部署檔（勿改建成 symlink）〕
範圍：bootstrap 腳本（冪等可重跑）＋安裝清單文檔（八面各附驗證命令）＋既有探針整合（/sync-sources 新鮮度、hooks/verify-memory-topology.sh、AIR-95 firing 協議）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AIR-116 對齊（EP AC-6.4，0917）：bootstrap 消費 governance/install.py 穩定 CLI 契約——uv run python governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run|--uninstall|--check|--verify]；退出碼 0 成功/1 drift/2 環境守衛/3 未實裝/4 執行錯誤。契約機器可讀投影＝governance/manifest.toml [bootstrap_cli]；新機器逐面檢查清單＝governance/README.md bootstrap 節（七項）。blocked-by 依賴成立：110 bootstrap 執行器以本契約為唯一安裝入口（不下手工 config）。fixture 模擬已驗證乾淨機器安裝（AC-6.3，發現並修復四個新機器 bug：skills 先於 rules 順序/symlink 父目錄/config 缺席自空建/config 父目錄）；muse 腿真機驗證歸 110 實機 bootstrap。

0917 re-scope 盤點（GLM-5.3 研究腿）：八面中 ①③⑥⑧⑨＋skills×2＋monitor 裝載＋firing 協議已由 governance installer 覆蓋（AC#3 第三項＝--verify codex L3 吸收）；真缺口＝G1 CC settings 前置鏈（repo settings.json gitignored local-only 含 API keys——user 手動拷，installer 不建 symlink、乾淨機器直接 install 會造 P0-3 斷鏈形 drift）／G2 四條 home symlink（CLAUDE.md、rules、agents×2——傾向擴 manifest skills 面）／G3 hooksPath／G4 monitor plist 絕對路徑（manifest.toml:66-67 指名 110 承接）＋monitor check stub／G5 backlog-cleanup plist 未版控／G6 池傳輸手動（MULTI-MACHINE §1）／跨 repo 工具（delegate-bridge、code-reality、NT-mosaic、mosaic launchd）列清單不安裝。完整覆蓋矩陣見研究報告（本 session .agent-tmp 產出）。四項 user 拍板：①secrets 重置＝手動拷 ②primary/副機角色（cron/monitor 裝載對象）③G2 symlink 歸屬（擴 manifest vs bootstrap 自建）④approve 三態恆手動（設計邊界）。
<!-- SECTION:NOTES:END -->
