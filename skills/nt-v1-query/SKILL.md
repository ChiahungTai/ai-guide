---
name: nt-v1-query
description: "Query NautilusTrader v1 (legacy Cython runtime — the consumer's CURRENT runtime, e.g. mosaic) correctly — docs-first for capability/concept, LSP-on-Cython-stubs for implementation, designer-intent for usage contract, plus NT type boundary audit. Use when investigating what the v1 runtime supports ('NT 支援/能不能/能力/概念', multi-account, OMS, position 計算, accounting, value types, emulated orders), where/how v1 implements something (cache, model, execution, backtest config, 'NT symbol 在哪', BacktestEngine, TradingNode, Actor, on_bar), whether an NT API is safe to call in a given context (thread/loop/caller — '跨線程', node.run/stop/dispose, loop ownership), or auditing NT type boundaries (Bar/Instrument/InstrumentId/BarType/Strategy 的 import 路徑、stub 正確性、簽名、Cython 邊界型別相容性). Prevents over-inferring a capability or usage boundary from one data structure or signature. For v2 (Rust+PyO3) / migration research use the nt-query skill instead."
when_to_use: Fires when a consumer project's LLM investigates NautilusTrader v1 runtime behavior — "does NT support X" (about the venv's actual v1 runtime), "NT 能不能", "how does NT compute position", "where is X defined in NT", "is it safe to call X from thread/loop Y" (usage contract — cross-thread node.stop/dispose, loop ownership, daemon thread), or when reading v1 nautilus_trader/ source / .pyi stubs. Load BEFORE diving into NT v1 source.
---

# nt-v1-query — Query NautilusTrader v1 (Cython runtime) correctly

You're investigating **NautilusTrader v1** — the legacy **Cython runtime** that the consumer's venv actually runs (e.g. mosaic). This skill covers v1-only machinery (`.pyx` source, fork stub workflow, Cython/PyO3 layer asymmetries). For the v2 Rust+PyO3 runtime or v1→v2 migration research, use the **nt-query** skill. NT has two distinct knowledge layers; confusing them causes the most expensive mistake.

## The one rule

> **Docs decide CAPABILITY. Source reveals IMPLEMENTATION. Never infer a capability boundary from a single data structure.**

`dict[Venue, AccountId]` (a 1:1 helper index) is an *implementation choice*, not proof that "one venue = one account" is a hard limit. A data structure shows how something is built today — not what the platform can do.

**Corollary — don't extrapolate behavior from one code path.** NT behavior often splits by lifecycle stage or account type, and each split is a separate code path. Example: margin reservation has a *pending-order* path (`_update_margin_init`) and a *filled-position* path (`calculate_margin_maint`); a finding from one (e.g. "market order has no price → skipped") does not describe the other. When a concern splits, verify the **specific path your scenario hits**. Same anti-pattern shape as the one rule — don't describe the whole from one part. The account/margin map and its two paths are written up in [account-model.md](account-model.md).

## Locate the NT repo — resolve `<NT_REPO>` once

The v1 checkout lives at `~/Github/nt_v1` (branch `main-v1`). All paths below use `<NT_REPO>`:

1. **Override** — env var `NT_REPO_PATH` is set → use it. (A consumer may set this in `.claude/settings.json` `env` to point at a specific checkout or worktree.)
2. **Default** — `~/Github/nt_v1`; verify with `test -d ~/Github/nt_v1/docs/concepts`.
3. **Not found** — stop and tell the user: "nt-v1-query needs the v1 NautilusTrader checkout; set `NT_REPO_PATH` or give me the path."

**Rename note:** documents predating the repo split that cite `~/Github/nautilus_trader` for Cython/v1 content (`.pyx`, stub workflow, `scripts/lsp_stubs/`) mean what is now `~/Github/nt_v1`.

## Upstream docs vs this fork — pick the right truth

