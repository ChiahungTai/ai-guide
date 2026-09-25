---
id: AIR-203
title: bridge-MCP-face-收編進-skill——rule-body-drift-補洞（AIR-201-judge-觀察1）
status: To Do
assignee: []
created_date: '2026-09-25 22:56'
updated_date: '2026-09-25 23:01'
labels: []
dependencies: []
ordinal: 189000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
judge 驗收 AIR-201 時發現：rules/bridge-dispatch.md body 的 MCP face 段（.mcp.json 註冊／codex-mcp-wiring／bridge_task 恆 --background）在 bridge-dispatch skill 無對應節。body 是 pre-existing 內容未動，但三條 projection 落地後 non-CC 常駐面只剩泛指針，MCP face 知識對 non-CC 變成兩跳且無錨。收編＝把 MCP face 段落成 skill 一節＋rule body 該段評估去留。

```mermaid
graph LR
A[rule body MCP face 段] -->|收編| B[bridge-dispatch skill 新節]
B --> C[non-CC 兩跳變一跳]
A --> D{body 去留評估}
D -->|CC 端 paths 條件載入| E[保留或 trim]
```
<!-- SECTION:DESCRIPTION:END -->
