# Interface Design — 介面合約設計 reference（arch-thinking 側檔）

> 前身＝`api-and-interface-design` skill（AIR-113 reference-demotion：退出 resident 注入面、內容降為 arch-thinking 的介面合約側檔）。語義與責任邊界判定歸 [arch-thinking](SKILL.md)；本檔承載介面合約的具體設計原則。

Design stable, well-documented interfaces that are hard to misuse. Good interfaces make the right thing easy and the wrong thing hard.

## Core Principles

### Hyrum's Law

> With a sufficient number of users of an API, all observable behaviors of your system will be depended on by somebody.

Every public behavior — including undocumented quirks, error message text, timing, and ordering — becomes a de facto contract. Be intentional about what you expose. Don't leak implementation details.

### Validate at Boundaries

Trust internal code. Validate at system edges: API route handlers, form submissions, external service responses, environment variable loading.

**Where NOT to validate**: between internal functions that share type contracts, in utilities called by already-validated code, on data from your own database. Over-validating internally adds noise and hides the real boundary.

**Third-party API responses are untrusted data.** Always validate their shape before using them in logic or decisions.

### 邊界 = Clean Architecture Adapter 邊界

「Validate at Boundaries」的 boundary，在 Clean Architecture 是 **adapter 邊界** — 介面（port）定義在內層（use case），實作在外層（adapter）。依賴向內：use case 定義 port，adapter 實作，infra 是外部細節。

- 驗證點 = adapter 邊界（系統邊緣：API、SDK、DB、跨進程）
- 內層（domain / use case）之間信任型別合約，不重複驗證
- 設計介面時，介面屬於內層（use case 定義 needs），實作屬於外層（adapter 提供）

**與 [arch-thinking](SKILL.md) 分工（RC-2 邊界）**：本檔設計**介面合約**（Hyrum's Law、Validate at Boundaries、穩定性）；arch-thinking 檢視**整體結構**（分層依賴、bounded context）。介面是 adapter 邊界的具體化 — 設計介面用本檔，看整體分層用 thinking。

### Prefer Addition Over Modification

Extend interfaces without breaking existing consumers. Add optional fields; don't change existing field types or remove fields. 移除既有欄位前先驗證全消費端（LSP findReferences + rg 字串引用 + 非 library 消費者）。

### Consistent Error Semantics

Pick one error strategy and use it everywhere. Don't mix throwing, returning null, and returning `{ error }` — consumers can't predict behavior.

### Predictable Naming

- REST endpoints: plural nouns, no verbs (`GET /api/tasks`, not `GET /api/getTasks`)
- Boolean fields: `is`/`has`/`can` prefix
- Input/output separation: input types exclude server-generated fields

### Agent-Friendly Interfaces

When an interface is consumed by AI agents (not just humans), it must be **machine-parseable and query-efficient**. A human-readable PDF or a rendered UI is useless to an agent that cannot render it.

- **Return structured data, not rendered artifacts**: Markdown / JSON / typed schemas — not PDF, screenshots, or binary blobs. If a human-facing rendering exists, expose the underlying structured form too.
- **Support filter / sort / pagination server-side**: agents must not download a huge payload and filter client-side. An API that only returns full records one-by-one forces an agent into slow, inaccurate aggregation — add deterministic filter/sort endpoints so the non-deterministic agent can ask precisely.
- **Agents need *stronger* deterministic support, not less**: agents don't replace deterministic workflows — they sit on top of them and require more robust deterministic primitives (filter/sort/validate/paginate), because their access pattern is non-deterministic.

**Why**: an interface that is merely "an API" but returns unparseable or unfilterable data defeats every agentic pattern built atop it — the contract is fine, the content is agent-hostile. Wrapping a legacy API behind MCP/Agent tooling without these improvements is the canonical anti-pattern (the adapter hides a hostile surface instead of fixing it).

## Verification

- [ ] Every endpoint has typed input and output schemas
- [ ] Error responses follow a single consistent format
- [ ] Validation happens at system boundaries only
- [ ] New fields are additive and optional
- [ ] List endpoints support pagination
- [ ] Interfaces consumed by agents return structured/parseable data (not PDF/screenshots/binary) and support server-side filter/sort/pagination
