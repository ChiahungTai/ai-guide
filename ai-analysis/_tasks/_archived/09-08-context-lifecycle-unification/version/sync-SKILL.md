---
name: instruction-sync

description: "檢查 Markdown 文檔與程式碼同步性及內部品質"
when_to_use: "Check instruction files (根 AGENTS.md source + CLAUDE.md wrapper/模組 nav) synchronization with code: navigation validity, code consistency, signal/noise ratio. Supports --recursive, --changed-since, --quality. 雙檔模式見 instruction-writing.md。"
argument-hint: "/instruction-sync [目錄路徑] [--recursive] — 預設檢查當前目錄，可指定目錄或 .md 檔案"
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
---

# /instruction-sync — 程式碼同步與品質檢查

> **instruction file 雙檔模式**：同步對象含根 `AGENTS.md`（source）+ `CLAUDE.md`（wrapper + 模組導航）——遞迴發現時兩者皆納入。見 [instruction-writing.md](../../rules/instruction-writing.md)。

驗證文檔與實際程式碼的一致性、涵蓋性，以及文檔內部品質。

Signal/noise framework: [encoder-philosophy.md](../_common/encoder-philosophy.md)

## 適用文檔

- **instruction 檔**（AGENTS.md source + CLAUDE.md wrapper / 模組導航）：AI 協作指南，必須與程式碼同步
- **說明文檔**：描述現有系統運作的技術文檔，必須與實際程式碼一致
- **不適用**：設計文檔（描述概念、提案、未來計畫）— 沒有對應的現有程式碼可驗證

---

## 價值金字塔

instruction 檔的價值層級：**導航**（LLM 找到程式碼）→ **理解**（LLM 知道為什麼）→ **品質**（LLM 高效消費）。導航層做不好，其他檢查都沒意義。

---

## 執行分層

| 層級 | 包含角度 | 參數 |
|------|---------|------|
| **核心層** | 導航有效性 + 程式碼一致性 + Signal/Noise | 預設 |
| **品質層** | + 內部品質 + 元資訊 + 引用語法 | `--quality` |
| **完整層** | + 涵蓋性 + 連鎖影響 + 蒸餾評估 | `--all` |

### 12 個檢查角度

| # | 角度 | 層級 | 一行摘要 |
|---|------|------|---------|
| 1 | 導航有效性 | 核心 | instruction 檔是否讓 AI 從概念定位到程式碼（最重要） |
| 2 | 程式碼一致性 | 核心 | 檔案路徑、簽名、行為描述是否與實際程式碼一致 |
| 3 | 涵蓋性 | 完整 | 核心模組和公開 API 是否被文檔記錄 |
| 4 | 元資訊 | 品質 | 是否存在版本號、日期等對 AI 無意義的內容 |
| 5 | 蒸餾評估 | 完整 | Signal/Noise ratio 是否健康 |
| 6 | 內部品質 | 品質 | 自洽、無矛盾、結構合理、內容精準 |
| 7 | Signal/Noise Ratio | 核心 | High Signal 佔比是否足夠 |
| 8 | 引用語法 | 品質 | `@` vs `[描述](path)` 選擇是否正確 |
| 9 | 連鎖影響 | 完整 | 程式碼變更是否影響消費端文檔 |
| 10 | dep-graph 矛盾 | 完整 | instruction 檔 "Does NOT depend on" 與 dep-graph import edge 矛盾 |
| 11 | 模組覆蓋缺口 | 完整 | dep-graph 有模組但無 instruction 檔 |
| 12 | 通用性 | 完整 | 泛用 rules/commands 是否含真實專案符號（應 `<placeholder>`） |

完整定義和判斷標準：[sync-check-angles.md](../_common/sync-check-angles.md)

---

## 內容變更評估原則

### 新增

**應該新增**（High Signal）：設計理由、架構約束、非顯而易見的選擇、模組邊界、失敗教訓

**不應該新增**（Low Noise）：API 簽名、參數表、欄位列表、完整範例（>5 行）

### 刪除

**應該刪除**：API 簽名、欄位列表、版本號/日期、歷史章節、過時範例、重複說明

**謹慎評估**（灰色地帶，預設保留）：範例程式碼 ≤ 5 行、行為約束檢查清單

### 修改

簡潔描述替代：詳細步驟 → 一句話總結 + 源碼引用；過多參數列表 → 關鍵參數 + 配置檔引用

---

## 執行流程

| 步驟 | 名稱 | 觸發 |
|------|------|------|
| 0.5 | Snapshot 載入 | `.project-snapshot.json` 存在時 |
| 1 | 遞歸發現 instruction files（根 AGENTS.md + CLAUDE.md） | 預設 |
| 1.5 | 依賴鏈擴展 | 有 git diff 變更 / --changed-since |
| 1.6 | Sub-doc 擴展 | instruction 檔引用了 .md 子文件 |
| 2 | 掃描程式碼結構 | 預設 |
| 3 | 提取文檔引用 | 預設 |
| 4 | 驗證一致性 | 預設 |
| 5-6 | 涵蓋性檢查 | --all |
| 7 | 清理元資訊 | --clean |
| 8 | 蒸餾 | --all |
| 9 | 內部品質 | --quality |
| 10 | 導航有效性 | 預設（最重要） |
| 10.5 | 交叉驗證（vs snapshot） | `.project-snapshot.json` 存在時 |

步驟詳細實作：[sync-implementation-steps.md](../_common/sync-implementation-steps.md)
遞歸發現邏輯: [recursive-discovery.md](../_common/recursive-discovery.md)
輸出格式模板：[sync-output-templates.md](../_common/sync-output-templates.md)
遞歸輸出格式: [recursive-output.md](../_common/recursive-output.md)

---

## 參數

| 參數 | 說明 |
|------|------|
| **無參數** | 檢查當前目錄的 instruction 檔（AGENTS.md 為主，legacy CLAUDE.md） |
| **檔案/目錄路徑** | 檢查指定檔案或目錄 |
| **--recursive, -r** | 遞歸檢查所有子目錄 |
| **--changed-since** | 增量模式：只檢查 git 變更涉及的檔案 |
| **--quality** | 品質層（加入內部品質 + 引用語法） |
| **--all, -a** | 完整層（12 個角度 + 清理 + 蒸餾） |
| **--dry-run** | 預覽模式 |
| **--verbose** | 顯示詳細過程 |

---

## 執行約束

- **實際驗證**：必須開啟程式碼檔案確認，不猜測
- **引用來源**：報告問題時標註具體位置和證據（檔案:行號）
- **報告先行**：先報告發現，再詢問是否執行清理或蒸餾
- **低風險自動修正**：以下問題修正成本極低且無歧義，發現時直接修正不詢問：路徑引用指向已更名/遷移的檔案（且能明確對應到正確檔案）。只有涉及模糊匹配（多個候選）或語意變更（描述文字要改）才需要確認

遞歸處理約束: [recursive-constraints.md](../_common/recursive-constraints.md)

---

> **同步哲學**: instruction 檔是活文檔，必須與程式碼同步演進。當 sync 發現 ⚠️ ≥ 3 個時，建議執行 `/instruction-sync {module} --all` 完整 12 角度深度驗證。

> **工作流**: `/instruction-clean [--distill]` → `/instruction-sync`
