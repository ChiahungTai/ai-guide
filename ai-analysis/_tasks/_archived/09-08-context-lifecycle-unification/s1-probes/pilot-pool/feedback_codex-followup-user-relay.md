---
name: feedback_codex-followup-user-relay
description: 跨家族 review 迴路的 followup 驗收＝user 在 codex session 直跑（review context
  在那）——AI 派 codex-rescue 驗收/深審腿缺 context 會被停，敗因＝薄 prompt 繞過 work-order
  合約；user 當 dispatcher 的迴路收弧宣稱要區分「語義驗證」vs「編排自動化」
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f775f7f0-c166-4a08-a570-89f04c09d160
---

跨家族 review 迴路（codex 深審 → AI 修復 → followup 驗收）的驗收腿由 **user 在 codex session 直接跑**，不從 AI 側派 codex-rescue 轉發——review 的完整上下文（原報告＋judge 區段）住在 user 的 codex session；fresh agent 只能機械複述 gate 數字，無法判「修的是不是被擋的那件事」。09-06 實證：派出的 codex-rescue 驗收腿被 user 停掉（「你那個沒有context」），改為 user 直跑 $followup-review。

**Why**：followup 驗收的判準依賴 reviewer 的前因記憶（上輪裁決了什麼、為何擋）；缺 context 的驗收＝有表格沒判斷。深審/驗收腿自動派發的敗因根因＝**薄清單 prompt 繞過 work-order 合約**（context 不自足）——work-order review variant 正是把 context 組裝義務寫死的載體；派發形態現況（muse 腿 bridge 自動化已實戰／codex 腿 first-real-usage-pending）標在 state-review skill，下弧首跑逐節填滿工單實測。

**How to apply**：修復完成後不派驗收 agent——輸出**證據清單交 user relay**：逐 blocker 的修復落點（file＋測試名）＋總 gate 數字（pytest/ruff/checker），讓有 context 的 codex 直跑驗收。與 [[feedback_judge-review-stays-main-agent]] 同族：裁決與驗收都留在有 context 的主體，跨家族只用於審查側（[[feedback_dual-family-review-dispatch]]）。另：**user 當 dispatcher（手動轉發/觸發/帶 verdict）的迴路，收弧敘述只可宣稱方法論/語義被驗證，不得宣稱「完整迴路被跑過/自動化被驗證」**（09-06 user 勘正「這我自己參與，不是自動」）——兩者顯式分開，派發形態如實標註。
