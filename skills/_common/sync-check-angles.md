# Sync 檢查角度完整定義

> **載入時機**: 僅在 `/instruction-sync` 執行時按需讀取。本檔案定義 12 個檢查角度的判斷標準和驗證方式。

---

## 角度一：導航有效性（核心層，最重要）

> **核心原則**：instruction 檔（AGENTS.md 為主、CLAUDE.md legacy）的導航職責是讓 AI 從「概念」定位到「符號」（導航-A）；符號→位置的機械查找由 LSP 接手（導航-B）。讀完 instruction 檔後，AI 應能回答「這個概念的核心符號是什麼？」，再由 LSP 解析到檔案位置。
>
> 導航-A / 導航-B 二分與 LSP 分工定義見 [instruction-writing.md](../../rules/instruction-writing.md)「導航優先原則」。

**判斷標準**：抽取 3-5 個關鍵概念，驗證每個概念是否有指向 class/function **符號名**的導航種子。若無法從文檔定位到符號，標記為導航缺口。檔案路徑非必要（LSP 可從符號名解析）。

| 檢查維度 | 說明 | 驗證方式 |
|---------|------|----------|
| **概念→符號連結** | 文檔引入的概念是否有 class/function **符號名**指引（檔案路徑選用） | 抽取 3-5 個關鍵概念，驗證是否能在 instruction 檔找到對應符號名；用 `workspaceSymbol "<符號名>"` 機械驗證符號可解析 |
| **職責→符號對應** | 文檔描述的每項職責是否指向具體符號 | 對照職責表或模組描述，驗證每項提到的職責都有對應符號指引 |
| **跨模組依賴導航** | 外部模組引用是否具體到 class/function（不只是模組名） | 檢查 instruction 檔中提到的外部模組依賴，驗證是否有「哪個 class/function」的指引，而非只寫模組名 |
| **資料流可追蹤性** | 多步驟流程中，step 間的 input/output 是否可追蹤 | 當文檔描述了多步驟流程時，驗證：(1) 每個 step 有入口符號的指引；(2) step 間的產出型別有描述；(3) 下游 step 的輸入來源可追蹤。無多步驟流程的模組標 N/A |

**導航 Decoder Test**：

基於 instruction 檔內容，嘗試回答以下導航問題（不查閱源碼）：

| 問題 | 通過標準 |
|------|---------|
| 「我要修改 X 的邏輯，核心符號是什麼？」 | 能定位到 class 或 function **符號名**（檔案路徑由 LSP `workspaceSymbol` / `goToDefinition` 解析即可） |
| 「Y 這個概念在哪裡實作？」 | 能指向符號名（檔案路徑選用） |
| 「Z 的上游資料從哪來？」 | 能追蹤到上游步驟和產出型別 |

**機械驗證（LSP 優先）**：文檔提到的 symbol，用 `workspaceSymbol "<name>"` 確認可解析 —— 比 `test -f file.py` 更準（直接驗證符號存在且 LSP 找得到，取代「檔案路徑是否存在」的間接驗證）。LSP 不可用時（worktree、Cython、無語言伺服器）降級為檢查檔案路徑。

**失敗處理**：若導航問題無法從 instruction 檔回答，標記為導航缺口（navigation gap），產出可執行的修改建議（見 Sync Summary ACTION 段落）。

---

## 角度二：程式碼一致性（核心層）

| 檢查項目 | 說明 | 驗證方式 |
|---------|------|----------|
| 檔案路徑引用 | 文檔中的路徑是否存在 | `Bash test -f` |
| 類別/函數簽名 | 描述的簽名是否正確 | `LSP goToDefinition` 精確定位（降級：`rg` 搜尋定義） |
| 行為描述 | 描述的行為是否與實際一致 | `Read` 程式碼內容比對 |
| 目錄結構 | 描述的結構是否正確 | `Bash ls` 驗證 |
| **語義正確性 spot-check** | 文檔描述的演算法行為是否準確 | 抽查 1-2 個核心函數的實作 |

### 語義正確性 spot-check 規則

