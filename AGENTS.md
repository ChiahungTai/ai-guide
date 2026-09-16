# ai-guide 專案

> **改名對照**：ai-guide（曾名 ai-rules；歷史文本〔AIR-\* 卡／ai-analysis／drafts〕中的 ai-rules 即本專案，git 歷史可考；舊路徑 `/Users/ctai/Github/ai-rules`、舊遠端 `ChiahungTai/ai-rules` 同指本專案）。
> 卡 id 前綴 `AIR` 為歷史沿革 namespace——rename 後 `task_prefix: air` 不變、新卡續編 AIR-N，branch 慣例 `air-<N>` 同（AIR 已不代表 ai-rules；codex 裁決 2026-09-14：A 選項保留單一 namespace）。

> 本檔是 **ai-guide 專案指令**（開本 repo 時讀）。**全域開發指南**（演化/驗證/UC-Driven/架構/量化鐵律）是另一份獨立檔 `ai-development-guide.md`，經各 harness 全域位置載入——非 Claude 端（ZCode/Codex/Muse，deploy targets 單一源＝`scripts/deploy_agents.py`）→ guide bundle；Claude 端：`~/.claude/CLAUDE.md` symlink → guide + `~/.claude/rules/` auto-load（不走 bundle）——非本檔。

本專案管理 AI coding agent 的 rules、skills、commands（跨 harness：Claude Code / ZCode / Codex / Muse）。

所有 rules/skills/commands 的**文件本身供 AI 消費**（AI 讀 `.md` 來執行命令）—— 寫作、審查、修改以「AI 能否正確執行」為準。readability 對 AI = 結構可機械解析、指令可遵行，**不是人類閱讀流暢度**；禁止用「人類讀者需要前置框架/會困惑」這類人類認知論證當審查發現。無需人類式證據出處、版本履歷、精確專案數字（詳見 instruction-writing skill、`rules/instruction-writing.md`）。

> **文件受眾 ≠ 命令受眾**：文件一律給 AI 讀（執行用）；但命令的**產出**服務不同對象 —— LLM 執行鏈（機器消費）或人類 viewport（人消費）。命令的設計、審查、討論一律以「產出受眾」為頂層脊柱（見下）。

## 消費端 context（know your customer）

> ai-guide 的 rules/skills/commands 部署到每個消費端專案、直接塑造其 session 行為——**設計決策 downstream 影響所有消費端**。設計/修改任何 command/skill/rule 前，先對照本段：它在消費端的真實工作情境下仍合理嗎？

**消費端畫像**：
- **solo developer + AI agent**（非團隊、無 CI）——一人與 AI 協作；沒有 code review 文化、沒有 CI 自動把關
- **工作單元 = 一 EP = 一 session**——一次 session 推進一個 Execution Plan；context 是稀缺資源
- **model 會退化**——長 session 後 LLM 行為變怪；消費端實務是「不硬撐：結算 EP 進度 → 開新 session 接續」（接續：`/at`、`/handoff`、EP 段落自足）
- **context 節奏**：`/compact` 分佈在 EP 各階段；command 必須在 compact 壓力下仍可接續
- **git 多軌**：多 worktree + 單一 trunk，feature 單向 rebase onto trunk（並行開發軌；軌名各專案自訂）
- **review 模式**：Writer/Reviewer 平行 session 分離（同 LLM 自審有 bias → 開新 session 審）

**設計含義**（設計 command/skill 時核對）：
- **自足**：段落自包含、進度可結算可接續（消費端會 compact、跨 session）
- **不依賴外部服務**：預設無 CI、無團隊 review——需人類判讀的走 viewport 命令（`/debrief`、`/illustrate`、`/smell-detector`），不假設 CI
- **git 認知**：涉及 git 的 command 尊重 worktree+trunk（不交互 rebase、trunk 永不被 rebase）
- **review 鏈**：review command 支援「產出 finding → 跨 session 貼回 → `/judge-review`」多 session 鏈
- **自主性**：自主 command（`/deep-work`、cron 排程）假設人類不在場——紅線/黃線分級 + 完成報告

