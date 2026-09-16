# implement 檢查點

已完成本項文件契約審查；未執行實作流程。

## IM1 — Important / confirmed：純 refactor 被等同小型，繞過最需要的架構內容同步

證據：skills/implement/SKILL.md:253 情境 C 無新 UC → 跳過結算；273 把「bug fix / 純 refactor = 情境 C」一併跳過 5b；但 5b 要處理模組/抽象/依賴設計文檔。metadata-sync:29、43 也只讓 A 觸發架構同步。

反例：跨多模組抽取共用介面，不增加 UC，屬純 refactor → C → 不更新 architecture.md/模組導航 → 下個 EP 從過時架構再生錯誤假設。

否證：泛用 instruction 同步原則存在，code-review 也有 ripple 提醒；但局部明確跳過使 builder 合規地略過；額外 review 提醒無法代替此處 owner。不是要求 refactor 新建 UC。

建議：UC 狀態變化與結構內容變化分開判定；無新 UC 僅跳 Capabilities 新增，結構信號仍觸發 5b；EP 自身完成/歸檔也不應綁新增 UC。

驗收：無新 UC 的跨模組 refactor 仍產相關架構/入口同步或具體 no-impact 證據；單檔無結構變化不強迫更新。

## IM2 — Important / confirmed：finalization 的 consent owner 自相矛盾

證據：implement:256 的 5a 說明以 working-tree 可逆編輯為由自主結算；metadata-sync:16、21 同意此分類，卻在 84-89 共用執行流程要求 build 內再次用戶確認。

反例：已批准 EP 的自主 build 到最後一段，呼叫 metadata-sync 後按其第 2 步停止等人；或按 implement 自主完成而違反 callee。兩条都不是幻覺，是文件各自要求。

建議：授權/可逆判定只有一個 authority；callee 回傳或執行結算項，不能重新發明「永久導航狀態」授權分類。具體 outward/commit gate 繼續交既有 consent rule。

驗收：已授權 EP 的本地 finalization 能走到底；未授權 commit 仍停。standalone 與 build 使用同一授權來源判斷。

## IM3 — Important / confirmed：同 worktree 的 parallel 路徑套用 isolated worktree 的 commit 前置

證據：階段 2 平行模式的 Pre-flight 寫「uncommitted changes 是 Agent dependency → 先 commit」，下一段卻指定 Agent 直接寫主 worktree；末尾禁止未經用戶指示 commit。agent-workflow 的該前置原因是隔離 worktree 只見 committed state。

反例：本 session 剛完成 shared interface、兩個 agent 都直接讀同一主 worktree，仍被要求 commit 才能派；並不需要的 git outward 動作變成執行依賴。

建議：先判 execution environment：shared tree 可直接讀 WIP；isolated tree 才處理 dependency transfer。轉移可用已授權 commit 或明確快照，不能把 commit 当所有 agent 的前置。

## 保留／觀察

docs mode 偵測仍以 .md/.py callable 描述，EP 已有 static HTML/互動 JS 規則，屬 adapter drift，合併到 PB1。scope 判斷、檔案數、UC 數、risk tier 分散各階段；不建議再加一個大總控 skill，只讓同一事實被明確傳遞。

loop 上限已明文禁止未收斂升級，不報「達三輪就自動 pass」。真正後續問題是 post-build 修改後是否重新讓證據/metadata 收斂，見後續 checkpoint。
