---
name: audit-test

description: "存量測試品質稽核 — 五證據域（Semantic Integrity／Traceability & Evidence Depth／Adversarial Strength／Test-System Integrity／Suite Operability）、vacuous-green 條件式斷言、oracle 分級 S/H/I/N、mutation 條件 gate；night-mode 夜間補強生產線。只讀不寫（night-mode P4 例外——紅線內只寫 tests/fixtures）。"
when_to_use: "Audit existing/legacy test suite strength — five evidence domains, vacuous-green guard-assertion detection, oracle authority grading (S/H/I/N), mutation conditional gates. Use after /implement, before /commit (Diff/Commit Audit), or via the night-mode reinforcement pipeline (--night; Daily Scan absorbed into night-mode)."
argument-hint: "/audit-test — uncommitted | /audit-test fd7a50e8 — commit | /audit-test --night — 夜間補強管線"
allowed-tools: ["Read", "Bash", "Agent", "Edit", "Write"]
---

# /audit-test — 存量測試品質稽核（五證據域）

偵測**通過但品質差**的測試。`ruff` 抓語法問題，`/fix-test` 修失敗測試，本命令抓**隱性品質問題**。定位＝**存量補強場景**：程式碼跑一段時間後回頭稽核測試強度並補強——建造管線（RED 流程）屬 [test-driven-development](../test-driven-development/SKILL.md) 領域。

方法論定義見 [test-driven-development](../test-driven-development/SKILL.md)（反模式定義）；behavior impact evidence（行為影響查詢，非 source↔test diff 對稱）的判定流程定義在本檔域 2。通用審查邏輯（嚴重度/信心水準/審查者自證/LSP 查證/多層驗證）見 [review-engine](../review-engine/SKILL.md)。

> **audit-test 是 review 執行預設的例外**：review 執行預設（force 獨立／風險 profile context 配置／mode 判定，見 [review-engine](../review-engine/SKILL.md)「review 執行預設」）適用 ep-review/code-review/execution-plan/implement；**audit-test 是 read-only 偵測器**（不做平行多腿配置、不 mode 判定；night-mode P1/P2 分段落盤的 `{agent}` 命名見 night-mode 節「長任務 findings 落盤策略」段），僅共用通用審查邏輯（spawn 失敗處理仍走 [agent-workflow](../agent-workflow/SKILL.md) general 階梯）。
>
> **與 review profile 覆蓋的關係（S1 證據復用——不固定全量重跑）**：既有 review（弧級／段級，帳本 header 帶 identity）的 `coverage` 已含**相同 test 的相同審核軸**時，本命令引用該證據不重跑——復用判準五條（同基線／同實物內容／scope 覆蓋／profile 相容／證據可讀）見 [workflow-review-pattern](../_common/workflow-review-pattern.md)「findings 去重與復用判準」；scope 新增的 test 檔補審。test 特有 mandate（反模式／mock 危險形態／mutation 抽查等域 detector）保留，不因 profile 覆蓋而省——profile 覆蓋只吸收**相同軸**；**複用 findings 不等於複用測試**——環境／config／input 改變時驗證證據另行失效（同 workflow-review-pattern 不變項）。

---

## 價值定位

| 工具 | 抓什麼 | 不抓什麼 |
|------|--------|---------|
| `ruff` / `mypy` | 語法、型別、import | 測試邏輯品質 |
| `/fix-test` | **已失敗**的測試（分類 A/B/C/D/E 再修） | **通過但有反模式**的測試 |
| **`/audit-test`** | **通過但有反模式的測試** | 語法問題（交給 ruff） |

測試通過 ≠ 測試有價值。幽靈斷言的測試永遠通過，但它驗證不了任何事。

---

## 輸入模式與掃描範圍

| 模式 | 參數 | 掃描範圍 | 場景 |
|------|------|---------|------|
| **Diff Audit** | 無參數 | uncommitted test files | pre-commit gate（接點不變——`/commit` pre-commit gate 消費本命令輸出） |
| **Commit Audit** | `fd7a50e8` | 該 commit 的 test file 變更 | post-commit review |
| **night-mode** | `--night` | target manifest 凍結範圍（契約 1） | 週期排程補強生產線——**Daily Scan 已被 night-mode 吸收**（night-mode 即 Daily 的強化形態；管線見「night-mode 補強生產線」節） |

### 掃描範圍判定

**Diff Audit**：`git diff HEAD` + `git diff --cached` 中 `tests/` 下的 `.py` 檔案。
**Commit Audit**：`git show <commit-id> --stat` 中 `tests/` 下的 `.py` 檔案。讀取 commit diff 取得完整 test body。
**night-mode**：範圍由 P1 前凍結的 target manifest 決定（見 night-mode 節契約 1），非無差別全掃。

---

## 五證據域（存量稽核主體）

| 域 | 抓什麼 | 核心 detector |
|---|---|---|
| 1 **Semantic Integrity** | 測試本身說的是真話嗎 | 反模式、vacuous-green、mock 危險形態、測試必要性 |
| 2 **Traceability & Evidence Depth** | 行為影響有證據嗎、來源可追溯嗎 | TC 契約對帳（第一 gate）、behavior impact evidence、出生證明查核 |
| 3 **Adversarial Strength** | 斷言經得起突變嗎 | mutation 三層 gate＋週期輪抽 |
| 4 **Test-System Integrity** | 測試系統自身健全嗎 | fixture provenance、隔離／污染 |
| 5 **Suite Operability** | 套件跑得動、結果穩嗎 | collect 健康、flake、skip 盤點 |

### 域 1：Semantic Integrity

#### 反模式掃描

對每個 test function，逐一檢查以下反模式（定義見 [test-driven-development](../test-driven-development/SKILL.md)）：

| 反模式 | 偵測方式 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|---------|
| **幽靈斷言** | 掃描 assert 語句品質 | Important | test body 只有 `assert result is not None` / `assert len > 0` / 無 assert；或 assert 存在但與 docstring 描述的行為無關 |
| **同義反覆** | 比對 test 與 source 的 hardcoded 值 | Important | test 的 expected value 和 source code 中的值完全相同（同一個 magic number 兩邊各寫一次） |
| **空殼覆蓋** | 掃描 test body 結構 | Critical | test function 只有 `pass` / `...` / `@pytest.mark.skip`（無 reason 或 reason 不含 "EP 標記"） |
| **標題不符** | 比對 test name 與 assert 內容 | Suggestion | test function name 暗示測某行為（如 `test_dividend_calculation`），但 assert 驗證的是另一件事（如只檢查 type） |

