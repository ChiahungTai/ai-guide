---
name: post-build
when_to_use: "After /implement (or any substantial change set) to orchestrate the review chain automatically: diff triage decides which sub-chains run."
argument-hint: "無參數；自動 triage（uncommitted 或 EP baseline 任務弧）"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Edit", "Write", "Agent"]
description: "build 後收尾鏈編排 — code-review → judge-review → 修正迴圈 → consistency → metadata-sync → tour corpus gate（general finalization）→ memory 收尾腿（弧 footprint 盤點＋即時蒸餾/標 terminal）→ Report Shell refresh（hook 2：實作章節＋產圖一次＋badge ✅；持久 delta tour＝ask-once 預設略過）一次觸發。只做編排與 diff triage，方法論真相源在各被編排命令/skill。觸發詞：build 後收尾、post-build、收尾鏈、review chain 自動化、commit 前收尾、memory 收尾腿、弧 footprint。"
---

# post-build — build 後收尾鏈編排

把「build 完手動跑 code-review → judge-review → consistency（→ metadata-sync → tour corpus 修復閉環）」的固定收尾序列編排成一次觸發。本 skill **只做編排與 triage**，各步驟的方法論真相源在被編排命令本身，不重抄（防 single-source drift）。

> dispatch 形態：本鏈各腿的 work units 定義於下方「WorkUnitContract rows」（AIR-91 S3）——orchestration＝decision（主 session 直做，判斷密集，不 agent 化）；spawn 腿（機械驗證／視覺驗收）照 [model-routing](../model-routing/SKILL.md) resolver 解析 candidate，消費側形態查 [agent-workflow](../agent-workflow/SKILL.md)「全生命週期 execution contract（消費側）」（表主體在 agents/AGENTS.md）；批次工單（單次 dispatch 承載多 unit 引用）照 [work-order](../_common/work-order.md)「批次 envelope」——review units 不共 worker context、跨 authority 不合併。

**受眾**：軌道 ①（LLM 執行鏈）——機器自讀自判自修；終點輸出收尾報告給人類判讀是否 commit。

被編排項目全為 skills（`code-review` / `judge-review` / `followup-review` / `consistency` / `metadata-sync`）：Claude 端以 slash（`/code-review`）或 Skill tool 調用，ZCode 端以 Skill tool 調用——跨 harness 統一。

## 標準收斂鏈（user 慣用 pipeline——「照標準鏈」即此）

角色鏈（Role≠Model——寫角色不寫 model 名；現行角色→model 映射查 [model-routing](../model-routing/SKILL.md) 解析表）：

```
Implementer → Reviewer → Judge → lite 機械收尾 → commit gate（在 user）
```

- 構件真相源各歸其主（implement／code-review／judge-review／commit consent），本節只鎖序與 gate
- commit gate 恆在 user（自主模式不豁免）；收尾段只做機械（commit 前整理），不重做判斷

## WorkUnitContract rows（本 workflow 持有——AIR-91 S3）

> 欄位語義單一源＝[model-routing](../model-routing/SKILL.md)（WorkUnitContract schema／Role→authority allow-list／resolver precedence 七步）；candidate 由 resolver 對 [catalog](../model-routing/catalog.toml) qualification records 硬過濾，本檔不材料化 model 值；無合格 candidate＝顯性 no-candidate，禁降 hard requirement。

| work unit | Role | authority | judgment_floor | qualifications | 說明 |
|---|---|---|---|---|---|
| 編排（diff triage／鏈編排／收斂判定／去重比對） | Planner（主 session 直做——Marshal 是 orchestration responsibility 非 Role；Role 值供 schema 對齊，本列不派工） | — | decision | — | 判斷密集段不 agent 化 |
| Reviewer legs（code 鏈／docs-mode 鏈的 code-review） | Reviewer | findings（無 apply／final disposition） | execution（預設；高保護面／跨邊界語義面升 decision） | review_findings | **authority 恆＝findings**——binding 隨保護面升級不改 authority（findings 腿不越權裁決，SM-6） |
| 裁決（judge-review） | Arbiter | final disposition | decision | adjudication | seat 非 decision-qualified 時外派；無 candidate 禁 self-downgrade |
| 已裁決修正（階段 3 apply） | Implementer | apply | execution | implement_from_accepted_ep | ✅ 清單＝execution/apply 腿——決策已由 Arbiter 落帳，apply 腿不做裁決 |
| 機械 finalization（consistency／metadata-sync／rename 反掃／tour corpus gate／lite-verify 對帳） | Verifier | evidence artifact（無 disposition/apply） | execution | evidence_retrieval | 組合命令＋agent 機械對帳 |
| 視覺驗收（visual observation） | Reviewer（observer 腿） | observation artifact／findings（無 final disposition） | execution | visual_observation | 需 `native_vision` ∩ binding `image_transport`——envelope 見下節 |

