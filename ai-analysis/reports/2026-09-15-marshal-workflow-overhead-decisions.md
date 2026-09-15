# Marshal 多模型開發：流程減量判斷

> 狀態：分析已整合入 EP S1/S2，增補審查後的採用範圍見最末節；不是現行規則變更。正文保留候選思路，最末節取代其中較寬的跨角色合併構想。
> 接續：[EP](../_tasks/09-15-development-workflow-redesign/ep.md)；[checkpoint](2026-09-15-development-workflow-redesign-checkpoint.md)。

## 結論

有不必要的 overhead。Marshal 已把工作能力與模型供給分開，部分 workflow 仍以主模型／effort／並發容量決定審查形態，形成兩套編排判準。應先去掉這種重複決策，再處理過細派工與材料搬運；不能只把旗艦換成便宜模型，保留原來所有呼叫。

本報告把 user 所說 fusion 理解為依 work unit 組合不同模型的協作；沒有證據顯示另有名為 Fusion 的 runtime，故不假設其機制。模型混用本身不保證獨立性；carrier family、provider family、context 隔離與證據來源是不同軸。

多模型成本應看「主 session 編排＋各 worker 啟動與讀料＋實際工作＋驗證與重工＋人的注意力」。便宜 worker 的單次輸出成本較低，不代表整條弧成本較低；目前沒有逐弧完整量測，以下沒有節省比例承諾。

## 已查現況與建議

| 項目 | 現行依據 | 判斷與處置 | 必須保留的能力 |
|---|---|---|---|
| agent 數量填滿 cap | `skills/review-engine/SKILL.md:141` 寫 agent 數量=max-agents | 刪除作為預設數量的用法；cap 只限制並發，數量由未覆蓋問題決定 | profile 各維度與必要独立視角 |
| 依主模型／effort 選審查形態 | review-engine:103–109；execution-plan:327–346 仍偵測主模型與 max-agents | 從 consumer 移除重複 routing；WorkUnitContract 決定工作，resolver 決定誰做 | qualification、effective effort、availability、authority |
| 普通中間段固定多視角，弧末再全審 | implement 的 Agent Review＋post-build 審查鏈 | 已審 EP 的 S2：普通段做實跑與證據，邊界段審，最後補完整弧級 review | 跨段互動、整合器／注入點 extras、缺 coverage 不結案 |
| 同內容再跑同一 profile | post-build:76–80 已有 identity reuse | 接好 identity producer；不是新增去重服務 | scope、內容、profile、證據可讀性；新 delta 另驗 |
| 無 finding 還走 judge/followup | post-build:88 已明確空 findings 直進 docs | 現況已省，不列為新增改革成效；保留此分支 | 只有真完成且可用的 review 才能是空 findings；失敗／截斷不是零 finding |
| 固定圖與反覆產殼 | execution-plan:383–388、implement:320 | 同一份 brief 更新，複雜關係才產圖；避免工藝成本蓋過理解價值 | 問題、前後行為、取捨、已驗／未驗及回源 |
| 每弧新 tour | 現行 hook 2 已 ask-once、預設略過 | 不再發明一次「去強制化」；修既有失效 tour 與新產 tour 分開 | 已被引用的結構導航可用 |
| compact 前 memory 整理 | compact-prep 與當日 compact 報告 | checkpoint 先落；長期知識整理不阻塞短期救援 | 不把未定案寫 memory、不跳寫入治理 |
| 自動維護=零成本 | overhead inventory 將排程項標零 | 更正評估口徑：只可能是低人力成本；本弧不改排程 | 維護價值按實際缺陷／漂移和 usage 衡量 |

以上是 current source 文件層查證，不是運行次數統計；不能斷言每次執行都派滿或每弧必然重審。

## Marshal 下還需補進設計的三件事

### 1. Role 是責任邊界，不是必須各開一個 worker

`skills/model-routing/SKILL.md:17–36` 定義 Role／workload／authority；`skills/post-build/SKILL.md:36` 已把主 session 編排列為不派工的責任。應將這個原則貫穿流程。

- Marshal 持有計畫、範圍與狀態，避免再派一個「Marshal 管理員」只重述這些資料。
- 同一 candidate 若滿足對應資格與 authority，可在同一 context 依序承担相容 work units；每單位仍有清楚輸入／輸出／权限，不因共處而擴權。
- Writer 與獨立 Reviewer 不合併；Reviewer 改寫自己剛審的成果後，不能再把同一視角當獨立驗收。
- Reviewer 跑錨點命令驗自己的 finding，可同輪附證據；只有需要獨立來源、不同能力或不同權限時再開 Verifier。不能以「已驗」自述替代可重現證據。
- 有資格的主 session 已能做 Arbiter 時，不為完成角色清單再開一個 Arbiter；資格不符仍須外派，不能以省 usage 降級。

直接效果是少 context 初始化；間接風險是權限或獨立性混淆。必測反例：同角色名卻不同 authority、同 candidate 缺第二 workload qualification、writer 假扮 reviewer。這些尚未行為驗證。

### 2. 派工按可驗收成果切，不按每個小動作切

建議把同 scope、同權限、共同 read-set 的「讀取→定位→機械查驗→回傳證據」合成一個有界工單；不要拆成多個各需重新理解背景的 worker。獨立檔案可以平行，存在 writer／reader 依賴時先交付再讀，不用同時起飛假裝並行。

