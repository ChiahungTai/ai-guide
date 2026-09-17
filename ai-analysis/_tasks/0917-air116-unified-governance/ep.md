# AIR-116 跨 harness 治理安裝統一套件——五部署面收斂＋installer＋drift gate（full tier standalone EP）

> **ep_type**: implementation
> baseline: `46fba51`（擴範圍重寫當下 main HEAD——session 快照，撰寫環境 Bash 權限被拒無法 `git log -1` 實查；**開工時必以 `git log -1`／`git status` 重刷為準**）。dirty 聲明：working tree 有未追蹤的 `ai-analysis/_tasks/0917-air116-unified-governance/`（本 EP 檔所在任務家）；`skills/python-type-gap/` 退役已於 46fba51 commit——無其他殘留。
> 追蹤卡：`backlog/tasks/air-116 - *.md`（To Do；AC#1 維持原文——見「範圍裁決紀錄」）。

## 範圍裁決紀錄（user 0917 拍板，覆寫先前 memory-only 範圍）

1. **v1 吞全部部署面**：rules bundle／skills 分發／hooks 註冊／agents registry／memory governance——五面全入 scope。**更正（0917 審查）**：muse R1 對卡 AC#1 的「僅 memory 域」判讀有誤——卡 AC#1 自創卡即五面全文；五面＝AC#1 本體驗收（非超額交付），closure receipt 逐面開立，memory receipt 為其中一腿；不可行面附機制證據（AC#1 括號條款）。
2. **AIR-110 消費契約＝裁決 (b)**：110 呼叫本套件子安裝器、依賴**穩定 CLI 契約**（install/--check/--verify/--uninstall，見 S6）、110 卡補 blocked-by dependency——本 EP 定義該契約，110 收尾時對齊。
3. 討論 findings（codex 8 條全文＋muse R1-R7 摘要）已吸收：單一源＝`.agent-tmp/guides-refactoring/air116-discussions.md`＋指派摘要；逐條落點見 Q 段與各 Segment。

## 實作總覽

AIR-100 政策（D1-D5＋closure 三層閘）已落地且 memory 域 hooks 已 commit；本 EP＝**部署面包裝工程**：把「共享 scripts＋五套離散部署面」（rules bundle 部署器、skills symlink 活視圖、hooks 四家註冊、agents 雙 registry 生成、muse memory governance plugin）收斂為**單一治理套件＋一鍵 installer＋drift gate＋bootstrap CLI 契約**，消除安裝面維護漂移、並為 AIR-110 全新機器 bootstrap 提供唯一安裝入口。不改任何閘的行為本體（divert+deny／path-deny／後綴擋形態已驗證）；不重寫既有部署器（wrap 不取代，見 Q2）。

**套件目錄＝repo-root `governance/`**（自 memory-only 版的 `memory-governance/` 擴名——範圍已非 memory 域；命名吸收擴範圍裁決）。

段落：**Segment 0（探針，架構凍結前）→ S1 套件骨架與 manifest（五面單一源）→ S2 installer 核心（install/dry-run/uninstall，六 surface）→ S3 approve 分欄與 --verify（含 codex discovery 三層驗收）→ S4 drift gate（--check，五面 parity）→ S5 monitor 收編與排程（已落地，本 EP 對帳）→ S6 bootstrap CLI 契約（AIR-110 消費）**。

## 設計決策（設計問題 1-9 拍板；Segment 0 探針可翻案者標 ⚠）

### Q1 套件形態 → **manifest 驅動套件目錄 `governance/`＋scripts 不搬**（⚠ P0-3 可部分翻案）

新建 repo-root `governance/` 套件目錄：`manifest.toml`（單一源——`[package]`、`[surfaces]`（五面安裝語義各自成節）、`[scripts]`（共享腳本相對路徑指既有 `hooks/`＋`scripts/`）、`[registrations]`（per-harness 註冊模板＋目標 config＋merge 鍵）、`[approve]`（分欄表資料化）、`[probes]`（verify 定義）、`[bootstrap_cli]`（S6 穩定契約的機器可讀投影））＋ `registrations/`（模板）＋ `install.py`（installer）＋ `README.md`（運維單一源）。muse plugin 本體＝既有 `muse-plugins/memory-governance/`（不改——範圍柵欄；manifest 條目指過去，installer 呼叫 muse CLI）。

**Tradeoff 已衡量**（同 memory-only 版，結論不變）：scripts 搬移＝四家 live config 絕對路徑引用同步改的高風險一次性遷移，否決；無實體 manifest＝--check 無生成源，否決。manifest 提供套件邊界，scripts 不搬提供路徑穩定性。

### Q2 與既有部署器的關係 → **呼叫封裝（wrap），不重寫、不取代**

五面中三面已有權威工具，installer 是 **orchestration 層**——子進程呼叫＋輸出透傳＋退出碼串接，絕不複製其邏輯：

| 面 | 既有權威工具 | installer 行為 |
|---|---|---|
| rules bundle | `scripts/deploy_agents.py`（90KiB/36KiB gate、--dry-run、fresh-session 驗證——bundle 線單一源） | `--surface rules` → subprocess 呼叫 `uv run python scripts/deploy_agents.py`（含其 --dry-run 映射）；muse 面 88.2% 等工具自身輸出透傳，installer 不再判讀 |
| skills 分發 | 無安裝動作（71 支 symlink 母鏈活視圖即時生效） | `--surface skills` → **建 symlink**：`~/.agents/skills`、`~/.claude/skills` 母鏈指 repo `skills/`（現值即母鏈形態；新機器沿用，零遷移原則——不動現況機逐支殘留） |
| hooks 註冊 | 共享 scripts（`hooks/*`）＋四家 config 手工註冊 | installer 直接面——**全部 hooks**（memory 域 block-memory-index-write/memory-watch-seed/…＋codex_memory_path_deny，非 memory 域 block-python-×2、sensors、stop-notification），不只 memory 域 |
| agents registry | `scripts/sync_agents.py`（生成制＋--check parity） | `--surface agents` → bootstrap 時 subprocess 觸發 sync；`--check` 時串接其 `--check` 退出碼 |
| memory governance | `muse-plugins/memory-governance/`（plugin 本體）＋AIR-100 S-A/B/C 註冊 | installer 直接面——muse plugin install/approve 走 muse CLI；hooks 部分併 hooks 面 |

**術語紅線**：本 EP 的「deploy」＝**安裝套件到 machine-local 消費點**；與 rules bundle 線的 `deploy_agents.py`（bundle 內容部署）是兩條線——installer 後者只 wrap 不擁有。文件一律避免裸用「deploy」指本套件動作，用 install/uninstall。

### Q3 installer CLI → `governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run] [--uninstall] [--check] [--verify]`

- **Python 地板守衛（muse R5，red line 級）**：machine `python3`=3.9、tomllib 需 3.11+——installer 檔頭 `sys.version_info < (3,11)` 即 fail-loud（印「請改用 `uv run python governance/install.py …`」）退出非零，**禁默默降級或 crash 於 import**；正典調用形態＝`uv run python governance/install.py`（README 首行）。
- **merge 語義（各家）**：
  - **CC**：`~/.claude/settings.json` 是 symlink→repo `settings.json`（gitignored local-only）——installer 經 `Path.resolve()` 寫**真實目標**（P0-3 驗），JSON 子樹 merge。**雙層鍵語義**：manifest membership＝install/uninstall 的權威集合（只有 manifest 列出的條目被增/刪）；`--check` 掃描鍵＝**窄鍵**（hooks 條目 `command` 含 `/ai-guide/hooks/` 或 `/ai-guide/muse-plugins/`）——permissions/env 等非 hooks 鍵永不掃描；**JSON byte-stability（muse R3）**：寫回採「讀原文→結構化編輯→serialize」時，序列化參數（indent/ensure_ascii/尾換行）以 P0-2/P0-3 探針實測原檔風格凍結，非套件鍵區域 byte-equal。
  - **ZCode**：`~/.zcode/cli/config.json` 的 `hooks:` 子樹 merge（`hooks/AGENTS.md:3` 鐵律——整檔覆蓋會毀 mcp/plugins 區塊）；逐條目 idempotent upsert；round-trip byte-stability 同 CC 由 P0-2 探針定（鍵序若無法保持，凍結「語義等值＋非套件鍵 JSON-equal」為可接受線並文件化）。
  - **codex**：`~/.codex/config.toml` inline `[[hooks.*]]` 段 append（帶 `# ai-guide governance` 註解標記）；**TOML transaction（codex ③）**：讀 preimage＋hash/stat → memory 產生新全文 → 寫 temp＋**parse 驗證** → 寫入前確認 live file 仍等於 preimage（不等＝fail/retry，防與 codex runtime `/hooks` approve 寫 `[hooks.state]` 的 concurrent read-modify-write lost-update race）→ `os.replace` atomic rename。**不代寫 `[hooks.state]`**——trust hash 由 codex runtime 於 user approve 時寫，手寫＝偽造 trust；「首次觸發自動 trust」可能性已由 codex 討論①排除（無 supported installer API，openai/codex#21615 在要求中），文件化。
  - **muse**：installer 呼叫 `muse plugins install <repo>/muse-plugins/memory-governance --scope user`＋`muse plugins approve <id>`（CLI 可自動化；非互動性由 P0-4 驗）。
