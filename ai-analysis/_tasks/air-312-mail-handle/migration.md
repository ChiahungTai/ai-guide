# AIR-312 migration evidence

中間檢查點，未宣稱遷移完成。user 本次承接整份 handoff；後續 steering 改為普通 inbox/read/待回覆模型。四封新協調信已送，沒有重發先前 provisioning 或 DRAFT-46 信。AUTH: user said "要處理的信件問題，交給你處理吧，可以用 flash實作， 你在跑 [$post-build](/Users/ctai/Github/ai-guide/skills/post-build/SKILL.md) 跟裁定。"

## 新地址建立

以 sanctioned leaf `/Users/ctai/.local/lib/delegate-bridge/runtime/current/dutymail address create --alias <name>` 執行，各次 exit 0、ok=true、lifecycle=active。storeId=1b08e53e-10c3-4321-b38f-c26044a01a94。

| alias | addressId |
|---|---|
| ai-guide | e4fd77ed-44e1-4080-b93e-ec105b99af44 |
| mosaic_alpha | 4b6d7f4a-0e90-4361-8361-0ee113506865 |
| code-reality | 7af5be6b-0a83-4f2a-a63b-7fd5be49939b |
| southchariot | 91a2f0de-24fd-4c81-8683-b5f379bc870a |
| delegate-bridge | ec978276-3f47-4fea-8d81-056c32a972be |

建立≠sender 切換≠SC 顯示≠舊址退役。

## 舊地址觀察

以下表為通知寄出前快照；後到 owner 回報以末節為準，不用舊 pending=0 宣稱遷移完成。

唯讀 agent 01a12d3f-ce05-7931-859b-337303019088 查 receive status / holder status，各 face 非原子快照。bound 不表示 carrier session 活著。

| address | pending | cursor/last | consume epoch/bound |
|---|---:|---|---|
| ai-guide-marshal | 0 | 73/73 | 110/true |
| ai-guide-exceptions | 0 | 0/0 | 0/false |
| mosaic-alpha-marshal | 1 | 2/3 | 3/true |
| mosaic_alpha-marshal | 1 | 0/1 | 0/false |
| code-reality-marshal | 0 | 21/21 | 4/true |
| southchariot-marshal | 0 | 40/40 | 28/false |
| southchariot-escalation | 1 | 1/2 | 1/true |
| delegate-bridge-marshal | 0 | 72/72 | 49/true |

liveBatch 全 null；未做 takeover/release/ACK。Mosaic 雙拼寫是不同 addressId。CLI 無 address retire/delete/redirect/rename，release 僅釋 authority，不能當地址停收。

## 在飛限制

outbound-log.jsonl 15 行/14 parent；14 parent scoped replies 中 5 個有回信（7 items），9 個回空。replyType=null 不代表無語義 reply，需解析 canonicalEnvelope 字串，再解析 body 字串找 reply_type。兩筆 body 有 result_pointer/evidence 尚未驗指向。不將 cursor/回空當責任閉環。

parent 0a9b8c7d-6e5f-4403-9281-7261544332aa 送 mosaic_alpha-marshal seq 1，cursor 0，未 drain。另兩筆 pending 未識別。各 repo owner 自查並遷移，禁止代消費他 repo mailbox。

## Bridge 帳面回報素材

primary ledger job-mv4etls7-1ie4y5：status=workspace-mismatch，exitCode=1/carrierExit=1，timestamp=2026-10-11T22:50:00.901Z。failureDetail=`stream disconnected before completion: ChatGPT final DOM could not be aligned with text already streamed to Codex`。errorExcerpt 另有 missing-content-type / 426 Upgrade Required。verdict 已留 primary .agent-tmp/improve-20261011/uc-codex-verdict.txt。status 與 failureDetail 不足自行推定同根因，應請 bridge owner 查分類，不重派。

## 下一步

查證結果：bridge ACK 不刪原文，但 prepare/peek 只讀 pending（receive.rs:724），無一般歷史 list/get 公開 face。SC 目前只接 escalation，先本地持久化再 ACK；read 與 done 分離。最小 inbox 模型需要 bridge 公開歷史讀信、SC 接 repo mailbox；五態 ledger 並非 transport 必需。source 查證 unverified-by-graph，未驗 installed UI。

