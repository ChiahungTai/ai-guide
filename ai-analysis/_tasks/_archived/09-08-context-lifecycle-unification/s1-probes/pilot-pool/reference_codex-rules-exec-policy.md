---
name: codex-rules-exec-policy
description: Codex 的 rules/＝exec policy（Starlark prefix_rule）非行為
  rules——名稱撞詞陷阱；行為承載仍是 AGENTS.md；ref-docs 鏡像在場但 contracts.md 無 codex 欄
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_2899ca4d-a35b-4774-ab87-e0f641c1c9c1
---

Codex `rules/` 機制（2026-09-07 查證 `ref-docs/harness/codex/rules.md`，官方標 experimental）＝**命令執行政策（exec policy）**，與 Claude `~/.claude/rules/*.md` 行為規範是名稱撞詞、語義完全不同：

- 格式＝Starlark 程式碼：`prefix_rule(pattern=[...], decision="allow|prompt|forbidden", justification, match/not_match)`（match/not_match 是載入時自驗證）；多規則命中取最嚴（forbidden > prompt > allow）
- 職責＝控制 sandbox 外命令——對應物是 Claude `settings.json` permissions，不是 rules/*.md；若未來要把 permission 清單搬到 codex 端，載體就是 prefix_rule（符合 [[permission-layer-no-behavioral]] 原則，Starlark 也裝不了 prose）
- 載入：啟動掃 active config layers 的 `rules/`（user `~/.codex/rules/`＋team config；project `<repo>/.codex/rules/` 需 trusted）；TUI 把命令加 allow list 時自動寫 `~/.codex/rules/default.rules`
- `bash -lc` 等複合命令：線性安全鏈（純字＋`&&`/`||`/`;`/`|`）用 tree-sitter 拆開逐段評估；含重導向/變數/萬用字元則整串當單一 invocation——防走私
- 離線測：`codex execpolicy check --pretty --rules <file> -- <cmd>`

**Codex 行為指令承載仍是 AGENTS.md**（官方 `guides/agents-md.md` 專頁）——ai-rules 把 guide bundle 部署到 `~/.codex/AGENTS.md` 已是 codex 端正解，無新機制可遷。

ref-docs 鏡像現況：`ref-docs/harness/codex/` 完整在場（manifest 95 頁，base=developers.openai.com）；多數頁面 07-03 抓、`rules.md`/`codex-manual.md`/`config-advanced.md`/`guides/` 08-16 更新、manifest（09-04 生成）已登記。**缺口：`contracts.md` 對照表只有 Claude/OpenCode/ZCode/Muse 四家，無 codex 欄**——要納 codex 對照分析時素材已在，只缺分析腿。
