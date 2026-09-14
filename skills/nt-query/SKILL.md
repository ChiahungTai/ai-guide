---
name: nt-query
description: "Query NautilusTrader v2 (Rust + PyO3 runtime) correctly — docs-first for capability/concept, in-repo AGENTS.md hubs for orientation, LSP on in-package generated stubs for implementation, designer-intent for usage contract, MIGRATION_V2.md for v1→v2 mapping. Use when investigating what NT v2 supports ('NT 支援/能不能/能力/概念' against the v2 runtime), v1→v2 migration impact (import flattening, API renames, behavior changes), where/how v2 implements something (LiveNode, DataActor, BacktestEngine, on_quote/on_bar, cache, portfolio, Rust crates), whether a v2 API is safe to call in a given context (loop ownership, node run/start/poll/stop), or porting consumer code from v1 to v2. Prevents over-inferring a capability or usage boundary from one source data structure, and prevents writing v1 names from memory into v2 contexts. For the legacy v1 Cython runtime use the nt-v1-query skill."
when_to_use: Fires when a consumer project's LLM investigates NautilusTrader v2 — "does v2 support X", "v2 API", "PyO3", "migration to v2", "MIGRATION_V2", porting v1 code (renames like on_quote_tick→on_quote, TradingNode→LiveNode, Actor→DataActor), reading python/nautilus_trader stubs, or Rust crates/ source. Load BEFORE diving into v2 source or migration work.
---

# nt-query — Query NautilusTrader v2 correctly

You're investigating **NautilusTrader v2** — the **Rust core + PyO3 Python package** under `python/` (the go-forward runtime; v1 Cython is legacy and lives in a separate skill/checkout). NT has two distinct knowledge layers; confusing them causes the most expensive mistake.

## The one rule

> **Docs decide CAPABILITY. Source reveals IMPLEMENTATION. Never infer a capability boundary from a single data structure.**

A data structure shows how something is built today — not what the platform can do. When a concern splits by lifecycle stage or code path, verify the **specific path your scenario hits** — don't describe the whole from one part.

## Locate the NT repo — resolve `<NT_REPO>` once

1. **Override** — env var `NT_REPO_PATH` is set → use it.
2. **Default** — `~/Github/nautilus_trader` (branch `main`, tracks `upstream/nightly` — the daily snapshot of develop, the more stable dev channel). Verify with `test -d ~/Github/nautilus_trader/python/nautilus_trader`.
3. **Not found** — stop and tell the user: "nt-query needs the v2 NautilusTrader checkout; set `NT_REPO_PATH` or give me the path."

**Layout reality (v2):** the Python package lives under `python/nautilus_trader/` — there is **no root `nautilus_trader/`**. Each subpackage (`model`, `common`, `config`, `live`, …) is a thin `__init__.py` star-importing the compiled `_libnautilus` Rust extension (`_fixup.fixup_module_names` remaps module paths), so **v1 deep paths** (`nautilus_trader.common.component`, `nautilus_trader.model.identifiers`) **do not exist** — import from the flat subpackage (`from nautilus_trader.common import Logger`). v1 and v2 both import as `nautilus_trader` — never install both into one venv; test migration in a separate environment. Real Python logic exists only in a handful of places — `analysis/` (tearsheet reporting), `testkit/providers.py`, `persistence/loaders.py`, `core/datetime.py`, `config/` (aggregation re-export), `adapters/binance/instruments.py` — every other subpackage is a pure shell. Python also has **no Kernel/Trader/LiveEngine**: orchestration entry points are `LiveNode` / `BacktestEngine` (Rust pyclass), and `trading.Controller` is actually `PyController` from `nautilus_system` mounted into the trading domain.

## In-repo navigation layer — AGENTS.md hubs (read first)

This checkout ships a module-level AGENTS.md navigation layer (if those files are absent — not kept — fall back to the path rules in this skill):

