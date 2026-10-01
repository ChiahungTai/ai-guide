# EP：CR 查證與收線證據閉環——review 腿 route 宣告→ledger receipt→judge 收線

> **ep_type**: implementation
> 對應卡：AIR-224（backlog/tasks/air-224*.md）；審計依據：.agent-tmp/cr-review-audit/report.md＋merged-brief.md＋verdict-codex.md＋mosaic 對話紀錄級審計（AIR-224 開卡信 d47ac7e7 已通報分工）

## 實作總覽

**問題**（兩份審計交叉實證）：review 的 CR 查證契約（route 宣告→bridge marker→judge 收線核對）條文完備，但**從未有腿走完全鏈**——外審 worker 零實呼（多為 docs diff 合法 N/A）、in-harness 腿 2/17（12%，一條 prompt 強制一條自發）、`.review/` ledger 九檔零 `[cr:*]` marker、bridge brief 零 route 宣告。根因＝**宣告無生產者強制點**（review-engine:190 條文在、spawn prompt 生成不強制）＋**receipt 無承載欄**（ledger schema 無 route 位）＋**代償掩蓋**（dispatcher 預跑 preprovided-cr 讓「整體有用」掩蓋 worker 零使用）。

**收口不變式（本 EP 的單一核心主張）**：對每條命中 structural-evidence trigger 的 review 腿，必須留下三段可機械對帳的 receipt——**route 宣告 → actual evidence → judge 收線**；未命中 trigger 的腿顯式 N/A（applicability sentinel）。**沒有 per-leg receipt 就不能宣稱 review chain 收斂。**

**設計裁定**（codex verdict 採納）：route 是 **review-leg 級**事實（非 finding 級）；ledger 走既有 `coverage=` 欄承載 per-leg CR receipt 子格式（不造平行 top-level schema）；`[cr:*]` 保留 material-evidence 語義與 route 正交；in-harness 用既有 `crsurface=` 投影（不發明新欄）；telemetry instrumentation 同卡、一週觀察另開 follow-up 卡。

**執行紀律**：docs mode＋**兩個 script**（review_ledger.py lint gate＋cr_usage.py telemetry——S4； Boundary profile 審查（控制面契約＋跨 context invariant）；統一用語繁中＋英文術語；md 編輯禁 sed；`rg "四家|三端"` 殘留掃描（歷史卡不計）；用語消歧——本 EP「receipt」專指 CR receipt，CollectionReceipt/provenance receipt 另稱原名。

## UC 盤點

### Backlog 關聯
- AIR-224（owning 卡，full tier）
- 上游：AIR-216（bridge route 三態＋收線核對——本 EP 把收線核對從 bridge 外審推廣到 in-harness＋ledger 承載）、AIR-220（grok schema 四形）
- 下游：mosaic dogfood（契約落地後新裁決腿依新形態執行並回報）

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（元專案）——跳過（正當跳過）

### 掃描範圍
- skills/review-engine/SKILL.md:190-198（spawn 注入＋bridge marker 消費）
- skills/bridge-dispatch/SKILL.md:66/:94-102（AIR-216 route 三態＋收線核對——本 EP 只讀對照不重刻）
- skills/agent-workflow/SKILL.md:45（crsurface= 派工宣告＋materialization gate）
- skills/judge-review/SKILL.md:124（negative verdict CR 複核）
- skills/_common/workflow-review-pattern.md:185（ledger identity/schema）
- skills/post-build/scripts/review_ledger.py:306（lint 實作）＋tests/test_governance_*
- skills/corrections-weekly/scripts/cr_usage.py（telemetry 面）
- 同主題 memory 條目：零命中（rg cr-receipt/unverified-by-graph 於 .agents/memory/_inventory.md 無相關條目）

