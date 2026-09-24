---
name: ep-validate

description: "POC 驅動的 EP 技術假設驗證。/ep-validate <EP路徑>"
when_to_use: "Validate high-risk technical assumptions in an Execution Plan by writing and executing POCs. Use when EP involves unverified external APIs, SDKs, concurrency models, or serialization formats."
argument-hint: "<Execution Plan 檔案路徑>"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "Agent"]
---

# /ep-validate — POC 驅動的 EP 技術假設驗證

EP Review 抓邏輯矛盾，EP Validate 抓跑不起來的。用 POC 驗證 EP 中的高風險技術假設。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則

---

## 核心概念

> **EP Review = 靜態分析**（讀文件找矛盾）
> **EP Validate = 動態驗證**（寫程式碼跑起來確認假設）

兩者正交互補，不是取代關係。

### 與 EP 段落驗證策略（前期 POC）的分工

EP 段落驗證策略做可行性 POC（能不能做），`/ep-validate` 做深度 POC（效能、邊界、壓力）。`/spec` 命令現為純需求釐清，不做 POC。

| | EP 段落驗證策略 POC | /ep-validate |
|--|-----------|-------------|
| 時機 | EP 段落設計時（前期） | EP 之後 |
| 深度 | 可行性驗證（能不能做） | 深度驗證（效能、邊界、壓力） |
| 範圍 | 該段落的高風險假設 | EP 所有段落的假設 |
| 產出 | `poc/poc_*.py`（build+commit 後清除） | EP 回寫 + `poc/poc_*.py` |

EP 段落已驗證過的假設，`/ep-validate` 可跳過或做更深入的邊界測試。

---

## 何時需要

| EP 特徵 | 需要 EP Validate？ | 說明 |
|---------|-------------------|------|
| 外部系統整合（API、SDK） | ✅ 需要 | 跨框架互動 pseudo code 看不出 |
| 新演算法 / 數學模型 | ✅ 需要 | 邊界行為難從 pseudo code 推斷 |
| 效能敏感路徑 | ✅ 需要 | 延遲假設需要實測 |
| 跨語言 / 跨進程通訊 | ✅ 需要 | 序列化、IPC 細節不跑不知道 |
| 無外部互動的變更（純重構、配置、文檔） | ❌ 不需要 | 不涉及技術風險，EP Review 足夠 |

**觸發時機**：
- 預設：EP Review → EP Validate → `/implement`（靜態先、動態後）
- 例外：EP 含「致命假設」（假設錯了整個 EP 要重寫）→ 可跳過 Review 先跑 Validate

---

## 與 EP Review 的順序

**預設**：EP Review → EP Validate（靜態先、動態後）

理由：EP Review 低成本高速度，先抓邏輯問題可減少後續 POC 數量；POC 基於邏輯正確的 EP，假設清單更精確。

**例外**：EP 含致命技術假設時，先 Validate 確認技術可行，再 Review 檢查邏輯。

判斷原則：**如果你心裡有「這個假設錯了整個 EP 要重寫」的疑慮 → 先 Validate。**

---

## 執行流程

### Phase 1: 假設識別

讀取 EP，識別高風險技術假設：

1. 掃描 EP 所有段落的 Pseudo Code 和 Context
2. 找出「未經外部系統驗證」的假設（API 行為、SDK 用法、序列化格式、併發模型、效能預期等）
3. 每個假設標記風險等級

**風險等級**：

| 等級 | 定義 | POC 失敗後果 |
|------|------|-------------|
| 致命 | 假設錯了整個 EP 要重寫 | 回到 `/execution-plan` 重新規劃（必要時先 `/spec` 釐清需求） |
| 高 | 假設錯了對應段落要大改 | 修正 EP 該段落 + 可能影響上下游段落 |
| 中 | 假設錯了需調整實作細節 | 微調 Pseudo Code，不影響段落結構 |

輸出 POC 清單（展示給用戶確認後再執行）：

| POC # | 假設 | 風險 | 驗證標的 | 預期結果 |
|-------|------|------|---------|---------|
| 1 | [假設描述] | 致命 | [具體驗證什麼] | [通過的定義] |

### Phase 2: POC 生成與執行

對每個假設生成 POC 並執行：

1. 生成 `poc/poc_<描述性名稱>.py`（遵循下方 POC 檔案規範）
2. `uv run python poc/poc_<描述性名稱>.py` 執行
3. 記錄結果（✅ 通過 / ❌ 假設錯誤 / ⚠️ 部分通過 + 具體發現）

**POC 設計原則**：
- 每個 POC 聚焦**一個假設**
- 包含 happy path + 至少一個邊界案例
- 必須可獨立執行（不依賴其他 POC 的結果）
- POC 之間可共用外部資源（如 Redis），但邏輯不耦合

