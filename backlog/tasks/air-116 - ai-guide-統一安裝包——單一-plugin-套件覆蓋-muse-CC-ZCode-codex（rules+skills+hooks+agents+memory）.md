---
id: AIR-116
title: >-
  ai-guide 統一安裝包——單一 plugin/套件覆蓋
  muse/CC/ZCode/codex（rules+skills+hooks+agents+memory 防線）
status: In Progress
assignee: []
created_date: '2026-09-16 22:09'
updated_date: '2026-09-17 08:10'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/0917-air116-unified-governance/ep.md
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原範圍（0916 user 提出）＝memory 治理防線四套各自註冊（muse plugin、CC settings、ZCode config、codex inline hooks）收斂為單一套件。**0917 user 擴範圍：套件＝ai-guide 整體，不限 memory**——部署面全部收斂：rules bundle（四家 guide 投影）、skills 共享根、hooks×三家註冊、agents registry（sync_agents 生成面）、memory 治理防線——各 harness 一鍵安裝同一套，消除多處註冊面的維護漂移。

分工邊界：本卡＝套件載體與內容物（what——打包單元、per-harness 安裝面、approve/升級程序）；[AIR-110](air-110 - 全新機器一鍵安裝-bootstrap——hooks×3-家＋symlink-活視圖＋bundle-部署＋驗證探針.md)＝全新機器安裝執行器（how——bootstrap 腳本、驗證探針）——110 開工時改為消費本卡套件（對齊動作列兩卡）。前置＝AIR-100 政策落地（D1-D5＋closure 契約）後再收斂成形。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 單一套件來源覆蓋四家安裝面×全部 ai-guide 部署面（rules/skills/hooks/agents/memory 防線——或明文記錄某面某家不可行的機制證據）
- [ ] #2 安裝/升級/approve 運維程序單一源
- [ ] #3 與 AIR-110 bootstrap 分工對齊（110 消費本卡套件或明文記錄邊界）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
0917 user cross-ref：AIR-113 domain-skills 遷出後的「ZCode 端 skills desc 注入」缺口，未來解法＝ZCode plugin 打包（marketplace 本地目錄源）——本卡擴範圍後 skills 分發面已在 scope 內，該場景為本卡用例之一（決策記錄仍在 AIR-113）。

09-17 Segment 0 完成——十探針（P0-1~P0-10）全數執行，三致命先驗全數解除、零翻案，架構凍結。凍結值：①序列化參數＝json.dumps(indent=2, ensure_ascii=False)＋尾換行（CC/ZCode live config 逐字重現實證）；②CC 寫入鐵律＝Path.resolve() 後才 os.replace（實證 os.replace 直打 symlink 路徑會斷鏈換普通檔）；③skills 面＝兩家皆單一母鏈 symlink（建 2 條即成，零遷移）；④deploy_agents 冪等重跑實證（[SKIP] identical×3、exit 0、dry-run 透傳形態）。新事實：codex pre_tool_use:1:0 已 trusted（user 已 approve——EP AC-3.2 括號陳述過時）；CC/ZCode hooks 子樹結構不同家（CC event→groups map vs ZCode {enabled,events}）；muse plugins hook test --fixture 內建命令（S3 probe 候選）；codex 面非 ai-guide groups 初盤＝Interrupt(chatgpt-web)＋SessionStart/SubagentStart(codebase-memory-mcp)。證據單一源＝references/probe-results.md（file:line 錨點＋逐字輸出）。下一步＝S1（manifest＋registrations 模板，逆抽取基準 P0-6 快照在手）；probe-results.md 尚未 commit（air-116 branch working tree）。

09-17 S1＋S2 核心完成：S1＝manifest＋registrations 三模板（live 逐字逆抽取，AC-1.2/1.3 receipt 全 PASS，references/s1-template-parity.md）＋README；S2＝install.py 核心（真機 TC-1 冪等兩跑全 noop／TC-3 dry-run 零寫入／TC-14 3.9 守衛 exit 2／F-11 flag 互斥 exit 2 全 PASS）。1201 事故（references/incident-20260917-dryrun-write.md）：dry-run mode 字串 bug＋merge 未走 merge_root→真寫入 CC/ZCode config；已全額復原（兩檔 shasum 逐字回事故前值；codex 未觸——parse 防線攔下）；複合故障＝prune 誤刪自家新 bak（檔名排序＋他弧備份入額度）。四 bug 全以結構固化修復（mode 歸一化／merge_root 子樹／codex group 級切塊＋註解搬移截斷／bak -gov 後綴＋mtime prune／通用 preimage 防線——ZCode runtime 併發重寫 config 為本事故新實證／dry-run 寫入 chokepoint 結構性斷言）。新增事實：muse CLI 無 plugin remove（uninstall=disable+leave-and-report，EP Q6 措辭與現實有差，記卡）。待續：S3（--verify）→S4（--check）→S5（monitor 對帳）→S6（契約已落 manifest/README，收尾 110 對齊）→單元測試→live uninstall round-trip（AC-2.5）。

