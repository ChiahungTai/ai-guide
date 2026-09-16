---
name: memory-card-lifecycle-gate
description: memory 卡流水結案閘門（AIR-37 已落地）——條文在 commit skill 2.8＋execution-plan UC 盤點；教訓錨：卡 id 弱鍵＋desc 過期快照主動誤導
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5fcef0cd-2b0f-4e95-8a02-4feb508cc4cc
---

memory 卡流水（弧狀態快照、git 可推導內容）結案清理已從流程自覺升為機械閘門（user 09-07 拍板「commit 跟開卡時要考慮清」；AIR-37 同日落地）——**條文單一源在 repo**：commit skill 2.8「memory 池對帳腿」（掃描鍵聯集＋結案態前置＋三分歸屬）＋execution-plan UC 盤點「同主題 memory 條目盤點」登記腿；蒸餾方法論單一源在 kanban 蒸餾第三動＋memory-audit 寫入端紀律。

**教訓錨**：①卡 id 是弱掃描鍵——21 條 `project_*` 中 11 條不含 AIR- 字串（無卡弧〔handoff brief 即工單〕掃不到），掃描鍵必須聯集（id ∪ EP 登記清單 ∪ 弧主題詞）；②desc 過期狀態快照會主動誤導——desc 是開場載入層，舊弧狀態持續灌輸（09-05 過期派發事故同根）；③結案態前置必要——mid-arc 掃到 in-flight 條目一律不動（進行中弧線等收案一次性蒸餾），當場蒸會打爆成長中條目。

存量債（21 條 `project_*` ~130KB＋5 檔流水詞）出口＝夜波/audit 波段，不隨弧清。後繼弧：[[air-38-routing-feedback-tier]]（execution-plan SKILL 同檔排後，已落地可接續）。
