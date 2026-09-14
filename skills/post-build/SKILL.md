---
name: post-build
when_to_use: "After /implement (or any substantial change set) to orchestrate the review chain automatically: diff triage decides which sub-chains run."
argument-hint: "無參數；自動 triage（uncommitted 或 EP baseline 任務弧）"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Edit", "Write", "Agent"]
description: "build 後收尾鏈編排 — code-review → judge-review → 修正迴圈 → consistency → metadata-sync → tour corpus gate（general finalization）→ Report Shell refresh（hook 2：實作章節＋產圖一次＋badge ✅；持久 delta tour＝ask-once 預設略過）一次觸發。只做編排與 diff triage，方法論真相源在各被編排命令/skill。觸發詞：build 後收尾、post-build、收尾鏈、review chain 自動化、commit 前收尾。"
---

# post-build — build 後收尾鏈編排

把「build 完手動跑 code-review → judge-review → consistency（→ metadata-sync → tour corpus 修復閉環）」的固定收尾序列編排成一次觸發。本 skill **只做編排與 triage**，各步驟的方法論真相源在被編排命令本身，不重抄（防 single-source drift）。

> dispatch 形態：編排者（本命令）＝主 session full（判斷密集，不 agent 化）；鏈上機械驗證／視覺驗收段 spawn 哪個 agent，查 [agent-workflow](../agent-workflow/SKILL.md)「全生命週期 execution contract（消費側）」（表主體在 agents/AGENTS.md）。

**受眾**：軌道 ①（LLM 執行鏈）——機器自讀自判自修；終點輸出收尾報告給人類判讀是否 commit。

被編排項目全為 skills（`code-review` / `judge-review` / `followup-review` / `consistency` / `metadata-sync`）：Claude 端以 slash（`/code-review`）或 Skill tool 調用，ZCode 端以 Skill tool 調用——跨 harness 統一。

## 標準收斂鏈（user 慣用 pipeline——「照標準鏈」即此）

角色鏈（Role≠Model——寫角色不寫 model 名；現行角色→model 映射查 [model-routing](../model-routing/SKILL.md) 解析表）：

```
Implementer → Reviewer → Judge → lite 機械收尾 → commit gate（在 user）
```

- 構件真相源各歸其主（implement／code-review／judge-review／commit consent），本節只鎖序與 gate
- commit gate 恆在 user（自主模式不豁免）；收尾段只做機械（commit 前整理），不重做判斷

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

**逐段 commit 後（弧模式——任務身份優先）**：context EP／卡 desc 記有 baseline（或殼頭可讀）→ 切**弧模式**：triage 與階段 1 的審查對象改為 `git diff <baseline>..HEAD`＋uncommitted（模式細則見 [code-review](../code-review/SKILL.md)「任務弧模式」）。context 無 EP 記憶（跨 session 接續）→ **從殼讀 baseline**：任務家 `*/index.html`（`ai-analysis/_tasks/`、`ai-analysis/_projects/*/tasks/`、或 `00-tasks/`——探測見 [illustrate html-mode](../_common/illustrate-html-mode.md)「產物位置分流」）殼頭部聲明 EP 路徑＋baseline hash（hook 1 起攜帶）——baseline 傳遞不依賴 build session context 存活。無任務 baseline（context 與殼皆無）→ 退 uncommitted 模式；uncommitted 亦空 → 印 `[WARN] no diff（逐段 commit 已落地？弧模式需任務 baseline）` 並停止——收尾鏈靜默 no-op 等於大聲錯誤被靜默化。**同樹多任務出口**：弧範圍內的非本弧 commits／uncommitted 檔列「**非本弧項**」清單（AIR-23 allowlist 人工形態正典化）——不納入審查與修正範圍、不順手修。

**Resume 場景**：`.review/<branch>.md` 已存在且有 `open` 狀態 findings（跨 session 從 reviewer session 帶回）→ **身份核對**：帳本 header identity（reviewed revision＋uncommitted identity）與當前任務狀態吻合 → 跳過 code-review，直接從階段 2 接續；**不吻合**（審後任務又有變更）→ 保留舊 findings、對新增變更補 delta review 再進階段 2（identity 欄位見 [workflow-review-pattern](../_common/workflow-review-pattern.md)「帳本 header identity」）。

印出 triage 結果：`[Post-Build] code=<yes/no> docs=<yes/no> resume=<yes/no> mode=<uncommitted|arc>`

