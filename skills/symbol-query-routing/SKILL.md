---
name: symbol-query-routing
description: "符號查詢路由深層參考 — LSP operation 速查表（自 rule 下沉）、驗證任務 workflow 與輸出格式、rg 陷阱真實案例群（truncation/masking/local import/覆蓋判斷 false negative）、方法論限制 loopback、Agent prompt 工具指定模板（spawn agent 必填工具選擇）、跨 harness LSP 載體對照（Claude native vs ZCode bridge）、workspace staleness/reindex 與條件式 fallback。always-on 核心（cr-first 路由、任務啟動 gate、fallback/zero-hit 紀律）在 rules/symbol-query-routing.md；做依賴審計/符號查證/review 需要反例論證、operation 對照、spawn agent 工具指定或跨 harness 呼叫細節時載入。觸發詞：符號查詢路由、LSP、findReferences、reindex、workspace stale、rg 陷阱、載體對照、operation 速查、agent prompt 工具指定。"
---

# 符號／型別查詢路由 — 深層參考

> 本 skill 是 `rules/symbol-query-routing.md` 的 on-demand 深層載體：rule 端保留 always-on 核心（cr-first 路由、任務啟動 gate、fallback/zero-hit 紀律）；本檔承載 LSP operation 速查表、驗證 workflow 與輸出格式、反例論證、Agent prompt 工具指定模板、跨 harness 載體細節與 staleness 處置。

## LSP operation 速查表（自 rule 下沉）

先依 [查詢路由 rule](../../rules/symbol-query-routing.md) 選 carrier；下表是在 LSP 適用時選 operation，不另設 LSP-first 路由。

| 查什麼 | 首選 | 降級／備註 |
|--------|------|-----------|
| 符號引用（dead code、API 變更影響範圍） | `findReferences` | LSP 區分 scope；rg 只匹配文字 |
| 介面的具體實作 | `goToImplementation` | ZCode pyright 不支援（載體差異見下方對照） |
| 型別/簽名即時查 | `hover` | 不耗 context（不讀檔知型別） |
| 編輯後型別檢查 | `diagnostics`（即時） | mypy 是權威驗證（見下方「重構與 diagnostics 查證義務」） |
| 註解/字串/config 值/日誌/TODO；Markdown、YAML、TOML、JSON 等非程式碼 | rg | LSP 不索引非程式碼內容 |
| 檔案搜尋（按名稱模式） | fd | LSP 不處理檔案系統 |

（`goToDefinition`／`workspaceSymbol`／`documentSymbol`／`incoming·outgoingCalls` 等標準 operation 語義跨 harness 一致、可推導；ZCode 端型別面由 code-reality-lsp-bridge 承接，非原生 LSP）

## LSP 驗證任務 workflow（5 步）

1. **依 rule 選工具** — 先依 [查詢路由 rule](../../rules/symbol-query-routing.md) 驗在場／freshness，再使用對應查詢或明示 fallback。
2. **Verify with evidence** — 禁「looks correct」，一律驗簽名/回傳/呼叫鏈
3. **Trace full chains** — 被問函式 → 同時追 incomingCalls + outgoingCalls
4. **Report precise locations** — 每個 finding 附 `file:line`
5. **Cross-verify** — 結果非預期時用 Read 交叉確認

## 重構與 diagnostics 查證義務

- rename、改簽名或回傳型別前必查全呼叫點：首選 code-reality refs/callers；缺場用 LSP `findReferences`。rg 可能漏動態引用，不可單獨作完整性證據。
- 編輯後驗證順序：Edit → ruff → `check_file` 即時診斷 → mypy 權威完整型別檢查 → pytest；diagnostics 不取代 mypy。Claude 編輯後自動推送 diagnostics 時同 turn 修正，其他 harness 主動觸發。

（驗證輸出 4 段格式——State question / Show operation / file:line finding / ✅❌ conclusion——見下方專段）

## 反例群：rg 的陷阱（符號查詢 + 依賴枚舉）

