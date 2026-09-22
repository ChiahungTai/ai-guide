# Cross-repo 協作慣例包

> 讀者＝跨 repo 協作的 AI session／user。 sovereignty 前提單一源＝AIR-135.5「repo sovereignty 總則」：每 mutation 歸其 repo 主權、每 acceptance 歸實際 consumer；跨 repo 只傳 request、evidence、candidate 與 verdict。本檔是慣例面模板，不覆寫總則、不設總則例外。
> 消費規則：欄位定義一欄一義，禁複用欄位承載第二語義；模板節（節二／節三）照佔位符〈〉填寫，填後禁刪填寫說明以外的結構行。

## 節一：scbus 訊息 schema 草案 v2——已吸收 sc-router needs-info 五條

身位宣告：本節是給 sc-router protocol amendment 的輸入草案，非 protocol 權威（protocol.md 歸 sc-router repo 單方）。發送端行為（逐次確認 gate、sent-record 八欄、transport 四路分流）單一源＝AIR-135.5 AC#6，本節只定線上訊息格式與回覆語義。

### 訊息共用欄位（各 msg_type 皆適用）

| 欄位 | 必填 | 語義（一欄一義） |
|------|------|------------------|
| msg_type | 必填 | 四值枚舉之一：cross-repo-bug／fix-ready／verify-pass／breaking-intent |
| target | 必填 | 對端地址＝`harness:sessionId` 字串形（canonical＝複合鍵 `(harness, session_id)`，mapping owner＝sc-router）；附 WS 尾名僅 display hint |
| source | 必填 | 本側身分；有對應卡時帶 Counterpart token（`repo-id/card-id` 格式） |
| correlation_id | 必填 | 回覆與原始訊息的配對錨；同因重發＝新 id＋`supersedes` 註記舊 id |
| want | 請求類必填 | 發送方要的動作＋期望回覆類型（structured，與 body 人話敘述分離）——接收端 automation 機械分診依據 |
| expires_at | 選填 | 時效界——到期後禁確認發送，須 fresh facts 重組草案；接收端可據此 triage／過期標記（「開工時回覆」「probe 週期內有效」類訊息建議必填） |
| card_ref | 選填 | 訊息歸屬卡／線 id（`repo-id/card-id`，如 `sc-189`／`air-154`）——busForeign 分組＋跨 repo card↔message 對帳錨 |
| body | 必填 | 訊息本體（UTF-8 ≤8192，bus 凍結面）；大材料落 repo 檔案、訊息只派路徑；欄位需求類回覆用固定段落標題（逐欄一節），禁散文化 |
| artifact_pointers | 選填 | 支撐材料指針＋hash（驗證錨，非權威斷言） |
| context_delta | 選填 | 收訊端重建語境所需的最小差量 |

### 回覆訊息共用欄位（semantic ACK 欄位化——機械契約不由 body 自由文承擔）

| 欄位 | 必填 | 語義（一欄一義） |
|------|------|------------------|
| reply_type | 回覆必填 | 四值枚舉：accept／needs-info／declined／completed——semantic ACK 的欄位化承載 |
| in_reply_to | 回覆必填 | 原始訊息的 message_id／command_id——機械追線錨，禁靠 body 內字串引用 |
| info_request | needs-info 必填 | 補件清單（接收端消費者視角的欄位／資訊需求） |

（v1 的 ACK 四態語義表維持有效，v2 起四態以 `reply_type` 欄位承載，body 只放人話補充。）

### 各 msg_type 附加必填欄位

| msg_type | 附加必填 | 語義 |
|----------|----------|------|
| cross-repo-bug | defect_pointer；observed_effect；minimal_repro | 回報對端缺陷——缺陷位置、觀察到的效應、最小重現步驟 |
| fix-ready | fix_pointer；verify_evidence | 修復候選就緒待對端驗收——只傳 candidate，驗收歸 consumer（mutation 歸對方主權，本類型不含寫入授權） |
| verify-pass | verify_scope；evidence_pointer | 對端交付的我方驗收結果——驗了什麼範圍、證據在哪 |
| breaking-intent | contract_face；freeze_window；consumer_signoff | 破壞形契約變更意向——變更面、凍結窗口、消費者會籤狀態（會籤完成前禁落地） |

