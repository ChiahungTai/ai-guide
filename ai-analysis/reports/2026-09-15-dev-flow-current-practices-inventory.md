# 開發流程現況總盤點——角色 / Model / 作法 / 雜項 / 記憶（AIR-91 Done 後基線）

> 日期：2026-09-15。基線：`ai-guide@b4a3019`（AIR-91 落地）＋ `0bbddb1`（AIR-96 建卡）。
> 目的：user 在 AI coding 時代程式碼產生太快，仍想某種程度上追上實作、理解重要設計。
> 本報告先做現況整理（descriptive inventory），合理性評估與缺漏判斷是下一步，不在本報告裁決。
> 範圍：ai-guide 本 repo 的開發流程 skills、角色與 model 體系、追蹤理解工具鏈、記憶體系（含原則與實例）。

材料來源：`skills/CLAUDE.md` 工作流拓撲、`AGENTS.md` 受眾模型與消費端 context、
AIR-91 卡與 `ai-analysis/_tasks/_archived/09-15-model-capability-routing/ep.md`、
`skills/model-routing/{SKILL.md,catalog.toml}`、`agents/{AGENTS.md,presets.toml,roles/}`、
各 workflow skill 頭段、`skills/memory-audit/SKILL.md`、`rules/context-management.md`、
`.agents/memory/{MEMORY.md,_inventory.md,_resident-set.md,_audit-state.md}`、
`~/.agents/memory-spine/`、`muse-plugins/memory-governance/README.md`、
`hooks/AGENTS.md`、`ai-analysis/schedule-registry.md`。

---

## 1. 一頁總覽：現在是怎麼開發的

### 1.1 主鏈（標準開發鏈）

```
對話討論新功能
  → [pre-EP 軟 gate] /illustrate 結構化提案（city map / 重用枚舉，人判讀，可多次，不硬擋）
  → /spec（可選，純輔助需求釐清；--write 落 <task>/spec.md）
  → /execution-plan（自足 Self-Contained Segments；段落 0 全域研究＋UC 盤點＋Scenario Matrix＋EP Review Cycle；定稿生 Report Shell hook 1＋EP 落任務家 <task>/ep.md）
  → [/ep-validate（可選，高技術風險 POC 驗證）]
  → post-EP checkpoint：人讀 Report Shell＋/ep-review（方向確認）
  → /implement（TDD 逐段；階段 5a metadata-sync Built 結算 Capabilities＋消費場景＋SYSTEM-MAP 預覽＋殼 badge 🟡；含 Agent Review＋/audit-test；收斂後 final 結案掛 post-build hook 2）
  → post-build checkpoint（看狀況，不硬定先後）：/illustrate（layer 3 結構 viewport，漂移/重造檢查）/ /debrief（深度選配：模組/檔案級深挖；日常判斷材料已由殼實作章節吸收）
  → /post-build（收尾鏈編排：diff triage → code 鏈 [dual-context code-review → judge-review → 修正迴圈] → docs 鏈 [consistency → metadata-sync → tour corpus 修復閉環] → 殼 refresh [hook 2：實作章節＋產圖一次＋badge ✅＋持久 delta tour] → 收尾報告）
  → /commit（lint 閘門 → POC/Demo 處置＋finalization 對帳 → message → user 確認；止於 commit，不含 push/deploy）
```

- 任務家探測順序：`ai-analysis/_tasks` ｜ `_projects/<線>/tasks` ｜ `00-tasks`。
- 卡片弧另有 kanban 生命週期並行：建卡即 commit（防 id 撞）→ 開工 In Progress＋refs → 結案兩步（precheck＋結算物同 commit）→ Done 歸檔。
- 自主形態：`/deep-work` 把 execution-plan→implement→post-build 整套跑完（三觸發：睡前 UC／外出／任務不難整套跑；非開發任務走自身階段；收尾寫 STATE.md）；`/at` 排程接續（先結算再排程）；`/handoff` 交接別人（self-contained prompt）；`/compact-prep` 是 /compact 前置外部化。

### 1.2 受眾二分（設計命令時的第一問：產出給誰）

| 軌道 | 消費者 | 產出形式 | 代表命令 |
|---|---|---|---|
| ① LLM 執行鏈 | 機器自讀自判自修 | 工程化 self-contained（EP、findings、code） | /spec、/execution-plan、/ep-review、/ep-validate、/implement、/post-build、/audit-test、/code-review、/judge-review、/followup-review、/fix-test、/lint-fix、/commit、/metadata-sync |
| ② 人類 viewport | 人用大原則判讀 | 意圖＋結構（行為 artifact＋認知誤差點＋whole-picture 心智模型） | /debrief（改動理解）、/illustrate（結構 viewport）、/smell-detector（壞味道 zoom/baseline） |

- 一檔兩受眾必然產生 token 牆——單檔單受眾（失敗實證：/human-review 三度重建又棄）。
- 三層介入（證據獨立性遞增）：L1 same-session LLM 自判 → L2 跨 session LLM 第二意見（findings 貼回→/judge-review）→ L3 人類 viewport（/debrief＋/illustrate＋/smell-detector）。
- 方向 >> 品質：LLM 預期能做到 Clean Code 等級；災難是方向錯。viewport 重度傾斜方向驗證，不浪費人注意力在 code 品質。

### 1.3 消費端假設（設計命令時核對的 downstream 約束）

solo developer＋AI、無 CI；一 EP＝一 session；model 會退化（結算→開新 session 接續）；/compact 分佈在 EP 各階段（段落自足可接續）；git 多 worktree＋單一 trunk（feature 單向 rebase onto trunk，trunk 永不被 rebase）；Writer/Reviewer 平行 session 分離。

---

## 2. 角色體系（Role ≠ Agent ≠ Model ≠ Carrier）

AIR-91 後詞彙已拆軸。正式定義單一源＝`skills/model-routing/SKILL.md` glossary；下表只做導航。

### 2.1 概念層

| 詞 | 定義 | 不擁有 |
|---|---|---|
| Workflow / Marshal responsibility | phase 順序、轉移、retry、escalation、停止條件；產生 WorkUnitContract | model 選擇、findings 裁決 |
| Role | work unit 可持有的責任與 authority；首期 Planner／Implementer／Reviewer／Verifier／Arbiter；只由 WorkUnitContract 指派 | model、provider、seat、tools |
| WorkUnitContract | work unit 的 Role、authority、qualification、judgment floor、capabilities、surface、independence、escalation | model supply、availability |
| ModelCatalog | 穩定 ModelIdentity、capabilities、qualification status×evidence source | Role、demand、quota、preset |
| DispatchBinding | carrier/surface 可用 token、token kind、effort encoding、transport capabilities | authority、即時可用性 |
| ExecutionPreset | harness 的 tools、read/write、sandbox、background、deployment default binding | Role 指派、runtime routing policy |
| Carrier | main session、native registry agent、bridge 等執行機制 | Role、authority |
| Subagent | DispatchPlan 執行後的 runtime instance | 概念 Role 或 policy |

- `Arbiter` 是 Role 值；`judge-review` 是執行 Role=Arbiter 的 workflow adapter。
- `Marshal` 是 composite workflow 的 orchestration responsibility，不是 Role／agent／skill（AIR-91 已決策：不新增 Marshal skill/agent）。
- 裸詞 `Execution Profile` 不再新增；`ExecutionPreset` 專指 harness deployment adapter，`profile` 保留給 external runtime 的 implement/review/advisory transport mode。
- Role→authority allow-list：Planner＝plan/EP synthesis（無 apply）；Implementer＝apply（accepted EP 後）/evidence；Reviewer＝findings（無 disposition/apply）；Verifier＝evidence artifact（無 disposition/apply）；Arbiter＝final disposition/adjudication。authority 越權在 artifact schema 層阻擋（evidence artifact 不含 disposition/apply 欄；findings 不含 apply/final disposition；只有 Arbiter artifact 有 disposition）。

### 2.2 執行層：9 個 registry agents（authoring 單一源 `agents/roles/`）

