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

## Repo well-known address 與收件責任

> 收件面 convention 單一源（AIR-225，2026-10-01 marshal 三封漏接事故收斂；
> 雙腿 verdict `.agent-tmp/addr-unify/`）。其他文檔只放 pointer，不重刻本節
> ——authoring source＝本節本體，無獨立 consumer 檔；consumer 接線＝值星
> session 開場讀本節，STATE.md 1001 起載指針。
> 通用 template：所有 repo 一體適用；他 repo 命名（各 `<repo>-marshal`）已符合，
> convention 采納隨各自觸點跟進——不發動跨 repo 搬遷，採納細節由各 repo 自主。

### Repo address cardinality（一 repo 一門牌）

- 每個 repo 預設**恰一個** well-known durable inbound address，命名 `<repo>-marshal`
  （ai-guide 即 `ai-guide-marshal`，由 workspace ext per-workspace 決定論身分長持）。
- 第二位址例外 predicate：必須證明**獨立 consumer UC**才可建立；「系統信／工作信」
  「值星／marshal」等訊息分類或命名差異不構成 UC——訊息種類用 envelope
  `mode`（steer/queue/notify）＋`intent`（inform/solicit/receipt）表達，不以多位址分類。

### Sender selection（二分 oracle）

| 訊息要給誰 | 動詞 |
|---|---|
| repo/workspace 承接、須跨 session 存活的責任信 | `send --to-address <repo>-marshal` |
| 已知 live session 的即時對話 | `send --to <session_id>` |

同信多址雙寄製造雙 envelope＋ack 歧義，禁。

### Holder ≠ monitor

- **holder** 負責 routing lease 與 ack（claim/acquire/renew/release/ack 的主體）；
  **monitor** 只負責發現新到 delivery event——不同角色，monitor 不需要 holder 身分。

#### 架構 invariant（AIR-233——三軸互不代理）

> Canonical address 只有一個 delivery lifecycle；**receipt timeline 是
> delivery-event authority**（sc-router `address receipts` 唯讀 face——accepted
> 為查詢軸，與 ack 狀態解耦）。三軸各持自己的 cursor/state、互不拿彼此的
> state 當 proxy：**transport ack**（`acked_at`，holder 面送達確認——ack ≠ 已讀
> ≠ 已處理）、**human seen/done**（mailbox unseen→seen→done，SC UI human
> lifecycle）、**AI notification**（consumer-owned `emitted_cursor`，語義＝
> reminder emitted——非 AI seen、非 processed，advisory badge 非責任結清點）。
> 任何一方不得用 mailbox `new/cur` 或 transport ack 代理另一方的閱讀／處理狀態；
> consumer 直讀 maildir（`addresses/*/new/`、`receipts/` 檔案面）＝downstream
> 重做 sc-router domain logic，已由 face 取代（AIR-225.1 iteration 2 的
> interim workaround superseded），非支援監看路徑。

- 值星/Marshal session 的收件義務＝**知會新到 delivery events＋掃自己的
  session inbox**，兩面都免 holder 身分：canonical 面由 receipt-timeline hook
  自動知會（下條）；人工 point-in-time 輪詢＝`dutymail receive status`
  （scbus 時代 address pending badge 已隨換代退役——現行面見下條 monitor；
  歷史實證錨 AIR-168 驗收③保留標註）。**已知崩潰史（SCR-8，scbus 時代）**：
  address row 在而磁上 `new/` 目錄缺時，pending badge 視圖曾整命令崩
  （raw FileNotFoundError）；上游已修（sc-router scr-8——缺目錄讀面 fail-soft
  回空清單＋pending_note，修復入 v0.2.0），本機已升級（歷史事實；maildir 直讀
  降級路徑隨 invariant 條退役）。scbus 時代 session inbox 輪詢已退役——現行
  收信處理面＝duty_receive 處理器＋monitor advisory（下條）。session 換手
  不動搖 ownership。因監控需求 acquire/renew/force-reclaim canonical address
  皆違反本節。
