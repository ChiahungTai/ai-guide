---
id: AIR-29
title: AIR-29 — agents 兩軸重構：role×dispatch×harness 正交
status: Done
assignee: []
created_date: '2026-09-05 05:46'
updated_date: '2026-09-05 12:22'
labels:
  - meta
  - agents
  - ep-ready
dependencies: []
references:
  - ai-analysis/_tasks/_archived/09-05-agents-two-axis-refactor/index.html
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
registry 兩軸正交：roles/ 單一源（目標→做法→skills，零 model/harness 字樣）＋sync_agents.py 生成式投影（zcode pins＝部署預設）＋dispatch matrix 兩軸（harness 怎樣用／model 按任務選——執行檔 flash≈terra≈sol-high≈sonnet≈muse-spark、判斷檔 opus≈fabel≈sol-max+）＋external 工單 role 段引用。role 集合不動（10 role UC 已驗證），修的是部署面可達性（CC 8/10 不可達、external 無檔面）。〔baseline c83ddf4；spec+ep 在 ai-analysis/_tasks/09-05-agents-two-axis-refactor/；驗收＝CC L4 逐名啟動 10 檔＋--check 綠＋12 命令檔零改動〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
build baseline: 40f47e8（EP codex 版＋二輪 ep-review 回寫後）；舊 desc 的「12 命令檔零改動」已被推翻——驗收改為 registry name 引用完整性 rg 對帳（含語義消費者），見 EP S3
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AIR-29 全弧終結：roles/ 單一源×10＋sync_agents.py 生成式投影（parity 雙層/原子寫/碰撞防線/exit 語義分離）→ zcode+claude 10+10；dispatch matrix 兩軸（harness 軸五行＋tier×provider 五公司欄＋額度政策）；work-order §2 Role contract；agents-projection-sync invariant；舊教義六檔清零。驗證：124 tests/CC L4 10+1/三視角 24＋muse 5 findings 全採納收斂 16/16/Role contract 首消費。偏差三件記錄（adopt-legacy 等效審計/8 檔溯源/③inline）。〔baseline 40f47e8〕
<!-- SECTION:FINAL_SUMMARY:END -->
