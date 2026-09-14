---
name: audit-test

description: "測試品質稽核 — 反模式偵測、覆蓋對稱性、mock 健康度。只讀不寫。"
when_to_use: "Audit test quality: detect anti-patterns, coverage gaps, and over-mocking. Use after /implement, before /commit, or in scheduled scans. Read-only report, does not modify any files."
argument-hint: "/audit-test — uncommitted | /audit-test fd7a50e8 — commit | /audit-test --daily — 全專案"
allowed-tools: ["Read", "Bash"]
---

# /audit-test — 測試品質稽核

偵測**通過但品質差**的測試。`ruff` 抓語法問題，`/fix-test` 修失敗測試，本命令抓**隱性品質問題**。

方法論定義見 [test-driven-development](../test-driven-development/SKILL.md)（反模式定義）；覆蓋對稱性（source↔test 對應）的判定流程定義在本檔角度 2。通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/多層驗證）見 [review-engine](../review-engine/SKILL.md)。

> **audit-test 是 review 執行預設的例外**：review 執行預設（force 獨立 / max-agents / 3-perspective / mode 判定，見 [review-engine](../review-engine/SKILL.md)「review 執行預設」）適用 ep-review/code-review/execution-plan/implement；**audit-test 是 read-only 偵測器**（不做平行 3-perspective、不 mode 判定；Daily Scan 分段落盤的 `{agent}` 命名見「長任務 findings 落盤策略」段），僅共用通用審查邏輯（spawn 失敗處理仍走 [agent-workflow](../agent-workflow/SKILL.md) general 階梯）。

---

## 價值定位

| 工具 | 抓什麼 | 不抓什麼 |
|------|--------|---------|
| `ruff` / `mypy` | 語法、型別、import | 測試邏輯品質 |
| `/fix-test` | **已失敗**的測試（分類 A/B/C/D/E 再修） | **通過但有反模式**的測試 |
| **`/audit-test`** | **通過但有反模式的測試** | 語法問題（交給 ruff） |

測試通過 ≠ 測試有價值。幽靈斷言的測試永遠通過，但它驗證不了任何事。

---

## 三種輸入模式

| 模式 | 參數 | 掃描範圍 | 場景 |
|------|------|---------|------|
| **Diff Audit** | 無參數 | uncommitted test files | pre-commit gate |
| **Commit Audit** | `fd7a50e8` | 該 commit 的 test file 變更 | post-commit review |
| **Daily Scan** | `--daily` | 全部 test files | 週期排程（排程載體條件段）→ append `### 🔍 audit-test` section 進 daily-report |

### 掃描範圍判定

**Diff Audit**：`git diff HEAD` + `git diff --cached` 中 `tests/` 下的 `.py` 檔案。
**Commit Audit**：`git show <commit-id> --stat` 中 `tests/` 下的 `.py` 檔案。讀取 commit diff 取得完整 test body。
**Daily Scan**：`fd -e py . tests/` 全部 test files。受影響的 source files = 所有被 import 的模組。

### 長任務 findings 落盤策略（Daily Scan 必讀）

> Daily Scan 涵蓋數百 test files，單一 agent 可能跑數十分鐘。**必須假設會中斷**（rate limit、context 上限、network），findings 即時落盤，避免 resume 重跑。

1. **分段輸出**：每完成一個子任務（一個 test 目錄 / 一組 test files），立即將該段 findings 寫入中間檔案（如 `ai-analysis/audit-test-daily-scan-{date}-{agent}.partial.md`），不在 context 中累積全部 findings 才一次輸出
2. **進度標記**：每段含進度標記（如 `<!-- agent=2, segment=3/8, completed=true -->`），resume 時讀 `.partial.md` 判斷已完成段落
3. **彙整**：全部子任務完成後，讀所有 `.partial.md` 彙整成最終報告，刪除中間檔
4. **resume**：中斷後 resume 先讀 `.partial.md`，只重跑未完成段落

**反例（真實案例）**：某 Daily Scan agent 跑多個子任務，findings 全留 context，彙整前因 rate limit 中斷 → resume 需完整重跑全部子任務。即時落盤則只需重跑中斷時正在做的那一段。

---

## 檢查角度

