# AIR-91：依工作階段能力自動選擇模型 Execution Plan

> **ep_type**: implementation  
> **baseline**: `df3741b81e90dad01ed30fb383750ad55630998d`  
> **任務卡**: AIR-91  
> **需求來源**: `backlog/tasks/air-91 - model-派工詞彙整體治理——vision-旗艦-最強檔三題軸清理（先整體討論再動手）.md`  
> **研究底稿**: `ai-analysis/_tasks/_archived/09-15-model-capability-routing/references/research.md`

## 進度節

- [x] UC 與架構方向經 user 確認
- [x] AIR-91 卡片正式 spec 已更新
- [x] 全域研究與 current-source ripple 盤點完成
- [x] 三個 native reviewers、Muse 與 GLM 5.3 外部 reviewers 已完成
- [x] 主 session 已裁決 findings 並回寫計畫
- [x] Report Shell hook 1 已以本版 EP content SHA 建立
- [x] S1–S4 實作完成（2026-09-15）：S1 catalog/resolver protocol＋S2 presets/projection 等價切換＋S3 work-unit doctrine 十二檔＋S4 manifest/gate/導航收斂——S1–S3 各過 scoped judge（修補已落地）；S4＝機械 gate＋coordinator 裁定（外部 review 腿覆蓋）
- [x] Behavior experiment（B 方案縮減）：IT-01/02/04/07/08 × 雙 arm × 3 reps＝30/30 PASS、0 FAIL（manifest=`references/instruction-testing.md`）
- [x] Deploy：三 harness user-level bundle 已部署＋fresh-context 載入驗證（user AUTH 2026-09-15）；收斂鏈（codex/muse review→5.3 judge→commit）進行中

## 實作總覽

### User Story

作為只想啟動既有 execution-plan、implement、judge-review、post-build 工作流的使用者，我要系統依每個階段真正需要的判斷能力、任務 qualification、原生影像、獨立 provider 與執行權限自動選擇 model binding 和 carrier，使高判斷工作不被額度或 seat 限制靜默降級，一般實作和機械查證也不浪費 decision-grade model。

### 問題

現行 `role → full/lite/vision → model` 把不同概念壓進單一 tier：

1. `full/lite` 同時被理解為任務要求、模型強度與成本檔。
2. `vision` 實際是 capability filter，卻與強度列並排。
3. Role、registry agent、model、provider、main/subagent seat 與 external carrier 在多份表格中交錯。
4. 同一 workflow 內已有不同能力 work units，但 `post-build=full` 等寫法容易被誤讀成整條鏈只用一個 model。
5. model qualification 可能依 dispatch token、carrier 與 effective effort 改變，不能綁在裸 model 名稱。
6. 個人訂閱與 quota 是快變狀態，混進穩定 routing doctrine 必然腐爛。

### 目標解析鏈

```text
workflow phase
  → WorkUnitContract（Role／authority／hard requirements／independence）
  → Resolver protocol
  → Candidate = ModelIdentity × DispatchBinding × effective effort
  → RuntimeCompatibility
  → AvailabilitySnapshot
  → ArcOverride／RoutingPolicy（只排序合格候選）
  → DispatchPlan（ExecutionPreset＋Carrier）
  → work-unit-local DispatchTrace
```

### 詞彙與 ownership

| 元件 | 唯一職責 | Source of record | 不擁有 |
|---|---|---|---|
| Workflow／Marshal responsibility | phase 順序、轉移、retry、escalation、停止條件；產生 WorkUnitContract | 各 owning workflow skill 的 phase rows；共用欄位語義引用 model-routing | model 選擇、findings 裁決 |
| Role | 責任與可持有 authority；首期為 Planner、Implementer、Reviewer、Verifier、Arbiter | `skills/model-routing/SKILL.md` glossary／Role→authority allow-list | model、provider、seat、tools |
| WorkUnitContract | work unit 的 Role、authority、qualification、judgment floor、required capabilities、surface、independence、escalation | owning workflow skill | model supply、availability |
| ModelCatalog | 穩定 ModelIdentity、capabilities、qualification status 與 evidence source | `skills/model-routing/catalog.toml` | Role、work-unit demand、quota、registry preset |
| DispatchBinding | carrier/surface 可用 token、token kind、effort encoding、transport capabilities | 同一 catalog 的 binding section | work-unit authority、即時可用性 |
| ExecutionPreset | harness 的 tools、read/write、sandbox、background 與 deployment default binding | `agents/presets.toml` | Role 指派、runtime routing policy |
| Resolver protocol | 依本表順序形成 DispatchPlan；它是 LLM instruction protocol，不是 `sync_agents.py` 的 domain service | `skills/model-routing/SKILL.md` | workflow phase 定義、供給 facts、volatile state |
| RuntimeCompatibility | `(model identity, binding, carrier, surface)` 的穩定相容性與 hard transport capability | catalog binding＋model-routing provider/runtime contract | quota、偏好 |
| AvailabilitySnapshot | `available/unavailable/unknown`、source、observed-at/freshness、failure family、retryable-at | 每次 dispatch 從 memory/spine／runtime probe 形成的輸入 | qualification、policy |
| ArcOverride | user 當弧指定的 candidate constraint／排序優先權 | 本次對話／work order | hard requirement、runtime fact |
| RoutingPolicy | 合格且可用集合內的穩定排序與 failover policy | `skills/model-routing/SKILL.md` | capability truth、availability observation |
| Carrier | main session、native registry agent、bridge 等執行機制 | agent-workflow／bridge contract | Role、authority |
| Subagent | DispatchPlan 執行後的 runtime instance | runtime | 概念 Role 或 policy |

