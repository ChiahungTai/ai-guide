---
id: AIR-101
title: 開發流程重設計實作——依風險安排審查、checkpoint 恢復、成果視圖（workflow redesign EP S1–S4）
status: To Do
assignee: []
created_date: '2026-09-15 15:49'
updated_date: '2026-09-15 15:49'
labels:
  - governance
  - skills
dependencies: []
ordinal: 86000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把已三輪外部審查 verified 的開發流程重設計 EP 落地：review 改依風險配置、中斷後 checkpoint 恢復、成果視圖與結算。現在到哪：EP 計畫定稿、等實作。本卡是 EP owner 卡，S1–S4 依 manifest 逐段實作與驗收。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 4fc5caa（main、clean、單 WT）；EP 實作基線 b4a3019 已核對在場〕
〔已決策勿重辯：①EP（ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md）四段計畫已 muse 三輪外部審查＋主 session N1–N8 外審全收斂 verified——實作照 manifest 與各段修改要點執行，不重辯計畫；實作前依 EP 條款 rg 重定位錨點（行號只作起點）②S1/S2 是同一政策切換、未全接完不 deploy；主線中間不插他卡改同檔——AIR-76 六檔落檔先於 EP S1 完成（同檔避撞）③AIR-60 部分承接（09-15 對帳已記兩卡 notes）：EP S3 承接其 rehydration 單一源骨幹、EP S2 承接段落結果寫 EP 進度方向；AIR-60 保留授權失效條款／雙 lens closure／segment receipt 自算，AIR-101 結算時回寫其 Plan/AC ④HTML 互動／視覺驗證本輪延後（user 明示於 EP），不阻擋交付 ⑤docs mode——若發現必須改 .py/.toml/.sh 才成立，先回報擴範圍不得偷渡 ⑥AIR-91/96 定稿的 catalog/generator 不動〕
範圍：EP manifest S1–S4 產品寫入集合（S1 review-engine＋workflow-review-pattern；S2 主鏈十二檔；S3 task-recovery.md 新檔＋恢復入口五檔；S4 殼/metadata-sync/deep-work/索引導航）＋AIR-76 前置落檔；驗證依 EP 各段驗證與完成條件（static＋behavior＋oracle）。
〔執行形態：marshal 調度（L1），worker 分段派工；review 鏈＝codex+muse 外審→5.3 judge→user commit consent；三線（air-101/air-98/air-63）檔案正交已驗證，序列化 ff 合併回 main〕
<!-- SECTION:PLAN:END -->