## git 慣例（本 repo 卡 branch）

- **命名**：卡 branch＝`<線縮寫>-<卡號>`——線縮寫＝**worktree toplevel basename 縮寫**（線的身份是 WT 路徑，穩定；branch 開卡 branch 後就換了）。本 repo 單 WT（repo 根）→ `air-<N>`（`air-46`＝卡 AIR-46；與卡 id 前綴字面重合屬巧合非要求）；卡號＝Backlog.md id
- **生命**：開工（implement 階段 1 起手式 ⑤ 後——⑤ 定義＝[kanban](skills/kanban-board/SKILL.md) 起手式五步）自 main `git checkout -b air-<N>`；branch 已存在→先 `git log main..<branch>` 判本卡遺留再續用（非本卡殘留不續用）；建卡不開 branch；卡 branch 上 commits message 帶卡 id（`(air-46)` scope 或 `air-46: …` 前綴）
- **收尾**：/commit 確認通過後——`git checkout main && git merge --ff-only air-XX && git branch -d air-XX`（WT 回 main）；`--ff-only` 被拒＝main 已前進→先 `/rebase main` 再吸（mosaic：`/rebase <owning線>`，禁默認 main）；clean 紀律由 /commit gate 守（dirty checkout 不衝突會帶走，不是護欄）；trunk 永不被 rebase、永不 force（[rebase skill](skills/rebase/SKILL.md) 鐵律）
- **WT 形態過渡條款（09-16 AIR-72 起雙軌）**：卡可走 **persistent card WT**（control/execution plane 分離）——開工＝`scripts/wt-open.sh <卡id> --base main`（只接已存在 card，不代建卡不配 id；**base 顯式＝owning 線 ref，絕不取呼叫端 HEAD**；`--base` 無預設值，一律顯式傳 owning 線；機械建立 `<repo-basename>-<branch>` WT＋池/inbox symlink→primary canonical＋identity contract（`<wt>/.agent-tmp/wt-identity.json`）＋{toplevel,branch,card,baseline} 驗證），收尾＝`scripts/wt-close.sh --wt <path> --preflight` 全檢查零變更，trunk 收斂由 marshal 收線時在 user 授權下 full 執行（rebase/ff-only 規則同「收尾」條；免卡小修走 `--ephemeral <name>` fast-path）。**未走 wt-open 的卡照舊**：上兩條 checkout 模式仍是 runtime authority；同一卡禁混用兩形態（primary 已切卡 branch 又開同卡 persistent WT＝ownership 不唯一）。WT 形態下 board single-writer 生效——卡 metadata 只有 board-control 可寫、spawned worker 禁碰（單一源＝[kanban skill](skills/kanban-board/SKILL.md)「board single-writer」）；形態定案與 wt-open/close transaction 規格＝[blueprint workflow.md](ai-analysis/blueprint/workflow.md)
- **`/rebase all` 護欄**：all 之前 `git branch --list 'air-*'` 非空 → 先收卡，不跑 all（`*` 不可省）；user 紀律：all 只在所有卡收尾後下
- **軟條款**：忘記 checkout 直落 main＝軟失敗不回頭搬（message 已帶卡 id）；夜間 automation commits 落卡 branch 無害；拋棄（`branch -D`）需 user 明確確認；跨 session 遺留屬正常（接手者續用或判死吸收）
- **mosaic 變體**：多線形態（前綴＝WT toplevel basename 縮寫、owning 線由卡 labels 線 tag 判（v2→v2 線、warrants→warrant 線、其餘含無線 tag＝main）、線判定路徑查表、收尾 rebase base＝owning 線）定義源＝[09-08 卡 branch EP](ai-analysis/_tasks/done/09-08-card-branch-lifecycle/ep.md)——落地由 mosaic 側 MOS 卡承接

