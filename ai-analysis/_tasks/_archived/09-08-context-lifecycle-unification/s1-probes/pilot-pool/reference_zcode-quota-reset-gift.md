---
name: reference_zcode-quota-reset-gift
description: ZCode 5h 額度 reset gift 機制——server-side 池逐次發放（各帶 expire_at）＋client 每
  5-10 分鐘輪詢索取，非日循環；API 在 /api/v1/coding-plan/reset/*
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_24d04571-9498-4580-905d-dfd9e3a97765
---

ZCode「可重置額度」（reset gift：把 5 小時／週額度提前重置的禮物）機制，09-08 從 `/Applications/ZCode.app/Contents/Resources/app.asar` 逆向確認：

- **資料模型**：server 維護「可用重置池」——`GET /api/v1/coding-plan/reset/status` 回 `available_five_hour_resets: [{expire_at}]`（陣列，每個 gift 各自帶死線）、`available_week_resets`、`latest_*_reset_history: {used_at}`、`has_unread_history`。
- **給予**：client coordinator 每 10 分鐘輪詢（minified 常數 `YUe=10*6e4`，綁 visibilitychange、視窗隱藏暫停），POST `/opportunity`（body 帶 `idempotency_key` ≤64 字元）向 server 索取；server 回 `{granted:true}`（池內加 item）或 business code 3301 帶 `next_try_at`（client 排 `max(next_try_at, now+5min)` 再試，`JUe=5*6e4`）；HTTP 429＝throttled。**發放節奏／TTL 全在 server 政策，客戶端碼不可見——不是每天計算 cycle**（asar 內「每日额度」字串屬 MCP 預設插件額度，另一功能）。
- **使用**：POST `/use` body `{idempotency_key, reset_type: FIVE_HOUR|WEEK}` → `{used:true}`；client 樂觀更新 nextResetAt＝now+5h，state 走 available→processing→completed 後刷 entitlement；POST `/history/read` 標已讀。
- **UI gate**：額度滿載（quotaFull）時整個隱藏（暗示 server 傾向在 5h 池吃緊時發放）；機會到期前 180 秒進 urgent 提醒、過期未用即消失；多個 gift 顯示「×N」＋最快到期。i18n key 前綴 `codingPlan.quotaReset`（zh「获得{count}次重置额度」＝收到禮物通知）。授權 zcode JWT＋maas JWT（錯誤碼 `coding_plan_reset_*_jwt_required`）。
- **考古技術**：Electron app.asar 是未壓縮拼接格式——`rg -aio ".{N}關鍵詞.{M}" app.asar` 直接搜 minified JS 有效；minified 變數（如 `xC="/api/v1/coding-plan/reset"`）靠「字串值反查」定位。

關聯：[[reference_zcode-platform-facts]]