**escalation**：鏈中任何 execution 腿命中 [implement](../implement/SKILL.md) 同款觸發（EP conflict／新 invariant／public boundary／跨 context 架構選擇／反覆失敗）→ 停止該腿＋escalation record＋轉 decision work unit 或等 user；不得由 execution 腿自行裁決續行。

### Visual input envelope（視覺證據腿——AIR-91 S3）

> 語義單一源＝[model-routing](../model-routing/SKILL.md) resolver precedence 步 7（direct／decomposed 判定）；此處列編排面要求。

- **dispatcher 產生**：source identity（圖檔路徑＋content hash）／transport binding／delivery receipt 由派工方（主 session）記錄——非收件方自報
- **`arbiter_viewed_source=true` 只能由 receipt 推導**（raw image 送達 Arbiter 的回執）；模型／agent 自述「已看圖」不算數
- **direct path**：存在同時 decision-qualified＋`native_vision`＋`image_transport` 的單一 candidate → raw image 送達 Arbiter，verdict 引用同 source identity
- **decomposed path**（無上述交集 candidate＝resolver declared decomposition）：visual-qualified observer 看原圖產 observation artifact → Arbiter input **無 raw image**、只含 observation artifact；verdict 帶 `arbiter_viewed_source=false`＋`decomposed-not-equivalent`（不得宣稱等價於單模型原生視覺裁決）；source identity 端到端一致（observer artifact 與 Arbiter verdict 引用同一 source id）
- **observer artifact 欄位**：facts／interpretations 分列＋region/coordinates＋uncertainty＋observer model/binding（歸因用）

---

## 階段 0 — Diff Triage（決定跑哪些子鏈）

收尾鏈開跑前先盤點背景寫入者（背景 agent／bridge job／排程任務）——有在跑的寫入者先收斂或明確排除，避免掃描吃到中間態。

分析 uncommitted diff（`git status` + `git diff` + `git diff --cached` + untracked）：

| Diff 內容 | code 鏈 | docs 鏈 |
|-----------|---------|---------|
| 含 `.py`/程式碼變更 | ✅ 跑 | 視 `.md` 是否也有變更 |
| `.md` 控制面變更（語義判準——定義見 [execution-plan](../execution-plan/SKILL.md) docs mode「行為控制面」，此處不重定義；路徑僅 hint） | ✅ 跑 docs-mode（code-review docs-mode 軸 → judge → followup） | ✅ 跑（consistency＋metadata 結算面） |
| `.md` 純修飾（單檔 typo／措辭、無契約語義變更；模態詞機械排除見下） | ❌ 跳過（走輕量快道） | ✅ 快道（consistency＋rg 引用掃） |
| `.md` 資料/報告文檔（ai-analysis 分析文） | ❌ 跳過 | ✅ 跑（consistency 鏈） |
| 兩者皆有 | ✅ 先跑 | ✅ 後跑（code 修正可能再動 doc，先收斂 code 再驗 doc，避免驗兩次） |

> **副檔名 ≠ 影響面**：`.md` 不等於無行為影響（ai-guide 的 md 就是控制面）——一律以語義判準分流，不以副檔名或路徑枚舉分流（路徑枚舉 self-defeating：repo-root guide 與消費端控制面都不在 skills/rules/agents/commands 清單，修法自己的檔逃過自己建的 gate）。
> **純修飾快道機械排除**（規範模態詞命中 → 一律升 docs-mode，不得走快道；producer「無語義變更」自述不背書——Claim→Evidence）：diff 命中 `禁`（單字——覆蓋禁掛/禁改/禁寫/禁用，本 repo 禁令主力形態）／`必須`／`禁止`／`不得`／`應該`／`永不`／`MUST`／`SHOULD`／`NEVER`（**詞表單一源＝此處**，他處引用不重列）。反例：單檔 MUST→SHOULD 過 consistency＋rg 卻改變控制語義＝PB1 失敗模式經快道復活。

**逐段 commit 後（弧模式——任務身份優先）**：context EP／卡 Plan 記有 baseline（或殼頭可讀）→ 切**弧模式**：triage 與階段 1 的審查對象改為 `git diff <baseline>..HEAD`＋uncommitted（模式細則見 [code-review](../code-review/SKILL.md)「任務弧模式」）。context 無 EP 記憶（跨 session 接續）→ **從殼讀 baseline**：任務家 `*/index.html`（`ai-analysis/_tasks/`、`ai-analysis/_projects/*/tasks/`、或 `00-tasks/`——探測見 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」）殼頭部聲明 EP 路徑＋baseline hash（hook 1 起攜帶）——baseline 傳遞不依賴 build session context 存活。無任務 baseline（context 與殼皆無）→ 退 uncommitted 模式；uncommitted 亦空 → 印 `[WARN] no diff（逐段 commit 已落地？弧模式需任務 baseline）` 並停止——收尾鏈靜默 no-op 等於大聲錯誤被靜默化。**同樹多任務出口**：弧範圍內的非本弧 commits／uncommitted 檔列「**非本弧項**」清單（AIR-23 allowlist 人工形態正典化）——不納入審查與修正範圍、不順手修。

