# EP：ai-rules → ai-guide 全表面改名落地

> **ep_type**: implementation
> **baseline**: `17a4fff`（`git rev-parse HEAD` 於 EP 建立當下；下游 post-build／code-review 任務弧審查範圍邊界）
> **docs mode**: 混合 docs-mode（主體 instruction／md 面＋少量 `.py` 字串常數、`config.json`、symlink／路徑操作；見 §0.4）
> **事實基礎**：`.agent-tmp/ai-guide-rename/investigation.md`（flash 主 session 全表面調查，2026-09-14）——本 EP 不重掃，逐段引用其 S 群組；行號／ref 數以 EP 執行時 `rg` 實測為準

## 0. 實作總覽

把 repo 稱謂 `ai-rules` 全表面改為 `ai-guide`（GitHub repo、目錄絕對路徑、家目錄形、裸名稱謂四形態；`ChiahungTai/ai-rules` → `ChiahungTai/ai-guide`，redirect 自動）。
觸發＝user 2026-09-14 拍板**立即執行**（codex 裁定零技術耦合；DRAFT-8 原「SouthChariot 落地同批」條件作廢，local decision）。

### 0.1 已決策（勿重辯）

- target＝**ai-guide**（DRAFT-8 三輪討論定案）；歷史文本不動 whitelist＝investigation.md S2（AIR-* 卡、`ai-analysis/**`、`backlog/completed|drafts`、`ref-docs/**`、ledger、`*.bak` 等）。
- judge 裁決補充（job-mu0zb7cu-orrtyh）：`~/.claude/file-history/**`＝工具自身歷史 snapshot——歷史 whitelist 永不動；zcode／CC artifacts 分類規則＝「runtime 會讀取、影響 agent 行為」→ 替換，「archive／transcript／backup／immutable」→ 歷史不動。
- 根 `AGENTS.md` 加一行新舊名對照（供 AI 檢索歷史文本解引用——DRAFT-8 驗收條件）。
- `agents/zcode/*.md`、`agents/claude/*.md` 生成檔**勿手改**（`scripts/sync_agents.py` 生成物；若命中舊名走生成器重跑，不直接編輯）。
- GitHub rename＝`gh repo rename`＋`git remote set-url`（黃線自主操作，一般段執行）。
- 記憶池全域掃替換＝user 明示授權（mosaic 三 WT 池／spine／zcode memories 11 專案 92 檔／CC 實體池／ai-rules 池）。
- 替換語義四形態：絕對路徑 `/Users/ctai/Github/ai-rules`→`/Users/ctai/Github/ai-guide`、家目錄形 `~/Github/ai-rules`→`~/Github/ai-guide`、裸名 `ai-rules`→`ai-guide`、檔名含舊名逐項改（僅 `.agents/memory/` 2 條目檔、`ai-guide.code-workspace`）。

### 0.2 全域紅線（所有段落適用，違反＝廢工單）

- **全程禁 `git commit`／禁 `git push`**（deep-work autonomous；commit consent 在 user——變更留 working tree）。
- **禁動 backlog 卡狀態**（DRAFT-8／AIR-94 由 caller 持有；本 EP 不建卡不結卡）。
- **目錄 `mv`＝最終段（段 8，S10），flash 主 session 親執行**；任何 bridge 委派段落（muse／codex）**禁碰 workspace 路徑**（runtime cwd 失效＝廢工單）。
- S2 whitelist 檔**禁動**；`MEMORY.md`／`_inventory.md` generator 投影**禁手寫**（改條目後跑生成器重投影）。

### 0.3 執行主體圖例（每段 Context 首行標註）

- `[flash 主 session]`＝in-harness 親執行（含全部 workspace／home 檔寫入；bridge 禁碰）。
- `[muse post-build]`＝收尾驗證鏈（只讀驗證＋機械重跑，不寫 workspace）。
- `[codex review]`＝code-review→judge-review（只讀審查，不寫 workspace）。

### 0.4 docs mode 聲明（混合形態）

- product scope 主體為 `.md`（instruction／skills／rules／AGENTS.md 家族——行為控制面，改後 AI 行為不同，走完整審查鏈）。
- 非 `.md` 例外（逐項列舉，無其他）：`pyproject.toml`（name 常數）、`hooks/zcode_agent_background_gate.py`（字串常數 1）、`scripts/deploy_agents.py`（header 字串＋docstring）、`scripts/check_report_shells.py`、`tests/*.py`（僅字串期望值）、`~/.zcode/cli/config.json`（hook 絕對路徑）、9 條 symlink、`*.code-workspace`。
- Pseudo Code 裁剪→各段以「修改要點」替代；驗證策略＝`rg` 殘留掃描＋`pytest` baseline＋`deploy_agents.py --dry-run`，非新功能 TDD。
- EP Review 維度改為「文檔一致性＋設計合理性＋引用 drift＋漏改」。

