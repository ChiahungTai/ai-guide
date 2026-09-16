---
id: AIR-25
title: memory 系統矯正四項——CC 對齊（gate 失敗模式／desc 契約／結案蒸餾／清償線聚）
status: Done
assignee: []
created_date: '2026-09-04 23:47'
updated_date: '2026-09-05 01:09'
labels:
  - memory-audit
  - hooks
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-05-memory-system-recalibration/ep.md
  - ai-analysis/_tasks/_archived/09-05-memory-system-recalibration/ep.md
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
09-05 診斷（CC 官方文檔對照）確診寫法＋distill 雙根因，四項矯正＋線聚政策落地。〔baseline：ai-rules 836c645〕〔已決策勿重辯：①gate 失敗模式改 CC 式——超限索引照寫＋exit 1＋錯誤訊息命令當下 session 縮（官方 memory.md:401-403）②desc 內容契約禁 commit hash／流水（hook 第三檢查）③結案即蒸餾掛弧生命週期（kanban 結案兩步第三動）④top-14 清償 ≤8K/條＋弧歸線聚（12-15 線，30 上限；不採 mega 條目／目錄分群／索引分節——條目數是 200 行載入上限的結構天花板）穩態 100-110 條／≤20K chars〕〔驗收：S1 超限寫出＋exit1＋行動訊息（測試釘）／S2 hook 擋 desc hash（含短 desc 仍擋）／S3 三掛點 rg 一致＋bundle 3/3／S4 水位 ≤20K chars／≤160 行＋_audit-state 記帳＋池副本 cmp 綠〕EP：ai-analysis/_tasks/09-05-memory-system-recalibration/ep.md
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
S1/S2/S3 已落地（S1：generator 超限寫出＋40 測試綠＋池副本 cmp＋停滯條目回索引可見；S2：hook desc hash 檢查＋三測試；S3：結案蒸餾第三動五掛點＋寫入第五問/desc 三不/承諾不進 memory＋bundle 部署 3/3 綠）。S4-P1/P1b 完成（14 檔 224K→75K −66%＋3 檔存量 desc）。剩餘＝S4-P2 弧歸線（55 project 條→12-15 線；chars 水位 23,133→目標 ≤20K 依賴此步；索引尺寸由條目數驅動——body 蒸餾不縮索引，EP 已勘誤）——建議新 session 依 EP S4 Phase 2 段執行。

P2 完成（agent 10 線＋主 session 半套修復 1 線）：條目 145→113、索引 18,205 chars/125 行 gate PASS（餘量 4,295）、零懸空、marker 清、EP 歸檔 done/。errs 路徑 CC 化後議→draft。agent 教訓：mem-distill 死於帳號級暫態，重試帶已知事實＋驗屍半套可收編。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 系統矯正四項全落地——gate CC 式寫出/desc hash 契約/結案即蒸餾五掛點＋寫入五問/清償＋弧歸線 11 線；池 145→113 條、索引餘量 163→4,295
<!-- SECTION:FINAL_SUMMARY:END -->
