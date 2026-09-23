---
name: cr-query
description: "Query the code knowledge graph (code-reality engine) correctly. Use when you need structural facts file-scanning cannot give efficiently — blast radius / impact radius of a change, who calls whom (callers/callees), affected execution flows, hub/bridge nodes, module communities, dead code, architecture overview, or token-efficient review context scoping — in a project with a graph (`.code-reality/graph.db`; MCP `code-reality` engine tools, or CLI `code-reality graph_query <op> --repo <root>`). Provides the LSP-vs-code-reality division (symbol truth→code-reality index: Rust=SCIP, Python=pyrefly; types→code-reality-lsp-bridge hover/check_file, .py/.rs-routed; graph ops→graph_query), the assume-present + warn-if-absent rule, and anti-over-reliance (graph = structure, not runtime behavior). Prevents manually re-tracing dependencies with LSP/rg when the graph has them, and inferring behavior/correctness from graph edges."
when_to_use: Fires in a graph-equipped project (`code-reality` MCP engine tools available or `.code-reality/graph.db` exists) when the task needs structural/impact facts — "who calls X", "blast radius of this change", "is X dead code", "hubs/communities", "scope my review to impacted nodes only", EP 撰寫（execution-plan 段落 0 依賴分析）. Load BEFORE manually tracing imports/callers with LSP findReferences or rg. Does NOT fire in projects without the engine (no warn noise). Parallels nt-query (discipline for a tool).
---

# cr-query — Query the code knowledge graph correctly

You're in a project with a **code knowledge graph** — the code-reality engine face over `.code-reality/graph.db` (self-owned schema since 2026-08-27; pure producer graph is the norm — legacy `.code-review-graph/` deleted across all consumer repos in W4/W5, only the retired CRG museum repo keeps a copy by user adjudication). The graph already holds who-imports-whom, call edges, communities, flows. Confusing what the graph gives you vs what LSP / reading code gives you causes two expensive mistakes.

## The one rule

> **Graph shows STRUCTURE, not BEHAVIOR. "A depends on B" ≠ "changing B breaks A" and ≠ "A is correct."**

A graph edge (A calls B / A imports B) is a *static, parse-time fact*. It says a dependency exists — not that it is exercised at runtime, not that exercising it is correct, not that changing B breaks A (A may never hit the changed path). The graph collapses hours of manual import-tracing into one query; it does NOT collapse the judgment of "does this matter, is it correct."

**Corollary — don't extrapolate behavior from one edge.** Runtime behavior splits by branch/config/data; the graph holds the union of parse-time edges, not the runtime path. "A calls B" where B has a config-driven branch does not say which branch runs. When behavior matters, read the code (or run it). Same shape as the one rule — don't describe the runtime whole from a static part.

## Detect the engine — assume present, warn if absent

This skill assumes the project has the code-reality engine. Detect once per task:

1. **MCP tools present** — code-reality engine tools callable (impact_radius / detect_changes / hub_nodes / bridge_nodes / list_communities / architecture_overview / list_flows / affected_flows / semantic_search / get_review_context / get_minimal_context / refs / callers / closure / audit) → engine live, use it. 兩種部署形態共用這組工具名：plugin stdio（ZCode/Claude plugin per-session spawn `code-reality-mcp --stdio`）與共享 HTTP resident（`127.0.0.1:8200/mcp`，選配——服務由 OS 服務層管理，目前未部署、現值以 launchctl 為準）。
2. **Graph DB exists** — `.code-reality/graph.db` in repo root → graph present; if MCP tools absent, use CLI `code-reality graph_query <op> --repo <root>` (see Fallback).
3. **Neither** — engine not present in this project.

🔴 **GATE — assume + warn, do not silently degrade.** A review/planning command that expects the engine (impact/callers/scoping) and finds it absent must emit a one-line `[WARN] graph not available — structural context (impact/callers/flows) degraded; build: code-reality graph_db build --repo <root>`, then fall back. **Silent fallback = the user gets a worse review without knowing why.** Do not block — proceed with the fallback below. **查詢面缺口**（該有的邊/符號不在 graph——如 macro 鏈、動態派發）：在**自己 repo** 的 backlog 開 `[cr-demand]` label 卡（`backlog task create "<缺口>" -l cr-demand -d "<觸發場景＋實證缺口＋期望能力>"`；無 `backlog/` 的 repo 落 pending 家；開卡形態依 kanban-board「開卡 Description 先行」——demand 卡屬 lightweight，至少 desc 標 draft-unconfirmed 待 user 確認）——demand-pull 觸發工具弧（ai-guide roadmap relay 段），不靠工具方猜測。

