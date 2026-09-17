# AIR-116 Segment 0 探針執行紀錄（P0-1～P0-10）

> 執行日：2026-09-17。執行環境：ai-guide repo branch `air-116`（開工 commit main `f67d99b`）。
> 探針 script 落 `.agent-tmp/guides-refactoring/p0{2,3}-*-probe.py`（暫存，隨清淤消失；本文留存逐字輸出）。
> **總判讀：十探針全數完成；三致命先驗（P0-2/P0-3/P0-7）全數解除；零翻案——架構可凍結。**

## 總表

| # | 探針 | 判決 | 摘要 |
|---|------|------|------|
| P0-1 | codex `[hooks.state]` trust 語義 | ✅ 不可代寫（確認） | state key 公式逐字驗證；`--dangerously-bypass-hook-trust` 僅 per-invocation；**`:1:0` 已 trusted（討論後 user 已 approve）** |
| P0-2 | CC/ZCode JSON round-trip byte-stability | ✅ **致命先驗解除** | 兩家皆被 `json.dumps(indent=2, ensure_ascii=False)`＋尾換行逐字重現；RMW 插入僅動插入點 |
| P0-3 | CC settings.json symlink 寫入語義 | ✅ **致命先驗解除（策略定案）** | `os.replace` 直接打 symlink 路徑＝斷鏈實證；**installer 必先 `resolve()` 再原子寫** |
| P0-4 | muse install/approve 非互動性 | ✅ 可行 | 無 `--yes` 但無 TTY 要求；歷史 pipe 環境實裝成功；**發現 `muse plugins hook test --fixture` 內建測試命令** |
| P0-5 | CC `/hooks` CLI 替代 | ✅ 確認無 | claude 2.1.270 無 hooks 子命令——手動 UI 步驟文件化 |
| P0-6 | 四家 live config 快照 | ✅ 基準到手 | shasum＋大小＋三家 hooks 子樹形態（CC/ZCode 結構不同家） |
| P0-7 | deploy_agents 冪等重跑 | ✅ **致命先驗解除** | 重跑三目標 `[SKIP] (identical)`、hash 不變、exit 0；`--dry-run` 輸出形態透明可透傳 |
| P0-8 | skills symlink 母目錄形態 | ✅ 母鏈形態 | `~/.agents/skills`、`~/.claude/skills` 皆單一 symlink → repo `skills/`（73 entries）——installer 建 2 條即成，零遷移 |
| P0-9 | codex mixed representation 現況 | ✅ 現況乾淨 | 無 active `~/.codex/hooks.json`（僅 `.bak-*`／`.retired-*` 殘留，不載入）；`~/.codex/hooks/` 空目錄 |
| P0-10 | codex discovery/trust 讀取機制 | ✅ 候選②成立 | `~/.codex/log/` 不存在（候選①死）；`[hooks.state]` 檔面直讀可用（候選②實證）＝診斷腿 |

---

## P0-1 codex `[hooks.state]` trust 語義

**方法**：直讀 `~/.codex/config.toml`（13,142 bytes）＋`codex --help` 掃描。

**CLI 面**（`codex-cli 0.154.0-alpha.6.2`，`codex --help` 行 100-102 逐字）：

```
      --dangerously-bypass-hook-trust
          Run enabled hooks without requiring persisted hook trust for this invocation. DANGEROUS.
          Intended only for automation that already vets hook sources
```

→ trust bypass 僅 per-invocation、非持久化＝**installer 無 persist-trust API**（openai/codex#21615 討論結論再證）；無 `codex hooks` 子命令。

**state key 公式逐字驗證**（config.toml 行 208-242）：key_source 三形態並存——

- inline hooks：`"/Users/ctai/.codex/config.toml:<event>:<group>:<handler>"`（如 `pre_tool_use:0:0`）
- plugin hooks：`"delegate@delegate-market:hooks/hooks.codex.json:session_start:0:0"`、`"muse@muse-market:hooks/hooks.json:session_end:0:0"`（`plugin@market:path` 形態）
- event 為 snake_case 正規化（config 段 PascalCase `[[hooks.PreToolUse]]` → key `pre_tool_use`）

