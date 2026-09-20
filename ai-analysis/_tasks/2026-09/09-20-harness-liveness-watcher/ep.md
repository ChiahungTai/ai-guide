# EP: harness liveness watcher——ZCode subagent 凍結偵測＋收割＋停止協議

> **ep_type**: implementation
> baseline: 308f9a718f0e958291f1cc29f094481db2933827
> author_family: glm

## 實作總覽

背景 worker 卡住的觀測面由 AIR-146（bridge 側）承接；本 EP 承接 **in-harness 子 agent**（ZCode Task-tool subagent）的凍結偵測。核心語義（user 裁決 0920）：**「20 分鐘全面零輸出＝bug 處理」——收割屍體再砍，不需要判斷死亡**。判死在可接受成本下不可觀測（凍結四態長相相同：深推理/長工具/楔死/崩潰），因此設計不偵測死亡，只機械偵測「全面靜默」，並用「先收割後砍」把誤殺成本壓到工具重跑等級。

設計裁決（已定案勿重辯）：`references/research.md`（含 codex 內外攻防 job-mu9lcidp／job-mu9lxzsj 兩輪結論＋AIR-148 probe 實證）。

## UC 盤點

### Backlog 關聯
- AIR-148 harness liveness probe（Done 結算：GO＋縮範圍「檔案系統優先唯讀 watcher」）——本 EP 即其「full EP 立案」交付
- AIR-135.7（Orchestration-reliability）——本 EP 是其「偵測與處置分離＋liveness 台帳」的 in-harness 側擴充；AC#3 工具化證據條件已滿（user 裁決＋批量手工回收實證）
- AIR-146／147（bridge 側 watcher＋doctrine）——正交不重疊（bridge job 維持 advisory-only）
- 自動建卡：EP 追蹤卡＋S1 實作卡（開卡 Description 先行人話＋圖，user 確認後建——見收尾步驟）

### SYSTEM-MAP 影響
無（repo 無 SYSTEM-MAP.md）

### 掃描範圍
- `backlog task list --plain`：AIR-146/147/148、AIR-135.7 命中（本 EP 依賴 **AIR-148**（probe 實證）與 **AIR-135.7**（邊界承接）；AIR-146 僅形態參考、AIR-147 觀察面正交但 doctrine 檔案相撞（見 F5 接線註記））
- instruction 檔：`scripts/` 無模組 AGENTS.md／Capabilities 表（新能力，收尾時建）；`skills/agent-workflow/SKILL.md:83-84`（watcher/驗屍法段落——S3 改寫對象）
- 同主題 memory 條目（結案蒸餾範圍）：**`project_air135-watcher-arc-inflight`**（弧座標＋liveness 事實——事實已由 research.md 吸收；EP acceptance 時更新弧狀態，結案蒸餾時去重或退休）＋`_inventory.md` 同步命中

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| bridge 派工回收 watcher | 📋→✅ | AIR-146 卡 | 無 | bridge 側，本 EP 不動 |
| in-harness 子 agent 凍結偵測 | 📋 | AIR-148 卡（probe 完成） | 新增 | 本 EP 主體 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| in-harness 子 agent 全面靜默偵測＋收割 | 📋 | `scripts/harness_waiter.py` |
| dispatch 註冊（attempt_id＋surviving-work＋silence lease） | 📋 | 註冊檔＋agent-workflow doctrine |
| STOP verification＋RETRY_SAFE gate | 📋 | doctrine＋watcher 輸出欄位 |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 子 agent 正常工作中 | 三面任一有推進 | watcher 靜默（零喚醒） | 無 | 凍結偵測 |
| SM-2 | 長工具呼叫（exec fd 活著、rollout 凍結） | lsof 偵測到 open lease | 不算凍結（豁免） | 無 | 凍結偵測 |
| SM-3 | 全面靜默跨 20m | 三面皆無推進＋無 lease＋無 terminal | harvest→wake main→（主 session）TaskStop | 收割快照路徑 | 收割 |
| SM-4 | TaskStop 後 quiescence 確認 | metadata terminal＋cursors grace 內不動 | STOP_CONFIRMED→主 session 決定重派 | 收割 B/delta | 停止協議 |
| SM-5 | stop 後仍有寫入者 | detached child 活著 | STOP_INCOMPLETE→禁重派→處置清單 | 收割 B | 停止協議 |
| SM-6 | generation mismatch（metadata 消失/異動） | registry 對照 | 立即喚醒（不等 20m）——hard-death path | 無 | 凍結偵測 |
| SM-7 | 機器睡眠後醒來 | 兩次 poll 間隔異常大 | 靜默計數重置/扣除，不誤殺 | 無 | 凍結偵測 |
| SM-8 | 內部佈局改變（檔案/表缺席） | 錨點缺失 | fail-loud 回 unknown，禁誤報 | 無 | fail-loud |
| SM-9 | 屍體超大 | rollout/artifact 超限 | harvest_partial=true→照樣砍 | manifest | 收割 |
| SM-10 | 未註冊的 task 出現在觀察面 | registry 無 entry | unknown（不監視不誤報） | 無 | fail-loud |

