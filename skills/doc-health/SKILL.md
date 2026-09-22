---
name: doc-health

description: "文件健康檢查。消費 scan findings + LLM 直接讀取驗證文件準確性。"
when_to_use: "Check documentation accuracy after /implement, before /commit, or during daily maintenance. Use --report for full report, --sync-system-map to align SYSTEM-MAP.md."
argument-hint: "[--quality] [--all] [--report] [--sync-system-map]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
---

# /doc-health — 文件健康檢查

> **角色**：documentation 的 lint layer — 檢查所有文件的準確性，回答「文件準確嗎？有沒有過時、斷裂、遺漏？」

---

## 核心哲學

**scan_project.py 做機械性檢查，LLM 做判斷性檢查。不依賴 snapshot registry。**

| 檢查類型 | 負責者 | 資料來源 |
|---------|--------|---------|
| 機械性（路徑、tag、重複） | scan_project.py → `findings` | `.project-snapshot.json` |
| 判斷性（品質、導航、覆蓋） | LLM 直接讀取 | instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）+ backlog 卡（`backlog/`） |

LLM 需要細節時，直接 Read instruction 檔（AGENTS.md 為主，legacy 單檔模組 fallback CLAUDE.md）和 backlog 卡（`backlog/tasks/` 檔或 `backlog task list --plain`），不依賴中間 registry。

---

## 使用模式

```
/doc-health              → 聊天報告（scan findings + 核心品質檢查）
/doc-health --quality    → 加品質層（instruction 檔 signal/noise + 導航有效性）
/doc-health --all        → 全部檢查（含過時卡片、SYSTEM-MAP 同步）
/doc-health --report     → 產出 doc-health-report.md 檔案
/doc-health --sync-system-map → 用 Capabilities 狀態同步 SYSTEM-MAP.md
```

---

## 執行流程

| 步驟 | 名稱 | 觸發 | 說明 |
|------|------|------|------|
| 1 | 消費 Scan Findings | 預設 | 讀 `.project-snapshot.json` 的 `findings`，按嚴重度呈現 |
| 2 | 清單一致性 | 預設 | Capabilities 表格/入口有效性 + Skill 索引↔`skills/` 目錄比對 |
| 2.5 | 知識庫真相源偵測 | 預設（慣例命中時） | 知識庫 instruction 檔帶「真相源映射」宣告 → 對可機械驗證宣稱跑 drift 偵測（report-only） |
| 3 | instruction 檔品質 | --quality | LLM 評估 signal/noise + 導航有效性 |
| 4 | 過時卡片 | --all | 讀 `backlog/tasks/` frontmatter `updated_date`（比 mtime 可靠），標記長期未動卡 |
| 5 | SYSTEM-MAP 同步 | --all / --sync-system-map | LLM 讀 SYSTEM-MAP.md + Capabilities，比對狀態 |
| 6 | 產出報告 | 預設（聊天）或 --report（檔案） | — |

### 步驟 1：消費 Scan Findings

如果 `.project-snapshot.json` 存在且 < 24 小時：
- 直接呈現 `findings` 陣列中的機械性問題
- 按嚴重度分類：critical / important

如果不存在或過期：
- 告知用戶執行 `uv run python scan_project.py --project-root . --output .project-snapshot.json`
- 或降級為純 LLM 直接讀取模式

**Scan findings 類型**：

| check_id | 說明 | 嚴重度 |
|----------|------|--------|
| X-cap-path | Capabilities 入口路徑不存在 | important |
| X-ep-ready | To Do/In Progress 卡片引用的 EP 檔案不存在 | important |
| X6 | 模組有 .py 但無 instruction 檔（AGENTS.md/CLAUDE.md） | important |

### 步驟 2：清單一致性（預設）

LLM 直接讀取索引/清單類段落，驗證與實際檔案一致：

**Capabilities（instruction 檔 `## Capabilities`——AGENTS.md 為主，CLAUDE.md legacy）**：
- **表格格式**：3 欄（能力 / 入口 / 狀態）完整、狀態 emoji 正確
- **入口有效性**：CLI 命令格式合理、路徑指向存在（scan 的 X-cap-path 已做路徑檢查，此處補充 CLI 命令等判斷）
- **模組覆蓋**：主要模組都有 Capabilities 表格（scan 的 X6 已做機械性檢查）

**Skill 索引（`skills/AGENTS.md` Skill 索引段）**：
- **機械比對**：`fd -t d . skills/ --max-depth 1` 列實際 skill 目錄，`rg` 抓索引列出的 skill name，比對差集
- **標記**：索引有但目錄無 = 幽靈（important）；目錄有但索引無 = 遺漏（important）
- **容錯**：無 `skills/AGENTS.md` 或無 Skill 索引段 → 跳過（非所有專案有 skill 索引）

### 步驟 2.5：知識庫真相源偵測（opt-in by 慣例）

**慣例偵測**：`rg -l "^#+ .*真相源映射" -g "AGENTS.md"` ——知識庫目錄的 instruction 檔以「真相源映射」**section**（表：每份文檔 ↔ 權威真相源）宣告派生視圖契約時，本步對該知識庫跑 drift 偵測。錨定 heading（非內文散句）避免導航文字誤命中。無命中 → 跳過（非所有專案有知識庫慣例）。

**偵測範圍**——只查可機械驗證的宣稱；語義 drift（敘事是否仍連貫、結論是否仍成立）屬知識庫重編流程（該 instruction 檔內的對齊流程）的工作，本步不硬偵測：

