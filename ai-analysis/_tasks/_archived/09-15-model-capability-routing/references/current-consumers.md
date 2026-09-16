# AIR-91 S4 Current-consumer manifest（舊 tier 詞彙語義）

> 產生者：S4 A 腿（broad rg 掃描＋逐命中判讀）。本檔是 EP「Current-consumer manifest」節的權威收斂——EP 表是下限，本掃描是封閉集合。
> 掃描基準：working tree @ S1–S3 完成後（branch air-91 變更落在 main working tree——見「掃描時點備註」）。
> 判讀原則：只收「tier 語義」用法（單軸強度檔／requirement token／role→tier 兩跳）；純英文單字（full path／full suite）、其他軸的 full/lite/vision（EP 規模、memory-audit 級別、deploy projection、視覺能力、模組 tiering）為誤命中、排除（類別見末節）。

## 掃描命令（可重現）

```bash
# 詞彙廣播（誤命中多，逐行判讀）
rg -n -w "full|lite|vision" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
# tier 詞（導航/表格/prose 引用）
rg -n "tier" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
# 定向：旗艦雙義／role→requirement／vision tier
rg -n "旗艦" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
rg -n "role→requirement|role -> requirement|role→tier|role-tier" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
rg -n "vision tier|tier=vision|vision-tier" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
# 定向：cr-research lite drift 殘留／workflow 綁單一 tier
rg -n "cr-research" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
rg -n "=full|= full|＝full|full 版|full-tier|full tier" rules/ skills/ agents/ scripts/ tests/ AGENTS.md ai-development-guide.md
```

掃描面＝current-doctrine roots（rules/ skills/ agents/ scripts/ tests/ 根 AGENTS.md、ai-development-guide.md；203 檔）。
排除＝backlog/、ai-analysis/reports/_done/、ai-analysis/_tasks/_archived/、ref-docs/、.agent-tmp/、.agents/、.code-reality/、node_modules/（歸檔歷史不改）。
`ai-development-guide.md` 全文零 tier 詞彙命中（guide 只骨架指向 rules——乾淨）。

## 統計

| 項目 | 數 |
|---|---|
| 掃描檔數（md/py/toml） | 203 |
| `full\|lite\|vision` 廣播 raw hits | 332（67 檔） |
| `tier` 詞 raw hits | 62 |
| 定向掃描（旗艦／role→requirement／vision-tier／cr-research／full 綁定） | 44 |
| tier 語義命中（判讀後列入下方 manifest） | migrate 24／pointer 3／compatibility 10 組／historical-exclusion 6 組 |
| 誤命中排除（非 tier 語義，按類別） | 約 240 hits／10 類別（末節） |

## migrate（舊語義仍在 active 檔——需改寫）

owner 標記：**B**＝B 腿範圍（S4A 不動）；**S4-nav**＝S4 navigation 收斂（主 session 派工）；**範圍外**＝非兩腿清單內、由主 session 裁定歸屬。

