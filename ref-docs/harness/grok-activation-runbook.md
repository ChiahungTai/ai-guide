# grok machine-local activation runbook（AIR-218 L1a 產出；user 執行面＝L1b）

> 本檔是 **machine-local activation 的操作程序**（~/.grok 與 ~/.claude 均為 user 主權面——
> 工程卡 AIR-218 零碰，只寫本 runbook）。目標形態＝**native bundle 為 grok 單一 instruction
> authority**（`~/.grok/AGENTS.md`＝guide＋neutral rules 打包），關閉 Claude instruction
> 重複載入但**保留 Claude hooks compatibility**（hooks 正是要 reuse 的面）。
> 執行者＝user（或 user 授權的 session）；每步附可判斷言，全程可 rollback。
## 前置事實（查證依據）

- grok rules 載入：global `~/.grok/`→repo root down 到 cwd，**無 size cap**（`features/project-rules.md:26`）——部署面配 30KiB 治理預算（`scripts/deploy_agents.py` `GROK_ATTENTION_BUDGET`，注意力自限非 runtime 線）。
- `[compat.claude]` cells 逐面獨立（skills/rules/agents/mcps/hooks 各自開關——**rules 與 agents 獨立**，關 rules 不殺 hooks）；`[paths] extra_rule_dirs` 是與 cells 平行的第二載入路徑（cells 全關仍可經此重複載入）。
- import marker＝二元組：`~/.grok/claude_import_state.json`（檔案）＋`~/.grok/config.toml` `[claude_compat] imported = true`；**只清其一無效**（行為實證 1.0.44：清一個 hooks 仍＝6，兩者皆清＝20）。清 marker **不會**移除 stale snapshot——`~/.grok/hooks/imported-from-claude.json` 檔案本身另貢獻 4 條 dangling。
- 現況 hooks 載入態＝broken：6 條（4 dangling user＋2 plugin），真實 `~/.claude/settings.json` 13 支 guard 零載入。
- c 形重複成本：語義重複已證（guide＋rules 全量 ×2），**full-c 精確 token 未量**（舊 +3,273 tok 數字基於 guide-only 假 bundle，已作廢）。

## 步驟（建議序；①②③ 無順序依賴，先 ③-1 消 dangling 再開 live-scan）

### ① 部署 native bundle（第 4 target）

```bash
cd /Users/ctai/Github/ai-guide && uv run python scripts/deploy_agents.py
```

斷言：stdout `[OK] deployed to 4/4 non-Claude harnesses`；`wc -c ~/.grok/AGENTS.md` ≤ 30,720；
`tail -1 ~/.grok/AGENTS.md`＝`<!-- bundle-end -->`（尾哨未截斷）。

### ② 部署形收斂（關閉 Claude instruction 重複，保留 hooks）

> **AIR-215 註記（2026-10-01，本節已超越）**：hooks 通道已**切斷**——13 支 guard 遷至 grok 原生 `~/.grok/hooks/ai-guide.json`（governance `[registrations.grok]` merge="file" 生成），`[compat.claude]` 現為 **全 false**（rules/agents/hooks/skills/mcps）＋`[paths] extra_skill_dirs` 移除（inert）。CC 第一方控制面退役完成；skills 72 支經 `~/.agents/skills` 根、agents 9 支經 `~/.grok/agents` symlink、MCP native 5 條＋codebase-memory-mcp 棄用。回滾＝compat cells 回 true＋重建 `~/.claude` symlink（AIR-215 卡 notes）。以下原始建議值保留供回滾形態參照。

編輯 `~/.grok/config.toml`：

```toml
[compat.claude]
rules = false    # 關 ~/.claude/rules 直讀
agents = false   # 關 ~/.claude/CLAUDE.md instruction scan（agents cell 仍載 CLAUDE.md——rules=false 單獨不夠）
hooks = true     # 【AIR-215 已改 false——hooks 遷 native ai-guide.json；此行為回滾形態】
# skills / mcps 維持現值（skills 面無重複問題）
```

