---
surface: muse-plugin
owner: muse-plugins/memory-governance（運維節單一源＝該 README）
---

## touches（候選偵測）

diff 命中 `muse-plugins/**`。

## probe（唯讀健康探針）

`muse plugins inspect <id> --json`：cache/source 一致＋`runtime_capabilities[].status`（未重新 approve＝閘靜默下線 fail-open 窗口）。

## health 判準

cache/source 一致且 status 非 stale＝healthy；不一致或 status 異常＝unhealthy。