## 測試規劃段

| TC | claim | Given-When | oracle | oracle_source | evidence | uncovered |
|----|-------|-----------|--------|---------------|----------|-----------|
| TC-1 | 狀態機轉移與 frozen spec 一致 | 各 SM 情境輸入 | 逐轉移對照 S1 docstring 轉移表 | 本 EP S1 frozen spec（frozen-at-review） | S | 併發競態 |
| TC-2 | stale-running 誤報為零 | 39 個真實殭屍 metadata＋rollout 缺席 corpus | 全部回 unknown/stale，禁誤報 active | 真實歷史 corpus（殭屍檔） | H | — |
| TC-3 | 凍結判準三面邏輯 | 合成 mtime/lease 矩陣（含 SM-2/7） | 判準表逐格 | S1 判準定義 | I | 真實 workload 分佈 |
| TC-4 | 收割→停止→驗證端到端 | **誘導機制：subagent brief 指示執行 stdout 全封閉的分離命令**（`sleep 1300 >/dev/null 2>&1 &`＋wait——無 exec fd 寫入、無 model I/O→三面全靜默，**不落入 SM-2 exec lease 豁免**） | harvest 完整性＋STOP_CONFIRMED/STOP_INCOMPLETE | 實機觀測 | H（dogfood） | — |
| TC-5 | fail-loud | 佈局錨點缺失 | unknown＋禁誤報，exit 非 0 | S1 fail-loud 條款 | I | — |

TC-2 之 H 級 oracle 使用真實殭屍 corpus（39 檔快照入 `references/fixtures/`，去敏後入 git）。same-family precondition：author_family=glm，實作若同家族（impl-lite=glm-5.3-flash），RED 前須 challenge（blind derive→reveal）或顯式降級記錄。

## 段落 0：全域研究

研究已完成（AIR-148 probe＋codex 兩輪攻防＋bridge 源碼驗證），全文轉錄 `references/research.md`（錨點齊）。摘要：
- **可複用基礎設施**：`scripts/agent_liveness_sweep.py:347-384` 的 sink 三步驗收 validate_sink（抽共用 receipt validator）；AIR-146 `scripts/bridge_waiter.py` 的 watcher 迴圈/exit 契約形態（bridge 側兄弟，結構可參考、代碼不共用——觀察面完全不同）
- **依賴關係**：唯讀依賴 `~/.zcode/cli/{agents,rollout,exec,log}` 佈局（內部實作細節——官方明言無管理介面，layout 未承諾）→ 必包 `ZCodeLivenessSource` adapter（S1），B path（上游 API）為 replacement
- **風險假設**：①layout 無聲變更（app 更新實證 asar 同日重寫）→ adapter 錨點缺失＝unknown fail-loud（S1 驗證）②「fd lease 可偵測」→ lsof 實測（S1 POC）③「registry 寫入紀律可維持」→ dogfood（S4）

