# Unified Snapshot Schema（v6）

> JSON 合約定義：scan_project.py 產出格式，供 daily-maintain / doc-health / sync 消費。

---

## 版本策略

- `schema_version: 1` — 舊格式（scan_imports.py 產出，只含 modules/edges/hotspots）
- `schema_version: 2` — USE-CASES.md 格式（含 uc_registry/uc_edges）
- `schema_version: 3` — 三層文件格式（含 capabilities_registry/kanban_registry/claude_md_registry/cross_validation）
- `schema_version: 5` — 精簡格式（dep_graph/findings/fingerprint，不含 registry）
- `schema_version: 6` — 無工具依賴 + 多語言（dep_graph.source 標示來源、內建 import 掃描 fallback、rust_workspace、dir_inventory、instruction_files）
- **向前不相容**：v5 移除所有 registry，改為 findings + fingerprint；v6 為新增欄位（v5 消費端讀 v6 不崩，但拿不到新區段）

### v3 → v5+ 遷移

消費端遇到 `schema_version < 5` 的 snapshot 時：
1. **刪除舊 snapshot**：`rm .project-snapshot.json`
2. **重新掃描**：執行 `/scan-project` 產出最新（v6）snapshot
3. 無需手動遷移——scan_project.py 只產出最新版（v6），不支援向下相容寫入

舊欄位對應：

| v3 欄位 | v5 對應 | 說明 |
|---------|---------|------|
| `capabilities_registry` | —（移除） | LLM 直接讀 instruction 檔（AGENTS.md/CLAUDE.md） |
| `kanban_registry` | —（移除） | LLM 直接讀 backlog 卡（`backlog/`——`backlog task list --json`） |
| `claude_md_registry` | —（移除） | LLM 直接讀 instruction 檔（AGENTS.md/CLAUDE.md） |
| `cross_validation` | `findings` | 重新命名，更新 check IDs |
| `modules/edges/hotspots` | `dep_graph.modules/edges/hotspots` | 移至 dep_graph 子物件 |
| (無) | `fingerprint` | 新增：變化偵測用 counts + hashes |

---

## 完整結構

```json
{
  "project": "my_package",
  "scan_timestamp": "2026-06-09T10:30:00+08:00",
  "schema_version": 6,

  "dep_graph": {
    "source": "builtin",
    "modules": {
      "mod_name": {
        "file_count": 88,
        "internal_deps": { "target_mod": ["import_path1"] },
        "external_deps": { "pandas": ["pandas.DataFrame"] },
        "imported_by": ["consumer_mod1"],
        "fan_out": 17
      }
    },
    "edges": [
      { "source": "mod_a", "target": "mod_b", "weight": 3, "imports": ["path1", "path2"] }
    ],
    "hotspots": [
      { "import_path": "my_package.common.enums", "imported_by": ["data", "features"], "fan_out": 5 }
    ]
  },

  "rust_workspace": {
    "root": ".",
    "crates": [
      {
        "name": "nautilus-model",
        "dir": "crates/model",
        "internal_deps": ["nautilus-core"],
        "has_python_bindings": true
      }
    ]
  },

  "dir_inventory": {
    "max_depth": 3,
    "truncated": false,
    "dirs": [
      {
        "path": "docs/concepts",
        "depth": 2,
        "subdirs": ["backtesting", "orders"],
        "files_total": 29,
        "file_exts": { "md": 29 },
        "files": ["architecture.md", "overview.md"]
      }
    ]
  },

  "instruction_files": [
    {
      "path": "crates/model/AGENTS.md",
      "module": "model",
      "has_module_boundaries": true,
      "has_capabilities_table": false
    }
  ],

  "findings": [
    {
      "check_id": "X-cap-path",
      "severity": "important",
      "detail": "Capabilities entry path 'runner.py' does not exist (in my_package/data/AGENTS.md)",
      "source_file": "my_package/data/AGENTS.md"
    },
    {
      "check_id": "X-ep-ready",
      "severity": "important",
      "detail": "Card '重構 Pipeline' in To Do references EP 'ep-refactor-pipeline.md' but file not found",
      "kanban_source": "backlog/tasks/task-43 - 重構Pipeline.md"
    },
    {
      "check_id": "X6",
      "severity": "important",
      "detail": "Module 'services' has 12 files but no instruction file (AGENTS.md/CLAUDE.md)",
      "module": "services"
    }
  ],

  "fingerprint": {
    "capabilities_total": 151,
    "capabilities_hash": "c647a67bf05a",
    "kanban_total": 66,
    "kanban_by_lane": { "To Do": 63, "In Progress": 2, "Done": 1 },
    "kanban_hash": "0b84e82352fd",
    "instruction_file_total": 71
  }
}
```