## 1. UC 盤點

### Backlog 關聯

- DRAFT-8（`backlog/drafts/draft-8 - ai-rules-→-ai-guide-改名…md`）——決策留檔（2026-09-14 觸發改寫註記已加；歷史描述段不動）。
- AIR-94（`backlog/tasks/air-94 - ai-rules→ai-guide-改名遷移…md`）——落地追蹤卡（caller 所建）。
- 自動建卡結果：本 EP 不建卡（紅線禁動 backlog；追蹤卡已存在，零新增正當）。

### SYSTEM-MAP 影響

- 無 SYSTEM-MAP.md（repo 根不存在）——建議後續建立；本 EP 無對應功能可掛，記「無」。

### 掃描範圍

- instruction 面：根 `AGENTS.md`、`rules/AGENTS.md`、`skills/CLAUDE.md`（工作流索引 description 同步檢查）、受影響 skills（§2 受影響 rules/skills 清單）。
- backlog：`backlog task list --plain`（DRAFT-8＋AIR-94 已確認在場，EP 執行時重驗）。
- 事實源：`.agent-tmp/ai-guide-rename/investigation.md`（S1–S10；免重掃，執行時 `rg` 覆核行號）。

### 同主題 memory 條目（結案蒸餾範圍）

- `ai-rules-dual-role-mosaic-shared.md`——檔名＋內容含舊名（S1 改名對象，段 1 執行）。
- `feedback_ai-rules-no-backward-compat.md`——同上。
- DRAFT-8 改名決策（draft 檔，非池條目；結案時判讀是否蒸餾終態 fact）。
- 池內 `ai-guide` 零命中（新名尚未入池，`rg -li "ai-guide" .agents/memory/` 空）。

### 既有 UC 狀態

元專案形態：本 repo 無 library Capabilities 表格（instruction 專案，非功能模組）——Capabilities 表格正當跳過（docs mode 對照表「元專案無 Capabilities 表格」）。
以「受影響 rules/skills 清單」代 UC 盤點本體：

| 能力／載體 | 狀態 | 來源 | 影響 | 說明 |
|---|---|---|---|---|
| 根 AGENTS.md＋CLAUDE.md 導航 | 更新 | investigation S1 | 改名替換＋新舊名對照行新增 | 消費端入口，DRAFT-8 驗收條件 |
| rules/AGENTS.md（部署紀律） | 更新 | investigation S1 | 4 refs 替換 | 部署源頭 |
| skills（corrections-weekly／sync-sources／standup／memory-audit／daily-maintain／cr-query／post-build／instruction-init／_common/work-order） | 更新 | investigation S1 | 路徑＋稱謂替換 | 方法論載體，行為控制面 |
| scripts/deploy_agents.py＋home 部署面 | 更新 | investigation S1／S3 | header 字串＋重跑部署自癒 | 三 bundle 源頭 |
| hooks（registration 範本＋background gate＋rollback 文檔） | 更新 | investigation S1 | 絕對路徑＋字串常數 | S5 消費端 |
| tests（memory_lifecycle／check_report_shells） | 更新 | investigation S1 | 字串期望值，改後跑 baseline | 驗收錨點 |
| 記憶池（repo 池＋mosaic 三 WT＋spine＋zcode memories＋CC 實體池） | 更新 | investigation S6 | user 明示授權全域掃替換 | 段 6 |
| 跨 repo AGENTS.md 活引用 | 更新 | investigation S8 | 6 repo 活表面 | 段 3 |

### 新增 UC

無（改名零新能力；📋 空表正當——純改名變更）。

