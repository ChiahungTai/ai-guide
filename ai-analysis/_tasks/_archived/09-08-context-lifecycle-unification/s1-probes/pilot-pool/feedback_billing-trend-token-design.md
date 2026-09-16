---
name: billing-trend-token-design
description: user 成本世界觀——帳制趨勢 token 化（zai 新方案 token、muse 暫 request）；設計
  request/token 雙少；成本精估不必要、大概判斷即可
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_a5069681-4db4-4e97-95ac-84baf6c05d6f
---

2026-09-03 裁定「推算優先」（四律3）不進 ai-rules 時 user 的完整論述：

- **probe 算不準**：除非有 API 可取得 usage 變化＋控制實驗——單發量測常低於回報粒度，量了也不準
- **估成本其實沒啥必要**：帳制趨勢＝zai legacy 走 request、muse 現在走 request、**zai 新方案已是 token 制**；除非 AI 算力供給過剩，市場會慢慢往 token 走
- **設計面本來就該偏向 request 少、token 少**；成本問題「就大概判斷吧」
- 推導鏈要求也不需要（原規則的「附推導鏈讓 user 可核」一併被否）

**Why**：精估流程投入產出不成比例且帳制在變；muse 額度經濟（~8 requests≈5h 窗 10%）那個量級的推算已經夠用。

**How to apply**：未來提案勿建議精細成本估計流程／推導鏈儀式——成本類一句 magnitude 判斷＋「設計雙少」原則帶過；細粒度量測只在行為驗證（無法從已知推導）時做。與 [[feedback-magnitude-over-precise-counts]]（display 層）互補——本條是決策方法層。弧脈絡見 [[agents-registry-split-design]]。
