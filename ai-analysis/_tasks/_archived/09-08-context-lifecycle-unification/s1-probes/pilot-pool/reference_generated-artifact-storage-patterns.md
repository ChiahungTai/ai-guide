---
name: reference_generated-artifact-storage-patterns
description: 生成物（code index/cache/db）存放三形態分類與工具實例——repo-local cache／中央
  per-project／兩層分離（Serena 與 CR 決策同構）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

工具/plugin 的生成物（code index、cache、db）存放三形態（2026-08-28 網查分類，回答「一般 plugin 怎樣處理這種事」）：

1. **repo-local cache**：生成物進 repo 點目錄＋gitignore——rust-analyzer（`target/`）、`node_modules/.cache`（webpack/babel/eslint cache）、XDG-ish `.cache/` 慣例。優點＝隨 repo/clone/CI 走、跨編輯器可分享；缺點＝污染 repo（需 ignore 紀律）。
2. **中央 per-project**（path-hash keyed、不進 repo）：VS Code `workspaceStorage`（Copilot 本地索引、Intelephense 住此）。**已知痛點**：bloat 到 10-15GB、無 per-workspace purge API、對使用者隱形、不隨 clone/CI 走。
3. **兩層分離**（repo 事實 repo 放＋生產材料中央放）：**Serena MCP＝`.serena/`（per-project caches/memories，project root）＋`~/.serena/`（global config/project registry）——與 code-reality 的 `.code-reality/graph.db`＋`~/.mosaic/code-reality/`（cache slot/sidecar/golden）同構**＝最近同類 MCP 先例。

code-reality 的取捨（repo 自足＋worktree 隔離 > 磁碟與 gitignore 成本）＝形態③，非異類決策；中央派的 bloat/不可 purge 痛點正是避開項。重議觸發＝worktree 數量或體積痛（詳 [[cr-live-faces-roadmap]]）。

**形態①變體——渲染產物 git 分工（2026-08-31 archify 案例）**：生成「理解型 artifact」（互動圖）時拆 source/產物兩層 git 政策——**小而可再生的 source 進 git（JSON IR ~4KB）、肥而近重複的渲染產物不進**（每顆 HTML ~720KB 內嵌整套 viewer runtime、真內容 ~5KB，175:1；**確定性編譯實證：刪 HTML 後一命令再生 sha256 逐位元組相同**——可再生主張有機械證據才成立）。配套：生成物住**專屬目錄、且可放 repo root**（終案 `arch-report/<主題>/` 入口 `index.html`——判準＝人類瀏覽優先的產物〔開 index.html 看〕與 AI session 中間產物〔ai-analysis/〕分區；命名對齊 repo 既有詞彙族，勿與既有報告區形成雙胞胎名）而非混進既有報告區——blanket ignore（`reports/**/*.html`）對混合用途目錄是潛伏衝突，規則 scope 進專屬目錄即解除。詳 [[project_archify-illustrate-html-mode-eval]]。

**消費端現況（2026-08-28 末盤點）**：NT ✓（自帶 ignore `.code-reality/.gitignore` 寫 `*`——fork 不動 root gitignore；status 乾淨；818MB）；offline_backtesting ✓（root .gitignore `0914dedd`；454MB）；ai-rules ✓（`5525ecf`；392K）；**mosaic_alpha 缺口**（112MB `??` 污染——root .gitignore 待補一行，或隨相互 rebase 繼承 offline_backtesting 的 commit）；trading_lab 未建庫、規則先加防患。總量 ~1.4GB、每 worktree 一份＝設計（repo-relative）；生成物安靜長大意識（ENOSPC 教訓）。另：CC 官方 `claude-plugins-official` 已出 `pyright-lsp`／`rust-analyzer-lsp` plugin＝分發軸 CC 接線形態定案時的對標物。