| # | 位置（逐字引用節錄） | owner |
|---|---|---|
| M1 | `skills/CLAUDE.md:130`「lite 任務必派 registry 角色」 | B |
| M2 | `skills/CLAUDE.md:132`「tier→(model,effort) 解析表〔中文標籤旗艦/一般〕＋full-tier 旗艦釘選…rule 端留角色→tier 表」——index 描述的是已移除結構（tier×provider 權威表 S2 已刪；rule 已改 work-unit precedence） | B |
| M3 | `AGENTS.md:107`「requirement 分類（full/vision/lite）」 | B |
| M4 | `agents/AGENTS.md:17`「roles 投影（full 別名釘選 model: opus〔AIR-44——別名可攜〕…）」 | B |
| M5 | `agents/AGENTS.md:47`「lite 測試＝規格陳述→驗收證據 full 複驗」 | B |
| M6 | `agents/AGENTS.md:49`「seat 非 full 時升級外派 bridge，禁 in-session 降級自判」——seat 能力以 tier token 表達 | B |
| M7 | `agents/AGENTS.md:99`「（full 亦釘——AIR-43）」 | B |
| M8 | `agents/AGENTS.md:115`「lite 角色任務誤派 general-purpose＝旗艦跑機械段…要省成本層必派 registry lite agent」 | B |
| M9 | `rules/model-routing.md:21`「S1→S2 遷移期：skill 內舊 role→tier／tier→model 表保留（帶 MIGRATION marker），S2 等價 gate 通過後移除；期間 registry 派工沿舊鏈」——遷移期已結束（表已移除、等值 gate 已過），句述過期 | B |
| M10 | `rules/AGENTS.md:69`「跨 harness subagent 模型分層骨架（角色→tier 表＋兩跳原則＋詞彙定義…）」——rule 內容已改 work-unit precedence，導航行述舊結構 | S4-nav |
| M11 | `skills/cross-verify/SKILL.md:30`「model-routing skill 權威表 lite 列」——指向已移除的 tier×provider 權威表（stale pointer） | 範圍外 |
| M12 | `skills/illustrate/SKILL.md:20`「殼生成分工二 tier〔full 篩選敘事→vision 驗收〕」 | 範圍外 |
| M13 | `skills/illustrate/SKILL.md:78`「model 依 [model-routing](../../rules/model-routing.md) 角色 tier——平行分組＝lite」——指向 rule 已不存在的角色 tier 表（stale pointer） | 範圍外 |
| M14 | `skills/_common/illustrate-html-mode.md:46`「殼生成分工（二 tier；registry 對號查 agents/AGENTS.md execution contract 表）」 | 範圍外 |
| M15 | `skills/_common/illustrate-html-mode.md:48`「篩選敘事（full 主 session）…不派 lite」＋`:49`「vision-review（vision 驗收）」 | 範圍外 |
| M16 | `skills/state-review/SKILL.md:21`「caller-harness full dual-context 承接＋記錄」＋`:37`「in-harness full 承接＋記錄」——full＝capability class 語義（額度降級承接檔） | 範圍外 |
| M17 | `skills/model-routing/SKILL.md` B 腿收斂清單（authitative 檔內 旗艦資格條款 `:79-89`、dispatch 預設 `:97-102`、thoughtLevel 但書 `:117`、詞彙對照 `:121,126`、lite 分工律 `:132-142`、家族表 `:157-158,170`、glm 契約 `:196`、跨家族解析 `:221`、CC path `:307`、並發表 `:311,318`、失敗態 `:331,333`；description `:3` 同）——保留或改寫是 B 腿設計裁量 | B |
| M18 | `skills/model-routing/catalog.toml:62`「（tier 表僅列家族欄）」——註解引用舊表名 | B |
| M19 | `skills/execution-plan/SKILL.md:103`「後續 handoff『建議執行 tier』的輸入」＋`:179`「decision／global-research——AIR-76 v3.1 裁升，非 lite」 | B |
| M20 | `skills/implement/SKILL.md:35`「lite 測試＝規格陳述，驗收證據由 full 複驗」＋`:217`「單一 lite agent」 | B |
| M21 | `skills/post-build/SKILL.md:24`「lite 機械收尾」 | B |
| M22 | `agents/roles/impl-lite.md:3,9`「lite 執行檔…lite 模型寫的測試僅規格陳述非驗收證據…（lite 寫的測試＝規格陳述，驗收證據由 full 複驗）」＋生成副本 `agents/zcode/impl-lite.md:3,12`、`agents/claude/impl-lite.md:3,10`——role prompt 內 tier 語義（S2 移除了 description tier tag，body prose 保留） | B |
| M23 | `skills/agent-workflow/SKILL.md:40`「取 registry name＋tier 欄」＋`:54-67` Step1 tier 歸屬表（`claude-opus-*`→opus（full）、`glm-5.3`→旗艦（full）、`glm-5.3-flash`→lite）＋`:240-241`「Agent model 依角色 tier」 | B＋S4-nav |
| M24 | `AGENTS.md`（root）:107 已列 M3；另 `agents/AGENTS.md:11` 治理註解見 H3 | — |

## pointer（指向單一源，合法——隨源頭詞彙同步）

| # | 位置（逐字引用節錄） | 說明 |
|---|---|---|
| P1 | `skills/blueprint-bootstrap/SKILL.md:55`「lite tier 並發上限較寬，見 [model-routing](../model-routing/SKILL.md) 並發表」 | 並發軸；值在 model-routing 並發表 |
| P2 | `skills/execution-plan/SKILL.md:340`「以將 spawn 的 agent 所在 tier 為準」 | 並發軸同上；表詞彙若 B 腿重標，此類引用須同步 |
| P3 | `skills/agent-workflow/SKILL.md:65`「以**將 spawn 的 agent 所在 tier** 為準…（表在 model-routing skill）」＋`:67`「`[Agent] model=<依 model-routing 角色 tier>, max=N, current=M`」 | 並發軸同上 |

## compatibility（刻意保留的相容形——無動作）

