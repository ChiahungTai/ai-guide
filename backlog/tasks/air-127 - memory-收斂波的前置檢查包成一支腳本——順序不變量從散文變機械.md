---
id: AIR-127
title: memory 收斂波的前置檢查包成一支腳本——順序不變量從散文變機械
status: To Do
assignee: []
created_date: '2026-09-17 15:08'
updated_date: '2026-09-17 15:09'
labels: []
dependencies: []
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-93 的對帳順序約束（快照提交前必須先跑異常篩，否則繞閘寫入被合法化）現在住在大段散文裡靠 LLM 照讀執行，走錯一步訊號就滅失。這卡把波前三步包成機械腳本，skill 只調用它分支。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 #1 preflight 腳本 tri-state 語義有測試#2 skill 改後「必須在流入快照提交之前」等排序關鍵詞前均有可機械執行命令#3 瘦身段保持人裁部分完整（decay 候選/quarantine 裁決不丟）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：main@f892c344〕〔已決策勿重辯：①腳本唯讀 tri-state（exit 0=clean 開波／1=無法判定停波／2=dirty 附清單）包既有 reconcile_memory_pool＋inbox age＋wave marker 檢查，不加新偵測邏輯②波次①後段（decay/觸發/regen/差異處置）仍是散文＋人裁③skill 端 memory-audit:73 巨段瘦身為「跑 preflight→按 verdict 分支」＋僅保留人裁判斷散文④源證據＝muse I-7＋memory-audit:73 實讀（單段 2000+ 字承載排序不變量）〕範圍——新增：scripts/consolidation_preflight.py；改：skills/memory-audit/SKILL.md 波前二分段。
<!-- SECTION:PLAN:END -->