## 2. Scenario Matrix（文檔語境：觸發／預期行為＝`rg` 命中／0 殘留，非程式執行結果）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|---|---|---|---|---|
| SM-1 | 全表面改名完成自查 | 執行者跑 `rg "ai-rules"`（migration 前後各一次） | 逐項分類（active 必修／歷史 whitelist／generated 可忽略＋理由）——**所有殘留必須有分類，不允許未知殘留**；active 類零殘留（S2 whitelist 除外；機械清單＝S1／S3／S4／S5／S8） | pre/post scan 對照＋分類併入完成報告（judge F3-01 縮小版，非長期 manifest） | 根 AGENTS.md 導航 |
| SM-2 | 部署產物自癒 | `uv run python scripts/deploy_agents.py --dry-run` | 綠＋三 bundle 無 ai-rules | dry-run 輸出 | 部署面 |
| SM-3 | symlink 指向新路徑 | `readlink` 9 條 | 全解析到 `/Users/ctai/Github/ai-guide/*` | readlink 輸出 9 行 | hooks |
| SM-4 | zcode config 手改失手 | Edit `config.json` 後 | `python3 -m json.tool` 合法＋7 hook 路徑檔存在 | json.tool exit 0 | hooks |
| SM-5 | 記憶投影一致 | 條目替換後跑生成器 | `MEMORY.md`／`_inventory.md` 重投影綠，無手寫 | generator 輸出 | 記憶池 |
| SM-6 | 跨 repo 誤傷他人變更 | 改前 `git -C <repo> status` 非空 | 命中檔跳過並記錄，不順手修 | 跳過清單 | 跨 repo 引用 |
| SM-7 | mv 後 session 失效 | `mv` 執行瞬間 | 完成報告預寫，必要時 user 於新路徑重開 session | 預寫報告在場 | — |
| SM-8 | 舊名可檢索解引用 | 根 AGENTS.md 對照行 | 新舊名對照行在場，歷史文本讀到可解 | `rg "ai-guide" AGENTS.md` 命中 | 根導航 |
| SM-9 | 測試錨點未漂 | `uv run pytest tests/test_memory_lifecycle.py tests/test_check_report_shells.py` | baseline 綠 | pytest exit 0 | tests |

## 3. 段落劃分原則

依 investigation.md S 群組切分（S1 repo 內容→S8 跨 repo→S9 GitHub→S5 home config→S6 記憶池→驗證閘→S10 最終段），依賴序執行：
段 1（S1）→ 段 2（S3）→ 段 3（S8）→ 段 4（S9）→ 段 5（S5-pre）→ 段 6（S6＋S7-pre）→ 段 7（pre-mv 驗證閘）→ 段 8（S10＋S4＋S7-post＋S5-post）→ 段 9（收尾鏈）。
S2 whitelist 為全段全域約束（§0.2＋各段「不動清單」），不單獨立段。S4／S7-post／S5-post 必須 post-mv（舊絕對路徑 mv 前有效，提前改＝自斷）。

## 段落 0：全域研究（已完成，前置引用）

- 本 EP 全域研究＝`.agent-tmp/ai-guide-rename/investigation.md`（flash 主 session，2026-09-14；S1–S10 活表面枚舉＋驗收 8 條＋風險 4 項）——EP 段落不再 spawn 研究 agent（工單明示免重掃）。
- 可複用基礎設施：`scripts/deploy_agents.py`（部署自癒入口）、`scripts/reconcile_memory_pool.py`（S6 對帳掛點，consolidation 開頭／memory-audit 機械層）、memory 生成器（`_inventory.md`／`MEMORY.md` 重投影）、`gh`（已登入、repo scope ✓）。
- 風險假設（等級＋消化段）：hooks 斷裂窗口（中，段 8 秒級重指向）／`config.json` 手改語法風險（中，段 5 `.bak`＋機械驗證）／外部 repo 他人未提交變更（中，段 3 改前對帳跳過）／mv 後本 session workspace 失效（高，段 8 報告預寫）。
- negative 宣稱：無「零消費者／可刪」類 verdict（純改名，S2 不動面以 whitelist 枚舉＋`rg` 覆核守衛，非 CR 查詢；code-reality 非必要，禁寫入面）。
- 依賴錨點（定義端／消費端）：`HEADER` 字串 → 定義 `scripts/deploy_agents.py:175`／消費 `~/.zcode/AGENTS.md` 等三 bundle＋`rules/AGENTS.md`；hook 路徑 → 定義 repo `hooks/*`／消費 `~/.zcode/cli/config.json`（line 68/81/89/102/116/124/139，執行時 `rg` 覆核）。
- 語義約束（全段共享）：四形態替換語義（§0.1）；S2 whitelist（§0.2）；bridge 禁碰 workspace（§0.2）。

