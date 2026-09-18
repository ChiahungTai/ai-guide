---
id: AIR-135
title: >-
  AI Development Arc 重整 program——card-first、Marshal 自動化、Code Lens、人機對齊＋跨 repo
  contract
status: In Progress
assignee: []
created_date: '2026-09-18 07:14'
updated_date: '2026-09-18 11:44'
labels: []
dependencies: []
ordinal: 117000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把「開發流程固定化」提升成 AI Development Arc program：核心不是固定一串 command，而是定義必要的 semantic obligations，讓人與 LLM 在關鍵時點保持同一張圖，同時把可委派的流程／model／WT／session 細節交給 Marshal 自動化。候選主鏈為 entry Align → Shape/Plan → Build → Verify → exit Align → Settle；Marshal 包覆全弧，不是 lifecycle node，同 repo handoff 退回 orchestration implementation detail，跨 repo 才保留 boundary 意義。

工作狀態改採 card-first：Backlog parent/sub-card tree 是 durable planning/control plane；Plan 是可修訂的 working hypothesis，不假設穩定，實作證據迫使改案時必須留下 superseded + reason/evidence，而不是另外維持一份「穩定 EP」。standalone EP 不再視為 semantic primitive，是否全面退役由 AIR-135.2 dogfood＋consumer migration 實證收尾。

human viewport 是 projection 而非第二真相源：Report Shell、/illustrate、Code Lens 等由 card tree + repo/code facts 按需產生。Code Lens 擬整合 code tours（narrative/sequence）＋pr-lens（topology/relationships/impact）成同一上位 viewport。跨 repo 採 owner/consumer contract：ai-guide 擁有 lifecycle semantics/policy/orchestration contract；SouthChariot 擁有人機 control surface；SC 不另建 lifecycle truth。跨 repo implementation card 要等 contract 收斂後在各 repo 自己開卡並以 shared arc/contract identity 關聯，不用跨 repo parent_task_id。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Development Arc 的 semantic nodes／transition obligations 收斂：human alignment moments 明確，Marshal-owned WT/session/model/retry 等 mechanics 不被誤當 lifecycle nodes
- [ ] #2 card-first contract 經 AIR-135 family 真實 dogfood：parent/sub-card 可讓 fresh session 還原 intent、current plan、plan revision rationale、evidence、verification 與 outcome；EP 是否退役有實證裁決
- [ ] #3 user 不需重複指定 model／review／WT/session／handoff procedure：AIR-135.1 可從 canonical card state＋runtime facts 產生可追溯 dispatch/transition obligations
- [ ] #4 Code Lens contract 收斂並以 code tour + pr-lens dogfood 證明 narrative/topology/impact 可由同一 code facts 投影；Report Shell／illustrate／Code Lens 都不成第二 truth source
- [ ] #5 ai-guide↔SouthChariot cross-repo ownership／identity／projection/action contract 收斂；SC implementation card 的開卡條件與回寫 canonical state 規則明確，SC 不另建 lifecycle truth
- [ ] #6 AIR-135 family 完整跑一輪後，產出現行流程→新 Arc 的 rename/deprecation/migration 清單，且 user 可用 human viewport 對照「系統理解 vs 真實意圖」完成最後方向裁決
- [ ] #7 AIR-135.1 dogfood 證明互動中 main agent 可持續留在 human discussion／steering seat，適合的工作自動 delegate/background；大／可恢復 worker 產出自動 artifact-first 落盤並回 bounded receipt，user 不需再提醒「開 sub／主 agent 待命／寫 .agent-tmp」
- [ ] #8 Context Continuity 經 AIR-135.6 dogfood：長弧在 context 壓力／compact／session restart 前後，可由 card-first canonical state＋artifact/runtime facts＋薄 continuation packet 恢復 current plan、已驗/未驗、active jobs 與下一動；不要求 user 重述，也不以 harness 自動 /compact 當主要狀態保存機制
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔定位〕AIR-135 是 program parent，不直接承載所有 implementation detail；parent 保留目標、跨子卡 invariant、整體 topology 與最終裁決，bounded work 下放 135.x。

〔已確認 evidence〕
- 實際 session audit 顯示，WT/session/handoff/bridge 等 execution mechanics 不應膨脹成 human-visible lifecycle nodes；Marshal 應吸收同 repo orchestration。
- mosaic_alpha MOS-22 precedent：原平級 MOS-16~21 為了真正成為 program children，重發為 22.1~22.6；Backlog.md source 又確認 parent 只在 create input、沒有 reparent edit path。
- Backlog.md source review：Task 原生承載 Description/AC/Plan/Notes/Comments/Final Summary + parent/subtask；Plan 有 replace/append semantics，官方 execution guideline 把 task 當 plan of record。真正風險是 plan 無痕覆寫，不是 plan 會變。

