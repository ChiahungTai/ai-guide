---
id: AIR-130
title: >-
  pr-lens 整合 slice 1——mosaic deterministic producer（tour＋graph.db 雙源→graph
  document→upstream validate/render）
status: To Do
assignee: []
created_date: '2026-09-17 22:36'
updated_date: '2026-09-17 22:38'
labels: []
dependencies: []
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**〔superseded 2026-09-19 → AIR-135.4，退休不實作〕**user 裁決吸收：pr-lens deterministic producer 是 AIR-135.4 Code Lens（canonical fact layer→derived view）的首個 implementation slice，即「視圖禁手抄、必須機械生成」的具體化。本卡 plan 全文（tri 三腿定案＋slice-0 POC＋範圍 AC）已移轉 135.4 Implementation Plan 節；本卡 archive 留檔。

把 mosaic 弧收尾的 SA viewport 自動化：deterministic producer 從 delta tour（變動面）＋graph.db（模組關係）雙源產 pr-lens graph document，經 upstream validate/render 出動畫 SVG。slice 0 POC 已驗（CJK PASS/determinism byte-identical/strictObject 拒 extension→provenance 走 sidecar/成本 30min+160 行）。tri 三腿設計定案：零 fork 消費 upstream、LLM 退出 document 路徑、.tour 凍結面不動。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：mosaic main＋ai-guide main（合併波後取當下值回填）〕

〔已決策勿重辯（tri 三腿＋slice 0 POC）：①POC 已驗：CJK 渲染 PASS（text.ts isWide 覆蓋）/determinism 兩次 render byte-identical/strictObject 拒 extension 欄（.strictObject 源碼證）→provenance/coverage/known-unknowns 走 sidecar 檔不進 document②零 fork：npx @coldtea/pr-lens-cli 消費 upstream（參考 checkout /Users/ctai/Github/pr-lens @ 1678527；本地 prlens/ 同名異專案已移除——禁憑名檢出）③producer＝Python 住 mosaic tools/prlens/——**雙源**：delta tour（變動面 nodes/delta colors）＋graph.db（模組關係 edges——slice 0 實證 tour 不帶關係、edge 必須查 graph.db；29709 raw edges 在庫）④LLM 退出 document 路徑——事實層全 deterministic；lane 命名/敘事＝overlay/sidecar 層輸入（後續 slice）⑤.tour/AIR-80 manifest 凍結面零改動；雙軌呈現（同 arcId 互鏈、殼 diagram slot 交會）⑥Id 禁中文→slug 規則（path 本身近合法）⑦walkthrough 原生在場（schema walkthrough.ts）——行級軌用原生承載不自造⑧消費點＝弧收尾 ask-once（sa= triage 訊號行照 smell= 前例）；map export 累積→AIR-122 freshness 閘泛化管轄⑨觸發制（boundary/topology 弧）非常態⑩成本基準：slice 0 手寫映射 ~160 行 30min——producer 自動化此曲線〕

範圍——mosaic repo（worktree mos-prlens-slice1 from mosaic main，純新增檔案）：tools/prlens/producer.py（輸入 arcId→找 snapshot pair＋delta tour→nodes/lanes/deltas＋graph.db 邊查詢→graph document＋sidecar）；tools/prlens/tests/。明示不動：.tours/ 本體、mosaic 其他檔、ai-guide 側條文（指針另卡）。
AC：①producer 對一條既有弧產 document，npx validate PASS ②render 兩次 byte-identical ③同輸入 producer 重跑 byte-equal ④edges 全來自 graph.db 查詢（禁 tour 推測/禁 LLM）⑤CJK lane 名渲染 PASS（SVG text 元素驗證）⑥.tour 與 manifest 零改動（git diff 對照）⑦pytest 綠⑧sidecar 帶 provenance（snapshot sha/tour path/graph.db 錨）。
<!-- SECTION:PLAN:END -->
