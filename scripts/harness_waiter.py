#!/usr/bin/env python3
"""harness_waiter — ZCode 子 agent timebox 監視＋收割＋停止協議（AIR-149 S1＋S2；frozen spec v2）.

一句話：ZCode Task-tool subagent 無獨立 process 可監看，且 per-task 活動面
不可觀測（K1 活體證偽：running 中的真 subagent 於四觀察面全數靜默/缺席）——
本 watcher **不做任何活/死宣稱**，只機械回報兩個事實：terminal transition
（權威狀態訊號）與 running 超 timebox（時間盒事實；user 裁決 0920：20 分鐘
不落地＝bug 處理）。timebox 到期＝先收割後喚醒（exit 3，advisory——不 stop
不重派；砍與重派歸主 session／deepwork 授權鏈）。

v2 Pivot（K1 amendment 淵源）
------
v1 以「rollout＋artifact＋exec 三面推進靜默計數」判凍結；TC-4 round 2 活體
證明 running 中的真 subagent 於四觀察面全數靜默/缺席（rollout 檔不存在——
子 agent model I/O 折疊進 parent session 層，per-task 不可分；exec 僅 fd
存在性無進度訊號；metadata 反指標；artifacts 無）→「三面觀察判定靜默」前提
證偽，凍結偵測（靜默計數）整體移除，改 timebox 模型。fd lease／表面 mtime
／cursors 推進全數降級 telemetry（不進判準）：exec lease 記
`exec-lease-held`；時鐘回撥記 `clock-rollback`（回撥輪禁判——視為 Fresh）。

契約源
------
- EP：ai-analysis/_tasks/2026-09/09-20-harness-liveness-watcher/ep.md
  （S1 節 frozen spec 轉移表 v2——S 級 oracle，本檔表格逐字搬入）
- 設計裁決：同任務 references/research.md（AIR-148 probe＋codex 兩輪攻防）
- 兄弟形態參考：bridge_waiter.py（bridge 側兄弟，結構參考、代碼不共用）

觀察面（v2；路徑常數集中 ZCodeLayout，禁散落）
--------------------------------------------------------
- metadata＝`<cli>/agents/sess_<parent>/agent_<id>/metadata.json`
  （status：running/completed/failed/stopped——spawn 與 terminal 兩點寫入；
  **terminal transition＝唯一權威狀態訊號**）
- exec＝`<cli>/exec/<taskId>/`（fd 存在性→lease probe；telemetry＋`--verify`
  surviving-writer 面，不進判準）
- artifact＝`<cli>/artifacts/<taskId>/`（telemetry＋verify cursors 面）
- rollout 面（v1）**整段移除**——K1 證偽：子 agent 無 per-task rollout；
  harvest 的 rollout tail 降為「存在才收」（缺席記 manifest `absent`，非
  fail-loud）
- daily log jsonl 的 `subagent.background.completed/.failed` 事件為輔助
  terminal 觀察面（未接線——frozen v2 T1 輪詢只查 metadata status＋registry
  對照）

`taskId` 慣例（機器實證 2026-09-20）：childSessionId 全形
`sess_subagent_agent_<uuid>`；exec/artifact 目錄名直接使用該全形 id；adapter
以 glob 解析 parent，agentId 由 taskId 機械映射。可註冊形兩種（AIR-160 追加，
marshal dogfood 2026-09-22 實證）：全形 `sess_subagent_agent_<uuid>`（v1）與
Task tool spawn 短形 `agent_<uuid>`（恒等映射；childSessionId 等價判定在
register 寫面）。

fail-loud（frozen 擴充）：metadata 錨點缺失（running 期消失＝T5 hard-death）、
JSON 不可解析／半寫 torn read、glob 歧義——一律 `unknown(原因)`，禁 crash
禁猜禁誤報。時鐘回撥（elapsed<0）＝視為 Fresh＋telemetry `clock-rollback`。

timebox 判準（v2 frozen）
------------------------
effective = now − entry.createdAt − poll gap 異常段（gap > interval×2 只記
一個 interval，餘額扣除；SM-7 機器睡眠不誤觸）。effective ≥ timebox（預設
20m；registry entry `silenceBudget`〔分鐘——v2 重解釋為 timebox，EP amendment
已載〕覆寫；`HARNESS_WAITER_FREEZE_MIN` env 覆寫〔v1 名保留——改名相容〕）
＝到期。表面推進／exec lease 不重置不豁免（timebox＝牆鐘年齡，非靜默量——
禁 liveness inference 回滲）。

狀態機（frozen spec 轉移表 v2——EP S1 節逐字；S 級 oracle，TC-1 對照本表；
實作者不得改表，改表走 EP amendment。v1 的「三面靜默計數」路徑整體移除——
per-task 活動不可觀測（K1 活體證偽）；timebox 取代靜默閾值）
------------------------------------------------------------------

| # | 來源態 | 事件 | 條件 | 到達態 | watcher 動作 |
|---|---|---|---|---|---|
| T1 | （註冊） | S2 registry entry 建立 | — | MONITORED | 開始輪詢（只查 metadata status＋registry 對照） |
| T2 | MONITORED | 輪詢 | metadata/status 出現 terminal transition | ALL_TERMINAL | 恰一次 collect（有 sink 時）→stdout 尾 CollectionReceipt→exit 0 |
| T3 | MONITORED | 輪詢 | status 仍 running 且 timebox（20m 預設；entry `silenceBudget` 覆寫）未到 | MONITORED | 續輪詢（零喚醒） |
| T4 | MONITORED | 輪詢 | status 仍 running 且 timebox 到 | HARVESTED | bounded 收割（partial 標記）→pending receipt（dedup）→exit 3 喚醒——**advisory，不 stop 不重派** |
| T5 | MONITORED | generation mismatch／registry entry 消失 | metadata 異動對照 | （hard-death fast path） | **立即 wake**（exit 2），不等 timebox——禁 retry |
| T6 | 任意 | 佈局錨點缺失／registry 缺 entry／JSON 不可解析 | adapter 查證失敗 | UNKNOWN | fail-loud 診斷（exit 1），零誤報 |
| T7 | （wake 後） | 主 session 處置 | TaskStop→verify→RETRY_SAFE 三問 | — | **互動 session**：主 session 介入判斷重派；**deepwork／無人在場**：收割→TaskStop→**自動重派一次**（新 attempt_id），二連失敗停止弧線留報告（autonomous-execution 授權，user 0920 裁決） |
| T8 | STOP_REQUESTED | verification | grace 內 metadata terminal＋cursors 靜止 | STOP_CONFIRMED | harvest B/delta（主 session 以 `--harvest-delta` 呼叫）→RETRY_SAFE 判定 |
| T9 | STOP_REQUESTED | verification | 仍有寫入者 | STOP_INCOMPLETE | 禁重派＋detached child 處置清單 |

不變量：watcher 代碼面零 stop／重派路徑（TaskStop／重派＝主 session 或
deepwork 授權的自動鏈，歸 S3 doctrine）；watcher 不做活/死宣稱；fd lease／
表面推進＝telemetry（不進判準）；terminal transition＝唯一權威狀態訊號。
wake 對「第一個到期」收割即 exit——其餘 entry 中止監視，主 session 處置後
重啟 watcher 續監（v1 從簡）。

偏差 ledger（v2 pivot 增補；v1 項隨移除面註銷——結案時補卡面 ledger）
------------------------------------------------------------------------------
1. 觀察面路徑記法：EP `sess_<taskId>` 前綴 vs 機器實證目錄名＝taskId 全形
   ——以機器佈局為準（v1 項保留）。
2. registry 存 taskId（S2 schema）非 EP S1 文句的 agentId——adapter 以
   `sess_subagent_<rest>→<rest>` 機械映射推 agentId 再 glob（v1 項保留）。
3.〔v2〕lease probe 失敗＝`exec_lease_checked=False` telemetry gap（v1 對
   running 報 unknown fail-loud）——lease 降 telemetry 後不再構成查證失敗；
   `--verify` 對 checked=False 維持 fail-closed STOP_INCOMPLETE（F-1/F-11
   保留）。
4. verify 模式 exit 延伸面（0=CONFIRMED／4=INCOMPLETE）——frozen exit 表為
   主迴圈 wake 語義，INCOMPLETE 以 stdout 尾行 `state` 機判（EP review F2；
   v1 項保留）。
5.〔v2〕harvest rollout tail 存在才收（subagent 無 rollout——K1）；manifest
   `tails.rollout.absent` 標記；transcript/task.output tail 未納入（未來
   工作——「收割器不變」約束下的最小變更）。
6. registry 監視集異動分流（F-4）：減項／attempt 變更＝exit 2；純增項＝
   吸納續 watch（v1 項保留）。
7. lsof exit 1 歧義（F-2）：stderr 非空＝錯誤→None；空＝無命中→[]（v1 項
   保留——probe 仍服務 telemetry＋verify 面）。
8. lease 路徑 realpath 正規化（F-3）：/tmp vs /private/tmp symlink 實證
   （v1 項保留）。
9. timestamp 不可解析＝fail-loud（F-6）：registry createdAt→registry-schema；
   metadata createdAt 對稱→metadata-corrupt（v1 項保留——createdAt 兼任
   timebox 起點，解析失敗＝禁判）。
10.〔v2〕wake 語彙改名：stdout 尾 JSON `state`＝`timebox-wake`（v1
   `freeze-wake`）、elapsed 欄＝`timeboxElapsedMin`——v2 語義誠實面；exit
   契約（0/2/3/1）與 dedup key（taskId＋attemptId）不變。
11.〔v2〕T2 all-terminal 新增 sink collect（CollectionReceipt——EP v2 表逐字
   要求，v1 無此步）；sink 相對路徑以 workspace 根（registry 上層目錄）解析。
12.〔D-A〕registry `interventionPolicy` 讀寫面不對稱：寫面明確給錯＝fail-loud、
   讀面缺省/未知值＝fail-safe coerce interactive（codex amendment ③——保守
   方向：誤判 autonomous 觸發自動鏈比多一次人工介入危險）。
13.〔D-B〕retryBudget ledger 以 taskId 為 logicalJobId（跨 attempt 續計——
   F4「同 task 換 attempt＝重派」語義的對偶）；帳損壞不 fail-loud 整個 wake
   而 fail-safe budgetRemaining=0（wake 本身仍發——收割證據不因帳壞而失）。
14.〔D-C〕watcher 端 TOCTOU recheck 落在收割 re-status（harvest 內建第二讀）
   ——controller 端 TaskStop 前的 recheck 走 `--verify`（receipt suggestedAction
   明列順序）；兩層 recheck 讀同一權威訊號（metadata status）。
15.〔codex amendment 未納入面〕① `silenceBudget`→`timeboxMinutes` 改名、
   ⑦ timebox 時間源改 eligible_elapsed（只計 observed-running 段）——EP v2
   POTION 已載，非本輪 D-A..D-D 範圍，隨 impl follow-up；④ STOP_INCOMPLETE
   deepwork bounded remediation 歸 S3 doctrine（非代碼面）。
   定性更名（EP amendment）：本物＝**timeboxed attempt supervisor**（三結果
   TERMINAL／TIMEBOX_EXPIRED／UNKNOWN-HARD_DEATH；所有 stop/retry 歸
   controller policy）。
16.〔AIR-160〕heartbeat sidecar 讀面為 T1-T9 frozen 主體的外掛 advisory 輸入
   （契約單一源＝agent-workflow SKILL「Worker supervision contract」節）：狀
   態機表與 exit code 零變；exit 3 觸發源增一（timebox 到期→stale-advisory
   提前喚醒）——「advisory 不 stop 不重派」語義不變；stale-advisory 不收割
   不記帳，與 T4 的分流以 stdout 尾 `state` 欄機判（先例＝偏差 4/10）；
   registry schema 增 `expectedHeartbeat?`＋`heartbeatFile?` 成對欄位。

exit 契約（frozen——watcher 主迴圈）
-------------------------------------
- 0＝正常收場（含空 registry、全 terminal〔stdout 尾附 CollectionReceipt〕）
- 2＝hard-death wake（generation mismatch／metadata 消失／registry entry 異動）
- 3＝advisory wake（timebox wake——stdout 尾附 harvest receipt JSON＋pending
  intervention；或 stale-advisory——heartbeat 斷訊提前醒〔AIR-160〕，不收割不
  記帳；兩者皆 advisory——不 stop 不重派）
- 其他非零＝內部錯／fail-loud（診斷至 stderr＋stdout 尾行狀態 JSON；本檔
  用 1）
- verification 模式延伸面（`--verify`——frozen 表為主迴圈 wake 語義，verify
  以 stdout 尾行 `state` 欄為機械判準）：0＝STOP_CONFIRMED、4＝
  STOP_INCOMPLETE（禁重派）、1＝fail-loud
- 註冊模式延伸面（`--register`，S2）：0＝registered、1＝fail-loud（欄位
  無效／schema 不符／重註冊；stdout 尾行 `state`＝registered／unknown）
- probe 模式延伸面（`--probe`，AIR-162）：0＝verdict 成立（MONITORED／
  TERMINAL／TIMEBOX_EXPIRED）、2＝HARD_DEATH_EVIDENCE（鏡像 frozen
  hard-death wake）、1＝UNKNOWN fail-loud；機械判準＝stdout 尾行 JSON 的
  `supervisionState` 欄（先例＝偏差 4 的 verify 延伸）

stdout：compact progress log＋尾行狀態／receipt JSON（單行，機械可判）；
stderr＝診斷。

用法
----
    uv run python scripts/harness_waiter.py <registry>
        [--poll-interval SEC] [--timebox-min MIN] [--max-cycles N]
    uv run python scripts/harness_waiter.py <registry> --verify <taskId>
        [--grace SEC]
    uv run python scripts/harness_waiter.py <registry> --probe <taskId>
        [--timebox-min MIN]
    uv run python scripts/harness_waiter.py <registry> --harvest-delta \
        <taskId> <manifestPath>
    uv run python scripts/harness_waiter.py <registry> --register <taskId>
        --attempt-id <id> --sink <path> [--expected <json>]
        [--surviving-handle HANDLE]... [--silence-budget-min MIN]
        [--intervention-policy interactive|autonomous_once]
        [--expected-heartbeat --heartbeat-file PATH]

registry＝workspace-local `.agent-tmp/liveness-registry.json`（寫入面＝
`--register`；atomic write 契約——watcher 逐輪重讀偵測 entry 異動）。schema：
`{"entries": [{taskId, attemptId, createdAt, sink, expected,
survivingHandles[], silenceBudget?, interventionPolicy?, expectedHeartbeat?,
heartbeatFile?}]}`；watcher 讀面：檔缺席＝fail-loud；entries 空＝exit 0
（等待語義：無可監視物）。register 寫面：同 taskId 重註冊＝fail-loud（新
attempt 前先移除舊 entry）；既有檔損壞／schema 不符＝fail-loud 禁覆蓋；
`createdAt`＝generation anchor，由 register 自 agent metadata 機械讀取（**非
牆鐘**——T5 對照基準＋v2 timebox 起點，寫牆鐘＝每次輪詢 hard-death）；
`sink`/`expected`＝AIR-135.7 AC#2 bounded receipt 欄位投影；
`survivingHandles`＝dispatch 前已知 detached job 的 ownership handle（in-
harness brief 禁未登記 long-lived/daemonized child；--verify 面＝correctness
boundary）；`silenceBudget`＝timebox 分鐘（v2 重解釋；缺席＝20m 標準）；
`interventionPolicy`（D-A）＝`interactive｜autonomous_once`——invoking
session 當下寫入、watcher 只 echo 進 receipt（**兩軸分離**：policy 管「誰處
置」、retry_safe 管「可否重派」）；`expectedHeartbeat`＋`heartbeatFile`
（AIR-160 heartbeat 協議——child 寫自己的 sidecar，watcher join 讀面）成對
出現，register 給 `--expected-heartbeat` 必帶 `--heartbeat-file`；缺省不寫
欄位、讀面缺省/未知值 fail-safe＝interactive、寫面明確給錯＝fail-loud。

收割（bounded）：metadata copy→表面 manifest（exec/artifact＋rollout 存在
才列；檔數上限）→rollout raw tail（位元組上限；存在才收；JSONL 收 raw
bytes——append 中末行半截合法，kill 後再解析）；超限 `harvestPartial=true`
照樣標。pending intervention receipt＝
`<workspace>/.agent-tmp/liveness/pending/<taskId>.json`，dedup key＝
taskId＋attemptId，已存在同 attempt 不重發。

retry budget（D-B）：同一 logical job（taskId 跨 attempt——F4 語義）
`AUTO_RETRY_BUDGET＝1`——attempt-1 timebox expiry 經 STOP_CONFIRMED＋
RETRY_SAFE 後消耗 budget 派 attempt-2（新 attemptId，**全新 timebox**）；
attempt-2 再 expiry→收割/stop/verify 後 terminal report、budget=0、無
attempt-3。帳檔＝`<liveness>/budget/<taskId>.json`（watcher 於 T4 wake 記
帳；同 attempt 重跑 dedup 不重複消耗；帳損壞＝fail-safe budgetRemaining=0
＋自癒重寫）。terminal failure／UNKNOWN／generation mismatch／
STOP_INCOMPLETE／terminal-race 各有 disposition，**不消耗 budget**。

pre-TaskStop terminal recheck（D-C）：expiry receipt 的 `suggestedAction`＝
明列處置順序——`harvest A → wake → fresh terminal recheck（--verify 重讀
metadata status：唯一允許的權威 terminal 訊號，TOCTOU 關閉——非 liveness
inference 偷渡）→〔terminal：final collect 不 stop 不 retry／running：
TaskStop → STOP verify → harvest B＋sink validation〕→ RETRY_SAFE &&
budgetRemaining>0 ? 新 attempt : halt`。收割 re-status 即 watcher 端的
recheck：命中 terminal（terminal-race）＝wake receipt 附 finalCollection、
零 stop 零 retry。

STOP fencing oracle（D-D，`--verify`）：STOP_CONFIRMED＝三項同時成立——
① metadata terminal；② 所有已註冊 owned handles quiescent（grace 觀察窗
前後 stat 不變）/collected（窗內消失）；③ authoritative sink grace 內無
writer（窗前後 stat 不變）。無法歸屬 handle（存在非普通檔/不可讀）→
STOP_INCOMPLETE；survivingHandles＝correctness boundary 非 telemetry。
exec lease probe＝寫入者面保留（active lease／probe 不可判定→
STOP_INCOMPLETE fail-closed）。

heartbeat sidecar 讀面（AIR-160；T1-T9 frozen 主體外掛——advisory 輸入）
--------------------------------------------------------
registry entry 可選 `expectedHeartbeat`（bool）＋`heartbeatFile`（workspace
相對路徑，與 sink 同解析面）。sidecar＝child 自己的 JSONL append-only 台帳
（格式單一源＝scripts/child_heartbeat.py 的 `child-heartbeat/1`：seq 自動遞
增、emittedAt/intervalSecs 由 helper 寫、半截行丟棄；本檔讀面為 standalone
最小投影，格式變更兩檔同步）。心跳週期（cadence）預設 60s（child CLI
`--interval-secs`），由 row `intervalSecs` 自載宣告；**stale 門檻＝2×週期**。
sweep 每輪對 expectedHeartbeat=true 且 timebox 未到（PollFresh）的 entry
join 讀 sidecar，三分支：

- **fresh**（本 attempt 最新記錄 age ≤ 2×週期）→ telemetry
  `heartbeat-fresh`——壓 advisory（recent-checkin 續等——heartbeat 只證明
  T 時刻執行過 emitter，不證明現在活著）；**禁延 timebox**
  （heartbeat 永不覆蓋 timebox／terminal——timebox 到期照醒，wake receipt 附
  `heartbeat.verdict` 供 parent 自選處置）
- **stale**（記錄存在但 age > 2×週期）→ `STALE_ADVISORY` 提前喚醒（exit
  3，stdout 尾 `state=stale-advisory`——advisory，不 stop 不重派，**stale 不
  判死**；不收割、不發 pending receipt、不消耗 retry budget）
- **missing**（無本 attempt 記錄且註冊起年齡 > 2×週期）→ telemetry
  `heartbeat_missing`（L0）——**缺席合法**（pilot 外 role／未回報皆合法），
  禁失敗禁喚醒；註冊未滿 2×週期的啟動窗＝零輸出

sidecar 檔缺席／不可讀＝丟棄該面（telemetry gap，非 fail-loud——heartbeat
是 advisory 輸入，禁拖垮 supervisor）；行級讀面與寫面 record contract 對稱
驗證（schema/taskId/attemptId/state/seq/intervalSecs/emittedAt 全欄位——
不合形行、attemptId 或 taskId 不符行、**末行無換行的 torn tail** 皆丟棄）。
ownership：registration 與 collected 都 parent 專屬；child 禁
寫 parent registry、禁自報 collected（偽造禁令——契約單一源＝
skills/agent-workflow/SKILL.md「Worker supervision contract」節）。順位：
hard-death > unknown > timebox-frozen（T4 主體）> stale——stale 與 timebox
到期同輪命中走 T4 收割路徑（stale 記進 wake receipt）。

probe mode（AIR-162——唯讀聚合；T1-T9 frozen 主體零變）
--------------------------------------------------------
`--probe <taskId>`：輸入 worker id，唯讀聚合 registry row／harness
metadata／heartbeat sidecar／workspace 觀察面，輸出分離兩軸 structured
JSON（schema `supervision-probe/1`）。零處置（不 stop 不重派不收割不記
帳）、零 registry 寫入；宿主＝本檔 probe mode（避免第二份死亡語義實作——
card AIR-162 已決策⑥）。雙腿設計源＝.agent-tmp/air-135-disc/
detection-{codex,muse}-result.md。

證據分級對照表（A-D；死亡宣稱僅 A 級——card AIR-162 已決策②③）：

| 級 | 內容 | 例 |
|---|---|---|
| A（authoritative） | harness 權威狀態訊號 | metadata terminal、generation mismatch（registry createdAt 對照）、已註冊身份 metadata 消失、timebox 到期（牆鐘事實） |
| B（corroborated） | 可歸因執行證據 | child heartbeat（taskId＋attemptId 可歸因）fresh |
| C（single weak） | 單一弱訊號 | registry row、native running row（可尋址／lifecycle intent，非 process liveness）、身份窗內 workspace 活動 |
| D（absence） | 缺席／無法歸因 | output 缺席、transcript mtime、ping 不在冊、registry 缺席——**永不支撐死亡** |

supervisionState 五態（僅 A 級證據可產生前三者）：
- TERMINAL：metadata status terminal（A）——唯一權威狀態訊號
- HARD_DEATH_EVIDENCE：generation mismatch／已註冊身份 metadata 消失（A）
  ——禁 retry；exit 2 鏡像 watcher hard-death wake 語義
- TIMEBOX_EXPIRED：running 超 timebox（A 級時間盒事實）——**不宣稱 dead**；
  處置照 T4 鏈（harvest→recheck→fence→RETRY_SAFE），probe 本身零處置
- MONITORED：running 且 timebox 未到（無不良證據）
- UNKNOWN：無法判定（exit 1＋manualReview=true，禁猜）——含「無 registry
  row 無 metadata」的 lookup miss（never-existed／reaped／打錯 id 不可區
  分，D 級缺席禁推死）

observations 三欄（與 supervisionState 分離——已決策①）：
- recentExecution：heartbeat fresh=yes（B）／stale=no（最新可歸因執行已逾
  2×週期門檻）／缺席或未設定=unknown（D 級缺席合法，禁推 no）
- addressable：native running row=yes（C：可尋址／lifecycle intent）／
  terminal=no／錨點缺席或損壞=unknown（lookup miss 禁推不可尋址）
- workspaceActivity：attempt 身份窗綁定（繫窗規則：registry.createdAt ≤ mtime ≤ now，已決策④）——窗內活動=yes／面上檔案全在窗外=no／無可觀察檔案或
  無窗錨點=unknown。歸因面：exec/artifact 目錄（路徑即 taskId 身份，機械
  歸因）＋registry 登記面（sink／survivingHandles——共享面）。共享面窗內
  活動或未來 mtime（時鐘異常）＝attribution_ambiguous（升 manualReview）。
  mtime／表面活動永不升級為 heartbeat、永不進死亡判準（K1 證偽——v2 已
  移除靜默計數，禁回滲）。窗錨點缺席（未註冊）時 workspace 活動不可綁定
  身份窗，觀察值維持 unknown。

strongestEvidence：A＞B＞C＞D 取最強（A 態恆 A；heartbeat fresh＝B；
registry row／running row／窗內活動任一＝C；僅缺席面＝D）。
manualReview：UNKNOWN 或 attribution_ambiguous 時 true；其餘 false——機械
verdict 的處置照既有鏈，人工判讀旗只為升級面。

ping 偵測節（AIR-162 五態矩陣結論——AC#3 偵測節吸收）
--------------------------------------------------------
矩陣記錄落點＝.agent-tmp/ping-matrix/（matrix.json／matrix.md／
contract-suggestion.md；2026-09-22 真機執行，ZCode 3.14.3 macOS arm64，
六 cell＝running〔self-verified live〕／completed-retained／failed／
stopped／reaped〔exec face 在、metadata 缺席的自然樣本〕／nonexistent）。

**ping 正式語義（矩陣凍結結論）**：TaskOutput／SendMessage 在 ZCode 為
parent session in-conversation 工具、**無 script CLI 面**（工具面機械探測
實證）——probe v1 零 ping 欄，reachability 判定全走被動面；in-conversation
ping 失敗＝「查詢面此刻找不到 active target」（NOT_ADDRESSABLE／不在冊），
⊃｛死、完成後被清、從未存在、查詢面錯｝——**禁死亡推論**；nonce ACK 可升
B 級一節仍未凍結（留 parent session 以 sacrificial workers 實驗——後續卡）。
SendMessage＝mutating probe，契約凍結前禁對真 worker 使用。

**被動查詢面正式語義（矩陣實證——probe 正式語義）**：
- metadata-status：五態可機械區分（running/completed/failed/stopped 逐字
  互異；terminal transition＝A 級唯一來源）；reaped 與 nonexistent 同文
  MISS——**metadata lookup miss ≠ 死亡**（本 probe 據此把無 registry row
  的錨點缺席判 UNKNOWN 而非 HARD_DEATH）。
- exec face：可機械區分 reaped（面在）與 nonexistent（全缺席）——但兩者
  皆非「死」，存在性 ≠ 活性，歸 UNKNOWN／needs_human 面。
- lsof-exec-lease：六格互異（live cell 唯一 LEASE HELD）＝process-presence
  訊號（C 級可尋址性），禁升 liveness／progress（K1）。
- output face：**output 缺席與活性並存實機實證成立**（live running cell
  output.txt/task.output 皆 ABSENT、同格 lease HELD）——D 級 output 缺席
  禁進任何判準（含 probe、含人工臨場判讀；09-22 marshal 誤判事故觸發面）。
- side effect：全部被動面查詢前後 stat 對照零變——唯讀安全。
"""

