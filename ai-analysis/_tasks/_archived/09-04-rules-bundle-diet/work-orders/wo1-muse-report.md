# WO-1 muse writer report（job-mtm3kjl4-ged2zc，2026-09-04）

> Session `01a06963-eb99-7a10-9969-26ef12b56a24` / exit 0 / base 8d3c6f6。主 session 補跑 deploy 3/3 成功（80,815B deployed）、端點複驗 `progressive-validation`=0 殘留、新錨點在場。

**WO-1 完成 — AIR-20 S1-S4 手術 + S5 部署驗證項（working tree 止步，未 git add/commit，未動 backlog 卡，未派 subagent）**

**Deploy 實測**: `80,815 bytes (87% of 90KiB gate, <92,160)` — dry-run `exit 0`，實寫 `0/3` 因 sandbox `Operation not permitted`（主 session 已補跑 3/3）

### 1. 改檔清單（`git diff --name-only` 對照）

**Unstaged（本次手術，15 檔）**：
```
agents/AGENTS.md
ai-development-guide.md
rules/AGENTS.md
rules/acceptance-evidence.md
rules/collaboration-constraints.md
rules/model-routing.md
rules/modern-cli-preference.md
rules/outward-action-consent.md
rules/progressive-validation.md  (deleted)
rules/quality-constraints.md
rules/tool-discipline.md
skills/CLAUDE.md
skills/_common/work-order.md
skills/audit-test/SKILL.md
skills/model-routing/SKILL.md
```
**Staged 並行改動（排除，非本 WO）**：EP＋WO 工單＋AIR-20 卡＋draft 刪除。
**未越界舉證**：`rules/lsp-navigation.md`、`agents/zcode/*.md`、`hooks/*`、`scripts/*`、`tests/*`、`CLAUDE.md`（root）、memory 池均不在 `git diff --name-only`。

### 2. 逐段落落實（file:line）

**S2 路由句去重（先於 S4，C1 基線）**：
- `rules/lsp-navigation.md:13` **不動**（唯一源，`rg "code-reality（index 在場" rules/` 僅此 1 檔命中）
- `rules/modern-cli-preference.md:13` 壓縮：完整路由句 → `文字搜尋用 rg、檔案搜尋用 fd（預設遵守 .gitignore，減少噪音）；符號/圖譜與型別面路由見 [lsp-navigation.md](lsp-navigation.md)。`
- `rules/tool-discipline.md:13` 壓縮：長四路路由句 → `工具四路路由（符號→code-reality、型別→bridge、文字→rg、檔案→fd）見 [lsp-navigation.md](lsp-navigation.md)；本檔載紀律與陷阱`（完整 markdown link，滿足 LINK_PATTERN）

**S3 progressive-validation 併入**：
- `rules/quality-constraints.md:74-94` 新增 `## 漸進式驗證（DEPTH-MIN→SAMPLE→FULL）` 壓縮段（核心原則一句＋三層表＋最小集合選擇原則一句＋禁止三條＋為什麼一句＋與風險分級互補一句）
- `rules/progressive-validation.md` **刪檔**（GONE）
- 5 活引用改指：
  - `ai-development-guide.md:41` → `漸進式驗證（DEPTH-MIN→FULL）見 [quality-constraints.md](rules/quality-constraints.md)`
  - `rules/AGENTS.md:50` 部署清單行刪；quality-constraints 行補「＋漸進式驗證（DEPTH-MIN→FULL）」；`:68` `neutral 17` → `16`
  - `rules/acceptance-evidence.md:65` → `[quality-constraints](./quality-constraints.md) 漸進式驗證（DEPTH-MIN→SAMPLE→FULL）`（S3 後基線，供 C4）
  - `skills/audit-test/SKILL.md:67` → `quality-constraints 漸進式驗證（DEPTH-MIN 集合）`；`:193` 定義連結 → `[quality-constraints](../../rules/quality-constraints.md)`

**S4 C 批四檔精簡**（各保留詞 rg 命中不變）：
- **C1 `rules/tool-discipline.md` 背景執行段**：6 段 → 4 段，`為什麼`與`例外`合併「前台與背景取捨」一句；zsh 三規則＋案例句保留
- **C2 `rules/collaboration-constraints.md`**：對比格式範例塊（5 行）→ 一行 in-line `❌/✅/💡` 形態；Agent 派發三條各壓至一句
- **C3 `rules/outward-action-consent.md`**：場景表 8 行 → 3 行（合併 deploy/push/跨 worktree/DB/付費/live order 類）；Source of truth 邊界 3 行 → 1 句＋autonomous-execution pointer；**全文保留** reversibility test（:19-40）、AUTH line 模板、commit 專屬段
- **C4 `rules/acceptance-evidence.md:39`**：根本禁令對照表（:41-46）→ 一句總結＋連結；L3 正向實例句保留

