---
name: backlog-card-edit-precheck
description: backlog 卡操作前先對時卡 id 歸屬——編號假設會撞平行 session（AIR-26 撞號實證）；--ref
  是整組替換會毀他卡 refs；誤改用 git checkout HEAD 全量復原
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

對 backlog 卡做 `task edit` 前先確認目標卡**真是自己預期的卡**：以建卡 CLI 輸出的 id 為準（編號會被平行 session 佔走——09-05 假設下一號 AIR-26 實配 AIR-28）。

**Why**：09-05 實證——`backlog task edit AIR-26 -s "In Progress" --ref ...` 打在平行 session 的**已結案卡**上：`--ref` 是整組替換（原 refs 直接被毀）、status 被覆蓋；「本 session 無其他寫入者」的 user 保證也可能在數小時內過時（平行線 09:16-10:49 落七 commit）。

**How to apply**：①建卡後只引用 CLI 回報的 id，禁假設下一號；②對非本 session 建的卡操作前先讀卡（status/refs 對時）；③誤改已 commit 卡→`git checkout HEAD -- <卡檔>` 全量復原（CLI 語義還原不夠——格式化差異會留 diff）；④撞號是 [[reference_backlog-md-browser-id-mechanics]] 防撞機制（建卡即 commit＋預掃）要防的活風險，也與 [[feedback_verify-wt-before-commit]] 同族（操作前對時）。