**證據身份比對（階段 1 前——去重≠砍審查）**：implement 階段 4 review 已覆蓋**同範圍＋同內容 revision＋同審查 profile**三者等價 → 只補 delta（階段 3 修正迴圈 diff＋跨段整合面）；任一不等價或**比對鍵缺席**（階段 4 findings 走 context 未落帳本——跨 session 必然）→ **fallback 全審**（明文接線——防 delta-only 永不觸發或誤砍 fresh-eyes）。比對鍵＝S1 帳本 header identity（[workflow-review-pattern](../_common/workflow-review-pattern.md)「帳本 header identity」）。跨段整合面、不同 context、高風險第二意見仍全審（去重只省重複面）。註：implement→post-build 完整鏈實測從未一體跑過——本機制主場景是同 session 連續弧與 standalone 鏈的重複審收斂，非 pipeline 常態。

收尾掃描（rg 殘留／consistency 範圍）須明列並行線排除清單——非本弧的 working tree 變更不納入、不順手修（並行原則見 [collaboration-constraints](../../rules/collaboration-constraints.md)「同 working tree 並行原則」）。

## 階段 1 — Code Review（僅 code 鏈）

執行 `code-review`（[skills/code-review/SKILL.md](../code-review/SKILL.md)；無參 = uncommitted diff，弧模式（階段 0 判定）= EP baseline..HEAD——見該命令「任務弧模式」；dual-context 雙審查者規則見該命令模式 B）。本 skill 是**跨命令自動化場景**，code-review 產出寫 `.review/<branch>.md`（Finding Record 表格）供後續 judge/followup 讀。primed 側 context 依 code-review 模式 B 餵料清單（EP 路徑由 build 上下文帶入；含 delta_tour 對照——code_reality baseline snapshot 在場時機械產「EP 宣稱模組 vs 實際變動」對照，機制見模式 B；無 EP 時依模式 B 降級規則處理）。

findings 全空 → 報告並直接進 docs 鏈。

## 階段 2 — Judge Review（僅 code 鏈）

執行 `judge-review`（[skills/judge-review/SKILL.md](../judge-review/SKILL.md)；**指定帳本＝`.review/<branch>.md` 工作帳本**——輸入從該帳本讀 findings，不需人工貼上）。產出 ✅/❌/⚠️ 決策清單。

⚠️ 需確認項：彙整到收尾報告給用戶，不阻塞其餘流程。

## 階段 3 — 修正迴圈（僅 code 鏈）

本 skill 是 judge-review 的**呼叫端**，負責 apply：

1. 實作所有 ✅ 採納項（反拖延原則：合理就當下落地；**先規劃整批再批次套用**——目標檔先 Read、多個 Edit 同 block 發、鄰近一行式小修合併、真依賴才序列，見 [tool-discipline](../../rules/tool-discipline.md)「獨立呼叫批次化」+「檔案修改禁令」（Read 紀律））
2. **證據過期標記（PB4）**：apply 後，先前驗證證據（lite-verify 錨點核對、EP 驗證策略覆蓋率核對）中受 apply 觸及檔影響者標過期 → 按變更風險重跑（修正面窄 → 重跑受影響項；修正面廣 → 全量重跑；組合命令形態，非全量無差別）
3. 執行 `followup-review`（[skills/followup-review/SKILL.md](../followup-review/SKILL.md)；讀 `.review/<branch>.md`）驗收
4. 未通過 → 再修 → 再驗收（**上限 3 輪**；超過 = 停下：卡維持 🟡／In Progress（**不發布 Done／badge ✅**），殘留項列入收尾報告＋EP 進度節（durable 落點——`.review` 隨 commit 清除、報告在對話，兩者皆非 durable）標「未收斂」——連續失敗比乾淨報告更糟，不硬撐）
5. EP 在場（uncommitted 或弧模式皆）→ spawn lite-verify 核對 **EP 驗證策略覆蓋率**（逐情境：入庫測試或跳過理由；agent 定義自帶此項）——機械對帳，不靠 judge 自覺回頭看