- `rg "<ServiceClient>\("` 結果被截斷（只顯示 `n`），只能「推測」呼叫端；`LSP findReferences` 精準列出結構化 references（定義 + import + 型別註解 + 唯一實際呼叫點）。
- **audit 覆蓋判斷（真實案例）**：`rg "list_.*_classes" tests/` → 0 hits，audit 誤報「多個 class 無 membership 斷言」。實際測試用不同符號（列舉函式 / registry 變數），LSP `findReferences` 可找到。**符號覆蓋判斷用 rg 會因命名 pattern 差異 false negative**。
- **judge-review 查證（真實案例）**：審查者 rg 稱「`<ExecutorClass>` 在 `<module>.py` 無建構點」，LSP `findReferences` 立刻列出 import 行 + 建構行。**符號存在性查證用 rg 會因 pattern 失誤 false negative，把「自己沒查到」誤判為「不存在」**。
- **rg display masking（真實案例）**：`rg "_update_x_axis_labels"` 把 method 名 mask 成 `n`（輸出 `def n(self) -> None:`）—— **看起來像真實輸出但不是**。masking 比 truncation 更危險：truncation 是「少給」（你知道有漏），masking 是「給錯的」（誤以為查到了，停止往下查）。符號引用查詢依 rule 路由取得結構證據，不能以失真的文字輸出下結論。
- **toplevel-only pattern 漏 local import（真實案例）**：`rg "^from <package>"` 只抓 toplevel import，漏掉函式內的 `from <package>.<module> import ...  # noqa: PLC0415`（local import，被刻意降級以規避循環依賴）。local import 往往是「開發者知道是違規但就地掩蓋」的信號（`# noqa: PLC0415` 是指紋）— 恰恰是最該被抓出的結構債。**依賴分析不可只錨 `^` toplevel**；需搭配 LSP `findReferences`（涵蓋 import 行 + call site）或 rg 不錨 `^` + 篩 `noqa: PLC0415`。

**結論**：rg 可能 truncated／漏查／pattern 失誤／masking；CR／LSP 提供可解析範圍的結構證據，仍受 source 新鮮度、索引與查詢 coverage 限制，不保證動態引用完整或輸出無截斷。依 rule 路由查證並列未覆蓋面，zero hits 不證明不存在。**依賴枚舉用錨定 `^` toplevel 會系統性漏一整類（local import）**。

## 方法論限制 loopback（報告內部一致性）

> **此段解決「自審與作答共享盲點」**：方法論限制段承認了工具的認知邊界（如「未 LSP 驗證」「rg 可能漏 local import」），但結論段若沒回照這個邊界，會產生**自相矛盾的報告** — 限制段說「可能漏」，結論卻斷言「不存在 / 未發現」。這不是工具問題，是報告紀律問題。

**強制 step**：報告完成前，對「方法論限制段」列出的每一項認知邊界，檢查「結論段 / 發現段」是否回照：

| 方法論限制段的承認 | 結論段必須 |
|------------------|-----------|
| 「未 LSP 驗證」 | 該結論標「未確認」而非斷言；或說明為何仍可信 |
| 「rg 可能漏 local import」 | 依賴邊的「未發現」結論改為「toplevel 未發現，local import 未驗證」 |
| 「測試覆蓋 proxy 非行覆蓋率」 | 「薄覆蓋」結論標明是 proxy 訊號 |

**反例（本規則的觸發源）**：依賴審計報告的 methodology limitation 段寫「rg `^from` 無法捕捉函式內 lazy import」，但 🔴 反向耦合段的 feed 結論卻寫「feed → workflows 邊不存在」。兩段自相矛盾 — 限制段承認可能漏，結論卻斷言不存在 — 卻沒被發現，因為寫限制與下結論是同一個 LLM 的同一個信念體系（自審與作答共享盲點，理論基礎見 [acceptance-evidence](../../rules/acceptance-evidence.md)「證據獨立性」）。

> **通用性**：此 loopback 紀律雖在 LSP/rg 場景觸發，但適用任何「方法論限制段 vs 結論段」的組合 — 工具限制、測試覆蓋、取樣口徑皆同。

## 優先級規則：task prompt 條件句不覆蓋全域規則

task prompt 寫「若有 LSP 工具可用...無 LSP 則用 rg」是**提醒確認可用性**，**不是授權默認假設無 LSP**。工具在場、freshness 與 fallback 依 [查詢路由 rule](../../rules/symbol-query-routing.md)；條件句不構成跳過在場確認的理由，也不能把既有 cr-first 路由改成固定 LSP-first。工單工具／唯讀限制仍按 rule 處理。

> **真實失誤案例（本規則的觸發源）**：分析任務全程用 rg，理由是「task prompt 寫若有 LSP 則用」。實際上 LSP 工具可用，但 LLM (a) 誤讀條件句為「預設 rg」、(b) 全程未調用 LSP、(c) 被提醒後用 `timeout` 命令（shell 工具）測試並下結論「LSP 不可用」 — 三重失誤全因缺強制啟動 step。

## Agent Prompt 工具選擇

