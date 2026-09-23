---
id: AIR-174
title: 治理 hooks 統一到 Python 3.12 runtime
status: To Do
assignee: []
created_date: '2026-09-23 08:42'
labels: []
dependencies: []
ordinal: 160000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
目前 Codex／Claude／ZCode 的治理 hooks 多數直接叫 `python3`，在這台機器會落到 macOS 內建 Python 3.9.6；但 ai-guide 本身已要求 Python 3.12 以上。這張卡把治理 hook runtime 統一到 uv 管理的 Python 3.12，並由 installer 在安裝時解析實際 interpreter 路徑，再投影到各 harness config。

不改 macOS 的 `/usr/bin/python3`，不靠 shell PATH，也不讓每次 hook 都經過 `uv run`。既有 hook 行為、stdin/stdout/exit contract 必須維持；部署前後要驗證 deny gate、sensor 與 compact restore 都沒有退化。

```mermaid
flowchart LR
  A["現在：hook → bare python3"] --> B["macOS Python 3.9"]
  C["AIR-174"] --> D["installer 解析 uv Python 3.12"]
  D --> E["Codex / Claude / ZCode config"]
  E --> F["hook 直接用 3.12 interpreter"]
```
<!-- SECTION:DESCRIPTION:END -->
