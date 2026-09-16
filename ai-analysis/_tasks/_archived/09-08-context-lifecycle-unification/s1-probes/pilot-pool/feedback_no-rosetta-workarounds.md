---
name: no-rosetta-workarounds
description: user 2026-09-02 裁定不用 Rosetta（macOS 將退場支援）——x86_64 套件繞路禁提，平台缺口直接等
  upstream 或找原生替代
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_6e1a64d3-b65c-4af6-8848-c147fd16be25
---

muse workflows 在 aarch64 缺 engine 時，AI 提出可改跑 x86_64 套件過 Rosetta 2 繞路；user 明確拒絕：「不要用 Rosetta OSX要退出支援了」。

**Why**：Apple 已宣布 Rosetta 2 退場時程——建立在它上的繞路是耗損性資產，不值得投入。

**How to apply**：遇到「平台 artifact 缺組件/缺功能」時，禁提 Rosetta x86 繞路；只給兩類解：等 upstream 原生修（追蹤+偵測降級）或找同平台原生替代功能（實例：muse workflows 缺口→subagent fanout 替代，見 [[agents-registry-split-design]]）。
