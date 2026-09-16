---
id: AIR-113
title: skills fleet 過時清理盤點——82 支逐支處置＋注入面複測
status: Done
assignee: []
created_date: '2026-09-16 13:51'
updated_date: '2026-09-16 22:27'
labels: []
dependencies: []
references:
  - ai-analysis/reports/guides-refactoring/usage-fit-audit-20260917.md
ordinal: 98000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
0916 互動弧遺留：user 判 skill fleet『有點太肥、有些可能過時』。ZCode 單根化後注入面＝82 條目（~6K chars/session），真成本在維護面（82 個 instruction surface 各需 consistency review）。盤點地基已備：AIR-107 觸發路徑矩陣（ai-analysis/_tasks/09-16-air107-skills-activation-matrix/matrix.md）。隨卡處理 instruction-testing:56 歸因張力（本弧 bi panel deferred 項——本卡 fleet 增減正是使其條件化的變數，縮進 metadataBudget 預算內即 desc 注入啟動）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 82 支逐支處置表附 usage 證據（AIR-107 矩陣錨位：31 rule 錨／24 語義自明／21 弱名〔5 錨＋16 fail-driven〕／6 零路徑）
- [ ] #2 專案特定六支外移評估落卡（nt-query／nt-v1-query／upgrade-nt／upgrade-sj／swing-analysis／kbar-form-analysis——locality vs 跨 repo 可用性取捨）
- [ ] #3 處置後注入面複測（headless rollout 條目數＋預算溢出態判定）
- [ ] #4 instruction-testing:56 歸因張力修正（絕對句→條件化＋PASS 歸因紀律補 desc channel）——acceptance 語義面，隨卡 tri 腿審查，本卡審查級別含 tri
- [ ] #5 .agent-tmp 遺留清掃（probe 證據 air-107-budget-probe／air-107-docsync＋journal 收斂）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
0917 凌晨第一波開工（caller 排程提前）：M-A 三類處置的現場核驗＋落地——六支 domain skills 逐支核（遷出 vs 留＋desc 瘦身）、nt 對 desc 瘦身、instruction-testing AC#4 歸因修正、when_to_use 補欄六支。逐項以現場證據重驗前提（F-01 教訓）。

0917 晨：AC#1 的 usage 證據軸已落地＝references 報告（82 支三源矩陣：30 天觀測窗、invocation/read/mention 三軸、conflict matrix、零低用清單）。要點：唯一非 young 真零消費＝flow-feedback（**已退役**，首例）；frontend-ui-engineering＝保守級 merge/localize candidate（UI 三支責任互異）；swing/upgrade-nt/upgrade-sj 零低用支持既有遷出；lint-fix/python-type-gap 有直讀非零用（併入選項前提＝保 lint/type recipes）。young 清單（age<60d）不進零用判據。
0917 S1+S2（架構性處置批——bi panel 計畫＋跨 session 審閱通過後執行；收 Done 後補記）：S1 拓樸掃描（`.agent-tmp/air113/s1-topology-table.md`：81 支＝hub 53／orch 2／leaf 23／orphan-candidate 3）；S2 處置（user 拍板「搬動吧」）——swing＋frontend 遷 mosaic（`.claude/skills/` 實體＋`.agents/skills/` symlink＝CC/codex/muse 覆蓋）、reference-demotion×3（code-review-and-quality→`review-engine/code-quality-profile.md`、lint-fix→`fix-test/lint-type-recipes.md`、api-and-interface-design→`arch-thinking/interface-design.md`；parent desc 已吸收 child 觸發詞）、inbound 15 檔重指（含 ai-development-guide:48）、fleet 82→76。bi 審查修正 5 項（DO-NOT-FLAG 筆誤/mosaic stale 自述/parent desc 觸發詞等）；82→76 對帳關閉（第 6 支＝flow-feedback）。shim 退場條件：索引「前身」註記行兩個 audit 週期零命中即刪。**剩餘（「之後處理」承接）**：AC#2 四支（upgrade-nt/sj＋nt 對）遷出待 mosaic 接收評估＋codex discovery smoke；S3 雙 gate（headless probe＋confusion pairs）；python-type-gap 逐支裁。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
第一波：六支遷出評估（mosaic 無接收面→全留）＋desc 瘦身(nt對 885→782/938→873)＋kbar 佔位化＋instruction-testing 條件化＋PASS 歸因 desc channel＋when_to_use×6（commit 6435955）；剩餘 82 支長尾＋注入面複測之後處理
<!-- SECTION:FINAL_SUMMARY:END -->
