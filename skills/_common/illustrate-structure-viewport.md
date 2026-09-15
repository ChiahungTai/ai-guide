# 結構 viewport — drill 與機械分工

> **載體**：[illustrate.md](../illustrate/SKILL.md) 的結構 viewport 模式（人類 viewport，B 軸）支撐檔。
> **能力來源**：[arch-thinking](../arch-thinking/SKILL.md) 的設計判準與觸發表，按需讀重用、state／補償、結構證據配方。本檔定義人類 viewport 的 drill、呈現與人類閱讀深度；finding 形式由 code-review 定義。

## drill 指令（whole-picture → 嫌疑）

whole-picture 渲染完（city map / flows / boundaries / 重用枚舉，資料來自 skill），人用 drill 深入：

```
artifact <type> <target>  — mid-session 切 active menu artifact（如 `artifact sequence <use-case>`、`artifact class-slice <module>`、`artifact data-flow <field>`、`artifact call-graph <symbol>`）；type 見 [illustrate-artifact-menu](./illustrate-artifact-menu.md) 詞彙表
city <module>      — 放大某模組的依賴細節（= boundary artifact）
flow <use-case>    — 畫另一個 use case 的 flow（= sequence artifact）
reuse <候選>       — 以符號或檔案定位候選，依 reuse.md 判語義相容性；呈現端可自行附候選 ID
verify <symbol>    — 鎖定嫌疑，依 symbol-query-routing 查證引用／呼叫關係與契約
boundary <module>  — 細看某模組邊界（= boundary artifact）

> menu artifact selection replaces 舊鬆散 運作流程/資料流/概念圖 labels；drill switches artifact，verify stays reactive。
```

或用自然語言描述「這感覺在重造什麼」。完成後說 `done` 或 `summary`。

## Phase 2：互動式調查

人提 whole-picture 線索，LLM 做精確查證：

| Type | 人類說什麼 | LLM 調查 |
|------|------------|----------|
| 🔗 重用嫌疑 | 「這感覺跟那個重複」 | 依 [reuse.md](../arch-thinking/reuse.md) 找候選並判語義／invariant／ownership／依賴成本 |
| 🗺️ 結構可疑 | 「這依賴怪怪的」 | 依結構證據配方取得呼叫／依賴關係，工具依 symbol-query-routing |
| 📐 邊界 | 「這不該在這模組」 | 查跨域存取與實際契約，對照 authority／修改責任 |
| 💬 Free-form | 任意 | 自動分類或直接回答 |

## 機械分工（何時用哪個工具）

> **核心**：依 arch-thinking 觸發表取得候選與結構證據，工具選擇遵循 [symbol-query-routing](../../rules/symbol-query-routing.md)。初始結論已有來源與限制；人鎖定嫌疑後進一步查證，不將第一次驗證延後到人開口。

| 子任務 | 工具 | 角色 |
|--------|------|------|
| 取得結構與重用候選 | arch-thinking 觸發表及對應配方 | 提供已查範圍、來源與限制；工具路由依 symbol-query-routing |
| 人鎖定「這 enum 跟那 enum 可能重疊」後驗證 | reuse 配方＋symbol-query-routing | 核對語義及消費者，不以相似度定共用 |
| City Map / Flows 渲染 | /illustrate | 渲染引擎（人 viewport） |

> LSP 是**反應式驗證**（驗證特定 claim → ✅/❌），不是 holistic 架構判讀 —— 判讀是人的 whole-picture 工作。它是查證 helper，不是結構判讀本身。

## 位置標示（可點擊）

標定 symbol / 檔案位置用 **repo-root 相對路徑 + 行號**（如 `data/fetcher.py:15`），讓 VSCode terminal Cmd+Click 可跳轉 —— 人類 viewport 判讀需要能鑽進 code 看嫌疑。純檔名 terminal 解析不到。

## city map 導航深度（審 authority 時）

