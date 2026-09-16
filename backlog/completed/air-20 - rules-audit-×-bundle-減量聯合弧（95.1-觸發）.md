---
id: AIR-20
title: rules audit × bundle 減量聯合弧（95.1% 觸發）
status: Done
assignee: []
created_date: '2026-09-03 22:09'
updated_date: '2026-09-03 22:50'
labels:
  - governance
  - bundle-diet
  - memory-audit
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-04-rules-bundle-diet/ep.md
  - ai-analysis/_tasks/_archived/09-04-rules-bundle-diet/ep.md
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
bundle 87,676B＝gate 92,160B 的 95.1%（09-03 兩日 +9,776B，來源＝AIR-19 WO-5 rule 手術批 11 檔＋AIR-18 L4）。觸發線 ≥93% 已過，draft rules-audit-bundle-diet-joint-arc promote 開工。範圍：①使用度腿（inbound pointer＋git 活躍度）②價值腿（always-on 正當性、降 skill on-demand 候選——reference 分層先例 acceptance-evidence/lsp-navigation）③合併腿（重疊 rule 對）。交付＝advisory 清單→user 裁決→執行減量→deploy gate 驗證。小弧 1 session，先例 bundle-diet-wave2（88KB→81KB）。〔baseline：ai-rules 8d3c6f6（實測 HEAD；desc 原寫 d121837 為 tail note 過時值，09-04 muse review F3 勘正）〕EP：ai-analysis/_tasks/09-04-rules-bundle-diet/ep.md（S1-S5，A2/A3 out-of-scope 待裁）
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Census 09-04：bundle 87,676B（95.1% gate 92,160B／WARN 85%=78,336B）。重量 top：tool-discipline 9,059(10.3%)、collaboration 7,561(8.6%)、acceptance-evidence 7,316(8.3%)、quality 6,427(7.3%)、model-routing 5,750(6.6%)、outward 5,402(6.2%)。成長歸因（09-01→）：model-routing +41行、guide +16、tool-discipline +11——全 AIR-18/19 刻意新增。inbound 低尾：context-management/modern-cli/must-execute 各 1 file。progressive-validation 0 commits/2月。重複證據：工具路由句 modern-cli≡lsp-navigation＋tool-discipline 同義第三份；SOLID 已正確 pointer；memory 四問僅在 rule（skill 無）＝搬移候選。Advisory A1-A3/B1-B2/C1-C4 已攤 user 裁決（材料在 session 09-04 早）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
rules audit × bundle 減量聯合弧完結——S1-S4 手術（model-routing 降級/路由句去重/progressive-validation 併入/C 批精簡）；EP 雙審（muse＋GLM 15 項回寫）→ muse WO-1 → GLM reviewer accept → consistency 15 檔 2 fail 全修；bundle 87,676→81,039B（95.1%→88% gate）、deploy 3/3、死鏈抽查 0 殘留；A2/A3 out-of-scope 未裁（材料在卡 notes）
<!-- SECTION:FINAL_SUMMARY:END -->
