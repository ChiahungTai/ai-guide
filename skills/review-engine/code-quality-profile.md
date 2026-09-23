# Code Quality Profile — code 六軸審查（what to check）

> 前身＝`code-review-and-quality` skill（AIR-113 reference-demotion：退出 resident 注入面、內容降為 review-engine 的 profile reference）。本檔是 code review 的 **profile 定義源**；觸發與執行走 `/code-review` 命令，通用審查邏輯（嚴重度分級、信心水準、審查者自證、LSP 查證方法、Writer-Reviewer 分離、多層驗證）真相源在 [review-engine](SKILL.md)。

Six-axis review with quality gates. Every change gets reviewed before merge — no exceptions.

**Approve when the change definitely improves overall code health**, even if it isn't perfect. Don't block because it isn't exactly how you would have written it.

## The Six-Axis Review

### 1. Correctness

> **lens vs checklist 邊界**：Correctness **lens**（base perspective，所有 review 共用的視角）定義在 [review-engine](SKILL.md) 點 4 ③；本段是 **checklist**（what to check 細節，profile 層）。

- Matches spec/task requirements?
- Edge cases handled (null, empty, boundary values)?
- Error paths handled (not just happy path)?
- **Loud→silent regression**（diff 改 error handling 時必查）：diff 含 `raise`→`return None`、新增/拓寬 `try/except`、crash→filter、validation 緩步化時，flag 為**潛在 silent-corruption 引入**。「error paths handled」檢查的是**有無**錯誤路徑；本項檢查的是 diff 是否**把原本大聲的錯誤靜默化**——loud→silent 危險（會炸卻靜默腐敗下游），silent→loud 安全（虛驚、測試推翻）。不限交易 critical path，任何 error-path 改動都套用。見 [acceptance-evidence](../../rules/acceptance-evidence.md)「silent vs loud 不對稱風險」。
- **錯誤處理點系統化枚舉**（diff 語義觸及錯誤處理時啟動——新增/修改任一類點）：**六類點** × **五維**逐點過：
  - 六類點：try/except（含 Result 型）；error callback／error event handler；error-state 條件分支；fallback logic／failure default value；log-and-continue（記 log 後執行續行）；optional chaining／null coalescing 可能吞錯
  - 五維：① logging 品質（context 足夠六個月後 debug？）② 使用者回饋（具體、可行動？）③ catch 具體性（只抓預期型別？會吞哪些非預期錯誤——枚舉出來）④ fallback 行為（spec/用戶明確請求？是否掩蓋底層問題？production fallback 到 mock/stub ＝ 架構問題）⑤ 錯誤傳播（該上拋卻就地吞？吞掉是否阻斷 cleanup／resource 管理）
  - 通則：silent failure 不可接受、fallback 必須顯式且 justified、catch 必須具體。與上方 loud→silent 檢查互補——該項抓「把大聲改小聲」的 diff 語義，本枚舉抓「每個錯誤處理點的處理品質」
- Tests cover the change and actually test the right things?
- Off-by-one errors, race conditions, state inconsistencies?
  - 多 writer / state mutation invariant 破壞的判定（ownership vs write-site 粒度）見 [arch-thinking 的 state 配方](../arch-thinking/state-and-compensation.md)「變更路徑計數（mutation-path counting）」—— 條件必填（觸及 mutable state 時）

