---
harness-scope: meta
---

# Rules 層指令

rules/ 是 ai-guide 的行為規範庫。**Claude 與非 Claude 的 rules 載入架構不同**（成因：rules auto-load 是 Claude 獨有功能，非 Claude 沒有）：

- **Claude 端**（雙路徑）：`~/.claude/CLAUDE.md` 是檔案 symlink → `ai-development-guide.md`（guide）；`~/.claude/rules/` 是**目錄 symlink** → `rules/`（rules auto-load，每 session 全載）。repo 改 → 即時生效，**不需 deploy**。
- **非 Claude 端**（ZCode/Codex/Muse，單檔）：無 rules auto-load 機制 → 靠 `scripts/deploy_agents.py` 把 **guide + neutral rules 拼裝成單一 AGENTS.md**（snapshot），部署到 `~/.{zcode,codex,config/muse}/AGENTS.md`（muse＝machine-wide user rules，probe 實證 always load；專案 AGENTS.md 衝突時贏）。改 rule 後須重跑 deploy 才同步。

## 部署紀律（authoring 驗證與正式部署分開）

**Authoring**：在隔離 worktree 編輯此目錄任一 rule 後，先執行無部署寫入的驗證：

```bash
uv run python scripts/deploy_agents.py --dry-run
```

**正式落地**：依 instruction-writing skill「落地前審查閘」完成風險分類、所需獨立審查與四欄回執，並取得 [outward-action-consent](outward-action-consent.md) 要求的授權後，才可 merge canonical 或 deploy；dry-run 成功不授予落地權。正式部署須從 canonical 的已接受 revision 執行 `uv run python scripts/deploy_agents.py`，並確認該來源內容與審查回執一致（含 working tree，不能只看 HEAD）；不得從未驗收 authoring WT 部署。

→ 正式部署重新 bundle guide + neutral rules → 寫入 `~/.{zcode,codex,config/muse}/AGENTS.md`（非 Claude 端的 rules 唯一來源）。
→ Claude 端不需 deploy，但 canonical merge 會更新 `~/.claude/rules/` symlink 指向的內容，因此同樣先過落地閘。
→ 注意：deploy 會將非 Claude 端的 AGENTS.md 從 symlink（live-sync）轉為 generated snapshot — 改 rule 後需重跑 generator 才同步。
→ 投影軸（AIR-85）：rule frontmatter 三鍵 `bundle-projection: pointer`＋`pointer-target`＋`bootstrap-pointer`＝非 CC bundle 投影——body 不進 bundle、作者 pointer 句逐字投影；deploy 全域 preflight（repo source＋`~/.agents/skills` runtime 可達）fail-closed、identical 重跑零寫入；`paths:` 是 CC runtime 軸，deploy 不解析（三軸分離）。
→ redeploy 後若本 session 續作，依 [context-management](context-management.md)「Session freshness」refresh/reset 後再繼續（刪除/反轉弧重讀不足，須 reset＋恢復主題材料）。

### 尺寸 gate 與截斷線（bundle 上限）

非 Claude 端 AGENTS.md 受 harness 截斷線約束；警告與合併方式各端不同，不能只驗全域 bundle：