> **目的**：sync 是結構性檢查（有沒有），但語義錯誤（描述了但描述錯了）是最危險的文檔問題 — 因為路徑存在、class 存在、方法存在，但行為描述是錯的。

**執行時機**：當文檔包含演算法/流程的具體行為描述時（如「用 X 方法排序」、「目標函數是 Y」）。

**檢查方式**：
1. 從文檔中識別描述了具體演算法行為的段落
2. 隨機抽 1-2 個核心函數，`Read` 實際 .py 比對
3. 比對重點：文檔描述的「方法/策略/目標函數/邏輯」是否與程式碼實作一致

**範例**：文檔說「`<BuilderClass>` 以 `<claimed_metric>` 為目標函數」→ Read `<builder>.py` 發現 `metric: str = "<actual_metric>"` → 標記為語義不準確。

---

## 角度三：涵蓋性檢查（完整層，--all）

| 檢查項目 | 說明 | 驗證方式 |
|---------|------|----------|
| 重要模組遺漏 | 核心模組是否被記錄 | 掃描目錄結構 |
| API 完整性 | 公開 API 是否都有記錄 | `Grep` 搜索 `def`/`class` |
| 規範覆蓋 | 重要規範是否被記錄 | 檢查配置檔案 |

---

## 角度四：元資訊檢查（品質層，--quality）

> **參考**: [instruction-clean](../instruction-clean/SKILL.md)

### 應該移除的元資訊

| 模式 | 範例 | 原因 |
|------|------|------|
| 版本號 | `> **版本**: 2.0` | AI 不關心版本歷史 |
| 更新日期 | `> **更新日期**: 2025-01-01` | AI 只需要當前規則 |
| 歷史變更 | `## 變更歷史\n - v1.0: ...` | 應放 CHANGELOG.md |
| 統計資訊 | `行數: 387`, `字數: 5234` | 對 AI 無意義 |
| 生效日期 | `> **生效日期**: 2025-01-01` | 不影響規則內容 |

### 可以保留的資訊

| 模式 | 範例 | 原因 |
|------|------|------|
| 符號連結說明 | `🔗 Symbolic Link: ...` | 解釋檔案結構 |
| 專案概述 | `## 專案概述\nxxx 專案是...` | AI 需要了解專案 |
| 繼承關係 | `**繼承**: 上層 AGENTS.md（全域 guide bundle）` | AI 需要知道繼承關係 |

---

## 角度五：蒸餾評估（完整層，--all）

> **參考**: [instruction-clean --distill](../instruction-clean/SKILL.md)

### Signal / Noise 分類

**High Signal（保留）**：
- 設計理由、架構約束、非顯而易見的選擇
- 模組邊界、失敗教訓
- 核心原則/約束、高層級架構圖

**Low Noise（蒸餾）**：
- API 簽名、參數表、欄位列表
- 完整範例 (>5 行)、過時範例、重複說明

**灰色地帶（預設保留）**：

| 內容類型 | 保留條件 | 移除條件 |
|---------|---------|---------|
| 範例程式碼 | <= 5 行，展示關鍵用法 | > 5 行或過時 |
| 檢查清單 | 行為約束、決策要點 | 顯而易見 |
| 表格 | 模組職責、組件對照 | 過時、重複 |

### Low Noise 處理策略

> **核心原則**：蒸餾 = signal/noise 分離，不是直接刪除。

**直接移除**：API 簽名、完整欄位列表、版本變更歷史
**簡潔描述替代**：重要設計概念（為什麼）+ `檔案:行號` 引用

---

## 角度六：內部品質檢查（品質層，--quality）

| 檢查維度 | 說明 | 驗證方式 |
|---------|------|----------|
| **自洽性** | 術語統一、前後描述一致、定義與使用吻合 | 文檔內容比對 |
| **矛盾性** | 規則衝突、範例與說明矛盾 | 邏輯分析 |
| **順序** | 章節編號連續、標題層級正確（不跳級） | 結構掃描 |
| **自包含** | 引用檔案/路徑存在、外部依賴可獲取 | `Bash test` 驗證 |
| **精準度** | 技術描述正確、程式碼範例可執行 | 實際驗證 |

