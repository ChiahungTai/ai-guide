---
id: AIR-134
title: 派工資源計畫按時間預備——窗口感知 model 使用策略＋spine 保鮮收尾
status: To Do
assignee: []
created_date: '2026-09-18 06:07'
updated_date: '2026-09-18 06:07'
labels: []
dependencies: []
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
讓弧內派工決策（implement/review/judge 各派哪家 model）在開發週期開頭就按時間窗口預備好，窗口跨越時有信號，不靠 session 記得載 skill。含 AIR-98 遺留的 launchd 保鮮排程安裝。現況：等 bi（muse＋codex）討論載體形態後收斂範圍。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ①bi（muse＋codex）討論 verdict 收斂進 Plan（四問各有裁決與理由）②機制落地後：測試弧內派工決策可追溯且不撞尖峰窗口③窗口跨越時有更新信號（形式依收斂定案）④AIR-98 launchd 安裝或其歸屬裁決落地
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide main 4fa2db94（建卡時 HEAD）〕

〔已查證勿重查（2026-09-18 本 session 盤點）：①政策面已上線——spine `model-runtime-entitlements` 尖峰減用政策（09-16 user 裁定：平日 14:00–18:00 GLM 3× 窗 GLM 系減用→實作/修正迴圈改派 muse、review 走 codex＋flash、judge 改 codex、18:00 後恢復常態）＋model-routing skill「窗口語義（重置週期正典）」節；本卡不重辯政策值②DispatchPlan 是派工當下 on-demand 判斷（resolver 七步）——session 漏載 model-routing skill＝無計畫，靠模型記憶＝drift 風險③spine 保鮮半人工：AIR-98（Done）已交付 scripts/probe_entitlements.py＋29 tests＋launchd plist 版控（deploy/entitlements-probe.plist）但排程待安裝；現行保鮮靠 /usage-ping 手動＋session 開場讀 as-of④「開發週期開始時產生 template」從未立卡（user 09-18 記憶確認）——原構想（產一份文件）與 user 方向（減冗餘、byproduct 化、零新增常駐文件）衝突，載體形態待定⑤今日實證：guide-129 session 13:37 察覺 14:00 尖峰搶派 flash——人工 aware 而非機制 aware〕

〔UC 草案 v1（待 bi 討論）：主要消費者＝主 session（dispatcher 角色）／EP 開工段。情境＝多弧並行下派工決策散點當場判斷、時間窗口在弧中途跨越。期望行為＝開發週期開頭取得「此時各工作單元類型該派誰」的計畫（依牆上時間×窗口表×spine 現值），窗口跨越時有更新信號，降級顯式。成功條件＝不撞尖峰、flash 零額度時段被利用、零新增常駐文件〕

〔待 bi 討論四問：Q1 計畫載體形態——(a) EP 段落 0 固定小節（開工順手寫、零新文件）(b) model-routing skill 增「arc dispatch plan」格式節 (c) 不產文件、派工當下查表 checklist 化 (d) launchd/cron 窗口邊界（14:00/18:00/23:00）向活躍 session 發信號；Q2 窗口跨越的更新機制歸誰（cron／skill 條文／派工前自檢）；Q3 AIR-98 launchd 安裝併入本卡或另卡；Q4 spine stale/unknown 時 fail 行為沿用既有 hard invariant（stale/unknown 永不當 available）是否即足〕

範圍與 AC：待 bi 討論收斂後回填本段。
<!-- SECTION:PLAN:END -->