- **ZCode 實測**：截斷線 **102,400 bytes（100KiB）**，硬編碼於 `zcode.cjs`（`hIn=100*1024`，讀前 100KiB bytes 再 UTF-8 decode），**無任何 config 可調**（官方文檔亦未記載）。載入模型：只讀 user 全域（`~/.zcode/AGENTS.md`）+ workspace（cwd 往上至 project root 第一個 `AGENTS.md`）**兩檔**，各檔獨立 100KiB 預算；**不展開 `@import/@include`、不掃子目錄、不依任務類型選規則檔**。
- **Muse delegation startup**：全域＋專案指令及包裝共用 **65,536 bytes**，超限會警告並截斷。部署器的 Muse global-only gate 留專案空間，但不保證任意 workspace 可載入；須在實際 workspace 驗合併量與 loader 警告。三端均保留全部 neutral rules；不可因 Muse 家族/headless 就假設它不改 instruction、不查符號或不需 context 紀律。任務是否允許寫入/委派由工單與可用工具決定。
- `deploy_agents.py` 的各端 size gate 是唯一數值源（ZCode/Codex 用 `BUNDLE_MAX_BYTES`，Muse 用 `MUSE_USER_BUDGET`＝36KiB 自限——64KiB 共享線內留專案層＋framing 緩衝，見 `resolve_targets`），超限拒絕該端部署。撞線先精煉重複與可推導內容，或將 on-demand 細節下沉既有 skill；rule 保留執行核心與觸發 pointer，禁用整檔排除掩蓋尺寸問題。
- 歷史教訓：部署版 141KB 時代，尾部 8 條 rules（含 tool-discipline、quality-constraints）落在截斷區靜默失效（2026-08-20 實證事故：spawn 背景規範沒載入 → 前景 spawn 被 user 插話殺掉）。**規範存在 ≠ 規範載入**。

### 部署驗證義務（deploy 跑通 ≠ 部署完成）

dry-run 只驗 authoring 產物，不能要求 deployed 檔已含尚未落地的修改。正式 deploy exit 0 也**不證明「各端讀到正確內容」**；正式落地後必須獨立驗證**每一端**（架構不同 → 驗證方式不同）：

- **非 Claude 端**（rules 唯一來源是 bundle）：`rg` 抽查 deployed AGENTS.md（如 `~/.zcode/AGENTS.md`）含新/改 rule 的 section marker + 關鍵內容；排除應排除的 claude-specific rule。**漏驗這端 = 非 Claude LLM 讀不到該 rule**（無其他載入途徑）。
- **Claude 端**（rules 來源是 `~/.claude/rules/` dir symlink）：`rg` 抽查 `~/.claude/rules/<rule>.md`（透過 symlink 讀 repo）含完整內容 — 瘦身後的 claude-specific rule 仍保留 Claude 專屬段。
- **多端一致性（per-target）**：逐端與 `expected_bundle_for(target)` 重建 bytes 比對；目前三端相同，但只比部署檔彼此 hash 抓不到「三端一起過時」。idempotence 是同端重跑前後 hash 相同；純簽名重構才要求改前/後 bundle 不變。
- **機械替代（部署新鮮度）**：`/sync-sources`（`check_single_source.py` REGISTRY `deploy_bundle_freshness`）逐 target 用 `expected_bundle_for` 重建並 byte 比對，stale 即 critical。真實案例：部署落後多條 rule，靠外部 session 才發現。此檢查只涵蓋非 Claude 三端；Claude 另驗 symlink 內容。

禁止：只看 deploy stdout 的 `[OK]` 就宣稱部署完成；只驗單端就推論其他端正常。

## harness-scope 分類

frontmatter `harness-scope:` 是**單一真相源**（每條 rule 自帶）。`deploy_agents.py` 掃 frontmatter auto-discover — 新增 rule 只需加 frontmatter、**不需改 script**。下表是 derived overview：

