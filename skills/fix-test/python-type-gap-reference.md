# Python Type Gap — Reference

python-type-gap skill 的詳細參考（pyproject overrides 清理 + disable_error_code 食譜）。SKILL.md 放四層策略與 Layer 1-4 核心；本檔是 lookup 細節，按需讀取。

## pyproject.toml MyPy Overrides 清理

定期檢查 `[tool.mypy.overrides]` 是否仍必要。

### 檢查流程

1. **識別冗餘 strict=true**：如果 global 已設 `strict = true`，override 再設一次是冗餘
2. **識別不存在的模組**：override 引用的模組目錄可能已刪除或從未建立
3. **逐項移除測試**：暫時移除 override → 跑 `uv run mypy <package>/` → 看是否仍需要
4. **驗證全專案**：`uv run mypy <package>/ --strict` 確認所有模組都能通過

### 常見可移除項目

| 類型 | 判斷方式 | 處理 |
|------|---------|------|
| 冗餘 `strict = true` | global 已有 | 直接刪除整個 override |
| 不存在的模組 | `fd -t d -d 1 . <package>/` 確認 | 直接刪除整個 override |
| 第三方 blanket ignore | 套件已有 `py.typed` | 移除，改用 Layer 1-3 |
| UI framework ignore | Panel/Bokeh 的 runtime metaprogramming | 保留，加註解 |

## disable_error_code 縮窄食譜

當 `ignore_errors = true` 被替換為 `disable_error_code = [...]` 後，每個 error code 都應驗證是否為「不可修復的第三方缺口」。以下食譜記錄各 error code 的分類和修復方式。

**重要前提**：此食譜適用於所有程式碼。生產碼中的 suppress 使用 per-line `# type: ignore[code]`（Layer 3）；只有 `no-untyped-call` 和 `operator` 可考慮 module-level（Layer 4），且僅限 examples/scripts/ui。

### 可修復的 Error Codes（不應全局壓制）

| Error Code | 修復方式 | 範例 |
|-----------|---------|------|
| `str-bytes-safe` | `float()` / `str()` 包裹 polars 回傳值後再用 f-string | `f"{float(df['close'].mean()):.2f}"` |
| `assignment` | 型別加寬（`dict[str, object]`）、isinstance narrowing、中間變數重新命名 | `stats: dict[str, object] = ...` |
| `no-any-return` | `float()` / `int()` 包裹返回值；複雜型別用 local `# type: ignore[no-any-return]` | `return float(self.config.initial_capital + self.realized_pnl)` |
| `valid-type` | 修正錯誤的型別名稱（`any` → `Any`）或移除 module as type | `-> dict[str, Any]` |
| `call-arg` | 第三方 API kwargs 缺口用 local `# type: ignore[call-arg]` | `figure(x_axis_type="datetime")  # type: ignore[call-arg]` |
| `type-arg` | 為 bare generic 加型別參數；Bokeh GlyphRenderer 等深層泛型用 partial stubs 定義為 non-generic | `dict` → `dict[str, Any]`、GlyphRenderer stub: non-generic class |
| `return-value` | `float()` 包裹 `Any` 返回值給 `.sort(key=...)` | `.sort(key=lambda x: float(x["avg_ret"]))` |

### 不可修復的 Error Codes（第三方缺口）

以下 error code 源自第三方套件的型別缺陷，無法透過修改我們的程式碼解決。但根據遮蓋風險，處理方式不同：

#### 可 module-level 壓制（間接覆蓋安全）

| Error Code | 來源 | 說明 | 允許 module-level 的理由 |
|-----------|------|------|------------------------|
| `no-untyped-call` | Shioaji / Panel / Bokeh 未標註函式 | 呼叫未標註的第三方 API | 只警告「呼叫了無型別函式」，真正的型別錯誤由 `assignment`、`arg-type`、`attr-defined` 等 downstream check 覆蓋 |
| `operator` | Polars `Any` 算術 | `Any + float` 無法靜態解析 | **僅限** examples/ 等非 production code |

#### 必須 per-line suppress（遮蓋風險高）

| Error Code | 來源 | 說明 | 為什麼不能 module-level |
|-----------|------|------|----------------------|
| `union-attr` | Polars 寬聯合型別 stubs | `.mean()` 回傳 `int \| float \| date \| ... \| None` | 遮蓋自己新增屬性存取的型別錯誤 |
| `arg-type` | Polars `Any` / NautilusCatalog union / Bokeh kwargs | `get_bars()` 回傳 `pd.DataFrame \| pl.DataFrame`；Bokeh `figure()` kwargs 不匹配 | 遮蓋引數型別錯誤，風險最高 |
| `attr-defined` | NT / Bokeh / Panel 動態屬性 | `config.initial_capital` 等 runtime 動態生成的屬性 | 遮蓋拼字錯誤或不存在屬性 |
| `type-arg` | 其他第三方泛型（非 GlyphRenderer） | 套件泛型參數過於複雜 | 遮蓋缺少型別參數的問題 |
| `assignment` | Bokeh Property 型別系統 | Panel 的 Parameter 和 Bokeh 的 Property 型別系統與靜態分析不兼容 | 遮蓋賦值型別不匹配 |
| `misc` | Panel Parameterized 子類 | Panel 的 `Parameterized` 基類回傳 `Any`，子類化時 mypy 無法推斷 | 遮蓋子類定義的各種型別問題 |

