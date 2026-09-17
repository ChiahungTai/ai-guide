---
id: AIR-117
title: post-build 增設 memory 收尾腿——本弧池條目盤點＋即時蒸餾＋.agent-tmp 分類
status: Done
assignee: []
created_date: '2026-09-16 22:13'
updated_date: '2026-09-17 00:54'
labels: []
dependencies: []
ordinal: 102000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
弧的記憶足跡（-inflight 條目、.agent-tmp 證據/暫存、probe 殘留）目前等到結案蒸餾或夜掃才處理，0917 池 91 筆積壓即證據。在 post-build 收尾段加一步：盤點本弧新增/修改的池條目→即時蒸餾或標 terminal、.agent-tmp 本弧產物分類（證據留/用完清）、probe 殘留確認。與 commit 2.8 對帳、結案蒸餾互補不重複（時點前移）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 post-build skill 增步驟條文（含與 commit 2.8/結案蒸餾的分工邊界聲明）
- [ ] #2 以一個真實弧試跑：產出本弧 footprint 清單＋處置紀錄
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
post-build memory 收尾腿條文落地（footprint 盤點＋即時蒸餾/terminal 分流＋2.8/結案分工邊界）＋guides-refactoring 弧試跑（3 條 terminal 登記＋.agent-tmp 分類）；落地前審查閘＝主 session low-risk 分類（additive step）＋muse BI 審（P-1/P-2 澄清已套用）
<!-- SECTION:FINAL_SUMMARY:END -->