### kill criteria（AIR-131）
| # | Assumption | Probe（最便宜證偽） | Kill observation | Action |
|---|---|---|---|---|
| K1 | rollout/exec/artifact 三面觀察足夠判定靜默 | S1 POC：**誘導法**——spawn 一個「20m+ 純推理、零工具呼叫」的任務，驗證 rollout 於 thinking 期持續 append（機械檢驗裁決 2 的經驗基礎）；「真工作中」操作化＝agent 事後 self-report 對照 rollout 時間軸 | 誘導任務期間 rollout 停止 append（即純推理也會靜默）實例成立 | pivot：三面判準加 job-class 豁免或升上游 API 請求（B path） |
| K2 | fd lease（lsof）可穩定豁免長工具呼叫 | S1 POC：跑 25m 靜默工具呼叫實測 lsof 命中率 | lsof 偵測不可靠（空手率 >50%） | freeze 判準退回 rollout+artifact 兩面＋threshold 上調 40m，或 B path |
| K3 | registry 寫入紀律可維持 | S4 dogfood：**分母＝log jsonl 的 `subagent.background.started` 事件數**（research §一實證），分子＝registry 行數，註冊率=分子/分母 | 註冊率 <80% | 註冊改機械化（spawn wrapper/hook），或 watcher 只對已註冊 task 服務（SM-10 語義） |

## 段落劃分原則

S1（觀測核心，code）→ S2（註冊契約，code-lite＋doctrine）→ S3（處置協議，doctrine）→ S4（dogfood 整合）。S1 先行（S2/S3 的輸出欄位依賴 S1 的觀察面）；S2/S3 可平行；S4 最後。

## S1：ZCodeLivenessSource adapter＋凍結偵測＋收割

### Context
實作〔in-harness 子 agent 全面靜默偵測＋收割〕。依賴：無（首段）。UC 引用：新增 UC 表第一行。基礎設施：`agent_liveness_sweep.py` validate_sink（receipt 三步）、AIR-146 watcher 迴圈形態參考。

語義約束：與 S2 共享 registry schema（attempt_id/sink/expected/silence_budget 欄位）；與 S3 共享輸出欄位（state/harvest_path/surviving_handles）。

依賴錨點：`~/.zcode/cli/agents/`（metadata）／`~/.zcode/cli/rollout/`（model-io jsonl）／`~/.zcode/cli/exec/`（stdout logs）／`~/.zcode/cli/log/`（事件 jsonl）——全部經 `ZCodeLivenessSource` adapter 間接（路徑常數集中一處；錨點缺失→unknown fail-loud，禁誤報）。技術選型：Python 3.12 stdlib（stat/lsof subprocess/json）＋無新依賴。成功標準：TC-1..3/5 綠。

### Invariant Impact
受影響 invariant：**「無訊號 ≠ 死亡」**（39 殘留實證的 harness 失敗模式——observer 不得複製）；critical path：無（觀測面唯讀）；驗證對齊：TC-2（真實殭屍 corpus 零誤報）＋TC-5。

