---
harness-scope: neutral
---

# Context 管理

## Session 管理

不同任務重置 context；大範圍探索用獨立 context agent 回摘要，Writer/Reviewer 分離；廣度探索／多檔查證先判外派（判準表＝conversation-dispatch skill，唯讀查證腿可自主派）。同題連續糾正兩次失敗就換 prompt＋重置 context，超過兩次先檢討 prompt。

**任務連續性（steering 語義）**：工作中 user 新訊息預設＝steering 現行任務非取代目標，唯明示取消或不相容新目標才替換；compact／context 重置不結束任務——跨 compact 視為單一邏輯鏈，不重做已完成工作、不重複已交付報告。

**Session freshness**：governing rules/bundle 在 session 中變更後（redeploy、slimming、刪除、政策反轉），下一個依賴該規則的 consequential action 前必 refresh context（重讀新版）；**刪除/反轉/衝突語義時重讀不充分**——舊文不會因重讀消失，須 reset/new session＋恢復主題材料（read-set 單一源＝`skills/_common/task-recovery.md`）。

## 想法即時落盤（durable checkpoint）

- 關鍵發現/理由、排除路徑/原因、下一步意圖產生即記，附「中間檢查點／最終」＋尚待事項，防未驗收被當完成。
- 有卡→`task edit --append-notes`；該弧原有 EP→併 append EP 進度節；都無→`.agent-tmp/session-journal.md`；長任務 spawn prompt 注入落盤要求。
- 唯讀/工單限制優先：不得自行寫 EP/卡/筆記，以進度訊息交有權寫入者；checkpoint 不擴張授權。
- quota 中斷接手按恢復順序續行（＝`skills/_common/task-recovery.md`）；journal 可記未定案工作，不觸發 memory。

**跨 session 回信**：收協作信（scbus／handoff）須實質回覆——semantic ACK（manual paste 無 message_id 免）後 completed（result_pointer＋evidence），hook drain 不算回；欄位＝handoff skill Phase 5。

## Memory 生命周期規範（pointer）

寫前載 memory-audit skill（寫入端紀律／載體統一定義表；讀取面＝消費端紀律節）：一句話提煉不出或歸因未定就不寫；任務終態／進度流水不入池（勿依賴 guard 攔）；desc/尺寸/六問依 skill。MEMORY.md 是投影禁手寫，條目檔唯一寫入點；弧結案蒸餾終態 facts。Spine（跨池）＝`~/.agents/memory-spine/`，索引＝`index.md`。

## STATE.md（Last session 觀察層）

定位/寫入見 state-md-write 共用子範本；由 at/deep-work 觸發，Open failures 走 kanban、不進 STATE。