| # | 角度 | 對應標準 | 嚴重程度 |
|---|------|---------|---------|
| 1 | 反模式掃描 | test-driven-development SKILL.md（5 項） | Critical / Important |
| 2 | 覆蓋對稱性 | 本檔角度 2 判定流程（+ quality-constraints 符號 vs 路徑覆蓋） | Important |
| 3 | Mock 健康度 | test-driven-development SKILL.md（Mock 階層） | Important |
| 4 | 消費端驗證覆蓋 | acceptance-evidence L3 + quality-constraints 符號 vs 路徑覆蓋 | Important / Suggestion |
| 5 | 漸進驗證合規 | quality-constraints 漸進式驗證（DEPTH-MIN 集合） | Suggestion |
| 6 | 測試必要性 | acceptance-evidence 證據時效性 | Important / Suggestion |
| 7 | 變異測試抽查（mutation-testing-lite） | acceptance-evidence L2 獨立性塌縮（機械量測面） | Critical（survived 真實缺口） |

---

## 檢查角度詳細定義

### 角度 1：反模式掃描

對每個 test function，逐一檢查以下 5 項反模式（定義見 [test-driven-development](../test-driven-development/SKILL.md)）：

| 反模式 | 偵測方式 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|---------|
| **幽靈斷言** | 掃描 assert 語句品質 | Important | test body 只有 `assert result is not None` / `assert len > 0` / 無 assert；或 assert 存在但與 docstring 描述的行為無關 |
| **同義反覆** | 比對 test 與 source 的 hardcoded 值 | Important | test 的 expected value 和 source code 中的值完全相同（同一個 magic number 兩邊各寫一次） |
| **空殼覆蓋** | 掃描 test body 結構 | Critical | test function 只有 `pass` / `...` / `@pytest.mark.skip`（無 reason 或 reason 不含 "EP 標記"） |
| **過度 mock** | 計算 mock/assert 比例 | Important | test file 中 `@patch` / `Mock()` / `mock_` 出現次數 > `assert` 出現次數 |
| **標題不符** | 比對 test name 與 assert 內容 | Suggestion | test function name 暗示測某行為（如 `test_dividend_calculation`），但 assert 驗證的是另一件事（如只檢查 type） |

**偵測方式**：

1. 讀取 test file，提取所有 test function（名稱、docstring、body）
2. 對每個 test function：
   - 計算 assert 數量和類型
   - 計算 mock 數量（`@patch`、`Mock()`、`mock_` 變數）
   - 比對 docstring/test name 語義與 assert 實際驗證對象
   - 檢查是否有 `@skip`、`pass`、`...`
3. 讀取對應的 source file，比對 hardcoded 值

### 角度 2：覆蓋對稱性

**核心原則**：修改了 source code，必須有對應的 test 驗證。

| 檢查項 | 嚴重程度 | 驗證方式 |
|--------|---------|---------|
| 修改了 `.py` 但沒有修改對應 test（或最近 N 個 commit 都沒改 test） | Important | 比對 `git diff` 中 source files vs test files |
| 新增了 public class/function 但無 test 引用 | Important | 見下方「覆蓋搜尋策略」 |
| test file 存在但對應 source file 已刪除 | Important | `test -f` 驗證 source 存在 |
| 新增 registry 成員（auto-discovery）但無 membership 斷言 | Important | 見下方「Registry Membership 流程」（多工具交叉，**禁用單一 rg pattern**）；per-class 單元測試只 import 不代表接上 registry（見 [quality-constraints](../../rules/quality-constraints.md) 符號 vs 路徑覆蓋） |

**判斷邏輯**：
- Source `foo.py` → 對應 test `test_foo.py`（同名慣例）為主要測試檔案
- 新增 class/function 在 `__init__.py` 或 `__all__` → 搜尋所有 test files

**覆蓋搜尋策略**（區分 function vs method）：

覆蓋判斷必須區分三種粒度，不可一概用 import 搜尋：

| 粒度 | 搜尋方式 | 範例 |
|------|---------|------|
| **standalone function** | `rg "from module import func"` 或 `rg "func("` in tests | `rg "compute_adj_factors" tests/` |
| **class 本身** | `rg "from module import ClassName"` in tests | `rg "TWSecurityIndex" tests/` |
| **class method** | 找到 class 的 import 後，追蹤 instance 上的 method call | 見下方 Method Coverage 流程 |