### 核心實作要點
- `ZCodeLivenessSource`：路徑解析＋錨點存在性（缺→`unknown` 帶原因）。**觀察面定義（frozen）**：rollout＝`~/.zcode/cli/rollout/model-io-<taskId>.jsonl`；exec＝`~/.zcode/cli/exec/sess_<taskId>/`；artifact＝`~/.zcode/cli/artifacts/sess_<taskId>/`；metadata＝`~/.zcode/cli/agents/sess_<parent>/agent_<id>/metadata.json`（registry 存 agentId，adapter 以 glob 解析路徑）。`status(taskId) -> {state, generation, lastActivity, outputCursor, exec_lease}`
- **fail-loud 擴充**：錨點缺失、**JSON 不可解析／半寫 torn read**、**corpus 數目漂移**——一律 `unknown(原因)`，禁 crash 禁猜
- **時鐘回撥**：elapsed<0 → 視為 Fresh＋記 telemetry
- **registry 生命週期**：檔缺席＝錨點缺失 fail-loud；檔在但空＝exit 0 帶空 receipt（等待語義：無可監視物）
- **wake 後生命週期**：watcher 對「第一個凍結」harvest＋exit(3)——**其餘 entry 中止監視**，主 session 處置後重啟 watcher 續監（v1 從簡；pending receipt 路徑＝`.agent-tmp/liveness/pending/<taskId>.json`，dedup key＝taskId＋attemptId）
- **STOP verification invocation**：`harness_waiter.py --verify <taskId>`（主 session TaskStop 後呼叫）——回 STOP_CONFIRMED/STOP_INCOMPLETE
- **收割 B**：`harness_waiter.py --harvest-delta <taskId> <manifest>`（主 session 於 STOP_CONFIRMED 後呼叫）
- 凍結判準（research.md §三）：rollout＋artifact 無推進＋無 exec fd lease＋無 terminal，連續 20m（可設定）；poll gap 異常→**該段時間扣除**（單一語義，不重置整個計數）。**Amendment（TC-4 活體證偽，97114424）**：fd lease 不再豁免凍結計數——阻塞命令恆持 call-log fd，豁免使 watcher 對靜默 agent 永遠報 fresh；lease 降級 telemetry＋STOP_INCOMPLETE survivingHandles 面
- 收割器：bounded（先 metadata/cursor/raw tail/manifest，超限 partial）；JSONL raw bytes；**corpus 於 S1 開工時快照入 `references/fixtures/`（TC-2 引快照時點計數，不綁固定數字）**
- 輸出：wake receipt（pending intervention dedup）——內容＝attempt_id/harvest 路徑/manifest/surviving_handles（自 S2 registry）/建議動作（TaskStop id）
- **exit 契約（frozen）**：0＝正常收場（含空 registry）／2＝hard-death wake（generation mismatch）／3＝freeze wake（附收割 receipt）／其他非零＝內部錯（fail-loud 診斷至 stderr＋stdout 尾行狀態 JSON 標記）——沿兄弟 bridge_waiter T-contract 形態
- 狀態機：**frozen spec 轉移表（S 級 oracle——TC-1 對照本表，實作者不得改表，改表走 amendment）**：

| # | 來源態 | 事件 | 條件 | 到達態 | watcher 動作 |
|---|---|---|---|---|---|
| T1 | （註冊） | S2 registry entry 建立 | — | MONITORED | 開始輪詢 |
| T2 | MONITORED | 輪詢 | 三面任一推進 | MONITORED | 計數續走（poll gap 異常→扣除間隔） |
| T3 | MONITORED | 輪詢 | 全面靜默 ≥20m | HARVESTED | bounded 收割（partial 標記）→寫 pending intervention receipt（**dedup：已有 pending 不重發**）→exit 3 喚醒 |
| T4 | MONITORED/HARVESTED | quarantine 期活動恢復 | 任一面推進 | （記 `resumed_during_quarantine=true` telemetry） | **仍照砍**——主 session TaskStop 不因恢復取消（user 裁決） |
| T5 | MONITORED | generation mismatch／registry entry 消失 | metadata 異動對照 | （hard-death fast path） | **立即 wake**（exit 2），不等 20m——禁 retry |
| T6 | 任意 | 佈局錨點缺失／registry 缺 entry | adapter 查證失敗 | UNKNOWN | fail-loud 診斷，零誤報 |
| T7 | （主 session） | TaskStop 下達 | — | STOP_REQUESTED | 主 session 執行（非 watcher） |
| T8 | STOP_REQUESTED | verification | grace 內 metadata terminal＋cursors 靜止 | STOP_CONFIRMED | harvest B/delta（主 session 以 `--harvest-delta` 呼叫本 script）→主 session 決定 RETRY_SAFE |
| T9 | STOP_REQUESTED | verification | 仍有寫入者 | STOP_INCOMPLETE | 禁重派＋detached child 處置清單 |

不變量：watcher 永不 stop/重派（TaskStop 歸主 session）；「無訊號≠死亡」；EXECUTION_DEAD 語義由 STOP 鏈承載、RETRY_SAFE 獨立判定。

