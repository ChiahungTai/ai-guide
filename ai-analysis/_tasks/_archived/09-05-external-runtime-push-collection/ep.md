# EP: external-runtime 委派收法 push 化（ETA-gate fallback）

> **ep_type**: implementation
> baseline: 55d128a1ef1b32f71fa211f774c57b59e8055ec0

## 實作總覽

**問題**：兩家現行委派（muse／codex）收法在 LLM 層輪詢（grok 同族架構、適用同一收法——但 09-05 時點 ZCode 未安裝，無現行收法）——`agents/AGENTS.md`「dispatch face 與收法」段記載 muse＝「背景 Bash＋jobs.json 輪詢（rg＋ps）」、codex＝「wrapper＋resume-to-poll」。每輪輪詢＝1+ LLM request 且全 context 重送（token-value 計費下 requests 與 context 雙重浪費）；AIR-13 弧實證 wrapper≠job 錯位（muse×2＋codex×2 均需介入收斂）。

**解法**：收法 push 化——主 session 背景 Bash 掛 bridge 阻塞呼叫（`task` 前景阻塞形／`wait` 子命令），process exit＝harness 自動喚醒，完成時恰好 1 個 request、等待期間 0 request。輪詢只存在 bridge 進程內部（muse `wait` 已是 `WAIT_POLL_MS=500` 固定輪詢 ledger——亞秒偵測、零 LLM 成本）。

**已決策（勿重辯）**：
- **push 優先**（user 2026-09-05 裁定）
- **bridge 端不做 ETA 階梯輪詢（YAGNI）**：muse `wait` 輪詢已 500ms、bridge 層輪詢零 LLM 成本——**interval 形狀**對成本與延遲皆無增益；ETA/階梯的價值只在「LLM 層自己 poll」的世界，而那正是本 EP 消滅的對象。user 提的階梯設計以 **LLM 層 fallback 紀律**形式吸收（見 SM-4）。**但 timeout 形狀是另一回事**：`wait` 預設 5min（`WAIT_DEFAULT_TIMEOUT_MS=300000`）／codex `status --wait` 預設 4min（`240000`）——長跑兩段式必帶 `--timeout 0` 或顯式大值（見 SM-2），user 階梯設計在 timeout 面的著力點即此
- **codex／grok upstream 不改**——push 模式下無需動 upstream repo（也動不了）
- **S2 降級為範本預載＋落差記錄**：三家 plugin 都有 SessionEnd 孤兒清理 hook（muse 0.2.4 `hooks/hooks.json`「cancel+kill on end」、codex `terminateProcessTree`、grok 同款），但 ZCode 3.7.7+ user-level hooks＝**7 事件子集、無 SessionEnd**（`ref-docs/harness/contracts.md:15,25` 定案；04 報告 §7 實測）——現版 config 註冊不可行；merge 延至官方支援（build 時對 zcode hooks 文檔事件表複核一次）

## UC 盤點（元專案 docs 形態——掃受影響命令/rules 清單）

### Backlog 關聯
- **AIR-21**（To Do「muse-plugin-cc bridge wait 子命令」）：root fix 已於 bridge 0.2.4 落地（阻塞至終態／`{job, finalText}` JSON／timeout exit 124，`muse-bridge.mjs:1706` runWait），**但 wait 零測試覆蓋**（`tests/bridge.test.mjs` 無 "wait" 命中），且卡 desc 的 `--interval N` 構想被本 EP YAGNI 決策取代。處置＝S3 更新卡 desc（落地事實＋補測試帶去 muse-plugin-cc session）；不在本 EP 擴 scope
- **AIR-13**（Done）：dispatch face 與收法段原始落地——本 EP 是其收法更新
- 自動建卡：EP 追蹤卡 1 張（AIR-26）

