# Lint/Type 修復 recipes — ruff＋mypy 自動修正與型別慣例（fix-test reference）

> 前身＝`/lint-fix` skill（AIR-113 reference-demotion：退出 resident 注入面、內容降為 fix-test 的 reference）。lint/type 修復是 fix-test 修復迴圈的一環——`/fix-test` 觸發時依本檔執行 ruff 三步與型別問題分析。

你是 Python 程式碼品質修正專家，專精於使用 ruff 和 mypy 自動修正常見的程式碼問題。

## 🎯 核心目標

1. **自動修正 AI 寫 code 的常見壞習慣**（ruff）
2. **強制執行 Python 3.12+ 的現代型別慣例**（mypy）
3. **減少 code review 時的重複工作**

## 🚀 執行流程

> **🔴 強制規則：三步都必須依序執行。ruff 無錯誤不代表可以跳過 mypy。mypy 檢查結果是後續「問題分析」的輸入，沒跑 mypy 就無法分析型別問題。**

### Phase 1: Ruff 自動修正（auto-fix）

```bash
uv run ruff check --fix $ARGUMENTS
uv run ruff format $ARGUMENTS
```

### Phase 2: MyPy 型別檢查（check + 人工分析）

```bash
uv run mypy $ARGUMENTS
```

> ⚠️ **mypy 輸出禁 `| tail/grep`**（exit code 被遮蔽 → 誤判通過，見 [bash-hard-rules](../../rules/bash-hard-rules.md)）；輸出要完整讀（餵問題分析），看 output 重導檔案再 Read。

- mypy 不會 auto-fix，輸出做為下方「問題分析與建議」的輸入
- **即使 Phase 1 零錯誤，Phase 2 仍必須執行** — 型別問題和 lint 問題是正交的

## 🔍 問題分析與建議

當發現無法自動修正的問題時，按以下優先級分析：

### 優先級 1：import outside toplevel (PLC0415)

#### ❌ 錯誤做法：直接在函數內 import 偷懶
```python
# AI 常偷懶這樣做，通常不是真的 circular import
def process_data(data):
    import pandas as pd  # ❌ 偷懶
    return pd.DataFrame(data)
```

#### ✅ 正確做法：toplevel import
```python
import pandas as pd

def process_data(data):
    return pd.DataFrame(data)
```

#### 判斷標準
1. **預設假設：不是 circular import**。AI 常偷懶放在函數內，99% 只是偷懶，不是真的有循環依賴
2. **真的遇到 circular import 時**：正確解法是重構目錄結構（調整 parent-child 關係），不是局部 import。局部 import 只掩蓋問題
3. **檢查 pyproject.toml 的 per-file-ignores**：如果專案已設定例外，尊重專案配置

### 優先級 2：`__init__.py` re-export

> 對齊 [python-standards.md](../../rules/python-standards.md) 的 re-export 禁令。判準是「**是否 re-export**」不是「行數」——一行 `from .x import Y` 就違規，50 行 docstring 沒問題。

#### ❌ 錯誤做法：re-export 符號到 `__init__.py`（LLM 最常犯的錯）

```python
# package/__init__.py — 禁止。建立隱性依賴鏈，import 開銷膨脹（實測 5ms→1300ms）
from .module_a import ClassA
from .core import PublicAPI

__all__ = ["ClassA", "PublicAPI"]
```

#### ✅ 正確做法：`__init__.py` 只放 docstring，消費端用完整路徑

```python
# package/__init__.py
"""Package docstring."""

# Import policy: 無 re-export。消費端用 from package.module import Class
```

```python
# 消費端 — 直接從子模組 import
from package.module_a import ClassA
```

**唯一例外**：套件發佈給外部使用的穩定 public API（Facade Pattern）。內部專案不適用，完整論證見 [python-standards.md](../../rules/python-standards.md) 的「Facade Pattern 為何不適用內部專案」段。

### 優先級 3：TYPE_CHECKING

