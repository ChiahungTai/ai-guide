---
id: AIR-143
title: 規劃必答不做與刪除現有——design-thinking 比較條 delete-first rewrite
status: Done
assignee: []
created_date: '2026-09-19 21:15'
updated_date: '2026-09-19 21:59'
labels: []
dependencies: []
references:
  - rules/design-thinking.md
ordinal: 130000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
<!-- INTENT:BEGIN -->
白話：規劃任何方案時，「不做」和「把現有的砍掉」是必答選項——本週 16 件過度工程（做出來再被砍：git 工具、tab 條、上下鍵、SC13、週末抓取、閒置 WT）的規劃面 rewrite。
tier: standard
<!-- INTENT:END -->
<!-- SA:CONTRACT:BEGIN -->
- [C1] rules/design-thinking.md「決策與後果（強制）」既有條「比較現況及可行選項」rewrite 為比較必含「不做／刪除現有」——先答不做得嗎、既有砍得嗎，再比其餘可行替代；非新增 gate、非新 rule
- [C2] skills/deep-thinking/SKILL.md「比較可行選項」步驟同步（drift 防護）：由「包含維持現況」擴為必含「不做（維持現況）」與「刪除既有」兩個基準選項；定義源＝design-thinking rule，skill 為深層參照
- [C3] 落地閘：boundary 歸級（控制面 rule 條文語義變更——decision 面）；驗證＝bundle 重部署後 check_single_source.py 無新 drift；receipt 四欄入卡 notes
<!-- SA:CONTRACT:END -->
<!-- SA:BOUNDARY:BEGIN -->
- [B1] 不新增審查 gate／hook；不改「決策分級」「架構三視角」段；實作面砍 code 的既有 edit-discipline 不動（規劃面與執行面分離）
- consumes: 無——standalone rewrite 卡
<!-- SA:BOUNDARY:END -->
<!-- SA:EXPORT:BEGIN -->
- 無（design-thinking／deep-thinking 是行為面，非卡面消費者）
<!-- SA:EXPORT:END -->
<!-- SA:PENDING:BEGIN -->
- 無
<!-- SA:PENDING:END -->

〔背景（detail，不上圖）〕證據＝ai-analysis/reports/corrections-2026-09.md:45-46 訊號3＋Warm 動作③「規劃段落把『不做/delete 選項』列必答（rewrite 既有 planning 慣例）」。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 rules/design-thinking.md 比較條含「不做／刪除現有」必答語義且仍單行（rg 命中）
- [x] #2 skills/deep-thinking/SKILL.md 比較步驟含「刪除既有」基準選項（rg 命中）
- [x] #3 deploy 三面 bundle 後 check_single_source.py deploy_bundle_freshness 0 CRITICAL
- [x] #4 審查腿 receipt 四欄（classification/review/session-freshness/deployment-surfaces）入卡 notes
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
①baseline：rules/design-thinking.md:9「比較現況及可行選項」；skills/deep-thinking/SKILL.md:22「比較可行選項：包含維持現況，以及最接近的可行替代」
②已決策勿重辯：rewrite 該既有條非新增 gate/rule（user 0920 prompt＋corrections:46 動作③禁 additive）；deep-thinking 為深層參照隨改同步（payload C2，digest 114c7acca5f50620）；boundary 歸級（review-engine 判定表示例行：rules 條文修改；AIR-129 收斂正典）
③scope：動＝rules/design-thinking.md:9 一句＋skills/deep-thinking/SKILL.md:22 一句；不動＝兩檔其餘條文、決策分級/架構三視角段、其他 rules、edit-discipline（實作面砍 code 紀律）
④scenarios：規劃比較時必列「不做（維持現況）」「刪除現有」兩基準選項再比替代；邊界＝規劃面與執行面分離；fail＝bundle 部署後 check 出現新 drift
⑤integration：下游＝deploy bundle 三面（zcode/codex/muse）經 deploy_agents.py＋~/.claude/rules auto-load；deep-thinking desc「比較現況及選項」屬觸發文案不動（回報記錄）
⑥驗證式：rg "不做／刪除現有" rules/design-thinking.md 命中；rg "刪除既有" skills/deep-thinking/SKILL.md 命中；check_single_source.py 0 CRITICAL；receipt 四欄在卡 notes
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【authoring receipt】accepted 114c7acca5f50620 2026-09-20

【review receipt】classification=boundary／review=in-harness full 雙 context PASS（fresh：零 Critical/Important；intent：C1/C2 PASS、無第三處殘留）＋external cross-family deferred:.review/air-143.md#open-pending（muse 429 failed-usage job-mu8wfgn6-nlzs3o，retryable 2026-09-21T00:00Z，due 2026-09-27——landing-ineligible 至補審；AC#3 的 deploy sync＋check 驗證同禁至補審後）／session-freshness=fresh／deployment-surfaces=pending

【findings 裁決】B1 desc 同步尾巴→不採納（plan⑤ 已記錄不動）；B2 現有/既有異字→不採納（凍結契約原文，ledger 驗證式掃雙詞）；B3 必含 vs 不湊選項張力→不採納（可自洽解讀，reviewed diff 凍結）；B4 judge-review 相鄰無引用→不動；C3 終驗待補審後 deploy 後於 main checkout 跑 check_single_source
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
design-thinking 比較條 delete-first 必答＋deep-thinking 同步；boundary 腿收斂，codex Important 修正＝刪除既有補 N/A 逃逸口（必答不跳過）；merge fc5fe841＋feafa283，bundle 已部署 check 0 CRITICAL
<!-- SECTION:FINAL_SUMMARY:END -->