**EP 撰寫面**（[execution-plan](../execution-plan/SKILL.md) 段落 0 依賴分析——CR 第一消費場景）：index 在場的 repo，EP 每個下游/ripple 宣稱必走 CR 查詢（分層：主 session 與掛白名單的 registry agents 走 MCP——EP 段落 0 research spawn＝registry `cr-research`〔2026-09-01 升級①：sidecar 形態零滲透實證後換軌〕；generic 無白名單 spawn 才以 CLI 清單寫進 prompt——見 execution-plan 段落 0）並在「依賴關係」小節附工具輸出引用（scip_refs 首行 `[SRC]`；graph_query 輸出無 `[SRC]` 行、附完整命令列＋repo root）。**callers 為空是嫌疑不是乾淨**：死路假設（宣稱被觸發、實際無人呼叫——真實案例 `_lazy_populate`）或盲區隱藏消費（字串鍵/meta、動態派發——anti-over-reliance 節）——兩者都以互補腿（`rg "<literal>"`、`hub_refs --hazard`）查證後才可下結論；CR 全綠 ≠ 無 ripple。

**滲透量測**（評估 CR 是否被實際消費；2026-09-01 評估的汙染教訓）：CLI 面計數帶 subcommand 錨——`rg "code-reality (scip_refs|graph_query|hub_refs|impact_radius|snapshot|delta_tour|detect_changes) "`，裸 `code-reality`／裸工具名會誤配檔名與路徑（`test_hub_refs.py`、`~/Github/code-reality` 實證）；MCP 面直接數 `mcp__plugin_code-reality_*` 工具名（零誤配）；排除 code-reality repo 自身 sessions（dogfooding）；歸因窗口＝skill 調用起至下一個 skill 調用。

## 🔴 Shared-server rule — every call carries repo_root

共享 HTTP server 沒有 per-session cwd：`repo_root` 是唯一的 repo 路由鍵。**每個 `code-reality:*` 呼叫都必須帶 `repo_root=<當前 repo root 絕對路徑>`**。

省略的失敗形態是**自信假陰性**而非報錯：server 落到自身 cwd 的空 graph，回 `"graph is empty"` + not_found（2026-08-24 spike 實證：NT graph 近 8 萬節點下查 `InstrumentId` 回空）。查詢結果出現 "graph is empty" 指紋＝漏了 repo_root，補上重試。server 無 session/workspace 綁定（repo 是參數非拓撲），所有端一律顯式帶上。

## LSP vs code-reality — the division (core)

Two facts backends, complementary not competing:

| You need | Tool | Why |
|---|---|---|
| Symbol **definition / signature / type** | **code-reality-lsp-bridge** `hover`（.py→pyrefly、.rs→rust-analyzer 副檔路由；bridge 缺場退 LSP `hover` / `goToDefinition`） | Live, precise, ~50ms（熱態） |
| **Single-symbol** references (who uses X) | **LSP** `findReferences` | Precise for one symbol |
| Symbol **callers** (direct) | **code-reality** MCP `callers`（sites 級）OR LSP `incomingCalls` | Either; CR if traversing further（`closure`） |
| Symbol **callees** (X 呼叫誰) | LSP `outgoingCalls`（CR MCP 無 callee 面；CLI `hub_refs` 有 callees 目錄面） | — |
| Symbol refs/defs（trait 消歧；Rust＋Python） | **code-reality** MCP `refs`／CLI `scip_refs`（Rust＝SCIP、Python＝pyrefly index；`[SRC]` provenance＋stale 守衛、跨 session 一致） | 雙語料皆有此路；index 缺場重建或退 LSP（workspace 狀態相依） |
| **Rust repo** callers／transitive callers | **code-reality** MCP `callers`（sites 級）／`closure`（BFS）；CLI `scip_refs --callers`／`--closure` | sites 級細節＋BFS transitive；LSP `incomingCalls` 單層 |
| **Transitive blast radius** (A changed → all downstream N hops) | **code-reality** `impact_radius` | LSP can't do transitive efficiently |
| **Change → risk score + affected nodes** (from a diff) | **code-reality** `detect_changes`（MCP tool；`analyze_changes` 是 `changes.py` 內部函式，非 MCP tool） | LSP has no diff/risk model |
| **Affected execution flows** (which call chains hit) | **code-reality** `affected_flows` | LSP has no flow concept |
| **Token-efficient review scoping** (read only impacted) | **code-reality** `get_minimal_context` / `get_review_context` | LSP has no context-budgeting |
| **Hub / bridge / community / architecture overview** | **code-reality** `hub_nodes` / `bridge_nodes` / `list_communities` (directory or `--leiden`) / `architecture_overview` | No LSP equivalent |
| **Dead code** (no callers + no tests) | `callers` 歸零＋CLI `hub_refs` hazard 分層安全網（「0 refs 可刪」前必跑） | LSP zero-hits 無 hazard 分層（動態派發盲區） |
| **Semantic search** ("where do we handle X concept") | **code-reality** `semantic_search` (keyword face; embeddings not adopted) OR rg | LSP is name-based；**有效形態＝單關鍵詞**（多詞落 LIKE 全短語比對 0 筆） |
| **Comments / strings / config / TODO** | **rg** | Neither LSP nor code-reality index non-code |

