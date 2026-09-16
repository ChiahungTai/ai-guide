---
id: AIR-26
title: external-runtime 委派收法 push 化——背景 Bash exit 喚醒＋ETA-gate fallback
status: Done
assignee: []
created_date: '2026-09-05 00:17'
updated_date: '2026-09-05 01:17'
labels:
  - delegation
  - model-routing
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-05-external-runtime-push-collection/index.html
  - ai-analysis/_tasks/_archived/09-05-external-runtime-push-collection/index.html
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
收法從 LLM 層輪詢（resume-to-poll／jobs.json 輪詢）改 push：主 session 背景 Bash 掛 bridge 阻塞呼叫，exit 喚醒、完成時 1 request。〔baseline: 55d128a〕已決策勿重辯：push 優先（user 09-05）；bridge 端 ETA 階梯 YAGNI（interval 面；timeout 面要管——muse 長跑 wait --timeout 0＝forever，codex status --wait 無 0=forever（--timeout-ms 0 靜默回落 4min），timeout 到期 muse＝exit 124／codex＝exit 0＋waitTimedOut 旗標）；codex/grok upstream 不改；S2 降級＝範本預載＋落差記錄（ZCode 事件子集無 SessionEnd 定案；三家 plugin hook 皆有，grok 未安裝註解待裝）。驗收：rg 舊收法詞彙（resume-to-poll/jobs.json 輪詢/poll 收集）0 殘留＋跨檔一致＋致命 POC（背景 Bash 直呼小委派 exit 喚醒）＋範本 parse 有效/hook 直跑 exit 0（config merge 延至官方支援）。EP: ai-analysis/_tasks/_archived/09-05-external-runtime-push-collection/ep.md（EP 10 findings＋diff 審查 2 P1，2 輪全閉環）
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
收法 push 化落地：S1 三層文檔（agents/AGENTS.md＋model-routing skill/rule）＋S2 範本預載＋落差記錄；POC 雙腿實證（sleep exit 喚醒＋muse review 真實委派 1 發 0 等待 request）；審查 2 輪（EP 10 findings＋diff 2 P1）全閉環
<!-- SECTION:FINAL_SUMMARY:END -->