### 掃描範圍
- `agents/AGENTS.md:39-42`（dispatch face 與收法）
- `skills/model-routing/SKILL.md:74-92`（reviewer 交接契約 74-78／flag profile→spawn 參數 80 起／bridge 必經 92）
- `agents/AGENTS.md:44-50`（三態判定表——row-2「poll 收集」處置隨收法更新）
- memory `reference_muse-code-cli-facts.md:50`（wrapper≠job 錯位收法處方——push 化後同步）
- `skills/post-build/SKILL.md:21,86,106`（bridge 必經＋jobId 清單引用——不涉收法，預期不動、驗證確認）
- `rules/model-routing.md`（pointer 段觸發詞）
- `hooks/zcode-registration.json`（S2 載體）；環境 `~/.zcode/cli/config.json` hooks.events
- memory `reference_external-runtime-delegation-family`（09-05 已記機制對照——S3 補終態）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|---|---|---|---|---|
| external-runtime 委派 dispatch face 與收法 | ✅ | agents/AGENTS.md | 更新 | 收法從 LLM 層輪詢改 push＋ETA-gate fallback |
| bridge 必經（muse 委派唯一入口） | ✅ | model-routing skill | 無影響 | 入口不變、收法變；jobId 欄位不變 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|---|---|---|
| external-runtime 委派 push 收法（背景 Bash exit 喚醒＋ETA-gate fallback） | 📋 | agents/AGENTS.md＋skills/model-routing/SKILL.md |

## Scenario Matrix（docs 語境：rg 命中／0 殘留；SM-4 為行為紀律）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|---|---|---|---|---|
| SM-1 | 簡單轉發委派 | review／critique／diagnosis | 主 session 背景 Bash 直呼 bridge `task`（阻塞形）→ exit 喚醒主 session → stdout 即 finalText；jobId 記錄不變（reviewer 交接契約欄位照舊） | 無 | push 收法 |
| SM-2 | 長跑 >10min | xhigh 委派 | 同 SM-1（背景 Bash 無前景 10min 限制）；或兩段式 `task --background` 拿 jobId → 背景 Bash 掛 wait → exit 喚醒讀 JSON。**timeout 到期訊號拆家系**——muse `wait <jobId> --timeout 0`：裸 wait 預設 5min 到期＝`process.exit(124)`（124＋running＝重掛；0＝forever）；codex `status --wait <jobId> --json`：預設 4min 到期＝正常 exit 0、JSON 帶 `waitTimedOut: true`（以此旗標判讀重掛；124 偵測對 codex 永不觸發；**無 0=forever**——`--timeout-ms 0` 靜默回落 4min，只能顯式大值）；wait 回非 completed 終態 → `jobs/<id>.jsonl`＋working tree 對照再判（reconcileStaleRunning 可能過早標 interrupted） | 無 | push 收法 |
| SM-3 | wrapper 保留場景 | codex prompt 工程（gpt-5-4-prompting 改寫） | wrapper 內單次阻塞 `task`＋env fallback 預寫（不變）；標註＝「wrapper Bash 10min 上限是**約束事實**、wrapper≠job 錯位是**獨立實證**、兩者因果未驗證」——預期超時的工單改走 SM-2 直呼 | 無 | push 收法 |
| SM-4 | LLM 層 fallback（罕見） | 原始派發無背景 Bash 掛載（wrapper 形態錯位補救等——前景短 arm 仍可用） | **ETA-gate 紀律**：推估完成時刻前零檢查（一段 `--timeout <eta>` arm）；屆時單次檢查；未終局→重掛遞減 timeout 的 `wait` arm（起點＝bridge 預設 5min／4min，按 ETA 緊化至 ~30s 級；每 arm 到期＝1 request——user 接受的 fallback cadence 成本形態）——永不做 LLM 層定時輪詢 | 無 | push 收法 |
| SM-5 | codex env 假完成 | `CLAUDE_PLUGIN_ROOT` 空→MODULE_NOT_FOUND | 判定 job 未建立→重派**新** agent（非輪詢、非雙跑）——memory reference_codex-companion-plugin-root-env | 無 | — |
| SM-6 | 孤兒 job | session 結束 job 仍跑 | 三家 plugin 都有 SessionEnd 清理 hook，但 ZCode 事件子集無 SessionEnd（已決策定案）→ 現版**不註冊**：S2 範本預載（muse／codex 條目；grok 註解待安裝）＋落差記錄；muse 側 bridge `reconcileStaleRunning` ledger 兜底＋post-build 開工背景寫入者盤點涵蓋 | plugin 升級→cache 版號路徑漂→hook 斷線（S2 記維護語義）；未來 ZCode 支援 SessionEnd 時補掛 | — |