- `<NT_REPO>/crates/AGENTS.md` — Rust workspace layering (who depends on whom), crate↔Python-domain map (with misalignments), per-crate navigation table, suggested reading order
- `<NT_REPO>/python/nautilus_trader/AGENTS.md` — shell loading mechanism, the "where real Python logic lives" table, domain→crate mapping
- `<NT_REPO>/python/AGENTS.md` — maturin/uv build, stub & docstring generation workflow, pytest entry points

For "where is X / which side owns Y" questions, read the relevant hub's mapping table before scanning source.

## Upstream docs vs this checkout — pick the right truth

- This checkout's `main` **tracks `upstream/nightly`** (the daily snapshot of develop), **and it is a fork** (origin = ChiahungTai/nautilus_trader; remote `upstream` = nautechsystems) carrying a thin patch layer on adapters (polymarket / lighter / derive). Upstream docs/context7 describe upstream v2 — released docs may **lag the rc-era branch**, and fork-patched adapters may diverge from upstream; verify rc-specific and adapter-behavior claims against `<NT_REPO>`.
- **`<NT_REPO>/MIGRATION_V2.md` is the authoritative v1→v2 contract** — import-path table, API renames, behavior changes, known limitations. For any "v1 did X, what does v2 do" question, ground the answer there before synthesizing.

## Step 1 — Classify the query

| Shape | Signal words | Authoritative source |
|---|---|---|
| **Capability / concept** | "does v2 support…", "can NT…", "NT 能力/概念/支援" | `docs/concepts/` **first** → cutover limits (Step 2) |
| **Migration impact** | "v1→v2", "port X", "why did X break" | **`MIGRATION_V2.md`** → stubs (Step 3) |
| **Implementation / symbol** | "where is X", "signature of Y", "who calls Z" | **LSP on in-package `.pyi`** → Rust source (Step 3-4) |
| **Usage contract / context** | "is it safe to call X from loop Y", node `run/start/poll/stop` ownership | **Designer intent** → Step 2b |

Most real questions are **mixed** → run capability/migration path first, then implementation.

## Step 2 — Capability path (docs-first)

1. Open `<NT_REPO>/docs/concepts/` — **restructured into subdirectories** (`data/`, `events/`, `orders/`, `instruments/`, `backtesting/`, …) with per-topic pages; `index.md` in each dir is the entry. No v1-style concept→source map file exists.
2. Read the concept file. Extract: (a) explicit support statements, (b) symbol names, (c) `:::note` / `:::warning` behavioral contracts.
3. **The docs statement IS the answer** — full stop.
4. 🔴 **GATE — cutover limits are capability boundaries:** v2's supported surface is scoped. Before concluding "v2 can / cannot do X", check the **known limitations / cutover limits** section of `MIGRATION_V2.md` (e.g. deferred: Python joined-response callbacks, LiveNode Redis/SQL backing injection, SQL cache loads/state persistence/heartbeat, v1 StreamingConfig/DataCatalogConfig iterator workflow, some adapter instrument-provider filters, external msgbus publishing of order/position snapshots). "Supported workflows" are listed in the release notes / migration doc — something outside that list is *deferred*, not impossible; say which (the upstream roadmap issue #4042 tracks the wider post-cutover surface).
5. Same GATE discipline as v1: a source data structure is **not** evidence of a capability ceiling; and the GATE follows claims anywhere they appear, including casual lines in an overview.
6. **State & recovery questions** ("v2 怎麼存/恢復狀態", "is the cache the source of truth") route to `docs/concepts/event_sourcing.md` + `docs/concepts/reconciliation.md`: the **event store is the durable authority**, the **cache is a write-through projection**, and **market data stays in the data catalog** (don't conflate catalog with event store). The event store itself is Rust-internal (`crates/event_store`); its API surface is still evolving (per that page's own note).

## Step 2b — Usage-contract path (designer intent)

"Method exists" ≠ "callable in any context." v2's Rust runtime owns the loop; the **`run()` / `start()` / `poll()` / `stop()` contract** (who owns the loop, what `poll()` services, residual-event grace) is documented in `MIGRATION_V2.md "Live node inspection and host-loop integration"`. Backtest-side inspection changes live in the same doc's "Inspection and state renames" and "Backtest node post-run inspection" sections. Designer-intent sources:

