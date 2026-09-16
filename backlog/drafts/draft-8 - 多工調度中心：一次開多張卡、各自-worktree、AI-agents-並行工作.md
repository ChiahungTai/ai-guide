---
id: DRAFT-8
title: 多工調度中心：一次開多張卡、各自 worktree、AI agents 並行工作
status: To Do
assignee: []
created_date: '2026-09-10 01:50'
updated_date: '2026-09-16 05:55'
labels:
  - governance
  - agents
dependencies: []
ordinal: 57000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
讓你（user）只開一個指揮中心 session，它同時推進兩三張卡：每張卡有自己的 worktree 隔離，每個 worktree 裡有兩三個 AI agent 協同工作（寫手＋審查者）。你不用再當 worktree 間的搬運工——進度、結論、異常都會彙整到 board 上給你看。目前狀態：POC 已驗證核心可行（mosaic 雙卡並行 8/8 全過），等你開工。

User 09-10 願景：一個 command center session 一次控制多卡（各卡對應 WT、每 WT 兩三個 agents 協同）——user 不再當 WT 間搬運工（mosaic 三 WT 痛點：context 經 user 轉譯）。分層：L0 user（一個 viewport）→L1 調度層（CC session：wt-open/close 呼叫者＋agent 編隊＋跨卡對帳，不寫 code——即本日 CC 形態的泛化）→L2 執行層（每卡一 WT，卡內 writer＋reviewers×2＋judge 編隊）→L3 shared（board control plane＋memory symlink＋bridge ledger）。範圍三段：〔A 調度層設計〕agents 進 WT 的機制（bridge cwd 參數／絕對路徑守則升級為主形態／worker session——對照 mosaic B 研究的三案；POC 已實證 subshell cd 形態可行＋路徑契約三閘〔prompt 只帶路徑/branch 自驗/錯位 STOP〕）＋agents 共享黑板（.agent-poc/<card>/ 落盤近似 CC agent teams 的 teammate 互訊——ZCode 無原生）＋CC context 預算（產出落盤只收 verdict）。〔B fleet 規範〕並行度成文上限＋成組慣例＋失敗階梯擴充＋fleet 成本量測腿＋stopped 回收慣例。〔C routing drift 查證〕review 主鏈實況 full 為主 vs model-routing reviewer-lite 預設。前置：AIR-72。素材：reports/2026-09-10-agents-fleet-research.md＋.agent-tmp/poc-wt-report.md。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide cfdb1ac〕
〔已決策勿重辯：①user 0916 拍板架構＝marshal 是唯一協調點，worker 禁互講（hub-and-spoke）；共享狀態＝磁碟落盤由 marshal 收斂——黑板機制從設計刪除（實戰 9 worker 全 PASS 零重派已證不需要）②前置已兌現：AIR-72 wt-open/close＋AIR-109 池拓撲 opt-in（f03f800）＋bridge heartbeat＋liveness ticker＋09-16 三 WT 實戰 ③硬約束：池拓撲敘述跟隨 AIR-100（sess_014a87f8）決策，禁寫死現行 pool-symlink 形狀；本卡實作排 AIR-100 之後〕
縮範圍＝marshal 實戰形態產品化：黃金模板六要素（role 宣告／baseline／三線規格表／已決策勿重辯／驗收／執行 tier）成文進慣例文檔＋路徑契約三閘＋[Dispatch] preview＋獨立機械驗證（重跑 pytest＋rg 抽查）標準化。B 段四項逐項建議（final 勾選待 user）：①can_run preflight 保留（與 model-routing 額度快照合流）②execution identity ledger 保留簡版（孤兒偵測優先）③fault domain 五欄併 agent-workflow 既有 doctrine 精簡 ④observability 彙整保留。執行 tier：本改卡＝主 session 文件工作；產品化實作排 AIR-100 之後另弧。
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔架構師輪擴充 09-10——三方終裁吸收（.agent-tmp/architect-os-notes.md 三方終裁節）〕B 段 fleet 規範擴充四項：①can_run(work_order) preflight——dispatch 前硬 capability 查詢（harness×provider×model×snapshot×tools/MCP×sandbox×quota）選 executor＋記 routing reason；②execution process table/lease——agent/job 掛 execution identity（card/revision tuple/parent/status 含 orphaned）＋fault class retry/backpressure/reap orphan；③fault domain 分類×五欄（detection/retryability/state residue/self-heal owner/escalation）——含『規則被忽略』fault 類（registry 缺 type/MCP 快照缺工具實證歸類）；④observability 掛 execution identity——desired/actual/terminal/health-cost 四問＋token/duration 彙整（metadata 已有從未彙整）。A 題兩原語（enforcement level 分級＋lifecycle reconciliation 六 gate）為組件級結構債——本卡範圍判定：reconciliation 的 dispatch/wt-open 兩 gate 屬本卡；全六 gate+enforcement 分級另議（blueprint 待落定案）。

〔09-11 補〕stuck detection＝架構師輪「execution identity 觀測（desired/actual/terminal/health-cost 四問）」的 runtime 腿：delegated agents 卡住偵測（liveness 訊號＝目標目錄寫入停滯＋spool 凍結組合，禁單看 CPU——model-bound 低 CPU 正常）。素材＝delegate-bridge 2026-09-11 實證（muse sandbox×測試孤兒行程 wedge 40min；memory muse-build-round-ops）；過渡治理＝model-routing skill「完成回報收法」liveness ticker 條（caller 端，背景 Bash 自動喚醒）；工具層根治（jobs.json heartbeat／wait --stuck-alert）＝delegate-bridge roadmap。

〔09-16 三 WT 實戰——A 段落地素材（marshal 形態已跑通，待本卡產品化）〕任務單黃金模板（user 開 marshal session 的 prompt 格式）：①role宣告（你是調度層，不寫 code：開/收 WT、派 worker、收 verdict、跨卡對帳）②baseline（main hash＋clean 聲明）③三線規格表（每線＝WT 路徑＋branch＋卡＋第一動）④已決策勿重辯（檔案正交性、不做項、S1/S2 同政策切換不 deploy、worker 進 WT 機制＝subshell cd＋路徑契約三閘、黑板落盤只收 verdict、commit 特赦①-④、序列化合併序）⑤驗收（各卡 AC＋跨卡零互踩＋無半新半舊）⑥執行 tier（marshal＝decision 主 session 直做、worker 機械段 lite/決策段 full）。實證教訓：①9 worker 全 PASS 零重派——派工前 [Dispatch] preview＋派工後獨立機械驗證（重跑 pytest＋rg 抽查）是关键 ②池 gitignored 拓撲→涉及池的交付拆『資產源隨 branch＋池副本 marshal 合併後套』兩段 ③webgpt 工單材料必須內聯（≤8KB，帶路徑讀不到）④muse review 子命令無 prompt 面——scoped 文件審查走 task＋read-only 紅線 ⑤共享檔跨弧改動以 (idA,idB) 合併歸因，禁 hunk 拆分 ⑥worker 禁 commit——verdict 收齊＋外審＋judge 修復後一次展示 commit 計畫等 user OK，序列化合併。已回寫 model-routing（webgpt 內聯/muse review 無 prompt）。
<!-- SECTION:NOTES:END -->