## 段落劃分原則

S1（約定）→ S2（hooks 接線）→ S3（收尾）線性；S1/S2 內容可平行。跨 repo 補淡（muse-plugin-cc 補 wait 測試）不進本 EP——AIR-21 承接。

---

## S1 收法約定 push 化（agents/AGENTS.md＋model-routing skill）

### Context
- **背景**：現行收法（見總覽）燒 request；三家 bridge 阻塞能力已齊（muse `task` 阻塞＋`wait`、codex `task` 阻塞＋`status --wait`、grok `run` 阻塞＋`runs --wait`）
- **UC 引用**：更新「dispatch face 與收法」＋新增「push 收法」
- **依賴錨點**：`agents/AGENTS.md:39-42`（定義端；消費端＝主 session 委派時、post-build 鏈 jobId 清單）；`skills/model-routing/SKILL.md:92`（bridge 必經段後承接）
- **語義約束**：與 S2 共享「bridge 必經入口不變」；與 post-build 共享「jobId 清單欄位不變」——只改收法不動契約
- **基礎設施盤點**：沿用現有兩列式（muse／codex）段結構，改寫非新增；無新檔
- **技術選型**：純文檔改動（docs mode）；**成功標準**＝rg 掃「resume-to-poll」「jobs.json 輪詢」殘留為 0（歷史文檔除外）＋決策樹可被未載入背景的 session 單讀執行

### 修改要點（docs mode——pseudo code 裁剪）
1. `agents/AGENTS.md` dispatch face 與收法段：
   - muse 列收法：「背景 Bash＋`.muse-bridge/jobs.json` 輪詢（rg＋ps 核對）」→「背景 Bash 掛 bridge 阻塞呼叫（`task` 阻塞形或 `wait <jobId>`）→ exit 喚醒；jobs.json／ps 核對降級為**診斷手段**（非收法）」
   - codex 列收法：「wrapper＋標準收法 resume-to-poll」→「預設＝主 session 背景 Bash 直呼 `codex-companion task`（阻塞）；wrapper 保留 prompt 工程場景（單次阻塞、wrapper Bash 10min 上限標註、env fallback 預寫不變）」
   - 新增共通條目：LLM 層 fallback 紀律（ETA-gate＋重掛遞減 timeout 阻塞 wait，SM-4）＋收法經濟學一句（N×request vs 完成時 1×request）
2. `skills/model-routing/SKILL.md` external-runtime 段（bridge 必經小節後）新增「完成回報收法」小節：決策樹（簡單轉發→直呼；長跑→直呼或兩段式 wait；prompt 工程→wrapper；fallback→ETA-gate）＋經濟學動機
3. `rules/model-routing.md` pointer 觸發詞補「收法」（如 description 未涵蓋）
4. `agents/AGENTS.md:49` 三態判定表 row-2 處置「poll 收集，禁重派」→「掛 `wait` 收，禁重派」——同檔相鄰段落隨收法同步