### Pseudo Code
```
class ZCodeLivenessSource:
    def status(task_id) -> Status | Unknown(原因)
class FreezeDetector:  # 三面 stat＋fd lease（lsof）＋poll-gap 扣除
    def poll(registry_entry) -> Fresh | Frozen(elapsed) | Unknown(原因)
class Harvester:  # bounded：manifest→metadata→tail；raw bytes；partial 標記
    def harvest(task_id) -> HarvestReceipt
    def harvest_delta(task_id, manifest) -> HarvestReceipt  # STOP 後主 session 呼叫
main loop:  # polling；exit 3=frozen wake／exit 2=hard-death wake
  poll 註冊表 → freeze? → harvest → pending receipt（dedup）→ exit 喚醒
  generation mismatch → 立即 wake（exit 2）
```

### 驗證策略
TC-1/2/3/5＋K1/K2 POC（`poc/poc_fd_lease.py`——lsof 命中率實測；`poc/poc_three_surface.py`——真 subagent 三面採樣）。引用 TC-ID：全（見測試規劃段）。

## S2：dispatch 註冊（attempt_id＋surviving-work＋silence lease）

### Context
實作〔dispatch 註冊〕。依賴：S1 schema。語義約束：registry 檔＝workspace-local `.agent-tmp/liveness-registry.json`（gitignored——暫存面；正式化為後續議題）；寫入者＝invoking session（dispatch 當下）。

要點：註冊欄位 `{taskId, attemptId, createdAt, sink, expected, survivingHandles[], silenceBudget?}`——`sink`/`expected` 語義＝AIR-135.7 AC#2 bounded receipt 欄位投影（同 AIR-146 CollectionReceipt 慣例）；**本 registry＝AIR-135.7 AC#3 六欄台帳的 in-harness workspace 投影（欄位映射 taskId↔id、sink↔sink、expected↔expect；正式化目標指向 AC#6 台帳，禁第二套 split-brain）**；`survivingHandles[]` 於 dispatch 前已知的 detached job 填入，執行中新增者由 harvest manifest 捕捉；`silenceBudget` 為有期限的 lease（預設無＝20m 標準）。**in-harness brief 禁未登記 long-lived/daemonized child**（要 server 須記 ownership handle——S3 doctrine 同步）。agent-workflow spawn 起手式加「註冊一行」doctrine；S4 dogfood 驗 K3（分母＝log started 事件數）。驗證：註冊率 dogfood ≥80%（K3 gate）＋schema 校驗測試。

## S3：STOP verification＋RETRY_SAFE gate（doctrine）

### Context
實作〔STOP verification＋RETRY_SAFE gate〕。依賴：S1 輸出欄位。語義約束：AIR-135.7「偵測與處置分離」邊界保留——watcher 永不 stop/re-dispatch，TaskStop 與重派決策＝主 session。

要點：STOP verification 程序（metadata terminal＋cursors grace 靜止→STOP_CONFIRMED；否則 STOP_INCOMPLETE＋detached child 處置清單）；RETRY_SAFE 判定清單（**三事分離**：surviving handles 全 collect？outward side effect 盤點？**deliverable 是否已存在（checkpoint/artifact 先 collect）？**——任一不明＝RETRY_SAFETY_UNKNOWN 禁重派）；**quarantine 期恢復活動記 `resumed_during_quarantine=true` 仍照砍（user 裁決，禁 liveness inference 回滲）**；`agent-workflow/SKILL.md:83-84` 驗屍法段改寫為工具化指涉。驗證：doctrine rg 錨點（`rg resumed_during_quarantine skills/agent-workflow/` 命中）＋情境演練記錄。

## S4：dogfood＋整合

真 subagent 實測：TC-4（長 sleep agent→收割→停止→驗證）＋K3 註冊率＋正常長工不誤殺（SM-1/2 連續 24h 觀察）。產出 dogfood 報告入任務家。

## 整合策略

baseline: 308f9a718f0e958291f1cc29f094481db2933827。author_family: glm。下游：AIR-135.7 結算材料；AIR-149 追蹤卡（開卡中）。與 AIR-146 正交（bridge 域不動）。

## 收尾步驟

1. `scripts/` instruction 檔新建（Capabilities 表＋watcher 導航）＋**EP 追蹤卡（AIR-149）與實作卡結案兩步**＋弧結案蒸餾第三動
2. SYSTEM-MAP：無
3. instruction 檔：`skills/agent-workflow/SKILL.md` watcher 段改寫（S3 交付）
4. `/audit-test`：新增測試稽核

