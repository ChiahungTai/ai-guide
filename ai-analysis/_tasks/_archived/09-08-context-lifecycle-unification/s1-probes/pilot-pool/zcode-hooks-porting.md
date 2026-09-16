---
name: zcode-hooks-porting
description: ZCode hooks 移植完結（940746a）——symlink 無效（config 絕對路徑）、事件子集、專案層被忽略；exit 2 stderr 回饋 LLM
metadata:
  node_type: memory
  type: project
  originSessionId: sess_9f18d654-1029-400d-a249-9465416c9bae
---

Claude hooks 移植 ZCode **完結**（2026-08-14 probe 通過＋正式註冊，commit 940746a）。留教訓：

- **symlink 對 hooks 無效**（對比 commands/skills 的目錄載入點）——ZCode 只認 `~/.zcode/cli/config.json` hooks 區塊＋plugin hooks；正確模式 = 腳本單一來源在 `ai-rules/hooks/`，兩家 config 絕對路徑引用。config.json 不可 symlink 進 repo（MCP secrets＋兩家 schema 不同）。
- **ZCode hooks 機制事實**：事件子集無 Notification/SessionEnd；**專案層 `.zcode/config.json` hooks 被整體忽略**；config 快照 per session（改動需新 session 生效）；stdin JSON 保留 Claude snake_case alias（hook 腳本零改動可攜）。
- **用戶決策**：不移植 notification.sh（PermissionRequest 替代太吵）；只上 PreToolUse(Bash)＋Stop 兩條。
- 除錯：`~/.zcode/cli/log/zcode-<date>.jsonl`（`hook.run.failed`）。

## stderr 回饋實證＋matcher 語義（2026-08-25，require-crg-repo-root hook 實測）

- **exit 2 + stderr 會回饋給 LLM（實證成立，官方文檔未載明 stderr 處理）**：新 session 觸發 PreToolUse 阻擋後，`[Hook Blocked]` 開頭的 stderr 指引**完整到達模型**，據以補參數一次重試成功（非盲重試）——hook 修正指引直接寫 stderr 即可，**不需**改 `hookSpecificOutput.permissionDecision` JSON 路徑。
- **matcher 語義**：純字母數字底線＋`|` 走精確名單分支；**含 `-` 等字元走 JS regex 分支（unanchored substring）**——`mcp__code-review-graph__`（server 名含連字號）實測 substring 命中。陷阱：未來 matcher 目標若改純底線名，同寫法會變精確匹配而**靜默失效**（regex 無誤但永不觸發）。
- **08-30 二次實證**（block-memory-index-write.py、`Edit|Write` matcher）：stderr 指引完整到達模型（含可直接執行的 generator 命令）、遵行無盲目重試——stderr 回饋非 Bash matcher 特例，跨 matcher 一致。

相關：[[multi-harness-architecture-direction]]、[[hook-vs-llm-flow-division]]

## 08-30 官方 hooks.md 鏡像補遺（memory hooks 接線時 grounding）

- **stdin 含 `cwd`**（與 session_id/transcript_path 同層基礎欄位，兩家皆有）——Stop hook 推導專案 memory dir 用，免 env 依賴
- **Stop 的 exit 2 = decision block：強制主模型再跑一輪（最多連續 3 次）**——通知/重生成類 Stop hook 必須恆 exit 0（memory-index-regen 即此設計）
- matcher 精確名單分支（字母數字底線＋`|`）與 08-25 實測一致；`Edit|Write|NotebookEdit` 屬精確名單形態
- **成功執行不落 log**（08-30 regen 腿實證）：`zcode-<date>.jsonl` 只記 `hook.run.failed`——成功的 Stop/PreToolUse 執行零 log 痕跡；**驗證 dispatch 靠效果面**（索引內容/mtime 變化）而非查 log。log 裡的 `hook.run.failed` 先看時間戳＋matcher＋sessionId 歸因——歷史 session 的舊失敗與新接線無關的排除法

## 09-01 補遺：PreToolUse 不攔 subagent 工具呼叫

- **subagent 的工具呼叫不過 PreToolUse hook**（09-01 實證）：寫入治理 hook（block-memory-index-write.py、`Edit|Write|NotebookEdit` matcher）對 subagent 的 Write 不生效——蒸餾 subagent 寫 16,154 chars 條目檔（>12,000 gate）成功落地，主 session 同款 Write 會被 exit 2 擋
- 含義：hook 治理覆蓋面＝主 session 工具呼叫 only；subagent 寫檔防線只剩 prompt 紀律——批量委派寫入任務時把數值上限寫進 agent prompt（mem-distill 定義模式）
