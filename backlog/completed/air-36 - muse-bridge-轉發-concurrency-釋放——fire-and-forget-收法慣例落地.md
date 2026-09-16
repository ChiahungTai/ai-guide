---
id: AIR-36
title: muse bridge 轉發 concurrency 釋放——fire-and-forget 收法慣例落地
status: Done
assignee: []
created_date: '2026-09-07 00:55'
updated_date: '2026-09-07 04:05'
labels:
  - skills
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/ai-analysis/_tasks/_archived/09-07-muse-bridge-fire-forget/index.html
  - ai-analysis/_tasks/_archived/09-07-muse-bridge-fire-forget/
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
長跑 muse 轉發從「caller session 掛背景 Bash 等 exit」升級為 fire-and-forget（--background 提交→jobId 即回→session 釋放→事後 wait/show 跨 session 認領→多工複用一 session 掃 N jobId）〔baseline：ai-rules 754f916〕〔已決策勿重辯：①--background/wait/show/runs/export 機制 bridge 0.2.5 已存在（源碼實證）勿重造；②兩端差異既存事實——ZCode 端 plugin hooks 不執行故 job 可跨 session 存活、CC 端 SessionEnd hook 殺 running job 故 holder 須活著；③此為收法慣例層文檔變更非 bridge 功能開發；④muse-rescue 契約與 callback roadmap 屬 muse-plugin-cc repo 跨 repo 不動；⑤judge 裁決層不變〕〔驗收：①model-routing skill 收法決策樹含 fire-and-forget 優先層＋兩端 hook 差異警示＋多工複用掃法且單讀可執行；②agents/AGENTS.md dispatch matrix 與 work-order.md 消費形態語義同步（rg 舊語義殘留掃過）；③memory reference_external-runtime-delegation-family 蒸餾為 fire-and-forget 階層〕
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
fire-and-forget 收法決策樹落地（skill 定義源＋AGENTS/CLAUDE/work-order/rule 四消費端同步＋兩端 hook 差異警示＋多工複用）；muse 委派實作 10/10 驗收全過、EP review 7 findings 全採納
<!-- SECTION:FINAL_SUMMARY:END -->
