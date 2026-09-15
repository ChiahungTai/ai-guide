---
id: AIR-97
title: MOS-105 實作：Muse 控制缺口補強——防護 hook 移植＋bundled 去重＋capability 探測＋清理
status: Done
assignee: []
created_date: '2026-09-15 10:40'
updated_date: '2026-09-15 11:06'
labels: []
dependencies: []
references:
  - muse-plugins/tool-governance/README.md
ordinal: 82000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把 ZCode 端已有的「攔 python heredoc 寫檔」防護閘移植成 muse plugin hook（bash-write-guard），並宣告 ai-guide skills 對 muse bundled skills 的優先序、探測 muse hook 契約支援範圍、清掉四個舊規則時代的 .bak 殘留。EP 由 mosaic 側研究定稿（EP：/Users/ctai/Github/mosaic_alpha/ai-analysis/_tasks/09-15-muse-control-gap/ep.md，本地複本指紋 8f16bcd1c8fb09ca），已過三輪獨立覆核＋四項 POC，user 拍板開工。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 S1：deny/allow/非法 stdin 三 fixture 全綠＋早退<100ms／全路徑<1000ms＋install 後 inspect trusted_enabled；S2：deploy 後優先句 rg 命中=1＋registry 文檔在位＋config dirs .bak 零殘留；S3：EVIDENCE.md 四能力 verdict 齊＋原始輸出存檔＋tool_name 收斂；N2：四 .bak mv 隔離有記錄
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide EP 載 c8bb0d3；build 起點 HEAD=b68b7d0（EP 後另有 AIR-91/95/96 commits，git 弧邊界以 build 起點為準）〕
〔已決策勿重辯（三輪獨立覆核 GLM×2＋codex＋四項 POC 收斂，user 2026-09-15 拍板）：
① 段落順序 S0→S3→S1→S2——deploy 殿後；S2 gate＝git status --short -- rules/ ai-development-guide.md 與 deploy_agents.py 併一條命令鏈；S2 句子先 commit 再 deploy（gate 自絆修正）
② S2 優先句落 ai-development-guide.md「Session 開場導引」（harness-generic 措辭）；registry 文檔放 muse-plugins/tool-governance/（含「最後驗證依據」欄位），不進 rules/
③ Muse hook crash＝fail-open——S1 deny 契約須 in-script 全路徑顯式 || deny；兩段式 fail-closed：不可分類工具 allow、入 shell 路徑後不可判讀／crash→deny
④ S3 矩陣：PostToolUse／Stop=supported、matcher=rejected（POC 已證）；updatedInput、exit-非零 hook 行為、timeout 逾時語義補測；bash tool_name 由 stdin-dump live 收斂
⑤ S3 diag 與 S1 guard 皆 user-scope install，checkpoint 式（install 後向 user 出示 inspect trusted_enabled）；diag 用完即 uninstall
⑥ N2：四個 .bak 全無 git 歷史→mv 隔離 .agent-tmp/mos105-cleanup/（EP 原 rm 依 user 裁決改 mv，弧末 rm）
⑦ 雙 hook 疊加 overhead（65–125ms）與無 per-repo opt-out 記入 README 已知事項
⑧ 範圍凍結：H2／H3／H4／H5／N1 不做；僅 muse 端（codex＝AIR-95 另卡）
⑨ 驗證載體＝EP 定義 fixture／rg／validate 命令（無 pytest 產物；／audit-test 不適用——EP 收尾載明）
⑩ mosaic EP commit 仍 pending——本卡以本地複本（sha256 前 16 碼 8f16bcd1c8fb09ca，274 行）為實作源，結案前 mosaic 側須落 commit 對帳〕
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
S0→S3→S1→S2 全段完成（順序依 user 拍板 v3）。S3：tool_name="bash" 收斂、exit-非零=fail-open、timeout 無截斷、updatedInput decision 層接受（EVIDENCE.md）。S1：bash-write-guard 五 fixture 綠＋13–465ms＋install trusted_enabled＋更新三步生命週期（改源→update→approve）實證。S2：優先句入 guide 開場導引（commit 6f0後補 hash）＋deploy 3/3＋rg muse=1/zcode=1＋registry.md（bundled 五對當日 ls 實測）。N2：四 .bak mv 隔離 .agent-tmp/mos105-cleanup/（兩大檔 diff 實證互為副本、同名合併無損）＋config dirs 斷言歸零。Live E2E：deny/allow 雙路徑活體通過（job-mu2k6djj-uch0sp）。待辦：EVIDENCE live 段落 commit（待 user OK）；MOS-105 卡結案在 mosaic 側（EP commit 仍未落）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
MOS-105 實作完成（S0→S3→S1→S2）：bash-write-guard hook live 端到端 deny/allow 雙路徑實證、bundled 優先句 deploy 後 rg=1＋registry 建檔、S3 契約矩陣齊（tool_name=bash／fail-open／無 timeout 截斷）、N2 四 .bak 清理歸零。commits 0a6a933→5852e55→cf74a2a；EP 宿主 mosaic（MOS-105 卡結案在 mosaic 側）。
<!-- SECTION:FINAL_SUMMARY:END -->
