---
name: feedback_llm-native-no-skill
description: skill 設置雙面判準——LLM 原生能力不設 skill（distill 類破壞性操作預設最保守）；重複性操作值得固化成一句話入口（觸發語句＋程序段＋when_to_use）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_372193ce-2444-49c7-9d0a-2c03d5efb247
---

2026-08-16 skills 大掃除（85→67 顆）時用戶裁決的治理準則——與下方「值得固化」正面判準合成 skill 設置的雙面判準：**設不設的分界＝程式碼/常識推導不出的專案校準，或 user 會重複觸發的操作程序**。

> merged_from: feedback_natural-language-entry-for-repeatable-ops.md, 2026-08-31

1. **LLM 已原生會的能力不設 skill**（平行 agent 調用、任務分解、增量交付、spec-first、TDD 循環、mermaid 語法、OWASP/code review 通用清單）——通用方法論層刪除，委託點改就地摘要。保留的是專案特化校準（並發表、worktree 紀律、失敗教訓反制）。
2. **distill 類破壞性壓縮預設最保守**：用戶明言「distill 常會太過頭，所以我不常用」→ instruction-clean --distill 預設 conservative、NEVER 清單（失敗教訓/設計理由/約束/負空間/型別關係/慣例映射任何強度禁觸）、資訊不滅（換形非刪除）、縮減 >30% 逐條列出。
3. **mermaid 圖設計成 theme 無關**：寧可簡單配色（顯式 fill+color 成對），禁 init 強制主題。

**Why**: 用戶 dark theme 下遇過 LLM 配色不可讀；distill 被 AI 過度壓縮燙過手。治理方向是「skill 只承載程式碼/常識推導不出的專案校準」。

**How to apply**: 未來新增/審查 skill 時先問「這是 LLM 原生能力還是專案校準？」；同類破壞性操作（清理/壓縮/刪除）預設強度取最保守。相關：[[feedback_ai-rules-no-backward-compat]]

**延伸到 spawn prompt（2026-08-31）**：native 能力不包腳手架同樣適用 agent dispatch——glm-5.3-flash 原生 vision，dispatch 時當一般 model 用（說目標＋給圖徑，它自己看、自己組織報告）；禁加「每張圖五問」rubric 或「怎麼看圖」操作指示——腳手架把 native 能力當外部設備驅動，多餘且污染模擬類任務（人類冷開模擬要自然反應，不要表格填寫）。self-driven probe 類合約（入口/驅動鏈/產物隔離）不屬腳手架——那是環境事實，仍要給。

**distill 產物驗證閘（2026-08-31 user 指示「蒸餾完之後要看結果是不是合理，可能開 agent 檢查 diff」）**：破壞性壓縮的產物必過 fresh-eyes agent diff 審查（語義損失軸優先：失敗教訓/設計理由/約束/負空間/慣例映射，「換形非刪除」逐段對照）——與最保守預設配套成雙閘：預設防過頭、agent 驗漏失。

## 正面判準：重複性操作值得固化成 skill 一句話入口（natural-language-entry-for-repeatable-ops 併入）

archify 弧收尾（2026-08-31）實例：user 問「我要下命令要怎樣再生？沒有啥 skill or 叫 llm 做的方法嗎」——首答給了兩條 shell 命令（deliver＋visual-check）被追問；第二次把程序固化成 skill 觸發語句（「重生 arch-report」／「重生 <主題>」＋when_to_use 加 "Regenerate arch-report"）才命中需求。

**Why**: user 的工作流萬事經 AI session——重複操作的記憶負擔應由 skill 承擔，不是 user 背命令。AI 即興執行（程序只存在對話/transcript 裡）在新 session 不可靠；固化成 skill 觸發語句＋程序段＝跨 session 確定行為。與上方第 1 條（LLM 原生能力不設）不衝突：本條固化的是**專案特化的重複程序**，不是通用方法論。

**How to apply**: 某操作性程序被 user 問「怎麼再做一次」時，別只給 CLI——把它固化進對應 skill：①寫明觸發語句（user 自然會說的話，中英並列）②機械可執行的 step-by-step 程序段（含例外：缺場/壞場如何報告）③frontmatter when_to_use 加觸發詞。回答 user 時「一句話入口」為主、CLI 為輔（理解底層用）。首例落地見 [[project_archify-illustrate-html-mode-eval]]。