- **interaction-boundary hook monitor（AIR-225.1 建面；AIR-233 scbus receipts
  消費面從未落地——AIR-254.4 降級重寫為 dutymail 面；review 修復重設計為
  holderless pending 語義）**：
  `hooks/duty_mailbox_monitor.py`（zcode UserPromptSubmit＋SessionStart 各
  獨立 sync 條目，註冊單一源＝governance registrations；AIR-225.1/233 舊
  提醒 hook 檔隨重寫退役）以 dutymail 唯讀面為資料
  源——`holder status`（live 偵測）＋`receive status`（pendingCount 現值）
  ；events face 消費（accepted 事件史計數）已退役——事件史不因 ack 消失
  ，對他方 holding 門牌會誤報且與 duty_receive 衝突行語義矛盾。決策表
  （per address）：`holder status` live=true（本 session hold——
  duty-receive per-session state epoch==status.epoch，或他方 live）→ 靜默
  （covered：處理面由 holder 承擔；收信處理面單一源＝duty_receive 處理器
  ；monitor ≠ holder——禁 bind/prepare/ack，三軸不互代理）＋baseline 歸零
  （session-local advisory baseline，非遷移 zero-pending gate）
  ；live=false（holderless——B′ 常態：pending 在 INBOX 等人判讀）→
  `receive status` pendingCount >0 且 ≠ baseline 出一行 advisory
  （「holderless pending N 封（pending 在 INBOX 等人判讀——B′：
  workspace 信終點＝durable INBOX；dutymail receive status 可查）」
  ——「本 session 提醒到哪」語義，絕不宣稱 global 狀態、不觸 human
  seen/done）；>0 且 ==baseline 靜默（防每 prompt 轟炸）；==0 靜默＋
  baseline 歸零（session-local advisory baseline，非遷移 zero-pending gate）。holderless＝常態（B′ 語義——AIR-258 解凍；2026-10-06
  SC-305 上線後 pending 落 durable INBOX 等人判讀，非 B′ 前 duty-active
  異常窗口語義；monitor 只提醒不代開 duty session）。baseline＝
  `${XDG_STATE_HOME:-~/.local/state}/ai-guide/duty-monitor/
  <safe_session_id>.json`（session-local——兩 session baseline 互不干擾
  ；按 address 記 `last_pending`；0600 atomic 寫、
  **advance-after-emit**——stdout 寫出成功後才推進，寫失敗寧可下次重複
  提醒；閒置完全安靜＝註冊面即邊界，無背景迴圈/watcher）。**舊全域游標檔
  `scbus-address-monitor.json` 隨本重寫停用——不刪不改零讀取（留歷史
  對帳）**。**monitor eligibility gate**：session cwd 在 script 所在 repo
  內才查詢／提醒／推進（user-level 註冊跨專案觸發——防錯誤 session 吃掉
  baseline；fail-closed——cwd 缺席亦不推進）。face 失敗 hook 呈 fail-soft
  （單門牌 stderr 註記續跑其他、零該門牌 stdout、exit 0）；人工輪詢
  （`dutymail receive status`）保留為 point-in-time fallback。
- 回歸鎖：情境 own session=0、retired address=0、canonical marshal>0 仍必須視為
  actionable（2026-10-01 事故形態——值星只掃 primary＋自己而漏 marshal）。
- ack 綁 live lease＋holder 複合鍵：跨身分 session 面 ack 他人位址必被拒
  （holder-operation gap）。lease 已過期時，同 trust boundary 的 operator 走
  **ext operator path**（以 ext holder 複合鍵執行 CLI——2026-10-01 migration
  三封 ack 實證形態）plain `acquire`（expired binding，generation+1）恢復 lease
  後即可 ack——非 transfer、非 force-reclaim，pin 仍屬原 holder 身分；
  **禁 session 面冒身 acquire**（identity 非 authN、trust boundary 內可 spoof
  是事實描述非授權，見紅線節——規範禁令不因技術可行而撤）。
- 閉環驅動路徑：monitor 發現 marshal 新到收件紀錄（receipt timeline；fallback
  ＝pending 快照 >0）後，正常＝**holder ext 自收**
  （workspace 重開窗即同身分 renew＋recv，generation 不變）；operator 代 ack
  僅限 holder 委託或緊急（漏接事故級），走前述 ext operator path。release
  命令形（AIR-225 primary release 實證）：`scbus release --harness zcode
  --session-id <holder> --address ai-guide-primary --generation <n>`
  （`--session-id`／`--generation` optional——後者為 fencing CAS）。

### Retirement 程序

退役一個 address 依序：①所有 sender 停止使用 →②drain/ack pending →③holder
`release`（或 lease 惰性 expiry）→④禁 reacquire。address row 留存不消失
（tombstone 語義以 scbus-address-contract.md:26 為準——對象為舊 binding
generation，非 address），不隨 release 消失——**退役後該位址 pending 再現
>0 ＝ stale-sender violation**（寄舊址者違規，不是正常第二 inbox）。

登記：`ai-guide-primary` 已退役（2026-10-01，AIR-225）——成立理由（AIR-206 SCR-6
位址面 drain 誤診）已被 SCR-6 否證，本退役＝部分反轉並於卡面聲明。此後
`ai-guide-primary` pending >0 即 stale-sender violation。

### Exception contract（第二位址五要件）

第二 durable address 要成立，須同時登記五要件，缺任一項不成立：
①獨立 consumer UC（非訊息分類）②canonical sender selection（誰寄它、何時）
③holder＋monitor 契約（誰持有、誰監看、各自生命週期）④ack owner（誰有權 ack）
⑤retirement rule（退役條件與程序）。現況登記：**無**（ai-guide 無第二位址）。

### Transport 事實登記（alias / multi-drop）

公開 scbus surface 無 alias、無 multi-drop：send 單一 `--to`／`--to-address` 二選一，
address 僅 create/ls/sweep。本節不新增 sc-router transport feature（AIR-225 不做項）；
fan-out 需求只能以多次單址 send 表達，且受上文禁雙寄約束。

## 證據錨點

southchariot：`src/scbus/controlChannel.ts:75-94`（身分決定論）、`:938-941`（B1）、
`src/scbus/client.ts:1029-1046`（ack holder-limit——ScbusAckCall deps）、
`src/scbus/controlChannel.ts:1057-1068`（name_conflict warn-once）、
`src/scbus/controlChannel.ts:1077-1101`（renewIfHeld＋crash backstop）；`src/extension.ts:3619-3631`（ownSid
register→acquireOnce）。
sc-router：`docs/protocol.md:828-867`（binding/lease/acquire 三態）、`:1720-1725`
（同 repo 多窗凍結慣例）、`:665-673`（claimed identity 非 authN）。
