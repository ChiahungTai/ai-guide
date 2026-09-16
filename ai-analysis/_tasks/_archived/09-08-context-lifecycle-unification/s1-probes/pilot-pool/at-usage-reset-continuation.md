---
name: at-usage-reset-continuation
description: usage 排程分流：/usage-ping 純叫醒 vs /at 接任務＋/at 開頭判讀（排程非立即執行）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 176db9fb-81c1-4c9c-8e9e-1434e91d4f01
---

5h 窗口用盡→估重置→排程→接續：「叫醒」與「接續」不同需求；`/at HH:MM` 開頭＝排程請求不是執行令。

> merged_from: feedback_at-prefix-schedule-not-execute, 2026-09-07 cluster-merge wave

## 工具分流（original: feedback，keeper 本體，08-18 用戶定調）

- **`/usage-ping HH:MM`**＝純叫醒：只寫時間不帶任務；階梯 3 發 one-shot 有界重試，落地即確認；**單 call 紀律**（落地一行零工具）；語音走 Stop hook sentinel。定義見 `skills/usage-ping/SKILL.md`
- **`/at HH:MM 任務`**＝reset 後自動接續。定義見 `skills/at/SKILL.md`
- **改期形態（08-29 閉環）**：pending ping 直接改期——刪 pending rung→同 session 重建（先刪後建，pending 在場建新被 session 綁定拒）；落地訊息尾巴接新指令時指令優先（零工具紀律只約束純落地 turn）。
- **5h limit 是 spawn 硬牆（08-30）**：背景 agent 收 `[1308]` 重試必敗→降級主 session 機械驗證＋報告明示 fallback；恢復靠 user 回報或 /at 接續。
- **How**：長任務中 usage 將盡主動建議（有未完任務→/at；只想被叫醒→/usage-ping）；host 需開到觸發時刻。標籤判讀以 cronExpr 為準非 title（08-19 混淆事件已修）；真 301min 累加做不到（interval 上限 200）——邊界見 [[at-skill-zcode-cron-gaps]]。

## /at 開頭判讀（original: feedback，08-20 糾正）

訊息**開頭** `/at HH:MM`＝排程請求：第一動調 at skill（context 檔＋CronCreate），本體到點才跑——誤讀成「現在順便看」＝燒 context＋打亂排程經濟。**中段**出現（「繼續/at 00:40 再繼續」）＝現在續跑到自然停點＋剩餘段排接續（prompt 自足＋硬 gate：commit 列 PENDING——cron prompt 非授權，見 [[commit-consent-in-autonomous-mode]]）。用戶改口「過時間可執行」＝排程意圖淘汰→直接執行不補排程。誤跑的調查折進 at-context「已查/未查」免重查；非 git 推進型任務 context 明示以清單為進度。
