# AI 協作開發指南

跨專案、harness-neutral 協作規範，量化交易優先；專案指令放各 repo AGENTS.md。

改 instruction 前載 instruction-writing skill；禁行數/字數/版本號/日期/Changelog。雙檔與引用規範見 [instruction-writing.md](rules/instruction-writing.md)。

## Session 開場導引

- **先定位現在在哪**：有 STATE.md 先讀最近 session 觀察，再以 active card／board 狀態與 card notes／EP 進度節核對目前工作、已完成處與 resume point；觀察層不能取代現況來源。
- **再決定下一個入口**：標準開發主鏈為 /execution-plan → /implement → /post-build → /commit；需求釐清、審查、修復等分支及各步方法論查 skills/AGENTS.md 索引與對應 skill。
- **skill 優先序**：skill 方法論衝突時，ai-guide 部署的 skills 優先於 harness 內建／marketplace bundled 同功能 skill。
- **需要跨 context 接續時先結算**：context 將耗盡先把進度與待辦寫回 EP／card；同一工作稍後續跑用 /at，交給另一個 session／repo／provider 用 /handoff。

## 驗證約束

修改後須實跑，再查語法/import 並依風險驗證；純文檔/註解例外見 [must-execute-before-complete.md](rules/must-execute-before-complete.md)，順序/消費端要求見 [quality-constraints.md](rules/quality-constraints.md)。

| 風險 | 範圍 | 驗證深度 |
|---|---|---|
| 高 | 核心架構、跨 context domain service、會計/風控總量與 sizing、數據庫、安全、重大 API | 完整驗證相關功能 |
| 中 | 新功能、演算法/性能優化 | 核心功能測試＋經驗分析 |
| 低 | 樣式、文檔、配置 | 至少確認語法；執行例外依上述 rule |

評估提供相對複雜度、風險、依賴、里程碑與排序；不預測絕對耗時或精確進度。

## UC-Driven Development

功能先定義 Use Case。AGENTS.md Capabilities＝已完成能力索引，backlog＝承諾池；多卡優先序可由 project blueprint dependency graph 決定（backbone），未被支撐的卡走 kanban triage；操作/refs/precheck 單一源為 kanban-board skill。

文檔角色：AGENTS.md＝導航/完成能力 what/where；architecture.md＝why；SYSTEM-MAP.md＝跨域現狀；dependency 地圖＝code-reality graph（機械產生；手繪 dependency-graph.md 已由 CR 取代——mosaic/ai-guide 均不再維護）；backlog/＝任務卡。長文按需 link，禁全量 transclude。

UC 狀態流轉與 Capabilities 寫入格式見 metadata-sync skill。

規模：simple（單檔小 tweak/bug）→card AC 直行不寫 EP；standard（跨檔 feature/refactor、無新 architecture/boundary 決策）→建立或更新 owning 卡＋**card Planning Contract**（六欄，定義見 execution-plan skill 流程規模分級節）；full（架構/跨模組/🔴高風險/新 boundary：state ownership、public contract、跨 context invariant、控制面 authority）→execution-plan standalone EP；accepted EP 的 bounded child→引用 parent EP＋card Planning Contract。實作中發現新 boundary 決策→升 EP amendment/子 EP（promotion）。小 bug/doc 免 UC；碰單位邊界/除權息/時區/會計/風控即非 simple，至少列受影響 invariant＋驗證式（silent-corruption 例外）。public contract 契約面新增／變更（含 additive）屬 full；既有 contract 純實作修復不升級（開卡時判定，詳＝execution-plan skill）。

動卡第一動設 In Progress；銜接機制（建卡即 commit 防 id 撞、結案兩步、precheck）單一源 kanban-board skill。

## Solo + AI 開發工作流

一人＋AI、無團隊/CI；一 EP＝一 session（bounded child 卡各自一 session，繼承 parent EP 已定決策），段落自含、可結算接續。model 退化先結算再 handoff 新 session；Writer/Reviewer 分離，review 支援跨 context／跨家族 findings 回貼。

## Marshal 姿勢（互動 session 預設）

需求足以選擇下一個可逆動作時 ⇒ 預設全程編排，不逐步請示：理解 → 派工依 model-routing resolver → 機械閘照跑 → 一般工程取捨自判、批次回報，檢查點照 quality-constraints。逐步徵詢僅限「需要 user 裁決的未決」：需求不明、方案分歧、風險裁決、優先序衝突。破壞性與單向門恆停；outward 及其例外（含互動 commit 機械例外）恆以 outward-action-consent 為唯一準據。已進入 unattended／autonomous 執行的工作歸 autonomous-execution，不適用本節。implementation work unit 一律 spawn（定義與 fallback＝agents/AGENTS.md execution contract；canonical 控制面直寫由 admission guard 機械擋）。

## 跨 repo 主權

跨 repo 寫入僅限對方主權隔離面＋授權面；mutation 歸 repo 主權、acceptance 歸 consumer；無小改例外；細節＝AIR-135.5。

## 架構設計紀律

spec/EP/implement/review 用 Clean Architecture＋DDD 視角，不強制模板/過度分層；決策證據與直接／間接後果見 [design-thinking.md](rules/design-thinking.md)，SOLID 見 [edit-discipline.md](rules/edit-discipline.md)；結構查證用 arch-thinking，介面合約設計（API／模組邊界／公開介面）用 arch-thinking 的 interface-design 側檔。

## 量化交易專屬鐵律

- 數據完整性優先：損壞比缺失更危險，禁靜默傳播（正文與 Crash-Only 適用範圍見 [quality-constraints.md](rules/quality-constraints.md)）。
- 回測完全可重現（hash＋config＋seed），波動 >0.01 必須重做。
- 狀態外部化；Live/Backtest 共用邏輯，避免模式分支。
- 隨機 seed 必須可注入，避免 np.random。

## Summary Instructions

壓縮對話必保留：已讀/改路徑、測試結果/錯誤、決策/理由、目標/待辦、已提交未執行命令/skill、待確認提案、背景/中斷工作。數字/比例須實際枚舉或逐字複製，禁憑記憶改寫。
