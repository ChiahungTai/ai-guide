---
name: deep-work

description: "深度工作模式 - 自主開發流程引擎：一整套開發流程直接跑（execution-plan → implement → post-build），AI 全力發揮、慢慢思考、完整交付"
when_to_use: "Autonomous full development pipeline (CC-workflow concept). Three trigger scenarios: 睡前下 UC 級任務 / 外出離開 / 任務不難但想整套開發流程自主跑。Chain runs unattended: plan→build→post-build→report, ending at commit consent."
argument-hint: "任務描述 | Execution Plan 檔案路徑"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]
---

# /deep-work — 深度工作模式

自主開發流程引擎。觸發三型——**睡前下 UC 級任務、外出離開、任務不難想整套直接跑**（CC workflow 概念：一條命令推完整個開發流程，規模判定在流程內做、不靠進場時預判）。用戶不在場或選擇放手，**全力發揮，完整交付。**

## 核心原則

**「深度思考 → 自主決策 → 完整交付 → 驗證通過」**

- **不問問題**：歧義時選最合理方案並記錄理由
- **不趕時間**：充分思考架構、權衡、邊界後再動手
- **不交半成品**：每個功能完整實作、測試通過、Demo 可跑

委託 Skills：
- [autonomous-execution](../autonomous-execution/SKILL.md) — 自主決策、錯誤自癒、完成報告、**紅線/黃線分級**（半夜自主跑時的危險操作安全網）
- [agent-workflow](../agent-workflow/SKILL.md) — 並發控制、模型偵測、Agent spawn 規範；**各段形態（哪段主 session 直做／哪段 spawn 哪個 agent）查表**見其「全生命週期 execution contract（消費側）」

---

## 前置：進入無人值守模式

deep-work 前提是用戶不在鍵盤前（離開／放手不盯）—— 權限提示會卡死無人 flow。**必須在 auto-mode 下執行**（流程 dispatch 前先確認）。auto-mode（詳見 [agent-workflow](../agent-workflow/SKILL.md)「Auto Mode」）：classifier model 在命令執行前把關（阻擋 scope 升級 / 未知基礎設施 / 惡意操作），取代人工權限提示。

### substrate 入口（三選一）