### 修復模式速查

#### `str-bytes-safe` — f-string 中的 `Any` 值

當 polars 方法回傳 `Any`（因為 `.mean()` / `.std()` 等回傳寬聯合型別），直接在 f-string 中格式化會觸發 `str-bytes-safe`。

```python
mean_val = df["close"].mean()  # mypy sees Any (Polars stubs gap); runtime: int | float | date | None
print(f"mean={mean_val:.2f}")  # ❌ str-bytes-safe

print(f"mean={float(mean_val):.2f}")  # ✅ float() 包裹
print(f"range={str(df['datetime'].min())}")  # ✅ str() 包裹（日期型）
```

#### polars `Series` 彙总方法的寬聯合 — `.max()`/`.mean()` 等

polars `Series` 因無泛型 dtype，其彙总方法（`.max()`/`.min()`/`.mean()`/`.std()`/`.first()`/`.last()`/`.item()`）皆回傳寬聯合 `int | float | Decimal | date | time | datetime | timedelta | str | bytes | ... | None`（同上方 `str-bytes-safe` 的 `.mean()`）。裸 `int(series.max())` / `cast(int, ...)` 觸發 `arg-type`（union 含 `date`/`bytes`，`int()` 不接受）。

```python
v = per_day["len"].max()  # mypy: int | float | Decimal | date | ... | None（同 .mean()）
n = int(v)                # ❌ arg-type（union 含 date/bytes，int() 拒絕）

n = v if isinstance(v, int) else 0           # ✅ isinstance narrowing
# 或先 .item() 確認非 None，再顯式轉換
```

**禁用** `int(series.max())` / `cast(int, series.max())` —— union 的 `date`/`bytes` 分支使裸轉換型別不成立；isinstance narrowing 或先 `.item()` + 顯式轉換才安全。

#### `type-arg` — bare generic 加型別參數

```python
def get_stats() -> dict:           # ❌ bare dict
def get_stats() -> dict[str, Any]: # ✅ 加型別參數

def load_data() -> list:              # ❌ bare list
def load_data() -> list[dict[str, Any]]: # ✅ 巢狀也加

from collections import deque
buf: deque = deque()       # ❌
buf: deque[Any] = deque()  # ✅
```

需要時加 `from typing import Any`。

#### `type-arg` — Bokeh GlyphRenderer deep generic via partial stubs

當第三方套件的 class 是 `Generic[T]` 但消費端不關心具體型別參數時，可用 partial stubs 將其定義為 non-generic。

**`stubs/bokeh/models/renderers.pyi`**:
```python
from typing import Any

class GlyphRenderer:
    """Non-generic stub for Bokeh's GlyphRenderer[GlyphType]."""
    data_source: Any
    glyph: Any
    visible: bool
    name: str | None
    level: str
    view: Any
    def __init__(self, **kwargs: Any) -> None: ...
```

**`stubs/bokeh/models/__init__.pyi`**:
```python
from typing import Any
from bokeh.models.renderers import GlyphRenderer as GlyphRenderer
def __getattr__(name: str) -> Any: ...
```

**`stubs/bokeh/__init__.pyi`**:
```python
from typing import Any
def __getattr__(name: str) -> Any: ...
```

#### `assignment` — 型別加寬與 narrowing

```python
# NautilusCatalog union 回傳 → 加寬型別
interval_dfs: dict[str, pl.DataFrame | pd.DataFrame] = {}

# dict[str, object] 回傳 → 用 int(float(...)) 鏈式轉換
val = int(float(stats.get("count", 0)))  # float(object) → arg-type (suppressed), int(float) → legal

# isinstance narrowing
df = df_real if isinstance(df_real, pd.DataFrame) else df_real.to_pandas()
```

#### `no-any-return` — 包裹或 local ignore

```python
# 簡單型別 → explicit conversion
def get_equity(self) -> float:
    return float(self.config.initial_capital + self.realized_pnl)

# 複雜型別（DataFrame / dict）→ local ignore
def load_data(self) -> pl.DataFrame:
    return self.catalog.get_bars(...)  # type: ignore[no-any-return]
```

#### `call-arg` — 第三方 API kwargs

```python
fig = figure(
    width=700, height=400,
    x_axis_type="datetime",  # Bokeh stubs 不認這個 kwarg
)  # type: ignore[call-arg]
```

#### `return-value` — sort key 中的 `Any`

```python
# dict[str, Any] 取出的值是 Any，sort key 期望 comparable type
candidates.sort(key=lambda x: x["avg_ret"])       # ❌ return-value
candidates.sort(key=lambda x: float(x["avg_ret"])) # ✅ float() 包裹
```

### 驗證流程

從 `disable_error_code` 中逐個移除 error code 的標準流程：

1. 暫時從 `disable_error_code` 移除目標 code
2. `uv run mypy <examples_dir>/ --no-error-summary > /tmp/mypy.txt`
3. `rg -F "[code-name]" /tmp/mypy.txt | wc -l` 計數
4. 分類：可修復（用食譜）vs 不可修復（保留壓制）
5. 可修復的用 agent 並行處理（按檔案分組）
6. 修完後驗證 `uv run mypy <examples_dir>/` 零錯誤
7. 確認 `uv run ruff check examples/` 通過
