---
name: relay-claims-verify-current-state
description: 跨 session relay/通知對「接收方現況」的宣稱常過時（傳送方 snapshot 落後）——接手第一動＝機械驗證當前狀態，勿照 relay 描述行動
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_d8de15e8-a98d-4c74-b58e-b5ba869564d7
---

跨 session relay/handoff/通知/回執/reviewer finding 對「現況」的描述可能是過時快照——**relay 是任務輸入，不是現況真相**。多 session 並行拓撲下連續 30+ 案例實證；本條已把逐案敘事壓縮為變體目錄，個案細節查各 repo EP/git log。

**核心機制**：傳送方對接收方的認知停在它最後一次接觸的快照；接收方（或其並行 session）持續演化，relay 延遲送達差距更大。反向同樣成立：我方發出的宣稱／bug report／驗證結論同級過時。

**How to apply**：收到關於「現況」的宣稱（版本、數字、狀態、快照、存在性、部署），第一動＝機械驗證當前狀態（diff 源頭、rg 錨點、實跑、磁碟檢查）。已滿足＝回報證據零動作；落差＝以實況為準修正行動。這是 [[session-topology-single-writer]] 拓撲的必然成本，與 acceptance-evidence 的 Claim→Evidence 同構——relay 宣稱也是 claim。關聯 [[settlement-scripts-are-code]]。

## 變體目錄（每條都是獨立踩過的坑型）

**宣稱源不止 relay 正文**：
- handoff 自帶的「複掃預期清單」也是 claim（漏自家 diff 沒碰的行＋掃描範圍外的檔）——每個 hit 逐條 triage，勿以「符合傳送方預期」跳過
- 「刻意保留」清單會被 relay 自身宣佈的變更失效——以當前語義 re-triage，核對保留理由是否仍被本次變更支撐
- 任務描述本身是快照：可能已完成（重掃零殘留即以證據回報「零殘留」，非重做）
- 附帶的 patch 建議／失敗歸因提示＝評估對象非命令——獨立驗因（歸因錯則 action item 全錯），可偏離但明示理由
- reviewer／調查 agent／fresh-eyes 的宣稱（含「X 不存在／無引用／死碼／死條目」）對 orchestrator 都是 relay——load-bearing 事實親驗或派獨立驗證（範圍涵蓋事實面不只結構面）；對立時以機械證據定案非多數票
- untracked 檔案 artifact＝寫下時的結構快照，「檔案在場」≠「內容新鮮」——收編前對現行結構核對
- 自己的 memory 檔、自己過去 session 寫過檔案的記憶、harness 注入的 session-start agentsMd 快照——全部同級過時；動手前 rg/re-Read 現值
- **評論/品評請求也是動手**：user 問「你覺得 X 檔寫得怎樣」→ 憑記憶作答＝拿 stale snapshot 打 stale snapshot（09-05 實證：評了自寫舊 ep.md，實況已被 codex 15:00 覆寫，被 user「codex 不是有重寫你有看嗎」打臉）。多寫入者環境（external runtime 產出／平行 session／codex/muse 重寫）下，任何檔案的品質評語前先 `ls -la` mtime＋讀現檔——成本秒級
- 監控／排程報告的量測值凍結於取樣時點——「精確數字與歷史里程碑吻合」正是歷史快照指紋；報告請求的處置先查最近 commit 是否已執行；逐項裁決，勿因龍頭宣稱過時整份丟棄

**驗證端自身的假陰性三源**（「我查不到」≠「不存在」）：
- rg pattern 用回報方宣稱的措辭＝太窄（執行者常換同義措辭）——零命中先讀實檔本體再下結論，否則冤枉誠實回報
- 工具用法失誤（fd 漏 `-H` 漏 dotfile、漏看 except 位點）
- 查證面不涵蓋目標域（workspace-scoped 排程/cron 要查該 workspace 的 memory＋對話 db）——user 說「有討論過 X」先信存在、擴大搜尋面，勿用自己查不到反推 user 記錯

