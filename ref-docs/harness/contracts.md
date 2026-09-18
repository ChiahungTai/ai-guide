# Harness 契約對照

各 harness（Claude Code / ZCode / Codex / Muse Code）的契約維度對照，**萃取自本地鏡像**（`claude-code/`、`zcode/`、`codex/`、`meta/muse-code/`，見 [`manifest.json`](manifest.json) **各 source 條目的 `generated_at`** 為該源新鮮度基準——頂層 `generated_at` 僅是 manifest 產出時間；source 條目無此欄＝該源尚未在新制下刷新過）。

> 過時以原站為準；每格附鏡像內的 `檔:行` 佐證以便查證，未載者標「--help 實機，鏡像未載」並說明查證過程。「（鏡像未提及）」= 該維度在所讀頁面沒寫，非保證不存在（可能在未鏡像的頁面）。本檔管「harness 能做什麼」（A 層官方契約）；各 harness 在本機的實際接線狀態（B 層 projection）另見 [control-plane-matrix.md](control-plane-matrix.md)。

## 對照表

| 維度 | Claude Code | ZCode | Codex | Muse Code |
|------|-------------|-------|-------|-----------|
| **專案/全域指令檔** | 專案 `./CLAUDE.md` 或 `./.claude/CLAUDE.md`；全域 `~/.claude/CLAUDE.md`；規則目錄 `.claude/rules/*.md`（記憶體 `memory.md:60,127,171`） | **讀 `AGENTS.md`**（全域 `~/.zcode/AGENTS.md` + workspace）；**不讀 CLAUDE.md**（僅 onboarding 一次性遷移成 AGENTS.md）（`agents.md:46-55`） | **原生讀 `AGENTS.md` 雙層**：global `~/.codex/AGENTS.md`（`AGENTS.override.md` 優先；`CODEX_HOME` 可遷）→ project 自 repo root **向下**走到 cwd、每目錄至多一份（override→`AGENTS.md`→`project_doc_fallback_filenames`），root-down 串接、越近 cwd 越後越強；合計上限 `project_doc_max_bytes`（**預設 32 KiB，可調**）；每次 run 重建 instruction chain（`codex/agent-configuration/agents-md.md:9-15,147-159,206`）；**不讀 CLAUDE.md**（未列入 fallback 名單即忽略） | AGENTS.md 為主，walks up 至 .git，每層依序 `AGENTS.md`→`CLAUDE.md`→`.agents/AGENTS.md`→`.claude/CLAUDE.md` 首命中勝出；project 規則需 trust 才載，user 規則永遠載（Muse Code `muse-code/configuration.md:41,46`） |
| **Skill** | `SKILL.md`（遵循 [Agent Skills](https://agentskills.io) 開放標準）；frontmatter 最豐富（`name`/`description`/`when_to_use`/`allowed-tools`/`context:fork`/`paths`…）；目錄 `~/.claude/skills/`、`.claude/skills/`（`skills.md:19,103,227`） | `SKILL.md`（範例僅 `name`+`description`）；`~/.zcode/skills/<name>/`；**可從 Claude Code/Codex/Augment/Windsurf 一鍵匯入**（單向導入）（`skill.md:39,51`） | `SKILL.md`（Agent Skills 標準，必帶 `name`+`description`；`agents/openai.yaml` 選配 UI/invocation policy/tool dependencies）；掃描：repo `$CWD`→`$REPO_ROOT` 各層 `.agents/skills`＋user `~/.agents/skills`（**canonical**）＋admin `/etc/codex/skills`＋system 內建；支援 symlink 目錄；progressive disclosure（初始清單 ≤2% context 或 8,000 字元）；`$skill`／`/skills` 顯式＋description 隱式匹配；`[[skills.config]]` 停用；`$skill-installer` 裝 curated（`codex/build-skills.md:33-45,92-96,133-146,163-188`） | SKILL.md 四源（built-in/user/project/plugin）；user 掃 `$XDG_CONFIG_HOME/muse/skills`＋`~/.agents/skills` 並自動發現 `~/.claude/skills`／`~/.codex/skills`；`muse skills` CLI（list/inspect/enable/install/validate/import --from claude\|codex）；frontmatter 底稿「收尾 `---` 自成一線」鏡像未載該句（Muse Code `muse-code/extending.md:57,60,67`） |
| **Subagent / Agent** | `~/.claude/agents/`、`.claude/agents/`（`settings.md:66`；格式在 `sub-agents.md`） | `~/.zcode/agents/<name>.md`；**僅用戶級（Beta）**，不支援工作區級子智能體（`subagents.md:65,67`） | 內建 subagent workflows（現行版本預設啟用，app/cli/ide）；**自訂 agent＝獨立 TOML 檔** `~/.codex/agents/`（user）或 `.codex/agents/`（project），每檔一 agent、必帶 `developer_instructions`，可設 model/effort/sandbox/skills——**非 markdown+frontmatter，與 CC/ZCode 定義檔不同構**（`codex/agent-configuration/subagents.md:5-11,25-27,336-345,389`）；CLI `/agent` 檢視切換 agent threads（`subagents.md:53-58`） | lead spawn 子代理；容量 8-64（`agents.execution_capacity`，ultra 未配置時 64）；per-child worktree isolation（拒絕不靜默回落）；孫代共享 root-tree capacity；背景 observers×4（Muse Code `muse-code/extending.md:21,33,39,48`） |
| **Slash command** | markdown 檔，**已合併入 skills**（同名 skill 優先）；`.claude/commands/<name>.md`（`skills.md:14`、`commands.md:11`） | `.md` 檔；`~/.zcode/commands/`（用戶級，工作區級在專案目錄下）；可從外部 Agent 匯入；內建 `/goal`、`/compact`（`commands.md:36,42`） | custom prompts（`~/.codex/prompts/*.md`，`/prompts:name`）**已 deprecated→改 skills**；顯式觸發＝`$` mention 或 `/skills`；內建 `/`（`/goal` `/resume` `/permissions` `/hooks` `/agent` 等）（`codex/custom-prompts.md:5-10,34`；`build-skills.md:92-96`；`developer-commands.md:423,431`） | 內建豐富（/plan /grill /taste /side /goal /loop /name /resume /fork /rewind /export 等），互動面為主；`/help` 展示全量（Muse Code `muse-code/interactive.md:19`＋`muse-code/extending.md:75`） |
| **Hook** | `settings.json` 的 `hooks` key；事件 PreToolUse/PostToolUse/Stop/SessionStart/…；handler `command`/`http`/`mcp_tool`/`prompt`/`agent`（`hooks.md:33,71,302`） | user-level config hooks 3.7.7+ 實測可用（7 事件子集、無 Notification/SessionEnd、專案層被忽略；`zcode/cn/docs/hooks.md`；詳 04 報告 §7 修訂） | `hooks.json` 或 `config.toml` inline `[hooks]`（`~/.codex/` 與 `<repo>/.codex/` 兩層四位置，**多源全載互不取代**）；12 事件（PreToolUse/PermissionRequest/PostToolUse/PreCompact/PostCompact/UserPromptSubmit/SubagentStart/SubagentStop/Stop/SessionStart/SessionEnd/Interrupt）；handler `command`+`mcp_tool` 可用（**prompt/agent 解析但跳過**）；non-managed hook 逐定義 **hash trust**（`/hooks` TUI；startup warning），project hooks 須 project trust；`[features].hooks=false` 可關；`--dangerously-bypass-hook-trust`；async 背景 hook 每session 8 併發（`codex/hooks.md:23-28,32-60,64-78,189-195,313-319,631-637`） | `.muse/hooks.json`（project，trust 後生效）＋user settings hooks；13 事件 SessionStart/UserPromptSubmit/PreToolUse/PermissionRequest/PostToolUse/PreLLMCall/PostLLMCall/PreCompact/PostCompact/SubagentStart/SubagentStop/Stop/SessionEnd；hooks 跑沙箱外；**malformed project/managed hook 檔＝該源貢獻 0 handler＋startup warning**（不 fail）（Muse Code `muse-code/extending.md:83,87,89,94,96`） |
| **MCP** | `.mcp.json`（project）；`~/.claude.json`（user/local）；`{"mcpServers":{}}`；stdio/http/sse/ws（`mcp.md:299,349`） | `~/.zcode/cli/config.json`（鍵 `mcp.servers`）；workspace `<root>/.zcode/config.json`；**相容 `.agents/mcp.json`**（鍵 `mcpServers`）；可從 Claude/Codex/OpenCode 匯入（`mcp-services.md:46,61`） | `config.toml` `[mcp_servers.<name>]`（`~/.codex/config.toml` 或受信 `<repo>/.codex/config.toml`）；`codex mcp add` CLI；stdio＋streamable_http；per-tool `approval_mode`；OAuth 支援；`required` server 初始化失敗＝整run abort（`codex/extend/mcp.md:37,83,127,131-198`；`non-interactive-mode.md:64`） | `settings.json` `mcp_servers`（stdio/streamable_http；mode required/optional；相容標準 `mcpServers` key）；MCP 工具不在沙箱內（Muse Code `muse-code/extending.md:102,110,112`＋`muse-code/changelog.md:35`） |
| **主設定檔** | `settings.json`（user `~/.claude/`、project `.claude/`、local、managed）；雜組態在 `~/.claude.json`（`settings.md:80,119`） | `config.json`：用戶 `~/.zcode/cli/config.json`、workspace `<root>/.zcode/config.json`（`mcp-services.md:59`） | `config.toml` 六層 precedence：CLI flags → project `.codex/config.toml`（**受信才載**）→ `--profile` → user `~/.codex/config.toml` → cloud-managed → system `/etc/codex/config.toml`；**untrusted project 跳過整個 project 層**（config/hooks/rules 全跳）（`codex/config-file/config-basic.md:5,21-28,37`） | `~/.config/muse/settings.json`（`schema_version:1` 必填，缺省檔 OK；缺鍵即 `malformed settings file`，未知值 `unsupported settings schema version`）（Muse Code `muse-code/configuration.md:17,27`） |

## 開放標準相容性（跨 harness 關鍵）

- **`AGENTS.md` = 跨 harness 最大公約數**：ZCode 主推、Claude Code 可用 `@AGENTS.md` import 或 `/init` 整合（不原生讀）（`memory.md:127,145`）；**Codex 原生讀**（global＋project 雙層，root→cwd 串接，`codex/agent-configuration/agents-md.md:5-13`）；Muse Code 原生主推 AGENTS.md，walks up 至 .git（Muse Code `muse-code/configuration.md:41`）。
- **`CLAUDE.md` 讀取分歧**：Claude 原生讀；**ZCode 不讀**（僅 onboarding 一次性遷移）（`agents.md:49`）；**Codex 不讀**（fallback 名單機制 `project_doc_fallback_filenames` 可納入，`agents-md.md:147-159`）；Muse Code 同目錄 `AGENTS.md` 優先於 `CLAUDE.md`（Muse Code `muse-code/configuration.md:41`）。
- **`.agents/` 開放標準**：ZCode（`.agents/mcp.json`）當相容路徑掃；Claude 鏡像未提及（`zcode/mcp-services.md:64`）；**Codex 以 `.agents/skills` 為 canonical**（repo 各層＋user `~/.agents/skills`，`codex/build-skills.md:135-142`）；Muse Code 亦掃 `~/.agents/skills` 與 `<repo>/.agents/skills/`（Muse Code `muse-code/extending.md:60`）。
- **`SKILL.md` 四家一致**（同 Agent Skills 標準，Codex 明示 agentskills.io，`build-skills.md:7-8`），frontmatter 豐富度差異大：Claude 最豐、ZCode 範例 2 欄；Muse Code 四源且跨 harness 自動發現 `~/.claude/skills`/`~/.codex/skills`（Muse Code `muse-code/extending.md:57,60`）。
- **Hook**：Claude 有；ZCode 3.7.7+ 實測支援 user-level hooks（`~/.zcode/cli/config.json`，stdin 含 Claude snake_case alias，腳本零改動可攜；專案層 hooks 被整體忽略、事件無 Notification/SessionEnd；實測紀錄 [04-multi-harness機制對照 §7 修訂](../../ai-analysis/reports/_done/superpowers/04-multi-harness機制對照.md)）；**Codex 12 事件＋hash trust**（`codex/hooks.md:23-28,64-71`）；Muse Code 13 事件且跑沙箱外（Muse Code `muse-code/extending.md:89,94`）。
- **Subagent 定義檔同構性（CC/ZCode 同、Codex 異）**：CC/ZCode 皆 markdown + YAML frontmatter（`name`/`description` 必填，正文 = 系統提示詞）；user 目錄載入點 `~/.claude/agents/`、`~/.zcode/agents/` 皆為目錄掃描 → symlink 部署可行。ZCode 為 Beta：僅 user 級、不可巢狀派發、自訂 tools 清單排除 MCP 工具（Claude 支援 `mcp__` patterns）、未知 frontmatter 欄位靜默忽略；**Codex 自訂 agent＝TOML 檔**（`developer_instructions` 必填），markdown registry 不能直接 symlink 過去（`codex/agent-configuration/subagents.md:336-345,389`）；Muse Code 容量 8-64＋per-child worktree isolation 拒絕不回落（Muse Code `muse-code/extending.md:21,33`）。

## Codex 軸補充（2026-09-19，AIR-138）

- **權限是多軸組合，非單一 mode enum**：①sandbox boundary——permission profiles（**Beta**）：內建 `:read-only`/`:workspace`/`:danger-full-access`＋自訂 filesystem（read/write/deny、deny 恆勝）與 network domain 規則，與舊 `sandbox_mode`/`sandbox_workspace_write` **不並存**（二擇一）（`permissions.md:5-12,45-53,171-198`）；②approval policy——`on-request`/`never`/granular（`untrusted` 已退役、`on-failure` deprecated）（`config-file/config-advanced.md:24-27`；`config-reference.md:87`）；③reviewer——`approvals_reviewer = user | auto_review`（`config-reference.md:120-125`）；④command policy——`.rules` execpolicy（Starlark `prefix_rule`，allow/prompt/forbidden 取最嚴格；`bash -lc` 線性鏈 tree-sitter 拆解逐段評估；experimental）（`agent-configuration/rules.md:5-11,42-60,77-119`）。UI 三檔模式是這些軸的預設組合投影。
- **sandbox enforcement 平台原生**：macOS Seatbelt、Linux/WSL bubblewrap+seccomp（Landlock fallback）、native Windows elevated/unelevated；政策無法 enforce 時**拒跑而非靜默 unsandboxed**（`sandboxing.md:27-30,87-95`；`permissions.md:496-510`）。
- **排程管理面不在 CLI**：Scheduled tasks 的建立/管理 UI 只在 ChatGPT web/desktop（desktop 可綁本地 project/worktree）；Codex CLI 與 IDE extension **無 Scheduled 管理介面**（`automations.md:16-19,31-37`）。
- **headless／SDK**：`codex exec`（預設 read-only sandbox；`--json` JSONL 事件流；`--output-schema`；`--ephemeral`；`--ignore-user-config`/`--ignore-rules`）＋`codex exec resume --last|--all`＋互動 `codex resume`＋TS/Python SDK（start/continue/**resumeThread**）＋App Server（`non-interactive-mode.md:5-8,53-74,90-118`；`developer-commands.md:218-227,303-313`；`codex-sdk.md:14,24-64,73`）。
- **plugins**：ChatGPT 與 Codex 共用 **universal plugin directory**；plugin 可捆 skills＋MCP servers＋lifecycle hooks（manifest `.codex-plugin/plugin.json` 的 `hooks` 條目；plugin hooks 同樣須逐定義 trust；相容 `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` env）（`skills-and-plugins.md:15-18,80-91`；`hooks.md:368-401,396-397`）。
- **memory**：local Codex clients 用獨立 local memory store（與 ChatGPT memory 分離）（`customization/memories.md:5-8,45`）。

## 功能對照（2026-08-14 實查：線上文檔 + 本 session 實測）

> 擴充機制面（ai-rules 消費的那一層）幾乎都有對應物；深度與事件/欄位覆蓋多為 Claude 子集。

| 能力 | Claude Code | ZCode | Muse Code | 對等度 |
|------|------------|-------|-----------|--------|
| Instructions | CLAUDE.md layers | AGENTS.md 原生（subagent 亦注入，v3.7.1+） | ✅ AGENTS.md（walks up 至 .git；同目錄 AGENTS.md 優先；需 trust 才載 project）（Muse Code `muse-code/configuration.md:41,46`） | ✅ |
| Skills / Commands | SKILL.md / `.claude/commands` | 同格式 + `.agents/` 相容路徑 | ✅ SKILL.md 四源＋跨 harness 自動發現 `~/.claude/skills`/`~/.codex/skills`；`muse skills` CLI（Muse Code `muse-code/extending.md:60,67`） | ✅ |
| Hooks | 完整事件 + 5 種 type | 3.7.7 user-level 可用；7 事件子集、process/command 兩 type、專案層被忽略（實測：`zcode/cn/docs/hooks.md` + 04 報告 §7 修訂） | ✅ 13 事件（跑沙箱外，cleared env 小 allowlist）（Muse Code `muse-code/extending.md:89,94`） | ⚠️ 子集 |
| Subagents | 巢狀、豐富 frontmatter（skills/hooks/memory/isolation） | Beta user 級；不可巢狀、frontmatter 精簡、未知欄位靜默忽略（`zcode/cn/docs/subagents.md`） | ✅ 容量 8-64＋worktree 隔離、孫代共享；observers×4 背景觀察者（Muse Code `muse-code/extending.md:33,39`） | ⚠️ 子集 |
| MCP | 完整 + inline 定義 | 完整；subagent 自訂 tools 清單會殺 MCP 工具（須手寫全名，萬用無效） | ✅ 不在沙箱（與兩家皆異）（Muse Code `muse-code/extending.md:112`） | ✅（有陷阱） |
| Plugins | marketplace | `.zcode-plugin` manifest，相容 Claude plugin（Browser Use 即官方 plugin，`zcode/cn/docs/browser-use.md`） | built-in skills 為主；鏡像未載 marketplace（Muse Code `muse-code/extending.md:62` 僅述 plugin bundles，`rg marketplace` 於 `muse-code/` 0 命中） | ✅ |
| Memory | CLAUDE.md + auto-memory + agent memory | Memory 功能 v3.6.4+（預設關、自動提取、專案隔離、`~/.zcode/cli/memories/`，`zcode/cn/docs/memory.md`） | ✅ 三 scope（personal-project/project `.agents/memory/`/personal；MEMORY.md 索引注入上限 48 檔）（Muse Code `muse-code/configuration.md:95,102,114`） | ✅ |
| 排程 | cron / scheduled tasks | Automations 定時任務（重複規則、綁會話投遞、上限 20、僅本地，`zcode/cn/docs/automations.md`） | ✅ `/loop` 5-field cron＋shorthand（5m/1h/2d；無 cadence 預設每 10 分鐘）；7 天自動過期；cron tools 管理（Muse Code `muse-code/interactive.md:105,112,114`） | ✅ |
| 瀏覽器自動化 | Playwright MCP | 內建瀏覽器面板 + 官方 Browser Use plugin（防網頁注入指令、Chrome 登入態導入） | 鏡像未載（`computer-use.md` 為 Meta API 層非 CLI；`muse-code/` 無 CLI 瀏覽器自動化記載；`rg browser` 命中 subscriptions/auth/changelog（皆非 CLI 自動化工具記載））（Muse Code 鏡像未載） | ✅ 各有千秋 |
| 背景執行 | v2.1.198+ 預設背景 + background agents | 背景 subagent（spawn 端 `run_in_background`，runtime 實測）+ 閒時任務 | ✅ observers×4＋背景 subagents（`/tasks`/`/subagents`）＋headless `muse exec` 背景（Muse Code `muse-code/extending.md:19,39`＋`muse-code/interactive.md:119`） | ✅ |
| 權限 | 宣告式 glob 白名單 + 多模式 | 4 檔 GUI 模式 + SQLite 精確匹配記憶（04 報告 §7） | ✅ 三態 approval-mode＋judge＋staged 審批＋Seatbelt/bubblewrap 沙箱；granular `--disable-write`/`--disable-shell`（--help 實機，鏡像未載）（Muse Code `muse-code/permissions.md:31,42,47,75`＋`muse --help`） | ⚠️ 無宣告式白名單 |
| LSP | 原生 plugin set | 無原生 → 自建 MCP 替代（symbol-query-routing「跨 harness LSP 載體對照」） | 無原生 LSP；工具面＝bash/read_file/search 三件套（Muse Code 鏡像未載；`rg LSP` 於 `muse-code/` 0 命中） | ❌ workaround |

**Claude 有、ZCode 無**：巢狀 subagent、agent teams、`/fork`、headless `-p`/Agent SDK（CI 自動化）、宣告式權限 glob、原生 LSP、hook 的 prompt/agent/http/mcp_tool type、subagent per-agent hooks/skills/memory/isolation、設定熱載入（ZCode 全靠 per-session 快照）。

**ZCode 有、Claude 無**：Repo Wiki（自動架構指南、宣稱帶 source location、隨 code 自動刷新、存 `~/.zcode/v2/repo-wiki/` 不進 repo，`zcode/cn/docs/repo-wiki.md`）、閒時任務（算力富餘免費執行）、飛書/微信 Bot Channel、內建瀏覽器 UI（element 選成 context）。

## Auto-memory 載入截斷（2026-09-03 雙端源碼反組譯，CLI 三版同構）

兩家同語義：**200 行 或 25,000 字元（UTF-16 code units，CJK 一字計 1）先到者截**——截斷處附 WARNING（易忽略）、尾端條目不進 context；注入路徑不剝 frontmatter（K9r 讀碼：`Wut()` 直收 `indexContent` 全文，行數含 frontmatter 行）。

| | 行數限 | 大小限 | 證據 |
|---|---|---|---|
| ZCode | 200（`Vut`） | 25,000 字元（`mre=25e3`——`Wut()` 以 `t.length` 比較） | `/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs` |
| Claude Code | 200（`YD`） | 25,000 字元（`GF=25000`——`mLe()` 回傳 `byteCount:t.length`：**欄位名叫 byteCount、計量是 `.length`＝字元**；TextEncoder 在另一 scope 屬 crypto，勿誤讀） | `~/.local/share/claude/versions/<v>` |

「25KB」＝兩端警告把 25,000 字元 ÷1024 顯示成 "24.4KB" 的**假象**——全鏈無 bytes 量測。重跑驗證（量詞須彈性——常數前綴不足 100 字元，`.{100}` 會 0 hits）：

```bash
rg -a -o '.{30}mre=[0-9*]+.{30}' /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs
rg -a -o '.{0,100}YD=200,GF=25000.{0,60}' ~/.local/share/claude/versions/$(ls -t ~/.local/share/claude/versions/ | head -1)
```

治理配套（ai-rules 端）：generator 硬 gate chars 22,500（真線 90%）／lines 190＋bytes 24,000 info 預警——單一源在 `skills/memory-audit/scripts/generate_index.py` 註解。


## 對 ai-rules 的啟示

ai-rules 現為 CLAUDE.md 體系。要真正跨 harness，最小可攜單位是 **`AGENTS.md`**（兩家原生讀、第三家可 import）；`SKILL.md` 內容格式可攜但**語意不可攜**（ai-rules 的 skills 深度綁 `/build`、`/commit`、`.kanban/` 等 Claude 工作流）。Hook 在 ZCode 3.7.7+ 已有對等物（user-level config hooks，stdin 相容 Claude snake_case）——腳本可跨 harness 共用，僅註冊 config per-harness（且無目錄載入點，不能用 symlink 部署）。
