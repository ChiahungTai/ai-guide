---
id: AIR-115
title: guides-refactoring 分類治理第一波——closure 三層閘＋無主機械批
status: In Progress
assignee: []
created_date: '2026-09-16 16:17'
updated_date: '2026-09-16 16:19'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/0917-guides-refactoring/ep.md
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AI 協作指南分類體檢的修正第一波：把「宣稱有防線但沒實作」的結案漏洞寫成驗收契約（closure 三層閘，acceptance-evidence 增節），順手清已查證的機械殘留（rules 重複句 pointer 化、trading mosaic 模組名、codex 設定檔過期條目），並產出 AIR-100 開工交接包。其餘議題分流歸 AIR-100／AIR-113。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 S0 acceptance-evidence 增節 AC-S0-1~4 全綠（EP 驗證式）
- [ ] #2 S1 四項機械批各自 AC 綠（S1.1 依查證分支）
- [ ] #3 S2 air100-handoff.md 三段結構＋快照前置完成
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 53f6362〕〔已決策勿重辯：①三層切分——AIR-100 修 enforcement truth／AIR-113 修 skill ownership／本卡只做跨卡 decision contract＋無主機械批（codex 建議＋caller 裁決採納）②S1.1＝查證後決策項非錯置修正（judge F-01 裁決——upgrade-flow 骨架文本支持原句非 bug，mosaic runtime 查證後分支處置）③modern-cli-preference 先 pointer 化、退役執行 defer 到 fd-.gitignore 非 bootstrap 驗證④deploy 不在本卡 scope＝user gate〕範圍＝S0 closure 三層閘（acceptance-evidence 增節）＋S1 機械批四項＋S2 AIR-100 handoff 包（含快照前置）；AC 與驗證式唯一源＝references EP
<!-- SECTION:PLAN:END -->
