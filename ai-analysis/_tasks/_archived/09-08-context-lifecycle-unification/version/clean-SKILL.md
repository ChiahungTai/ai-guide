---
name: instruction-clean

description: "清理 Markdown 文檔中不必要的元資訊（版本號、日期、統計、Changelog）；--distill mode 蒸餾低 signal 內容（保守防護欄：換形為主，僅 clean 範圍元資訊直刪）"
when_to_use: "Remove unnecessary metadata (version numbers, dates, statistics, changelogs) from instruction files (根 AGENTS.md source + CLAUDE.md wrapper/模組 nav); add --distill to also compress derivable low-signal content into one-line summaries + source references. 雙檔模式見 instruction-writing.md。"
argument-hint: "/instruction-clean [目錄路徑|--recursive|--dry-run|--force] [--distill [--conservative|--moderate|--aggressive]]"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

# Instruction File Clean — 元資訊清理 + 蒸餾（雙 mode）

> **instruction file 雙檔模式**：操作範圍含根 `AGENTS.md`（source）+ `CLAUDE.md`（wrapper + 模組導航）——遞迴發現時兩者皆納入。見 [instruction-writing.md](../../rules/instruction-writing.md)。

兩個 mode，安全度遞減：

| Mode | 做什麼 | 風險 | 何時用 |
|------|--------|------|--------|
| **clean**（預設） | 機械移除元資訊（版本/日期/統計/changelog）+ 引用語法檢查 | 🟢 低——全是無爭議的噪音 | 常規 |
| **--distill** | 蒸餾低 signal 內容為「一句話 + 源碼引用」 | 🟡 中——壓縮判斷可能過頭，有防護欄（見下） | 文檔明確肥大時 |

Signal/noise framework: [encoder-philosophy.md](../_common/encoder-philosophy.md) — 讀取此檔案以理解 High Signal / Low Noise 分類標準。

## 適用文檔

- **Instruction files（AGENTS.md / CLAUDE.md）**：AI 協作指南，不需要人類導向的元資訊
- **說明文檔**：描述現有系統運作方式的技術文檔
- **不適用**：設計文檔（描述概念、提案、未來計畫）——歷史脈絡可能有其參考價值

---

## Mode A: clean（預設）

### 應該移除的元資訊

| 模式 | 範例 | 原因 |
|------|------|------|
| 更新日期 | `> **更新日期**: 2025-01-01` | AI 只需要當前規則 |
| 歷史變更 | `## 變更歷史` / `## Changelog` | 應放 CHANGELOG.md |
| 統計資訊 | `行數: 387`, `字數: 5234` | 對 AI 無意義 |
| 版本號 | `> **版本**: 2.0` | AI 不關心 v1→v2 |
| 生效日期 | `> **生效日期**: 2025-01-01` | 不影響規則內容 |

### 識別 pattern（冒號錨定）

掃描用**帶冒號錨定**的 pattern：`**版本**:`、`> **更新日期**:`、`> **生效日期**:`、`行數:`、`字數:`、`wc:`、`lines:`、`## 變更歷史`、`## Changelog`。**禁裸匹配** `wc`/`lines`——會誤命中合法 CLI 範例（`wc -l`）或 size 指引（`~100 lines`）。常見漏點：模組描述的 `(N lines)` 行數標註、`（v3: ...）` 版號標註。

### 可以保留

符號連結說明、專案概述、繼承關係——AI 理解結構所需。

### 引用語法正確性

依據 [instruction-writing.md](../../rules/instruction-writing.md)：

| 情境 | 正確語法 | 錯誤語法 |
|------|---------|---------|
| 每次對話都需要 + 內容精簡 | `@path`（自動展開，僅 CLAUDE.md） | `[text](path)` |
| 偶爾才需要 / 檔案偏長 | `[描述](path)`（按需讀取） | `@path`（浪費 context） |
| Skill 中的引用 | `[描述](path)` | `@path`（Skill 不支援 `@`） |

---

## Mode B: --distill（蒸餾，附防護欄）

> **設計立場**：蒸餾的已知失敗模式是「太過頭」——把 High Signal 的設計理由、失敗教訓一起壓掉，留下乾淨但無知的文檔。本 mode 的防護欄就是為此而設；寧可少壓，不要誤壓。

### 🔴 NEVER 清單（任何強度都禁觸碰）

即使 `--aggressive` 也**絕不**蒸餾以下內容——它們是從程式碼猜不到的知識本體：

