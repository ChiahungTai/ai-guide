---
id: AIR-88
title: llm-output pointer activation probe 補跑——provider 恢復後 5 分鐘收尾（AIR-85 第二支收帳）
status: To Do
assignee: []
created_date: '2026-09-13 11:46'
labels: []
dependencies: []
ordinal: 74000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## 目標一句話
補跑 AIR-85 第二支 pilot（llm-output-convention）的 activation 行為 probe（positive/nonmatch 成對）——當日因 provider 端故障（z.ai coding-plan「Model creation failed」，bridge 交叉證實）PENDING。

## baseline
main @ 開卡 commit。配方完整 staged＝ai-analysis/_tasks/09-13-conditional-loading-vertical-slice/ep.md「第二支 pilot」節（carrier home 重建＋config stage（provider 解析照 bridge glm.rs）＋canary skill 副本＋positive/nonmatch prompt；第一支同方法五輪全過的實證在同 EP「段 3 驗收證據」節）。

## 已決策（勿重辯）
- 機制面已驗證（404 tests＋三端 28,487B identical＋interface debt 試煉 PASS）；本卡只補 activation 行為證據
- 判準＝「首個 consequential action 前是否實際載入／nonmatch 未載入」＋四態；description recall 不算（AIR-87 已決策同判準）
- 若 probe 顯示 trigger 語義需調校→修 pointer 句為後續 commit（不重開 AIR-85）

## 驗收
- positive/nonmatch 各 ≥2 reps 四態記錄落本卡 notes；PASS 則 AIR-85 第二支 activation 宣稱閉合，FAIL/UNEXPECTED 則修 pointer 句
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 positive/nonmatch 各 ≥2 reps 四態記錄落卡；或 trigger 句調校後重跑 PASS
<!-- AC:END -->
