# DutyMail Round-Trip — 信件生命週期一頁（AIR-254.3；裁決＝delegate-bridge `00-tasks/2026-10/10-04-dutymail/references/`）

> 給 ai-guide 側消費者（duty receive processor、handoff/delivery 腿、未來 send 遷移）的
> round-trip 契約摘要。mailroom 本體契約凍結在 dutymail CLI 3.1.0（M2）——本頁是消費側
> 導覽非第二權威；衝突時以 CLI／delivery EP 為準。

## 生命週期（八段）

```
send（intent＋reply_address＋envelope_id）
  → durable inbox（per-address queue；送達≠承接）
  → processor receive（holder bind→prepare 連續前綴）
  → transport ack（處置後才推 delivery cursor——不是 human seen/done）
  → semantic accept（對方 session 真正承接；handoff 面）
  → work（執行）
  → completed（result_pointer＋evidence）
  → user done（人類 ✓——SC 面權威）
```

- **send→ack 是 transport 面**（dutymail）；**accept→done 是語義／人類面**（消費側自持）。
  前段完成不宣稱後段——receipt/ack ≠ 對方承接（同 scbus 時代 queued-visible 語義）。

## 地址模型（address-model 裁定）

- **per-repo mailbox**：`<repo>-marshal`（本 repo＝`ai-guide-marshal`）＝repo 的長期責任入口
  （durable alias）。**holder**＝目前哪個 session 值星（epoch-fenced、可換代不搬信）——
  責任 identity 與執行者 identity 分開。章位分離（AIR-298）：消費章（prepare/ack）
  ＝值星 session 短持、durable INBOX 送達＋viewport 顯示無章可持（holderless
  常態）；ext 長持只及 escalation／人類 viewport 地址——正典＝
  `governance/scbus-address-ownership.md`「章位分離」。
- **門牌建立**：新 repo 加入 dutymail 時由該 repo 值星建 `<repo>-marshal` 門牌
  （`address create` 一次性；跨 repo 對址慣例）。
- **reply_address 慣例**：從 repo mailbox 發出者，body machine-header `reply_address` 一律
  ＝originating repo-marshal；只有明確 direct-session 對話才回 session address。
- **session address 殘餘角色＝direct channel**（指定特定 session／session-exit continuation）；
  不當 backlog 輪詢、死後不收新 primary routing（回 repo-marshal）。
- **不預設 card sub-address**；任務歸屬用 body machine-headers（`class`/`task`/`card`）＋
  `in_reply_to` thread 鍵。**label 是 display metadata 不是地址**（session label 歸
  SessionDiscovery seam，AIR-254.1/254.2）。

## Envelope（v2 凍結摘要）

`schema_version=2`／`message_id`（uuid4）／`envelope_id`（冪等鍵＝(address, envelope_id)）／`from{session_id,name,harness}`／
`to{address}`／`delivery{mode, intent: inform|solicit|receipt, ...}`／`created_at_us`／
`body`（UTF-8 ≤8192 bytes JSON；machine-headers：`class`、`task`/`card`、`reply_address`）／
`in_reply_to`（選配 thread 鍵）。

## 三線獨立（控制保證——永不合併）

| 線 | 權威 | 誰推進 |
|---|---|---|
| transport ack（delivery cursor） | dutymail store | duty receive processor（處置後） |
| human seen/done | SC workspaceState | 人類（✓/Undo）——transport 永不代推 |
| AI 提醒 baseline（holderless pending 計數） | session-local advisory（AIR-254.4；review 修復改 pendingCount 源）；session 級 mail-waiter（AIR-266——背景 shell 掛哨喚醒，推進自己的 events 觀察游標）與此並存、互不代理 | 各 session 自己（監看 hook） |

同一 address 任一時刻僅一個 consuming authority（epoch-fenced holder）；prepare 不消耗、
ack 是唯一 cursor 前進邊、只前進連續前綴；crash 重送不跳信。

## 值星收信處理器（ai-guide 側落點）

