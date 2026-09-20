---
id: AIR-146
title: >-
  bridge wait watcher——fan-in 包 wait、124 內部 re-arm、CollectionReceipt（AIR-135.7
  工具化承接）
status: Done
assignee: []
created_date: '2026-09-20 08:12'
updated_date: '2026-09-20 13:52'
labels: []
dependencies:
  - AIR-135.7
ordinal: 133000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**一句話**：寫一支值班程式（watcher），盯著背景 worker 做完事才叫醒 AI——中間不管跑多久，AI 都不用被吵醒。

**現在的痛**：AI 派長工給背景 worker 之後，系統每幾分鐘就把 AI 叫醒一次「還沒好、繼續等」——一小時的工被吵醒十幾次，每次都燒 token；夜間批量也照樣被折騰（0920 實證）。

**做完之後**：AI 派完工就去睡。值班程式接手盯場——worker 做完了，叫醒 AI 收結果；worker 疑似卡住，只通知、不亂殺不重派（處置權留在 AI）；其他時間靜悄悄。

```mermaid
flowchart LR
  subgraph 現況
    A1[AI 派工] --> B1[傻等迴圈]
    B1 -->|每隔幾分鐘| W1[叫醒 AI 問進度]
    W1 --> B1
    W1 -.-> F1[token 燒掉·工沒多做]
  end
  subgraph 落地後
    A2[AI 派工] --> W2[值班程式接手]
    W2 -->|做完| U2[叫醒 AI 收結果]
    W2 -.->|疑似卡住| S2[只通知·不殺不重派]
    W2 -.->|沒事| Z2[(AI 安穩睡覺)]
  end
```

**附註**（實作細節，不影響上面理解）：設計源＝SC 弧 codex 報告 job-mu9hmdar 轉交＋marshal 裁決；形態＝`scripts/bridge_waiter.py` 單顆包多工、動態等隔、worker／runtime 雙軸卡死判準、收工回執欄位沿用 AIR-135.7 AC#2、bridge CLI 版本 pin；狀態機四態為 frozen spec（轉移表見 AC）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 124→內部自動 re-arm、零 redispatch（真實歷史 job replay 驗證，H 級 oracle）
- [x] #2 fresh progress 調大下一 arm（×1.5 cap 20m）；runtime silence 跨 floor 僅產 stalled-advisory（exit 3），不 stop 不重派
- [x] #3 terminal completed 恰一次 collect、terminal failure 立即喚醒 caller；CollectionReceipt JSON 於 stdout（欄位＝AIR-135.7 AC#2 bounded receipt 投影）
- [x] #4 N-job fan-in 至最後一顆 terminal 才 completion
- [x] #5 restart／generation mismatch → unknown/reconcile 喚醒，禁自動 retry；missing/corrupt status fail-loud
- [x] #6 watcher 無 stop/judge/commit 路徑（代碼面保證）；bridge CLI 版本不符 fail-loud 附升級指引
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
bridge wait watcher 落地——fan-in 包 wait、exit 124 內部 re-arm 零 LLM 喚醒、動態 T、heartbeatAt/lastEventAt 雙軸 advisory、exit 2 四面貌重探分流、CollectionReceipt（AIR-135.7 AC#2 投影）、bridge CLI 版本 pin。AC#1 證據：T4 advisory 節制＋T5 collect 各 H 級真 job 實證（round 3 advisory 攔截後 job 自行完成＝節制價值活體驗證）；124-re-arm 面 I 級如實記錄（glm 靜默>10m 即 advisory 攔截，自然不可達）。fresh 審查 7 findings（1 Critical single-id 零 collect）＋followup 驗收 pass＋N1 gap 帶併修，44 測試＋全套 1075 綠
<!-- SECTION:FINAL_SUMMARY:END -->