**狀態落差成因學**（下因果結論前先問「這段時間有誰動過它」）：
1. 傳送方快照過時（主型）
2. 任務已被完成——常由接收端自己的並行 session 完成：handoff 待辦逐項驗是否已落地（git log＋rg 錨點），非只驗 baseline hash；「裁定→動手」窗口同樣會被並行 session 搶先
3. 產出後送達前第三方動了同一目標（零匹配＝已知清理動作的確定結果，勿誤診為快照飄移；接收方的更正/歸因本身也是宣稱）
4. 發佈 in-flight（tag push→CI build→publish 有時間窗）——排延遲驗證，非立即回報上游補救
5. 反向對偶：「已完成」宣稱把計畫寫成完成式、實際未發生——release 類宣稱分面驗（git tag／PyPI registry／plugin cache 三面獨立演化）；我方 FAIL relay 也不是終局裁決，重驗指令＝快照刷新信號

**驗證手法要點**：
- 檔案/commit 清單可能沿用寫入方 cwd 語境（跨 repo）——路徑 404 先跨 repo fd 撈，404≠不存在；定位後遵守單一寫入者拓撲
- 工具名宣稱必標面別（CLI 子命令／MCP tool／config 鍵）——未標面先問「哪個面」，兩面各有機械真相源（--help vs tools/list probe）
- relay 對「環境拓撲」（設定存哪、狀態在哪）的宣稱同級——傳送方可能搜錯位置；「做不了/須特殊操作」類宣稱先驗存放位置是否真如其述
- 「部署已同步/落後」先驗機制（symlink 下 byte-identical/mtime 一致 trivially true，不構成任何動作發生過的證據）
- 錨點精確 ≠ 診斷準確——「缺口在哪」的 scope 宣稱與行號宣稱分開驗，複掃可能改寫修復落點
- 「清理完畢／全刪」＝ls/rg 實點對帳，不採信回報清單（清單會漏自己埋的）；closure 宣稱區分「修正已落地」vs「記錄已寫回」，驗完證據當場抓進自己的報告（gitignored artifact 隨時被並行 session 清掉）
- 「機制假設被推翻」級驚訝宣稱先排時間線（config mtime vs session 啟動 vs 測試時點）——新 session 拿舊 config 的預期路徑常被誤歸因為熱載入；被拒絕的假宣稱會換措辭回鍋，每輪重新機械對抗；transcript/tool-call 記錄是最高等級證據（直接證明「沒有那個動作」）；機械對抗＝逐項裁決，查證成立的項照樣採納
- reviewer 引自身 session context 當磁碟/部署現況證據＝快照謬誤——judge 一律驗磁碟；coordinator spawn 時把「外部現況已變」主動寫進 reviewer prompt（對 session 內時序事實有告知義務）
- 承接 handoff：驗 baseline hash＋目標檔有無被 baseline 之後的 commit 動過（重疊則編輯指令是對舊檔寫的）；handoff 的 caveat 先查是否已被接收端既有檔案解決
- 診斷訊息先問「指哪個主體」再歸因（訊息無主體標示＝工具缺陷，但歸因前查主體是接收方義務）；「升級/修改某段落」任務開工前 re-Read 現行段＋查 baseline 之後 commit
- 接管他人（跨 LLM 尤甚）工作：其「已完成」清單逐項 rg 實檔——宣稱同步面積≠實際同步面積；session transcript 是對質材料（讀法見 [[muse-code-cli-facts]]）
- **自己 1308 中斷後的接管考古（09-07 實證）**：接手指令常只給 session id＋branch＋任務家路徑——完整圖像＝git log（分支分岔點/他人代 commit）＋任務家 EP（status 行可能 drift——「尚未實作」vs 已 commit 的 S1）＋session 記錄抽取（muse jsonl 需 probe 結構：runtime.user_intent.accepted 的 refill_blocks 抽 user、run.terminal.completed 抽 assistant——頂層 payload_type 遍歷對 retained_frame 包裹無效，要遞迴 children[].record_json）；先跑分叉預覽再預期衝突（merge-base 可能＝對方直接基於最新 main——純 ff 吸收零衝突，預期衝突是假設）
- 被更正時秒級唯讀複驗閉環，勿爭論勿重做
- 覆核範圍宣稱精確到 claim 級（「全部經獨立覆核」會超賣）；對抗驗證鏈（獨立覆核＋魔鬼代言人＋翻案親驗）實證有效，值得保留為 deep-work 標配

相關：[[project_session-topology-single-writer]]、[[full-read-base-not-context-copy]]（elide 面）