> 對齊 [python-standards.md](../../rules/python-standards.md) 的 TYPE_CHECKING 禁令。與優先級 1（PLC0415 局部 import）同理——circular import 是架構問題，重構模組結構才是解法，TYPE_CHECKING 只是掩蓋。

#### ❌ 錯誤做法：用 TYPE_CHECKING 掩蓋 circular import
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from somewhere import SomeType  # ❌ 掩蓋循環依賴，非解決

def process(x: "SomeType"):
    pass
```

#### ✅ 正確做法：現代 Python（3.12+）不需 TYPE_CHECKING

TYPE_CHECKING 的傳統用途都有更好解法：

| 情境 | ❌ TYPE_CHECKING | ✅ 現代解法 |
|------|-----------------|-----------|
| 同檔前向引用 | （誤用） | 字串註解 `"B"` / `Self`（回傳自身） |
| 跨檔循環型別 | `if TYPE_CHECKING: from b import B` | 重構模組（抽型別到獨立模組）/ 局部 import（優先級 1） |
| 重型 import 延遲 | `if TYPE_CHECKING: import pandas` | stubs / 接受 runtime import |

```python
# 同檔前向引用 — 字串註解（Python 原生）
def process(node: "TreeNode") -> None: ...

# 回傳自身 — Self（Python 3.11+）
from typing import Self
def copy(self) -> Self: ...

# 循環依賴 — 重構或局部 import（優先級 1），不用 TYPE_CHECKING 掩蓋
```

### 優先級 4：舊式 typing 慣例

#### ❌ 錯誤做法：使用舊式型別
```python
from typing import List, Dict, Optional

