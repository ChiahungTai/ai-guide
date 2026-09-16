---
name: compact-output-context-not-transcript
description: compact/summary 產出＝脈絡壓縮非時序流水帳、素材涵蓋全 session 非只尾端對話（user 09-07；AIR-35 已落地）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_44ce10e8-3773-4756-925a-68e81ca4363e
---

user 09-07 對 compact-prep 產出的回饋：「不要記流水帳，不要傻傻單純的只使用最後幾筆討論跟內容」。

**Why:** 摘要的目的是接續（目標/決策/現況/待辦），時序流水無接續價值且擠掉真脈絡；只抓尾端對話會漏 session 前段的任務結構——session 常多線（實例：開場記憶治理 findings → 中段 tour_validate 修復 → 尾段 deep-work 對齊），尾端窗口只涵蓋最後一線。

**How to apply:** 任何摘要面（compact-prep/handoff/at-context）先重建整個 session 的任務骨架（TodoWrite/里程碑/待辦/懸掛），按脈絡維度組織非按時間序；verbatim 的選擇標準是相關性不是對話位置。

落地（AIR-35，09-07）：compact-prep skill 重寫——落檔對象從「最後 6 則 raw tail」改 `compact-context-<date>.md`（preserve-list 結構、素材掃全 session message.sequence）；CC hook 重定位＝機械 verbatim 復原層（腳本做不了脈絡壓縮，分層而非衝突；hook 注入不含 context 檔存在資訊＝讀檔提醒仍必要）；無 db fallback 同步去尾端窗口語義；skills/CLAUDE.md 索引同步。卡已 Done；commit 已落地（user 授權 post-build→commit，skill＋CLAUDE.md＋卡 finalization 三檔同 commit）。

相關：[[feedback_compact-user-judgment-memory-continuity]]
