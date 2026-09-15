---
name: model-routing
description: "Spawn／委派／派工前必載——決定用哪個 model 的解析表單一源。AIR-91 doctrine（WorkUnitContract schema／Role→authority allow-list／resolver precedence 七步／AvailabilitySnapshot tri-state／ArcOverride／RoutingPolicy／DispatchPlan/Trace schema——model 供給事實單一源＝catalog.toml、registry 部署預設＝agents/presets.toml，本檔不重抄值）＋dispatch 預設與額度 failover（policy 面；額度現值不住本檔，查 spine model-runtime-entitlements）＋external-runtime family（muse/codex/glm-bridge）→(model, effort, 容量) 解析＋lite 分工律（保護面厚度、判斷密集位 full）＋eligibility gate／reviewer 交接契約／套用三路徑＋rate limit 並發表＋webgpt 使用約束與五類失敗態＋glm bridge 契約（native-ID-only、write-mode、effectiveModel）＋spawn 失敗態（1301/1308/1302、classifier unavailable 重試≤2）＋thoughtLevel sticky 但書。always-on 骨架在 rules/model-routing.md。觸發詞：spawn model、派工、委派、工單、額度、failover、tier、pins、glm-5.3-flash、chatgpt-web、webgpt、muse、codex、分工律、保護面、haiku、external-runtime、effectiveModel、額度池、wham、ran out of room、eligibility、收法、三態判定、定向接續、session-id、fork、1301、1308、1302、work unit、WorkUnitContract、resolver、DispatchPlan、qualification、judgment floor、catalog、presets。"
---

# Model Routing — 解析表與 provider 事實

> 本 skill 是 `rules/model-routing.md` 的 on-demand 深層載體：rule 端保留 always-on 骨架（precedence 七步、hard invariants、external-runtime routing 段頭＋pointer——內容在本檔）；本檔承載 glossary／WorkUnitContract schema／resolver protocol、dispatch 預設與額度 failover policy、external-runtime family→(model, effort, 容量) 解析表、eligibility gate、reviewer 交接契約、套用三路徑、rate limit 與並發上限表、thoughtLevel 但書與 classifier 處置。model wire token／effort encoding／transport 供給事實單一源＝同目錄 [catalog.toml](catalog.toml)；registry 部署預設（pins）單一源＝[agents/presets.toml](../../agents/presets.toml)（default binding FK→catalog，`sync_agents.py --map` 機械對帳）——本檔不重抄 wire token／effort encoding／transport 供給事實（dispatch 政策敘述中的 model 具名除外）。

## AIR-91 doctrine：vocabulary／WorkUnitContract／resolver protocol（派工權威）

> 本節是 instruction resolver 的唯一源（glossary／schema／precedence／輸出契約）；機械可驗證的供給事實（ModelIdentity／DispatchBinding／qualification records／allow-list metadata）單一源＝同目錄 [catalog.toml](catalog.toml)——`sync_agents.py` loader 驗 schema（token 分欄／enum／FK／唯一性／volatile 欄位拒斥），本檔不重抄 wire token／effort encoding／transport 供給事實（dispatch 政策敘述中的 model 具名除外）。resolver 是 LLM instruction protocol，不是 Python runtime router；TOML 與 sync_agents 只承擔可機械驗證的 supply 與（S2 起）deployment projection。

### glossary（vocabulary）

| 詞 | 定義 |
|---|---|
| Role | work unit 可持有的責任與 authority（首期 Planner／Implementer／Reviewer／Verifier／Arbiter）；只由 WorkUnitContract 指派——catalog／preset／registry slug 不擁有 Role（role-like slug＝compatibility adapter） |
| judgment_floor | 判斷需求軸，首期 {decision, execution}；decision 滿足 execution、反向不可；effort 不能把未 qualification 的 candidate 補成 decision-qualified |
| capabilities | 與判斷正交的能力軸：native_vision（ModelIdentity 的模型能力）× image_transport（DispatchBinding 的運輸能力）；direct visual eligibility＝兩者交集 |
| qualification | model 對 workload 的資格，catalog 兩正交欄：status{qualified, conditional, unqualified} × evidence_source{user_observed, repo_observed, official_documentation, pending_first_use}；conditional 是資格狀態非證據來源；availability 禁入任一欄 |
| workload | 首期六值：ep_synthesis／adjudication／implement_from_accepted_ep／evidence_retrieval／review_findings／visual_observation（allow-list 在 catalog） |
| candidate | 四元組 (model_identity, dispatch_binding, requested_effort, effective_effort)——不是裸 model 名 |
| Arbiter／Marshal | Arbiter＝Role 值（judge-review 是執行 Role=Arbiter 的 workflow adapter）；Marshal＝composite workflow 的 orchestration responsibility，非 Role／agent／skill |
| family／profile | family＝external runtime 家族（muse／codex／glm——**運輸身分軸**，非 model 強度軸）；profile＝external runtime 的 transport mode（implement／review／advisory）。詞彙定義單一源＝本 glossary；rule 端僅留 pointer |

### WorkUnitContract schema（owning workflow 持有；欄位語義本節單一源）

| 欄位 | 語義 |
|---|---|
| role | Planner／Implementer／Reviewer／Verifier／Arbiter |
| authority | 輸出權限上限（見 Role→authority allow-list） |
| judgment_floor | decision／execution |
| qualifications | 需求的 workload tokens（對 catalog qualification records 硬過濾） |
| capabilities | 需求能力軸（如 native_vision＋direct visual） |
| independence | kind=different_provider_family＋relative_to＋required＋fallback（預設 soft-visible；user 明示為 hard） |
| surface／escalation | 派工面與升級停止條件（pending finding／EP conflict／invariant／public boundary／反覆失敗→decision escalation） |

### Role→authority allow-list（越權輸出＝artifact schema 層阻擋）

| Role | 允許 authority |
|---|---|
| Planner | plan／EP synthesis（無 apply） |
| Implementer | apply（accepted EP 後）／evidence |
| Reviewer | findings（無 disposition／apply） |
| Verifier | evidence artifact（無 disposition／apply） |
| Arbiter | final disposition／adjudication |

authority 輸出契約：evidence artifact 不含 disposition/apply 欄；findings artifact 不含 apply/final disposition；Arbiter artifact 才有 disposition。

### resolver precedence（七步，順序不可換）

1. workflow phase 建立 WorkUnitContract
2. qualification／judgment／capability hard filter——status=qualified 且（如記錄帶 minimum）effective effort 可確認且達標；conditional 不過 decision hard gate；capability 需求取交集；無記錄＝fail-closed 不通過
3. binding／carrier compatibility——token kind／effort encoding／transport 可否承載 contract 的 surface
4. availability tri-state——見下；stale／unknown 不得當 available（probe 或顯性 no-candidate）
5. ArcOverride constraint——user 當弧指示只約束合格候選的排序／優先，不能降低 contract；要降級須 user 明說接受該 work unit 的 degraded contract
6. RoutingPolicy soft ranking——合格且可用集合內的穩定偏好（本檔 dispatch 預設段）
7. 產出 DispatchPlan；高推理＋影像無單一合格 candidate 時＝declared decomposition（兩段式 visual fallback：visual-qualified observer 看原圖、decision-grade Arbiter 只消費 observation artifact，輸出帶 source identity、不確定項、`arbiter_viewed_source=false` 與 `decomposed-not-equivalent`，不得宣稱等價單模型原生視覺裁決）；皆無＝no-candidate report（列缺失條件，禁降 hard requirement）

