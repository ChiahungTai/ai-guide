---
id: AIR-106
title: 治理第二波——activation-before-review＋deployment surface 契約＋completion receipt
status: Done
assignee: []
created_date: '2026-09-16 03:16'
updated_date: '2026-09-16 05:28'
labels: []
dependencies: []
references:
  - skills/instruction-writing/SKILL.md
  - skills/post-build/SKILL.md
ordinal: 91000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-105 落地時實證的洞（F8）：Claude 端規則是 live symlink，主樹一 commit 就對所有 Claude session 生效，審查永遠追不上。這張卡把治理接線的三個剩餘件補完，讓「審查中」的條文不被讀到、每個弧結算時有機械回執。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 card WT 隔離 authoring 流程成文並有 gate（控制面修改不落 canonical 主樹）
- [ ] #2 deployment surface 發現契約在場（每 surface 自答觸及 path 與唯讀探針，post-build 只編排）
- [ ] #3 completion receipt 四欄（classification/review/freshness/deployment）進 commit／post-build 報告格式
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide c8acedd〕
〔已決策勿重辯：①三件範圍＝activation-before-review（card WT 隔離 authoring→審→merge canonical；Claude live symlink 生效面——AIR-105 F8 實證）＋deployment surface 發現契約（每 surface 自答「哪些 path 觸及」＋「唯讀探針」，post-build 只做 discover→dispatch→collect）＋completion receipt 四欄進 commit／post-build 報告（AIR-105 已試行原型）②方向源＝muse job-mu3gjvye＋codex job-mu3gjvtj 顧問 verdicts（.agent-tmp/air-101/）③不重造風險分類——路由 review-engine profile④分類預期＝boundary（開工時正式重分類）〕
範圍：instruction-writing／post-build／commit skill 條文＋deploy/腳本接線；風險面：gate 過嚴會儀式化（防：fast-track static-only 機械可判定不擴張）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔審查腿回收 0916〕bi panel＋fresh/intent 四腿全回收：①muse job-mu3k8gcj-xx1hbp（conditional pass——P1 hooksPath fail-open/merge 無閘/語義矛盾＋P2 四欄值域/N-A-未覆全劃界）②codex chatgpt-web/high（needs-fix——P0 canonical checkout 生效面：live symlink 指 canonical working tree，primary 切卡 branch＝checkout 即生效與 commit 無關；本腿中途撞 web 池限額 09-19 16:22 後恢復，findings 已完整交付）③fresh flash（needs-fix——P0 quotePath：非 ASCII 路徑 octal-escape 包裹致三 regex 分支全失效，機械重現兩次）④intent flash（conditional pass——P1 commit 捷徑模式漏 2.9）。judge 裁決：P0/P1/P2 全修（dee87d8＋ec80291），tri panel 終審待四卡齊；不採：NUL-safe（solo repo 記錄）、客製 break-glass、tests/ 全閘。

〔落地回執（post-build 終版）〕classification=boundary（review-engine 判定表：控制面 authority/gate 面）。review=七腿：bi panel muse job-mu3k8gcj（conditional pass→P1/P2 修）＋codex chatgpt-web/high 首腿（needs-fix→P0 canonical checkout 生效面修；jobId 未錄，輸出 .agent-tmp/air-106/review-codex.out；中途撞 web 池限額後由 user 裁定重派）＋fresh flash（needs-fix→P0 quotePath 修）＋intent flash（conditional pass→捷徑旁路修）＋tri 終審 muse job-mu3m0kl5（conditional pass→限域/句式/欄名修）＋tri GLM-5.3 full（conditional pass→merge-tree 卡檔 union 解＋P3 批修）＋tri codex-web job-mu3mic6x（needs-fix→skill 限域/Workflow 漏接/nt 補錨修）。修復 commits：dee87d8/ec80291/36f7463（branch 已 merge 保留 hash）。session-freshness=applied（model-routing 派工前重載；codex-web 重派＝user arc 改判）。deployment-surfaces=pending（bundle redeploy 待 user 授權——新條文已進 main；muse-plugin/code-reality/symlink 三面 healthy）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
治理第二波三件全落地（card WT 隔離閘／deployment surface 契約／回執四欄正典）＋canonical 正典升級 persistent card WT。七腿審查（bi panel＋fresh/intent＋tri 終審）3×P0＋P1/P2 全修，merge cfdb1ac 已 push。bundle redeploy 待授權（deployment-surfaces=pending）。
<!-- SECTION:FINAL_SUMMARY:END -->
