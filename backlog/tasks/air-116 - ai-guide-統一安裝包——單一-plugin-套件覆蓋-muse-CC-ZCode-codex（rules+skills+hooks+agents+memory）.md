---
id: AIR-116
title: >-
  ai-guide 統一安裝包——單一 plugin/套件覆蓋
  muse/CC/ZCode/codex（rules+skills+hooks+agents+memory 防線）
status: In Progress
assignee: []
created_date: '2026-09-16 22:09'
updated_date: '2026-09-17 03:27'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/0917-air116-unified-governance/ep.md
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
原範圍（0916 user 提出）＝memory 治理防線四套各自註冊（muse plugin、CC settings、ZCode config、codex inline hooks）收斂為單一套件。**0917 user 擴範圍：套件＝ai-guide 整體，不限 memory**——部署面全部收斂：rules bundle（四家 guide 投影）、skills 共享根、hooks×三家註冊、agents registry（sync_agents 生成面）、memory 治理防線——各 harness 一鍵安裝同一套，消除多處註冊面的維護漂移。

分工邊界：本卡＝套件載體與內容物（what——打包單元、per-harness 安裝面、approve/升級程序）；[AIR-110](air-110 - 全新機器一鍵安裝-bootstrap——hooks×3-家＋symlink-活視圖＋bundle-部署＋驗證探針.md)＝全新機器安裝執行器（how——bootstrap 腳本、驗證探針）——110 開工時改為消費本卡套件（對齊動作列兩卡）。前置＝AIR-100 政策落地（D1-D5＋closure 契約）後再收斂成形。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 單一套件來源覆蓋四家安裝面×全部 ai-guide 部署面（rules/skills/hooks/agents/memory 防線——或明文記錄某面某家不可行的機制證據）
- [ ] #2 安裝/升級/approve 運維程序單一源
- [ ] #3 與 AIR-110 bootstrap 分工對齊（110 消費本卡套件或明文記錄邊界）
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
0917 user cross-ref：AIR-113 domain-skills 遷出後的「ZCode 端 skills desc 注入」缺口，未來解法＝ZCode plugin 打包（marketplace 本地目錄源）——本卡擴範圍後 skills 分發面已在 scope 內，該場景為本卡用例之一（決策記錄仍在 AIR-113）。
<!-- SECTION:NOTES:END -->
