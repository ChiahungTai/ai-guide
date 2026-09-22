---
id: AIR-155
title: compact 前交接準備自動化——外部化改機制觸發與恢復證明
status: Done
assignee: []
created_date: '2026-09-22 01:52'
updated_date: '2026-09-22 20:30'
labels:
  - session-lifecycle
dependencies: []
references:
  - skills/compact-prep/SKILL.md
ordinal: 141000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**這卡解什麼**：compact-prep 現況靠 LLM「記得外部化」＋compact 後靠 user 提醒 AI 讀檔——零機械觸發、零恢復證明（auto-compact 發生在外部化之前＝直接損失，實證多次）。本卡把壓縮前後的機制面交給機制：checkpoint event-driven 化、compact 時只 materialize thin continuation packet（引用 canonical state）、restore 有 restore-proven 證明、restore 證明前禁清 recovery artifact；compact-prep skill 降成 boundary adapter。

**不做什麼**：外部化內容取捨自動化（判斷面＝LLM 職權）、自製 compactor、continuation packet 成第二 workflow truth、per-turn Stop-hook 催告進正典（tri 裁決：至多有期探針）。

**開工硬 gate**：ZCode compact hook 有「0824 實測不觸發 vs 新 hooks 文檔寫支援」drift——minimal live acceptance 先行；若 compact 事件不可觀測，event-driven 的退化形態（periodic／手動／誠實 unsupported）須預寫，不能預設事件存在。

```mermaid
flowchart LR
  A["LLM 記得外部化"] --> B["auto-compact 損失"]
  C["本卡：機制承接"] --> D["event-driven checkpoint"]
  C --> E["thin continuation packet"]
  C --> F["restore-proven 證明"]
  F --> G["證明前禁清 recovery artifact"]
  D --> H["compact-prep 降 boundary adapter"]
  E --> H
```

〔已決策勿重辯〕tri 五裁決點之 5：135.6 event-driven checkpoint＋thin packet＋restore-proven 為正典；Stop-hook per-turn 催告不進正典；ZCode compact hook live acceptance＝開工前硬 gate；降級形態預寫；參數（grace／閾值）開工時定死。母卡脈絡 air-135.6（其 AC#4/#8 已寫方向）。溯源：codex job-mubyzjvf-q0rb0c＋muse tri job-muc00i2l-o7uv04＋5.3 seat；合併檔 .agent-tmp/air-135-disc/session-skills-marshal-tri-merged.md。開工時依 card Planning Contract 補 AC/Plan。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ZCode compact hook live acceptance 探針落地：fixture 產生 marker log，於真實 compact 事件後 marker 檔存在（附 path＋內容行）；或 gate 否決結論（無法觸發＋原因）——兩者擇一有機械證據
- [ ] #2 checkpoint 格式驗證函式＋test：四問可答機械判準，壞檔 fail-loud 有 test
- [ ] #3 restore-proven 判準＋test：restore 驗證通過才發 proven；cleanup 於未 proven 時被擋有 test
- [ ] #4 compact-prep SKILL.md 改版：人肉提醒句（讀 context 檔續任務）移除或降 fallback 標註；rg 檢查指針指向機制面
- [ ] #5 uv run pytest 相關測試全綠＋既有測試零退化
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔Baseline〕skills/compact-prep/SKILL.md L15-19＝現況五步驟全靠 LLM 自律＋user 手動：步驟 1 session 自錨定 SQL、步驟 2 落檔外部化、步驟 4 請 user 手動 /compact＋「明確提醒 user：compact 後開口第一句讓 AI 讀 context 檔」、步驟 5 被提醒後才讀檔；L34 ZCode SessionStart(compact) 2026-08-24 L4 終驗實測不觸發（死路記錄）；CC 側 hooks/compact-tail-inject.py 已註冊（settings.json matcher=compact，2026-08-30 接線，僅 verbatim raw tail 注入）；機制面缺口＝無 event-driven checkpoint、無 restore-proven 證明、recovery artifact 清理無 guard。母卡 air-135.6（AC#4/#8 已寫 event-driven＋thin packet 方向）。

〔已決策勿重辯〕①tri 裁決 5：135.6 event-driven checkpoint＋thin packet＋restore-proven 為正典；per-turn Stop-hook 新鮮度催告不進正典（溯源 .agent-tmp/air-135-disc/session-skills-marshal-tri-merged.md 裁決點 5＋muse job-muc00i2l）②ZCode compact hook live acceptance＝開工硬 gate：0824 舊實測 vs 新 hooks docs（ref-docs/harness/zcode）drift，探針先行程式碼；gate 否決時降級形態（periodic／手動／誠實 unsupported）預寫＋參數定死③判斷面（外部化內容取捨）不自動化＝LLM 職權④thin packet 引用 canonical state、禁成第二 workflow truth（anchor：air-135.6 卡 AC#4/#8）⑤恢復順序單一源＝skills/_common/task-recovery.md（消費不重定義）。

〔Scope〕動——skills/compact-prep/SKILL.md（降 boundary adapter 改版）；新增 scripts/（checkpoint 格式驗證＋restore-proven 判準 helper）；tests/（新增對應測試）；探針 fixture＋註冊 JSON（機器註冊由主 session 執行，worker 產材料）。不動——task-recovery.md 定義、air-135.6 卡面、skills/handoff 與 skills/at（AIR-156/157 範圍）、hooks/compact-tail-inject.py 本體（CC 側已上線，僅必要時參照）。

