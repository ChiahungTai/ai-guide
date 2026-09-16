---
name: ai-rules-dual-role-mosaic-shared
description: "ai-rules 雙角色:通用 rules + mosaic(3 worktree)共用 skills/commands 的家;看到 mosaic-specific skill 別當漂移"
metadata: 
  node_type: memory
  type: project
  originSessionId: 911d9e1e-20bb-4fdc-9c28-5bb09d82acad
---

ai-rules 扮演雙角色:(1) **通用 rules/commands/skills**(跨專案);(2) **mosaic 共用 skills/commands 的家**。

**Why**:mosaic 專案(mosaic_alpha_offline_backtesting)有 main + 2 worktree,三個都要同一份 mosaic-specific skills/commands(trading-analysis、upgrade-nt、python-type-gap 等)。ai-rules → `~/.claude`(user-level)→ 每個 session/worktree 都載入,**就是那個共通處**。worktree 共享 `.git` 不共享 working files,不能靠 worktree 機制分享 skills;user-level `~/.claude` symlink 是唯一乾淨解。symlink 相對路徑技術上可行(target 相對 symlink 目錄),但 cross-worktree 不同絕對路徑,relative symlink 解不了 → 現有機制已最佳。

**How to apply**:
- 看到 ai-rules 有 mosaic-specific skill/command(NT / shioaji / mosaic_alpha / trading-analysis / upgrade-nt),**不要當漂移旗標** —— 它是 mosaic 共用工具,放這裡 by design(跨 3 worktree 共用)
- 只有 `rules/`(auto-loaded)的**規則邏輯**要通用(例子可領域特定,見 [[rules-no-project-specific-facts]])
- upgrade-nt / upgrade-sj / swing-analysis 是刻意的專案工具(memory 例外),也不是漂移
- 若要視覺整潔:mosaic 專屬 skills 可考慮放 `skills/mosaic/` 子目錄(純組織,非功能需求)

關聯:[[rules-no-project-specific-facts]]、[[archify-illustrate-html-mode-eval]]。