## 命令的受眾視角

> **核心心智模型**：commands 不是按生命週期階段（EP / code）分，是按**產出受眾**分。設計、審查、討論任何命令時，先問「這命令的產出給誰消費」。

### 受眾二分

| 軌道 | 消費者 | 產出形式 | 誰推動 |
|------|--------|---------|--------|
| **① LLM 執行鏈** | 機器自讀自判自修 | 工程化、self-contained（EP、findings、code） | AI 自主（人類開頭觸發） |
| **② 人類 viewport** | 人類用「大原則」判讀 | 意圖（行為 artifact + 認知誤差點）+ 結構（whole-picture 心智模型） | 人類切入（或 AI 產出、人類讀） |

兩軌道平行不交匯，服務不同讀者。`/ep-review`、`/code-review`、`/audit-test`、`/implement` 內部審查、`/judge-review` 屬軌道 ①；`/debrief`（改動理解）、`/illustrate`（結構 viewport）、`/smell-detector`（壞味道：zoom 放大鏡 / baseline 盤點）是軌道 ② 的命令。**一檔兩受眾必然產生 token 牆——單檔單受眾**（失敗實證：/human-review 三度重建又棄）。

### 原理：人補 LLM 的結構性 blind spot（direction >> quality）

人類 viewport 補的是 LLM 結構上做不到的兩件事 —— 都靠人的互補認知：

| LLM blind spot | 失敗 | 人類互補認知 | 命令 |
|----------------|------|-------------|------|
| 缺 whole picture → 重造既有 | 重造 enum / 模組 | 整體直覺（細節忘但感覺得到關係 / 重用） | `/illustrate`（結構 viewport） |
| 抓不準意圖 → 偏方向 | 漂亮但錯方向 | 持有 vision，判「這是我要的嗎」 | `/debrief` |

**優先級：方向 >> 品質**。LLM 預期能做到 Clean Code 等級（頂多需人提點）；災難性、無法靠 polish 彌補的是方向錯 ——「程式碼架構再好也沒用，如果直接做錯方向」。所以 viewport 重度傾斜在**方向驗證**，不浪費人注意力在 code 品質（那是 `/code-review` + LLM 自身能力的事）。

> viewport 渲染的是人類**用來承載意圖 / 理解結構的 artifact**（use case / scenario / UI / 範例 / 心智模型），不是 code 結構（簽名 / 檔案樹 / drift / 覆蓋率 —— 那是 LLM 鏈的 `/code-review`、`/audit-test`）。

### 三層介入（證據獨立性遞增）

| 層 | 機制 | 獨立性 | 軸 |
|----|------|--------|-----|
| 1 | same-session LLM 自判（agent review、`/ep-review` in-pipeline、`/audit-test`） | 低 | A |
| 2 | 跨 session LLM 第二意見（開新 session 跑 `/code-review`/`/ep-review`，findings 貼回實作 LLM → `/judge-review`） | 中 | A |
| 3 | `/debrief`（改動理解+驗證證據）+ `/illustrate`（結構 viewport）+ `/smell-detector`（壞味道：zoom 放大鏡/baseline 盤點）：人類 viewport 判讀 | 高（不同智能） | B |

理論底層（A/B 軸、L1-L6 證據階層、證據獨立性、Claim→Evidence→Trust）見 `rules/acceptance-evidence.md`（always-on 核心）；深層理論（Runtime Invariant Assurance、Intent Drift Type A/B、filter trap、B 軸演進）見 acceptance-evidence skill（on-demand）。本節是入口摘要。

### 核心流程命令分類