**位置公式活驗證**：config.toml 兩個 PreToolUse group——group 0＝`matcher = "Bash"`（行 333，兩 handler：block-python-c-comment `:0:0`、block-python-file-write `:0:1`）；group 1＝`matcher = "apply_patch"`（行 381，codex_memory_path_deny `:1:0`）。state 條目與公式逐字吻合（12 條全在場）。

**⚠ 狀態比 EP/討論記錄新**：`.agent-tmp/guides-refactoring/air116-discussions.md` 記「`pre_tool_use:1:0` 缺場＝寫進 config≠生效活證」——**本次探針該條已在場**（行 241-242，`trusted_hash = "sha256:51a711d8..."`）＝user 已於討論後完成 AIR-100 hook 的 codex approve。EP AC-3.2 括號「現機 `:1:0` 缺場為活證」過時；verify 實作照「trust 態如實報告」原則不受影響。`[hooks.state]` orphan 證據（muse/delegate 殘留他 source 條目）仍支持 Q6 leave-and-report 契約。

## P0-2 CC/ZCode JSON round-trip byte-stability（致命先驗）

**方法**：`.agent-tmp/guides-refactoring/p02-roundtrip-probe.py`（唯讀——parse→重序列化比對＋模擬插入編輯）。

**CC `~/.claude/settings.json`（13,104 bytes，→ repo `settings.json`）**：

```
top-level keys: ['$schema', 'skillListingBudgetFraction', 'env', 'permissions', 'model', 'hooks', 'worktree', 'statusLine', 'enabledPlugins', ...]
hooks.Notification: 1 / hooks.Stop: 1 / hooks.SessionEnd: 1 / hooks.SessionStart: 2 / hooks.PreToolUse: 2 / hooks.PostToolUse: 1 / hooks.FileChanged: 1
byte-equal serialization params: indent=2, ensure_ascii=False   （＋尾換行）
RMW insertion-edit: changed lines=6, only-additions=True
```

**ZCode `~/.zcode/cli/config.json`（3,977 bytes）**：

```
top-level keys: ['mcp', 'plugins', 'hooks']
hooks.enabled: … / hooks.events: …   （注意：與 CC 的 event-map 結構不同家）
byte-equal serialization params: indent=2, ensure_ascii=False   （＋尾換行）
RMW insertion-edit: changed lines=8, only-additions=False（差異＝插入點前 entry 收尾 `}`→`},` 一行＋新增塊）
```

**判讀**：
1. **兩家 live config 都被 `json.dumps(indent=2, ensure_ascii=False)`＋尾換行逐字重現**——序列化參數就此凍結；byte-stability 可達成，「生成 diff＋user 手貼」降級形態不觸發。
2. key order 保持（byte-equal 蘊含）；RMW 非編輯區僅插入點收尾逗號一行變動——可接受線，文件化進 S2。
3. **CC hooks 子樹形態＝`hooks.<Event>: [groups]`（event→matcher group 陣列）；ZCode＝`hooks: {enabled, events}`**——manifest 模板必須分家原生格式，禁跨形複製。
4. CC `FileChanged` 1 條在場（EP 已知：CC 單家）。

## P0-3 CC settings.json symlink 寫入語義（致命先驗）

**事實**：`~/.claude/settings.json` → `/Users/ctai/Github/ai-guide/settings.json`（13,104 bytes；`.gitignore:37` gitignored）。

**fixture 實測**（`.agent-tmp/guides-refactoring/p03-symlink-probe.py`，temp dir，不碰 live）：

```
(a) write_text via symlink path: link_still_symlink=True, target_content='{"a": 2}\n'
(b) os.replace(tmp, symlink_path): link_still_symlink=False, link_is_regular_file=True, content='{"a": 3}\n', real_untouched='{"a": 2}\n'
(c) os.replace(tmp, link.resolve()): link_still_symlink=True, target_content='{"a": 4}\n'
```

