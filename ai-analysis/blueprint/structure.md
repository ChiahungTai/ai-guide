# structure — 載體層結構地圖（誰引用誰、誰部署到哪、誰消費誰）

> **定位**：ai-rules 載體（rules／skills／agents／hooks／記憶／tour／排程）之間結構關係的合成視角——回答「這個 repo 的東西怎麼互相接」。規範權威在各域治理檔與 generator source，本檔不建立第二套規則；任何邊改動後依 [AGENTS.md](AGENTS.md) 更新紀律消化重編本檔。機械可驗的單源邊已由 invariant 守護（見「治理邊」），本檔僅補無機械守護的結構全景。

## 五層載體

```
L0 authoring（repo 內手改單源）
     │ generator（deploy_agents / sync_agents / index.html 投影）
     ▼
L1 生成投影（機械生成，禁手改）
     │ symlink ／ config 絕對路徑引用
     ▼
L2 部署接線（各 harness 全域位置）
     │
     ├─▶ L3 狀態資料（memory / tour / graph / findings）
     └─▶ L4 排程消費（cron / launchd → skills）
```

| 層 | 內容 | 單源與治理 | 生成/接線 | 機械守護 |
| --- | --- | --- | --- | --- |
| L0 | guide（`ai-development-guide.md`）、`rules/`、`skills/`（含 `_common/` 共用子範本）、`agents/roles/`、`hooks/`、`muse-plugins/memory-governance/`、root 與模組 `AGENTS.md`（單檔 source，wrapper 已退役）、`backlog/`、`ai-analysis/` | 各域治理檔：[rules](../../rules/AGENTS.md)／[agents](../../agents/AGENTS.md)／[hooks](../../hooks/AGENTS.md) AGENTS.md＋[skills](../../skills/AGENTS.md)＋root AGENTS.md | —（手改） | — |
| L1 | `agents/zcode/`＋`agents/claude/` registry；ZCode／Codex／Muse／grok bundle；`blueprint/index.html`（本目錄文件與 root 受眾節投影） | `roles/` 為 authoring 單源、`agents/presets.toml` 為 binding 部署源；bundle targets＝[governance manifest](../../governance/manifest.toml) `surfaces.rules` | `scripts/sync_agents.py`（roles＋presets→雙 registry）；`scripts/deploy_agents.py`（guide＋neutral rules→bundle）；index.html 由 source refresh（手寫＋殼 codegen） | `agents_projection_sync`、`deploy_bundle_freshness`、[projection freshness manifest](projection-manifest.toml) |
| L2 | skills 母鏈 `~/.agents/skills`→repo `skills/`；`~/.zcode/agents`→`agents/zcode/`、`~/.grok/agents`→`agents/claude/`；hooks 絕對路徑註冊、Muse user-scope plugin＋marker `.agents/memory-governance.json` | symlink 活視圖與 bundle snapshot 分開；CC guide/rules/skills/agents 自動載入 symlinks 與 hooks 註冊已退役（AIR-215），`agents/claude/` 是 grok registry 源名，不代表 CC 接線 | [governance manifest](../../governance/manifest.toml) 擁有 symlinks 與 registrations：grok hooks 整檔 render、ZCode hooks 子樹 merge、Codex TOML groups；四 bundle 目標同 manifest | `hook_registration`、`zcode_live_parity`、`skill_allowlist_coverage` |
| L3 | `.agents/memory/` 主體（gitignored 自帶池 git）＋`memory-inbox/`、`~/.agents/memory-spine/`、`.tours/`（corpus＋manifest provenance）、`.code-reality/`（graph.db）、`.review/`（profile-driven findings，弧後清理） | 寫入端紀律＝memory-audit skill；tour 契約＝tour-bootstrap／code-reality skill | 記憶拓撲（AIR-223 direct-anchor）：主體＝唯一 real dir；ZCode→主體直鏈（唯一必要鏈）、CC 舊徑 symlink→主體（optional compat，可缺席）；codex 唯讀（單一寫入點） | memory hooks sensors＋index-regen PreToolUse gate、`tour_validate`（finalization gate） |
| L4 | ZCode cron ×3、launchd（backlog-cleanup／report-server `:6421`／nightly-sequence）、mosaic 23:20 report | 反查表＝[schedule-registry](../schedule-registry.md) A1–A6 | cron prompt 引用 skill 為方法論源；`deploy/scripts/run-backlog-cleanup.sh`→kanban precheck | precheck 紅燈跳過該卡 |

跨 repo 邊（消費非部署）：code-reality（`~/Github/code-reality`，機械 symbol graph 工具鏈）、delegate-bridge（`~/Github/delegate-bridge`，Muse／Codex／GLM／grok 四家族委派 bridge；契約回 root [AGENTS.md](../../AGENTS.md)）、mosaic（report-server 宿主、測試契約 consumer）。

## 四種邊型

### 部署邊（誰投影到哪）

generator＋symlink 群＋harness 註冊——新鮮度/projection/接線由機械 invariant 守護，期望拓撲在 [governance manifest](../../governance/manifest.toml)，各機器是否生效須另驗 install/check/verify。bundle 對應 ZCode／Codex／Muse／grok 的全域 `AGENTS.md`；grok 的注意力預算與其他 harness 截斷線分開。細節在 [rules/AGENTS.md](../../rules/AGENTS.md)「部署紀律」與 [agents/AGENTS.md](../../agents/AGENTS.md)「registry 結構」，此處不複載。

### 引用邊（誰引用誰）

- **reference 分層配對**（rule 留 always-on 核心＋pointer，深層住同名/鄰名 skill；DRAFT-5 的 slimming 波次延續此模式）：

