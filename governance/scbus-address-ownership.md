# scbus 位址持有模型——pin 制租約（operator 正典）

> 單一源：sc-router protocol（凍結事實）＋southchariot SC-254/271/273 實作＋三方討論
> R1/R2 裁定（AIR-210）。AIR-168 契約（scbus-address-contract.md）為歷史提案；
> consumer 操作語義以本檔為準。

## 心智模型（一句話）

> 位址是一個 single-holder **routing pin**：pin 給身分、不給視窗；活 holder 的租約
> operator 可視為**不到期**；死後 24h 惰性 expiry 是自動拔 pin 的 crash backstop；
> 切換平常靠 acquire（同身分＝冪等常態），越過仍活的 pin 才需要 force-reclaim。

## 身分粒度——pin 給誰

- pin 綁複合鍵 `(holder_harness, holder_session_id)`，不是 VS Code window/process。
- **ext 面**：`scbus-ext-<sha256(realpath(workspace_root))[:16]>` per-workspace 決定論
  ——同 workspace 重啟/多開視窗＝**同一個 pin**（協議凍結慣例：同 repo 多窗 upsert
  同一 identity、共享 mailbox、at-most-one-winner 擇一收信）。
- **CLI 面**：pin 給個別 session；換 session＝換身分。

## 「不到期」的精確語義（分面）

- 活著就永續：holder 定期 renew，lease 恆 now+24h（ext 45s tick；renew 不 bump
  generation、不是 ownership transition）。**renew-failed log 是 pin 鬆動預警，
  不可忽視**；renew 成功靜默是約定。
- 死後 24h 自動拔 pin（惰性判定、無 reaper）——分面按**接手者身分與 binding 狀態**：
  - ext 位址（realpath 不變前提下恆同身分）：重開視窗恆**秒接**——24h 內＝
    live same-holder 冪等 renew（generation 不變）；逾 24h＝binding 已過期，
    plain acquire 仍立即接管但 **generation+1**（新 ownership 邊界，舊
    generation 受 fencing）。24h 對 ext 通常不造成 availability wait，但
    generation 語義有別（ack CAS／fencing 讀者注意）。
  - CLI 位址換 session＝異身分 → 撞活 pin 才有 force-reclaim／等 24h 之別。

## 切換動詞（三態）

| 情境 | 動詞 | generation |
|---|---|---|
| 同身分（同 workspace ext）＋binding live | plain `acquire`（renew 冪等常態，含重啟） | 不變 |
| 同身分＋binding 已過期（逾 24h 重開） | plain `acquire`（立即接管） | +1 |
| 異身分＋死 pin／無 pin | plain `acquire` | +1 |
| 異身分＋活 pin（明確要求換手） | `force-reclaim` | +1 |
| 活 holder 可協作交接 | `transfer` | +1 |

## 紅線

- **pin 是 routing ownership，不是 authN**：scbus identity 是 claimed identity，
  單一 user-home trust boundary 內可 spoof——禁當安全邊界設計。
- ack 權綁 live lease＋holder 複合鍵（防 zombie ack）；duty 轉送 B1 gate 讀
  leaseHeld（single-holder 路由）；`name_conflict`＝異身分搶活 pin 的 fail-loud
  正確行為（與視窗數無關）。
- release／transfer／force-reclaim／過期後 acquire 皆 ownership 邊界——
  舊 generation 受 fencing（renew/drain/ack 被擋）。
- queue 信過期照送（park 30 天 body 保留）；steer/notify 過期 fail-loud，
  fallback 僅限 envelope 明示——無靜默降級。

## CLI 慣例（惰性 recipe）

- 預設走 raw session-id direct routing（`send --to <session_id>`），不維護
  logical-address lease。
- 要收某位址的信才 `scbus acquire`（過期 binding 即重綁）；撞 `name_conflict`
  ＝異身分搶活 pin，二選一：`force-reclaim`（僅當確認活 pin 應讓位——會 bump
  generation＋產生審計事件＋搶走路由）或等 24h 惰性過期。
- **禁教 renew**：renew 綁 holder 身分，新 session 執行必失敗（identity mismatch）。
- 只有明確 address-consumer UC 的 owner 才 claim/renew；一般 session workflow
  不加入 renew chore。

## 證據錨點

southchariot：`src/scbus/controlChannel.ts:75-94`（身分決定論）、`:938-941`（B1）、
`src/scbus/client.ts:1029-1046`（ack holder-limit——ScbusAckCall deps）、
`src/scbus/controlChannel.ts:1057-1068`（name_conflict warn-once）、
`src/scbus/controlChannel.ts:1077-1101`（renewIfHeld＋crash backstop）；`src/extension.ts:3619-3631`（ownSid
register→acquireOnce）。
sc-router：`docs/protocol.md:828-867`（binding/lease/acquire 三態）、`:1720-1725`
（同 repo 多窗凍結慣例）、`:665-673`（claimed identity 非 authN）。