| 宣稱類型 | 機械驗證 |
|---------|---------|
| 引用存在性 | 知識庫文檔內的檔案連結/路徑 → `fd` / 存在性檢查 |
| 入口宣稱 | 文檔提到的 CLI command / script / 函式符號 → `rg` 於 repo；0 hits 只標「未驗證（rg 無命中）」供判讀，不斷言不存在（動態引用不可見） |
| 狀態宣稱 | 知識庫的 UC/功能狀態 ↔ Capabilities / SYSTEM-MAP cross-read，有出入列兩邊現值 |
| 排程宣稱 | 文檔提到的排程（launchd plist / cron / 排程腳本時刻）↔ 專案排程配置目錄現況 |

**嚴重度與處置**：全部 🟡 important **只報告不修正**——知識庫是敘事文檔，修正 = 消化重編（狀態語義），機械 patch 會侵蝕敘事連貫。findings 前綴 `[KB-drift]`（便於晨報 rg 聚合）。偵測輸出同時是知識庫對齊流程的輸入（[maintain](../maintain/SKILL.md) 晨報 🔥 累積 → 重編 session 認領）。

### 步驟 3：instruction 檔品質（--quality）

遵循 [instruction-writing.md](../../rules/instruction-writing.md) 品質標準：

- **Signal/Noise**：無可推導內容（API 簽名、參數表）、無統計/版本/日期
- **導航有效性**：每個關鍵概念有 symbol 種子（位置由 LSP 解析）（導航 Decoder Test）
- **消費場景**：Capabilities 行有下游消費者資訊

### 步驟 4：過時卡片（--all）

讀 `backlog/tasks/` 每張卡 frontmatter 的 `updated_date`（CLI 寫入維護，比 mtime 可靠）：
- To Do > 30 天 → important
- In Progress > 14 天 → important

### 步驟 5：SYSTEM-MAP 同步（--all / --sync-system-map）

1. 讀取 SYSTEM-MAP.md（如果存在）
2. 對每個功能區塊，從模組 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities 讀取能力狀態
3. 比對功能生命週期狀態是否一致
4. `--sync-system-map`：自動推導並更新 SYSTEM-MAP.md（展示 diff 待確認）

生命週期推導規則（**功能層級**狀態 — 聚合該功能內所有 UC；UC 層級狀態 ✅📋❌🔧🟡🟢 見 [ai-development-guide.md](../../ai-development-guide.md)）：

| 條件 | 狀態 |
|------|------|
| 功能內 UC 全部 ✅ + 有整合驗證 | ✅🔍 Verified |
| 全部 ✅ 但無整合驗證 | ✅ Built |
| 有 📋/🔧 | ⚠️ Issues 或 📋 Planned |

---

## 聊天報告格式

```markdown
## Doc Health Report

### Scan Findings（機械性檢查）

| check_id | 嚴重度 | 說明 | 來源 |
|----------|--------|------|------|
| X-cap-path | important | ... | data/CLAUDE.md |

### 🔴 Critical（必須修正）
- [ ] ...

### 🟡 Important（建議修正）
- [ ] ...

### 💡 Suggestion（可以改善）
- [ ] ...

### Summary
- scan_findings: X (critical: X, important: X)
- quality_issues: X
- needs_action: true/false
```

---

## `--report` 檔案產出

`--report` flag 產出 `doc-health-report.md`，包含：
- 健康度總覽表格
- 🔴/🟡/💡 問題清單（scan findings + 品質檢查）
- **系統能力地圖**：按模組組織所有 Capabilities，含可點擊連結

---

## 與其他命令

| 重疊區 | 歸誰 | 判準 |
|--------|------|------|
| 文件↔程式碼同步、Capabilities/Kanban 準確性、專案級 S-N、過時卡片 | **/doc-health**（本命令） | 跨檔、doc↔code、消費 scan findings |
| 單一文檔內部自洽（術語/章節/引用/邏輯/格式） | **/consistency** | 單檔、內部 |
| 跨檔 single-source invariant | **/sync-sources** | 機械跨檔單一源 |

> 本命令看**文件與程式碼/專案狀態同步**；單一文檔內部自洽交 /consistency。

---

## 執行約束

- **release-gate（drop-module 後必跑）**：刪除整檔/整模組的 refactor 後，跑本命令 + `rg -F "<deleted-symbol>"` 掃導航文檔（root AGENTS.md / architecture.md / dependency-graph.md / SYSTEM-MAP.md + 各模組 AGENTS.md）當 release-gate。真實案例：清理日刪 facade 後 ≥6 個導航檔仍引用它，靠事後審計才抓——drop-module 不跑此 gate = 文檔 drift 漏到下個 session。
- **前瞻 vs 回溯分工**：本命令的 X-cap-path 是**回溯查**（既有 Capabilities 路徑還在嗎）；**前瞻查**（這次 doc 編輯有沒有新增指向虛無的引用）屬 `/code-review` docs mode 的「前瞻 phantom 偵測」——兩者互補，不重疊。
- **容錯**：無 `.project-snapshot.json` 時降級為純 LLM 檢查，不報錯
- **容錯**：無「真相源映射」慣例命中時跳過步驟 2.5，不報錯
- **容錯**：無 `backlog/` 目錄時只檢查 Capabilities，不報錯
- **容錯**：無 SYSTEM-MAP.md 時跳過步驟 5，不報錯
- **容錯**：無 `## Capabilities` 的 instruction 檔跳過，不報錯
- `--report` 產出覆蓋既有 `doc-health-report.md`（不備份）
- `--sync-system-map` 修改 SYSTEM-MAP.md 前展示 diff 待確認