---

## 角度七：Signal/Noise Ratio 評估（核心層）

> **核心原則**：instruction 檔是 Encoder（壓縮知識表示），品質取決於 signal/noise ratio，不是長度。

| 檢查項目 | 說明 | 判斷方式 |
|---------|------|----------|
| High Signal 內容比例 | 設計理由、架構約束、失敗教訓佔比 | 估算 high signal 行數 / 總行數 |
| Low Noise 內容 | API 簽名、參數表、欄位列表、完整範例 >5 行 | 識別並標記 |
| 程式碼範例長度 | 每個範例是否 <= 5 行 | 逐個檢查 |

**評估標準**：
- 良好：High Signal >= 60%，無 Low Noise 內容
- 需改善：High Signal 40-60%，或有少量 Low Noise
- 需蒸餾：High Signal < 40%，或有大量 Low Noise

**建議動作**：signal/noise ratio 不足時，建議執行 `/instruction-clean --distill` 進行 signal/noise 分離。

---

## 角度八：引用語法正確性（品質層，--quality）

> **核心原則**：`@` 是強制載入（每次 session 都付代價），`[描述](path)` 是按需讀取。選錯語法會導致 AI context 浪費或知識缺失。

| 檢查項目 | 說明 | 判斷方式 |
|---------|------|----------|
| `@` 濫用 | 用 `@` 引用長文件或偶爾需要的內容 | 檢查 `@` 引用的檔案行數和內容性質 |
| markdown link 漏用 | 該用 `@` 的核心約束卻用了 `[text](path)`（**對 AGENTS.md 不適用**——AGENTS.md 禁 `@`，見下方修正建議） | 檢查每次對話都需要的引用是否用了 `@` |
| Skill/Command 誤用 `@` | Skill 不支援 `@` transclusion | 檢查 command/skill 檔案中是否有 `@` |

**修正建議**：
- **AGENTS.md 禁 `@`**（跨 harness 不展開，CC 專屬機制）：每次對話需要的核心約束直接寫入本檔；`@path` 僅限 legacy CLAUDE.md；跨檔引用一律 markdown link
- 偶爾才需要 / 檔案偏長 → 改用 `[描述](path)`
- Skill / Command 中的引用 → 必須用 `[描述](path)`

---

## 角度九：消費端文檔連鎖影響（完整層，--all）

> **核心原則**：程式碼變更不只影響同目錄的 instruction 檔（AGENTS.md/CLAUDE.md），還會影響消費端目錄的 instruction 檔和其他相關 .md 文檔。

當目標目錄的程式碼有變更時，必須追蹤 import 鏈找出所有消費端：

| 步驟 | 說明 | 驗證方式 |
|------|------|----------|
| 識別變更 | 從 `git diff` 提取被修改的 class/function | diff 分析 |
| 追蹤 import 鏈 | 搜尋哪些目錄 import 了被修改的模組 | `rg` 搜尋 import 語句（用 LSP findReferences 確保消費端完整覆蓋） |
| 定位消費端文檔 | 消費端目錄是否有 instruction 檔或相關 .md | `Glob` 搜尋 |
| 檢查連鎖影響 | 消費端文檔是否引用了已變更的 API | `Read` + `rg` 比對 |

**範例**：`<module>/` 的核心 class 變更 → 不只 `<module>/` 的 instruction 檔（AGENTS.md/CLAUDE.md），連 `examples/<module>/CLAUDE.md` 和引用該 API 的說明文檔也需要檢查同步性。

---

## 角度十：dep-graph 矛盾（完整層，--all）

> **核心原則**：instruction 檔宣告的 "Does NOT depend on" 必須與實際 import 依賴一致。宣告不依賴但實際有 import 是最危險的文檔問題 — 因為它讓 AI 誤判模組邊界。
>
> **為何用 dep_graph 而非 LSP**：X1 是「否定宣稱」—— 證明 data 對 strategies **沒有任何** import 邊。這需窮舉邊集合，LSP 點查詢（findReferences）結構上不擅長否定驗證（要確認每個符號都零引用）。dep_graph 一次靜態分析給完整 `edges`，集合差集即驗證。分工定義見 scan-project SKILL「LSP 與 dep_graph 的分工」。

