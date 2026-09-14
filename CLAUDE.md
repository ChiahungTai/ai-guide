# ai-guide 專案 — Claude wrapper

@AGENTS.md

> **全域開發指南**：由 Claude 經 `~/.claude/CLAUDE.md`（→ `ai-development-guide.md`）獨立載入（演化/驗證/UC-Driven/架構/量化鐵律）—— 不在此 `@import`（全域指南是獨立檔，避免雙源 drift）。

## Claude 專屬機制（AGENTS.md neutral 化後補回）

> ai-guide 轉型 multi-harness——AGENTS.md 已拔除 Claude 專屬機制（保持 neutral，四家 harness 都讀），Claude 端細節在此。

### 載體選擇（Hook/Rule/Skill/Agent）

> 載體維度是「**執行確定性**」（何時載入、多確定會執行），與「受眾」（產出給誰）正交。同一命令（如 `/debrief`，人類受眾）可用 Rule 治理其行為、用 Agent 委派調查。

| 需求 | 用什麼 | 為什麼 |
|------|--------|--------|
| 必須每次零例外執行 | **Hook**（`~/.claude/settings.json`，user 層——本 repo hooks 的實際註冊處） | 確定性保證，非建議性 |
| 每次 session 都需遵守的行為規範 | **Rule**（`~/.claude/rules/`） | Auto-loaded，治理性 |
| 不需要每次載入的領域知識或工作流 | **Skill**（`.claude/skills/`） | On-demand，不消耗日常 context |
| 按需委派的專家子能力 | **Agent**（repo `agents/` 單一來源，`~/.claude/agents` symlink → 本目錄；慣例見 `agents/AGENTS.md`） | 獨立 context，由主對話視任務委派 |

> 判準單一源＝instruction-writing skill「載體選擇」＋memory-audit skill「載體統一定義表」；本表為快查投影，衝突時以單一源為準。

**判斷原則**（等價摘要——判準以單一源為準）：純機械＋單一入口＋無語義例外 → Hook；須在首個有後果決策前在場 → Rule；on-demand 方法論 → Skill；獨立 context 專家 → Agent（repo `agents/` 定義，symlink 部署）。