| agent | 職責一句 | read/write | requirement 相容 token |
|---|---|---|---|
| code-reviewer | fresh eyes 獨立審查（自帶嚴重度/信心/自證/否證方法論） | read-only | lite |
| code-reviewer-primed | primed 側（diff＋EP＋delta_tour＋Capabilities＋dependency-graph 由呼叫端餵） | read-only | lite |
| cr-research | EP 段落 0 全域研究（CR callers/closure/impact in-path） | read-only | full（AIR-76 v3.1 裁升，原 lite；AIR-91 修掉兩處 lite drift） |
| cross-verify-investigator | 參數化單軸取證（軸由 prompt 指定；源缺場報 unverified） | read-only | lite |
| impl-lite | EP 段落實作（TDD；其測試僅規格陳述，驗收另補 full 複驗） | read-write | lite |
| lite-verify | 機械驗證／consistency gate／followup 對帳（逐項機械證據，非對抗審查） | read-only | lite |
| mem-distill | 肥大 memory 條目蒸餾重寫（逐檔全覆寫，禁碰清單外） | write（memory） | lite |
| spec-miner | 規格挖掘（凍結源碼/文檔鏡像/規範→file:line＋逐字引用） | read-only | lite |
| vision-review | 視覺驗收（讀本地圖檔逐張 verdict；遠端先 curl 落地） | read-only | vision |

- 生成式同步：只改 `roles/`＋`presets.toml`，`uv run python scripts/sync_agents.py` 重建 `agents/zcode/`＋`agents/claude/`；`--check` 是 drift gate；`--map`（＋`--verbose`）是機械對帳源；stale cleanup 只刪 marker-owned 生成物，unmarked 同名檔 fail loud。
- 部署＝registry 視圖：`~/.zcode/agents`→`agents/zcode/`、`~/.claude/agents`→`agents/claude/`（目錄載入點，symlink 成立；registry 內是實檔拷貝因為 per-harness frontmatter 分歧）。
- 已知刻意分歧：claude 拷貝 tools 減 CR MCP 白名單行（生成器承載）。
- pin 單一源紀律（AIR-91 S2 起）：zcode 生成檔 pins 由 `presets.toml` default binding 經 `catalog.toml` 解析生成；改 pin＝改 presets（＋catalog binding）→重跑 sync；`presets.background` 與 roles frontmatter 有 parity gate。
- 內建型別陷阱：`general-purpose`／`Explore` 非 registry、無 pin、繼承主 session 旗艦；lite 角色任務誤派內建型別＝旗艦燒機械段（AIR-50 兩次實例）。

### 2.3 全生命週期 execution contract（表主體 `agents/AGENTS.md`，消費側 `skills/agent-workflow/SKILL.md`）

- 開卡：主 session 直做（decision work unit）。
- 研究：spawn cr-research（decision/global-research）／spec-miner（execution）。
- EP 規劃：主 session 直做（判斷密集）。
- EP review（雙家族）：主 session 編排 GLM 側 code-reviewer×2＋muse 側 bridge 工單；muse `task` 形態＝`--background` fire-and-forget＋`wait`/`show` 晚收。
- build 實作段：主 session 編排；機械可規格化段 spawn impl-lite。
- build 內 Agent Review：3-perspective（fresh＋primed＋lite-verify 錨點驗證）。
- judge 裁決：主 session 直做（seat 非 full 時升級外派 bridge，禁 in-session 降級自判）。
- post-build 編排：主 session 直做；Reviewer legs 依保護面選 binding 但 authority 固定 findings。
- 機械驗證／consistency：spawn lite-verify。
- 視覺驗收：spawn vision-review（pin 禁降非影像款；失敗→標未驗證，禁主 session 直讀圖）。
- 多源查證：spawn cross-verify-investigator。
- commit preparation：主 session（對帳可 spawn）；commit consent＋執行：主 session 互動永遠（任何 dispatch 不覆蓋）。
- memory 結案蒸餾：spawn mem-distill。

### 2.4 External runtime 家族（thin forwarder，不長特化 agent）

- 家族＝運輸身分軸（muse／codex／glm），非 model 強度軸；profile＝transport mode（implement／review／advisory）。
- 角色→family→profile 映射：實作→muse/implement；external second-opinion review→muse/review；in-harness acceptance reviewer→GLM；診斷 rescue→codex/implement（ad-hoc 低頻）；advisory 掃描→muse/advisory；機械驗證/探索→GLM/lite；視覺驗收→GLM/vision（muse 跨家族備選）；架構級 EP→muse/implement（user 在場裁決為放行前提）。
- 治理原則：external-runtime 不新增特化 agent 定義檔；工單即介面；flag 具體值、收法、transport 三態判定單一源在 model-routing skill；flag 未暴露項以工單紅線承載。
- bridge 必經：委派外部 runtime 一律經 delegate-bridge 入口（`task --family muse|codex|glm`），禁直呼 `muse exec`／`codex exec`；caller surface→合法路徑對照在 `rules/bridge-dispatch.md`（禁手拼版本化 cache 路徑；禁造第二 pin）。
- 承載者硬性：外部 runtime 委派＝caller 背景 Bash 直呼 bridge，禁 subagent wrapper 承載（不佔 agent slot／rate limit；wrapper 的 600s timeout 約束從未存在）。
- GLM bridge 契約：native-ID-only（裸委派落 `GLM-5.3-Flash`；旗艦必顯式 `--model GLM-5.3`；`sonnet`/`opus` fail-closed）；寫入＝`--write-mode edit`（缺席≡plan 唯讀；`build` 是唯讀收緊檔，勿當寫檔腿）。
- webgpt（chatgpt-web 池）三約束：審查/規劃專責禁大型實作（單則訊息上限遠小於窗口，派發前段落級評估）；額度池意識（`wham/usage` 看不見 web 池）；五類固定失敗態分流處置，禁盲重派。
- 顧問兩層語義：user 說了（「跟 codex 討論」＝指令動作，禁自收斂跳過；顧問僅意見權；兩段式回報）vs user 沒說（AI 按需自判，難題才叫，勿套會議儀式）。

---

## 3. Model 體系（AIR-91 doctrine）

### 3.1 解析鏈與 resolver 七步

```
workflow phase → WorkUnitContract → candidate（model identity × binding × effective effort）
→ RuntimeCompatibility → AvailabilitySnapshot → ArcOverride / RoutingPolicy → DispatchPlan → carrier
```

resolver 是 model-routing skill 的 instruction protocol（不是 Python runtime router；TOML＋sync_agents 只承擔可機械驗證的 supply 與 deployment projection）：

1. workflow phase 建立 WorkUnitContract。
2. qualification／judgment／capability hard filter（qualified 且 effective effort 可確認達標；conditional 不過 decision hard gate；無記錄 fail-closed；effort 不能把未 qualification 候選補成 decision-qualified）。
3. binding／carrier compatibility（token kind／effort encoding／transport 能否承載 surface）。
4. availability tri-state（available／unavailable／unknown＋source＋freshness＋failure family＋retryable-at；stale/unknown 永不當 available；1308 在 retryable-at 前不重選；retry 有界）。
5. ArcOverride constraint（user 當弧指示只約束合格候選排序；要降級須明說接受 degraded contract；指向不合格/不可用＝零 dispatch＋顯性報告）。
6. RoutingPolicy soft ranking（合格且可用集合內穩定偏好＝dispatch 預設段）。
7. 產出 DispatchPlan；高推理＋影像無單一合格 candidate＝declared decomposition（兩段式 visual fallback）；皆無＝no-candidate report。

- DispatchPlan＝selected candidate 四元組＋carrier adapter 路由（等於 named preset default 用 registry／spawn override 同 contract 換 binding／否則 main-or-bridge 完整裝載 Role/authority/surface＋禁再委派）＋ExecutionPreset reference。
- DispatchTrace（work-unit-local）：contract hash、candidate/binding、failure family、retryable-at、attempt disposition。
- Hard invariants：no-silent-downgrade；token provenance（native／alias／slug 分欄禁混型）；effective effort；model fact single source；volatile state 不住 catalog／rule。
- 供給事實單一源 `skills/model-routing/catalog.toml`：ModelIdentity（glm-5.3、glm-5.3-flash〔native_vision〕、claude-opus、chatgpt-web-high、gpt-5.6-sol、gpt-6-astra、fabel〔binding 待補＝零 candidate fail-closed〕、muse-spark-1.3〔native_vision〕）＋DispatchBinding（token/token kind／effort encoding／transport，例 flash binding 帶 image_transport）＋qualification records（workload×status×evidence_source×binding scope×effort 約束；首期六 workload：ep_synthesis、adjudication、implement_from_accepted_ep、evidence_retrieval、review_findings、visual_observation）。
- 部署預設單一源 `agents/presets.toml`：registry slug→harness membership／read-write／sandbox／background／default binding FK→catalog；S2 等價 gate 證 9-agent pins 逐 byte 不變後才刪 legacy dict。