`hooks/duty_receive.py`（SessionStart＋UserPromptSubmit 邊界）→ `scripts/duty_receive.py`：
bind（consent CAS）→ prepare（bounded batch ≤8）→ triage（**default-deny**：class×action 表
〔`governance/dutymail-processor.toml`，user 可編輯〕＋intent∈{inform,receipt}＋可機械驗證才
auto；未知 class/solicit/人類信恆 surface）→ 處置（auto＝digest 吸收；surface＝一行摘要
——class 計數＋envelope_id 前 3、無 body，全文判讀面＝SC INBOX〔B′ 解凍 2026-10-06，
SC-305 上線——surface 項照樣計入 ack 前處置，差別只是不注入全文〕）→ ack（**絕不
flush-ack**——全批處置前不觸發）。auto 絕不宣稱 work accepted
（terminal status 只是 fact）。**v1 不主動送信**（send/replies＝outward，逐次 AUTH）。

## class 封閉詞彙（body machine-header——AIR-283）

body machine-header `class` 的 ai-guide 側封閉詞彙，現行六值逐字對齊
`governance/dutymail-processor.toml` `[[class_rule]]` 表：

| class | 語義（一句） | 分診現值 |
|---|---|---|
| `usage-liveness` | usage／存活類例行回報 | auto（inform） |
| `terminal-completion` | 委派工作的終態完成回報 | auto（inform） |
| `receipt` | 運輸回執（配 `in_reply_to`／`task`/`card` 冪等鍵） | auto（receipt） |
| `handoff` | 交接求承接（solicit 形） | surface（恆人工） |
| `patrol` | 巡檢／催辦 | surface（恆人工） |
| `work-order` | 工單／任務指派 | surface（恆人工） |

**分權聲明**：本檔承載**詞彙與語義**；**執行底線承載在 code**——
`scripts/duty_receive.py`（klass 判定＋ALWAYS_SURFACE 恆人工名單）與
`governance/dutymail-processor.toml`（class×action 政策表，user 可編輯）：
solicit 恆 surface、未列 class 恆 surface、handoff／patrol／work-order 恆人工
不可經表放寬。發送端須輸出本表詞彙——新值未入表＝不獲 auto、落人工審
（surface；缺 class 鍵者分類前提不成立、顯示 unknown），default-deny 使枚舉
可安全滯後。新值流程＝toml 加 row＋本表補行。本表是 **ai-guide 側詞彙非跨
repo 正典**——晉升共用 schema 須 conventions.md amendment（msg_type 先例同形）。

## 回信發現與收信面

- **回信發現正典**：等回信/查回信恆用 scoped 形 `dutymail replies --envelope-id <parent>
  --address <自己門牌>`——已知回信回到哪個 mailbox 就 scope 那個 mailbox。**跨地址禁用
  unscoped**：unscoped 從 parent 信出現過的地址推導 scope——跨 repo 往返中 parent 常在
  對方信箱，回信回到自己信箱，unscoped 合法地查錯邊回空。**回空不蘊含語義**（不等於
  未寄/未 ack/不存在）——它只證明「此查詢形下未見」。等回信推進鏈：`wait --address <self>`
  （bounded；wake 是提示、requery 才是 correctness）→醒後 `receive status`→`prepare`→
  `replies`。unscoped 完整語義以 bridge 為準（delegate-bridge repo dutymail CLI 源碼＋
  docs——本節不複製定義）。

| face | 正確用途 | 不能拿來推什麼 |
|---|---|---|
| wait | 等自己門牌新事件（bounded） | 有事件≠已讀到信件內容 |
| events | transition timeline／audit 流 | **無 body——不是讀信面**；不能判信內容 |
| receive status | pendingCount／cursor 投影 | 無 body，不能判信內容 |
| receive prepare | 讀信面（canonical envelope＋body；reserve 不 consume） | prepare≠ack |
| replies（scoped） | 回信執行緒視圖 | 未消費回信也查得到——查不到≠未寄 |