### 既有 UC 狀態／新增 UC
| 能力 | 狀態 | 說明 |
|------|------|------|
| bridge 外審 route 宣告＋收線核對 | ✅（AIR-216/220） | 本 EP 對照源，不重刻 |
| in-harness crsurface= 派工宣告 | ✅ 條文在 | 本 EP 補「投影→receipt→judge」後半鏈 |
| per-leg CR receipt（ledger） | 📋 新增 | S1 |
| review_ledger.py receipt lint gate | 📋 新增 | S2 |
| judge 收線 receipt gate | 📋 新增 | S3 |
| CR telemetry 分項量測 | 📋 新增 | S4 |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | review 腿命中結構查證 trigger | WO/spawn 命中 callable 變更審查 | 腿定義帶 route 宣告（external＝route: 行；in-harness＝crsurface 投影） | WO lint/prompt 檢查 | per-leg receipt |
| SM-2 | 腿無結構查證 trigger | docs-only diff 審查 | 顯式 `cr: n/a（無結構查證 trigger）` receipt——非空欄 | ledger lint | per-leg receipt |
| SM-3 | live-cr 腿完成 | worker/judge 收線 | coverage 含 `cr(route=live-cr:MCP, evidence=<ref>)`＋material `[cr:present|empty]` 正交並存 | review_ledger lint | receipt |
| SM-4 | degraded 腿（glm 無 face） | crsurface=absent | `cr(route=degraded, reason=no-cr-query-face)`＋受影響 claim 逐條 unverified-by-graph | ledger lint＋judge | receipt |
| SM-5 | eligible 腿缺 receipt | ledger 無該腿 receipt | review_ledger lint FAIL——不得收斂 | lint gate | receipt lint |
| SM-6 | 宣告 live-cr 但零 evidence | histogram 0 命中 | lint FAIL（宣告≠實際）＋AIR-216 收線核對語義引用 | lint gate | receipt lint |
| SM-7 | telemetry 分項 | 週期 cr_usage | 輸出 route 宣告率/實呼率/receipt 率/closure 率分項（dispatcher 預跑不洗白） | cr_usage 輸出 | telemetry |

## 測試規劃段（review_ledger.py 可執行變更——TC 凍結）

| # | claim | Given-When | oracle | oracle_source | evidence | uncovered |
|---|-------|-----------|--------|---------------|----------|-----------|
| TC-1 | eligible 腿缺 cr receipt→lint FAIL | ledger 檔含命中 trigger 的腿（legs 名冊在場）無 cr 子格式 | exit 非 0＋定位該腿 | review_ledger.py 既有 lint 契約＋本 EP schema 節 | L2 | schema 外欄位語義 |
| TC-2 | degraded 無 reason→FAIL；N/A 有 reason→PASS | 兩 ledger fixture | exit codes | 同上 | L2 | — |
| TC-3 | live-cr/preprovided 有 evidence ref→PASS | 兩 fixture（evidence=<job/tool receipt>/<artifact provenance>） | exit 0 | 同上 | L2 | evidence ref 內容真偽（另腿） |
| TC-4 | 真實舊檔形態（frozen snapshot）無 cr receipt→ledger 級 FAIL＋cr-專屬 violation 字串命中 | 凍結 snapshot fixtures（tests/fixtures/review_ledgers/——.review/ ephemeral 不入測） | exit 非 0＋斷言 cr-receipt 專屬訊息（防空洞——air-91 fixture 本就因非 cr 原因 FAIL） | 同上＋fresh-F5 三坑規避 | L2 | 逐腿定位（legacy 檔無名冊——ledger 級 FAIL 為現實 oracle） |
| TC-5 | monitor/第三方消費端零回歸 | 既有 tests/test_review_ledger.py（正確錨——governance suite 不觸 review_ledger）＋tests/fixtures/review_ledgers/ | 全綠 | 既有 suite | L2 | — |

author_family: glm（EP 作者 session＝GLM-5.3）——implement dispatch 時 same-family precondition 適用（challenge 已由 dual-family 審計替代：兩份獨立審計即 challenge 證據）。

## 段落 0 全域研究（摘要——研究主體已由兩份審計完成，本節引用）

- 可複用基礎設施：review_ledger.py lint 框架（:306 identity lint 既有）、`route：` WO 慣例（receipt:/watcher: 先例，AIR-216 已定義三態）、crsurface= 投影表（AIR-216 收線核對段）、cr_usage.py telemetry 框架
- 依賴：ledger schema 變更＝public/cross-context invariant（review_ledger.py:306 identity lint 消費）→ full tier 成立
- 風險假設：①ledger 舊檔（九檔）無 cr 子格式→lint 全 FAIL——**設計如此**（結案前補 receipt），backfill 策略＝只對「新 landing 腿」要求，舊檔標 legacy-exempt（lint 對 legacy-exempt 標記放行）②route 宣告被複製貼上空轉——telemetry 分項（宣告率 vs 實呼率）讓空轉可見
- kill criteria：若 review_ledger.py lint 無法在不破壞既有 identity/coverage 解析下容納 cr 子格式（schema 衝突實證）→ 停止本 schema 設計，改走 ledger v2 遷移 EP（Assumption/Probe/Kill/Action 四欄齊——Probe＝S2 RED 對真實舊檔）

