---
id: AIR-122
title: 投影 freshness 驗收閘——index.html 複本降級改 link＋manifest hash gate
status: To Do
assignee: []
created_date: '2026-09-17 11:06'
updated_date: '2026-09-17 11:07'
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
〔baseline：/Users/ctai/Github/ai-guide main@a06690a（開卡 commit 走暫時 worktree --no-verify——governance parity 暫態敗為 air-119 在飛已知問題，事由記 commit body）〕

〔已決策勿重辯：①R0（muse）：治理規則複本本不該進殼——html-mode:44 內容篩選通則明文殼不裝治理規則，index.html:642-672 三層介入表＋命令分類表（root AGENTS.md 複本）違反自家契約與殼頭『不建立第二套規則』宣言 → (c) 刪複本改回源 link（structure.md:64 pointer 先例）②剩餘合法投影面 → (a) manifest 補真源（含 root AGENTS.md 節錨點）＋slice hash gate——hash 申報 slice 非整檔（防無關改動噪音閘）；parity 先例＝sync_agents.py:1038-1061 形態（唯讀比對、drift 列清單 exit 1）③AIR-73 html-mode『投影鎖定與 stale 標記』節補 owner/trigger/stale 標記——現況義務有宣示無機制（:88-95）④quality-constraints 加獨立相鄰小節（非 AIR-121 第三句）：派生產物須可追溯 upstream；upstream 變更未重驗＝stale 不得當 current projection（codex R4：stale 以 current 姿態呈現＝比沒有更糟）⑤(b) 政策翻轉 gate 僅 lite backstop（gate ③ Delegate 列加 html 一行），不作 freshness 主機制 ⑥內容篩選（semantic synthesis）不追求 deterministic——只機械化 freshness（雙家一致）⑦triple-source 收斂：root AGENTS 權威 → workflow.md 敘事 consumer（link root）→ index.html viewport consumer（從權威表示投影）⑧bi 審查 job-mu5f07gq-hitns4／job-mu5f07hz-bvwuub；四份 verdict .agent-tmp/dispatch-compiler-proposal/projection-*.md〕

範圍——改：ai-analysis/blueprint/index.html（刪兩表複本改 link）；skills/_common/illustrate-html-mode.md（投影鎖定節補 owner/trigger/stale＋manifest 契約）；scripts/ 新增 projection freshness check（或併既有工具）；rules/quality-constraints.md（獨立小節）；skills/post-build/SKILL.md（gate ③ html 一行 lite）。
明示不動：AIR-118/121 已落地檔；structure.md/workflow.md/onboarding.md 本體（敘事 consumer 僅加 link 指針）。
AC：①freshness check script＋pytest fixture（stale/fresh 兩態 exit 契約）②index.html 兩表複本移除改 link、refresh 後 rg 零舊詞彙③html-mode 三補項在場④quality-constraints 獨立小節在場⑤instruction-writing 審查閘（boundary 跨家族）＋post-build 收斂鏈過。
<!-- SECTION:PLAN:END -->