修正迴圈或收尾期間 diff 增量擴至 ≥3 檔時，補一輪審查視角（不需全鏈重跑、但不得零審）——與 code-review 模式 B 的 dual-context ≥3 files 升級門檻對齊，已觸發則不重複。

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
- **③ Delegate（委派既有機制——不重定義 scan）**：定義源變更 → instruction-writing single-source scan；blueprint 在場 → 讀其 AGENTS 真相源映射／更新觸發；否則 rename 反掃的 project AGENTS／EP fast-drift list；`rg` catch-all 封底。
- **④ Dispose（處置四值）**：`update`（改新政策／新錨）／`historical`（刻意留的退役說明；provenance 規則見 instruction-writing）／`no-change`（證據足才用）／`unverified`（證據不足——**不視為收斂**，報告帶未驗 consumer／原因）。**rg 命中≠待修**；零命中＝完成證據。

## 階段 5 — Report Shell refresh（hook 2——commit 前最後穩定點）

**前置清理（第一腿，夜掃兜底）**：列 `.agent-tmp/` 清單（`ls .agent-tmp/`）→逐項 LLM 判「後續還用嗎」→用則保留（可 `touch` 保活）、不用當場刪＋清單入收尾報告；夜間掃腿兜底（7 天）。

本 EP 對應殼存在（任務家 `<task>/index.html`——execution-plan 定稿 hook 1 所建）時，在收尾鏈收斂後 refresh（掛點規格單一源見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」）：

1. **實作章節生長**（同一殼的第二幕；內容＝殼規格「敘事骨架變體」實作完成報告列）：做了什麼（分組檔案地圖）／驗證證據（命令+exit code）／delta 前後對照（有圖時）／認知誤差點＋回源連結——**反映修正迴圈後最終態**（排在階段 3 修正迴圈之後，正是為此）
2. **產圖一次**：hook 1 骨架未產的渲染管線圖（mermaid）在此補 degraded 槽——選型依 [diagram-selection](../diagram-selection/SKILL.md)、嵌法依 [mermaid](../mermaid/SKILL.md) 殼內嵌段（HTML 塊/表格屬敘事內容、hook 1 已可寫）；內容凍結後一次產，避免計畫圖重投影
3. **badge**（收斂後 ✅——implement 5a 同步的是 🟡，此處驗證後升級 ✅；中間段殘留 → 維持 🟡）
4. **持久版 delta tour＝ask-once（demand-driven，AIR-80）**：弧條件成立（HEAD 越過 EP baseline、a/b snapshot 在場且非 stale——時點條件真相源見 [code-review](../code-review/SKILL.md) 模式 B）→ 收尾報告「⚠️ 待用戶確認」清單增列「delta tour：產生／略過？」——**預設略過**（user 實證常常產生沒在看；ai-lifecycle 整合弧定案 demand-driven）。**兩階段契約（無論 user 選哪邊都先 register）**：①`code-reality tour register <arcId> --base <sha> --target <sha> [--ep <ep.md>] [--card <id>]`——**pending row 立即持久化**（略過＝row 無 tourPath；ai-lifecycle 憑 row 觸發 UI，缺 row＝永久不可達）；②user 選產生 → `code-reality tour materialize <arcId>`（row-driven intent CLI——snapshot pair／stale gate／EP 解析由 CLI 自組，語義單一源見 [code-reality](../code-reality/SKILL.md)）落 `.tours/delta/<arcId>.tour`（**進 git**）＋row 補 tourPath。略過 → inputs 保留（snapshot pair 不清）＋pending row 在場＝日後單憑 arcId 可補產；條件不符 → 殼實作章節標明 delta 未產（非降級——demand 驅動下不產是正常態）
5. 殼不存在（hook 1 未跑、EP 建於舊慣例）→ 跳過並於收尾報告標明

> **為什麼掛這裡**：實作章節要反映修正迴圈後最終態——鏈中任何一步都可能改 code，只有此點是最終態；且這是 commit 前最後穩定點——掛弧後（commit 後）的產物在 session context 耗盡時必死（三弧實證：弧後敘事——debrief／corpus 重產／delta tour——全滅）。

## Tour corpus gate（general finalization——不限 `.md` 弧；AIR-80 修正）

> 原掛階段 4 docs 鏈下＝bug：純 code 變更時 tour 漂移不會被驗（ai-lifecycle 整合弧定案移出）。任何弧收尾（code／docs 皆然）、repo 有 `.tours/manifest.toml` → 跑 `code-reality tour_validate --manifest --repo .`；FAIL>0 走**修復閉環**（上限 3 輪，同階段 3 慣例），不只列入報告——只報不修讓 corpus 債滾雪球，存量 FAIL 反覆佔據後續每個收尾報告（mosaic 09-07 實證 77 FAIL 積債）：