### 3.2 各 workflow 的 WorkUnitContract rows（各 owning skill 持有，語義引用 model-routing）

- execution-plan：段落 0 證據收集（Verifier/evidence/execution/evidence_retrieval）／段落 0 全域綜合（Planner/plan/decision/ep_synthesis，主 session）／UC 盤點＋EP synthesis（Planner/decision/ep_synthesis，主 session）／EP Review legs（Reviewer/findings/execution 預設，高保護面升 decision）／finding 裁決（Arbiter/final disposition/decision/adjudication）。
- implement：實作主腿（Implementer/apply/execution/implement_from_accepted_ep，受 accepted-EP predicate 約束）／機械驗證腿（Verifier/execution）／Agent Review legs（Reviewer）／finding 裁決（Arbiter/decision）／decision escalation 腿（觸發時才派）。
- judge-review：固定 Arbiter＋adjudication＋decision＋final_disposition；decision ≠ apply（judge 交付決策＋驗證依據，apply 由呼叫端）。
- post-build：編排（主 session 直做 decision）／Reviewer legs（authority 恆 findings，binding 可升）／裁決（Arbiter）／已裁決修正（Implementer/apply/execution）／機械 finalization（Verifier）／視覺驗收（observer 腿，需 native_vision ∩ image_transport）。
- 單次呼叫原則：user 只呼叫一次 workflow，execution/decision 腿由 resolver 分流，中途不手選 model。

### 3.3 關鍵政策（穩定 policy 住 skill，現值住 spine）

- 額度現值（V）不住 skill：派工前查 spine `model-runtime-entitlements`（as-of rolling state；查不到＝探測後派）。
- Harness 主軸：ZCode 日常主力（主 session GLM 5.3；full-tier registry 釘 glm-5.3 不隨主 session 漂移；lite 執行檔 glm-5.3-flash）；muse code 直用時該弧主力（muse-spark-1.3 全棧）；審查類→lite 預設（judge 裁決層固定主 session 旗艦）；實作 bridge 委派預設 muse；影像現值 glm-5.3-flash（選它因原生多模非因成本）；codex 預設不派（僅 user 顯式指定）；CC sonnet/haiku/opus 可派（預設 sonnet，haiku 基本不用）。
- 額度 failover（僅撞牆時）：GLM 1308→muse 承接執行段；muse 亦乾→等 reset（/at）或 user 裁定硬跑；任何降級顯式記錄。
- arc 內改判：user 最新一句為準，只影響該弧。
- 旗艦資格五項（跨文件交叉推導力／judge 否決力／規劃契約查證力／長弧查證紀律／寫入邊界首改邊界意識；坐位現值 ZCode 主軸 GLM 5.3）。
- lite 分工律：執行層可降 lite 條件＝保護面厚度三件全滿（既有測試釘住＋驗證閉環＋非跨邊界語義面）；判斷密集位（judge／EP 規劃／post-build 編排）不可降；lite＋max effort 補償是未驗證路徑；模型歸因必須 per-message modelID 機械對帳，不接受 session 自述。
- effort 家族對譯表（ZCode thoughtLevel／CC effort／muse effort／codex --effort 語義對應，非等價保證；thoughtLevel sticky 不達 wire 但書；flip 實驗實證定義值 silent no-op）。
- rate limit 與並發上限表（haiku/sonnet/opus 並發 3；flash 高；provider 改限額只改此表）。
- spawn 失敗態辨識（處置相反禁混用）：classifier unavailable→重試≤2；1301 content filter→禁原 prompt 重試，改寫後再派；1308 usage limit→等窗口重置；1302 帳號級暫態→重試≤2 仍撞則顯式降級記錄。
- session 定向接續：一律視為 mutating continuation（原卷不動走 codex fork 或讀卷面）；writer 守衛＋workspace 守衛皆 fail-loud；成本警示（continuation 帶整包 context；可口述走 handoff doc）。
- 完成回報收法：簡單直跑（背景 Bash 阻塞形，exit 喚醒）／長跑 fire-and-forget（`--background`＋`wait`／`show` 晚收；timeout 語義 exit 124＝重掛；ZCode/CC SessionEnd 差異決定能否跨 session 認領；liveness ticker 看產物停滯與 heartbeat 互補）／prompt 工程（wrapper 已退役）／LLM 層 ETA-gate fallback（永不 LLM 層定時輪詢）；多工複用（N 個 jobId 統一掃；並行買 wall-time 不省花費）；晚收陷阱（有界 timeout 迴圈、stop 前先 show/export、工單冪等、jobId 持久化 workspace ledger）。
- eligibility gate 六條（implement 形態）：決策凍結／條款客觀化／單一 writer 無待決／主價值＝承接 implementation loop／環境可啟動／架構級 EP 須 user 在場；review/advisory 形態改判 ①②⑤＋read-only transport＋跨家族成立＋可重現輸出（③④是 implement 專屬，不得擋 review 腿）。
- 跨家族解析表（未指定 family 時）：GLM/ZCode→muse；codex→muse；glm→muse；muse caller→fail-loud 停下要 user 選（禁解析層自選降級）。
- inherit（pseudo-binding）：spawn 未點名 model 的 carrier adapter 第四形態；binding=inherit 非 catalog binding；contract-preserving；需 decision/特定 qualification 而解析不滿足→換實 binding；CC sonnet/haiku 在 catalog binding 補上前標 pending_binding；解析結果記 DispatchTrace，實際 wire model 由 `[Agent] model=…` 承載。
- 視覺兩段式 fallback：無單一 decision＋native_vision＋image_transport candidate 時，observer 看原圖產 observation artifact（facts/interpretations＋region＋uncertainty＋observer 身分），Arbiter input 無 raw image 只消費 artifact；verdict 帶 source identity＋`arbiter_viewed_source=false`＋`decomposed-not-equivalent`；`arbiter_viewed_source=true` 只能由 dispatcher 的 source-delivery receipt 推導，模型自述不算。

### 3.4 AIR-91 驗收與殘項

- S1 catalog＋resolver protocol；S2 presets＋projection 等價切換；S3 十二檔 work-unit doctrine＋accepted-EP 硬閘門＋視覺 envelope；S4 manifest＋doctrine gate＋導航收斂。
- 驗證：段級 scoped judge×3＋全套 510 tests＋行為實驗 30/30 PASS＋外部 review 三腿（codex×2 零 finding、muse 5 findings 全 apply）＋三 harness deploy＋fresh-load。
- 殘項收於 AIR-96（In Progress）：effort 三處 parity gate／inherit 正式化／muse bundle 瘦身（33,013B＝36KiB gate 的 89% WARN，目標 ≤80%）／pre-commit 環境隔離／glm bridge 四操作缺陷診斷腿。

---

## 4. 作法（開發方法與品質機制）

### 4.1 規劃與實作