> judge 裁決 Q2 doctrine：qualification 記錄 `minimum_effective_effort` 缺席＝記錄未要求 effort 軸（非 effort 已確認）；對 `effort_encoding=unsupported` 的 binding 新增 qualified 記錄時，effort 軸永久不可確認——事後無法以任何 requested effort 補認。

### AvailabilitySnapshot（tri-state，volatile——不進 catalog）

`state={available, unavailable, unknown}`＋source＋observed-at／freshness＋failure family＋retryable-at。輸入來源＝memory spine（`model-runtime-entitlements`）／runtime probe，每次 dispatch 形成。stale／unknown 永不當 available。DispatchTrace（work-unit-local）至少記：contract hash、candidate/binding、failure family、retryable-at、attempt disposition；1308 candidate 在 retryable-at 前不重選；retry 有界（429 依既定 backoff／並發政策、候選耗盡轉 no-candidate，禁 loop）。

### ArcOverride／RoutingPolicy／DispatchPlan／DispatchTrace

- **ArcOverride**：user 當弧 candidate constraint／排序指示（本次對話／work order）；selected override 需 echo；指向不合格或不可用 candidate＝零 dispatch＋顯性 failure report（禁靜默換人）。
- **RoutingPolicy**：合格且可用集合內的穩定排序與 failover policy（現值＝本檔 dispatch 預設段；不擁有 capability truth／availability 觀測）。
- **DispatchPlan**：selected candidate 四元組＋carrier adapter 路由（selected binding 等於 named preset default＝registry；harness 支援 spawn override＝同 WorkUnitContract／ExecutionPreset 只換 binding；否則 main-or-bridge 並完整裝載 Role／authority／surface 與禁止再委派）＋ExecutionPreset reference（S2 起 `agents/presets.toml`）。
- **DispatchTrace**：欄位清單見 AvailabilitySnapshot 段（work-unit-local attempt 史）。

<!-- AIR-91 S2：legacy tier × provider 權威表已移除（等價 gate 通過）——wire token／
     effort encoding／transport 供給事實改由 catalog.toml dispatch_binding 承載；
     registry pins 改由 agents/presets.toml default binding 承載；dispatch 政策
     （預設不派／禁派／顯式指定）保留在下方 dispatch 預設段與 external-runtime
     family 表。 -->

## 旗艦資格條款（五項）

> 定義「有資格被解析為旗艦（full）」的模型能力條款——資格線穩定（大綱層）；同 tier 內強弱排行不進條款（另見下行坐位註記）。候選模型須全部滿足：

1. **跨文件交叉推導力**：docstring↔斷言、EP↔code、caller↔callee 型不一致能抓；證據指針＝四家同尺比較中五項跨文件案唯終審層抓到。
2. **judge 否決力**：對高信心措辭 finding 有否決傾向而非順勢採納；證據指針＝同尺比較首輪全採納傾向反例。
3. **規劃的契約查證力**：把既有測試契約當設計約束、會推導決策前提失效；證據指針＝同尺比較 wrapper parity 約束與前提失效推導案。
4. **長弧查證紀律**：查證密度不隨 session 長度衰減；證據指針＝同尺比較後段淺驗反例。
5. **寫入邊界首改的邊界意識**：首次改動寫入契約／human truth 層時主動設唯一入口與 crash-only 防線；證據指針＝同尺比較唯一刪改入口案。

> **坐位註記**（換代只改此行；現值坐位＝ZCode 主軸 GLM 5.3，見下方 dispatch 預設段；registry pin 值查 catalog binding）：候選觀察：無；升坐位法：既有比較尺（四軸＋旗艦不可讓五項任務）跑一弧實測。

## dispatch 預設（user 裁定；訂閱現值查 spine `model-runtime-entitlements`——變更改 spine 條目，政策變更改本段）

**額度現值（V）不住本檔**——派工前「這家現在能不能派」查 memory spine `model-runtime-entitlements`（`~/.agents/memory-spine/`，as-of rolling state；查不到＝探測後派，禁從歷史 instruction 推定）。政策（路由/failover/顯式指定優先權）與機制（計費模型/分帳/窗口形態）仍在本檔；耗盡處置政策見 memory `quota-failover-policy`。

**harness 主軸（user 的開發入口決定主力 model——與下方 external-runtime「角色 → family → profile 映射」同源）：**

- **ZCode 開發（日常主力）**：主 session＝**GLM 5.3**（判斷/規劃/EP/judge；full-tier agent＝registry 釘 glm-5.3〔AIR-43——不隨主 session 漂移〕）；lite subagent 執行檔＝glm-5.3-flash（省成本層）；**內建 `general-purpose`／`Explore` 非 registry——無 pin、繼承主 session 旗艦**（官方設計行為，鏡像 `ref-docs/harness/zcode/cn/docs/qa.md`；例外：ZCode 設定頁可為內建型別單獨釘模型，清空恢復繼承）——lite 角色任務誤派內建型別＝旗艦燒機械段（真實案例：AIR-50 弧考察任務兩次誤派 general-purpose 被 user 抓——「registry lite agent＝flash」不可外推到內建型別）
- **muse code 開發（user 直用時＝該弧主力 harness）**：muse-spark-1.3 全棧——實作/審查都在該 harness 內（額度貴，非省成本預設——省成本層走 GLM flash）；repo 層 AGENTS.md muse 會載入（bridge log 實證；全域 guide 的 muse 部署點未查證）
- **審查類（ep-review／code-review 等 review agent 層）→ lite 預設（user 裁定；ZCode/GLM 主軸＝glm-5.3-flash、CC 端＝sonnet 詞彙——wire 值查 catalog.toml binding）**：findings 生產層跨家族/跨層品質已實證，判斷價值集中 judge 裁決層；跨家族第二意見仍 muse 優先（非 GLM 視角）；升 full 條件＝高保護面／跨邊界語義面（保護面厚度反轉為升級觸發）；**judge 裁決層不變：固定主 session 旗艦（ZCode 主軸＝GLM 5.3，AIR-24 三防線）（seat 非 full 時依 rules/model-routing.md 升級外派，禁 in-session 降級自判）**；dual-family 鏈 judge 全採納（零否決）時顯性自查三防線#2（sycophancy 下傳——AIR-46 實證零否決×2 未觸發）；外部 runtime 委派承載者＝主 session 背景 Bash（禁 subagent wrapper——見 reviewer 交接契約「承載者」）；registry 釘選＝base 非強制——顯式升級＝換 full-tier 載體（高保護面／跨邊界語義面；GLM 無 spawn-time model 參數，升級走 carrier adapter 換 binding／載體）；跨家族第二意見換 muse
- **實作（implement profile bridge 委派）＝預設 muse**（user 修訂拍板）：重實作段 muse、lite 機械段 glm-5.3-flash；**CR 工具鏈 registry agent cr-research 已裁升 full（v3.1——AIR-76 定案，脫離 muse＋glm-5.3-flash 收斂）**；全域研究 fallback＝內建 Explore（繼承主模型，釘 lite 可選非必要）——與「user 直在 muse code 開發」仍是兩種形態（委派 vs harness 切換）
- **影像需求＝需「支援影像的 model」（native_vision ∩ binding image_transport），現值＝glm-5.3-flash**（user 拍板「影像目前都用 flash」——選它因 5.3 flash 原生多模，非因成本檔；非所有一般款都具影像能力）；CC 端影像需求暫不派（無影像 binding 釘選，inherit 鏈無多模保證）——muse `--image` 是能力備註（external-runtime family 表），非現值路由
- **codex（OpenAI）→ 預設不派**（額度面 as-of 查 spine——不派屬 ad-hoc 政策非額度因素）——僅 user 顯式指定（例：「codex sol max」；顯式指定多一種形態：`chatgpt-web/*` 走 web 訊息額度 pool，例「codex web high」→ `chatgpt-web/high` 旗艦）。**webgpt 形態專責 review／規劃、禁大型實作**（三條使用約束與失敗態處置見 External-runtime 段 webgpt 專節）。定性甜蜜點實證：control-plane／docs 形態 repo 的全 repo 狀態對抗深審（[/state-review](../state-review/SKILL.md) 的候選家族之一）——產出與 in-family 盲點正交（權威模型／事務完整性／provenance 類問題）；本行是能力備註，不構成取消顯式指定授權；顧問形態（user 說「跟 codex 討論」）見「顧問觸發兩層語義」節（點名即顯式指定已滿足）
- **CC（Anthropic 詞彙面）→ sonnet／haiku／opus 可派**（user 拍板；**預設 sonnet、haiku 基本不用**——user 裁定）；背後接線＝machine-local（user 維護，訂閱變更自換），規範層不記載；未訂閱家禁派（現值 as-of 查 spine `model-runtime-entitlements`）

