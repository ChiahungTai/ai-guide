---
id: decision-5
title: Marshal 批量模式配置——過關直行 commit、無額度帽、首批准入 standard＋full tier
date: '2026-09-19 07:22'
status: accepted
---
## Context

D-002（Marshal mode taxonomy）的 user 三裁決（0919 互動 session AskUserQuestion 親選）。配合 dw 承諾制（135.7 卡 notes：dw 指令＝承諾做完卡 AC、判斷阻塞→bi/tri→續做、報告僅終場）與 goal-integration tri 三腿共識（Settle typed predicate contract、N=2 stall、pending 分軸）。解消 codex 日審指出的權威衝突：decision-2（過關直行）vs autonomous-execution（自主 commit 紅線）在批量場景的打架。

## Decision

1. **批量模式過關弧直接 commit**：bi/tri＋post-build 全綠的弧，夜間批量即 commit（decision-2 委任延伸至批量檔位）；紅線（強 outward／破壞性／跨 repo 寫）仍即時停。本條為 autonomous-execution 紅線的顯式 user 例外（限 goal-governed 批量檔位內、限本 repo）。
2. **無額度帽**：不設每晚固定花費帽——停機條件＝stall（N=2 輪無 evidence delta）＋紅線＋額度自然耗盡。花費由 dw 承諾範圍（卡 AC）天然界定。
3. **首批准入＝standard＋full tier**：兩類卡皆可進夜間批量（信任畢業制首批即含 full tier，狗糧數據更快）；跨 repo outward 行為不因本條解鎖（135.5 憲法級 gate 恆在）。

## Consequences

- 批量模式（D-002 結案：兩檔制——隨行互動／批量夜間）的預算與預授權邊界定著：無額度帽、過關直行、紅線恆停。
- autonomous-execution skill 的紅線枚舉與 rule 面（outward-action-consent）須吸收本例外——歸條文收編批走落地前審查閘；落地前批量模式 commit 以本 decision＋decision-2 為 canonical 依據。
- 135.7 Settle 契約數值齊備（N=2 stall、無額度帽、standard＋full 准入）——契約設計階段完成，可進實作。
- 信任畢業數據：首批含 full tier＝首次夜間批量即產生升降級證據；否決率／residue 率入 parent S7 度量。