`Arbiter` 是 Role 值；`judge-review` 是執行 `Role=Arbiter` 的 workflow adapter。`Marshal` 是 composite workflow 的 orchestration responsibility，不是 Role、agent 或 skill。裸詞 `Execution Profile` 不再新增；`ExecutionPreset` 專指 harness deployment adapter，`profile` 保留給 external runtime 的 `implement/review/advisory` transport mode。

### Resolver 的規範邊界

本弧不建立跨 harness 的 Python runtime router。provider availability、native spawn 能力、bridge failure 與 user 當弧指示含語義判斷，強行機械化會製造另一個不完整 resolver。正式 resolver 是 `model-routing` skill 的 instruction protocol；TOML 與 `sync_agents.py` 只承擔可機械驗證的 supply、binding 與 deployment projection。

```text
resolve(
  WorkUnitContract,
  ModelCatalog,
  RuntimeCompatibility,
  AvailabilitySnapshot,
  ArcOverride,
  RoutingPolicy,
  DispatchTrace,
) -> DispatchPlan | DecompositionPlan | NoCandidate
```

`sync_agents.py` 只把 `agents/roles/*.md + agents/presets.toml + catalog binding` 投影成 harness registry；不得讀取個人 memory、執行 availability probe、選 runtime fallback 或擁有 workflow qualification。

### 已定設計

1. 不新增「最強檔」tier，也不建立單一模型排行榜。model 是否合格由 workload qualification、binding、effective effort 與 evidence status 共同表示。
2. `judgment_floor` 首期只有 `decision`、`execution`，且 `decision` 可滿足 `execution`、反向不可；effort 不能把未 qualification 的 candidate 補成 decision-qualified。
3. `native_vision` 是 ModelIdentity capability；真正可派的 direct visual candidate 還必須有 DispatchBinding 的 `image_transport` capability。
4. 首期 workload qualifications：`ep_synthesis`、`adjudication`、`implement_from_accepted_ep`、`evidence_retrieval`、`review_findings`、`visual_observation`。
5. qualification 使用兩個正交欄位：`status={qualified,conditional,unqualified}`；`evidence_source={user_observed,repo_observed,official_documentation,pending_first_use}`。`conditional` 是資格狀態，不是證據來源；availability 不得出現在任一欄。
6. GLM 5.3、ChatGPT Web High、Sol medium-high、Astra、Opus、Fabel 對 EP synthesis／judge 先記為 `qualified + user_observed`；Muse Spark 1.3 為 `conditional + user_observed`，並綁適用 binding／最低 effective effort；GLM Flash 對 visual observation 為 `qualified + user_observed`。
7. 高推理＋影像沒有單一合格 candidate 時，兩段式 fallback 為正式 decomposition：visual-qualified observer 看原圖，decision-grade Arbiter 只消費 observation artifact；輸出保留 source identity、不確定項與 `arbiter_viewed_source=false`，不得宣稱等價於單模型原生視覺裁決。
8. Role 只由 WorkUnitContract 指派。ModelCatalog、ExecutionPreset 與 registry slug 不取得概念 Role ownership；既有 role-like slug 首期保留為 compatibility adapter。
9. 穩定能力、binding、provider/runtime mechanism 和 routing policy 留 ai-guide；訂閱、帳號、quota、reset、暫時 availability 與當弧偏好留 memory/spine 或 dispatch input。
10. 既有 pins 和常見 dispatch 結果先保持等價；新增的兩段式 visual fallback、source-delivery receipt、dispatch evidence 與 fail-loud gate 是預期行為增量。

### 替代方案裁決

| 方案 | 裁決 | 理由 |
|---|---|---|
| 只保留散文 resolver，不建 catalog | 不採 | 無法機械區分 provider-native ID、harness alias、carrier slug、effort encoding，也無法讓 generated registry 與 model facts 做 parity；這正是現行 drift 的來源 |
| catalog 同時放 model、work-unit、Role 與 presets | 不採 | supply、demand、authority、deployment 變更原因不同，會形成雙寫與 false green |
| 中央 mega lifecycle table 擁有四個 workflow 全部 phase rows | 不採 | 共用 schema 應中央化，但 phase 轉移與 work-unit demand 必須由 owning workflow 自治；中央表只做導航投影會再次複寫 |
| supply catalog＋workflow-owned demand＋preset adapter＋instruction resolver | 採用 | 機械 facts 可對帳，語義決策留在正確 adapter；使用者仍只呼叫原 workflow |

### 相對複雜度與風險

- **相對複雜度：高**。核心難點是拆 model supply、workflow demand、deployment preset 與 volatile state，同時保住三 harness registry 與現有 routing 行為。
- **主要依賴**：S1 vocabulary／catalog → S2 projection → S3 workflow consumers → S4 convergence。S2/S3 只在 S1 schema 定稿後開始。
- **高風險**：qualification 未綁 binding/effective effort、workflow/preset 雙寫 demand、固定 registry pin 掩蓋 escalation、override 繞 hard gate、quota retry loop、image 未真正送達 Arbiter 卻自報已看、歷史報告被 current-doctrine gate 誤掃、partial user-level deploy。
- **不採 Blueprint**：四段皆有可獨立驗收的垂直結果，不需各自衍生完整子 EP。

## 段落 0：全域研究

完整證據見 `references/research.md`。本節保留會影響實作的結論。

### 可複用基礎設施

