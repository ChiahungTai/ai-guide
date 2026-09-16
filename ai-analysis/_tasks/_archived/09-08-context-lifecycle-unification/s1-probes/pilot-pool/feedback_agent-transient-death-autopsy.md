---
name: agent-transient-death-autopsy
description: 背景 agent 死於帳號級 Model request failed——重試 prompt 燒入前任已知事實；驗屍＝mtime
  時間線（含 .py）＋半套偵測＋懸空掃；半套由主 session 收編
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_e905a8a2-8ca4-495c-8958-75095e04ab90
---

背景 agent 中途死於「Model request failed」＝**帳號級暫態**（多 agent 同窗同時長即證——對照 1302 帳號級框架），非任務/prompt 錯；單 agent 死≠任務死，先驗屍再重派。

**Why**：重派最大浪費＝重複前任的發現期；「像在 loop」常是分析期長讀取（UI 觀感反覆）——判據是**檔案系統副作用**（mtime，記得掃 `.py` 非只 `*.md`——前者曾漏看部署證據誤判零進度）非 agent 狀態；零寫入探測可能只是跑在寫入開始前。

**How to apply**：
1. 重試 prompt **燒入前任已知事實**（池/任務形態、已完成項、剩餘清單）＋防呆條款（工具連續失敗 3 次即停、回報已完成部分與中斷點）
2. 驗屍三步：mtime top 清單定時間線 → **半套偵測**（合併類手術：宿主已寫入但成員檔在→驗宿主吸收完整後刪成員收編）→ **懸空掃**（已刪名 `[[]]` 全池 rg 零命中）
3. 執行中 agent 可 SendMessage 注入結構事實導正（如單池 inode），不必等它死
4. **另一種「像在 loop」形態（B2 實證）**：subagent Edit 工具失效**降級為 no-op**（15+ 次靜默重試、Write 正常）——UI 觀感同 loop；判據同樣看副作用，「工具連續失敗 3 次即停」防呆條款正是為此（B2 靠它停手並完整回報）
5. **agent 成功回報的數字/宣稱同樣要驗**（B2 實證）：報 gate 18,500 實為 22,500（誤讀自算百分比）＋generator 落後一版未被發現——主 session 驗收必含回報值機械複核（gate 常數 rg、cmp、--check 實跑），agent 自述與人類自述同等對待（[[relay-claims-verify-current-state]] 同構）

實證：09-05 弧歸線 agent 死於最後一組合併手術中途，主 session 驗屍收編半套（刪 4 成員＋regen）即全數達標。

相關：[[memory-cc-alignment-diagnosis-0905]]、[[subagent-background-spawn]]
