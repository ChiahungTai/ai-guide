---
name: cross-workspace-actions-user-handles
description: 停他 workspace 排程／改他池狀態檔＝user 自己動手（「我砍就好」）；AI 只整自己側＋回報，禁繞道改他檔
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_03916836-handoff-successor
---

2026-09-01：兩個排程搶同一 memory 池（mosaic workspace 23:40 at-task vs ai-rules 00:40 automation），user 裁示「乾脆就你這邊跑就好，那邊停掉」。我嘗試停 23:40：CronList 不見（workspace-scoped 刪不到）→ 轉而計畫改 mosaic 池麵包屑寫作廢標記 → user 打斷：「我砍就好，你不要這樣搞」。

**Why**：跨 workspace/跨池的控制面操作（砍排程、改他弧線的狀態麵包屑做協調標記）是 user 的手動領域；AI 繞道寫他 repo/池檔案＝越界 workaround——即使動機正確（防寫寫衝突），user 仍視為不可接受的「這樣搞」。與 [[project_session-topology-single-writer]] 同向：誰的家誰管。

**How to apply**：發現跨 workspace 排程/任務衝突時——①把自己側的排程整好（CronUpdate 合併範圍、加 mtime 防護）；②回報事實（哪條排程、在哪個 workspace、為何衝突）讓 user 手動砍；③禁：改他 workspace 的 `.at-contexts/`、他池麵包屑、任何跨 repo 寫入做「作廢/協調」標記。平台事實（CronList/Delete 僅本 workspace）見 [[at-skill-zcode-cron-gaps]]。
