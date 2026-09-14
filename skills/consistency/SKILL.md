---
name: consistency

description: "文檔修改後的品質 gate——自洽性、矛盾性、順序、自包含、精準度、Signal/Noise Ratio。/consistency <文檔路徑>"
when_to_use: "Check a single Markdown document for internal quality: self-consistency, contradictions, ordering, self-containedness, accuracy, and signal/noise ratio."
context: fork
agent: Explore
argument-hint: "要檢查的文檔路徑（單一檔案）"
allowed-tools: ["Read", "Grep", "Glob", "Bash"]
---

# /consistency - 簡化版文檔品質檢查器

你是文檔品質檢查專家，負責對單一文檔進行快速、直接的品質檢查。

## 📚 委託 Skills

- [rules-reminder](../rules-reminder/SKILL.md) — `rg`/`fd` 取代 `grep`/`find`、禁止 `sed` 等 Bash 規則

Signal/noise framework: [encoder-philosophy.md](../_common/encoder-philosophy.md) — 讀取此檔案以理解 High Signal / Low Noise 分類標準。

## 🎯 檢查維度

### 1. 自洽性 (Self-Consistency)
- 術語使用是否統一
- 前後描述是否一致
- 定義與使用是否吻合

### 2. 矛盾性 (Contradiction)
- 是否存在互相矛盾的陳述
- 規則之間是否有衝突
- 範例與說明是否矛盾

### 3. 順序 (Order/Structure)
- 章節編號是否連續
- 標題層級是否正確（不跳級）
- 內容組織是否合理

### 4. 自包含 (Self-Contained)
- 引用的檔案/路徑是否存在
- 外部依賴是否可獲取
- 讀者是否需要額外資訊才能理解

### 5. 內容精準度 (Accuracy)
- 技術描述是否正確
- 程式碼範例是否可執行
- 連結是否有效

### 6. Signal/Noise Ratio（依 encoder-philosophy.md）
- **High Signal 是否充分**：設計理由、架構約束、非顯而易見的選擇、模組邊界、失敗教訓
- **Low Noise 是否存在**：API 簽名、參數表、欄位列表、完整範例 >5 行、元資訊（版本號/日期/統計）、通用知識（LLM 訓練資料已有的）
- **引用語法是否正確**：CLAUDE.md/rules 用 `@`，Skill/Command 用 `[描述](path)`，長文件用 `[描述](path)` 而非 `@`

---

## 📋 執行流程

### 步驟 0: 決定檢查目標

**目標只有兩種合法來源**：

1. **`$ARGUMENTS` 空**（無參數調用）→ 走 git diff fallback（下方）自動偵測**未 commit** 的 `.md`
2. **`$ARGUMENTS` 是一個存在的 `.md` 檔案路徑，且該路徑 ≠ 本命令定義檔（`skills/consistency/SKILL.md`）** → 直接檢查該檔，跳過 fallback

> **🔴 fail-fast guard（防 silent 自檢 — 無論如何不得繞過）**
>
> 出現以下任一情況，**立即停止，不得完成檢查、不得產出報告分數**，回「未收到有效的文檔路徑；請用 `/consistency <path>` 指定，或用無參數 `/consistency` 自動偵測 git 變更」：
>
> - **目標 = 本命令定義檔自身**（`skills/consistency/SKILL.md`）— silent 自檢的明確訊號。不論參數解析為何，只要你發現自己即將檢查的目標是這份你正在執行的命令定義檔，**必定是出錯**（用戶不會叫你檢查命令定義檔本身的品質），立即停止。這是最常見的程式化調用失敗模式（`Skill(consistency, args=...)` + `context: fork` 時，harness 可能未替換 `$ARGUMENTS`，導致你拿不到真實目標而退而求其次檢查手上的定義檔）。
> - **`$ARGUMENTS` 非空但不是一個存在的 `.md` 路徑** — 含未替換的占位符字面值（而非真實路徑）、自然語言指代（「你剛改好的」「最近改的」）、不存在的路徑。
>
> **為什麼絕對禁止**：拿不到目標卻退而求其次去檢查任意 `.md`（尤其定義檔自身），等於在沒有真實檢查對象的情況下產出分數——虛假信心，比「沒跑」更危險（違反 fail-loud）。silent 自檢（檢查定義檔自己）是最危險的形式：報告看起來完整，但檢查的是錯誤對象。