**禁一欄多義條款**（SC 案例①）：欄位語義以本表為唯一源；接收端落地映射（如 kanban 欄位分工 desc＝現況／AC＝驗收／Notes＝append 流水）由接收端自決，發送端不得要求單一 scbus 欄位同時承載「現況＋驗收＋流水」等多重語義。WANT/DONE 類訊息須顯式宣告所映射的接收端欄位，禁靠欄位復用省訊息數。

### semantic ACK 四態回覆語義

| ACK 態 | 回覆語義 | 該態附加必填 | 發送端後續動作 |
|--------|----------|--------------|----------------|
| accepted | 收訊方接受主張／承接請求 | — | 關閉 correlation，等待實質交付 |
| declined | 拒絕 | reason | 禁原樣重發；重議須新論據新訊息 |
| needs-info | 資訊不足 | info_request | 補件後以同 correlation 重發 |
| completed | 請求動作已執行 | result_pointer＋evidence | 消費端驗 evidence 後關閉 |

**ACK 附加欄位定義**：reason＝declined 的一句話拒絕理由；result_pointer＝completed 的交付物指針（格式複用 artifact_pointers：path＋hash）；evidence＝completed 的驗證證據指針（同 artifact_pointers 格式）——三者單義，禁與共用表欄位混用。

**evidence 指向條款**（SC 案例②）：ACK 與 receipt 的文字須帶 evidence 指向（path／hash／可機驗指針），禁權威斷言——「已完成」是宣稱非證據，「result 在 `<path>` hash=`<h>`」是。訊息文案禁斷言權威：transport consent ≠ mutation authority，送達≠取得寫入權。

### 與 proto §5.7 receipt 的對照表（審計錨）

transport receipt（機器面，delivery 保證）≠ semantic ACK（消費面，語義保證），兩面禁互升格。proto 現況：§5.7 receipt 兩 stage（accepted／visible）＋§5.8 consume 兩態（pending／consumed）；歷史用語「四態 queued/delivered/read/acted」（出處＝AIR-154 卡 notes SC 要席回執案例③；135.5 AC#6 僅泛稱「四態 receipt」）即由下表映射承接——本表為術語對齊審計錨（SC 案例③）。

| transport 面（proto 實況） | 語義 | 對應歷史四態 | 對應草案 ACK |
|---------------------------|------|--------------|--------------|
| receipt stage=accepted（claim＋envelope 落 new/） | 已收信，未達收件方可見 | queued | 無對應（純 transport） |
| receipt stage=visible（envelope 對 receiver 可見） | 可見＝「未讀」全部語義 | delivered | 無對應（純 transport） |
| bus pending→consumed（recv rename，at-most-one-winner） | 已消費；消費是回 ACK 的前置 | read | accepted／declined／needs-info 皆可自此態發出 |
| semantic ACK＋evidence | 消費面完成證據 | acted | completed |

**對照即審計錨條款**（SC 案例③收束）：任何「已送達／已同意／已完成」宣稱須能同時指出 transport receipt 檔（command_id 鍵）與 semantic ACK 訊息（correlation 鍵）；僅有其一＝未閉環，禁記完成。receipt 檔路徑僅以 command_id 為鍵（跨 sender 撞名後寫蓋前寫，proto 已知限制）——審計時須核對 message_id 欄。

### v1→v2 對照註記（sc-router needs-info 五條吸收記錄）

| needs-info 條目 | v2 落點 |
|-----------------|---------|
| ① in_reply_to＋reply_type 欄位化（ACK 禁埋 body 自由文） | 新增「回覆訊息共用欄位」表：reply_type enum＋in_reply_to 錨 |
| ② want 欄位（請求動作＋期望回覆類型，structured 分診） | 共用欄位表新增 want（請求類必填） |
| ③ expires_at（時效 triage／過期標記） | v1 expiry 改名 expires_at，語義擴充接收端 triage 面 |
| ④ card_ref（卡／線歸屬錨） | 共用欄位表新增 card_ref（選填） |
| ⑤ body 慣例（長材料入檔＋欄位需求回覆固定段落標題） | body 欄語義補固定段落標題要求；冪等去重維持現狀無新增 |