## 段 1：repo 內活表面替換（S1）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（workspace 寫入；bridge 禁碰）。
- UC 引用：更新「根 AGENTS.md＋CLAUDE.md 導航」「rules／skills 方法論載體」「tests 驗收錨點」。
- 需求邊界：改 S1 活表面；S2 whitelist 禁動（不動清單見下）；`agents/zcode/*.md`、`agents/claude/*.md` 生成檔禁手改（命中舊名→跑 `scripts/sync_agents.py` 重生成，不直接編輯）。
- 依賴關係：本段為 S3（段 2）前置（部署源頭先改）；S4／S5／S7-post 須等段 8 mv。
- 基礎設施盤點：Edit／Write（逐檔精準 Edit；先 Read）；`rg` 覆核行號（investigation ref 數為調查時快照，執行時以實測為準）。
- 成功標準：S1 清單逐檔替換完成，`rg "ai-rules"` 殘留僅 S2 whitelist。

### 修改要點（Pseudo Code 裁剪替代）

1. `pyproject.toml`：`name = "ai-rules"` → `"ai-guide"`。
2. `settings.json`（repo 根；`~/.claude/settings.json` symlink 源）：hooks 絕對路徑＋Read 權限行，全改 ai-guide（調查時 12 refs，EP 建立時實測 14——執行時 `rg` 為準）。
3. 根 `AGENTS.md`／`CLAUDE.md`：稱謂替換＋**新增一行新舊名對照**（DRAFT-8 驗收條件；措辭示例：`ai-guide（曾名 ai-rules；歷史文本中 ai-rules 即本專案）`）。
4. `hooks/zcode-registration.json`（7 refs）、`hooks/zcode_agent_background_gate.py`（字串常數 1）、`hooks/memory-hooks-rollback.md`（文檔 1）。
5. `scripts/deploy_agents.py`（line 175 header 字串＋docstring）、`scripts/check_report_shells.py`（3 refs）。
6. skills：corrections-weekly（6，4 路徑）／sync-sources（4）／standup（3，2 路徑）／memory-audit／daily-maintain／cr-query（各 3）／post-build／instruction-init／`_common/work-order.md`（各 1）＋其餘裸名稱謂（全 repo `rg` 為準）。
7. `rules/AGENTS.md`（4 refs）、`.claude/settings.local.json`（1）。
8. `tests/test_memory_lifecycle.py`（13）、`tests/test_check_report_shells.py`（5）——僅字串期望值。
9. repo 池 `.agents/memory/`（~25 檔內容＋2 條目檔改名：`ai-rules-dual-role-mosaic-shared.md`、`feedback_ai-rules-no-backward-compat.md`；改名用 `mv` 單檔操作，非目錄 mv 紅線範圍）→ 改後跑生成器重投影 `_inventory.md`（禁手寫）。
10. 不動清單（S2）：`ai-analysis/**`、`backlog/completed/**`、`backlog/tasks/**`、`backlog/drafts/**`（AIR-94／DRAFT-8 由 caller 持有）、`ref-docs/**`、`.agent-tmp/**`、`.review/**`、`.delegate-bridge/**`、`.muse-bridge/**`、`.tours/**`、`*.bak-*`、`.git/**`、`ai_rules.egg-info`、`.muse/hooks.json.bak-*`。

### 驗證策略

- `rg -n "ai-rules" --files-with-matches` 逐項歸類：命中僅 S2 whitelist（SM-1）。
- `rg -n "ai-guide" AGENTS.md` 對照行在場（SM-8）。
- `uv run pytest tests/test_memory_lifecycle.py tests/test_check_report_shells.py` baseline 綠（SM-9；改字串期望值後跑）。

## 段 2：home 部署面重跑（S3）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（home 檔寫入；bridge 禁碰）。
- UC 引用：更新「scripts/deploy_agents.py＋home 部署面」。
- 需求邊界：只重跑部署，不手改產物；不動 `~/.config/muse/AGENTS.md.bak-spawn-rule`。
- 依賴關係：前置段 1（源頭先改）；`~/.claude/rules/`、`~/.claude/CLAUDE.md` 為 symlink 自動跟隨，免另改。
- 語義約束：與段 1 共享四形態語義。
- 成功標準：`--dry-run` 綠＋三 bundle 無舊名。

### 修改要點