**Resume 場景**：`.review/<branch>.md` 已存在且有 `open` 狀態 findings（跨 session 從 reviewer session 帶回）→ **身份核對**：帳本 header identity（reviewed revision＋uncommitted identity＋**scope／review_profile／coverage 三欄**）與當前任務狀態吻合（復用判準五條全過——見下「證據身份比對」）→ 跳過 code-review，直接從階段 2 接續；**不吻合**（審後任務又有變更）→ 保留舊 findings、對新增變更補 delta review 再進階段 2（identity 欄位見 [workflow-review-pattern](../_common/workflow-review-pattern.md)「帳本 header identity」）。

印出 triage 結果：`[Post-Build] code=<yes/no> docs=<yes/no> resume=<yes/no> mode=<uncommitted|arc>`

**證據身份比對（階段 1 前——去重≠砍審查；首先核對前段 identity）**：implement 段內 Agent Review 已覆蓋 **scope**（header scope 包含目前所需檔案與 UC/invariant）＋**review_profile**（identifier 相同且定義內容 identity 未變、獨立性配置滿足目前要求）＋**相同實物內容 revision**（tracked diff hash＋untracked 路徑與 content hash 一致）且 **coverage 各軸完成、evidence ref 可讀未失效** → 只補 delta（階段 3 修正迴圈 diff＋跨段整合面）；任一不等價或**比對鍵缺席**（前段 findings 走 context 未落帳本——跨 session 必然）→ **fallback 全審**（明文接線——防 delta-only 永不觸發或誤砍 fresh-eyes）。比對鍵與復用判準（五條，缺一即不得宣稱 complete coverage）單一源＝[workflow-review-pattern](../_common/workflow-review-pattern.md)「帳本 header identity」＋「findings 去重與復用判準」。跨段整合面、不同 context、高風險第二意見仍全審（去重只省重複面）。**修正產生新 scope → 重分級**：修正迴圈或收尾觸及新檔／新 invariant／邊界語義時，重新走風險 profile 判定（[review-engine](../review-engine/SKILL.md)「審查模式判定規則」），不以舊 identity 覆蓋新 scope。註：implement→post-build 完整鏈實測從未一體跑過——本機制主場景是同 session 連續弧與 standalone 鏈的重複審收斂，非 pipeline 常態。

收尾掃描（rg 殘留／consistency 範圍）須明列並行線排除清單——非本弧的 working tree 變更不納入、不順手修（並行原則見 [collaboration-constraints](../../rules/collaboration-constraints.md)「同 working tree 並行原則」）。

## 階段 1 — Code Review（僅 code 鏈）

執行 `code-review`（[skills/code-review/SKILL.md](../code-review/SKILL.md)；無參 = uncommitted diff，弧模式（階段 0 判定）= EP baseline..HEAD——見該命令「任務弧模式」；審查 context 配置由風險 profile 推導——單一源＝[review-engine](../review-engine/SKILL.md)「審查模式判定規則」，Agent 載體接線見該命令「B. Agent 載體」（S1 風險 profile 派發））。本 skill 是**跨命令自動化場景**，code-review 產出寫 `.review/<branch>.md`（Finding Record 表格）供後續 judge/followup 讀。boundary profile 的 intent 腿餵料依 code-review「B. Agent 載體」primed 側清單（EP 路徑由 build 上下文帶入；含 delta_tour 對照——code_reality baseline snapshot 在場時機械產「EP 宣稱模組 vs 實際變動」對照，機制見該節 delta_tour 段；無 EP 時依「B. Agent 載體」降級規則處理）。

**零 findings 快道（先驗完成證據，再判空——空輸出不當零 findings，SM-23）**：判 findings 全空前必先核對——①**terminal=completed**（bridge job／agent 終態；timeout、非零 exit、worker 異常終止皆不算）、②**輸出完整**（非空白、非截斷）且含明確 review 結果與 **scope coverage**（可對照帳本 header identity 的 scope／review_profile／coverage 欄——審了哪些檔案與軸有跡可循）、③**無 job 的合法執行面**（triage 判定無需獨立審查等）需等價的完成與輸出證據，**不臆造 job**。三者皆過才報告並直接進 docs 鏈；timeout／非零失敗／輸出空白／截斷／缺 coverage 一律**留 pending**（列收尾報告＋帳本 open 項），不能直進成功結算——**只靠 exit 0 不足**。

## 階段 2 — Judge Review（僅 code 鏈）

