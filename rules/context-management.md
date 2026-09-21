---
harness-scope: neutral
---

# Context 管理

## Session 管理

不同任務重置 context（Claude: /clear）；大範圍探索用獨立 context agent 回摘要，Writer/Reviewer 分離。**會話查證外派**：廣度探索／多檔查證先判外派；唯讀查證腿可自主派——判準表載入 `skills/conversation-dispatch/SKILL.md`。同題連續糾正兩次仍失敗就換 prompt＋重置 context，超過兩次應檢討 prompt。

**Session freshness**：governing rules/bundle 在 session 中變更後（redeploy、slimming、刪除、政策反轉），下一個依賴該規則的 consequential action 前必 refresh context（重讀新版）；**涉及刪除/反轉/衝突語義時重讀不是充分條件**——舊文已在 context 不會因重讀消失，須 reset/new session＋恢復主題材料（resume read-set：卡/EP/notes→journal/compact-context→active .review→目標態報告→所需 skills）。

## 想法即時落盤（durable checkpoint）

context 揮發且 quota 可能突然耗盡。

- 關鍵發現/理由、排除路徑/原因、下一步意圖產生即記，附「中間檢查點／最終」＋尚待事項，防未驗收被當完成。
- 有 EP→append；有卡→`task edit --append-notes`；都無→`.agent-tmp/session-journal.md`。長任務 spawn prompt 注入落盤要求。
- **唯讀/工單限制優先**：不得自行寫 EP/卡/筆記；以進度訊息交有權寫入者。checkpoint 不擴張授權。
- quota 中斷接手先讀 journal/EP/卡 notes，按檔案現況續行；恢復順序／checkpoint 欄位單一源＝`skills/_common/task-recovery.md`，此處不重抄清單。
- journal 可記未定案工作，不觸發 memory；memory 須一句話測試＋確定才寫。

## STATE.md（Last session 觀察層）

定位/寫入見 state-md-write 共用子範本（Claude: `skills/_common/state-md-write.md`）；由 at/deep-work 觸發，Open failures 走 kanban、不進 STATE。

## Memory 生命周期規範（pointer）

寫前載 memory-audit skill「寫入端紀律/載體統一定義表」：一句話提煉不出或歸因未定就不寫；六問/rank/尺寸/body/desc 依 skill。**任務終態／進度流水不入池**（歸卡/EP/report；勿依賴 guard 攔）；**desc ≤100 chars、禁 hash/日期流水/session id**。MEMORY.md 是 frontmatter 投影禁手寫，條目檔是唯一寫入點；弧結案蒸餾終態 facts（結案兩步第三動）。
