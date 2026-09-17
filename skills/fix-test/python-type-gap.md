# Python Type Gap — 第三方套件型別缺口的四層處理策略

> 前身＝`python-type-gap` skill（AIR-113 reference-demotion：退出 resident 注入面、降為 fix-test 的型別章 reference——`lint-type-recipes.md` 的型別展開層；lookup 食譜見 [python-type-gap-reference.md](python-type-gap-reference.md)）。觸發由 fix-test 的 lint/type 面承載。

當第三方套件的 type annotations 不完整時，按以下順序嘗試：

## Layer 1：Type Narrowing（最推薦）

適用：union type 導致的方法解析衝突。

```python
# ❌ 錯誤：# type: ignore 處理 union type
df = catalog.get_bars(...)  # returns pd.DataFrame | pl.DataFrame
if df is None or df.is_empty():  # type: ignore[operator]
    return []
df_pd = df.to_pandas()  # type: ignore[operator]

# ✅ 正確：isinstance type narrowing
import polars as pl

df = catalog.get_bars(...)
if not isinstance(df, pl.DataFrame) or df.is_empty():
    return []
df_pd = df.to_pandas()  # mypy 知道 df 是 pl.DataFrame
```

原理：mypy 在 union type 上找不到一致的方法簽名時會報錯。`isinstance` 讓 mypy 收窄為單一型別，方法解析不再衝突。附帶好處：runtime 真的會驗證型別。

### 繼承鏈窄化（Inheritance Chain Narrowing）

適用：變數靜態型別是基底類別，但實際持有子類別（有額外欄位/方法）。

```python
 # 問題：Recipe.labeling_params 是 LabelingParams | None，基底沒有 interval
 # DualMAParams 子類才有 interval: Interval
 ohlcv_df = catalog.get_bars(
     instruments[0],
     interval=recipe.labeling_params.interval,  # type: ignore[arg-type] — 不得已
 )

 # ✅ 正確：assert isinstance 讓 mypy 知道是子類型別
 params = recipe.labeling_params
 assert isinstance(params, DualMAParams)
 ohlcv_df = catalog.get_bars(
     instruments[0],
     interval=params.interval,  # mypy 推斷為 Interval，無需 suppress
 )
```

原理：`isinstance` / `assert isinstance` 觸發 mypy 的型別窄化（type narrowing），將靜態型別從 `LabelingParams | None` 收窄為 `DualMAParams`。mypy 就能正確解析 `params.interval: Interval`。**不需要 `Interval()` 包裹，不需要 `# type: ignore`**。

### `@overload` vs `isinstance` — 解決不同的問題

兩者解決不同層面的型別推斷問題，互不替代：

| 技術 | 解決什麼 | 範例 |
|------|---------|------|
| `@overload` | 回傳值型別推斷 | `format="polars"` → 回傳 `pl.DataFrame` |
| `isinstance` | 引數型別窄化 | `params.interval` 從 `Any` → `Interval` |

```python
 # @overload 解決回傳值（IDE 知道 ohlcv_df 是 pl.DataFrame）
 def get_bars(self, code: str, interval: Interval, *, format: Literal["polars"] = "polars") -> pl.DataFrame: ...

 # isinstance 解決引數（mypy 知道 params.interval 是 Interval，不是 Any）
 params = recipe.labeling_params
 assert isinstance(params, DualMAParams)
 catalog.get_bars(code, interval=params.interval)  # OK
```

關鍵認知：加了 overload 後 `arg-type` 仍然可能報錯，因為 overload 只影響回傳值推斷。引數型別仍需 caller 端的型別窄化。

### PoC 驗證方法論

遇到「不確定 mypy 是否能推斷」的情況，寫最小 PoC 驗證：

```bash
 1. 建立最小重現（/tmp/poc_typing.py），只包含相關型別定義和呼叫
 2. 用 uv run mypy /tmp/poc_typing.py --strict 驗證
 3. 逐一嘗試各方案（isinstance / cast / type: ignore），確認哪個零錯誤
 4. 選擇最乾淨的方案套用到實際程式碼
```

判斷標準：isinstance > assert isinstance > cast > type: ignore（優先順序由高到低）。

**LSP type intelligence（跨所有 Layer）：**
- LSP `hover` 在任意位置顯示 mypy 推斷的型別 — 不用讀檔案就能確認 narrowing 是否生效
- LSP `goToDefinition` 從第三方符號跳到 stub 檔案 — 立刻看到型別定義品質（是精確型別還是 `Any`）
- LSP `diagnostics` 在編輯後即時回報型別錯誤 — 不用等 `uv run mypy` 就知道修正方向
- 新增 stub 後，diagnostics 立刻顯示是否解決了對應的 type error

