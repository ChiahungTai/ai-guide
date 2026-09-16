---
name: output-self-sufficiency-gate-values
description: gate/檢查工具輸出行必自帶門檻常數——輸出真空被旁側 stale prose 填補成假警（nightly-watch 兩次同型實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_5ad68a25-9a25-4d0e-8fe9-33d024b7e9b5
---

量測/檢查工具的輸出若不含 gate 值，消費 session 無法就地校驗——真空不會留白，會被旁側更不可靠的源填補（狀態戳 prose、prompt 記憶），而那些源會 drift。

實證（memory 索引 generator，同型兩次）：`--check` 輸出只報數字不報 gate → 09-02 nightly-watch 用 prompt 硬編碼舊值假警；09-05 消費 session 轉引 `_audit-state.md` prose 舊值（18,500 vs 真值 22,500）誤報「貼線、餘裕 1,069」（真實 77.5%、餘裕 5,069）——「輸出真空由 prose 填補」是同一盲區第二次發生。

**Why**：工具輸出行是消費端唯一信任的當下事實；它缺的資訊不會消失，只會改從會腐敗的地方來。與 [[settlement-scripts-are-code]] 同軸（尺的可信度），互補面在此是「尺的讀數自足」；與 [[feedback_inflow-needs-outflow]] 對偶——數字放 prose 會漂，放權威輸出行才穩。

**How to apply**：①設計 gate/閾值檢查輸出時，OK 路徑附 gate 常數、FAIL 路徑附超限比值——消費端 quote 該行即自足；②下游引用 gate 一律以工具輸出行為源，不信 prose/prompt 轉述值；③審查既有檢查工具時把「輸出是否自足」列為維度。已落地：generate_index.py 三條輸出路徑附 gate（OK×2＋size FAIL 比值）。
