---
id: AIR-42
title: Memory 知識治理改善——寫入歸因、讀取觀測與載體分流
status: Done
assignee: []
created_date: '2026-09-07 08:44'
updated_date: '2026-09-07 11:23'
labels:
  - memory
  - governance
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-07-memory-governance/ep.md
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
目標：以可信 telemetry 改善 memory 的知識分流，讓下次情境能召回已確定事實與約束。〔baseline：ai-rules f03d346〕〔已決策勿重辯：做過哪些事由 backlog/git 承載；沿用 AIR-40/41；不加 hook 或寫入閘門；母卡只協調與驗收，不重複子卡實作；順序 AIR-40→AIR-41→內容分流子卡；AIR-39 已完成作既有基線〕〔驗收：子卡 EP 與證據可追溯、首跑量測有覆蓋限制、分流樣本判讀可全部保留、不以刪除量或違規數驗收〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 子卡與 EP 完整連結，依賴無循環
- [ ] #2 寫入、讀取與分流首輪證據分開陳述；未知不冒充零
- [ ] #3 不增加寫入閘門，結案依子卡行為驗收而非計畫存在
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 知識治理三弧全落地：AIR-40 寫入歸因 telemetry（22 tests＋weekly live）、AIR-41 body Read 觀測（13 tests＋reads live＋dual review 修正輪）、AIR-42.1 載體分流校準（advisory 10 條＋Q2/固化/blocker/cluster 規則修訂）。證據分立陳述（寫入/讀取/分流三份 evidence）、未知不冒充零（window_shortfall/unpaired 揭露）、無新閘門（hooks/ 零變更）。advisory 遺留 user 裁量：退出候選 1＋指針保留 1＋遷移候選 1（均未動共享池）。歸檔 ai-analysis/_tasks/_archived/09-07-memory-governance/
<!-- SECTION:FINAL_SUMMARY:END -->
