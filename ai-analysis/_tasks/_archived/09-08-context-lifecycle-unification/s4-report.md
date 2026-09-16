# S4 Report：生命週期統一（S3 路徑跑一次四動）

## 引擎落地
`skills/memory-audit/SKILL.md` 新增生命週期引擎段（六步＋分類判準＋保全＋投影驗證），定位：兩級稽核做池內核實，四動做跨載體處置循環。不碰既有層級與寫入端紀律。

## 本輪處置（S3 路徑候選 5 項）
- C1 必要集合 12：保留。S1 部分行為證據＋本弧活躍使用，無反證；6 未測記缺口不處置。
- C2 slim 指針完整性：保留。6 檔標記配平、YAGNI 指針目標在場、各 skill 家在場、rg 無懸空引用；無源變更。
- C3 quota-failover-policy：保留。09-07 修訂現行，無反證；現值查證屬 billing 面另案。
- C4 路徑相交 inflow 5 條：保留。mtime 變動＝活躍維護訊號，非過時證據。
- C5 Arm C 生成器：HOLD（S1 既定 merit，不在本段處置）。

## 投影與消費端
必要集合未變 → armB 無需重建（verified no-op）。消費端驗證沿用 S1 行為腿＋S3 盲探針＋本次 YAGNI 指針 rg；四動產物為本報告＋引擎段，無孤兒產物。

## SM-6/7
候選皆有附證據處置；證據不足項 HOLD（C1 未測部分、C3 現值、C5）。符合「驗收知識健康非產物存在」。

## 擴大判定（staging gate）
- S2 全量（16 條 frontmatter）：維持延期至 S5 規模 rollout（s2-report 登記）；現無消費者（bundle rank 排序待全量），提前做無收益。
- S3 多 repo（mosaic 主案）：待 mosaic 側 session 回來（判準表已交 s3-report）；ai-rules 側不得代驗 mosaic。
- 因此擴大＝零執行＋兩項 pending 登記，不另產物。
