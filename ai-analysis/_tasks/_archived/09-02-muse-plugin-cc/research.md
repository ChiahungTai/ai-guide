# Research: Muse Code 賣點 → plugin 功能映射（段落 0 產出）

> 研究 agent（Explore）2026-09-02 完成；證據基底 `ref-docs/harness/meta/`（行號指向鏡像檔）。
> 注意：cookbook 個別 recipes 未在鏡像（僅索引 `cookbook/muse-code.md`），主張基於 muse-code/ 12 頁。

## A. Headless 可整合的真差異（codex/grok plugin 沒有的 CLI 面）

**1. JSONL 事件流 `--json`** — must-have
- `muse-code/extending.md:122`：`muse exec --json`（JSONL events on stdout）
- 委派利用：forwarder 剖析事件（工具呼叫/核准），runs 表即時進度；rescue 判卡死看事件時間戳
- 整合：forwarder 原生輸出模式，預設開

**2. Exit code 語義** — must-have
- `extending.md:125`："The code reflects **how the run ended, not whether the work is correct**"；0=turn 完成、1=失敗/取消/超限、2=usage error、130/143=SIGINT/SIGTERM；"gate on your own test command, not on Muse Code's exit code alone"
- 整合：forwarder 契約映射 exit code；verdict 永不由 exit code 推導

**3. `--max-model-steps <n>`** — must-have
- `extending.md:132`："Cap a run's work with --max-model-steps so a stuck task can't loop indefinitely"（超限算 exit 1）
- 整合：每 run 強制上限（預設 200）、caller 可覆寫；runs 表標 capped

**4. `muse export --session <uuid> --out run.json`** — must-have
- `extending.md:141,144`；`interactive.md:165`："append-only event log: model calls, tool calls and their results, and approval decisions"
- 整合：review 後整包匯出當證據（含核准決策）——deterministic replay/audit 底層；真差異

**5. `--sandbox-network <proxy-only|restricted|enabled>`** — must-have
- `permissions.md:88-92`：proxy-only（預設）/restricted（無網路）/enabled
- 整合：review 固定 restricted（離線防洩漏）；task 預設 proxy-only

**6. `--trust-workspace`（獨立於 --yolo）** — must-have
- `configuration.md:77` flags 清單；`permissions.md:71`："When you trust a workspace, Muse Code loads its project-local skills, rules, and hooks"
- 整合：讀 repo 規則不關沙箱用這個（不是 --yolo）；setup 偵測信任狀態；caller 明示 pass-through

**7. Verification observer（內建）** — nice-to-have（偏必備）
- `extending.md:41-48`："check that the agent ran the work it claims it finished"；"All four observers, including verification, are on by default"
- 整合：確保不被關（settings/rollout 可能停用）；setup 回報狀態；review verdict 信心來源之一

**8. Subagent fanout + worktree 隔離（prompt 驅動）** — nice-to-have
- `extending.md:21,23,33`：child 預設共享 checkout、可要求隔離、"eight agents at once by default"、`agents.execution_capacity` 1-64
- 整合：prompt 模板要求 fanout；runs 表靠 --json 事件呈現 child 進度

**9. `muse skills` 家族 + 跨 agent skill 互通** — nice-to-have
- `extending.md:60-61,67-72`：muse 原生探索 `~/.claude/skills`、`.codex/skills`、`<repo>/.agents/skills/`；`muse skills import --from claude`
- 整合：文檔宣傳 + setup 跑 `muse skills list` 驗證；零開發成本

**10. Workflows（JS 編排）** — nice-to-have（平台 gate）
- `workflows.md:16`："The current public `aarch64-apple-darwin` package does not include `workflow-script-engine-v8`"——**Apple silicon macOS 不可用**（本機平台！）
- `workflows.md:48,104,139`：1,000 child tasks、`muse workflows save`、`recover`
- 整合：不進核心；setup 偵測 engine 缺席 → 降級 subagent fanout

**11. `--reasoning-effort` 到 `xhigh`/`ultra`** — nice-to-have
- `configuration.md:61,68`：none…high(預設)、xhigh、ultra（"can make Muse Code delegate more aggressively"，ultra root 容量 64）
- 整合：review `--deep` 映射 xhigh

**12. `--approval-mode untrusted` / `--approval-judge off`** — nice-to-have（文檔）
- `permissions.md:33-34,44`；`configuration.md:87`
- 整合：文檔說明，勿做預設

**13. `muse config` + doctor skill + `muse trace inspect`** — nice-to-have
- `changelog.md:23,51`；`interactive.md:170`
- 整合：setup 健檢彈藥

## B. 互動面專屬 → headless 不可整合，skip

| 功能 | 證據 | 理由 |
|---|---|---|
| `/loop` + cron | `interactive.md:109-115`（auto-expire 7 天） | 綁活 session；排程在 caller 端重實作（每次觸發一次性 muse exec） |
| Session messaging | `session-messaging.md:171`（headless 不入 peer list） | 明文排除 |
| Rewind | `rewind.md:84`（僅互動 terminal） | 手勢限定 |
| Side chats | `interactive.md:59-71` | TUI 限定 |
| Voice/steering/clarify//compact | `interactive.md:27-30,85-86,142,150` | 互動 UI |
| `/goal` | `interactive.md:95-103` | headless 無證據可設；補償=prompt 模板內建 completion check + observer |

## C. 模型面（文檔宣傳，不進 headless 契約）

- 1M context：`models.md:25`（1,048,576-token）——review「單 run 吞整 repo」賣點
- 多模態：`coding-agents.md:69-73`；訂閱含 image/video uploads（`subscriptions.md:22`）；`muse exec` 無文檔化圖片 flag

## 優先級摘要

- **must-have（6）**：--json、exit-code 語義、--max-model-steps、muse export、--sandbox-network、--trust-workspace
- **nice-to-have（7）**：verification observers、subagent fanout、skills 互通、workflows（Apple silicon gate）、xhigh/ultra、approval-mode 文檔、muse config+doctor
- **skip（6+）**：loop/cron、session messaging、rewind、side chats、voice/steering/clarify、/goal（prompt 補償）