| 命令 | 受眾 | 層 | 誰呼叫 |
|------|------|----|--------|
| `/spec` | LLM（人互動·需求釐清） | 鏈 | 人類觸發 |
| `/execution-plan` | LLM | 鏈 | 人類觸發 |
| `/ep-review` | LLM | 1（同 session 自判）/ 2（跨 session） | AI-self / 人類（跨 session） |
| `/ep-validate` | LLM | 鏈 | AI-self |
| `/implement` | LLM | 鏈 | 人類觸發 |
| `/post-build` | LLM | 鏈（build 後收尾鏈編排） | 人類觸發 |
| `/audit-test` | LLM | 1 | AI-self |
| `/code-review` | LLM | 1 / 2（跨 session） | LLM / 人類（跨 session） |
| `/judge-review` | LLM | 鏈 | AI-self |
| `/followup-review` | LLM | 2（Review LLM 驗收實作 LLM） | LLM / 人類觸發 |
| `/fix-test` `/lint-fix` | LLM | 鏈（修復） | AI-self |
| **`/debrief`** | **人類（改動理解簡報）** | **3** | **人類** |
| **`/illustrate`** | **人類（結構 viewport）** | **3** | **人類** |
| **`/smell-detector`** | **人類（壞味道偵測）** | **3** | **人類** |
| `/commit` | 人類確認 | — | 人類 |
| `/metadata-sync` | LLM | 1 | 人類 / AI-self |

工具/維護命令（`/doc-health`、`/consistency`、`/instruction-*` 等）與受眾模型正交，完整索引見 `skills/CLAUDE.md`。

## 專案結構