## Layer 2：Project Stubs（推薦）

適用：套件無 type support、inline annotations 缺口多、或有 `py.typed` 但特定子模組缺 stubs。

**前置檢查**：先用 `fd 'py.typed' .venv/.../package/` 確認套件是否已有型別支援（替換 `.../package/` 為實際套件路徑如 `.venv/lib/python3.12/site-packages/polars/`）。

在你的專案根目錄建立 `stubs/` 目錄（透過 `pyproject.toml` 的 `mypy_path = "stubs"` 啟用），目錄結構按需建立。以下為範例：

```
stubs/
├── nautilus_trader/    # NT 有 py.typed 但部分子模組缺口多 → stubs 補缺口
├── shioaji/            # 完全沒有 type support → stubs 是唯一型別來源
└── pyarrow/            # 有 py.typed + __getattr__ → Any，但 compute 子模組缺 stubs → partial stubs 只補 compute.pyi
    ├── __init__.pyi    # 只有 __getattr__ → Any，確保 top-level 透傳不覆蓋
    └── compute.pyi     # 只補用到的 8 個函式（year, sum, is_null, ...）
```

判斷標準：
- **無 `py.typed`** → stubs 有效（如 shioaji）
- **有 `py.typed` 但缺口多** → partial stubs 有效（如 nautilus_trader）。**前提**：必須提供完整的中間 `__init__.pyi`（含 `__getattr__ → Any`），空的 `__init__.pyi` 會完全取代真實模組，殺死所有 re-export
- **有 `py.typed` + 特定泛型 class 造成 `type-arg` 錯誤** → partial stubs 將泛型 class 定義為 non-generic（如 Bokeh GlyphRenderer）
- **msgspec Struct 基底 class**（如 NT StrategyConfig）→ stub 加 `__init_subclass__` 和 `__init__(**kwargs)`（見下方模式）
- **有 `py.typed` 但 mypy 對 dataclass 繼承處理有 bug**（如 Bokeh `figure` 的 `InitVar` 不傳播）→ re-import 繼承：從真實 stub import class，子類化只覆寫有問題的方法（見下方模式）
- **有 `py.typed` + `__getattr__ → Any`，但特定子模組缺 stubs** → partial stubs 只補缺口子模組，`__init__.pyi` 用 `__getattr__ → Any` 透傳（如 pyarrow）
- **有 `py.typed` 且大部分可用，缺口的子模組也能用 `# type: ignore` 解決** → 看缺口數量決定，3+ 處用 stubs，1-2 處用 `# type: ignore[code]`

### `mypy_path` 覆蓋機制

`pyproject.toml` 中的 `mypy_path = "stubs"` 會讓 stubs 目錄中的檔案**完全取代**對應的真實套件型別資訊，即使套件有 `py.typed`。

這意味著：
- 空 `__init__.pyi` 會殺死真實模組的所有 re-export（所有符號變成不可見）
- 必須用 `__getattr__(name: str) -> Any` 透傳未覆蓋的符號
- 必須明確 re-export 需要覆蓋的符號（如 `from bokeh.models.renderers import GlyphRenderer as GlyphRenderer`）

### `*` import 陷阱

`from X import *` 不保證 re-export 所有符號。Bokeh 的 `__init__.py` 用 `from .glyph_renderer import *` 但 `*` 只導出 `__all__` 列出的符號。在 stubs 中需要明確 `as` import 確保 re-export。

### `ignore_missing_imports` 的空心綠

`mypy ignore_missing_imports = true` 的綠**只證沒 import 到，不證型別正確**——stub 缺口靜默通過（全綠但零覆蓋）；驗 stub 覆蓋度用顯式 probe（對已知用法看 mypy 型別回饋）。fork venv `_core.pyi`＋patches 優於 `__init__.pyi` override（nominal-type split：兩來源同名型別不相容，override 靜默分裂型別身分）。

### 何時不該寫 Partial Stubs（直接走 Layer 3 per-line）

以下情境寫 stubs 的成本遠高於收益，per-line suppress 是務實選擇：

- 套件使用深度繼承鏈（3+ 層，如 Markdown → HTML → Panel）
- 缺口分散在數十個不同 class 的 `__init__` 參數
- stubs 需覆蓋的 class 數量 > 20
- 每個 class 只需修 1-2 個 type-arg → 成本/收益比太差

