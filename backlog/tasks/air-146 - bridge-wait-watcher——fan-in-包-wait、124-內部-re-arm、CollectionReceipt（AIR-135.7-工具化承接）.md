---
id: AIR-146
title: >-
  bridge wait watcher——fan-in 包 wait、124 內部 re-arm、CollectionReceipt（AIR-135.7
  工具化承接）
status: To Do
assignee: []
created_date: '2026-09-20 08:12'
labels: []
dependencies:
  - AIR-135.7
ordinal: 133000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bridge 派工回收現況＝背景 shell fan-in wait，exit 124 每 arm 喚醒 caller LLM 重掛，正常長跑主 session 被迫反覆醒來（0920 批量實證）。SC 弧 codex 設計報告（job-mu9hmdar）轉交＋marshal 裁決（.agent-tmp/air-135/watcher/adjudication.md）落地：scripts/bridge_waiter.py 單顆 fan-in watcher——124 內部消化 re-arm（零 LLM 喚醒）、動態 T（T0=clamp(P50_prior/3,5m,15m)、fresh×1.5 cap 20m、stall 減半；prior 表 family×work-kind 內嵌常數）、卡死判準＝heartbeatAt/lastEventAt 雙軸（jsonl mtime fallback）、CollectionReceipt＝AIR-135.7 AC#2 bounded receipt 欄位投影（sink 驗收程序引用 bridge repo delegate-run-output「Receipt acceptance」節）、bridge CLI 版本 pin（啟動 probe fail-loud）、狀態機 running-fresh|stalled-advisory|terminal|unknown/reconcile 為 frozen spec（轉移表進卡，S 級 oracle）。generation 變＝reconcile 禁 retry；watcher 永不 stop/judge/commit。UX 北極星：正常長跑主 session 完全不醒；完成才醒、明確 stall 才醒、124 永遠不醒。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 124→內部自動 re-arm、零 redispatch（真實歷史 job replay 驗證，H 級 oracle）
- [ ] #2 fresh progress 調大下一 arm（×1.5 cap 20m）；runtime silence 跨 floor 僅產 stalled-advisory（exit 3），不 stop 不重派
- [ ] #3 terminal completed 恰一次 collect、terminal failure 立即喚醒 caller；CollectionReceipt JSON 於 stdout（欄位＝AIR-135.7 AC#2 bounded receipt 投影）
- [ ] #4 N-job fan-in 至最後一顆 terminal 才 completion
- [ ] #5 restart／generation mismatch → unknown/reconcile 喚醒，禁自動 retry；missing/corrupt status fail-loud
- [ ] #6 watcher 無 stop/judge/commit 路徑（代碼面保證）；bridge CLI 版本不符 fail-loud 附升級指引
<!-- AC:END -->
