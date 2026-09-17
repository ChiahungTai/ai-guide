---
id: AIR-118
title: 審查腿簡化——取消手動另開 session 常設補審，第二意見改由跨模型家族擔任
status: In Progress
assignee: []
created_date: '2026-09-17 06:41'
updated_date: '2026-09-17 11:03'
labels: []
dependencies: []
ordinal: 103000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
規則現在建議高風險變更再手動開一個新 session 補審一次。muse＋codex 雙家審查一致認為：同家族新 session 買不到額外獨立性，有效的第二意見是換 AI 家族。本卡改規則：審查獨立性階梯＝同家族 fresh context → 跨家族 → 人類；手動 session 只留窄門（審查機制本身被懷疑時當對照組）。等 user 開工拍板。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 rg 掃描零殘留：epistemic 詞組（另開 session／最強獨立／跨 session 第二意見／layer 2 跨 session）全 repo *.md 零命中；durability 保留清單（post-build:76,80／judge-review:69／agent-review-cycle:76,78／workflow-review-pattern:125,319／code-review:35,125／acceptance-evidence:193）逐項在場
- [ ] #2 review-engine 點 7 新語義四件齊：spawn 預設＋跨家族升級軸＋單家族顯性降級語義（explicit_same_family_degradation 或 no-candidate 記帳）＋meta-review escape clause（手動 session 窄門）
- [ ] #3 點 4 ③ 系統性偏誤例外改指跨家族＋措辭約束落檔（禁宣稱同家族 manual session 與 spawn 證據獨立性完全相等）
- [ ] #4 instruction-writing 審查閘通過（profile=boundary、跨家族腿 verdict 回卡）＋deploy_agents.py 部署＋fresh session 驗證（含 ai-development-guide.md bundle 側同步）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@f67d99b——卡片 commit 直落 main，implement 自 card commit 後起算〕

〔已決策勿重辯：①砍 review-engine 點 7「另開 session（user 手動、最強獨立）——高風險建議補跑」；manual new session 不再是獨立性層級 ②root AGENTS.md 層 2 重定義為「跨家族第二意見」（kind=different_provider_family，欄已存在 agent-review-cycle/model-routing）；A 軸階梯＝同家族 fresh-context spawn → 跨家族 → 層 3 人類 viewport（層 3 不變）③措辭約束（codex）：禁宣稱「同家族 manual session 與 spawn 證據獨立性完全相等」——正確表述＝同家族 fresh reviewer 處理 anchoring／局部 reasoning failure、跨家族是 systematic bias 升級軸、跨家族非萬能（acceptance-evidence 三層守衛）④跨 session 鏈（review→judge-review→apply→followup-review）保留並重新定位＝durability 基建，與 session 邊界脫鉤 ⑤跨家族外審（muse/codex bridge）保留；overhead 盤點 item 27（EP 外審）／28（段落 3-perspective）是另一決策，本卡不動 ⑥muse 條件（缺席則轉不同意）：(a) 單家族可用／額度撞牆的顯性降級語義——explicit_same_family_degradation（agent-review-cycle.md:67 詞彙）或 no-candidate 記既有帳本（review-engine SKILL.md:166），user 明示跨家族仍 fail loud；(b) 高風險 review spawn prompt 最小餵料衛生（fresh 腿禁塞 implementer 解讀——退化 dispatcher 污染面）⑦codex escape clause：manual new session 保留為窄義 escape/control mechanism——僅用於 reviewer orchestration 本身被審查／spawn isolation 不可信時 ⑧雙家審查紀錄：muse job-mu55o7p5-26xnk7（部分同意，附⑥兩條件）＋codex job-mu55o7qb-v5z5iz（部分同意，附③⑦修正案），工單與全文產出在 .agent-tmp/cross-session-leg-proposal/（gitignored；結算時 verdict 摘要落卡 notes）〕

範圍（sync 落點，muse/codex 彙整）——改：skills/review-engine/SKILL.md（點 7 刪另開 session＋點 4 ③ 例外改指跨家族＋:118 分離理由措辭）；root AGENTS.md（三層介入表層 1 標籤 same-session 修正＋層 2 行＋:30 review 鏈行「跨 session 貼回」→「跨 context／跨家族貼回」＋核心流程命令分類表 /ep-review:86、/code-review:91、/followup-review 格）；skills/ep-review/SKILL.md:14；skills/implement/SKILL.md:93,277,302,304,363,401 layer 術語；skills/handoff/SKILL.md:26＋流程段（改寫為跨家族第二意見入口）；ai-analysis/blueprint/workflow.md:441；ai-development-guide.md:44（bundle 側）。
明示不動（P3 durability 面，防誤砍）：skills/post-build/SKILL.md:76,80；skills/judge-review/SKILL.md:69；skills/_common/agent-review-cycle.md:76,78；skills/_common/workflow-review-pattern.md:125,319；skills/code-review/SKILL.md:35,125；skills/acceptance-evidence/SKILL.md:193。
掃描法（codex 建議）：epistemic 詞組（layer 2／second opinion／systematic bias／另開 session／最強獨立）與 transport/durability 詞組（cross-session／finding record／followup／handoff）分開掃——後者原則上保留。
本卡為控制面 instruction 語義變更：實作走 instruction-writing 審查閘（profile=boundary、跨家族腿），部署走 deploy_agents.py＋fresh session 驗證。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
實作完成（agent_6d678929，主 session 獨立抽查綠）：7 檔——review-engine 點7獨立性階梯四件＋點4③改跨家族＋分離理由措辭；AGENTS.md 三層表/review鏈行/命令分類表；ep-review:14；implement 五處；handoff 跨家族入口；blueprint:441；guide:44。bi 外審 job-mu55o7p5/mu55o7qb 附條件同意全吸收。殘留：index.html 投影 stale（已知情，另卡處理）；AGENTS.md:24 同檔 drift sync 經裁准。AC#4 落地閘（跨家族審查腿＋deploy＋fresh session）收線前執行
<!-- SECTION:NOTES:END -->
