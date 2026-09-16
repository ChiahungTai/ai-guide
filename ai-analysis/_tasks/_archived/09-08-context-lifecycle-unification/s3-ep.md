# S3 子 EP：投影器與層級軸（代表性 project，先驗後擴）

> **ep_type**: implementation（pilot/mixed mode——deploy script 改造屬工具碼，改動走 RED/GREEN；層級重分配為 docs；驗收含行為對照 probe）
> **parent**: ai-analysis/_tasks/09-08-context-lifecycle-unification/ep.md（master blueprint，S3 段＋Review 承接 18/19）
> baseline: 28734c5

## Context

先在代表性 project（ai-rules 工作區）驗證 S1 勝出方案與 S2 最小條目化；mosaic root 42.7KB 為主案但由 mosaic 側 session 執行（工單路由，本 EP 只出判準表與驗收，user 可改指 owning session）。draft-3 承諾範圍驗收後才結案。

## 做什麼

1. `scripts/deploy_agents.py` → 以必要常駐集合∩scope 投影，rank 只排集合內順序。per-target gate 保留：muse trusted user-floor ≤50KB 且 floor＋workspace project＋實際 framing ≤65,536；codex 100K 軟；zcode 100K 硬；opencode 依部署範圍處置。
2. 低頻不可漏約束不因 rank 或預算被裁掉；必要集合超額須顯式處置（degraded 宣告，非靜默截斷）。
3. 層級重分配：每下沉單位交代原保障行為／新位置入口／上層短指引／盲測任務；適用範圍≠檔案目錄；S0 瘦身幅度為候選，實際可移量由取用驗證定。
4. Trust 分支（18/19）：部署面僅 ZCode/Codex/Muse 三端，Claude 原生另行抽驗；Muse 以實際 framing/source 對帳，untrusted/project 省略/超額記 degraded；不自動改 trust。

## 驗收

SM-2/3/4/5＋逐單位下沉前後行為對照（bytes 下降不判成功）＋部署後探針（記 trust/source 數、rendered/text bytes 與內容錨點）。回滾：投影前 bundle 形態快照進 version 目錄。

## 產出

`s3-report.md`（投影規則＋gate 實測＋重分配行為對照）＋`s3-probes/`（探針腳本與輸出）。
