---
name: reference-codex-rollout-jsonl-autopsy
description: codex session 屍體考古機械——rollout JSONL 結構、jq 抽取路徑、配額死亡訊號形態、resume 檔名規則
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_57806287-329c-4d9e-a171-03f78e1ab697
---

codex 對話記錄＝`~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<session-id>.jsonl`；resume 產**新檔** `rollout-<ts>-<orig-id>_<new-id>.jsonl`（後綴接續，非同檔 append）。cwd 在首行 `session_meta` payload（codex worktrees＝`~/.codex/worktrees/<hash>/<repo>`）。殘留 `thread-writer-locks/<id>.lock`。

抽取（jq）：每行 `{timestamp, type, payload}`；type＝session_meta / response_item / event_msg / token_usage_record / world_state / inter_agent_communication_metadata。

- user prompts：response_item `.payload.type=="message"` + `role=="user"` + `.content[].text`——**Codex Desktop 會把環境序言（plugin 清單、AGENTS.md instructions）以 user role 注入**，真 prompt 被埋，需過濾
- 想法（只活在 transcript 的）：`.payload.type=="reasoning"` 的 `.summary[].text`
- 最終發言：`role=="assistant"` message，或 event `agent_message`（多 agent 通訊，author 形如 `/root/arc_fresh`）
- 工具呼叫：`.payload.type=="custom_tool_call"` 的 `.name`（如 exec）

**配額死亡訊號**：非硬崩潰——turn 照常以 `task_complete` 收尾；kill 訊號在最後一則 agent_message（常由 sub-agent 回報）：`Agent errored: You've hit your usage limit... try again at <重置時間>`。死亡規模統計＝`rg -l "hit your usage limit" ~/.codex/sessions/` 逐日 census。

2026-09 上旬實證：15 檔帶配額死亡（09-07 單日 6）、死者審查弧只寫到「中間檢查點」→ 驅動 durable-checkpoint rule（見 [[project-codex-quota-death-durable-checkpoint]]）。同族驗屍法：[[feedback_agent-transient-death-autopsy]]（mtime 時間線，適 in-harness agent）；本條是 codex JSONL 面。
