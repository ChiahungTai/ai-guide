---
name: flow-feedback-done-archive
description: 處理完的 flow-feedback 搬 ai-analysis/flow-feedback/_done/；/commit 是否自動化討論中
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 01979bd2-f87f-4909-b7e5-7e017a51eb53
---

處理完的 flow-feedback（/flow-review 已決策、且對應變更已 commit；或明確 decide-to-defer 帶紀錄）→ `mv ai-analysis/flow-feedback/<file>.md ai-analysis/flow-feedback/_done/`。仍 under-discussion、未決策的留 root（/flow-review 既有「defer → 留 feedback」規則）。`_done/` 首次使用時建立（截至 2026-06-17 僅 `execution-plans/_done/` 存在）。

**Why:** active inbox（root）只顯示未處理項，避免噪音；與 EP `_done/`、kanban Done/ 生命週期一致。user 2026-06-17 明示「處理完的都要丟到 _done，要記得喔」。

**How to apply:** /commit 階段若該 commit 解決某 feedback → 隨該 commit 把檔 mv 進 _done/（mv 後 add _done/ 路徑，使檔在 resolving commit 直接落地 _done/，不先留 root）。/flow-review 中 decide-to-defer 帶紀錄者亦可歸檔。仍在討論、未決策的不搬（如 2026-06-17 討論中的 `consistency-forked-arguments-self-check.md`）。

**跨 repo gap（2026-06-18 補）**：mosaic 與 ai-rules 各有獨立 `ai-analysis/flow-feedback/` + `_done/`；`/commit` 階段 2.8（skills/commit/SKILL.md:144）路徑是 repo-relative，只歸檔**當下執行 commit 的那個 repo 自己的** flow-feedback。mosaic 的 feedback 討論的變更雖落在 ai-rules，但 ai-rules 的 resolving commit 不會回頭歸檔 mosaic 的檔 → mosaic 的會累積 root，需**人為逐個比對「核心訴求是否已落地」**（查 ai-rules rules/skills/commands 現狀 + git log，附 path:line 證據）再補歸檔；部分解決的留 root 並在檔頭標狀態（✅ 已解決切面 / ❌ 待解切面），不可整檔歸檔丟失未解訴求。

**已落地**（2026-06-17，commit 62d78de）：/commit 階段 2.8「flow-feedback 歸檔識別」+ 階段 6 mv→add `_done/` 機制；/flow-review 補歸檔生命週期註。durable home 在 /commit（非 memory）。本 memory 僅留決策脈絡：歸檔觸發點選 /commit（resolving commit）而非 /flow-review，因「歸檔 = 證明改動落地」語義最強（呼應 EP 最後段落 commit 才歸檔）；forgetting 風險靠階段 5 可見清單把關。Related: [[archify-illustrate-html-mode-eval]]（B 軸段）。