- Self-Contained Segment：每段獨立 Context／功能完整／驗證自足／執行獨立；AI 只讀該段能做。
- EP 類型：implementation（預設，可直接 /implement）vs blueprint（≥5 段中型變更的綱要，每段衍生子 EP，`parent:` 繼承，不直接 implement）。
- 規模分級：是否寫 EP（跨檔 feature／中型以上才寫；單檔小 tweak 不寫；碰單位邊界/除權息/時區/會計/風控即非 simple，至少列 invariant＋驗證式）。
- accepted-EP predicate（implement 進場硬閘門）：ledger 每列 terminal（implemented/rejected/verified）＋adopted 全回寫＋無 needs-confirmation/pending＋user 顯式呼叫 implement；任一不成立禁 execution/apply。
- escalation 觸發（命中即停腿＋escalation record＋派 decision）：EP conflict／新 invariant／public boundary／跨 context 架構選擇／反覆失敗（連 3 次）。
- TDD（test-driven-development skill）：RED→GREEN→重構；反 rationalization、mock 階層、xfail strict。
- 驗證策略（validation-strategy）：e2e 優先／交易 replay>live／放 scripts／不重驗 package；DEPTH-MIN→SAMPLE→FULL（失敗回 MIN，禁改後直跑 FULL）；消費端驗證模式（先定位主要消費者跑完整流程；symbol 命中≠接線被驅動）。
- 驗收證據（rules/acceptance-evidence＋skill 深層）：證據獨立性（AI 同寫 test＋impl 只證自洽）；no-impact claim 須獨立機械證據；L1-L6 階層（禁低層冒充高層）；A/B 軸分工；Intent Drift Type A/B；filter trap；Runtime Invariant Assurance。
- 質量約束（rules/quality-constraints）：完整交付（功能＋測試＋邊界＋文檔同步）；Crash-Only（量化/高頻/風控/批次：無效輸入立即崩潰，禁吞錯續行；不適用長會話/UI/UX 優先）；Fail Loud（未確認成功/跳過/未驗邊界明列限制）；多步驟檢查點。
- 修改後必須執行驗證（rules/must-execute）：每個可執行檔改後實跑；測試改後跑 pytest；新增測試先 RED；例外僅純文檔/註解/ruff import 排序。

### 4.2 審查鏈

- review-engine（通用審查邏輯單一源）：嚴重度／信心水準／審查者自證／LSP 查證／審查模式判定／Writer-Reviewer 分離／多層驗證／review 執行預設（force 獨立／max-agents／model／視角／spawn-vs-session）。
- code-review-and-quality（六軸 what to check：Correctness／Readability／Architecture／Security／Performance／Capability Coverage）。
- /code-review：任務弧模式（baseline hash..HEAD＋uncommitted；baseline 來源 EP/卡/殼頭；非本任務 commits 註明；dual-context 同吃一份 diff，範圍判定先於 spawn）；Lint 預檢（F401／PLC0415）；預設 spawn 獨立 agent（force 獨立，取消 Main 自審）；派發前 arch-thinking 觸發表檢查。
- /ep-review：F1-F5（完整性／合規／一致性／遺漏／場景覆蓋）；受眾是 LLM 執行鏈不給人看；人類 viewport 是 /illustrate。
- /judge-review：不盲從（✅/❌/⚠️；反拖延：合理當下落地，actor 邊界＝judge 落帳本、apply 由呼叫端）；三防線（每行裁決附證據／全採納當警訊否證重查／inferred 必重跑實測）；機械化補償（closed 宣稱命令對帳／✅ 清單＝驗收輸入＋閘門候選／長弧後段列查證）。
- /followup-review：審查者回頭驗收實作結果（review 工單預告驗證式→judge→修正→同 session followup 複驗優於 fresh context）。
- /audit-test：測試品質稽核（反模式／覆蓋對稱性／mock 健康度，只讀不寫）。
- /fix-test：先 triage（哨兵＋病歷＋仲裁）再分類 A/B/C/D/E＋階段 4.5 TWINS 同類 sweep。
- /lint-fix：ruff＋mypy 自動修正。
- /consistency：文檔品質（自洽／矛盾／順序／自包含／精準／Signal-Noise）；與 post-build 鏈必跑非 optional。
- /state-review：全 repo 狀態對抗審查（A 軸機器，抓 diff-review 盲區的 state-rot）：環境凍結＋scope manifest→external family 單發深審→in-family judge→gate 候選；read-only。
- /cross-verify：多源交叉查證（db/git/log/memory/cr/web 軸群平行取證→對帳→verdict＋unverified；源枚舉制，web 須顯式點名；產出軌道①可餵 judge-review）。

### 4.3 思考與架構方法

- deep-thinking：可查證決策（使用者行為與消費者、事實/假設、現況與選項、直接/間接後果、回復與改判條件；摘要融入消費命令格式）。
- arch-thinking：use case／依賴／bounded context 判準；按觸發表查重用/state/補償/結構證據；Clean Architecture＋DDD 三 lens（政策不依賴外部細節、按語義定 context、先問消費者行為）；不憑目錄或 _private 判邊界。
- design-thinking（rule）：決策先釐清行為/成功條件/約束；事實/假設分開；追蹤變更→直接/間接後果；單向門查失敗與回復條件。
- api-and-interface-design：穩定 API／模組邊界（Hyrum's Law、邊界驗證、agent-friendly interface）。
- debugging-and-error-recovery：系統性根因（no-guessing 熔斷、用戶糾正訊號表）。
- autonomous-execution：無人自主決策／錯誤恢復／完成回報／workspace safety／path invariants／session recovery（false-done 偵測）。
- python-type-gap：第三方型別缺口四層策略；Python 規範（rule）：`__init__` 禁 re-export、3.12 型別（禁 future annotations／TYPE_CHECKING、Self、內建泛型）、`uv run` 強制、禁 PYTHONPATH／外部 timeout。
- 工具紀律（rule）：符號→code-reality、型別→bridge、文字→rg、檔案→fd；Edit/Write 前先 Read；Edit 失敗階梯；閘門禁 pipe 到 tail/grep；獨立呼叫批次化；輸出繁中＋英文術語。

### 4.4 文件與知識維護

- /metadata-sync：三 mode（build 5a Built 結算／收斂後結案／standalone 補漏；--check 僅報告）；偵測漏掉的 Capabilities/Kanban/SYSTEM-MAP/arch/EP 歸檔/flow-feedback。
- /doc-health：Capabilities＋Kanban 健康檢查（12 角度；--report 能力地圖；--sync-system-map）。
- /instruction-init／-clean／-sync：專案 instruction 體系生成／清理（--distill 保守防護）／文檔與程式碼同步性。
- instruction-writing（reference skill）：rule 留 always-on 核心、完整規範住 skill；載體選擇（hook＝純機械＋單一入口＋無語義例外三者皆是，缺一退 LLM 流程）；文檔自洽五維檢查；single-source drift 防護（改定義源強制 rg 掃引用逐檔同步）。
- instruction-testing（draft）：四 surface gate（activation／behavior／micro-test／static）＋pressure scenario／retrieval-application probe；A 軸不取代 B 軸；pilot 未執行（AIR-91 行為實驗是其 B 方案縮減實例）。
- /sync-sources：跨檔 single-source invariant 機械檢查（含非 Claude 部署 bundle 新鮮度）。
- /rebase：trunk-based（trunk 永不被 rebase；feature rebase onto trunk；`all` 批次；dirty 例外）。
- /standup：晨間 digest（跨 worktree session 聚合＋commit/kanban/SYSTEM-MAP transition；由排程載體整合進 daily-report）。
- /daily-maintain：每日自動維護（排程用；低風險自動修正＋commit；maintain skill 是其 4-phase 核心）。
- corrections-weekly：糾正模式週報＋CR 健檢＋memory 寫入歸因（ZCode db 撈候選＋LLM 判讀；暴增＝規則衰減訊號；CR 主形態已轉事件觸發，本 cron 僅週期診斷）。
- /flow-feedback：session 摩擦收集器（user 植入摩擦＋AI map 到 skills，產 type-1 時機/type-2 設計建議，寫 ai-analysis/flow-feedback/）。
- /flow-review：定期讀累積 feedback（找重複摩擦＋聚合 type-2＋memory-routing 判定；定案→/execution-plan 或 kanban→/implement）。
- self-contained-prompt：交接 prompt 設計原則（/handoff 與 agent-review-cycle 共用；foreign work order 帶 contract＋禁再委派＋binding evidence）。
- diagram-selection＋mermaid：畫圖前選載體（四問＋跨載體共性；vision 三段式契約）＋Mermaid pragmatism（禁 init、fill+color 成對、殼內嵌配方）。
- context7：library/framework/SDK/API 用法先查最新官方文檔（優先於 web search）。
- symbol-query-routing：cr-first（符號→code-reality refs/callers/closure、型別→bridge hover、文字→rg、檔案→fd；index 是 build-time，編輯後重 harvest；降級須標未 index 驗證，禁把未查到斷言不存在）。
- llm-output-convention：雙通道（print 當索引、Logger 當資料庫；Logger name 用 module-path；tag 全表）。
- voice-notification：三通道語音通知。