- **`<NT_REPO>/examples/`** — current live-node builders, adapter factories, strategies (the v1-flavored tutorials are known-stale; trust examples + stubs + tests over tutorials).
- **`<NT_REPO>/python/tests/`** — acceptance tests (`acceptance/test_backtest.py`) and reference strategies (`strategies/ema_cross.py`) show sanctioned usage, including the v2 StrategyConfig custom-fields pattern.
- **API shape**: if the runtime wanted you to call it cross-loop, it would expose a scheduling API — check how the node itself schedules work.

## Step 3 — Implementation path (LSP on in-package stubs)

- Stubs are **in-package generated** (`python/nautilus_trader/**/*.pyi`, pyo3_stub_gen) — they are the **supported Python contract**; LSP works directly off the checkout (or off an installed v2 wheel — stubs ship with it). No sync workflow, no fork-side stub layer.
- Stubs **and** Python docstrings are **generated artifacts** (sources: `crates/*/src/python/` `py_*` wrappers; regenerate via `make py-stubs` / `python/generate_docstrings.py`; drift checked by `make check-generated-drift`) — never hand-edit them; a stub defect is fixed at the Rust source or the generator.
- `workspaceSymbol` / `hover` / `findReferences` as usual; classes are `@typing.final` where marked (e.g. `ParquetDataCatalog`, wranglers) — **subclassing is not a capability** unless the Rust side opts in (contrast: `FeeModel` is explicitly Python-subclassable; `FeeModel.get_commission` must be overridden).
- Known stub gaps (callable at runtime, absent from stubs): Kraken `edit_orders_batch` / `submit_orders_batch` variants, adapter wire-DTO runtime attributes — don't report these as "missing API".

## Step 4 — Source truth (only when docs/stubs are insufficient)

Implementation lives in **Rust**: `<NT_REPO>/crates/<domain>/` (core/model/common/execution/live/…), PyO3 bindings under `crates/<domain>/src/python/*.rs`, adapters under `crates/adapters/<venue>/`. Python-side `__init__.py` files are thin star-import shims. Label every source finding as IMPLEMENTATION, not CAPABILITY.

Workspace layering (dependency direction): core ← model ← common ← execution/data ← portfolio/risk/trading ← system ← backtest/live/event_store; `crates/pyo3` aggregates all bindings into the `_libnautilus` extension module; adapters are injected via factories (**system never imports adapters**). Use this to reason about "where would X live / who can call whom". The standard adapter crate anatomy (config / factories / data / execution / http / websocket / signing + the `python/` binding layer, with credential redaction) is documented in `crates/adapters/AGENTS.md`.

**Adapter authoring reality:** the v2 Python surface has **no client base classes** (`LiveDataClient`/`LiveExecutionClient` etc. do not exist as Python classes) — adapters are Rust/PyO3, registered via `LiveNodeBuilder.add_data_client(name, factory, config)`. Custom adapters must be written in Rust against the crates; reference existing `crates/adapters/<venue>/` structure. The conceptual adapter component model (HTTP/WS clients, instrument provider, data/execution clients) is documented in `docs/concepts/adapters.md`, and per-venue capabilities in `docs/integrations/`. v2's `nautilus_trader.network` Python surface is only the `TransportBackend` enum — v1's generic Python HTTP/WebSocket/rate-limit clients have no v2 Python equivalent (that machinery is Rust-internal in `crates/network`).

## 🔴 Symbol-name discipline — v2 names, verified

**Never write an NT name from v1 memory into a v2 context.** The v1→v2 rename surface is large; classic traps: `on_quote_tick`→`on_quote`, `subscribe_quote_ticks`→`subscribe_quotes`, `cache.quote_tick()`→`cache.quote()`, `TradingNode`→`LiveNode` (+ builder pattern), `Actor`→`DataActor`, `ActorConfig`→`DataActorConfig`, `LoggingConfig`→`LoggerConfig`, `ExecAlgorithm`→`ExecutionAlgorithm`, portfolio `is_flat()`→`is_net_flat()`, `FeeModel.get_order_filled_fee`→`get_commission`, `register_currency()`→`Currency.register()`, plus properties→methods (`Order.events()`). The full tables live in `MIGRATION_V2.md`.

