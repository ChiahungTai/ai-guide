---
id: AIR-122
title: 投影 freshness 驗收閘——index.html 複本降級改 link＋manifest hash gate
status: Done
assignee: []
created_date: '2026-09-17 11:06'
updated_date: '2026-09-17 13:21'
labels: []
dependencies: []
ordinal: 107000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
人類 viewport 投影頁（blueprint index.html）被發現殘留舊詞彙且常態落後 2-3 個弧：上游變更無機制觸發重投影，而殼裡根本不該有治理規則複本（違反 html-mode 自家篩選通則）。muse＋codex 雙家審查裁定：先降級複本改 link、再對剩餘投影面補 manifest＋hash 驗收閘、補 owner/trigger。等 user 開工拍板。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@b05311f（開卡 commit 已走暫時 worktree --no-verify，事由記 commit body）〕

〔已決策勿重辯：①R0（muse）：治理規則複本本不該進殼——html-mode:44 內容篩選通則明文 → (c) 刪 index.html:642-672 兩表複本改回源 link（structure.md:64 pointer 先例）②剩餘合法投影面 → (a) manifest 補真源（含 root AGENTS.md 節錨點）＋slice hash gate——hash 申報 slice 非整檔（防無關改動噪音閘）；parity 先例＝sync_agents.py:1038-1061 形態③AIR-73 html-mode『投影鎖定與 stale 標記』節補 owner/trigger/stale 標記——義務有宣示無機制④quality-constraints 加獨立相鄰小節：派生產物須可追溯 upstream；upstream 變更未重驗＝stale 不得當 current projection⑤(b) 政策翻轉 gate 僅 lite backstop⑥R4：stale 無 validity 語義＝比沒有更糟⑦**repo-agnostic 設計約束（pr-lens 接線前置——tri 三腿裁定 AIR-122 先行於 map 累積）**：freshness check script 讀 manifest 宣告的 upstream 清單比對 hash，不含 ai-guide 專屬路徑——mosaic 的 pr-lens committed map 為泛化消費者⑧**pr-lens 對接註記（源碼級查證）**：pr-lens schema strictObject 拒 extension 欄→provenance/coverage 走 sidecar 不進 document；.pr-lens/ gitignore 可再生 vs committed map export＝AIR-74 殼進版控同構；本地 /Users/ctai/Github/prlens 為錯誤同名專案已移除，正確 checkout＝/Users/ctai/Github/pr-lens pin 1678527⑨bi 審查 job-mu5f07gq/mu5f07hz＋GLM fresh 腿；四份 verdict 在 .agent-tmp/dispatch-compiler-proposal/projection-*.md⑩控制面條文變更走 instruction-writing 審查閘〕

範圍——改：ai-analysis/blueprint/index.html（刪兩表複本改 link）；skills/_common/illustrate-html-mode.md（投影鎖定節三補項）；scripts/projection_freshness.py（新：repo-agnostic）；rules/quality-constraints.md（獨立小節）；skills/post-build/SKILL.md（gate ③ html 一行 lite）。
明示不動：AIR-118/121/123 已落地檔；mosaic 本體（泛化消費者在彼 repo）。
AC：①freshness check script＋pytest（stale/fresh 兩態 exit 契約；fixture）②index.html 兩表複本移除改 link、rg 零舊詞彙③html-mode 三補項在場④quality-constraints 獨立小節在場⑤script repo-agnostic 斷言（path 清單全來自 manifest 參數，零 hard-code）⑥instruction-writing 審查閘（boundary 跨家族）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
結算（final）：落地 main 7320ea7（rebase 與 AIR-121 quality-constraints 段衝突已解——兩節並存正是 tri 裁定形態）。審查鏈＝bi 投影根因（mu5f07gq/hz）＋tri 三事項（mu5gjcrh/csm＋GLM 腿）裁定全吸收。12 tests 綠＋live 三方 hash 對帳 MATCH＋index.html 舊詞彙零殘留。deploy 隨收線執行。blueprint/AGENTS.md 真相源映射補記（impl 建議）＋AI R-106 follow-up：card-WT governance check 假漂移另修。
<!-- SECTION:NOTES:END -->
