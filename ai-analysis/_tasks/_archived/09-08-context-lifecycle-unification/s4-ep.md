# S4 子 EP：生命週期統一（S3 路徑跑一次四動）

> **ep_type**: implementation（docs/audit mode——稽核方法論＋處置執行，無 production 行為碼；以既有工具驗證，不依賴 S5 未完成的工具重構）
> **parent**: ai-analysis/_tasks/09-08-context-lifecycle-unification/ep.md（master blueprint，S4 段＋處置保全）
> baseline: 28734c5

## Context

在 S3 代表性取用路徑上跑一次完整四動，驗證引擎與分類判準；S5 再承接已驗證流程。依賴 S1/S2＋S3 代表性路徑驗收。

## 做什麼

memory-audit 擴充為生命週期引擎，六步：收集候選→附證據→判定處置→更新來源→重建投影→驗證消費端。共用處理程序，處置判準按類保留：memory 觀察是否仍成立、rule 約束是否仍必要、skill 流程是否走得通、project 指引是否仍能找到入口。Read/mtime/字數只產候選，不直接裁定升格、常駐或淘汰；重複教訓亦須核實適用範圍，不僅憑次數固化。

處置保全：精煉保留必要條件，淘汰不切斷唯一入口，晉升不把一次性經驗泛化；證據不足可保留候選不處置。

## 驗收

SM-6/7＋四動處置證據及消費端行為對照（含跨 session 接續後仍有效）。驗收的是知識健康（條件未丟、入口未斷、未過度泛化），不只四動產物存在。

## 產出

`s4-report.md`（候選清單＋逐項處置證據＋行為對照）—— nuclear：任一保全 violation 即該輪否決。
