---
name: muse-memory-mechanism-divergence
description: muse local memory 與 CC/ZCode 結構性不同（三 scope/48 檔上限/observer 召回）——telemetry 源覆蓋暫緩 draft，要用先重設計
metadata:
  node_type: memory
  type: project
---

user 2026-09-08 拍板：telemetry 歸因源覆蓋（codex 接線／muse+grok 探測）**全部先留 draft，等真的用再處理**；muse 本身 local memory 作法「跟其他人差很多，可能要重新設計那邊的機制」。

**muse memory 機制事實**（官方 configuration.md「Local memory」段，ref-docs/harness/meta/ 鏡像）：三 scope——personal project（repo 外本機，default）／project（`<repo>/.agents/memory/` 進版控）／personal（machine-wide）；注入＝session 開頭 MEMORY.md 索引＋路徑清單（**上限 48 檔**——我們池 129 條，直接共享會截斷）＋on-demand 讀＋**background observer 可在 turn 前插入相關筆記**（主動召回，我們體系沒有）；**untrusted workspace 也載 committed memory**（官方自警 prompt-injection 面）。

**注意點（真要用時先想）**：①muse 在本 repo 是唯讀約束（AGENTS.md「禁 add_memory/edit_memory」——共享池寫入權要在那之前重新拍板）②48 檔截斷 vs 我們 127+ 條——共享形態要嘛分池要嘛瘦身投影③bridge ledger（.muse-bridge/jobs/*.jsonl）只覆蓋 bridge 派發任務非全部 session——歸因面不完整④mosaic memory 共享方案（.agents/memory/＋symlink）落地考古是既有 pending（等 user）。

相關：[[memory-governance-air40-42]]（telemetry 雙源現況與 drafts 開卡 45c4bc3）、[[external-runtime-delegation-family]]。
