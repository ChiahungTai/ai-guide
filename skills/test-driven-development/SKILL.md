---
name: test-driven-development
description: "Drives development with tests. Use when implementing any logic, fixing any bug, or changing any behavior. Use when you need to prove that code works, when a bug report arrives, or when you're about to modify existing functionality."
---

# Test-Driven Development

Write a failing test before writing the code that makes it pass. Tests are proof — "seems right" is not done.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? **Delete it. Start over.** Delete means delete —— 不留作「reference」、不「邊寫測試邊 adapt」、不看著它寫測試。從失敗測試重新實作。

違反 letter 就是違反 spirit。「只這一次跳過」「太簡單不用測」是 rationalization，不是例外。

---

## The Prove-It Pattern (Bug Fixes)

**Do not start by fixing the bug.** Start by writing a test that reproduces it.

1. Write a test that demonstrates the bug → test FAILS (bug confirmed)
2. Implement the fix → test PASSES (fix proven)
3. Run full suite → no regressions

This guarantees the bug can't resurface silently.

## Tests Verify Intent, Not Just Behavior

Every test must encode **why** the behavior matters. A test that can't fail when business logic changes is a broken test.

**Worthless**: both the function and the test hardcode the same value — proves nothing.
**Meaningful**: test constrains the output against a business rule — would fail if logic changes.

**Rule**: If you can't write a test that fails when the business logic changes, either the function is wrong or the test is wrong.

## 測試反模式自檢

寫完每個測試後，確認沒有踩入以下陷阱：

| 反模式 | 辨識特徵 | 修正 |
|--------|---------|------|
| **幽靈斷言** | 標題說測 X，但 body 只有 `assert result is not None` | 斷言具體業務值 |
| **同義反覆** | function 和 test 都 hardcode 同一個值，證明不了任何事 | 用獨立計算或業務規則驗證 |
| **空殼覆蓋** | 有 test function 但用 `@skip` 跳過或 body 只有 `pass` | 要麼刪要麼補實作 |
| **過度 mock** | test file 中 mock 數量 > assert 數量 | 改用繼承式 mock 或 real impl |
| **標題不符** | test 名稱暗示測某行為，但 assert 驗證的是另一件事 | 名稱和斷言必須一致 |
| **class body scoping** | pytest helper 寫在 class body 直接引用外層函式參數→NameError | helper 用 factory 函式或 kwargs 注入；外部家族寫測試常犯（muse S3 四紅根因）；回覆混散文落檔前須 strip |

**自檢時機**：每個 test function 寫完後立即對照此表。RED 階段就該發現反模式，不要等到 GREEN。

**出生證明接口**：每個新測試標注 provenance——值域 S/H/I/N/unknown（分級定義見 [acceptance-evidence](../../rules/acceptance-evidence.md)「oracle authority 分級」；oracle 來源無法判定標 unknown），存放位＝測試檔 docstring 行或 fixture 檔頭；供 audit-test 出生證明查核消費。

## Test What Matters

- **State over interactions**: Assert on outcomes, not on which methods were called. Interaction tests break on refactor.
- **Real implementations over mocks**: Real > Fake > Stub > Mock. Over-mocking creates tests that pass while production breaks.
- **One assertion per concept**: Each test verifies one behavior, named descriptively.

## Test User Logic, Not the Framework

假設第三方套件（Panel/Bokeh/React…）正常，測**你的邏輯**（handler → 資料流 → 行為結果），不是套件機制（渲染、WebSocket、document lock）。框架機制的 debug 是無底洞，且就算解了也沒驗證你的邏輯。

- **任務起始自問**：我測的是使用者的程式碼，還是框架/套件？「如果框架完全正常，這個測試還剩下什麼要驗？」剩下來的才是真正該測的。
- **投入機制前問**：這個 POC/工具/config 驗證什麼**具體行為**？答不出來（如「figure 渲染驗證什麼行為？」），就不要投入 —— 會掉進框架 debug 無底洞。
- **漂移警報**：連續 2 次在解「框架為何不工作」（渲染、連線、配置、版本）→ 停，回問「使用者的邏輯是什麼、怎麼純粹測它」。