分拆理由只需能說明一項：獨立性、能力或權限差異、隔離可恢復的寫入範圍、可獨立驗收的並行成果。若只因某 skill 名稱不同就拆，不足以證明收益。

合併也不是無限加大工單：受 transport payload、context 與失敗重做範圍約束；共享資料多但錯誤連帶面大時仍拆。採 path＋局部 read-set，讓 worker 自讀必要段落；不要每腿塞整段歷史。

此項不自行推翻現有 lite 派工政策，也不偷加「小工全部主模型親做」例外；優先批次化既有合法派工。若要新增直接執行捷徑，需另查所有 consumer／资格及實測，不在本報告當作已定政策。

### 3. 省重讀，不能省新鮮度判定

同一個 context 已讀且未變更的契約可引用已載內容；新 worker 仍須拿到足夠的 governing rules／任務契約。文件寫成 pointer 不代表 token 成本消失，實際載入才算。

每次 dispatch 仍核對 availability；不能為省 probe 把 stale／unknown 當 available。可以把同一批來源讀取與獨立查詢批次化，但不新增任意 TTL，也不以早先快照永久授權後續派工。政策翻轉後，依 freshness 規範 fresh context 接續；本輪不在舊 context 實作新版控制規則。

## 應保留與不應混入本弧的工作

保留 accepted EP、任務／WT 身份、唯一 writer、獨立 review、必要 invariant／runtime 驗證、finding 裁決及修正複驗、job 回收、commit/deploy 授權、逐端載入驗證。多模型會增加交接錯誤機會，這些機制不能因便宜或模型多而刪。

backlog id 防撞、branch／rebase、memory 寫入治理及排程成本值得個別量測，但本轮未查到足夠證據支持刪改；不能藉流程精簡把所有治理一併重寫。instruction-testing 已有 AIR-91 實驗記錄，舊 overhead 報告「仍是 draft、pilot 沒跑」不是現況依據。

## 最小主鏈（目標態，非立即替換現行規則）

任務與風險定位 → 足夠的計畫＋必要計畫審查 → 有界 writer 工單與實跑 → 未覆蓋範圍的獨立 review → 有 finding 才裁決與修正複驗 → 一次成果結算與簡短 brief → user commit。

全程只維護既有任務入口與必要證據；不是每經一個角色／命令就新建一份報告或新 worker。高風險工作增加具體防線，一般工作不為形式走完整角色輪替。

## EP 接續與驗證條件

已審 EP 已涵蓋 review 減量、身份復用、checkpoint、brief；新增「相容 work unit 合併／派工粒度／重讀」尚未被前輪 reviewer 審過。下一輪整合入 S1/S2 的範圍應先查現行 dispatch 政策，精確區分「只是批次化」和「修改 authority／路由政策」；後者不得碰 AIR-96 在途檔而不對齊 owner。

驗證選相同任務、相同輸入基線：記每個 context 載入量、dispatch 次數、有效工作／等待、重試與重做、可取得的 usage、seeded 缺陷檢出、未決與人類補問。特別測零 findings、空輸出、timeout、新 untracked 內容、角色資格不符、整合器、新政策舊 context。不能只數少幾個 agent 就報改善。

若合併工單提高漏錯或重做量，縮小批次；若 context 共用讓獨立性失效，恢復隔離；若無可用 usage，保留 unknown 並只報實測動作變化。新提案先 scoped 增補審查，不重跑整套已完成背景研究。

## 整合後的採用範圍

已把骨架、精確修改位置、責任、失敗處理與 SM-20–24 放進 EP，不停在本報告的候選想法：

1. 角色不等於 worker 保留，但本弧不建通用跨 authority worker。合格主 session 延用既有決策角色；多成果 batch 只限同 authority 的機械查證／實作子成果。
2. 多 review units 分開 context；同一弧級 review 審多檔仍可是一個 unit，但不能把獨立任務改名合併。S1 ordinary 單 reviewer 新預設需通過對照實驗；高風險 lens 不被 batching 吞掉。
3. batch 用既有 work-order envelope，逐 unit 解析及回收，保留部分成功／依賴失效；不改 routing schema、catalog、runtime 或 AIR-96 dirty。
4. followup 契約採 Reviewer/findings；主鏈編排者單寫 verified/closed **status**，新或矛盾 findings 由 Arbiter 裁 **disposition**。兩者不同；不憑主鏈自報修好。
5. 明指 post-build:88 的零 findings 快道，必須先有 completed＋完整結果＋coverage；空白／失敗／截斷不是零 findings。
6. 每 dispatch availability 與 new worker read-set 不省略；無 TTL／resume 新假設。HTML 互動／視覺驗證依 user 指示本輪不做；只同步閱讀版文字。

增補調查與 followup 原始結果存 EP 的 references/marshal-integration-review.json、marshal-followup-review.json；目前最後三點修補等待有界 closure 回覆，終態查 checkpoint。所有 runtime／成本效果仍待實作 LLM 實驗，文件審查不冒充運行驗收。

**終態**：references/marshal-closure-review.json 已返回，三點修補全部 resolved，無新增 Important。EP 已完整整合並可交其他 LLM 實作；上段「等待」為中間狀態，已結束。