1. 跑 `uv run python scripts/deploy_agents.py`（源頭＝段 1 改後 repo），再生 `~/.zcode/AGENTS.md`、`~/.codex/AGENTS.md`、`~/.config/muse/AGENTS.md`（舊 header 各 1 ref 自癒）。
2. `~/.claude/rules/`、`~/.claude/skills/`、`~/.claude/agents`、`~/.claude/CLAUDE.md`、`~/.claude/settings.json`、`~/.agents/commands`、`~/.agents/skills`、`~/.zcode/agents`、`~/.zcode/skills` 皆 symlink→repo（自動跟隨，驗證即可不改）。

### 驗證策略

- `uv run python scripts/deploy_agents.py --dry-run` exit 0（SM-2）。
- `rg "ai-rules" ~/.zcode/AGENTS.md ~/.codex/AGENTS.md ~/.config/muse/AGENTS.md` 零命中（SM-2）。
- 9 條 symlink `readlink` 仍解析到舊路徑（mv 前正確；post-mv 由段 8 重驗 SM-3）。

## 段 3：跨 repo 活引用（S8）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（他 repo working tree 寫入；bridge 禁碰 workspace 路徑）。
- UC 引用：更新「跨 repo AGENTS.md 活引用」。
- 需求邊界：判準「今天新 session 讀到會誤導」才改；各 repo 歷史（`ai-analysis/**`）、`.delegate-bridge/`／`.muse-bridge/` ledger、`muse-plugin-cc/dist/**`、delegate-bridge `00-tasks/**` 禁動。
- 依賴關係：可與段 1／2 並行（不同 working tree），但同 session 序列執行；改前逐 repo 對帳。
- 基礎設施盤點：`git -C <repo> status --porcelain`（改前）；Edit 逐檔。
- 成功標準：活表面替換完成，他人未提交變更檔零誤傷＋跳過清單記錄。

### 修改要點

1. 改前對帳：`git -C <repo> status --porcelain`（mosaic_alpha ×3 WT、ai-lifecycle、code-reality、southchariot、zcode-vscode、hermes-agent）——有他人未提交變更的檔跳過並記錄（SM-6）。
2. mosaic_alpha（×3 WT）：`AGENTS.md`、`CLAUDE.md`、`tests/AGENTS.md`、`tools/AGENTS.md`、`mosaic_alpha/broker_flow_analysis/AGENTS.md`、`deploy/README.md`、`.code-reality.toml`（offline_backtesting WT 2 註釋 refs）。
3. ai-lifecycle：`AGENTS.md`；code-reality：`AGENTS.md`、`README.md`；southchariot：`lifecycle/AGENTS.md`；zcode-vscode：`lifecycle/AGENTS.md`；hermes-agent：`ai-analysis/README.md`（nav 面）。
4. 四形態語義同 §0.1（跨 repo 多為絕對路徑＋裸名稱謂）。
5. **Dirty skip closure（judge F1-01 採納）**：每筆跳過記錄 `path／skip reason／required follow-up`（`.agent-tmp/ai-guide-rename/skip-list.md`，有 skip 才建）；migration 結束前每筆收斂為三態之一——「已處理／確認歷史不動／明確延期原因」——**禁存在未分類 skip entry**。

### 驗證策略

- 逐 repo：`rg -n "ai-rules" <活表面檔>` 零命中（歷史／ledger 除外；SM-1 跨 repo 腿）。
- 跳過清單（有他人變更而跳過者）列入段報告（SM-6）。
- skip-list 逐筆三態收斂確認（有 skip 時）；段結束時無未分類 entry（judge F1-01）。
- `git -C <repo> status --porcelain` 確認僅預期檔被改（禁 `git commit`，變更留各 repo working tree）。

## 段 4：GitHub＋遠端＋workspace 檔（S9）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（黃線自主操作；bridge 禁碰）。
- UC 引用：更新「GitHub repo 名＋遠端＋workspace 檔」。
- 需求邊界：AUTH 基礎＝user「改名改好」＋DRAFT-8 遷移清單 item 1；只做 rename＋remote＋workspace 檔，不碰 GitHub 其他設定。
- 依賴關係：段 1–3 後（內容先就緒，招牌後換）；段 8 mv 前後皆可，建議段 8 緊前執行。
- 成功標準：`gh repo view ChiahungTai/ai-guide` 200＋`git ls-remote origin` 通＋workspace 檔名內容一致。

### 修改要點

1. `gh repo rename ai-guide -R ChiahungTai/ai-rules --yes`（redirect 自動）。
2. `git remote set-url origin git@github.com:ChiahungTai/ai-guide.git`。
3. `/Users/ctai/Github/ai-rules.code-workspace`：內容 `path` 改 ai-guide＋檔名改 `ai-guide.code-workspace`（`mv` 單檔操作）。