## 段落 S1——receipt 語義凍結＋schema（workflow-review-pattern.md）

- **Context**：per-leg CR receipt 子格式的 canonical 語義住 workflow-review-pattern.md「帳本 header identity/schema」節；消費端＝review_ledger.py（S2）與 judge-review（S3）。UC：per-leg CR receipt。與 S2 共享 grammar；與 S3 共享 terminal state 值域。
- **修改要點**：coverage= 欄擴 per-leg 行——`<family/leg>: ... cr(route=live-cr:MCP|live-cr:CLI|preprovided-cr|degraded, evidence=<ref>|reason=<why>)`；**applicability 與 route 兩範疇分離**：`cr: n/a（reason=無結構查證 trigger；dispatch 端 trigger 事實 ref 必附）`是 applicability sentinel 非 route 值（fresh-F10）；**leg 名冊為強制行**（fresh-F1）：ledger header 加 `legs：<leg key> <jobId> [trigger|n/a]；…`（收編 .review/air-91.md:7 既有先例）——receipt 行以 jobId join 名冊，缺名冊＝lint FAIL（SM-5/TC-1 可實現的前提）；**judge 收線另立行**（fresh-F7）：`cr-closure：<leg key> checked|rejected`——producer 事實（route/evidence）與 Arbiter 裁決分離，兩段式寫入（腿寫 receipt→judge 寫 closure）；**legacy-exempt 機械錨**（fresh-F4）：僅 `reviewed` hash 早於凍結 cutoff 常數（S2 內定義）的帳本可蓋章，telemetry 加 exempt 率分項防大量靜默豁免；grammar 凍結句＋單一源宣示：route 值域單一源恆在 bridge-dispatch、cr grammar 單一源在 workflow-review-pattern、lint 為 consumer-equivalent 鏡像（fresh 軸 2 canonicality 起皺點收口）。文件同步：judge-review:124 引用、agent-workflow:45 投影表（S2 對照）。
- **EP Review 修訂紀錄**（fresh F1/F4/F7/F10＋intent 準阻塞——2026-10-01 judge 採納寫入本段）
- **驗證策略**：S2 TC-1/2/3 對 grammar 的正負 fixture；文件 consistency（rg 新 grammar 段在場）。

## 段落 S1b——producer carrier：WO route 行＋crsurface 投影（intent 腿準阻塞缺口補段）

- **Context**：intent 腿準阻塞——卡決策①/Scope 首項/codex AC#1/合併簡報根因#2 四處共同要求的 external WO route carrier 生產者面，EP 初稿無 segment 擁有 work-order.md（懸空指針）。本段補齊。
- **修改要點**：①skills/_common/work-order.md review/advisory variant（:156 一帶）加 per-leg route carrier 必填行——`route：live-cr[:MCP|:CLI]｜preprovided-cr｜degraded｜n/a（reason=無結構查證 trigger）`（漏欄＝contract-incomplete，比照 receipt:/watcher: 慣例形態）②skills/agent-workflow/SKILL.md:45 補 crsurface→route canonical projection 表（mcp→live-cr:MCP、cli→live-cr:CLI、attach→preprovided-cr、absent→degraded；既有 materialization gate 不變）③review-engine:190 owner 接線明示兩 enforcement points（external＝WO route carrier；in-harness＝materialization gate）——不加重複 MUST（決策⑧）。
- **驗證策略**：rg route carrier 行在場；WO fixture 漏欄判 contract-incomplete 的條文斷言；投影表四 mapping 與 AIR-216 收線核對段一致。

## 段落 S2——review_ledger.py receipt lint gate

- **Context**：UC「receipt lint gate」。消費 review_ledger.py 既有 lint 框架（:306 identity）；與 S1 共享 grammar。
- **修改要點**：lint 新增 cr-receipt 檢查（命中 trigger 腿缺 receipt FAIL／degraded 無 reason FAIL／N/A 有 reason PASS／live/preprovided 有 evidence ref PASS／legacy-exempt 放行）；正負 fixture 五組（TC-1~4）；`--stage converged` 全查。
- **驗證策略**：TC-1~4 全綠（RED 先行對真實舊檔）。

