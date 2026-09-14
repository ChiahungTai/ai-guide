---
name: self-contained-prompt
description: "把工作交給另一個 LLM/session/repo 時，打包成對方讀懂的 self-contained prompt 的設計原則唯一真相源。接手方三層（同 repo 新 session / 跨 repo / 跨 provider 網路 LLM）決定嵌入程度、標準 schema、決策脈絡必含（為何選 X 不選 Y）、drift 防護（嵌 code 讀回 commit 版本）、跨 provider 機密 redact。/handoff command 與 agent-review-cycle subagent prompt 共用。觸發：handoff、交接、接續、給另一個 session/LLM、問 ChatGPT/Gemini、跨 repo、self-contained、開新 session 並行、交工作給別的 worktree、給 prompt。"
---

# self-contained-prompt — 交接 prompt 設計原則 domain 層

把工作交給另一個 LLM / session / repo 時，**對方讀不到你的對話 context**（決策脈絡、進度、為何這樣做都只在對話裡）。本 skill 是把這些「對話結晶」打包成 self-contained prompt 的原則唯一真相源，被 [`/handoff`](../handoff/SKILL.md)（產交接 prompt）與 [agent-review-cycle](../_common/agent-review-cycle.md)（subagent prompt）共用。

## 與既有機制邊界

| vs | 本 skill（原則） | 對方 |
|----|---------------|------|
| [`/handoff`](../handoff/SKILL.md) | 三層、schema、drift、機密 | **動作**（收集進度→套 schema→產出 block）|
| [agent-review-cycle](../_common/agent-review-cycle.md) | subagent prompt 也遵循本原則（同環境・審查型）| 3-perspective 執行範本 |
| [`/at`](../at/SKILL.md) | 不重疊 | **usage reset resume**（5h limit，自己續）|

**handoff vs `/at`**：`/at` 解「時間接續」（usage 用盡，自己 resume）；handoff 解「空間分工」（交另一個 session/provider 並行或接手）。不互斥、不重疊。

## 收進判準

一條原則收進本 skill：**所有交接場景都適用**（同repo / 跨 repo / 跨 provider）。場景特化（如跨 provider 機密 redact）在對應段落標示，不另開 skill。

---

## 接手方三層（self-contained 程度 = 讀得到什麼的反函數）

| 接手方 | 讀得到 | self-contained | 機密 |
|--------|--------|---------------|------|
| **同 repo 新 session** | 源 repo（EP/code/kanban）| 引用路徑 + 決策脈絡 + 起手式 | 無慮 |
| **跨 repo session**（如 `<other-repo>`）| 它自己 repo，讀不到源 repo | 跨 repo 背景 + 源 repo 相關片段 | 無慮 |
| **跨 provider**（網路 LLM：ChatGPT/Gemini/...）| 無 code | 嵌**最小必要**片段 + 抽象化 | ⚠️ redact |

**「完整內嵌」是迷思** —— 嵌「回答問題必要的最小片段」，非整檔。對方讀得到 repo 就引用路徑；讀不到才嵌必要片段；跨 provider 連不相關細節都該抽象化掉。

## 標準 schema

每份交接 prompt 套用（實例歸納一致）：

| 欄位 | 說明 |
|------|------|
| 任務一句話 | 對方要做什麼 |
| baseline commit | grounding |
| 來源 EP 路徑 | 有 EP 必引（EP 是 self-contained 載體，不重造）|
| 已完成清單 | 避免對方重做 |
| **已決策（為何選 X 不選 Y）** | **必含** —— 決策脈絡只在對話，不交就重推導 |
| 下一步 / 待決項 | 接手者起手 |
| 驗收標準 | 怎樣算完成 |
| 承接 commit 不重做 | 明示「做到 commit X，別重做」|
| 建議執行 tier | 條件式路由建議（非斷言、無模型名）：一般（lite）需三條件全滿（保護面厚＋EP 條款機械可判＋審查鏈全開）；旗艦 only 五項不可讓（全文見 model-routing skill「旗艦資格條款」） |
| workspace／卡歸屬 | 強制欄：repo／WT 路徑＋卡 id 歸屬（runtime workspace 不自管卡歸屬） |

## 決策脈絡原則

> **核心：已交代就附上，重點在 self-contained**（不搞「自動摘 vs 明指」二分）。

- 對話中交代過的背景/決策 → 帶上
- **「為何選 X 不選 Y」必含**：對方不知道你的取捨，不交代就重新爭論已定的事（最尖銳痛點：code 用 branch 交得過去，決策脈絡交不過去 → 接手方重推導浪費）
- **不過濾判斷框架** —— 用戶交代的就是該傳的，由用戶拿捏該帶多少（用戶要新 LLM 帶不同視角時，自然會少給）
- 沒交代的不硬擠

## drift 防護

嵌 code 到 prompt 時，**讀回已 commit 版本**（非記憶 / 非 uncommitted），確保嵌的是權威版本，不留 drift。

## 跨 provider 機密檢查

丟網路 LLM（ChatGPT/Gemini）前 flag 可能敏感並提醒 redact：帳號/金鑰/token、真實持倉/帳戶資料、未公開策略邏輯、真實客戶資料。**對方看不到 code，能抽象化的抽象化** —— 不必給實作細節，給問題本質。

## 與既有整合

- **引用 EP**：工作有 EP → 引用段落（self-contained 載體），handoff 補「這次對話剛定的決策」；無 EP → 現擠 brief（套完整 schema）
- **`.at-contexts/`**：僅 `at-context-*`（`handoff --save` 寫檔已退場，改掛卡 `--append-notes`）