| 入口 | 何時用 | 與 auto-mode 關係 |
|------|--------|----------------|
| **agent-view `claude agents` / `claude --bg "<task>"`**（長程 loop 推薦） | EP→build→review 多命令 loop、user 要可監控/介入、要關 terminal 離開 | 用 dir `defaultMode: auto`（repo 已設），**免旗標**；須先互動接受 auto 一次。supervisor 接管、session survive terminal 關閉（「我去洗澡了」不再綁 terminal；[研究預覽 v2.1.139+](https://code.claude.com/docs/zh-TW/agent-view)） |
| **headless `claude -p`**（一次性） | 要 stdout 報告、單一短任務 | `claude --permission-mode auto -p`（現況保留） |
| **`/at` 組合**（跨 session） | 任務超過一個 usage 窗 | `--bg` 派發 → usage 用盡 → `/at <time>` reset 後 resume |

### 與其他自主入口分工（正交可組合）

- **agent-view** = 本機背景長程（同 session，`claude agents` peek/attach 監控）
- **`/at`** = 跨 session 接續（provider usage reset 後 resume；inline 出現在任務描述內，如「`/at 02:20 繼續修`」）
- **`/handoff`** = 跨 session / repo / provider 交接（換手給另一個 session）

組合例：`--bg` 派發長程 loop → usage 用盡 → `/at` reset 接續 → 必要時 `/handoff` 換 provider。

### `--agent <name> --bg` named-agent 形態（CC 端）與 ownership state machine

agent-view 的 named-agent 形態：`claude --agent <name> --bg "<task>"`——registry agent 定義檔（claude/ registry，生成物）成為 session 主體，worktree 自動隔離（基於 **committed state**）。全 role 名在兩 registry 生成在場（可用性機械對帳＝`scripts/sync_agents.py --map`）；引用不存在的名稱仍立即退出（`--agent '<name>' not found`，session 報 backgrounded 但即刻死亡）。

**ownership state machine（閉環——變更不滯留失蹤）**：

```
dispatch（從 committed ref；agent 依賴 uncommitted → 先 commit〔該預派 commit 走尋常 commit consent gate——不因本分支豁免〕，或主 session attach 餵料）
  → agent 在隔離 worktree 產出（可能無 commit）
  → owning session attach 驗收（無 commit 時 attach 讀 worktree diff＋產物檔）
  → consent gate（主 session 互動——commit-consent 唯一 override 源，見下）
  → commit（agent worktree 的 branch 上）
  → rebase 回主線（trunk+多 WT 慣例：單向 rebase onto trunk、不交互 rebase、trunk 永不被 rebase）
```

- **worktree isolation 與 trunk+多 WT 線模型對齊**：agent worktree 是暫時支線，產出回主線只走 rebase 慣例（同消費端 git 多軌模型）
- **auto-commit override**：agent-view 文檔列「git instructions take precedence」的來源為 task／CLAUDE.md／memory——**rules/ 檔（outward-action-consent）路徑是否同樣覆蓋＝待實測點**；規範立場：rules/ 檔為唯一 override 源；實測未過前此條款標〔未驗證〕，且 L4 驗收雙面照跑：**不 outward**（無 auto-commit/push）**且可回收**（變更可被 owning session 找到→驗收→進既定 branch）
- agent-view 為 research preview——行為可能隨版本變，L4 結果記入當次完成報告

### 誠實處理

permission mode 是 CLI 啟動旗標 / dir 設定，**命令本身無法中途切換**。若當前非 auto-mode → 印出警告「非 auto-mode，無人值守會卡在權限提示；請以 `claude agents`（dir defaultMode=auto）或 `--permission-mode auto` 重啟」並停下，**不靜默降級成互動模式硬跑**。

---

## 流程 dispatch（自主 overlay，依 ARGUMENTS 決定程序）

**deep-work 是「行為模式」（mode）+ 自主 overlay**，可疊加在任意 LLM-chain 程序上。組合時 procedure 委派，deep-work 疊加自主行為（自主決策、歧義選最合理並記錄、完整交付、錯誤自癒、語音通知）。

```
/deep-work <ARG>  ──ARG 決定程序 + 疊加自主行為──

  ├─ ARG 命名 LLM-chain 命令 → 委派該命令 + 自主疊加
  │   • observed：/implement、/execution-plan、/code-review、/ep-review、/ep-validate
  │   • reasonable：/fix-test（含 lint/type 修復）（自癒 loop）、/audit-test（測試）、/consistency（文檔自洽）、
  │                /followup-review（驗收）、/metadata-sync（commit 前更新 + 補漏）、
  │                /handoff（跨 provider）
  │
  ├─ ARG = 任務描述（開發任務：feature/fix/refactor）→ **預設＝完整開發流程**：
  │   /execution-plan（UC 盤點＋EP；流程規模分級在此裁定——simple 邊界不寫 EP 直接 build、
  │   standard 走 card Planning Contract、大型自動建 backlog 卡（full 寫 standalone EP））→（可選 /ep-validate、/ep-review）→ /implement → /post-build
  │   （收尾鏈：code-review〔風險 profile 派發〕→judge-review→修正迴圈→consistency→metadata-sync→殼 refresh）
  │   → 收尾報告；變更留 working tree，commit 等 user 確認（自主紅線不 override）
  │   例外＝非開發流程任務（純研究/調查、環境修復、一次性維護操作）→ 自身階段 1-5（complex；
  │   可自癒接 /fix-test（含 lint/type 修復）；完成後自主品質閘門 → /audit-test、/code-review）
  │
  └─ ARG 內含接續/substrate 指令：
      • /at <time> → 跨 session 接續修飾詞（reset 後 resume；inline，非獨立分支）
      • substrate 見「前置」（agent-view / -p / /handoff）
```

- **ARGUMENTS = `/implement <EP>`**（observed 主路徑）：流程骨架**委派 [build.md](../implement/SKILL.md)**（階段 0-6 全跑），deep-work 自身階段 1-5 **不執行**。**不得省略的 build 步驟**（無人在場時唯一機械防線）：階段 0「EP 快檢」強制輸出、階段 1「POC + demo 盤點」映射表、**階段 2「整合路徑覆蓋硬閘門」**（`rg "<新參數>=" tests/`）、**階段 3「全量測試 exit 0 完成閘門」**、階段 5c `/audit-test` —— 絕不靜默跳過（`/deep-work /implement` 時硬閘門在最需要它的無人路徑必須生效）。
- **ARGUMENTS = 任務描述**：預設完整開發流程（execution-plan → implement → post-build；自身階段 1-5 不執行——同 /implement 委派路徑）；僅非開發流程任務（研究/調查/環境修復）用 deep-work 自己的階段結構（下方）。

## 執行流程

### 階段 1：深度理解

1. **解析輸入**：檔案路徑 → 讀取 EP / Design Plan；任務描述 → 自行分析
2. **探索現有程式碼**：閱讀相關檔案、依賴、import 路徑、模組邊界
3. **架構思考**：列出 ≥ 2 個方案 → 評估權衡 → 選擇最佳並記錄理由
4. **POC + demo 盤點**：掃描 `poc/**/*.py`、`demo_*.py`、`scripts/demo_*.py`、`notebooks/*.ipynb`，建立 `{module} → [poc/demo paths]` 映射表

輸出思考筆記（簡短）：
```markdown
## 深度思考筆記
**任務理解**: [一句話]
**方案選擇**: [選了什麼，為什麼]
**實作範圍**: [新增/修改哪些檔案]
**風險評估**: 🟢/🟡/🔴 + 說明
```

### 階段 2：實作計畫

拆解為 Self-Contained Segments，用 TaskCreate 建立任務清單，按順序逐一執行。

### 階段 3：自主實作

- **Edit 優先**：修改現有檔案用 Edit，新檔案用 Write
- **Read before Edit**：每次編輯前先讀取最新內容
- **Write 降級**：Edit 失敗兩次後改用 Write 整檔覆寫
- **遵循 rules**：遵守所有 `~/Github/ai-guide/rules/`

### 階段 4：驗證

每段完成後：
1. 語法檢查
2. Import 檢查
3. `uv run pytest <test_file> -v`（背景跑）
4. **POC/demo 驗證**（強制）：查映射表，若模組被 POC/demo 引用 → `uv run python <path>`

### 階段 5：收尾

1. `uv run ruff check --fix . && uv run ruff format .`
2. 全量測試（**用專案命令**如 `make test`，非 bare `uv run pytest`；完成閘門見 [build.md](../implement/SKILL.md) 階段 3）（背景跑）
3. POC/demo 全量驗證
4. **Agent Review Cycle**（見下方）
5. instruction 檔同步檢查（AGENTS.md 為主，legacy CLAUDE.md）
6. 移除除錯用程式碼
7. **/audit-test checkpoint**（見 [audit-test](../audit-test/SKILL.md)）：跑 `/audit-test`（Diff Audit）。重點看域 2 的消費端路徑證據（新 public 參數路徑、整合器型真實邊界）與覆蓋查詢（registry 接線）。缺口不得帶進 /commit。用戶不在場時，這是「單元全綠但接線/邊界沒測」隱性 regression 的唯一機械化閘門。
8. **任務級整合路徑檢查**（非 `/implement` 任務；若變更含新 callable 參數/注入點 → `rg "<新參數>=" tests/` → 0 hits 必須補消費端整合測試，見 [build.md](../implement/SKILL.md) 階段 2）
9. **紅線跳過覆盤**：盤點任務過程中跳過的紅線操作（見 [autonomous-execution](../autonomous-execution/SKILL.md) Don't-Self-Decide Boundaries 🔴 紅線段），寫入 completion report「🔴 紅線跳過清單」段。半夜自主跑時不阻塞、不語音通知——早上靠此覆盤段判讀任務是否因紅線而半完成。
10. **寫 STATE.md Last session 觀察**：**若本 session 有轉向 / 卡點觀察**，把卡點 / 轉向 / 下次起手點寫入 repo root `STATE.md`（覆寫非累積；寫入步驟 + A↔C negative guidance 見 [state-md-write](../_common/state-md-write.md)）。
11. 生成摘要報告——遵循[結論先行原則](../_common/conclusion-first.md)：先講做成了什麼與下一步，id／代碼為附註

#### Agent Review Cycle

**Writer/Reviewer 分離**：用戶不在場，Agent Review 是唯一的品質閘門。review 執行預設（force 獨立 / 風險 profile 配置 / model 預設 / 三 lens）見 [review-engine](../review-engine/SKILL.md)「review 執行預設」——**context 配置由風險 profile 推導，不按 max-agents 填滿**（並發容量＝上限非配額）；開發流程任務（委派 `/implement`）的 review 接線＝**邊界觸發**段級 review＋全弧獨立 review（普通中間段不觸發段級——語義單一源＝[implement](../implement/SKILL.md)「段落收斂」）；三 lens（① fresh/clean + ② intent/UC-anchored + ③ correctness）完整流程見 [agent-review-cycle.md](../_common/agent-review-cycle.md)。

#### 主 LLM — /judge-review

用 Skill tool invoke `judge-review`，傳入**所有 agent 的 review findings**（合併；**含 coverage**——各軸完成／未驗＋evidence ref，欄位語義見 [workflow-review-pattern](../_common/workflow-review-pattern.md)「帳本 header identity」的 scope／review_profile／coverage 三欄）。評估每項：✅ 採納 / ❌ 不採納 / ⚠️ 需確認。

#### 主 LLM — Apply Changes

根據 judge-review 的 ✅ 採納清單修改 code。修改完跑 `ruff check --fix && ruff format`。

---

## 自主授權形態（user 原話授權時）

- **顧問共識授權**：「有共識就做，不用我同意」→ **user 已點名的顧問參與者**共識＝動工 gate（5.3 仍須 user 點名，見 [model-routing](../model-routing/SKILL.md)）；仍受紅線／黃線約束，commit 仍人 gate（見 [autonomous-execution](../autonomous-execution/SKILL.md)）
- **對抗驗證／交卷互改**：review 段可用多家族各自審查→互相討論→歸納修正方向；難題位可用對抗驗證——兩者皆需 user 原話授權（睡前授權內含「用些對抗驗證」即算）

## Agent Spawn 規則

Agent prompt 開頭加上 /rules-reminder 規則摘要：
`#` 是毒藥、`$` 是禁區、`rg/fd` 取代 `grep/find`、`uv run` 是王道、`sed` 是地雷、繁體中文、獨立同發、先 Read 再改

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始深度工作"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「深度工作完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```

---

## 使用範例

```bash
/deep-work 實作用戶認證模組，包含 JWT token 生成、驗證、刷新機制
/deep-work docs/execution-plan.md
/deep-work 重構 data_loader.py，將 CSV 和 Parquet 載入邏輯分離
```

---

## 執行約束

### 強制
1. 動手前先充分思考
2. 核心邏輯必須有單元測試
3. 實作後執行 `uv run pytest` 和 `uv run python demo`
4. 自主決策必須記錄理由

### 禁止
- ❌ 交出半成品就停
- ❌ 遇到錯誤就放棄
- ❌ 使用 `sed` 修改程式碼
- ❌ 多行 `python -c` 中使用 `#` 註解
- ❌ 使用 `timeout`/`gtimeout`/`PYTHONPATH`

### 遵循的 Rules
- `python-standards.md` — Python 規範
- `code-edit-constraints.md` — 編輯約束
- `quality-constraints.md` — 品質約束

---

## 與其他命令的協作

**自主可調度**：`/execution-plan`（無 EP 時 deep-work 任務中自主產，非 user 前置）、`/implement`、`/post-build`（pipeline 預設終段——收尾鏈編排）、`/code-review`、`/ep-review`、`/ep-validate`、`/audit-test`
**後續**：`/commit`（等 user 確認——自主模式不豁免 commit consent）→ `/instruction-sync`
**接續/換手**：`/at`（跨 session reset 接續）、`/handoff`（跨 provider 交接）

**收尾前觸發檢查（AIR-131——在 commit 判定前執行，codex finding：宣告式掛點不構成 orchestration）**：
1. **控制面變更弧**：consumer-dry-run corpus 四型必跑（契約見 [consumer-dryrun-corpus](../_common/consumer-dryrun-corpus.md)）；每季保底 due-check＝查季內弧結算有無 dry-run 記錄（last-run evidence＝弧結算紀錄），無 → 本弧補跑 fresh-agent 演練；跳過＝弧結算顯式記降級
2. **arc-risk threshold 命中**（Heat Warm/Hot、escaped Critical——聚合源 [corrections-weekly](../corrections-weekly/SKILL.md) Heat 段）→ `/code-review --reheat`（升溫弧審查：scope/lanes/cadence 見 code-review --reheat 段）

> **Agent Review Cycle 已完成。** 可直接 `/commit`；如需額外審查可跑獨立 `/code-review`。

**搭配 `/goal`**：`/goal all TaskCreate tasks completed, uv run pytest exits 0, ruff clean, mypy clean, all demos run`（收尾前觸發檢查見上——AIR-131）
