---
id: AIR-45
title: context 統一生命週期機制——觸發保證×層級優化×instruction-*重構（blueprint）
status: Done
assignee: []
created_date: '2026-09-08 04:25'
updated_date: '2026-09-08 12:33'
labels:
  - memory
  - governance
  - context
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/_tasks/_archived/09-08-context-lifecycle-unification/ep.md
  - ai-analysis/_tasks/_archived/09-08-context-lifecycle-unification/ep.md
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
統一 context 讀取機制（座標系＋投影＋觸發文法＋查詢紀律）＋完整生命週期（掃描/歸類/精煉/淘汰）＋層級軸（user floor 收斂／project 層重整——mosaic root 42.7K 主案）＋instruction-* 四 skill 重構承載。〔baseline：d90f37d〕〔已決策勿重辯：①載體分立——rules 不搬 memory pool；②生命週期四動＝機制本體；③觸發保證（有需要就觸發）＝關鍵需求、desc 用語＝觸發面（情境句領頭）；④層級軸一等公民（mosaic 目錄分層已 OK 為前提、root 有改善空間）；⑤instruction-*.writing/init/clean/sync 承載機制不另創；⑥不向後相容；⑦draft-3 併 S3 吸收（座標系溶解 A/B）；⑧memory 寫入哲學保留〕〔驗收：SM-1~9（EP Scenario Matrix）；四端載入面機械驗證（部署後探針）；floor 預算與池成長脫鉤；EP=ai-analysis/_tasks/_archived/09-08-context-lifecycle-unification/ep.md（S0-S6 blueprint）〕
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
blueprint＋S0-S6 最小範圍全落地（d00bfe2）：(a) 採B（載入 8.9× 省量）、muse no-mechanics 變體＋per-target 50KiB gate（原始痛點 64KiB 截斷解決）、desc 文法五條入寫入紀律、spine 落地、池收斂 gate FAIL→PASS 20,153、codex live SM-1 12/12、三輪審查閉環；user 北極星（稀缺性分層）入 EP 進度結算。殘餘移交：B 上線切換＋catalog 探針→AIR-48（P3/驗收⑤）；mosaic 層級軸→mosaic 側 session。dogfood 傘＝AIR-48。
<!-- SECTION:FINAL_SUMMARY:END -->