---

## 5. 追上實作的工具鏈（user 核心目標的現有裝備）

### 5.1 Report Shell（任務家報告殼：方向確認與日常判斷材料的主載體）

- hook 1（/execution-plan 定稿建）：EP 計畫的人類 viewport（Scenario Matrix 情境＋baseline hash；post-EP checkpoint＝人讀殼＋/ep-review）。
- hook 2（/post-build 殼 refresh；無 post-build 弧由 implement 階段 6 fallback）：實作章節＋產圖一次（diagram-selection 選型補 degraded 槽）＋badge ✅＋持久 delta tour。
- 日常弧判斷材料（做了什麼／驗證證據／認知誤差點）已由殼實作章節吸收；殼是 commit 前穩定點。
- 殼生成分工（decision 篩選敘事→vision 驗收）＋機械底稿規則見 illustrate-html-mode；殼全走手寫 codegen（archify 產線已退役，AIR-74）；index.html 一律進版控。

### 5.2 /debrief（行動後聽取報告；深度選配）

七段倒金字塔：意圖一句話／行為黑盒子（對外行為變了 vs 純結構重構；docs 變更渲染 behavior delta）／前後差異（語義 diff；機械底稿 delta_tour）／檔案地圖（按角色分組）／波及與缺口（hub 波及吃 hub_refs）／驗證證據（demo-checklist，NONE 不掩蓋）／認知誤差點（Type A 詮釋假設/歧義選擇/推斷行為＋Type B 動態漂移，每點附確認問題）。理解非審判（不產 finding／不審結構／不質疑存在）。無參數＝任務弧優先（baseline→弧模式；無→uncommitted；皆空→HEAD~1）。

### 5.3 /illustrate（結構 viewport；4 mode＋3 checkpoint）

- 4 mode：A 設計決策（這樣設計對嗎）／B 理解既有（這怎麼運作；artifact menu：call graph／sequence／class slice／data-flow／boundary，default boundary）／C 審查驗證（對不對；語義 diff＋假設驗證矩陣＋city map）／D 溝通傳達。
- 3 checkpoint：pre-EP 軟 gate／post-EP／post-build drift detection。
- 輸出：Console（ASCII 精簡）／MD（Mermaid 詳盡）／HTML（報告殼 opt-in；圖可 zoom/主題跟隨；無參數委派 /debrief）。
- 與 /code-review axis 3 共用 arch-thinking 但受眾不同（人 viewport vs 機器 finding）。

### 5.4 /smell-detector（行動前偵察；與 /debrief 對仗）

- zoom `<dir|files>`：變焦批判（質疑存在：6 判準＋查證誠信＋Domain 層判準；重構第一問＝最好的重構是刪除）。
- `--baseline <dir>`：廣角盤點（per-directory 4 檔＋invariants＋--status/--stale/--arch 追蹤）。
- smell＝表面訊號只指向不指控，判讀是人（no-severity）；read-only，修復走 /implement、/fix-test；CR 接線唯一（YAGNI/dead-code verdict 走 hub_refs hazard 防護）。

### 5.5 code-reality 工具鏈（meta 層機械底稿；獨立 repo `~/Github/code-reality`，Rust carrier）

`code-reality <tool> --repo <root>`：build（一鍵數據面：偵測→producer→graph_db；mixed repo 雙語言合一）／snapshot／hub_refs（hazard 分層防「0 refs 可刪」誤判）／runtime_edges／boundary／delta_tour（snapshot diff＋EP 宣稱對照；持久版復用 post-build 產物，落 `.tours/delta/` 進 git；臨時版落 .agent-tmp）／chain_tour／graph_audit（Rust 完整度）／scip_refs／tour_validate／tour_upgrade／tour_manifest。repo profile `.code-reality.toml`；工具事實真相源＝CR plugin skill（本 repo skill 管接線/紀律）。implement 階段 1 baseline snapshot；post-build/code-review 弧模式 delta_tour 對照；debrief 第 3/5 段機械底稿。

### 5.6 導覽與知識庫（tour／blueprint）

- tour-bootstrap：Chain 場景／Delta 時間層；corpus 前門與動線優先序裁定；`.tour` 語言契約（CodeTour 消費端正則）；機械驗證＋AI 不代終審停點；建在 code-reality 之上。
- blueprint-bootstrap：人讀合成視角 scaffold（骨架＋半滿＋🤖/👤標記＋誘導問題＋治理模板）；callstack 場景敘事生成＝斷點③解法（重複度盤點→鏈枚舉→逐幀實證→coverage 稽核→findings，餵 tour 場景層）；既有 blueprint 走 audit 不重建。

### 5.7 地圖與索引（Capabilities／SYSTEM-MAP／dependency-graph／backlog）

- AGENTS.md Capabilities＝已完成能力索引；backlog＝承諾池；architecture.md＝why；SYSTEM-MAP.md＝跨域現狀；dependency-graph.md＝人工依賴/ripple 地圖（機械查詢交 code-reality）。
- 長文按需 link，禁全量 transclude；UC 狀態流轉與 Capabilities 寫入格式見 metadata-sync。
- 多卡優先序可由 project blueprint dependency graph 決定（backbone），未被支撐的卡走 kanban triage。

### 5.8 回饋與演化迴路

/flow-feedback（摩擦收集）→ /flow-review（聚合 type-2＋memory-routing 判定）→ /execution-plan 或 kanban → /implement。corrections-weekly 量測糾正模式（暴增＝規則衰減訊號）＋CR 健檢＋memory 歸因。/state-review 抓跨弧累積漂移（state-rot）。

---

## 6. 記憶體系（原則＋實例，不遺漏）

### 6.1 拓撲（一句話：主體在 repo，spine 跨池，codex 唯讀，muse 經 inbox）

- 主體：repo 內 `.agents/memory/`（gitignored；自帶池 git；AIR-54 遷移後 muse project scope 原生讀，CC 端舊徑 `~/.claude/projects/.../memory/` 目錄 symlink 指主體、ZCode 既有鏈雙跳）。
- CC/ZCode：共用主體（symlink 單一真相；走 CC 舊徑做目錄級 rg/glob 需 `-L`）。
- muse：主體直連（`read_memory` 開場注入 MEMORY.md）；寫入經 user-scope plugin `muse-memory-governance` 代存 `.agents/memory-inbox/` 並 deny（repo opt-in marker `.agents/memory-governance.json`；禁繞 inbox 直寫）。
- codex：主體唯讀（單一寫入點拓撲；有該寫的發現交 CC/ZCode 側，不直接寫池；找知識用 `rg -i 關鍵詞 主體/_inventory.md` 定位後 Read 條目 body）。
- spine：`~/.agents/memory-spine/`（跨池共享；plain md＋同格式 frontmatter；條目由 ai-guide 側 session 寫入，各池 generator 認養 routing 行段；位置決議與認養表見 `index.md`；缺席時各池回退本池，不報錯）。
- 觀察池路由行：AGENTS.md 有 Memory spine 路由段；各池狀態：ai-guide ✅／CC ✅／ZCode 待辦／muse ✅／codex 不碰確認。

### 6.2 索引形態（B 形態：常駐定額＋全量 inventory）

