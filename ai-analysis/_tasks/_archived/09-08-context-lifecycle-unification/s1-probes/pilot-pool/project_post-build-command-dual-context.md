---
name: post-build-command-dual-context
description: post-build/review 鏈線終態——收尾鏈與 dual-context 雙審查者、鏈上載體分工（judge=主 agent）、新 skill 收編 post-build docs 鏈慣例
metadata:
  node_type: memory
  type: project
  originSessionId: sess_36533380-1749-4450-bfc6-d7b66bd716dc
  merged_from: [project_kbar-form-analysis-landing]
---

`/post-build`（diff triage → code 鏈 → docs 鏈 → 收尾報告，止步 /commit 前）與 dual-context 審查已落地（現址 `skills/post-build/`）。動機：user 在 mosaic_alpha 高頻手動跑此固定序列（Claude 359 sessions 抽樣證實）。

## dual-context 雙審查者（≥3 files 才 dual）

- `code-reviewer-primed`（餵 diff＋EP＋Capabilities＋dependency-graph，抓 intent drift／架構契合／YAGNI↔過度工程）＋ fresh-eyes `code-reviewer`（只餵 diff）；**context 差異在 spawn prompt 餵料非 agent 定義**；primed 餵料含 code_reality transition 報告（EP 宣稱 vs 實際變動機械對照——產出機制單一源在 code-review 模式 B，見 [[cr-live-faces-roadmap]]）
- 矛盾 finding 標 conflict 交 judge-review 裁決，不合併端裁決
- **鏈上載體分工（查證定案）**：stage1 code-review＝spawn 獨立 agent（Main LLM 自審模式已廢）；stage2 judge-review＝**主 agent**（skill 經 Skill tool 載入主對話執行——judge-review allowed-tools 無 Agent tool、registry 無 judge agent 型）——judge 角色是「實作工程師」評審查者建議，需 EP/build context 才能判 intent drift，不違 Writer/Reviewer 分離（獨立性在審查側）。**無「派他家族（muse/codex）當 judge」接線**——external-runtime routing 只定義 reviewer 交接；獨立使用 judge-review 可貼 `ai1:/ai2:` 多來源建議合雙家族 findings 一起裁（[[feedback_dual-family-review-dispatch]]）
- 收尾報告模板含「EP 對照」triage 行（可見性掛自動鏈終點——用戶不會每次跑 debrief，靠人記的步驟會漏）

## 新 skill 收編＝post-build docs 鏈標準流程（kbar-form-analysis 收編弧沉澱）

外部 session 產出的 untracked skill 經 user 明示納入本 session 流程（**明示指令可推翻同 working tree 並行原則的「不審不改」預設**）→ post-build docs 鏈典型 fail-fixed 檢查點：

1. 缺 frontmatter（sibling 慣例全有 name/description；缺它 auto-discovery 無描述）→ 補 name+description+when_to_use
2. 術語孤例→對齊通篇用語；矛盾條款（agent 被要求評斷沒看過的東西）→ 改「盲判產出後由 caller 對照浮現」
3. skills/CLAUDE.md 對應段補索引行（**新 skill 不補即斷鏈**）
4. 外部引用逐項驗證存在（消費端工具檔、agent 在 registry）
5. **接手 first move：`git log --oneline` 查收編 commit 是否已落地再動作**（並行 session 狀態過時防護）

**ai-rules repo 工具鏈事實**：ruff-only（pyproject 無 mypy）——/commit 的 MyPy gate 對本 repo 不適用；`Failed to spawn: mypy` 是環境缺裝非型別錯誤，如實記「➖ 不適用」勿硬跑。

相關：[[feedback_consistency-gate-not-optional]]、[[project_instruction-init-blueprint-scope]]（commands→skills 段）、[[cr-live-faces-roadmap]]（transition 接線）、[[feedback_review-even-on-quick-fix]]
