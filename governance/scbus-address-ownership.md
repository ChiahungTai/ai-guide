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
> duty 消費 custody 授權（AIR-312 repo 身份制）＝duty_receive 只消費呼叫端 repo
> 自己的 address——canonical alias 由呼叫端 git common-dir 反推 primary root
> 的 basename 推導（linked WT／subdir／symlink 同一身份；非 git／bare／無法
> 判定 fail-closed；錯址在任何 consuming side effect 前拒絕）。AIR-311
> per-caller consume TOML 已退役（無授權檔、無 migration bypass）——
> class×action 分診表仍中央（dutymail-processor.toml）。

### Repo address cardinality（一 repo 一門牌）

- 每個 repo 預設**恰一個** well-known durable inbound address。AIR-312
  命名＝**repo basename**（ai-guide 即 `ai-guide`；duty_receive 身份閘
  exact match 強制）；歷史命名 `<repo>-marshal`（`ai-guide-marshal` 等
  五址＋舊 exceptions 址）＝AIR-311 前慣例、過渡期並存——sender/
  reply_address 切換與在飛責任對帳完成後才退役（AIR-312 S3 對帳條款
  ——不以 pending=0 宣稱完成）。
- **章位分離（AIR-298）**：消費章（prepare/ack 的 epoch-fenced holder binding）歸
  **當時的值星 session**——ext 決定論身分長持只及 escalation／人類 viewport 地址，
  AI 消費者地址不適用；INBOX 章（送達＋viewport 顯示）無章可持——durable INBOX
  holderless 常態（B′），顯示面不依賴任何 binding。值星 session 死後＝
  death-evidence 接管——判死證據分兩面勿混：**現行機械面**＝duty_receive
  自動接管判準＝per-session state 檔 mtime 陳舊 ≥24h（`HOLDER_STALE_SECONDS`
  具名常數，保守誤殺防線）——非即時；**內容面心跳**（exec 目錄/artifacts
  停止前進）＝消費端自律判準／目標態——AIR-296 驗活判準（內容面偵測為唯一
  可靠訊號）可自律套用，但其機械 sweep（`agent_liveness_sweep --zcode-scan`）
  只掃 spawn subagent 域、不涵蓋 in-harness session，勿推得基礎設施已備；
  機制收緊歸 bridge/duty 弧（bridge db100 已排卡＋S1 amendment 互引）。
  換代條款單一源＝`scripts/duty_receive.py` module docstring。
- 第二位址例外 predicate：必須證明**獨立 consumer UC**才可建立；「系統信／工作信」
  「值星／marshal」等訊息分類或命名差異不構成 UC——訊息種類用 envelope
  `mode`（steer/queue/notify）＋`intent`（inform/solicit/receipt）表達，不以多位址分類。

### Sender selection（二分 oracle）

| 訊息要給誰 | 動詞 |
|---|---|
| repo/workspace 承接、須跨 session 存活的責任信 | `send --to-address <repo>`（repo basename——AIR-312 命名） |
| 已知 live session 的即時對話 | `send --to <session_id>` |

同信多址雙寄製造雙 envelope＋ack 歧義，禁。

> **遷移註記（AIR-312 S3——sender/reply_address 切新址）**：在飛 thread
> 的回信仍落舊址（`<repo>-marshal`）——舊址讀取以 raw producer 唯讀面
> （`dutymail mail list --address <舊址> --box pending`）對帳，非 S2 CLI
> （S2 只消費呼叫端 repo 身份址）；對帳完成後舊址才退役
> （「Repo address cardinality」節）。

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
  session inbox**：自動知會面已隨 AIR-312 退役（prompt 邊界 monitor 註冊
  拆除，見下條）——現行面＝session 內明確觸發（[mail-handle](../skills/mail-handle/SKILL.md)
  mail_waiter per-repo watcher 掛哨喚醒；once 看信＝S2 inbox（mail-handle））
  ＋人工 point-in-time 輪詢＝
  `dutymail receive status`（歷史實證錨 AIR-168 驗收③保留標註；scbus 時代
  address pending badge 與 session inbox 輪詢已隨換代退役）。
  **已知崩潰史（SCR-8，scbus 時代）**：
  address row 在而磁上 `new/` 目錄缺時，pending badge 視圖曾整命令崩
  （raw FileNotFoundError）；上游已修（sc-router scr-8——缺目錄讀面 fail-soft
  回空清單＋pending_note，修復入 v0.2.0），本機已升級（歷史事實；maildir 直讀
  降級路徑隨 invariant 條退役）。session 換手
  不動搖 ownership。因監控需求 acquire/renew/force-reclaim canonical address
  皆違反本節。
