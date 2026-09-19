---
id: decision-3
title: Plugin 安裝授權——cc/codex 可直接裝免問、zcode 僅 user 手動
date: '2026-09-19 03:22'
status: accepted
---
## Context

user 0919 原話（互動 session 親述）：「plugin cc codex，可以直接裝不用問我，zcode 只能我手動，這在流程要知道」。背景：plugin 更新是高頻操作（先例：delegate-bridge 2.0.18 re-release 待裝；marketplace 更新流程見各 plugin repo）。

## Decision

1. **CC（Claude Code）plugin**：agent 可直接安裝／更新，免逐次請示（standing consent）。
2. **codex plugin**：同上，直接裝免問。
3. **ZCode plugin**：**只能 user 手動安裝／更新**——agent 禁代裝（含 marketplace 更新、config.json hooks 子樹 merge 等任何觸及 ZCode 安裝面的動作），需更新時列清單回報待 user 手動。

## Consequences

- plugin 相關弧（如 delegate-bridge re-release）的收尾分流：cc/codex 端 agent 直裝並驗證；zcode 端產出「待 user 手動」清單（plugin id＋版本＋安裝指令）。
- 先例套用：bridge 2.0.18 re-release 落地時，CC/codex 端可自動更新；ZCode 端升級動作列單交 user。
- rule 面收編（outward-action-consent.md outward 場景枚舉）走 instruction 落地前審查閘，隨 decision-2 同批條文收編。