| rule | scope | 說明 |
|---|---|---|
| `design-thinking` | 🟢 neutral | 決策與架構核心（行為、證據、直接／間接後果；決策方法見 deep-thinking，結構觸發表見 arch-thinking）|
| `quality-constraints` | 🟢 neutral | crash-only / fail-loud / 消費端驗證＋漸進式驗證（DEPTH-MIN→FULL） |
| `acceptance-evidence` | 🟢 neutral | L1-L6 證據階層 / A/B 軸 / Claim→Evidence→Trust（深層理論：Runtime Invariant、Intent Drift、filter trap 在 acceptance-evidence skill）|
| `must-execute-before-complete` | 🟢 neutral | 改了要跑、非靜態檢查 |
| `collaboration-constraints` | 🟢 neutral | anti-sycophancy / 事實查證 |
| `_ai-behavior-constraints` | 🟢 neutral | single-source drift 修改紀律＋元資訊禁止 pointer（行為表在 instruction-writing skill）|
| `instruction-writing` | 🟢 neutral | instruction file 撰寫核心（完整規範在 instruction-writing skill）|
| `python-standards` | 🟢 neutral | Python 標準（language；Python 專案適用）|
| `context-management` | 🟢 neutral | context 重置＋想法即時落盤（durable checkpoint）＋STATE.md pointer＋memory 生命周期 pointer（六問/寫入點規範在 memory-audit skill「寫入端紀律」；Claude 機制用括號註）|
| `outward-action-consent` | 🟢 neutral | outward action 需用戶授權（commit / deploy / push / send / live order；reversibility test + AUTH line）|
| `llm-output-convention` | 🟢 neutral | print/Logger 雙通道核心——state transition 定義＋Namespace（tag 表/細則在 llm-output-convention skill）|
| `symbol-query-routing` | 🟢 neutral | cr-first 符號/型別查詢路由＋任務啟動 gate（LSP operation 速查表、反例群、Agent prompt 模板、載體對照、staleness 處置在 symbol-query-routing skill）|
| `modern-cli-preference` | 🟢 neutral | 工具分工指針（路由權威＝symbol-query-routing rule；陷阱目錄在 modern-cli-preference skill；Claude 權限段括號註隔離）|
| `tool-discipline` | 🟢 neutral | 通用工具紀律（uv run / pipe-exit / 禁 sed / pytest 背景跑 / 視覺判讀 agent 路由——禁主 session 讀圖；Edit 失敗階梯、zsh flags 邊界、Read 紀律案例在 tool-discipline skill）|
| `edit-discipline` | 🟢 neutral | 通用編輯紀律（SRP/DIP/變更紀律/禁混合寫法）|
| `bash-hard-rules` | 🔴 claude-specific | Claude 權限偵測（`#` 換行註解 / `$` 展開 / 陣列靜態攔截）|
| `code-edit-constraints` | 🔴 claude-specific | Claude Edit/Write 工具 API（old_string 精確匹配 / 多位元組備註；失敗處置指針 tool-discipline）|
| `model-routing` | 🟢 neutral | 跨 harness subagent 派工路由骨架（WorkUnitContract→candidate→DispatchPlan precedence＋hard invariants——no-silent-downgrade／token provenance／effective effort／model fact single source；glossary／resolver 協議／解析表在 model-routing skill、供給事實在 `skills/model-routing/catalog.toml`） |
| `bridge-dispatch` | 🟢 neutral | delegate-bridge 委派路徑紀律（registry pin 唯一源／caller surface 合法入口對照／禁第二 pin；webgpt 大內容與 dispatch⇄collection 完整模式在 bridge-dispatch skill，事故脈絡在 delegate-bridge repo AGENTS.md「Caller dispatch discipline」節） |

**default = neutral**：通用知識預設跨 harness — 新 rule 不標 scope 即進 bundle。Claude 專屬 rule 需顯式標 `harness-scope: claude-specific` 才被排除。`deploy_agents.py` 的斷 ref 檢測會阻塞任何 neutral rule 引用 claude-specific rule 的 deploy（強制修 ref 或重劃 scope）。已下沉 skill 的 rule（self-consistency 五維檢查、context7 MCP 查詢——內容在 instruction-writing skill／context7 skill；design-thinking 輸出格式、model-routing 解析表、llm-output-convention 細則、modern-cli 陷阱目錄等同模式分層）。

## Rule 寫作原則

- **可驗證**：rule 必須含可機械檢查的標準（沒有驗證的規則是噪音）
- **signal 導向**：保留從程式碼猜不到的知識（設計理由、失敗教訓），移除可推導內容
- **harness-scope 自描述**：每條 rule 的 scope（neutral/claude-specific）標在上表，新 rule 需歸類

## Neutral rule 中性化規範

> **適用**：`harness-scope: neutral` 的 rule。這類 rule 會被 `deploy_agents.py` 打包進 bundle，部署到 ZCode / Codex / Muse 三家非 Claude harness。寫作時必須假設讀者**不是 Claude** — 不會展開 `@`、不能用 slash command、沒有 `~/.claude/rules/`、沒有 `CLAUDE.md wrapper`。

