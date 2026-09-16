---
name: spec

description: "需求釐清：結構化需求討論（User Story、UC 定位、Scenario Matrix、邊界），為 /execution-plan 做需求層準備。/spec [需求描述] [--write]（--write 落任務家 <task>/spec.md）"
when_to_use: "Clarify a requirement (User Story + UC + Scenario Matrix + boundaries) before /execution-plan. Lightweight, optional — EP is self-sufficient."
argument-hint: "你要做什麼功能或改變"
---

# /spec — 需求釐清

EP 前的**需求層**澄清。把「討論一下感覺對了」的鬆散共識，結構化成 User Story + UC 定位 + Scenario Matrix + 邊界，為 `/execution-plan` 提供需求層輸入。

**定位（純輔助）**：spec 是需求釐清（問「要做什麼」），不是實作規劃。全域 codebase 研究、前期 POC、UC 盤點建卡都在 `/execution-plan`（EP 自足）。spec 不做這些。

> **為什麼這樣切**：人走阻力最小的路——重命令會被跳過。把研究/POC/UC盤點放必走的 EP（一定執行），把 spec 瘦身為輕量需求澄清（阻力降、更可能用）。討論期共識 ≠ 結構化對齊；普通對話給的是共識幻覺，spec 強迫把「感覺」變成 User Story + UC + SM + 邊界的結構。

UC-Driven Development 方法論見 [ai-development-guide.md](../../ai-development-guide.md) 的「UC-Driven Development」章節。

---

## 參數

| 參數 | 說明 |
|------|------|
| 無參數 | 預設：對話中產出需求摘要（不寫檔案），可直接接 `/execution-plan` |
| `--write` | 寫入任務家 `MM-DD-<task-name>/spec.md`（**任務家探測**：`ai-analysis/_tasks/` 在場→雜項家、線任務→`ai-analysis/_projects/<線>/tasks/`、否則 repo-root `00-tasks/`——單一源見 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」；task 目錄與後續 EP／Report Shell 同處——一弧全生命檔案同處）。適用於換 session 時傳遞 context |

---

## 執行流程

### Phase 1: 對齊（2-3 turns）

快速確認方向和範圍。

1. **User Story 一句話**：目標 + 痛點 + 範圍
2. **規模判定**：

| 規模 | 後續行為 |
|------|---------|
| 大型（跨模組、新功能） | 完整 Phase 1-4 + 後續 `/execution-plan` |
| 中型（功能優化、新 API） | Phase 1-4（深度調整）；後續規劃載體（card Planning Contract 或 standalone EP）依 [execution-plan](../execution-plan/SKILL.md) 流程規模分級裁定 |
| 小型（bug fix、文檔） | 建議直接做，跳過 `/spec` |

User Story 格式（參考）：
```
作為 [角色]，我想要 [功能]，因為 [動機]。
目前的痛點：[問題]
現在怎麼處理：[workaround]
```

**假設浮出**：對齊時立即列出假設，不靜默填補模糊需求。
```
ASSUMPTIONS I'M MAKING:
1. [假設]（來源：用戶確認 / 既有討論）
→ 正確的話請告知，否則我將按照這些假設繼續。
```

> 技術假設的**驗證**（POC）不在 spec 階段——前期可行性 POC 在 `/execution-plan` 段落驗證策略，深度驗證在 `/ep-validate`。

### Phase 2: UC 定位 + Scenario Matrix

**UC 是開發的驅動層**。在此定義需求要實現什麼能力（需求層），而非盤點 codebase 既有 UC（那是 `/execution-plan` UC 盤點 + 自動建卡的事）。

1. **UC 定位**：需求要實現的能力描述（日後 EP 段落引用）。若疑似已有相近 UC，標注讓 EP 盤點時留意
2. **Scenario Matrix**：強制思考使用者會遇到的情境，避免實作完成才發現漏掉錯誤路徑或邊界

| # | 場景 | 觸發 | 預期行為 |
|---|------|------|---------|
| SM-1 | [使用者意圖] | [CLI flag / 事件 / 錯誤操作] | [系統該怎麼反應] |

**必須涵蓋**：Happy path / 錯誤操作 / 邊界案例 / 效能期待差異

> Scenario Matrix 產出後，`/implement` 階段 5a 會將場景提煉成自包含描述散到 UC 的「消費場景」欄位。

### Phase 3: 邊界 + 成功條件

**邊界定義**：
```
Always（一定做）：[列表]
Ask First（先討論再做）：[列表]
Never（不做）：[列表]
```

**成功條件量化**：將模糊需求轉為可驗證的目標（測試類型分佈、關鍵情境覆蓋，不寫數量）。

### Phase 4: 產出

**預設（無參數）**：在對話中產出需求摘要，不寫檔案。用戶可直接接 `/execution-plan`。

**`--write`**：寫入任務家 `MM-DD-<task-name>/spec.md`（任務家探測見參數表；task 目錄與後續 EP／Report Shell 同處）。適用於換 session 時傳遞 context。

**需求摘要格式**：

```markdown
## 需求摘要
### 目標 / User Story
### UC 定位
- [能力描述]（📋 新增 / 更新既有）
### Scenario Matrix
### 邊界（Always / Ask First / Never）
### 成功條件
```

> 此摘要作為 `/execution-plan` 的需求層輸入。EP 自足——有 spec 則引用其 UC/SM，沒有則 EP 自己產。

---

## 流程位置

```
/spec（純輔助·需求釐清，可選）→ /execution-plan（自足：全域研究 + UC盤點 + SM + 段落）→ [/ep-validate] → /implement → [/code-review] → /commit
```

> spec 是需求釐清（人類在 EP 前澄清意圖）；EP 是實作規劃（機器自足）。全域研究、前期 POC、UC 盤點建卡都在 EP——spec 不做這些。