**Method Coverage 流程**（避免將有覆蓋的方法誤判為零覆蓋）：

1. **建立候選清單**：從 source file 提取所有 public method（排除 `_` 開頭）
2. **找測試檔案**：不只看同名 `test_foo.py`，用 `rg "ClassName" tests/ -l` 找所有引用該 class 的 test files
3. **搜尋 method call**：對每個候選 method，在所有找到的 test files 中搜尋 `.method_name(` pattern
4. **判定零覆蓋**：只有當 method 在**所有** test files 中都不出現時，才判定為零覆蓋
5. **交叉驗證**：報告前用 `rg "\.method_name\(" tests/` 確認，避免單一檔案掃描遺漏

**Registry Membership 流程**（避免單一 rg pattern 造成 false positive）：

> ⚠️ **教訓（真實案例）**：audit 用單一 rg pattern（如 `rg "list_.*_classes" tests/`）判斷 membership 斷言存在與否，但專案可能用不同符號（列舉函式 `list_*_classes()`、registry 變數 `*_REGISTRY`、registry module 的 import）。**單一 pattern 0 hits ≠ 斷言不存在**，必須多工具交叉。

1. **候選符號清單**：從 source file 提取 registry 的所有可能符號（registry 變數名 `*_REGISTRY`、列舉函式 `list_*_classes()` / `<enum_classes>()`、registry module 的 import）
2. **多工具交叉搜尋**（至少兩個獨立途徑）：
   - `rg "<registry_var>" tests/ -l`（找直接引用 registry 變數的 test files）
   - **LSP `findReferences`**（從 registry 變數定義找所有引用點 — 100% 涵蓋，含動態引用，避免 pattern 失誤）
   - `rg "<ClassName>.*(in|__name__).*<registry>" tests/`（找 per-class membership 斷言的多種寫法）
3. **檔案存在性用 fd + ls 雙查**：`fd "<test_name>" tests/` 0 results 時，必須 `ls <expected_dir>/` 或 `fd -g "<exact_name>.py" tests/` 確認 — **不能單靠 fd 結果下結論**（gitignore、pattern 差異會造成 false negative）
4. **判定零覆蓋**：只有當上述多個工具都 0 hits 時，才判定為零覆蓋
5. **報告前交叉驗證**：報告中列出「已查的工具與結果」，讓 reviewer 可複現

### 角度 3：Mock 健康度

**核心原則**：Mock 應該用最少代價隔離外部依賴，不是把被測系統也隔離掉。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| Mock 比例 > 50%（mock 數 > assert 數） | Important | test file 層級計算 |
| Mock 被測對象本身（mock 了正在測的 class） | Critical | `@patch("module.ClassUnderTest")` — 如果 mock 了主角，測試什麼？ |
| Mock 層級過低（patch private method / 內部函數） | Suggestion | patch 路徑含 `_` 開頭的函數 |
| 未使用繼承式 Mock（可用但未用） | Suggestion | 多個 test 用相同 `@patch` 組合 → 建議抽取 `MockClient(RealClient)` |
| **`type(obj).attr = PropertyMock(...)` patch 真實 class** | Important | 見下方「PropertyMock type-level 危險性」 |

#### PropertyMock type-level 危險性

`type(obj).attr = PropertyMock(...)` 是 class-level patch，跨測試殘留風險真實。但**是否危險取決於 `obj` 的型別**：

| `obj` 型別 | 風險 | 判定 |
|-----------|------|------|
| `MagicMock` instance / 純 mock fixture | 🟢 安全 | `type(obj)` 是 mock 類型，patch 不影響真實 class |
| 真實 class instance（fixture 回傳 `RealClass()`） | 🔴 危險 | `type(obj)` 是真實 class，patch 污染整個 class，跨測試殘留 |

**調查 / 修改前的強制義務**：