### Partial Stubs 關鍵約束

- **`__init__.pyi` 必須有 `__getattr__ → Any`**：確保 top-level 屬性（如 `pa.schema`、`pa.Table`）透傳到已安裝套件的型別資訊。如果沒有它，mypy 會用 stubs 的 `__init__.pyi` 完全取代 site-packages 的型別資訊，導致已正確標註的型別全部變成 Any
- **只補缺口的子模組**：不需要為整個套件寫完整 stubs
- **只 stub 用到的函式**：先 `rg 'pc\.\w+' <package>/ -t py --no-filename -o > /tmp/usage.txt`，再用 `sort -u /tmp/usage.txt` 找出實際用量

### msgspec Struct 基底 class stub 模式

適用：`msgspec.Struct` 或類似動態 metaclass 基底 class（如 NautilusTrader 的 `StrategyConfig`），子類別用 `frozen=True` 或定義自己的屬性。mypy 看不到 metaclass 生成的 `__init_subclass__` 和 `__init__` 簽名，導致大量 `call-arg`。

```python
# stubs/nautilus_trader/trading/config.pyi
from typing import Any

class StrategyConfig:
    # 暴露子類別常用屬性為 Any
    instrument_id: Any
    bar_type: Any
    trade_size: Any

    # 關鍵：讓 mypy 認識 frozen=True 是合法的 class keyword
    def __init_subclass__(cls, *, frozen: bool = False, **kwargs: Any) -> None: ...
    # 關鍵：讓 mypy 認識任意 kwargs 建構子（msgspec Struct 動態生成 __init__）
    def __init__(self, **kwargs: Any) -> None: ...
```

**效果**：2 行 stub 一次消除所有 `StrategyConfig` 相關的 `call-arg`（class `frozen=True` 定義 + 建構子呼叫）。實測消除 21 處 per-line suppress。

**為什麼不用 `*args`**：msgspec Struct 的 `__init__` 是 keyword-only（`def __init__(self, *, field1=..., field2=...)`），`**kwargs` 是正確近似。

### Re-import 繼承 stub 模式

適用：套件有完整的 `.pyi` 型別資訊（`py.typed`），但 mypy 對特定模式處理有 bug（如 `@dataclass` 繼承鏈中的 `InitVar` 不傳播）。**關鍵區別**：不能用 bare class 替換（會丟失所有方法型別），必須從真實 stub 繼承再覆寫。

```python
# stubs/bokeh/plotting/__init__.pyi
from typing import Any

from bokeh.plotting._figure import figure as _BokehFigure

def __getattr__(name: str) -> Any: ...

class figure(_BokehFigure):
    def __init__(self, **kwargs: Any) -> None: ...
```

**效果**：`figure` 繼承 Bokeh 真實 stub 的完整 GlyphAPI（100+ glyph methods），只覆寫 `__init__(**kwargs)` 修好 mypy 的 `call-arg`。實測消除 6 處 per-line suppress，零新增錯誤。

**何時用 msgspec Struct vs re-import 繼承**：
- **msgspec Struct**（bare class）：套件**無**型別資訊 → stub 是唯一型別來源，定義 bare class + `__init__(**kwargs)` 即可
- **re-import 繼承**：套件**有**完整型別資訊但 mypy 處理有 bug → 必須繼承保留型別，只覆寫有問題的方法

## Layer 3：精確的 `# type: ignore`（所有程式碼的預設選擇）

適用：Layer 1-2 都不適用時的預設方案。**所有程式碼（包含 adapters、examples、生產碼）的第三方 gap 都應先用 per-line suppress。**

```python
# ✅ 精確到具體 error code + 第三方 gap
pq.write_table(  # type: ignore[no-untyped-call]
    table, where=str(path), compression="snappy",
)
```

約束：
- 必須指定 error code（`[no-untyped-call]`、`[operator]`），不用裸 `# type: ignore`
- 只用於第三方套件的 gap，不用於我們自己程式碼的型別問題
- **即使是 adapter/膠水碼，也應用 per-line 而非 module-level**（見 Facade 模式）

### 為什麼 per-line 是預設選擇（即使只有 1 處）

| 優勢 | 說明 |
|------|------|
| **最小 blast radius** | 只影響單行，不會隱藏同模組其他位置的型別問題 |
| **`warn_unused_ignores`** | pyproject.toml 設定後，mypy 自動偵測 stale suppress（第三方修復後自動暴露） |
| **可審計** | `rg "# type: ignore" <package>/` 即可列出所有 suppress，每個都有明確位置 |
| **不掩蓋新問題** | module-level disable 會靜默隱藏同模組內未來新增程式碼的同類型錯誤 |

