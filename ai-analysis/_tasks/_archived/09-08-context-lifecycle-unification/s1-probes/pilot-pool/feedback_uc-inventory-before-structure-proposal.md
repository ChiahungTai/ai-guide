---
name: uc-inventory-before-structure-proposal
description: 結構提案與架構討論皆 UC-first——先盤工作流/讀者與 repo 先例再提方案；論證用 use case 角度＋clean code 具名原則，勿自創縮寫
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 09-05 糾正我對 agents registry 設計債的處理順序：我完成三視角診斷後直接提「修法方向＋決策點」，user 退回——「**你應該先整理目前工作流程，illustrate 整個工作流程的工作，然後標記哪些適合 agent 做，需不需要特化。這才是uc繼續**」。

**Why:** 結構提案跳過了方向驗證層（B 軸）——UC-driven 的順序是「先盤點真實工作、再判斷哪些該 agent 化、最後才導出結構結論」；不盤點就提案結構，等於用結構直覺取代 use case 驅動，且盤點本身可能推翻或重塑提案（本次實證：盤點結果是 role 集合不動、題目收斂為部署面 only——提案被驗證但範圍被收窄）。

**How to apply:** 對 agent registry／流程／結構類重構提案，先渲染**工作盤點 viewport**（console 即可）：全生命週期逐項工作 × 當前執行主體 × agent 適性 × 特化裁決，讓 user 判讀方向後才提結構。適性四判準：可凍結（目標/範圍/驗收能事先寫成客觀條款）、單一 writer、紀律密集（有明確規則不靠 taste）、跨弧重複（高頻才值得 registry 名，一次性歸泛用 agent＋prompt）；反判準＝判斷密集（意圖對齊/裁決/編排）永遠主 session。實例與結論詳 [[project-agents-registry-split-design]]（AIR-29 候選段）。

**第二實例（09-06，agents/ 去重提案）**：建議砍 agents/AGENTS.md §dispatch face 與 model-routing skill 的重複段（提 pointer 方案），user 追問「md 不是可以用引用？@？_common 我之前怎樣用的？deploy 怎樣處理？你有參考嗎？」——提案時未引用既有機制先例。補盤點三機制：①`@` transclusion 僅 Claude CLAUDE.md 啟動展開，AGENTS.md（ZCode/OpenCode/Codex）明文不展開＋deploy_agents.py purity lint（at-transclusion）禁；②`_common/`＝markdown link＋AI 按需 Read（非展開）；③deploy＝建置期拼接 bundle。**Why 補充**：補證後原建議恰好被驗證（pointer＝_common 模式等價），但順序錯了——選項空間應由 repo 先例推出、非提完再補證。**How 補充**：去重/引用類提案，先把候選機制（@／link／共享檔／建置期合併）對 repo 先例盤一遍再提方案；通用 markdown 知識（「md 可以 @」）在自家 repo 治理下不可假設。

**第三實例（09-06 續，討論框架被退）**：先例盤點後我以「消費語境錯位 vs 在地完整性」二選一 fork 收尾，user 退回——「**聽不懂，你用 use cases 角度思考，還有 clean code/arch 角度思考後再跟我討論**」。重推方法：①**讀者盤點表**（A registry 維護者／B 任務派發者／C muse 委派者——各自場景×到達路徑×需要哪些段），結論收斂成一句白話「該段三個讀者沒有一個為它而來」；②clean code 具名三訊號：SRP 雙改變理由（registry 檔因收法演進而變動）、DRY 帳單在演化時支付（快速演進域×雙拷貝＝分叉是時間問題）、無讀者的耦合＝純成本。**Why**：自創壓縮術語（「消費語境錯位」）把分析結論當分歧軸丟給 user，等於要 user 腦補論證；use case 讀者盤點才是 user 要的推理骨架。**How**：內容放置/去重決策一律用「讀者盤點（誰、何時、經什麼入口、要哪段）＋具名原則（SRP/DRY/coupling/YAGNI）」論證。方法紅利：rg 查證發現三態判定表＝repo 唯一份（非重複、是放錯家）——**刪「重複」內容前必查它真的在他處存在**（刪 vs 搬的鑑別）。

**方法補注（同日，flag 形態表裁量翻盤）**：宣稱為「摘要/mirror」的內容，裁量前必**並排權威原表驗差異度**——本例「只寫形態」表實為同表 trim 指令前綴（假摘要真拷貝），並排後裁量從「留」翻「收」；真摘要是不同抽象高度（一行句），不是同表少幾個字。
