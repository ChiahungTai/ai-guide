---
id: AIR-143
title: 規劃必答不做與刪除現有——design-thinking 比較條 delete-first rewrite
status: To Do
assignee: []
created_date: '2026-09-19 21:15'
updated_date: '2026-09-19 21:18'
labels: []
dependencies: []
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【authoring receipt】accepted 114c7acca5f50620 2026-09-20
<!-- SECTION:NOTES:END -->