### Phase 3: 結果回報與 EP 更新

**回報格式**：

| POC # | 假設 | 結果 | 關鍵發現 |
|-------|------|------|---------|
| 1 | [假設] | ✅ 通過 | [具體發現] |
| 2 | [假設] | ❌ 假設錯誤 | [哪裡錯了 + 正確行為] |

**EP 回寫**（回寫原則同 [ep-review.md](../ep-review/SKILL.md)）：

card-first 弧（AIR-135.2 AC#4）：回寫錨改載**卡 id＋卡 section 錨**——findings 表「EP 段落」欄載卡 section（AC 編號／Plan 段／約束區），POC 結果記卡 comments、採納修正回寫卡對應 section（supersedes＋reason）、結算面進 Final Summary（回寫語序單一源＝[ep-review](../ep-review/SKILL.md)「回寫格式」card-first 段）；EP review 區段回寫＝條件分支（該弧原有 EP 時照舊）——

在 EP review 區段用 Finding Record 表格(同 ep-review,欄位定義見 [workflow-review-pattern.md](../_common/workflow-review-pattern.md)),「問題」欄填 POC 驗證結果:

```
## EP Validate Findings

| ID | 嚴重度 | EP 段落 | 問題(POC 結果) | 建議 | 狀態 |
|----|--------|---------|----------------|------|------|
| 1 | 🔴 | S1 | POC#1 ❌ 假設錯誤 | 修正設計 | implemented |
| 2 | ⚠️ | S2 | POC#2 部分通過 | 調整段落 | needs-confirmation |
```

✅ 通過 → `verified`;❌ 錯誤 → `implemented`(回寫修正)+ 必要時標「需重新 Review」;⚠️ 部分通過 → `needs-confirmation`。

**致命假設被推翻** → 提示用戶：EP 需要大幅修正，建議重新跑 `/execution-plan`（必要時先 `/spec` 釐清需求）。

---

## POC 檔案規範

**放置位置**：`poc/poc_<描述性名稱>.py`

**命名慣例**：
- `poc_tick_to_bar.py`（Tick 聚合邏輯驗證）
- `poc_sj_subscription.py`（SJ 訂閱回調驗證）
- `poc_nt_redis_writer.py`（NT + Redis 寫入驗證）

**檔頭格式**：

```python
"""POC: [假設描述]

驗證: [具體驗證標的]
EP 段落: S{N}
風險: [致命/高/中]
來源: [假設來源，如 path/to/file.py:ClassName 或用戶確認]
"""
```

**POC↔plan linkage（card-first，AIR-135.2 AC#4）**：card-first 弧的檔頭標注改載**卡 id＋section 錨**——`TaskRef: <卡id> <section>`（如 `TaskRef: AIR-135.2 AC#4`；卡 section 即錨，存儲分配見 AIR-135.2 AC#3，不另立格式）；`EP 段落: S{N}` 標注形態對 EP 弧保留（上方檔頭照舊）。

**生命週期**：POC 為暫時性驗證產物，僅存活到該 EP 的 build+commit 完成。
- 驗證期間：保留供 build 提煉驗證意圖
- build 時：其驗證的行為被改寫成正式測試（提煉行為意圖，非搬檔案）
- commit 時：`/commit` 階段 2.7 確認承接後清除 POC 檔案

---

## 輸出格式

```markdown
## 🔬 EP Validate 結果

**EP**: [路徑] | **POC**: [N]（✅ [X] / ❌ [Y] / ⚠️ [Z]）

### POC 清單
| POC | 檔案 | 假設 | 結果 | 關鍵發現 |
|-----|------|------|------|---------|

### EP 回寫紀錄
[段落 + 修正摘要]

### 建議
[可直接 /implement / 需修正 EP 後重新 Review / 需重新規劃]
```

---

## 執行約束

- **每個 POC 必須實際執行**（`uv run`），不憑靜態分析宣稱驗證通過（遵守 `must-execute-before-complete` rule）
- **POC 失敗不中止**：繼續驗證其他假設，最後統一回報
- **不生產化**：POC 只驗證假設，不直接成為生產程式碼（行為在 `/implement` 改寫成測試，檔案 commit 後清除，見 `/commit` 階段 2.7；生產化在 `/implement` 階段，可參考 POC 設計但需遵循生產標準）
- **遵守 [rules-reminder](../rules-reminder/SKILL.md)**：`uv run` 前綴、`rg`/`fd` 取代 `grep`/`find`

---

## 流程位置

```
/spec（純輔助·需求釐清，可選）→ /execution-plan（含 EP Review）
  → [/ep-validate]（可選，高技術風險時）
  → /implement
```

前置：`/execution-plan`（或手動撰寫的 EP）
後續：`/implement`（基於驗證後的 EP）

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始 EP 技術驗證"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「技術驗證完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```