- `scripts/sync_agents.py:83-188` 已有段落解析、role requirement 與 pin parity；`252-431` 已有 registry render、expected projection、zero-write check/map、collision guard 與 atomic apply。
- `tests/test_sync_agents.py` 已有 model pin golden bytes、未知 requirement fail-loud、tree snapshot purity、idempotence 與 real-repo parity fixture。
- `skills/scan-project/scripts/check_single_source.py` 的 `agents_projection_sync` 已把 `sync_agents.py --check` 接入長期 gate；不另造第二個 projection checker。
- `skills/post-build/SKILL.md:19-79` 已有 role chain、judge、apply、followup 和 lite verification；本弧改成 work-unit contracts。
- Python stdlib `tomllib` 可讀 machine-readable catalog／presets，不新增 dependency。

### 結構與 drift 證據

- `.code-reality/graph.db` 在場；SCIP index 與 baseline 同為 `df3741b`。
- `impact_radius` 只覆蓋 generator call graph，Markdown consumers 與 pytest 動態 loader 不在圖內；空 transitive result 不可作 zero-ripple 證據。
- 已確認 `cr-research` drift：`rules/model-routing.md:23`、`skills/model-routing/SKILL.md:64`、`scripts/sync_agents.py:33` 為 full；`agents/AGENTS.md:66` 與 `skills/execution-plan/SKILL.md:165` 仍為 lite。
- 現行 `agents/zcode/code-reviewer.md:6` 固定 pin Flash，但 `agents/AGENTS.md:41` 又允許高保護面升 full；本弧必定義 DispatchPlan 到 carrier adapter 的換載體規則。

### Current-consumer manifest

| Consumer | Disposition |
|---|---|
| `rules/model-routing.md` | migrate：always-on resolver skeleton 與 hard invariants |
| `skills/model-routing/SKILL.md` | authoritative：glossary、resolver protocol、runtime traits、policy；model values 改 pointer catalog |
| `skills/agent-workflow/SKILL.md` | migrate：只承接 DispatchPlan→carrier 與 failure handback |
| `skills/execution-plan/SKILL.md`、`skills/implement/SKILL.md`、`skills/judge-review/SKILL.md`、`skills/post-build/SKILL.md` | migrate：各自擁有 phase WorkUnitContract rows |
| `skills/ep-review/SKILL.md`、`skills/review-engine/SKILL.md` | migrate/pointer：review demand 與升級改引用 work-unit schema |
| `skills/_common/agent-review-cycle.md`、`workflow-review-pattern.md`、`work-order.md` | migrate/pointer：authority、independence、work-order envelope |
| `skills/self-contained-prompt/SKILL.md` | migrate：foreign work order 帶 contract、禁止再委派與 binding evidence |
| `agents/AGENTS.md` | projection/navigation：不再擁有 phase demand；保留 work-unit ID、preset、artifact、fallback 導航 |
| `agents/roles/*.md` | migrate：移除 tier tag；保留 neutral task behavior |
| `agents/presets.toml` | new authoritative deployment adapter source；不含 Role |
| `agents/{zcode,claude}/*.md` | generated compatibility adapters |
| `scripts/sync_agents.py` | migrate：讀 catalog bindings＋presets，保持 projection-only |
| `skills/CLAUDE.md`、root/rules/agents navigation | pointer：不重列 values |
| `tests/test_sync_agents.py`、`tests/test_check_single_source.py` | migrate：schema、equivalence、projection、manifest gates |

實作前以 broad `rg` 產完整 candidate 清單，逐檔標 `migrate/pointer/compatibility/historical`；上述是已知下限，不得當成封閉集合。

### 風險假設

| 假設 | 等級 | 驗證歸屬 |
|---|---|---|
| catalog 能承載 model identity、binding、qualification/evidence，而不吸收 demand/availability | 高 | S1 schema negative tests |
| instruction resolver 足以統一 runtime semantics，且不與 `sync_agents.py` 形成分裂腦 | 高 | S1 protocol fixtures＋S3 behavior experiment |
| registry 仍只需 materialized deployment default；動態升級可換 binding/carrier並保留同一WorkUnitContract | 高 | S2 dual Reviewer cases＋S3 carrier smoke |
| workflow-owned rows配共用schema比中央mega table更少drift | 中 | S3 manifest checker＋cross-workflow consistency |
| source-delivery receipt能區分direct visual與decomposition | 高 | S3 input-envelope micro-tests＋consumer sample |

### Negative claim 表

| type | subject | evidence | verdict |
|---|---|---|---|
| zero consumer | old `vision` tier semantics | CR不覆蓋Markdown；`rg`有多個current consumers | **否定**：不可宣稱零consumer |
| no impact | generated registry pins | 尚未有新舊resolver equivalence與golden bytes | **待驗**：S2必須證明 |
| unique source | model IDs／effort | skill tables＋copied dicts並存 | **不成立**：S1/S2收斂 |
| safe rename | registry slugs | named-agent consumers與固定pins在場 | **不成立**：首期不rename |

## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議／裁決 | 狀態 |
|---|---|---|---|---|---|
| R-01 | Important | ownership／S1／S3 | Native F3-01、Muse F1：catalog、preset、workflow三處重寫demand | supply、demand、preset三個owner分離；workflow rows為唯一demand source | implemented |
| R-02 | Important | ownership／S1 | Native F3-02、Muse F4/F7：resolver無owner，machine/prose分裂 | resolver定為model-routing instruction protocol；sync_agents僅projection；記錄窄catalog理由 | implemented |
| R-03 | Important | S2／S3 | Native F3-03：固定registry pin無法承接同Role升級 | DispatchPlan→carrier adapter定named preset／spawn override／main-or-bridge三路 | implemented |
| R-04 | Important | glossary | Native F3-04、Muse F2：Arbiter/Judge/Profile/Carrier混義 | Arbiter為Role；judge-review是adapter；Marshal是responsibility；保留external profile舊義 | implemented |
| R-05 | Important | S1／S3 | Native F3-05、F5-03/F5-04：availability、override、policy、attempt混合 | tri-state snapshot、override只約束排序、work-unit DispatchTrace與bounded retry | implemented |
| R-06 | Critical | S1 | Native F1/F2、Muse F3/F4：裸model qualification漏binding/effective effort，native ID無法容納三種token | ModelIdentity／DispatchBinding／effective effort組candidate；token_kind與effort encoding明列 | implemented |
| R-07 | Important | S1／S2 | Native F3：Role又被catalog preset擁有 | catalog/preset禁normative Role assignment；Role只來自WorkUnitContract | implemented |
| R-08 | Important | 段落0／S2／S4 | Native F4、Muse F5/F6：manifest、cr-research第二drift、map遷移與等價probe缺漏 | 加manifest；保留4-column map，verbose擴展；全agent等價矩陣；S1/S2原子遷移 | implemented |
| R-09 | Important | S3／S4 | Native F5、F5-06、GLM R5/R6：behavior與smoke混用，authority越權無壓力測試 | 拆5+ reps behavior experiment與單次consumer smoke；artifact schema/micro-test＋越權情境 | implemented |
| R-10 | Important | S1／S3 | Native F5-05、GLM R1：viewed-source自報，model capability未證carrier傳圖 | model native_vision＋binding image_transport；dispatcher產source-delivery receipt | implemented |
| R-11 | Important | S3 | Native F5-01：accepted EP無predicate | ledger全terminal且adopted已回寫，並由user呼叫implement；pending阻擋 | implemented |
| R-12 | Important | S1／S3 | Native F5-02、GLM R3：independence無比較對象，hard/degradable衝突 | 結構化relative_to/required/fallback；default soft-visible，user explicit為hard | implemented |
| R-13 | Important | S1 | GLM R4：qualification status與evidence source混流 | 兩欄分治並列正式tokens；availability不進evidence | implemented |
| R-14 | Important | S3 | GLM R2/R5：quota failure injection與output schemas未驗 | 加fixture failure injection與escalation/no-candidate/override micro-test | implemented |
| R-15 | Important | S4 | Native F6：mixed diff被誤寫成只跑docs-mode | code review chain先跑，control-plane docs-mode chain後跑，各自judge/followup | implemented |
| R-16 | Important | finalization | Native F7：hook 1 shell缺失 | 本次execution-plan定稿建立shell，S4只更新既存artifact | implemented |
| R-17 | Critical | S4 | Native F8：user-level deploy無授權gate且可能partial split | source/diff/tests先完成；展示target diff後取explicit AUTH；保存bytes並rollback/repair | implemented |
| R-18 | Important | S4 | Native F9：Codex對project memory唯讀 | actor-aware closeout；Codex只交接精確memory delta給CC/ZCode | implemented |
| R-19 | Suggestion | architecture | Muse F7：未評估無catalog／中央mega table | 已補替代方案裁決；保留窄supply catalog，拒絕demand catalog與中央mega owner | implemented |

GLM 5.3 follow-up review（`job-mu1z29x2-qwsjec`）在上述 findings 回寫後裁定 `ACCEPTED`，無剩餘 Critical／Important finding；其兩項可立即修正的 residual（Report Shell 進度、卡片 qualification 範例）亦已同步。

## UC 盤點

### Backlog 關聯

- AIR-91：本EP唯一追蹤卡，既有卡吸收所有UC，不新建卡。
- 舊AIR-29／AIR-43／AIR-44／AIR-76作相容性約束，不重新開卡。

### SYSTEM-MAP 影響

- repo無`SYSTEM-MAP.md`；本弧更新root／rules／agents navigation與skills index，不新建SYSTEM-MAP。

### 同主題 memory 條目（結案蒸餾範圍）

- `project_agents-registry-split-design`：完成時改成capability/binding/preset終態。
- `feedback_volatile-user-facts-not-in-instructions`：穩定policy與個人狀態分界保留。
- `project_role-vocabulary-discussion-pending`：終態後移除pending說法。
- `project_air87-skills-contract-inflight`：AIR-91 pending pointer結案時處理。
- `model-runtime-entitlements` spine：只作AvailabilitySnapshot輸入；無entitlement新事件不更新。

### 既有與更新 UC

| 能力 | 現況 | AIR-91結果 |
|---|---|---|
| role authoring→harness registry projection | ✅ AIR-29 | 保留named entry，改由presets＋bindings產pin |
| tier→provider model/effort routing | ✅但混軸 | 改成WorkUnitContract→Candidate→DispatchPlan |
| main／lite agent分工 | ✅ | 保留結果，改以qualification/authority表達 |
| GLM Flash visual review | ✅ | 保留binding，增加native_vision＋image_transport與receipt |
| entitlement state in memory | ✅ | 形成tri-state snapshot，不搬入catalog |
| 一命令按phase自動派工 | 📋 | workflow-owned work units＋shared resolver protocol |
| decision hard gate／execution escalation | 📋 | qualification、accepted-EP predicate、escalation record |
| provider-independent review | 📋 | structured independence contract |

## Scenario Matrix

