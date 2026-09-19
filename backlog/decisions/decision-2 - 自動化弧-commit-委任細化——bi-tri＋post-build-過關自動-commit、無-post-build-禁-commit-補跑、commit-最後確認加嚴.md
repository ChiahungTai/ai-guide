---
id: decision-2
title: >-
  自動化弧 commit 委任細化——bi/tri＋post-build 過關自動 commit、無 post-build 禁 commit
  補跑、commit 最後確認加嚴
date: '2026-09-19 03:22'
status: accepted
---
## Context

user 0919 原話（互動 session 親述，細化 parent 卡【0919 Two-Touch 落地旅程】⑦ 的 commit consent 委任）：「補一些自動化事項 bi or tri ＋ post-build 後就自己 commit，但如果沒跑 post-build 就不可以，補跑就是了，然後 commit 要多做些最後確認，要注意」。適用面＝審查通過的自動化事項弧（含 deep-work／排程／bridge 工單弧的結算）。

## Decision

1. **gate 順序（constitution 級）**：bi 或 tri 審查過關 → post-build 過關 → 自動 commit（免逐次請示）。
2. **post-build 是硬前置**：沒跑 post-build＝不得 commit；補救＝補跑 post-build（不是跳過 gate、不是改走請示）。
3. **commit 最後確認加嚴**：走委任 commit 時 commit skill 收尾檢查做足——staged 檔案逐檔核對（只 add 指名檔）、審查腿 verdict／post-build receipt 在場驗證（機驗非自報）、commit message 與結算物對帳。
4. 一次授權≠永久授權的正典不變：本 decision 是 standing 委任的細化，非新授權模式；跨 repo 寫入仍不在委任內、恆停。

## Consequences

- 自動化弧結算少一輪 commit 請示往返；補跑 post-build 成為標準路徑而非例外。
- commit skill 的委任路徑需載明本加嚴清單（rule/skill 面落地走 instruction 落地前審查閘——boundary 級、bi 腿；載體＝rules/outward-action-consent.md＋skills/commit/SKILL.md，排程歸 135 program 條文收編批）。
- autonomous session 紅線條款（outward-action-consent「Autonomous shortcut」）與本 decision 競合時：deep-work 排程場景仍以 autonomous-execution 紅線枚舉優先，本 decision 補的是「紅線內的 commit」的 gate 細則。