**偵測方式**：

1. 讀取 test file，提取所有 test function（名稱、docstring、body）
2. 對每個 test function：
   - 檢查 assert 數量和類型（類型語義，非計數）
   - 比對 docstring/test name 語義與 assert 實際驗證對象
   - 檢查是否有 `@skip`、`pass`、`...`
3. 讀取對應的 source file，比對 hardcoded 值

#### vacuous-green（綠燈但零驗證）

**核心原則**：綠燈但**不可能紅**的測試——green 不承載任何證偽力。問「這個 green 在什麼輸入變化下會變紅？」答不出具體變化 → vacuous-green。與 oracle 分級強相關：**N oracle（無 oracle）測試是 vacuous-green 高風險群**——兩偵測器獨立跑、findings 互相引用。

| 訊號 | 偵測方式 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|---------|
| **條件式斷言（守衛無 else-fail）** | 掃 test body 的 if/try/with 包 assert 結構，核對 else／fail 路徑存在 | **Important** | 條件不成立時斷言從未執行、測試靜默通過（test_accounting 形態：`if hasattr(strategy, "qty"): assert strategy.qty > 0`——無 `qty` 屬性時整段斷言零驗證；`try: ... except: pass` 包斷言同型） |
| 禁用斷言路徑 | 讀完整 test body 控制流 | **Important** | try/except 吞掉 assert 區、`pytest.raises` 後無後續狀態驗證 |
| skip／xfail 計入「通過」面 | 掃 marker 與 runner 設定 | **Important** | 無 reason、xfail 非 strict、TODO 型 skip 無追蹤 |
| 測試與 impl 共享同一組典型數字 | 邊界值盤點（0、1、空集、極值、域特定邊界如 price<1） | **Important** | happy path 斷言具體、邊界值系統性缺席（mutation 抽查的靜態前兆） |

#### Mock 危險形態

**核心原則**：Mock 應該用最少代價隔離外部依賴，不是把被測系統也隔離掉。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
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

#### per-repo mock 豁免教義

**被迫正確的環境 API mock 是豁免項，不是過度 mock**：某些環境 API 在測試環境無法真實存在（editor 全域、外部 provider 帳號面），mock 它們是唯一可選項——如 `vi.mock('vscode')` 形態（editor API）、NT test-kit providers（外部 provider 面）。判定＝該依賴在測試環境**是否被迫**（無法真實存在）而非「圖方便」。**豁免清單 repo 自持**（各 repo tests/ instruction 檔列自己的豁免清單）——audit-test 對清單內依賴不報 mock finding，清單外的同型 mock 仍逐案判。

#### 測試必要性

**核心原則**：過時測試比沒測試更危險 — 它給虛假信心。其餘 detector 假設「測試該存在」，本節質疑「測試還有必要存在嗎」。理論見 [acceptance-evidence](../../rules/acceptance-evidence.md)「證據時效性」。

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

**與同義反覆的區別**：反模式「同義反覆」是靜態（test/source 同值）；「過時」是動態（重構後 test 被改迎合）。同義反覆抓不到動態漂移。

**與靜態隱含覆蓋的區別（/smell-detector zoom 判準 2 收窄後的分界）**：本節（動態過時）與「靜態他處已測 = 冗餘」語義不同 — 後者指測試的行為已被**另一個測試**隱含驅動。分界：**production wrapper 重複測試**（測 thin wrapper 且 wrapper 無獨立 production 入口）的判斷見 [smell-detector zoom mode](../smell-detector/zoom.md) 判準 2；**其餘靜態冗餘**（同行為不同入口重複測等）屬本命令（域 1 反模式／測試必要性）；本節聚焦動態過時。

**3-signal correlation（升級 2-signal → 3-signal，捕 intent drift）**：判讀 passing test 是真通過還是 silent drift，單看「過時」（動態）不夠 —— 須關聯三訊號：① 原始 test intent（story / 建立時擷取）② 當前 test result ③ 引入的 code changes。三者不一致 = intent drift 訊號（test 還過但已不驗原意圖）。coverage 增加也不保證 test 仍驗意圖。3-signal taxonomy 見 [acceptance-evidence skill](../acceptance-evidence/SKILL.md)「Intent Drift 的兩型 + 3-signal correlation」（rule 端 always-on 核心見 [acceptance-evidence](../../rules/acceptance-evidence.md)）。

### 域 2：Traceability & Evidence Depth

#### TC 契約對帳（第一 gate——EP 含凍結 TC 時）

**核心原則**：凍結 TC 是契約，測試是契約的消費——本域機械對帳「測試忠實消費契約且 provenance 完整」。TC 格式（claim／Given-When／oracle／oracle_source／evidence class／uncovered）定義源＝[execution-plan](../execution-plan/SKILL.md) 測試規劃段（引用不重複定義）；三 gate 語彙（STRUCT_OK／SEM_OK／BEFORE_GREEN）與 [implement](../implement/SKILL.md) RED provenance 精確同名——對帳鍵單一套。**有凍結 TC 時本對帳是域 2 第一 gate**——先對帳再談其他覆蓋查詢。

**觸發輸入（operationalize）**：任務家 `ep.md` 探測（arc/獨立跑形態——讀 EP 整合策略有無凍結 TC 段）或 session context EP（in-context 形態）；兩者皆缺 → 對帳子節跳過（standalone 無 EP 的存量測試不適用），改走出生證明查核（下下方）。