| ID | 場景 | 觸發 | 預期行為 | Checkpoint |
|---|---|---|---|---|
| SM-1 | 一次啟動EP | user呼叫execution-plan | 中途不需user再選model；evidence可execution，synthesis/judge為decision | DispatchPlan＋EP ledger |
| SM-2 | 弱seat呼叫judge | execution-grade main seat | 外派decision-qualified candidate；沒有即fail loud | no-candidate／dispatch evidence |
| SM-3 | accepted EP實作 | ledger全terminal、adopted已回寫，user呼叫implement | 產`implement_from_accepted_ep + execution + apply` work unit | acceptance predicate receipt |
| SM-4 | EP未accepted／實作遇新決策 | pending finding、EP conflict、invariant、public boundary或反覆失敗 | 阻擋execution/apply，產decision escalation | escalation record |
| SM-5 | 小型證據工作 | 查file:line、rg、test | 只產evidence；面對「直接裁決/修改」壓力仍不越權 | evidence artifact，無disposition/apply |
| SM-6 | review findings | 一般或高保護面 | 同一Reviewer Role保持findings authority；model可由execution升decision | work-unit/selected binding |
| SM-7 | 跨provider第二意見 | workflow soft requirement或user明示 | `relative_to=writer`；soft缺場顯性同家族降級，user明示則fail loud | independence_degraded／jobId |
| SM-8 | 一般視覺觀察 | screenshot／diagram／UI | `execution + visual_observation + native_vision`且binding支援image transport | source-delivery receipt |
| SM-9 | direct高推理視覺裁決 | candidate同時decision-qualified、native_vision、image_transport | 原圖送達Arbiter，verdict引用同source identity | true由receipt推導 |
| SM-10 | decomposed高推理視覺裁決 | 無單一candidate滿足交集 | observer看圖→artifact；Arbiter input無raw image，只裁決observations | false＋non-equivalence＋兩腿IDs |
| SM-11 | quota/provider failure | 注入429／1308／unavailable | DispatchTrace排除或延後failed candidate，有限retry後換同contract candidate | attempts＋retryable-at |
| SM-12 | 無合格候選 | candidates exhausted | 停止並列缺失條件，不降hard requirement | no-candidate report |
| SM-13 | user指定合格candidate | 明示model/provider/family | hard filters後提高candidate優先權並echo | override receipt |
| SM-14 | user指定不合格或不可用candidate | 可用但不合qualification，或unavailable | incompatible/unavailable override；零dispatch、不暗換 | override failure report |
| SM-15 | projection | sync agents | catalog binding＋preset解析成既有pin與bytes | legacy/new equivalence＋golden |
| SM-16 | schema／doctrine drift | unknown token、漏binding、舊tier/current consumer | fail loud、zero write；historical artifacts排除 | manifest＋tree snapshot |

## 段落劃分

- S1建vocabulary、supply catalog、binding schema與resolver protocol，不改registry consumer。
- S2建deployment preset source、切generator、完成新舊等價後才移除舊tables/dicts；S1/S2不可單獨deploy或合main。
- S3更新workflow-owned demand、authority、fallback與visual envelope，不反向擁有catalog/preset。
- S4合流active consumers、兩條review/test lanes、user-level deployment gate與closeout。

## S1：Supply catalog、binding 與 resolver protocol

### Context

- **實作能力**：ModelIdentity／DispatchBinding／qualification evidence／resolver protocol。
- **前置**：已定glossary、替代方案裁決、consumer manifest。
- **依賴**：S2/S3都引用本段schema；S1不刪現行parity tables。
- **Invariant Impact**：no-silent-downgrade、token provenance、effective effort、model fact single source。

### 變更檔案

- `skills/model-routing/catalog.toml`（新增）：ModelIdentity、DispatchBinding 與 qualification evidence 的 supply source。
- `skills/model-routing/SKILL.md`：glossary、WorkUnitContract、resolver precedence 與 trace/output contracts。
- `rules/model-routing.md`：always-on hard invariants 與 skill pointer。
- `scripts/sync_agents.py`：先加入 catalog schema loader／validator，不在本段切換 registry projection。
- `tests/test_sync_agents.py`：catalog schema、negative fields、binding/effort/capability eligibility fixtures。

### 核心實作要點

1. 新增`skills/model-routing/catalog.toml`，只含ModelIdentity、DispatchBinding、qualification records與allow-list metadata；明確拒絕Role、work_unit、authority、registry slug、quota、reset、account、available-now欄位。
2. `ModelIdentity`是穩定概念key；每個wire token住binding：`token_kind={provider_native,harness_alias,carrier_slug}`、carrier/surface、token、effort encoding、transport capabilities。
3. resolver candidate固定為`(model_identity, dispatch_binding, requested_effort, effective_effort)`；qualification record必帶workload、status、evidence source、binding scope、minimum/effective effort constraint。要求effective effort但無法確認時只能conditional，不滿足decision hard gate。
4. `chatgpt-web/high`的effort由slug固定；Claude`opus`是harness alias；GLM bridge token是provider-native；三者不得塞進同一native ID欄。
5. `native_vision`住ModelIdentity；`image_transport`住DispatchBinding。direct visual eligibility是兩者交集。
6. `skills/model-routing/SKILL.md`成為glossary、WorkUnitContract schema、Role→authority allow-list、resolver precedence、RuntimeCompatibility、AvailabilitySnapshot、ArcOverride、RoutingPolicy、DispatchPlan/Trace schema的唯一instruction source；具體values指向catalog。
7. precedence：建立WorkUnitContract→qualification/judgment/capability hard filter→binding/carrier compatibility→availability tri-state→ArcOverride constraint→soft policy ranking。model/provider指定不能降低contract；若user真要降低能力，必須明說接受該work unit的degraded contract。
8. AvailabilitySnapshot的stale/unknown不得當available；需probe或顯性no-candidate。DispatchTrace至少記contract hash、candidate/binding、failure family、retryable-at與attempt disposition，禁止在reset前重選1308 candidate，retry次數有界。
9. `rules/model-routing.md`只保留always-on precedence與hard invariants，不材料化model values。
10. S1只新增catalog與新doctrine；舊skill tables保留migration marker，直到S2等價gate通過才移除，避免`sync_agents --check`中間態紅燈。

