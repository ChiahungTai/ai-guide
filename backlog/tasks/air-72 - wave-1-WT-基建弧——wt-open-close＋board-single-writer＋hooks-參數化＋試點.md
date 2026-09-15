---
id: AIR-72
title: wave-1 WT 基建弧——wt-open/close＋board single-writer＋hooks 參數化＋試點
status: In Progress
assignee: []
created_date: '2026-09-10 01:50'
updated_date: '2026-09-15 22:23'
labels:
  - governance
  - wt
dependencies: []
references:
  - scripts/wt-open.sh
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Blueprint workflow.md『待建基建』清單全部（ai-analysis/blueprint/workflow.md 定案）：①scripts/wt-open.sh（只接已存在 card——lock→驗卡→worktree add 自 owning 線→池/inbox symlink 兩條→muse hooks 重跑或參數化〔二選一〕→{toplevel,branch,card,baseline} 驗證→回報 cwd 啟動 session）＋wt-close.sh（lock→preflight→rebase/ff-only 既有收斂→board finalization→worktree remove→釋鎖）。②board single-writer：check_active_branches false→true＋卡 metadata（status/ref/id allocation）只有 board-control 可寫＋跨 WT max-id 預掃（補 untracked/staged 盲區）＋kanban SKILL 條款。③muse hooks 路徑參數化（.muse/hooks.json 絕對路徑半殘修——WT 內寫得到讀不到）。④outward 特赦裁定（metadata commit 擴展——user 裁）。⑤AGENTS.md git 慣例 WT 版（過渡條款收斂：primary checkout 模式→control/execution plane）。⑥試點一卡驗證（外卡落點歸零/撞號預掃/relay 新鮮度三項即驗）＋ephemeral WT fast-path（免卡小修）。融合定案吸收（reports/2026-09-10-wt-research-synthesis.md §六）：identity contract（owning_line/base/task/branch/WT path 落盤）＋scratch 三條件 materialize（①main 被卡佔用②review 期間 main 續推進③污染性測試）＋per-WT stale state 檢查位（.code-reality index/bridge ledger/backlog 副本）＋錯峰聲明落 card desc 欄位。驗收：試點卡全流程（wt-open→工作→wt-close→board Done）機械證據＋verify-memory-topology 在 card WT 通過＋blueprint workflow.md ❌TODO 標記升級。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-16 wave 決策——Wave-1 基建線＋試點已定〕試點卡＝AIR-73（真實交付＋dogfood wt-open→工作→wt-close→Done 全流程）。必吸收本 session（09-16 三 WT 實戰）新增形態：①池 gitignored 拓撲→涉及池的交付拆『資產源隨 branch＋池副本 marshal 合併後套』兩段——wt-open/close 應內建此分流 ②backlog 卡 metadata 由 marshal 單點 commit 的慣例已實證可行（board single-writer ③ 的實戰依據）③plist 進 deploy/ 版控慣例（deploy/entitlements-probe.plist 先例）。
<!-- SECTION:NOTES:END -->
