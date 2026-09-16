---
name: crg-install-platform-coverage
description: CRG（code-review-graph）安裝語義——三段式安裝、「one command」僅指 install、16 平台不含 ZCode、直寫 config 非 marketplace
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_bdd4d7c1-8464-44f1-8ec7-c1d0c8847e12
---

CRG（tirth8205/code-review-graph，PyPI 套件）安裝語義，2026-08-29 對照 upstream README 查證（user 問「一行還是三行、含 plugin 嗎」）：

- **三段式非一行**：① `pip install code-review-graph`（全域套件）② `code-review-graph install`（全域平台設定，一次性）③ `code-review-graph build`（**per-project** 建圖，每 repo 各跑一次，不屬「安裝」）。README 的 "One command sets up everything" 話術只指 ②——一次設定所有*支援的*平台，不是整個流程一行。
- **16 支援平台不含 ZCode**：codex/claude-code/cursor/windsurf/zed/continue/opencode/gemini-cli/antigravity/qwen/qoder/kiro/copilot/copilot-cli/codebuddy/hermes。**Zed 與 OpenCode 都是名字相近的不同產品**，Z.ai 的 ZCode 不在清單——installer 對 ZCode 零動作。
- **機制非 plugin marketplace**：對支援平台是直接寫 MCP config、裝平台原生 hooks/skills、注入 graph-aware 指令到平台 rules 檔；無任何 marketplace/registry 流程。
- **本地實況（2026-08-30 殘餘全清完結）**：:5555 server 曾**復活**——08-26 cutover 的 `launchctl bootout` 只卸載當下實例，plist 留在 `~/Library/LaunchAgents/` 且 `RunAtLoad=true`，**每次登入自動重生**（cr-query SKILL:106「已 bootout」宣稱因此與現實矛盾——真退場＝bootout＋刪 plist 缺一不可）。用戶裁決「舊的就刪除清乾淨」後已全清：`com.user.crg-mcp` plist 刪、port 5555 釋放、**uv tool uninstall code-review-graph v2.3.7**（`code-review-graph`＋`crg-daemon` 兩 bin 移除；曾雙份並存＝uv tool v2.3.7＋plist 的 uvx @2.3.8）、`~/.mosaic/logs/launchagent-crg-mcp*.log` 舊日誌刪；museum repo `~/Github/code-review-graph` 保留（先前 user 裁決）。殘留一筆 doc 過時：cr-query SKILL:106「plist 留檔可回滾」已不成立（plist 已刪）——**已修**（現 cr-query SKILL:107 記「完全退場：launchd 退場＋plist 刪＋uv tool 解裝」）。

**Skills/rules 注入內容盤點＋參考評估（2026-08-29，v2.3.7 `skills.py` 逐檔讀；user 問「CRG 有 skill 可供參考？ai-rules rules 要跟著調？」）**：

- **CRG 出貨三件**：①4 個任務型食譜 skill（`_SKILLS` dict：explore-codebase/review-changes/debug-issue/refactor-safely）＝任務→工具序列 step-by-step，尾巴統一 Token Efficiency Rules（ALWAYS get_minimal_context 先行／`detail_level="minimal"`／≤5 calls ≤800 tokens）；**只產 Claude 格式** `.claude/skills/<name>/SKILL.md`，其他平台只吃 rules 注入。②rules 注入 `_CLAUDE_MD_SECTION` 寫進 CLAUDE.md/AGENTS.md——核心句「ALWAYS use graph tools BEFORE Grep/Glob/Read」＋when-first 清單＋key tools 表。③hooks（PostToolUse Edit|Write→`update --skip-flows` 30s、SessionStart）。
- **裁決：ai-rules rules 不跟著調**——路由已更精細（文字→rg 本來就大宗，telemetry 實測 rg=CR CLI 2.7 倍，ALWAYS-graph 是倒退）；install-time copy 已被 08-28 包裝裁決否決（symlink live > copy）；≤5/≤800 是不可驗證行銷數字；hooks 自動刷新已裁 WARN 驅動（YAGNI）。fork repo skills/ 有 7 個（多 review-delta/review-pr/build-graph）＝vintage 差異。
- **兩個吸收點已決（2026-08-31 audit 回寫）**：原標的 crg-query skill 已隨 CRG 全退場由 cr-query（code-reality）取代，吸收前提消失——①`detail_level` 分級未吸收（cr-query 0 hits）②get_minimal_context 已在 cr-query 路由表在場（:23/:52/:70），無需另補。原評估：①=CR list_communities/get_community/architecture_overview 支援的分級教學、②=cold-session 首次進大 repo 場景句（不吸收 ALWAYS 版）；錦上添花非缺口修復。

相關：CRG fork lineage 與 :5555 來源見 [[cr-live-faces-roadmap]]；CR 分發軸（PyPI wheel/plugin carrier）見 [[cr-live-faces-roadmap]]。