**帳本 lint（AIR-121——進本階段前機械閘）**：`uv run python skills/post-build/scripts/review_ledger.py lint .review/<branch>.md --stage discovery`——發現時態（judge 前，decision＝—／status＝open 是常態）只查 identity 錨＋欄位存在性，decision/status 值域不查；exit 0 進；exit 1/3＝帳本不合 canonical（identity 缺失／欄位缺），先修帳本格式再進（lint 約束見腳本 docstring）；exit 2（帳本不存在）＝首次審查常態，跳過 lint 直接進。

執行 `judge-review`（[skills/judge-review/SKILL.md](../judge-review/SKILL.md)；**指定帳本＝`.review/<branch>.md` 工作帳本**——輸入從該帳本讀 findings，不需人工貼上）。產出 ✅/❌/⚠️ 決策清單。

⚠️ 需確認項：彙整到收尾報告給用戶；**影響 scope／AC／gate 的需確認項阻擋 accepted／Verified**（不結案、badge 維持 🟡、不移 Done——未決即收斂≠全清），純建議類可保留顯性未決但收尾報告必明列未決清單，不偽裝全清。

## 階段 3 — 修正迴圈（僅 code 鏈）

本 skill 是 judge-review 的**呼叫端**，負責 apply：

1. 實作所有 ✅ 採納項（反拖延原則：合理就當下落地；**先規劃整批再批次套用**——目標檔先 Read、多個 Edit 同 block 發、鄰近一行式小修合併、真依賴才序列，見 [tool-discipline](../../rules/tool-discipline.md)「獨立呼叫批次化」+「檔案修改禁令」（Read 紀律））
2. **證據過期標記（PB4）**：apply 後，先前驗證證據（lite-verify 錨點核對、EP 驗證策略覆蓋率核對）中受 apply 觸及檔影響者標過期 → 按變更風險重跑（修正面窄 → 重跑受影響項；修正面廣 → 全量重跑；組合命令形態，非全量無差別）
3. 執行 `followup-review`（[skills/followup-review/SKILL.md](../followup-review/SKILL.md)；讀 `.review/<branch>.md`）——followup 只回驗收 findings／證據（逐項重跑驗證式）；**closure 腿（同 session 續接）只做逐 finding closure，修正越出 finding scope／新問題密度高 → 補 regression（優先跨家族）腿再結案**（分工單一源＝[workflow-review-pattern](../_common/workflow-review-pattern.md)「closure lens 分工」）；**本 skill（主鏈編排者）是帳本 status 唯一寫入者**：僅有可核對驗證結果且原 judge 決策未受挑戰才寫 `verified`/`closed`；followup 帶回新增／矛盾 findings → 回階段 2 交 judge 重裁後再更新（寫入責任與值域見 [followup-review](../followup-review/SKILL.md)「status 寫入責任」）
4. 未通過 → 再修 → 再驗收（**上限 3 輪**；超過 = 停下：卡維持 🟡／In Progress（**不發布 Done／badge ✅**），殘留項列入收尾報告＋EP 進度節（durable 落點——`.review` 隨 commit 清除、報告在對話，兩者皆非 durable）標「未收斂」——連續失敗比乾淨報告更糟，不硬撐）
5. EP 在場（uncommitted 或弧模式皆）→ spawn lite-verify 核對 **EP 驗證策略覆蓋率**（逐情境：入庫測試或跳過理由；agent 定義自帶此項）——機械對帳，不靠 judge 自覺回頭看

修正迴圈或收尾期間變更觸及**新 scope**（新檔／新 invariant／邊界語義——不以檔案數計）時補審（不需全鏈重跑、但不得零審）：重新走風險 profile 判定（[review-engine](../review-engine/SKILL.md)「審查模式判定規則」），命中 extras（整合器／新簽名注入點→段級 review）照映射附加；已按同 profile 觸發過者不重複。

## 階段 4 — Docs 鏈（僅有 `.md` 變更時）