**Verify before writing — 0 hits means the name is wrong or from the other version:**

- `rg "<name>" <NT_REPO>/python/nautilus_trader/<subpackage>/__init__.pyi`, **or**
- `LSP workspaceSymbol "<name>"`.

## Fallback — LSP is blind / stub looks wrong

- LSP can't resolve v2 symbols → confirm the query targets the v2 checkout (python/ layout) and the venv (if any) installed a v2 wheel (`--pre`), not a v1 wheel. Both install as `nautilus_trader` — a v1 venv resolving v2 imports is a version-mix symptom.
- Stub content wrong/missing → it's an **upstream issue** (this checkout tracks upstream; there is no fork stub layer to fix locally). Report it; optionally pin/avoid the API in consumer code.

## Reference material

- **v1→v2 migration contract (authoritative):** `<NT_REPO>/MIGRATION_V2.md` — import tables, renames, behavior changes (e.g. `Order.avg_px`/`slippage` now `Decimal`; `use_mark_prices` defaults true), known limitations
- **Concept docs:** `<NT_REPO>/docs/concepts/` (subdirectory layout, per-topic pages)
- **State & recovery concepts:** `<NT_REPO>/docs/concepts/event_sourcing.md`, `reconciliation.md` (event store = durable authority; cache = projection; market data stays in the catalog)
- **Per-venue capabilities:** `<NT_REPO>/docs/integrations/` + `docs/concepts/adapters.md` (adapter component model)
- **Python contract:** generated stubs in `<NT_REPO>/python/nautilus_trader/**/*.pyi`
- **Sanctioned usage examples:** `<NT_REPO>/examples/` + `<NT_REPO>/python/tests/` (acceptance backtest, reference strategies)
- **Rust implementation:** `<NT_REPO>/crates/` (bindings in `src/python/`, adapters in `crates/adapters/`)
- **In-repo navigation hubs:** `<NT_REPO>/crates/AGENTS.md` (workspace layering + Python↔Rust map), `<NT_REPO>/python/nautilus_trader/AGENTS.md` (shell mechanism + real-Python map), `<NT_REPO>/python/AGENTS.md` (build / stubs / tests)
- **Release-specific breaking changes:** `<NT_REPO>/RELEASES.md`
- **Install / channels:** `<NT_REPO>/docs/getting_started/installation.md` (nightly vs develop wheel cadence; `--pre` install; separate venv rule)

---

## 附錄：v2 遷移查證快捷（消費端移植工作）

| 問題形態 | 查證順序 |
|---|---|
| 「這個 v1 import 在 v2 對應什麼」 | `MIGRATION_V2.md` import 表 → `rg` v2 `__init__.pyi` 確認 |
| 「這個 v1 API 名還在嗎」 | `MIGRATION_V2.md` rename 表 → `workspaceSymbol` → 0 hits = 改名或移除 |
| 「v2 有沒有支援 X」 | `docs/concepts/` → `MIGRATION_V2.md` known limitations（deferred ≠ impossible） |
| 「v2 怎麼存/恢復狀態」 | `docs/concepts/event_sourcing.md` + `reconciliation.md`（cache 是 projection，不是真相） |
| 「v2 config 怎麼讀回/敏感值怎麼顯示」 | `MIGRATION_V2.md` "Config readback and sensitive values" 段 |
| 「行為跟 v1 一樣嗎」 | `MIGRATION_V2.md` Behavior changes 段 → 有列 = v2 契約；沒列也要驗（rc 演進中） |
| 「自訂 adapter / FeeModel 怎麼寫」 | Step 4 adapter reality；FeeModel = 可 subclass（`get_commission`）；client = 僅 Rust |
