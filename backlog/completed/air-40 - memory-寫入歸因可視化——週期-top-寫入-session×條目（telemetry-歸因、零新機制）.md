---
id: AIR-40
title: Memory 寫入歸因——成功事件、複製去重與分量報告
status: Done
assignee: []
created_date: '2026-09-07 07:56'
updated_date: '2026-09-07 11:23'
labels:
  - memory
  - governance
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-07-memory-governance/write-attribution/ep.md
parent_task_id: AIR-42
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
目標：以唯讀 telemetry 還原 memory 寫入事件，供治理判讀。〔baseline：ai-rules f03d346〕
〔已決策勿重辯：零新 hook/閘門；週期落點 corrections-weekly，首跑成功後整合 skill，不改排程配置；實際 actor 取事件 session，originSessionId 只作來源參考；payload chars、可重建檔案 delta、索引 snapshot delta 分開，缺 before-image 不硬算；fork/side-chat 複製事件需 lineage+操作時間+input hash 查證，callID 可能改寫，不能按 session 或 callID 直接計數，也不能整批排除 fork 新工作；成功/失敗/未完成分開；大寫入不是違規，允許零問題〕
〔POC：現存 ZCode 只從 2026-08-16 起；有跨 session 相同 input/操作時間但 callID 不同的複製事件；既有 standup digest 有損不重用。證據見母任務 evidence/README.md〕
〔驗收：成功操作可逐筆追源、複製與未知歸屬不污染確定排行、單位分量清楚；真實首跑含覆蓋限制與誤差；已知大寫入可還原但不要求找出違規；零新增寫入閘門；新增 collector/測試/週報接線按 EP 落地〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 成功、失敗與未完成分開；actor 來自事件，origin 不當作者歸因
- [ ] #2 fork/side-chat 複製事件與真正重複操作可區分；無法裁決的獨列 unknown
- [ ] #3 payload、可重建檔案 delta、index snapshot delta 分開；缺前態明示 unknown
- [ ] #4 ai-rules 真實首跑與抽樣事件對帳，允許零違規；corrections-weekly 入口與索引同步
- [ ] #5 不改 hooks/、不動 memory 池與排程配置
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 成功寫入歸因全弧閉：S1 collector（codex，TDD 11 tests）→S2 投影分量（TDD 18 passed＋真池首跑 385 writes/9 folded evidence）→S3 corrections-weekly 三職接入（實跑驗證 index_delta 流量≠存量）；流量非品質、違規抽驗留 LLM
<!-- SECTION:FINAL_SUMMARY:END -->