〔program workstreams〕
S1 / AIR-135.3：Development Arc semantic model＋命名。只定必要 obligations / transition gates / human alignment moments；Marshal-owned mechanics 不升格成 nodes。
S2 / AIR-135.2：card-first planning contract＋EP 退場 dogfood。定 section ownership/mutability、plan revision rationale、fresh-session reconstruction、既有 ep.md consumer 遷移與 reversal condition。
S3 / AIR-135.1：Arc compiler／Marshal automation。從 card tree 投影 ArcSpec/ArcPlan/DispatchSlice，把 role/model/window/review/retry/WT/session 義務程式化，user 不再重複 procedural prompt。
S4 / AIR-135.4：Code Lens。統一 code tour + pr-lens，定 canonical facts vs derived views、on-demand rendering、entry/exit Align 用法；原 S1 pr-lens graph 成為本 workstream 的 dogfood evidence，不再等同整張 AIR-135。
S5 / AIR-135.5：cross-repo contract。定 ai-guide↔SouthChariot ownership、shared arc identity、projection/action contract、何時在 SC 開對應 implementation card；禁止 SC 成第二 workflow DB。
S6 / AIR-135.6：Context Continuity。把 card-first state、artifact/runtime facts、event-driven checkpoint、thin continuation packet、adaptive rehydration 與 compact boundary 組成跨弧可靠性機制；不自製 summarizer、不把 /compact 時機從 user 手上拿走。
S7：整體 dogfood／對照：用 AIR-135 family 本身跑一輪，驗證 user 只給方向也能正確走流程；包含 context pressure/compact/restart recovery，再固化條文、rename/deprecate 舊 lifecycle/EP/viewport/compact-prep 名稱與入口。

〔決策原則〕
- human/LLM shared understanding 優先於 command completeness。
- canonical state 少且明確；視圖按需產生。
- Plan 可變；變更必有 reason/evidence/superseded trace。
- 同 repo orchestration 隱藏在 Marshal；cross-repo 才用 explicit contract/boundary。
- 子卡可以平行研究，但跨 repo implementation 不在 contract 未定前搶跑。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0918 開工】原卡以「完整標準流程六 lane + pr-lens 第一產物」為中心，已完成 v1 graph/validate/render 作方向對照；後續實際 session audit 與 user 校正顯示這個 framing 過度貼近 implementation mechanics。

【0918 方向校正】user 定調：模型會更強、可給更多自主權；最重要是 human 與 LLM 同一張圖。Report Shell、code tours、pr-lens、/illustrate 是 human alignment surfaces；反覆提醒方法／model flow 應由系統消除。同 repo WT/session/handoff 由 Marshal 自己處理，handoff 主要留跨 repo。

【0918 card-first 證據】Muse 直接讀本機 Backlog.md source 後，推翻前輪「full-tier 保留 EP」結論：Backlog Task 已有完整 structured sections + nested parent/subtask；Plan 原生可 replace/append，並非穩定 artifact；官方 guideline 明示 task 是 plan of record。缺口是 bare plan replacement 可能無痕丟 rationale，因此 AIR-135.2 要把「改 plan 必留 supersedes + reason/evidence」做成 contract/finalization gate。另確認既有 top-level task 無 reparent edit，需像 mosaic MOS-16~21→MOS-22.1~22.6 重發；AIR-134/DRAFT-12 的承接因此改走 135.1/135.2。

【0918 program 擴張】user 提議 Code Lens 整合 code tours + pr-lens，並考慮 AI lifecycle 改名／調整新流程；SouthChariot 未來也需開 implementation card，但跨 repo 關係要先設計。本卡因此改為 program parent，新增 semantic model、Code Lens、cross-repo contract workstreams；SC 卡等 AIR-135.5 contract 收斂後再開。

【0918 prompt-burden 補充】反覆 user correction 顯示兩個 orchestration 細節尚未被 program 明文化：互動 main-seat/delegation-first、以及大輸出 artifact-first delivery。ownership 下放 AIR-135.1；parent 只保留 dogfood 成功條件，不把它們升成 lifecycle node。

【0918 context continuity 補充】研究 09-15 compact architecture／controlled strategy／direction handoff、memory §6 與 09-08 compact feedback 後，新增 AIR-135.6。定位不是新增 lifecycle node，也不是自製 compact：把 context preservation 升成 Marshal cross-cutting reliability mechanic——card/artifact 平時持續 checkpoint，壓力來時只產 thin continuation delta，compact/new session 後 adaptive rehydrate 並驗實物。user 仍保留 /compact／換 session 時機裁決。
<!-- SECTION:NOTES:END -->