| # | 對帳項 | 機械操作 |
|---|---|---|
| 1 | predicate 對帳 | TC predicate-ID ↔ test 斷言逐一映射（`rg <TC-ID> tests/`；缺漏列 finding） |
| 2 | mock↔evidence class | TC 標 L4-L6 的項若以 mock 驅動→finding（evidence 降級）；mock 回傳值來源比對 oracle_source |
| 3 | oracle 圓形依賴 | oracle_source 指向待測實作（或 test 硬編碼 impl 值）→Critical（此類屬 oracle 級：標記 escalate challenge，非 audit 自斷） |
| 4 | RED receipt＋digest | receipt 檔（任務家 `red-receipts.md`）存在、TC-ID 齊、sha256 與 frozen test 現值一致（不一致＝GREEN 期靜默改——Critical） |
| 5 | 基線跑法（BEFORE_GREEN） | receipt 記 failing predicate；抽查測試在 baseline（`git stash` 形態）確實紅；STRUCT_OK／SEM_OK gate 痕跡核對 |
| 6 | fixture provenance | fixture 值來源標注（歷史數據/構造）；無源 fixture 用於 oracle 級斷言→finding |
| 7 | 路徑覆蓋反查 | 掛引用：消費端路徑證據（符號≠路徑）——TC 對應消費端路徑驅動確認（下方「消費端路徑證據」），本項不重複定義 |

判斷密集項（如「mock 回傳值是否即 oracle」的 fidelity 裁決）標「需查證」交下游（judge-review／實作查證）——與「Audit 誠信約束」一致。

#### behavior impact evidence 覆蓋查詢

**核心原則（behavior impact evidence，非 diff 對稱）**：不查「source 改了 test 有沒有跟著改」（source↔test diff 對稱——開發期視角，存量場景誤導：行為未變的重構不需動 test，反之 test 檔在改也不代表行為被驗）；查「**行為影響有無測試證據**」——對稽核範圍內每個 behavior-bearing 變更（新 public 契約／行為分支改變／invariant 觸及），找驅動該行為的測試證據（符號覆蓋＋路徑驅動，缺一即缺口）。有凍結 TC 時與 TC 對帳互補（對帳查「忠實消費」，本節查「契約外的行為面漏網」）。

| 檢查項 | 嚴重程度 | 驗證方式 |
|--------|---------|---------|
| behavior-bearing 變更（public class/function 新增或行為分支改變）無測試驅動證據 | Important | 符號覆蓋搜尋（見下方覆蓋搜尋策略）＋路徑驅動確認 |
| test file 存在但對應 source file 已刪除 | Important | `test -f` 驗證 source 存在 |
| 新增 registry 成員（auto-discovery）但無 membership 斷言 | Important | 見下方「Registry Membership 流程」（多工具交叉，**禁用單一 rg pattern**）；per-class 單元測試只 import 不代表接上 registry（見 [quality-constraints](../../rules/quality-constraints.md) 符號 vs 路徑覆蓋） |

**覆蓋搜尋策略**（區分 function vs method）：

覆蓋判斷必須區分三種粒度，不可一概用 import 搜尋：

| 粒度 | 搜尋方式 | 範例 |
|------|---------|------|
| **standalone function** | `rg "from module import func"` 或 `rg "func("` in tests | `rg "compute_adj_factors" tests/` |
| **class 本身** | `rg "from module import ClassName"` in tests | `rg "TWSecurityIndex" tests/` |
| **class method** | 找到 class 的 import 後，追蹤 instance 上的 method call | 見下方 Method Coverage 流程 |

**Method Coverage 流程**（避免將有覆蓋的方法誤判為零覆蓋）：

1. **建立候選清單**：從 source file 提取所有 public method（排除 `_` 開頭）
2. **定位候選測試**：不只看同名 `test_foo.py`；`rg -l -F "ClassName" tests/` 與 `rg -F ".method_name(" tests/` 僅定位文字候選，不構成完整引用清單或 runtime 覆蓋證據
3. **追蹤 method 驅動路徑**：對每個候選 method，依 [symbol-query-routing](../../rules/symbol-query-routing.md) 查結構引用／呼叫鏈，不限於文字命中的檔案；核對 alias、繼承、`getattr`、decorator 與測試入口的實際驅動證據，CR／LSP 仍受 freshness／coverage 限制，不保證涵蓋動態引用
4. **判定覆蓋證據**：0 hits 只表示已查範圍未見引用／呼叫；未能確認的路徑標 unverified，不直接宣稱 runtime 零覆蓋；文字命中也不代表該 method 或消費端路徑已被測試驅動
5. **報告前交叉驗證**：列出已查工具、範圍、結果及測試入口／路徑驅動證據；已確認的測試缺口照既有規則列 finding，證據不足者標 unverified 並列待查面

**Registry Membership 流程**（避免單一 rg pattern 造成 false positive）：

> ⚠️ **教訓（真實案例）**：audit 用單一 rg pattern（如 `rg "list_.*_classes" tests/`）判斷 membership 斷言存在與否，但專案可能用不同符號（列舉函式 `list_*_classes()`、registry 變數 `*_REGISTRY`、registry module 的 import）。**單一 pattern 0 hits ≠ 斷言不存在**，必須多工具交叉。

1. **候選符號清單**：從 source file 提取 registry 的所有可能符號（registry 變數名 `*_REGISTRY`、列舉函式 `list_*_classes()` / `<enum_classes>()`、registry module 的 import）
2. **多工具交叉搜尋**（至少兩個獨立途徑）：
   - `rg "<registry_var>" tests/ -l`（找直接引用 registry 變數的 test files）
   - **結構引用查詢**（依 [symbol-query-routing](../../rules/symbol-query-routing.md) 選工具；從 registry 定義找可解析引用，避免文字 pattern 漏查。CR／LSP 仍受 freshness／coverage 限制，不保證涵蓋動態引用）
   - `rg "<ClassName>.*(in|__name__).*<registry>" tests/`（找 per-class membership 斷言的多種寫法）
3. **檔案存在性用 fd + ls 雙查**：`fd "<test_name>" tests/` 0 results 時，必須 `ls <expected_dir>/` 或 `fd -g "<exact_name>.py" tests/` 確認 — **不能單靠 fd 結果下結論**（gitignore、pattern 差異會造成 false negative）
4. **判定覆蓋證據**：上述工具都 0 hits 只表示已查範圍未見引用／斷言；仍須核對動態註冊與測試入口，未覆蓋面標 unverified，不直接宣稱 runtime 零覆蓋。
5. **報告前交叉驗證**：報告中列出「已查的工具與結果」，讓 reviewer 可複現

#### 消費端路徑證據

