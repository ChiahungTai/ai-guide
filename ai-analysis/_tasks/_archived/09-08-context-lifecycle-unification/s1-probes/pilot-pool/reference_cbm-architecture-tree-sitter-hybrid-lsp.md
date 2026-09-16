---
name: reference_cbm-architecture-tree-sitter-hybrid-lsp
description: CBM 索引架構——tree-sitter 162 grammars＋手寫 C type-resolvers（非 LSP/SCIP）；zero-edge；MCP 已裝 ZCode
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_b3591376-6323-4b4d-a172-744a5f37afa0
---

codebase-memory-mcp（DeusData，~/Github/codebase-memory-mcp，純 C）多語言索引架構（2026-08-30 調查）：

- **兩層**：① tree-sitter syntactic pass——162 個 vendored grammars 編進 binary（`internal/cbm/grammar_*.c`），零外部依賴，每檔都跑（defs/calls/imports）；②「Hybrid LSP」層——**名字誤導：不 spawn 任何 language server、也不是 SCIP**，是手寫 C 實作的 per-language type-resolution（`internal/cbm/lsp/`，10 語言：py/ts/php/c#/go/c/c++/java/kotlin/rust/perl），跑在 tree-sitter AST＋import graph＋cross-file definition registry（type_registry.c）上，把 CALLS 精煉成 RESOLVED_CALLS。其餘 152 語言 fallback textual resolution。
- **C resolver**：`lsp/c_lsp.c` 6,125 行＋macro_table＋preprocessor.cpp＋pipeline `pass_compile_commands.c`——macros/typedef chains/header-vs-source linking；**compile_commands.json 是選用增強**（有就解析 include paths/defines、沒有就 heuristic）→ 繞過 scip-clang 的硬前置。
- **Go resolver**：`lsp/go_lsp.c` 3,448 行——per-package cross-file registry/generics/embedded structs/interface satisfaction。
- **精度紀律 zero-edge guarantee**：unresolved receiver 寧可不產邊、不產錯邊。自評 benchmark（64 repo）：C＝Excellent（≥90%）、Go＝Good（75-89%）。
- **選近似＋compile_commands 選用的必然性（08-30 續論）**：零設定「下載即用」產品不能要求消費者 repo 先建置成功——scip-clang 的建置耦合硬前置對通用產品不可行。CBM 路線是產品約束下的唯一解，非工程能力妥協（user 點破建置耦合後定案；對照組：cr 是自用工具、repo 本來就建得起來，但 freshness 模型仍被 C 的 compile 級 re-index 打破）。
- **MCP 面已裝在 ZCode harness**：`mcp__codebase-memory-mcp__*`（get_architecture/search_graph/trace_path/detect_changes 等）——C+Go repo 的 coarse structural 查詢可直接消費，不需 cr 擴語言。

**引擎生態事實（同日澄清，user 問「pyrefly 支援 C？」）**：pyrefly 只支援 Python——Meta 的 Python type checker（Rust 寫但**只分析** Python，官方 repo 明載），不涵蓋 C/Go。SCIP 級 symbol resolution 每語言需自己的語言引擎（cr 雙腿＝pyrefly〔Python〕＋rust-analyzer〔Rust〕正是此體現）；tree-sitter 是唯一一套多語言但 parse-only 無 resolution。

對 cr C+Go 決策的意義與分層消費建議：[[cr-live-faces-roadmap]]（語言面＋拆軸段）；工具定位定論（evidence vs map machine）：[[reference_cr-vs-cbm-positioning]]。
