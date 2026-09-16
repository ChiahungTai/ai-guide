---
id: AIR-37
title: memory 卡資訊生命週期閘門——commit 對帳腿＋開卡登記腿
status: Done
assignee: []
created_date: '2026-09-07 04:39'
updated_date: '2026-09-07 05:21'
labels:
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-rules/ai-analysis/_tasks/_archived/09-07-memory-card-lifecycle-gate/ep.md
  - ai-analysis/_tasks/_archived/09-07-memory-card-lifecycle-gate/
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
把弧結案蒸餾（memory 卡流水清理）從流程自覺升為機械保證：commit skill 2.8 對帳閘門加 memory 池對帳腿（卡 id 掃描→命中三分→流水當場蒸）；execution-plan UC 盤點加同主題 memory 條目登記（存量債隨弧消化）〔baseline：ai-rules 8e9915e〕〔已決策勿重辯：①蒸餾方法論單一源在 memory-audit/kanban 既有條文，兩腿只引用不重抄；②判斷形態＝機械掃描列命中＋LLM/user 判歸屬（2.7/2.8 同構），不做純 hook（卡語義判斷難）；③存量債（21 條 project_ 130KB＋6 檔流水詞）不在本弧清——出口＝夜波/audit 波段，EP 記指針；④活知識錨（教訓索引）保留非清理對象〕〔驗收：①commit skill 2.8 含 memory 對帳腿條文（卡 id 掃描＋三分歸屬＋流水當場蒸＋命中清單入報告）；②execution-plan UC 盤點含同主題 memory 登記行（結案蒸餾範圍語義）；③跨檔詞形一致（rg 三分歸屬詞形兩檔對齊）；④單一源不重抄（2.8/UC 盤點引用 memory-audit 蒸餾條文而非複製）〕
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
memory 卡流水結案機械對帳落地：commit 2.8 池對帳腿（掃描鍵聯集＋結案態前置＋三分歸屬）＋execution-plan UC 盤點登記腿（獨立子步＋模板槽位）；雙家族 review（GLM 7＋4、muse 5）全吸收、muse 實作 9/9 驗收
<!-- SECTION:FINAL_SUMMARY:END -->