## Subagent Testing Pattern

For complex bug fixes, spawn a subagent to write the reproduction test. The main agent then verifies the test fails, implements the fix, and verifies it passes. This separation ensures the test is written without knowledge of the fix.

## Test Classification

在 RED 階段，先分類每個測試的類型，再決定放哪裡、用什麼 fixture。

**分類決策**：

| 問題 | 是 | 否 |
|------|------|------|
| 測試對象涉及外部系統（DB、API、filesystem）？ | integration | unit |
| 測試驗證跨模組互動？ | integration | unit |
| 測試需要真實外部服務（無法 mock）？ | external API test | 用 mock/fake |

**目錄歸屬**：
- **Unit**：`tests/unit_tests/` — 快速、mock、純函數邏輯
- **Integration**：`tests/integration_tests/` — 真實 DB、跨模組、需要 fixture
- **External API**：`tests/external_api/` — 真實外部服務，加 skip 機制（資源限制、時段限制）
- **Case Study**（可選）：`tests/case_studies/` — 理論驗證 vs 真實數據對齊

**原則**：不確定時歸類為 integration — 寧可多隔離也不要 unit test 裡藏外部依賴。

## Fixture & Mock Strategy

### Scope 選擇

| Scope | 適用場景 | 範例 |
|-------|---------|------|
| `session` | 昂貴資源、建構慢、可安全共用 | DB 連線、外部 API 回應快取、Ground Truth 計算 |
| `module` | 同類測試共用、中等建構成本 | 模組級 conftest、同類 API 回應 |
| `function` | 需要隔離、每次用新狀態 | 單一測試的 mock instance |

**錯誤模式**：用 function scope 建立 DB 連線 → 測試慢 10×。用 session scope 建立可變狀態 → 測試互相污染。

### Mock 階層（推薦度由高到低）

1. **繼承式 Mock**：`class MockClient(RealClient)` — 繼承真實 class，只 override 需要的方法。保留真實行為，重構時測試不易斷。
2. **Patch**：`@patch("module.Client")` — 直接替換。簡單但 brittle，重構時容易斷。
3. **Fake**：完整實作介面的輕量版本。成本高但最穩定。適用於核心介面、跨多模組共用。

### 資料管線測試模式

- **Ground Truth Pattern**：昂貴計算只做一次（session-scoped fixture），後續測試比對基準值。適用：特徵計算、統計指標。
- **Golden Master Pattern**：持久化預期值到 JSON/檔案。首次執行記錄並 skip，後續執行比對。適用：標籤生成、複雜轉換邏輯。
- **Real-World Fixture Pattern**：用真實市場數據的精確值作為 test fixture。

#### Real-World Fixture Pattern

適用於數學轉換邏輯的 regression guard 和域特定 edge case 文件化。

**適用場景**：
- 數學轉換邏輯（adj 計算、特徵計算）— 精確值提供可追溯 ground truth
- 域特定 edge case 文件化（除權息、減資、混合事件）— 人造數據無法重現的邊界
- 需要可追溯 ground truth 的計算驗證

**不適用場景**：
- 業務邏輯測試（語義比精確值重要）
- 經常變動的數據（fixture 會持續過時）

**選材原則**：
- 每種邊界類型至少一個代表（如：除權息、減資、混合事件）
- fixture 方法名即說明（`_make_3041_capital_reduction_daily`）
- docstring 記錄事件的 domain context（ratio、日期、影響）

**與 Ground Truth 的區別**：Ground Truth 是「從系統產出抓基準」，Real-World Fixture 是「從真實世界抓基準」。前者基準可能錯，後者基準來自可驗證的外部事實。

## EP Integration

EP（Execution Plan）的驗證策略是 TDD 的輸入。在 RED 階段按以下步驟轉譯：

