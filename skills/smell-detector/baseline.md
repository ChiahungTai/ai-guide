# baseline mode — 廣角盤點完整規格

> 本檔是 [smell-detector](SKILL.md) **baseline mode**（`/smell-detector --baseline <dir>`）的完整規格。mode 分工與測試 smell 三類見 [SKILL.md](SKILL.md)。

> **Purpose**：一次性全面審查每個目錄的核心檔 + 建立 baseline（深審 + invariant CI-guarded）+ 架構 onboarding（快速掌握整個 codebase）。目標：foundations 審一次 → 後續 AI coding 改動是非核心 delta → `/code-review` 輕審即可。
>
> **核心理念**：**人類產出格式優先**（genesis 教訓——前次設計失敗都在重造 AI 機械、欠投資人類產出 → token 牆 → 「人類不會看」）。本 mode 把設計預算花在**人類可讀產出**（廣到精細 + 受眾分離 + emoji-first Mermaid），AI 機械（tiering/graph/渲染）委外給既有 skills。
>
> **與 zoom mode 的分工**：zoom（同 skill 預設）質疑既有 code 是否該存在（放大鏡）；baseline 盤點既有穩固度（守護既有）——正交，見 [zoom.md](zoom.md) 定位段。「人類產出優先」教訓為兩 mode 共同設計依據。
>
> **vs `/code-review`**：code-review = change-driven（pre-merge diff）；baseline = baseline-sweep（既有 code + 週期）。正交不合併。

## When to use
- 首次全面審某目錄的核心（不變式 + 結構 + 結構債 + coverage shape）
- 週期 re-review（`--stale` 抓審完後 drift）
- 架構 onboarding（`--architecture` 產 codebase 全圖）
- **不用於** change review（用 `/code-review`）；針對性質疑存在（用 zoom mode）

## Argument

| 用法 | 行為 |
|------|------|
| `/smell-detector --baseline <directory>` | sweep 一目錄（module 名如 `common` 或路徑 `mosaic_alpha/common`）→ 產 4 檔 + 提取觸及的跨 folder invariant |
| `/smell-detector --baseline`（無 dir） | 印 status + 用 code-reality graph 目錄級消費者聚合（`graph_query communities` 對賬）挑下一個 pending core 目錄（或問） |
| `/smell-detector --status` | 印 `ai-analysis/codebase-review/README.md` 狀態表（reviewed/pending/stale + tier） |
| `/smell-detector --stale [dir]` | `git diff <last-reviewed-sha>..HEAD -- <dir>` → 標 stale → re-sweep。無 dir = 全 reviewed 目錄掃 |
| `/smell-detector --architecture` (`--arch`) | (重)產 codebase 級 `ai-analysis/codebase-review/architecture.md`（code-reality graph onboarding 全圖） |
| `/smell-detector --invariants` | 重刷 `_invariants/`（既有：刷新結構部分保留 design_lessons;新:生成 + 標 design_lessons 待人補） |

> 輸出目錄沿用 `ai-analysis/codebase-review/`（project-side 既有 baseline 資產不遷移——消費專案的歷史審查資料是 production data，改名不重刷）。

## 起手：graph refresh + stale precheck

> graph 是結構事實來源，但會 drift。**不 assume doc-only drift**（實證：doc/test/chore 混合 commit 也改結構）。

1. `code-reality scip_refs --audit --repo <root>` 看 index/HEAD 對齊（[SRC] 行）。
2. 若不同步 → 語料重生（Python：`pyrefly-index --repo <root>`；Rust：重生 SCIP index——**直呼 repo-pin binary**，rustup proxy 從 any cwd outside the repo 呼叫會靜默降 toolchain；事故實案＝CR plugin skill）→ `code-reality graph_db build --repo <root>`（單一 build 面、冪等、純 producer）。
3. refresh 後才信任 impact/caller/community 結果。engine 缺場 → `[WARN]` + fallback [scan-project](../scan-project/SKILL.md)/LSP（cr-query GATE，**不靜默降級**）。

## 執行模式（直接執行優先，勿過度 workflow）

> **教訓**（indicators/ rollout 實證）：首次用平行 StructuredOutput workflow（6 agents，nested schema + 多 required）→ **6/6 retry-exhausted**（agents 做了 224 tool uses 真實分析但 schema 太嚴產不出，全廢）；改**直接執行（單 session）**→ 一次成。

