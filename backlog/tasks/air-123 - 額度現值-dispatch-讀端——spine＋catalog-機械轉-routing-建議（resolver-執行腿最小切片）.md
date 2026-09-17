---
id: AIR-123
title: 額度現值 dispatch 讀端——spine＋catalog 機械轉 routing 建議（resolver 執行腿最小切片）
status: Done
assignee: []
created_date: '2026-09-17 11:28'
updated_date: '2026-09-17 13:47'
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
〔baseline：/Users/ctai/Github/ai-guide main@dff0815〕

〔已決策勿重辯（tri 三腿覆核後修訂版——job-mu5gjcrh/uzdogu＋GLM fresh 腿）：①定位＝六層架構段 3 最小切片；evaluator-not-router——輸出命名 availability evaluation，禁 selected/rank/fallback/『下一個派 X』欄位②exit 契約統一 0/1/2/3：0 fresh 產出／1 無法判定 fail-closed（as-of 缺席、可用行解析失敗）／2 輸入缺席／3 stale→unknown——三處歷史不一致（卡 0/1/2、POC 0/2/3、AIR-121 AC 0/1/2/3）以本版為準③family→binding 映射正解＝catalog [[dispatch_binding]] 加顯式 family 欄（閉集 enum：glm/muse/codex/anthropic/xai）＋loader fail-loud 驗證——GLM 實查舉證：surface 後綴只覆蓋 bridge 面（zcode-registry surface=agent-definition、cc-registry-opus 無 family 字面），surface heuristic 為會漂的路、明確拒絕；family＝穩定供給事實，在 catalog 所有權宣告管轄內、非 volatile、不在 loader 拒絕清單④totality validation AC（codex）：新 binding 未映射／映射到不存在 binding／重複衝突→全 fail-closed⑤codex 兩池回歸 AC：native usage-limit 訊號≠web 池耗盡——per-family note 逐字保留 spine 原文指針禁壓縮⑥8 次手工派工回放＝behavior parity 最低層（spine 目錄不版控、歷史態不可重放——SAMPLE 級），須升級：tri-state 三分支覆蓋（≥1 stale、≥1 unavailable、多數 available）＋bridge ledger 當 ground truth＋輸出不變量（unknown 永不與可派並存）⑦判斷腿不動：contract 形成、eligibility 六條、override 解讀留 LLM protocol⑧前置＝修 POC 帶病（wrong keys：取了 catalog 不存在的 model/effort/family 欄；muse 垃圾樣本實證）⑨審查紀錄：bi job-mu59xt4g/uzdogu＋tri job-mu5gjcrh/mu5gjcsm＋GLM fresh 腿〕

範圍——改：skills/model-routing/catalog.toml（dispatch_binding 加 family enum 欄＋sync_agents.py loader 同步驗證）；skills/model-routing/scripts/availability_snapshot.py（新：讀 spine＋catalog→availability evaluation）；tests/test_availability_snapshot.py；skills/model-routing/SKILL.md（AvailabilitySnapshot 節執行器指針）。
明示不動：spine 本體、AIR-98 probe、resolver 判斷腿、bridge。
AC：①catalog family 欄＋loader fail-loud（未知 family 值拒載）②availability_snapshot.py 四態 exit 各有 pytest（stale 邊界恰 3/4 天、as-of 缺席、可用行 vs 禁派事件衝突態、malformed 可用行 WARN 不 crash）③family 覆蓋斷言（每 family ≥1 binding 或顯式 no-binding 行，禁靜默）④8 回放＝behavior parity leg（bridge ledger ground truth）⑤SKILL 指針⑥instruction-writing 審查閘（boundary 跨家族）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
結算（final）：落地 main 7b8e420＋deploy 3/3。catalog family 欄（9 binding 歸屬凍結＋loader fail-loud 雙向）＋availability_snapshot.py（evaluator-not-router）＋31 tests。審查鏈：tri 三事項 panel 裁定→spec 修訂→flash 實作→fresh 腿 7 findings→R2 修復（衝突配對收緊等）。AC④ 回放：15 次 bridge 派工全完成 vs snapshot available 零矛盾。殘留：live keyword 掃描限制（能力序裁定行）接受並 SKILL 明示非窮興。
<!-- SECTION:NOTES:END -->