**前置條件**：需要 `.project-snapshot.json`（由 `/scan-project` 產出）。無 snapshot 時跳過此角度。

| 檢查項 | 說明 | 驗證方式 |
|--------|------|----------|
| X1 矛盾 | instruction 檔宣告 "Does NOT depend on X" 但 dep-graph 有 import edge → X | LLM 讀取 instruction 檔的 "Does NOT depend on" 段落，比對 `dep_graph.edges[]` |
| X1 缺失宣告 | dep-graph 顯示模組 A 大量依賴模組 B，但 instruction 檔未宣告邊界 | 分析 `dep_graph.edges[]` 中模組間依賴密度 |

**判斷標準**：

- **critical**：明確宣告 "Does NOT depend on" 但有 import edge（矛盾）
- **suggestion**：高耦合模組對（fan_out > 5）但無 Module Boundaries 段落

**範例**：`data/` 的 instruction 檔（如 `data/AGENTS.md` 或 `data/CLAUDE.md`）宣告 "Does NOT depend on: strategies" 但 dep-graph 顯示 `data.indicators` import `strategies.signal_gen` → 標記為 X1 矛盾。

---

## 角度十一：模組覆蓋缺口（完整層，--all）

> **核心原則**：dep-graph 中有明確邊界的模組（≥ 3 個檔案）應有對應的 instruction 檔（AGENTS.md/CLAUDE.md）。缺少 instruction 檔的模組對 AI 是知識黑洞。

**前置條件**：需要 `.project-snapshot.json`。無 snapshot 時跳過此角度。

| 檢查項 | 說明 | 驗證方式 |
|--------|------|----------|
| X6 缺口 | dep-graph 有模組但無 instruction 檔 | 消費 `findings[]` 中 check_id=X6 的項目；或比對 `dep_graph.modules[]` vs 目錄結構 |
| X6 小模組 | 模組 < 3 個檔案，instruction 檔非必要 | 過濾 `file_count < 3` |

**判斷標準**：

- **important**：模組 ≥ 3 個檔案但無 instruction 檔
- **suggestion**：模組 1-2 個檔案，無 instruction 檔可接受

**與角度三（涵蓋性）的區別**：角度三檢查「文檔是否記錄了核心模組」，角度十一用 dep-graph 精確資料驗證「哪些模組缺少文檔」。

---

## 角度十二：通用性（完整層，--all）

> **核心原則**：泛用 rules/commands（非專案特定工具）教 pattern，不應釘死真實專案符號/路徑/數字 —— 否則 fact drift（該專案一改，例子就錯）且跨專案失效。原則定義見 [instruction-writing.md](../../rules/instruction-writing.md)「應該避免 → 專案特定事實」。

**判斷標準**：泛用 rules/（auto-loaded）、泛用 commands（非某專案專屬，如 `upgrade-*`）中，例子是否用 `<placeholder>` 而非真實專案符號。

| 檢查項 | 說明 | 驗證方式 |
|--------|------|----------|
| 專案符號殘留 | 泛用檔含真實專案 package/module/class 名（非 `<placeholder>`） | LLM 語義判斷「這是泛用檔卻出現非佔位的具體符號」；抽查 examples / import 路徑 |
| 例外：專案特定工具 | `upgrade-sj`/`nt`、`trading-analysis` 等本質是某專案工具 | 標 N/A，不檢查 |

**判斷方式**：用 LLM 語義判斷，**不用 denylist**（denylist 脆弱，新專案加入就失效）。判斷準則：符號是「具體專案的 package/class」還是「通用佔位（`<package>`/`<EnumClass>`）」。

**與角度二（程式碼一致性）的區別**：角度二檢查「描述是否與程式碼一致」，角度十二檢查「泛用檔是否不該出現該專案符號」。