四封協調信 queued-visible，完整 acceptance 三鍵見 outbound-receipts.json。bridge seq73、Mosaic 連字號舊址 seq4、CR seq22、SC marshal seq41。各信附新 user 模型、現況限制與遷移條件；回信暫回 ai-guide-marshal，尚未宣稱對方承接/完成。已以既有 duty_disposition record-outbound 記帳，target cursor-at-send=null（未在 send 當下重查）。

新信箱已建但常態入口尚未切換；舊址保持歷史資料与現有責任。退役採對帳條件，不臆造日期。等 producer/SC owner 對最小讀信契約回覆，再完成 source 與 post-build；不以 consumer 複製信箱繞過歷史讀取缺口。

## Owner 回報：code-reality / CR-8

來源＝user 手動轉貼，非本 session live 複驗；無 message_id，不另寄 semantic ACK。CR-8 commit 含對帳 ledger，但回報未附 commit hash。

- code-reality-marshal 22 信全數核對：六 inbound thread 與六 outbound thread 已有 closure／回音，只有 seq22 AIR-312 solicit 待回覆寄出；cursor21/22、pending1、holder epoch4 bound 未動。先前21/21是通知到達前快照。
- repo 修改僅 CR-8 卡與 consume.toml 退役待閘註記，card_validate PASS（owner 報告）；共用 skill 接管前不先拆活機制。歷史卡／EP 保持歷史記錄。
- sender 尚未切到 code-reality；新址 epoch0 未動。現存 outbound 已閉或由對方持有。
- 舊址退役三閘：sender 切換、共用處理信 skill 落地、bridge ACK 後歷史讀取入口。閘前不宣稱退役，不重建 envelope，不刪歷史。

ai-guide 承接：維持此三閘；S1 繼續，S2 接 producer 正式契約。CR 歷史對帳已回報，不要求重做。回覆文字已交 user、尚未寄送，不把 manual paste 當 transport ACK。

## Owner 回報：Mosaic / MOS-189、MOS-190

來源＝user 手動轉貼，非本 session live 複驗。MOS-189 commit `ae9eaee27`；責任接續另記 MOS-190。信件 body 由 owner 讀 store 副本核對，兩址 holder 為協調方活綁，因此未 ACK、未推 cursor。

| 舊址 | cursor / pending | 已辨識內容與責任 |
|---|---|---|
| mosaic-alpha-marshal | 2 / 3 | seq3 CR 0.12.0 landing；seq4 AIR-312（78502f82）；seq5 CR-7 0.12.1 驗收回執。只有 AIR-312 需回覆，實質答覆已由本 manual paste 提供，其餘免回。 |
| mosaic_alpha-marshal | 0 / 1 | seq1 ai-guide draft-46 閉環回執，無待回覆。 |

雙址成因據 owner：原提案 reply_address 用底線，CR 寄往連字號。Mosaic 自持 consume holder 已 release（owner 機验 bound=false），不等同協調方持有的上述兩址被釋放；watcher stopped。

canonical mosaic_alpha 空箱在場、未重建。未來 sender/reply_address/watch target 慣例已記卡，尚未宣稱 watch/read 實際切換。repo 舊址引用僅 draft-46 一處，owner 報告無 config/hook 需改。待共用 skill 與 bridge 歷史契約到位再切；不猜 CLI、不硬切日期、不轉寄、不刪信。

ai-guide 承接：接受本報告為 semantic 回報，不冒充 transport ACK 或實際 sender 已切；四封 pending 的責任已辨識，不再要求重盤。S2 接線驗收後才結算遷移。

## 切換通知已寄（新址首信）

AUTH: user said "不會受影響就寄吧"

四封 coordination/inform 切換通知（skill 落地＋用法要點＋S3 條款＋各 repo 專屬回指）已寄達四個 **repo-basename 新址**（各 acceptanceSeq=1；冪等 replayed 驗證通過）。三鍵回執見 outbound-receipts.json 後四筆。影響評估先行：與進行中 AIR-318/319/320 零矛盾（318 auto-arm 為強化非矛盾、319/320 不觸信件內容面）。此信＝遷移三閘之「共用 skill 落地」閘正式通報——sender 切換與舊址退役歸各 owner 依 S3 條款收線。