- **預設直接執行**（單 session）：目錄核心檔通常 ~6 個，§zoom 深審分析 fit 一個 session（common/ + indicators/ 實證）。讀 reference → 讀核心檔 → 真實 `uv run`/LSP/CR graph → 寫 4 檔。
- **目錄極大才用 workflow**（如 50+ 檔；未達此規模仍預設直接執行）：若用，agent 產出是**給主 session 組 4 檔的原料**（非 agent 直接交付）→ 用 **free-text 或極簡 schema**（單層、少 required、optional 多）；**禁 complex nested StructuredOutput**（strict schema 對「產大量結構化分析」的 agent 是 anti-pattern → retry-exhaust，真實分析全廢）。複雜結構交主 session 從 free-text parse。
- 詳見 [agent-workflow](../agent-workflow/SKILL.md)「Subagent 產出格式：schema 嚴格度」。

## Flow（5 步，per directory）

> 廣到精細 + 受眾分離。委託：[arch-thinking](../arch-thinking/SKILL.md)（core/leaf tiering + City Map）+ [cr-query](../cr-query/SKILL.md)（graph facts）+ [illustrate](../illustrate/SKILL.md)（渲染）+ [review-engine](../review-engine/SKILL.md)（severity/confidence only）。

### 1. Profile
- 讀 `<dir>/AGENTS.md`（職責 + 关鍵設計決策 + 可複用基礎設施）。**fallback**：無 AGENTS.md → 目錄名 + top-level README 推導職責 + `[WARN] 無 instruction 檔`。
- code-reality `get_minimal_context` / `list_communities`（找 dir 的 community）＋目錄級消費者聚合（`graph_query communities` 成員對賬或 `rg -l` 反查）。
- `pytest --cov <dir>`（coverage **hint** only，非 verdict）。

### 2. Tier（arch-thinking core/leaf + domain overlay）— smart effort 分配
- **ripple**：`hub_nodes` / `bridge_nodes`（node 級；**mega-cluster caveat** — 排除 `<mega-cluster dir>` blob noise）+ 目錄級消費者聚合。
- **test 軸 = invariant guard 狀態**（guarded / partial / unguarded）— **非 raw coverage %**（coverage 綠 ≠ invariant 守，L2 trap）。verdict 看 invariant 有沒有被測 + assertion 強度。
- **domain overlay**：silent-corruption path 上的檔（shift/i128/cash/時區/volume 張股）無論 dep weight = core。
- matrix → core 深審 §zoom（四段深審，見 step 3）/ leaf behavior-only（每檔至少碰一次 — 抓 stale core/leaf label）。

### 3. Smart scan（依 tier）
- **core**：§zoom 四段深審（I/O 邊界契約：**真實 `uv run` output**（非發明）+ 不變式 + 失敗模式因果敘事 + 可執行驗證指令 + `#L` 跳行）+ Test Map + Heavy Checklist（含補償邏輯反向搜）。
- **leaf**：behavior-only（docstring + has-test，每檔碰過）。
- coverage × hub 熱點交叉（untested hotspot）機械補充審查佇列。

### 4. architecture.md（illustrate + code-reality graph）
illustrate 渲染 5 張圖：**emoji-first，color 僅 accent 每圖 1-3 節點**：
1. 內部分層（依賴向內）
2. keystone fan-out（common/此目錄 → 消費者鏈；**codebase 統計數字（importer/模組/test/graph node 數）人類檔顯示用 magnitude**（數十/數百/幾乎全 codebase/上萬），**禁寫精確整數** — 精確數只進 state.yaml（機器）；人類檔寫精確整數必 drift 且零邊際信號（「數百」與「342」對讀者決策等效）。如實計數用於 tiering，計數法目錄級消費者聚合（`graph_query communities` 對賬）/ `rg -l | wc -l`，禁 `rg -l | head` 截斷人工數，見 [modern-cli-preference.md](../../rules/modern-cli-preference.md)）
3. critical path 拓樸（如 single-writer 匯流）
4. invariant flow（cross-folder 消費者，grounded in MCP `callers`）
5. domain overlay 輻射（silent-corruption path）

**Mermaid 約束**（必讀 [mermaid](../mermaid/SKILL.md)）：跨主題安全色 `#3b82f6`（🔵 source）/ `#f59e0b`（🟡 critical）/ `#10b981`（🟢 guard）；**arch 圖禁紅底 `#ef4444`**（刺眼；mermaid 認可紅用於真正 error 節點，但 arch 圖刻意不用 — 子集政策）/ 禁淺 tint / 禁 stroke-only；`fill`+`color` 必同時；classDef ≤ 3；禁 `%%{init}%%`。
**合規檢查**：`rg -i '#dc2626|#b91c1c|#ef4444|#fee|#fdd|#fef|fill:#fff|fill:#ffffff|stroke:#' <dir>/architecture.md ai-analysis/codebase-review/architecture.md` → 0 hits（範圍僅 arch 圖檔，紅留 review.md 標 error 用）；`rg -c classDef <dir>/architecture.md` → ≤3。