**判讀**：
- (b) 實證**原子寫直接打 symlink 路徑＝symlink 被換成普通檔（斷鏈），真實目標留舊內容**——EP 擔心的場景為真。
- (c) 實證**先 `Path.resolve()` 到真實目標再 `os.replace`＝link 保留、target 正確更新**。
- **S2 鐵律：CC 面 atomic_write 前必 `resolve()`**；`--check` 對 symlink 健康加驗（`is_symlink()`＋resolve 指向正確）。

## P0-4 muse install/approve CLI 非互動性

**CLI 面**（`muse plugins --help` 逐字節錄）：

```
install <path> [--scope user|project] [--json]     Install a local plugin bundle into the cache
install <plugin>@<marketplace> [--json]            Install a plugin from a configured marketplace snapshot
approve <plugin-id[[:kind]:capability-id] | stable-id> [--json]   Trust and enable current runtime capability definitions
reject <plugin-id...> [--json]                     Trust and disable
hook test <plugin-id>:<hook-id> | plugin:<plugin-id>:hook:<hook-id> --fixture <path> [--json]
enable/disable <id> / update <id> / inspect <id> [--json]
```

**判讀**：
- install/approve **無 `--yes` 類 flag 也無 TTY 要求記載**；AIR-100 live receipt（2026-09-14 四 gate PASS）即 pipe 環境 CLI 實裝成功——非互動可行（L2 實證先例）。install 流程免 TTY 降級（「印命令 user 貼」不觸發）。
- **新發現：`muse plugins hook test <plugin-id>:<hook-id> --fixture <path>`**——muse 原生 hook fixture 測試命令，S3 `--verify` 的 muse probe 可消費（補強 pipe payload 法）。

## P0-5 CC `/hooks` CLI 替代

`claude --version`＝2.1.270；`claude --help` 無 hooks 子命令（僅 `--bare`〔skip hooks〕、debug filter 字樣、`--include-hook-events`〔遙測面〕）。→ **手動 `/hooks` UI 步驟文件化**（Q4 分欄確認）。

## P0-6 四家 live config 快照（S1 模板逆抽取基準）

| config | sha256（前 12） | bytes |
|---|---|---|
| `~/.claude/settings.json`（→ repo settings.json） | `485c2ba1df24` | 13,104 |
| `~/.zcode/cli/config.json` | `68dfbe65c106` | 3,977 |
| `~/.codex/config.toml` | `8d6b714b08cf` | 13,142 |

hooks 子樹形態：
- **CC**：`hooks.{Notification,Stop,SessionEnd,SessionStart×2,PreToolUse×2,PostToolUse,FileChanged}`（event→group 陣列；完整條目內容 S1 逆抽取時逐字取）
- **ZCode**：`hooks: {enabled, events}`——結構與 CC 不同家
- **codex**：七 groups（行 324-387）——`Interrupt`（chatgpt-web，非 ai-guide）、`PreToolUse` matcher=`Bash`（ai-guide block-python ×2）、`SessionEnd`（ai-guide stop-notification）、`Stop`（ai-guide stop-notification）、`SessionStart`（codebase-memory-mcp，非 ai-guide）、`SubagentStart`（codebase-memory-mcp，非 ai-guide）、`PreToolUse` matcher=`apply_patch`（ai-guide AIR-100）
- muse plugin：`muse-plugins/memory-governance/` 在冊（install/approve 態由 `muse plugins inspect --json` 動態取，S3）

**所有權初盤**（AC-1.3 對帳表輸入；manifest membership 終判歸 S1）：codex 面已註冊 7 groups 中 ai-guide 擁有 4（Bash 群、SessionEnd、Stop、apply_patch 群）；非 ai-guide 3（Interrupt＝chatgpt-web、SessionStart/SubagentStart＝codebase-memory-mcp）——不在 manifest membership 內、`--check` 不掃（F-5 窄鍵語義）。

## P0-7 deploy_agents 冪等重跑（致命先驗）

**CLI 面**：`deploy_agents.py [-h] [--scope SCOPE] [--dry-run]`（default scope=neutral）。

**冪等實證**（hash → `--dry-run` → real run → hash 對比）：