- **備份紀律（.bak 政策——muse R7，red line 級）**：**僅變更備份**（compute 後 content-equal 的目標零寫入零備份——冪等重跑不增殖 .bak）；備份用 `shutil.copy2`（保留 mtime）；prune 保留每目標最近 3 份；**malformed config（JSON/TOML parse 失敗）絕不覆寫**——fail-loud 報告原檔路徑＋parse 錯誤，退出非零，由 user 處置。
- **plan journal（muse R2）**：install/uninstall 執行前把 plan（逐 target：動作/備份路徑/preimage hash）落 `~/.local/share/ai-guide/governance-plan-journal/<timestamp>.json`——multi-target 中途 kill 後可據 journal 精確回滾（哪些 target 已寫、哪些未動）；**prune**：保留最近 10 份（比照 .bak 政策語義，數量 implement 期可調並記卡）。
- **形態先例**：`sync_agents.py` compute-then-apply 安全模型（任何寫入前 return；temp＋`os.replace` 原子寫）。

### Q4 approve 面 → 可自動化／必須手動分欄文件化

| harness | approve 形態 | installer 角色 |
|---|---|---|
| muse | `muse plugins approve <id>`（CLI） | **自動化**（install 流程內含）＋S-E monitor 監 `trusted_enabled` |
| CC | `/hooks` UI 審查（user 手動） | 印手動步驟；probe 驗 firing |
| ZCode | per-session 快照自動生效（僅需新 session） | 印「重開 session」提示 |
| codex | trust approval＝codex startup review／`/hooks` TUI（user 手動——無 installer API，見 Q3） | 印手動步驟；不碰 `[hooks.state]`；**discovery 三層驗收**（見 S3） |

