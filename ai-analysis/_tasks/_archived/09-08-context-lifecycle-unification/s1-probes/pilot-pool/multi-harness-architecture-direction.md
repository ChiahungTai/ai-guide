---
name: multi-harness-architecture-direction
description: ai-rules 跨 harness 方向——兩消費端、standards-first＋客製化 overlay、ref-docs/harness 為參考
metadata: 
  node_type: memory
  type: project
  originSessionId: 3fded13d-730e-4c48-b708-0cde072353f2
---

ai-rules 多 harness 方向（2026-07-03 定）。兩個面向都要跨 harness：**(1) 消費端 mosaic_alpha**（專案層）、**(2) ai-rules 自身**（全域 source 層）。目標 harness：Claude Code / ZCode / OpenCode。

**設計原則**：standards-first（`AGENTS.md` + `SKILL.md` 開放標準為基底）+ per-harness 客製化 overlay。`ref-docs/harness/`（已建，commit c2ba159）的角色＝**客製化參考**——要在某 harness 客製時，查該 harness 鏡像文檔「怎麼做」。

**Why**：AGENTS.md 是跨 harness 公約數（OpenCode/ZCode 原生讀、Claude 可 `@import`）；CLAUDE.md 三家分歧（**ZCode 不讀**，僅 onboarding 一次性遷移，見 ref-docs/harness/contracts.md 引 zcode agents.md:49）；SKILL.md 格式可攜但**語意不可攜**（skills 綁 `/implement` `/commit` backlog board 等 repo 慣例）。

**架構分層方向**（foundation 已落地，見下方「✅ 落地狀態」）：L0 neutral intent（rules/skills 內核，harness 中立）→ L1 standard emission（AGENTS.md/SKILL.md）→ L2 per-harness adapter（Claude hooks/paths、ZCode `.zcode/`、OpenCode `opencode.json`）。鐵律：**客製化只往外層（adapter）加，不可往內層（neutral core）滲**（共用層外溢陷阱，見 arch-thinking skill）。

**範圍邊界**：`commands/`（slash command）+ `hooks/` + `agents/`（subagent frontmatter/位置/ZCode UI-Beta 都 harness-specific）本質 Claude-specific，**不強求跨 harness**（過度工程）；可移植的是 `rules/` + `skills/` 的「知識/工作流意圖」。agents/ 的 system prompt body 相對可攜，frontmatter/位置不可攜——跨 harness 時同 hooks 處理（frontmatter 轉換 + 丟對應全域目錄；ZCode 跳過）。

**superpowers 參考定位**（見 ai-analysis/reports/superpowers/）：obra/superpowers 三層架構是「neutral core + adapter」範例，`docs/porting-to-a-new-harness.md` 是 adapter 範本；但 session 已決定**只借內容/手法不借結構**。ai-rules 比 sp 容易（sp 是 plugin 要 adapter；ai-rules 是個人 rules/skills 走 OpenCode fallback 相容）→ **superpowers 參考價值收斂到只剩 hooks adapter**（sp `.opencode/plugins/superpowers.js` 為範本，CC `PreToolUse` ≈ OpenCode `tool.execute.before`）。詳 reports `03-OpenCode退路.md`。

**✅ 落地狀態（2026-07-07 更新）**：foundation 已落地（`ep-ai-rules-multi-harness-foundation` 架構 B + `ep-deploy-scope-neutralization`）。原「最小動作」已超額完成——不只 root `AGENTS.md`，更演化成 `scripts/deploy_agents.py` bundle（scope-aware neutral-only 生成 + 斷 ref guard + idempotent），部署到三個非 Claude 端（zcode/opencode/codex），已驗證 bundle marker 同步 = 非 Claude 端讀得到 neutral rules（S4 dogfood 變相涵蓋）。原「雙向門先走最小」已通過。**未做（非必要）**：source restructure 成 core/+adapters/；skills 語意可攜性仍是潛在單向門。

**鏡像更新工具**：`ref-docs/harness/crawl.py` 是鏡像的既有刷新工具（五源 discover + sha256 增量寫入 + manifest 維護；zcode 走 HTML 正文抽取，code.claude.com 支援 `.md` 直取）。更新鏡像跑它，**不要手動逐頁鏡像**——2026-08-14 session 因沒查到它（存在 `ref-docs/harness/` 而非 `scripts/`）手寫了 6 頁才發現工具存在，工時浪費。已補進 root AGENTS.md ref-docs bullet。09-05 三源刷新實證 crawler 行為：只增改不刪——上游暫時 404 的頁磁上留舊檔（如 meta api-reference/files/schemas.md），下次重跑自癒，不需手補；多源更新逐源跑（每次重寫 manifest）。

**2026-09-02 增量**：第五鏡像源 `meta`（dev.meta.ai＝Meta Muse Code/Model API，92 頁；索引在 `/docs/llms.txt`，站無 root llms.txt/sitemap）。User 發起 Muse Code 第二 harness 候選評估——詳 [[muse-code-second-harness-eval]]。

**How to apply**：相關討論/決策 recall 本 memory；落地前用 `/arch-thinking`（結構視角）+ `/execution-plan`（實作計畫）。落地後回寫 CLAUDE.md 一個 section。關聯 [[ai-rules-dual-role-mosaic-shared]]（ai-rules 是 mosaic 共用 skills 的家）、[[feedback_ai-rules-no-backward-compat]]（演化式乾淨重構，無外部合約）。