```
重跑前後三部署檔 shasum byte-equal（~/.zcode/AGENTS.md ≡ ~/.codex/AGENTS.md ≡ ~/.config/muse/AGENTS.md = 3193b6de5d69…）
real run 輸出（節錄）：
  [SKIP] /Users/ctai/.zcode/AGENTS.md (identical)
  [SKIP] /Users/ctai/.codex/AGENTS.md (identical)
  [SKIP] /Users/ctai/.config/muse/AGENTS.md (identical)
[OK] deployed to 3/3 non-Claude harnesses
real-run exit=0；dry-run exit=0
```

**dry-run 輸出形態**（透傳友善——逐 harness `[OK]/[WARN]` 行＋gate %＋`[DRY-RUN] skipping deploy` 收尾）：

```
[OK] [zcode] bundle: 17 rules (scope=neutral) + guide   size: 544 lines, 32,565 bytes (…35% of 90KiB gate)
[OK] [codex] bundle: … 35% of 90KiB gate
[WARN] [muse] bundle at 88% of size gate (36KiB) -- deploy still OK, but slimming should happen before the gate…
[DRY-RUN] skipping deploy
```

**判讀**：wrap 前提全成立——冪等、退出碼語義單純（0=OK）、輸出逐行可透傳。`--dry-run` 映射直接成立。附帶：muse bundle 88% gate（WARN 常態）；三部署檔彼此 byte-identical（parity）。

## P0-8 skills symlink 母目錄形態

```
~/.agents/skills -> /Users/ctai/Github/ai-guide/skills   (lrwxr-xr-x, 73 entries)
~/.claude/skills -> /Users/ctai/Github/ai-guide/skills   (lrwxr-xr-x)
```

→ **兩家皆單一母鏈**（非逐支 symlink 陣列）。`--surface skills`＝建 2 條 symlink；已存在且 resolve 正確＝零動作（冪等）；現況機零遷移。

## P0-9 codex mixed representation 現況

`~/.codex/` 無 active `hooks.json`——僅 `hooks.json.bak-20260916-migration`、`hooks.json.bak-ai-guide-rename`、`hooks.json.retired-20260916`（0916 single-representation convergence 的歷史殘留，codex discovery 不載入帶後綴檔）；`~/.codex/hooks/` 空目錄。→ **現況基準乾淨**；mixed-rep 偵測照 codex 討論⑦入 `--check`（未來防禦）。附帶：`config.toml.bak-*` 已累積九份——.bak prune（保留 3 份）政策的現況佐證。

## P0-10 codex discovery/trust 讀取機制

- 候選①（`~/.codex/log/`＋RUST_LOG）：**`~/.codex/log/` 不存在**——死候選。
- 候選②（`[hooks.state]` 檔面直讀）：**成立**——P0-1 已實證 key＋`trusted_hash` 可直讀；在場性＋hash 比對（modified 偵測需可重算 hash——公式在 codex source，本 EP 不逆推，以「在場性診斷＋user `/hooks` 目視＋層三 host-level fixture」為驗收腿，符合 EP 降級契約）。
- 候選③（app-server/IPC）：不需求，跳過。
- **版本耦合記錄**：`codex-cli 0.154.0-alpha.6.2` 基準；state key 公式與 `--dangerously-bypass-hook-trust` 行為隨版本可能變——README 記版本診斷行。

---

## 對 EP 的架構影響彙總（零翻案；四點精化）

1. **序列化參數凍結值**（P0-2）：`json.dumps(indent=2, ensure_ascii=False)`＋尾換行——S2 直接採用。
2. **CC 寫入鐵律**（P0-3）：`resolve()` 後原子寫；`--check` 加 symlink 健康腿。
3. **skills 面定案**（P0-8）：兩條母鏈 symlink，零遷移。
4. **muse probe 強化**（P0-4）：`muse plugins hook test --fixture` 入 manifest probes 候選；trust 面維持 user approve＋inspect 監看。

新事實（EP 文字微陳舊，不影響架構）：`:1:0` 已 trusted（AC-3.2 括號過時）；codex 面非 ai-guide groups 所有權初盤見 P0-6。