**核心原則**：功能是給特定消費端用的，單元測試通過 ≠ 功能可用。**符號覆蓋（symbol 出現在 tests）≠ 整合路徑覆蓋（新參數 / 新接線 / 多組件組合被實際驅動）** — 見 [acceptance-evidence](../../rules/acceptance-evidence.md) L3 + [quality-constraints](../../rules/quality-constraints.md) 符號 vs 路徑覆蓋。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| 新增 public 參數 / 注入點但消費端路徑無測試 | **Important** | `rg "<新參數>=" tests/` → 0 hits，或 hits 僅符號 import 非路徑驅動 |
| 整合器型變更（接 ≥2 真實組件）只在 unit test 驗證 | **Important** | 缺真實邊界整合測試（`integration_tests/`），mock 循環論證風險 |
| 修改了 library 模組但只在 unit test 驗證 | Suggestion | source 在 library 層，test 只在 `tests/unit_tests/` |
| 修改了共用模組但未跑跨模組測試 | Suggestion | 修改的模組被 ≥ 2 個 test directory 引用 |

消費端驗證模式定義見 [quality-constraints](../../rules/quality-constraints.md) 的「消費端驗證模式」段。

#### 載體對帳（production caller 驗證）

**制式步驟（night-mode manifest 與本域稽核共用）**：manifest source 須驗 production caller——被測物≠生產路徑時 invariant 零證偽力。機械式：對 manifest 每個 target 查 caller（`rg "<symbol>" <非測試目錄>` 或 code-reality callers）——零 production caller 的測試載體列 finding（Important），其全綠結果不計入覆蓋證據（0918 r2 T4 實證：16 tests 全綠釘零-caller 載體）。

#### 出生證明查核

**核心原則**：存量測試無 TC 對帳來源時**標注追蹤、非跳過**——測試無出生證明（無 EP 凍結 TC 涵蓋、無 provenance 標注）→ 標 `provenance:unknown` 列 finding（Important：oracle 來源不可追溯，證據權威無法分級）。出生證明接口（新測試側）見 [test-driven-development](../test-driven-development/SKILL.md) 出生證明段——新測試寫入 provenance 鍵（值域 S/H/I/N/unknown），audit 對讀到的鍵做一致性查核（宣稱 S/H 須能出示 anchor，否則降標）。

### 域 3：Adversarial Strength

**核心原則**：AI 同寫 test+impl 的同義反覆，靜態掃描（域 1）抓不到其真實形態——實測（mosaic 2026-08-30 spike，mutmut 3.7.0 scoped）證明盲區不是 `assert x==x` 廢話型，而是**測試與 impl 共享同一組典型數字**（happy path 斷言具體、邊界值系統性缺席：0、1、恰好一半、price<1 這類金融商品邊界）。只有機械突變能把這種盲區變成可數的 survived 名單。

#### mutation 三層 gate（條件 gate 語義）

| 層 | 觸發 | 形態 | gate 權威 |
|---|------|------|----------|
| 1 | **P0 critical path 變更弧**（會計/風控/單位邊界 silent-corruption path 在 Diff/Commit 掃描範圍內） | scoped mutmut **必跑** | **唯一 hard gate**：判定「**新增且確認 non-equivalent survivor**」→ blocking Critical（survived 抽讀分類後，真實測試缺口類） |
| 2 | 普通變更弧 | 免跑 | 無 |
| 3 | 週期輪抽（存量——見下方輪抽查） | 照舊執行 | **kill-rate drop＝investigation signal 不阻擋**（trend telemetry 無 blocking authority）；hard gate 僅層 1 形態 |

**mutation feedback 權威禁令**：survivor／mutation 結果**永不取得 oracle / expected value 修正權**——survivor 只可指出 probe 位置（哪裡缺斷言），禁用 survivor 反推或改寫 expected value／oracle（封閉迴圈防護：oracle 不變而 test 被 survivor steering 的繞道封死）。補強測試的 expected value 仍須來自 S/H oracle（分級正典見 [acceptance-evidence](../../rules/acceptance-evidence.md)「oracle authority 分級」）。

**survived 必抽讀分類**（主成本在此，非機械跑）：(a) 真實測試缺口（斷言沒鎖行為/邊界——層 1 gate 的「確認 non-equivalent survivor」）(b) equivalent mutant（語義等價，殺不死是正常的——不觸發 gate）(c) 無實務意義的極端邊界——每個附 file:line 與 mutated operator。

#### 週期輪抽查（存量——層 3 形態）

spot audit 只看本週變更——**零變更的舊測試不在掃描半徑**（真實案例 2026-08-30：mosaic test_cash_tracker.py 舊測試、當週零 commits，變異缺口只被 ad-hoc spike 抓到）。週期 audit-test 跑時從 repo 的 **critical path 模組清單**（來源：AGENTS.md ripple/風控標記、dependency-graph hotspots）**輪選一個**（最久未跑者優先；輪選狀態由 report 歷史或 repo 自存小檔推導）跑 scoped mutmut＋survived 全抽讀。每模組機械成本 ~秒級、不增加常態負擔。此輪選清單同時是 night-mode target manifest 的來源之一（night-mode 節契約 1）。

**執行**（mutmut 3 形態；POC 暫存性，結束零足跡清除）：

1. 挑 1-2 個 critical path 的 source+test（窄：全量會跑不完）
2. `uv add --dev mutmut`；scoped config：`[tool.mutmut]` 的 `source_paths`（copy 全 package 保 import）＋`only_mutate`（目標檔 glob）＋`pytest_add_cli_args_test_selection`（目標測試檔）
3. `mutmut run`；記錄三數字：總耗時／mutant 總數／killed:survived
4. survived 全抽讀分類（三分類見上）
5. 報告：(a) 類缺口列 Critical finding（測試補強項）；清除聲明（mutants/ 目錄＋pyproject config 段＋dep＋uv.lock 還原）。**輸出落點**：open 項照既有慣例 append 進 daily report；跨 repo open 項 hub-relay 落消費端 pending-decisions inbox（mosaic 例：`ai-analysis/_inbox/pending-decisions.md`——2026-09-02 三池重構後路徑，每日 report「⏳ 待裁決」節吸收，修復可見性）