1. 對每個變更的 `.md` 執行 `consistency`（[skills/consistency/SKILL.md](../consistency/SKILL.md)）；fail 項當場修再驗（**重驗範圍 = 修正觸及的檔**，非整個 docs 鏈重跑；上限同階段 3 的 3 輪）
2. diff 觸及 Capabilities / `SYSTEM-MAP.md` / `dependency-graph.md` / `backlog/` → 執行 `metadata-sync`（[skills/metadata-sync](../metadata-sync/SKILL.md)）
3. **rename 反掃（結案 gate 機械收口——非 rename 弧自然空跳）**：①清單萃取（`git diff --diff-filter=R -M` 檔級＋LLM 讀 diff 提取符號級）；②反掃 `rg "<舊符號>"` 掃 AGENTS.md 家族＋專案快 drift 檔；③命中即修或記 drift；零命中＝完成證據。
4. **政策翻轉 consumer-propagation gate**：retire／政策句改寫弧跑[下方 gate](#政策翻轉-consumer-propagation-gateair-75)；candidate 空＝空跳（證據）。他類弧空跳。
5. **CR wiring telemetry checkpoint（AIR-67 弧B；與第 4 點 AIR-75 分軸——政策傳播 vs 行為量測）**：diff 觸及 CR 接線載體（`rules/symbol-query-routing.md`、`skills/cr-query/`、`agents/roles/*`、`skills/_common/work-order.md` §7、review-engine／implement 等 skill 的 CR 接線段）→ 收尾報告必附 `uv run python /Users/ctai/Github/ai-guide/skills/corrections-weekly/scripts/cr_usage.py --days <弧天數>` 輸出（三源計數見 [corrections-weekly](../corrections-weekly/SKILL.md)）。**checkpoint＝基線數字，非 effectiveness proof**——接線已改≠行為已形成，後續真實 review/job 樣本才是判讀面（corrections-weekly 週期承載）。candidate 空＝空跳（證據）。

### 政策翻轉 consumer-propagation gate（AIR-75）

> 觸發：retire／政策句改寫／定義源新增列節弧（他類弧空跳——階段 4 主表第 4 點 candidate 空＝空跳）。retire 翻轉可留原名改語義，舊符號 rg 掃不出來（實證三類）。**第二個獨立消費者出現時晉升 `_common/policy-reversal-gate.md`**（三方共識 09-11）。成本原則：非相關弧只付 candidate detection；不做全檔重驗。

- **① Detect（機械 candidate detector——先跑，便宜）**：`git diff --diff-filter=D` 刪檔清單＋新增列／節存在性＋定義源載體變動（何為定義源依 instruction-writing 單一源規則；叠加階段 4 表頭「僅 `.md` 變更」前置過濾）。
- **② Extract（LLM 萃取——candidate 非空才做）**：舊主張／新約束／consumer concept（＝引用該政策句主張的下游陳述）；全判無政策影響才空跳。
- **③ Delegate（委派既有機制——不重定義 scan）**：定義源變更 → instruction-writing single-source scan；blueprint 在場 → 讀其 AGENTS 真相源映射／更新觸發；否則 rename 反掃的 project AGENTS／EP fast-drift list；`rg` catch-all 封底。**html 投影面（lite backstop——非 freshness 主機制）**：弧 diff 觸及 projection manifest 宣告的任一 upstream → 跑 freshness check（`uv run python scripts/projection_freshness.py --manifest <manifest>`；exit 1 drift → refresh 重投影後 `--update` 收斂，或不重投影則殼頭標 stale）；契約細節見 [illustrate html-mode](../_common/illustrate-html-mode.md)「投影鎖定與 stale 標記」。
- **④ Dispose（處置四值）**：`update`（改新政策／新錨）／`historical`（刻意留的退役說明；provenance 規則見 instruction-writing）／`no-change`（證據足才用）／`unverified`（證據不足——**不視為收斂**，報告帶未驗 consumer／原因）。**rg 命中≠待修**；零命中＝完成證據。

## 收斂態落卡（階段 5 前——AIR-121）

帳本收斂態機械落卡（`.review/` 隨 commit 清除、對話報告非 durable——durable 落點＝卡 notes）：

- 卡在場（本弧 owning 卡）→ 先 `uv run python skills/post-build/scripts/review_ledger.py lint .review/<branch>.md --stage converged`（帳本此時已是終態——converged 全查含值域），exit 0 再 `uv run python skills/post-build/scripts/review_ledger.py parse .review/<branch>.md` → exit 0：輸出 payload 以一行 `backlog task edit <卡id> --append-notes "<payload>"` 落卡
- exit 1/2/3 → **不落卡**：payload 改列收尾報告＋顯性降級記錄（fail-closed 禁猜）
- 卡檔不在本工作樹可見（窗期——卡 commit 在 main）→ 同樣緩衝到輸出檔＋收尾報告，**禁開暫時 worktree 硬寫**

## 階段 5 — Report Shell refresh（hook 2——commit 前最後穩定點）

**前置清理（第一腿，夜掃兜底）**：列 `.agent-tmp/` 清單（`ls .agent-tmp/`）→逐項 LLM 判「後續還用嗎」→用則保留（可 `touch` 保活）、不用當場刪＋清單入收尾報告；夜間掃腿兜底（7 天）。

本 EP 對應殼存在（任務家 `<task>/index.html`——execution-plan 定稿 hook 1 所建）時，在收尾鏈收斂後 refresh（掛點規格單一源見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」）：

1. **實作章節生長**（同一殼的第二幕；內容＝殼規格「敘事骨架變體」實作完成報告列）：做了什麼（分組檔案地圖）／驗證證據（命令+exit code）／delta 前後對照（有圖時）／認知誤差點＋回源連結——**反映修正迴圈後最終態**（排在階段 3 修正迴圈之後，正是為此）
2. **產圖一次**：hook 1 骨架未產的渲染管線圖（mermaid）在此補 degraded 槽——選型依 [diagram-selection](../diagram-selection/SKILL.md)、嵌法依 [mermaid](../mermaid/SKILL.md) 殼內嵌段（HTML 塊/表格屬敘事內容、hook 1 已可寫）；內容凍結後一次產，避免計畫圖重投影
3. **badge**（收斂後 ✅——implement 5a 同步的是 🟡，此處驗證後升級 ✅；中間段殘留 → 維持 🟡）
4. **持久版 delta tour＝ask-once（demand-driven，AIR-80）**：弧條件成立（HEAD 越過 EP baseline、a/b snapshot 在場且非 stale——時點條件真相源見 [code-review](../code-review/SKILL.md)「B. Agent 載體」delta_tour 段）→ 收尾報告「⚠️ 待用戶確認」清單增列「delta tour：產生／略過？」——**預設略過**（user 實證常常產生沒在看；ai-lifecycle 整合弧定案 demand-driven）。**兩階段契約（無論 user 選哪邊都先 register）**：①`code-reality tour register <arcId> --base <sha> --target <sha> [--ep <ep.md>] [--card <id>]`——**pending row 立即持久化**（略過＝row 無 tourPath；ai-lifecycle 憑 row 觸發 UI，缺 row＝永久不可達）；②user 選產生 → `code-reality tour materialize <arcId>`（row-driven intent CLI——snapshot pair／stale gate／EP 解析由 CLI 自組，語義單一源見 [code-reality](../code-reality/SKILL.md)）落 `.tours/delta/<arcId>.tour`（**進 git**）＋row 補 tourPath。略過 → inputs 保留（snapshot pair 不清）＋pending row 在場＝日後單憑 arcId 可補產；條件不符 → 殼實作章節標明 delta 未產（非降級——demand 驅動下不產是正常態）
5. 殼不存在（hook 1 未跑、EP 建於舊慣例）→ 跳過並於收尾報告標明

> **為什麼掛這裡**：實作章節要反映修正迴圈後最終態——鏈中任何一步都可能改 code，只有此點是最終態；且這是 commit 前最後穩定點——掛弧後（commit 後）的產物在 session context 耗盡時必死（三弧實證：弧後敘事——debrief／corpus 重產／delta tour——全滅）。

## Tour corpus gate（general finalization——不限 `.md` 弧；AIR-80 修正）

> 原掛階段 4 docs 鏈下＝bug：純 code 變更時 tour 漂移不會被驗（ai-lifecycle 整合弧定案移出）。任何弧收尾（code／docs 皆然）、repo 有 `.tours/manifest.toml` → 跑 `code-reality tour_validate --manifest --repo .`；FAIL>0 走**修復閉環**（上限 3 輪，同階段 3 慣例），不只列入報告——只報不修讓 corpus 債滾雪球，存量 FAIL 反覆佔據後續每個收尾報告（mosaic 09-07 實證 77 FAIL 積債）：

- **graph 新鮮度前置**：重產前先 `code-reality build --repo .`——stale graph 帶重錨會寫出舊簽名壞錨（09-07 實證殘留 4 條根因；rebuild 冪等分鐘級，FAIL=0 時零成本）
- **觸及族重產一律經 `chain_tour`**（LLM 不手改 `.tour`）；帶 isPrimary 前門的族重產必再帶 `--primary`（漏帶＝旗標靜默掉落）
- **curated（manifest `generator=manual`）族不覆蓋**——其 FAIL 逕落應修清單（兩鐵律單一源見 [tour-bootstrap](../tour-bootstrap/SKILL.md)「重跑語義」）
- 重產後仍 FAIL → callstack md 幀手術（dead symbol／簽名漂移；rg 現場驗證行號與簽名）→ 再重產
- 最終殘留列收尾報告「tour corpus 應修清單」＋閉環統計（重產 N 族／手術 N 檔）；工具語義見 [code-reality](../code-reality/SKILL.md)

## 部署面對帳閘（conditional finalization——AIR-105 設閘、AIR-106 surface 契約化）

**surface 發現契約**：每個部署 surface 在 `deploy/surfaces/<name>.md` 自答三項——①**touches**（候選偵測：什麼 diff 算觸及本 surface）②**probe**（唯讀健康探針 command）③**health 判準**（歸 surface owner，不在本檔重寫各產品怎麼判健康）。本 skill 只做 **discover→dispatch→collect**，禁硬編 surface 清單（新 surface＝加一個契約檔，非改本 skill）：

- **discover**：`ls deploy/surfaces/*.md`；registry 缺席或零 surface → 一筆 `N/A`（附 registry 狀態為證），不給非部署變更加稅——**僅限非 owner repo；owner repo（ai-guide）registry 缺席＝覆蓋缺失，記 `unverified`**
- **dispatch**：逐 surface 跑其 touches 候選偵測；觸及者執行 probe（typo-only 的 `rules/**` 變更免審查腿但**不免**對帳探針）
- **collect**：產出 `deployment-convergence` verdict 四態進收尾報告（即回執 `deployment-surfaces` 欄之值）：`healthy`／`unhealthy`（探針**實證不健康**——已驗證失敗，非未驗）／`pending`（已知應做、因 AC／授權未完成）／`unverified`（探針沒跑或無法判定）。**`unhealthy` 與 `unverified` 都擋收線**（部署面壞＝下次鏈斷，不可帶病收）；`pending` 保持——不得以翻 Done 沖掉，且 `pending`／`unverified` 同步登記該 repo 總驗卡（AIR-104 收 Done 條款的集中驗收機制——verdict 是總驗卡的輸入，結案消費之）；`N/A` 僅在 surface-owned 候選偵測明確零命中時使用。

防偽：觸及面定義模糊時禁填 N/A；探針輸出附原始行，禁貼了不看；部署面存在但無對應 surface 檔＝**未覆全**，collect 記 `unverified`（擋收線）＋登記補檔。

## Memory 收尾腿（finalization——弧 footprint 前移處置；AIR-117）

> 弧的記憶足跡（in-flight 池條目、`.agent-tmp` 證據/暫存、probe 殘留）等結案蒸餾或夜掃才處理＝積壓（真實案例：0917 池 91 筆待蒸餾積壓）。本腿把處置時點前移到收尾當下——記憶新鮮、context 在場。方法論真相源不重抄：池寫入守 [memory-audit](../memory-audit/SKILL.md)「寫入端紀律」，歸屬判定語義同 [commit 階段 2.8](../commit/SKILL.md) 池對帳腿。

1. **池條目盤點**：`rg` 本弧識別鍵（卡 id ∪ EP title 詞——本腿鍵 ⊆ commit 2.8 鍵聯集，漏網由 2.8 兜底；掃描面同 commit 2.8 池對帳腿——`_inventory.md` 全量 desc 投影＋條目檔）→ 本弧新增/修改條目逐條二值處置：**即時蒸餾**（判別式：僅本弧已穩定教訓可收斂重寫——重寫非加段，禁加段紀律不變；照 memory-audit 寫入端紀律形態）或**登記 terminal 清單**（列收尾報告，交結案蒸餾一次性收斂；禁為此在池上發明新標記機制）。in-flight 弧線禁動（既有紀律不變——「進行中弧線收案前禁加段」）；歸屬他弧 → 不動不列
2. **`.agent-tmp` 本弧產物分類**：與階段 5 前置清理同掃不同軸（前置清理＝逐項「還用嗎」；本腿＝弧歸屬）——驗證證據（測試輸出/exit code 節錄、review findings）→ 留至 EP/卡承接後清；probe/scratch/POC → 用完當場清，清單入收尾報告
3. **probe/scratch 殘留確認**：本弧暫建的 probe 檔、POC 目錄、scratch 腳本 `fd` 反掃零殘留（清除義務單一源＝[must-execute-before-complete](../../rules/must-execute-before-complete.md)「POC 到所屬 EP 段落 build＋commit 承接後清除」）

**分工邊界（互補不重複——時點前移）**：本腿＝build 後收尾時點的主動處置；[commit 階段 2.8](../commit/SKILL.md)＝commit 時點的機械防漏對帳（三分歸屬＋in-flight 不動）；結案蒸餾（[kanban-board](../kanban-board/SKILL.md) 結案兩步第三動）＝弧收案時的終態一次性重寫。本腿蒸餾掉的 → 2.8 零命中、結案蒸餾清單變短；標 terminal 的 → 成為後兩者的輸入。

## 結案（收斂點——invoke metadata-sync 結案段）

修正迴圈收斂（followup 全 verified）→ 本 skill 是**呼叫端**，invoke [metadata-sync](../metadata-sync/SKILL.md)「收斂後結案」mode：backlog 結案兩步＋SYSTEM-MAP 升級＋EP 歸檔＋flow-feedback 歸檔（命令合約見 [kanban-board](../kanban-board/SKILL.md)「結案兩步」；掛點全貌見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」）＋badge ✅。未收斂 → 不結案（見階段 3 上限處置）。code 鏈未跑弧（triage code=no——純修飾快道／資料文檔）→ 以 docs 鏈收斂（consistency 綠＋metadata 結算面完成）視為收斂，走同結案段。無 post-build 弧時此結案由 `/implement` 階段 6 fallback 承接（並列主路徑）。

## 階段 6 — 收尾報告（終點，不 commit）

```markdown
## Post-Build 收尾報告
- 回執四欄（控制面弧必填；非控制面弧標 N/A）：classification=<profile>／review=<腿＋evidence ref>／session-freshness=<值>／deployment-surfaces=<verdict>——欄位定義單一源＝[instruction-writing](../instruction-writing/SKILL.md)「落地前審查閘」節
- post-build receipt：寫 `.agent-tmp/post-build-receipts/<branch 經 `/`→`__` 編碼>.json`（branch 原值／head_sha＝寫入當下 `git rev-parse HEAD`／legs 結算／completed_at／本報告指針；AIR-119）——/commit 階段 2.95 與 Stop hook `post-build-gate.py` 的消費源，漏寫＝commit 閘 fail-loud；branch 編碼須與閘側 `_branch_key()` 一致
- code 鏈：findings N（✅N/❌N/⚠️N）、修正 N 項、followup <通過|未收斂(殘留清單)>
- muse 委派（鏈內有派 muse 時才列）：jobId＋status 清單（經 bridge 入口）；ledger 查無的 muse 產出標「未經 bridge，副作用側考古」
- EP 對照：delta_tour=<機械底稿|LLM 對照|無（原因：uncommitted 模式/小變更）>——宣稱觸及 vs 實際變動模組、unexplained 差異項
- 殼 refresh（hook 2）：<完成（badge ✅；delta tour＝已產（落點＋arcId）｜略過（user 裁定，inputs 保留）｜條件不符）|跳過（原因：無殼）>
- 已產 delta tour 時附註：AI Tours 視圖（ai-lifecycle）可走讀本弧——殼實作章節已連結 `.tours/delta/`
- docs 鏈：consistency N 檔（pass N / fail-fixed N）、metadata-sync <跑/跳過>、tour corpus <PASS|閉環後 PASS（重產 N 族/手術 N 檔）|應修清單 N 條>
- memory 收尾腿：池條目 <盤點 N＝即時蒸餾 N＋terminal N＋他弧不動 N｜無池>、.agent-tmp <證據留 N｜清 N>、probe/scratch 殘留 <零殘留｜清單>
- callstack 菜單（repo 有 `ai-analysis/blueprint/callstack-plan.md` 時）：積壓 N 條待生成（機械＝plan **成鏈行數**（①-③ 軌行；④ scripts/索引行不計）− `callstack/` 既有 md 數）——報庫存不催行動，生成＝獨立觸發＋報價（blueprint-bootstrap）
- smell=<建議 zoom 的 dir|無>——訊號源＝階段 1/2 findings 中「疑似 AI 亂加／junk／scope creep」類 finding 所指目錄。**triage 訊號非鏈內調用**：人類看到再決定開 viewport session 跑 [smell-detector](../smell-detector/SKILL.md) zoom（受眾分離——smell-detector 是軌道②人類 viewport，不進本鏈自動跑；baseline/onboarding 盤點屬週期需求，不掛 post-build）
- ⚠️ 待用戶確認：<決策清單>
- 下一步：`/commit`（commit 需人類確認，本 skill 止步於此）
```

**EP 對照行是再次提醒**（主歸納點在 [implement](../implement/SKILL.md) 階段 6——build 現場最清楚）：弧模式帶階段 1 機械底稿；同 session 接續 → 帶入 implement 階段 6 歸納；修正迴圈有新增變動 → 更新後再報。此行是 commit 決策的 triage 訊號（一眼看出 EP 未解釋的變動），深度渲染屬 `/debrief`；delta_tour 機制與時點條件真相源見 code-review「B. Agent 載體」（S1 風險 profile 派發）。

dual-family 第二審查者因訂閱窗口／額度不足跳過時，必須顯式記錄降級（「額度降級：X 跳過，原因＝…」入收尾報告），禁靜默略過——與 [quality-constraints](../../rules/quality-constraints.md)「主動揭露錯誤（Fail Loud）」同族。

---

## 執行約束

- **新工具／新流程的首個真實消費者＝自己的 build 弧**：消費對照寫進收尾報告（工具驗收與弧審查合同一件事，不另造驗收場景）——適用全鏈（含 docs-mode 弧）
- **止步於 commit 之前**：commit 需人類確認（硬規則，自主模式亦然）
- **鏈內委派 muse 必經 bridge**：任何階段把工作派給 muse（dual-family 第二審查者、docs 鏈分擔等）一律走 bridge task 入口，收尾報告記 ledger jobId——入口約束單一源見 [model-routing](../model-routing/SKILL.md)「bridge 必經」；ledger 查無的 muse 產出＝收尾不可考，標「未經 bridge，副作用側考古」
- **不重抄被編排命令的方法論**：審查軸、judge 準則、consistency 六維都在各命令/skill 內，本檔只編排
- 修正迴圈上限 3 輪，超過即停（不硬撐原則）

## 流程位置

canonical review flow 以 [code-review](../code-review/SKILL.md)「流程位置」為單一源。本 skill 是該 flow 中 code-review → judge-review 段 + docs 鏈（consistency → metadata-sync）的**執行載體**：

```
/implement → post-build（本 skill：編排 code-review→judge-review→修正迴圈→consistency→metadata-sync→tour corpus 修復閉環→殼 refresh〔hook 2〕）→ /commit
```
