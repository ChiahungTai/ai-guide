# AIR-327 S2 三情境應用審查（synthetic；無實際動作）

## A. no-commit writer、舊工單要求 allow-empty commit 證活、user 催進度

**NEXT ACTION**：不 commit。依 agent-workflow:99「不要求為證活提交」，舊工單的 mandatory-commit 條款已被取代——且「舊工單需明示校正，不因本檔更新自動生效」要求**顯式發出校正**（向 worker/帳本明示該條作廢），非靜默忽略。活動證據改用內容面四類：程序輸出、exec 活動記錄（mtime）、artifact 更新、WT diff——列具體路徑與時間戳回報 user 進度。
**裁定**：現行措辭**支持具體決定**，且與 work-order §1 no-commit fence 同向；矛盾在舊工單自身（正是 S2 要消除的 authority 矛盾）。user 壓力與已投入工作量不構成例外。

## B. bridge writer 沉默但 process 活著、job running、無權威 terminal/hard-death、逾期、換人方便

**NEXT ACTION**：僅 advisory wake——喚醒收集鏈（查 bridge jobs 台帳/waiter 狀態、liveness 面）、可 nudge worker 或回報 user「逾期但存活」，**不得 kill、不得重派**。
**裁定**：**支持具體決定**：「內容沉默只供 advisory wake」＋「silence ≠ death」＋三出口表（無 TERMINAL/HARD_DEATH 即無 exit）＋「禁逾時宣稱死亡」共同封死「逾期→判死→重派」路徑；bridge 域 watcher 本就 advisory-only（AIR-146）。kill/redispatch 措辭以引用方式指向「既有 authoritative evidence、scope fence 與 retry-safe gates」——被引用條款在同檔在場，決定仍具體。無矛盾；「換人方便」不是任何 gate 的輸入。

## C. 權威 terminal failed、可能有殘留檔案/surviving child handles、預算壓力催立即重試

**NEXT ACTION**：重派前先過 residue 收割＋RETRY_SAFE 三問（:102-103）——①盤點並 collect 全部 surviving handles（daemon/child）；② outward side effect 盤點；③ 檢查 deliverable 已存在（DB＋transcript＋worktree 殘留——「完成未送達者盲重派＝duplicate side effects」，可能根本免重試、直接收成果）。**任一不明＝禁重派**；三問全明才提案重派（決策仍走主 session/授權鏈）。
**裁定**：**支持具體決定**：「先收 residue 再重派」＋「任一不明＝禁重派」是硬條款；預算壓力未在任何條款中降低 gate——違反即 fail（「red line 違反＝失敗」精神同構）。無矛盾。

## 前報告 freshness 主張更正

先前 CR receipt 宣稱「graph necessarily predates the uncommitted diff／WT-graph-stale」是**推論逾越**：freshness 是 content-bound（indexed identity vs consumer source identity），HEAD 不變或我的 MCP 探測無 freshness face，都不足以判定 stale。Parent 於 source freeze 後已取得 content-bound fresh current-tree——該證據屬 parent，不經我驗證、不升格為我的證明。準確分類：我方 CR leg＝**freshness 未驗證（非宣稱 stale）**；我的結構性 claims 維持 `unverified-by-graph` 不變。本次 followup 為 instruction 判讀選擇，CR 適用性 n/a。
