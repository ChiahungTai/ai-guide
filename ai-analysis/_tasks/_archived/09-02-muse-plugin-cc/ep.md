# EP: muse-plugin-cc — Muse Code 委派 plugin（ZCode/CC 雙端）

> **ep_type**: implementation
> **baseline**: `6efae1690a6d955e66a16f02e9f1ac8dbf734f45`（ai-rules；plugin 屬新 repo `~/Github/muse-plugin-cc`，其 baseline 於 S1 git init 時自立）

## 實作總覽

致敬 [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) 與 [xai-org/grok-build-plugin-cc](https://github.com/xai-org/grok-build-plugin-cc)（兩者 Apache-2.0）開發 Muse Code 委派 plugin：ZCode / Claude Code session 透過 headless `muse exec` 把任務委派給 Muse Code CLI。架構取 grok 的單一 bridge（每 task spawn 一次、無常駐 broker——`muse exec` 是 one-shot 行程），功能面取 codex 的 forwarder 契約與結構化 review、grok 的 runs 表格 UX。

**核心差異化（兩個前輩都沒有）**：訂閱制計費——bridge 主動從子行程環境剝除 `META_API_KEY`（Muse auth 優先序 env key > stored key > browser session，`ref-docs/harness/meta/muse-code/auth.md:47`）。剝除 env key 後依優先序落到 stored key（onboarding 自動連接的那支＝訂閱載體，`subscriptions.md:42`）或 browser session——兩者都是訂閱計費。**殘餘風險**：user 曾以 `muse auth set` 存入 PAYG key 時，stored key 會**靜默**蓋掉訂閱（文件只承諾 env key 蓋 session 時告知）→ 對策：env 剝除＋`auth-failed` 錯誤分類（2026-09-02 修訂：原「SM-13 ＋ setup 綠燈硬前提」已移除——auth.json 實證為 oauth/device_code 訂閱載體，stored-key 向量由使用紀律承擔，見 S1 硬前提條款；發佈公開前重評）。這是唯一 flat-rate 路徑——ZCode 直連／ccr／codex plugin 三種 API 供給路徑全是 pay-as-you-go（`subscriptions.md:53`："Your subscription only works through the Muse Code CLI while signed in"）。

**已裁定設計決策**（user 2026-09-02）：
1. 不支援 `META_API_KEY` 設定——純訂閱制；bridge 防禦性剝除 + setup 警告
2. `--yolo` 由呼叫端（ZCode/CC session）opt-in pass-through；預設 `--disable-approval`（sandbox 開）
3. 要讀 repo 規則用 `--trust-workspace`（獨立 flag，`permissions.md:71`），不是 `--yolo`

## 段落 0：全域研究摘要

研究素材：`ref-docs/harness/meta/` 92 頁鏡像（背景 research agent 完整報告見任務家 `research.md`；證據行號皆指向鏡像）＋兩個致敬對象原始碼（本機 plugin cache + GitHub repo）＋ ZCode plugin 開發文檔鏡像。

### 可複用基礎設施

| 元件 | 來源 | 用途 |
|---|---|---|
| forwarder 契約（單次 task、stdout 原樣回、flag pass-through） | `openai/codex-plugin-cc` agents/codex-rescue.md + skills/codex-cli-runtime | S3 muse-rescue 移植 |
| 結構化 review schema（verdict: approve/needs-attention + findings 分 severity） | 同上 schemas/review-output.schema.json | S4 直接搬改 |
| 單一 bridge 架構（1107 行 grok-bridge.mjs，spawn-per-task、job ledger、runs 表格） | `xai-org/grok-build-plugin-cc` scripts/grok-bridge.mjs | S1/S5 架構藍本 |
| SessionStart/End lifecycle hooks | 兩者皆有 scripts/session-lifecycle-hook.mjs | S5 搬 |
| directory marketplace 安裝先例 | `code-reality-market`（`~/Github/code-reality/dist/marketplace`，已登錄於 `~/.zcode/cli/plugins/known_marketplaces.json`） | S6 打包與安裝 |
| plugin 目錄結構慣例 | 兩者：`.claude-plugin/ agents/ commands/ prompts/ schemas/ scripts/ hooks/ skills/` | S1 骨架 |

### Muse CLI headless 面事實（委派契約的依據）

- `muse exec [--json] [--prompt-file] [--session-id <uuid>] [--disable-approval|--yolo] [--max-model-steps <n>]`；`muse export --session <uuid> --out run.json`（`extending.md:117-144`）
- exit code 語義：0=turn 完成（**≠工作正確**）、1=失敗/取消/超 steps 上限、2=usage error、130/143=SIGINT/SIGTERM；官方明言 gate on tests 不 gate on exit code（`extending.md:125`）
- `--sandbox-network <proxy-only|restricted|enabled>`（`permissions.md:88-92`）；`--trust-workspace`（`configuration.md:77`）
- `--reasoning-effort none|minimal|low|medium|high|xhigh|ultra`（`configuration.md:61`）
- verification observer 預設開（驗證宣稱完成的工作，`extending.md:48`）——rescue 信任基礎，確保不被關
- 1M context、多模態輸入 = 模型能力（文檔宣傳用，不進 headless 契約）

### 風險假設清單

| # | 假設 | 等級 | 驗證 |
|---|---|---|---|
| R1 | `muse` CLI 可安裝於 macOS arm64 且 headless exec 可跑 | **致命** | ✅ **已過**（POC 實測，`poc-results.md`） |
| R2 | 台灣區可開通 Meta dev 帳號＋訂閱；headless exec 走簽入 credential = 訂閱計費 | **致命** | 半證：第一層成立（零 API key 下 4 runs 全成功）；dashboard 歸屬核對待 user（判別步驟見下） |
| R3 | `muse exec --json` JSONL 事件流穩定可解析 | 高 | ✅ **已過**（事件 schema 已映射：`stream.id`=session、`run.model.configured`、`run.terminal.completed`.text、`tool.result`、`run.output.delta`） |
| R4 | `--json` 事件 schema 跨版本 churn（Muse Code 產品新、changelog 活躍） | 高 | bridge 鬆剖析（unknown type **與不可解析行**均跳過計數，不炸）+ S2 版本偵測 |
| R5 | ~~`--model` 假想 flag~~ → **已證實**（`configuration.md:76` 文檔化「Common to both」，POC 實用）；`--effort` 為 bridge 層縮寫，映射 `--reasoning-effort` | 低（已解） | POC 實測 |
| R6 | ZCode directory marketplace 載入自寫 plugin（code-reality 先例已證） | 低 | S6 安裝即驗 |
| R7 | **CLI 預設模型不穩定**（POC 4 runs：contributor×2、standard×2，catalog/rollout 決定） | 高 | bridge 預設顯式 `--model muse-spark-1.3`（standard：數據不用於訓練，隱私保守；2026-09-04 由 1.2 升級）；caller 可覆寫 |

**R2 判別步驟（可操作化，EP review C-P1-11 採納）**：4 個帳務錨點（見 `poc-results.md` 末表，含 standard 與 contributor 模型各 2）——(a) dev.meta.ai `/usage` API dashboard 前後對照：**全數不出現**＝走訂閱（出現＝PAYG，R2 敗）；(b) Accounts Center 訂閱用量窗口計數應 +4；(c) 特別注意 standard 模型 runs（#2/#3）是否例外進 API dashboard——若是，代表訂閱僅涵蓋 contributor tier，bridge 預設模型改 pin contributor（計費必要性凌駕隱私偏好，屆時 README 警告雙模型差異）。截圖為必要產物。

**死路假設嫌疑**：無（全新 artifact，無既有符號整合宣稱）。

### 平台限制（研究發現）

- **workflows（JS 編排引擎）在 `aarch64-apple-darwin` 套件缺席**（`workflows.md:16`）——本機正是此平台。workflows 不進核心功能；S2 setup 偵測 engine 缺席時文檔化降級為 subagent fanout（prompt 驅動，`extending.md:21-33`）。

## UC 盤點

ai-rules 為 meta repo（無模組 Capabilities 表格）——本 EP 變更不觸及 ai-rules 既有命令/rules 行為；受影響面 = 新 plugin repo。新增 UC 住 plugin repo README（build 後成為其 AGENTS.md 種子）。

### Backlog 關聯
- `.kanban/Backlog/` 無既有相關卡（新弧）
- 自動建卡：EP 產出後建「EP 追蹤卡」一張（本檔尾部清單）

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（跳過，理由：meta repo 無此檔）

### 掃描範圍
- ai-rules AGENTS.md 專案結構（plugin 為新 repo，僅日後加一行指紋）、`.kanban/` 全 lanes、兩致敬 plugin 原始碼、meta 鏡像 92 頁

### 新增 UC

| 能力 | 狀態 | 實作路徑（plugin repo 內） |
|---|---|---|
| 任務委派（rescue：診斷/研究/修復，forwarder 契約） | 📋 | `plugins/muse/agents/muse-rescue.md` + `scripts/muse-bridge.mjs task` |
| 結構化 code review（verdict+findings+trajectory 審計） | 📋 | `commands/muse-review.md` + `schemas/review-output.schema.json` |
| 背景 runs 管理（表格 UX、export 審計） | 📋 | `commands/muse-runs.md` 等 + bridge job ledger |
| 環境健檢（binary/登入/訂閱/沙箱/observer） | 📋 | `commands/muse-setup.md` + `scripts/muse-bridge.mjs setup` |
| 雙端發佈（directory marketplace） | 📋 | `dist/marketplace/marketplace.json` |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|---|---|---|---|---|
| SM-1 | 委派修復任務 | `/muse 修這個 failing test` | bridge spawn `muse exec --json --disable-approval --model muse-spark-1.3 --reasoning-effort xhigh --max-model-steps 200`，stdout 原樣回 | 無 | 任務委派 |
| SM-2 | muse 未安裝 | 任務委派時 `command -v muse` 失敗 | 明確錯誤訊息引導 `muse-setup`，非 stack trace | 無 | 環境健檢 |
| SM-3 | 未登入/訂閱失效 | muse exec 回 auth 錯誤 | 錯誤分類為「認證」（JSONL 錯誤事件關鍵字，分類失敗=原文透傳），指引 `/muse-setup`；不建議設 API key（違反設計裁定） | 無 | 環境健檢 |
| SM-4 | parent env 帶 `META_API_KEY` | shell profile 設過 | setup 警告「將剝除以保訂閱計費」；bridge spawn 前剝除 | 無 | 環境健檢 |
| SM-5 | caller 要 yolo | `/muse ... --yolo` 明示 | pass-through `--yolo`；未明示則 `--disable-approval`（實證涵蓋 network review 層——POC 網路任務 200） | 無 | 任務委派 |
| SM-6 | run 超步數上限 | `--max-model-steps` 滿 | exit 1；JSONL 步數事件剖析標 `capped`；不偽裝成成功 | 無 | 任務委派 |
| SM-7 | run 中斷接續 | `/muse 繼續 --resume` | `--session-id <last>`（last 解析在 bridge `task --resume-last`；sessionId 捕獲實證＝事件流第一行 `stream.id`） | session ledger | 任務委派 |
| SM-8 | 唯讀 review | `/muse-review` | `--sandbox-network restricted`＋verdict 走 JSON schema（bridge `review` 子命令驗證）；附 `muse export` trajectory 路徑 | 無 | code review |
| SM-9 | 訂閱用量牆 | mid-run 達 plan 上限 | JSONL 錯誤事件剖析標 `failed-usage`、如實透傳；不重試燒 API 計費 | 無 | 任務委派 |
| SM-10 | 長任務背景化 | `--background` | bridge 記 ledger、detach；`/muse-runs` 查表格 | ledger 檔 | runs 管理 |
| SM-11 | workspace 不信任 | repo 從未信任 | 預設忽略 repo 規則；caller 明示 `--trust-workspace` 才載入 | 無 | 任務委派 |
| SM-12 | JSONL 異常 | muse 升版新增 event type／SIGTERM 死在半行 JSON 上 | bridge 鬆剖析：unknown type 與不可解析行（尤其尾行）跳過並計數，不炸 | 無 | 任務委派 |
| SM-13 | stored PAYG key 靜默蓋訂閱 | user 曾 `muse auth set` | ~~bridge task 硬前提＝setup 綠燈未過即拒跑~~ **2026-09-02 修訂：綠燈硬前提移除（user 裁定，依據見 S1 硬前提條款）；防線＝env 剝除（SM-4）＋`auth-failed` 錯誤分類；發佈公開前重評** | 無 | 環境健檢 |
| SM-14 | 跨 workspace resume 被拒 | session 的 workspace 與當前 cwd 不符 | `--allow-workspace-switch` caller 明示 pass-through；未帶時錯誤分類「workspace-mismatch」＋提示 | 無 | 任務委派 |
| SM-15 | 雙流消費與容錯 | `muse exec --json` 人類可讀在 stderr、JSONL 在 stdout；ledger 損毀／`muse export` 失敗 | bridge 同時消費 stdout（事件）與 stderr（狀態行）；ledger 解析失敗＝重建索引＋原始檔保留；export 失敗＝review verdict 照常交付、標記 trajectory-missing | 無 | 任務委派／runs 管理 |

## 段落劃分原則

垂直切片：先讓一個委派跑通（S1-S3 主動脈），再疊 review（S4）、runs（S5）、發佈（S6）。段落間共用契約（flag 語義、exit code 映射、ledger 格式）顯式化於各段語義約束。

---

## S1：專案骨架 + bridge MVP + 致命先驗 POC

### Context
新 repo `~/Github/muse-plugin-cc`（standalone，照兩上游 `-cc` 先例；Apache-2.0 可開源）。本段建立骨架與最小可跑的 `task` 子命令，並驗證三項致命先驗。

**UC 引用**：任務委派（最小形态：本地手跑 bridge task 成功）。

**Blocking user prerequisites**（build session 無法自理）：
1. 安裝 `muse`（`curl -fsSL https://dev.meta.ai/install.sh | sh`）
2. dev.meta.ai 開帳＋Billing（訂閱需 Accounts Center 開通）
3. `muse` 首次登入（browser sign-in）

### 依賴錨點
- 參考實作（非依賴）：`~/.zcode/cli/plugins/cache/xai-grok-build/grok-build/0.2.1/scripts/grok-bridge.mjs`（spawn/ledger/render 模式）
- 外部依賴：`muse` binary（R1/R2 致命先驗對象）

### 語義約束（S1 是唯一 flag 契約源——旗標面擴充一律回歸本段，S3/S4 只消費不擴充）
- env 剝除清單：`META_API_KEY`（唯一強制項）
- 預設 flags：`--json`、`--disable-approval`、`--model muse-spark-1.3`（R7：CLI 預設模型不穩定，顯式 pin；standard tier＝數據不用於訓練；2026-09-04 由 1.2 升級——ai-rules 解析表同步，L4 探針實證 1.3 在服）、`--reasoning-effort xhigh`（2026-09-04 user 裁定：原不帶 flag 落 muse CLI 預設 high；caller `--effort` 可覆寫）、`--max-model-steps 200`
- caller flag 面（S3/S4 消費）：`--yolo`（opt-in，取代 disable-approval）、`--trust-workspace`、`--resume`→bridge 解析 last session、`--steps N`、`--effort <v>`→`--reasoning-effort <v>`、`--model <id>`、`--network <v>`→`--sandbox-network <v>`、`--allow-workspace-switch`
- **硬前提（2026-09-02 修訂）**：`task` 拒跑條件＝binary 缺失。原「setup 綠燈未取得即拒跑」條款**移除**——user 裁定：auth.json 實證為 oauth/device_code 訂閱載體（無 stored API key），stored-key 向量由使用紀律承擔（不執行 `muse auth set`）；發佈公開前重評 spawn 時即時檢查方案。setup 降為診斷工具（綠燈仍計算顯示，不再作為 task 前提）；auth 類失敗仍由錯誤分類 `auth-failed` 攔截＋指引
- exit code 映射表：`0`→completed、`1`→failed-or-capped、`2`→usage-error、`130/143`→interrupted；verdict 永不由 exit code 推導；**細分狀態（capped/failed-usage/auth-failed/workspace-mismatch）由 JSONL 錯誤事件關鍵字剖析**（事件樣本以 POC 記錄為規格源；分類失敗＝原文透傳，不猜）
- **ledger 契約（升 S1 擁有）**：per-repo `.muse-bridge/jobs.json`（job index：id、sessionId〔來源＝事件流首行 `stream.id`〕、status、steps、effort、model、summary、exitCode、timestamp）＋ per-job JSONL 原始檔。**寫入原子化（write-tmp＋rename）**——S3/S4/S5 平行段共享，併發 bridge 同寫不得丟 job（muse 複審 #3 採納）；`status` 枚舉 `running|completed|failed|failed-usage|capped|interrupted|review-fail`（JSONL 事件剖析產出；`review-fail` 為 S4 review verdict schema 驗證失敗專屬——S4 fix round 回寫），`exitCode` 另存原值——雙源並存非二選一
- prompt 傳遞：一律 `--` 分隔後接 prompt（防 `-` 開頭誤判 flag）；超過閾值（~2KB）自動改寫暫存檔＋`--prompt-file`
- spawn cwd＝workspace root（git root；無 git 則 cwd）

### 核心實作要點
- repo 骨架：`plugins/muse/{.claude-plugin/plugin.json, agents/, commands/, prompts/, schemas/, scripts/, skills/, hooks/}`、`LICENSE`（Apache-2.0 全文，vendor 源＝handoff `reference/LICENSE.apache2.verbatim`）、`NOTICE`（**Apache-2.0 §4(d)：再製兩上游 NOTICE 原文＋附加本 plugin 衍生與變更聲明**——EP review C-P2 採納；codex 原文 vendor 源＝`reference/NOTICE.codex.verbatim`）、`README.md`、`package.json`（node ≥18，無 runtime 依賴）、`tests/`
- `scripts/muse-bridge.mjs`：`task "<prompt>"` 子命令——spawn `muse exec --json --disable-approval --max-model-steps 200 -- <prompt>`、子行程 env 剝除 `META_API_KEY`、stdout JSONL 透傳＋人類可讀 render、exit code 映射輸出
- binary 偵測：`command -v muse` 失敗 → 引導訊息（SM-2）

### Pseudo Code

```
muse-bridge.mjs
├── main(argv)
│   ├── subcommand = argv[0]  // task | setup（S2 補）
│   └── task: runTask(prompt, flags)
├── runTask(prompt, flags)
│   ├── assertBinary()          // spawnSync("muse", ["--version"])；缺 → exit 2 + 引導訊息
│   ├── env = { ...process.env }; delete env.META_API_KEY   // 設計裁定 #1
│   ├── args = ["exec", "--json", "--disable-approval",
│   │          "--model", flags.model ?? "muse-spark-1.3",   // R7：顯式 pin
│   │          "--reasoning-effort", flags.effort ?? "xhigh", // 2026-09-04 user 裁定
│   │          `--max-model-steps`, flags.steps ?? 200]
│   │   + (flags.yolo ? ["--yolo"] : [])                    // 裁定 #2：caller opt-in
│   │   + (flags.trustWorkspace ? ["--trust-workspace"] : [])
│   │   + (flags.sessionId ? ["--session-id", flags.sessionId] : [])
│   │   + (flags.network ? ["--sandbox-network", flags.network] : [])
│   ├── child = spawn("muse", args.concat(prompt), { env, cwd })
│   ├── child.stdout → JSONL 鬆剖析器（unknown type 忽略）→ 即時 render + 落 ledger
│   └── child.on close(code) → mapExitCode(code) → exit(mapped.semantic ? 0/1/2)
├── mapExitCode(code)   // {0:completed, 1:failed-or-capped, 2:usage-error, 130/143:interrupted}
└── renderEvent(evt)    // message/tool_call/approval 分行；timestamp 留供 runs 表
```

### 驗證策略
- **POC（致命先驗，`poc/`）**：
  - `poc-1`（R1）：`muse --version` + `muse exec "say hi" --disable-approval` 成功回覆
  - `poc-2`（R2）：簽入狀態下跑一次委派 → dev.meta.ai usage dashboard 確認計入訂閱窗口（非 API key 計費）；同時驗證 env 有 `META_API_KEY` 時 bridge 剝除後仍走訂閱
  - `poc-3`（R3）：`--json` 輸出存檔，JSONL 每行可 `JSON.parse`；記錄事件 type 清單
  - 附帶（R5）：`muse exec --help` 全 flag 面存 `poc/flags-snapshot.txt`
- **測試計畫**：單元（mapExitCode、env 剝除、JSONL 鬆剖析——unknown type 與 malformed 行不炸、`--prompt-file` 閾值改寫）＋整合（fake-muse fixture script 模擬 exit 0/1/2/130，照上游 `fake-codex-fixture.mjs` 模式）＋E2E（真 muse 跑 poc-1 場景）
- **已知未覆蓋**：訂閱用量牆（SM-9）無法在 POC 重現，靠錯誤如實透傳設計 + 上線後觀察

---

## S2：setup 健檢

### Context
**UC 引用**：環境健檢。所有失敗路徑（SM-2/3/4）的診斷入口。研究發現的觀察者保護與平台偵測落在這裡。

### 語義約束（binary 偵測沿用 S1；與 S3 共享警告文案語彙：SM-4 的 META_API_KEY 警告、auth-failed 分類指引——SM-13 綠燈硬前提已於 2026-09-02 移除，setup 為診斷工具）
### 核心實作要點
- `muse-bridge.mjs setup`：逐項檢查輸出 `[OK]/[WARN]/[FAIL]` 表
  1. binary＋版本（對照 changelog 已知 flag 面）
  2. credential 判別（EP review S-P2 採納細化；muse 複審 #2 操作化）：讀 `~/.config/muse/auth.json`（結構實證：`{schema_version, providers.meta.{mechanism, storage, obtained_via, api_base_url, user_full_name, user_email}}`）——判別鍵＝`providers.meta.mechanism` 與 `obtained_via`（onboarding/browser 簽入 vs `muse auth set`）。onboarding credential（訂閱載體）= OK；PAYG stored key = FAIL＋指引清除；完全未登入 = FAIL＋指引 `muse login`。**規格源＝vendored 脫敏樣本**（onboarding 樣本現有；PAYG 樣本於隔離環境 `muse auth set` 製作後補，再寫判別器）；**PII 禁令**：`user_email`/`user_full_name` 不得出現在 setup 輸出或 ledger
  3. parent env `META_API_KEY` 在場 = `[WARN]` 將剝除（SM-4）
  4. 沙箱可用性（EP review C-P2 採納：可操作化——跑 trial `muse exec` 觀察 sandbox 錯誤分類間接推斷；`permissions.md:79` 僅描述 muse 自身驗證時點，非外部可呼叫檢查）
  5. verification observer 狀態（研究 #7：確保沒被 settings 關掉）
  6. workflows engine 偵測（aarch64 缺席 = `[WARN]` 降級文檔）
  7. `muse skills list` 抽驗（SK 載入面）
  8. 綠燈結果快取進 ledger（診斷資訊——2026-09-02 修訂後**非** task 前提）
- `commands/muse-setup.md`：渲染健檢表 + 修復指引

### Pseudo Code
```
setup()
├── checks = [binary, login, envHygiene, sandbox, observers, workflowEngine, skills]
├── 各項回 {status: ok|warn|fail, detail}
└── 彙總印表；任一 fail → exit 1 + 修復指引（安裝/登入/訂閱連結）
```

### 驗證策略
- 整合：fake-muse fixture 驅動各 fail 分支（未安裝/未登入/env 髒）
- E2E：本機真跑 `setup` 全綠截圖進 research.md 附錄
- 未覆蓋：訂閱用量/帳單細節不可程式驗證（無公開 API），僅狀態面

---

## S3：muse-rescue agent + `/muse` command + runtime skills（委派入口全家）

### Context
**UC 引用**：任務委派（完整形態：從 ZCode/CC session 以 agent 委派）。移植 codex-rescue 契約 + grok delegate 的 command 層（EP review S-P0 採納：command 入口是四個場景（SM-1/5/7/10）的唯一落點，不可省）。

### 語義約束（共享 S1 的 flag/exit 語義——S3 只消費不擴充；agent 契約與 codex-rescue 對齊：單次 task、stdout 原樣、不做獨立分析）
### 核心實作要點
- `commands/muse.md`（委派入口，grok delegate.md 模式）：
  - 執行模式：`--background`/`--wait`（caller 端背景＝背景跑 agent；與 bridge detach 是兩件事）
  - resume 流程：呼叫 bridge `task --resume-candidate` 取 last session＋AskUserQuestion 確認
  - 預設 write 語義：muse 在 sandbox 內本來就可寫——無 `--write` flag（上游 codex 的 `--write` 在 muse 端無對應物，不搬）
- `agents/muse-rescue.md`：forwarder 契約——只呼叫一次 `muse-bridge.mjs task`、stdout 原樣回、flag 規則：
  - `--yolo`：caller 明示才帶（預設不帶 = `--disable-approval`）
  - `--trust`：明示才帶（repo 規則載入，SM-11）
  - `--resume`→bridge `task --resume-last`；`--steps N` 覆寫預設 200
  - `--effort <v>` 映射 `--reasoning-effort`；`--model <id>` 直通；`--network <v>` 直通；`--allow-workspace-switch` 明示才帶（SM-14）
- `skills/muse-runtime/`：helper 契約（內部、user-invocable: false），含 verification observer 信任基礎說明（verdict 信心來源之一，非唯一）
- `skills/muse-run-output/`：JSONL 事件解讀慣例（grok-run-output 對應物）

### Pseudo Code
```
muse-rescue agent flow:
  prompt 解析（唯一 Claude-side 工作）
    ├── strip routing flags（--yolo/--trust/--resume/--steps/--effort/--background）
    ├── 組 bridge 呼叫：node muse-bridge.mjs task "<raw text>" [flags]
    └── 回傳 stdout 原樣（不潤飾、不補分析）
```

### 驗證策略
- E2E（消費端驗證）：在 ZCode session 真的 spawn muse-rescue 跑一個小任務（如「讀 README 列出三個重點」），驗 stdout 回傳完整性
- 文檔驗證：契約文件 rg 檢查 flag 清單與 bridge 實際支援一致（drift 掃）
- 未覆蓋：muse 端回答品質（模型面，不測）

---

## S4：結構化 code review

### Context
**UC 引用**：code review。codex schema 搬改 + Muse 差異項（`--sandbox-network restricted` 離線、export trajectory、completion-check 話術補償 `/goal`）。

### 語義約束（verdict 一律 JSON schema 判定，永不由 exit code 推導——S1 共享語義）
### 核心實作要點
- **bridge `review` 子命令（EP review S-P1 採納：schema 驗證 owner 在 bridge 層，`task` 保持純 forwarder）**：prompt 組裝（模板＋diff＋completion-check 要求）＋ spawn（`--sandbox-network restricted`、`--reasoning-effort xhigh` 預設）＋ verdict JSON 解析＋schema 驗證（不符 = review-fail，不猜）＋ export trajectory
- `commands/muse-review.md` + `prompts/review.md`：
  - prompt 模板內建 requirement-by-requirement completion check（研究 B 節 `/goal` 補償）
  - 大 diff 走 `--prompt-file`（S1 契約：超閾值自動改暫存檔）
- `schemas/review-output.schema.json`：codex 版搬（verdict/summary/findings[severity,title,...]/next_steps）
- **CR 條件式接線（2026-09-02 軌跡實證＋同日 MCP 接線後修訂）**：muse 端已於 `~/.config/muse/settings.json` 掛 `mcp_servers.code-reality`（stdio `code-reality-mcp --stdio`、mode optional——實證 headless run 可見 20+ `mcp__code_reality.*` 工具）。「存在認知」機器層已解；review prompt 模板教的是**用法指引**：repo 有 `.code-reality.toml`（或 graph.db）時符號/呼叫鏈/影響面查證優先 CR 查詢工具（refs/callers/closure/impact_radius），無 index 退 rg；**禁用寫入面工具**（build/snapshot/delta_tour——MCP 不在 muse 沙箱內，防 review run 產生副作用）。根據：rules-based tool routing 不傳播給委派 agent（mosaic 軌跡實證 CR 零呼叫）——接線須顯式做（本條＝MCP 機器層＋prompt 用法層雙保險）
- review 完成後自動 `muse export --session <id>` 存 trajectory，verdict JSON 附路徑（審計鏈）

### Pseudo Code
```
review(baseRef)   [bridge 子命令]
├── git diff 範圍收集（--base/--scope，codex review 同參數面；--scope 縮減為僅 --base——S4 fix round 裁定記 deviation，實作留後續段，見 BUILD-REPORT）
├── prompt = review 模板 + diff + completion-check 要求（超閾值 → --prompt-file）
├── spawn：flags = {network: "restricted", effort: "xhigh"}
├── 解析 verdict JSON → schema 驗證（不符 = review-fail，不猜）
└── muse export --session <id> --out <ledger>/review-<ts>.json；verdict.trajectory = path
```

### 驗證策略
- 整合：fake-muse 回 fixture verdict JSON（合法/非法各一）驗 schema 閘
- E2E：對本 repo 一個小 commit 真跑 review，verdict + trajectory 落檔
- 未覆蓋：finding 品質（模型面）；大 diff 1M context 消化（模型賣點，記錄不測）
- **CR 紅利實驗（可選，單變數設計）**：同 diff、`--model muse-spark-1.3` pin（防 R7 漂移）、只切「prompt 明示 CR CLI」一項——量 findings 差異。注意：`--trust-workspace` 是另一個實驗（規則載入混合效應，非純 CR），勿混組

---

## S5：runs 管理 + lifecycle hooks

### Context
**UC 引用**：runs 管理。grok 表格 UX 搬 + export 審計包裝。

### 語義約束（ledger 格式與 S1 共享：JSONL + job index；runs 表欄位固定）
### 核心實作要點
- bridge `runs`/`show`/`stop`/`export` 子命令：job ledger（背景 runs、狀態、exit 映射、capped 標記 SM-6）
- bridge `wait <jobId> [--timeout <ms>] [--json]`（AIR-21 延伸，2026-09-04）：`task --background` 的輪詢機械化——500ms 輪詢 ledger 至終態、每輪 stale-running reconcile（dead pid 即時收斂 interrupted 不掛死）、終態渲染同 `show`；`--timeout` 預設 300000（0＝無限）逾時 exit 1 附當前狀態；exit 隨終態（completed→0／failed 家族→1／unknown job 或 usage error→2）；純 ledger 消費、零 muse spawn
- **capped/failed-usage 偵測來源（EP review S-P1 採納）＝JSONL 錯誤/步數事件剖析**（事件 type 清單以 POC-3 記錄為規格來源），非 exit code 推導
- `commands/muse-runs.md`（表格渲染，grok runs.md 同契約）+ `muse-show`/`muse-stop`
- `hooks/hooks.json` + `session-lifecycle-hook.mjs`（grok 搬）：**SessionEnd 對 still-running job ＝ cancel ＋ terminate process tree（照 grok 原行為，EP review C-P2 採納——非僅「提醒」，否則孤兒 muse 行程續燒訂閱額度）**；bridge 自身被殺時的 stale running reconciler（pid liveness 檢查）

### Pseudo Code
```
runs()
├── ledger 讀取（per-repo .muse-bridge/jobs.json，S1 契約格式含 sessionId）
├── 表格：id | status | model | steps | effort | summary | follow-up
└── capped / failed-usage / interrupted 狀態 = JSONL 事件剖析（S1 契約）
export(id) → muse export --session <sessionId> --out <file>
```

### 驗證策略
- 整合：fake-muse 驅動背景 job 生命週期（running→completed/capped/interrupted）
- E2E：背景跑兩個任務 → runs 表正確、stop 殺得掉、export 落檔
- 未覆蓋：跨機器 ledger 共享（out of scope）

---

## S6：marketplace 打包 + 雙端安裝 + 收尾

### Context
**UC 引用**：雙端發佈。照 code-reality 先例。

### 核心實作要點
- `dist/marketplace/marketplace.json`：`{source: "directory", path: plugins/muse}` 條目 + version
- ZCode：設定→插件→添加 marketplace（本地路徑）→ 安裝 muse
- Claude Code：`~/.claude/plugins` 對應安裝（官方 local plugin 機制）
- `README.md`：安裝、訂閱前提、flag 面、與 codex/grok plugin 的差異表（訂閱制/審計/沙箱分級）、NOTICE 授權聲明
- 收尾：`.kanban/Backlog/` 建卡結案搬 `Done/`（ai-rules 端）；ai-rules AGENTS.md 專案結構加一行指紋（`~/Github/muse-plugin-cc` 獨立 repo，同 code-reality 條目格式）

### 驗證策略
- E2E：**雙端各自真裝**——ZCode 安裝後 skill 清單見 `muse:*`、spawn muse-rescue 可用；CC 端同驗（消費端驗證模式，缺任一端不可宣稱完成）
- marketplace version 一致性：`plugin.json` version == marketplace.json 條目 version（ZCode 更新檢查的口徑，文檔鏡像 `plugin.md:75`）

---

## 整合策略

- 段落順序（EP review S-P2 採納修正）：S1→S2 序列；S3/S4/S5 平行（共享契約一律以 S1 語義約束為準）；S6 收尾
- 每段完成即 `node scripts/muse-bridge.mjs <subcommand>` 實跑（must-execute）
- baseline：S1 git init 後 tag `v0.1.0` 起，各段一 commit（**commit 前取得 user 同意**——outward-action-consent）
- 測試跑法：`node --test tests/`（node 內建 test runner，零依賴）

## 收尾步驟（build 後）

1. `.kanban/Backlog/` 建卡：EP 追蹤卡（本 EP 五個 UC）→ 結案搬 `Done/`
2. ai-rules AGENTS.md 專案結構加 muse-plugin-cc 一行（獨立 repo 指紋，照 code-reality 格式）
3. plugin repo README = 其 AGENTS.md 種子（UC 表 + 入口）
4. `/audit-test`：對 fake-muse fixture 測試群稽核
5. 雙端安裝驗證截圖進任務家 `research.md` 附錄

## EP Review 區段（Finding Record）

雙 agent 平行審查（結構面 top-down＋細部正確性）2026-09-02 完成；主 LLM judge：**P0×1、P1×9 全數採納並寫回 EP**；P2 全數採納（規格精確化）。關鍵修正：

| Finding | 等級 | 裁決 | 落點 |
|---|---|---|---|
| `/muse` command 入口在六段全缺席（SM-1/5/7/10 無落點） | P0 | ✅ 採納 | S3 擴為 agent＋command＋skills |
| S4 verdict schema 驗證 owner 未指定、與 S1 透傳契約衝突 | P1 | ✅ 採納 | S4 bridge `review` 子命令 |
| `--effort` 缺 S1 flag 面（平行段落依賴未定義介面） | P1 | ✅ 採納 | S1 flag 契約補全＋「旗標面擴充回歸 S1」 |
| `--resume` last 解析 owner 未指定 | P1 | ✅ 採納 | bridge `task --resume-last`（sessionId 捕獲已實證＝事件流 `stream.id`） |
| SM-3 錯誤分類機制無 owner | P1 | ✅ 採納 | S1 錯誤事件關鍵字分類表（分類失敗＝原文透傳） |
| SM-9 `failed-usage` 無法由宣稱來源推導（EP 自違「狀態不由 exit code 推導」） | P1 | ✅ 採納 | 改 JSONL 事件剖析 |
| ledger 格式 S5 宣稱共享但 S1 未定義（S4 平行依賴 S5） | P1 | ✅ 採納 | ledger 契約升 S1 |
| stored PAYG key 靜默蓋訂閱＋EP:10 auth 措辭不精確 | P1 | ✅ 採納 | 措辭修正＋SM-13＋setup 綠燈硬前提 |
| default flags 下網路任務行為未定義 | P1 | ✅ **實證解** | POC 網路任務 200——`--disable-approval` 涵蓋 network review 層 |
| POC-2 驗法不可操作 | P1 | ✅ 採納 | R2 判別步驟具體化（雙 dashboard＋截圖＋standard/contributor 對照） |
| R5 把 `--model` 列假想 flag（事實錯，configuration.md:76 已文檔化） | P2 | ✅ 採納 | R5 已修＋進 S3 flag 面 |
| `--allow-workspace-switch` 缺席／SM-12 未涵蓋 malformed line／SM-1 `--write` 懸空／prompt 大小炸 argv | P2 | ✅ 採納 | SM-14、SM-12 擴、`--write` 不搬（muse sandbox 內本可寫）、`--prompt-file` 閾值 |
| NOTICE §4(d) 義務／SessionEnd 應 cancel+kill 非「提醒」／整合策略矛盾／路A/B/C 懸空／S2 判據過粗／沙箱檢查不可操作 | P2 | ✅ 採納 | 各落點已修 |

審查者自證與完整報告：本對話 session（2026-09-02）；POC 實證記錄 `poc-results.md`。

### 第三輪：muse 獨立複審（2026-09-02，user 另開 muse session 產出）

無 🔴 必須修正；4 項 🟡 全數採納回寫：

| # | Finding | 裁決 | 落點 |
|---|---|---|---|
| 1 | S1 pseudo code 缺 model pin（實作者照 pseudo 會漏，R7 對策失效） | ✅ 採納 | S1 pseudo args 補 `--model flags.model ?? "muse-spark-1.2"` |
| 2 | S2 credential 判別未操作化（auth.json 格式未釘） | ✅ 採納＋本輪 grounding | S2 check 2 補實證結構（mechanism/obtained_via 判別鍵）＋vendored 脫敏樣本＋PII 禁令 |
| 3 | ledger 併發寫競爭＋雙源 status 易誤讀 | ✅ 採納 | S1 ledger 契約補原子寫＋status 枚舉＋exitCode 並存 |
| 4 | stderr/stdout 分流與 export 容錯未顯式 | ✅ 採納 | 新增 SM-15 |

ℹ️ LICENSE/NOTICE vendor 路徑與 `--prompt-file` 測試缺口：BUILD.md 已補，EP 真相源同步（S1 骨架行＋測試計畫）。