1. **確認 fixture 回傳型別**：用 LSP `hover` / `goToDefinition` 跳到 fixture 定義，確認回傳 `MagicMock` 還是 `RealClass()`。**禁止憑 fixture 名稱猜測**（`<client_fixture>` 可能回傳真實 `<ServiceClient>`，不是 mock）
2. **必讀專案踩雷指南**：修改 PropertyMock 前，讀專案 `tests/CLAUDE.md` 的 mock 規範段落（每個專案可能有不同的 PropertyMock 例外規則）

**反例（真實案例）**：audit 稱某 `type(obj).attr = PropertyMock(...)` 多餘可刪，認為 fixture 回傳 mock；實作查證推翻 — fixture 回傳**真實 class**，該行是唯一讓某狀態（如某個 boolean 連線旗標）成立的機制，不能刪。調查前未確認 fixture 型別。

### 角度 4：消費端驗證覆蓋

**核心原則**：功能是給特定消費端用的，單元測試通過 ≠ 功能可用。**符號覆蓋（symbol 出現在 tests）≠ 整合路徑覆蓋（新參數 / 新接線 / 多組件組合被實際驅動）** — 見 [acceptance-evidence](../../rules/acceptance-evidence.md) L3 + [quality-constraints](../../rules/quality-constraints.md) 符號 vs 路徑覆蓋。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| 新增 public 參數 / 注入點但消費端路徑無測試 | **Important** | `rg "<新參數>=" tests/` → 0 hits，或 hits 僅符號 import 非路徑驅動 |
| 整合器型變更（接 ≥2 真實組件）只在 unit test 驗證 | **Important** | 缺真實邊界整合測試（`integration_tests/`），mock 循環論證風險 |
| 修改了 library 模組但只在 unit test 驗證 | Suggestion | source 在 library 層，test 只在 `tests/unit_tests/` |
| 修改了共用模組但未跑跨模組測試 | Suggestion | 修改的模組被 ≥ 2 個 test directory 引用 |

消費端驗證模式定義見 [quality-constraints](../../rules/quality-constraints.md) 的「消費端驗證模式」段。

### 角度 5：漸進驗證合規

**核心原則**：測試集應有 DEPTH-MIN 子集可快速確認基本邏輯。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| 無 DEPTH-MIN / smoke test marker | Suggestion | `tests/` 下無 `@pytest.mark.quick` / `@pytest.mark.smoke` 或對應 marker |
| 全部測試都是慢速（無分層） | Suggestion | `pytest.ini` / `pyproject.toml` 無 marker 定義 |

定義見 [quality-constraints](../../rules/quality-constraints.md) 漸進式驗證（DEPTH-MIN→SAMPLE→FULL）。

### 角度 6：測試必要性

**核心原則**：過時測試比沒測試更危險 — 它給虛假信心。角度 1-5 假設「測試該存在」，本角度質疑「測試還有必要存在嗎」。理論見 [acceptance-evidence](../../rules/acceptance-evidence.md)「證據時效性」。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| 過時測試（重構後 assertion 被改成迎合實作） | Important | 測試在最近重構 commit 被改，改動是 assertion 值/邏輯迎合新實作（非新增案例）— 從「驗證意圖」降級為「反映實作」（同義反覆的動態版本） |
| 死測試（還在過但驗證行為已無關） | Important | 測試斷言的行為與當前 EP/spec 無對應；或測試的消費端已不存在 |
| 大型重構後未重評估的測試 | Suggestion | 重構（行為語意改變）後，受影響測試未被重新檢視必要性 |

**過時偵測流程**：

1. `git log --oneline -20` 找最近重構 commit（行為語意改變，非純重命名/格式）
2. `git show <commit> --stat` 找該 commit 改動的 test files
3. 對這些 test files，diff 看改動是「assertion 值/邏輯迎合新實作」（過時信號）還是「新增測試案例」（正常）
4. **判定「迎合」標準並報告**：assertion 改成等於新實作輸出（literal value 追隨），而非新增獨立案例 — 需讀完整 test body 判斷（不能只看 diff 的 `+/-` 行，rename 也會產生 diff）。若不確定，標「需實作查證」而非定論。**判定為迎合 → 過時信號，報 Important**

**與角度 1 的區別**：角度 1「同義反覆」是靜態（test/source 同值）；角度 6「過時」是動態（重構後 test 被改迎合）。角度 1 抓不到動態漂移。

