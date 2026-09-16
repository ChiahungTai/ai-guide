---
id: AIR-38
title: 四家比較路由反饋修訂——handoff tier 欄／架構級 EP 出口／開卡屬性標註（六項）
status: Done
assignee: []
created_date: '2026-09-07 04:53'
updated_date: '2026-09-07 05:30'
labels:
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-07-routing-feedback-tier/ep.md
  - ai-analysis/_tasks/_archived/09-07-routing-feedback-tier/
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
基於 mosaic 0906/07 四家模型比較修訂 ai-rules 路由三處（handoff 建議執行 tier 欄、external-runtime 架構級 EP 角色行、開卡風險屬性標註）＋flash off-peak 但書＋自報元資料不可信 claim＋旗艦 tier 資格條款（五項）＋單一源掃描〔baseline：ai-rules 50230b3〕〔已決策勿重辯：①路由詞彙一律「旗艦/一般」tier 抽象（user 拍板）——模型名只在解析層，family 軸是第二軸非 tier 降級；②tier 詞彙體系（full/lite/vision）不動——只擴充出口；③四家比較結論已定案不重推，證據自包含於任務家 spec；④G 項分層——資格條款（五項）進大綱層、同 tier 強弱排行是註記層不進條款，與 tier token 同構；⑤G 入選驗法＝既有比較尺跑一弧實測，不建獨立 benchmark；⑥實作排在 AIR-37 之後（execution-plan SKILL 同檔避撞）〕〔驗收：①七項 A-G 逐項落地或記錄不採納理由；②F 的 rg 掃描證據（改動定義引用面清單）；③tier 詞彙一致性——旗艦/一般（tier 層）vs 模型名（解析層）不混用；④G 資格條款與強弱註記分層落地（條款在大綱、坐位註記在解析表側欄單行）〕
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
四家比較路由反饋七項落地：handoff 十欄 schema（tier 欄＋卡歸屬）、架構級 EP family 出口（gate 六條）、旗艦資格條款五項＋坐位註記、開卡屬性標註、自報元資料 claim、詞形統一（隨意→一般）；雙家族 review（GLM 11＋muse 5）全吸收、muse 實作 11/11 驗收、D1 fixture ripple 修復 76 tests passed
<!-- SECTION:FINAL_SUMMARY:END -->