| rule | skill（深層載體） | 分層內容 | bundle role |
| --- | --- | --- | --- |
| design-thinking | deep-thinking | 輸出格式模板、8 問清單、查證細則 | bootstrap split |
| acceptance-evidence | acceptance-evidence | Intent Drift、filter trap、Runtime Invariant 深層理論 | bootstrap split |
| symbol-query-routing | symbol-query-routing | LSP 速查表、rg 陷阱群、跨 harness 載體對照 | bootstrap split |
| instruction-writing | instruction-writing | 撰寫規範全量、五維自洽檢查 | projected（AIR-85 已落地：三鍵標註＋deploy 投影＋行為測試 5/5） |
| llm-output-convention | llm-output-convention | print tag 全表、閉環細則 | second pilot ready（同介面 opt-in，AIR-85 機制已驗證） |
| modern-cli-preference | modern-cli-preference | fd/rg 陷阱目錄、雙掃陷阱 | reference layering（近完成態） |
| model-routing | model-routing | tier×provider 解析表、收法決策樹、family 契約 | bootstrap split |
| context-management | memory-audit | 寫入端紀律（六問）、載體統一定義表 | bootstrap split |
| quality-constraints | validation-strategy | 消費端驗證模式、整合器判定、漸進驗證細則 | bootstrap split |

> bundle role 欄：bootstrap split＝rule 留 minimal semantic closure/bootstrap、body 在 skill；projected＝AIR-85 投影已落地（三鍵 opt-in、非 CC 端 body→pointer、preflight fail-closed）；second pilot ready＝機制已驗證、待該 rule 自行 opt-in；reference layering＝常規深層配對。判準源＝scope 分界研究（reports/2026-09-13-scope-boundary-memory-rules-skills/）＋memory-audit 載體統一定義表。

- 其餘 rule→skill pointer 為常規跳轉（不配對，如 tool-discipline→debugging-and-error-recovery／agent-workflow）；skill→rule 反向引用 20+ 檔（驗證/紀律 anchored 回 rule）。
- skill→skill：review-engine 是 review 家族（ep-review／code-review／audit-test／execution-plan EP Review／implement Agent Review）的 domain 真相源；`_common/` 20 檔被 15+ skills 引用（work-order、workflow-review-pattern、illustrate 家族、state-md-write 等）；工作流 skill 鏈互引見核心流程拓撲。

### 消費邊（workflow 哪階段用誰）

四張表各自完整、單一視圖在本檔：

| 消費面 | 表 | 位置 |
| --- | --- | --- |
| 生命週期 dispatch（stage→orchestrator→agent→tier→artifact→fallback） | execution contract | [agents/AGENTS.md](../../agents/AGENTS.md) |
| 命令受眾（LLM 鏈 vs 人類 viewport 兩軌道） | 命令分類表 | root [AGENTS.md](../../AGENTS.md)「命令的受眾視角」 |
| 核心流程拓撲（pre-EP→spec→execution-plan→implement→post-build→commit＋review 鏈＋viewport 三 checkpoint） | 流程圖 | [skills/AGENTS.md](../../skills/AGENTS.md) |
| 排程消費（cron/launchd→skill） | A1–A6 反查表 | [schedule-registry](../schedule-registry.md) |

### 治理邊（誰驗誰）

- **single-source invariants**（11 條，源＝[check_single_source.py](../../skills/scan-project/scripts/check_single_source.py)，`/sync-sources` 消費）：部署新鮮度（deploy_bundle_freshness）、投影同步（agents_projection_sync）、接線在位（hook_registration／zcode_live_parity）、詞彙契約（bridge_model_vocab）、review schema（severity／confidence／base_perspective）、受眾自標（audience_self_declare）、清單覆蓋（skill_allowlist_coverage）、殼 provenance（report_shell_provenance）。
- blueprint 對齊覆核觸發（AGENTS.md 12 條）、kanban precheck（結案/清板前 exit 1 停手）、memory hooks（write/dirty sensor＋inbox 閘）。

## 已知斷鏈與受控缺口

| 項 | 狀態 | 處置 |
| --- | --- | --- |
| `blueprint/index.html` 投影 freshness | 機械閘在場 | `scripts/projection_freshness.py` 對照 upstream hash；先重投影再更新快照，hash 對齊不取代內容覆核 |
| grok 註冊定義與本機生效狀態 | source 在場、機器面另驗 | governance manifest 包含 grok hooks、agents 與 bundle；本圖描述 source 拓撲，不以 source 在場證明本機部署 |
| ZCode 無 SessionEnd 事件（plugin 孤兒清理缺席） | ⚠️ | hooks/AGENTS.md 定案＝remediation 成本極低非缺口 |
| `skills/AGENTS.md` 索引手維護（自標 drift-prone） | ⚠️ | 無機械防線；超載時可評估 invariant 化 |
| AGENTS.md 家族單檔 source | ✅ wrapper 已退役（AIR-290） | root 與各域以 AGENTS.md 為 source；legacy wrapper 不再是 active 載體 |
| WT 形態（board single-writer／wt-open/close） | ✅ 已落地（AIR-72） | 落地錨點＝workflow.md「待建基建」＋`scripts/wt-open.sh`／`scripts/wt-close.sh`（wt-open 試點通過、wt-close 真卡收線已驗——AIR-77 74d483d；receipt 每次執行自動落盤 .git/wt-close.log——AIR-112；board single-writer 大致落地）；_tasks 遷移由 AIR-77 落地。此處僅 pointer，語義以 workflow.md 為準 |

## 維護語義

本檔的邊清單是**盤點快照**（2026-09-12 全域掃描結晶）；各邊的權威語義在上表連結的源檔。載體增退役、generator／invariant／接線改變時依 [AGENTS.md](AGENTS.md) 對齊覆核流程消化重編，不局部 patch 留雙敘事。
