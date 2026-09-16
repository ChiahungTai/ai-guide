# Agent B 報告 — 架構藍圖↔程式碼一致性掃描（2026-09-09）

## 一、結論（倒金字塔）

**核心架構宣稱全數與 code 現實吻合，零 P0。** architecture.md 的依賴塔（24 模組、L0–L4 零 inbound L5、L5 橫向邊清單）、§3.2 循環唯一性（adapters↔data 唯一剩環細節逐字吻合、labels↔datasets 斷環、歷史環全單向）、§3.4 Ripple 表主要行（Recipe 精確到「labels 7 檔 + 四模組零命中」、Interval 全 24 模組、Pipeline 恰三模組、paths 恰 11 模組）、§3.5 parity matrix 11 組 file:line 釘點——這些架構決策關鍵面**經 rg + code-reality 雙源機械驗證成立**。

Drift 集中在**「快 drift 檔」的維護滯後**：uc/ 家族（daily-ops-map、observation-carriers）與 SYSTEM-MAP 個別行——多為 2026-09-04 LabelsExtend 移除與 MOS-67 golden 樹退役後未同步的殘留。計 **finding 14 項：P1×1、P2×8、P3×5**；已驗證成立大項 40+。

## 二、Findings（嚴重度排序）

### P1（會誤導營運認知）

**F-1 [P1] daily-ops-map.md:93 — LabelsExtend 仍列為每日 pipeline 步驟**
- 藍圖側：「factors | **FeaturePhase + LabelsExtend**（…labels 完成窗…）｜ workflows `labels_extend.py` | ✅」
- code 側：`mosaic_alpha/workflows/daily.py:316`「LabelsExtendStep 已自 daily 移除——2026-09-04 user 裁決」；steps list（daily.py:326-330）無 LabelsExtendStep；SYSTEM-MAP.md:44 已記載移除
- 嚴重性：退役理由是 33min/天白算——讀者會誤判每日 pipeline 仍在跑此步。daily-ops-map 自述「快 drift、每次 build 5a 結算後更新」卻漏更。信心：高

### P2（過時，會誤導查證方向）

**F-2 [P2] root AGENTS.md:305 — 熱點表「`RiskGuard`（trading）」位置過時**
- 實際 `class RiskGuard` 在 `mosaic_alpha/apps/_shared/risk_guard.py:55`；trading/ 目錄零 RiskGuard class（僅 __init__.py:11 搬遷說明註解）。trading/AGENTS.md:104 已正確記載「→ apps/_shared/risk_guard.py（S2 搬）」。architecture.md §2.3/§3.5 亦正確指 apps/_shared。僅 root AGENTS.md 熱點表殘留舊位。信心：高

**F-3 [P2] SYSTEM-MAP.md:269 —「update-db 10 條 rule」與同檔行 34「11 張 DB 表」矛盾**
- code：`mosaic_alpha/data/update_scheduler.py:106-178` TABLE_RULES 恰 11 個 TableRule（tw_stock_info…tw_futures_night_products），表名與行 34 逐字對齊。行 269 過時。信心：高

**F-4 [P2] SYSTEM-MAP.md:48 —「13 內層 + 6 外層共 19 個 PipelineStep」過時（實際 18）**
- code：內層 13（`data/daily_close/pipeline.py:106-118`）＋外層 5（`workflows/daily.py:326-330`：Data/Feature/Setup/Analysis×1/Output；default `analyses=("naive_kc",)` daily.py:60）＝18。疑為 LabelsExtend 移除後 6→5 未同步（同檔行 44 已記移除）。連帶：daily-ops-map.md:85「15 步（[MAP] 權威）」與 14 步展示表/19 註/code 18 四說法並存。信心：高

**F-5 [P2] SYSTEM-MAP.md:101 —「`execution.py:1179` → cache.balance_free」釘點錯位**
- code：`adapters/sj/execution.py:1179` 是 `_batch_cancel_orders`；live T+2 broker 寫入鏈實際在 `execution.py:1450` `_async_get_balance_and_settlements` → AccountBalance(total/free/locked)。語義（live 寫入鏈保留、display 不讀）仍成立——`balance_free` 字樣全 repo 僅存於「不讀它」的註解。信心：高

