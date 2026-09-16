# Task Recovery — 跨入口恢復順序與 checkpoint 欄位（共用片段）

> 共享片段——compact-prep／at／handoff／autonomous-execution（Session 級 Recovery）與 [rules/context-management](../../rules/context-management.md) 引用此處，恢復清單不在各入口各自維護。**非 skill、非狀態檔、非自動化引擎**：本檔只持有「中斷前寫什麼」（checkpoint 必要欄位）與「接手後按什麼序核對」（恢復順序）。不新增 active-pointer 檔／registry／跨任務索引——active pointer 就是既有 EP 進度節的 checkpoint 指針（無 EP 用既有 journal／user 指定 report）。

## 寫入端：checkpoint 必要欄位

中斷／離開前把工程狀態落進**既有 durable 載體**，落點優先序：

1. 有 EP → 更新 EP 進度節（含本弧 checkpoint 指針）＋必要 evidence 檔
2. 無 EP → 既有 `.agent-tmp/session-journal.md`
3. user 指定 report → 該 report
4. compact-context 等交接包只**引用** durable owner、不重抄內容——需逐字保存的錯誤／findings 原文例外

必要欄位（恢復端要能從檔案找到；缺一即 checkpoint 未就緒）：

| 欄位 | 問的是 |
|---|---|
| 目標與成功條件 | 這弧做什麼、怎樣算成 |
| 現行階段 | 做到哪一段 |
| scope/cwd/baseline＋本弧 dirty | 在哪個 tree、基準與本弧變更（機械比對鍵） |
| 已決策理由及排除方案 | 為何選 X 不選 Y、哪些路徑已排除 |
| 已驗/未驗證據 | 實跑命令與結果指針、尚未驗證項 |
| open findings | 未裁決／未閉合的審查發現 |
| 背景 jobId/owner/收法 | 未收回委派如何認領與收取（running/unknown/terminal） |
| 授權來源與範圍指針 | AUTH 依據與邊界（引用 governing consent） |
| 下一個可執行 action | 接手第一動 |
| read-set 與未恢復範圍 | 接手要讀什麼、哪些範圍未涵蓋 |

**已有欄位不重抄**——既有 owner 持有者只留指針：成功條件→EP／卡 AC；baseline/dirty→[work-order](work-order.md) §3、[workflow-review-pattern](workflow-review-pattern.md) header identity；實跑與段落結果→EP 進度節＋evidence 檔；findings→`.review/<branch>.md`／EP review 區段；job 收法→[work-order](work-order.md) §10 附加＋model-routing「完成回報收法」；授權→[outward-action-consent](../../rules/outward-action-consent.md) AUTH line。

**memory 整理在落盤之後**：工程狀態落盤成功後才做可選 memory 候選整理。gate 故障／無授權／無寫權都不能阻止保存工程狀態，也不能跳過後宣稱「已蒸餾」——未蒸餾就記交接待辦（owner／待辦承載）。

## 恢復順序（接手端）

1. **定位指定任務**——以 user 指定／卡／工單為準；**不用「最新 session」猜身份**（同 worktree 並行 session 會撈錯）
2. **核對當前實物**——git HEAD/dirty、EP 進度、卡狀態、active job（機械核對檔案／hash／job 狀態）。段落 receipt 在場時跑 `scripts/segment_receipt.py --verify <receipt>`（FRESH＝EP 進度判斷欄仍有效；DRIFTED＝以實物 re-derive，receipt 是 validity token 非第二真相源；跨 repo 消費以 ai-guide checkout 絕對路徑呼叫）
3. **active findings＋最新證據**——`.review`／EP review 區段、實跑結果指針
4. **checkpoint 理由及未決**——為何轉向、哪些未決；checkpoint 舊 hash 只是比對依據，**不是當前 HEAD 必須回到的 target**
5. **按需 STATE/memory**——STATE 是觀察層，補「為什麼」不覆蓋完成度；完成度以實物核對為準
6. **所需新鮮 guidance**——governing rules/政策 session 中變更過，依 freshness 條款重載／fresh context；舊 context 不作新政策證明
7. **確認下一動作前置**——語義核對下一動是否符合仍有效的目標與決策，前置成立才動手

**恢復驗證＝機械核對＋語義核對**，只重述摘要不算恢復驗證。漂移只擋受影響行動——能獨立進行的工作照做，不因單點漂移整弧停擺。

**缺 transcript**：只聲明可見範圍（檔案＋實物），標明未恢復範圍，不要求無限考古。**背景 job timeout**：先辨識 running/unknown/terminal，保留所有未收回工作，照既有 bridge 收法——禁把 timeout 當失敗重派同一工作。

## 不變項（寫入與恢復皆適用）

- 恢復不得跨 task/WT 寫入；不得把推測升級成完成；不得重派仍活的 writer；checkpoint 不擴張授權
- 不以模型切換自動 compact、不設不可取得的 token threshold、不依賴 SessionEnd——無 hook 也能執行（全流程靠檔案與機械命令）
- 未定案推論可存 checkpoint，不能寫成 memory fact