### Pseudo Code

```text
contract = workflow.create_work_unit()
candidates = catalog.expand_bindings_with_effective_effort()
candidates = hard_filter(candidates, contract)
candidates = filter_runtime_compatibility(candidates, contract.surface)
candidates = apply_availability_tristate(candidates, snapshot, trace)
candidates = constrain_by_compatible_override(candidates, override)
return rank(candidates, policy) or declared_decomposition or no_candidate
```

### 驗證策略

- RED：duplicate identity/binding/token scope、unknown enums、native/alias/slug混型、qualification無evidence、effort-required但effective unknown、volatile field、Role/work-unit/preset欄位、native vision model＋no-image binding被當direct candidate。
- GREEN：GLM native、Claude alias、web carrier slug、Muse minimum effort、Sol effort range、Flash visual binding可分別表達。
- table fixtures覆蓋hard filter、stale/unknown availability、compatible/incompatible override、decision floor、direct/decomposed visual的選擇層；runtime failure injection留S3。
- behavior contract明示instruction resolver是權威；parser tests只證schema，不高報為model品質。

### 成功標準

- catalog能回答supply與binding facts；workflow能回答demand；model-routing skill能形成DispatchPlan；任何一層都不需要讀另一層的私人state或重寫其資料。

## S2：ExecutionPreset 與 harness registry projection

### Context

- **實作能力**：tools/sandbox preset、default binding與generated registry。
- **前置**：S1 catalog schema穩定，舊表仍在。
- **Invariant Impact**：projection-only、pin equivalence、zero-write check/map、marker ownership。

### 變更檔案

- `agents/presets.toml`（新增）：registry slug 到 tools／sandbox／default binding 的 deployment source。
- `agents/roles/*.md`：移除 tier metadata，保留 harness-neutral behavior。
- `scripts/sync_agents.py`：切換為 catalog＋preset projection，保留 `--map` 相容輸出並新增 verbose view。
- `agents/AGENTS.md`：改成 work-unit／preset／artifact／fallback 導航。
- `agents/zcode/*.md`、`agents/claude/*.md`：由 generator 重產的 compatibility adapters。
- `tests/test_sync_agents.py`：legacy/new 全 agent equivalence、golden bytes、unknown/collision/zero-write gates。

### 核心實作要點

1. 新增`agents/presets.toml`，以registry slug定harness tools/read-write/sandbox/background與default binding reference；禁止Role、authority、qualification、availability。
2. `agents/roles/*.md`保留neutral behavior prompt，移除description的`tier:`；slug首期不rename。
3. `sync_agents.py`讀catalog bindings＋presets，取代`ROLE_REQUIREMENTS`、`ZCODE_PINS`、`CLAUDE_PINS`與Markdown model-table regex；只驗static deployment binding，不執行runtime resolver。
4. 先在tests凍結legacy 9-agent map、generated bytes/hashes；新舊解析同時跑一次全量等價矩陣。全部相等後才刪copied dict/table parser與skill migration table。
5. `--map`保持既有`role/requirement/zcode/claude`四欄相容輸出；新增`--verbose`顯示preset、binding、model identity、token kind、capabilities，避免breaking consumer。
6. DispatchPlan→carrier adapter：selected binding等於named preset default時用registry；harness支援spawn override時保留同一WorkUnitContract/ExecutionPreset只換binding；否則走main或bridge並把Role、authority、surface與禁止再委派完整裝入work order。
7. `vision-review`preset的default binding仍落GLM Flash；`cr-research`default收斂到既定decision/global-research binding，修正兩處lite drift。
8. `agents/AGENTS.md`lifecycle table改成work-unit/preset/artifact/fallback導航，不再擁有judgment/capability demand；`--map`是projection機械源。
9. S1/S2全在同一card branch完成；新舊parity未綠前不得刪舊表、部署或合main。失敗即revert本弧S2變更，舊parser/source仍可由git恢復。

### Pseudo Code

```python
catalog = load_catalog(CATALOG_SOURCE)
presets = load_presets(PRESET_SOURCE)
for preset in presets:
    binding = catalog.binding(preset.default_binding_ref)
    validate_harness_projection(preset, binding)
expected = render_all(role_prompts, presets, catalog)
```

### 驗證策略

- RED：unknown preset/binding、Role欄侵入、binding/harness不相容、capability mismatch、unmarked collision、legacy/new map mismatch。
- Regression：全9 roles legacy→new pin equivalence、generated golden bytes、marker、check/map zero-write、idempotence、stale cleanup、CR MCP divergence。
- 真repo：`uv run pytest tests/test_sync_agents.py`；`uv run python scripts/sync_agents.py --check`；`--map`與`--map --verbose`；sync後second sync zero diff。
- 同一`Role=Reviewer`兩案：一般review可用default execution binding；高保護面選decision binding，authority都只為findings。

### 成功標準

- role prompt、work-unit demand、model/binding facts、preset default與generated registry各有一個owner；named agents可用，既有pins無意外改變，動態升級不被固定pin吞掉。

## S3：Workflow work units、authority、fallback 與視覺證據

### Context

- **實作能力**：一命令workflow產正確WorkUnitContract並執行DispatchPlan。
- **前置**：S1 schema可引用；S2 carrier adapter contract在場。
- **Invariant Impact**：accepted-EP gate、authority separation、independence、bounded fallback、source provenance。

### 變更檔案

