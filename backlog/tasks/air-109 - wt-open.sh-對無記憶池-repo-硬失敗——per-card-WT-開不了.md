---
id: AIR-109
title: wt-open.sh 對無記憶池 repo 硬失敗——per-card WT 開不了
status: Done
assignee: []
created_date: '2026-09-16 05:29'
updated_date: '2026-09-16 05:29'
labels:
  - infra
dependencies: []
references:
  - scripts/wt-open.sh
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
southchariot 動卡跑 wt-open.sh 直接死在「primary 記憶主體不存在」——腳本宣稱 repo 無關但硬性要求 .agents/memory 在場。修法＝池拓撲改 opt-in（primary 無 .agents/ 即跳過池 symlink），已修在 working tree，與卡同 commit 結案。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide main cfdb1ac〕〔已決策勿重辯：①池拓撲改 opt-in——primary 無 .agents/ 目錄即整段跳過池 symlink 建立＋解析驗證迴圈，info 提示不 die；採池 repo（ai-guide 自身）行為不變 ②.git/info/exclude 的 .agents/memory 條目冪等追加維持無條件（無害且向前相容未來採池）③斷鏈 die 語義只在採池 repo 保留〕範圍：scripts/wt-open.sh 兩處 gate（池 symlink 建立段＋解析驗證段）——已實作於 working tree，與卡同 commit 結案。驗收：①無 .agents/ 的 repo（southchariot）wt-open 全鏈 ✅ 完成並開出卡 WT（活體已證：reuse path 重跑通過、identity contract 落盤）②採池 repo 行為不變（gate 條件不觸及既有分支邏輯）。
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
池拓撲改 opt-in——southchariot 活體驗證 wt-open 全鏈通過（reuse path 冪等），採池 repo 零觸及。
<!-- SECTION:FINAL_SUMMARY:END -->