**成本實證**（供報價）：288 行 critical path＋68 tests＝8.2s wall、103 mutants、87.4% kill rate、13 survived 抽讀約 10 分鐘 LLM 判讀——抓到 10 個真實缺口（含 price<1 會計＋風控雙處無保護）；補強後重跑同模組＝100:3（97.1%）、殘留 3 皆 (b)(c) 類——**輪抽查基準用補強後數字，勿把已修缺口重報**（mosaic memory `project-mutation-testing-spike-t32` 有收案記錄，承接先查勿重做）。

### 域 4：Test-System Integrity

**核心原則**：測試系統自身的健全——fixture 來源可追溯、測試互相隔離。測試系統自身腐壞時，所有綠燈不可信。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| 無源 fixture 用於 oracle 級斷言 | Important | fixture 值無來源標注（歷史數據/構造）卻用於關鍵斷言——TC 對帳缺席的存量形態（有 TC 時走對帳項 6，無 TC 時逐 fixture 查） |
| 跨測試殘留／污染 | Critical / Important | session/module scope 建可變狀態被多測試共用改寫；class-level patch 未還原（PropertyMock type-level 判定見域 1） |
| conftest／測試基礎設施隱式耦合 | Suggestion | fixture 過時、conftest 隱式順序依賴（**已失敗**的基礎設施走 `/fix-test` Type D；此處查**未失敗**的隱性耦合） |

### 域 5：Suite Operability

**核心原則**：套件要「跑得動、結果穩」——不可操作的套件會被繞過（手動 skip、只跑局部），稽核覆蓋隨時間塌縮。

| 檢查項 | 嚴重程度 | 判斷標準 |
|--------|---------|---------|
| collect／import 錯誤使部分測試**靜默缺席** | Critical | pytest 收集錯誤被 `--ignore`／局部跑法壓制——缺席的測試從未執行（名義覆蓋≠實際覆蓋） |
| flake（間歇失敗） | Important | 同 commit 重跑結果不一致；flake 使紅燈失去號誌力（修復路徑見 fix-test 階段 0.5 triage 的自癒 flaky 判定） |
| skip／xfail 累積盤點 | Suggestion | skip/xfail 佔比與理由盤點（無理由 skip 已在域 1 空殼覆蓋；此處查套件層累積趨勢） |

### 域特化指針（圍欄——本檔只留問題陳述，設計細節住彼側卡）

| Repo | 問題陳述 | 彼側承載 |
|------|---------|---------|
| mosaic | determinism gate＋invariant/PBT/hash gate 測試補強（含 domain-validity guardrail——PBT generator 須先通過 domain 有效性驗證） | MOS 側卡（問題定義與設計細節住 mosaic backlog——此處不展開） |
| SC | 測試補強薄改清單——**message protocol contract schema 化列首位**（protocol contract >> E2E）＋trace/retry＋selector 漸進＋vitest coverage＋flake census | SC 側卡 |
| coverage 態度 | coverage＝trend telemetry，非 gate | mosaic test-cov 側（同下落定 gate 前提） |

**落定 gate（uncommitted 前提）**：上表指針項對應的彼側卡多為 uncommitted——audit-test 消費任一指針項前，先確認彼 repo 對應 commit hash 已回填 AIR-124 卡 notes；**未落定的對應項 defer**（不消費、不展開其設計細節）。

---

## finding schema 與 oracle 分級

每個 finding 必含（缺一即不合格）：

- **file:line**（精確位置）＋**證據**（rg/fd/LSP 指令＋結果，或原始碼引用）
- **域＋嚴重程度＋信心水準**（信心水準定義見「Audit 誠信約束」）
- **oracle_level 欄**：`S`/`H`/`I`/`N`/`unknown`——分級正典見 [acceptance-evidence](../../rules/acceptance-evidence.md)「oracle authority 分級」（audit-test 引用不重複定義）；被測斷言的 oracle 來源無法判定標 `unknown`，**I/N 級 finding 觸發補強時須知 I/N 禁 autonomous 補強授權**（升級路徑＝找 S/H oracle，無則列 human queue）
- **建議**（具體可執行）

> **分級是 detector 標注非判官**——findings 非定論（含 oracle_level 標注），judge-review／實作查證可推翻。

---

## 輸出格式

### 報告模板

