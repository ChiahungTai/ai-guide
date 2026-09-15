---
id: AIR-58
title: codex顧問化治理——model-routing角色升級＋agents.toml納管＋mosaic記憶路由
status: Done
assignee: []
created_date: '2026-09-09 21:45'
updated_date: '2026-09-15 14:34'
labels:
  - codex
  - model-routing
  - memory
  - agents-registry
dependencies: []
ordinal: 50000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
codex 從「額度稀缺、只能救火」升級為常備顧問（規劃/審查弧的跨家族第二意見）。舊 agents 設定檔已刪（09-09 執行完畢）；剩下的 mosaic 記憶路由修復排在 AIR-54 記憶移植落地之後。目前不需要 user 裁決任何事——等依賴到位再開工。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 model-routing skill codex 段 sweet spot 備註擴為規劃/審查弧候選（webgpt 觀察期語意）；dispatch 預設不變
- [x] #2 agents/*.toml 決策落地（09-09）：ai-rules 二 toml 已刪除（零 dispatch 消費者＋方法論經 skills 層送達＋手動複本違單一源——詳 S2 裁決）；CBM 三 toml 保留非治理面
- [ ] #3 mosaic 側 AGENTS.md 觀察池路由段落地（AIR-54 mosaic 移植後形態；handoff brief 已開給 center），codex session 實測讀得到池
- [ ] #4 S4 決策與 knob 記錄歸檔（卡或 model-routing/memory-audit 引用面擇一）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 5fe4018〕
09-09 查核定調 codex＝超強力顧問（規劃/審查五角色：spec、execution-plan、ep-review、code-review、judge-review）。基建已實證 90% 在位（rollout 解剖：bundle 40,092B 全載 sentinel 在場、skills 經 ~/.agents/skills symlink 進 codex USER scope、$skill-link 調用實測成功、memory 三層注入健康）；bundle 砍 rules 已裁決不砍（AIR-53 前例：角色約束歸工單不歸 bundle；codex 自身 memory 記有「直接修好」使用模式，實作守則在場是保護面非死重）。

本卡收斂三個治理缺口＋一個決策記錄：

S1 model-routing codex 角色升級：現值「額度最少、預設不派、僅 user 顯式指定」，sweet spot 備註只有 state-review。user 09-09 定調：webgpt model 導入後額度改觀「可能可以多用了，不過還要再確認，才剛開始用」——先擴 sweet spot 備註為「規劃/審查弧跨家族第二意見候選（webgpt 觀察期）」；dispatch 預設翻轉（預設不派→顧問角色可派）等 webgpt 穩定度確認後另行拍板，本卡不翻。webgpt 現值快照：model=chatgpt-web/medium、bridge openai_base_url=127.0.0.1:17841（codex-chatgpt-web 管理）。

S2 ~/.codex/agents/*.toml 治理——〔09-09 已決策並執行：**刪除**〕arch-thinking 三視角裁決：①use case——codex 官方「only spawns subagents when you explicitly ask」，rollout 全掃零 dispatch 紀錄（09-09 live $code-review session 亦 in-session 自跑、無 spawn），bridge 工單禁止再委派＝無任何消費者；②依賴規則——方法論已由 skills 層送達（$skill-link 注入 full SKILL.md 實證），toml 內嵌方法論是冗餘第二源；獨立性來自跨家族/跨 session 分離（GLM 寫→codex 審），非 codex 內部 spawn fresh-eyes subagent；③bounded context——手動複本脫離 roles/ 單一源三週即 drift，sync 納管要為零消費者多養一個 registry 面（toml 欄位契約另套）。執行：code-reviewer.toml＋code-reviewer-primed.toml 已刪（tombstone 暫存 .agent-tmp/codex-agents-tombstone-0909/）；CBM 三 toml（codebase-memory/scout/auditor——CBM 自帶三層查證 agents）非 ai-rules 物、保留不動。

S3 mosaic 記憶路由修復（user 09-09 拍板「這要修」）：mosaic_alpha AGENTS.md 無任何 codex/觀察池路由——zcode/CC 側教訓不會流進 mosaic 場的 codex。telemetry 證據：CC 側 09-09 仍在寫 mosaic 池（~/.claude/projects/-Users-ctai-Github-mosaic-alpha/memory/，project-consistency-sweep、project-arch-tours-drift-audit 等）——教訓在累積、codex 看不到。**排序依賴（09-09 補）**：AIR-54 mosaic 移植（owning 線實體＋其餘 symlink）先落地，路由行以遷移後形態寫——mosaic 主體將住 repo `.agents/memory/`（ai-rules 已落地同型可照抄：repo AGENTS.md「觀察池路由」段＋codex 唯讀＋`rg -i <關鍵詞> _inventory.md` 檢索式）；規格已開 handoff brief 給 center（AIR-54 執行 session）順手併入 mosaic AGENTS.md 同步步驟，或留本卡後接驗證。mosaic_alpha_offline_backtesting / mosaic_alpha_trading_lab 同型一併評估。

S4 決策記錄（無改動）：bridge 工單饋入 codex memory 生成＝保留。評估：符合 memory 原則——codex 官方 pipeline 自帶寫入端紀律等價物（extract/consolidation 雙模型、max_unused_days decay、secrets redact、rate-limit gate、idle-wait），memory_summary 實證品質良好（AIR-50/MOS 知識可用）；退場 knob 供日後翻案：thread 級 /memories、memories.disable_on_external_context=true（bridge 工單有用 MCP 面）。附帶已完成（09-09 本弧）：~/.codex/config.toml 過時註解 79KB→40KB 修正（backup config.toml.bak-advisor-0909）。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-12 註〕AC#1「擴 sweet spot 備註（webgpt 觀察期語意）」已被 09-11 webgpt 三條使用約束裁定實質涵蓋（rules/model-routing.md external-runtime 段＋skill webgpt 專節已落檔，commit e9b12e3）——開工時 AC#1 改為一致性檢查：確認 dispatch 段 sweet spot 備註與 webgpt 專節無矛盾即可，勿重寫（裁定紀錄＝memory feedback_quota-failover-policy 09-11 段）
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
撤回獨立承諾：前段（codex 舊 agents 設定檔刪除）09-09 已執行完畢；唯一殘項 mosaic 記憶路由修復已由 AIR-54 S6 落地（mos-88 分工吸收、8e33163fe inbox hooks＋AGENTS 觸發器——final summary 可考）＋DRAFT-4 後續審視承接，無獨立遺留。
<!-- SECTION:FINAL_SUMMARY:END -->
