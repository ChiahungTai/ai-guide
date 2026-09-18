---
id: DRAFT-12
title: >-
  EP 與卡結構評估——full-tier 雙載體冗餘削減（單一源邊界／分級收緊／EP 模板按需化）。源：0918 pr-lens 整合討論
  session，user 方向＝先固定開發流程再優化、省略冗餘步驟；與 AIR-134（派工資源計畫）同批 bi 討論
status: Draft
assignee: []
created_date: '2026-09-18 06:20'
labels: []
dependencies: []
---

> **〔superseded 2026-09-18 → AIR-135.2〕**Muse 直接讀 Backlog.md source 後推翻本 draft 的 Q6／Q9 裁決：Task 原生承載 Description／AC／Plan／Notes／Comments／Final Summary＋nested parent/subtask，Plan 原生可 replace/append，官方 guideline 把 task 當 plan of record——「EP 獨佔決策面＋卡瘦身指針」的 A 類收斂不再成立，方向改走 AIR-135.2 card-first migration＋EP 退場 dogfood（Q9 的 D 收斂條件「所有 consumer 改讀 logical Plan API」即 135.2 AC#4）。本 draft 仍有承接價值的條目：Q8 retrospective（抽樣最近 5-10 張 full EP 驗證 section 實際消費）→ AIR-135.2 AC#1；Q7 full_trigger contract（evidence 一行的分級 trigger）→ AIR-135.2 於 standard/full 分級收斂時再裁。決策理由與「改案必留 supersedes + reason/evidence」契約見 AIR-135.2。

## Bi 收斂（2026-09-18，muse job-mu6ku5gf＋codex job-mu6kuaxw，九題零分歧）

- **Q6 單一源邊界**：EP 獨佔＝技術 baseline／邊界決策／scope 權威／Scenario Matrix／test contract／kill criteria／review ledger；卡獨佔＝identity／人話目標／lifecycle／tier／refs／AC／final summary；full-tier 卡 Plan 只留 tier＋EP pointer＋1-2 句人話，禁再抄 baseline/scope/decisions；EP 對照 acceptance 引用卡 AC ID 不重抄；指針腐爛＝相對路徑＋首行錨 fail-loud。
- **Q7 分級**：不做 scoring——**full_trigger contract**（kind: state_ownership｜public_contract｜cross_context_invariant｜control_plane_authority｜architecture｜red_risk＋evidence 一行）；無 trigger 回 standard；machine 只驗欄位、LLM 判語義；escalation 沿用現行 promotion。
- **Q8 EP 模板按需化**：Report Shell 改 user 要看才生成（最明顯 YAGNI）、段落 0 只在 load-bearing unknown／新 mechanism／reuse 不明、POC/kill criteria 只對可證偽假設；每個 optional section 必須有 observable trigger（禁「視情況」）；決策理由永不按需；落地前對最近 5-10 張 full EP 做 retrospective 驗證哪些 section 真被消費。
- **Q9 真合併（D）**：不做——A+B+C 吃掉大部分痛點且可逆；D 未來收斂條件＝task 永久化＋structured attachments＋所有 consumer（ep-review/ep-validate/delta_tour/producer）改讀 logical Plan API。
- **與 AIR-134 耦合**：本裁決（A 類收斂）＝ArcSpec compiler 假設的輸入契約；S1 contract 條文工作與本 draft promote 同批推進。
- **待 user 拍板**：promote 成卡（條文變更觸 instruction-writing 閘，落地前走審查腿）。
