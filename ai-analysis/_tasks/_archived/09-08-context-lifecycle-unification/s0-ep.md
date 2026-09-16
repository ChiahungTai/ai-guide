# S0 子 EP：前置研究與 probe（AIR-45 context 統一生命週期機制）

> **ep_type**: implementation（docs/probe mode——產物為報告與樣本，無 production code；無 TDD）
> **parent**: ai-analysis/_tasks/_archived/09-08-context-lifecycle-unification/ep.md（master blueprint，S0 段）
> baseline: 7566bab

## Context

Master EP 的 S0 段：為統一 context 機制設計補齊六項事實。六項彼此獨立，可任意順序；每項產出寫進本任務家 `s0-report.md`（**增量 append——每完成一項就寫，不要最後一次寫**）。

已知事實（直接用，不重驗）：muse user-rules context block 硬上限 65,536B（官方名 subagent delegation startup context limit）、user-first 串接 project 層共享預算、檔 79,287B 時 produced 92,940B（+13,653≈ai-rules 專案層 12,550B＋~1.1KB framing）；ZCode 純 markdown＋rg 制（無 sqlite backing 的 memory）；memory 池 136 條。

## P1：ZCode 召回機制鑑識（致命假設先驗——最重要）

**問題**：ZCode 對 user message 是否有 desc-matching 的記憶召回注入（system-reminder 形態），還是只有靜態索引預載？這決定 master EP 觸發面設計的投資報酬率。

**方法（forensics，禁開新 ZCode session）**：
1. `~/.zcode/cli/db/db.sqlite`（SQLite；表：session（id/title/time_archived）、message（role/modelID）、part（正文））。先 `python3 -c "import sqlite3;..."` 或寫 `.py` 進本任務家 `s0-probes/` 查 schema（`.schema` 等值：`SELECT sql FROM sqlite_master`）
2. 撈歷史 sessions 的 parts 中含 `system-reminder` 且內容含 memory 條目特徵（如 `memory/`、`MEMORY.md`、`[[` wiki 連結形態、條目 frontmatter 痕跡）的事件——判別：**動態召回注入**（內容=特定條目 body/desc 片段、時點跟隨 user message）vs **靜態索引**（內容=MEMORY.md 投影、時點=session 開頭）
3. 統計：動態召回事件數、出現 session 數、注入時機（user message 後多久/第幾輪）
4. 若 db 找不到 system-reminder 形態 → 擴大：parts 含 recalled/reminders 關鍵詞掃描

**產出**：verdict（有動態召回／僅靜態索引／證據不足）＋evidence row 樣本（session id＋part 摘錄）＋對 master EP 的意義一段。

## P2：OpenCode AGENTS.md 上限驗證

**方法**：①`ref-docs/harness/opencode/` 鏡像 rg（AGENTS.md 載入、limit/truncate/size 條款）；②`which opencode`——CLI 在場才做 live probe（產生小於/大於疑似上限的暫存 instruction 檔測截斷），不在場或失敗 → 標「未驗證（CLI 缺場）」。**產出**：verdict＋文檔引用 file:line。

## P3：muse 於 mosaic 工作區的 lane 行為（forensics only）

**方法（禁跑任何 muse 命令——訂閱額度與進行中 session 共享）**：
1. 掃 `~/.local/share/muse/sessions/2026/09/{07,08}/*/session.jsonl`：抽 `payload_type=runtime.session` → `payload.event`，`kind=context_block_diagnostic` 且 `block_id=rules_file` 的 `text_bytes`
2. 對照工作區：session 內 `session.workspace_branch.observed` 事件或 tool output 提到的路徑判定 workspace（ai-rules vs mosaic vs 其他）
3. 目標：mosaic 工作區（project 42,740B）的 rules_file text_bytes 實測值——驗證「任何 user floor 都裝不下單 64KiB lane」假設
4. **順帶解謎**：09/07 有 sessions rules_file=23,583B——無任何已知專案 AGENTS.md 對得上（ai-rules 12,550/plugin-cc 7,416/code-reality 18,462/mosaic root 42,740）。查明這些 session 的 workspace 與 23,583 的來源
5. 大檔（>5MB）禁全讀——用 python 逐行過濾（script 進 `s0-probes/`）

**產出**：mosaic 場景實測值＋23,583 之謎解＋lane 模型修正（若與已知不符）。

## P4：mosaic root AGENTS.md 組成分析

**方法**：Read `~/Github/mosaic_alpha/AGENTS.md`（42,740B；**read-only——禁改任何 mosaic 檔案**）。逐段分類到三層：
- **必中集**（每次 session 都要：build/test 命令、全域慣例、風控級約束）
- **下沉目錄層**（module-specific——對照既有 51 個目錄 AGENTS.md 是否已有承載、建議搬去哪個目錄）
- **走觸發層**（on-demand 方法論/深層參考——master EP S2 條目化後走 routing）

**產出**：組成表（段落×行數×分類×去向建議）＋三層 bytes 統計＋重分配草案（S3 消費）。

## P5：desc 用語樣本 10 條（情境句領頭——文法校準材料）

**方法**：memory 池 `~/.zcode/cli/memories/projects/ai-rules-01610fbb20315a8b/memory/`（**禁改池內任何檔案**）。挑 10 條高頻 feedback_*/reference_*（優先：commit/deploy/dispatch/review/驗證類主題）。每條產出 before/after：
- after 形態：**情境條件句領頭**（「當你要〈任務動詞〉…時」開頭）＋核心事實一句；觸發詞涵蓋 session 當下會想的詞（zh+EN 混想——如 commit/確認/consent 都留）；**≤100 chars**（PreToolUse hook 上限）
- 附一行：舊 desc 的觸發弱點（哪個詞彙錯位）

**產出**：10 條 before/after 表＋「desc 文法規則」草案（3-5 行，S1 lint 候選）。user 校準後才批次套用——本 EP 只出樣本。

## P6：codex knob runtime 認證（best-effort，一次為限）

**方法**：`~/.codex/config.toml` 已有 `project_doc_max_bytes = 102400`（TOML 解析過）。live probe 一次：`codex exec`（在 /Users/ctai/Github/ai-rules 下）問「逐字引用你載入的全域指引（~/.codex/AGENTS.md）的最後一行」——預期含 `<!-- bundle-end -->` sentinel 即 knob 生效（32KiB 預設下尾端看不到）。CLI 缺場/失敗/逾時 → 標「deferred——主 session 執行」。**只試一次，禁重試**（外部額度）。

## 驗證策略（docs/probe mode）

- 每項 verdict 附機械證據（命令＋輸出節錄或 file:line）；找不到的明說「未驗證」，禁腦補
- 產出單一檔 `s0-report.md`（本任務家）——P1-P6 各一節＋頂部結論表（六項 verdict 一覽）
- 完成回報：report 路徑＋六項 verdict 各一行＋未驗證項清單

## 紅線

- read-only：`~/Github/mosaic_alpha`、memory 池、`~/.codex/`、`~/.config/muse/`、`~/.local/share/muse/sessions/`
- 禁 git commit/push、禁動 backlog 卡、禁跑 muse 命令（額度共享）、codex 只試一次
- 工具：rg/Read/fd；SQLite 探測寫 `.py` 進任務家 `s0-probes/` 跑（repo 有 uv：`uv run python <file>`；python -c 禁換行+註解）
- 中間發現即時 append s0-report.md（防中途死亡失憶）