### 驗證策略（docs mode）
- **rg 殘留**：`rg "resume-to-poll|jobs\.json 輪詢|poll 收集"` 全 repo（含 memory 條目、post-build、agents）——命中處逐檔同步或標歷史
- **跨檔一致性**：agents/AGENTS.md ↔ model-routing skill ↔ post-build 引用鏈語義一致（bridge 必經／jobId 不變）
- **導航有效性**：新小節標題可從 rule pointer 觸發詞找到
- `/consistency`
- **致命假設 POC（build 階段 1 前必跑）**：真實小委派（muse `review` 或 codex 短 `task`）以主 session 背景 Bash 直呼——驗證跨 turn 阻塞至終局、exit 自動喚醒、stdout＝finalText。失敗＝EP 方向重評（harness 背景 Bash 對長阻塞進程的行為是唯一未實證前提）

### Invariant Impact
無（文檔約定；不觸 domain invariant）

---

## S2 SessionEnd 孤兒清理 hook——範本預載＋落差記錄（降級段）

### Context
- **背景（F1/F2 修正後事實）**：三家 plugin 都有 SessionEnd 孤兒清理 hook（muse 0.2.4 `hooks/hooks.json`＝「reconcile stale jobs on start, cancel+kill on end」；codex＝`terminateProcessTree`；grok 同款）——CC 原生載入、ZCode 不載入；且 **ZCode 3.7.7+ user-level hooks＝7 事件子集、無 SessionEnd**（`ref-docs/harness/contracts.md:15,25` 定案）→ 現版 config 註冊不可行，本段降級為範本預載＋落差記錄
- **UC 引用**：SM-6
- **依賴錨點**：muse `plugins/muse/hooks/hooks.json`（cache 0.2.4）；codex `plugins/codex/hooks/hooks.json`（cache 1.0.6）；grok 僅在 marketplace clone（**未安裝——條目註解待裝）；`hooks/zcode-registration.json`（範本）
- **語義約束**：與 S1 共享「不動 plugin 檔案本體」——只做 ai-rules 側範本與文件
- **風險（中）**：plugin 升級→cache 版號路徑漂移→範本絕對路徑過時——維護語義寫進範本註解

### 修改要點
1. `hooks/zcode-registration.json` 範本**預載**三條 SessionEnd 條目（muse／codex＝絕對路徑指 plugin cache scripts、timeout 5s；grok＝註解形態標「待安裝後啟用」）＋維護註解（plugin 升級同步路徑；ZCode 支援 SessionEnd 前不 merge 進 config）
2. 落差記錄：`hooks/` 目錄 AGENTS.md（或 README）記「ZCode 無 SessionEnd 事件（contracts.md 定案）→ plugin 孤兒清理 hook 在 ZCode 缺席；muse 側由 bridge `reconcileStaleRunning` ledger 兜底＋post-build 開工背景寫入者盤點涵蓋；**remediation＝ZCode app 重開（收同生命週期進程；detached 背景進程跑完自然結束、結果照落 ledger）＋`git status` 檢 working tree 半套編輯**——實務成本極低（user 2026-09-05 確認），非防護缺口」
3. **條件式 merge**（現版不執行）：build 時複核 zcode hooks 官方文檔事件表——若已支援 SessionEnd，才走 `cp config.json config.json.bak` → merge → parse 驗證（memory backup 慣例）

### 驗證策略
- 範本 JSON parse 有效；muse／codex hook 腳本手動直跑：`echo '{}' | node <plugin cache>/scripts/session-lifecycle-hook.mjs SessionEnd` exit 0（無 side effect on 空 state）
- 落差記錄存在（rg 命中）；config.json **未**被本段觸碰（現版 dead path 不硬做）
- zcode hooks 文檔事件表複核結果記錄在完成報告

### Invariant Impact
無

---

## S3 收尾

