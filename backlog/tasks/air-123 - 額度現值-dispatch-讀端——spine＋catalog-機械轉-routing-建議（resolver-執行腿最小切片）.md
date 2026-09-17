---
id: AIR-123
title: 額度現值 dispatch 讀端——spine＋catalog 機械轉 routing 建議（resolver 執行腿最小切片）
status: To Do
assignee: []
created_date: '2026-09-17 11:28'
updated_date: '2026-09-17 11:28'
labels: []
dependencies: []
ordinal: 108000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
每次派工前，AI 都在手工讀 memory spine 額度現值＋對 catalog family 表組 flags——執行漂暴露面。探測寫端已自動化（AIR-98 probe_entitlements.py＋launchd），缺的是讀端：一個 script 把 spine 現值＋catalog 機械轉成『此刻可派誰／什麼 effort／誰禁派』的建議卡，未知態 fail-closed。等 user 開工拍板。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@3dea384〕

〔已決策勿重辯：①定位＝六層架構段 3 最小切片（bi 審查 job-mu59xt4g/uzdogu 已裁：執行腿程式化、判斷腿留 protocol；Q4 約束＝dispatch 時讀現值禁 bake、probe 輸出事件行追加）②寫端已存在不動：AIR-98 probe_entitlements.py＋launchd（Done）③準則接線：機械讀取面（spine）寫入權歸屬照 AIR-121 準則——本卡只做讀端④判斷腿不動：contract 形成、eligibility 六條、override 解讀留 LLM protocol（AIR-91）⑤輸出＝建議卡非代派：tri-state availability＋candidate 建議＋DispatchTrace 草料，LLM 消費後自行派工⑥未知/stale fail-closed：spine as-of 過期或缺 family 記錄→unknown，禁猜 available（ AvailabilitySnapshot tri-state 教義）⑦對照語料：本 session 8 次手工派工紀錄（muse/codex/GLM）＝第一組驗收對照〕

範圍——新增：skills/model-routing/scripts/availability_snapshot.py（讀 ~/.agents/memory-spine/reference_model-runtime-entitlements.md＋skills/model-routing/catalog.toml → 輸出 per-family 建議：available/unavailable/unknown＋model/effort 建議＋禁派清單＋as-of 新鮮度警告；exit 契約 0/1/2）；tests/test_availability_snapshot.py（fixture：spine 樣本固化）；skills/model-routing/SKILL.md「AvailabilitySnapshot」節加一行執行器指針。
明示不動：spine 本體、AIR-98 probe、catalog schema、resolver 判斷腿條文、bridge。
AC：①script＋tests（spine 樣本 fixture、stale 偵測、未知 family fail-closed）②本 session 8 次手工派工回放：script 建議與當時手工判讀一致率報告③SKILL 指針在場④instruction-writing 審查閘（boundary 跨家族）。
<!-- SECTION:PLAN:END -->
