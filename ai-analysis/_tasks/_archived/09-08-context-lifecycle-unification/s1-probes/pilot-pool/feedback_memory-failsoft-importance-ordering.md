---
name: memory-failsoft-importance-ordering
description: user 記憶治理設計觀——與其難 audit/壓縮，順著截斷特性設計：重要放前、可遺漏沉後、fail-soft（機制失靈也不離譜）；已落地 rank 排序
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_5fcef0cd-2b0f-4e95-8a02-4feb508cc4cc
---

user 2026-09-07 設計方向：memory 索引載入（200 行／25,000 chars）**尾端截斷**——與其追求完美 audit/壓縮，**順著截斷特性設計**：重要放前面、可遺漏隨時間沉後、定期整理——「就算機制有失靈，也不會太離譜」（fail-soft：失敗模式有序，爆炸半徑被結構性限制）。

**原則要點**：截斷只影響開場自動載入——條目檔仍在池、rg 可查；真實失敗形態＝**召回率下降非資料丟失**，重要性排序把召回損失導向冷門。排序鍵住條目 frontmatter（`rank: hot|core|cold`、缺省 core）；MEMORY.md 是機械投影禁手排——「定期整理」＝整理排序鍵非手排索引；同 rank 內順序無語義（位置非身份）。

已落地（AIR-39）：generator 排序＝type 組×rank×mtime 尾序＋memory-audit 三處條文（寫入端初判/層 1 語義/夜波排序鍵覆核）——條文單一源在 repo。與 [[inflow-needs-outflow]] 同族（user 治理世界觀：與失敗共存、給失敗設計出口，而非追求不失敗）。