city map 預設渲染到**模組層**（不過載）。但 user 審 **authority / 資料流**（問「誰發布 X」「X 權威源」「data vs exec client」）時，加一層「**欄位 ← 發布者**」annotation —— 導航從「模組→符號」下到「**欄位→發布者**」，user 不用再追問權威源。

範例：`<欄位> ← <發布 client>`（如 `<balance> ← <exec_client>`、`<price> ← <data_client>`——替換成你的專案符號）。

**觸發判準**：authority 語境才加（避免噪音）；一般結構檢視不加。

## drift rendering 格式（drift checkpoint — post-EP / post-build）

drift detection 細節（5 signal class / baseline degradation ladder / no-severity 硬規）見 [illustrate-artifact-menu](./illustrate-artifact-menu.md)「Drift Overlay Spec」——本檔定義 viewport 端渲染格式。

**Console**：ASCII call graph with drift markers（`+`/`-`/`!` inline on edges + legend mapping marker→signal-class；對應 3 bucket：added / removed-broken / violated）。

**MD**：Mermaid `flowchart`/`classDiagram` with **3 styled bucket**（max-3-styled-group 硬限制，marker 重用 style 不倍增）：added`{+edge,+type}` / removed-broken`{-edge,broken-caller}` / violated`{boundary-crossing}`；fill+color 成對；emoji 優先標狀態。位置用 repo-root 相對 path:line（VS Code Cmd+Click，沿用上方「位置標示」慣例）。

**no-severity 硬規**（layer-3 viewport 線）：NO severity、NO file:line fix、NO「this is wrong」verdict——僅「this moved; you judge direction」。每個 drift-rendering site 重複此 constraint，防 audience split 崩潰。

## Selective Review Matrix（既有 core 審查 artifact）

**既有 core 骨幹審查（無 change，純審穩固度）的 P1 產物**：core/leaf 證據來自 [arch-thinking 的結構證據配方](../arch-thinking/structure-evidence.md)。本消費端將證據映射成人類審查方式：core → 逐行閱讀關鍵政策與消費路徑；中間層 → structure viewport＋spot-read；已確認影響局部、非 critical path 的 leaf → behavior-only。證據不足先補查，不以零 caller 或檔案類型放行。分類依據由 arch-thinking 提供，人類閱讀深度由本段定義。

**欄位**：`| 模組 | dep weight | 消費者數 | ripple/hotspot tier | domain core overlay? | core/leaf | 建議審查深度 | 位置 |`

- **位置欄**：repo-root 相對 path:line（沿用上方「位置標示」慣例，VS Code Cmd+Click 跳轉）。
- **Console**：ASCII 表；**MD**：markdown 表 + Mermaid city map（沿用 [illustrate.md](../illustrate/SKILL.md) 雙模式，MD 寫 `ai-analysis/reports/`）。

**輸出範例**：

| 模組 | dep weight | 消費者數 | ripple/hotspot tier | domain core overlay? | core/leaf | 建議審查深度 | 位置 |
|------|-----------|---------|--------------------|------------------------|-----------|--------------|------|
| common | lean | 20 | 🔴 16 mods | — | core | deep | common/enums.py |
| data | heavy | 7 | 🔴 cluster | ✅ 除權息 | core | deep | data/catalogs/... |
| ui | heavy | 0 | 🟢 terminal | — | leaf | behavior-only | ui/__init__.py |

## Final Summary

```
## 結構 viewport Summary

### Context
- Scope: <module> / EP / 變更
- 覆蓋: City Map | Flows | Boundaries | 重用枚舉

### 結構判定
| 項目 | 判定 | 說明 |
|------|------|------|
| 分層 / 依賴方向 | ✅/⚠️/❌ | ... |
| 邊界 | ... | ... |
| 重用（whole-picture） | N 嫌疑 | ... |

### Confirmed 重用 / 結構問題
| ID | 類型 | 位置 | 判定 | Action |

### Items for Discussion
| # | 嫌疑 | 確認問題 |
```