## 段落 S3——judge 收線 receipt gate

- **Context**：judge-review:124 既有 negative verdict CR 複核；本段加「收線前 ledger gate」——eligible 腿 route/evidence 缺失或宣告≠實際不得收斂（引 S2 lint 為機械面）；in-harness 腿核對語義（我方審計 G2）同段下沉。
- **修改要點**：judge-review SKILL 收線節＋workflow-review-pattern judge state 值域；[cr:*] 四態正交條文確認（不與 route 混欄）。
- **驗證策略**：條文 consistency＋S2 lint 為機械閘引用。

## 段落 S4——telemetry 分項＋owner 對齊＋mosaic dogfood

- **Context**：AIR-216 落地後 dispatcher 零跟進（我方審計 G1）——量測先行。
- **修改要點**：cr_usage.py 加 route 宣告掃描計數（bridge brief `route：` 行＋in-harness crsurface 分布）——輸出分項照 codex AC6 七項補齊（eligible/declared/observed-evidence/receipt/degraded/N-A/silent fallback 各獨立計數，receipt/closure 率的帳本掃描源與窗口語義凍結——fresh-F8）；SM-6 histogram 核對歸本段＋bridge 收線核對引用（**不進 review_ledger lint**——fresh-F6：禁腳本化條款相抵）；review-engine:190 owner/pointer 對齊（S1b 兩 enforcement points）；mosaic dogfood 通報（AIR-224 卡 notes 記——契約落地後 mosaic 新裁決腿依新形態）。
- **驗證策略**：cr_usage 輸出新分項（fixture job jsonl）；rg pointer 在場。
- **S3 judge checklist 補**（fresh-F9）：N/A 腿豁免主張複核（n/a 行須附 dispatch 端 trigger 事實 ref，矛盾即不收斂）。

## EP Review Cycle 紀錄（boundary profile——fresh＋intent，2026-10-01）

- fresh 腿：Approve-with-amendments——F1 High（legs 名冊缺→SM-5/TC-1 不可實現）＋F2 High（TC-5 錨錯 suite）＋F3/F4/F5 Important＋F6-F12——**全數採納**：F1/F4/F7/F10 已寫入 S1 grammar；F2/F5 已改 TC-4/TC-5；F3 已改執行紀律（兩個 script）；F6 已改 SM-6 歸屬；F8 已入 S4；F9 已入 S3 checklist；F11 已補掃描範圍（test_review_ledger.py/improvement_signals/commit+post-build invocation/帳本變體/用語消歧入執行紀律）；F12 process note。
- intent 腿：ALIGNED-WITH-NOTES——準阻塞（WO carrier 生產者段缺失）→**新增 S1b**；收口順序恢復五段（telemetry baseline 凍結前置）→本 EP 整合策略已照五段；分項七項補齊→S4；「不動面」顯式複述→決策清單照卡（隱式保證記錄為可接受）。
- judge（5.3）：兩腿 19 項全採（0 駁）——EP 修訂已寫入本檔各段。**accepted**。

## 收尾段

1. 卡 AIR-224：AC 對照結算＋review_ledger lint 對九檔 legacy-exempt 決策記錄
2. instruction 檔同步：workflow-review-pattern/judge-review/agent-workflow/review-engine 相互指針 consistency
3. /audit-test：review_ledger.py 新測試稽核
4. follow-up 觀察卡開立（一週 conversion 驗證——mosaic dogfood＋我方 job sample）
5. 弧結案蒸餾：本弧 memory 候選（審計方法論：job histogram＋ledger 對帳）

## 整合策略

baseline: d259bd4b（開卡 commit；EP 定稿後重錄）
産出順序＝收口順序（codex 裁定五段＋intent 順序恢復）：**telemetry baseline 凍結**（S1 前置）→S1（凍結語義＋legs 名冊）→S1b（producer carrier）→S2（lint gate）→S3（judge consumer）→S4（instrumentation＋mosaic dogfood）。S1/S1b/S2 同弧同 landing（producer/consumer schema 不留半套窗口）。
