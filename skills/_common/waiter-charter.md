# Waiter Charter — 通知與收取唯一契約（AIR-328）

> 觀察與投遞分界、通知能力選擇、無事件不注入回合的**唯一源**。消費者＝mail-watch、mail-handle、bridge-dispatch、agent-workflow、deep-work、autonomous-execution、model-routing。本檔只管「何時通知、用什麼能力通知」；各 domain 的觀察生命週期／游標／收取判斷**不複製進本檔**——責任分見下方責任表。衝突時：通知面以本檔為準，domain state 面以各 domain 檔為準。

## 責任表（唯一 owner——禁雙寫定義）

| 責任 | 唯一 owner |
|---|---|
| 通知能力選擇／無事件不注入回合 | 本檔 |
| collection-owner invariant／supervision 裁決 | [agent-workflow](../agent-workflow/SKILL.md)「Worker supervision contract」 |
| bridge receipt acceptance／transport 操作 | 已安裝 delegate plugin（`delegate:bridge-dispatch`／`delegate:delegate-run-output`——guide 只引用、不重定義） |
| mail 觀察／generation／游標與夜間上限 | [mail-watch](../mail-watch/SKILL.md) |
| mail read／待回覆／idempotent reply | [mail-handle](../mail-handle/SKILL.md) |
| 時間排程工作 | 各排程 skill 與 carrier——只服務 user 明示的時間工作 |

## 觀察與投遞分界

- **觀察（observer）**：watcher／waiter 對 domain state 的唯讀監看——只做事件存在性偵測。各 domain 保留自己的資料模型、退出碼與 stop 權威；本檔不合併 state、不重定義。
- **投遞（通知）**：把「有事件」送達消費回合的動作。通知是 **at-least-once hint**，不是 processing exactly-once 保證——收取端 re-query domain authoritative state、用 domain 身份／游標／冪等機制消化重放。**mail 觀察游標不是 processing dedupe key**；處置權威＝各 domain 既有 envelope／pinned bytes／jobId 身份面。
- **無事件不注入回合**：沒有事件，observer 留在程序內等待——禁以定時喚醒／recurring automation 製造空回合。user 明示的時間工作（含 recurring 報表）不受此限，走其排程 owner。

## 通知能力選擇（依序判定，當次事實優先）

1. **當次 exposed capability 優先**：以呼叫當下 carrier 實際暴露的通知路徑為準；歷史對照表（harness 通知能力表等）只是 prior，不覆蓋當次事實。
2. **有 confirmed event route 才用**：原生完成通知／事件通道須經證實（live trace 在案）才作投遞路徑；未驗證的 after-turn delivery 路徑標 `unverified-by-live-trace`，不得宣稱可用。
3. **否則活躍回合 bounded wait**：活躍回合內有界等待（**<=60s per call**——多用並行工作分攤輪次），到期內部 re-arm 續等，不外洩成假喚醒。
4. **無路徑→durable pending**：既無事件通道也無法活躍等待——留 durable pending receipt＋明確 resume 指令；不承諾無人值守推送，不以 cron／排程回合替代事件監聽。

exit code（含 143）與空輸出不作行為證據、不推固定收割政策——死因依 domain 流程查 authoritative evidence。

## watch intent priority（授權與撤銷）

- 最新明示 stop 優先；較新的明示 start 可覆蓋。
- 當次 explicit watch 或已核實的 prior running intent 延續；status 只讀、不授權亦不撤銷。
- marker 僅 opt-in advisory；absent 不抹除 explicit watch，malformed 使 autoarm 提示 fail-loud。
- watcher freshness 不證 callback 接線。
- Domain annex 只解釋各自 rearm/replay/stop 指向，不合併 state，也不增加 exactly-once 保證。

hook invariant 單一源＝`hooks/AGENTS.md`。

## 保留邊界（刪 mandatory 監控≠刪收取義務）

- **collection obligation 保留**：背景＋有限工 dispatch ⇒ register 義務（單一源＝[agent-workflow](../agent-workflow/SKILL.md)「Worker supervision contract」）——刪除 heartbeat mandate 不可把有界收取改成提早結束工作。
- **checkpoint／advisory／retry-safe fences 保留**：各 domain 既有機制不動。
- **服務合法時間工作或 child telemetry 的 heartbeat 工具保留**：user 明示時間工作的排程、child 端 heartbeat sidecar 不因本契約退役；liveness gate（zombie 防線）對任何在用的 heartbeat／automation 場景仍是強制。