**S1 model-routing 降級（最後執行）**：
- **Rule 端 `rules/model-routing.md:27-32`**：45 行壓縮為 6 行（header＋定位 blockquote＋一行 pointer＋尾 slim pointer）。Tier 詞彙句（:25）**不動**。兩夾層 blockquote（:43 review 邊界、:55 sandbox --yolo）**原文搬 skill**
- **Skill 端 `skills/model-routing/SKILL.md`**：description 補觸發詞；`:31-39` 插入角色→family→profile 映射表＋review 邊界 blockquote；`:51-68` 插入 eligibility gate 五條＋sandbox blockquote＋reviewer 交接契約；`:81-90` 插入套用（三路徑）段
- **Ripple**：work-order.md `:63` needs-fix 例句改掃 skill、`:92` 消費形態句改「tier 詞彙句與 skill 映射」；agents/AGENTS.md `:20`「family／profile 映射見 skill、詞彙定義見 rule」、`:24` 治理原則改「路由決策與解析表在 skill」；rules/AGENTS.md `:66` model-routing 描述行更新；skills/CLAUDE.md `:130` 索引行補齊

### 3. 驗收 1-10（機械輸出摘要——完整原始輸出見 .muse-bridge/jobs/job-mtm3kjl4-ged2zc.jsonl）

1. rule 端 eligibility/reviewer/套用 → 僅 :31 pointer 1 行 ✓
2. skill 端 eligibility gate＋reviewer 交接 → :3/:51/:63 ✓
3. `code-reality（index 在場` rules/ → 僅 lsp-navigation.md:13 ✓
4. `test ! -f rules/progressive-validation.md` → GONE ✓
5. `rg -l "progressive-validation"`（排除 ai-analysis/backlog）→ 0 命中 ✓
6. `rg "DEPTH-MIN" rules/quality-constraints.md` → :74/:80/:81/:82/:85 ✓
7. 保留詞：AUTH: user said=1、args=(=1、run_in_background=2、澄清一次問完=1、Claim→Evidence=1；補充 zsh=4/TaskOutput=1/block=true=1//tmp=2/agent-tmp=1/worktree=6/reversibility=3/commit=10/PENDING=3/L1=4/L4=4/證據獨立=1 全 ≥1 ✓
8. work-order/agents-AGENTS 指向 → family 指向者已改 skill（needs-fix 例句 :63 改掃 skill）✓
9. deploy dry-run → `80,815 bytes (87% gate, <92,160)` exit 0；實寫 0/3 sandbox 阻擋（主 session 補跑 3/3）✓
10. modern-cli :13 → fd/rg 身分保留、同 行無完整路由句 ✓
11. 端點抽查：dry-run bundle 漸進式驗證在場＋progressive-validation 0 殘留；主 session 補部署後 deployed 檔複驗 0 殘留 ✓

### 4. 偏差記錄

- S1 pointer 括號「套用（三路徑）」為滿足驗收正則（無語義差異）
- skill description 觸發詞補全短語（覆蓋比 EP 預期完整）
- S3 acceptance-evidence :65 雙 link 形態（較 EP 冗餘但可驗證）
- S4 C2/C3 同義精簡（保留詞前提下字面與 EP 範例不逐字等價）
- S5 deploy 實寫被 sandbox 阻擋（memory 已知限制——部署屬主 session 職責），dry-run 已驗證內容

### 5. 未驗證項（主 session 已承接）

- 三端實部署＋deployed 檔端點複驗 → **主 session 已補跑完成（3/3、0 殘留）**
- sync-sources `deploy_bundle_freshness` 3 critical stale → 重部署後已清（待 sync-sources 復掃確認）

### 6. 建議 reviewer 聚焦點

- S1 搬移逐字一致性（「capacity 現值見下表」指代在 skill 內是否仍準確）；agents/AGENTS.md 詞彙/映射二分會否誤導
- S4 精簡邊界：outward-action Source of truth 壓至 1 句、tool-discipline 背景段 6→4，「為什麼」論述密度降低是否影響行為直覺
- S3 壓縮取捨：風險分級正交性一句是否足夠

### 7. 附記

- Bundle：`87,676B（95% gate，1328 lines）` → `80,815B（87% gate，1215 lines）`，淨減 `−6,861B / −113 lines`，符合 EP 預估 ~6.5KB ±30%