- **interaction-boundary hook monitor（AIR-225.1 建面；AIR-233 scbus receipts
  消費面從未落地——AIR-254.4 降級重寫為 dutymail 面；review 修復重設計為
  holderless pending 語義；**AIR-312 註冊退役**）**：
  `hooks/duty_mailbox_monitor.py` 曾掛 zcode UserPromptSubmit＋SessionStart
  sync 條目——**AIR-312 起註冊拆除**（manifest hooks surface 除名；腳本
  留 repo，入口 inert no-op——觸發零 face 呼叫零寫入零輸出；重掛＝違反
  退役裁定）。現行知會面＝session 級
  mail_waiter per-repo watcher（背景 shell 掛哨喚醒——
  [mail-watch](../skills/mail-watch/SKILL.md)）＋消費入口（S2 inbox——
  [mail-handle](../skills/mail-handle/SKILL.md)）；人工
  point-in-time 輪詢
  （`dutymail receive status`）保留為 fallback。monitor 的 holderless
  pending advisory／pending-age 帳語義＝歷史契約（git log）。
- 回歸鎖：情境 own session=0、retired address=0、canonical marshal>0 仍必須視為
  actionable（2026-10-01 事故形態——值星只掃 primary＋自己而漏 marshal）。
- ack 綁 live holder＋epoch fencing：跨身分 session 面 ack 他人位址必被拒
  （holder-operation gap；dutymail 時代 ack 由 epoch-fenced holder 執行）。
  歷史實證〔scbus 時代，已隨換代退役——AIR-288 拔鐘後 lease 過期態不可達〕：
  2026-10-01 migration 時 lease 已過期的位址曾由同 trust boundary 的 operator
  走 **ext operator path**（以 ext holder 複合鍵執行當時的 scbus CLI）
  plain `acquire` 恢復 lease 後代 ack 三封——非 transfer、非 force-reclaim，
  pin 仍屬原 holder 身分；此恢復程序 dutymail 時代不存在，不可照做。
  **規範禁令不隨換代退役**：session 面冒身 acquire 禁（identity 非 authN、
  trust boundary 內可 spoof 是事實描述非授權，見紅線節——規範禁令不因技術
  可行而撤）。
- 閉環驅動路徑：發現本 repo 新到收件（現行面＝mail_waiter per-repo watcher
  喚醒；消費面＝S2 inbox（mail-handle once）；歷史〔AIR-312 前〕＝prompt 邊界 monitor；
  fallback＝pending 快照 >0）後，正常消費＝**值星 session 持章自收**（duty_receive
  處理器 bind→prepare→ack；前任 session 死後 death-evidence 接管——章位分離
  見上，AIR-298）。程式面無從舉證時（外點 bind 無 per-session state 檔、
  token 遺失——2026-10-09 epoch-102 孤兒綁定實證），24h 窗口內持有實質
  death evidence 的正當接管面＝operator-invoked
  `dutymail holder takeover --address <ALIAS> --expected-epoch <N>`
  （CLI 形態以 `dutymail holder takeover --help` 為準；接管規則消費端自律
  ——dutymail 不 impose policy，明文 operator-invoked 是正當面）。
  scbus 時代實證〔已退役〕：AIR-225 曾以 holder ext 自收／ext operator path
  代 ack，並以當時的 scbus release 命令釋放 primary 章位（含 generation
  fencing CAS 參數）——CLI 與命令形已隨換代退役，留 audit-trail 歷史價值、
  不可照做；dutymail 時代釋出面＝`release_holder`（SessionEnd hook 接線）。

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