**與靜態隱含覆蓋的區別（/smell-detector zoom 判準 2 收窄後的分界）**：本角度（動態過時）與「靜態他處已測 = 冗餘」語義不同 — 後者指測試的行為已被**另一個測試**隱含驅動。分界：**production wrapper 重複測試**（測 thin wrapper 且 wrapper 無獨立 production 入口）的判斷見 [smell-detector zoom mode](../smell-detector/zoom.md) 判準 2；**其餘靜態冗餘**（同行為不同入口重複測等）屬本命令（角度 1 反模式 / 角度 6 測試必要性）；本段角度 6 聚焦動態過時。

**3-signal correlation（升級 2-signal → 3-signal，捕 intent drift）**：判讀 passing test 是真通過還是 silent drift，單看「過時」（動態）不夠 —— 須關聯三訊號：① 原始 test intent（story / 建立時擷取）② 當前 test result ③ 引入的 code changes。三者不一致 = intent drift 訊號（test 還過但已不驗原意圖）。coverage 增加也不保證 test 仍驗意圖。3-signal taxonomy 見 [acceptance-evidence skill](../acceptance-evidence/SKILL.md)「Intent Drift 的兩型 + 3-signal correlation」（rule 端 always-on 核心見 [acceptance-evidence](../../rules/acceptance-evidence.md)）。

### 角度 7：變異測試抽查（mutation-testing-lite）

**核心原則**：AI 同寫 test+impl 的同義反覆，靜態掃描（角度 1）抓不到其真實形態——實測（mosaic 2026-08-30 spike，mutmut 3.7.0 scoped）證明盲區不是 `assert x==x` 廢話型，而是**測試與 impl 共享同一組典型數字**（happy path 斷言具體、邊界值系統性缺席：0、1、恰好一半、price<1 這類金融商品邊界）。只有機械突變能把這種盲區變成可數的 survived 名單。

**形態＝scoped 手跑抽查，非常態 gate**（spike 裁決）。**雙 trigger**：
- **①變更觸發**：審計對象（本週變更的 tests/）含 silent-corruption critical path（會計/風控/單位邊界）且用戶明示或 EP 要求深度驗證。
- **②存量輪抽查（週期 trigger 必跑一個）**：spot audit 只看本週變更——**零變更的舊測試不在掃描半徑**（真實案例 2026-08-30：mosaic test_cash_tracker.py 舊測試、當週零 commits，變異缺口只被 ad-hoc spike 抓到）。週期 audit-test 跑時從 repo 的 **critical path 模組清單**（來源：AGENTS.md ripple/風控標記、dependency-graph hotspots）**輪選一個**（最久未跑者優先；輪選狀態由 report 歷史或 repo 自存小檔推導）跑 scoped mutmut＋survived 全抽讀。每模組機械成本 ~秒級、不增加常態負擔。

**執行**（mutmut 3 形態；POC 暫存性，結束零足跡清除）：
1. 挑 1-2 個 critical path 的 source+test（窄：全量會跑不完）
2. `uv add --dev mutmut`；scoped config：`[tool.mutmut]` 的 `source_paths`（copy 全 package 保 import）＋`only_mutate`（目標檔 glob）＋`pytest_add_cli_args_test_selection`（目標測試檔）
3. `mutmut run`；記錄三數字：總耗時／mutant 總數／killed:survived
4. **survived 必抽讀分類**（主成本在此，非機械跑）：(a) 真實測試缺口（斷言沒鎖行為/邊界）(b) equivalent mutant（語義等價，殺不死是正常的）(c) 無實務意義的極端邊界——每個附 file:line 與 mutated operator
5. 報告：(a) 類缺口列 Critical finding（測試補強項）；清除聲明（mutants/ 目錄＋pyproject config 段＋dep＋uv.lock 還原）。**輸出落點**：open 項照既有慣例 append 進 daily report；跨 repo open 項 hub-relay 落消費端 pending-decisions inbox（mosaic 例：`ai-analysis/_inbox/pending-decisions.md`——2026-09-02 三池重構後路徑，每日 report「⏳ 待裁決」節吸收，修復可見性）

