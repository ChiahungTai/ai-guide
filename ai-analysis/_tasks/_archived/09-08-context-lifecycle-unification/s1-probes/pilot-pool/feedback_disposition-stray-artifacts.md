---
name: feedback_disposition-stray-artifacts
description: working tree 殘留物（非本 session 產物）user
  期待主動處置到收斂——查歸屬→按設計生命週期收斂（gitignore/清檔），並行排除非唯一出口
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_44ce10e8-3773-4756-925a-68e81ca4363e
---

user 09-07（bundle-watch-state.json untracked 噪音）：「這是你弄的嗎？不是你弄的也處理一下」——非本 session 產物的殘留檔，期待的不是「並行排除＋回報」了事，而是處置到 git status 乾淨。

**Why**: 並行原則保護的是他 session 活躍中的工作；無主產物（cron state、背景任務遺留）留 untracked 是之後每個 session 的永久噪音。本次處置形＝查歸屬（內容 per-rule bytes＋mtime＋cron prompt 引用鏈→週日治理 cron 的趨勢 state）→按其設計生命週期收斂（活檔 working tree 不進版控→`.gitignore` 附生命週期註解，同 nightly-convergence.log 模式）。

**How to apply**: 三步——①機械查歸屬（誰的設計寫入它：內容/mtime/引用鏈）；②按該設計的生命週期收斂（活檔→gitignore；暫存→清單＋清）；③commit 收尾（小 chore 也是完成態）。與 [[cross-workspace-actions-user-handles]] 邊界：他 workspace/他池的東西仍 user 自己動，本條只及本 repo working tree 無主殘留；疑似活躍並行 session 的產物先回報歸屬證據再動手（[[feedback_relay-claims-verify-current-state]]）。
