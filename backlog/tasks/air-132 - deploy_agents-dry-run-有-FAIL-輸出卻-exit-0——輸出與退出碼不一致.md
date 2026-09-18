---
id: AIR-132
title: deploy_agents --dry-run 有 FAIL 輸出卻 exit 0——輸出與退出碼不一致
status: Done
assignee: []
created_date: '2026-09-18 02:34'
updated_date: '2026-09-18 04:22'
labels: []
dependencies: []
references:
  - scripts/deploy_agents.py
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
新 clone 跑 --dry-run 明明印 FAIL 卻回報成功（exit 0），自動化會誤判綠燈。對齊 fail-loud：有 FAIL 就該非零退出。發現點＝AIR-126 收線的新 clone 模擬（fake HOME 實查）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 模擬未裝 skills 母鏈的新 clone 跑 --dry-run：輸出 FAIL 時 exit 非零（修前紅修後綠）
- [ ] #2 正常環境 --dry-run 仍 exit 0（零回歸）
- [ ] #3 README/文檔若有 dry-run 行為描述同步
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@0f6035c8〕〔已決策勿重辯：①fail-loud——preflight 有 FAIL 乾貨就非零退出（dry-run 不安裝、只檢查的語義不變，只修退出碼契約）②輸出契約不動（FAIL 行照印）③範圍限 scripts/deploy_agents.py 的 dry-run 路徑與其測試④來源＝AIR-126 新 clone 模擬實查（既存 TC-3 行為）〕範圍——改：scripts/deploy_agents.py（dry-run 退出碼）、tests/（dry-run 測試）；文檔若有描述同步。AC 見卡面。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
審查 disposition（bi）：症狀根因改寫——deploy_agents 本體已 fail-loud（AIR-105 S7，10/10 FAIL 印點有非零出口，muse 逐點核對）；原觀測「FAIL＋exit 0」根因＝caller 層 installer dry-run 吞碼（codex high，已修＋回歸測試）與/或 shell pipe 遮蔽（機制重現證實；當時命令 transcript 未保留，muse F5 如實記）。交付＝零 source 改動於 deploy_agents＋subprocess 契約測試＋caller 修復。

S 結算 Receipt（AIR-105 四欄）：classification=boundary（installer 退出碼契約＋TC-11 串接）｜review=bi——muse 通過 5 low（job-mu6fimgo）＋codex NO-GO 修入（caller 吞碼 high／AC 對齊／vacuous guard；job-mu6fimjh）｜session-freshness=fresh｜deployment-surfaces=healthy（install.py 落 main 即生效）
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
症狀根因改寫：本體已 fail-loud，真缺陷＝installer dry-run 吞碼（已修＋回歸測試）；subprocess 契約測試釘死
<!-- SECTION:FINAL_SUMMARY:END -->
