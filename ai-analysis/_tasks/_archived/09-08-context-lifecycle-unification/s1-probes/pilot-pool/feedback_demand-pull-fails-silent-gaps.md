---
name: feedback_demand-pull-fails-silent-gaps
description: Demand-pull 只對顯性故障有效——沉默缺口（undercount/覆蓋不足）需主動量測（spike-now-decide-on-data）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

Demand-pull 機制（消費端 [cr-demand] 卡→hub sweep→user 裁決）的前提是**消費端感知得到痛**。沉默缺口（query 結果看起來合理但 undercount、覆蓋不足、精度損失）結構性不滿足此前提——消費端要開卡得先獨立知道正確答案長什麼樣，它做不到。

**Why**：2026-08-28 W6（Rust 語法互補面）真實案例——hub 先裁定 demand-triggered（「等 NT 被 macro 邊缺口咬到再開卡」），user 挑戰「為何不直接做」後 hub 承認盲點：NT session 跑 impact_radius 得到 10,985 看起來合理就收工，無從知道真實答案是 13,000——undercount 不是 error，等卡＝永遠等不到。對照組：同機制對 pipeline-gap 產壞庫（顯性故障、看得見）流程正確（mosaic 報告→2442692 修復）。

**How to apply**：為共享工具規劃加值面時先分類缺口——①顯性故障（error/壞輸出/崩潰）→ demand-pull 合適（卡會來）；②沉默缺口（undercount/覆蓋不足/精度損失）→ 需求方無法自我發現 → 走「spike-now-decide-on-data」：主動量測殘餘（spike 便宜）→ 數字給 user 裁決建不建。勿把沉默缺口掛在 demand-pull 下（＝變相永不觸發）。判準一句話：**消費端能不能在不參照工具內部的情況下察覺這個缺口？能→開卡機制；不能→量測機制**。

**兌現（2026-08-28 W6 結局）**：spike-now-decide-on-data 實際執行→數據＝**不建**（高信心殘餘 ≈0-1；「Rust+Python 需求都大」假設被量測推翻）——機制閉環：沉默缺口走量測、量測餵裁決、裁決關案。demand-pull 機制本體（[cr-demand] 卡三件套）保留不拆——對未來顯性故障仍正確。
