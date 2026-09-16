---
name: init-py-reasonableness-not-pattern
description: __init__.py 檢查的是「內容合理性權衡」不是「re-export pattern 偵測」
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 99e81c05-48f7-41f3-b478-e4d035f21715
---

`__init__.py` 內容是否合理，唯一本質判準是 **「這個內容的收益，是否大於它對所有消費者的代價？」**——這是 context 權衡，code（regex/hook/linter）看 pattern 看不到 context。

`__init__.py` 內容是光譜：純 docstring（合理）/ `__version__`（合理）/ handy functions（個案衡量）/ 初始化邏輯（個案衡量）/ re-export（內部專案原則不合理，facade 外部套件例外）/ 業務邏輯（不合理）。re-export 禁令只是「收益≈0、代價>0」這個公理在內部專案的**推論**，不是公理本身。

**Why**: 把 re-export 禁令當主原則，會讓 LLM 遇到 handy functions / 初始化邏輯不知如何判斷（它們可能合理）。本質原則是「合理性權衡」，re-export 是其推論。`python-standards.md` 的「審查原則」（每個內容要能回答「為什麼放在這裡而非子模組？」）就是這個公理，但過去被 re-export 強框架蓋過。

**How to apply**: `__init__.py` 合理性判斷用收益/代價權衡（python-standards.md:26）。/build 檢查時完整權衡所有內容（re-export 是否違規、handy functions/初始化個案衡量）；/lint-fix 聚焦辨識 re-export（最高頻違規，pattern + 對齊禁令），完整權衡見 python-standards.md。分工見 [[hook-vs-llm-flow-division]]。