> **核心原則**：spawn agent 時，prompt 必須依查詢路由 rule 與任務性質指定實際工具。禁止只寫「驗證/讀取/確認」不指定工具（always-on 摘要見 rules 端 tool-discipline「工具選擇原則」）。

**Agent prompt 工具指定模板**：

```
# 工具選擇（必填）
- 簽名/型別/定義位置 → 依 rules/symbol-query-routing.md 指定查詢；LSP 適用時用 hover / goToDefinition
- 呼叫鏈/引用 → 依同一 rule 指定 CR 或 fallback；LSP 適用時用 outgoingCalls / incomingCalls / findReferences
- 文字搜尋（字串、註解、config）→ 用 rg
- 檔案搜尋 → 用 fd
- Cython 模組（.pyx/.so）→ 用 rg + Read（LSP 不索引 Cython）
- audit-test 域 2（Traceability）覆蓋判斷 → 禁用單一 rg pattern；registry membership / class 引用 / method call 依 rule 取得結構證據，另查字串/config 與動態入口
- judge-review 符號查證 → 「X 是否存在 / 在哪引用」依 rule 查詢；CR/LSP/rg 0 hits 均不可直接下「不存在」結論
```

**判斷方式**：任務描述含「簽名」「型別」「定義」「呼叫」「繼承」「Protocol」→ 依 rule 的符號／型別路由；含「字串」「註解」「config」「檔案路徑」→ 依文字／檔案路由，不另定工具優先序。

## 跨 harness LSP 載體對照

當一個概念跨 harness 通用但呼叫方式不同時，用對照表表達（中性化規範的「跨 harness 載體對照」pattern，見 [rules/AGENTS.md](../../rules/AGENTS.md)）：

| harness | LSP 機制 | 呼叫方式 |
|---------|---------|---------|
| Claude Code | 原生 plugin set（pyright/rust-analyzer/clangd/gopls/jdtls/...）| `LSP` tool（native，非 MCP），參數 `operation`/`filePath`/`line`/`character` |
| ZCode | 無原生 → 現行：符號走 cr index（`pyrefly-index`／SCIP）、型別走 `code-reality-lsp-bridge`（lsp-python MCP 2026-08-28 起停擺，見下「現況」註） | 舊形態（歷史）：單一 `mcp__lsp-python__lsp(operation=...)` tool（mosaic_alpha `tools/lsp_mcp/server.py` 參考實作；CC-aligned dispatch） |
| 未來無 native 的 harness | 用 MCP server 支援 | mosaic_alpha `lsp-python` 為 reference impl（per-project http server） |

LSP operation 語義一致，差異只在載體（native tool vs MCP tool）— 決策樹、反例、驗證 workflow 跨 harness 通用。mosaic_alpha `lsp-python` MCP 已進一步對齊 CC：單一 tool + `operation` 參數 + camelCase operation 值，跨 harness 呼叫結構一致（差異僅 `LSP` vs `mcp__lsp-python__lsp` 前綴）。goToImplementation：CC 有、ZCode pyright 不支援（`implementationProvider` 未實作）。

ZCode 無原生 LSP：型別面由 code-reality-lsp-bridge 承接（.py→pyrefly、.rs→rust-analyzer）；pyright-langserver 是 harvest golden oracle，禁解除安裝。

## Workspace 狀態相依性（reindex 後再下結論）

LSP 結果是 workspace 狀態相依的 — 若 `findReferences` 回傳意外少的結果（尤其對 `_`-prefixed 私有 symbol），**先觸發 workspace reindex 再下結論**，不要直接推論為工具固有 false-negative。

> **⚠️ 現況（2026-08-28 起）**：`lsp-python` MCP server 已停擺（:8000 無 listener；退役屬 cr-lsp roadmap）——ZCode 符號面 LSP dispatch 無載體：符號查詢走 cr index（`pyrefly-index`／SCIP）、型別面走 `code-reality-lsp-bridge`。下方 reindex 觸發與條件式 fallback 兩節為 lsp-python 時代的歷史設計記錄（CC 端原生 LSP 的 stale 處置概念仍可參考）。

| harness | reindex 觸發 |
|---------|-------------|
| ZCode | `mcp__lsp-python__lsp(operation="reloadWorkspace")`（git 操作後、或符號查詢結果異常少時呼叫）。行為依 transport：**http**（共用 WorkspacePool）5-10s 重建 client；**stdio**（無 pool）回降級訊息、需手動重啟 server 觸發 reindex |
| Claude Code | 原生 plugin **無 reloadWorkspace**（檔案變更自動推送 diagnostics，但 git rebase/reset 大幅變動後仍可能過時；stale 時無法主動 reindex → 見下「條件式 fallback」）|