**成本實證**（供報價）：288 行 critical path＋68 tests＝8.2s wall、103 mutants、87.4% kill rate、13 survived 抽讀約 10 分鐘 LLM 判讀——抓到 10 個真實缺口（含 price<1 會計＋風控雙處無保護）；補強後重跑同模組＝100:3（97.1%）、殘留 3 皆 (b)(c) 類——**輪抽查基準用補強後數字，勿把已修缺口重報**（mosaic memory `project-mutation-testing-spike-t32` 有收案記錄，承接先查勿重做）。

---

## 輸出格式

### 報告模板

```markdown
## Audit-Test Report

### 總覽

| 指標 | 數值 |
|------|------|
| 掃描模式 | Diff Audit / Commit Audit / Daily Scan |
| 掃描範圍 | N 個 test files |
| 健康度 | XX% |

### 🔴 Critical（必須修正）

> Critical 只能是 `[confirmed]` 或 `[evidence-based]`，禁止 `[inferred]`（見「Audit 誠信約束」）。

- [ ] **[空殼覆蓋]** `[confirmed]` `test_<module>.py:test_<case>:NN` — test body 只有 `pass`（讀過原始碼確認）
- [ ] **[Mock 被測對象]** `[confirmed]` `test_<module>.py:test_<case>:NN` — `@patch("<module>.<ClassUnderTest>")` mock 了主角

### 🟡 Important（建議修正）

- [ ] **[幽靈斷言]** `[confirmed]` `test_<module>.py:test_<case>:NN` — 只有 `assert result is not None`
- [ ] **[過度 mock]** `[evidence-based]` `test_<module>.py` — N 個 mock / M 個 assert（比例 X:1）
- [ ] **[覆蓋缺口]** `[evidence-based]` `<module>.py:<func>` — `rg "<func>" tests/` → 0 hits。⚠️ 單一 rg，建議下游用 LSP `findReferences` 交叉確認
- [ ] **[同義反覆]** `[confirmed]` `test_<module>.py:test_<case>:NN` — test 和 source 都 hardcode 同一值

### 💡 Suggestion（可以改善）

- [ ] **[標題不符]** `[confirmed]` `test_<module>.py:test_<case>` — 名稱暗示測 X，但 assert 驗證 Y
- [ ] **[消費端缺驗證]** `[evidence-based]` `<module>.py` 修改只在 unit test 驗證，建議跑 integration
- [ ] **[Mock 層級過低]** `[confirmed]` `test_<module>.py:test_<case>:NN` — patch `_internal()`（private method）
- [ ] **[技術判斷]** `[inferred]` ⚠️ 未實證：宣稱「<套件行為>」基於推理。**禁止列 Critical**，建議實作層跑 demo 確認

### 建議處理方式

| 反模式 | 處理路徑 |
|--------|---------|
| 空殼覆蓋 | `/fix-test --redesign` 或刪除空殼 test |
| 幽靈斷言 | 補充具體業務值斷言（先理解測試意圖） |
| 過度 mock | 重構為繼承式 Mock 或 Real-World Fixture Pattern |
| 覆蓋缺口 | 新增測試（RED → GREEN） |
| 消費端缺驗證 | 在消費端上下文中跑一次完整流程 |

### Audit Summary（結構化結論）

- mode: diff|commit|daily
- files_scanned: N
- critical: X（全為 confirmed/evidence-based）
- important: X（含 Y inferred，已標 ⚠️）
- suggestion: X
- health_score: XX%
- needs_action: true/false
- **findings_nature: 待驗證（非定論）** — 建議經 judge-review / 實作查證後再行動
```

### 健康度計算

```
健康度 = (通過檢查的 test function 數 / 總 test function 數) × 100%
```

每個 test function 的觸發檢查項全通過 = 1 個通過。任一 Critical/Important = 不通過。
Diff/Commit Audit 檢查 5 角度（反模式 + 覆蓋對稱性 + mock 健康度 + 消費端驗證覆蓋 + 測試必要性），Daily Scan 檢查全部 6 角度。

| 評分 | 意義 |
|------|------|
| ≥ 90% | ✅ 健康 |
| 70-89% | ⚠️ 需注意 |
| < 70% | ❌ 需修正 |

---

## 執行流程

