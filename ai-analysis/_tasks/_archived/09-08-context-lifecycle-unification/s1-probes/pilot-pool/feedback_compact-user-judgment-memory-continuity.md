---
name: compact-user-judgment-memory-continuity
description: compact 時機與 session 收線都是 user 判斷——AI 不推自動觸發、不自行提議收線；context 因應＝接續品質
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_38bc3cc9-d5eb-4080-8c39-168647bca011
---

2026-08-18 用戶裁決（token 計費翻轉審查 F3 討論）：「compact 這件事應該是使用者判斷吧，倒是重點在好接續就好，所以應該是善用 memory」。

**Why**: 跨 session 審查報告建議「compact 水位自動觸發紀律」（token 計費下最大槓桿 18%），但這越俎代庖——compact 時機涉及使用者工作節奏與 EP 段落邊界的判斷，不該自動化。與 repo 既有哲學一致（一 EP = 一 session、model 退化就換不硬撐、接續靠 EP 段落自足）。且實測 guide 的 /compact 節奏 prose 是死信（224 sessions 僅 7 次執行）——prose 無效，但解法不是自動化，是把「隨時可結束」做扎實。

**How to apply**: 當 context/token 分析導向「自動壓縮/水位觸發」類建議時，改提**接續品質**導向——確保 session 隨時可關可接（STATE.md 觀察、memory 檔、EP 段落自足、handoff context、kanban 卡結算），context 成本的因應是「可接續 → 隨時關 session 換新」而非「撐長 session + 自動壓縮」。compact 決策本身留給使用者。**09-04 增證（同族擴界）**：「這 session 該收了、開新 session 做」的收線建議也被推翻——user「你這邊做就好，不需要new」「用30.5% context 還很夠吧」：context 剩餘量與要不要換 session 接續全是 user 判斷；AI 可陳述用量事實，但不以 context 為由自行收窄當前 session 的承接範圍。相關：[[per-call-billing-model]]、[[cr-live-faces-roadmap]]（implement 消耗分析段）。
