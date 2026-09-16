---
name: hook-vs-llm-flow-division
description: hook 只做純機械/單入口/立即危害；語義判斷交 LLM 流程（rule + command）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 99e81c05-48f7-41f3-b478-e4d035f21715
---

決定一個防範需求用 hook 還是 LLM 流程（rule + lint-fix/build/sync），用三個判準：**單一入口**（只有一條路徑觸發）、**無語義例外**（永遠該擋，無「看情況」）、**純機械 pattern**（字串匹配即決定）。三者皆是 → hook；任一不符 → LLM 流程。

第二維度是危害的時間性：**立即危害**（如 python -c 換行 + `#` 觸發權限卡關）→ hook 零例外；**累積型危害**（如 re-export 慢慢長成 40 個）→ LLM 流程漸進清理即可。

**Why**: re-export 防範本質是語義判斷（facade 例外、docstring 範例、handy functions、既有存量），用 hook 程式碼補 regex 漏洞、堵 Bash 多入口，永遠補不全。更危險的是——hook 補不全時「確定性保證」是假的，假確定性讓人放鬆警惕，比真語義（LLM 流程，雖非每次但判斷正確）更糟。

**How to apply**: 評估 hook 前先過三判準。對照組：`hooks/block-python-c-comment.py` 適合 hook（python -c 只在 Bash、換行後 `#` 永遠該擋、純字串 pattern）；re-export 三個全違反（多入口 Write/Edit/Bash、facade/docstring 例外、需 context），故不該 hook。相關：[[init-py-reasonableness-not-pattern]]

**已固化（AIR-8 結案，2026-09-02）**：三判準＋假確定性論證＋對照組已進 instruction-writing skill「載體決策樹」段；AGENTS.md 寫作治理第 2 點展開為四載體判準＋指路。未建獨立 mechanical-gate-philosophy skill（acceptance-evidence reference 分層已收斂原散落）。