- **context7 / online docs** describe **upstream NT** — fine for general concepts and syntax (not fork-state claims). Upstream has moved to v2 (Rust+PyO3); online docs increasingly describe v2 — **verify v1 claims against `<NT_REPO>`**, not context7.
- **`<NT_REPO>`** describes **this fork's v1 runtime** (Cython runtime in use, stub workflow added).
- For any claim about what THIS fork actually does — capability, architecture, language layer, enabled features — ground in `<NT_REPO>`, not context7. context7 structurally cannot see this fork's state.
- Cautionary case: an overview once claimed "Cache is in Rust" (drawn from upstream-general context7). Ground truth is layered — `cache.pyx:Cache` (the in-memory core) is **Cython for hot-path performance**; only the DB-backing adapters wrap Rust (`nautilus_pyo3`). Two errors compounded: upstream-vs-fork drift **and** generalizing one layer's language (Rust backing) to the whole module — the same anti-pattern as the one rule (don't infer the whole from one part). When a module mixes layers, name the layer.

## Step 1 — Classify the query

| Shape | Signal words | Authoritative source |
|---|---|---|
| **Capability / concept** | "does NT support…", "can NT…", "is X a hard limit", "NT 能力/概念/支援" | `docs/concepts/` **first** → Step 2 |
| **Implementation / symbol** | "where is X", "signature of Y", "who calls Z", "NT symbol 在哪/實作" | **LSP on `.pyi`** → `.pyx` source → Step 3-4 |
| **API contract** | "what params does X take" | `docs/api_reference/` OR `.pyi` + docstring → Step 3 |
| **Usage contract / context** | "is it safe to call X from thread/loop Y", "can stop/dispose run cross-thread", "NT 跨線程 / loop ownership" | **Designer intent** → Step 2b |

Most real questions are **mixed** ("can NT do X, and how do I call it?") → run the **capability path first**, then implementation.

## Step 2 — Capability path (docs-first)

1. Open `<NT_REPO>/docs/concepts/CLAUDE.md`. It maps each concept → doc file → source module, with a **"Non-derivable knowledge"** column that tells you what only the docs can answer.
2. Read the concept file (e.g. `accounting.md`, `positions.md`). Extract: (a) what NT explicitly says it supports, (b) any symbol names mentioned, (c) `:::note` / `:::warning` behavioral contracts.
3. **The docs statement IS the answer.** If `accounting.md` says "multi-account venues", multi-account is supported — full stop.
4. 🔴 **GATE — the failure this skill exists to prevent:** before concluding "NT can / cannot do X", you must hold **docs evidence** — an explicit statement, a `:::note`/`:::warning`, or a verified absence in the relevant concept doc. A source data structure is **not** evidence of a capability ceiling. If you only have a structure, stop and return to Step 2.1.
5. **The GATE follows claims, not query type.** It applies to any "NT can / cannot / is X" statement wherever it appears — including a line dropped inside an overview or a casual answer, not only when you run a dedicated capability query. Overview framing does not suspend verification: a specific, falsifiable, fork-dependent claim needs docs / `<NT_REPO>` evidence even mid-sentence. "Probably right, I'll leave it" is not evidence — some unverified claims are already wrong, and you cannot tell which without grounding.

## Step 2b — Usage-contract path (designer intent)

"Method exists" ≠ "callable in any context." NT APIs — especially lifecycle (`node.run/stop/dispose`), threading, loop ownership, Actor registration timing — carry a **design contract** about *where/how* they're meant to be called. Violating it produces symptoms that look like "NT bug" but are contract violations (e.g. calling `node.stop()/dispose()` cross-thread while the loop runs in a daemon thread → `loop.stop()` interrupts `run_until_complete` → `RuntimeError("Event loop stopped before Future completed")`).

**This is a third knowledge layer** — not docs/concepts (capability, Step 2), not stubs (implementation, Step 3). The source is **NT designer intent**:

- **NT's own examples** (`<NT_REPO>/examples/live/**`): **mixed — don't generalize from one family.** Most (binance/bybit/dydx…) use main-thread `node.run()` block + SIGINT stop + `finally: node.dispose()`. But several IB examples (`connect_with_tws.py`, `with_databento_client.py`, `connect_with_dockerized_gateway.py`) call `node.stop()` from a `daemon=True` timer thread — and only get away with it because `stop()` swallows the resulting `RuntimeError` (see source bullet). **That swallowed error is the tell, not a sanction.**
- **NT's own source** (`nautilus_trader/live/node.py:stop`, ~L381): `stop()` schedules via in-loop-only `loop.create_task(self.stop_async())`, wrapped in `try/except RuntimeError`. A cross-thread call hits `create_task` from the wrong thread → `RuntimeError` → silently swallowed by the except. **Stronger evidence than any example survey** (immune to the over-generalization above) and the real reason a cross-thread `stop` "doesn't crash."
- **NT's own tests** (`<NT_REPO>/tests/live/**`): what usage does NT itself test?
- **NT's own API choices**: when NT needs cross-thread scheduling, what does it use? (`asyncio.run_coroutine_threadsafe` is the sanctioned cross-thread API — NT uses it in `adapters/interactive_brokers/client/client.py`; `loop.create_task` is in-loop only. If NT never routes `stop` through `run_coroutine_threadsafe`, `stop` isn't designed for cross-thread call.)

Combine with arch-thinking: loop/thread lifecycle is NT's internal (bounded context) — don't operate it from outside the owning thread.

🔴 **GATE — same shape as the one rule:** before concluding "I can call X from context Y (thread/loop/caller)", hold designer-intent evidence — an example, a test, or NT's own API-choice pattern. A method's existence or signature is **not** evidence of usage safety. "It's a public method" = inferring usage from structure = the same anti-pattern this skill exists to prevent.

## Step 3 — Implementation path (LSP on the stub layer)

Use the symbol names from Step 2 (or the query) as seeds:

- `workspaceSymbol "<Name>"`, or `documentSymbol` on the `.pyi` → locate the class/method
- `hover` → signature. Stubs are now **cross-package-precise** — `hover`/`findReferences` give real types (`order() -> Order | None`, `Cache(CacheFacade)`) wherever the symbol's dependency has a deployed `.pyi`. Some remain `Any` — the generator couldn't resolve certain return types (e.g. `cache.mark_price() -> Any`; its docstring gives `MarkPriceUpdate | None`), plus the PyO3 layer. **Still `Read` the `.pyi` docstring** for semantics types can't express (behavioral notes, "X or None" intent).
- `findReferences` / `incomingCalls` → who uses it

NT `.pyi` sit next to the `.pyx`/`.so`; in a consumer repo they reach the LSP via `make sync-stubs`.

## Step 4 — Source truth (only when docs/stubs are insufficient)

`rg` the `.pyx` for the real internal structure. This answers *how* something is implemented — never *whether* it is possible.

**Discipline:** label every source finding as IMPLEMENTATION, not CAPABILITY. `cache._index_venue_account: dict[Venue, AccountId]` = "there is a venue→account lookup index" (implementation), NOT "NT allows only one account per venue" (capability — check docs).

## 🔴 Symbol-name discipline — verify before you write

Before **writing down** any NT class / method / function name (in your notes, a `CLAUDE.md`, code, or this skill), confirm it exists in the **Cython runtime**. Do NOT infer a name from naming symmetry, an abbreviation, or the Rust/PyO3 layer — that blind spot has repeatedly produced wrong symbols:

- `calculate_maintenance_margin` is the **Rust/PyO3** name; the Cython runtime method is `calculate_margin_maint`.
- a private `_update_margin_init` was assumed to have a `_update_margin_maint` sibling — **it does not exist** (the maintenance path is the public `update_positions`).
- the leading `_` on private `cdef` methods (`_update_balance_locked`, `_update_margin_init`) was dropped.

**Verify before writing — 0 hits means the name is wrong or from another layer; do not use it:**

- `rg "def <name>|cdef .*<name>|cpdef .*<name>" <NT_REPO>/nautilus_trader/<dir>/`, **or**
- `LSP workspaceSymbol "<name>"`.

NT naming is often **asymmetric** (pending path is private `_update_margin_init`, filled path is public `update_positions`) — never assume a counterpart exists.

## Fallback — LSP is blind / stub looks wrong