**額度 failover（僅撞牆時）**：GLM 撞 1308（錯誤訊息含重置時間戳）→ muse 承接執行段；muse 亦乾 → 等 reset（`/at`）或 user 裁定硬跑；任何降級必顯式記錄（AIR-13）

**arc 內改判（user 最新一句為準）**：同弧內 user 改派（例「subagent 改用 5.3 flash」）→ 後段路由以最新指派為準，前一指示不鎖死；改判只影響該弧，不改本檔預設

<!-- AIR-91 S2：legacy pins 填法表與 role→requirement 分配表已移除（等價 gate
     通過）——registry 部署預設（zcode pins／claude 別名釘選／requirement 相容
     token）單一源＝agents/presets.toml（default binding FK→catalog，
     sync_agents.py 生成與 --map 對帳；改 pin＝改 presets＋catalog 後重跑
     sync）。cr-research 於 v3.1 裁升 full（AIR-76 定案，原 lite）——決策記錄
     保留；新 role 須在 presets.toml 登記 preset，缺登記＝sync fail loud
     （防靜默 unpinned 上線）。 -->

> ZCode 注意：`thoughtLevel` 綁具體 model（inherit 時不生效）；欄位名**不是** `reasoningEffort`——未知欄位靜默忽略。**thoughtLevel 但書**：sticky user reasoningLevel 在場時（user-scope `local_setting`），定義的 thoughtLevel **不達 wire**——telemetry `variant` 記 user 層級而非定義值（兩數據點：lite-verify＋vision-review 定義 `high` 皆記 `max`，sticky `max` 在場、主 session rows 同 max）。**model pin 不受影響**（frontmatter model 字串逐字到 wire——vision-review 首筆遙測實證）。full 釘選後（AIR-43）定義 thoughtLevel 進入本但書管轄（sticky 在場記 user 值）——model 軸同樣不受影響。**flip 實驗已跑（AIR-44）**：直寫 `local_setting` DB 改 user level→`low` 後同 session spawn 釘選 agent（定義 `high`）——variant 仍＝`max`（舊快取值，非新 user 值亦非定義值）：①定義值 silent no-op 確認；②spawn 不逐次重讀 local_setting（app 層快取 session 起始值）；「UI 層動態改是否傳播」DB 實驗無法回答（UI 可能同寫記憶體＋DB），user UI 級實驗殘餘——對應**已知 open bug 家族**（zai-org/feedback #339「thought-level changes silently discarded after first selection」＋#306 reasoning effort injection 缺陷；EN/cn 文檔一致、用法無誤）。CC 注意：enum 別名（sonnet/haiku/opus）＝CC 詞彙面 token；背後解析 machine-local，不進 doctrine。

## effort 家族對譯表（跨 runtime 詞彙對照）

> 同一思考投入檔位在四家 runtime 的詞彙對照（AIR-28 補；execution contract tier 欄與跨家族工單 effort 欄對話時用）。**單一源在本表**——registry pins／工單模板／contract 表引用不自带數值；muse/codex 現值權威見下方 external-runtime family 表。對譯是語義對應非等價保證——實現機制不同（ZCode `thoughtLevel` 綁具體 model＋sticky 不達 wire 家族〔見上方但書〕、CC spawn-time enum、muse/codex runtime 參數）。

| 檔位語義 | ZCode thoughtLevel | CC effort（spawn-time） | muse effort | codex `--effort` | repo 慣用位 |
|---------|--------------------|------------------------|-------------|------------------|------------|
| 純機械（渲染／掃描） | low | low | `low` | `minimal`～`low` | advisory 掃描降檔（省 quota） |
| 執行層（lite tier 預設） | `high`（registry pins 標配） | `high` | `medium` | `medium` | lite tier pins |
| 審查／判斷（review 委派） | `high` | `high` | `high` | `high` | review 工單 |
| 深推理（判斷密集／深挖） | `max`（user 層級；定義檔設值 sticky 不達 wire——見上方但書） | `high` | `xhigh`～`ultra` | `xhigh` | muse 委派預設（user 定）；深推理升 `ultra` |

> 可考值域：codex 接受 `none`/`minimal`/`low`/`medium`/`high`/`xhigh`（**codex plugin** 的 codex-cli-runtime skill——plugin cache 面，非本 repo 檔；repo 內鏡像 `ref-docs/harness/codex/config-file/config-sample.md` 的 config-level enum 無 `none`——companion flag 值域與 config 值域是兩個面）；`chatgpt-web/*` 例外＝slug 自帶固定 effort（light/medium/high＝display Instant/Medium/High），effort 旗標不換 browser model（值域對 web slug 無效）；muse 用 `low`/`medium`/`high`/`xhigh`/`ultra`（`ultra`＝CLI alias → provider 最高級＝API `max`）；ZCode 欄位名是 `thoughtLevel`（非 `reasoningEffort`——未知欄位靜默忽略）、user reasoningLevel 層級含 `max`；CC effort enum 以 CC runtime 為準（repo 慣用 `high`）。跨家族委派時 effort 值以**各家族解析表**為準（muse/codex 見 external-runtime family 表、in-harness 見 tier 解析表），本表只對詞彙。

## lite 分工律（執行層降級條件）

> GLM-5.3-Flash 全切換的三軸鑑識（對話行為／git 產出／建議查證）定版；rule 端只錄 tier 語義與升降級條件，證據與細節在此。