**F-6 [P2] vocabulary.md:24 ＋ research-loop.md:47 —「A6 `golden_tree.json` 檔案化（已落地）」——檔案不存在**
- code：`fd golden_tree` 全 repo 零檔；`rg golden_tree` mosaic_alpha/ + scripts/ 零命中。實際機制＝`per_label_trees.json`（`research/perlabel.py:36` PERLABEL_TREE_PATH；`fit_classifier.py:502`「MOS-22.7（A6 樹序列化）：sklearn 樹 → per_label_trees.json candidate」）。golden mutex 樹已隨 MOS-67 S6 退役（architecture.md §3.3:164 的 2026-09-08 覆核已更新，此兩檔未跟）。信心：高

**F-7 [P2] architecture.md §3.4 services Facade 行 — 消費者清單低報**
- 藍圖側（:183）：「alpha_forge, ui, watchlist — 所有透過 Facade 存取的消費端」
- code：另有 `apps/paper_trading/trading_host.py:75`、`cli/data.py:59`、`cli/_broker_breakdown_wiring.py:51` 皆 `from mosaic_alpha.services import MarketService`。改 Facade 介面會波及 apps+cli，表中未列。信心：高

**F-8 [P2] observation-carriers.md — line-pin 大面積漂移＋DashboardMode 成員清單過時**
- 抽查 5 組 file:line 僅 1 組命中（state_actor.py:136 timer ✓）。漂移例：`_switch_generation` doc 291-317 → 實際 shell.py:162,326-331；CashTracker 建構 doc trading_host.py:972-973 → 實際 967-968；dynamic_chart ÷1000 四釘點 doc :293/:704/:821/:892 → 實際 ~:298/:855/:976；td.py DashboardMode 分支 doc 295-300,480-489,646-654 → 實際 185/248/325-327
- 成員清單：doc「TRADING/REPLAY/BACKTEST」→ 實際 TRADING/REPLAY/**SESSION**（`common/enums.py:336+`；SESSION 為 EP-F2 新增、BACKTEST placeholder 已回收——同 docstring 自述）。該檔自述「快 drift」、載體大改（MOS-25/EP-F2）後未重驗。信心：高

### P3（噪音／微小漂移）

**F-9 [P3] blueprint/AGENTS.md:14 —「callstack/（32 篇系列）」**：實際 34 篇（fd 計數；callstack/README.md:1 自述 34、root AGENTS.md 亦 34）。僅此檔殘留舊數。

**F-10 [P3] architecture.md §2.2 —「max_waves→max_legs」括號釘 trend_run.py**：`max_legs` 參數實際在 `structure/structure_tree_builder.py:86`（trend_run.py 檔案存在、改名本身屬實）。

**F-11 [P3] architecture.md §3.4 TaskType 行 datasets 腿**：「datasets (LabelGenerator)」——datasets/ 全域 rg TaskType/task_type 零命中（label_generator.py、assemble.py 零；config/recipes.py 僅註解提及）。model 腿成立（model/lgbm.py、ensemble/double_ensemble.py、config/model_config.py）。datasets 若受影響是經 Recipe 間接，非直接消費。

**F-12 [P3] 空目錄殘留**：`mosaic_alpha/feed/`、`mosaic_alpha/apps/feed/`（feed 退役 2026-08-19 後空殼，零檔案——退役宣稱本身 code 面成立）；`./.kanban/`（2026-09-02 退役後空殼，零檔案）。

**F-13 [P3]（觀察）.tours/manifest.toml 205 tours 引用 32 個 source 全命中**；34 鏈中 `ml-model-training.md`、`warrant-filter-valuation.md` 兩鏈未入 manifest（可能為 plan 待生成項，非 drift 斷言）。

## 三、已驗證成立彙總（宣稱→證據）

### architecture.md
| 宣稱 | 證據 |
|---|---|
| §1 24 模組清單 | fd 25 目錄＝24 模組＋feed 空殼；逐層成員全存在 |
| §1 L0–L4 零 inbound import L5（2026-09-08 覆核） | 15 個 L0-L4 模組 × L5 七模組，絕對＋相對 import 兩形態全掃零命中 |
| §1 L5 橫向邊（ui→trading/strategies/alpha_forge；workflows→watchlist；workflows→alpha_forge 僅 daily.py 組裝根＋setup_phase 純 DI；trading→strategies/workflows 已消失） | ui 8 檔命中；workflows/daily.py:3、setup_phase.py:11,71「本模組不 import alpha_forge」註解與宣稱逐字吻合；trading/ 雙掃零命中 |
| L0 common / L1 config 零向上依賴 | rg 全掃零命中 |
| §3.1 critical paths | tests/unit_tests/common/test_anti_leakage_guard.py ✓、features/factor_cache.py:218 FactorCache ✓、labels/store.py:38 LabelStore ✓ |
| §3.2 唯一循環 adapters↔data（細節） | adapters→data：client.py:54-61＋mock_client.py:50-53（protocols/tradable_universe/tw_security_index/instrument_prune 逐字吻合）；data→adapters：catalogs/integrity.py:40＋daily_update/base_updater.py:42-43；venues→adapters 零命中（已償宣稱 ✓）；labels→datasets 零命中（第二環斷環 ✓）；structure/datasets/config/features 歷史環成員互查全單向 |
| §3.4 Recipe 行 | rg＋CR refs 雙源：labels 恰 7 檔、datasets 2、alpha_forge 1、research 1、ui 1；model/watchlist/services/workflows 零命中（rg -c ZERO×4）；「workflows 不經 datasets.assemble 間接」✓（workflows 零 import datasets）；Recipe DEF recipes.py:240、21 refs（CR [SRC] scip index @8de1b52） |
| §3.4 Interval 行 | 全 24 模組 import 命中（conditions 34 檔最廣） |
| §3.4 Pipeline 行 | 消費者恰 data(daily_close×2)/alpha_forge(1)/workflows(4) |
| §3.4 paths 行「11 個模組」 | 恰 11 模組（adapters/alpha_forge/apps/cli/data/features/labels/research/strategies/ui/workflows） |
| §3.4 sizing 三符號 | strategies/equity_calc.py＋margin_momentum.py＋kc_momentum_naive.py（current_equity）；common/cash_tracker.py:63；apps/_shared/risk_guard.py:55（位置漂移見 F-2） |
| §3.5 parity matrix 釘點 | backtest.py:41/96 fill_model=None ✓、fee_model.py:36 ✓、kc_momentum_naive.py:308-309 ✓、replay_host.py:1310/1090/1132 ✓、risk_guard.py:28 ✓、execution.py:1688 ✓、trading_host.py:994 ✓、live.py:157/163-164 ✓、daily_dispatcher.py:77-81 ✓（execution.py:1179 除外→F-5） |
| §2.2 max_waves→max_legs 改名 | max_legs 存在（structure_tree_builder.py:86；釘檔漂移見 F-10） |
| §2.3 trading 基礎設施 | equity_policy.py、mtm_helpers.py、trading/types.py EngineConfig ✓ |

### SYSTEM-MAP.md
- 14 個 scripts 入口＋run_session_loader＋probe_sj 全存在（fd 逐一）
- CLI：workflow daily（cli/workflow.py:21-22）、data broker-breakdown（data.py:413）、backfill-tdcc（107）、daily-close（398）、update-db（277）、check-db（369）、sync-calendar（286）、sync-themes（377）全存在
- TABLE_RULES 11 條與行 34 表格逐字對齊（行 269 除外→F-3）
- 內層 13 steps（pipeline.py:106-118）、CONV_WINDOW=400（workflows/types.py:34）、LabelsExtend 移除（daily.py:316）
- 退役掃描：MOSAIC_DISPLAY_TZ 僅存退役說明註解（time_utils.py:22）✓、feed import 殘留零 ✓、weekend-verify plist 已無 ✓、dependency-graph.md 不存在（未啟用一致）✓
- DataMode.REDIS docstring（enums.py:379-389）與行 112 宣稱逐字吻合
- ranked_watchlist_backtest.py risk_guard 零命中（§3.5 research script 例外宣稱 ✓）
- 入口旗標：viewer -i/--instruments（run.py:78-79）、annotate --market twse|otc（run.py:17,45-47）、golden_pretriage 五 subcommand（1019/1040/1061/1069/1079）、scan_capital_increase_events --milestone 三值（63-65）

### uc-matrix.md
- F1 仍缺：WatchlistResult 僅 alpha_forge/backbone_analysis_pipeline.py，strategies 零消費 ✓
- F2 仍缺：無 validated=True code path ✓
- F4 仍缺：comment→rule 橋無實作（fit_classifier.py:654 rule_bridge 為 golden 口徑過渡報告欄位，非此橋）✓
- （F3/F5 為載體/流程級缺口，未逐項機械驗）

### daily-ops-map.md
- 入口符號 13 個全存在：walkforward_folds（experiment.py:392）、apply_indicators（engine.py:146）、FeatureService.calculate（service.py:346）、build_single_interval（structure_tree_builder.py:104）、load_features_concat（feature_loader.py:133）、NaiveDatasetRanking（naive_ranking.py:33）、run_filter_tree_pipeline（filter_tree_pipeline.py:1285）、BackboneAnalysisPipeline（backbone_analysis_pipeline.py:322）、generate_performance_report（performance_report.py:49）、backtest_dashboard/run.py、ma_crossover_labels.py、_generate_dual（label_generator.py:248）、_build_instrument_selector 等（LabelsExtend 行除外→F-1）

### vocabulary.md（抽樣 18 項全命中）
SqueezePattern/ConsolidationPattern/KeyCandlePattern/NPatternFeature（features/）、ConsolidationCondition/MarketStateCondition/NPatternCondition（conditions/）、SetupClassifier/SetupCandidate/SetupRanking、RegimeSegment 四 regime（year_constants.py:117,140-146）、MarketRegimeProfile（venues/market_regime.py:38）、WyckoffPhaseCondition（conditions/wyckoff_phase.py:55）、DayVerdict/BandVerdict（broker_flow_analysis/types.py:40,59）、MODIFIER_TAGS（notes.py:46）、ChartAppShell（ui/shell.py:114）/ResearchAppShell（research_app_shell.py:97）、TabSpec/compose_right_tabs/VIEWER_PROFILE/ANNOTATE_TABS/CAMPAIGN_PROFILE、MABreakCondition 已實作且帶 ma_period/buffer_pct/window_bars（conditions/ma_break.py:42）、ElliottWaveCondition 整檔退役（elliott_wave.py 不存在 ✓；registry 28+MABreak=29 類別數算術吻合）、LegExtractor/StructureTreeBuilder/leg_scalar_feature.py（features/）/leg_scalars.py、LegDirection（common/directions.py，leg.py:31 import）
- golden_tree.json 宣稱除外→F-6

### research-loop.md
三種子 scripts（crawl_disposition_studyset.py／scan_capital_increase_events.py／scan_research_trend_runs.py）✓、StudyAreaKind 五源（study_set.py:48-55：DISPOSITION/ATTENTION/SCREEN_FIRE/SWING_BOX/CAPITAL_INCREASE）✓、rule_classifier.py（research/）✓、FilterTree 三步驟（SwingTagProfilingStep:513/TagRankingBuildStep:630/TreeAssemblyStep:871）✓、Wilson CI（filter_tree_types.py/population_report.py）＋SequentialGreedy（sequential_greedy.py）✓、FOLD 斷點＝F1 ✓

### blueprint/AGENTS.md ＋ callstack ＋ .tours
映射目標 9 檔全存在 ✓、trading-philosophy.md symlink → ../../mosaic_alpha/trading_philosophy.md ✓、callstack 實數 34＝README 自述＝root AGENTS（blueprint/AGENTS.md「32」除外→F-9）、.tours/arch 01-06 族＋04-每日選股/01.tour isPrimary ✓、manifest 205 tours 32 sources 全命中 ✓

## 四、查證誠信段

- **覆蓋範圍**：architecture.md 全部 §1/§3.1/§3.2/§3.4 主推行＋§3.5 抽 11 釘點＋§2 抽查；SYSTEM-MAP 六區塊抽查＋退役掃描；uc 三檔（F1/F2/F4 機械驗、F3/F5 未逐項）；vocabulary 抽樣 18 項；research-loop 全載體；blueprint/AGENTS.md 映射全表＋callstack 全對帳＋manifest 全 source 對帳。SYSTEM-MAP 細部行（如排程分鐘級參數、parity 矩陣未列軸）與 §3.4 個別低頻行（condition_mappings.yaml/setup_definitions.yaml/IndicatorDef 等）未逐行驗。
- **方法**：rg（絕對＋相對 import 雙形態）為主，CR MCP 交叉（refs Recipe [SRC] scip @8de1b52＝HEAD、無 stale）；CR callers 符號需 bare-name 形式（module-path 形式查無 DEF——SCIP path 格式差異，已改用 refs bare name 命中）。
- **自我勘誤**：一次 `rg -rn` 誤觸 replace 旗標造成 EngineConfig「顯示替換」假象，當場抓出更正（EngineConfig 存在 trading/types.py）——符號查詢顯示 masking 風險的活例。
- **read-only**：未修改任何 repo 檔案；僅寫 .agent-tmp/consistency-sweep-2026-09-09/ 下本報告與 agent-b-notes.md（5 個中間檢查點）。
- **未腦補聲明**：F3/F5（uc-matrix）僅驗證「缺口仍未閉合」的機械面；「disposition-weekly 實體 plist 手動管理」與 repo 內 plist 模板並存屬部署語義，未判定為 drift。
