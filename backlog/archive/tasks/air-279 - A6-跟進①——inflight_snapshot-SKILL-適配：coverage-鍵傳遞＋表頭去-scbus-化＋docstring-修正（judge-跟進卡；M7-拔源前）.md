---
id: AIR-279
title: >-
  A6 跟進①——inflight_snapshot/SKILL 適配：coverage 鍵傳遞＋表頭去 scbus 化＋docstring 修正（judge
  跟進卡；M7 拔源前）
status: To Do
assignee: []
created_date: '2026-10-07 23:10'
labels:
  - dutymail
dependencies: []
ordinal: 270000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-277 judge 跟進卡（codex F3＋muse F1/F3，不阻擋 A6）：inflight_snapshot.py 三處——①collect_scbus_sessions 回傳補 coverage 鍵傳遞（新 seam 已誠實宣稱但下游不轉發）②markdown 表頭「## scbus live sessions」＋footer「registry 總列」去 scbus 化＋live 語義對齊（live=未封存非存活觀測）③docstring「runner 注入形態保留」失實修正＋skills/handoff/SKILL.md :105/:116 機制敘述更新（:105 registry 唯一讀取點已非 registry、:116 OSError/CalledProcessError 同型 code 的 subprocess 路徑已刪）。時限：bridge M7 拔 scbus 源前完成。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 coverage 鍵自 seam 傳遞至 snapshot 輸出
- [ ] #2 表頭/footer 去 scbus 化＋live 語義 caveat 對齊
- [ ] #3 docstring runner 失實修正＋SKILL.md :105/:116 更新
<!-- AC:END -->