def process(items: List[str], config: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    ...
```

#### ✅ 正確做法：Python 3.12+ 內建型別
```python
# 優先使用內建型別語法
def process(
    items: list[str],
    config: dict[str, int] | None = None
) -> dict[str, int]:
    ...
```

#### 修正規則
- `List[T]` → `list[T]`
- `Dict[K, V]` → `dict[K, V]`
- `Set[T]` → `set[T]`
- `Tuple[T1, T2]` → `tuple[T1, T2]`
- `Optional[T]` → `T | None`
- `Union[T1, T2]` → `T1 | T2`

#### `type-arg`：裸型別缺參數（mypy strict）

mypy strict 模式要求泛型型別必須帶參數，裸 `list`、`dict` 會觸發 `type-arg` 錯誤。

```python
# ❌ 裸型別缺參數
def get_indicators(self) -> list: ...
def build_config(self) -> dict: ...

# ✅ 帶型別參數
def get_indicators(self) -> list[IndicatorDef]: ...
def build_config(self) -> dict[str, Any]: ...
```

#### ignore_errors 模組仍應修 type-arg

即使 `pyproject.toml` 有 `ignore_errors = true`（Layer 4），修 type-arg 和 no-untyped-def 仍然有價值：
1. 未來可能移除 ignore_errors（當套件改善型別支援時）
2. IDE（PyCharm、VS Code）使用 pyright/pylance，不讀 mypy overrides
3. 正確的型別標註幫助人類理解程式碼

### 優先級 5：濫用 Any

#### ❌ 錯誤做法：動不動就用 Any
```python
from typing import Any

def process(data: Any) -> Any:  # ❌ 太寬鬆
    ...
```

#### ✅ 正確做法：用具體型別
```python
def process(data: dict[str, int | float]) -> list[str]:
    ...
```

#### 何時使用 Any
- 真的無法確定型別的動態程式碼
- 與缺乏型別註解的第三方庫互動
- **必須加註解釋為什麼需要 Any**

### 優先級 6：第三方套件 Type Gap

當第三方套件的 type annotations 不完整時，遵循 [python-type-gap](../python-type-gap/SKILL.md) skill 的四層處理策略（isinstance narrowing → Project Stubs → `# type: ignore[code]` → pyproject.toml Override）。

### 工具陷阱（ruff／uv／pytest／mypy 實測）

- **RUF100 對帳必 `--extend-select RUF100`**：`--select` 會**替換**專案 select → 專案啟用的 noqa 全變 unused（大量假值）。`--fix` 刪 noqa 前先確認理由真消失；per-file-ignores 條目刪 rule 要整體對帳（原子性）。
- **uv resolver「最高版本優先」兩頭都不可信**：floor-only constraint 遇 transitive cap 衝突會**穿過 pre-release 找解**（實證：解析成 alpha 版）——constraint 明寫 cap `>=目標,<依賴的cap` 並註解 cap 來源；`uv run` 會回寫 lock＝lock 漂移檢查點。
- **pytest `.pytest_cache/lastfailed` 是歷史不是現況**：刪檔條目永存（只在「跑且 pass」時移除）——拿它當現況失敗清單會追殺幽靈。
- **mypy overrides 的 unused note 以全 repo run 為準**：單檔 run 只觸及該檔依賴圖 → 其他模組 overrides 全報 unused（範圍假象）；刪 pyproject override 死條目前必跑全 repo mypy 取 note。

## 📋 輸出格式

### 標準輸出結構
```
## 執行摘要
[簡述執行結果，修正了多少問題]

## Ruff 修正結果
[列出自動修正的問題]

## MyPy 檢查結果
[列出型別問題]

## 需要手動處理的問題
### PLC0415: import outside toplevel
[檔案:行號] 建議：...

### 型別問題
[檔案:行號] 建議：...

## 建議修正優先級
1. [高優先級問題]
2. [中優先級問題]
3. [低優先級問題]
```

## 🔧 執行約束

### 必須遵守
- **使用 uv run**：所有 Python 命令必須使用 `uv run`
- **空 path＝工具預設＝全專案 sweep，禁自行窄化**：不把範圍代決成 git-modified 檔（實證：漏掉 lab/poc 檔 7 errors、user 兩度糾正）——跑工具的自然 scope
- **`$ARGUMENTS` 是 slash command placeholder**：Phase 1/2 的 `$ARGUMENTS` 是 slash command 參數替換（Claude Code 在 shell 執行前把它換成使用者傳入的路徑），非 shell `$VAR` 展開，不觸發 rules-reminder 的 `$` 禁令
- **尊重專案配置**：使用現有的 `pyproject.toml`，不覆蓋
- **分析前先查證**：確認問題真的存在，不基於猜測

### 分析 circular import 時
1. 檢查是否在 `pyproject.toml` 的 per-file-ignores 中
2. 如果不在，分析導入鏈是否真的循環
3. 建議重構架構而非使用局部 import

### 處理 `# type: ignore` 時
- `warn_unused_ignores = true` 會標記不必要的
- 每個被標記的都應該檢查是否真的需要
- **遵循 [python-type-gap](../python-type-gap/SKILL.md) skill 的四層策略**，`# type: ignore` 是最後手段
- 必須指定 error code（如 `[no-untyped-call]`、`[operator]`），不用裸 `# type: ignore`
- 只用於第三方套件的 gap，不用於我們自己程式碼的型別問題

## 🎯 品質檢查清單
- [ ] 執行了 ruff check --fix
- [ ] 執行了 ruff format
- [ ] 執行了 mypy
- [ ] 分析了所有 PLC0415 問題
- [ ] 檢查了 TYPE_CHECKING（對齊優先級 3 禁令）
- [ ] 識別了舊式 typing 慣例
- [ ] 檢查了裸型別缺參數（`type-arg`：裸 `list`/`dict`）
- [ ] 第三方 type gap 遵循 [python-type-gap](../python-type-gap/SKILL.md) skill 四層策略
- [ ] 每個 `# type: ignore` 都有指定 error code
- [ ] 檢查了 pyproject.toml overrides 是否仍必要
- [ ] 提供了具體的修正建議
- [ ] 建議了修正優先級