**codex state key（codex ①②，診斷用契約）**：key 公式＝`"<key_source>:<event>:<group_index>:<handler_index>"`（如 `.../config.toml:pre_tool_use:0:1`）。**positional key 非 stable identity**——group 插入/刪除/重排即變（group_index 是位置非 hook ID）；installer/verify/**--check 一律不以 predicted key（`:2:0` 類序號）作永久期望值或驗收契約**，key 僅作診斷輸出；驗證以 codex 實際 **discovery 結果**（source+event+matcher+command+trust status）為準。機器證據：AIR-100 `^apply_patch$` group 依公式應為 `pre_tool_use:1:0`，現機 `[hooks.state]` 無此條——「寫進 config ≠ 已生效」的活證。

### Q5 drift gate → `--check` 五面 parity＋codex trust/content drift 獨立 failure class

live 逐面與 manifest 生成期望比對：CC/ZCode＝JSON 子樹語義 diff；codex＝套件註解段存在＋條目內容；muse＝plugin 在冊＋source.path 指 canonical＋approve 態＋**source↔cache hash 腿（muse R6）**；rules/agents＝串接 `deploy_agents.py`／`sync_agents.py` 自身檢查退出碼（各自 --dry-run/--check 語義，installer 不重造）。**codex 專屬腿（codex ⑦）**：registration 正確但 `trustStatus=Modified`（內容 hash 變——套件 upgrade 改 command/path 後常態）報**獨立 failure class**「需 user 再 approve」非一般 drift；**mixed representation 偵測**——install/uninstall 寫入前各掃一次（防同 semantic hook 叠加）＋`--check` 常態掃；`--verify` 不掃（probe 面非 config 態面）。「同一 semantic hook 另有 `~/.codex/hooks.json` copy 或重複 inline copy」（同 layer 混載會 warning＋雙 fire，codex runtime 兩者並載非覆蓋）。drift 即列清單 exit 1，零寫入。排程＝併 S-E monitor（daily）。

### Q6 uninstall/rollback → plan journal 回滾＋codex state leave-and-report＋後續 hooks trust 驗證

muse＝`muse plugins remove`；CC＝移除套件自有 hooks 條目（保留他鍵）；ZCode＝逐條目移除（識別鍵同 install）；codex＝移除套件註解段；skills＝拆母鏈 symlink（`~/.agents/skills`、`~/.claude/skills`）——**明示影響**：活視圖失效＝harness 即時讀不到 ai-guide skills（session 內已載入者不受影響）；不刪 repo 母體；rules/agents＝hooks 面以外不受 uninstall 影響（wrap 不擁有——**uninstall 不反部署 bundle/registry**，README 明載：rules bundle 回退走 `rules/AGENTS.md` 部署紀律、agents registry 走 sync_agents 自身）。共享 scripts 留 repo（uninstall 只拆接線不刪源——live config 中斷接線＝dead but harmless，先例 AIR-100 S-A rollback 條）。**codex 專屬（codex ⑤）**：`[hooks.state]` orphan 條目 codex 無 GC 路徑（現機 Muse plugin trust state 殘留為證）——installer **不憑 predicted key 無條件刪 state**；契約＝移除前取當前實際 key/current hash，`key＋trusted_hash` 皆與 owned hook 相符才精準 cleanup，否則 **leave-and-report**（文件化隨 session 失效）；**positional index 前移**——本套件 group 之後若有人再 append 同-event group，uninstall 本套件會使後續 group index 前移、其既有 trust 失效——uninstall AC 必驗「受影響後續同-event hooks 的 trust 態」，不只驗 owned block 消失。**multi-target 中途 kill（muse R2）**：plan journal 記錄逐 target 完成態，kill 後 `--verify`/`--check` 可指出哪些 target 已寫哪些未動，resume 或回滾二選一（journal 有指引）。

### Q7 monitor → **已落地，本 EP 收編對帳**（非新建）

現況事實（0917）：`scripts/muse_approve_monitor.py` 擴展＋plist 排程**已安裝並首次實跑 PASS（launchd 在線）**——S5 的任務由「新建排程」改為：**對帳**（已落地形態 vs 本 EP manifest/probe 定義的期望態，缺腿補齊）＋擴為五面 health（Q5 drift＋approve 態＋註冊在場）＋收編入套件（`--surface monitor` 的 install/uninstall 映射到 plist 裝載）。`muse_approve_monitor.py` 改名或被吸收由 S5 對帳後定（吸收時 rg 殘留掃描收尾）。

### Q8 告警消費（muse R4）→ 三選一由 Segment 0 後 user 裁決，EP 預設形態

health check 告警需有落地消費者，三選一：(a) log-only＋`--verify` 手動查、(b) `osascript` notification（macOS user 面）、(c) 寫 sentinel 檔供開場 session 讀。EP 預設 (a)（零外溢、與 hook log 同域），(b)/(c) 若 user 於 S5 開工前裁決則改——不阻塞其他段。

### Q9 alias 語義（codex ④）→ 文件化確認

live 實值 matcher＝`apply_patch`（未錨字串比對——0917 caller 字串比對實證後由 `^apply_patch$` 改；**manifest/registrations 模板一律採 live 實值，AC-1.2 模板等值以此為準**）。`apply_patch` 一條 matcher 足以覆蓋 built-in path——`Edit`/`Write` 是 `apply_patch` 的 **matcher aliases**（hook stdin canonical `tool_name` 仍是 `apply_patch`，非「轉換」而是「內部 tool 暴露 canonical name＋額外 aliases」）。README 記此語義，禁再擴第二條 matcher。

## UC 盤點

元專案（docs mode 混合：本 EP 含可執行 installer/monitor code）：掃受影響命令/rules 清單，無 library Capabilities 表格。

### Backlog 關聯
- 本 EP 對應卡：AIR-116（To Do）。上游：AIR-100（Done——政策 D1-D5＋四家註冊面落地，本 EP 收斂其安裝與註冊面並擴至五面）。下游消費者：AIR-110（To Do——全新機器 bootstrap，依裁決 (b) 呼叫本套件、加 blocked-by——S6 定契約）。
- 自動建卡：**禁做**（本指派硬約束禁 git 寫操作）——AIR-116 已是本 EP 追蹤卡；擴範圍後若 user 認為需拆承接卡，回報裁決而非自行建卡。

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md，跳過（元專案正當跳過）。

### 掃描範圍
- `AGENTS.md`（hooks 節／Muse memory 節／專案結構五面描述）、`hooks/AGENTS.md`、`hooks/zcode-registration.json`、`muse-plugins/memory-governance/{README.md,.muse-plugin/plugin.json,hooks/}`、`scripts/{deploy_agents,sync_agents,muse_approve_monitor}.py`、live config 三份（`~/.claude/settings.json`、`~/.zcode/cli/config.json`、`~/.codex/config.toml`）、`.agent-tmp/guides-refactoring/{air116-discussions,mech-synthesis,f-probe-output}.md`、air-100/110/113/115/116/117 卡、`~/.agents/skills` 與 `~/.claude/skills` symlink 形態現值。

### 同主題 memory 條目（結案蒸餾範圍）
- `rg` 主題詞（plugin／hooks 註冊／install／bootstrap）掃池：`reference_muse-code-cli-facts`、`reference_codex-cli-exec-facts`（AGENTS.md 引用的計費/CLI 事實條目）命中——形態判讀＝穩態 reference，無弧流水過期詞；結案蒸餾補「統一安裝套件／五面 CLI 契約」新事實，不重複處置。

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| 四家 memory 治理閘（行為本體） | ✅ | hooks/*＋muse plugin＋codex config.toml（AIR-100 S-A/B/C，已 commit） | 不變 | 本 EP 零行為改動，只收斂安裝/註冊面 |
| rules bundle 部署器 | ✅ | `scripts/deploy_agents.py`（gate/--dry-run/fresh-session） | 更新 | 被 installer wrap（Q2）——工具本體零改動 |
| skills 分發（symlink 活視圖） | ✅ | 71 支 symlink（即時生效） | 更新 | 新機器建法入套件（AIR-113 fleet 處置 Done） |
| agents registry 生成制 | ✅ | `scripts/sync_agents.py`（--check PASS） | 更新 | bootstrap 觸發入套件（Q2 wrap） |
| ZCode hooks 註冊範本 | ✅ | hooks/zcode-registration.json | 更新 | S1 收編為套件 registrations 一員 |
| S-E monitor＋launchd 排程 | ✅ **已啟用** | plist 在線、首次實跑 PASS（0917） | 更新 | S5 改「對帳＋擴五面」，非新建 |
| 多機安裝（手動文檔形態） | ✅ | hooks/MULTI-MACHINE.md＋setup-memory-symlinks.sh | 更新 | 收尾步驟改指套件 installer（AIR-110 對齊） |
| python-type-gap / flow-feedback | 已退役 | 46fba51 / c095241 | 無 | 空白面，不入套件 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| 單一治理套件（五面 manifest＋註冊模板） | 📋 | `governance/`（S1） |
| 一鍵 installer（六 surface：install/dry-run/uninstall/--check/--verify） | 📋 | `governance/install.py`（S2/S3/S4） |
| drift parity gate（五面 vs 生成源，含 codex trust drift class） | 📋 | install.py `--check`（S4） |
| 五面 governance health 排程 | 📋 | 既有 monitor 對帳擴展＋`deploy/` plist 收編（S5） |
| bootstrap 穩定 CLI 契約（AIR-110 消費） | 📋 | `[bootstrap_cli]`＋README 契約節（S6） |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 全套一鍵安裝 | `install.py --surface all`（乾淨機器或現況機） | 五面全就位：hooks 四家註冊、rules bundle 部署（deploy_agents 被呼叫且輸出透傳）、skills symlink、agents registry sync、muse plugin install+approve；machine-local config 有 `.bak`（僅變更者）；重跑零 delta（冪等） | `--check` 綠＋`ls *.bak-*` | installer |
| SM-2 | 乾跑 | `--dry-run` | 列出逐面/逐 target 將寫入 diff，零檔案落盤 | config mtime/內容不變 | installer |
| SM-3 | ZCode config 整檔保護 | install 寫 `~/.zcode/cli/config.json` | mcp/plugins 區塊逐鍵不變（只動 hooks 子樹） | install 前後 `jq 'del(.hooks)'` diff 空 | installer |
| SM-4 | live config 手工漂移 | user 手改 CC settings.json 移除套件條目 | `--check` exit 1 列 drift；`--surface hooks` 重裝修復 | check 輸出 | drift gate |
| SM-5 | 解除安裝 | `--uninstall --surface hooks` | 套件條目移除、他鍵原樣；rules/agents 面不動；codex state leave-and-report | diff 對照 `.bak` | installer rollback |
| SM-6 | muse update 後 approve 漂移 | `muse plugins update` 未 re-approve | health check 告警（非 trusted）＋指引 | monitor 輸出 | monitor |
| SM-7 | codex trust 未過 | install 後 codex 未跑 approve 流程 | installer 印手動步驟；`--verify` discovery 層顯 Untrusted（**預期態非 FAIL**，trust 層獨立報告）；`[hooks.state]` 未被代寫 | config.toml 無新增 state 條目 | approve 程序 |
| SM-8 | installer 自身 crash／中途 kill | 寫入中途例外或 kill -9 | 原子寫入——目標檔要么舊要么新；plan journal 記逐 target 完成態，可精確 resume/回滾 | journal 檔＋單元測試注入 | installer |
| SM-9 | ZCode 新 session 才生效 | install 後舊 session | 文件化預期：hooks per-session 快照，新 session 前不判失敗 | README 條文 | installer |
| SM-10 | rules 面 wrap | `--surface rules` | subprocess 呼叫 `deploy_agents.py`，其 gate/--dry-run 輸出逐行透傳，退出碼串接；installer 不重造 bundle 邏輯 | stdout＋exit code | installer／rules 面 |
| SM-11 | 新機器 bootstrap | AIR-110 呼叫 `install.py --surface all` 於空白機 | 七面全就位：hooks 四家註冊、rules 部署**＋CC 端 CLAUDE.md/rules symlink**、skills 母鏈、agents sync**＋雙 registry symlink**、muse plugin＋**池拓撲 setup-memory-symlinks**；hooksPath＝repo clone 步驟（110 清單項，非本套件面） | S6 checklist 全綠 | bootstrap 契約 |
| SM-12 | malformed config | live config JSON/TOML parse 失敗時 install | 絕不覆寫——fail-loud 報路徑＋parse 錯誤，非零退出，user 處置 | stderr 訊息 | installer |
| SM-13 | Python 3.9 直跑 | `python3 governance/install.py`（machine 3.9） | 檔頭版本守衛拒跑，印「改用 `uv run python`」，非零退出——禁 import 期 crash | exit code＋訊息 | installer |
| SM-14 | codex 後續 group 前移 | uninstall 後同-event 後續 hooks | positional index 前移使後續 hooks trust 失效——uninstall 輸出**警告其 trust 態變化**（Untrusted/Modified），文件化 | uninstall 輸出＋README | uninstall |

## 測試規劃段（TC 凍結）

> author_family: glm（ZCode 側 authoring）。oracle 獨立性＝live config 事實＋closure 三層閘契約＋冪等恆等式（install∘install＝install），非待測實作自證。amendment 附錄見檔尾。

| TC-ID | claim | Given-When | oracle（predicate） | oracle_source | evidence class | uncovered |
|-------|-------|------------|---------------------|---------------|----------------|-----------|
| TC-1 | installer 冪等（五面） | 已安裝機器重跑 `--surface all` | P1-1 第二次執行逐面 zero-diff；P1-2 exit 0；P1-3 零新增 `.bak`（僅變更備份） | 冪等恆等式（sync_agents compute-then-apply 先例） | L2 | — |
| TC-2 | ZCode 非套件鍵保護 | install 前後取 config | P2-1 `del(.hooks)` 後 JSON 相等；P2-2 plugins/mcp 鍵在 | hooks/AGENTS.md 鐵律（文件契約） | L4 | 鍵序（P0-2 探針定可接受度） |
| TC-3 | dry-run 零寫入 | `--dry-run --surface all` | P3-1 全部 machine-local config byte-equal；P3-2 stdout 含逐面計畫；P3-3 wrap 面（rules/agents）子進程以 --dry-run/--check 形態呼叫不落盤 | dry-run 語義契約（setup-memory-symlinks.sh 先例） | L2 | — |
| TC-4 | drift 偵測雙向 | 手工增/刪一條套件條目後 `--check` | P4-1 exit 1＋drift 清單命中該條；P4-2 復原後 exit 0；P4-3 muse source↔cache hash 不符列 drift（R6） | parity gate 語義（sync_agents --check 先例） | L2 | codex trust drift 歸 TC-10 |
| TC-5 | uninstall 對稱 | install→uninstall→比對 | P5-1 套件條目全消；P5-2 非套件鍵 byte-equal（`.bak` 對照）；P5-3 共享 scripts 仍在 repo；P5-4 rules/agents 面不受 uninstall 影響 | Q6 設計（拆接線不刪源；wrap 面不反部署） | L2 | codex `[hooks.state]` 殘留（leave-and-report 文件化） |
| TC-6 | verify probe 逐家 | `--verify` | P6-1 muse trusted_enabled；P6-2 CC/ZCode pipe payload exit 2；P6-3 codex pipe payload exit 2 | closure 三層閘 Existence/Invocation 層 | L4 | actual-runtime firing（AIR-100 deferred 總驗卡承接，明列不重測；codex host-level 另見 TC-9） |
| TC-7 | health check 告警 | mock 非 trusted inspect 輸出 | P7-1 告警行＋非零 exit | AIR-100 TC-7 同型（monitor 擴展不改判定語義） | L2 | cron 載體自身故障（人工面） |
| TC-8 | 原子寫入＋journal | 注入寫入中途例外／kill -9 | P8-1 目標檔為完整舊檔或完整新檔（可解析）；P8-2 plan journal 記錄逐 target 完成態 | sync_agents temp+replace 先例；R2 journal 設計 | L2 | — |
| TC-9 | codex discovery 三層驗收（codex ⑥） | install 後逐層驗 | P9-1 層一：discovery 列出套件 hook 且 trust=**Untrusted**（註冊在場的預期態）；P9-2 層二：user `/hooks` approve 後 discovery trust=**Trusted**（user 手動，AC 驗收點非 installer 動作）；P9-3 層三：disposable fixture 跑真 codex `apply_patch` blocked test——目標檔 byte-level 未改 | codex runtime 行為（openai/codex hooks engine；2026 apply_patch deny-bypass bug 先例——script pipe 不可替代 host-level） | L4 | 層二依賴 user 在場（autonomous 段落標 blocked-on-user） |
| TC-10 | codex trust/content drift class（codex ⑦） | 套件條目內容變（模擬 upgrade）後 `--check` | P10-1 報「trustStatus=Modified，需再 approve」**獨立 class**（非一般 drift 措辭）；P10-2 mixed representation：植入同名 `hooks.json` copy → install/check/uninstall 至少一者報重複警告 | codex discovery hash 語義 | L4 | — |
| TC-11 | rules/agents wrap 透傳 | `--surface rules`／`--surface agents` | P11-1 子進程 argv 命中既有工具路徑；P11-2 stdout 逐行透傳；P11-3 退出碼串接（子工具非零 → installer 非零） | Q2 wrap 契約 | L2 | 既有工具自身行為（其測試管轄） |
| TC-12 | skills symlink 面 | 空母目錄（或暫存 fixture）`--surface skills` | P12-1 symlink 建立且 resolve 指 repo `skills/`；P12-2 冪等重跑零錯零重複 | Q2 skills 面設計 | L2 | 既有 71 支形態遷移（零遷移原則——不動現況） |
| TC-13 | malformed config 拒寫（R7） | fixture 損壞 JSON/TOML 後 install | P13-1 目標檔 byte 不變；P13-2 非零退出＋fail-loud 報告 | R7 設計 | L2 | — |
| TC-14 | Python 地板守衛（R5） | 以 3.9 直跑 installer | P14-1 載入任何 tomllib 前退出；P14-2 訊息含 `uv run python` 指引 | R5 設計（machine python3=3.9 事實） | L2 | — |

## 段落 0：探針（架構凍結前跑完）

| # | 探針 | 餵給 | 已知前提 |
|---|---|---|---|
| P0-1 | codex `[hooks.state]` 語義：installer 代寫 trust hash／首次觸發自動 trust 是否可能 | Q3/Q4/Q6 | 預期不可行（codex 討論①已排除——無 installer API，openai/codex#21615）；探針以本機 `codex-cli 0.154.0-alpha.6.2` 現況確認並記 state key 公式實測值 |
| P0-2 | CC/ZCode JSON round-trip byte-stability（muse R3）：讀-改-寫 serialize 後非編輯區是否 byte-equal；鍵序保持度 | S2 | hooks 子樹 merge 制已知；round-trip 鍵序/縮排/ensure_ascii 是風險——探針凍結序列化參數或宣告可接受線 |
| P0-3 | CC settings.json symlink 寫入語義：`Path.resolve()` 寫真實目標 vs 直接寫 symlink 路徑行為是否一致；repo `settings.json` 是否存在（gitignored） | S1/S2 | symlink 事實已知（hooks/AGENTS.md） |
| P0-4 | muse install/approve CLI 非互動性：subprocess 呼叫是否需 TTY／`--yes` 類 flag | S2 | README 命令形態已知；非互動未驗 |
| P0-5 | CC `/hooks` UI 有無 CLI 替代（`claude hooks` 命令面） | S3 | 預期無；確認後文件化手動步驟 |
| P0-6 | 四家 live config 現值快照（install 前後 diff 對照基準；S1 模板逆抽取源） | S1 | 已知事件子集限制：ZCode 無 FileChanged/SessionEnd（harness 限制，不可套件化修補——文件化）；CC FileChanged 單家（已知） |
| P0-7 | `deploy_agents.py` 現況機 idempotent 重跑（wrap 前提）：重跑是否零破壞、退出碼語義、--dry-run 輸出形態 | S2/S6 | bundle 線權威；wrap 只透傳，探針確認 subprocess 介面穩定 |
| P0-8 | skills symlink 母目錄現值：`~/.agents/skills`／`~/.claude/skills` 是目錄（逐支 symlink）還是母鏈；新機器建法選形態 | S2/S6 | 現況 71 支母鏈活視圖；零遷移原則——新機器形態不得強迫現況機遷移 |
| P0-9 | codex mixed representation 現況：`~/.codex/` 下有無 `hooks.json` 同層 copy；同 semantic hook 重複偵測的實測基準 | S2/S4 | codex 討論⑦——同 layer 混載 warning＋雙 fire |
| P0-10 | codex discovery／trust 讀取機制（CLI 無 hooks 子命令——--help 實測）：候選①`~/.codex/log/`＋`RUST_LOG=debug` fixture session 的 hook 載入行捕捉；②`[hooks.state]` 檔面讀取（key 在場＝曾 discovery＋approve；缺席不可推未發現）＋content hash 重算比對（若可逆推升正式腿，記版本耦合）；③app-server/IPC hooks 查詢介面 | S3/S4/TC-9/TC-10 | 0.154.0-alpha.6.2 基準；升級可能破壞——採用形態明文記版本耦合。**失敗降級**：三候選皆不可行 → codex 驗收腿＝`[hooks.state]` 在場性診斷＋user `/hooks` 目視＋層三 host-level fixture 為唯一 acceptance 腿 |

執行紀錄落任務家 `references/probe-results.md`（file:line 錨點＋逐字輸出）。**致命先驗**：P0-2（round-trip 若毀非編輯區且無法以凍結序列化參數避免→JSON 面寫入策略重設計，退「生成 diff＋user 手貼」降級形態）；P0-3（resolve 寫會斷 symlink 鏈→CC 寫入策略重設計）；P0-7（deploy_agents 若非 idempotent／介面不穩→rules 面退「印命令 user 自跑」降級形態）。P0-1/P0-5 預期確認「不可行/無替代」——只影響文件化不影響架構。P0-4 若需 TTY→muse 面退「印命令、user 貼」（降級非重設計）。

---

## S1｜套件骨架與 manifest（五面單一源）

### Context
- 現況：五套部署面離散——hooks 註冊四家手工（CC settings.json 多 hook 註冊、ZCode config.json＋範本 `hooks/zcode-registration.json`、codex config.toml inline 段、muse plugin）；rules bundle／agents registry 各有權威工具但無統一入口；skills 分發無安裝動作文件化於新機器。安裝面漂移根源（air-116 卡 Description）。
- UC 引用：實作「單一治理套件（五面 manifest＋註冊模板）」。
- 依賴：Segment 0 P0-6（live config 快照＝模板逆抽取基準）、P0-8（skills symlink 形態）、P0-9（codex mixed representation 基準）。無段落間依賴（S2-S6 全消費本段產物）。
- 語義約束：與 S2 共享「manifest 條目 schema 凍結」——installer 只消費不擴 schema；與 S4 共享「模板＝生成期望唯一定義」；與 S6 共享 `[bootstrap_cli]` 投影。
- 需求邊界繼承：無 /spec。範圍＝五部署面安裝/註冊收斂；**行為本體零改動**（閘邏輯、bundle 內容、registry 生成邏輯、plugin 功能皆不碰）。此邊界寫進 manifest README 首段。
- 基礎設施盤點：`hooks/zcode-registration.json`（既有範本——收編或被取代，零重複源原則定）；`agents/presets.toml`＋catalog（manifest schema 先例）；`muse-plugins/memory-governance/.muse-plugin/plugin.json`（套件自描述先例）。
- 依賴錨點：新 `governance/manifest.toml`（定義端＝本段新建；消費端＝S2 install.py、S4 --check、S5 health、S6 契約投影）；hooks 模板內容逆抽取自 live config（行號為 EP 撰寫時快照，開工重驗）。
- 技術選型：TOML manifest＋JSON/TOML 模板檔（各家原生格式，禁 JSON-encode-TOML 跨形）。成功標準＝manifest 條目可機械列舉、模板與 live config 現值逐字等值（逆抽取驗證）。

### 核心實作要點
- `governance/manifest.toml` 節結構：`[package]`（name/version）；`[surfaces]`（五面各一節：hooks〔含 `[surfaces.hooks.scripts]` 共享腳本清單——memory 域＋block-python-×2、sensors、stop-notification 全量〕、rules〔wrap 指針→`scripts/deploy_agents.py`＋argv 模板〕、skills〔symlink 形態＋目標清單，P0-8 定〕、agents〔wrap 指針→`scripts/sync_agents.py`〕、memory〔muse plugin 路徑＋approve/probe 定義〕）；`[registrations]`（per-harness 模板檔＋目標 config 路徑＋merge 鍵）；`[approve]`（Q4 分欄表資料化）；`[probes]`（verify 定義——含 codex discovery 三層）；`[bootstrap_cli]`（S6 契約機器可讀投影）。
- `governance/registrations/`：`cc.json`（hooks 子樹套件條目）、`zcode.json`（同語義，吸收 `hooks/zcode-registration.json`——後者刪或留指針，零重複源）、`codex.toml`（`[[hooks.*]]` 套件段＋`# ai-guide governance` 註解標記）。
- `governance/README.md`：運維單一源（五面 install/uninstall/approve/健康檢查/已知限制：ZCode 事件子集、CC FileChanged 單家、codex trust 手動＋state key positional 語義、alias 語義 Q9）。
- **模板等值驗證**：逆抽取完成當下，模板渲染結果與 live config 對應段落逐字相等（零行為變更承諾的機械證據）。

### Pseudo Code（檔案結構）
```
governance/
  manifest.toml          # 五面單一源
  install.py             # S2
  README.md              # 運維單一源
  registrations/
    cc.json              # hooks 子樹套件條目
    zcode.json           # 同（吸收 hooks/zcode-registration.json，零重複源）
    codex.toml           # [[hooks.*]] 套件段＋註解標記
references/probe-results.md  # Segment 0 產物（任務家，非套件內）——ai-analysis/_tasks/0917-air116-unified-governance/references/
```

### 驗證策略
- **AC-1.1（Existence）**：`ls governance/{manifest.toml,README.md,install.py,registrations/cc.json,registrations/zcode.json,registrations/codex.toml}` → 全存在；`rg -c "surfaces\.(hooks|rules|skills|agents|memory)" governance/manifest.toml` → 五面各 ≥1 命中。
- **AC-1.2（模板等值）**：對照 P0-6 快照，`registrations/` 三檔渲染結果與 live config 對應段落逐字等值（diff 空，receipt 落 `references/`）。
- **AC-1.3（Invocation 對帳）**：manifest hooks scripts 清單 vs live 四家註冊面清單逐條對帳表（含非 memory hooks——block-python-×2、sensors、stop-notification 必在場）；`rg -l "zcode-registration" hooks/AGENTS.md AGENTS.md` 指到新位置零殘留（若收編）。
- **AC-1.4（Behavior）**：S2 完成後回填——install 重裝＝live config 與快照逐字等值（模板→live 方向行為驗證）。

---

## S2｜installer 核心（install／dry-run／uninstall，六 surface）

### Context
- UC 引用：實作「一鍵 installer（六 surface）」。
- 依賴：S1（manifest＋模板）；Segment 0 P0-2/P0-3/P0-4/P0-7/P0-8 前置。
- 語義約束：與 S4 共享識別鍵（套件自有條目以 command 路徑含 `/ai-guide/` 為鍵——install/check/uninstall 三模式同鍵）；與 S3 共享「installer 不做 approve 動作除 muse CLI 面」（Q4 分欄）；wrap 面（rules/agents）退出碼串接語義與 S6 契約凍結值一致。
- 基礎設施盤點：`scripts/sync_agents.py`（compute-then-apply＋temp/os.replace 原子寫先例）；`hooks/setup-memory-symlinks.sh`（dry-run 預設＋`.bak` 先例）；tomllib（3.11+ stdlib，讀 manifest/模板——R5 守衛前提）。
- 依賴錨點：`governance/manifest.toml`（定義 S1；消費 install.py `load_manifest()`）；CC 寫入真實目標＝`~/.claude/settings.json` readlink resolve（P0-3 驗）；codex TOML transaction（Q3）。
- 技術選型：單檔 installer（`governance/install.py`，stdlib-only）；成功標準＝TC-1/2/3/5/8/11/12/13/14 全綠＋五面 live 安裝 receipt。

### 核心實作要點
- **檔頭守衛（R5）**：`sys.version_info < (3,11)` → 印 `uv run python` 指引＋exit 非零（任何 tomllib import 之前）。
- CLI：`--surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run] [--uninstall] [--check] [--verify]`（--check S4 實裝、--verify S3、monitor 面 S5——骨架本段就位，stub exit 3 not-implemented 防 silent no-op）。**模式互斥矩陣（F-11）**：`--dry-run`／`--uninstall`／`--check`／`--verify` 四 flag **兩兩互斥**——違規組合 exit 2＋列出衝突 flag（不靜默短路；S6 退出碼表 exit 2 語義含 flag 衝突）；`--uninstall` 與 `--verify` mutually exclusive 亦落此矩陣。
- **compute-then-apply＋plan journal**：任何寫入前完成全部分析，plan（逐 target：動作/備份路徑/preimage hash）先落 journal（`~/.local/share/ai-guide/governance-plan-journal/<timestamp>.json`）再逐 target 執行——中途 kill 可精確 resume/回滾（R2）。
- 各家 apply（Q3 語義）：CC/ZCode JSON 讀→merge hooks 子樹→**凍結序列化參數**（P0-2 定）原子寫回；codex TOML **transaction**（preimage hash→memory 新全文→temp 寫＋parse 驗證→live 仍等 preimage 才 `os.replace`；不等＝fail/retry）；muse 委託 CLI；rules/agents＝subprocess wrap（argv 由 manifest 模板，輸出透傳＋退出碼串接）；skills＝建 symlink（形態 P0-8 定，冪等——已存在且 resolve 正確則零動作）。
- **識別鍵（F-5 雙層語義）**：manifest membership＝install/uninstall 的權威集合（只有 manifest 列出的條目被增/刪）；`--check` 掃描鍵＝窄鍵（hooks 條目 `command` 含 `/ai-guide/hooks/` 或 `/ai-guide/muse-plugins/`）——permissions/env 等非 hooks 鍵永不掃描；notification.sh 等已註冊但未入 manifest 的條目在 AC-1.3 對帳表逐條定歸屬。
- **symlink 面（rules/agents 擴充腿＋skills 面）compute-then-apply 同語義**：已存在且 resolve 指正確 target＝零動作（冪等）；斷鏈/指錯＝fail-loud 報告不自動改（user 處置，零遷移原則）。
- **.bak 政策（R7）**：僅 compute 後內容將變的 target 備份（`copy2`）；prune 保留每 target 最近 3 份；**parse 失敗＝拒寫 fail-loud**。
- uninstall：Q6 路徑（含 codex state leave-and-report＋後續 group 前移警告輸出）。

### Pseudo Code
```
main():
  guard_python_floor()                                  # R5：3.11+ 或 fail-loud
  manifest = tomllib.load(governance/manifest.toml); args = parse()
  plan = compute(args.surface, manifest, live_configs)  # compute-then-apply：全部分析先完成
  write_journal(plan)                                   # R2：逐 target 完成態追蹤
  if args.dry_run: print_plan(plan); return 0           # 零寫入（wrap 面以 --dry-run/--check 形態呼叫）
  if args.check:  return check(plan)                    # S4 實裝
  if args.verify: return verify(plan)                   # S3 實裝
  for target in plan.targets:
      if args.uninstall: new = strip_entries(target)
      else:               new = merge_entries(target)   # codex 面＝TOML transaction（Q3）
      if byte_equal(current, new): mark_done("noop"); continue   # R7：僅變更備份
      backup_copy2(target); atomic_write(target, new); mark_done(target)
  print_manual_steps(args.surface)                      # Q4：CC/codex approve 手動、ZCode 新 session
def atomic_write(path, content):
  tmp = path.with_suffix(f'.tmp-{os.getpid()}'); tmp.write_text(content)
  if toml: assert_parses(tmp)                           # codex transaction：parse 驗證
  if preimage_changed(path): raise LostUpdate           # codex：併發防護，fail/retry
  os.replace(tmp, path)
```

### 驗證策略（closure 三層閘 receipt；rollback 驗證必含）
- **AC-2.1（Existence）**：`rg -n "version_info|add_argument|atomic|bak-|journal" governance/install.py` → 守衛/CLI 骨架/原子寫入/備份/journal 五 pattern 皆命中；`uv run python governance/install.py --help` → exit 0 列六 surface＋四 flag。
- **AC-2.2（Invocation）**：`--dry-run --surface all` → stdout 逐面計畫＋全部 machine-local config byte-equal（TC-3）；`python3 governance/install.py`（3.9）→ 守衛拒跑＋uv 指引（TC-14）。
- **AC-2.3（Behavior install，TC-1/2）**：實跑 `--surface all` → `--check`（S4 前用模板 diff 手驗）綠；重跑第二次 zero-diff＋零新增 `.bak`；ZCode `del(.hooks)` 前後非套件鍵相等；rules/agents 面輸出含 deploy_agents/sync_agents 逐行透傳（TC-11）。
- **AC-2.4（skills 面，TC-12）**：fixture 空母目錄跑 `--surface skills` → symlink 建立且 resolve 指 repo `skills/`；重跑冪等。
- **AC-2.5（rollback，TC-5）**：`--uninstall --surface hooks` → 套件條目全消＋`diff` 對 `.bak` 僅差套件條目行；`--uninstall --surface all` 後 machine-local config 回 install 前快照（codex `[hooks.state]` 殘留＝leave-and-report 豁免）；**rules/agents 面不受 uninstall 影響**（wrap 不反部署）；**回復後重 install 全綠**（uninstall↔install 對稱）；uninstall 輸出含後續 group 前移警告（SM-14）。
- **AC-2.6（failure-path，TC-8/13）**：單元測試注入寫入例外（monkeypatch os.replace raise）→ 目標檔完整舊檔＋journal 記錄完成態＋非零 exit；malformed fixture → 拒寫 fail-loud。**resume 實證**：模擬 multi-target 中途 kill（第 2/N target 後 terminate）→ journal 顯示已完成/未完成分野 → 重跑 install 僅執行 pending targets（輸出證明 noop 已完成者）。
- 已知未覆蓋：codex trust 後 actual firing 的 host-level 驗收歸 AC-3.4（TC-9）；muse CLI 異常分類（P0-4 後補）。

---

## S3｜approve 分欄與 --verify（含 codex discovery 三層驗收）

### Context
- UC 引用：實作「approve 與驗證 probe 程序」（Q4 分欄的機械面）。
- 依賴：S2 installer 骨架；P0-1/P0-5 前置（確認 codex trust 不可代寫、CC 無 CLI 替代→文件化手動）；P0-9（mixed representation 偵測基準）。
- 語義約束：與 S5 共享 probe 判定函式（verify 與 health check 同一實作，非兩套）；codex 驗收以 **discovery 結果為準**——predicted positional key 僅診斷輸出（Q4）。
- 基礎設施盤點：`muse plugins inspect --json`（真訊號源——plugin README 運維節）；AIR-100 closure receipt 形態（pipe 合成 payload exit 2）；`scripts/skill_activation_probe.py`（probe 先例）；codex ⑥ 三層驗收形態（discovery→trusted→fixture blocked）。
- 依賴錨點：probe 定義＝manifest `[probes]`（S1）；消費＝install.py `--verify`＋S5 health check。
- 成功標準：TC-6/TC-9/TC-10 綠；README approve 節與 Q4 分欄表逐行對應。

### 核心實作要點
- `--verify` 逐家執行 manifest probes：muse＝`muse plugins inspect <id> --json`→assert `trusted_enabled`；CC/ZCode＝`echo '<synthetic payload>' | python3 hooks/block-memory-index-write.py`→exit 2；codex＝**三層**（TC-9）：
  - 層一（discovery）：codex 對 config.toml 的 hook discovery 結果列出套件 hook（source/event/matcher/command）＋trust=Untrusted（install 直後預期態——**非 FAIL**，獨立報告行）；
  - 層二（trust）：user 經 `/hooks`／startup review approve 後 trust=Trusted——**user 手動，AC 驗收點標 blocked-on-user**，installer 僅印步驟；
  - 層三（host-level）：disposable fixture 跑真 codex `apply_patch` blocked test——目標檔 byte-level 未改（2026 apply_patch deny-bypass bug 先例：script pipe 不可替代 host-level）。
- **mixed representation 掃描（codex ⑦）**：verify 亦報「同一 semantic hook 另有 `~/.codex/hooks.json` copy／重複 inline copy」。
- capability/version gate（codex ⑧）：codex 面 verify 附版本/feature 記錄行（本機 `codex-cli 0.154.0-alpha.6.2` 基準）——真 gate 仍以 discovery＋host-level 為準，version 僅診斷。
- 手動步驟輸出：install 完成後印 CC（`/hooks` UI）、codex（新 session startup review／`/hooks`）、ZCode（新 session）三行——文案凍結於 README，installer 引用不複寫。
- AIR-100 deferred 總驗卡對 actual-runtime 面的分界維持——但 codex host-level（層三）**本 EP 做**（codex ⑥ 裁決：不可拿 script pipe 代替 installation acceptance）。

### Pseudo Code
```
def verify(manifest):
    for s, probe in manifest["probes"].items():
        ok, detail = run_probe(probe)      # PASS/FAIL/UNTRUSTED-EXPECTED＋detail
        print(f"[{s}] {status} {detail}")  # codex：三層獨立行＋mixed-rep 掃描＋版本診斷行
    return 0 if all pass else 1
```

### 驗證策略
- **AC-3.1（Existence）**：`rg -n "trusted_enabled|verify|discovery" governance/install.py` 命中；`rg -n "approve" governance/README.md` → 分欄表（「user 手動」於 CC/codex 行）＋state key positional 語義節。
- **AC-3.2（Invocation）**：`--verify` 於現況機器實跑 → muse PASS（trusted_enabled）、CC/ZCode pipe probe PASS（TC-6）、codex 層一 discovery 行在場（trust 態如實報告——現機 AIR-100 `:1:0` 缺場為活證）。
- **AC-3.3（Behavior negative，TC-7/10）**：mock 非 trusted inspect 輸出餵 muse probe → FAIL＋非零 exit；模擬內容變（Modified）＋植入 hooks.json copy → 獨立 class 報告＋重複警告。
- **AC-3.4（host-level，TC-9 層三）**：disposable fixture 實跑 codex `apply_patch` blocked test → 目標檔 byte-level 未改；層二（approve 後 Trusted）＝blocked-on-user，user 完成後補驗 receipt。
- **AC-3.5（誠實標記）**：README 與 `--verify` 輸出對未測面（CC/ZCode actual-runtime firing 等 AIR-100 deferred 範圍）標「未測——總驗卡承接」，`rg "未測" governance/README.md` 命中。

---

## S4｜drift gate（--check 五面 parity）

### Context
- 漂移根源實證：muse plugin source.path 曾指 rename 前舊路徑（air-100 notes 0916）；五套部署面手工維護（卡 Description）。
- UC 引用：實作「drift parity gate（五面，含 codex trust drift class）」。
- 依賴：S1 模板（生成期望源）＋S2 識別鍵；P0-9 前置。
- 語義約束：與 `sync_agents.py --check` 同語義（唯讀、drift exit 1）；rules/agents 面檢查＝串接既有工具（不重造）；與 S5 共享（health check 內嵌 drift 腿）。
- 基礎設施盤點：`scripts/sync_agents.py`（--check 先例）；closure 三層閘（本段 AC 消費——enforcement 段）；codex discovery hash 語義（Modified class，codex ⑦）。
- 依賴錨點：`--check` → 定義 install.py `check(plan)`／消費 S5 health＋`/sync-sources` 家族語義。
- 成功標準：TC-4/TC-10 綠；hook 由 S2 stub 轉正式。

### 核心實作要點
- 比對軸五面：CC/ZCode＝模板渲染 vs live config 套件條目（語義 JSON 比對）；codex＝套件註解段存在＋條目逐行等值＋**trust drift class**（registration 正確但 trustStatus=Modified → 獨立「需 user 再 approve」class）＋mixed representation 掃描；muse＝plugin 在冊＋source.path 指 canonical＋`trusted_enabled`＋**source↔cache hash 腿（R6）**；rules/agents＝子進程串接 `deploy_agents.py`／`sync_agents.py` 自身檢查退出碼。
- **positional key 禁入期望值**（codex ②）：`--check` 一律不把 `pre_tool_use:N:M` 序號寫進 manifest/期望——key 僅出現在診斷輸出。
- 輸出：逐面 drift 清單（缺條目/多條目/內容差/未 approve/trust-Modified/mixed-rep）＋修復指引（`install.py --surface <s>` 或 user approve 步驟）；exit 0/1。

### Pseudo Code
```
def check(plan):
    drifts = []
    for s in plan.surfaces:
        if s in ("rules", "agents"): drifts += passthrough_subcheck(s)      # 串接既有工具退出碼
        else:
            expected = render(plan.templates[s]); actual = extract_owned(live[s], OWNERSHIP_KEY)
            drifts += semantic_diff(s, expected, actual)   # + muse approve/hash 腿 + codex trust class + mixed-rep
    print_drifts(drifts); return 1 if drifts else 0
```

### 驗證策略（closure 三層閘——enforcement 段）
- **AC-4.1（Existence）**：`rg -n "def check|semantic_diff|trustStatus|hooks.json" governance/install.py` 命中；`--check --surface all` exit 0 於乾淨態。
- **AC-4.2（Invocation）**：手工刪 CC 一條套件條目 → `--check` exit 1＋清單命中該條（TC-4 P4-1）；復原 → exit 0（P4-2）。
- **AC-4.3（Behavior negative—muse/規則面）**：暫時 unapprove（或 mock）→ 列「未 approve」drift＋exit 1；muse source↔cache hash 不符 → drift 行（TC-4 P4-3）。
- **AC-4.4（Behavior—codex trust class，TC-10）**：模擬條目內容變 → 報 Modified class（措辭含「再 approve」）；植入 hooks.json copy → mixed-rep 警告。
- **AC-4.5（wrap 面串接）**：`sync_agents --check` 人工置 fail（暫時改 registry）→ `--check` 透傳該失敗非零。
- **AC-4.6（防 dead 檢查／缺席容錯）**：negative AC-4.2 即防恆綠；live config 缺席（新機器）→ 報 drift 不 crash（單元測試覆蓋）。

---

## S5｜monitor 收編與排程（governance health check——**已落地，本 EP 對帳**）

### Context
- 現況（0917 更新事實）：monitor 已安裝並**首次實跑 PASS（launchd 在線）**——S5 任務形態由「新建排程」改為「**對帳＋擴面＋收編**」：(1) 已落地形態 vs 本 EP manifest/probe 期望態對帳，缺腿補齊；(2) 擴為五面 health；(3) `--surface monitor` install/uninstall 映射到既有 plist 裝載機制。
- UC 引用：更新「五面 governance health 排程」（既有 UC 狀態表：✅ 已啟用→對帳擴展）。
- 依賴：S3 probe 判定函式＋S4 check 函式（複用非重寫）。
- 語義約束：monitor 判定語義與 AIR-100 TC-7 相容（muse 腿只擴不改）；排程載體＝launchd（`deploy/` 版控先例）；告警消費者＝Q8 三選一（預設 log-only，user 開工前可改）。
- 基礎設施盤點：`deploy/entitlements-probe.plist`（plist 版控落點先例）；既有 monitor/plist（已啟用——路徑與名稱開工盤點記 `references/`）；`scripts/muse_approve_monitor.py`（吸收後改名/刪除由對帳定，殘留掃描收尾）。
- 依賴錨點：health check（無論名稱）→ 定義＝消費 install.py verify＋check；`deploy/` plist 源收編 `--surface monitor`。
- 成功標準：對帳 receipt（已落地 vs 期望 delta 清單）；TC-7 綠。

### 核心實作要點
- 對帳：列既有 monitor 腿（muse approve）vs 期望（muse＋Q5 drift＋CC/ZCode/codex 註冊在場）delta；缺腿補齊（複用 S3/S4 函式——import 或 subprocess，零重寫）；monitor 若改名/吸收，rg 殘留掃描收尾。
- 輸出 log 與 hook log 同域；任一 FAIL → 非零 exit＋告警行（Q8 形態）。
- plist 源歸 `deploy/`（版控）；installer `--surface monitor` 裝載（cp 至 `~/Library/LaunchAgents/`＋`launchctl load`——machine-local 副本不入版控）；`--uninstall --surface monitor`＝unload＋移除本地副本。

### Pseudo Code
```
main():
    v = run(["uv", "run", "python", "governance/install.py", "--verify"])   # F-4：uv 避免 3.9 地板守衛誤觸
    c = run(["uv", "run", "python", "governance/install.py", "--check"])
    append_log(results); alert(Q8_form)
    exit(0 if v.ok and c.ok else 1)   # fail-loud：查不到＝告警非靜默綠
```

### 驗證策略
- **AC-5.1（Existence）**：對帳 receipt 落 `references/`（delta 清單＋補腿紀錄）；五面 health 腿清單 vs manifest probes 對帳表。
- **AC-5.2（Behavior positive）**：實跑 health check 於現況機器 → exit 0＋log 一筆（延續已落地 PASS 事實，擴面後複驗）。
- **AC-5.3（Behavior negative，TC-7）**：mock 漂移（同 AC-4.2 手法）→ 非零 exit＋告警行。
- **AC-5.4（排程實跑）**：`--surface monitor` 收編後 `launchctl start` 觸發 → log 出現五面執行紀錄——**斷言：log 行證明五面腿實際執行（出現 surface 名/探針輸出），非版本守衛拒絕訊息**。
- **AC-5.5（殘留掃描）**：monitor 吸收/改名後 `rg -l "muse_approve_monitor" scripts/ deploy/ AGENTS.md skills/ governance/` 零命中（或僅刻意保留的歷史指針，明列）。
- 已知未覆蓋：launchd 自身故障（面外）。

---

## S6｜bootstrap 穩定 CLI 契約（AIR-110 消費介面）

### Context
- 裁決 (b)（user 0917）：AIR-110（全新機器 bootstrap）呼叫本套件子安裝器、依賴**穩定 CLI 契約**、110 卡加 blocked-by——本段定義該契約並落機器可讀投影。
- UC 引用：實作「bootstrap 穩定 CLI 契約（AIR-110 消費）」。
- 依賴：S2 CLI 全形態（六 surface＋四 flag）定案；P0-7（deploy_agents 介面穩定）。
- 語義約束：契約一旦 110 開工消費即凍結為 **public contract**——後續改動走 semver（manifest `[package]` version bump 單一源＋變更理由記卡 notes）；README 只寫**當前契約態**，禁 Changelog 節（instruction 寫作禁令）；禁 silent breaking。
- 基礎設施盤點：`manifest.toml [bootstrap_cli]` 節（S1 已建骨架）；`hooks/MULTI-MACHINE.md`（既有手動多機文檔——收尾改指套件）。
- 依賴錨點：`[bootstrap_cli]` → 定義本段；消費＝AIR-110 bootstrap 執行器＋README 契約節。
- 成功標準：契約文件化＋新機器逐面檢查清單（bootstrap AC 形態）凍結。

### 核心實作要點
- **穩定契約**（凍結值）：
  - 命令面：`uv run python governance/install.py --surface {rules,skills,hooks,agents,memory,monitor,all} [--dry-run] [--uninstall] [--check] [--verify]`
  - 退出碼：0＝成功/綠；1＝drift/verify FAIL；2＝環境守衛（Python 地板/工具缺席）；3＝子命令未實裝；其他非零＝執行錯誤（journal 有線索）
  - 前提宣告：uv 在場、repo 在本機路徑（bootstrap 先決條件，110 負責驗）
- `manifest.toml [bootstrap_cli]`：上述契約的機器可讀投影（surfaces/flags/exit codes）——110 可解析校驗而非 regex stdout。
- README「bootstrap 節」：新機器逐面檢查清單——① uv/repo 前提 ② `--surface all --dry-run` 計畫可讀 ③ `--surface all` 安裝（.bak 生成）④ 手動 approve 步驟（CC `/hooks`、codex trust、ZCode 重開 session）⑤ `--verify`（含 codex 層一 discovery）⑥ `--check` 五面綠 ⑦ monitor `launchctl` 觸發一輪。每項帶命令＋預期。**「全綠」定義（F-1）**：逐面 PASS＝manifest 七面（五 surface 中 rules/agents/memory 各含 symlink/拓撲腿）；hooksPath 由 bootstrap 清單獨立項驗（`git config core.hooksPath` 輸出 `.githooks`）。
- 110 卡對齊：收尾時於 air-110 卡 `--append-notes` 記「消費 `governance/install.py` 契約（指針 README bootstrap 節）＋blocked-by 依賴成立」（AC-6.4）。

### 驗證策略（bootstrap 場景 AC＝逐面檢查清單形態）
- **AC-6.1（Existence）**：`rg -n "bootstrap_cli" governance/manifest.toml` 命中且含 surfaces/flags/exit-code 三類鍵；README bootstrap 節七項清單在場（`rg -c "dry-run|approve|--verify|--check|launchctl" governance/README.md` ≥4）。
- **AC-6.2（Invocation 契約一致）**：`--help` 輸出 vs `[bootstrap_cli]` 投影逐項一致（單元測試：argv 面與 manifest 面對帳）；退出碼語義以 AC-2.x/AC-4.x 既有驗證覆蓋（0/1 實測；2/3 以 fixture/stub 觸發實測）。
- **AC-6.3（模擬 bootstrap）**：以暫存 HOME/config fixture 模擬「新機器」（空 live config）跑七項清單①-⑥ → 逐項 PASS（真 launchd ⑦ 於現況機觸發一輪代替——AC-5.4 共享 receipt）。
- **AC-6.4（110 對齊）**：air-110 卡 notes 含消費指針＋blocked-by 記錄（或 user 裁決時點的明示延後，理由記卡）。

---## 整合策略

- 執行序：**Segment 0 → S1 → S2 → S3 ∥ S4 → S5 → S6**。S3/S4 平行可（同消費 S2 骨架、不同函式）；S5 複用兩者；S6 契約凍環 last（CLI 全形態定案後）。S5 對帳部分可與 S3/S4 平行（已落地事實 vs 期望態比對不依賴新代碼）。
- 整合點：S4 `--check` 與 S3 `--verify` 由 S5 一次消費；`[bootstrap_cli]` 由 S6 凍結；`/sync-sources` 家族語義——收尾評估 `--check` 是否掛入既有新鮮度檢查（掛法＝執行其一即可，文件指針）。
- closure 三層閘自我消費：S3-S6 AC 均帶 Existence/Invocation/Behavior（含 negative）三層＋AC-2.6/AC-4.3-4.5 failure-path；actual-runtime 面一致標記「未測——AIR-100 deferred 總驗卡承接」（codex host-level 層三除外——本 EP 做）。
- TC 對帳：TC-1/2/3/5/8/11/12/13/14→AC-2.x；TC-4/10→AC-4.x；TC-6/9→AC-3.x；TC-7→AC-5.x；bootstrap 契約→AC-6.x。

## 明列不做（範圍柵欄＋相鄰卡對照）

| 卡 | 關係 | 邊界 |
|---|---|---|
| AIR-110（bootstrap，To Do） | 下游消費者（裁決 b：110 呼叫本套件＋blocked-by） | 本 EP 定 CLI 契約（S6）；bootstrap 執行器、新機器先決（uv/repo 取得）歸 110；110 收尾對齊（AC-6.4） |
| AIR-113（skills fleet，Done） | 上游已完成 | 本 EP 不動 skills fleet 內容；只管分發 symlink 面；其 cross-ref「ZCode plugin 打包 skills 分發」未來另卡（本 EP skills 面＝symlink 建法，非 plugin 打包） |
| AIR-115（closure 三層閘，Done） | 只消費 | 不修改 `skills/acceptance-evidence/SKILL.md`；AC 全帶三層閘形態 |
| AIR-117（post-build memory 收尾腿，Done） | 零重疊 | 不觸 post-build skill 與池蒸餾程序 |
| AIR-100（Done） | 上游 | 政策面（D1-D5／防線四態）不重辯；行為本體零改動；deferred 總驗卡分界維持（codex host-level 除外，見 S3） |

- 不做：`deploy_agents.py`／`sync_agents.py` 本體修改（wrap 只透傳）；muse plugin 功能本體（divert+deny）；rules bundle 內容治理（bundle 線歸 `rules/AGENTS.md` 部署紀律）；pool 存量再處置（AIR-100 已清）；teardown prevention（機制不可能已裁決）；ZCode 缺席事件（FileChanged/SessionEnd）修補（harness 限制，文件化）；installer 代寫任何 trust／approve（red line）；skills ZCode plugin 打包（AIR-113 另卡方向）。

## 回復方式（rollback）

- 全包：`install.py --uninstall --surface all`（AC-2.5 對稱驗證，含 monitor unload）。`.bak-*` 備份在場可手工回貼；plan journal 支援中途 kill 後精確回滾。
- 逐段：S1 目錄整刪即回復（live config 未動）；S2-S4 任一失敗＝`--uninstall` 拆接線，scripts 留 repo dead-but-harmless；S5＝unload＋刪本地 plist 副本（若吸收改名，恢復原名）；S6＝契約節文件回退（無 machine-local 態）。
- rules/agents 面：uninstall 不反部署——bundle 回退走 `rules/AGENTS.md` 部署紀律、registry 走 `sync_agents.py` 自身。
- codex `[hooks.state]` orphan 條目：leave-and-report，隨 codex session 自然失效（README uninstall 節）；後續 group 前移的 trust 失效於 uninstall 輸出警告。

## 給 implement LLM 的接手入口

- 進場＝讀本 EP＋air-116 卡＋AIR-100 EP（政策與既有落地）＋`muse-plugins/memory-governance/README.md`＋`.agent-tmp/guides-refactoring/air116-discussions.md`（codex 8 條 findings 全文）。Segment 0 先跑（P0-1~P0-9），`references/probe-results.md` 落任務家後才凍結架構。
- **Red lines**：🚫 machine-local config（`~/.claude/settings.json` 真實目標、`~/.zcode/cli/config.json`、`~/.codex/config.toml`）寫入前必備份（僅變更者，copy2），ZCode 絕不整檔覆蓋，malformed 絕不覆寫；🚫 approve/trust 面（CC `/hooks`、codex `/hooks`＋startup review）＝user 手動——installer 只印步驟，禁代寫 `[hooks.state]`／禁模擬 approve／禁以 predicted positional key 當驗收契約；🚫 禁重寫/修改 `deploy_agents.py` 與 `sync_agents.py`（只 wrap 透傳）；🚫 禁 deploy 術語混淆——本套件動詞一律 install/uninstall，bundle 部署（deploy_agents）是另一條線；🚫 autonomous 禁 commit（收斂後交 `/commit` gate）；🚫 禁重辯 D1-D5／Q1-Q9 設計（Segment 0 探針可翻案者以探針證據為準，落地當日記理由於卡 notes）；🚫 禁碰 AIR-113/115/117 已結案範圍。
- 開工形態：AGENTS.md git 慣例（branch `air-116`）；控制面路徑（hooks/、governance/ 屬控制面）commit 走卡 branch，canonical main 由 pre-commit guard 擋；baseline 重刷（檔頭聲明）。
- Compact 壓力：每段自足；段落收斂即結算進度，接續走 `/at`＋EP 段落；blocked-on-user 點（TC-9 層二 approve）明確標注避免 autonomous 卡死。

## 收尾步驟

1. 卡回寫：AC#1/#2/#3 逐項 closure receipt 指針（`--check` 綠輸出、README 對應、AIR-110 對齊動作列）；**範圍對帳行**——擴範圍（五面 vs 卡 AC 原文 memory 域）以「AC#1 原文驗收＋五面超額交付」措辭記卡 notes（範圍裁決紀錄第 1 條）→ `backlog task edit air-116 --append-notes`；結案兩步照 kanban 慣例。
2. instruction 檔同步：`hooks/AGENTS.md`（zcode-registration 收編後指針改 `governance/registrations/zcode.json`）；`AGENTS.md` hooks 節補「跨 harness 治理安裝單一源＝`governance/`（install/check/uninstall，五面）」；`hooks/MULTI-MACHINE.md` 安裝節指 installer（AIR-110 對齊——僅指針，bootstrap 本體仍屬 110）；`skills/CLAUDE.md` 索引無涉及（無新 skill）。
3. AIR-110 對齊（AC-6.4）：於 air-110 卡 `--append-notes` 記「bootstrap 消費 `governance/install.py`（契約＝README bootstrap 節＋`[bootstrap_cli]`）＋blocked-by 依賴成立」。
4. `/audit-test`：對 install.py/health check 單元測試（冪等/原子/journal/negative cases/守衛）稽核，receipt 附完成報告。
5. memory 結案蒸餾：本弧教訓（套件形態 tradeoff、Segment 0 探針結果、approve 分欄實證、codex positional trust 語義、五面 wrap 契約）走 consolidation（D1 唯一入池權威）。

## amendment 附錄（TC 變更判決落點）

（空——凍結後 TC 變更須記 old/new oracle＋reason＋authority 於此）