0917 Stop-hook POC（機械閘方案 B 查證，用戶指示）：POC hook 已註冊 live config（擋 2 次放行第 3 次；backup=config.json.bak-20260917-124149-stop-poc），firings 落 .agent-tmp/stop-poc/。自動觸發兩路皆不通——①automation 投遞 append 進「綁定 session」（=建立 automation 的 session，AIR-82 拓撲重演），hook 快照在註冊前→不觸發；②subagent session 結束不觸發 Stop hook（實測 agent 完成、firings 空）。逆向：桌面 bundle（asar/out/host）僅含 hook 事件 schema（Stop 在 enum）但無 stop_hook_active/decision payload 實作——agent 迴圈疑似遠端（coding plan backend），本地 RE 無法閉合。結論：Stop hook block 語義只有官方文檔（明確：decision block+reason 續跑、exit 2 快捷、連續 3 次上限）＋schema 證據，runtime 驗證需要「註冊後啟動的新 main session」——只能由 user 開。附帶新證據：ZCode hook 機械在 main session 確認運作（本 session 內 PreToolUse hook 即時擋下 heredoc 寫入）。

09-17 S3 完成：--verify stub 轉正——四家 probe（muse inspect fail-closed／CC+ZCode 自含 fixture pipe payload exit 2／codex 三層 L1 註冊在場+L2 trust 診斷+L3 真codex exec canary）＋mixed-rep 報告腿＋單元測試 21 tests（AC-3.3 negative＋防恆綠）。live --verify --surface all 全 PASS exit 0：codex L2 五 handlers 全 Trusted 與 P0-1 十二條吻合；L3 bypass flag=per-invocation 正當用途（不寫 state、非模擬 approve）。live 首跑抓到 S2 死碼 codex_trust_diagnostics 兩 bug：HANDLER_HEADER 缺 MULTILINE（L2 整段消失）＋state key event 段 .lower() 應為 snake_case（誤報 Untrusted）——皆修復＋回歸測試守衛。附帶：manifest [bootstrap_cli.exit_codes] 補 4=執行錯誤（S2 實裝漏投影）。receipt＝references/s3-verify-receipt.md。待續：S4（--check 五面 parity）→S5→S6 收尾→live uninstall round-trip（AC-2.5）。

09-17 S4 完成：--check stub 轉正——五面 parity（JSON 語義 diff 缺/多/內容差＋symlink 健康腿／codex Modified 獨立 class＋mixed-rep／muse R6 source↔cache 逐檔 byte 腿（複用 probe_muse，S3/S4 同一實作）／rules=唯讀 import deploy_agents.expected_bundle_for()／agents=sync_agents --check 退出碼串接／skills 母鏈）＋單元測試 21 tests。live：AC-4.1 乾淨態 exit 0；AC-4.2 CC 刪條目→exit 1 命中該條→復原 sha 逐字等→exit 0（附帶實證：mutation heredoc 被 block-python-file-write 即時攔，治理閘在 authoring session 自身生效）；AC-4.5 弄髒生成 registry→透傳 rc=1→復原 exit 0。receipt＝references/s4-check-receipt.md。待續：S5（monitor 對帳）→S6 收尾→live uninstall round-trip（AC-2.5）。

09-17 S5 完成：monitor 對帳收編——AIR-100 S-E muse approve monitor 吸收（舊 script＋測試刪、probe_muse 補 non-dict 腿、plist git mv 改名 governance-health-monitor），五面 health 上線（governance_health_monitor.py 消費 install.py verify+check，薄編排零重寫）。--surface monitor 裝載/卸載入 installer（manifest [surfaces.monitor]）。live：直跑 exit 0、launchctl start 觸發 log 五面行 PASS（含 codex L3 於 launchd 環境）、冪等 noop、殘留掃描零命中（AC-5.5）。途中三事故結構性修復：launchd PATH 無 codex 裸 crash（probe_codex 加 has_cli 守衛，L1/L2 照報+L3 GUARD）／XML 註解含雙連字號被嚴格解析拒讀（create 路徑補 plistlib 源驗證——帶病寫入 chokepoint 堵死；R7 fail-loud 攔截 reload 實證有效）／stale-loaded 誤報 noop（重載分支涵蓋 created）。單元測試 5 支（TC-7）。receipt＝references/s5-monitor-receipt.md。待續：S6 收尾（110 對齊＋instruction 同步＋live uninstall round-trip＋全段補跑 post-build）。

09-17 S6 完成（弧收尾）：bootstrap 契約凍結（CLI_SURFACES/CLI_FLAGS 常數＋[bootstrap_cli] 對帳測試四支）；AC-6.3 fixture 模擬乾淨機器揪出四個新機器 bug 全修復（skills 先於 rules 順序／symlink 父目錄／config 缺席自空根建／config 父目錄 mkdir）；AC-2.5 live uninstall round-trip 定版全 PASS（三 config shasum 逐字對稱；揪出 muse disable 後 approve 失敗——install path 改 install→enable→approve 順序契約，實證回復 trusted_enabled）；AC-6.4 air-110 卡對齊落 notes。post-build 全段補跑（user 指示）：audit-test agent（1C/4I/7S 全採納——substring oracle／寫入側 21 條新測試）＋code-review agent（1C/3I/5S＋red lines 五條全 PASS——C-1 all-uninstall 補 muse disable＋monitor unload、I-1 codex exec rc≠0 fail-closed、I-2 apply_plan 第二層 dry-run 斷言、I-3 blueprint 指針、S 全補）＋judge 主 session 降級記錄；跨 session 轉交修復（fresh-worktree matcher parity 假敗＋收編三來源斷鏈＋check_single_source fixtures）；EP amendment 記 TC-6 P6-3 取代。既有缺陷記錄未修：hook_registration invariant 看不到 codex 註冊面（誤報孤兒 CRITICAL）。receipt＝references/s6-closing-receipt.md（含 audit/review 明細）。待：最終 commit gate→結案兩步。
<!-- SECTION:NOTES:END -->
