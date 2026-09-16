---
name: instruction-init

description: "為任意專案自動產生 instruction file 體系（root + 模組都雙檔：AGENTS.md source + CLAUDE.md @AGENTS.md wrapper，bottom-up）；truth/shell 分離的 repo（domain truth 在一種語言、另一語言是綁定 shell）採 Truth-Anchored 雙側地圖"
when_to_use: "Generate instruction files for a new or unfamiliar codebase. Bottom-up: analyze structure, generate module AGENTS.md (source) + CLAUDE.md (@AGENTS.md wrapper), synthesize Root AGENTS.md (source) + CLAUDE.md (wrapper). 雙檔模式見 instruction-writing.md。"
argument-hint: "/instruction-init — 預設為當前目錄，可指定專案根目錄"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent"]
---

# /instruction-init — instruction file 體系自動生成

為專案從零產生 instruction file 導航體系（**root + 每個模組都雙檔**：`AGENTS.md` source + `CLAUDE.md` `@AGENTS.md` wrapper，雙檔模式見 [instruction-writing.md](../../rules/instruction-writing.md)）。Bottom-up 策略：先理解子模組，再合成 Root，確保上層導航表準確。

## 輸入

- 預設：當前工作目錄
- 可指定：`/instruction-init /path/to/project`

## 執行步驟

### Phase 1：結構探索

先用 subagent 掃描整個目錄結構，產出結構報告：

- 目錄樹（排除 `.git`、`node_modules`、`__pycache__`、`.venv`、`build` 等噪音）
- 識別核心模組、入口點、配置、測試目錄
- 識別語言組成（單語言 / 多語言 / FFI binding）；**若為 truth/shell 分離**（domain truth 在一種語言，另一語言是綁定/re-export shell，例：Rust core + PyO3 Python shell）→ Phase 2 改用 **Truth-Anchored 策略**
- 偵測 **re-export shell 模組**：目錄只有 star-import 綁定的 `__init__.py` + 生成的 stub（`.pyi` 等）、無實質邏輯 → 記進清單，Phase 2 不為其建獨立檔（由 hub 對應表涵蓋）
- 模組間依賴方向（哪些模組被最多地方 import）；多語言 repo 分語言各自掃（例：Python import 面 + Rust crate 的 Cargo.toml 依賴面）

### Phase 1.5：Dependency Snapshot（如果 scan-project 可用）

執行 [/scan-project](../scan-project/SKILL.md) skill 產出統一知識快照。**腳本在 scan-project skill 的 `scripts/` 下——本 skill 目錄沒有 scripts/，別在自己的 skill dir 找**。依 harness 解析 scan-project skill 根目錄後執行（例：Claude 的 `${CLAUDE_SKILL_DIR}` 相對路徑是 `../scan-project/`）：

```bash
uv run python <scan-project-skill-dir>/scripts/scan_project.py --project-root . --output .project-snapshot.json
```

多語言 repo：Rust 側依賴由 snapshot 的 `rust_workspace` 涵蓋；其他語言用 Phase 1 分析補。

**腳本找不到時的紀律**：預期路徑不存在 ≠ 腳本不存在——先在部署的 skills 根下搜尋（`fd scan_project.py <skills 根>/scan-project/`；各 harness skills 目錄如 `~/.zcode/skills/`、`~/.agents/skills/`），找到即用；真的沒有才跳過 Phase 1.5。單一路徑失效就放棄機械盤點，列舉品質會退回 LLM 摘要（dogfood 實證：init 曾因跳過 snapshot 而以 agent 摘要列目錄，漏掉近半項目）。

從 snapshot 取得：

- `dep_graph.modules` / `dep_graph.edges` — 模組依賴結構（內建掃描即有；`dep_graph.source` 標示來源）
- `rust_workspace.crates` — Cargo workspace 成員、crate 內部依賴、`has_python_bindings`——truth/shell 分離 repo 的分層與綁定標記，直接餵 Truth-Anchored 策略
- `dir_inventory.dirs` — **機械目錄盤點**（深度 ≤3；檔名僅在目錄 ≤60 項時列出）——寫任何「目錄內含什麼」段落的列舉依據
- `instruction_files` — 哪些目錄已有 AGENTS.md/CLAUDE.md（取代人工掃描）
- `findings` — 預計算的機械性問題（X6 模組缺 instruction 檔、X-cap-path 路徑失效等）
- `fingerprint` — 變化偵測用 counts + hashes

其餘資訊（Capabilities 內容、Kanban 卡片內容）由 LLM 直接讀取檔案系統，不經 snapshot。

