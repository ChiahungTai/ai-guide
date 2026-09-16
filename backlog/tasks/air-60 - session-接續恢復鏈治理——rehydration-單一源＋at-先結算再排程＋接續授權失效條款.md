---
id: AIR-60
title: session 接續恢復鏈治理——rehydration 單一源＋at 先結算再排程＋接續授權失效條款
status: Done
assignee: []
created_date: '2026-09-09 13:20'
updated_date: '2026-09-16 01:23'
labels:
  - governance
  - skills
  - handoff
dependencies: []
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔baseline：ai-rules 6e96e0e〕09-09 三顧問 session 接續討論（muse/flash/codex 交叉兩輪）收斂的恢復鏈治理落地卡；討論全程記錄 .agent-tmp/session-journal.md（ephemeral 7d，決策以本卡為準）。

〔已決策勿重辯：①rehydration 順序單一源——三份局部版在場且會 drift（at skill「Resume 後的行為」1-4／context-management rule「接手 quota 中斷先讀」清單／handoff schema 欄序），合併為一條寫死的恢復序列單一源、三處改引用；「死前結算寫進五處、死後只讀兩處」是現況缺口（五落盤層：EP／卡 notes／journal／compact-context／STATE／.review）；先合併再談新載體（不新增第六落盤層）②at Phase 0 改序——先結算（EP append＋卡 notes＋STATE.md 觀察）再寫 at-context 排程；/at 本來就是 cold rollover 形態（不捕 snapshot＋fresh landing＋git log 重建），殘餘缺口只在結算順序、非 rollover 形態③接續授權失效條款——mutating continuation 工單＋at resume prompt 固定加「卷內既有授權全部失效，outward 動作一律 PENDING」；at「禁止詢問用戶確認」是自主執行指令、不得解讀為授權展期（授權隨卷延續＝接續最大未管理風險，恰好繞過 outward-action-consent「一次授權≠永久授權」）〕

〔驗收：①rg 驗三處（at／context-management／handoff）均引用同一單一源恢復序列，無各自為政殘留②at SKILL.md Phase 0 含結算三件且時序在寫 at-context 之前③授權失效條款在 at resume prompt＋work-order 範本（skills/_common/work-order.md）＋model-routing「session 定向接續」節三處在場④sync-sources 機械新鮮度檢查通過＋guide 部署同步（deploy_agents）〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔triage 併弧 09-10——升級為 session 接續×review closure 治理弧〕併入 AIR-61（雙 lens review closure 標準化：primed finding closure＋fresh 跨家族腿＋codex followup 接線——原卡搬 completed/ 可查全 desc）＋AIR-62（segment receipt：EP 段落收斂狀態盤上化——機械欄生成＋freshness 鏈）。三段連續做：①rehydration 單一源＋at 先結算＋接續授權失效條款②雙 lens closure③segment receipt。

〔09-15 對帳——AIR-101 owner 卡開工（workflow redesign EP）〕本卡三段與 EP（ai-analysis/_tasks/09-15-development-workflow-redesign/ep.md）對帳：EP S3（_common/task-recovery.md 恢復順序單一源）承接段①的 rehydration 單一源骨幹（含 at 先結算再排程＋handoff 同 read-set）；EP S2（段落結果寫 EP 進度＋followup status 單一寫入者）部分觸及段③ segment receipt 方向但非全量。本卡保留自算：①內授權失效條款（at resume prompt＋work-order＋model-routing 三處在場——EP S3 不覆蓋此三處）②雙 lens closure（AIR-61 併入段）③segment receipt 機械欄生成＋freshness 鏈（AIR-62 併入段）。AIR-101 結算時本卡 Plan/AC 依實際交付修訂（已交付部分劃出、剩餘重述），不雙 writer 並做。

〔09-16 wave 決策〕排 Wave-1 並行線第二位（AIR-98 P2–P4 之後）——本卡段①動 model-routing『session 定向接續』節＋work-order，與 AIR-98 P2 窗口正典節同檔錯開。S3 骨幹已由 AIR-101 交付（_common/task-recovery.md＋at Phase 0 先結算）；本卡結算時 Plan/AC 按已交付部分劃出（09-15 對帳 notes 承諾的修訂）。

〔09-16 Wave-1 lane60 worker 檢查點——全程未 commit，詳 verdict＝.agent-tmp/air-60/verdict.md〕段①授權失效條款三處在場（at:34,102-103／work-order:13／model-routing:270，rg 逐字驗證）；段②雙 lens closure 條文落 workflow-review-pattern「closure lens 分工」節＋post-build 階段 3 hook（primed 術語碰撞改稱 closure 腿/fresh 腿——待裁決 D2-a）；段③segment receipt 生成器 scripts/segment_receipt.py＋6 測試 GREEN＋implement 斷點條文＋實跑 FRESH。待 marshal：D4 Plan/AC 修訂草案套用、task-recovery 讀端一行（D3-a）、真實 codex followup runtime 驗證（D2-b）、deploy 實跑授權（dry-run 量測 30,335B＝32%/82% gate）。全套件 569 passed。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
授權失效條款 4 處＋closure lens＋segment_receipt.py 進 main（d030fa5）；570 tests 綠＋外審六項裁決全落地＋三代命名一致性掃描閉環。
<!-- SECTION:FINAL_SUMMARY:END -->
