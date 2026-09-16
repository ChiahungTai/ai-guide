---
name: feedback_permission-layer-no-behavioral
description: 改 settings.json permission 時不要重複 rules/skills 層的 behavioral 約束
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d4389841-60bd-47ed-96af-049290852219
---

改 settings.json（permission 層）時，只處理「技術上允許/禁止某命令」。不要在 permission 討論裡長篇提醒 behavioral 風險（git add -A、rebase 衝突、--hard 等）—— 那些是 ai-rules 那層（rules / skills / commands）的職責，那邊已經處理。

**Why:** 層次混淆 = 在錯的層重複另一層的職責。permission 是機械允許閘門；行為約束歸 rules（如 `[[feedback_verify-wt-before-commit]]`）、流程歸 skills（如 `/rebase` 衝突處理）、同意歸 rules（如 commit-consent）。在 settings 層重講 = 多餘噪音，且暗示 permission 層該解決行為問題（錯誤期待）。

**How to apply:** 改 settings 時，分析聚焦「這命令可逆嗎 / 風險等級 / 與已允許命令的一致性」。行為風險一句帶過「歸 rule/skill 層」即可，不展開。這是 [[hook-vs-llm-flow-division]]（機械層 vs 語義層分工）在 permission 軸的體現，也呼應 CLAUDE.md「載體選擇」。
