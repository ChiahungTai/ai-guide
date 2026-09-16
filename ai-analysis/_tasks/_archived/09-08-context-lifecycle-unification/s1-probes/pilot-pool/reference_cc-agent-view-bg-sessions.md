---
name: cc-agent-view-bg-sessions
description: CC --agent <name> --bg：registry agent 當 session 主體；supervisor 存活；worktree＋auto-commit 接線點
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

CC agent-view（ref-docs/harness/claude-code/docs/en/agent-view.md，research preview）：一屏管理全部背景 session 的 substrate——09-05 查畢並裁定「輕接線」進 AIR-26 CC 端段。

**對 agent 特化弧最關鍵的機制**：`claude --agent <name> --bg "<prompt>"`——**registry agent 直接當背景 session 的主體跑**（不是被 spawn 的 subagent）；session 內 `/bg` 背景化當前對話、`/fork` 複製到背景（獨立續跑）、`claude agents` 分組管理（Needs input/Working/Completed）＋peek（Space 不 attach 回話）/attach（Enter 全對話）。

**存活語義**：獨立 supervisor process 撐背景 session——關 terminal/關 agent view 照跑、機器睡眠喚醒後 process 續跑；每 session 獨立吃訂閱 quota（成本面）。`!` 前綴＝背景 shell job（`--exec` 同）；in-flight 工作（背景 subagent/workflow/排程）隨背景化攜帶。

**兩個必寫進接線的互動**（AIR-26 EP 要涵蓋）：
1. **worktree 隔離**：背景 session 編輯前自動搬進 `.claude/worktrees/` 隔離 worktree（`worktree.bgIsolation: "none"` 可關）——需與我們 trunk＋多 worktree 單向 rebase 線模型對齊
2. **收尾 auto commit+push**：文檔明說「your git instructions take precedence（CLAUDE.md/memory 說 commit 自己管就留給 user）」——我們 commit-consent rule 在場即覆蓋，但接線時必須**機械驗證 override 真的生效**（auto-commit 出事=單向門）

**L4 實測（09-05，claude 2.1.261，ai-rules repo）**：①**unknown-name（SM-10）**——warning `no agent named 'X' — spawning with default template`＋報 backgrounded＋session 即刻死（`claude agents --json` 查無、logs 報 control.sock ENOENT）；行為與文檔一致、**warning 措辭與文檔引句不同**（版本差——引句驗行為不驅逐措辭）。②**named agent 載入成立**：`claude --agent code-reviewer --bg` → `@code-reviewer` 成 session 主體、唯讀任務正確回報、零檔案修改、`claude stop` 收乾淨＝**讀取型可回收已驗證**（CLI 非 TTY 下 `claude agents` 要 `--json`）。③**未驗證**：寫入型 worktree 產出回收（attach 驗收→consent→commit→rebase）與 **rules/ 檔 auto-commit override**（文檔列舉 task/CLAUDE.md/memory 三來源，rules/ 是否同樣覆蓋＝待實測）——留首個寫入型工單實測；接線文本在 deep-work skill `--agent --bg` 段。

相關：[[reference_cc-workflow-model-zcode-absence]]（workflow runtime；agent-view 是背景 session 層非 workflow 層）、[[agents-registry-split-design]]、[[commit-consent-in-autonomous-mode]]
