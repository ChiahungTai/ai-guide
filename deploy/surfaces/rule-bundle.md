---
surface: rule-bundle
owner: ai-guide deploy（sync-sources）
---

## touches（候選偵測）

本 repo 為 ai-guide 且 diff 命中 `ai-development-guide.md` 或 `rules/**`——他 repo 的 `rules/` 非本 surface。

## probe（唯讀健康探針）

`/sync-sources` 部署新鮮度——三家 harness bundle 對 source 重建 byte-match 比對（`rules/`＋guide）。

## health 判準

三家 bundle byte-match 全過＝healthy；任一 drift＝unhealthy。
