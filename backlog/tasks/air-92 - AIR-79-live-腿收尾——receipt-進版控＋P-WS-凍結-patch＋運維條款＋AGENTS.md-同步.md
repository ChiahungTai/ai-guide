---
id: AIR-92
title: AIR-79 live 腿收尾——receipt 進版控＋P-WS 凍結 patch＋運維條款＋AGENTS.md 同步
status: Done
assignee: []
created_date: '2026-09-14 01:36'
updated_date: '2026-09-14 02:05'
labels: []
dependencies: []
references:
  - >-
    ai-analysis/_tasks/done/09-12-muse-memory-governance-plugin/poc/live_receipt_20260914.md
ordinal: 78000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕muse memory 防護閘的 live 驗證已全綠（mosaic 端跑完），這卡把四件收尾落到本 repo：證據進版控、一個小 patch、寫兩處文檔。做完後每次升級 governance plugin 都記得重新 approve。

〔baseline：ai-rules main @ 016eff9〕證據源＝ai-analysis/_tasks/done/09-12-muse-memory-governance-plugin/poc/live_receipt_20260914.md（untracked，live 驗證 L1-L6 全綠 2026-09-14）

〔已決策勿重辯：①approve 綁 definition_hash（content update→hash 變→hook 停火＝fail-open 窗口，形態是 update 後非 install 後；重新 approve 即恢復）②O7 修正：plugins list 的 hooks-require-review warning 是常駐雜訊非 approval 訊號，真訊號＝inspect --json 的 runtime_capabilities[].status③P-WS 凍結：resolver 以 .cwd 為權威首選（live stdin 無 workspace/host_workspace 欄），patch 文本已在 receipt 禁重新設計④mosaic 側已收口勿越界⑤L4 收緊是 open user 裁決項非本卡範圍〕

〔驗收：①receipt 進版控（具名 add，working tree 他弧髒檔禁掃入）②P-WS patch 落 muse-plugins/memory-governance/hooks/muse_memory_governance.sh＋resolver 測試補進 tests/test_muse_memory_governance_plugin.py 既有 seam（:306/:659 附近）＋該檔 targeted＋full suite 綠③README 運維條款三條（update 後必 approve／health check assert trusted_enabled／O7 措辭修正）④AIR-79 卡 notes 補 live 腿結算＋四 gate 終局＋ai-rules AGENTS.md Muse memory 段 O7 同步⑤rg "workspace // .cwd" 舊鏈零殘留〕
<!-- SECTION:DESCRIPTION:END -->

<!-- SECTION:NOTES:BEGIN -->
09-14 審查修復批：
- 驗收⑤掃描範圍解讀：活碼（hooks/tests/README）零殘留；receipt:27 屬凍結提案證據文本不在掃除域。
- receipt 隨結算 commit 具名納入（F1——凍結主張的證據錨點必須進版控）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AIR-79 live 腿收尾閉合——receipt 進版控＋P-WS 凍結（cwd 權威首選，receipt 逐字）＋4 測試 RED→GREEN（full 420 綠）＋README 運維三條款＋AGENTS.md legacy 語義收斂；dual 審查 fresh GO＋primed 🔴 AGENTS.md 已修；judge GLM-5.3 全數認可 GO
<!-- SECTION:FINAL_SUMMARY:END -->
