---
id: AIR-55
title: memory last-writer歸因sidecar（b）實作——telemetry投影＋hash腿＋actor schema
status: Done
assignee: []
created_date: '2026-09-09 04:54'
updated_date: '2026-09-09 05:31'
labels:
  - memory
  - telemetry
dependencies: []
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
P5裁決①實作（AIR-48定稿，提案檔裁決段）。範圍：memory_telemetry管線後加last_tracked_writer投影（JSON map：stem→{last_write_ts,source,session,actor}）＋content-hash驗證腿（consistent/unattributed_external/ambiguous三態；consistent禁叫verified）＋actor（kind＋root＋prompt＋leaf；session_id留join key）＋as_of時間戳。觀察項（非本卡）：watermark、(e)journal。驗收：sync-sources式機械驗證＋projection/verifier職責分離（verifier才說信多少）。規格源：ai-analysis/_tasks/_archived/09-08-carrier-misuse-definition/p5-writer-attribution-proposal.md裁決段。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 sidecar JSON map落地且有as_of
- [ ] #2 三態語義（consistent非verified）有機械驗證
- [ ] #3 actor雙欄＋prompt_id
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
歸因sidecar(b)落地：telemetry投影＋hash五態＋actor schema＋hook merge；ChatGPT-R1四修＋R2 migration全收斂；全倉263綠；commit air-55
<!-- SECTION:FINAL_SUMMARY:END -->
