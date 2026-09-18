---
id: AIR-134
title: 派工資源計畫按時間預備——窗口感知 model 使用策略＋spine 保鮮收尾
status: To Do
assignee: []
created_date: '2026-09-18 06:07'
updated_date: '2026-09-18 06:33'
labels: []
dependencies: []
ordinal: 116000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**〔superseded 2026-09-18 → AIR-135.1，退休不實作〕**本卡連同 AIR-134/DRAFT-12 重整已由 AIR-135 program 承接：Arc compiler 設計全數吸收進 AIR-135.1（ArcPlan＋DispatchSlice 兩層、雙 authoritative 值 fail-loud、窗口跨越 recompile、真弧 dogfood、零常駐文件；bi 決策 S3 fallback playbook 一行亦由 135.1 承接），且依 AIR-135.2 card-first 裁決將「full-tier 無 EP 指針 fail loud」反轉為「不存在 mandatory EP pointer 假設」。下方 plan/notes 為 bi 雙腿收斂原文，留作設計歷史；本卡不再開工。

讓弧內派工決策（implement/review/judge 各派哪家 model）在開發週期開頭就按時間窗口預備好，窗口跨越時有信號，不靠 session 記得載 skill。含 AIR-98 遺留的 launchd 保鮮排程安裝。現況：等 bi（muse＋codex）討論載體形態後收斂範圍。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 ①bi（muse＋codex）討論 verdict 收斂進 Plan（四問各有裁決與理由）②機制落地後：測試弧內派工決策可追溯且不撞尖峰窗口③窗口跨越時有更新信號（形式依收斂定案）④AIR-98 launchd 安裝或其歸屬裁決落地
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide main 4fa2db94（會隨開工重確認）〕

〔原文定位（sess_7ee5e230 msg_mu59q4nf，09-17 16:29 user 逐字）：「深度思考這件事，如果將整個開發流程一起考慮，有個template 連原本放在memory spine的 model 建議guide line 都程式化呢？可能從開卡之後 的動作都能機械性產生整個給Llm跑的指導手冊，每個階段觸發不同模式？llm 主要做他擅長的？〔arch-thinking〕整體架構後跟 muse, codex 討論？」〕

〔已落地勿重做：AIR-98 Done（L1 probe，launchd 待安裝——另卡）／AIR-121 Done（寫入權正典）／AIR-123 Done（L3 讀端）／L0 catalog＋L4 bridge 在場〕

〔已決策勿重辯（0918 bi 雙腿一致，詳 notes）：①JIT compiler——純函式 stdout 現算、零常駐文件，audit 走 dispatch receipt②條文引用不 inline，inline 僅 instance data③ArcPlan（穩定）＋DispatchSlice（揮發、dispatch 前重算）兩層；迴圈中不換 family④輸入＝ArcSpec ephemeral projection（卡＋Contract／EP pointer→正規化；雙 authoritative 值 fail loud；full-tier 無 EP 指針 fail loud）⑤第一步先定 ArcSpec＋single-source contract 再寫 compiler（codex「若只能做一件事」雙腿認可）〕

〔與 DRAFT-12 耦合：Q4 收斂＝compiler 假設 A（EP 為 full-tier 決策唯一源、卡 Plan 瘦指針）＋ArcSpec adapter 使 compiler 對 DRAFT-12 最終裁決免疫〕

範圍（待 user 拍板後細化）：S1＝ArcSpec／single-source contract 定義（與 DRAFT-12 收斂同批條文工作）；S2＝ArcPlan＋DispatchSlice 編譯器（純函式＋pytest）；S3＝model-routing fallback playbook 一行＋work-order 模板接線；S4（可選）＝debug 落檔形態。

AC：①S1 contract 條文經 instruction-writing 閘審查②compiler 純函式 pytest 綠（含窗口跨越 recompile、雙 authoritative 值 fail loud、full-tier 無 EP fail loud、unknown→PENDING playbook）③真弧 dogfood 一次：ArcPlan 產出＋兩階段 DispatchSlice 現算與實際派工一致④零新增常駐文件（弧收尾 tree 對照）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0918 盤點修正】早版 plan 寫「開發週期開始時產生 template 從未立卡」有誤——原構想（09-17 16:29）同段對話已結晶出 AIR-121/123 兩卡（皆 Done）；未立卡剩餘段＝「開卡後機械產生指導手冊」編譯器（六層架構 L2/L3 剩餘），本卡 scope 已改寫。原文逐字與六層對照見 plan。

【0918 bi 雙腿收斂（muse job-mu6ku5gf＋codex job-mu6kuaxw，九題零分歧）】①形態＝JIT compiler 純函式 stdout 現算（落檔即 stale）；落檔僅 opt-in debug；durable audit 走既有 job log 的 dispatch receipt（inputs digest＋resolved model＋phase），手冊本身不 authoritative②引用 skill 不 inline，inline 僅 instance data（phase/role/scope/model flags/window）；external carrier 讀不到 workspace 時在 transport boundary materialize＋附 source path/hash（transport payload 非第二真相源）③兩層：穩定 ArcPlan（phase graph）＋揮發 DispatchSlice（每次 dispatch 前 JIT resolve，AIR-123 讀端唯一真相源）；迴圈中不換 family、新階段才切④輸入契約＝ArcSpec ephemeral projection：input adapter 把（卡＋Planning Contract／EP pointer＋parent anchors）正規化，同欄雙 authoritative 值 fail loud；ArcSpec 禁持久化；容忍 EP 缺席但 full-tier 無 EP 指針＝fail loud 不編譯⑤launchd 安裝另卡；stale/unknown 沿用 hard invariant＋model-routing 補 fallback playbook 一行（unknown→PENDING＋保守預設：實作 muse／review 延後、不自動派 web 池）⑥codex 單獨建議採納：先定 ArcSpec＋single-source contract 再寫 compiler（否則把 ambiguity 程式化）。範圍與 AC 回填见 plan。
<!-- SECTION:NOTES:END -->