### 2. Readability & Simplicity
- Names descriptive and consistent with project conventions?
- Control flow straightforward?
- Could this be done in fewer lines? (1000 lines where 100 suffice is a failure)
- Are abstractions earning their complexity? (Don't generalize until the third use case)
- Dead code artifacts: no-op variables, backwards-compat shims, `// removed` comments?

### 3. Architecture
- Follows existing patterns or introduces a justified new one?
- Clean module boundaries, dependencies flowing in right direction?
- Appropriate abstraction level (not over-engineered, not too coupled)?

**測試架構六項（diff 含 test files 時啟用——軸B；v3.1 測試契約）**：審這次 diff 的整體測試邏輯作為系統守不守得住（架構面）。本節是六項的**定義源**；啟用 wiring（dual-context 兩側注入／axis 3 觸發）見 [code-review](../code-review/SKILL.md)。

| # | 項 | 判準 |
|---|---|---|
| 1 | 拓撲 vs blast radius | 測試拓撲與變更 blast radius 對稱——高 ripple 低覆蓋→finding |
| 2 | 層級平衡 | unit/integration 分佈與變更性質匹配（整合器型變更 unit-only→finding） |
| 3 | 符號≠路徑 | 掛引用 [audit-test 域 2 消費端路徑證據](../audit-test/SKILL.md)，不重複定義 |
| 4 | evidence fidelity | 測試宣稱的證據等級與實際機制相符——標 E2E 實為 mock 鏈→finding。**機械觸發問句：mock 回傳值是否參與期望值推導鏈？**（是→evidence 降級 finding——MVP 實證 lite tier 對此形態漏檢，問句強制觸發不靠語意判斷） |
| 5 | shared dependency | 測試間共享狀態/fixture 污染面（跨測試殘留、order-dependent flake） |
| 6 | 耦合面 | test 與 impl 耦合深度（斷言綁實作細節非行為面） |

**排除面（防越權回流）**：翻譯忠實度（test↔TC 逐條對帳）不歸軸B——歸 [audit-test](../audit-test/SKILL.md) TC 契約對帳（域 2 第一 gate；軸A 機械對帳）。與 ### 1 Correctness「Tests cover the change and actually test the right things?」的分工：**結構面充分性**（測試架構守不守得住）由本六項判；**逐條 TC 對帳**由 audit-test 軸A 判——本檔審測試架構時不做逐條對帳。

### 4. Security

- User input validated and sanitized?
- Secrets kept out of code, logs, and version control?
- SQL queries parameterized, outputs encoded for XSS?
- External data (APIs, logs, user content, config files) treated as untrusted?

### 5. Performance

- N+1 query patterns? Unbounded loops or data fetching?
- Missing pagination on list endpoints?
- Large objects created in hot paths?

### 6. Capability Coverage

For projects using UC-Driven Development, verify implementation against module instruction files' Capabilities tables (AGENTS.md preferred, CLAUDE.md legacy).

- Does implementation cover all Capabilities-defined behaviors?
- Are Capabilities-referenced behaviors present in the diff?
- EP segment capability references consistent with Capabilities tables or backlog cards?
- Capabilities entry points point to library modules (not scripts/ — scripts/ is demo entry, not capability)?
- Implementation covers all consumer scenarios (happy path, error handling, boundaries, performance expectations)?
- Skip for small changes (bug fix, docs)

## Review Process

### Step 1: Understand Context
- What is this change trying to accomplish?
- What spec or task does it implement?

### Step 2: Review Tests First
Tests reveal intent and coverage:
- Do they test behavior (not implementation details)?
- Edge cases covered?
- Would they catch a regression?

### Step 3: Review Implementation
Walk through code with the six axes.

### Step 4: Categorize Findings

嚴重度分級（3 級：Critical / Important / Suggestion）+ 信心水準標註見 [review-engine](SKILL.md) 嚴重度框架與信心水準段。Nit/FYI 已併入 Suggestion（統一 3 級，理由見 review-engine）。

### Step 5: Verify Verification
- What tests were run? Did the build pass?
- Manual testing done? Screenshots for UI changes?

## HIGH SIGNAL filter（finding 訊噪比政策 — code-review profile）

> 源：Anthropic plugin review 方法論吸收（通則化重寫，AIR-28）。**適用邊界**：本 filter 是 code-review 軌（change review 產 findings）的訊噪比政策，**非全域**——ep-review 的結構／覆蓋類 Important/Suggestion、audit-test 的偵測報告（recall 導向）不受此限（全域化會壓掉合法 findings）。單一源於本節；review-engine 只收全命令適用的歸因條款（見其「審查者自證」），不收本 filter。

**只 flag HIGH SIGNAL**（審 diff 找 bug／違規時）：

- code 會編譯／解析失敗（syntax error、type error、missing import、unresolved reference）
- 不論輸入為何**必然**產生錯誤結果（明確邏輯錯誤）
- 明確無歧義的 instruction 檔違反，且能**逐字引用**被違反的規則原文

**DO NOT flag**（六條）：

1. **Pre-existing issues**（mixed-tree 歸因）：非「永不提」——是不報為**本次 diff 新引入**；baseline 態已存在的問題標 `pre-existing` 或不報，不計入回歸
2. **看似 bug 實為正確**：刻意行為、guard 條件、呼叫端契約（flag 前先查呼叫端是否已保證前提）
3. **Pedantic nitpicks**：senior engineer 不會 flag 的
4. **Linter 會抓的**（禁為驗證而跑 linter——lint 預檢見 [code-review](../code-review/SKILL.md)「Lint 預檢」節，是該命令的獨立步驟）
5. **通用 code quality 顧慮**（測試覆蓋率、一般性安全建議）——**僅 instruction 檔明示要求時才報**（本 repo load-bearing：Capabilities／測試規範明示者為契約，非泛化偏好）
6. **instruction 檔提及但 code 已顯式靜默的**（如 lint ignore comment）——已記錄的決策事實，非新違規

**不確定是否真實 → 不 flag**：false positive 侵蝕信任、消耗 judge 注意力——訊噪比是 findings 的品質單位。

## Dead Code Hygiene

After refactoring, check for orphaned code. **Deletion is a no-impact self-claim** ("zero callers") — treat it as Claim→Evidence→Trust: independently verify across the **full consumer surface** before removing; don't trust the author/commit self-claim (see [acceptance-evidence](../../rules/acceptance-evidence.md) Claim→Evidence→Trust「刪除/死碼自述同理」). This is the routine-review counterpart of what `/smell-detector` zoom 判準 1 does on demand — the gap it fills is that post-build `/code-review` previously trusted the self-claim.

**Full consumer surface for "zero callers"** (LSP findReferences alone is insufficient — it misses dynamic dispatch and non-library consumers):
- LSP `findReferences` (static imports)
- rg the symbol name across .py/.yaml/.json — including `scripts/`, `lab/`, demo, `poc/`, saved configs (not just the module's own tree)
- dynamic dispatch: getattr/importlib, registry auto-discovery, StrEnum string-values-in-config
- for whole-file / whole-class deletion: actually execute an import of the affected consumers (`uv run python -c "import <consumer>"`) — static zero-hit ≠ runtime zero-consumer

```
DEAD CODE IDENTIFIED:
- formatLegacyDate() — replaced by formatDate()
- OldTaskCard component — replaced by TaskCard
→ Verified zero callers across full surface? (LSP + rg scripts/lab/configs + import test)
```

## Architecture Doc Drift Reminder

> 補 axis 6（只看「改到目錄的 Capabilities 表」）的盲區：**跨模組結構變更 → 架構文檔可能需更新**。code-review 是 read-only，只 **flag 提醒**（finding 指向 owner tool），不做 sync、不重複 [doc-health](../doc-health/SKILL.md) 的 accuracy check（doc-health 問「文件準確嗎」；本項問「這結構變更該不該觸發文檔更新提醒」——正交）。

**觸發（structural signal — 非 file-count；1-file 高 ripple 也觸發，file-count gate 會漏此類改動）**：
- 新增 / 移除 / 改名 module（目錄）或 top-level package
- 新增 / 移除跨模組 import edge（尤其新依賴方向：反向耦合、新循環）
- 觸及已知 hub / ripple component（讀專案的跨模組依賴文檔——如 root AGENTS.md 的熱點表、`dependency-graph.md` 的 ripple rules（若存在）——比對 diff 是否碰 listed component）
- 新抽象層 / 新公開 Protocol / 新跨模組 base class
- fallback：≥3 files 跨多模組

**提醒對象 + owner（finding 指向，不自己做 sync）**：

| 架構文檔 | owner | 何時該更新 |
|---|---|---|
| `dependency-graph.md`（per-repo opt-in） | 無自動 owner（人工策展） | 新/移/改名 module、import edge 變、hub component 改 — **無 build-time owner，最易 silent drift** |
| 模組 AGENTS.md 架構段 / `architecture.md` | build 5b（未跑 /implement 則手動） | 設計決策 / 新抽象 / 模組結構 / 依賴方向 變更 |
| `SYSTEM-MAP.md`（lifecycle） | metadata-sync / build 5a | 功能生命週期變化（新功能完成、狀態升級） |

**嚴重度**：Suggestion（mild signal）→ Important（強信號：新/移除 module 必更 `dependency-graph.md`——在持有此檔的 repo）。

**不適用**：docs mode（純文檔審查本身就是改文檔；本提醒是「code 變更 → 架構文檔忘了跟」）。

## 通用審查邏輯（見 review-engine）

以下通用邏輯已移至 [review-engine](SKILL.md)，本檔不重複（避免跨命令 drift）：

- **嚴重度分級 + 信心水準**（原 5 級含 Nit/FYI → 統一 3 級 Critical/Important/Suggestion + confirmed/evidence-based/inferred；Critical 禁止 inferred）
- **審查者自證 / 誠信**（原 Reviewer Self-Verification + Honesty in Review — 每 claim 必須查證、findings 非定論、對外部行為判斷必須實證、不 rubber-stamp）
- **查證方法 + 自我否證義務**（查詢路由依 [symbol-query-routing](../../rules/symbol-query-routing.md)；證據範圍與「找不到 ≠ 不存在」依 review-engine）
- **Writer-Reviewer 分離 + 多層驗證**（原 Multi-Model Review Pattern — 獨立 context 審查避免自審、review→judge→followup 各層都可能錯）

See also: [review-engine](SKILL.md)（通用審查邏輯真相源）
