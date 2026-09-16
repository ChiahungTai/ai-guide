---
id: AIR-51
title: sub-agent 派發模型路由寫法修補——內建型別繼承語義補洞
status: Done
assignee: []
created_date: '2026-09-09 00:50'
updated_date: '2026-09-09 03:26'
labels:
  - docs
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-09-subagent-model-routing-fix/index.html
  - ai-analysis/_tasks/_archived/09-09-subagent-model-routing-fix/index.html
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
補洞常犯錯：ZCode 內建 general-purpose／Explore 無 pin 繼承主 session 旗艦（qa.md:95 設計行為），session 誤派它跑 lite 機械任務＝旗艦燒機械段（AIR-50 弧兩次實例）——模型路由寫法四層修補＋roles tier 標籤＋registry regen＋三端部署。〔baseline：ai-rules 083ffff105d0c0c5b1872e974942402ef226d5c9〕〔已決策勿重辯：①四層承載（rule 表列／skill 深層／消費側檢查點／agents 治理節）＋roles description 只用 tier 詞禁 model 名；②否決設定頁釘死 general-purpose→flash（無能力上界 fallback 靜默降級）；③spawn 型別規則限縮 lite／機械場景——唯讀探察＝內建 Explore 承接（EP Review F1）；④muse bundle by-design 不含 model-routing〕〔驗收：tier 標籤三目錄 10/10/10；內建列 zcode/codex bundle＋Claude rules 三處在場；sync --check exit 0；bundle<gate（74.7KB/90KiB）；dogfood 面（新 session 不再誤派）非本弧 gate〕EP：ai-analysis/_tasks/_archived/09-09-subagent-model-routing-fix/ep.md（docs mode；EP Review 一輪 4 findings 全採納回寫；已落地 7836f08）
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 四層修補＋索引同步＋tier 標籤落地（rg 可驗）；commit 帶本弧 35 檔＋EP 任務家；結案含 memory 蒸餾（reference 條目對齊＋feedback_dispatch-model-tier-glm53 :12/:14 錯誤表述必改）
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
四層修補（rule 內建列/skill 派發段/agent-workflow 檢查點/agents 治理節）＋roles tier 標籤 10/10/10＋registry regen 三端部署落地（7836f08，dual-context 複審＋judge 修正完）
<!-- SECTION:FINAL_SUMMARY:END -->