**執行層可降 lite，條件＝保護面厚度**（三件全滿）：既有測試釘住（可重跑驗證）＋驗證閉環（機械閘門在場）＋非跨邊界語義面（單位換算／領域語義轉換不屬此段）。

- 實證（GLM-5.3-Flash 可靠面）：lite-verify 10/10、cron 四段全交卷、reviewer 20/20 交卷（dual-context 兩側獨立交叉命中）且 10 findings 經 full 複驗全成立、findings 修正 10 分鐘落地、測試警告清理走顯式契約（僅 1 條窄域 filter）
- 已知風險面（降級時主動防）：跨單位語義換算錯＋靜默失效＋斷點汙染（西元↔民國 P0×2/P1）；測試合法化 bug（mock 假設即 bug——lite 模型測試僅規格陳述，驗收證據另補 full 複驗）；inferred findings（報「機制可能」非「實測確認」——judge 遇 inferred 必重跑實測，見 judge-review 三防線）；機械掃描漏變體（rg pattern 需含空格/等號形）；Edit 前未 Read 偏高（20 vs 3——spawn prompt 注入 Read 紀律）
- **判斷密集位不可降**：judge 裁決／EP 規劃／post-build 編排＝full 能力檔——judge 自證塌陷＋sycophancy（錯信心 finding＋順勢採納＝最危險組合）是能力剖面問題。**lite＋max effort 補償＝未驗證路徑**：欲採用先小規模實證（舊 findings 重裁對照 full 裁決），結果記回本節
- **歸因紀律**：模型歸因結論必須 per-message modelID 機械對帳（ZCode db.sqlite；unpinned subagent 跟 spawning session 模型走、registry pin 不受手動切換影響），不接受 session 自述——三例自述歸因錯（full 亦被 priming 帶偏）
- **管轄對照（兩套降級條件邊界）**：本段三件（既有測試釘住＋驗證閉環＋非跨邊界語義面）＝**spawn 執行層降級**判定；handoff「建議執行 tier」三條件（保護面厚＋EP 條款機械可判＋審查鏈全開）＝**handoff 路由建議**判定——兩套條件管轄面各異，詞形差異非 drift

## External-runtime（family 軸）解析表

> 維護原則：model／effort／容量現值演進只改此段（rule／registry／模板不寫數字與型號——分層：骨架在 `rules/model-routing.md`、現值與映射在本檔）。family／profile 詞彙定義見本檔 glossary，本段只給權威值。

### 角色 → family → profile 映射（family 表）

| 角色 | family | profile | 備註 |
|------|--------|---------|------|
| 實作（implementation） | muse | implement | 主力 implementation loop 承接 |
| external second-opinion review | muse | review | 獨立第二意見，與 in-harness 驗收審查職責分離（見下） |
| in-harness acceptance reviewer | GLM | — | 驗收委派工單的主審（Writer/Reviewer 分離的 in-harness 側） |
| 診斷 rescue | codex | implement | ad-hoc 選項（想到再用、低頻）；context 小＋消耗快禁大工單 |
| advisory 掃描 | muse | advisory | 唯讀掃描、盤點 |
| 機械驗證／探索 | GLM | lite | 機械查證、探索（沿用 tier→lite 路由） |
| 視覺驗收 | GLM | vision | 預設路由；muse 具視覺能力為跨家族備選 |
| 架構級 EP（blueprint） | muse | implement | 使用者會話在場裁決為 eligibility 前提（gate 第六條）；無 user 在場不放行 |

> 兩種 review 邊界：external second-opinion review（跨家族獨立視角）與 in-harness acceptance reviewer（GLM 主審、把關工單結案）職責分離，前者補視角、後者定結論。容量不足的家族禁派大工單——現值見下表，rule 不寫數字與型號。重大架構／風控／會計 diff 的跨家族 review＝**軟提醒非硬閘**（額度現實：muse/codex 額度吃緊時派不動）——額度允許時至少一側跨家族；不足時顯式記錄降級（in-harness full 雙 context 承接），禁靜默略過。

### family → (model, effort, 容量現值)

| family | model | effort | 容量現值 | 備註 |
|--------|-------|--------|----------|------|
| muse | `muse-spark-1.3` | `xhigh`（user 定；純機械掃描 advisory 可降 `low`/`medium` 省 quota）；深推理可升 `ultra`（CLI alias → provider 最高級＝API `max`，限 1.3 Standard tier；reasoning tokens 佔 output 比例更大，留意輸出上限截斷） | 長 context（以 provider dashboard 為準） | 具視覺輸入 `--image`，跨家族備選；advisory／implement／review 共用此 family；bridge 端預設 pin 與本表對齊（delegate-bridge 弧維護），`--model`／`--effort` passthrough 僅供臨時 override |
| codex | `gpt-6-astra`（最強檔；Plus 帳號不可用——帳號面 as-of 查 spine）／`gpt-5.6-sol`（原生旗艦）／`gpt-5.6-terra`（日常）／`gpt-5.6-luna`（基本不用）；**5.6 以下不派**（spark 舊代已汰）／**`chatgpt-web/high`（旗艦，user 拍板）**、`chatgpt-web/medium`（web 形態） | 原生 `high`；**web slug 自帶固定 effort**——slug 即檔位，`--effort` 不換 browser model | 原生 ~258K 級、web 256K（以 provider 為準；user 實值 as-of 查 spine `model-runtime-entitlements`）——原生 pool 額度最少故預設不派（見 dispatch 預設段，web 形態同政策）；大 context 任務仍優先 muse；web 池單則訊息上限遠小於窗口——大 payload 單發 turn-0 即死，webgpt 專責 review／規劃（見下方 webgpt 專節） | ad-hoc 選項（僅 user 顯式指定）；**bridge ≥1.0.0 承載（`task --family codex`，AIR-47 吸收）**——`--model`／`--effort` bridge flag 直達；**帳號路徑分界機制（2026-09-12 實證；現行帳號面 as-of 查 spine `model-runtime-entitlements`）**：ChatGPT 帳號登入下 native slug 全不可派（server 拒：`The 'spark' model is not supported when using Codex with a ChatGPT account`）——僅 `chatgpt-web/*` 可用，切回 credits 載具才恢復 native 面；raw 形態＝`-m <id>`＋`-c model_reasoning_effort=<v>`（raw `codex exec` 不收 `--effort`——unexpected argument 實證；codex 無 `ultra`）。**web 形態（webgpt bridge）**：`chatgpt-web/*` 底層 gpt-5.6-sol、吃 ChatGPT web 訊息額度（零 API 費、與原生 slug 的訂閱 Codex 額度分帳）；原生 slug 經 bridge passthrough 額度照舊；**bridge（`127.0.0.1:17841`）＝全 model 單點——launcher 死＝全 fail-closed**。**不帶旗標分兩形態：raw CLI＝落 config 預設（值隨本機 config 漂移，查驗以當下 config 為準）——要 family 表值必須顯式帶旗標，禁信 config 預設；bridge＝不適用——bridge 一律顯式 `-m`，無 `--model` 時自填 adapter 預設 `chatgpt-web/high`（user 定案，delegate-bridge v1.0.2+），config 預設在 bridge 路徑不存在，要換池必須顯式 `--model`**。raw CLI 事實集（事件流／resume／fork／sandbox／spawn stdin 陷阱）見 memory `reference_codex-cli-exec-facts`——官方 companion 已退役（AIR-47），委派一律經 bridge；webgpt 額度池分帳、usage 查詢盲點與五類失敗態處置見下方 webgpt 專節 |
| glm（bridge） | **native ID only**（case-insensitive canonicalize）：`GLM-5.3`（旗艦，顯式）／`GLM-5.3-Flash`（**bridge 預設——裸委派落 flash**）；舊 alias `sonnet`/`opus` **fail-closed**（terminal failure、exit 1、永不 completed） | —（不收 `--effort`） | 同 GLM（in-harness）行（高） | `task --family glm`；**呼叫端擁檔位→native 映射**（口語檔位↔native ID——flash→`GLM-5.3-Flash`、旗艦→`GLM-5.3`；映射值查 catalog.toml binding，派發前正規化，bridge 不再代解 habit 詞）；寫入委派＝`--write-mode edit`（詳見下方 glm 專節）；實現細節（alias 歷史、VR-1 裁決）＝delegate-bridge repo docs |
| GLM（in-harness） | 見 dispatch 預設段＋catalog binding | 見 named preset（presets.toml） | 高（遠高於 200K 級，見 provider dashboard） | 沿用 named preset 路由（lite／vision default binding），不經 external-runtime 派發；in-harness acceptance reviewer 屬此 |