### 驗證策略

- `gh repo view ChiahungTai/ai-guide` exit 0（SM 驗收 7 腿）。
- `git ls-remote origin` 通（SM 驗收 7 腿）。
- `rg -n "ai-rules" /Users/ctai/Github/ai-guide.code-workspace` 零命中。

## 段 5：home 活 config（S5-pre：備份＋非路徑項）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（home config 寫入；bridge 禁碰）。
- UC 引用：更新「hooks 消費端 config」。
- 需求邊界：hook 絕對路徑 7 條**禁提前改**（mv 前改＝自斷；留段 8 S5-post）；本段只做備份＋可先行項。
- 依賴關係：備份越早越好（段 1 後即做）；S5-post 併入段 8。
- 成功標準：`.bak` 在場＋JSON 合法（改前基線）。

### 修改要點

1. `cp ~/.zcode/cli/config.json ~/.zcode/cli/config.json.bak-<date>`（先備份；S2 `*.bak-*` whitelist 精神：備份檔本身不動）。
2. `~/.claude/settings.json`＝repo 檔 symlink（段 1 改完自動生效，免另改——驗證 `readlink` 即可）。
3. `~/.config/muse/trust.json`：**禁提前改**（新路徑 mv 前不存在）→ 留段 8（改／加 ai-guide 路徑）。

### 驗證策略

- `ls ~/.zcode/cli/config.json.bak-*` 在場。
- `python3 -m json.tool ~/.zcode/cli/config.json` exit 0（改前基線；SM-4）。
- `rg -n "ai-rules" ~/.zcode/cli/config.json` 仍 7 命中（pre-mv 正確值，證明未提前改）。

## 段 6：記憶池內容替換（S6＋S7-pre）——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（repo 外記憶池寫入係 user 明示授權；bridge 禁碰 workspace 路徑——記憶池段仍由 flash 親執行，不委派）。
- UC 引用：更新「記憶池」。
- 需求邊界：只替內容＋2 條目檔改名；`MEMORY.md`／`_inventory.md` 禁手寫（生成器重投影）；CC／zcode 舊 session transcripts 內舊路徑＝歷史不動；S7 新鍵建鏈禁提前（留段 8）。
- 依賴關係：段 1 repo 池可同批；外部池隨時可做（與 mv 無序約束，唯 S7-post 除外）。
- 基礎設施盤點：`scripts/reconcile_memory_pool.py`（對帳掛點）；各池生成器（CC／zcode 面）。
- 成功標準：全域池 `rg` 零殘留＋重投影綠。

### 修改要點

1. ai-rules 池：段 1 §9 已做（內容＋2 檔名＋重投影）——本段覆核。
2. mosaic 三 WT 池（實體副本）：頭部大戶先改（`project-memory-audit-advisory-only.md` 26、`reference-archify-illustrate-html.md` 13、`project-backlog-md-integration-arc.md` 12、`reference-zcode-platform.md` 11、`reference-zcode-memory-generator.md` 7、`project-muse-code-review-adoption.md` 7、`_audit-state.md` 6…三池同構；ref 數執行時 `rg` 覆核）。
3. spine `~/.agents/memory-spine/`：`index.md`（2）、`reference_model-runtime-entitlements.md`（2）。
4. zcode memories 全專案（11 專案 92 檔：code-reality 32、delegate-bridge 16、ai-lifecycle 15、nautilus_trader 9、zcode-vscode 4、muse-plugin-cc 4、machine-learning-for-trading 3、codetour 3、shioaji-pro-app 2、codex-chatgpt-web 2、codebase-memory-mcp 2）。
   - **pre/post scan 基準（judge F1-02 終局：scan＋diff 即可，不建 manifest 體系）**：起手前已凍結 `rg -l` 基準（`.agent-tmp/ai-guide-rename/manifests/zcode-memories-frozen.txt` 等）；替換後 re-scan diff，確認逐筆處置。
5. CC 實體池 `~/.claude/projects/-Users-ctai-Github-code-review-graph/memory/`（1 檔）。
6. S7-pre：記下新鍵 `ai-guide-91ff86777c287082`（sha256 絕對路徑前 16 碼；建鏈留段 8）。舊鍵目錄保留（CC 舊鍵含歷 session transcripts；zcode 舊鍵僅 memory symlink）。

### 驗證策略

