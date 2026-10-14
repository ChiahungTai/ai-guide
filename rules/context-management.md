---
harness-scope: neutral
---

# Context 管理

## Session 管理

不同任務重置 context；廣度探索依 conversation-dispatch 判外派、獨立 context agent 回摘要；Writer/Reviewer 分離。同題連續糾正兩次失敗，先檢討並更換 prompt、重置 context。

**任務連續性**：user 新訊息預設 steer 現行任務；僅明示取消或新目標不相容才取代。compact／reset 不結束任務：續既有 scope，勿重做／重報。

**Session freshness**：session 內 rules/bundle 變動（redeploy、瘦身、刪除、反轉）後，下一個依賴它的 consequential action 前必重讀新版；刪除／反轉／衝突語義時，重讀無法清除舊文，須 reset/new session 並依 `skills/_common/task-recovery.md` 恢復 read-set。

## Durable checkpoint

關鍵發現／理由、排除路徑、下一步即時落盤，標「中間檢查點／最終」及未完；未驗收禁記完成。有卡→`task edit --append-notes`；原有 EP→append 進度；皆無→`.agent-tmp/session-journal.md`。長任務 spawn prompt 要求落盤。

唯讀／工單限制優先：禁自行寫 EP／卡／筆記，以進度訊息交有權者；checkpoint 不擴權。quota 中斷依 task-recovery 接續；journal 可記未定案工作，不觸發 memory。跨 session 收信須實質回覆：semantic ACK（manual paste 無 message_id 免）→completed（result_pointer＋evidence）；hook drain 不算——欄位依 handoff skill Phase 5。

## Memory 生命周期

寫 memory 前讀 memory-audit skill：無法一句話提煉或歸因未定禁寫，終態／進度流水不入池；`MEMORY.md` 是投影禁手寫，條目檔為寫入點、結案僅蒸餾終態 facts；六問／desc／讀取紀律依 skill。Spine＝`~/.agents/memory-spine/`（索引 `index.md`）。

## STATE.md

定位／寫入依 state-md-write 共用子範本；由 at/deep-work 觸發，Open failures 歸 kanban，不進 STATE。