**git diff fallback**（僅當 `$ARGUMENTS` 空）— 只取**未 commit** 變更，不 fallback 到已 commit：

1. 合併 `git diff --name-only`（unstaged）+ `git diff --cached --name-only`（staged），去重 = working tree 與 HEAD 的全部落差
2. **禁止 fallback 到 `HEAD~1 HEAD`**：自動偵測的服務對象是「剛改完待檢查」的未 commit 狀態 —— 已 commit 的文檔不在服務範圍（提交前閘門非 Always：純 `.md` 常繞過 `/implement` 直接 `/commit`、且 `/implement` 5d 僅大型/中型；故不假設「已 commit = 已被 consistency 檢查」），要審請顯式 `/consistency <path>`。無未 commit 變更 = 提示用戶並結束（fail-loud，不硬擠目標）

從結果篩選 `.md`，**排除 `skills/consistency/SKILL.md`（定義檔自身）**，作為檢查目標。若無任何 `.md`，提示用戶並結束。

### 步驟 1: 完整讀取文檔（whole-document，禁只看 diff hunk）

**完整讀取整份目標文檔**（第一行到最後一行）—— **禁止只讀 git diff hunk 或「修改過的段落」**。

**為什麼必須 whole-document**：consistency 的六維度（自洽／矛盾／順序／自包含／精準／S-N）本質需要全文視角 —— 術語前後矛盾（第 10 行用 A、第 200 行用 B）、章節順序跳級、cross-section 引用斷裂，只看修改處的 diff hunk 結構上抓不到。git diff 告訴你「改了什麼」；consistency 要判斷「改動後整份文檔還自洽嗎」—— 兩者視角不同。

### 步驟 2: 執行六維度檢查
依序檢查上述六個維度，記錄發現的問題。

### 步驟 3: 驗證引用
對於文檔中引用的檔案路徑，驗證其是否存在。

### 步驟 4: 輸出報告
按照標準格式輸出品質報告。

---

## 📊 輸出格式

### 發現問題時

```markdown
## 文檔品質檢查報告

**檔案**: [文檔路徑]
**整體評分**: [X]/100

### 檢查結果

#### 1. 自洽性 [✅/⚠️/❌]
[發現的問題或「通過」]

#### 2~6. [矛盾性、順序、自包含、精準度、Signal/Noise Ratio — 格式同上]

### 問題清單

| 優先級 | 類型 | 位置 | 問題描述 |
|--------|------|------|----------|
| 🔴/🟡/🟢 | 維度名稱 | 行號 | 具體問題 |

### 改善建議
1. [具體可執行的建議]
```

### 無問題時

```markdown
## 文檔品質檢查報告

**檔案**: [文檔路徑] | **評分**: 100/100 ✅
六維度全部通過，文檔品質優秀。
```

---

## 🔧 執行約束

- **單一檔案**: 本命令專注於單一文檔檢查
- **快速執行**: 不啟動多 Agent，直接分析
- **簡潔輸出**: 報告精簡但資訊完整
- **可執行建議**: 提供具體的改善方向
- **Whole-document**: 完整讀取文檔，禁只看 diff hunk（見步驟 1）
- **Git 感知**: 無參時只從**未 commit** 變更決定檢查目標（不 fallback 到已 commit）

---

## 🔗 與其他命令

| 重疊區 | 歸誰 | 判準 |
|--------|------|------|
| 單一文檔內部自洽（術語/章節/引用/邏輯/格式/S-N） | **/consistency**（本命令） | 單檔、內部一致性 |
| 文件↔程式碼同步、Capabilities/Kanban 準確性、專案級 S-N | **/doc-health** | 跨檔、doc↔code、消費 scan findings |
| 跨檔 single-source invariant | **/sync-sources** | 機械跨檔單一源驗證（含 rules/ → 非 Claude 部署 bundle 新鮮度） |

> 本命令只看**單一文檔內部**自洽；該文檔與程式碼/其他檔是否同步，交 /doc-health。

---

## 📝 使用範例

```bash
# 自動偵測：檢查未 commit 的 .md（無未 commit 變更則提示，不 fallback 到已 commit）
/consistency

# 檢查指定文檔
/consistency CLAUDE.md

# 檢查指定路徑的文檔
/consistency docs/api-design.md
```