> 容量為「需現況查證」性質，隨 model 世代更新只改本表。

### webgpt（chatgpt-web 池）使用約束與失敗態

> 三條 user 裁定；約束對象＝web 形態（`chatgpt-web/*`），原生 slug 派發政策不變（見 dispatch 預設段）。

1. **審查／規劃專責，禁大型實作**：窗口雖大（現值見上表），**單則訊息上限遠小於窗口**——review 大 diff 單發必死（真實案例：delegate-bridge ledger 4 筆 `ran out of room in the model's context window`，全數 turn-0 死亡）。派發前提（裁定原文「僅段落級評估確認可完成**才派**」）：範圍段落級＋派發前評估確認單則 payload 可完成，不滿足不派——是前提不是例外條款，不從「限 review／規劃」開出實作授權。
2. **額度池意識（usage 查詢盲點）**：原生 `gpt-5.6-sol` 走 Codex credits 池（＝上表「原生 pool」／訂閱 Codex 額度；會耗盡、有 reset 日）——ChatGPT 帳號路徑下 native slug 全不可派（帳號路徑分界機制見 family 表；現行帳號面 as-of 查 spine `model-runtime-entitlements`）；`chatgpt-web/*` 走 ChatGPT web 訊息額度（web 池）、不吃 credits；**`wham/usage` 只回報原生訂閱池、看不見 web 池**——額度判斷禁依賴 usage 查詢（對 web 池等於沒查）。
3. **失敗態辨識（五類固定失敗態）**：處置分流如下，禁盲目重試。

| 錯誤簽名 | 機制 | 處置 |
|---------|------|------|
| `ran out of room in the model's context window` | 單則訊息超 web 池上限（同約束 1） | 切 chunk／降 payload 再派；**禁同 payload 重試**（必再撞） |
| `stopped responding after the task started` | launcher 側 ChatGPT 分頁失聯，非任務本身失敗 | 先查 launcher 分頁健康再判；盲目重派＝雙跑風險 |
| `connector menu ... no row named "Codex Native2"` | connector 環境缺損 | 環境修復（建 connector）後再派；重派無效 |
| `personalization preflight exceeded its readiness deadline` | ChatGPT UI／登入狀態未就緒 | 查 UI／登入狀態，修因後重派 |
| `You've hit your usage limit ... try again at <time>` | web 池訊息額度耗盡（同約束 2） | 解析 `<time>` 排程重派（`/at`）；禁立即重試 |

> 本表＝webgpt runtime 側任務失敗；bridge 進程面卡死（wait 空轉等）分流見「完成回報收法」節 transport 三態判定。bridge 機械分類另有第六類非池失敗（trusted-env——turn context 組裝缺 cwd），非 user 裁定五類範圍，處置見 delegate-bridge 側 webgpt 工單文檔。

### glm（bridge）委派契約

> `task --family glm` 的呼叫面契約（實現細節＝delegate-bridge repo docs）。

1. **model 詞彙＝native-ID-only（VR-1）**：`--model` 只收 provider-table native GLM ID（不分大小寫 canonicalize）；**裸委派＝預設 `GLM-5.3-Flash`**（省額度腿可不帶）；旗艦腿必顯式 `--model GLM-5.3`。**呼叫端擁 tier→native 映射**——派發前把口語檔位（flash／旗艦）正規化成 native ID，bridge 不代解 habit 詞；禁用 CC 詞彙 `sonnet`/`opus`（**fail-closed：prepare-throw→terminal failure entry、exit 1、永不 completed**——terminal 不可當 completed 誤判成功）。
2. **寫入與唯讀檔位（write-mode）**：寫入委派＝`--write-mode edit`（headless 唯一寫檔檔位）；缺席≡`plan`（read-only）；`build`＝**唯讀收緊檔——headless 不可寫**（勿教 `build` 當寫檔腿）；`yolo` fail-closed。
3. **flag 面**：收 `--model`／`--write-mode`／`--background`／`--caller-session`／`--json`／`--resume`／`--disallowed-tools`（透傳）＋positional prompt（`--prompt` 恆結尾）；拒收 `--trust-workspace`／`--steps`／`--yolo`／`--effort`／`--allow-workspace-switch`／`--network`——muse 形的 flag 組合（如 `--trust-workspace --steps 800`）照抄即炸，委派範例須標 family 差異。
4. **resume/fork semantics unverified**：`--resume` 收單在場但 session identity 連續性未證——do not infer continuation support from muse/codex。
5. **ledger 語義**：`model`＝caller 原始拼法、`effectiveModel`＝canonical native（parsed-success attestation）、`mode`＝handed——analytics 鍵 `(family, model, effectiveModel)`、身份認 `effectiveModel`；兩欄不合并。

### 顧問觸發兩層語義（「跟 codex(,5.3) 討論」）

- **user 說了（指令層）**：「跟 codex(,5.3) 討論」「問顧問團」等原話＝判斷密集位的**指令動作**——**禁自收斂跳過**；顧問僅意見權（最終裁決歸 user／primary session）；**兩段式回報**（先外部收斂、再跟 user 討論；原話已授權「討論後做」者除外）；codex 授權＝點名即顯式指定已滿足（舊「逐弧原話」二次確認已退役，user 裁定）——經 bridge 照常派發，payload／eligibility／失敗態 gate 照走；bridge 不可用時出 paste-ready 工單由 user 轉貼為備用
- **user 沒說（自判層）**：AI 按需調用——難題（架構取捨／多方案裁決／疑似 bias）才叫顧問；**勿套會議儀式**（開場群聊／三家融合需 user 明示）
- 安全邊：大 payload 派發前段落級評估（webgpt 約束）；失敗態按表處置，禁盲重派

### eligibility gate（六條，逐條判）

