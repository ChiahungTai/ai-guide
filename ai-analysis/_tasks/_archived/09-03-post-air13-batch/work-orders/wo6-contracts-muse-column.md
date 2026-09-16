# 工單：contracts.md 補 Muse Code 對照欄（WO-6）

> 定位：`ref-docs/harness/contracts.md` 的對照表（7 維度）與功能對照表（12 行）補 muse 欄——每格附鏡像 file:line 證據。

## 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡
- 只准動 `ref-docs/harness/contracts.md` 一檔
- 禁 /tmp；禁版本號／日期／統計數字新增
- **硬約束（user 裁定）**：每格附鏡像 `file:line`；**過時以原站為準**（檔頭加一句此性質聲明）；鏡像文檔未載、僅 CLI `--help` 可見的事實，標「`--help` 實機，鏡像未載」——禁把未查證的當文檔事實

## 目標（一句話）

給 contracts.md 兩張表各補 Muse Code 欄：對照表 7 維度全補；功能對照 12 行補「Muse Code」欄（形態一句；既有「對等度」欄語義是 CC↔ZCode，不動）。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`；working tree 已有 WO-5 未 commit 修改（既有狀態非衝突——你的改動僅 contracts.md）
- 證據源：`ref-docs/harness/meta/` 鏡像（muse-code/ 子目錄＋muse-code.md）＋CLI `muse --help`／`muse exec --help`（實機在場）

## 必讀（按序）

1. `/Users/ctai/Github/ai-rules/ref-docs/harness/contracts.md` 全文（表格結構與既有格式的 file:line 引用慣例）
2. 鏡像文檔逐格取證：`ref-docs/harness/meta/muse-code/configuration.md`、`extending.md`、`interactive.md`、`permissions.md`、`session-messaging.md`、`workflows.md`、`../overview.md`

## 已決策（勿重辯）＋矛盾例外

**事實底稿（2026-09-03 已實機調查——你逐格對鏡像驗證＋取 file:line，不合則以鏡像為準）**：

對照表 7 維度（muse 欄事實）：
- **專案/全域指令檔**：AGENTS.md 為主（walks up to `.git` boundary；同目錄 AGENTS.md 優先於 CLAUDE.md——後者被忽略並警告）；project rules 需 workspace trust、user rules 永遠載（configuration.md）
- **Skill**：SKILL.md 四源（built-in/user/project/plugin）；user 根＝`$XDG_CONFIG_HOME/muse/skills`＋`~/.agents/skills`＋`~/.claude/skills`＋`~/.codex/skills` 自動發現；`muse skills` CLI（list/inspect/enable/install/validate/import --from claude|codex）；frontmatter 收尾 `---` 須自成一線（extending.md）
- **Subagent**：lead spawn 子代理、容量 8-64（`agents.execution_capacity`）、per-child worktree isolation（拒絕不靜默回落）、孫代共享 root-tree capacity（extending.md multi-agent 節）
- **Slash command**：內建豐富（/plan /grill /taste /side /goal /loop /name /resume /fork /rewind /export 等）；互動面為主（interactive.md）
- **Hook**：`.muse/hooks.json`（project，trust 後生效）＋user settings hooks；13 事件（SessionStart/UserPromptSubmit/PreToolUse/PermissionRequest/PostToolUse/PreLLMCall/PostLLMCall/PreCompact/PostCompact/SubagentStart/SubagentStop/Stop/SessionEnd）；**hooks 跑在沙箱外**（extending.md hooks 節——對照表可標註此差異）
- **MCP**：settings.json `mcp_servers`（stdio/streamable_http；mode required/optional；相容標準 `mcpServers` key）；**MCP 工具不在沙箱內**（extending.md MCP 節）
- **主設定檔**：`~/.config/muse/settings.json`（`schema_version:1` 必填、缺省檔 OK）（configuration.md）

功能對照 12 行（muse 形態一句/格）：
- Instructions ✅（AGENTS.md＋trust 分層）／Skills ✅（四源＋跨 harness 自動發現）／Hooks ✅ 13 事件（跑沙箱外）／Subagents ✅（容量 8-64＋worktree 隔離、observers×4 背景觀察者）／MCP ✅（不在沙箱——與兩家皆異）／Plugins：查鏡像——無 marketplace 記載則寫「built-in skills 為主；鏡像未載 marketplace」／Memory ✅ 三 scope（personal-project/project `.agents/memory/`/personal；MEMORY.md 索引注入上限 48 檔）（configuration.md）／排程 ✅（/loop cron 5-field＋7 天自動過期＋cron tools）（interactive.md）／瀏覽器自動化：查鏡像（computer-use.md 是 Meta API 層非 CLI——若 CLI 層無記載標「鏡像未載」）／背景執行 ✅（observers＋背景 subagents＋headless exec 背景）／權限 ✅（approval-mode 三態＋approval-judge＋staged shell 審批＋OS sandbox〔Seatbelt〕＋granular `--disable-write/--disable-shell`〔--help 實機，鏡像未載〕——**分層最細**）／LSP：無（原生工具面＝bash/read_file/search 三件套）

**矛盾例外**：鏡像內容與底稿不符 → 以鏡像為準並在報告記錄差異；兩者皆無 → 標未驗證，不留空格不腦補。

## 範圍限定

- 動：`ref-docs/harness/contracts.md`
- 不動：其他一切（含 ref-docs/harness/meta/ 鏡像本身）

## 工具接線

bash（cat/rg/ls）＋`muse --help`／`muse exec --help`（實機標記用）；字串搜尋一律 rg；禁 /tmp。

## 驗收（命令＋預期，逐條實跑）

1. `rg -c "Muse Code" ref-docs/harness/contracts.md` → 計數 ≥19（7 維度欄頭＋12 行；實際以表結構為準，報告附最終計數與算法）
2. `rg -n "muse-code/configuration.md" ref-docs/harness/contracts.md` → ≥2 命中（指令檔/設定檔/memory 格的證據引用）
3. `rg -n "extending.md" ref-docs/harness/contracts.md` → ≥3 命中（skill/subagent/hook/MCP 格）
4. `rg -n "過時以原站" ref-docs/harness/contracts.md` → 檔頭聲明命中
5. `rg -n -- "--help 實機" ref-docs/harness/contracts.md` → ≥1 命中（granular 權限等 CLI-only 事實的標記）
6. 逐格抽查自驗：抽 4 格（Hook 事件數／MCP 沙箱外／Memory 三 scope／Subagent 容量）比對鏡像行號正確——報告附 4 組「格值 ↔ 鏡像行:內容」對照
7. 範圍：`git diff --name-only` ＝ contracts.md＋WO-5 既有檔

## 證據紀律＋PII 禁令

每格 file:line 是硬要求（無行號的格標「鏡像未載」並寫明查證過程）；報告禁 email／人名（鏡像 docs 有作者資訊不入）。

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔 diff 摘要 2. 兩張表 muse 欄逐格值＋file:line（底稿不符處標差異） 3. 驗收 1-7 原始輸出 4. 偏差記錄 5. 未驗證項 6. 建議 reviewer 聚焦點