**Capabilities 覆蓋缺口報告**：列出缺少 Capabilities 表格的 library 模組（instruction 檔 AGENTS.md/CLAUDE.md），但不自動生成（需要人類意圖）。

**無 scan-project 時**：跳過此 phase，Phase 2 使用 Phase 1 的粗略分析。

### Phase 2：Bottom-up 產生 instruction files（每層 AGENTS.md source + CLAUDE.md wrapper）

從最深層的子模組開始，一路往上寫到 Root：**每層**（root + 模組）都產生 AGENTS.md（source，neutral）+ CLAUDE.md（`@AGENTS.md` wrapper，讓 Claude 讀到 AGENTS.md）——雙檔模式見 [instruction-writing.md](../../rules/instruction-writing.md)。

**既有 instruction 檔處理**：
- Phase 1.5 有 snapshot → LLM 直接掃描目錄結構確認哪些目錄已有 AGENTS.md，跳過
- 無 Phase 1.5 → 目錄已有 AGENTS.md 時預設跳過。使用者可明確確認覆蓋
- legacy 單檔模組（只有 CLAUDE.md，無 AGENTS.md）：從 CLAUDE.md 抽中立內容寫進 AGENTS.md source，CLAUDE.md 改為 `@AGENTS.md` thin wrapper

**Fork repo 的 root 檔**：root `AGENTS.md`/`CLAUDE.md` 可能是**上游維護檔**（fork 帶下來的專案自有檔）——一律不覆蓋、不修改（每個 byte 都會與 upstream 永久衝突）。此時：

- 導航 hub 落在**第一個 fork 可控層**（例：truth 側頂層、shell 側頂層各一個 hub），Module Navigation Map 由 hub 承載，不硬塞進 root
- 模組 CLAUDE.md wrapper 沿用 root 既有格式（例：root 是 `# Read AGENTS.md` + `@AGENTS.md`，模組比照）
- 最終報告註明 root 檔為上游所有、刻意不動

**Truth-Anchored 策略**（truth/shell 分離的 repo）：

- instruction 檔以 **truth 側模組**為 anchor（逐模組檔寫在 truth 側）；shell 側只為**有實質 shell 語言邏輯**的目錄建檔（re-export shell 模組不建——見 Phase 1 清單）
- shell 側 hub 必含兩張表：①「shell 模組 ↔ truth 模組對應」——標註不對齊處（shell 有目錄但 truth 無對應，或反向）②「哪裡有真的 shell 邏輯（其餘全是 shell）」
- 每個 shell 側檔案開頭指回 truth 位置（「邏輯真實所在」）——防止讀者在 shell 側找實作、或在 shell 側加邏輯
- 分層敘述以 truth 語言為主軸（例：Rust crate 分層）；理解動線 = truth 實作 → 綁定層（truth 側 `src/python/` 之類）→ shell re-export

**每個模組 AGENTS.md 包含**（source，四家 harness 都讀）：

- **模組職責**：這個模組做什麼、不做什麼
- **架構定位**：在整體系統中的角色
- **Module Boundaries**：Depends on / Consumed by / Does NOT depend on
- **關鍵設計決策**：從程式碼推導不出來的「為什麼」
- **導航索引**：如果模組很大，用 `### 類別小標題` 分組導航種子（非集中符號對照表，見 [instruction-writing skill](../instruction-writing/SKILL.md)「大模組 selectivity」段；檔案路徑選用，LSP 可從符號解析）

**Module Boundaries 精確度**（有 Phase 1.5 時加成）：
- `Depends on` 從 `edges[]` 精確推導（而非猜測）
- `Does NOT depend on` 從 `modules[]` 的 `imported_by` 反向推導
- Use LSP findReferences on module-level symbols to verify module boundaries when dep_graph is unavailable
- 無 snapshot 時，Module Boundaries 基於 Phase 1 的粗略 import 分析

**Root AGENTS.md 包含**（source，neutral 專案資訊——四家 harness 開本專案都讀）：

- 架構總覽（語言組成、分層、核心設計理念）
- Module Navigation Map（每個重要目錄一行，含模組 AGENTS.md 連結）
- Key Patterns（反覆出現的設計模式）
- Build and Development（如何建置、測試、lint）
- "Finding Things" quick reference（常見問題 → 去哪裡找）

**Root CLAUDE.md** = `@AGENTS.md`（把 neutral 專案資訊拉進 Claude session）+ Claude 專屬段（Claude 端 hook 註冊細節、slash command workflow——若有）。**thin wrapper，不重複 AGENTS.md 內容**。

**模組 CLAUDE.md** = `@AGENTS.md` thin wrapper（通常只一行——模組層少有 Claude 專屬機制；純粹讓 Claude 讀到模組 AGENTS.md source）。其他 harness（ZCode/OpenCode/Codex）直接讀模組 AGENTS.md，不需此 wrapper。