| # | 位置 | 說明 |
|---|---|---|
| C1 | `agents/presets.toml:12,28`＋全部 requirement 條目（`:32,44,56,71,83,95,107,119,131`） | 「requirement 欄＝legacy --map 四欄相容 token（full/vision/lite），非路由」——S2 明文設計 |
| C2 | `agents/AGENTS.md:25`「requirement 相容 token（full/vision/lite）定義在 `presets.toml` allow_lists（tier 詞彙歷史語義見 `rules/model-routing.md`）」 | token 源頭宣告＋pointer |
| C3 | `agents/AGENTS.md:68-76` preset 表 requirement 欄（lite/full/vision per slug） | 相容 token 欄 |
| C4 | `agents/AGENTS.md:71`「cr-research \| full…此行曾 drift 為 lite，AIR-91 S2 修正」 | 修正後正確值＋歷史註記 |
| C5 | slug 家族：`lite-verify`／`impl-lite`／`vision-review`（roles/＋agents/zcode/＋agents/claude/ 全部 name: 行） | EP 已定設計 #8：role-like slug 首期保留為 compatibility adapter |
| C6 | `skills/handoff/SKILL.md:55,57,67`「建議執行 tier」欄 | model-routing:142 管轄對照明文裁定「handoff 路由建議判定——兩套條件管轄面各異，詞形差異非 drift」 |
| C7 | `skills/self-contained-prompt/SKILL.md:50`「建議執行 tier｜條件式路由建議…一般（lite）需三條件全滿…旗艦 only 五項不可讓（全文見 model-routing skill『旗艦資格條款』）」 | 同 handoff schema 十欄；目標節（旗艦資格條款）在場非 stale |
| C8 | 「lite agent」dispatch 簡稱族（指 lite-verify registry agent）：`skills/code-review/SKILL.md:75,121`、`skills/implement/SKILL.md:217`、`skills/review-engine/SKILL.md:173`、`skills/_common/workflow-review-pattern.md:40,213`＋`:222`「ANCHOR_MODEL = 'sonnet' // lite 地板」、`skills/execution-plan/SKILL.md:121`、`skills/post-build/SKILL.md:40,101,104`、`skills/ep-review/SKILL.md:36,65`、`skills/implement/SKILL.md:124` | slug 型 dispatch 引用；B 腿若改寫 model-routing 分工律詞彙，此族隨之（現列 compatibility） |
| C9 | `skills/kbar-form-analysis/SKILL.md:30`「Agent dispatch 合約（vision-review 為載體…）」 | slug 引用 |
| C10 | `skills/execution-plan/SKILL.md:179`「非 lite」否定形 | 已遷移後的正確描述（cr-research＝decision） |

## historical-exclusion（歷史標記／guard——非 active doctrine）

| # | 位置 | 說明 |
|---|---|---|
| H1 | `skills/model-routing/SKILL.md:73,109`「AIR-91 S2：legacy tier × provider 權威表已移除（等價 gate 通過）…」 | S2 移除標記註解（非表本體） |
| H2 | `skills/model-routing/SKILL.md:113`「cr-research 於 v3.1 裁升 full（AIR-76 定案，原 lite）——決策記錄」 | 決策記錄 |
| H3 | `agents/AGENTS.md:11`「description 不帶 tier 標記——AIR-91 S2 起 requirement…」 | 治理註解（描述 S2 已完成的移除） |
| H4 | `scripts/sync_agents.py:61`「（AIR-91 S2 legacy tier→pin dict／skill 表 parser／check_parity 已於等價 gate…」 | 移除標記註解 |
| H5 | `tests/test_sync_agents.py`（109 raw hits） | S2 等值 fixtures（LEGACY_* 凍結快照）＋doctrine guards（`test_skill_legacy_tier_tables_removed_and_pointers_present`:1285） |
| H6 | `tests/test_check_single_source.py:559-612` | bridge_model_vocab fixtures 引用合法 tier 表形（測試語境） |

## 誤命中排除類別（非 tier 語義——不逐行列）