**`warn_unused_ignores` 重要限制**：只對 per-line `# type: ignore[code]` 有效，**不適用於** module-level `disable_error_code`。這是 per-line 的關鍵優勢 — 第三方修復後自動暴露 stale suppress。

### Facade / Wrapper 模式

當 adapter 模組大量呼叫第三方 API 時，正確做法是在 adapter 內部用 per-line suppress 隔離第三方缺口，而 adapter 的公開 API 保持正確的型別標註。消費端（使用 adapter 的程式碼）不會被 suppress 污染。

```python
# ✅ adapter 內部：per-line suppress 隔離第三方缺口
class ShioajiDataClient:
    def get_bars(self, code: str, interval: Interval) -> pl.DataFrame:
        raw = self._api.bars(  # type: ignore[no-untyped-call]
            code, interval=interval.value,
        )
        return self._to_polars(raw)  # 回傳值有正確型別

# ✅ 消費端：完全不受 suppress 影響
client = ShioajiDataClient(...)
df = client.get_bars("2330", Interval.DAILY)  # mypy 知道 df 是 pl.DataFrame
```

**原則**：adapter 的公開方法是型別安全的邊界。第三方 API 的型別缺陷停留在 adapter 內部，不外溢。

### Polars 特別技巧

- 移除 `*args` 的 `[]`：`select([col("a")])` → `select(col("a"))`（Polars `select()` 接受 positional args，加 `[]` 會觸發 `arg-type`）
- 顯式標註異構 dict：`result: dict[str, Any] = {...}` 避免 mypy 推導為 `dict[str, int]` 後因後續賦值衝突
- **不要 wrapper**：Polars 的 fluent API（`df.select().filter().sort()`）不適合 facade 包裝，會破壞鏈式呼叫

### `no-any-return` 的替代技巧

當 `wrangler.process()` 等第三方函式回傳 `Any`，觸發 `no-any-return` 時，用 explicit variable annotation。**前提**：函式回傳型別必須接受 `list[Any]`（mypy 認為 `list[Any]` 與 `list[T]` 相容）；若回傳型別是嚴格的 `list[Bar]` 且 mypy 報 `incompatible return`，仍需 `# type: ignore[no-any-return]`。

```python
# ❌ 直接收會觸發 no-any-return
return wrangler.process(df_pd)  # type: ignore[no-any-return]

# ✅ 先賦值給 typed variable
bars: list[Any] = wrangler.process(df_pd)
return bars
```

## Layer 4：pyproject.toml Override（最後手段）

### Module-level disable 的根本風險

`disable_error_code` 是 module-level 設定，它會**遮蓋同模組內所有同類型錯誤**，包含你自己新增的程式碼。這是核心問題：

```
在 adapter 模組加了 disable_error_code = ["untyped-decorator"]
→ 之後在同一模組新增程式碼，如果也犯了 untyped-decorator 錯
→ mypy 不會報錯，因為 module-level 設定遮蓋了它
→ 型別安全退化，且沒有任何機制會警告你
```

相比之下，per-line `# type: ignore[code]`：
- 只忽略那 1 行，新增程式碼犯同類型錯 → mypy **正常報錯**
- `warn_unused_ignores = true` 可以偵測 stale suppress → module-level 沒有這個機制

**結論**：即使模組有大量第三方 API 呼叫，也應該用 per-line suppress（Layer 3）搭配 Facade 模式，而非 module-level disable。

### 只有兩種 error code 可以考慮 module-level

| Error Code | 允許 module-level 的理由 | 適用範圍 |
|-----------|------------------------|---------|
| `no-untyped-call` | `no-untyped-call` 只警告「你呼叫了無型別函式」，不檢查引數或回傳值。真正的型別錯誤會被其他 check 抓住：回傳值賦值觸發 `assignment`、引數傳遞觸發 `arg-type`、屬性存取觸發 `attr-defined`。壓制 `no-untyped-call` 不會遮蓋這些 downstream check | examples/、scripts/、ui/ |
| `operator` | Polars 算術的本質限制（`Any + float` 無法靜態解析） | **僅限** examples/ 等非 production code |

其他所有 error code（`arg-type`、`call-arg`、`untyped-decorator`、`attr-defined`、`assignment`、`misc` 等）一律用 per-line suppress，**不可** module-level。

### Per-line vs Module-level 決策樹

