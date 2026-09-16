---
name: stale-experiment-rerun
description: dated 實驗與「定案」都會錯——重跑當場 probe（symlink 判決被推翻實證）；工具失敗歸因須受控複測否證後才定案
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_e917b9f0-22e9-4192-98c4-c7c4b09fab87
---

user 對 AI 引用 8 天前實驗結論（08-29 registry symlink 不載入）並斷言「硬平台事實、不是設計選擇」後，直接要求「你全部再重跑一次實驗吧」——重跑**推翻**了舊判決（symlink 可載入；confound＝快照過期）。「定案」語氣不免錯。實驗型 spawn 派 flash agent（user：「派 flash agent 去做實驗」）。

**Why:** harness 平台短期內可能已改（loader/config 語義），且實驗本身可能有 confound——本例舊判決疑為「探針 mid-session 放入、未經真正新 session 即判不載入」的快照過期混淆；dated 實驗與 doc staleness 同性質（[[feedback_dispatch-reread-governing-docs]]、[[relay-claims-verify-current-state]]），load-bearing 架構前提建立在舊實驗上，錯了整個設計跟著錯。

**How to apply:** ①引用 dated 實驗前查日期，舊且 load-bearing → 主動重跑：檔案系統/行為 probe 當場做；startup-snapshot 相關行為（registry 載入等）由 user 開新 chat session、prompt 指示寫檔回報——creator-bound cron 不開新 session；restart+resume 對實檔會刷新快照（09-06 spawn 實測成功），判決載具以新 chat 最穩、判決證據用 spawn 嘗試本體而非錯誤訊息的枚舉文字。②實驗設計要分辨 confounder——快照外名稱直接 spawn 得 not found 是歧義負向；鐵證設計＝positive control 對照（實檔探針＋symlink 探針並放：只載實檔＝機制拒載、兩者皆載＝快照問題、皆不載＝快照沒刷新）。③重跑裁決前，舊定論標「待複驗」不再當既成事實引用。