**Rule of thumb:** *symbol* → code-reality（index 在場；Rust＝SCIP、Python＝pyrefly-index）; *graph* (impact/callers/flows/community/scope) → code-reality `graph_query` 家族; *type*（hover/diagnostics，.py 與 .rs） → code-reality-lsp-bridge（`hover`/`check_file`）; *text* → rg. index 缺場/過期 → 重建或退 LSP＋標「未 index 驗證」。For "what does this change affect," start at the engine's `impact_radius`/`detect_changes`, then LSP/Read for the specific symbols.

## Standard query map

| Need | Tool (MCP / CLI) |
|---|---|
| "who calls X" | MCP `callers`（sites 級）；CLI `scip_refs <sym> --callers --repo <root>` |
| "X 的 transitive callers" | MCP `closure`（BFS，depth 參數）；CLI `scip_refs <sym> --closure --depth N --repo <root>` |
| "X calls whom" | LSP `outgoingCalls`（CR 無 callee 面） |
| "change these files → what's hit" | `impact_radius` (CLI: `graph_query impact_radius`) |
| "diff → risk + affected nodes" | `detect_changes` (CLI: `graph_query detect_changes`) |
| "which flows pass through X" | `affected_flows` / `list_flows` (CLI: `graph_query affected_flows` / `flows`) |
| "token-cheap context for reviewing this change" | `get_minimal_context` / `get_review_context` |
| "architectural hotspots / chokepoints" | `hub_nodes` / `bridge_nodes` (CLI: `graph_query hub` / `bridge`) |
| "module clusters / coupling" | `list_communities` / `get_community` / `architecture_overview` (CLI: `graph_query communities` / `arch_overview`；`get_community` MCP-only) |
| "is X dead code" | `callers` 歸零＋CLI `hub_refs <sym> --repo <root>` hazard 分層（含 test/prod 切分）——「0 refs 可刪」前必跑安全網 |
| EP 規劃期投影（整合器型/跨模組 EP） | MCP `project` 或 CLI `code-reality project --repo <repo> --plan <plan.toml>`——overlay 鑄造＋投影面查詢：規劃新符號反向鏈＋claims 三態（`HOLE`/`MISSING`/`WIRED`）；輸出帶 `[projected]` 標籤＝**宣告非證據**（洗衣陷阱防護）；操作/語義真相源 [code-reality](../code-reality/SKILL.md) 工具表；EP 接線見 [execution-plan](../execution-plan/SKILL.md) 段落 0。**觀察窗**（cr-audit R8）：零正面案例期，不擴接線面，首個實證後再評估常態化 |
| "find symbol by concept/keyword" | `semantic_search` (keyword face；embeddings 未採用) or rg |

## 受影響測試集 → test files 標準配方（修改檔 → 受影響 test files）

> 受影響測試集列舉必須走機械反查，禁目錄直覺（測試檔跨目錄擺放時直覺必漏）。

- ① 有 graph：`code-reality graph_query impact_radius --repo <root> --files <絕對路徑>` 取影響檔案集，再對 tests 目錄 `rg "<符號>"` 交叉確認
- ② 無 graph／stale：退 `rg "<符號>" tests/ -l`
- ③ 輸出證據三級標記：`graph-derived`／`text-derived`／`未驗證 dynamic consumers`——`rg` 命中 ≠ 完整 impact（動態派發與字串鍵耦合是 CR 盲區，graph 亦盲）

