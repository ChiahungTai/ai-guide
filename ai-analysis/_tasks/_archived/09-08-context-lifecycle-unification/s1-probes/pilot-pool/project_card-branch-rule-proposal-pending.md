---
name: project_card-branch-rule-proposal-pending
description: 卡 branch 弧 09-08 進行中——主場反轉 mosaic（三 VSCode=三 WT、branch=ambient UI）；命名定稿 線縮寫-卡號（war-77/v2-77/mos-77/air-46）；EP 已寫＋AIR-46 建卡 commit 7c2f947；muse ep-review 背景跑，待 findings→judge→task brief→S1 實作
metadata:
  node_type: memory
  type: project
  originSessionId: sess_88e4ceae-eba2-409a-b9f1-7061b101f11f
---

卡 branch 生命週期弧（2026-09-08，AIR-46）。**user 末端拍板：設計主場是 mosaic**（「我這設計主要是為了 mosaic 啊」）——user 日常三 VSCode 視窗＝mosaic 三 WT（main/v2/warrant），branch 顯示是 harness/VSCode 恆渲染的唯一 ambient UI，現行只顯示線名看不到當前卡。早期「ai-rules 採用、mosaic 不採用」結論作廢。

**終態設計**（單一源＝EP `ai-analysis/_tasks/09-08-card-branch-lifecycle/ep.md`，docs mode）：
- 命名 `<線縮寫>-<卡號>`：mosaic＝`war-77`/`v2-77`/`mos-77`（main 線無歧義→卡 id 小寫）；ai-rules 單線＝`air-46`。前綴語義＝**最穩定消歧層**：多線 repo 用線縮寫（user 明確拒絕該場景的 mos/air repo 前綴）、單線 repo 用 repo 縮寫。卡號全 repo 唯一，branch↔卡機械對應、與卡檔名前綴共字串
- 生命：建卡不開 branch；開工（implement 階段 1 起手式⑤後）**自 owning 線** checkout `-b`；結案 /commit 確認後回 owning 線 `merge --ff-only` 吸收＋刪 branch＋WT 回線 branch；branch 生命＝session 級
- mosaic 配套（衍生 MOS 卡承接，不在 ai-rules 動 mosaic 檔）：線判定機械升級（`線名 OR 線縮寫前綴`——war-77→warrant，資訊更多非更少）；owning 線記卡 desc＋開工驗證 checkout 起點
- SM-1..13 要點：吸收時線已前進→`--ff-only` 大聲拒絕→/rebase 兩步；忘記 checkout＝**軟失敗禁回頭搬 commits**；夜間 automation commits 落卡 branch 無害；單 writer 前提不變＝**非並行授權**；跨 session 接手 checkout 續用不 `-b`
- product＝ai-rules/AGENTS.md「git 慣例」節（S1）；業界 grounding 在 EP 段落 0（Anthropic --worktree、Kempé per-task 可拋棄、ticket-ID 命名、TBD 直線正統）——接手勿重跑研究

**立場演進軌跡（防退回舊立場）**：①AI 初判「不一律、branch=重複索引」→②muse 同向（線映射破裂/開錯 base/清理債/rebase 暴增）＋tag 替代論→③user 顯示論點＋業界研究扭轉（branch＝harness 唯一恆渲染 git 狀態＝ambient UI；顯示軸上 tag/commit-id 不等價）→④**主場反轉**：mosaic 才是目標，muse 前次反對論點以「線縮寫前綴＋判定升級＋session 級生命」回應，已派 muse 逐項反轉對照審查。

**弧狀態**：EP 已寫；AIR-46 建卡＋commit（`7c2f947`，desc 三必有）；muse ep-review 背景跑（F1-F5＋「前次七反對論點逐項對照」必答段）。待辦：muse findings→judge-review（主 agent）→修正寫回 EP→task brief 殼→S1 實作→開 mosaic 衍生 MOS 卡。

user mosaic 維護習性（設計輸入）：三 WT 一 branch 用到爛、很少切 branch；「一個 main 不能多 WT」→ 常把線 rebase onto main 當變相回 main；動機＝VSCode 看碼。教訓見 [[feedback_design-target-repo-confirm-first]]。

Related: [[project_session-topology-single-writer]]、[[project_rebase-skill-nowt-ff-fix]]、[[ai-rules-dual-role-mosaic-shared]]、[[feedback_dual-family-review-dispatch]]、[[feedback_rules-no-project-specific-facts]]。