- 逐池 `rg -l "ai-rules" <池>` 零命中（transcripts 除外；SM 驗收 5 腿）。
- 生成器重投影綠（`MEMORY.md`／`_inventory.md` 無手寫 diff；SM-5）。
- `uv run python scripts/reconcile_memory_pool.py /Users/ctai/Github/ai-rules`（pre-mv 路徑；對帳 exit 0＝clean）。

## 段 7：pre-mv 驗證閘——[flash 主 session]

### Context

- 執行主體：**flash 主 session**（段 8 mv 放行門；不通過禁進段 8）。
- UC 引用：全段覆核（①LLM 執行鏈自判層）。
- 需求邊界：只驗證不修改；任一紅燈停下修，不帶病進 mv。
- 依賴關係：段 1–6 全綠為前置。
- 成功標準：investigation 驗收 1／2／7-pre／8 全綠。

### 修改要點

無（純驗證段）。

### 驗證策略

- `rg -n "ai-rules" --files-with-matches`：逐項分類（active／歷史 whitelist／generated＋理由），active 類零殘留、分類結果併入完成報告（驗收 1 pre-mv 腿；SM-1；judge F3-01 縮小版）。
- `uv run python scripts/deploy_agents.py --dry-run` 綠（驗收 2；SM-2）。
- `uv run pytest tests/test_memory_lifecycle.py tests/test_check_report_shells.py` 綠（驗收 8；SM-9）。
- `rg -n "ai-guide" AGENTS.md` 對照行在場（驗收 7-doc 腿；SM-8）。
- `git status --porcelain` 確認變更面符合預期（無 S2／backlog 意外寫入；禁 `git commit`）。

## 段 8：目錄 mv＋斷裂面重接（S10＋S4＋S7-post＋S5-post）——[flash 主 session 親執行]

### Context

- 執行主體：**flash 主 session 親執行**（全鏈唯一 mv 段；bridge **禁碰** workspace 路徑——muse／codex 任何段落禁動目錄／symlink／home config，違者廢工單）。
- UC 引用：全鏈收口（hooks 重連＋記憶鍵遷移＋config 切換）。
- 需求邊界：mv→重指向→建鏈→config→驗證，一氣呵成（hooks 斷裂窗口秒級，可接受）；完成報告**預寫**（本 session workspace 於 mv 後失效，必要時 user 於新路徑重開 session）。
- 依賴關係：段 7 放行門綠為前置；段 9 收尾鏈在新路徑（或新 session）執行。
- 語義約束：舊絕對路徑自本段起失效；所有 post-mv 命令用新路徑。
- 成功標準：驗收 3／4／5-post／6／7 全綠＋完成報告已交付。

### 修改要點

1. `mv /Users/ctai/Github/ai-rules /Users/ctai/Github/ai-guide`（flash 親執行）。
2. S4：9 條 symlink 一次重指向新 repo（`~/.claude/CLAUDE.md`→`<新repo>/ai-development-guide.md`、`~/.claude/agents`、`~/.claude/rules`、`~/.claude/skills`、`~/.claude/settings.json`、`~/.agents/commands`、`~/.agents/skills`、`~/.zcode/agents`、`~/.zcode/skills`）。
3. S7-post：建鏈 `~/.claude/projects/-Users-ctai-Github-ai-guide/memory` → `<新repo>/.agents/memory`；`~/.zcode/cli/memories/projects/ai-guide-91ff86777c287082/memory` → `~/.claude/projects/-Users-ctai-Github-ai-guide/memory`。舊鍵目錄保留。
4. S5-post：`~/.zcode/cli/config.json` 7 條 hook 路徑改 ai-guide（`.bak` 在場才動）→ `python3 -m json.tool` 驗證；`~/.config/muse/trust.json` 改／加 ai-guide 路徑。
5. post-mv 驗證（新路徑）：SM-3（9 條 `readlink` 全到 ai-guide）／SM-4（json 合法＋7 路徑檔存在）／驗收 6（zcode→CC→pool 鏈解析通）。

### 驗證策略

- `readlink ~/.claude/CLAUDE.md ~/.claude/agents ~/.claude/rules ~/.claude/skills ~/.claude/settings.json ~/.agents/commands ~/.agents/skills ~/.zcode/agents ~/.zcode/skills`：9 行全含 `/Users/ctai/Github/ai-guide/`（驗收 3；SM-3）。
- `python3 -m json.tool ~/.zcode/cli/config.json` exit 0＋7 hook 路徑 `test -f` 全過（驗收 4；SM-4）。
- 新鍵鏈：`readlink` 兩跳皆通＋目標 `test -d`（驗收 6）。
- `rg -n "ai-rules" <新repo> --files-with-matches`：殘留僅 S2 whitelist（驗收 1 post-mv 腿）。
- `cd /Users/ctai/Github/ai-guide && uv run python scripts/deploy_agents.py --dry-run` 綠（新路徑部署面）。