### 禁止（非 Claude 讀者會斷裂）

| ❌ 禁止 | ✅ 改成 |
|---|---|
| 裸 slash command `/implement` `/commit` `/execution-plan` | 流程名 `build` / `commit` / `execution-plan`（無 slash）；Claude 端原文放 `(Claude: /implement)` 括號註 |
| `@~/...` 或 `@/path` transclusion | 一般 markdown link；`@` 僅在描述 Claude 機制時用，並標明「Claude 端」 |
| `../skills/xxx/SKILL.md` 跨域 ref | 描述該 skill 名稱（slash `/xxx` 語意跨 harness 有效）；或泛化為「跨 harness 機制，路徑從略」 |
| 未標註的 `CLAUDE.md wrapper` | 「Claude 端 CLAUDE.md wrapper」或「instruction 檔（AGENTS.md source；Claude 端 CLAUDE.md wrapper）」 |
| `~/Github/ai-guide/rules/xxx.md` user-specific 絕對路徑 | repo-relative markdown link `[xxx.md](xxx.md)`（同目錄）或 `xxx.md`（純名 + 「source 在 ai-guide repo」） |
| 「Claude 端 `~/.claude/rules/` symlink auto-load」作為主要描述 | 標準載入機制註記（見下方）|

### 標準載入機制註記

載入機制集中在 guide 與本檔；neutral rule 不需每檔重複。確需描述 Claude 特例時可用：

```
> **載入機制**: 本檔 source 在 ai-guide repo `rules/`；各家 harness 經全域 guide 部署載入（Claude 端另有 `~/.claude/rules/` symlink auto-load）
```

### 通用模式：括號註隔離 Claude 機制

當內容原則通用、但需提及 Claude 端具體機制時，用 `(Claude: ...)` 括號註隔離：

```markdown
# ✅ 正確：原則為主，Claude 機制括號註
- **任務切換時重置 context**（Claude: `/clear`）
- **commit 需用戶確認**（完整流程見 commit 命令文檔；Claude: `skills/commit/SKILL.md`）

# ❌ 錯誤：Claude 機制作為主要指令
- **任務切換用 `/clear`**
- **完整流程見 `../skills/commit/SKILL.md`**
```

括號註**不是殘留** — 它是策略：讓 Claude 讀者讀到完整的 Claude 機制資訊，同時讓非 Claude 讀者知道「這是 Claude 特例，我有對應機制即可」。

### 通用模式：跨 harness 載體對照（當工具呼叫方式跨 harness 不同時）

當一個概念跨 harness 通用、但呼叫載體不同時（典型：LSP），用**對照表**表達，而非把某家 harness 的呼叫語法寫成主體。範例見 symbol-query-routing skill「跨 harness LSP 載體對照」段。模式：

```markdown
### 跨 harness X 載體對照

| harness | 機制 | 呼叫方式 |
|---------|------|---------|
| Claude | ... | ... |
| ZCode | ... | ... |
| Codex | ... | ... |
```

判準：一個概念跨 harness 通用、但「怎麼呼叫」各家不同 → 用對照表；若概念本身某家沒有（如 hooks），那不是載體差異而是 scope 差異 → 整段放 claude-specific rule 或括號註。

### 機械檢查清單（review 用）

新增/修改 neutral rule 後，以下 grep 應無命中（括號註內除外）：

```bash
# 裸 slash command（應只在 (Claude: ...) 內）
rg '`/[a-z][a-z-]+[ `]' rules/*.md | rg -v 'Claude[:：]'

# @ transclusion
rg '@~/|@\.\./|@/[a-z]' rules/*.md

# 跨域相對路徑
rg '\.\./(commands|skills)/' rules/*.md

# 未標註的 CLAUDE.md wrapper
rg 'CLAUDE.md wrapper' rules/*.md | rg -v 'Claude 端'

# user-specific 絕對路徑
rg '~/Github/ai-guide/' rules/*.md
```
