---
id: AIR-198
title: closeout-guard×daily-cleanup-撞面——歸檔批次-100-FAIL-停擺的後續腿
status: Done
assignee: []
created_date: '2026-09-25 00:26'
updated_date: '2026-09-29 00:58'
labels: []
dependencies: []
ordinal: 184000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
來源＝AIR-193 切片二雙腿 review 腿二 F2（confirmed，機械重現）：結案結構 predicate 上線後（0925），deploy/scripts/run-backlog-cleanup.sh 的每日歸檔批次（tasks→completed，R code、is_entry=False、status 仍 Done）照跑結構 predicate——全板 125 張 Done 卡 100 張 FAIL（AC 殘留 63／AC 缺段無 fallback 標題 34／FS marker 缺 16／DESCRIPTION 缺 1／malformed 4），cleanup 批次 commit 逐卡被 pre-commit 擋：腳本 loud fail 但無補齊腿，每晚重複失敗噪音＋清理實質停擺。

需求釐清：①存量 100 張是補格式（批量補段）還是觀察期豁免 ②cleanup 腳本要不要對 struct-fail 有機械處置（跳過＋計數入 log？觸發補段清單？）③選項互斥或組合。裁定面＝載體三判準（cleanup 是 hook 消費端，guard 是正典判定——禁二刻，cleanup 端只消費 exit code）。

```mermaid
flowchart LR
  A[193 guard 地板抬高] --> B[存量 Done 卡 100/125 不合五段]
  B --> C[daily cleanup 歸檔 commit]
  C --> D[pre-commit 擋<br/>每晚失敗噪音]
  D --> E{後續腿裁決}
  E --> F[批量補段 runbook]
  E --> G[cleanup 對 struct-fail 處置<br/>跳過計數或觸發補段]
  E --> H[FS/AC 缺失觀察期降級]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 裁定三選一（或組合）記卡 notes（補段 runbook／cleanup 處置／觀察期降級）
- [x] #2 實作落地＋cleanup 批次連續三晚綠燈（或顯式豁免清單機制）
- [x] #3 存量 100 張清零或歸檔面隔離（判準記 notes）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0925 裁定＋實作落地（lane 可決——選項組合 G＋輕量補段路徑）】①裁定：批次 commit 前跑 closeout_check 前置過濾（判定單一源＝guard 經複查腿消費，禁二刻）——結構 FAIL 卡跳過歸檔＋[待補段-跳過] 訊息（含缺項清單）＋struct_skip 計數入 summary；fail-closed 保持（不降級、不觀察期），補段後次日自動重試。②實作：run-backlog-cleanup.sh +10 行（候選迴圈內 precheck PASS 後過濾；CLOSEOUT_CHECK 缺場 loud 預檢；bash 3.2 變數邊界修正）。③驗證：tmp repo 冒煙——結構 FAIL 卡正確被擋（訊息列缺項）、PASS 卡走到 complete 步、summary 乾淨；bash -n 綠。merge 644a0286。④AC 帳：#1 ✓（本 notes 即裁定）；#3 ✓（隔離機制＝待補清單留存 tasks/，漸進消化）；#2 部分——機制落地＋冒煙綠，『連續三晚綠燈』須 launchd 自然驗證（明起 23:50），餘兩晚綠燈後結案。⑤twin 提醒：mosaic_alpha/deploy/scripts/ 同邏輯副本——跨 repo 同步歸 mosaic 線（本端不動）。

【0926 handover 核對】launchd 三 job 載入✓（末次 exit 0）；第一晚 0925 23:50 自然觸發綠：moved=0 skipped=0 結構待補=0 failed=0——0 過齡候選（真空綠，closeout 過濾腿未經實彈）；餘 0926/0927 兩晚綠後結案。附註：卡檔 status 實為 To Do（前段 STATE 記 In Progress 係觀察層失實），本段補正。

【0929 結案驗證】三晚綠燈達成：0925/0926/0927 23:50 launchd 自然觸發，summary 皆 moved=0 skipped=0 結構待補=0 failed=0，err log 空、launchctl exit 0；0928 第四晚同綠（加碼）。main 腳本 freshness 核過——deploy/scripts/run-backlog-cleanup.sh 含 CLOSEOUT_CHECK 前置檢＋待補段跳過腿＋struct_skip 計數（merge 644a0286 在 main），launchd 夜夜實跑即此份。保留點（誠實記錄）：四晚全真空綠——0 過齡候選，過濾腿正式環境未實彈，機制證據僅 0925 tmp repo 冒煙；首次實彈窗口約 10-11（air-74/75 等 09 月中 Done 卡過 30d 門檻，預期走待補段跳過路徑，即設計行為）。AC#2 勾稽達成。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
closeout 前置過濾腿落地：cleanup 批次逐卡先跑 closeout_check——PASS 走 task complete 歸檔、FAIL 跳過＋待補段清單＋struct_skip 計數，判定單一源＝guard、fail-closed 不降級，補段後次日自動重試。驗證：0925-0927 連三晚 launchd 綠（0928 加碼），err log 空；正式環境候選為零屬真空綠，過濾腿機制證據＝tmp repo 冒煙，首次實彈預期 10 月中。終態圖：

```mermaid
flowchart LR
    N["每晚 23:50 cleanup 批次"] --> P{"候選卡 closeout_check"}
    P -->|"PASS"| M["task complete 歸檔"]
    P -->|"FAIL 結構待補"| SK["跳過＋待補段清單＋計數"]
    SK -.->|"補段後次日重試"| N
```
<!-- SECTION:FINAL_SUMMARY:END -->