import argparse
import glob as glob_mod
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

WATCHER_NAME = "harness_waiter"
WAKE_RECEIPT_SCHEMA = "liveness-wake-receipt/1"
PENDING_RECEIPT_SCHEMA = "liveness-pending-intervention/1"
HARVEST_MANIFEST_SCHEMA = "harness-harvest-manifest/1"
HARVEST_DELTA_SCHEMA = "harness-harvest-delta/1"
COLLECTION_RECEIPT_SCHEMA = "harness-collection-receipt/1"
PROBE_SCHEMA = "supervision-probe/1"  # AIR-162 --probe 唯讀聚合輸出

EXIT_OK = 0
EXIT_FAILLOUD = 1
EXIT_HARD_DEATH = 2
EXIT_FREEZE = 3
EXIT_VERIFY_INCOMPLETE = 4

DEFAULT_TIMEBOX_MIN = 20.0
# rig/測試用覆寫（TC-4 dogfood）——env 設定時連同 argparse default 一併調整；
# env 名保留 v1 `HARNESS_WAITER_FREEZE_MIN`（改名相容）
TIMEBOX_MIN = float(os.environ.get("HARNESS_WAITER_FREEZE_MIN", DEFAULT_TIMEBOX_MIN))
DEFAULT_POLL_INTERVAL_S = 60.0
DEFAULT_VERIFICATION_GRACE_S = 30.0
POLL_GAP_FACTOR = 2.0  # gap > interval×此倍數＝異常（機器睡眠）→扣除間隔
# AIR-160：stale 門檻＝週期×此倍數——週期以 sidecar row `intervalSecs` 宣告為
# 準（無有效記錄回落 HEARTBEAT_PERIOD_S_DEFAULT）
HEARTBEAT_STALE_FACTOR = 2.0
HEARTBEAT_SCHEMA = "child-heartbeat/1"  # 格式單一源＝scripts/child_heartbeat.py
HEARTBEAT_STATES = frozenset({"working", "done"})  # child 禁自報 collected
HEARTBEAT_PERIOD_S_DEFAULT = 60.0  # 契約預設週期（＝child CLI --interval-secs 預設）

