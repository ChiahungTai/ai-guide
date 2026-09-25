---
name: python-standards
description: "Python 程式設計規範深層載體（reference skill）——命名與 demo 生命周期（demo_ 暫存 commit 時移 scripts/ 或刪、值得測行為 build 提煉正式測試）、`__init__.py` re-export 禁令（例外判準：消費者是否外部、handy function 權衡、不以行數判；既有 re-export 遷移程序：禁先刪→全消費者含相對 import 逐一改→才清）、Python 3.12+ typing 四禁令細則（future annotations／TYPE_CHECKING／舊 typing／Any 查證流程與白名單、Self 場景）、IEEE 754 fail-open gate（NaN 比較語義、`if not (x > 0)` gate 形式、helper 抽取判準）、hook 相容型別例外。always-on 核心（核心禁令與 gate 形式）在 rules/python-standards.md bootstrap-pointer；撰寫或修改 Python、typing、__init__.py、NaN gate、清 re-export 時載入。觸發詞：demo_、test_、re-export、__init__.py、TYPE_CHECKING、from __future__、Optional、Union、typing 白名單、Self、Any、py.typed、NaN、isfinite、fail-open。"
---

# Python Standards — 規範深層載體

> 本 skill 是 `rules/python-standards.md` 的 on-demand 深層載體：non-CC bundle 端 rule 以 AIR-85 pointer 投影常駐（核心禁令在 bootstrap-pointer），本檔承載判準、程序與語義細節。Python 命令執行單一源＝[tool-discipline](../tool-discipline/SKILL.md)。

## 命名約定與 demo 生命周期

demo 用 demo_，禁 test_；測試用 test_。demo 暫存到 commit 時移 scripts/ 或刪除，值得測的行為在 build 另提煉正式測試。

## `__init__.py` 禁止 re-export

只放 docstring/註解/__version__，禁 `from .submodule import Symbol` re-export（含 __all__）；消費端用 `from package.module import Class`。

**例外判準**：每個例外內容都須回答為何不放子模組；判準＝消費者是否外部——內部共同重構收益不足抵銷 import/循環/IDE 代價。handy function/註冊初始化衡量全消費者代價，不以行數判。真實案例見 git 歷史本節。

### 遷移既有 re-export

禁先刪：先查全消費者（含相對 import）逐一改完整 module 路徑，全部改完才清 __init__ re-export。文字 rg、符號查詢依 symbol-query-routing rule（cr-first）。

## 型別註解（Python 3.12+）

- 禁 `from __future__ import annotations`：字串化會掩蓋缺失/circular import；其他 class 前向引用用字串。
- 禁 TYPE_CHECKING：循環須重構解決；回傳自身/子類用 Self（cls、enter、copy 等場景）。
- 禁 List/Dict/Set/Tuple/Optional/Union 舊 typing——改內建泛型與 `T | None` / `T1 | T2`；typing 只 import Callable、Protocol、TypeVar、ParamSpec、Self、Any。
- Any 限 JSON/第三方外部邊界並註明理由——先查 venv 套件 py.typed 與 source 型別，確認無法推導才用，禁猜。

**hook 相容例外**：hook 相容性所需的型別例外依 owner runtime／rollback 契約（ai-guide：hooks/AGENTS.md）。

## 比較式驗證 gate（IEEE 754 fail-open 防護）

NaN 的有序比較（`< <= > >=`）與 `==` 為 False，`!=` 為 True——`if x <= 0: reject` 會漏擋 NaN（fail-open）。正值 gate 用 `if not (x > 0): reject`；非有限值先用 `math.isfinite` 擋；多處共用再抽 helper。
