# scbus 位址制契約 v2（AIR-168 → sc-router 工單附件；併兩腿 amendments）

> 提案方：ai-guide marshal（consumer 側）。實作歸 sc-router 主權，本契約為提議，審後可改可收。
> 審查：codex＋muse 雙腿 GO-with-amendments（報告同目錄 air168-contract-{codex,muse}-review.md），amendments 全數併入。

## 0. 身分模型：既有三層 identity ＋ 新增 logical address abstraction

| identity | 是什麼 | owner | 禁止事 |
|---|---|---|---|
| bridge job id | bridge ledger job 追蹤鍵 | delegate-bridge | 禁代充 session id／address；只可持 provenance relation（job→native sid） |
| carrier session id | runtime 原生（zcode sess_*），birth surface（SessionStart hook）自我註冊 | carrier runtime | 禁冒充 logical address |
| SC ext endpoint id | `scbus-ext-<sha256(realpath)[:16]>` workspace endpoint | southchariot extension | 禁誤讀為 worker 身分 |
| **logical address**（新增） | 線/角色命名；**namespace/registry 擁有 address 與 mailbox，session 僅持 binding lease** | registry（address 不因 transfer/lease 過期消失） | address 非 runtime identity——不得當程序存活證據 |

正交性：bridge `--marshal`（authority profile）⊥ logical address（routing identity）——marshal 不自動取得任何 well-known address 的 claim 權。

## 1. address + binding（含 fencing）

- mailbox per-address（durable queue）；address 由 namespace/registry 擁有。
- binding 欄位：`holder_session_id + binding_generation(fencing token) + lease_expires_at + provenance`。
- claim/transfer/reclaim **atomic（CAS）**；transfer 後舊 generation 不得 renew/drain/ack（fencing）；**tombstone 對象＝舊 binding generation，非 address**（address/mailbox 永不消失）。
- crash 走 lease expiry → reclaim；顯式 handoff 走 transfer。fresh replacement 等 native birth 完成 → atomic transfer；resume（同 native session）不換 binding。
- raw session id ＝ **legacy direct-session target**（直投既有 mailbox，不參與 claim/transfer/lease；trust 與 approval 面由 sc-router 裁決）。

## 2. 送達語義（三態＋意圖/wake 軸明確化）

- 三態：`steer`（active session 下個 safe step 加入——**非搶佔式中斷**）／`queue`（durable pending，於下一個成功 drain opportunity 注入——**不宣稱 next-turn**）／`notify`（只進通知面，刻意不進 model context）。
- **禁靜默降級**：steer 無 active binding／carrier 不支援時 → machine-readable fail；僅 envelope 明示 fallback 才降 queue。
- 意圖×wake 軸：muse 有 intent（notification/solicitation）×wake（idle 即醒/wake-if-idle/safe point）三軸——**是否全抄或聲明子集＝待裁決**；solicitation 重發上限與退避種子：三次無回應即停。
- delivery 保證宣告：at-least-once＋`envelope_id` stage 幂等（transfer/retry/adapter crash 的重複 drain 防護）。

## 3. 消費 stage（oracle 命名收緊）

- receipt ≠ read（accepted+unverified_target_receipt 只證投遞）——先立此原則再加 stage。
- stages：`accepted` → `injected_at`（成功進 consumer context 後寫）→ `acked_at`（consumer 顯式回執）。**acked ≠ action/outward 成功**。
- `notify` mode-specific：成功 oracle＝通知面 visible；不套 injected/acked lifecycle。
- stage 寫入者與可信度＝待裁決（adapter self-report 為上限）。

## 4. registry 觀察/註冊分離

- observe 不得更新 liveness 欄位（observed 與 self-claimed 分欄）；`live` 收緊為 **ACTIVE_RECENT/self-fresh**（不宣稱 running——generic scbus 無 process-death authority）。
- **observe 絕不 renew binding lease**（防 ghost freshness 換形復活）。

## 5. drain adapter 能力矩陣

| harness | register | drain | 備註 |
|---|---|---|---|
| zcode | ✅ SessionStart | ✅ UserPromptSubmit additionalContext | 含 bridge glm worker（真 HOME inherit——DB-27） |
| codex | ✅ SessionStart/End | ❌ | 需 drain adapter |
| claude | ✅ SessionStart/End | ❌ | 需 drain adapter |
| muse | ❌ 無 hook 面 | ❌ | 完整缺口 |
| headless worker（bridge） | ✅（carrier birth hook） | ❌ 無「下一個 prompt」 | queue/steer 標 unsupported，或 route 到 controlling logical address；**job terminal 禁充消費回執** |

## 6. envelope 與治理面（muse 種子值）

- size cap 8192B／`envelope_id` 去重／self-send 拒收（種子抄 muse）。
- approval 面：unverified/non-matching sender 觸發 holder 批准（sender 名＋id＋workspace＋preview＋delivery effect；allow/reject once＋for-session；30min 過期＋retry cooldown——值可調）。
- namespace 種子：case-insensitive user-wide、3–32 chars、小寫字母開頭、單連字元、保留字（all/self/current…）、ASCII 正規化。
- 孤兒 mailbox GC：lease 過期信件保留上限＋隱私殘留清理＝待裁決。
- watcher：durable subscription 或 claim 時自動 re-arm（session-owned watch 會死——實證）。

## 7. 待 sc-router 裁決清單（合併兩腿）

TTL 值／tombstone retention／steer fallback 預設／namespace 規則／**claim collision 與 CAS 實作／transfer+reclaim authority／binding generation 粒度／expired-unbound address 三態行為／legacy raw-id approval 政策／ordering 保證等級／stage 寫入者與 oracle／adapter capability negotiation／watch re-arm 語義／size·dedup·self-send 初值／intent×wake 軸取捨／approval 面欄位與值／孤兒 GC 政策**。

## 8. ai-guide 側驗收（sc-router 落地後）＋對抗案例

驗收：①轉移 binding 後寄 address 可收②三態行為可區分（含 steer fail-loud）③injected_at/acked_at 機械可查④假新鮮消失⑤muse 線可用收信路徑。
對抗案例：**同時 double-claim 只一方成功；transfer 後 stale holder renew/ack 被 fencing 擋；headless queue 不偽報 consumed；resume 同 native session 不換 binding、fresh replacement 才換 generation**。

## 9. 相關但不在本契約

bridge `--marshal`（DB-33，authority profile）；commit 治理（caller conditional delegation）；SC-225 A-bar facet（渲染面）。