```
是第三方套件的型別缺口嗎？
├─ 否 → 修自己的程式碼（不是 type gap 問題）
└─ 是
    ├─ 能用 isinstance narrowing？ → Layer 1
    ├─ 能用 stubs 補缺口？ → Layer 2（一次修好所有呼叫點）
    ├─ 大部分情況 → Layer 3（per-line `# type: ignore[code]`）
    │   └─ adapter 模組用 Facade 模式：內部 per-line，公開 API 型別安全
    └─ 只有 no-untyped-call 或 operator？
        ├─ 是，且在 examples/scripts/ui → Layer 4（`disable_error_code`）
        └─ 否，或在 production code → 回到 Layer 3（per-line）
```

Layer 4 通用約束：
- `disable_error_code` 優先於 `ignore_errors = true`（精準壓制 > 全面忽略）

### 合理使用案例

```toml
# ✅ Examples 目錄 — 100% demo 膠水碼，只有 no-untyped-call 和 operator
[[tool.mypy.overrides]]
module = ["examples.*", "<package>.examples.*"]
strict = true
disable_error_code = ["no-untyped-call", "operator"]

# ❌ 過度壓制 — 即使在 examples 也不應一口氣加這麼多
[[tool.mypy.overrides]]
module = ["examples.*"]
strict = true
disable_error_code = ["operator", "no-untyped-call", "union-attr", "call-arg", "misc", "attr-defined", "arg-type"]
# union-attr, call-arg, misc, attr-defined, arg-type 應用 per-line suppress
```

### 反模式：在 adapter 用 module-level 壓制 arg-type 等錯誤

```toml
# ❌ 反模式：adapter 用 module-level 壓制 arg-type
# 原因：遮蓋同模組內未來新增程式碼的 arg-type 錯誤
[[tool.mypy.overrides]]
module = "<package>.adapters.sj.data"
strict = true
disable_error_code = ["arg-type", "untyped-decorator"]

# ✅ 正確：adapter 內部用 per-line suppress（Layer 3）+ Facade 模式
# adapter 的公開方法有正確型別標註，消費端不受影響
# @raw_shioaji.on_tick_stk_v1()  # type: ignore[untyped-decorator]
# self._api.set_order_callback(cb)  # type: ignore[arg-type]
```

### 反模式：在生產碼用 module-level disable

```toml
# ❌ 反模式：生產碼用 module-level disable
# 原因：會靜默隱藏同模組內未來新增程式碼的型別錯誤
[[tool.mypy.overrides]]
module = "<package>.common.logging"
strict = true
disable_error_code = ["call-arg"]

# ✅ 正確：補 stubs（Layer 2）或 per-line suppress（Layer 3）
# stubs/nautilus_trader/common/component.pyi 加上缺失的 kwarg
# 或 init_logging(component_levels=...)  # type: ignore[call-arg]
```

### UI 模組的特殊情況

UI 模組（`<package>.ui.*`）本質上是 Bokeh/Panel 的整合膠水碼，但仍然包含業務邏輯（K 線圖渲染策略、特徵顯示邏輯）。

**允許 module-level 的**：
- **`no-untyped-call`**：Panel/Bokeh 建構子大量未標註，且 `assignment`/`arg-type` 等其他 check 間接覆蓋

**必須 per-line 的**：
- **`call-arg`、`arg-type`**：隱藏 UI 邏輯中的型別問題風險高
- **`misc`**：Panel Parameterized 子類問題，但只應在實際觸發的行 suppress
- **`assignment`**：Bokeh Property 型別過嚴，但需要逐一確認

```toml
# ✅ UI 模組 — 只壓制 no-untyped-call
[[tool.mypy.overrides]]
module = "<package>.ui.*"
strict = true
disable_error_code = ["no-untyped-call"]
```

約束：
- **只壓制 `no-untyped-call`**：UI 模組不需要 `operator`（Bokeh/Panel 不涉及 Polars 算術）
- 必須加註解說明為什麼需要（不能只寫「ignore」）
- 定期 re-evaluate 是否仍需要（第三方修復後可能不再需要）
- 不用於可以被 Layer 1-3 解決的問題

### 不推薦：全域寬鬆設定

```toml
# ❌ 過度抑制 — polars 1.x 已有完整 py.typed
[[tool.mypy.overrides]]
module = "polars.*"
ignore_errors = true
```

## 詳細參考

disable_error_code 食譜（各 error code 修復模式 lookup）與 pyproject.toml MyPy Overrides 清理流程見 [python-type-gap-reference.md](python-type-gap-reference.md)。