> 任一不過 → 主 session 直做；「≥30 分鐘」僅提醒信號非機械判準。

1. **決策凍結**：工單目標、範圍與驗收已凍結，無待決設計選擇
2. **條款客觀化**：驗收條款為機械可判（命令＋預期結果），非主觀描述
3. **單一 writer 無待決**：單一 writer 可獨立完成，無需主 session 中途決策或協調多 writer
4. **主價值＝承接 implementation loop**：主價值在承接完整實作迴圈，而非零碎問答或探測
5. **環境可啟動**：目標 runtime 環境可啟動（bridge setup 綠、binary 在場），非環境阻塞
6. **使用者會話在場裁決**：架構級 EP（blueprint）委派須有使用者會話在場裁決——無在場證據面為零，不放行

> **review／advisory 形態條款**（read-only 委派——external second-opinion review、[state-review](../state-review/SKILL.md) 深審腿、advisory 掃描）：以 ①②⑤＋三條專屬判定——**read-only transport**（flag 或工單紅線承載，產出＝findings/報告）、**跨家族成立**（委派對象與 caller 相異家族——external 視角是派發理由本身）、**可重現輸出**（findings 附錨點＋驗收設計，in-family judge 可機械重現）。條件③④（單一 writer／implementation loop 主價值）是 **implement 形態專屬**，不得用以擋 review 形態——否則跨家族審查腿結構性不可達（真實案例：state-review 深審腿依原條文④被擋）。
>
> **跨家族解析表**（未指定 family 時；顯式指定與 caller 同 family → fail-loud）：GLM／ZCode caller → muse；codex caller → muse；glm caller → muse；**muse caller → fail-loud**——相異家族僅剩 codex／glm 可選，而兩者皆 explicit-only 不因解析繞過：**停下要求 user 選擇**——顯式 `--family codex` 或 `--family glm`，或明示接受同家族 degraded review（caller-harness decision-grade dual-context 承接＋記錄）；禁解析層自選降級。

> sandbox-error 禁以 `--yolo` 賭重試（父層沙箱不可越權重試）；分類走 auth-failed／environment，修因後重派。

### reviewer 交接契約

- **完成回報固定欄位**：jobId 或 thread id／base commit／改檔清單／實跑驗收命令與原始輸出／未驗證項
- **reviewer 讀料順序**：work order → diff → evidence → writer report 最後讀
- **產出**：accept／reject／needs-fix 三態 verdict；無 reviewer record 不得結卡（record 落 EP 或工單指定位置）
- **承載者（硬性）**：外部 runtime 委派＝caller 背景 Bash process 直呼 bridge（run_in_background＋stdout 重導），**禁 subagent wrapper 承載**——外部 runtime 不佔 in-harness agent slot／rate limit（wrapper 唯一「價值」是被誤判的 600s timeout 約束——從未存在，見「完成回報收法」）

### flag profile → spawn 參數（external-runtime）

> 本表為 flag 具體值單一源（registry 側只留 thin forwarder 治理原則，見 `agents/AGENTS.md`）。bridge 未暴露的 flag 以工單紅線承載（見 `skills/_common/work-order.md`），暴露後改 flag；roadmap 記錄在 delegate-bridge 側。表列 `muse task`／`codex task` 為語義縮寫——實體命令＝`delegate-bridge.mjs task [--family muse|codex|glm]`（Muse 家族 CLI 相容不變）。

| profile | family | spawn 參數 | 說明 |
|---------|--------|------------|------|
| advisory | muse | `muse task`＋read-only 紅線承載（`--disable-write` flag 未暴露——bridge 實測至 v1.0.0 未暴露；暴露列 delegate-bridge roadmap） | read-only 掃描（SM-2）；effort 取上表 muse 列 |
| implement | muse | `muse task --trust-workspace --yolo`（**implement 一律帶 `--yolo`**——user 拍板） | 實作 agent 需完整工具面。實證：muse sandbox 與測試環境假設衝突（repo-observed delegate-bridge 229-test：sandbox 13 fail＋孤兒子行程握 stdio 永不退出〔tool call 無 timeout〕；`--yolo` 全綠 43.6s≈乾淨環境基線 38s）。**反向約束：read-only 委派（advisory/review/研究）維持預設 sandbox——其他 profile 的 yolo 適用性待續討論（user 保留）**。writer 紀律：writer 內部 test／process 前景執行＋per-test bounded timeout（transport／caller 可背景；muse tool guard 連 `--yolo` 下都禁 unmanaged 背景行程）；**全量 gate＝orchestrator clean-env 重跑**——writer 環境全量不作 gate（環境差異——自述不可信之外第二理由）。wedge 診斷/救援＝delegate-bridge memory `muse-build-round-ops`。背景跑（見 rules/tool-discipline） |
| implement／advisory（定向接續形態） | muse | `muse task --session-id <uuid>` ＋ base profile flags（composition rule：接續 flag 只 augment 不取代——implement 續接如 `muse task --trust-workspace --yolo --session-id <uuid>`；advisory 續接維持 sandbox base；bridge ≥0.2.6 起暴露；跨 workspace 加 `--allow-workspace-switch`；codex 家族同形＝`task --family codex --session-id`） | resume 指定 session 續問——語義矩陣與守衛處置見下「session 定向接續」節 |
| implement | codex | `codex task`（bridge `--family codex`；預設 sandbox＝auto-approved workspace-write，read-only 走 `--network restricted`／`proxy-only` 映射 `-s read-only`） | 診斷／救援寫入型——`--write` 是已退役 companion 旗標，bridge 不收 |
| review | muse | `muse review --json`（bridge `review` 子命令——**git-diff 審查工具**：`--base <ref>` 定 diff 範圍；非文件審查形態——EP 等文件審查走 `task`＋read-only 紅線，`--schema` flag 不存在〔bridge 0.2.5 實測〕） | diff 審查產出 verdict |
| review | codex | `codex review --json`（bridge `--family codex`——`--output-schema` 注入＝verdict schema 原生機制，POC 實證） | 同上，codex 形態 |

**bridge 必經（external-runtime 家族委派唯一入口——muse／codex／glm 三家）**：委派外部 runtime 跑 repo 任務一律經 bridge 入口（上表列＝`delegate-bridge.mjs` 子命令的抽象形態，`--family` 選家族），禁直呼 `muse exec`／`codex exec` 或其他繞過 bridge 的入口。**caller surface → 合法 bridge 路徑對照（registry pin 唯一源、禁手拼版本化 cache 路徑）＝[rules/bridge-dispatch.md](../../rules/bridge-dispatch.md)**。**派發前正規化**：user 對話中的模型／檔位口語詞（flash／max…）不是值——派發前經 family 表正規化為 `--model`／`--effort` 顯式旗標；非表內詞＝查表觸發訊號，禁猜測直接套用（flash 對 muse 非合法 effort 值，本身就是該查表的訊號）——bridge 落 per-repo `.delegate-bridge/jobs.json` ledger（jobId／sessionId／status／text／family 欄；v1.0.0 前舊 ledger dir 相容雙讀、id 去重——新者勝），非 bridge 入口的產出 ledger 查無，事後只能從副作用側考古（真實案例：mosaic post-build 鏈同鏈兩段 muse 委派一走 bridge 一繞道，繞道段收尾不可考）。完成回報攜帶 ledger jobId（reviewer 交接契約欄位）；委派了外部 runtime 而 jobId 缺席＝入口違規，補查或標明。