1. **讀「測試類型分佈」**（單元 / 整合 / E2E / 外部 API mock）→ 決定每種測試放哪個目錄、用什麼 fixture scope
2. **讀「關鍵情境覆蓋」**（happy path、邊界案例、error handling、冪等性）→ 每個情境寫一個 test function（這就是 RED 的 test list）
3. **讀「已知未覆蓋的風險」** → 標記為 `# TODO: EP 標記未覆蓋` 或 `@pytest.mark.skip(reason="EP 標記未覆蓋")`，**不默默跳過**
4. **實作完成後** → 對 EP 的「完成檢查」逐項驗證，確認每項都有對應測試覆蓋

**關鍵**：EP 的驗證策略是 TDD 的「合約」— 如果 EP 說要測某個情境但沒測，等同段落在撒謊。

## 已知 bug 釘住：xfail(strict=True)

當發現一個 bug，但修復需要獨立 EP（超出當前段落範圍）— 用 `@pytest.mark.xfail(strict=True)` 釘住**目標行為**（斷言期望的正確行為，現在 fail），驅動後續 EP，修復後強制提醒轉綠。

**與「未覆蓋風險 skip」（上方步驟 3）的區分**：

| 情境 | 特徵 | 做法 |
|------|------|------|
| 未覆蓋風險 | 功能還沒做，**沒東西可測** | `skip` + TODO（步驟 3） |
| 已知 bug、修復超出範圍 | 功能存在但壞，**有目標行為可釘** | `xfail(strict=True)` |

**為什麼 xfail strict 優於 skip/TODO**：
- `skip` = 不跑（無壓力、易遺忘、修復後無提醒）
- `TODO` = 純文字（無強制力）
- `xfail(strict=True)` = 跑且預期 fail；**修復後測試 pass → XPASS → 報失敗 → 強制移除 xfail → 測試成正式 regression guard**

**範例**：

```python
@pytest.mark.xfail(
    reason="TDD red — pins target: X should do Y. Currently red because Z. "
           "Open as EP-X. strict=True surfaces XPASS when fixed.",
    strict=True,
)
def test_x_should_do_y():
    assert actual == expected  # target behavior, currently fails
```

**關鍵**：xfail 釘的是「該實現的正確行為」，不是「接受錯誤行為」。這是 TDD red 驅動後續 EP 的機制，避免目標被遺忘 — 優於「移除斷言默默接受」（用 crash-only 等設計哲學合理化不修，見 [validation-strategy](../validation-strategy/SKILL.md)「crash-only 邊界」）。

## Verification

After completing any implementation:

- [ ] Every new behavior has a corresponding test
- [ ] Bug fixes include a reproduction test that failed before the fix
- [ ] No tests were skipped or disabled

## 抗規避自檢（Anti-Rationalization）

技術正確不代表走過 TDD —— agent 會找藉口跳過。出現以下念頭時是 rationalization，不是例外：

| 藉口 | 現實 |
|------|------|
| 「太簡單不用測」 | 簡單的 code 也會壞（除權息邊界、減資調整、NaN 傳播）。測一下 30 秒。 |
| 「先寫碼再補測就好」 | 事後測試立刻 pass，證明不了任何事（可能測錯東西、測到實作非行為）。Tests-first 才強迫看見失敗。 |
| 「回測框架都搭好了，先跑起來再補」 | Sunk cost fallacy。先跑起來的 code 沒測 = 不能信任的技術債。 |
| 「刪掉 X 小時的工作太浪費」 | 留下沒測的 code 才是浪費。Delete means delete（見 Iron Law）。 |
| 「量化講速度，先有策略再說」 | TDD 比事後 debug 快（抓 bug 在 commit 前）。Pragmatic = test-first，不是趕路。 |
| 「這只是 config/參數調整，不用測」 | config 錯 = 回測全錯（hash 鎖不住語義）。行為改變就要測。 |

### Red Flags — 出現這些念頭就 STOP

- 「先寫碼，測試之後補」
- 「測試立刻 pass」（沒看見失敗 = 沒在測對的東西）
- 「已經手動測過了」（ad-hoc ≠ 可重現）
- 「刪掉太浪費，留作 reference」
- 「只這一次跳過」
- 「TDD 太教條，我務實一點」

**以上全部 = 回 Iron Law，刪 code，從失敗測試重來。**
