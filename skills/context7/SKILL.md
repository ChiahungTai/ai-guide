---
name: context7
description: "Context7 MCP 文檔查詢 — user 問 library / framework / SDK / API / CLI tool / cloud service 用法時載入，用 Context7 取最新官方文檔再回答（優先於 web search；即使自認知道也要查——training data 可能過時）。涵蓋 API syntax、configuration、版本遷移、library-specific debugging、安裝與 CLI 用法。不適用：refactoring、從零寫 script、業務邏輯 debug、code review、通用程式概念。觸發詞：Context7、library 文檔、framework、SDK、API 用法、查官方文檔、resolve-library-id、query-docs。"
---

# Context7 文檔查詢

Use Context7 MCP to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service -- even well-known ones. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Use even when you think you know the answer -- your training data may not reflect recent changes. Prefer this over web search for library docs.

Do not use for: refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

## Steps

1. Always start with `resolve-library-id` using the library name and the user's question, unless the user provides an exact library ID in `/org/project` format
2. Pick the best match (`/org/project`) by name match, description relevance, snippet count, reputation, benchmark score; if results look wrong, refine the query
3. `query-docs` with that ID and the user's full question
4. Answer using the fetched docs

## 跨 harness 支援

Context7 MCP 三家 non-Claude harness 支援（ZCode 已驗證、OpenCode/Codex 預計）；Claude 端同樣有 Context7 MCP——查詢流程跨 harness 一致。