**真實案例（cross-harness 驗證）**：同一 `_PREV_COUNT` 符號（mosaic_alpha `structure/wave_scalars.py:50`），Claude session `findReferences` 只回傳 intra-file ref（誤判為工具對私有 symbol 的 false-negative），ZCode session 卻成功回傳跨檔引用 — 差異根因是 pyright workspace reindex 時機，非 LSP 對私有 symbol 的固有限制。**兩 session 結果矛盾時，先懷疑 workspace 狀態，再懷疑工具能力。**

> **符號查詢的預設繞道（2026-08-27 起，不再 Rust 限定）**：code-reality index 在場（`~/.mosaic/code-reality/scip/<repo>/` 或 code-reality MCP 工具可用）時，符號查詢**優先** code-reality（MCP `refs`/`callers`／CLI `scip_refs`＋`--callers`/`--closure` 旗標；`[SRC]` provenance＋stale WARN）——免 workspace stale、跨 session 一致。**雙語料**：Rust＝rust-analyzer SCIP；**Python＝`pyrefly-index`**（code-reality producer；refs 密度低於 LSP 面是已知語義，詳 code-reality skill）。index 缺場/過期 → 重建（Python 跑 `pyrefly-index --repo <repo>`）或退 LSP＋標「未 index 驗證」。**LSP 保留面**：Rust hover／型別簽名（P2 橋接前）、documentSymbol 即時形、working-tree 即時性（index 是 build-time 產物）——Python hover／diagnostics 已由 `code-reality-lsp-bridge` 承接（2026-08-28 P1；bridge 缺場退 LSP，詳 rule「核心原則（cr-first 路由）」段）。

### 條件式 fallback（無原生 reloadWorkspace 的 harness）

CC 原生 LSP plugin **無 `reloadWorkspace`** —— workspace stale（冷啟動 index 未完成、git 大幅變動）時，原生 `findReferences` 回可疑少（典型症狀：只回 intra-file refs、跨檔全消失），無法主動 reindex 只能乾等。當時的解法（**lsp-python 時代設計，server 已於 2026-08-28 停擺——見上「現況」註**）：連接 `lsp-python` MCP（http 模式，ZCode 當時在用的同一 server）作**條件式 fallback**（非常駐取代原生）：

1. 原生 `findReferences` 回**可疑少**（只 intra-file / 跨檔消失）→ 判 stale，**非符號沒人用**
2. → 切 MCP `lsp` dispatch 立刻拿正確跨檔結果（`mcp__lsp-python__lsp(operation="findReferences", ...)`——**單一 dispatch tool**，Claude/ZCode 同 server 同 API；`symbol_name` + `current_file`（name-based）或 `line` + `character`（position-based）皆可，兩組參數同一 tool，無「分立 references tool」）
3. 必要時 `mcp__lsp-python__lsp(operation="reloadWorkspace")`（http 有效；stdio 降級）觸發 reindex

**refs 數比對差異**：原生 `findReferences` 含定義點，MCP `lsp(operation="findReferences")` 不含 → 同符號原生恆多 1，語義一致；行號隨 index 漂移（未提交改動 + reindex），比 refs「數」與跨檔覆蓋非精確行號。

**reload_workspace 對原生恢復的因果（實測）**：觀測 reload_workspace 後原生也從 stale 恢復，但 T0→reload→T3 間有時間推移，原生冷啟動本就背景 indexing，可能「時間到了」（相關非因果）。**fallback 成立不依賴此點** — MCP 立刻給正確答案才是核心。

## 跨命令共用的 LSP 驗證輸出格式

每次 LSP 驗證任務（驗證特定 claim、refs 查證、call chain 追蹤）產出依此格式：

1. **State the question** — 釐清要驗證什麼（例：「`Strategy.on_bar()` 的簽名是否正確？」）
2. **Show the LSP operation used** — 明示用了哪個 LSP operation（例：`LSP hover on Strategy.on_bar`）
3. **Report the finding with precise file:line** — 每個 finding 附 `file_path:line_number`（禁「looks correct」，必須引用實際位置）
4. **Give a clear ✅/❌ conclusion** — 結論明確（通過/不通過），不留模糊

> 此格式跨 audit-test / judge-review / illustrate verify drill / arch-thinking 驗證段通用。工具驗證特定結構 claim；整體架構判斷結合 use case、契約與證據，由消費命令決定交付機器 finding 或人類 viewport。
