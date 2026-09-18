---
id: AIR-126
title: 治理安裝後防護預設在線——hooksPath 檢查補面＋monitor 未裝顯性警示
status: Done
assignee: []
created_date: '2026-09-17 15:08'
updated_date: '2026-09-18 02:29'
labels: []
dependencies: []
references:
  - governance/install.py
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
五面安裝器裝完後，兩道防護預設是關的：控制面 guard 要每個 clone 手動 git config core.hooksPath（新 clone 裸奔）、--surface all 不裝 monitor（健康警鈴沒開）。這卡讓安裝器主動檢查這兩項並顯性警示，把看不見的 fail-open 變成看得見的。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 #1 未設 core.hooksPath 的 clone 跑 install/check 主動報「guard 未啟用」顯性警示(非沉默)#2 --surface all 完成輸出列 monitor 缺席＋一行後果與裝法#3 新行為有測試(修前紅修後綠)#4 README 同步
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@f892c344〕〔已決策勿重辯：①五面架構不變——加檢查/警示面，不重寫 installer②hooksPath 仍是 bootstrap 清單獨立項語義（governance/README.md:97），但 install/check 結尾必須主動偵測未設並顯性警示（看不見的 fail-open→看得見）③monitor 仍是顯式排程面，但 --surface all 完成輸出必須列「偵測網缺席清單」（monitor 未裝＋其後果）④源證據＝0917 重構弧全域審查 muse intent 腿 I-1/I-2＋rg 實證（install.py:493-495 all-install 不含 monitor；governance/ 內 hooksPath 僅 README 提及）〕範圍——改：governance/install.py（install/check 結尾報告）、governance/README.md；可選：新增 --surface git 檢查面。AC 見卡面。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Receipt（AIR-105 四欄）：classification=standard（installer 警示 info 面；退出碼契約凍結）｜review=bi——muse approve（job-mu69k3h3-rx92ha）＋codex finding 已修 41eb635b（無法判定改 fail-visible 對齊 bootstrap G3）｜session-freshness=fresh｜deployment-surfaces=healthy（repo-local install.py＋README）；殘餘缺口 4 項列 final report 待 user 裁 follow-up
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
投放預設態顯性化——hooksPath/monitor 警示進 install/check 完成輸出＋README fail-open 聲明；新 clone 模擬全鏈行為表落地
<!-- SECTION:FINAL_SUMMARY:END -->
