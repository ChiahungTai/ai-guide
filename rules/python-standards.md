---
harness-scope: neutral
paths:
  - "**/*.py"
---

# Python 程式設計規範

## 命名約定

demo 用 demo_，禁 test_；測試用 test_。demo 暫存到 commit 時移 scripts/ 或刪除，值得測的行為在 build 另提煉正式測試。

## `__init__.py` 禁止 re-export

只放 docstring/註解/__version__，禁 `from .submodule import Symbol` re-export（含 __all__）；消費端用 `from package.module import Class`。每個例外內容都須回答為何不放子模組，handy function/註冊初始化衡量全消費者代價，不以行數判。判準＝消費者是否外部：內部共同重構收益不足抵銷 import/循環/IDE 代價；真實案例見 git 歷史本節。

### 遷移既有 re-export

禁先刪：先查全消費者（含相對 import）逐一改完整 module 路徑，全部改完才清 __init__ re-export；文字 rg、符號依 symbol-query-routing。

## 型別註解（Python 3.12+）

- 禁 from __future__ import annotations，字串化會掩蓋缺失/circular import；其他 class 前向引用用字串。
- 禁 TYPE_CHECKING，循環須重構解決；回傳自身/子類用 Self（cls、enter、copy 等）。
- 禁 List/Dict/Set/Tuple/Optional/Union 舊 typing——改內建泛型與 T | None / T1 | T2；typing 只 import Callable、Protocol、TypeVar、ParamSpec、Self、Any。
- Any 限 JSON/第三方外部邊界並註明理由——先查 venv 套件 py.typed 與 source 型別，確認無法推導才用，禁猜。

## 比較式驗證 gate（IEEE 754 fail-open 防護）

比較式 gate 對非有限值 fail-open（IEEE 754：NaN 的任何比較恆 False，`x > 0` 對 NaN 靜默放行）——正 gate 用 `not (x > 0)` 形（NaN→擋），非有限輸入以前置 finite 驗證擋（`math.isfinite`，專案多處使用時 helper 化）。

## Python 命令執行

Python 命令執行（uv run 強制、pytest 背景跑、PYTHONPATH 禁令、timeout 禁令）單一源＝[tool-discipline.md](tool-discipline.md)。
