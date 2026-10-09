---
id: AIR-297
title: >-
  dutymail pending-age 帳 episode fencing——延遲寫入復活舊 flag 邊界封閉（AIR-294 judge F3
  後續卡）
status: Done
assignee: []
created_date: '2026-10-09 16:42'
updated_date: '2026-10-09 22:50'
labels:
  - dutymail
dependencies: []
ordinal: 288000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-294 bi 分歧 Arbiter 裁決 codex F3（Important/Evidence-based）後續卡：`hooks/duty_mailbox_monitor.py` 的跨 session 共享年齡帳 `pending-age.json` 採 atomic replace last-writer-wins、無 fencing——「A 舊寫延遲反超 B 清帳」可復活已清帳 episode 的 `stall_reported=True`，後果＝單 episode 漏報一次（advisory 面、窗窄——AIR-294 修補僅補 docstring 邊界註記並明示「接受，fencing 不引入（後續卡）」）。本卡封閉該邊界：pending-age.json 寫入面引入 episode fencing（episode token 或 CAS）——延遲寫入不得復活已清帳 episode 的 flag；涉及 schema 變更＋既有帳相容處置（AIR-294 judge 裁決原文：episode fencing/CAS 涉 schema 變更，後續卡追蹤）。裁決指針：`.review/air-294.md` 修復節（裁決全文錄存）；原檔 `/Users/ctai/Github/ai-guide/.agent-tmp/air294-judge-verdict.md`（.agent-tmp 暫存，以其為 best-effort 指針）。

```mermaid
flowchart LR
  a["跨 session 讀改寫交錯"] --> b["A 舊寫延遲反超 B 清帳"] --> c["復活 stall_reported flag"] --> d["episode fencing（token 或 CAS）封閉"]
```


```mermaid
flowchart LR
  a["holder 章長持——下班 session 綁死收信"] --> b["ai-guide：慣例修正 ext 語義＋death-evidence 接管"]
  a --> c["bridge：INBOX 章 vs 消費章分離提案"]
  b --> d["雙 repo 寄信討論→各自落地"]
  c --> d
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 pending-age.json 寫入面 fencing 落地（episode token 或 CAS）——延遲寫入不得復活已清帳 episode 的 stall_reported flag（含延遲寫入反超情境測試）
- [x] #2 schema 變更＋既有 pending-age.json 相容／遷移處置（無 schema 版本帳的舊檔不打爆）
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 老規矩審查鏈（規模比照 AIR-294：codex＋judge）
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【裁決機制原文（AIR-294 bi 分歧 Arbiter，codex F3 段節錄）】last-writer-wins 無 fencing 下「A 舊寫延遲反超 B 清帳、復活 stall_reported=True」窗口屬實；觸發窗＝跨 session 讀改寫毫秒交錯、後果＝advisory 單 episode 漏報一次；問題核心是 monitor docstring「後果方向安全」論證未涵蓋亂序復活——安全性宣稱不完備屬誠實性問題（該註記已隨 AIR-294 必修 5 落地）；episode fencing/CAS 涉 schema 變更，後續卡追蹤。
- 落地兩層防線：①episode fencing（entry `episode_id`＝holder bindingEpoch，讀側不匹配→stale 清帳重建，ad23dbec）②doc-rev CAS（帳文件單調 `rev` 欄，commit closure 寫入時比對 snapshot、不符即丟棄＋stderr「寧重複不漏報」，7d0dea18）——judge 指出 bindingEpoch 粒度不足（同 binding 內 drain→重積不換 token），CAS 補同 epoch write-after-clear 復活＋陳期 seed 蓋新 seed（年齡虛胖早報）兩類 stale-read overwrite
- 舊檔相容：無 `episode_id`／無 `rev` 欄舊檔＝視 stale／rev 0 冷啟動，不打爆
- 審查鏈：codex needs-attention（F1 high 同 epoch 競態）＋GLM approve→judge（GLM-5.3）裁 F1 fix-now、GLM approve 辯護駁回（per-binding-epoch 反 spam 語義與模組自身 per-帳窗語義矛盾）；修復腿 RED 3 failed→GREEN 94 passed，全套 3800 passed 1 skipped
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
pending-age 帳 fencing 以兩層防線收口：episode token（bindingEpoch）讀側比對擋跨 binding 殘留、doc-rev CAS 寫邊界擋同 epoch 與所有 stale-read overwrite（復活 flag／陳期 seed 蓋新 seed）；舊 schema 檔冷啟動相容。同 epoch 延遲寫入反超原形有真交錯測試釘死（RED→GREEN），丟棄方向＝至多重複一報不漏報（模組自陳偏好方向）。全套 3800 passed，main=7d0dea18。

```mermaid
flowchart LR
  r["monitor_once 讀帳"] --> s["snapshot rev＋episode_id"] --> w["commit closure 寫入"] --> cas{"doc-rev CAS：rev 相符？"}
  cas -- "否（stale writer）" --> x["丟棄寫入＋stderr（寧重複不漏報）"]
  cas -- "是" --> ok["rev+1 存檔"]
  s2["讀側 episode_id 不匹配"] --> y["視 stale 清帳重建（fresh seed）"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