### session 定向接續（`--session-id` resume／fork；L4 實測）

> 判準落點分工：本節管 routing 機械面（語義矩陣／守衛處置／通道現值）；「continuation vs handoff doc」形態選擇見 [handoff](../handoff/SKILL.md)「與 /at 的邊界」。

**語義矩陣**：

| harness | 命令 | live session | 結束後 | fork |
|---|---|---|---|---|
| muse | `muse exec --session-id <uuid> -- "<p>"`（經 bridge＝`task --session-id`） | exit 1 `already in use`（fail-loud，模型不跑） | 續寫語義兩個觀察並記（差異因子未隔離——workspace 形態×載體）：同 workspace raw exec 宣稱 ephemeral 不寫回；**跨 workspace bridge＋`--allow-workspace-switch` 實證 durable 續寫**（原 transcript append `session.resumed`→回應→`session.end` 段，回應內容持久化）——**路由一律視為 mutating** | 無 |
| codex | `codex exec resume <uuid> "<p>"` | exit 1 thread-store conflict | 真續寫（append 同 rollout） | `codex exec fork <uuid> "<p>"`——live 也可；新 uuid 複製完整歷史、原卷不動 |
| claude | `claude -p --resume <uuid> "<p>"` | 未驗（help 暗示同款守衛） | 真續寫（mtime 實證） | `--fork-session` 在場、未驗 |

**路由預設**：定向接續一律視為 **mutating continuation**——原卷不動的查詢走 codex `fork`，或不 spawn 的讀卷面（transcript jq／bridge `export`）。接續＝載入舊 context＋新 prompt 一起走（resume/fork 命令形態直接帶新任務）。

**守衛處置（兩道，皆 fail-loud 帶自解說）**：
- **writer 守衛**（live session 已有寫者）：muse `already in use`／codex thread-store conflict → 請 user 關對方 app/thread 釋放後重派，禁繞道
- **workspace 守衛**（muse 跨 workspace resume）：session 建立於 workspace A、在 B resume 預設拒絕——經 bridge 加 `--allow-workspace-switch`（workspace 綁定移到 caller cwd）；raw `muse --workspace <path>`（釘原 workspace）bridge 未暴露

**bridge 必經管轄**：定向接續經 bridge 產生新 ledger entry（caller-cwd `.delegate-bridge/jobs.json` 記**原 sessionId**，新 entry prepend）——跨 repo 絕對定址已實證（caller ledger 從未見過該 session，照樣定址成功）；flag 暴露前禁繞道直呼 `muse exec`。

**成本警示**：continuation 帶整包 context（codex resume 實測 127K tokens／fork 65K）——任務可口述就走 handoff doc，別為省一張工單續整卷。

**審查工作流鏈形態**（MOS-74 實證）：review 工單預告驗證式 → judge → 修正 → `--session-id` 同 session followup——reviewer 帶自己 findings context 複驗，優於 fresh context（followup 工單零背景重複＋驗證式直接回收複用；reviewer 對自己 findings 的修正驗證比 fresh context 準）。

### 完成回報收法

> **經濟學動機**：LLM 層輪詢每輪＝1+ request 且全 context 重送；push 收法等待期間 0 request、完成時恰好 1 request。輪詢只存在 bridge 進程內部（muse `wait` 內建亞秒級固定輪詢——零 LLM 成本）。

**決策樹**（未載入背景的 session 單讀可執行）：

1. **簡單直跑（review／critique／diagnosis）**：主 session 背景 Bash 直呼 bridge 阻塞形（`task`，家族經 `--family`）→ process exit 自動喚醒 → stdout 即 finalText；jobId 記錄不變（reviewer 交接契約欄位照舊）。派發時必印 `[Bridge] family=<f> model=<m> effort=<e>`（與 in-harness `[Agent] model=…` spawn 確認對稱——派發前肉眼攔截；muse effort 口語誤讀事故即此欄位缺席所致）
2. **長跑（>10min，xhigh 委派）＝fire-and-forget 優先**：`task --background "<prompt>"`（長 prompt 改 `--prompt-file <path>` 形態）提交 → jobId 即回 → caller 結束 turn 釋放（不掛前景、不綁 session）。**收法分流（session 是否需接續）**：session 活著且完成後要接續做事 → **背景 Bash 掛 `wait <jobId>`（首選 wait 收法）**——零 model request，wait exit 觸發 harness notification **自動喚醒 session 接續**；session 將結束或不在乎即時收 → 純認領制（事後任何時刻 `show <jobId>`——**完成無推送、不會自己回來**，須主動查）。finalText 由 per-job jsonl 重導出，ledger entry 只存 status／exitCode／summary。**timeout 語義（AIR-47 S3 起對外單一形，所有 bridge task family 共用——wait 是 bridge ledger job lifecycle 面，非 family carrier 面）**：
   - bridge `wait <jobId>`：timeout 到期＝`process.exit(124)`——exit 124＋status 仍 running＝重掛；`--timeout 0`＝forever（長跑必帶）
   - 任一家回非 completed 終態 → `jobs/<id>.jsonl`＋working tree 對照再判（reconcileStaleRunning 可能過早標 interrupted）
   - **兩端 SessionEnd 差異（caller 在哪家 harness，決定能否跨 session 認領）**：ZCode 端 plugin hooks 不執行 → background worker（detached，脫離 caller 進程樹）跨 session 存活 → 任何 session 以 `runs`／`show` 認領（fire-and-forget 完整可用）；CC 端 SessionEnd hook 殺 running job 進程樹＋標 interrupted → holder session 必須活著 → fire-and-forget 限縮為「session 內釋放 turn」，跨 session 認領前先確認 holder 在場（事實源：`…/delegate-market/delegate/<ver>/scripts/session-lifecycle-hook.mjs`＋`hooks/hooks.json`，以 plugin cache 現版為準）
   - **liveness ticker（長跑 implement 委派的卡住偵測——user 要求）**：`wait` 只盯「完成」；wedge（如 sandbox 孤兒行程握 stdio）下 wait 永掛。派長跑 implement 工單時**平行掛第二個背景 Bash ticker**：每 5 分鐘檢查 liveness 訊號（目標目錄 `fd . <dirs> --changed-within 5m`＋`tool-outputs/` 下最新檔 mtime〔`.spool/` 只收 staging 期——commit 後輸出長在 `tool-outputs/<task>/` 下持續增長，禁只看 `.spool/` 目錄 mtime〕）——**停滯 >20 分鐘 exit 1 → 背景 Bash 完成自動喚醒 caller 處置**（show 診斷→`stop <jobId>`／kill pipeline children，救援法＝delegate-bridge memory `muse-build-round-ops`）。門檻誠實註記：低 CPU（0.5–1%）是正常（model-bound）——訊號必須是「檔案寫入停滯＋spool 凍結」組合，禁單看 CPU；大輪思考停頓可達數分鐘故取保守門檻。advisory 先報不殺。bridge 端 heartbeat 已交付——背景 worker 每 ~2s 寫 `extra.heartbeatAt`＋`lastEventAt` 雙軸（前景不寫）；consumer＝`wait --stuck-after <ms>`（strict parser、stderr 軸別 alert＋dedup）＋`runs` 600s `running (stuck?)` 提示；AIR-71 fleet 架構位（execution identity 觀測 runtime 腿）不變。上方 ticker 建議保留——它看工作產物停滯，與 heartbeat 軸互補。