## 節二：contract 雙軌期條款模板

適用場景：兩 repo 契約格式遷移的過渡期（新舊形並存）。佔位符〈〉須全數填畢才生效。

### 並存期宣告

```
本契約〈名稱〉進入雙軌期：
- 舊軌：〈舊格式識別＋仍接受的範圍〉
- 新軌：〈新格式識別＋適用範圍〉
- 權威軌：〈新軌｜舊軌〉——衝突時以此為準
- 窗口：〈起點條件〉至〈終點條件或期限〉
- 窗口內禁令：禁新增依賴非權威軌的 consumer；權威軌變更須同步映照非權威軌
```

### migrated 回執格式

```
MIGRATED: <repo-id>/<card-id 或 contract face>
FROM: <舊格式標識>
TO: <新格式標識>
EVIDENCE: <可機驗指針——rg 命令／diff／path:line>
STATUS: done | partial（partial 須列殘留清單）
```

回執貼雙邊對應卡 Notes；對帳＝雙邊 MIGRATED 行互指一致，drift 即 fail-loud。

### 逾期未遷處置

```
窗口到期後：
- 未交 migrated 回執的 consumer＝非權威軌斷鏈；權威方無等待義務
- 斷鏈不靜默：權威方後續變更時對斷鏈 consumer 發 breaking-intent（節一），掛原 correlation
- 舊軌殘留產物禁刪除讓位前未機驗；刪除＝跨 repo 寫，歸 owner 主權逐次授權
```

## 節三：incident 預授權紅線清單模板

跨 repo incident 的事前盤點產物。前提句（sovereignty 總則，不可省略）：讓步只放寬「誰暫時承接」，永不放寬 isolation；讓步共同條件＝可逆＋留痕＋事後追認。

### 三分類判準

| 分類 | 判準 | 例 |
|------|------|-----|
| 可碰 | 本 repo 主權面內且授權面已含；或對方主權隔離面內且對端 session／user 已授權 | 本側卡 notes；已授權的對方 ephemeral WT |
| 禁碰 | 對方 canonical／authoritative state；他 session 在途檔案；無隔離面直寫；config／credential 面 | 對方主幹分支；共享 config；另一 AI session 的 working tree |
| provisional | incident 搶修讓步路徑——僅在「對端長期無主／packaging 原子性拆不開／incident 搶修」三情境內，且同時滿足可逆＋留痕＋事後追認 | 對方 repo 緊急 hotfix（走 --ephemeral）；外洩 credential 停用 |

### provisional 標記格式

```
PROVISIONAL: <動作摘要>
SCOPE: <repo-id>/<路徑>
REVERSIBLE: <是——附回滾步驟｜否——禁標 provisional，改逐次請示>
TRACE: <留痕位置——commit／log／檔案指針>
RATIFY-BY: <追認責任方＋追認動作>
```

provisional 未追認＝懸置狀態，禁升級為常態授權；本清單一次 incident 一次盤點，下次 incident 不自動沿用。

## 節四：orphan WT TTL 建議——終局盤點

結項狀態：原交付物④「orphan WT TTL 建議值（給 bridge）」已由 DB-21 裁決線消化，本檔不承載建議內容。

- owner 裁決：orphan WT 回收機制歸 ai-guide；bridge 端僅 spawn-time 驗證（DB-18），不做回收
- 承接卡：ai-guide `AIR-159`（backlog/tasks/air-159）——wt-close 擴充 TTL sweep；TTL 值與機制由該卡依 bridge 側規格提案定案，開工前置＝提案送達
- bridge 側提案落點：delegate-bridge repo `00-tasks/`（spawn-observability 弧）——邊界評估＋機制規格（方向：wt-identity.json 即 registry、TTL sweep 掛 wt-close/Settle 或獨立 gc）
- 本節角色：指針登記，非機制定義源——禁在本檔重寫或推導 TTL 值，禁以本節為據跳過 AIR-159 開工前置