### 5. Verdict → 4 檔（受眾分離）
產 `<dir>/{README, architecture, review, state.yaml}`：
- **README**（人入口，5 秒）：目錄定位 + core/leaf matrix（審查重點）+ 看 code 注意 + 廣到精細讀序。
- **architecture.md**（中層圖）：上述 5 張 Mermaid + code-reality graph 事實 + 設計決策。
- **review.md**（精細 §zoom）：core 檔 full §zoom + Test Map + Heavy Checklist + 方法論限制段。
- **state.yaml**（機器，**開頭標「⚠️ 非人類閱讀」**）：verdict / last-reviewed-sha / guarded / gaps / drift_basis / crg_facts。
- 更新 `ai-analysis/codebase-review/README.md` 狀態表。

## graph 整合（conditional — cr-query GATE）
- ripple：`hub_nodes` / `bridge_nodes`（node 級；排除 mega-cluster）
- 優先化：coverage × hub 熱點交叉（untested hotspot）
- invariant 消費者：MCP `callers`（浮現 folder 外）
- 每份 architecture.md 必含 **mega-cluster caveat** 段：community ≠ module boundary（`<mega-cluster dir>` N 節點退化 blob）；用目錄+AGENTS.md 為模組真相。

## Invariant 提取（hybrid 模型 — 防 drift 但保人類脈絡）
> 用戶「command 生成」= 防 **drift**（結構事實過時），**非**丟掉人類設計脈絡。

- **既有 invariant**（已存在 `ai-analysis/codebase-review/_invariants/`）：**保留 hand-written 全部**（含 design_lessons — 從 code/graph 猜不到的糾錯軌跡）。命令只**刷新結構部分**：`golden_set`（MCP `callers` + LSP findReferences）、`guard_test_status`（`uv run pytest <guard>` 驗 pass/fail + assertion 強度）、`cross_folder_consumers`（MCP `callers`）。
- **新 invariant**（sweep 新發現）：命令生成完整 doc，`design_lessons` 欄標 `[待人審補]`。
- **`--invariants`**：重刷既有結構 + 掃新；`--stale`：guard 還在？新 call-site？新 consumer？
- **🔴 Provenance 一致性（多 sub-command 交叉 refresh）**：refresh / sweep 寫入的 provenance 須標**當時**的 graph 狀態錨（以現行自報面取得：查詢 `[SRC]` 行或 `code-reality --version` 嵌入 rev）。若 graph 之後被 refresh（如 `--architecture` 重跑、或下次 sweep 起手 refresh），後跑者須 **re-stamp 所有 provenance** 到新 sha，或顯式標「refresh 對 `<舊 sha>`，graph 現 `<新 sha>`，<code 變/未變> → data valid/stale」。**禁止**讓 _invariants 的 refresh sha 與 architecture/state 的 build sha 靜默漂移（sha-based drift 追蹤是核心價值，provenance 自相矛盾削可信）。

## Output structure（project-side，非 ai-guide）
```
ai-analysis/codebase-review/
├── README.md              # 狀態表 + 廣到精細讀序 + 與 /code-review 關係
├── architecture.md        # codebase 全圖（--architecture 產）
├── _invariants/           # 跨 folder 不變式（既有保留 + 命令刷新結構）
└── <directory>/
    ├── README.md          # 人入口 + core/leaf matrix
    ├── architecture.md    # SA + graph 圖（illustrate 渲染）
    ├── review.md          # §zoom 四段深審
    └── state.yaml         # 機器狀態（非人類閱讀）
```
> Command 是 generic（ai-guide）；state + _invariants 是 **project content**（不准 hardcode 進命令）。

## 🔴 受眾分離 guardrail（最關鍵，勿違反）
> 一個檔案只伺候一個受眾。一檔兩受眾 → 壓縮 token 妥協 → token 牆 → 「人類不會看」（前次失敗根因）。

| 檔 | 受眾 | 形式 |
|---|---|---|
| README / architecture / review | **人類** | 敘事 + 真實 uv run + `#L` 跳行 + emoji Mermaid |
| state.yaml | **機器** | verdict/sha/guarded/gaps/drift（開頭標非人類） |

禁止：state 欄位塞進人類檔；人類敘事壓成 token。

## Reference
- [arch-thinking](../arch-thinking/SKILL.md) — core/leaf tiering + City Map + domain overlay
- [cr-query](../cr-query/SKILL.md) — graph facts 紀律（LSP-vs-CR 分工、GATE、anti-over-reliance、mega-cluster caveat）
- [illustrate](../illustrate/SKILL.md) — B 軸人類 viewport 渲染
- [review-engine](../review-engine/SKILL.md) — severity/confidence（severity/confidence only；baseline 非 review 命令家族，自有 baseline 預設）
- [mermaid](../mermaid/SKILL.md) — 跨主題安全色（產圖前必讀）
- [acceptance-evidence](../../rules/acceptance-evidence.md) — coverage ≠ assertion 強度（L2 trap）
