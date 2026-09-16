---
name: global-vs-project-permissions
description: "ai-rules/settings.json 是全局權限,專案特定權限由各專案自己的 settings 管"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cae50ca2-e57d-4ad2-9b0e-add53231113f
---

`ai-rules/settings.json` 是**全局**權限檔(gitignored)。專案特定權限(如 mosaic 的 `.claude` 讀取、跨專案 additionalDirectories)由**各專案自己的 settings** 設定,不塞進全局檔。

**Why:** 全局檔要保持通用、乾淨;專案各自擁有自己的權限才不會讓全局檔累積專案特定噪音(這次清理就刪掉一堆 mosaic-specific 一次性殘留)。

**How to apply:** 改全局 settings.json 的 permissions 時,只放跨專案通用的 allow(唯讀工具、共用水源 Read);遇到「某專案才需要」的權限,引導用戶寫進該專案的 `.claude/settings.json`,不要加到 ai-rules 全局檔。相關:[[ai-rules-dual-role-mosaic-shared]]。