> **Stale graph check:** Rust repos — `code-reality scip_refs <sym> --repo` 的 `[SRC]` 行只作 per-symbol provenance 顯示，**不對照 repo HEAD 判新鮮**（舊 HEAD 對照觸發重建的語義已廢）；**新鮮判定一律走 freshness face**——`code-reality freshness --repo <root> --json`，`head_drift` 為獨立欄位、不進 `stale_reasons`（HEAD 前進不算過期，identity 相同即 fresh）。Graph freshness — rebuild with `graph_db build --repo <root>` (Python cache first: `pyrefly-index --repo <root>`). Graph facts are build-time; stale graph = stale facts (parallel: LSP workspace state-dependence — re-verify before concluding). **freshness 判準單一源＝AIR-135 invariant（ai-development-guide「AIR-135 協作 invariant」條 2）：`fresh ⇔ indexed_source_identity == requested_consumer_source_identity`（content-addressed identity，涵蓋 dirty WT/content）**——判準由 freshness face 機械求值：`code-reality freshness --repo <root> --json`，欄位 `fresh`／`stale_reasons`／identity pair `indexed_source_identity` vs `current_source_identity`／`identity_algo`／`serves`；`fresh=true` → graph 可宣稱新鮮；stale 或 legacy index（無 identity 戳記，face 經 `stale_reasons` 回報 legacy-signals）→ 既有降級語義（graph 只當 committed baseline）。identity 覆蓋未提交 dirty content，編輯中即時 delta 仍以 live LSP 為準。

## 🔴 Anti-over-reliance (the failure this skill prevents)

Graph edges are **static parse-time** facts. They miss:

- **Dynamic dispatch** — `obj.method()` resolves by runtime type; graph edges the declared type's method, not the subclass that runs.
- **Config / data-driven branches** — graph has both branches; runtime takes one.
- **Reflection / string-based calls / plugin registries** — graph can't see them（例外：profile `[[hazard_registry]]` 的註冊推定納入 hub_refs hazard 判定層）— best-effort, not complete.
- **Cross-process / network calls** — not in the local graph.

🔴 **GATE:** before concluding "X is dead code" / "this change is safe — nothing depends on it" / "A always calls B" — for any *dynamic* case, hold evidence beyond the graph: read the call site, check for dispatch/config/reflection. A graph "no callers" is strong for static calls, **blind for dynamic**. Label graph-only findings `evidence-based`, not `confirmed`, when behavior is in question. (Parallel: nt-query — a data structure is not evidence of a capability ceiling.)

## Boundary — discipline vs CRG's workflow skills

CRG's `install` generates **four workflow skills** (`debug-issue`, `explore-codebase`, `refactor-safely`, `review-changes`) — *step-by-step procedures* for a task with the graph, project-local (`.claude/skills/`).

**`cr-query` is the discipline** — *how to query the graph correctly* (LSP-vs-CR 分工、GATE、anti-over-reliance), global (ai-guide).

They compose: a CRG workflow gives the steps; `cr-query` governs *how each query in those steps is interpreted* (don't over-infer, fall back to LSP/code when behavior matters). On conflict, this skill's discipline wins — workflows don't suspend verification.

## Fallback — engine absent or stale

- **Not installed** → `[WARN]` (above) + LSP `findReferences`/`incomingCalls` (single-symbol, no transitive) + scan-project dep_graph (folder/module-level ripple) + rg. Accept degraded: no transitive impact, no flows, no communities.
- **MCP tools absent but graph.db exists** → CLI 直用：`code-reality graph_query <op> --repo <repo-root>`（ops: impact_radius detect_changes hub bridge communities arch_overview flows affected_flows review_context minimal_context search symbols；`--leiden` 社區分層——`--union` 已退休：聯集邊於 build 時物化，查詢預設全量）。新庫缺場 → `code-reality graph_db build --repo`（純 producer graph 為常態——`import_legacy` 已完全移除〔W5 2026-08-28〕）。
- **Graph stale** → regen the producer cache (Rust: SCIP index; Python: `pyrefly-index`) + `graph_db build --repo <root>`. Or verify critical edges with LSP and note the staleness.

## Reference

- **CLI commands:** `code-reality --help`（graph_query 家族＋scip_refs＋graph_db build 等）
- **code-reality MCP 接線：** stdio `code-reality-mcp --stdio`（plugin 形態）或 streamable-http `127.0.0.1:8200/mcp`（共享 resident，服務由 OS 服務層管理——目前未部署，現值以 launchctl 為準）；工具呼叫一律帶 `repo_root`（不自動偵測）。舊 CRG server（port 5555）已**完全退場**（服務解裝；5555/launchctl 清潔態——勿再期待）。
- **engine semantics 真相源:** ai-guide `skills/code-reality/SKILL.md`（接線語義）＋code-reality repo（`crates/AGENTS.md`＋plugin skill＝工具事實）
- **Sibling facts discipline:** [symbol-query-routing](../../rules/symbol-query-routing.md) (symbol queries) — this skill is its graph counterpart
- **Consumers:** [review-engine](../review-engine/SKILL.md) (change-impact lens), [arch-thinking](../arch-thinking/SKILL.md) §二 結構機械 (structure-facts lens), [execution-plan](../execution-plan/SKILL.md) 段落 0 (EP 依賴分析——ripple 宣稱工具證據 + 死路假設信號)