〔Scenarios〕①正常：compact 前外部化由機制觸發（事件或降級形態），checkpoint 檔產生且四問可答②compact 後 restore：機制先驗 checkpoint 存在＋四問→restore-proven→cleanup 才放行③gate 否決情境：探針證實 compact 不可觀測→預寫降級形態運作（文件化）④checkpoint 檔損壞→fail-loud 禁靜默續行（數據完整性優先）⑤restore 未 proven 時 cleanup 被擋。

〔Integration〕下游＝task-recovery.md 恢復順序（checkpoint 欄位相容）；AIR-156 handoff 的 completion 四段消費 restore-proven 同形概念；觸發面＝SessionStart(compact) hook（gate 通過則 ZCode 接線）＋skill 調用（fallback）；上游客戶＝每個會 compact 的 session。

〔驗證式〕見 AC 欄（機械可判：探針 marker 或否決記錄、驗證函式 test、cleanup 擋行 test、skill 文字 rg 檢查、pytest 全綠）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
0922 gate 判決（AC#1 結案）：**VETO**——ZCode 3.14 兩次獨立 /compact 實測（12:26、12:37，session sess_7deee1b7，DB compaction 記錄×4 對照 marker 零命中）皆不派發 SessionStart（無 matcher 亦然）。0824 舊實測為真，新 hooks 文檔的 compact source 真機不存在。附帶發現：session 切換會派發 SessionStart(resume)（scbus 收信注入可用點）。探針已卸載（config 備份 124302），marker 證據保留 .agent-tmp/probe/。**segment 2 設計方向據此定案：放棄 compact-moment 觸發，checkpoint 轉持續責任制**（工作中持續寫 durable owner＋restore-proven 驗證，compact 任意時刻發生皆不丢）——具體形態 segment 2 出。

2026-09-22 審計註記（lite-verify agent_01cd2439）：機制已 merge（47f9d1f4，compact-restore-inject 284 行＋tests 408 行），但 AC#1 要求之「真 compact 事件證據或 gate 否決結論」兩者皆未發生。live dogfood 排定：marshal session 內由 user 跑 /compact 觸發真實事件，驗證 restore 注入後補結論（通過→真 Done；失敗→記 gate 否決）。

2026-09-23 live dogfood 結案（AC#1 補證）：真實 compact（user /compact，sess_54554200）後首個 user prompt，hook 真觸發——AC-B gate 過（zcode DB 有晚於 baseline 的 compaction part）＋四問驗證 fail→corrupt 警示注入（fail-loud 非靜默，決策表 corrupt 分支 live 實證）。root cause＝marshal 手寫 checkpoint 缺 schema 錨定欄（寫入端缺陷；hook 行為照規格）。修復補 schema=compact-checkpoint/1 錨定欄→四問 VALID→bare python3 重放（真 DB＋真 checkpoint）→完整 thin pointer JSON（inject 分支；sha256 b56e832e）→write_restore_proven→重放 0 bytes（consumed 靜默）。corrupt（live）／inject（replay）／consumed（replay）三分支全驗；證據檔保留 .agent-tmp/compact-checkpoints/sess_54554200-b21a-4acb-b794-468f3d629ce6/。附帶發現：compact 後注入的 agentsMd＝session 開場快照非磁碟重讀（session 內 rules 再部署後 compact 不自動 refresh——Session freshness 重讀義務不受 compact 豁免）。教訓：compact_checkpoint 模組無 checkpoint writer helper，手寫 JSON 易漏 schema 欄。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
compact 前後脈絡保全落地（VETO 驅動的持續責任制設計）：scripts/compact_checkpoint.py（四問驗證/restore-proven hash 綁定/cleanup guard）＋hooks/compact-restore-inject.py（UserPromptSubmit sync 注入：compaction 記錄代理閘防誤拿——gate 過＋未消費→thin pointer 注入；gate 過＋已 proven→re-restore 注入；fail-open 全程）＋SKILL.md 降 boundary adapter（持續外部化義務清單＋人肉依賴句零殘留）。settlement fresh reviewer pass（F1 註冊材料進版控 hooks/＋F3 re-restore 語義翻轉——reviewer 可推翻條款成立＋F4 schema 驗證；marshal judge 應用）。focused 71＋全套 1403 綠。機器註冊完成（backup 182954、installer 五面 parity 綠、新 session 生效）。live restore dogfood：下次真實 compact 事件驗證。附帶：gate 實驗推翻 zcode 文檔 compact source（drift 回報鏡像流程）。

```mermaid
flowchart LR
  W["工作中"] -->|"持續義務"| CP["checkpoint 檔＋durable owner"]
  CP --> C["compact 任意時刻"]
  C --> U["下次開口"]
  U --> H["UserPromptSubmit hook"]
  H -->|"閘：有新 compaction"| I["注入 thin pointer"]
  H -->|"無"| S["靜默"]
  I --> V["四問驗證→restore-proven"]
  V --> G["cleanup guard 解除"]
```

live dogfood（2026-09-23）：真 compact 事件 hook 真觸發；corrupt 分支 live 實證（手寫 checkpoint 漏 schema 欄被 fail-loud 攔下）→修復後 inject（thin pointer 重放）與 consumed（proven 後靜默）重放驗證——恢復生命週期三分支全通，AC#1 以真實事件證據結案。
<!-- SECTION:FINAL_SUMMARY:END -->