**LSP can't resolve NT Cython symbols** (`workspaceSymbol` empty, `attr-defined` / `Unknown` on `Bar` / `Price` / `Quantity` / `InstrumentId`):
→ stubs aren't synced to this repo's venv. Interim: `rg` the `.pyi` / `.pyx` directly. **Flag the user: run `make sync-stubs` in the consumer repo** (common cause: `uv sync` or an NT upgrade wiped the venv `.pyi`). Known recurring failure — don't struggle silently.

**LSP resolves but a type/signature looks wrong or a method is missing** (e.g. return should be `X | None` but isn't; `unknown import symbol`; method absent):
→ the stub **content** is stale — not a sync issue. Fix fork-side in `<NT_REPO>`:
- **Auto-gen stub** (most modules): regenerate — `uv run python scripts/lsp_stubs/generate_nt_stubs.py nautilus_trader/<mod>/<file>.pyx` → then `make sync-stubs` in consumer. **Don't hand-edit** (regen overwrites). If the generator itself is the limit (dependency lacks `.pyi` → stays `Any`; C-only `cdef` call artifact), that's a generator-evolution item — flag it, don't paper over with `# type: ignore`.
- **Hand-written stub** (11: `model/{data,objects,identifiers}`, `trading/strategy`, `core/correctness`, `persistence/wranglers`, `indicators/{averages,momentum,trend,volatility,volume}`): hand-edit directly (they're audited for unmangled signatures).

Which stub is which + the generator's precision rules (cross-package preservation, Optional-ize, elide): `<NT_REPO>/scripts/lsp_stubs/README.md`.

## Reference material

- **Concept → doc → source map (authoritative — do not re-derive):** `<NT_REPO>/docs/concepts/CLAUDE.md`
- **Docs root navigation:** `<NT_REPO>/docs/CLAUDE.md`
- **NT module guide + LSP stub workflow:** `<NT_REPO>/CLAUDE.md`
- **LSP stub generation tools:** `<NT_REPO>/scripts/lsp_stubs/README.md`
- **The failure this prevents (case study):** `<NT_REPO>/ai-analysis/analysis/2026-06-16-nt-docs-over-source.md`
- **Account / balance / equity / margin model** (account_type → 4 layers, two lifecycle paths, gotchas incl. `margin_maint=0` trap): [account-model.md](account-model.md) — load when the query touches account types, balances, equity, margin, or PnL computation
- **Worked examples (4 query shapes, exact tool calls) + common concept→symbol seeds:** [reference.md](reference.md)

---

## 附錄：NT 型別邊界 audit 表

> NT 型別位於 Cython 邊界後方。LSP 是唯一可靠驗證型別用法的方式 —— `.so` 編譯模組無可讀 Python 原始碼，直接讀原始碼不足以驗證。audit 時遇到以下高風險型別，依表查證。

| Category | Module Path | Common Pitfall |
|----------|------------|----------------|
| `Bar` | `nautilus_trader.model.data` | Import from wrong module |
| `Instrument` | `nautilus_trader.model.instruments` | Missing `.pyi` → Unknown type |
| `InstrumentId` | `nautilus_trader.model.identifiers` | Constructor vs `from_str()` |
| `BarType` | `nautilus_trader.model.data` | `from_str()` existence |
| `Strategy` | `nautilus_trader.trading.strategy` | `on_bar()` signature |
| `BarDataWrangler` | `nautilus_trader.persistence.wranglers` | Input format requirements |

**Audit checklist**（每個 NT 型別遇到時）：
1. `LSP hover` → LSP resolve 什麼型別？若 `Unknown`，stub missing/broken
2. `LSP goToDefinition` → 跳到 `.pyi`？若否，stub sync issue
3. Constructor/method signature → `LSP hover` 在 call site 驗參數型別
4. Return type → `LSP hover` 在 variable assignment 驗回傳型別

**Stub health detection**：LSP 回 `Unknown` → 跑 `make sync-stubs`（NT 專案）刷新 stub；或手動從 NT source tree 同步 `.pyi` 到 `stubs/` 與 `.venv/.../nautilus_trader/`。