| 步驟 | 名稱 | 觸發 |
|------|------|------|
| 1 | 定位掃描範圍 | 預設 |
| 2 | 讀取 test files | 預設 |
| 3 | 讀取對應 source files | 預設 |
| 4 | 反模式掃描（角度 1） | 預設 |
| 5 | 覆蓋對稱性（角度 2） | 預設 |
| 6 | Mock 健康度（角度 3） | 預設 |
| 7 | 消費端驗證覆蓋（角度 4） | 預設 |
| 8 | 漸進驗證合規（角度 5） | `--daily` |
| 9 | 測試必要性（角度 6） | 預設 |
| 10 | 產出報告 | 預設 |

### 步驟 1：定位掃描範圍

**Diff Audit**：
```bash
git diff HEAD --name-only -- "tests/"
git diff --cached --name-only -- "tests/"
```

**Commit Audit**：
```bash
git show <commit-id> --name-only -- "tests/"
```

**Daily Scan**：
```bash
fd -e py . tests/
```

### 步驟 2：讀取 test files

完整讀取掃描範圍內的每個 test file，提取：
- test function 名稱、docstring、body
- `@patch` / `Mock()` / `mock_` 數量
- `assert` 數量和類型
- `@skip` / `pass` / `...` 標記

### 步驟 3：讀取對應 source files

從 test files 的 import 語句推斷 source files，讀取以比對 hardcoded 值。

### 步驟 4-9：逐一檢查

對每個 test function，按角度 1-3 的標準檢查（步驟 4-6）。步驟 7-9（角度 4/5/6）按各自角度定義段落執行。記錄發現。

### 步驟 10：產出報告

按輸出格式模板產出報告。Daily Scan 時由排程載體（週期條件段）直接 append `### 🔍 audit-test` section 進 daily-report（test-quality 在報告裡有自己的 section）；手動跑的 claude-sync log 落點慣例隨 claude -p 載體退役一併停用。

---

## 與其他命令的協作

| 命令 | 與 /audit-test 的關係 |
|------|---------------------|
| `/fix-test` | 互補：fix-test 修**失敗**的測試，audit-test 偵測**通過但品質差**的測試 |
| 排程載體（週期條件段） | Daily Scan 結果直接 append `### 🔍 audit-test` section 進 daily-report |
| `/code-review` | Correctness 軸可引用 audit-test 發現 |
| `/implement` | 段落完成後跑 audit-test 確認測試品質 |
| `/commit` | pre-commit gate：audit-test 無 Critical 才建議 commit |

### 測試品質完整流程

```
寫測試 → /audit-test（偵測反模式）→ 發現問題 → 人類判斷
  ├─ 簡單修正（改名、補斷言）→ 直接改
  ├─ 重構測試（過度 mock → Real-World Fixture）→ /implement 段落
  └─ 刪除壞測試（空殼）→ 確認後刪除
```

### 設計不良測試的處理路徑

| 情境 | 工具 | 說明 |
|------|------|------|
| 測試**失敗**了 | `/fix-test` | 分類 A/B/C/D/E → 修 source 或修 test |
| 測試**通過但有反模式** | `/audit-test` → 人類判斷 → 對話修正 | 偵測 → 報告 → 決策 → 執行 |
| 需要從頭重寫壞測試 | `/implement` 段落或對話指令 | 按反模式修正建議重寫 |

**核心原則**：修正反模式需要**理解測試意圖**，無法全自動。`/audit-test` 是偵測器（眼睛），不是修復器（手）。修復的決策權在人類。

---

## Audit 誠信約束

> audit 是偵測器（眼睛），不是判官。偵測結果可能 false positive，必須以「可被下一層（judge-review / 實作查證）推翻」的心態輸出。
>
> **stance 釐清**：「偵測器非判官 + read-only」是 audit-test 專屬 stance（只產 findings 不下判）。通用誠信「findings 非定論」見 [review-engine](../review-engine/SKILL.md) — code-review/ep-review 要下判（給結論/commit/回寫），適用通用誠信但不適用偵測器 stance。

### 1. Findings 不是定論 — 標示信心水準