TERMINAL_STATES = frozenset({"completed", "failed", "stopped"})

# D-A：interventionPolicy 兩軸分離——policy 管「誰處置」（watcher 只 echo）、
# retry_safe 管「可否重派」（S3 doctrine 三問）；缺省/未知值 fail-safe＝interactive
INTERVENTION_POLICIES = frozenset({"interactive", "autonomous_once"})
# D-B：同一 logical job 的自動重派預算（attempt-1 expiry 經 STOP_CONFIRMED＋
# RETRY_SAFE 後消耗、派 attempt-2 全新 timebox；attempt-2 expiry＝terminal
# report 無 attempt-3）；terminal failure／UNKNOWN／generation mismatch／
# STOP_INCOMPLETE 各有 disposition，不消耗 budget
AUTO_RETRY_BUDGET = 1

MAX_TAIL_BYTES = 65_536
MAX_MANIFEST_FILES = 2_000

_SUBAGENT_PREFIX = "sess_subagent_"
# Task tool spawn 的真實 id 前綴（AIR-160 追加，marshal dogfood 2026-09-22 實證）
_AGENT_PREFIX = "agent_"


# ---------------------------------------------------------------------------
# 路徑常數集中地（觀察面 frozen 定義的唯一落點）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ZCodeLayout:
    """ZCode CLI 觀察面路徑——cli_root 可注入（測試用 tmp_path，零真機依賴）."""

    cli_root: Path

    @classmethod
    def default(cls) -> "ZCodeLayout":
        return cls(cli_root=Path.home() / ".zcode" / "cli")

    @property
    def rollout_root(self) -> Path:
        return self.cli_root / "rollout"

    @property
    def exec_root(self) -> Path:
        return self.cli_root / "exec"

    @property
    def artifact_root(self) -> Path:
        return self.cli_root / "artifacts"

    @property
    def agents_root(self) -> Path:
        return self.cli_root / "agents"

    def rollout_file(self, task_id: str) -> Path:
        return self.rollout_root / f"model-io-{task_id}.jsonl"

    def exec_dir(self, task_id: str) -> Path:
        return self.exec_root / task_id

    def artifact_dir(self, task_id: str) -> Path:
        return self.artifact_root / task_id


def agent_id_from_task(task_id: str) -> str | None:
    """taskId→agentId 機械映射；非可註冊形→None.

    兩形：`sess_subagent_<rest>→<rest>`（childSessionId 全形，v1 機械映射）；
    `agent_<uuid>` 恒等映射（Task tool spawn 的 taskId 即 agentId——其
    childSessionId 全形＝sess_subagent_＋agent_<uuid>，寫面等價判定見
    run_register）。其餘（空 id／無前綴亂值）＝None 拒絕。
    """
    if task_id.startswith(_SUBAGENT_PREFIX):
        agent_id = task_id[len(_SUBAGENT_PREFIX) :]
        return agent_id or None
    if task_id.startswith(_AGENT_PREFIX) and len(task_id) > len(_AGENT_PREFIX):
        return task_id
    return None


# ---------------------------------------------------------------------------
# 觀察結果型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Cursors:
    """寫入者面 cursor 快照（verify 靜止比對＋harvest resumed 判定用）.

    v2：rollout 欄位移除（K1 證偽——子 agent 無 per-task rollout）；只剩
    artifact＋exec 兩面；None＝該面目錄缺席＝合法。
    """

    artifact_mtime_ns: int | None
    artifact_size: int | None
    exec_mtime_ns: int | None
    exec_size: int | None


@dataclass(frozen=True)
class TaskStatus:
    """`status(taskId)` 的可判讀結果（EP S1 欄位集）.

    exec_lease_checked＝False 表示 lease 面未查成（prober 不可判定）——v2
    lease 僅 telemetry＋verify 面，probe 失敗不再 fail-loud 判準面；verify
    對未查成 fail-closed STOP_INCOMPLETE（F-1 禁假確認）。last_activity/
    output_cursor 為 exec＋artifact 聚合 telemetry，不進判準。
    """

    task_id: str
    state: str
    generation: tuple[str, str]  # (childSessionId, createdAt)
    created_at: str
    last_activity: datetime | None
    output_cursor: int
    exec_lease: tuple[str, ...]
    exec_lease_checked: bool
    cursors: Cursors


@dataclass(frozen=True)
class UnknownFace:
    """fail-loud 面：原因明示，禁猜禁誤報（T6）。"""

    reason: str
    detail: str = ""


def lsof_lease_prober(paths: Sequence[Path]) -> list[str] | None:
    """lsof 偵測 open fd lease；回 None＝lsof 不可判定（fail-loud 面）.

    lsof exit 0＝有命中；exit 1＝「無命中或錯誤」——二者不可由 exit code
    区分（實測皆 exit 1）：stderr 非空→錯誤→None（F-2），空→無命中→[]。
    其他 exit／逾時／找不到 binary＝None（禁猜）。路徑比對兩側先
    realpath 正規化（F-3：/tmp vs /private/tmp symlink 實證），回報值維持
    caller 傳入路徑。`-F pn` machine-readable 輸出，`n` 行為路徑。
    """
    if not paths:
        return []
    cmd = ["lsof", "-F", "pn", "--", *[str(p) for p in paths]]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 1 and proc.stderr.strip():
        return None  # exit 1 ＋ stderr 非空＝查詢錯誤（如檔案不存在），非無命中
    if proc.returncode not in (0, 1):
        return None
    reported = {
        os.path.realpath(line[1:])
        for line in proc.stdout.splitlines()
        if line.startswith("n")
    }
    return [str(p) for p in paths if os.path.realpath(str(p)) in reported]


def _files_in_dir(d: Path) -> list[Path]:
    """單層檔案列舉（exec/artifact 目錄為 flat 佈局）；缺席→空."""
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file())


def _newest_in_dir(d: Path) -> tuple[int | None, int | None]:
    """可選表面（exec/artifact）最新檔；檔案 stat 失敗（清除競速）→跳過該檔."""
    files = _files_in_dir(d)
    stats = []
    for p in files:
        try:
            stats.append(p.stat())
        except OSError:
            continue  # 列舉後消失＝表面清理競速——可選面不因它 fail-loud
    if not stats:
        return None, None
    newest = max(stats, key=lambda s: s.st_mtime_ns)
    return newest.st_mtime_ns, newest.st_size


class ZCodeLivenessSource:
    """四觀察面 adapter——路徑解析＋錨點存在性＋fail-loud（B path 換源不動語義）."""

    def __init__(
        self,
        layout: ZCodeLayout,
        lease_prober: Callable[[Sequence[Path]], list[str] | None] | None = None,
    ) -> None:
        self._layout = layout
        self._prober = lease_prober or lsof_lease_prober

    @property
    def layout(self) -> ZCodeLayout:
        return self._layout

    def resolve_metadata(self, agent_id: str) -> Path | UnknownFace:
        pattern = str(self._layout.agents_root / "sess_*" / agent_id / "metadata.json")
        hits = sorted(Path(p) for p in glob_mod.glob(pattern))
        if not hits:
            return UnknownFace("metadata-anchor-missing", f"glob 零命中：{pattern}")
        if len(hits) > 1:
            return UnknownFace(
                "metadata-glob-ambiguous",
                f"{len(hits)} 命中：{[str(h) for h in hits]}",
            )
        return hits[0]

    def read_metadata(self, path: Path) -> dict | UnknownFace:
        try:
            raw = path.read_text()
        except OSError as exc:
            return UnknownFace("metadata-unreadable", str(exc))
        try:
            meta = json.loads(raw)
        except json.JSONDecodeError as exc:
            # 半寫 torn read 同面——metadata 兩點寫入外的讀撞＝不可解析
            return UnknownFace("metadata-unparseable", str(exc))
        if not isinstance(meta, dict):
            return UnknownFace("metadata-corrupt", "非 JSON object")
        for key in ("agentId", "childSessionId", "createdAt", "status"):
            if not isinstance(meta.get(key), str) or not meta[key]:
                return UnknownFace("metadata-corrupt", f"缺必要欄位：{key}")
        if _parse_iso(meta["createdAt"]) is None:
            # F-6 對稱面：timestamp 不可解析＝禁靜默跳過 generation 對照
            return UnknownFace(
                "metadata-corrupt", f"createdAt 不可解析：{meta['createdAt']}"
            )
        return meta

    def status(self, task_id: str) -> TaskStatus | UnknownFace:
        """v2 觀察面：metadata status＋exec/artifact telemetry（rollout 移除）.

        K1 證偽後 running 期不要求任何表面錨點——可判讀性只依 metadata（含
        createdAt：timebox 起點）。lease probe 失敗＝checked=False（telemetry
        gap，不 fail-loud）；verify 端另行 fail-closed。
        """
        agent_id = agent_id_from_task(task_id)
        if agent_id is None:
            return UnknownFace("invalid-task-id", task_id)
        meta_path = self.resolve_metadata(agent_id)
        if isinstance(meta_path, UnknownFace):
            return meta_path
        meta = self.read_metadata(meta_path)
        if isinstance(meta, UnknownFace):
            return meta
        state = meta["status"]
        a_mtime, a_size = _newest_in_dir(self._layout.artifact_dir(task_id))
        e_mtime, e_size = _newest_in_dir(self._layout.exec_dir(task_id))
        cursors = Cursors(
            artifact_mtime_ns=a_mtime,
            artifact_size=a_size,
            exec_mtime_ns=e_mtime,
            exec_size=e_size,
        )
        # 寫入者面（F-1）：terminal 亦列舉 exec 並 probe lease——verify 的
        # STOP_CONFIRMED 不得跳過 detached writer 檢查。v2：lease＝telemetry
        # ＋verify 面，probe 失敗＝checked=False（不進判準，不 fail-loud）
        exec_files = _files_in_dir(self._layout.exec_dir(task_id))
        raw_lease = self._prober(exec_files) if exec_files else []
        checked = raw_lease is not None
        lease = tuple(str(p) for p in raw_lease) if checked else ()
        sizes = [v for v in (a_size, e_size) if v is not None]
        mtimes = [v for v in (a_mtime, e_mtime) if v is not None]
        return TaskStatus(
            task_id=task_id,
            state=state,
            generation=(meta["childSessionId"], meta["createdAt"]),
            created_at=meta["createdAt"],
            last_activity=(
                datetime.fromtimestamp(max(mtimes) / 1e9, tz=UTC) if mtimes else None
            ),
            output_cursor=sum(sizes),
            exec_lease=lease,
            exec_lease_checked=checked,
            cursors=cursors,
        )


# ---------------------------------------------------------------------------
# registry（S2 schema 的 S1 讀取面）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegistryEntry:
    task_id: str
    attempt_id: str
    created_at: str
    sink: str
    expected: object
    surviving_handles: tuple[str, ...]
    silence_budget_min: float | None
    intervention_policy: str = "interactive"
    expected_heartbeat: bool = False  # AIR-160：heartbeat 協議——與 heartbeatFile 成對
    heartbeat_file: str | None = None


def _require_str(entry: dict, key: str) -> str | None:
    value = entry.get(key)
    return value if isinstance(value, str) and value else None