### Phase 3：驗證

- 確認所有 instruction files（每層 AGENTS.md + CLAUDE.md）的交叉引用路徑存在
- 確認 Root AGENTS.md 的 Module Navigation Map 涵蓋所有重要模組，且連結指向模組 AGENTS.md source
- 確認每個模組 CLAUDE.md = `@AGENTS.md` thin wrapper（不重複 AGENTS.md neutral 內容）；Root CLAUDE.md 同
- **dep-graph 驗證**（有 Phase 1.5 時）：確認 Module Boundaries 的 "Depends on" 與 `edges[]` 一致
- **元資訊自檢**（強制，防產出導向任務漏禁令）：對所有產出的 instruction 檔跑元資訊掃描，採 `/instruction-clean` Mode A 的**錨定 pattern**（見 [instruction-clean](../instruction-clean/SKILL.md)「識別 pattern」：`行數:`/`wc:`/`lines:`/`> **版本**:` 等，帶冒號錨定；裸匹配 `wc`/`lines` 會誤命中合法 CLI 範例如 `wc -l` 或 size 指引如 `~100 lines`）。命中標記為候選，判讀確認為元資訊後移除（非盲目刪）。常見漏點：模組描述的 `(N lines)` 行數標註、`（v3: ...）` 版號標註（dogfood 實證：外部 repo init 產出含 `(1951 lines)`）。此為 [instruction-writing](../instruction-writing/SKILL.md)「元資訊禁止行為」硬規則，產出時易忘，須機械掃描兜底。

## 判斷哪些模組需要 instruction 檔

**需要**：
- 包含 ≥3 個**實質**原始碼檔案的目錄（生成的 stub / 綁定 re-export 不算）
- 架構關鍵層（core、model、engine、config 等）
- 外部參考頻繁的區域（docs、examples）

**不需要**：
- 單檔案目錄（demo 給老闆入口，基於 library）
- 純配置目錄（只有 `__init__.py`）
- 第三方依賴目錄
- re-export shell 模組（star-import 綁定 + 生成的 stub）——hub 的對應表涵蓋即可

**Phase 1.5 加成**：`findings` 中的 X6 問題直接指出哪些模組缺少 instruction 檔。

## instruction 檔寫作品質

Signal/noise framework: [encoder-philosophy.md](../_common/encoder-philosophy.md)

產出時遵守 encoder-philosophy 的 High Signal / Low Noise 分類。額外約束：
- **功能性描述**：用「做什麼」描述模組，不用版號標記
- **生成物導向**：repo 內的生成物（`.pyi` stub、生成 docstrings）不重述內容、不建議手改——instruction 指向生成源與生成命令即可
- **機械盤點原則**：結構性列舉（目錄內容清單、模組清單、既有 instruction 檔位置）必須以機械輸出為依據（snapshot 的 `dir_inventory` / `instruction_files`，或直接 `ls` / `fd`）——subagent 報告是**理解素材**，不是**列舉來源**；寫下任何「目錄含 X、Y、Z」的段落前，對該目錄跑一次 `ls` 對齊

## 產出

1. 每個重要模組目錄新增 `AGENTS.md`（source，四家 harness 讀）+ `CLAUDE.md`（`@AGENTS.md` thin wrapper，Claude 讀）
2. 專案根目錄新增 `AGENTS.md`（source，harness-neutral）+ `CLAUDE.md`（`@AGENTS.md` wrapper + Claude 專屬段）——見 [instruction-writing.md](../../rules/instruction-writing.md) 雙檔模式
3. `.project-snapshot.json`（如果 Phase 1.5 有執行）
4. 最後列出所有新增的 instruction file 路徑

> **下一步**：產出後建議執行 `/instruction-sync` 驗證同步性與品質；人類 viewport scaffold → [blueprint-bootstrap](../blueprint-bootstrap/SKILL.md) 骨架（低中成本）。其 callstack 生成屬高成本獨立觸發（報價＋分批），不在連續流程建議內。

---

## 語音通知

遵循 [voice-notification skill](../voice-notification/SKILL.md)（隨機稱謂、sentinel 進度提醒、say 樣板見 skill）：

- **開始**（第一個動作前）：建進度提醒 sentinel + say 開始
  ```bash
  touch /tmp/.claude-voice-pending
  say -v Meijia -r 180 "開始產生 instruction 檔"
  ```
- **完成**（輸出結果後）：清 sentinel + 套 skill「任務完成」樣板 say（隨機稱謂，填「instruction 檔產生完成」）
  ```bash
  rm -f /tmp/.claude-voice-pending
  ```
