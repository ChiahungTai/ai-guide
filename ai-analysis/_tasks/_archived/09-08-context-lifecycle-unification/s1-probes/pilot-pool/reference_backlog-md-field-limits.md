---
name: reference_backlog-md-field-limits
description: Backlog.md 卡欄位大小限制分寫入入口——CLI/REST/直接改檔無限制、僅 MCP schema 有
  maxLength（desc 10000/title 200/notes 20000）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_caba823b-ad38-4810-bb9f-fb752ec56411
---

Backlog.md 卡欄位（description 等）的大小限制**取決於寫入入口**（09-08 查證 upstream `MrLesk/Backlog.md`，本地 CLI 1.50.1）：

- **CLI**（`backlog task create/edit -d`）：無長度限制——type 層 `description: string?`，原樣傳 core 寫 markdown
- **REST API**（web board 編輯）：無長度限制——handler 只驗 `typeof === "string"`
- **直接編輯卡檔**（`backlog/tasks/*.md`）：無限制——卡是 plain markdown，board 只是渲染層
- **MCP 工具**（Backlog.md 自家 MCP server）：`src/mcp/utils/schema-generators.ts` 有 JSON Schema maxLength——description **10000**、title 200、implementationNotes 10000、finalSummary/plan/notesSet 20000（append 形態每條 5000×最多 20 條）、references/documentation 每條 500、acceptanceCriteria 每條 500×最多 50

實務：ai-rules/mosaic agent 走 CLI（kanban-board skill 命令合約）→ desc 實際無上限；desc gate 三必有正常幾百字元遠低於任何上限。對「有沒有限制」的宣稱必須標明入口面（同卡多入口限制不一致）。版本注意：maxLength 數字針對 upstream master；本地版 MCP schema 可能隨版本漂，引用前可重查。

相關：[[reference_backlog-md-browser-id-mechanics]]