```markdown
## Audit-Test Report

### 總覽

| 指標 | 數值 |
|------|------|
| 掃描模式 | Diff Audit / Commit Audit / night-mode |
| 掃描範圍 | N 個 test files |

### 證據域 vector（8 維）

| 維度 | 承載域 | 狀態 |
|------|--------|------|
| semantic_integrity | 域 1 | 🔴 Critical evidence / 🟡 findings / 🟢 clean / n-a（本次不適用） |
| traceability | 域 2 | ... |
| critical_invariant_coverage | 域 2+3 | P0 invariant 測試證據在場與否 |
| path_evidence | 域 2 | 消費端路徑驅動（符號≠路徑） |
| adversarial_strength | 域 3 | mutation 三層 gate 結果 |
| fixture_provenance | 域 4 | fixture 值可追溯 |
| flake_isolation | 域 4 | 隔離／污染／殘留 |
| suite_operability | 域 5 | 套件可運作 |

**gate 判準（blocking，僅此三條）**：
1. 任一維存在 `[confirmed]`/`[evidence-based]` 的 **Critical evidence**（`[inferred]` 禁列 Critical）
2. **P0 mandatory dimensions 缺場**——掃描範圍觸及 silent-corruption critical path（會計/風控/單位邊界）時，critical_invariant_coverage 與 path_evidence 兩維不得為 n-a／缺場
3. **mutation 層 1 gate**：新增且確認 non-equivalent survivor（域 3）

> **trend 註記**：維度狀態與歷次比較是趨勢觀察面，**分數類無 blocking authority**——不因「比上次差」擋路（investigation signal）；blocking 只走上方三判準。

### 🔴 Critical（必須修正）

> Critical 只能是 `[confirmed]` 或 `[evidence-based]`，禁止 `[inferred]`（見「Audit 誠信約束」）。

- [ ] **[空殼覆蓋]** `[confirmed]` `test_<module>.py:test_<case>:NN` — test body 只有 `pass`（讀過原始碼確認）〔oracle_level: unknown〕
- [ ] **[Mock 被測對象]** `[confirmed]` `test_<module>.py:test_<case>:NN` — `@patch("<module>.<ClassUnderTest>")` mock 了主角〔oracle_level: N〕

### 🟡 Important（建議修正）

- [ ] **[vacuous-green]** `[confirmed]` `test_<module>.py:test_<case>:NN` — `if hasattr(...)` 守衛內 assert、無 else-fail〔oracle_level: I〕
- [ ] **[幽靈斷言]** `[confirmed]` `test_<module>.py:test_<case>:NN` — 只有 `assert result is not None`〔oracle_level: N〕
- [ ] **[覆蓋缺口]** `[evidence-based]` `<module>.py:<func>` — `rg "<func>" tests/` → 0 hits。⚠️ 單一 rg，建議下游用 LSP `findReferences` 交叉確認〔oracle_level: unknown〕
- [ ] **[同義反覆]** `[confirmed]` `test_<module>.py:test_<case>:NN` — test 和 source 都 hardcode 同一值〔oracle_level: I〕

### 💡 Suggestion（可以改善）

- [ ] **[標題不符]** `[confirmed]` `test_<module>.py:test_<case>` — 名稱暗示測 X，但 assert 驗證 Y〔oracle_level: —〕
- [ ] **[Mock 層級過低]** `[confirmed]` `test_<module>.py:test_<case>:NN` — patch `_internal()`（private method）〔oracle_level: —〕
- [ ] **[技術判斷]** `[inferred]` ⚠️ 未實證：宣稱「<套件行為>」基於推理。**禁止列 Critical**，建議實作層跑 demo 確認〔oracle_level: unknown〕

### 建議處理方式

| 反模式 | 處理路徑 |
|--------|---------|
| 空殼覆蓋 | `/fix-test --redesign` 或刪除空殼 test |
| 幽靈斷言／vacuous-green | 補充具體業務值斷言（先理解測試意圖；守衛改 else-fail） |
| 過度 mock（被測對象/層級形態） | 重構為繼承式 Mock 或 Real-World Fixture Pattern |
| 覆蓋缺口 | 新增測試（RED → GREEN） |
| 消費端缺驗證 | 在消費端上下文中跑一次完整流程 |

### Audit Summary（結構化結論）

- mode: diff|commit|night
- files_scanned: N
- vector: {semantic_integrity: red|yellow|green|n-a, ...8 維}
- gate_blocking: true/false（三判準）
- critical: X（全為 confirmed/evidence-based）
- important: X（含 Y inferred，已標 ⚠️）
- suggestion: X
- oracle_levels: {S: n, H: n, I: n, N: n, unknown: n}
- needs_action: true/false
- **findings_nature: 待驗證（非定論）** — 建議經 judge-review / 實作查證後再行動
```

---

## 執行流程

| 步驟 | 名稱 | 觸發 |
|------|------|------|
| 1 | 定位掃描範圍（模式判定） | 預設 |
| 2 | 讀取 test files | 預設 |
| 3 | 讀取對應 source files | 預設 |
| 4 | TC 契約對帳（域 2 第一 gate） | 條件觸發（EP 含凍結 TC——觸發輸入見域 2）；無 TC → 出生證明查核（標 provenance:unknown） |
| 5 | 域 1 Semantic Integrity | 預設 |
| 6 | 域 2 behavior impact evidence＋消費端路徑證據 | 預設 |
| 7 | 域 3 Adversarial（mutation 三層 gate 判定） | 條件觸發（層 1＝P0 critical path 變更弧必跑；層 3 週期輪抽） |
| 8 | 域 4 Test-System Integrity | 預設 |
| 9 | 域 5 Suite Operability | 預設 |
| 10 | 產出 vector 報告（oracle_level 標注） | 預設 |

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

**night-mode**：見 night-mode 節（P1 target manifest）。

### 步驟 2：讀取 test files

完整讀取掃描範圍內的每個 test file，提取：
- test function 名稱、docstring、body
- assert 類型與守衛形態（if/try/with 內斷言）
- `@patch` / `Mock()` / `mock_` 使用位置（位置語義——patch 了誰、哪一層）
- `@skip` / `pass` / `...` 標記

### 步驟 3：讀取對應 source files

從 test files 的 import 語句推斷 source files，讀取以比對 hardcoded 值。

### 步驟 4：TC 契約對帳（域 2，條件觸發）

EP 含凍結 TC 時（觸發輸入見域 2），按七項對帳表逐一執行（第一 gate）；receipt/digest 比對與 baseline 抽查按對帳項 4/5 操作。無凍結 TC → 出生證明查核：標 `provenance:unknown` 列 finding（非跳過），並在報告標記理由。

### 步驟 5-9：逐域檢查

對每個 test function，按域 1-5 各自 detector 定義執行。記錄發現（每 finding 帶 oracle_level）。

### 步驟 10：產出報告

按輸出格式模板產出 vector 報告。Diff/Commit Audit 由 `/commit` pre-commit gate 消費（無 Critical 才建議 commit）。

---

## night-mode 補強生產線（多家族夜間管線）

**rationale**：夜間補強的 stage→家族分配軸＝**獨立性需求 × 判斷密度 × 成本**（掃描要便宜、盲審要跨家族、裁決要 decision-qualified）；夜間可用性以 spine 事件＋三訊號判定（見 [model-routing](../model-routing/SKILL.md) AvailabilitySnapshot），**不預設任一家族充裕**。panel 詞彙（tri／bi／single）定義源＝[model-routing](../model-routing/SKILL.md)「審查陪審團」段——本節引用不重定義。

> 執行主體 repo 歸屬（user 0918 拍板回填，原 EP open item 結案）：**專用弧 worktree（detached @ main SHA，零 branch 污染）跑管線；main WT 唯一寫入＝readout append；隔離形態由 manifest 明記**——跨 WT 寫入是明示而非靜默（契約 9「零靜默寫入」的字面張力以此解；0918 r1 首跑實證形態）。readout 落點即契約 9 durable sink adapter 的解析路徑。

### 五段管線

