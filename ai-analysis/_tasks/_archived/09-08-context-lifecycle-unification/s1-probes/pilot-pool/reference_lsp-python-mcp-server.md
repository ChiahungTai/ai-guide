---
name: lsp-python-mcp-server
description: 【已停擺 08-28：型別面由 CR bridge 接班】lsp_mcp v2 歷史記錄——payload 路由鏈＋多語言 backend（pyright/RA）；ZCode 單一 entry
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_0afead70-a31b-4eda-8873-484fe11d1ca6
---

lsp-python＝user 自建 LSP MCP server，live 在 mosaic_alpha repo（`tools/lsp_mcp/`），launchd `com.mosaic.lsp-mcp` 常駐 `127.0.0.1:8000`。**v2（2026-08-25 commit `8badf25d`，14 檔）已上線**：launchd 直跑 checkout 碼，重啟即載新版。

**⚠️ 現況（2026-08-28 末第三次更新——P3 ✅ 全域退役完畢）**：**:8000 無 listener（死）**；**三 worktree 的 in-repo lsp_mcp 已全數消失**——offline_backtesting 退役批次（`d0345603`＋`0914dedd`）經 user 相互 rebase 傳播至 main＋trading_lab（hub survey 實證 tracked=0 ×3）＝**server 本體不存在於任何 worktree，「真空期急用 make lsp-http 一鍵回」路徑已消失**；**ZCode user-level lsp-python entry 已拔**（hub 執行，config 備份 `.bak-p3`）；**三處 `.mcp.json` dead entries 已清**（`3040216b`〔main＋v2 同 parent 同變更同秒＝同一 git 物件〕＋`b728b641`〔trading_lab 保留 code-reality 條目〕）＝P3 收案、lsp-python 在本機零殘留。**接班完成**：型別面由 CR bridge 雙語言落地（P1＋P2，NT/mosaic 雙實證）。**共享 server 形態確定不復活**：LSP 已內部化為 bridge spawn 的 backend 子進程。本文其餘＝歷史設計記錄（v2 路由鏈／多語言 pool／L4 陷阱對 bridge 設計仍有參考價值）。

**v2 架構（payload 路由＋多語言）**：
- workspace 路由鏈（server 端 `_resolve_ws_id`）：**workspace 參數（resolve canonicalize）> file_path 白名單最長前綴推斷（`pool.infer_workspace`）> `x-workspace-id` header（Claude 端 headersHelper 相容層）> --workspace default > loud error 帶修正指引**。file_path 推斷優先 header 是 payload-first 合理語意（LSP 查詢本該在檔案所屬 ws）。
- 多語言：WorkspacePool client key=`f"{ws}::{lang}"`、`acquire(ws, language)`；config `~/.mosaic/lsp-mcp-config.json` 增 `language_servers` 段（**既有語言 bin 覆寫走 config；新語言需 code 三張表**：`LANGUAGE_SUFFIXES`/`LANGUAGE_SERVER_ARGS`（lsp_client.py）＋`_SUFFIX_LANGUAGES`（server.py））；LSPClient languageId/diagnostics 副檔名過濾（.py/.rs）/probe per-language（rust 跳過、`LSP_PROBE_SYMBOL` env 僅作用 python）。
- **L4 陷阱（釘住）**：rust-analyzer 不收 `--stdio` 旗標（"unexpected flag" 立即退出）——`LANGUAGE_SERVER_ARGS = {"python": ["--stdio"], "rust": []}` per-language；未知語言 LSPClient 構造期 loud ValueError。
- goToImplementation 僅 rust 放行（rust-analyzer 有 implementationProvider；pyright 無，python 攔截回誠實訊息）＋新 `tools.implementation()`。
- rust cross-file 查詢（goToDefinition/goToImplementation）首次背景索引期可能回空——documentSymbol 是 file-local 不受影響。

**四端接線（v2 後）**：**ZCode＝user-level `~/.zcode/cli/config.json` http entry（無 header）——三份 worktree `.zcode/config.json` 已於 2026-08-25 刪除**（offline_backtesting 那份含舊 crg stdio 一併除役）；Claude(mosaic)＝專案層 `.mcp.json` headersHelper（路由鏈第三層相容）；NT 透過 config repo_roots（`~/.mosaic/lsp-mcp-config.json`：mosaic＋nautilus_trader＋rust=rust-analyzer）。**ZCode 無原生 LSP**（native 工具詞彙表零 LSP operation，本 server 是唯一解）。

**品質狀態**：165 tests passed＋mypy 8 files 乾淨＋ruff 綠；dual-context 審查 18 findings 修正（含 R11 預先存在 evict lock-pop race 前移、AGENTS.md 設定章節 intent drift 改寫）；followup 19/19 verified。**新 session 驗證閉環（2026-08-25，依 handoff capsule V1-V6 實測全過、零 bug）**：V4 file_path 推斷免 workspace 直查 ✓、V5 workspaceSymbol loud error→補 workspace 重試成功 ✓、V6 NT `.rs` 經 rust-analyzer 回 100+ 符號 ✓——capsule 存 `.at-contexts/handoff-20260825-0645.md`（handoff→新 session 驗證→回報機制本身驗證成功）。歷史形態（per-worktree .zcode static header）的演進敘事與「路 A 回退」始末見 [[agents-registry-split-design]]（MCP 接線段）；CRG 姊妹作（同日共享 server 化）詳見 [[cr-live-faces-roadmap]]（CRG server 段）。

**repo 覆蓋需求（user 2026-08-25：「lsp_mcp 應該是各個 repo 都要可以」）**：機制已支持（repo_roots 白名單＋file_path 最長前綴推斷）；目前 `~/.mosaic/lsp-mcp-config.json` roots 僅 `mosaic_alpha`＋`nautilus_trader`——**ai-rules 等其他 repo 未列入**，各 repo 通＝每 repo 加一行 config；pyright 走程式碼內建 `DEFAULT_LANGUAGE_SERVERS`（config 只列 rust 是常態非缺漏）；未知 root loud error 屬設計。