3. **prompt 工程（codex gpt-5-4-prompting 改寫）**：官方 companion 已退役（AIR-47）——wrapper 形態不再是 ai-guide 路由引用面（plugin 快取仍在場可手動用）；歷史實證保留供參（**已退役形態，僅供考古**——現行一律直跑）：wrapper Bash 10min 上限是約束事實、wrapper 在 runtime 未終局時提前 complete 是系統性常態（muse×2＋codex×2 均需介入實證）——預期超時的工單改走 2
4. **LLM 層 fallback（罕見——原始派發無背景 Bash 掛載；前景短 arm 仍可用）**：ETA-gate 紀律——推估完成時刻前零檢查（一段 `--timeout <eta>` arm）→ 屆時單次檢查 → 未終局重掛遞減 timeout 的阻塞 wait arm（起點＝bridge 預設 5min／4min，按 ETA 緊化至 ~30s 級；每 arm 到期＝1 request）——**永不做 LLM 層定時輪詢**

> **多工複用（fire-and-forget 的複用形態）**：一個 session 持 N 個 jobId 統一掃（`runs --json` sweep 後逐個 `show`／`wait` 認領）；並行 quota 語義＝同 5h window token 加總（並行買 wall-time 不省花費），實用並行上限 2-3 長任務。
>
> **晚收陷阱（Muse 諮詢收編——決策樹尾注）**：`wait` 用有界 timeout 迴圈、勿單一大 block；`stop`/清理前先 `show`／`export`（ledger GC 會吃證據；`export` 對 codex job fail-loud——codex 無 trajectory export 等價物，AIR-47 R8）；委派工單設計成冪等（timeout 後可能重 wait 重收）；jobId 持久化在 workspace ledger（`.delegate-bridge/`），不依賴提交 session 的 context——認領 session 只需 jobId＋同 workspace。
>
> **診斷手段（非收法）**：`.delegate-bridge/jobs.json`／`show <jobId> --json`／`ps` 進程核對——懷疑 job 狀態時用它們查證，不當等待機制。

> 工單模板見 `skills/_common/work-order.md`（foreign runtime 共用；prompt 為任務本文，禁含委派語言）。

#### transport 三態判定（症狀→證據→處置）

> 收法執行中懷疑 job 卡死時的處置分流；證據以上方診斷手段採集。

| 症狀 | 證據 | 處置 |
|------|------|------|
| transport 未啟動 | env/module 錯誤、log `MODULE_NOT_FOUND`、exit 1、jobs.json 無該 job | 可安全重派 |
| transport 在跑、caller 已收（jobId 在手、wait 掛載中） | jobs.json 狀態 running、ps 進程在 | 背景 Bash 掛阻塞 `wait` 收，禁重派（雙跑） |
| transport 死中途、wait 空轉（背景 Bash 活、job 無進展） | 進程已亡、jobs.json 停滯、無新輸出 | 機械驗收（working tree＋jobs.json 終局）＋停背景 Bash job（bridge `stop <jobId>`／kill，恢復主體＝caller process） |

### 套用（三路徑都從 catalog／presets 取值，不寫死絕對 model）

- **external-runtime 派發前重讀本檔「完成回報收法」節**——收法演進快，禁用 session 記憶／memory desc 派發（真實案例：過期派發事故——看到改版 commit 標題 ≠ 重讀條文，舊詞 resume-to-poll 被 wrapper 契約拒絕）
- **CC Workflow path**（ultracode；CC 端；ZCode 端＝registry 釘選）：script `agent({model})` 填 literal —— review command agent = inherit（lite 預設；高保護面／跨邊界語義面升 full）；lite 類＝named preset 生成檔 inherit（spawn-time 需點名時用 CC 詞彙 `sonnet`——**sonnet／haiku 的 catalog binding＝pending_binding**，補 binding 前由 harness 詞彙面解析）
- **inherit＝contract-preserving carrier bypass**：spawn 未點名 model 時（CC 8/9 preset 的實際路徑），Role／authority／surface 隨 WorkUnitContract 傳遞、binding 身份記 inherit——不等於降級 contract（正式化為 inherit pseudo-binding＝後續卡）
- **CC Agent Tool path**（fallback）：spawn `model` param 同上
- **ZCode path**：pins 釘在 `agents/zcode/` 定義檔 frontmatter（由 presets.toml default binding 生成，治理見 agents/AGENTS.md registry 段）

spawn 前印出確認：`[Agent] model=<依角色 tier>, max=N, current=M`（max 查本檔並發表——lite 層較寬）。

## rate limit 與並發上限（model facts 單一源 — 以 provider 現況為準，可能滯後）

| 模型 | rate limit | 並發上限 |
|------|-----------|---------|
| haiku / sonnet / opus | 10 | **3** |
| glm-5.3-flash（lite／vision 層） | — | **高**（遠高於上列；具體數字以 provider dashboard 為準） |

> provider 帳號級事實，repo 無法驗證；改限額時**只改本表**（agent-workflow 等引用此，不自帶數字，避免 provider 改限額時兩處 drift）。數字可能滯後 — 以 provider dashboard 為準。

## classifier 間歇 unavailable（harness 已知風險，與 model 分派正交）

GLM / 非 Claude harness 的 safety classifier 可能**間歇 unavailable**（spawn agent 收 note、無 findings，非主動阻擋）。這是已知服務端間歇故障，**重試 spawn 是正解**（≤ 2 次，常成功），非異常 —— 別因此直接降級主 LLM 自審（會丟失獨立 review）。完整處置（重試 / 降級 + 標記 fallback）見 agent-workflow skill「Auto Mode」（on-demand 載入）。

### spawn 失敗態辨識（處置相反，禁混用）

| 症狀 | 機制 | 處置 |
|------|------|------|
| 收 note、無 findings、無錯誤碼 | classifier 間歇 unavailable（服務端暫態） | 重試 spawn ≤2 次（上段正解） |
| 錯誤碼 **1301**（content filter） | 內容審查攔截——prompt 用詞觸發 provider 端關鍵詞過濾；**同 prompt 重試必再撞** | **禁原 prompt 重試**——改寫用詞後再 spawn；仍撞 → 換任務表述或升 full 層 |
| 錯誤碼 **1308**（usage limit） | 額度窗口耗盡（錯誤內含重置時間戳；~2 秒即敗＝根本沒跑） | 等窗口重置再派（重置前重派無效）；中途陣亡 ≠ 沒跑——先查產物判進度；不用預先降級 |
| 錯誤碼 **1302**（spawn 即敗／agent 中途陣亡） | 帳號級暫態（rate limit／spawn 通道）——**非模型專屬**（full 亦撞；晨間 full reviewer 連續兩案例） | 重試 spawn ≤2；仍撞 → **顯式降級記錄**（序列延後／in-harness 自做），禁靜默棄審 |
