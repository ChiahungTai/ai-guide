---
id: AIR-23
title: illustrate 報告殼 template 化（可折疊 sidebar）
status: Done
assignee: []
created_date: '2026-09-04 00:31'
updated_date: '2026-09-04 03:29'
labels:
  - skills
  - illustrate
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-04-illustrate-shell-template/index.html
  - ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/index.html
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
殼布局/視覺/互動約束從 illustrate-html-mode.md prose 抽成共用 template（skills/_common/illustrate-report-shell.html＋可折疊 sidebar）。baseline 46005e2。已決策勿重辯：template 落 _common 非 archify repo、承襲 AIR-13 殼既有視覺決策（dark/NB 視口/?embed=1/首屏規則）、折疊禁重載 iframe、降級=同 template degraded slot、不做產生器、done/ 舊殼不動。驗收：slot 標記齊全＋rg 殘留掃描（布局值只住 template）＋/consistency＋本 task 殼（首個消費者）渲染/互動/視覺驗收。EP：ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/ep.md
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
共用 Report Shell template、折疊/首屏/降級機制與三處 skill pointer 已落地；post-build 雙 context review 的 AIR23-01..11 全數 resolved。驗證：node verify-shell.cjs exit 0（39 passed/0 failed，含 hostile hash、reload restore、1024px、projection SHA）；獨立視覺盲驗 3/3 PASS；7 份 docs consistency 0 failures。
<!-- SECTION:FINAL_SUMMARY:END -->