- **查證一行**：查詢回空只授權「此查詢形下未見」；對外做根因陳述前須源碼或實測（真相源：
  delegate-bridge repo `dutymail/crates/` 源碼與 `00-tasks/2026-10/10-04-dutymail/` 契約
  文檔＋CLI `--help`——實證：2026-10-06 unscoped 回空被誤歸因「只索引已 ack」，源碼證偽）。
- **對外信慣例**：對外信（通知/歸因/更正）中的因果或機制斷言須攜證據基（查詢形/源碼行/
  實測輸出），攜不了自標「未查證推測」；更正信顯式 supersede——`in_reply_to` 指原信＋一句
  推翻證據＋新結論，禁兩信互不相認。

## 審計錨正典（兩錨閉環——AIR-283 遷入；本節為 ai-guide 側正典）

> **身位聲明**：審計錨條款正典＝本檔（G5 節同形）——scbus→dutymail 遷移後，
> conventions.md 節一「對照即審計錨條款」（SC 案例③收束）與 evidence 指向條款
> （SC 案例②）遷入本節、節一已凍結。本檔開頭「衝突時以 CLI／delivery EP 為準」
> 適用**機制行為面**；**審計判準（完成認定）以本節為準**——CLI 文檔不承載
> ai-guide 側完成認定，防「衝突以 CLI 為準」反噬審計錨效力。

transport receipt（機器面，delivery 保證）≠ semantic reply（消費面，語義保證），
兩面禁互升格。任何「已送達／已同意／已完成」宣稱須能**同時**指出兩錨；僅有其一
＝未閉環，禁記完成：

- **transport receipt 錨**（鍵＝`envelope_id`）＝`dutymail send` acceptance stdout
  三鍵：`envelopeId`＋`acceptanceSeq`＋`envelopeSha256`。append-only `receipts`
  軸（holder 逐條 append 的運輸觀察）**非閉環必要條件**——send 不自動落軸，
  `receipts list --address <alias>` 回空≠未寄。
- **semantic reply 錨**（correlation 鍵＝`in_reply_to` 對 parent `envelope_id`）＝
  scoped 查得的 reply（`dutymail replies --envelope-id <parent> --address <自己門牌>`）；
  完成閉環的 reply 須 `reply_type=completed`＋`result_pointer`＋`evidence`
  （承接中間態＝`accept`；`declined`＝禁原樣重發、`needs-info`＝補件後同
  correlation 重發）。

**evidence 指向條款**（遷自 conventions 節一 SC 案例②；原主詞「ACK 與 receipt 的文字」——receipt 面在 dutymail 由 transport acceptance 三鍵機械承載〔含 envelopeSha256〕，自由文字面僅存 ACK/回信）：ACK 與回信文字須帶 evidence 指向（path／hash／可機驗指針），
禁權威斷言——「已完成」是宣稱非證據，「result 在 `<path>` hash=`<h>`」是。訊息
文案禁斷言權威：transport consent ≠ mutation authority，送達≠取得寫入權。

## 閒置語義

無 duty session＝零查詢零輸出（註冊面即邊界；無背景輪詢/watcher）。SC badge 的未處理數
源＝dutymail projection（undone 數），不是 AI 提醒 baseline（AIR-254.4 降級）。monitor 的
holderless advisory＝常態語義（B′ 解凍 2026-10-06，SC-305 上線：pending 在 INBOX 等人
判讀——workspace 信終點＝durable INBOX；`dutymail receive status` 可查，非異常窗口）。

## zero-pending gate 語義（G5 正典——本檔為 ai-guide 側定義源）

bridge G5/TC-R5 zero-pending gate＝archive bytes 保留＋零 unowned/unexplained pending
obligations；archived＝已對帳 records，非「清檔歸零」——ai-guide 側文檔禁以 zero-pending
語義宣稱檔案歸零（monitor advisory baseline 歸零是 session-local 另層語義，兩者不可混用）。