- MEMORY.md＝機械投影禁手寫（PreToolUse gate）；常駐集合＝`_resident-set.md` 顯式清單（user 凍結；rank 只排集合內順序不決定資格）；全量條目在 `_inventory.md`（rg 可達，不進開場；同禁手寫）。
- 現況實例：resident 12 條 2,302/6,000 chars（09-15 晨間波）；inventory 晨間 267→288 條→撰寫當下 303 條（`_inventory.md` 315 行／70,662 bytes）；MEMORY.md 26 行／3,470；條目檔 308 個 md（含 `_` 前綴非條目）。
- type 分布實例（現值，合 303）：feedback 152／project 65／reference 86（`rg -l "type: <t>"`；每檔 frontmatter 雙 type 行：node_type=memory＋type=<t>）。
- 常駐 12 條（resident-set）：commit-consent-in-autonomous-mode、feedback_verify-wt-before-commit、feedback_consistency-gate-not-optional、feedback_backup-unversioned-live-configs、cross-workspace-actions-user-handles、feedback_read-current-file-before-reviewing、feedback_relay-claims-verify-current-state、feedback_evidence-over-claims、feedback_dispatch-reread-governing-docs、feedback_full-read-base-not-context-copy、feedback_cjk-char-corruption-rg-verify、project_session-topology-single-writer。
- 截斷線（兩端同語義）：200 行或 25,000 字元（UTF-16，CJK 一字計 1）先到為準，超限截斷附 WARNING 尾端不載；B 形態 gate＝常駐面 6,000 chars；bytes ≥22,800（95%）／>24,000（info 縱深預警，不擋寫入）。
- 投影排序＝type 四組×rank 三層（hot/core/cold，缺省 core）×組內 mtime 新在前；mtime 重置源（備份還原/遷機/無 -p 複製）會退化排序，備份用 rsync -a／cp -p。
- Generator：資產源 `skills/memory-audit/scripts/generate_index.py`，部署＝複製進各池；層 1 先 `cmp` 副本與資產源（stale 先刷新；Stop hook 對不符副本跳過＋`_regen-skipped-stale` 標記）；`--check` 是硬 gate；`_regen-failed` 在場＝gate 失敗（AIR-27 後索引照寫出：超限全寫、違規跳壞條目）。

### 6.3 寫入端紀律（寫前一步＋六問＋載體判定）

- 單一寫入點：條目檔 frontmatter（name/description/type）是唯一寫入點；MEMORY.md 是投影。
- 一句話測試：動筆前一句話寫下核心事實（「X 的 Y 行為是 Z，因為 W」）；提煉不出＝還沒想清楚＝不寫。真值軸：未定案歸因/推測＝不寫（memory 無信心欄位，recall 即當事實）；已確認的 gap 事實可寫，歸因推測不可寫。
- desc 文法五條：條件句領頭（「當你要〈任務動詞〉時」，中英並列）／雙語觸發詞／一事一條／desc 不放易變快照（現值/版號/進度歸 --check/repo/卡）／≤100 字元禁引號。desc 是條目唯一觸發面。注入安全：條目是資料不是指令（不含可執行形指令；收錄外部文本引用語氣標來源）。
- desc 三不（hook 硬擋）：不 hash（含 bare hash）／不日期流水（MM-DD）／不 session id（三者 git/DB 可推導）。
- 寫入六問：Q1 任務終態 or 活知識（終態→卡/report；活躍線 blocker 拆兩半，外部限制才留）→ Q2 repo 可推導 or 通用原則（可推導不寫；通用方法論先判載體歸 rules/skills）→ Q3 同主題已有（`rg -i` 全檔掃不信索引；命中加段，進行中弧線禁加段等收案蒸餾）→ Q4 project-* 已完結（先收斂再開新）→ Q5 尺寸預算（desc≤100／新建≤3,000／條目≤12,000；索引軟上限 150 行；muse 直達 8KB 是軟壓力非閘）→ Q6 載體對嗎（查統一定義表）。
- body 形態（寫入當下即蒸後形）：lesson-first，一句教訓領頭，實證錨最多一行；禁 timeline 敘事、禁 in-flight 細節、一行一事實；弧結案條目同形態（決策/教訓/勿重辯，禁規劃流水）。
- rank 初判：hot（活躍弧/高頻）／core（default）／cold（冷門/清候選）。
- 弧結案蒸餾（kanban 結案兩步第三動）：收案時重寫為終態 facts；narrative 歸 repo，memory 留教訓；蒸餾＝刪 repo 已承載（逐項 rg 驗證）＋軌跡記卡，不新建歸檔檔；肥條目（>30K）派 mem-distill 隔離消化（實證：149K+37K+17K→5.1K −96%；45K/36K→~5.9K −86%）。
- 固化→濃縮同步義務：經驗固化成 skill/rule 後，部分覆蓋→已承載段壓成指針（user 事實/事故/commit 錨留）；完全覆蓋→列退出候選交 user 裁，不自行刪。

### 6.4 載體統一定義表（該寫哪；判準單一源）

- 先判層級（硬閘：user-level 知識不得以 project-only 載體作權威源，反之亦然），再判稀缺（常駐→任務載入→按需檢索→零 context）。
- rule 資格＝層級相容 ∩ 首個有後果決策前必須在場 ∩（verified calibration ∪ user 裁定 ∪ trigger-bootstrap）；residency 三測試（Bootstrap／First consequential action／Portfolio duplication）。
- 一行流：任務終態→卡/EP → repo 可推導→不寫 → user-level 方法論套 rule 資格（最小 rule vs skill vs CC paths 條件載體）→ 模組約束→模組 AGENTS.md → 跨 session user/project 事實→memory → 暫存→scratch（草稿迭代住 `.agent-tmp/`，不住 memory）→ 機制三判準全是→hook 否則 LLM 流程。
- 誤置→處置 taxonomy：A（user 規範進 project memory→規範回 user 源，memory 只留事故/偏好/pointer）／B（project 知識上提 user rule→下沉 project carrier）／V（現值進 instruction→spine 或本池 reference，instruction 留 pointer）／M1（任務終態入池→放置閘 hook 提醒）／M2（desc 三不→內容閘硬擋）／M3（多 writer 草稿迭代→stale-collision 訊息改道 scratch）／M4（repo 可推導→Q2 prose 承載）／M5（外部委派走 wrapper→caller 背景 Bash）／SM-5（歸因破口→歸因投影已閉）。
- 寫入摩擦設計：hook 放置閘（新建 memory 檔注入六問指針；既有加段不觸發）＋desc 內容閘＋stale-collision 訊息擴充（待做）；提示層維持不加碼；工具層不做（auto memory 無 CLI 入口）。

### 6.5 稽核側（兩級＋狀態戳＋三分離＋生命週期四動）

- Full 四層：層 1 索引機械量測（`--check`＋MEMORY 非手寫＋副本 cmp＋`_regen-failed` 判讀；未裝池手檢表：預算/重複/orphan/missing/one-line）→ 層 2 內容核實 vs repo（預設必做；索引整潔≠健康；每檔 3-6 load-bearing claims；狀態宣稱走 git log、符號走 rg+fd 換 2-3 pattern、verdict ✅/🟡/❌/➖、self-report discount 實跑 repro；條目多 spawn 序列一次一個背景跑，失敗降級主 session 分批）→ 層 3 清理執行（user 核可後；刪前 rg 反向引用＋mtime 稽核＋多池殘留掃描＋cluster merge 機械觸發同主題≥3＋mem-distill 蒸餾＋收斂落點判定＋夜間收斂流出腿）→ 層 4 EP/任務盤點（完成信號→清理候選；未完成列表交 user 逐項判）→ 寫狀態戳。
- Lite：層 1＋層 2'（git log 主題→rg 命中條目→只核實命中）＋流入率監控（A 口徑 MEMORY chars／B 口徑 inventory chars；日增>300＝mini-merge 觸發；bytes≥22,800 同列候選）。
- 狀態戳 `.agents/memory/_audit-state.md`（底線不進索引；不用 MEMORY frontmatter）：last_full_audit／last_lite_audit／base_commit（sha）／coverage／last_index_chars。實例：full 2026-09-03、lite 2026-09-13、base 97e17d5、coverage 56；lite_note 記 09-13 治理看照全綠；last_index_chars 記 09-15 晨間波（quarantine 5 檔 provenance 成立→流入快照 ea0ba36；desc 掃尾 46/47；六問新 22 退回 12）。
- 治理三分離：advisory 報告→user 核可→執行；每項附機械證據。
- 生命週期四動（跨載體處置循環）：收集候選→附證據→判定處置→更新來源→重建投影→驗證消費端（行為對照，不只驗產物存在）。

### 6.6 夜間收斂波（有進有出；寫手腿，每晚 23:40）