| Stage | 載體 | 輸入 | 輸出 | 停止條件 |
|-------|------|------|------|---------|
| **P1 掃描** | GLM flash（in-harness spawn） | target manifest（P1 前凍結——契約 1） | findings ledger（`.partial.md` 分段落盤——下方落盤策略） | manifest 掃完；flash unavailable（GLM 撞 1308 家族級→flash 預設不存活，除非 flash 有獨立 fresh snapshot＝available）→ stop＋degradation receipt |
| **P2 跨家族盲審** | muse＋codex bridge 並行（兩 blind reviewer） | target manifest **同一份**（禁 P1 findings 入 P2 工單——契約 1/2） | 各自 findings ledger（分段落盤） | 兩家 reviewer 全缺（unavailable/timeout）→ stop＋degradation receipt（**禁靜默跳過**）；單家缺→降級記錄（契約 8）續跑 |
| **delta 二分** | 機械比對（主 session） | 兩 reviewer findings ledgers | delta（交集／差集）＋三選一歸類（契約 3） | 零交集仍成 delta（全差集）→全部進裁決隊列，**禁自動 P4** |
| **P3 judge 裁決** | decision-qualified judge（GLM 主 session 或 user——lite 分工律：judge 腿永不降） | delta 裁決隊列 | 決策記錄（durable ledger：finding 判定＋authority 類別＋歸類） | 無 decision-qualified judge → **stop-before-P4**（停在裁決隊列，禁進 P4） |
| **P4 補強生產** | 補強 agent（受 admission gate） | P3 裁決通過＋admission 三證據鏈齊（契約 5）的 findings | 新 tests／fixtures（**只寫 tests/fixtures**——紅線） | admission 缺任一證據鏈成分→拒絕進入（非降級放行）；S/H oracle 測試使 baseline RED＝production defect→pending-decisions，**夜間禁改 production** |
| **P5 機械驗收** | completion aggregator（唯一 readout 生產者——契約 10） | P4 產物＋mutation baseline（契約 4） | receipts（每 finding：驗收結果＋mutation delta）；morning readout | 驗收失敗（exit 條件不滿足）→ 列回 pending-decisions，不自動重試 |

**resume 條（中斷恢復）**：P2-P5 產物同等 durable 落盤（P2 reviewer ledgers／P3 決策記錄／P4 產物 commits 前工作樹狀態標記／P5 receipts）。中斷後 resume 先讀 ledgers 判**已完成 stage**，從下一 stage 續跑——**禁重跑已完成 stage、禁污染 blind 邊界**（resume 的 P2 不得回讀已存在的另一 reviewer output；已盲審完成的 reviewer 續跑時工單仍照契約 2 禁讀清單）。

### 執行契約 10 條

1. **target manifest**：P1 前凍結；兩 blind reviewer 用**同一份** targets；來源＝Adversarial 域 critical-path 輪選清單（域 3 週期輪抽查）＋dependency-graph hotspots＋**事故面（過去 incident 的測試面——0918 r2 實證：UI 出口 double-÷＝事故 F-B 同面，因不在 AGENTS 標記面漏出射程）**；**禁 P1 findings 決定 P2 targets**（獨立性污染）；**manifest invariant 條款逐字引用來源原文、禁壓縮措辭，並附來源錨點（owner 文件／段落）——壓縮＝改 oracle**（0918 r1 偽陽性根因：工單轉述 invariant 觸發偽陽性，r2 逐字後零復發）
2. **blind input contract**：P2 工單明示**禁讀清單**——P1 `.partial.md`／daily report／另一 reviewer output；如實標注＝**procedural blindness** 非 hard isolation（hard 隔離待實作期 sandbox 驗證）；**工單須要求 reviewer 如實申報讀了什麼**（申報進 receipts）；**工單預先聲明 carrier sandbox 限制**（例示非正典，以工單生成時的當前實測為準——muse：`uv run` 拒寫 cache→直接指定 `.venv/bin/python -m pytest`；0918 實證 reviewer 自行繞道成本）；**工單 invariant 逐字引用契約 1 manifest 原文、禁轉述壓縮**（r1 根因路徑的工單面封堵）
3. **delta identity**：canonical key＝target/module＋behavior/predicate＋oracle anchor；交集定義＝**support-count ≥2**（寫死）；**零交集→全差集進裁決隊列、禁自動 P4**。delta 三選一歸類表：spec 歧義→修 spec／單邊漏→取聯集／兩可→user 裁決（晨間）
4. **mutation baseline**：P4 前獨立機械 pre-run 產 survivor set（P1 不跑 mutation）；P5 以**同 scope／operator／config** rerun 得可比 delta。**rerun invariant（零 commit 紅線）**：P5 rerun 前必須全清 mutants/ 後重跑、增量 rerun 語義不可用——mutmut git-change-detection 對未提交變更（config 與 test 皆）不失效快取（0918 r1+r2 實證）；清除前先 `pwd` 斷言在弧工作樹根，僅清該樹 `mutants/`。**口徑 invariant**：timeout 類單獨列示、不入 kill-rate 分母——kill-rate＝killed／(total−timeout)，分母為零記 n/a 並視同疑號升級；timeout 數量穩定性另軌觀察、突增＝疑號（0918 r1「timeout=config artifact」假設被 r2 證偽——60× 穩定不變）
5. **P4 admission**：finding 須具 **S/H oracle authority**（[acceptance-evidence](../../rules/acceptance-evidence.md)「oracle authority 分級」——I/N 禁 autonomous 補強授權）＋**三證據鏈缺一即拒**（非降級放行）：①spec/invariant oracle ②property/metamorphic/differential 測試形態 ③mutation challenge；**survivor 只可指出 probe 位置、禁決定 expected value**（封閉迴圈防護——oracle 可不變而 test 被 survivor steering 的繞道封死）
6. **P4 exit**：補強測試驗收＝canonical baseline **GREEN** ＋ targeted mutant/negative-control **RED**；**baseline RED＝抓到 production defect→pending-decisions**（夜間禁改 production code）
7. **per-stage availability**：P1/P2/P3/P4/P5 **各自** resolve AvailabilitySnapshot（非管線級一次判定）；GLM 撞 1308（家族級）→flash 掃描腿預設不存活（除非 flash 有獨立 fresh snapshot＝available）；P3 無 decision-qualified judge→stop-before-P4；**兩家 reviewer 全缺→stop＋degradation receipt**
8. **degradation receipt**：降級顯式記錄——`panel=single` ＋ same-family 退化標注（`explicit_same_family_degradation` 是 independence 欄狀態非 panel token——panel token 詞彙＝[model-routing](../model-routing/SKILL.md)、degradation token 詞彙＝[review-engine](../review-engine/SKILL.md)／[agent-review-cycle](../_common/agent-review-cycle.md)，複用不改）；禁靜默降級
9. **sink resolver**：durable sink＝**repo adapter**（mosaic inbox 慣例；無 inbox repo fallback＝daily-report 或 `.agent-tmp/`＋晨間報告）；**adapter 缺席→fail-closed＋degradation receipt＋零靜默寫入**（禁止無 sink 時把 findings 寫進未約定位置）
10. **readout owner**：morning readout 由 **P5 completion aggregator 唯一生產**，從 immutable ledgers＋P3 決策記錄＋P5 receipts 組裝（**禁 reviewer 自述摘要**）

