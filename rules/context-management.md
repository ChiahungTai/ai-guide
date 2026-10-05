---
harness-scope: neutral
---

# Context 管理

## Session 管理

不同任務重置 context；大範圍探索用獨立 context agent 回摘要，Writer/Reviewer 分離。**會話查證外派**：廣度探索／多檔查證先判外派；唯讀查證腿可自主派——判準表載入 `skills/conversation-dispatch/SKILL.md`。同題連續糾正兩次仍失敗就換 prompt＋重置 context，超過兩次應檢討 prompt。

**任務連續性（steering 語義）**：工作中 user 新訊息預設＝steering 現行任務非取代目標，唯明示取消或不相容新目標才替換；compact／context 重置不結束任務——跨 compact 視為單一邏輯鏈，不重做已完成工作、不重複已交付報告。

**Session freshness**：governing rules/bundle 在 session 中變更後（redeploy、slimming、刪除、政策反轉），下一個依賴該規則的 consequential action 前必 refresh context（重讀新版）；**刪除/反轉/衝突語義時重讀不充分**——舊文不會因重讀消失，須 reset/new session＋恢復主題材料（read-set 單一源＝`skills/_common/task-recovery.md`）。

**跨 session 回信紀律**：收協作信（scbus／handoff）須實質回覆——先 semantic ACK（reply_type＋in_reply_to；manual paste 無 message_id 則免）再 completed（result_pointer＋evidence）；hook 自動 drain／recv 消化不等於回（真實案例：他端 hook 已收信、漏實質回覆）。閉環欄位照 handoff skill Phase 5 四段表。

## 想法即時落盤（durable checkpoint）

- 關鍵發現/理由、排除路徑/原因、下一步意圖產生即記，附「中間檢查點／最終」＋尚待事項，防未驗收被當完成。
- 有卡→`task edit --append-notes`；該弧原有 EP→併 append EP 進度節；都無→`.agent-tmp/session-journal.md`。長任務 spawn prompt 注入落盤要求。
- **唯讀/工單限制優先**：不得自行寫 EP/卡/筆記；以進度訊息交有權寫入者。checkpoint 不擴張授權。
- quota 中斷接手先讀卡 notes／EP（該弧原有 EP 時）／journal，按檔案現況續行；恢復順序／checkpoint 欄位單一源＝`skills/_common/task-recovery.md`。
- journal 可記未定案工作，不觸發 memory；memory 須一句話測試＋確定才寫。

## STATE.md（Last session 觀察層）

定位/寫入見 state-md-write 共用子範本；由 at/deep-work 觸發，Open failures 走 kanban、不進 STATE。

## Memory 生命周期規範（pointer）

寫前載 memory-audit skill「寫入端紀律/載體統一定義表」：一句話提煉不出或歸因未定就不寫；六問/rank/尺寸/body/desc 依 skill。讀取面消費紀律＝同 skill「消費端紀律」節。**任務終態／進度流水不入池**（歸卡/EP/report；勿依賴 guard 攔）；**desc ≤100 chars、禁 hash/日期流水/session id**。MEMORY.md 是 frontmatter 投影禁手寫，條目檔是唯一寫入點；弧結案蒸餾終態 facts（結案兩步第三動）。

Spine（跨池）＝`~/.agents/memory-spine/`，條目索引＝`index.md`。
