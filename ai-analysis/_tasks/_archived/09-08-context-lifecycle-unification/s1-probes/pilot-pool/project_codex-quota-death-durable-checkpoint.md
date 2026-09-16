---
name: project-codex-quota-death-durable-checkpoint
description: 09-07 codex 配額死亡弧——durable-checkpoint rule 已 commit＋部署五端；worktree 0c6f findings 四輪反例驅動全閉（R1-R6→F1-F3→N1，bbd4467/bf38afb/5c7c7d9）
metadata:
  node_type: memory
  type: project
  originSessionId: sess_57806287-329c-4d9e-a171-03f78e1ab697
---

09-07 codex session 01a07ad8 死於 usage limit（sub-agent arc_fresh 回報，配額重置 09-08 02:00）。驗屍機械見 [[reference-codex-rollout-jsonl-autopsy]]。

**已落地**：`rules/context-management.md` 新增「想法即時落盤（durable checkpoint）」節——事件驅動落盤（發現/決策+理由/排除路徑/下一步意圖）、載體分流（EP 進度節即時 append｜backlog 卡 `--append-notes`｜探索期 `.agent-tmp/session-journal.md`）、內容自帶完成度狀態（中間檢查點/最終）、spawn 長任務 agent 注入落盤義務、quota 死亡接手第一動讀檔非對話記憶。`rules/AGENTS.md` derived 表同步；已 deploy 四端＋Claude rules symlink 驗證；已 commit（09-07，經 post-build docs 鏈＋consistency 雙檔通過）。

**孤兒已收（09-07 晚～09-08，三輪反例驅動閉環）**：worktree 0c6f 的 R1-R6 由主 session judge 逐項查證（R1 親重現：relative 同檔輸出真的覆寫 SQLite）6/6 採納 → `bbd4467`。**muse followup 判「6/6 closed」被 codex 二輪驗收推翻**（F1 margin 非契約／F2 guard 只掃現存檔／F3 None 進分組鍵——三項皆附 CLI 實跑反例）→ judge 3/3 採納修復（SQL op 等價選取、單池契約、時間證據 gate）→ `bf38afb`＋muse followup 全 closed。codex 三輪再揪 N1（SQLite `datetime()` 截小數秒，ISO 小數窗邊界漏）→ 上界 `<=` superset 修復＋三 case 測試，199 tests。**教訓：工單式 followup 的「全 closed」不可盡信——codex 每輪用自構反例實跑驗收，抓到 muse 照著修復宣稱走的盲區；反例驅動的驗收深度 > 宣稱對照式驗收**。裁決表全在 EP 段可重放。語義沉澱見 [[memory-governance-air40-42]]。
