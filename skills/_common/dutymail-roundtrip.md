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
  責任 identity 與執行者 identity 分開。
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
| AI 提醒 baseline（holderless pending 計數） | session-local advisory（AIR-254.4；review 修復改 pendingCount 源） | 各 session 自己（監看 hook） |

同一 address 任一時刻僅一個 consuming authority（epoch-fenced holder）；prepare 不消耗、
ack 是唯一 cursor 前進邊、只前進連續前綴；crash 重送不跳信。

## 值星收信處理器（ai-guide 側落點）

`hooks/duty_receive.py`（SessionStart＋UserPromptSubmit 邊界）→ `scripts/duty_receive.py`：
bind（consent CAS）→ prepare（bounded batch ≤8）→ triage（**default-deny**：class×action 表
〔`governance/dutymail-processor.toml`，user 可編輯〕＋intent∈{inform,receipt}＋可機械驗證才
auto；未知 class/solicit/人類信恆 surface）→ 處置（auto＝digest 吸收；surface＝呈報值星，
全文≤3 筆）→ ack（**絕不 flush-ack**——全批處置前不觸發）。auto 絕不宣稱 work accepted
（terminal status 只是 fact）。**v1 不主動送信**（send/replies＝outward，逐次 AUTH）。

## 閒置語義

無 duty session＝零查詢零輸出（註冊面即邊界；無背景輪詢/watcher）。SC badge 的未處理數
源＝dutymail projection（undone 數），不是 AI 提醒 baseline（AIR-254.4 降級）。