- `rules/` — 行為規範的 **always-on 核心**（載入機制因 harness 而異；部署紀律 + scope 分類 + 截斷線/尺寸 gate 見 `rules/AGENTS.md`——非 Claude 端是單檔 bundle，受 harness 截斷線約束（ZCode 實測 100KiB 硬編碼），rule 只放須在首個有後果決策前在場的最小核心——資格判準見 memory-audit 統一定義表）
- `skills/` — 領域知識和工作流 skills（on-demand；SKILL.md 開放標準，跨 harness 可攜；Claude 端 `/name` slash 與 Skill tool 皆可觸發，工作流 skills 索引見 `skills/CLAUDE.md`）。**reference skill 分層**：on-demand 級 rule 內容下沉至此——rule 留 always-on 核心＋pointer，深層住 `skills/<同名>/SKILL.md` 經全域 symlink 四 harness 按需可讀；這是控制 bundle 尺寸的既定模式（先例：acceptance-evidence / symbol-query-routing / instruction-writing）
- `skills/_common/` — 共用子範本（跨 skill 引用單元，非 skill；`instruction-*` 等使用）
- `hooks/` — Hook 實作腳本（跨 Claude/ZCode 單一來源。hooks 無目錄載入點，**不能 symlink**——兩家 config 以絕對路徑引用本目錄腳本：Claude `~/.claude/settings.json`；ZCode 3.7.7+ user-level hooks，註冊範本 `hooks/zcode-registration.json`——**範本內容是 `~/.zcode/cli/config.json` `hooks:` 鍵下的子樹值，merge 進去而非整檔覆蓋**（整檔覆蓋會毀掉 config 的 mcp/plugins 區塊）、`notification.sh` 不移植。詳細實測與 ZCode 限制（事件子集、專案層忽略、per-session 快照）見 [04 報告 §7 修訂](ai-analysis/reports/_done/superpowers/04-multi-harness機制對照.md)）
- `agents/` — 跨 harness subagent 定義（**`roles/`＋`presets.toml` 是 authoring 單一源（roles frontmatter 白名單、零 model／thoughtLevel 鍵；presets＝deployment 單一源——default binding FK → `skills/model-routing/catalog.toml`）→ `scripts/sync_agents.py` 生成 `zcode/`（pins＝presets default binding 經 catalog 解析）與 `claude/`（full 別名釘選、其餘省略 model＝inherit）兩 registry**——`~/.zcode/agents`→`agents/zcode/`、`~/.claude/agents`→`agents/claude/`；requirement 相容 token（full/vision/lite——`--map` 相容輸出，非路由依據；正式能力需求＝workflow 自有 WorkUnitContract rows）、**全生命週期 execution contract 表（work-unit／preset／binding 指針）與 harness 軸 dispatch matrix**、欄位相容策略與 ZCode Beta 限制見 [agents/AGENTS.md](agents/AGENTS.md)）
- `ref-docs/` — 參考文檔（外部書籍 PDF + 衍生分析）；PDF 受版權不 commit（`.gitignore` `ref-docs/*.pdf`）。`ref-docs/harness/` 是五家 harness 官方文檔鏡像（claude-code/opencode/zcode/codex/meta〔Muse Code〕）+ `contracts.md` 對照分析——**更新鏡像用既有工具 `ref-docs/harness/crawl.py`**（`uv run python ref-docs/harness/crawl.py [--source zcode]`，discover + sha256 增量寫入 + manifest 維護；不要手動逐頁鏡像）
- `deploy/` — launchd plist 等部署資產的**版控落點**（先例 `deploy/entitlements-probe.plist`）——plist 源進版控、機器本地安裝副本（`~/Library/LaunchAgents/`）不入版控；改排程行為改這裡的源再安裝（AIR-72 吸收形態③）
- code-reality 工具鏈 — meta 層工具，**住獨立 repo `~/Github/code-reality`（Rust carrier，非本 repo 目錄）**；消費形態 `code-reality <tool> --repo <repo-root>`（binary 安裝與存在性偵測真相源見 skill）；工具用法/時點真相源 [skills/code-reality/SKILL.md](skills/code-reality/SKILL.md)；repo 知識歸各 repo 的 `.code-reality.toml` profile
- delegate-bridge — **三家族委派 bridge** plugin（muse＋codex＋glm，`task --family muse|codex|glm`；ZCode/CC 雙端 marketplace 發佈），**住獨立 repo `~/Github/delegate-bridge`（非本 repo 目錄）**；消費形態 plugin agent（`delegate-rescue` 委派、`delegate:delegate-runtime` skills）＋ bridge CLI；計費鐵則＝muse 純訂閱 5h 窗口（無 API key 面）、codex 訂閱載具（bridge 剝 `OPENAI_API_KEY` 防 API-key 計費翻轉；現行帳號面見 spine `model-runtime-entitlements`）、glm＝GLM provider 帳號面（native-ID-only，見 model-routing glm 專節）；registry 預設 pin 單一源＝`agents/presets.toml`（default binding→`skills/model-routing/catalog.toml` 解析；model／effort 供給事實＝catalog.toml）——不在此 materialize；muse CLI 事實真相源 [memory reference_muse-code-cli-facts]、codex raw CLI 事實 [memory reference_codex-cli-exec-facts]、委派細節真相源 repo `docs/`
- **Muse memory（受約束寫入者——AIR-54；AIR-79 plugin 化）**：記憶主體＝repo 內 `.agents/memory/`（gitignored；自帶池 git）——muse 以 project scope 原生讀（`read_memory`；開場自動注入 MEMORY.md），CC 端 `~/.claude/projects/-Users-ctai-Github-ai-guide/memory` 換目錄 symlink 指主體、ZCode 既有鏈雙跳；寫入流：`add_memory`/`edit_memory` 被 user-scope muse plugin `muse-memory-governance`（source home `muse-plugins/memory-governance/`——install＋approve 裝一次，所有帶 marker 的 repo 生效）的 PreToolUse 閘代存 `.agents/memory-inbox/` 並 deny——repo opt-in marker＝`.agents/memory-governance.json`（`protocol:1` 三態：absent→allow 原生／valid→導流／malformed→deny 禁 fail-open）；**禁繞過 inbox 直寫條目或索引**；consolidation（六問＋frontmatter＋path contract/CAS）＝memory-audit skill「Inbox 消費」節（夜波——波前二分之後；或手動）。live 驗證已通過（2026-09-14 四 gate PASS，receipt＝`ai-analysis/_tasks/done/09-12-muse-memory-governance-plugin/poc/live_receipt_20260914.md`）；**legacy 已退役（同日）**——`.muse/hooks.json` 註冊（本 repo＋mosaic 三 WT machine-local）與 `hooks/muse_memory_inbox.sh` launcher 鏈（含 setup 腳本＋inbox 測試）已移除，plugin 為唯一寫入閘（pipe-test 實證接管：muse add_memory→inbox 代存 deny）。運維：governance plugin 每次 content update 後必重新 approve（否則閘靜默下線——fail-open 窗口），真訊號＝`muse plugins inspect <id> --json` 的 `runtime_capabilities[].status`；細節單一源＝[muse-plugins/memory-governance/README.md](muse-plugins/memory-governance/README.md) 運維節。**已知缺口與對帳網（AIR-93）**：muse runtime 在 session 結束後以非 tool 路徑原生直寫池（teardown 學習——PreToolUse 與 sandbox 兩防線皆不涵蓋，mosaic 2026-09-14 實證，機制調查＝`ai-analysis/_tasks/09-14-air93-muse-session-end-bypass/dossier.md`）；偵測＝`scripts/reconcile_memory_pool.py <repo-root>`（唯讀 porcelain delta 對帳——池 HEAD＝approved 基線、working tree delta 即未收編寫入；掛點＝consolidation 開頭／memory-audit 機械層；exit 0＝clean、1＝無法判定 fail-closed、2＝dirty 待補審）。
- **Memory spine 路由**：跨池共享記憶 spine 住 `~/.agents/memory-spine/`（plain md＋同格式 frontmatter；條目由 ai-guide 側 session 寫入，各池 generator 認養 routing 行段——位置決議與認養表見該目錄 `index.md`）
- **觀察池路由**：codex 端可讀本專案記憶主體——主體路徑 `/Users/ctai/Github/ai-guide/.agents/memory/`（AIR-54 遷移；CC 舊徑 `~/.claude/projects/-Users-ctai-Github-ai-guide/memory/` 仍通——目錄 symlink 指主體）；`MEMORY.md` 是索引投影——找知識用 `rg -i "<關鍵詞>" <主體>/_inventory.md` 定位後 Read 條目檔 body（走 CC 舊徑做目錄級 rg/glob 需 `-L`——rg 預設不跟目錄 symlink；直指主體路徑則免）；**主體對 codex 唯讀**（單一寫入點拓撲）——有該寫的發現照回報慣例交 CC/ZCode 側 session，不直接寫池