## EP Review 紀錄

boundary profile（fresh＋intent 分離）。intent 腿 10 findings（job 紀錄見 session log）——judge 裁決：

| # | Severity | Finding 摘要 | 裁決 | 落點 |
|---|---|---|---|---|
| F1 | 高 | TC-1 S 級 oracle 未材料化（缺四類轉移：wake dedup／quarantine 恢復仍砍／UNKNOWN 進出／hard-death exit） | ✅ 採納 | S1 frozen spec 轉移表 T1-T9（本輪材料化） |
| F2 | 中 | 「恢復活動仍照砍」無 EP 條文落點（doctrine 回滲縫） | ✅ 採納 | S1 T4＋S3 要點＋rg 驗證式 |
| F3 | 中 | K1 probe 被動採樣不可證偽 | ✅ 採納 | K1 改誘導法＋真工作中操作化定義 |
| F4 | 中 | TC-4 長 sleep 誘導落入 SM-2 豁免（測不到收割路徑） | ✅ 採納 | TC-4 改 stdout 封閉分離命令 |
| F5 | 低 | RETRY_SAFE 清單缺 deliverable-exists 第三事 | ✅ 採納 | S3 三事分離補全 |
| F6 | 低 | brief 禁未登記 daemonized child 無落點 | ✅ 採納 | S2 要點＋S3 |
| F7 | 低 | K3 分母結構性盲 | ✅ 採納 | K3 分母＝log started 事件數 |
| F8 | 低 | sink/expected 欄位語義缺口＋harvest B 執行者未定 | ✅ 採納 | S2 欄位語義＝AC#2 投影；harvest_delta 主 session 呼叫 |
| F9 | 低 | SM-7 reset/扣除二義 | ✅ 採納（擇扣除） | S1 凍結判準＋T2 |
| F10 | 低 | 收尾無建卡步（UC 盤點指涉斷鏈） | ✅ 採納 | 收尾步驟 1 補建卡結案 |

fresh 腿 11 findings（5 Important＋6 Suggestion）——judge 裁決全數 ✅ 採納：

| # | Severity | Finding 摘要 | 落點 |
|---|---|---|---|
| F1 | Important | 「池掃零命中」宣稱被證偽（`project_air135-watcher-arc-inflight` 雙命中——掃描當時未實跑） | 掃描範圍修正＋收尾納入蒸餾 |
| F2 | Important | STOP 相位驅動者歧義＋wake 後生命週期未定 | S1 加 `--verify`／`--harvest-delta` invocation＋exit 後其餘 entry 中止監視語義＋pending receipt 路徑/dedup key |
| F3 | Important | exit 契約不完整 | S1 frozen exit 表（0/2/3＋內部錯） |
| F4 | Important | 「artifact」面未定義 | 觀察面 frozen 定義＝`~/.zcode/cli/artifacts/sess_<taskId>/` |
| F5 | Important | AIR-147 doctrine 檔案相撞（同改 agent-workflow:83-84） | 兩卡互加接線註記：本 EP S3 先寫工具指涉、AIR-147 疊加 auto-arm |
| F6 | Important | registry 與 AIR-135.7 台帳概念重疊 | S2 對帳句（in-harness workspace 投影） |
| F7 | Suggestion | 殭屍 corpus 數字漂移（36→39→40） | S1 開工快照入 fixtures，TC-2 引快照計數 |
| F8 | Suggestion | 空 registry 行為未定 | 檔缺席 fail-loud／空檔 exit 0 |
| F9 | Suggestion | torn read／JSONDecodeError 未歸類 | fail-loud 擴充 |
| F10 | Suggestion | 時鐘回撥未命名 | elapsed<0＝Fresh＋telemetry |
| F11 | Suggestion | 「前兩者」指涉歧義 | 具名 AIR-148＋AIR-135.7 |

**Review ledger：全 terminal（intent 10＋fresh 11 全 ✅ 回寫完成）→ EP accepted，S1 可進 /implement。**
