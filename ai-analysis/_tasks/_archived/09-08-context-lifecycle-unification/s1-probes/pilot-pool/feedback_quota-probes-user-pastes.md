---
name: quota-probes-user-pastes
description: 額度敏感測試/probe（runtime 冒煙、A/B 測試）→ 給 user paste-ready 命令塊自己跑，AI 不派
  agent 代跑——額度主權在 user（09-08 兩次實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_e9d91786-3a08-477f-be85-b652ab85460c
---

user 09-08 三次實證的互動模式：AI 派 agent 跑 runtime 冒煙／測試 → user 叫停（「你將你要傳的給我，我自己貼」；codex P5「很傷額度你不要亂搞」）→ AI 給 paste-ready 命令塊（命令＋預期輸出＋異常判讀各一行）→ user 自跑貼回結果 → AI 計分落盤。第三實證＝codex P5 腿：AI 依額度考量取消後 user 仍自跑（自選 gpt-5.5/low）貼回計分——**取消的是「AI 代跑」，user 自己跑不受限**；AI 的角色＝出材料/prompt＋計分。

**Why**：額度主權在 user（codex 單發數萬 tokens 級、訂閱窗有限）；agent 代跑多包裝成本且 user 對花費無感。**How to apply**：會燒外部 runtime 額度的 probe/測試——先出 paste 塊等 user 貼回；零額度靜態檢查（版本/symlink/config 探測）AI 自己做，先做完靜態把要燒額度的項目收到最少再交 user。與 [[quota-failover-policy]]（dispatch 派工主軸）互補——本條只管測試/probe 面。觸發詞：冒煙、smoke、probe、額度、paste-ready、user 自跑。
