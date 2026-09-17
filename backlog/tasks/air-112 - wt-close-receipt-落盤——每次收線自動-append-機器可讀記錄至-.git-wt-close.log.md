---
id: AIR-112
title: wt-close receipt 落盤——每次收線自動 append 機器可讀記錄至 .git/wt-close.log
status: Done
assignee: []
created_date: '2026-09-16 13:50'
updated_date: '2026-09-17 00:54'
labels:
  - governance
dependencies: []
references:
  - scripts/wt-close.sh
ordinal: 97000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
wt-close.sh 每次執行自動落一行 receipt（時間/WT/branch/結果）到共享 .git/wt-close.log，收線證據不再依賴 session 暫存輸出——AIR-77 首例 receipt 為人肉補記（見該卡 notes），此卡讓未來收線自帶證據。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 執行 wt-close（ephemeral fast-path 即可）後 .git/wt-close.log 出現對應 receipt 行（含 mode/time/wt/branch/結果）；git status --porcelain 不顯示 .git/wt-close.log；模擬 log 不可寫（chmod 000）→ wt-close exit code 與行為不變、stderr 出現警告；rg 全 repo 無殘留「receipt 待補記」措辭（本卡落地後對時）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 4ad660e〕〔已決策勿重辯：①log 落點＝.git/wt-close.log——.git 內容永不進版控（免 gitignore）、共享 .git 跨 WT 集中、存活於 WT 移除；代價＝不隨 clone 同步（machine-local，刻意）②append-only 一行一筆：時間戳＋mode（preflight|full）＋WT path＋branch＋結果摘要；失敗調用也記（failure receipt）③log 寫入失敗不得改變 wt-close 的 exit code（僅 stderr 警告——收線本身是主體）④首例人肉 receipt 已存 AIR-77 卡 notes，本卡不做歷史回填〕範圍：scripts/wt-close.sh 加 receipt append（preflight 與 full 都寫、mode 欄位區分）；測試接線（有則更新、無則最小 shell 斷言）；workflow.md wt-close 節＋structure.md/索引用「receipt 待補記」措辭改「每次執行自動落盤 .git/wt-close.log」。
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
wt-close receipt 落盤機制（.git/wt-close.log 五 terminal 點＋die failure receipt）；throwaway clone e2e＋chmod 000 行為不變實證；首筆機器 receipt 已在場
<!-- SECTION:FINAL_SUMMARY:END -->
