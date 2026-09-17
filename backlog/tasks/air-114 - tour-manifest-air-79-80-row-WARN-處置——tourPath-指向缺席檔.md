---
id: AIR-114
title: tour manifest air-79-80 row WARN 處置——tourPath 指向缺席檔
status: Done
assignee: []
created_date: '2026-09-16 13:51'
updated_date: '2026-09-17 00:54'
labels: []
dependencies: []
ordinal: 99000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
0916 post-build tour corpus gate 回報 WARN 1：.tours/manifest.toml 的 [[delta_arc]] air-79-80（base beb86429 target 11fd0d73 quality=degraded）tourPath=.tours/delta/air-79-80.tour 檔不存在。AIR-80 demand-driven 契約下 pending row 無 tourPath 屬正常；帶 tourPath 而檔缺席＝異常態。處置二選一：materialize（code-reality tour materialize air-79-80——但 user 實證常不看 delta tour，預設略過）或 row 狀態修正（移除 tourPath／刪 row——弧已收斂多年期）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 處置落地後 code-reality tour_validate --manifest --repo . 重跑：WARN 0，或處置理由入卡 notes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
處置＝維持 manifest 原狀——卡前提查證不成立（tour 檔存在且已版控 a21ced6）；WARN 1 為 delta-corpus 結構提示非異常（tour_validate 源碼實證）
<!-- SECTION:FINAL_SUMMARY:END -->