## 段 9：收尾鏈（post-build→review→judge）——[muse post-build]＋[codex review]

### Context

- 執行主體：**muse**（post-build 收尾鏈編排：只讀驗證＋機械重跑）→ **codex**（code-review→judge-review 獨立第二意見）；兩者皆**禁碰** workspace 路徑（審查只讀；修正回 flash 主 session 落地）。
- UC 引用：收尾三項（Capabilities／SYSTEM-MAP／instruction 更新）元專案跳過——改為「受影響命令／rules 行為已反映＋`skills/CLAUDE.md` 工作流索引 description 同步」檢查（docs mode 對照表）。
- 需求邊界：**全程禁 `git commit`**（commit consent 在 user；deep-work autonomous 紅線——收尾段不得排任何 commit 動作；kanban 結案兩步不執行，AIR-94 保持原狀態交 user）。
- 依賴關係：段 8 完成＋完成報告已交付為前置（post-mv 路徑或新 session）。
- 成功標準：post-build 綠＋judge 無開放 blocking finding（⚠️ 需確認項彙整交 user，不阻塞）。

### 修改要點

1. muse post-build：`uv run pytest` 重跑＋`rg` 殘留覆核＋`deploy_agents.py --dry-run`＋`/consistency ai-analysis/_tasks/09-14-ai-guide-rename/ep.md`（EP 自洽 gate）。
2. codex code-review（docs-mode 軸：文檔一致性＋引用 drift＋漏改）→ judge-review 裁決；findings 回 flash 落地修正（上限參 post-build 修正迴圈）。
3. `skills/CLAUDE.md` description 同步檢查（改名影響工作流索引時）。

### 驗證策略

- `uv run pytest tests/test_memory_lifecycle.py tests/test_check_report_shells.py` 綠（muse 重跑腿）。
- review findings 清零或僅剩 user 待確認項（codex judge 腿）。
- `git status --porcelain` 最終舉證：變更面＝預期（commit 零次；`git log --oneline -1` 仍 `17a4fff`）。

## 4. 整合策略

- baseline：`17a4fff`（EP 建立當下 `git rev-parse HEAD`；caller 凍結一致）。
- 並行改動：working tree 先前已有 caller 產物（`.agent-tmp/ai-guide-rename/` 調查＋本工單、`backlog/drafts/draft-8` 註記、`backlog/tasks/air-94` 新卡）——皆非本 EP 執行面，段 1–9 禁動；`git status --porcelain` 對帳以此為基線。
- 執行序：段 1→2→3→4→5→6→7（mv 放行門）→8（mv＋重接）→9（收尾鏈）；段 3 與段 1／2 可交錯（不同 tree），同 session 序列。
- 跨 session 交接：段 8 後 workspace 失效預案（完成報告預寫＋新路徑重開）；post-build／review 以本 EP＋`baseline: 17a4fff` 跨 session，不重新推導。
- family／effort 語境（`skills/model-routing/SKILL.md` External-runtime family 表）：實作段 flash in-harness；post-build＝muse（implement／review profile，`muse-spark-1.3`／xhigh 由承接側解析）；review＝codex（ad-hoc 顯式指定；大工單禁派——本 EP 為規劃消費 docs，符合 review 甜蜜點）。

## 5. 收尾步驟（後續鏈執行，非本 EP 寫入）

1. 受影響命令／rules 行為反映確認＋`skills/CLAUDE.md` 索引同步（段 9 §3；元專案 Capabilities／kanban 跳過——理由：無 library Capabilities 表格＋紅線禁動卡）。
2. SYSTEM-MAP：不存在，跳過（建議後續建立）。
3. `/audit-test`：無新增測試（字串期望值改動沿用既有測試），跳過並記錄理由。
4. **禁 `git commit`／禁 `git push`**——commit consent 在 user；完成報告列 `git status --porcelain`＋`git log --oneline -1` 舉證零 commit。
5. EP 歸檔：本 EP 留任務家（歷史不動 whitelist 精神；後續 session 讀到舊名可經根 AGENTS.md 對照行解引用）。