| 類別 | 代表位置 |
|---|---|
| EP 規模軸（simple/standard/full） | `skills/execution-plan/SKILL.md:64,70,230` |
| memory-audit full/lite 稽核級別 | `skills/memory-audit/SKILL.md`×11、`skills/CLAUDE.md:134`、`generate_index.py:32` |
| deploy projection full mode | `scripts/deploy_agents.py`×8、`tests/test_deploy_agents.py`×17、`tests/test_air85_projection_oracle.py`×5、`scan_project.py`×2、`check_single_source.py:438,441`、`doc-health:5` |
| vision＝視覺能力／人類視覺（非 tier token） | `AGENTS.md:62`、`diagram-selection:3,4,43`、`ui-visual-verify`×5、`kbar-form-analysis:3,10`、`mermaid:49,62`、`trading-analysis:61`、`tool-discipline:9`、`acceptance-evidence:40`、`CLAUDE.md:145,156,160`、`illustrate:169` |
| 英文形容詞 full | `rules/tool-discipline:30`（full Read）、`deep-work:5`、`test-driven-development:28`、`nt-query:55,85`、`context7:16`、`api-and-interface-design:55`、`debugging-and-error-recovery:116`、`state-review:20`（full-repo）、`test_crawl:119`、`illustrate-artifact-menu:77`、`symbol-query-routing:27` |
| tour quality full\|degraded／full replace | `tour-bootstrap:19,20`、`code-reality:48` |
| debrief 覆蓋欄 full/partial | `debrief:55` |
| nt-v1-query domain 語義 | `account-model.md:17,18,26,137`、`reference.md:3,54,78,96`、`nt-v1-query/SKILL.md:51` |
| mutation-testing-lite（名稱） | `audit-test:69,218` |
| 模組 tiering（codebase 分層，非模型 tier） | `smell-detector/baseline.md:7,25,50,63,71,83,126`、`zoom.md:27`、`illustrate-structure-viewport.md:72,79` |

## Negative claim 對帳（EP「Negative claim 表」）

| EP claim | 掃描結果 |
|---|---|
| zero consumer：old `vision` tier semantics | 裸「vision tier」collocation＝**0 active hits**；vision 作 capability 軸語義以遷移形存續（`native_vision ∩ binding image_transport`，agents/AGENTS.md:52,76）——詞彙退役、能力保留。不可宣稱「零消費者」的原始裁決成立於掃描前；掃描後現樹已收斂 |
| no impact：generated registry pins | S2 已交付等值（test_sync_agents.py:1569 全 agent equivalence）；本腿以 `sync_agents.py --check` 綠複驗（見 S4A 驗證證據） |
| cr-research lite drift | **零殘留**——5 個提及全為 full／否定形／決策記錄（agents/AGENTS.md:44,71、execution-plan:179、model-routing:100,113）；EP 記載的 `agents/AGENTS.md:66`／`execution-plan:165` 兩處 lite drift 已由 S2/S3 修正（行號已漂移） |
| workflow 整體綁單一 tier（post-build=full 形） | **零命中**（`\b(workflow-name)\s*[=＝]\s*(full|lite|vision)` 全域零）；殘留最近形為 model-routing:140「post-build 編排＝full 能力檔」——已限定編排子單元、非整鏈綁定，B 腿收斂 |
| 旗艦雙義 | 旗艦詞活躍面集中於 model-routing skill（B 腿 M17）＋CLAUDE.md:132（M2）＋agents/AGENTS.md:115（M8）＋self-contained-prompt:50（C7，目標節在場）——全部有 disposition |

## 機械 gate 對應（S4A 交付）

由本掃描反推的最小 forbidden-pattern 集合（`check_single_source.py` 新 invariant `model_routing_current_doctrine`）：

1. 舊 tier 權威表 **header**（`tier →`／`tier ×` 行首 `#` 錨定）——H1 移除標記註解與 H5 guard fixtures 不誤中（非 header、且 tests/ 不在掃描面）。
2. `role → requirement|tier` **header**——同上錨定。
3. workflow＝tier 綁定（`post-build=full` 形）。
4. `vision tier`／`tier=vision` collocation。
5. roles frontmatter `tier:` tag 回歸（S2 移除項；projection gate 不攔未知 frontmatter 鍵）。

不加的（schema/projection 已涵蓋或機械不可行）：cr-research pin（presets/golden 等值已釘）、requirement token 值（presets.toml 非 .md 不在 forbidden 掃描面、且為相容設計）、prose 級 lite/旗艦 用語（合法面太廣——C6-C8 管轄對照已裁定）。

## 掃描時點備註

- 工作目錄 checkout 在 `main`（`air-91` branch 存在且為 main 的 ancestor——同 tip `c8bb0d3`）；S1–S3 產物以未 commit 變更落在 main working tree。本 manifest 掃的是該 working tree 現況。
- B 腿（model-routing/agents/四 workflow skill/CLAUDE.md/root AGENTS.md/sync_agents.py/rules/model-routing.md）與本腿平行推進——migrate 清單中 owner=B 的行在 B 腿收斂後應重新對帳（本檔 disposition 以掃描時點為準）。