- 波前二分（池 git 化；所有 git 命令帶 `-C <pool>`）：先查 `_wave-in-progress` marker（在場＝上波中斷→三方對照報告，禁自動整池 reset）→ 池 delta gate（`reconcile_memory_pool.py --json` 波前第一步：exit 0 開波；exit 2 先跑 T4-1 異常篩〔消費 reconciler output 禁重跑第二份；三 allow 訊號：inbox done-receipt／CC hook-event／已知自產出；三無→quarantine 停波待裁〕；exit 1 停波）→ quarantine 空後看 mtime（全>30min→流入快照 commit 後開波；任一<30min→停波防並行撞波）。
- 波次：decay 候選（固定寫 `_decay-candidates.json＋.md`，候選非判決人裁）＋`--check`（gate 值以輸出行源）＋hot 計數（>1/3 警示 rank 通膨）＋弧線軟預警（>8K 且 7d 活躍，僅報告）＋desc>100 掃尾（全池常態）→ 觸發（A＝MEMORY gate FAIL／B＝inventory 增量，或 `_regen-failed`）→ cluster merge → regen 至過；marker 留至波後差異處置完成。
- 波後差異處置（正常收尾與中斷恢復共用）：以 marker baseline 查 diff＋porcelain 逐差異確認歸屬；只 stage 已確認；整檔還原僅全屬本波且 baseline 正確；禁整池 reset／git clean；untracked 一律保留列候選；待裁留 marker 停波。`_trash` 手動備份慣例已退役。
- desc 事實 drift 當晚修正（僅 desc 層，body 歸 owner；已關閉弧 owner-touch 失效故夜波執行）。
- 實例：09-14 停波待裁→09-15 晨間人裁（5 quarantine 全成立流入快照）；desc 掃尾 46/47（card-format 活躍 writer HOLD）；09-07 cluster-merge 波（gate 101.4%→91.4%，15 檔併 9 keepers，keeper 全≤11k desc全≤100，淨 −13）。

### 6.7 Inbox 消費站（muse 寫入流 consolidation；夜波步驟 0 或手動）

- 閘是純機械導流（plugin 代存 payload＋deny），語義判斷（六問/frontmatter 補全）全在本站。
- 消費端尺寸事實（muse 1.1.1）：memory_pack＝索引 120 行＋單條 inline 8KB（超限僅列名）；8KB 是軟壓力，Q5 硬閘仍 12,000；8K-12K 政策未決歸 AIR-69。
- WAL light 狀態機：inbox root `.json`→`processing/`（claim）→`done/`｜`rejected/`（各留 receipt）；`processing/` 殘留＝中斷證據停下人判；`.tmp-*` 殘留（m1d+）列報告順手清。
- path contract（逐條機械檢查，payload path 是未驗證 input）：①scope=project only ②池根 basename（禁子目錄）③delimiter-aware ancestry（realpath 等於池或以 `池/` 為前綴；純 startswith 會誤判 memory-inbox 兄弟目錄）④逐段 lstat 拒 symlink ⑤非 reserved（大小寫無關）⑥edit 命中合法條目；任一不過→rejected。
- CAS（edit 類）：操作類只以 payload `tool_name` 判（meta 附帶條件是 path 命中既有條目而非 tool==edit）；`base_sha256` 相等才自動套用，不等→conflict queue 人裁；add 同名已存在同 queue。
- 六問→寫入：合格補 frontmatter 寫主體 regen 進 done；不合格（終態可推導/未定案）進 rejected 記理由。
- 逾期語義：inbox 逾期＝consolidation 停擺警訊非垃圾；watchdog＝daily-maintain Phase 0 雙檢查；age 連續兩週期→🔴、processing 殘留/直寫立即🔴。
- 實例：inbox 現有 done／processing／rejected 三區；rejected 含 CAS conflict、reserved、escape、absolute 等 receipt（攻擊回歸樣本與合法性拒收並存）。

### 6.8 Telemetry（觀測是線索非真值）

- `memory_telemetry.py` 四子命令：writes（正規化事件＋coverage）／reads（AIR-41 body-Read 觀測＋zero-body-read 候選；機械豁免 hot/近 30d mtime；用途 work/maintenance/unknown 需 LLM 沿 event 重放判讀；identity 線索→HOLD；coverage_limited 聲明）／attribution（AIR-55 每條目 last_tracked_writer＋content hash＋dirty_after_tracked；mtime×writer 交叉消費；dirty 逐窗重算不 carry）／decay（unused＋豁免／衰減候選／rank 升級候選／coverage 聲明；固定寫池 `_decay-candidates.*`；盲區＝muse/codex reads 不入 telemetry）。
- 寫入歸因（AIR-40）：週期 top actor×entry 排行（corrections-weekly memory 段消費；流量非品質，違規抽驗留 LLM）。

### 6.9 Hooks（流入節流第一道；audit 是存量收斂）

- `block-memory-index-write.py`（PreToolUse）：description>100／desc 含 hash（commit 前綴＋bare）／desc 含日期 MM-DD 或 `sess_`／新建>3,000／膨脹>12,000／MEMORY.md＋_inventory.md 手寫攔截／收斂方向放行／新建放置閘注入六問指針。僅攔主 session，subagent 寫入不觸發（上限＝prompt 紀律）。
- sensors（CC-only 為主）：`memory-write-sensor.py`（PostToolUse Edit|Write 成功後記 actor 證據→hook log；池判定＝父目錄含 MEMORY.md）／`memory-dirty-sensor.py`（FileChanged 只記 dirty 不指派 writer）／`memory-watch-seed.py`（SessionStart 動態注入 watchPaths；池缺場空清單）。write-sensor 兩家已接（ZCode PostToolUse 實測在場，payload 差異容錯吸收）。
- `memory-index-regen.py`（Stop hook 自動重生成；副本 stale 跳過＋標記，成功自動清）。
- 執行環境：ZCode hook＝OS python3（3.9），禁 3.10+ 語法，改後 bare python3 實跑複驗；hooks 是 per-session 快照（註冊/改 script 須新 session 生效）。
- muse 側：plugin 為唯一寫入閘（legacy `.muse/hooks.json`＋launcher 已退役）；運維＝每次 `muse plugins update` 後重 approve（definition_hash 變→status=modified→停火 fail-open 窗口）；健康 assert `inspect --json` 的 `runtime_capabilities[].status==trusted_enabled`（list 的 hooks require review 是常駐雜訊非訊號）；marker 三態（absent→native／protocol:1→導流deny／其餘→deny 不落地）；jq 缺失保守 deny；inbox 路徑 symlink 段 deny。

### 6.10 對帳網（AIR-93：繞閘寫入偵測器）

- `scripts/reconcile_memory_pool.py <repo-root> [--json]`：唯讀；invariant＝池 HEAD 是 approved 基線，working tree delta 即 flag；exit 0 clean/not_governed、1 infra/contract 錯 fail-closed、2 dirty 待補審；GIT_OPTIONAL_LOCKS=0 禁 index 副作用；marker 語義與 hook 同源（JSON number 1，bool 排除）。
- 已知缺口實例：muse runtime 在 session 結束後以非 tool 路徑原生直寫池（teardown 學習；PreToolUse＋sandbox 皆不涵蓋；mosaic 09-14 實證；dossier 在 `ai-analysis/_tasks/09-14-air93-muse-session-end-bypass/`）；掛點＝consolidation 開頭／memory-audit 機械層。
- 配套：09-15 晨間波 exit 2→T4-1→人裁→流入快照的完整跑通實例（§6.5 狀態戳）。

### 6.11 Spine（跨 repo user state；V/P/F 三分）