- **失敗教訓**（含「真實案例」marker 的段落）
- **設計理由**（為什麼選 X 不選 Y）
- **不可妥協的約束 / 架構限制**
- **負空間指導**（不做什麼、禁止事項）
- **型別關係區別**（相似型別的用途差異）
- **跨模組慣例映射**（名稱推導不出語義的映射）

### Signal/Noise 分類

- ✅ **High Signal**（保留）：從程式碼猜不到的知識——設計理由、約束、非顯而易見的選擇、模組邊界、失敗教訓
- ❌ **Low Noise**（蒸餾標的）：從程式碼可直接推導——API 簽名、參數表、欄位列表、完整範例（>5 行）、過時範例、重複說明、通用知識
- ⚠️ **灰色地帶（預設保留）**：

| 內容類型 | 保留條件 | 蒸餾條件 |
|---------|---------|---------|
| 範例程式碼 | ≤ 5 行，展示關鍵用法 | > 5 行或過時、重複 |
| 檢查清單 | 行為約束、決策要點 | 顯而易見的項目 |
| 配置參數 | 影響行為的關鍵參數 | 很少修改的環境參數 |

### 資訊不滅原則（核心紀律）

蒸餾是**換形不是刪除**：Low Noise 內容壓縮為「一句話總結 + 源碼引用（`file.py:15-30`）」，讀者仍能循引用找回完整內容。唯一允許直接刪的：版本變更歷史、統計數字（clean 範圍）。

### 強度分級（預設最保守）

| 強度 | 行為 |
|------|------|
| **--conservative（預設）** | 只處理明確冗餘（重複說明、>5 行範例、可推導內容）；灰色地帶全保留 |
| --moderate | 灰色地帶依表判斷；需顯式指定 |
| --aggressive | 灰色地帶傾向蒸餾；NEVER 清單仍然禁觸；需顯式指定 + 逐條列出所有壓縮項 |

### 防護欄（強制執行順序）

1. **備份先行**：蒸餾前建立 `.backup`（還原：`mv file.md.backup file.md`）
2. **段落級對照預覽**：每個蒸餾項顯示「原文摘要 → 蒸餾後」對照，用戶確認才寫入（`--force` 跳過）
3. **縮減比門檻**：單檔縮減 >30% 時，必須逐條列出**每一個**被壓縮的項目（防止整段消失未被察覺）
4. **停止條件**：掃描 Low Noise = 0 項 → 不做（文檔已精簡，再壓就是壓 Signal）
5. **Decoder Test 把關**：蒸餾後回答四問（見下），任一題答不出 → 從 `.backup` 還原

---

## 共用：執行流程

1. **遞迴發現**：[recursive-discovery.md](../_common/recursive-discovery.md)（根 AGENTS.md + CLAUDE.md + 模組層）
2. **讀取並識別**：clean mode 掃元資訊 pattern；distill mode 另做三類分類
3. **報告先行**：列出發現（位置 + 原因）+ 清理/蒸餾預覽，詢問後執行（`--dry-run` 只報告；`--force` 跳過確認）
4. **執行**：Edit 移除 / 改寫；distill 先 `.backup`
5. **Decoder Test（dry run）**：基於清理後內容回答——① 模組核心職責？② 關鍵設計決策與理由？③ 不可妥協的約束？④ 模組邊界（不做什麼）？全部可答 = 通過；任一失敗 = 還原重評

遞迴輸出格式: [recursive-output.md](../_common/recursive-output.md)；遞迴處理約束: [recursive-constraints.md](../_common/recursive-constraints.md)

## 參數

| 參數 | 說明 |
|------|------|
| **無參數** | 處理當前目錄的 instruction 檔（clean mode） |
| **檔案/目錄路徑** | 處理指定對象 |
| **--recursive, -r** | 遞迴處理所有子目錄 |
| **--dry-run** | 預覽模式，不實際修改 |
| **--force** | 跳過確認直接執行 |
| **--distill** | 啟用蒸餾 mode（搭配下述強度旗標） |
| **--conservative / --moderate / --aggressive** | 蒸餾強度；預設 conservative |

## 執行約束

- **報告先行**：先報告發現，再詢問是否執行
- **絕不刪除規則和約束內容**（NEVER 清單）
- **明確標記**：每項移除/壓縮附原因
- **可還原**：clean 建議備份；distill 強制備份

---

> **清理哲學**: instruction 檔是模組知識的 Encoder。clean 移除對 AI 零資訊的元資訊；distill 把可推導內容換形為引用。目標不是越短越好，而是 signal/noise ratio——寧可少壓，不要誤壓。