### autonomous 紅線

- **不 commit**：夜間管線零 git commit（P4 產物停留工作樹，晨間由人類審後走正常 commit gate）
- **夜間止於 P5 證據齊**：管線終點＝receipts＋readout，不做超出授權的修復/重構
- **P4 只寫 tests/fixtures**：禁改 spec／oracle／production source（改這三者的需求一律 pending-decisions）

### 長任務 findings 落盤策略（P1/P2 必讀）

> 管線涵蓋數百 test files，單一 agent 可能跑數十分鐘。**必須假設會中斷**（rate limit、context 上限、network），findings 即時落盤，避免 resume 重跑。

1. **分段輸出**：每完成一個子任務（一個 test 目錄 / 一組 test files），立即將該段 findings 寫入中間檔案（如 `ai-analysis/audit-test-night-{date}-{stage}-{agent}.partial.md`），不在 context 中累積全部 findings 才一次輸出
2. **進度標記**：每段含進度標記（如 `<!-- agent=2, segment=3/8, completed=true -->`），resume 時讀 `.partial.md` 判斷已完成段落
3. **彙整**：全部子任務完成後，讀所有 `.partial.md` 彙整成該 stage 最終 ledger，刪除中間檔（P5 readout 組裝後）
4. **resume**：中斷後 resume 先讀 `.partial.md`，只重跑未完成段落（blind 邊界照 resume 條）

**反例（真實案例）**：某掃描 agent 跑多個子任務，findings 全留 context，彙整前因 rate limit 中斷 → resume 需完整重跑全部子任務。即時落盤則只需重跑中斷時正在做的那一段。

### Deferred（judge 裁決記錄）

mutation baseline（契約 4）＋管線契約抽 `_common/night-mode-contract.md`——**本弧不抽**（單一消費者，YAGNI）；promotion trigger＝第二個 night-mode 消費者（如 code-review night mode）出現時抽離。

---

## 與其他命令的協作

| 命令 | 與 /audit-test 的關係 |
|------|---------------------|
| `/fix-test` | 互補：fix-test 修**失敗**的測試，audit-test 偵測**通過但品質差**的測試 |
| `/code-review` | Correctness 軸可引用 audit-test 發現 |
| `/implement` | 段落完成後跑 audit-test 確認測試品質 |
| `/commit` | pre-commit gate：audit-test 無 blocking Critical 才建議 commit |

### 測試品質完整流程

```
寫測試 → /audit-test（偵測反模式）→ 發現問題 → 人類判斷
  ├─ 簡單修正（改名、補斷言）→ 直接改
  ├─ 重構測試（mock 危險形態 → Real-World Fixture）→ /implement 段落
  └─ 刪除壞測試（空殼）→ 確認後刪除
```

### 設計不良測試的處理路徑

| 情境 | 工具 | 說明 |
|------|------|------|
| 測試**失敗**了 | `/fix-test` | 分類 A/B/C/D/E → 修 source 或修 test |
| 測試**通過但有反模式** | `/audit-test` → 人類判斷 → 對話修正 | 偵測 → 報告 → 決策 → 執行 |
| 需要從頭重寫壞測試 | `/implement` 段落或對話指令 | 按反模式修正建議重寫 |

**核心原則**：修正反模式需要**理解測試意圖**，無法全自動。`/audit-test` 是偵測器（眼睛），不是修復器（手）。修復的決策權在人類（night-mode P4 的 autonomous 補強是唯一例外，受 night-mode 契約與紅線管轄）。

---

## Audit 誠信約束

> audit 是偵測器（眼睛），不是判官。偵測結果可能 false positive，必須以「可被下一層（judge-review / 實作查證）推翻」的心態輸出。
>
> **stance 釐清**：「偵測器非判官 + read-only」是 audit-test 專屬 stance（只產 findings 不下判）。通用誠信「findings 非定論」見 [review-engine](../review-engine/SKILL.md) — code-review/ep-review 要下判（給結論/commit/回寫），適用通用誠信但不適用偵測器 stance。

### 1. Findings 不是定論 — 標示信心水準

信心水準定義（confirmed / evidence-based / inferred + Critical 必須 confirmed 或 evidence-based，禁止 inferred）見 [review-engine](../review-engine/SKILL.md) 信心水準段。本命令每個 finding 必須標信心水準，讓下游（judge-review / 實作查證）知道哪些需重點查證。

test 場景的信心判準參考：confirmed = 已讀完整 test body + source 比對符號；evidence-based = 有 file:line + rg/fd 結果（覆蓋缺口多數）；inferred = 基於套件行為推理（如「無 seed → 不 deterministic」）。

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
- **域 + 嚴重程度 + 信心水準 + oracle_level**
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

- **稽核段只讀不寫**：Diff/Commit Audit 與 night-mode P1-P3/P5 只檢查和報告，不修改任何檔案；**唯一例外＝night-mode P4 補強**（只寫 tests/fixtures，紅線見 night-mode 節）
- **必須讀取實際程式碼**：不憑檔名猜測測試品質，必須讀取 test body
- **引用來源**：報告問題時標註具體位置（test file:function name）
- **繁體中文輸出**：報告使用繁體中文 + 英文術語
- **不重複 ruff 工作**：語法問題交給 ruff，本命令只關注邏輯品質

---

## 反思閉環（大型 night-mode 管線後執行）

> 每次大型 night-mode 管線涵蓋大範圍、產出數十 findings，是真實流程經驗的富礦，**不提煉等於浪費**。本段定義大型 audit 後的反思流程。

### 觸發條件

- night-mode 管線完成且 findings ≥ 20（Critical + Important + Suggestion 總和）
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
