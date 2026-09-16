---
id: AIR-116
title: 跨 harness memory 治理統一安裝包——單一 plugin/套件覆蓋 muse/CC/ZCode/codex
status: To Do
assignee: []
created_date: '2026-09-16 22:09'
labels: []
dependencies: []
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
現在的記憶防線是四套各自註冊（muse plugin、CC settings、ZCode config、codex inline hooks）。user 提出：長期應由 ai-guide 產出單一治理套件，各 harness 一鍵安裝同一套閘與 sensor，消除四處註冊面的維護漂移。前置＝AIR-100 政策落地（D1-D5＋closure 契約）後再收斂成形。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 單一套件來源覆盖四家安裝面（或明文記錄某家不可行的機制證據）
- [ ] #2 安裝/升級/approve 運維程序單一源
<!-- AC:END -->