- `skills/execution-plan/SKILL.md`、`skills/implement/SKILL.md`、`skills/judge-review/SKILL.md`、`skills/post-build/SKILL.md`：各自擁有 phase WorkUnitContract rows 與 escalation。
- `skills/ep-review/SKILL.md`、`skills/review-engine/SKILL.md`：review qualification／authority pointer。
- `skills/agent-workflow/SKILL.md`、`skills/self-contained-prompt/SKILL.md`：DispatchPlan→carrier、work-order envelope 與 failure handback。
- `skills/_common/agent-review-cycle.md`、`skills/_common/workflow-review-pattern.md`、`skills/_common/work-order.md`：共用 authority、independence 與 artifact schema。
- `ai-analysis/_tasks/_archived/09-15-model-capability-routing/references/instruction-testing.md`（新增）：tracked trial manifest、scoring、結果摘要與 receipt 路徑。

### 核心實作要點

1. execution-plan、implement、judge-review、post-build各自在phase table定義自己獨有work-unit rows；欄位schema只引用model-routing，不在preset/agents governance複寫。
2. execution-plan：evidence collection可execution；global synthesis、UC/invariant design、EP synthesis、review finding裁決為decision。user只呼叫一次，不在中途手選model。
3. accepted EP predicate：EP review ledger每列必為terminal`implemented/rejected`、所有adopted修正已進EP、無`needs-confirmation/pending`，且user顯式呼叫implement。任何一項不成立即禁止execution/apply，轉decision escalation或等待user。
4. implement：`implement_from_accepted_ep + execution + apply`；遇EP conflict、新invariant、public boundary、跨context架構選擇或反覆失敗時停止該leg，產escalation record，再派decision work unit。
5. judge-review固定`Role=Arbiter + adjudication + decision + final_disposition`；seat不足外派，無candidate不得self-downgrade。
6. post-build：orchestration=decision；Reviewer findings依保護面選execution/decision但authority固定findings；Arbiter=decision；已裁決修正=execution/apply；機械finalization=execution/evidence；visual observation要求native vision。
7. independence schema：`kind=different_provider_family`、`relative_to`、`required`、`fallback`。一般高保護面沿現行soft-visible policy，缺alternate family可`explicit_same_family_degradation`；user明示跨家族時`required=true`，缺場fail loud。
8. authority output recipe：evidence artifact不提供disposition/apply欄；findings artifact不提供apply/final disposition；Arbiter artifact才有disposition。加入要求越權的pressure scenarios，以實際輸出/副作用判分。
9. visual input envelope：source identity/hash、transport binding、delivery receipt由dispatcher產生。direct path要求raw image receipt送達Arbiter；`arbiter_viewed_source=true`只能由receipt推導。decomposed path的Arbiter input明確無raw image，只含observation artifact；source identity端到端一致。
10. observer artifact分facts/interpretations，記region/coordinates、uncertainty、observer model/binding；Arbiter verdict保留observation reference、source identity、自己的binding、false與`decomposed-not-equivalent`。
11. quota/runtime fallback用fixture注入429/1308/unavailable，寫DispatchTrace；1308在retryable-at前排除，429只依既定有限backoff/並發政策，候選耗盡轉no-candidate，禁止loop。
12. dispatch preview與output contracts至少涵蓋work unit、Role/authority、qualification、judgment/capabilities、candidate model/binding、requested/effective effort、carrier、override、independence、fallback/decomposition、jobId/attempts。
13. self-contained work order帶WorkUnitContract、ExecutionPreset、binding token、authority、input envelope與禁止再委派；不複製catalog values作新source。

### Pseudo Code

```text
if requires(decision, native_vision) and no direct candidate:
    receipt, observations = dispatch_visual_observer(raw_image)
    assert observations.source_id == receipt.source_id
    decision = dispatch_arbiter(observations_only)
    decision.arbiter_viewed_source = false
    decision.equivalence = decomposed-not-equivalent
```

```text
on carrier_failure(candidate, family):
    trace.record(candidate, family, retryable_at)
    re_resolve(contract, trace)
```

### 驗證策略

- **Behavior experiment lane**：先取得修改前RED；control/treatment、固定model/family、每arm至少5個fresh-context reps、逐字輸出、預先固定scoring與PASS/FAIL/UNEXPECTED/INCONCLUSIVE；tracked `references/instruction-testing.md` manifest逐筆指向`.agent-tmp/air-91/instruction-testing/`receipts。
- high-risk scenarios：weak-seat judge、accepted/pending EP、implementation escalation、evidence/reviewer越權壓力、soft/hard independence、compatible/incompatible override、quota failure injection、no candidate、direct/decomposed visual。
- **Output micro-test lane**：dispatch preview、acceptance predicate、escalation record、evidence/findings/Arbiter artifacts、independence degradation、override echo/failure、no-candidate、DispatchTrace、visual envelope/receipt與non-equivalence必要欄位。
- **Consumer smoke lane**：四workflow各一個bounded fresh-context dry run，驗入口接線與輸出；單次smoke不可冒充behavior experiment。
- provider未訂閱或live route缺場標INCONCLUSIVE；不retry-to-green，不把instruction結果高報成跨模型benchmark。

### 成功標準

- user只下原workflow命令，系統在consequential dispatch前選對work-unit requirements；無合格candidate、override衝突、fallback、visual decomposition或escalation都可見且有界。

## S4：Current-source convergence、部署與 acceptance

### Context

- **實作能力**：active consumers、generated artifacts、behavior evidence與user-level targets收斂。
- **前置**：S1–S3完成，無背景writer，Report Shell hook 1已在本次規劃建立。
- **Invariant Impact**：current-doctrine completeness、bundle freshness、generated equality、outward authorization、partial deploy recovery。

### 變更檔案