同檔 `[paths]` 段：`extra_rule_dirs` **移除 `"~/.claude/rules"`**（第二 bypass 路徑——cells 全關後仍會經此把 rules 載回來）。

### ③ import 修復（清 marker＋處理 stale snapshot）

形態 B（可 script 化，建議）：

1. 刪（或改名備份）`~/.grok/hooks/imported-from-claude.json`——消除 4 條 dangling（`/Users/ctai/Github/ai-rules/hooks/*`）
2. 刪 `~/.grok/claude_import_state.json`——marker 半一
3. `~/.grok/config.toml` 移除 `[claude_compat]` 段（`imported = true`）——marker 半二（順帶消一條 configWarning）

形態 A（TUI 互動替代）：session 內 `/import-claude` slash command 或歡迎畫 `Ctrl+I`——
re-import 對 snapshot 檔是覆寫或合併＝**UNKNOWN**（未實測）；若走此形，執行後必跑下方
斷言，`rg 'ai-rules'` 非零命中即改走形態 B。

### ④ user 執行後可判斷言（L1b 驗收面）

```bash
# cwd＝任一 trusted 目錄（如 /Users/ctai/Github/ai-guide）；輸出落 repo 內 .agent-tmp/
grok inspect --json > /Users/ctai/Github/ai-guide/.agent-tmp/grok-inspect.json
```

- [ ] global `~/.grok/AGENTS.md` 在 projectInstructions／rules 清單且 enabled（b 形生效）
- [ ] hooks 計數 **≥15**（13 user live-scan＋2 plugin；trusted project 再加 project 條）——【AIR-215 後改判準：active hooks＝native `~/.grok/hooks/ai-guide.json` 13 條（source dir `~/.grok/hooks`）＋plugin 2；`.claude` source 條目全 disabled＝斷言通過態】
- [ ] `rg -c 'ai-rules' /Users/ctai/Github/ai-guide/.agent-tmp/grok-inspect.json`＝**0 命中**（dangling 全消）；`rg -c 'ai-guide/hooks'` ≥13
- [ ] `~/.claude/CLAUDE.md`／`~/.claude/rules` **不再是** grok enabled instruction source（c 形重複收斂）
- [ ] 行為斷言（B2 重跑）：寫入 synthetic-pool 任務被擋（事件流現 deny、exit 2）；普通檔案 write positive control 成功

### ⑤ rollback

- 部署形回退：`[compat.claude]` rules/agents 回 `true`＋`[paths] extra_rule_dirs` 加回 `"~/.claude/rules"`（接受重複載入）。
- import 機制回退：`~/.grok/hooks/imported-from-claude.json` 自備份還原（或接受 13 支 live-scan 形態——live-scan 本身是建議形，回退 marker 才需要）。
- bundle 回退：`git -C /Users/ctai/Github/ai-guide checkout <prev> -- rules/ ai-development-guide.md && uv run python scripts/deploy_agents.py`（單檔也有 `.md.bak` 自動備份機制）。
- 全退（grok 面完全棄用）：刪 `~/.grok/AGENTS.md`＋`[compat.claude]` 全 false＋依 [LIFECYCLE.md](LIFECYCLE.md) 退役流程評估鏡像除名。

## 已知邊界（不因 runbook 消失）

- FileChanged 雙鉤（memory-dirty-sensor／watch-seed）在 grok **n-a**（無此事件；watchPaths passive 被忽略）——零改碼。
- compact-tail-inject 在 grok **partial/unknown**（`transcript_path`／`source` payload 契約 UNKNOWN；SessionStart(compact) 語義形態不同）——payload 證據補齊前不硬修。
- grok binary 自動更新（1.0.13→1.0.44 已自動發生）——契約面隨版本漂移，驗收以當日 `grok --version` 為準（LIFECYCLE 更新節 grok 變體）。