信心水準定義（confirmed / evidence-based / inferred + Critical 必須 confirmed 或 evidence-based，禁止 inferred）見 [review-engine](../review-engine/SKILL.md) 信心水準段。本命令每個 finding 必須標信心水準，讓下游（judge-review / 實作查證）知道哪些需重點查證。

test 場景的信心判準參考：confirmed = 已讀完整 test body + source 比對符號；evidence-based = 有 file:line + rg/fd 結果（角度 2 多數覆蓋缺口）；inferred = 基於套件行為推理（如「無 seed → 不 deterministic」）。

### 2. 技術 / 套件行為判斷必須實證

對「套件行為」「演算法行為」「數值特性」的判斷（如「無 seed → 不 deterministic」「浮點運算 → 誤差累積」「此 API 會 raise」），**不能只靠推理**。判斷前必須：

- 寫最小 demo（`uv run python -c "..."` 或獨立腳本）實際跑一次，或
- 引用套件 source（`.venv/lib/python*/site-packages/<pkg>/`）具體行號佐證，或
- 標「inferred」+「未實證」並降級為 Suggestion

**反例（真實案例）**：audit 稱「<ML 訓練庫> 無 seed → 每次訓練結果不同」並列為 Critical。實驗推翻（同 config 兩次訓練結果完全相同，該庫有預設 seed）。**推理看起來合理但與套件實際行為不符**。

### 3. Findings 輸出格式（嚴格）

每個 finding 必須包含（缺一即不合格）：

- **file:line**（精確位置，不能只寫檔名）
- **證據**（rg/fd/LSP 指令 + 結果，或原始碼引用）
- **角度 + 嚴重程度 + 信心水準**
- **建議**（具體可執行，不是「建議改善」）

**禁止**：把多個 finding 壓成摘要（如「2 Critical + 4 Important」）回報 — 摘要丟失 file:line，下游無法定位。摘要只能作為總覽表格，**明細必須完整保留**。

### 4. 多層驗證設計意圖

audit-test → judge-review → 實作查證 是**刻意設計的三層**，每一層都可能錯：

| 層 | 抓什麼錯 |
|---|---------|
| audit（偵測器） | 測試品質問題（主要產出 findings） |
| judge-review（審查者） | audit 的 false positive / 過度陳述 |
| 實作查證（最終） | judge-review 的查證失誤 / 調查 agent 誤判 |

---

## 執行約束

- **只讀不寫**：本命令只檢查和報告，不自動修改任何檔案
- **必須讀取實際程式碼**：不憑檔名猜測測試品質，必須讀取 test body
- **引用來源**：報告問題時標註具體位置（test file:function name）
- **繁體中文輸出**：報告使用繁體中文 + 英文術語
- **不重複 ruff 工作**：語法問題交給 ruff，本命令只關注邏輯品質

---

## 反思閉環（大型 Daily Scan 後執行）

> 每次 Daily Scan 涵蓋全專案、產出數十 findings，是真實流程經驗的富礦，**不提煉等於浪費**。本段定義大型 audit 後的反思流程。

### 觸發條件

- Daily Scan 完成且 findings ≥ 20（Critical + Important + Suggestion 總和）
- 或 judge-review / 實作查證階段發現 ≥ 3 個 audit false positive / over-statement
- 或長任務因 rate limit / context 中斷重跑

### 反思流程

1. **收集教訓**：哪些 finding 被 judge-review 推翻？哪些被實作查證推翻？哪些技術判斷推理錯？哪些流程造成重跑？
2. **歸因到 ai-guide 具體段落**：每個教訓對應哪個 rules/skills 檔案的哪段不足？是規範缺（沒寫）還是規範有但 agent 沒讀？
3. **產出改進建議**：寫到 `ai-analysis/audit-test-improvement-proposals-{date}.md`（不直接改規範，使用者 review 後併入）
4. **滾動更新**：建議被採納後更新對應段落，下次 audit 自動受惠

### 反思的反思

反思本身也可能 over-engineering。判斷標準：

- **該提煉**：同類問題在 ≥ 2 次 audit 反覆出現（結構性 gap）
- **不該提煉**：單一偶發案例（個案，不值得改規範）

避免把每個個案都上升成規範 — 規範膨脹會降低 signal/noise ratio。