- **graph 新鮮度前置**：重產前先 `code-reality build --repo .`——stale graph 帶重錨會寫出舊簽名壞錨（09-07 實證殘留 4 條根因；rebuild 冪等分鐘級，FAIL=0 時零成本）
- **觸及族重產一律經 `chain_tour`**（LLM 不手改 `.tour`）；帶 isPrimary 前門的族重產必再帶 `--primary`（漏帶＝旗標靜默掉落）
- **curated（manifest `generator=manual`）族不覆蓋**——其 FAIL 逕落應修清單（兩鐵律單一源見 [tour-bootstrap](../tour-bootstrap/SKILL.md)「重跑語義」）
- 重產後仍 FAIL → callstack md 幀手術（dead symbol／簽名漂移；rg 現場驗證行號與簽名）→ 再重產
- 最終殘留列收尾報告「tour corpus 應修清單」＋閉環統計（重產 N 族／手術 N 檔）；工具語義見 [code-reality](../code-reality/SKILL.md)

## 結案（收斂點——invoke metadata-sync 結案段）

修正迴圈收斂（followup 全 verified）→ 本 skill 是**呼叫端**，invoke [metadata-sync](../metadata-sync/SKILL.md)「收斂後結案」mode：backlog 結案兩步＋SYSTEM-MAP 升級＋EP 歸檔＋flow-feedback 歸檔（命令合約見 [kanban-board](../kanban-board/SKILL.md)「結案兩步」；掛點全貌見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」）＋badge ✅。未收斂 → 不結案（見階段 3 上限處置）。code 鏈未跑弧（triage code=no——純修飾快道／資料文檔）→ 以 docs 鏈收斂（consistency 綠＋metadata 結算面完成）視為收斂，走同結案段。無 post-build 弧時此結案由 `/implement` 階段 6 fallback 承接（並列主路徑）。

## 階段 6 — 收尾報告（終點，不 commit）

```markdown
## Post-Build 收尾報告
- code 鏈：findings N（✅N/❌N/⚠️N）、修正 N 項、followup <通過|未收斂(殘留清單)>
- muse 委派（鏈內有派 muse 時才列）：jobId＋status 清單（經 bridge 入口）；ledger 查無的 muse 產出標「未經 bridge，副作用側考古」
- EP 對照：delta_tour=<機械底稿|LLM 對照|無（原因：uncommitted 模式/小變更）>——宣稱觸及 vs 實際變動模組、unexplained 差異項
- 殼 refresh（hook 2）：<完成（badge ✅；delta tour＝已產（落點＋arcId）｜略過（user 裁定，inputs 保留）｜條件不符）|跳過（原因：無殼）>
- 已產 delta tour 時附註：AI Tours 視圖（ai-lifecycle）可走讀本弧——殼實作章節已連結 `.tours/delta/`
- docs 鏈：consistency N 檔（pass N / fail-fixed N）、metadata-sync <跑/跳過>、tour corpus <PASS|閉環後 PASS（重產 N 族/手術 N 檔）|應修清單 N 條>
- callstack 菜單（repo 有 `ai-analysis/blueprint/callstack-plan.md` 時）：積壓 N 條待生成（機械＝plan **成鏈行數**（①-③ 軌行；④ scripts/索引行不計）− `callstack/` 既有 md 數）——報庫存不催行動，生成＝獨立觸發＋報價（blueprint-bootstrap）
- smell=<建議 zoom 的 dir|無>——訊號源＝階段 1/2 findings 中「疑似 AI 亂加／junk／scope creep」類 finding 所指目錄。**triage 訊號非鏈內調用**：人類看到再決定開 viewport session 跑 [smell-detector](../smell-detector/SKILL.md) zoom（受眾分離——smell-detector 是軌道②人類 viewport，不進本鏈自動跑；baseline/onboarding 盤點屬週期需求，不掛 post-build）
- ⚠️ 待用戶確認：<決策清單>
- 下一步：`/commit`（commit 需人類確認，本 skill 止步於此）
```

**EP 對照行是再次提醒**（主歸納點在 [implement](../implement/SKILL.md) 階段 6——build 現場最清楚）：弧模式帶階段 1 機械底稿；同 session 接續 → 帶入 implement 階段 6 歸納；修正迴圈有新增變動 → 更新後再報。此行是 commit 決策的 triage 訊號（一眼看出 EP 未解釋的變動），深度渲染屬 `/debrief`；delta_tour 機制與時點條件真相源見 code-review 模式 B。

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