- `skills/CLAUDE.md`、root `AGENTS.md`、`rules/AGENTS.md` 與其他由 current-consumer manifest 指定的 navigation/pointer files。
- `skills/scan-project/scripts/check_single_source.py`、`tests/test_check_single_source.py`：projection 與 current-doctrine convergence gates。
- `tests/test_sync_agents.py`：整弧 schema/projection/equivalence acceptance。
- `ai-analysis/_tasks/_archived/09-15-model-capability-routing/references/current-consumers.md`（新增）：每個 active hit 的 disposition 與 historical exclusion。
- `ai-analysis/_tasks/_archived/09-15-model-capability-routing/index.html`：Report Shell hook 2 最終狀態。
- AIR-91 卡片與 actor-aware memory handoff artifact：只在終態收斂時更新。

### 核心實作要點

1. broad`rg`重建current-consumer manifest並逐檔disposition；active roots不得有未處置舊語義，archive/reports/history保留。
2. 更新root/rules/agents navigation、skills index與common templates，只留source/pointer或必要adapter contract；不重列catalog values或workflow demand。
3. 擴充既有`agents_projection_sync`／generator validation；只有無法由schema/projection捕捉的current-doctrine drift才加精準forbidden-pattern invariant。
4. 驗證DEPTH-MIN→SAMPLE→FULL：catalog/preset schema→legacy/new equivalence＋golden→real repo check/map→behavior experiment→consumer smoke→manifest/consistency→review chains。
5. mixed code/docs收尾：Python/generator diff先跑標準code-review→judge→apply→followup；instruction control-plane Markdown再跑docs-mode review→judge→apply→followup；之後才跑consistency/metadata。
6. deploy前完成source、generated registries、tests、dry-run與deployer列出的所有user-level targets具體diff/hash摘要。`scripts/deploy_agents.py`是outward action；必須向user展示可審結果並取得本次對話explicit deploy authorization，記`AUTH:`，否則標`PENDING`且不執行。
7. deploy前將所有目標的舊bytes/hash保存在本弧scratch。任一replace/freshness失敗即停止finalization與Done；整批修復重部署，或以保存bytes還原所有已改target，再逐端比對，禁止留下split state。
8. deploy成功仍須在fresh session做必要routing behavior sample；exit 0不等於harness已載入新bundle。
9. 更新同一Report Shell hook 2：實作章節、驗證證據、最終圖與badge；不存在時是本弧錯誤，不可跳過。
10. memory closeout actor-aware：CC/ZCode owning session載memory-audit做六問後寫入；Codex owning session只輸出精確entry/delta/evidence handoff給CC/ZCode，禁止直寫project pool。Spine只有實際觀察到entitlement事件才更新。
11. AIR-91 AC、Final Summary與done refs只在adopted findings、deploy/behavior evidence、memory handoff與Report Shell收斂後更新。

### Pseudo Code

```text
MIN    schema + static resolver fixtures
  ↓
SAMPLE legacy/new projection + behavior experiments + consumer smoke
  ↓
FULL   current manifest + code review chain + docs review chain
  ↓
PREP   target diffs + old target bytes/hashes
  ↓ explicit user AUTH
DEPLOY all targets → freshness + fresh-session behavior
  ↘ failure: stop finalization → repair-all or rollback-all
```

### 驗證策略

- `uv run pytest tests/test_sync_agents.py tests/test_check_single_source.py`，涵蓋catalog/preset schema、projection、legacy/new equivalence與current-source gate；instruction behavior evidence由tracked `references/instruction-testing.md` manifest驗收，不用pytest重抄散文判準。
- `uv run python scripts/sync_agents.py --check`、`--map`、`--map --verbose`；sync後second sync zero diff。
- `uv run python skills/scan-project/scripts/check_single_source.py`。
- current manifest對帳：舊role→tier、vision-tier、旗艦雙義、cr-research lite與workflow整體綁單一tier皆有disposition；不使用裸token zero-hit冒充判讀。
- user授權後才跑deploy；其後驗source/targets hashes與fresh-session behavior。
- post-build兩條review鏈Important findings全收斂後才finalization。

### 成功標準

- machine facts、instruction protocol、workflow demand、deployment presets、generated registry、user-level bundles與實際workflow選擇一致；錯capability、authority、binding、effort、pin、silent fallback或visual provenance遺失都能被獨立gate阻擋。

## 整合策略

- **baseline**: `df3741b81e90dad01ed30fb383750ad55630998d`
- 全弧用AIR-91 card branch；S1/S2在同branch完成且不得中途deploy/merge。S1先加新source但保留舊parity，S2等價綠後才切換與刪舊源。
- S3只消費WorkUnitContract schema/Resolver protocol，不引用generated registry內容作需求真相源。
- 每段先確認git diff無混入其他弧；shared file只改本段錨點。
- S2切換前保存legacy map與generated hashes；切換後逐項比較model token、effort、tools、body與output bytes。
- 若窄catalog仍無法分離supply/demand或維持pin equivalence，停止S2/S3，回寫AIR-91重新裁決；不得退回多份Markdown tables補丁。
- deploy與commit各有獨立consent gate；本EP授權規劃與local working-tree實作，不授權未來deploy或commit。

## 收尾步驟

1. 完成consumer manifest、兩條review鏈、behavior/consumer evidence與Report Shell hook 2。
2. 準備user-level target diff/hash與rollback材料，取得當次deploy授權後才部署；fresh session驗收。
3. 依actor-aware memory branch蒸餾或交接，不把Codex唯讀限制變成假完成。
4. 將AIR-91設Done、Final Summary指向使用者行為，整個task family搬done並換refs。
5. 止步於`/commit` gate；未取得當次確認不commit。