---

## 欄位說明

### dep_graph

| 欄位 | 型別 | 說明 |
|------|------|------|
| `source` | string | `builtin`（內建 AST 掃描）/ `none` |
| `modules` | dict | 模組依賴結構（key = module name；builtin 模組 = package root 第一層目錄，另含 `(root)`） |
| `edges` | array | 模組間 import edges |
| `hotspots` | array | 高 fan-out imports |

dep_graph 由內建 AST 掃描產出（外部 scan_imports rich face 已退役）；連 package root 都沒有時三個欄位為空（`{}`、`[]`、`[]`）。

### rust_workspace

Cargo workspace 的機械解析（無 Rust 時為 `null`）。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `root` | string | workspace **目錄**相對路徑（非 manifest 檔路徑；workspace 在 repo 根時為 `"."`） |
| `crates[].name` / `dir` | string | crate 名與目錄 |
| `crates[].internal_deps` | array | 只含指向其他 workspace 成員的依賴（分層圖的邊） |
| `crates[].has_python_bindings` | bool | 有無 `src/python/`（PyO3 綁定層——truth/shell 分離訊號） |

### dir_inventory

機械目錄盤點（深度 ≤3、目錄數上限 800、`truncated` 標記截斷）——結構性列舉的 ground truth。`files`（檔名）僅在直接檔案 ≤60 時列出，否則只有 `files_total`。

### instruction_files

各目錄 instruction 檔（AGENTS.md 優先、CLAUDE.md legacy）的位置與 `has_module_boundaries` / `has_capabilities_table` 標記——init/sync 流程判斷「哪些目錄已有檔」的機械依據。

### findings

機械性交叉驗證問題。LLM 不需要重複這些檢查，直接消費即可。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `check_id` | string | 檢查代碼 |
| `severity` | string | critical / important |
| `detail` | string | 人類可讀的問題描述 |
| 其餘欄位 | any | 依 check_id 而異 |

### fingerprint

輕量變化偵測。用於 daily-maintain Phase 1 的 diff。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `capabilities_total` | int | 所有 instruction 檔（AGENTS.md 為主，CLAUDE.md legacy）Capabilities ✅ 條目總數 |
| `capabilities_hash` | string | sorted capability:module:status 的 MD5 前 12 碼 |
| `kanban_total` | int | backlog 任務總數（欄位名歷史保留——源已遷 `backlog/tasks/`） |
| `kanban_by_lane` | dict | 各 status 任務數（欄位名歷史保留） |
| `kanban_hash` | string | sorted id:title:lane 的 MD5 前 12 碼 |
| `instruction_file_total` | int | instruction 檔總數（AGENTS.md + legacy CLAUDE.md） |

---

## 機械性交叉驗證清單

| check_id | 檢查邏輯 | severity |
|----------|---------|----------|
| `X-cap-path` | Capabilities 入口路徑不存在（檢查 project root / package root / instruction 檔目錄（AGENTS.md/CLAUDE.md）三個候選位置） | important |
| `X-ep-ready` | To Do/In Progress 卡片引用的 EP 檔案在任務家目錄找不到 | important |
| `X6` | dep-graph modules 中有模組（≥3 files）但該模組目錄下無 instruction 檔（AGENTS.md/CLAUDE.md）；模組目錄在 project root 與 package root 兩處都檢查 | important |

**語義性驗證（由 LLM 判斷，不在 findings 中）**：
- X1：dep-graph 矛盾（instruction 檔 "Does NOT depend on" vs 實際 import edge）
- X8：幽靈 Capabilities 引用（SYSTEM-MAP.md 提到的能力不在 Capabilities 表格中）