## 寫作治理

新增 rule/skill/command 時遵守：

1. **先修剪測試**：這行知識從程式碼推導得出嗎？是 → 不寫
2. **選對載體**：Hook？Rule？Skill？Prompt/LLM 流程？判準——hook＝純機械＋單一入口＋無語義例外**三者皆是**（缺一即退 LLM 流程，假確定性比真語義危險）；rule＝須在首個有後果決策前在場的最小核心/bootstrap（always-on 預算稀缺；資格公式見 memory-audit 統一定義表）；skill＝on-demand 方法論（理論深掘、失敗案例群、撰寫規範細則＝reference 分層）；語義判斷（有「看情況」例外）＝prompt/LLM 流程。「該寫哪」統一定義表（載體職責×常駐-按需×寫入預設）單一源見 memory-audit skill；hook 資格論證與對照組見 instruction-writing skill「載體選擇」；`deploy_agents.py` 的 90KiB gate 撞線時以此為處方
3. **驗證附著**：rule/command 是否包含可驗證的標準？沒有驗證的規則是噪音
4. **長度預算**：CLAUDE.md 越長，AI 越容易忽略重要規則。一條規則一行能說完最好
5. **部署同步**：編輯 `rules/` 後的部署與驗證紀律見 [rules/AGENTS.md](rules/AGENTS.md)「部署紀律」（含 `/sync-sources` 機械新鮮度檢查）
