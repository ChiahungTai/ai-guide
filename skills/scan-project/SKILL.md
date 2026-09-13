---
name: scan-project
description: >
  Unified project knowledge scanner (on-demand). Scans Python imports (built-in AST), Rust Cargo
  workspaces (members + internal crate deps + PyO3 binding marker), mechanical directory inventory,
  instruction files (AGENTS.md preferred, CLAUDE.md legacy), and backlog/ cards. Produces dep_graph +
  rust_workspace + dir_inventory + instruction_files + findings + fingerprint. Nightly maintain no
  longer generates snapshots (structural graph freshness is code-reality's domain); run on demand
  for mechanical inventory / cross-validation findings.
when_to_use: >
  Run on demand — during init, when you need mechanical cross-validation
  findings, or when the dependency inventory may be stale. Nightly maintain
  no longer runs this.
argument-hint: "[--project-root PATH] [--output PATH]"
allowed-tools: Bash(uv run python *)
---

# /scan-project — 統一專案知識掃描器

掃描 Python import 依賴（內建 AST）、Rust Cargo workspace、機械目錄盤點、模組 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities 表格、backlog 卡（`backlog/tasks/` frontmatter），產出 **dep_graph + rust_workspace + dir_inventory + instruction_files + findings + fingerprint**。

Schema 定義：[unified-snapshot-schema.md](reference/unified-snapshot-schema.md)

---

## 核心設計

**scan_project.py 做機械性檢查，不產出完整 registry。LLM 需要細節時直接讀取檔案。**

產出：
1. **dep_graph** — Python import 關係（LLM 無法自行可靠計算）。`source` 標示來源：`builtin`（內建 AST 掃描，模組 = package root 第一層目錄）/ `none`（無 package root）
2. **rust_workspace** — Cargo workspace members、crate 間內部依賴、`has_python_bindings`（PyO3 綁定層標記——truth/shell 分離 repo 的關鍵訊號）；無 Rust workspace 時為 `null`
3. **dir_inventory** — 機械目錄盤點（深度 ≤3；檔名僅在 ≤60 時列出）——**結構性列舉的 ground truth**，LLM prose 摘要不可取代
4. **instruction_files** — 各目錄 instruction 檔位置 + 邊界/能力表有無
5. **findings** — 機械性交叉驗證問題（路徑、tag、重複等）
6. **fingerprint** — 輕量變化偵測（counts + hashes）

內部解析（instruction 檔（AGENTS.md 為主、CLAUDE.md legacy）、backlog 卡）僅用於計算 findings，**不在輸出中包含 registry**。

**LSP 與 dep_graph 的分工（正交，非競爭）**：

| 查詢類型 | 用誰 | 理由 |
|---------|------|------|
| 單點依賴（「X 用到 Y 嗎？」「誰呼叫 Z？」） | **LSP** findReferences / incomingCalls | live、無 snapshot 時效衰減 |
| 否定宣稱（X1：instruction 檔「Does NOT depend on」是否為真） | **dep_graph** edges 集合差集 | 證明「不存在」需窮舉邊，LSP 點查詢不擅長否定驗證 |
| 全域拓撲（fan-out、熱點、blast radius、遞迴閉包） | **dep_graph** | 一次看全圖；LSP 需 N 次點查詢重建 |
| code↔doc 一致性（X-cap-path / X6 等 findings） | **scan-project** | LSP 符號世界裡沒有「文檔宣稱什麼」這一側 —— **scan-project 真正不可替代的價值，非 dependency graph 本身** |

**原則**：單點查詢優先 LSP（dep_graph snapshot 可能 stale）；否定宣稱、全域拓撲、code↔doc 一致性用 dep_graph / scan-project。兩者在不同軸上互補。

---

## 執行

```bash
# 掃描當前專案
uv run python "${CLAUDE_SKILL_DIR:-$HOME/.agents/skills/scan-project}/scripts/scan_project.py" --project-root . --output .project-snapshot.json

# 輸出到 stdout（pipe 用）
uv run python "${CLAUDE_SKILL_DIR:-$HOME/.agents/skills/scan-project}/scripts/scan_project.py" --project-root /path/to/project
```

## Graceful Degradation

- **內建 AST 掃描**（模組 = package root 下第一層目錄；`source: builtin`）；連 package root 都沒有才為空（`source: none`）
- 沒有 Cargo workspace：`rust_workspace` 為 `null`
- 如果沒有 `backlog/` 目錄：backlog 卡相關 findings 不產出
- 輸出格式 schema_version: 6

## 產出

`.project-snapshot.json` 包含：

| Section | 來源 | 說明 |
|---------|------|------|
| `dep_graph.source` | — | `builtin` / `none` |
| `dep_graph.modules` | 內建掃描 | 模組依賴結構（file_count, internal_deps, fan_out 等） |
| `dep_graph.edges` | 內建掃描 | 模組間 import edges |
| `dep_graph.hotspots` | 內建掃描 | 高 fan-out imports |
| `rust_workspace` | Cargo.toml 解析 | workspace 成員 + crate 內部依賴 + `has_python_bindings` |
| `dir_inventory` | 檔案系統盤點 | 深度 ≤3 目錄清單（subdirs、檔名/副檔統計）——列舉 ground truth |
| `instruction_files` | instruction 檔掃描 | 各目錄 AGENTS.md/CLAUDE.md 位置 + 邊界/能力表有無 |
| `findings` | 機械性交叉檢查 | X-cap-path / X-ep-ready / X6 |
| `fingerprint` | 計數 + 雜湊 | capabilities_total, kanban_total, kanban_by_lane, hashes |

**不在輸出中的**：capabilities_registry、kanban_registry、claude_md_registry、cross_validation（v3 舊格式）。

## 與其他命令整合

維護流程（`/daily-maintain`）已不產出 snapshot（快照鏈退役，結構新鮮度歸 code-reality——見 [maintain](../maintain/SKILL.md) Phase 1）；本 skill 為 on-demand 工具。

| 命令 | 如何使用本 skill |
|------|-----------------|
| `/instruction-sync` | 可選：載入 dep_graph 用於 import 驗證 |
| `/instruction-init` | 可選：執行本 skill，用 findings 報告缺口 |
| `/doc-health` | 步驟 1 消費 findings，LLM 直接讀 instruction 檔（AGENTS.md/CLAUDE.md）+ backlog 卡（`backlog/`）做品質檢查 |

## 交叉驗證（機械性）

| Check | 說明 | 嚴重度 |
|-------|------|--------|
| X-cap-path | Capabilities 入口路徑不存在（檢查 project root / package root / instruction 檔目錄（AGENTS.md/CLAUDE.md）） | important |
| X-ep-ready | To Do/In Progress 卡片引用的 EP 檔案不存在 | important |
| X6 | dep-graph 有模組（≥3 files）但無 instruction 檔（AGENTS.md/CLAUDE.md） | important |

語義性驗證（X1 dep-graph 矛盾、X8 幽靈 Capabilities 引用）由 `/instruction-sync` 和 `/doc-health` 的 LLM 判斷完成。