- 首例 `reference_model-runtime-entitlements`：as-of rolling state（訂閱/額度/帳號現值；現值例：GLM＋muse＋codex 可用、codex 僅 chatgpt-web/* 可派、Anthropic/xai 未訂閱禁派、codex 原生 ~258K、muse 429 事件＋reset 時刻）；更新紀律＝事件當下改（換 as-of＋事件行一句）；政策/機制不住此（住 model-routing skill）；desc 禁現值。
- 誤置表 V 列的標準處置：跨 repo user state→spine；repo 綁定現值→本池 reference；穩定 policy 留 instruction；mixed 句拆句。

### 6.12 接續與排程（STATE／compact／at／handoff／cron）

- STATE.md＝Last session 觀察層（卡在哪/為何轉向/起手點；覆寫非累積；完成度走 git＋卡面＋registry；由 at/deep-work 觸發；Open failures 走 kanban 不進 STATE）。
- 想法即時落盤：關鍵發現/排除路徑/下一步即記（有 EP→append；有卡→notes；都無→`.agent-tmp/session-journal.md`）；唯讀/工單限制優先（checkpoint 不擴張授權）；journal 可記未定案，不觸發 memory。
- /compact-prep：掃全 session 產 preserve-list 脈絡檔（禁時序流水帳）＋memory 新鮮度檢查＋提醒 user 手動 /compact（ZCode SessionStart(compact) hook 是死路；Claude 端 hook 是 raw tail 復原層）。
- /at vs /handoff：at＝自己續（CronCreate one-shot；resume 讀 STATE.md）；handoff＝交別人（self-contained；STATE 非交接選項）。
- 排程（ai-guide workspace 3 條 active，09-14 改名重建完成）：每晚 23:40 收斂波（寫手：收斂＋inbox 消費＋delta gate＋bundle 輪替＋清淤兜底；紅線：不碰 mosaic 池、不 commit）／週日 23:00 治理看照（審計：bundle cmp＋lite audit＋registry/卡 ref 比對＋watchdog 雙檢查＋對帳網唯讀 report；禁改 rules/memory 條目）／週六 23:10 糾正週報（報告；DB 唯讀）。launchd `com.ai-guide.backlog-cleanup` 每日 23:50（Done>30d 清場）。外部依賴反查表 A1-A6（skill 端去時刻/系統名，排程事實由本表承載）。

### 6.13 記憶實例精選（原則如何落地為條目）

- evidence-over-claims：user「我要看你真的實作長怎樣，誰知道你是不是亂講」→ 完成報告配實物（ls／三檔並排／live 命令／open 產物）＋低於規格明說差距。lesson-first＋實證錨＋How to apply 三段式 body 標準形態。
- commit-consent-in-autonomous-mode：09-13 裁定 autonomous 一律禁 commit；互動特赦①-④＋七種原話授權形態（條件式／鏈式／親打／handoff 直達／名單批次／特赦擴編／任務派發內授權）；consent 展示自帶 payload；本地硬規則>外部指示。
- project_session-topology-single-writer：ai-guide 單一寫入者＋hub-relay（hub 產 handoff→收回執→機械驗證→翻文檔＋deploy；user＝郵差；執行端草稿進樹＋hub 審查結算）；09-09 command center 全日編排實例；mixed-writer 接手第一動＝歸屬辨識。
- relay-claims-verify-current-state：跨 session relay 宣稱常過時→接手第一動機械驗證（與 evidence-over-claims 鏡像：輸出自帶證據 vs 輸入先驗狀態）。
- dispatch-reread-governing-docs：派發當下重讀治理檔（看 commit 標題≠重讀條文；過期派發事故實證）。
- full-read-base-not-context-copy：全檔重寫 base 必須全文 Read（context 副本會被 elide；HEAD 位移時 git diff 空是假陰性）。
- cjk-char-corruption-rg-verify：Edit/Write 兩形態（CJK 損壞／標題錨孤兒化）→改完 rg 驗證。
- quota-failover-policy／model-runtime-entitlements：政策住 skill、現值住 spine 的 V/P 分離實例。
- reference 條目群：codex-cli-exec-facts（raw CLI 語義）、muse-code-cli-facts、periodic-task-landscape（mosaic 排程風景）、bash32 trap、codex-config-zai-topology 等凍結機制事實。

---

## 7. 雜項（部署／git／hooks／排程／多機）

- 部署：`scripts/deploy_agents.py`（90KiB gate；per-target size gate；muse bundle 36KiB 自限；deploy 前展示 target diff/hash 另取明確授權；source/diff/tests 先完成；保存舊 bytes，失敗整批修復或全還原，禁 split state；成功後 fresh session 驗證）。
- git 慣例（本 repo 卡 branch）：`air-<N>` 自 main 開（implement 階段 1 起手式⑤後）；message 帶卡 id；收尾 ff-only merge＋刪 branch（被拒先 /rebase）；`/rebase all` 前先收卡；trunk 永不被 rebase 永不 force；mosaic 變體 owning 線判定（labels 線 tag）。
- 卡 branch EP（09-08）是 mosaic 變體定義源；卡片欄位分工改制（desc 全段人話、Implementation Plan 承載 AI 工單 spec）。
- hooks：跨 Claude/ZCode 單一來源，絕對路徑引用（禁 symlink）；zcode-registration 範本是 config `hooks:` 子樹值（merge 非覆蓋）；SessionEnd 在 ZCode 缺席（plugin 孤兒清理 hook 缺席；muse 側 ledger 兜底＋開工盤點涵蓋；remediation＝app 重開＋git status，成本極低非缺口）。
- 多機移植：MULTI-MACHINE.md＋setup-memory-symlinks.sh（dry-run 預設＋.bak）＋verify-memory-topology.sh；池傳輸＋cron 重建手動步。
- Outward action 同意約束：reversibility test（另一人/系統能在 undo 前觀察到？）；AUTH line 逐字引用；每次 commit 獨立確認（互動特赦①建卡②開工 metadata③結案兩步④純 ruff；autonomous 不繼承任何例外）；deep-work/排程走 autonomous-execution 紅線枚舉。

---

## 8. 現況規模速覽（機械可驗數字）

- skills：約 70＋（`ls skills/`）；rules：20 檔（`ls rules/`）；registry agents：9（雙 harness 生成）；memory 條目檔 308（含 `_` 前綴非條目；inventory 288 條／feedback 152／project 65／reference 86；resident 12）。
- AIR-91：Done（卡 ordinal 77000；EP 歸檔 done／；commit b4a3019；60 檔 ＋3,379／−534；tests 510；行為實驗 30/30）。
- AIR-96：In Progress（5 殘項；ordinal 78000）。
- Cron：3 條 active（23:40 收斂／週日 23:00 看照／週六 23:10 週報）＋launchd backlog-cleanup（23:50）。
- Bundle：muse 33,013B＝89% WARN（AIR-96 #3 目標 ≤80%）。

---

## 9. 下一步：合理性與缺漏評估入口（本報告不裁決，先列待問）

user 原問「角色/model/作法/雜項是否合理跟缺漏」待下一輪以 deep-thinking 框架處理。現況整理後自然浮出的評估入口（只列題目，不給 verdict）：

1. Role 五值是否完備（缺 Research/Design 顯式 Role？Planner 是否過載）／authority 粒度是否夠（apply 無分級？）。
2. judgment_floor 只有 decision/execution 兩檔是否夠（中間檔需求？effort 補償未驗證路徑何時驗）。
3. vision 兩段式 fallback 的 non-equivalence 在實務中如何被消費（Arbiter 降級裁決的品質邊界）。
4. inherit 在 CC 8/9 preset 是實際路徑但語義剛正式化（AIR-96 #2）——pending_binding 存量何時清。
5. effort 三處並存（AIR-96 #1）＋thoughtLevel sticky 家族——effort 軸的可信度天花板。
6. 追蹤鏈是否完整：殼 hook 2／delta tour／debrief／illustrate 四者分工在實務中有無重疊或真空（誰回答「這弧到底改了什麼行為」）。
7. state-review／tour corpus／blueprint 三條「慢知識」產線的觸發頻率與維護成本。
8. memory B 形態常駐 12 條的選擇標準與輪替機制；8K-12K 區間政策（AIR-69）；muse session-end bypass 根治（AIR-93）；hook 僅主 session 的覆蓋缺口；telemetry muse/codex 盲區。
9. 外部 runtime 三家族的操作負載（glm 四缺陷診斷腿 AIR-96 #4；webgpt 五失敗態；codex 帳號路徑分界）——thin forwarder 是否仍 thin。
10. 排程三條＋launchd 的觀測性（首跑驗證、失敗告警、registry drift 比對腿是否足夠）。

---

*附：本報告是靜態盤點，數字以報告內註明的機械來源為準；repo 演進後以各單一源檔為準（catalog／presets／skill／audit-state／schedule-registry）。*