def load_registry(path: Path) -> list[RegistryEntry] | UnknownFace:
    """registry 讀取＋schema 校驗——檔缺席＝錨點缺失 fail-loud；空＝[]（exit 0）."""
    if not path.is_file():
        return UnknownFace("registry-missing", str(path))
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return UnknownFace("registry-unparseable", str(exc))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        return UnknownFace("registry-schema", '需 {"entries": [...]}')
    entries: list[RegistryEntry] = []
    for i, raw in enumerate(payload["entries"]):
        if not isinstance(raw, dict):
            return UnknownFace("registry-schema", f"entries[{i}] 非 object")
        task_id = _require_str(raw, "taskId")
        attempt_id = _require_str(raw, "attemptId")
        created_at = _require_str(raw, "createdAt")
        sink = _require_str(raw, "sink")
        if task_id is None or attempt_id is None or created_at is None or sink is None:
            return UnknownFace(
                "registry-schema",
                f"entries[{i}] 缺必要欄位 taskId/attemptId/createdAt/sink",
            )
        if _parse_iso(created_at) is None:
            # F-6：T5 fast path 的對照基準不可解析＝禁靜默跳過——fail-loud
            return UnknownFace(
                "registry-schema",
                f"entries[{i}] createdAt 不可解析：{created_at}",
            )
        handles_raw = raw.get("survivingHandles")
        if not isinstance(handles_raw, list) or not all(
            isinstance(h, str) for h in handles_raw
        ):
            return UnknownFace(
                "registry-schema", f"entries[{i}] survivingHandles 需 list[str]"
            )
        budget_raw = raw.get("silenceBudget")
        budget: float | None = None
        if budget_raw is not None:
            if not isinstance(budget_raw, (int, float)) or isinstance(budget_raw, bool):
                return UnknownFace(
                    "registry-schema", f"entries[{i}] silenceBudget 需數值（分鐘）"
                )
            if not (budget_raw > 0):
                return UnknownFace(
                    "registry-schema", f"entries[{i}] silenceBudget 需正數"
                )
            budget = float(budget_raw)
        # D-A：interventionPolicy 缺席/未知值 fail-safe＝interactive（保守方向
        # ——interactive＝主 session 介入，禁誤判 autonomous 觸發自動鏈）
        policy_raw = raw.get("interventionPolicy")
        policy = policy_raw if policy_raw in INTERVENTION_POLICIES else "interactive"
        # AIR-160：expectedHeartbeat 需 boolean，且 =true 時需 heartbeatFile 成對
        hb_expected_raw = raw.get("expectedHeartbeat")
        if hb_expected_raw is not None and not isinstance(hb_expected_raw, bool):
            return UnknownFace(
                "registry-schema", f"entries[{i}] expectedHeartbeat 需 boolean"
            )
        hb_file_raw = raw.get("heartbeatFile")
        if hb_file_raw is not None and not (
            isinstance(hb_file_raw, str) and hb_file_raw
        ):
            return UnknownFace(
                "registry-schema", f"entries[{i}] heartbeatFile 需非空字串"
            )
        if hb_expected_raw and hb_file_raw is None:
            return UnknownFace(
                "registry-schema",
                f"entries[{i}] expectedHeartbeat=true 需 heartbeatFile 成對",
            )
        entries.append(
            RegistryEntry(
                task_id=task_id,
                attempt_id=attempt_id,
                created_at=created_at,
                sink=sink,
                expected=raw.get("expected"),
                surviving_handles=tuple(handles_raw),
                silence_budget_min=budget,
                intervention_policy=policy,
                expected_heartbeat=bool(hb_expected_raw),
                heartbeat_file=hb_file_raw,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# 凍結判準（FreezeDetector）
# ---------------------------------------------------------------------------


@dataclass
class WatchState:
    """單 entry 的輪詢累積狀態（poll gap 扣除累積／T5 generation 對照）.

    v2：無靜默累積（timebox＝牆鐘年齡，非輪詢計數）——只累積「異常 gap 扣
    除額」；deducted_s 自 createdAt 年齡中扣除。
    """

    deducted_s: float = 0.0
    prev_poll_at: datetime | None = None
    generation: tuple[str, str] | None = None
    telemetry: tuple[str, ...] = ()


@dataclass(frozen=True)
class PollFresh:
    elapsed_s: float
    telemetry: tuple[str, ...] = ()


@dataclass(frozen=True)
class PollFrozen:
    elapsed_s: float
    cursors: Cursors


@dataclass(frozen=True)
class PollTerminal:
    state: str


@dataclass(frozen=True)
class PollHardDeath:
    reason: str


@dataclass(frozen=True)
class PollUnknown:
    reason: str
    detail: str = ""


PollResult = PollFresh | PollFrozen | PollTerminal | PollHardDeath | PollUnknown


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


class FreezeDetector:
    """timebox 判準（v2 frozen）：effective = now − createdAt − 異常 gap 扣除.

    不做活/死宣稱、不做靜默計數——表面推進／exec lease 不重置不豁免（只記
    telemetry）；時鐘回撥（gap<0 或 effective<0）＝該輪禁判，視為 Fresh＋
    telemetry `clock-rollback`。
    """

    def __init__(
        self,
        source: ZCodeLivenessSource,
        *,
        threshold_min: float = TIMEBOX_MIN,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    ) -> None:
        self._source = source
        self._threshold_min = threshold_min
        self._poll_interval_s = poll_interval_s

    def threshold_for(self, entry: RegistryEntry) -> float:
        if entry.silence_budget_min is not None:
            return entry.silence_budget_min
        return self._threshold_min

    def poll(
        self, entry: RegistryEntry, state: WatchState, now: datetime
    ) -> tuple[PollResult, WatchState]:
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            if st.reason == "metadata-anchor-missing":
                # T5：metadata 消失＝identity 不在——hard-death fast path
                return PollHardDeath("metadata-gone"), state
            return PollUnknown(st.reason, st.detail), state

        # T5：registry attempt createdAt 對照（首次 poll 即比——fast path）
        reg_created = _parse_iso(entry.created_at)
        meta_created = _parse_iso(st.created_at)
        if (
            reg_created is not None
            and meta_created is not None
            and (reg_created != meta_created)
        ):
            return PollHardDeath("generation-mismatch-registry-createdAt"), state
        # T5：輪詢間 generation（childSessionId＋createdAt）異動對照
        if state.generation is not None and st.generation != state.generation:
            return PollHardDeath("generation-mismatch"), state

        threshold_s = self.threshold_for(entry) * 60.0
        if st.state in TERMINAL_STATES:
            # T2：terminal transition＝唯一權威狀態訊號，先於 timebox 判定
            reset = WatchState(prev_poll_at=now, generation=st.generation)
            return PollTerminal(st.state), reset

        # T3/T4：timebox——effective = now − createdAt − 異常 gap 扣除
        gap = (
            None
            if state.prev_poll_at is None
            else (now - state.prev_poll_at).total_seconds()
        )
        telemetry: list[str] = []
        deducted = state.deducted_s
        rollback = False
        if gap is not None and gap < 0:
            # 時鐘回撥：elapsed<0 → Fresh＋telemetry（frozen 條款；禁判）
            telemetry.append("clock-rollback")
            rollback = True
        elif gap is not None and gap > self._poll_interval_s * POLL_GAP_FACTOR:
            # SM-7：poll gap 異常（機器睡眠）→扣除異常段（只記一個 interval）
            telemetry.append("poll-gap-deducted")
            deducted = state.deducted_s + (gap - self._poll_interval_s)
        if st.exec_lease:
            # v2：lease＝telemetry `exec-lease-held`——不豁免 timebox
            telemetry.append("exec-lease-held")

        raw_age = (now - meta_created).total_seconds() if meta_created else 0.0
        effective = raw_age - deducted
        if effective < 0:
            # createdAt 在未來／扣除越界＝時鐘不可信——禁判，Fresh＋telemetry
            telemetry.append("clock-rollback")
            rollback = True

        new_state = WatchState(
            deducted_s=deducted,
            prev_poll_at=now,
            generation=st.generation,
            telemetry=tuple(telemetry),
        )
        if rollback:
            return PollFresh(max(effective, 0.0), tuple(telemetry)), new_state
        if effective >= threshold_s:
            # T4：timebox 到——PollFrozen.cursors 供 harvest resumed 判定
            return PollFrozen(effective, st.cursors), new_state
        return PollFresh(effective, tuple(telemetry)), new_state


# ---------------------------------------------------------------------------
# 收割器（bounded；raw bytes；partial 標記）
# ---------------------------------------------------------------------------


def _sanitize(component: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", component)
    return cleaned or "unnamed"


def cursors_to_dict(c: Cursors) -> dict:
    return {
        "artifactMtimeNs": c.artifact_mtime_ns,
        "artifactSize": c.artifact_size,
        "execMtimeNs": c.exec_mtime_ns,
        "execSize": c.exec_size,
    }


class Harvester:
    """bounded 收割：manifest→metadata copy→rollout raw tail；超限 partial 標記."""

    def __init__(
        self,
        source: ZCodeLivenessSource,
        layout: ZCodeLayout,
        liveness_root: Path,
        *,
        max_tail_bytes: int = MAX_TAIL_BYTES,
        max_manifest_files: int = MAX_MANIFEST_FILES,
    ) -> None:
        self._source = source
        self._layout = layout
        self._liveness_root = liveness_root
        self._max_tail_bytes = max_tail_bytes
        self._max_manifest_files = max_manifest_files

    def _surface_files(self, task_id: str) -> list[tuple[str, Path]]:
        # v2：rollout 存在才列（K1——subagent 無 rollout；缺席非 fail-loud）
        pairs: list[tuple[str, Path]] = []
        rollout = self._layout.rollout_file(task_id)
        if rollout.is_file():
            pairs.append(("rollout", rollout))
        pairs += [
            ("artifact", p) for p in _files_in_dir(self._layout.artifact_dir(task_id))
        ]
        pairs += [("exec", p) for p in _files_in_dir(self._layout.exec_dir(task_id))]
        return pairs

    def _bundle_dir(self, task_id: str, attempt_id: str, leaf: str = "") -> Path:
        bundle = (
            self._liveness_root / "harvest" / _sanitize(task_id) / _sanitize(attempt_id)
        )
        if leaf:
            bundle = bundle / leaf
        bundle.mkdir(parents=True, exist_ok=True)
        return bundle

    def harvest(
        self, entry: RegistryEntry, freeze_cursors: Cursors | None = None
    ) -> tuple[dict, Path] | UnknownFace:
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            return st
        agent_id = agent_id_from_task(entry.task_id)
        meta_path = (
            self._source.resolve_metadata(agent_id)
            if agent_id is not None
            else UnknownFace("invalid-task-id", entry.task_id)
        )
        if isinstance(meta_path, UnknownFace):
            return meta_path
        bundle = self._bundle_dir(entry.task_id, entry.attempt_id)
        try:
            (bundle / "metadata.json").write_bytes(meta_path.read_bytes())
        except OSError as exc:
            return UnknownFace("harvest-metadata-copy-failed", str(exc))
        listing = self._surface_files(entry.task_id)
        truncated = len(listing) > self._max_manifest_files
        files = []
        for surface, path in listing[: self._max_manifest_files]:
            try:
                stat = path.stat()
            except OSError as exc:
                # F-10：收割 manifest 必須準確——stat 讀撞＝fail-loud 不收割
                return UnknownFace("harvest-stat-failed", str(exc))
            files.append(
                {
                    "surface": surface,
                    "path": str(path),
                    "size": stat.st_size,
                    "mtimeNs": stat.st_mtime_ns,
                }
            )
        # v2：rollout tail 存在才收（K1——subagent 無 rollout；缺席記 absent）
        rollout_path = self._layout.rollout_file(entry.task_id)
        tail = b""
        tail_absent = not rollout_path.is_file()
        tail_partial = False
        if not tail_absent:
            try:
                # F-8：seek-based tail——殭屍 rollout 可達數百 MB，禁全檔載入
                size = rollout_path.stat().st_size
                with rollout_path.open("rb") as fh:
                    fh.seek(max(0, size - self._max_tail_bytes))
                    tail = fh.read()
            except OSError as exc:
                return UnknownFace("harvest-rollout-read-failed", str(exc))
            tail_partial = size > len(tail)
            (bundle / "rollout.tail.jsonl").write_bytes(tail)
        resumed: bool | None = None
        if freeze_cursors is not None:
            resumed = st.cursors != freeze_cursors
        manifest = {
            "schema": HARVEST_MANIFEST_SCHEMA,
            "watcher": WATCHER_NAME,
            "taskId": entry.task_id,
            "agentId": agent_id,
            "attemptId": entry.attempt_id,
            "harvestAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            "harvestPartial": bool(truncated or tail_partial),
            "cursors": cursors_to_dict(st.cursors),
            "filesTruncated": truncated,
            "files": files,
            "tails": {
                "rollout": {
                    "path": "rollout.tail.jsonl",
                    "bytes": len(tail),
                    "sha256": hashlib.sha256(tail).hexdigest(),
                    "partial": tail_partial,
                    "absent": tail_absent,
                }
            },
            "metadata": {
                "path": "metadata.json",
                "status": st.state,
                "createdAt": st.created_at,
            },
            "resumedDuringQuarantine": resumed,
        }
        (bundle / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        return manifest, bundle

    def harvest_delta(
        self, entry: RegistryEntry, manifest_path: Path
    ) -> tuple[dict, Path] | UnknownFace:
        """STOP 後增量收割（harvest B；主 session 以 --harvest-delta 呼叫）."""
        try:
            prev = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            return UnknownFace("delta-prev-manifest-unparseable", str(exc))
        if (
            not isinstance(prev, dict)
            or prev.get("schema") != HARVEST_MANIFEST_SCHEMA
            or prev.get("taskId") != entry.task_id
            or not isinstance(prev.get("cursors"), dict)
        ):
            return UnknownFace(
                "delta-prev-manifest-schema",
                "需 harvest manifest（schema/taskId/cursors 對得上）",
            )
        st = self._source.status(entry.task_id)
        if isinstance(st, UnknownFace):
            return st
        listing = self._surface_files(entry.task_id)
        truncated = len(listing) > self._max_manifest_files
        prev_sizes = {
            f.get("path"): f.get("size")
            for f in prev.get("files", [])
            if isinstance(f, dict)
        }
        new_files: list[dict] = []
        grown_files: list[dict] = []
        for surface, path in listing[: self._max_manifest_files]:
            try:
                stat = path.stat()
            except OSError as exc:
                # F-10：delta 判準（寫入者偵測）必須準確——讀撞＝fail-loud
                return UnknownFace("harvest-stat-failed", str(exc))
            row = {
                "surface": surface,
                "path": str(path),
                "size": stat.st_size,
                "mtimeNs": stat.st_mtime_ns,
            }
            prev_size = prev_sizes.get(str(path))
            if prev_size is None:
                new_files.append(row)
            elif stat.st_size > prev_size:
                row["prevSize"] = prev_size
                grown_files.append(row)
        cursors = cursors_to_dict(st.cursors)
        resumed = cursors != prev["cursors"]
        attempt_id = (
            str(prev["attemptId"])
            if isinstance(prev.get("attemptId"), str)
            else "delta"
        )
        bundle = self._bundle_dir(entry.task_id, attempt_id, leaf="delta")
        delta = {
            "schema": HARVEST_DELTA_SCHEMA,
            "watcher": WATCHER_NAME,
            "taskId": entry.task_id,
            "attemptId": attempt_id,
            "prevManifestPath": str(manifest_path),
            "prevCursors": prev["cursors"],
            "cursors": cursors,
            "newFiles": new_files,
            "grownFiles": grown_files,
            "harvestPartial": truncated,
            "resumedDuringQuarantine": resumed,
        }
        (bundle / "manifest.json").write_text(
            json.dumps(delta, ensure_ascii=False, indent=2) + "\n"
        )
        return delta, bundle


def consume_retry_budget(liveness_root: Path, entry: RegistryEntry) -> dict:
    """D-B retry budget 記帳（T4 timebox expiry 專屬——其他路徑不消耗）.

    帳檔＝`<liveness>/budget/<taskId>.json`（logical job 跨 attempt 續計——
    同 taskId 新 attemptId＝重派，F4 語義）。同 attempt 重跑＝dedup 回報現
    值不重複消耗（對齊 pending receipt dedup 語義）；帳損壞＝fail-safe
    `budgetRemaining=0`（halt 方向安全——autonomous 過額外重派比漏重派危險）
    ＋帳檔自癒重寫。
    """
    path = liveness_root / "budget" / f"{_sanitize(entry.task_id)}.json"
    used = 0
    corrupt = False
    last_attempt: str | None = None
    if path.is_file():
        try:
            data = json.loads(path.read_text())
            raw = data.get("attemptsUsed")
            if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
                raise ValueError("attemptsUsed 需非負整數")
            used = raw
            la = data.get("lastAttemptId")
            last_attempt = la if isinstance(la, str) else None
        except (OSError, ValueError, json.JSONDecodeError, AttributeError):
            corrupt = True
            used = 0
            last_attempt = None
    if not corrupt and last_attempt == entry.attempt_id:
        return {
            "logicalJobId": entry.task_id,
            "attemptsUsed": used,
            "budgetRemaining": max(0, AUTO_RETRY_BUDGET - (used - 1)),
        }
    new_used = used + 1
    remaining = max(0, AUTO_RETRY_BUDGET - (new_used - 1))
    if corrupt:
        remaining = 0  # fail-safe：帳不可信＝禁自動重派
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "logicalJobId": entry.task_id,
                "attemptsUsed": new_used,
                "lastAttemptId": entry.attempt_id,
                "updatedAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    budget: dict = {
        "logicalJobId": entry.task_id,
        "attemptsUsed": new_used,
        "budgetRemaining": remaining,
    }
    if corrupt:
        budget["corrupt"] = True
    return budget


def _stop_chain_suggestion(entry: RegistryEntry, bundle: Path) -> dict:
    """D-C：timebox expiry receipt 的 suggestedAction＝明列處置順序.

    順序＝controller（主 session／deepwork 授權鏈）執行面；watcher 只建議。
    兩軸分離：interventionPolicy 管「誰處置」、retry_safe 管「可否重派」。
    TOCTOU 關閉＝TaskStop 前重讀 metadata status（唯一允許的權威 terminal
    訊號——非 liveness inference 偷渡）。
    """
    return {
        "policy": entry.intervention_policy,
        "sequence": [
            {
                "step": "harvest-A",
                "status": "done",
                "manifestPath": str(bundle / "manifest.json"),
            },
            {"step": "wake", "status": "done"},
            {
                "step": "terminal-recheck",
                "status": "pending",
                "how": f"--verify {entry.task_id}——TaskStop 前重讀 metadata "
                "status（唯一權威 terminal 訊號，TOCTOU 關閉）",
            },
            {
                "step": "branch",
                "status": "pending",
                "terminal": "final collect（不 stop 不 retry）",
                "running": f"TaskStop {entry.task_id} → STOP verify → harvest B"
                "（--harvest-delta）＋sink validation",
            },
            {
                "step": "retry-gate",
                "status": "pending",
                "rule": "RETRY_SAFE && retryBudget.budgetRemaining>0 → 派新 "
                "attempt（新 attemptId，全新 timebox）；否則 halt 留報告",
            },
        ],
    }


def _final_collect_suggestion(
    entry: RegistryEntry, collection: dict, bundle: Path
) -> dict:
    """D-C terminal-race 分支：收割時已 terminal——final collect，不 stop 不 retry."""
    return {
        "policy": entry.intervention_policy,
        "sequence": [
            {
                "step": "harvest-A",
                "status": "done",
                "manifestPath": str(bundle / "manifest.json"),
            },
            {"step": "wake", "status": "done"},
            {
                "step": "terminal-recheck",
                "status": "terminal-at-harvest",
                "detail": "收割時重讀 metadata 即 terminal——TOCTOU 命中，TaskStop 免除",
            },
            {"step": "final-collect", "status": "done", "collection": collection},
            {"step": "halt", "status": "job terminal——不 stop 不 retry"},
        ],
    }


def write_pending_receipt(
    liveness_root: Path,
    entry: RegistryEntry,
    manifest: dict,
    harvest_dir: Path,
    *,
    elapsed_s: float,
    resumed: bool,
    retry_budget: dict | None = None,
    suggested: dict | None = None,
) -> Path:
    """pending intervention receipt——dedup key＝taskId＋attemptId，同 attempt 不重發."""
    pending_dir = liveness_root / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    path = pending_dir / f"{_sanitize(entry.task_id)}.json"
    if path.is_file():
        try:
            existing = json.loads(path.read_text())
        except json.JSONDecodeError:
            existing = None
        if isinstance(existing, dict) and existing.get("attemptId") == entry.attempt_id:
            return path  # dedup：已有 pending 不重發
    manifest_path = harvest_dir / "manifest.json"
    receipt = {
        "schema": PENDING_RECEIPT_SCHEMA,
        "taskId": entry.task_id,
        "attemptId": entry.attempt_id,
        "dedupKey": f"{entry.task_id}+{entry.attempt_id}",
        "interventionPolicy": entry.intervention_policy,
        "harvestDir": str(harvest_dir),
        "manifestPath": str(manifest_path),
        "survivingHandles": list(entry.surviving_handles),
        "timeboxElapsedMin": round(elapsed_s / 60.0, 2),
        "resumedDuringQuarantine": resumed,
        "retryBudget": retry_budget,
        "suggestedAction": suggested,
        "createdAt": datetime.now(tz=UTC).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return path


# ---------------------------------------------------------------------------
# 輸出 helpers
# ---------------------------------------------------------------------------


class _Writable(Protocol):
    """stdout/stderr 的最小寫入面（sys.stdout／TextIOBase／StringIO 共通）."""

    def write(self, s: str) -> int | None: ...

    def flush(self) -> None: ...


def _emit(file: _Writable, text: str) -> None:
    file.write(text + "\n")
    file.flush()


def _dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _emit_face(
    out: _Writable,
    err: _Writable,
    state: str,
    *,
    task_id: str | None,
    face: UnknownFace,
) -> int:
    _emit(
        out,
        _dumps(
            {
                "state": state,
                "taskId": task_id,
                "reason": face.reason,
                "detail": face.detail,
            }
        ),
    )
    _emit(err, f"[{WATCHER_NAME}] {state}: {face.reason} {face.detail}".rstrip())
    return EXIT_FAILLOUD


def _system_now() -> datetime:
    return datetime.now(tz=UTC)


def _anchors_from_expected(expected: object) -> list[str]:
    """expected 遞迴收字串為錨點清單（dispatcher 顯式給定，不過濾長度）."""
    if isinstance(expected, str):
        return [expected] if expected else []
    if isinstance(expected, dict):
        out: list[str] = []
        for v in expected.values():
            out.extend(_anchors_from_expected(v))
        return out
    if isinstance(expected, (list, tuple)):
        out = []
        for v in expected:
            out.extend(_anchors_from_expected(v))
        return out
    return []


def collect_sink(entry: RegistryEntry, sink_base: Path) -> dict:
    """sink 三步機驗（存在→非空→錨點）——T2 CollectionReceipt 的 row 面.

    AIR-135.7 AC#2 bounded receipt 投影：sink 相對路徑以 sink_base（workspace
    根）解析。delivery verdict 只是資訊面——terminal transition 才是權威，
    verdict 不影響 exit 0。
    """
    sink = Path(entry.sink)
    path = sink if sink.is_absolute() else sink_base / sink
    row: dict = {
        "taskId": entry.task_id,
        "sink": entry.sink,
        "expected": entry.expected,
        "l1Present": False,
        "l2NonEmpty": False,
        "anchorHits": [],
        "verdict": "sink-missing",
    }
    if not path.is_file():
        return row
    row["l1Present"] = True
    try:
        size = path.stat().st_size
        content = path.read_text(errors="replace")[:200_000] if size else ""
    except OSError:
        row["verdict"] = "sink-unreadable"
        return row
    row["l2NonEmpty"] = size > 0
    if size == 0:
        row["verdict"] = "sink-empty"
        return row
    anchors = _anchors_from_expected(entry.expected)
    if not anchors:
        row["verdict"] = "delivered"  # 無錨點條件＝存在＋非空即收
        return row
    hits = [a for a in anchors if a in content]
    row["anchorHits"] = hits
    row["verdict"] = "delivered" if hits else "anchor-missing"
    return row


# ---------------------------------------------------------------------------
# heartbeat sidecar join（AIR-160——advisory 輸入；T1-T9 frozen 主體外掛）
# ---------------------------------------------------------------------------


def _valid_heartbeat_record(
    rec: object, *, task_id: str, attempt_id: str
) -> dict | None:
    """record contract 驗證——與 scripts/child_heartbeat.py 寫面對稱.

    schema/taskId/attemptId/state/seq/intervalSecs/emittedAt 全欄位檢查，不
    合形者回 None（丟棄語義，不 raise）。taskId 須與 entry 一致（他 task 的
    記錄禁計入本 attempt freshness）；state 集只有 working|done（child 禁自報
    collected——偽造禁令）；seq 與 intervalSecs 須正整數。
    """
    if not isinstance(rec, dict):
        return None
    if rec.get("schema") != HEARTBEAT_SCHEMA:
        return None
    if rec.get("taskId") != task_id or rec.get("attemptId") != attempt_id:
        return None
    if rec.get("state") not in HEARTBEAT_STATES:
        return None
    seq = rec.get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        return None
    interval = rec.get("intervalSecs")
    if not isinstance(interval, int) or isinstance(interval, bool) or interval < 1:
        return None
    emitted = rec.get("emittedAt")
    if not isinstance(emitted, str) or _parse_iso(emitted) is None:
        return None
    return rec


def _read_heartbeat_sidecar(
    path: Path | None, task_id: str, attempt_id: str
) -> tuple[dict | None, str | None]:
    """sidecar join 讀面——回 (本 attempt 最新有效記錄, 異常註記).

    格式單一源＝scripts/child_heartbeat.py（`child-heartbeat/1`）——本檔為
    standalone 最小投影（不 import sibling；格式變更兩檔同步）。record
    contract 驗證與寫面對稱（`_valid_heartbeat_record`）；append-only 台帳讀
    語義：**末行無換行＝torn tail 丟棄**（縱使完整可解析 JSON——crash 半寫
    不計 freshness）、不可解析／欄位不合／taskId 或 attemptId 不符行丟棄；
    檔缺席／不可讀＝(None, 原因)——缺席合法（advisory 面，禁 fail-loud 拖垮
    supervisor）。
    """
    if path is None:
        return None, "sidecar-not-configured"
    if not path.is_file():
        return None, "sidecar-absent"
    try:
        raw = path.read_text(errors="replace")
    except OSError as exc:
        return None, f"sidecar-unreadable:{exc}"
    torn_tail = bool(raw) and not raw.endswith("\n")
    lines = raw.split("\n")
    if torn_tail:
        lines = lines[:-1]  # 末行無換行＝crash 半寫——丟棄
    latest: dict | None = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue  # 半截／損壞行——append-only 台帳的丟棄語義
        rec = _valid_heartbeat_record(parsed, task_id=task_id, attempt_id=attempt_id)
        if rec is not None:
            latest = rec
    return latest, ("torn-tail-discarded" if torn_tail else None)


def _heartbeat_verdict(
    entry: RegistryEntry, now: datetime, *, ws_root: Path
) -> tuple[str, dict]:
    """heartbeat 三分支判準（AIR-160）——回 (verdict, info).

    stale 門檻＝2×週期；週期以最新有效記錄的 `intervalSecs`（child 宣告）為
    準，無有效記錄回落契約預設 60s。fresh（age ≤ 門檻，壓 advisory 禁延
    timebox）／stale（記錄存在但斷訊超門檻，advisory 提前醒禁判死）／
    missing（無本 attempt 記錄且註冊起年齡超門檻，telemetry L0 缺席合法）／
    none（啟動窗——零輸出）。
    """
    latest, _anomaly = _read_heartbeat_sidecar(
        _ws_path(ws_root, entry.heartbeat_file) if entry.heartbeat_file else None,
        entry.task_id,
        entry.attempt_id,
    )
    if latest is not None:
        period_s = float(latest["intervalSecs"])
        threshold_s = period_s * HEARTBEAT_STALE_FACTOR
        emitted = _parse_iso(latest["emittedAt"])
        age_s = max(0.0, (now - emitted).total_seconds())
        info = {
            "lastHeartbeatAt": latest["emittedAt"],
            "intervalSecs": latest["intervalSecs"],
            "ageS": age_s,
            "thresholdS": threshold_s,
        }
        if age_s <= threshold_s:
            return "fresh", info
        return "stale", info
    threshold_s = HEARTBEAT_PERIOD_S_DEFAULT * HEARTBEAT_STALE_FACTOR
    created = _parse_iso(entry.created_at)
    waited_s = (now - created).total_seconds() if created else None
    if waited_s is not None and waited_s > threshold_s:
        return "missing", {"thresholdS": threshold_s, "waitedS": waited_s}
    return "none", {"thresholdS": threshold_s, "waitedS": waited_s}


# ---------------------------------------------------------------------------
# 主迴圈（T1-T6；狀態機實作對應 module docstring frozen spec）
# ---------------------------------------------------------------------------


def run_watcher(
    layout: ZCodeLayout,
    registry_path: Path,
    liveness_root: Path | None = None,
    *,
    threshold_min: float = DEFAULT_TIMEBOX_MIN,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    max_cycles: int | None = None,
    now_fn: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    now = now_fn or _system_now
    do_sleep = sleep_fn or time.sleep
    liveness = (
        liveness_root
        if liveness_root is not None
        else registry_path.parent / "liveness"
    )
    src = source or ZCodeLivenessSource(layout)
    detector = FreezeDetector(
        src, threshold_min=threshold_min, poll_interval_s=poll_interval_s
    )
    harvester = Harvester(src, layout, liveness)
    ws_root = registry_path.parent.parent  # workspace 根（sink/heartbeatFile 共用）

    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=None, face=entries)
    if not entries:
        _emit(err, f"[{WATCHER_NAME}] registry 空——無可監視物（等待語義）")
        _emit(out, _dumps({"state": "empty-registry", "entries": 0}))
        return EXIT_OK

    # F-4：基線＝task→attempt；純增項吸納續 watch，減項／attempt 變更才 hard-death
    baseline: dict[str, str] = {e.task_id: e.attempt_id for e in entries}
    states: dict[str, WatchState] = {e.task_id: WatchState() for e in entries}
    cycle = 0
    while True:
        cycle += 1
        if max_cycles is not None and cycle > max_cycles:
            _emit(
                out,
                _dumps(
                    {"state": "error", "reason": f"max-cycles-exceeded:{max_cycles}"}
                ),
            )
            _emit(err, f"[{WATCHER_NAME}] max-cycles {max_cycles} 用盡——內部錯收場")
            return EXIT_FAILLOUD
        current = load_registry(registry_path)
        if isinstance(current, UnknownFace):
            return _emit_face(out, err, "unknown", task_id=None, face=current)
        # T5：registry entry 消失／attempt 變更＝hard-death fast path（禁 retry）；
        # 純增項（正常追加註冊）＝吸納進監視集續 watch（F-4：增項非死亡訊號）
        current_map = {e.task_id: e for e in current}
        gone_or_refenced = [
            task
            for task, attempt in baseline.items()
            if task not in current_map or current_map[task].attempt_id != attempt
        ]
        if gone_or_refenced:
            tail = {
                "state": "hard-death-wake",
                "taskId": None,
                "reason": "registry-entry-changed",
                "detail": f"registry 監視集減項／attempt 變更：{gone_or_refenced}"
                "——重生／重派跡象，禁 retry",
            }
            _emit(out, _dumps(tail))
            _emit(err, f"[{WATCHER_NAME}] {tail['reason']}——立即 wake，禁 retry")
            return EXIT_HARD_DEATH
        for entry in current:
            if entry.task_id not in baseline:
                baseline[entry.task_id] = entry.attempt_id
                states[entry.task_id] = WatchState()
                _emit(
                    out,
                    f"[{WATCHER_NAME}] registry 純增項吸納：{entry.task_id}"
                    f"（attempt={entry.attempt_id}）——續 watch",
                )

        cycle_now = now()
        results: list[tuple[RegistryEntry, PollResult]] = []
        for entry in current:
            verdict, states[entry.task_id] = detector.poll(
                entry, states[entry.task_id], cycle_now
            )
            kind = type(verdict).__name__.removeprefix("Poll").lower()
            tele = getattr(verdict, "telemetry", ())
            _emit(
                out,
                f"[{WATCHER_NAME}] cycle={cycle} task={entry.task_id} "
                f"verdict={kind} elapsed={getattr(verdict, 'elapsed_s', 0.0):.1f}s "
                f"tele={','.join(tele) if tele else '-'}",
            )
            results.append((entry, verdict))

        hard: tuple[RegistryEntry, PollHardDeath] | None = None
        unknown: tuple[RegistryEntry, PollUnknown] | None = None
        frozen: tuple[RegistryEntry, PollFrozen] | None = None
        for entry, verdict in results:
            if isinstance(verdict, PollHardDeath) and hard is None:
                hard = (entry, verdict)
            elif isinstance(verdict, PollUnknown) and unknown is None:
                unknown = (entry, verdict)
            elif isinstance(verdict, PollFrozen) and frozen is None:
                frozen = (entry, verdict)

        if hard is not None:
            entry, verdict = hard
            _emit(
                out,
                _dumps(
                    {
                        "state": "hard-death-wake",
                        "taskId": entry.task_id,
                        "reason": verdict.reason,
                        "detail": "generation mismatch／metadata 消失——禁 retry",
                    }
                ),
            )
            _emit(err, f"[{WATCHER_NAME}] hard-death: {entry.task_id}——立即 wake")
            return EXIT_HARD_DEATH

        if unknown is not None:
            entry, verdict = unknown
            return _emit_face(
                out,
                err,
                "unknown",
                task_id=entry.task_id,
                face=UnknownFace(verdict.reason, verdict.detail),
            )

        if frozen is not None:
            # T4／wake 後生命週期：對第一個到期 entry 收割＋exit 3（advisory，
            # 不 stop 不重派）——其餘 entry 中止監視，主 session 處置後重啟
            entry, verdict = frozen
            harvest = harvester.harvest(entry, freeze_cursors=verdict.cursors)
            if isinstance(harvest, UnknownFace):
                return _emit_face(
                    out, err, "unknown", task_id=entry.task_id, face=harvest
                )
            manifest, bundle = harvest
            # D-C TOCTOU：收割 re-status 即 fresh terminal recheck——freeze 輪
            # 與處置間自然完成＝terminal race，TaskStop 免除、不消耗 budget
            harvest_status = manifest.get("metadata", {}).get("status")
            terminal_race = harvest_status in TERMINAL_STATES
            if terminal_race:
                collection = collect_sink(entry, ws_root)  # workspace 根
                budget = None
                suggested = _final_collect_suggestion(entry, collection, bundle)
            else:
                collection = None
                budget = consume_retry_budget(liveness, entry)
                suggested = _stop_chain_suggestion(entry, bundle)
            pending = write_pending_receipt(
                liveness,
                entry,
                manifest,
                bundle,
                elapsed_s=verdict.elapsed_s,
                resumed=bool(manifest.get("resumedDuringQuarantine")),
                retry_budget=budget,
                suggested=suggested,
            )
            wake = {
                "state": "timebox-wake",
                "schema": WAKE_RECEIPT_SCHEMA,
                "taskId": entry.task_id,
                "attemptId": entry.attempt_id,
                "interventionPolicy": entry.intervention_policy,
                "timeboxElapsedMin": round(verdict.elapsed_s / 60.0, 2),
                "resumedDuringQuarantine": manifest.get("resumedDuringQuarantine"),
                "terminalRace": terminal_race,
                "finalCollection": collection,
                "retryBudget": budget,
                "harvestDir": str(bundle),
                "manifestPath": str(bundle / "manifest.json"),
                "pendingReceiptPath": str(pending),
                "survivingHandles": list(entry.surviving_handles),
                "suggestedAction": suggested,
                "manifest": manifest,
            }
            if entry.expected_heartbeat:
                # AIR-160：fresh 不延 timebox（照醒）——verdict 進 receipt 供
                # parent 自選處置（fresh＝recent-checkin 可續等；stale 加證處置）
                hb_name, hb_info = _heartbeat_verdict(entry, cycle_now, ws_root=ws_root)
                if hb_name != "none":
                    wake["heartbeat"] = {"verdict": hb_name, **hb_info}
            _emit(out, _dumps(wake))
            if terminal_race:
                _emit(
                    err,
                    f"[{WATCHER_NAME}] terminal-race: {entry.task_id} 於收割時"
                    "已 terminal——final collect，不 stop 不 retry",
                )
            else:
                _emit(
                    err,
                    f"[{WATCHER_NAME}] timebox: {entry.task_id} "
                    f"running {verdict.elapsed_s:.0f}s（超 box）——已收割，"
                    "advisory wake（不 stop 不重派）",
                )
            return EXIT_FREEZE

        terminal_states = [v.state for _e, v in results if isinstance(v, PollTerminal)]
        if len(terminal_states) == len(results):
            # T2：全 terminal＝恰一次 collect（有 sink 時）→CollectionReceipt
            deliveries = [collect_sink(e, ws_root) for e in current]
            delivered = sum(1 for d in deliveries if d["verdict"] == "delivered")
            receipt = {
                "schema": COLLECTION_RECEIPT_SCHEMA,
                "watcher": WATCHER_NAME,
                "state": "all-terminal",
                "exitState": "all-terminal",
                "summary": {
                    "entries": len(results),
                    "terminal": sorted(set(terminal_states)),
                    "delivered": delivered,
                },
                "deliveries": deliveries,
            }
            _emit(out, _dumps(receipt))
            return EXIT_OK

        # AIR-160 heartbeat face：expectedHeartbeat=true 且 timebox 未到
        # （PollFresh）的 entry join 讀 sidecar——fresh/missing＝telemetry 續
        # 輪詢；stale＝STALE_ADVISORY 提前醒（advisory，不收割不記帳不判死）
        stale: tuple[RegistryEntry, dict] | None = None
        for entry, verdict in results:
            if not entry.expected_heartbeat or not isinstance(verdict, PollFresh):
                continue
            hb_name, hb_info = _heartbeat_verdict(entry, cycle_now, ws_root=ws_root)
            if hb_name == "fresh":
                _emit(
                    out,
                    f"[{WATCHER_NAME}] cycle={cycle} task={entry.task_id} "
                    f"heartbeat=fresh age={hb_info['ageS']:.0f}s "
                    f"(threshold={hb_info.get('thresholdS', 0):.0f}s)",
                )
            elif hb_name == "missing":
                _emit(
                    out,
                    f"[{WATCHER_NAME}] cycle={cycle} task={entry.task_id} "
                    f"heartbeat=missing (L0——缺席合法)",
                )
            elif hb_name == "stale" and stale is None:
                stale = (entry, hb_info)

        if stale is not None:
            entry, hb_info = stale
            wake = {
                "state": "stale-advisory",
                "schema": WAKE_RECEIPT_SCHEMA,
                "taskId": entry.task_id,
                "attemptId": entry.attempt_id,
                "interventionPolicy": entry.intervention_policy,
                "reason": "heartbeat-stale",
                "heartbeat": hb_info,
                "advisoryOnly": True,
                "survivingHandles": list(entry.surviving_handles),
            }
            _emit(out, _dumps(wake))
            _emit(
                err,
                f"[{WATCHER_NAME}] stale-advisory: {entry.task_id} heartbeat "
                f"斷訊 {hb_info['ageS']:.0f}s（>{hb_info['thresholdS']:.0f}s）"
                "——提前醒（advisory，不 stop 不重派，stale 不判死）",
            )
            return EXIT_FREEZE

        do_sleep(poll_interval_s)


# ---------------------------------------------------------------------------
# STOP verification（T8/T9）與 harvest delta invocation
# ---------------------------------------------------------------------------


def _ws_path(sink_base: Path, raw: str) -> Path:
    """workspace 相對路徑解析（sink／owned handles 共用；絕對路徑原樣）。"""
    p = Path(raw)
    return p if p.is_absolute() else sink_base / p


def _fence_snap(p: Path) -> str | tuple[int, int] | None:
    """fencing stat 快照：None＝缺席；"not-file"/"unreadable"＝無法歸屬；
    (size, mtime_ns)＝普通檔."""
    try:
        if not p.exists():
            return None
        if not p.is_file():
            return "not-file"
        st = p.stat()
    except OSError:
        return "unreadable"
    return (st.st_size, st.st_mtime_ns)


def run_verify(
    layout: ZCodeLayout,
    registry_path: Path,
    task_id: str,
    *,
    grace_s: float = DEFAULT_VERIFICATION_GRACE_S,
    sleep_fn: Callable[[float], None] | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--verify <taskId>：STOP fencing oracle（明列三項）→ STOP_CONFIRMED.

    D-D——三項缺一即 STOP_INCOMPLETE：
    1. metadata terminal（唯一權威狀態訊號）
    2. 所有已註冊 owned handles quiescent/collected——grace 觀察窗前後 stat
       不變＝quiescent；窗內消失＝collected；窗內出現/成長＝writer；存在非
       普通檔／不可讀＝無法歸屬（→ STOP_INCOMPLETE）
    3. authoritative sink grace 內無 writer——窗前後 stat 不變（缺席＝無
       writer；窗內新出現/成長＝writer）
    另 exec lease probe＝寫入者面：active lease 或 probe 不可判定＝
    STOP_INCOMPLETE（F-1/F-11 fail-closed 禁假確認）。survivingHandles＝
    correctness boundary（禁重派判定面）非 telemetry。fail-closed：任何面
    無法確認（含 metadata 消失）＝STOP_INCOMPLETE。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    do_sleep = sleep_fn or time.sleep
    src = source or ZCodeLivenessSource(layout)
    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=task_id, face=entries)
    entry = next((e for e in entries if e.task_id == task_id), None)
    if entry is None:
        return _emit_face(
            out,
            err,
            "unknown",
            task_id=task_id,
            face=UnknownFace("registry-entry-missing-for-verify", str(registry_path)),
        )

    sink_base = registry_path.parent.parent  # workspace 根（registry 慣例）
    surviving = list(entry.surviving_handles)
    reasons: list[str] = []

    def _face_reason(face: UnknownFace) -> str:
        return f"{face.reason}: {face.detail}".rstrip(": ")

    sink_path = _ws_path(sink_base, entry.sink)
    sink_before = _fence_snap(sink_path)
    handle_before = {h: _fence_snap(_ws_path(sink_base, h)) for h in surviving}

    first = src.status(task_id)
    if isinstance(first, UnknownFace):
        reasons.append(_face_reason(first))
    do_sleep(grace_s)
    st2 = src.status(task_id)
    terminal_state: str | None = None
    if isinstance(st2, UnknownFace):
        reasons.append(_face_reason(st2))
    else:
        terminal_state = st2.state
        # fence 1：metadata terminal
        if st2.state not in TERMINAL_STATES:
            reasons.append(f"metadata-not-terminal:{st2.state}")
        # fence 2：registered owned handles quiescent/collected
        for h in surviving:
            after = _fence_snap(_ws_path(sink_base, h))
            before = handle_before[h]
            if after in ("not-file", "unreadable"):
                reasons.append(f"owned-handle-unattributable:{h}")
            elif after is None:
                pass  # collected（窗內消失或本就缺席）
            elif before is None or before != after:
                # 窗內新出現或成長＝writer
                reasons.append(f"owned-handle-writer-active:{h}")
            # before == after（存在且穩定）＝quiescent
        # fence 3：authoritative sink grace 內無 writer
        sink_after = _fence_snap(sink_path)
        if sink_after in ("not-file", "unreadable"):
            reasons.append("sink-unattributable")
        elif sink_before is None and sink_after is not None:
            reasons.append("sink-writer-active")  # 窗內新出現
        elif sink_before is not None and sink_after != sink_before:
            reasons.append("sink-writer-active")  # 窗內成長
        # 寫入者面（F-1/F-11 保留）
        if not st2.exec_lease_checked:
            # F-11 面：probe 不可判定——verify 端 fail-closed 禁假確認
            reasons.append("lease-unknown:prober-undecidable")
        if st2.exec_lease:
            surviving.extend(le for le in st2.exec_lease if le not in surviving)
            reasons.append("exec-lease-active")
    if not reasons and terminal_state in TERMINAL_STATES:
        _emit(
            out,
            _dumps(
                {
                    "state": "STOP_CONFIRMED",
                    "taskId": task_id,
                    "terminal": terminal_state,
                    "fences": {
                        "metadataTerminal": True,
                        "ownedHandlesQuiescent": True,
                        "sinkNoWriter": True,
                    },
                    "survivingHandles": surviving,
                }
            ),
        )
        _emit(err, f"[{WATCHER_NAME}] STOP_CONFIRMED: {task_id}")
        return EXIT_OK
    _emit(
        out,
        _dumps(
            {
                "state": "STOP_INCOMPLETE",
                "taskId": task_id,
                "reasons": reasons,
                "survivingHandles": surviving,
            }
        ),
    )
    _emit(
        err,
        f"[{WATCHER_NAME}] STOP_INCOMPLETE: {task_id}——禁重派，detached child 見 survivingHandles",
    )
    return EXIT_VERIFY_INCOMPLETE


def run_harvest_delta(
    layout: ZCodeLayout,
    liveness_root: Path,
    task_id: str,
    manifest_path: Path,
    *,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--harvest-delta <taskId> <manifest>：STOP_CONFIRMED 後增量收割（harvest B）."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    src = source or ZCodeLivenessSource(layout)
    harvester = Harvester(src, layout, liveness_root)
    try:
        prev = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        prev = None
    raw_attempt = prev.get("attemptId") if isinstance(prev, dict) else None
    attempt_id = raw_attempt if isinstance(raw_attempt, str) else "delta"
    entry = RegistryEntry(
        task_id=task_id,
        attempt_id=attempt_id,
        created_at="",
        sink="",
        expected=None,
        surviving_handles=(),
        silence_budget_min=None,
    )
    result = harvester.harvest_delta(entry, manifest_path)
    if isinstance(result, UnknownFace):
        return _emit_face(out, err, "unknown", task_id=task_id, face=result)
    delta, bundle = result
    _emit(
        out,
        _dumps(
            {
                "state": "harvest-delta",
                "taskId": task_id,
                "manifestPath": str(bundle / "manifest.json"),
                "delta": delta,
            }
        ),
    )
    _emit(
        err,
        f"[{WATCHER_NAME}] harvest-delta: {task_id} "
        f"new={len(delta['newFiles'])} grown={len(delta['grownFiles'])} "
        f"resumed={delta['resumedDuringQuarantine']}",
    )
    return EXIT_OK


# ---------------------------------------------------------------------------
# dispatch 註冊（S2 寫入端——schema 逐欄對齊 load_registry 讀取面）
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, payload: dict) -> None:
    """atomic write：同目錄隱名 tmp＋os.replace（讀面永見完整檔，無半寫）."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def run_register(
    layout: ZCodeLayout,
    registry_path: Path,
    task_id: str,
    *,
    attempt_id: str | None,
    sink: str | None,
    expected_raw: str | None = None,
    surviving_handles: Sequence[str] = (),
    silence_budget_min: float | None = None,
    intervention_policy: str | None = None,
    expected_heartbeat: bool = False,
    heartbeat_file: str | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--register <taskId>：dispatch 當下寫入 registry entry（S2 寫入端）.

    `createdAt` 由 agent metadata 機械讀取（generation anchor——T5 對照
    基準＋timebox 起點，禁寫牆鐘）；metadata 不可解析／childSessionId 不符＝
    fail-loud。`interventionPolicy`（D-A）＝invoking session 當下寫入——
    缺席不寫欄位（讀面 fail-safe＝interactive）；明確給錯值＝fail-loud
    （寫面驗證與其他欄位一致；讀面的未知值才走 fail-safe coerce）。
    其餘 fail-loud 面：欄位無效（task 非可註冊形——sess_subagent_／agent_
    兩前綴之外／attempt/sink 空／
    expected 非 JSON／silenceBudget 非正數）、同 taskId 重註冊、既有
    registry 損壞或 schema 不符（禁覆蓋——損壞比缺失危險）。失敗一律不
    落地半套檔；成功以 atomic write 全檔替換。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr

    def fail(reason: str, detail: str) -> int:
        return _emit_face(
            out, err, "unknown", task_id=task_id, face=UnknownFace(reason, detail)
        )

    agent_id = agent_id_from_task(task_id)
    if agent_id is None:
        return fail(
            "invalid-task-id",
            f"需 {_SUBAGENT_PREFIX} 或 {_AGENT_PREFIX} 前綴：{task_id}",
        )
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        return fail("invalid-attempt-id", "需非空字串（--attempt-id）")
    if not isinstance(sink, str) or not sink.strip():
        return fail("invalid-sink", "需非空字串（--sink）")
    expected: object = None
    if expected_raw is not None:
        try:
            expected = json.loads(expected_raw)
        except json.JSONDecodeError as exc:
            return fail("expected-unparseable", f"需 JSON 字串：{exc}")
    if silence_budget_min is not None and not (
        isinstance(silence_budget_min, (int, float))
        and not isinstance(silence_budget_min, bool)
        and silence_budget_min > 0
    ):
        return fail("silence-budget-invalid", "需正數（分鐘）")
    if intervention_policy is not None and intervention_policy not in (
        INTERVENTION_POLICIES
    ):
        return fail("invalid-intervention-policy", "需 interactive｜autonomous_once")
    handles = tuple(h.strip() for h in surviving_handles)
    if any(not h for h in handles):
        return fail("invalid-surviving-handle", "handle 需非空白（--surviving-handle）")
    if expected_heartbeat and not (
        isinstance(heartbeat_file, str) and heartbeat_file.strip()
    ):
        # AIR-160：expectedHeartbeat 與 heartbeatFile 成對——缺路徑＝禁落地半套
        return fail(
            "heartbeat-file-required",
            "--expected-heartbeat 需 --heartbeat-file（sidecar join 讀面依賴）",
        )

    src = source or ZCodeLivenessSource(layout)
    meta_path = src.resolve_metadata(agent_id)
    if isinstance(meta_path, UnknownFace):
        # spawn 未落地／taskId 打錯——註冊當下就可判，禁猜禁拖到輪詢
        return fail(meta_path.reason, meta_path.detail)
    meta = src.read_metadata(meta_path)
    if isinstance(meta, UnknownFace):
        return fail(meta.reason, meta.detail)
    if meta["childSessionId"] != task_id and meta["childSessionId"] != (
        _SUBAGENT_PREFIX + task_id
    ):
        # agent_<uuid> 短形註冊：metadata childSessionId 為全形
        # sess_subagent_agent_<uuid>——兩形等價（同一 child），禁誤判 mismatch
        return fail(
            "metadata-generation-mismatch",
            f"childSessionId 不符：{meta['childSessionId']}",
        )

    entries = load_registry(registry_path)
    if isinstance(entries, UnknownFace):
        if entries.reason != "registry-missing":
            return fail(entries.reason, entries.detail)  # 禁覆蓋損壞 registry
        raw_entries: list = []
    else:
        try:
            payload = json.loads(registry_path.read_text())
        except (OSError, ValueError) as e:
            return fail("registry-read-failed", f"第二次讀取失敗：{e}")
        raw_entries = payload["entries"]
        if any(e.task_id == task_id for e in entries):
            return fail(
                "duplicate-registration",
                f"taskId 已註冊：{task_id}——新 attempt 前先移除舊 entry",
            )
    entry: dict = {
        "taskId": task_id,
        "attemptId": attempt_id,
        "createdAt": meta["createdAt"],
        "sink": sink,
        "expected": expected,
        "survivingHandles": list(handles),
    }
    if silence_budget_min is not None:
        entry["silenceBudget"] = float(silence_budget_min)
    if intervention_policy is not None:
        entry["interventionPolicy"] = intervention_policy
    if expected_heartbeat:
        entry["expectedHeartbeat"] = True
        entry["heartbeatFile"] = heartbeat_file
    raw_entries.append(entry)
    _atomic_write_json(registry_path, {"entries": raw_entries})
    _emit(
        out,
        _dumps(
            {
                "state": "registered",
                "taskId": task_id,
                "attemptId": attempt_id,
                "registryPath": str(registry_path),
                "entry": entry,
            }
        ),
    )
    _emit(err, f"[{WATCHER_NAME}] registered: {task_id} attempt={attempt_id}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# supervision probe（AIR-162——唯讀聚合；T1-T9 frozen 主體零變）
# ---------------------------------------------------------------------------


def run_probe(
    layout: ZCodeLayout,
    registry_path: Path,
    task_id: str,
    *,
    threshold_min: float = DEFAULT_TIMEBOX_MIN,
    now_fn: Callable[[], datetime] | None = None,
    source: ZCodeLivenessSource | None = None,
    stdout: _Writable | None = None,
    stderr: _Writable | None = None,
) -> int:
    """--probe <taskId>：唯讀聚合——分離兩軸＋A-D 證據分級（AIR-162）.

    契約與證據分級對照表見 module docstring「probe mode」節（單一源）；
    本函式只實作：registry face→heartbeat/workspace 觀察→metadata 狀態
    判定（terminal→generation→timebox→monitored）→structured JSON 尾行。
    判定規則（已決策勿重辯）：死亡宣稱僅 A 級；D 級缺席永不支撐死亡
    （lookup miss＝UNKNOWN 非 HARD_DEATH）；workspace 活動須身份窗綁定
    （registry.createdAt ≤ mtime ≤ now），窗外/時鐘異常禁歸因；probe 零
    處置零寫入。
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    now = (now_fn or _system_now)()
    src = source or ZCodeLivenessSource(layout)
    ws_root = registry_path.parent.parent
    evidence: list[dict] = []
    hb_extra: dict | None = None  # heartbeat 面輸出（face 2 填入；早退路徑 None）

    def row(grade: str, face: str, detail: str) -> None:
        evidence.append({"grade": grade, "face": face, "detail": detail})

    def strongest_of(state: str) -> str:
        if state in ("TERMINAL", "HARD_DEATH_EVIDENCE", "TIMEBOX_EXPIRED"):
            return "A"
        if observations["recentExecution"] == "yes":
            return "B"
        if any(r["grade"] == "C" for r in evidence):
            return "C"
        return "D"

    def finish(
        state: str,
        *,
        exit_code: int,
        ambiguous: bool,
        **extra: object,
    ) -> int:
        # manualReview＝UNKNOWN 升級態或 attribution_ambiguous（人工判讀旗）
        manual = ambiguous or state == "UNKNOWN"
        if hb_extra:
            extra.setdefault("heartbeat", hb_extra)
        payload = {
            "schema": PROBE_SCHEMA,
            "watcher": WATCHER_NAME,
            "taskId": task_id,
            "supervisionState": state,
            "observations": observations,
            "strongestEvidence": strongest_of(state),
            "manualReview": manual,
            "attributionAmbiguous": ambiguous,
            "evidence": evidence,
        }
        payload.update(extra)
        _emit(out, _dumps(payload))
        _emit(
            err,
            f"[{WATCHER_NAME}] probe: {task_id} → {state} "
            f"(evidence={payload['strongestEvidence']}, "
            f"manualReview={manual})",
        )
        return exit_code

    observations = {
        "recentExecution": "unknown",
        "addressable": "unknown",
        "workspaceActivity": "unknown",
    }

    def unknown(reason: str, detail: str = "") -> int:
        row("D", "unknown", f"{reason}: {detail}".rstrip(": "))
        return finish(
            "UNKNOWN",
            exit_code=EXIT_FAILLOUD,
            ambiguous=False,
            unknownReason=reason,
            unknownDetail=detail,
        )

    # face 1：registry row（C）／缺席（D）／損壞（fail-loud UNKNOWN）
    entries = load_registry(registry_path)
    entry: RegistryEntry | None = None
    if isinstance(entries, UnknownFace):
        if entries.reason == "registry-missing":
            # probe 輸入是 task 非 registry——缺席＝D 級缺席面（非 fail-loud，
            # 與 watcher T6 不同面）；損壞仍 fail-loud（損壞比缺失危險）
            row("D", "registry", f"registry-missing: {entries.detail}")
        else:
            return unknown(entries.reason, entries.detail)
    else:
        candidates = {task_id}
        if task_id.startswith(_AGENT_PREFIX):
            candidates.add(_SUBAGENT_PREFIX + task_id)
        entry = next((e for e in entries if e.task_id in candidates), None)
        if entry is not None:
            row("C", "registry", f"row present attempt={entry.attempt_id}")
        else:
            row("D", "registry", "registry has no entry for this task")

    # face 2：heartbeat sidecar join（可歸因執行證據——fresh=B／stale=C）
    if entry is not None and entry.expected_heartbeat and entry.heartbeat_file:
        hb_name, hb_info = _heartbeat_verdict(entry, now, ws_root=ws_root)
        hb_extra = {"verdict": hb_name, **hb_info}
        if hb_name == "fresh":
            observations["recentExecution"] = "yes"
            row("B", "heartbeat", f"fresh age={hb_info['ageS']:.0f}s")
        elif hb_name == "stale":
            observations["recentExecution"] = "no"
            row("C", "heartbeat", f"stale age={hb_info['ageS']:.0f}s")
        else:
            row("D", "heartbeat", f"{hb_name} (absence legal)")
    else:
        row("D", "heartbeat", "not-configured")

    # face 3：workspace 觀察面（身份窗綁定——registry.createdAt ≤ mtime ≤ now；
    # task-scoped 面＝路徑即身份可機械歸因；shared 面（sink/handles）恆ambiguous）
    faces: list[tuple[str, Path]] = []
    full_task = (
        task_id if task_id.startswith(_SUBAGENT_PREFIX) else _SUBAGENT_PREFIX + task_id
    )
    for tid in dict.fromkeys((task_id, full_task)):
        faces += [("task-scoped", p) for p in _files_in_dir(layout.exec_dir(tid))]
        faces += [("task-scoped", p) for p in _files_in_dir(layout.artifact_dir(tid))]
    window_start: datetime | None = None
    if entry is not None:
        window_start = _parse_iso(entry.created_at)
        shared = [_ws_path(ws_root, entry.sink)]
        shared += [_ws_path(ws_root, h) for h in entry.surviving_handles]
        faces += [("shared", p) for p in shared]
    in_window = False
    future_hit = False
    shared_hit = False
    any_file = False
    for face_label, path in faces:
        try:
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime_ns / 1e9, tz=UTC)
        except OSError:
            continue  # 讀撞＝可選面 telemetry gap，不拖垮 probe
        any_file = True
        if window_start is None:
            continue  # 無窗錨點（未註冊）＝活動不可歸因——維持 unknown
        if mtime > now:
            in_window = True
            future_hit = True  # 未來 mtime＝時鐘異常，禁歸因
        elif mtime >= window_start:
            in_window = True
            if face_label == "shared":
                shared_hit = True
    if not any_file:
        row("D", "workspace", "no observable files")
    elif window_start is None:
        row("D", "workspace", "no window anchor (unregistered)")
    elif in_window:
        observations["workspaceActivity"] = "yes"
        row("C", "workspace", "in-window activity")
    else:
        observations["workspaceActivity"] = "no"
        row("D", "workspace", "files observable, none in attempt window")
    ambiguous = shared_hit or future_hit

    # face 4：harness metadata（唯一權威狀態訊號）——terminal→generation→timebox
    st = src.status(task_id)
    if isinstance(st, UnknownFace):
        if st.reason == "metadata-anchor-missing" and entry is not None:
            # 已註冊身份的 metadata 消失＝A 級 hard-death fast path（T5 對稱）；
            # 無 registry row 的 lookup miss（never-existed/reaped/打錯 id）＝
            # UNKNOWN——D 級缺席禁推死（已決策③）
            row("A", "metadata", f"registered-identity-gone: {st.detail}")
            return finish(
                "HARD_DEATH_EVIDENCE",
                exit_code=EXIT_HARD_DEATH,
                ambiguous=ambiguous,
            )
        return unknown(st.reason, st.detail)

    if entry is not None:
        reg_created = _parse_iso(entry.created_at)
        meta_created = _parse_iso(st.created_at)
        if (
            reg_created is not None
            and meta_created is not None
            and reg_created != meta_created
        ):
            row("A", "metadata", "generation-mismatch-registry-createdAt")
            return finish(
                "HARD_DEATH_EVIDENCE",
                exit_code=EXIT_HARD_DEATH,
                ambiguous=ambiguous,
                metadataStatus=st.state,
            )

    addressable = st.state not in TERMINAL_STATES
    observations["addressable"] = "yes" if addressable else "no"
    if addressable:
        row("C", "metadata", f"native running row status={st.state}")
    else:
        row("A", "metadata", f"terminal transition status={st.state}")

    if st.state in TERMINAL_STATES:
        extra: dict = {}
        if entry is not None:
            extra["sink"] = collect_sink(entry, ws_root)  # 資訊面——verdict 不影響
        return finish(
            "TERMINAL",
            exit_code=EXIT_OK,
            ambiguous=ambiguous,
            **extra,
        )

    meta_created = _parse_iso(st.created_at)
    if meta_created is None:
        # read_metadata 已擋不可解析 createdAt——防禦面（F-6 對稱）
        return unknown("metadata-corrupt", "createdAt unparseable")
    threshold_eff = (
        entry.silence_budget_min
        if entry is not None and entry.silence_budget_min is not None
        else threshold_min
    )
    elapsed_s = (now - meta_created).total_seconds()
    timebox_info = {
        "thresholdMin": threshold_eff,
        "elapsedMin": round(elapsed_s / 60.0, 2),
    }
    if elapsed_s < 0:
        # 時鐘回撥（createdAt 在未來）＝禁判 timebox（frozen 條款對稱）
        row("D", "timebox", "clock-rollback (elapsed<0)——禁判 timebox")
        return finish(
            "MONITORED",
            exit_code=EXIT_OK,
            ambiguous=ambiguous,
            timebox=timebox_info,
        )
    if elapsed_s >= threshold_eff * 60.0:
        row(
            "A",
            "timebox",
            f"expired {timebox_info['elapsedMin']}min ≥ "
            f"{threshold_eff}min——時間盒事實，不宣稱 dead",
        )
        return finish(
            "TIMEBOX_EXPIRED",
            exit_code=EXIT_OK,
            ambiguous=ambiguous,
            timebox=timebox_info,
        )
    return finish(
        "MONITORED",
        exit_code=EXIT_OK,
        ambiguous=ambiguous,
        timebox=timebox_info,
    )


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None, *, layout: ZCodeLayout | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=WATCHER_NAME,
        description=(
            "ZCode 子 agent timebox 監視＋收割＋停止協議（AIR-149 S1＋S2；"
            "frozen spec v2）——watcher 永不 stop／重派，wake 歸主 session／"
            "deepwork 授權鏈處置"
        ),
        epilog="契約：EP 09-20-harness-liveness-watcher S1（frozen spec v2）"
        "＋S2；狀態機 frozen spec 見 module docstring。",
    )
    parser.add_argument(
        "registry",
        type=Path,
        metavar="registry",
        help="workspace-local liveness registry（.agent-tmp/liveness-registry.json）",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify",
        metavar="taskId",
        default=None,
        help="STOP fencing verification（明列三項）：metadata terminal＋"
        "registered handles quiescent/collected＋sink grace 內無 writer→"
        "STOP_CONFIRMED（exit 0）／STOP_INCOMPLETE（exit 4）",
    )
    mode.add_argument(
        "--probe",
        metavar="taskId",
        default=None,
        help="唯讀聚合 probe（AIR-162）：分離兩軸 supervisionState×"
        "observations＋A-D 證據分級＋manualReview 旗（零處置零寫入；"
        "exit 0=verdict／2=HARD_DEATH_EVIDENCE／1=UNKNOWN）",
    )
    mode.add_argument(
        "--harvest-delta",
        nargs=2,
        metavar=("taskId", "manifest"),
        default=None,
        help="STOP_CONFIRMED 後增量收割（harvest B）",
    )
    mode.add_argument(
        "--register",
        metavar="taskId",
        default=None,
        help="dispatch 註冊：寫入 registry entry（S2）——需 --attempt-id/--sink；"
        "同 taskId 重註冊＝fail-loud",
    )
    parser.add_argument(
        "--attempt-id",
        default=None,
        help="--register 必帶：本 attempt 唯一識別",
    )
    parser.add_argument(
        "--sink",
        default=None,
        help="--register 必帶：bounded receipt sink（AIR-135.7 AC#2 投影）",
    )
    parser.add_argument(
        "--expected",
        default=None,
        help="--register 選帶：sink 驗收條件（JSON 字串）",
    )
    parser.add_argument(
        "--surviving-handle",
        action="append",
        default=None,
        metavar="HANDLE",
        help="--register 選帶：dispatch 前已知 detached job ownership handle（可多次）",
    )
    parser.add_argument(
        "--silence-budget-min",
        type=float,
        default=None,
        metavar="MIN",
        help="--register 選帶：timebox 分鐘（v2 重解釋 silenceBudget；缺席＝20m 標準）",
    )
    parser.add_argument(
        "--intervention-policy",
        default=None,
        metavar="POLICY",
        help="--register 選帶：interactive｜autonomous_once（D-A 兩軸分離——"
        "誰處置；缺省 fail-safe＝interactive；可否重派歸 RETRY_SAFE）",
    )
    parser.add_argument(
        "--expected-heartbeat",
        action="store_true",
        default=False,
        help="--register 選帶：啟用 child heartbeat sidecar join（AIR-160）"
        "——需成對 --heartbeat-file",
    )
    parser.add_argument(
        "--heartbeat-file",
        default=None,
        metavar="PATH",
        help="--register 選帶：child sidecar JSONL 路徑（workspace 相對——"
        "與 sink 同解析面；--expected-heartbeat 必帶）",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_S,
        help=f"輪詢間隔秒（預設 {DEFAULT_POLL_INTERVAL_S:.0f}）",
    )
    parser.add_argument(
        "--timebox-min",
        "--freeze-threshold",
        dest="timebox_min",
        type=float,
        default=TIMEBOX_MIN,
        help=f"timebox 分鐘（預設 {DEFAULT_TIMEBOX_MIN:.0f}；entry "
        "silenceBudget 可逐案覆寫；--freeze-threshold 為 v1 名相容別名）",
    )
    parser.add_argument(
        "--grace",
        type=float,
        default=DEFAULT_VERIFICATION_GRACE_S,
        help=f"--verify fencing 觀察窗秒（handles/sink 窗前後 stat 比對；預設 "
        f"{DEFAULT_VERIFICATION_GRACE_S:.0f}）",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="輪詢上限（測試／看門狗用；預設無限）",
    )
    args = parser.parse_args(argv)

    layout = layout or ZCodeLayout.default()
    liveness = args.registry.parent / "liveness"
    if args.verify is not None:
        return run_verify(layout, args.registry, args.verify, grace_s=args.grace)
    if args.probe is not None:
        return run_probe(
            layout,
            args.registry,
            args.probe,
            threshold_min=args.timebox_min,
        )
    if args.harvest_delta is not None:
        task_id, manifest = args.harvest_delta
        return run_harvest_delta(layout, liveness, task_id, Path(manifest))
    if args.register is not None:
        return run_register(
            layout,
            args.registry,
            args.register,
            attempt_id=args.attempt_id,
            sink=args.sink,
            expected_raw=args.expected,
            surviving_handles=tuple(args.surviving_handle or ()),
            silence_budget_min=args.silence_budget_min,
            intervention_policy=args.intervention_policy,
            expected_heartbeat=args.expected_heartbeat,
            heartbeat_file=args.heartbeat_file,
        )
    return run_watcher(
        layout,
        args.registry,
        liveness,
        threshold_min=args.timebox_min,
        poll_interval_s=args.poll_interval,
        max_cycles=args.max_cycles,
    )


if __name__ == "__main__":
    raise SystemExit(main())