- `/consistency`（docs 單檔閘門——純 .md 變更 commit 前必跑）
- 受影響命令行為反映檢查：post-build dual-family 段、skills/CLAUDE.md 索引 description（如涉收法詞彙）
- **AIR-21 卡處置**（卡動作約束：先 `task edit AIR-21 -s "In Progress"` 再動）——desc 更新：wait 已落地事實＋零測試覆蓋＋`--interval` YAGNI 論證；補 wait 測試帶去 muse-plugin-cc session；處置完 `-s To Do`（未結案——測試未補）或依 user 裁定結案
- EP 追蹤卡結案兩步（`-s Done --final-summary` → `--ref` 換 done/ URL）
- memory 更新：`reference_external-runtime-delegation-family` 補終態（收法已 push 化＋ETA-gate＋timeout 紀律）；`reference_muse-code-cli-facts.md:50` wrapper≠job 錯位收法處方改 push 語義（jobs.json／ps＝診斷非收法）——兩檔 MEMORY.md 索引行同步檢查
- AIR-26 卡 desc 同步 S2 降級決策（F-1 型 scope 校準回寫）
- /audit-test 不適用（無測試產物）；元專業形態收尾＝受影響命令行為已反映

---

## 整合策略

- **順序**：S1 POC（致命先驗）→ S1 → S2 → S3
- **baseline**：55d128a1ef1b32f71fa211f774c57b59e8055ec0
- **跨邊界**：`~/.zcode/cli/config.json` 為無版本活配置（.bak 先行）；muse-plugin-cc 補 wait 測試＝AIR-21 承接（跨 repo session，非本 EP）
- **commit 邊界**：S1+S3 文檔同 commit；S2 的 config.json 不入 repo（環境檔），範本入 repo
- **量測（可選）**：下次真實 dual-family review 記錄委派收法 request 數對比（push 前後）

---

## EP Review Findings（獨立審查 → judge 裁決 → 修正記錄）

> 審查：Explore 獨立 agent（2026-09-05，VERDICT: ACCEPT-WITH-FIXES）；裁決：主 LLM judge-review（10/10 ✅，反sycophancy：P0＋P1×3 於裁決**前**獨立機械複核屬實、F7 否證重查＝措辭非邏輯洞）。EP flow status：open → **implemented**（本節即修正落點記錄）。

| id | severity | title | decision | 證據（一行） | 處置落點 |
|----|----------|-------|----------|--------------|---------|
| F1 | P0 | muse 其實有 SessionEnd hook | ✅ | muse 0.2.4 `hooks/hooks.json`「cancel+kill on end」親驗在場 | S2/SM-6 改「三家皆有」 |
| F2 | P1 | ZCode 無 SessionEnd 是既有定案 | ✅ | `ref-docs/harness/contracts.md:15,25`（7 事件子集） | S2 降級＝範本預載＋落差記錄 |
| F3 | P1 | grok 未安裝、無 cache 可指 | ✅ | installed_plugins 無 grok（本弧親驗） | 總覽改「兩家現行」；grok 條目註解待裝 |
| F4 | P1 | wait 撞預設 timeout | ✅ | `WAIT_DEFAULT_TIMEOUT_MS=300000`／codex `240000` 親驗 | SM-2 timeout 紀律；YAGNI 補「timeout 形狀」面 |
| F5 | P1 | 三態表「poll 收集」漏改 | ✅ | `agents/AGENTS.md` 三態表 row-2 親驗 | S1 要點 4＋rg pattern 增補 |
| F6 | P2 | muse-code-cli-facts:50 舊收法處方 | ✅ | 該行 prescriptive（本弧親讀） | S3 memory 更新清單補列 |
| F7 | P2 | SM-4 觸發/處置語義含混 | ✅ | 前景短 arm 可行＝非邏輯洞 | SM-4 觸發改寫＋arm 成本標明 |
| F8 | P3 | model-routing 範圍 74-92 | ✅ | rg：reviewer 交接契約＝74、flag profile＝80 | 掃描範圍改 74-92 |
| F9 | P3 | wrapper 10min 因果未標推測 | ✅ | memory 僅證錯位實證＋上限記載 | SM-3 改「約束事實／獨立實證／因果未驗證」 |
| F10 | P3 | reconcileStaleRunning 早退風險 | ✅ | runWait 每輪呼叫＋memory 已警告 | SM-2 補 jsonl＋working tree 對照 |
