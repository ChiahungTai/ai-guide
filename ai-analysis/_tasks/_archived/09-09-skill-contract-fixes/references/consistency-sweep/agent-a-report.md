# 文檔↔程式碼一致性地毯查證報告（Agent A，2026-09-09）

**範圍**：root AGENTS.md Tier-1 深查、mosaic_alpha/ 全模組＋子目錄 AGENTS.md（44 檔）Capabilities/入口機械驗證、MOS-74 re-export 退役後 .md drift 掃描。
**方法**：rg/fd/Read/read-only；每檔抽提 .py 引用（含 file:symbol）逐一驗存在性，flagged 項逐條人工判定（fd 全域搜索＋git log＋上下文語境）。
**工具腳本**：`.agent-tmp/consistency-sweep-2026-09-09/check_refs.sh`（可重跑）。

---

## 結論（倒金字塔）

**總 finding：14 條 = P0×0、P1×3、P2×5、P3×6。**
已驗證成立：Tier-1 root 57 條路徑＋7 env vars＋6 plist＋8 組慣例宣稱全數成立；mosaic_alpha/AGENTS.md 62 條符號/路徑全中；scripts/tests/tools/apps 四份 Tier-1 文檔全綠；Tier-2 44 檔 ~1173 條 .py 引用中失效僅 7 條（5 檔）；MOS-74 六包 `__init__.py` 確認零 re-export，殘留失效教學僅 1 條 P1。

Drift 熱點集中且高度相關：**2026-09-04 research-family-split（UI 下沉）與 2026-09-06 market-regime-profile（AnalysisProfile 重構）兩個 EP 之後，受影響模組的 AGENTS.md 未同步**——5/8 條 P1+P2 都源自這兩弧。

---

## P1 Findings（宣稱已失效、會誤導操作；3 條）

### P1-1 venues/tw/AGENTS.md — regime 表符號全數過時（MOS-73/09-06 重構未同步）
- 文檔：`mosaic_alpha/venues/tw/AGENTS.md:59` —「`regimes.py:TW_STOCK_REGIME` / `TW_FUTURES_REGIME` / `MARKET_REGIMES` — 商品特性參數宣告式 regime 表…`MarketRegime` frozen dataclass 實作 `venues/market_regime.py:MarketRegimeProfile`」
- 事實：`rg "TW_STOCK_REGIME|TW_FUTURES_REGIME|MARKET_REGIMES" mosaic_alpha/ -g '*.py'` → 0 定義；`class MarketRegime` → 0 hits。現況 `mosaic_alpha/venues/tw/regimes.py:62` `TW_STOCK_ANALYSIS = AnalysisProfile(`、`:71` `TW_FUTURES_ANALYSIS`、`:80` `ANALYSIS_PROFILES`；profile Protocol 在 `venues/market_regime.py:38 MarketRegimeProfile`；值計算邏輯在 `venues/analysis_policy.py:129 class AnalysisProfile`、`:239 derive_ma_break_buffer`。
- 影響：本模組 AGENTS.md 的核心入口（值鎖定測試釘的 silent-corruption 鄰接面）指到三個不存在的符號。信心：high（git：ai-analysis/_projects/marking/done/09-06-market-regime-profile/ EP 重構後未同步）。

### P1-2 research/AGENTS.md — buffer 單源指向不存在符號
- 文檔：`mosaic_alpha/research/AGENTS.md:42` —「buffer 單源 `venues/tw/regimes.py:TW_STOCK_REGIME`〔SPOT 1.5%；期貨 0.3%…〕」
- 事實：同上 0 定義。現行單源鏈：`venues/analysis_policy.py:239 def derive_ma_break_buffer(profile)` → `venues/resolver.py:167 def resolve_ma_break_buffer` → `venues/resolver.py:161 ma_break_buffer_pct=analysis_policy.derive_ma_break_buffer(profile)`；消費端 `conditions/ma_break.py:104 params["buffer_pct"] = policy.ma_break_buffer_pct`。
- 影響：文檔教人改 buffer 值去 `regimes.py:TW_STOCK_REGIME`——那裡沒有東西可改。信心：high。

### P1-3 alpha_forge/watchlist_pipeline.md — 教學範例 import 已失效（MOS-74 波及 config 包）
- 文檔：`mosaic_alpha/alpha_forge/watchlist_pipeline.md:113` —```from mosaic_alpha.config import WatchlistConfig```
- 事實：`mosaic_alpha/config/__init__.py` docstring 明示「Import policy: 無 re-export／消費端直接從子模組 import」→ 此 import 在 runtime ImportError。正確路徑 `from mosaic_alpha.config.watchlist import WatchlistConfig`（`mosaic_alpha/config/watchlist.py:34 class WatchlistConfig`）。同檔 :107 的表格其實已正確寫 `config/watchlist.py`——範例碼與自家表格矛盾。
- 影響：照抄範例即炸。信心：high。

---

## P2 Findings（路徑漂移：符號存在但 file:name 失準；5 條）

### P2-1/P2-2 ui/AGENTS.md — pl→pd 邊界兩條宣稱過時（09-04 research-family-split）
- `mosaic_alpha/ui/AGENTS.md:66` —「`trajectory_viewer.py:_to_pandas()`（全檔單一 `to_pandas`）」→ `rg "to_pandas" mosaic_alpha/ui/trajectory_viewer.py` 0 hits。現況：`mosaic_alpha/ui/presentation/windowing.py:36 def to_pandas(df: pl.DataFrame)`（EP-F5 單一邊界，public 函式非 method）。
- `mosaic_alpha/ui/AGENTS.md:69` —「`trajectory_viewer.py:_align_columns_to_chart()`」→ 現在 `mosaic_alpha/ui/research_app_shell.py:1247 def _align_columns_to_chart(`；`TrajectoryViewerApp(ResearchAppShell)`（trajectory_viewer.py:61）繼承取得，行為仍在但 file 錨點失效。
- 來源：ai-analysis/_projects/marking/done/09-04-research-family-split/ep.md:73（~50 methods 下沉清單含此二者）。信心：high。

### P2-3 research/AGENTS.md — box loader 消費者路徑過時
- `mosaic_alpha/research/AGENTS.md:73` —「viewer（`ui/trajectory_viewer.py:_compute_current_boxes`）」→ 該符號現於 `mosaic_alpha/ui/research_app_shell.py:238 def _compute_current_boxes`；trajectory_viewer.py 0 hits（同下沉弧）。信心：high。

### P2-4 features/AGENTS.md — 幽靈符號（改名＋搬檔雙重漂移）
- `mosaic_alpha/features/AGENTS.md:262` —「DepAware chart 端走 columns 投影（遞移閉包展開，`ui/data_strategies.py:_columns_for_feature_classes`）」→ `rg "_columns_for_feature_classes" mosaic_alpha/ -g '*.py'` 全 repo 0 hits。現況：`mosaic_alpha/services/_chart_compute.py:141 def columns_for_feature_classes(`（委派 `features/store.py:261 def columns_for_feature_classes`）；`ui/data_strategies.py:464` 只剩 `visible_feature_classes`。信心：high。

### P2-5 adapters/sj/historical/AGENTS.md — 引用已刪除模組（weekend-verify 退役）
- `mosaic_alpha/adapters/sj/historical/AGENTS.md:54` —「非 coordinator caller（`data/verification/verifier.py`、`scripts/ops/backfill_futures_gap.py`）不顯式 catch 此二例外…（verifier 整輪 abort 進度續跑下週末…）」→ `mosaic_alpha/data/verification/` 不存在；`fd verifier mosaic_alpha/` 0 hits。git：`6eb3f9ef5 chore(data): weekend-verify 退役——verification 七模組／Step 11／CLI／env gate 全刪`。root AGENTS.md 已知退役，本檔仍以現在式描述其行為。信心：high。

---

## P3 Findings（噪音/歷史引用；6 條）

| # | 位置 | 內容 |
|---|------|------|
| P3-1 | `mosaic_alpha/common/AGENTS.md:18` | 引 `poc/poc_log_suppress_key.py` 為「POC-verified」證據——檔已刪（poc/ 無此檔） |
| P3-2 | `mosaic_alpha/strategies/AGENTS.md:198` | 引 `poc/poc_composite_warmup.py` 為「POC 實證」——檔已刪（同段 :203 對 warmup_builder.py 已正確標「已刪除」，僅 poc 引用殘留） |
| P3-3 | `mosaic_alpha/venues/tw/AGENTS.md:58`＋`mosaic_alpha/venues/tw/market_hours.py:47` | `common/utils.py:TAIPEI_TZ`——符號已不存在；兩處均為歷史語境（「收斂自」），現行單源 `market_hours.py:TW_VENUE_TZ` 有正確記載 |
| P3-4 | `tests/unit_tests/conditions/test_ma_break.py:13`、`tests/unit_tests/research/test_classification_features.py:617`、`tests/unit_tests/research/test_rule_classifier.py:14` | docstring 引 `venues/tw/regimes.py:TW_STOCK_REGIME`——測試本體 import 的是新符號（`test_regimes.py:31-34` import ANALYSIS_PROFILES 等），僅註解層過時 |
| P3-5 | `ai-analysis/blueprint/callstack/condition-rendering-tags.md:174` | 已帶 drift 警示 header，但 header 內「值單源 `venues/tw/regimes.py:TW_STOCK_REGIME`」一句在 MOS-73 後二度過時 |
| P3-6 | `ai-analysis/archive/shap/SHAP-論文分析.md:777` | `from mosaic_alpha.features import SHAPFeatureAnalyzer`——符號全 repo 0 定義；位於歸檔區（依慣例不維護），僅記錄 |

---

## 已驗證成立彙總（宣稱→證據通過）

**Tier-1 root AGENTS.md**：觸發器表與引用路徑 57 條全存在（`scripts/lsp_stubs` 確認指 `~/Github/nt_v1/scripts/lsp_stubs/`，存在）；plist 6 個宣稱全在 `~/Library/LaunchAgents/com.mosaic.*.plist`（weekend-verify 已退役不存在＝與文檔一致）；env vars 7 條與 paths.py:71/106/174/189、logging.py:160/353、paths.sh:16/28 一致；MOSAIC_DISPLAY_TZ 殘留 6 hits 全為明示退役的 docstring；volume 四 caller（dynamic_chart.py:317/827/958/1025，÷_SHARES_PER_LOT:88）成立；`sj_vol_to_internal` units.py:34；Interval enums.py:84-86；bare `# noqa` 0 hits＋RUF100 pyproject:67；版權：618/631 檔有 All rights reserved、長版 592（~94%，與「~92%」宣稱相符）、AGPL 0 hits；Makefile init-services:9/test:86/test-quick:90/test-par:110/sync:126/sync-stubs:132/sync-sj-stubs:140/hooks:136。

**mosaic_alpha/AGENTS.md**：可複用基礎設施 45 條 file:symbol、NT 回測生態系 14 API、三條資料存取路徑、alpha_forge/condition_mappings.yaml＋condition_system.md、services 三 facade——全數存在。

**scripts/AGENTS.md**：ops 19＋backtesting 8＋research 21 腳本、10 個 CLI command（cli/data.py decorator 實查）、引用 lib 7 條（build_pretriage_pool=pretriage.py:193）——全存在；scripts/ 無 __init__.py、mypy scripts.* strict（pyproject:131）。

**tests/AGENTS.md**：目錄樹 20 目錄、12 個具名測試檔、__snapshots__ 24 個 .spec、pyproject（importlib:205/pythonpath:212/asyncio strict:213/playwright>=1.60:264）、fixtures（trader/shared_trading_node/catalog_available×2）——全成立。

**tools/AGENTS.md**：4 Capabilities 入口全存在；退役宣稱 5 項（lsp_mcp/test_lsp_mcp/run-lsp-mcp.sh/Makefile lsp-*/pyproject mcp dep）全確認不存在。

**apps/AGENTS.md**：5 子 app 入口＋run_session_loader、_shared 10 元件、TradingHost.request_cold_restart:414、_maybe_exit_for_cold_restart:59、AnnotateApp:628、append_overlay:50、load_golden_train:58、sentinels 三函式、三個 Dashboard class——全存在。

**Tier-2（44 檔 AGENTS.md，~1173 條唯一 .py 引用）**：失效 7 條集中於 5 檔（上方 P1×2＋P2×5）；其餘 39 檔零機械失效（含 data/AGENTS.md 148 refs、common 87、strategies 52 等大檔——裸檔名引用經 fd 全域搜索全數落位於子目錄）。ui/tabs/AGENTS.md 無 .py 引用（純目錄描述）。

**MOS-74**：data/datasets/labels/features/structure/conditions（＋alpha_forge/config/model 等）package-root `__init__.py` 零 re-export（`rg "^from \.[\w.]* import [A-Z]"` 0 hits）；data 保留 get_catalog origin（data/__init__.py:34）與 root 宣稱一致；features __init__ 為註冊接線副作用（docstring 明示豁免）。code 端 `from mosaic_alpha.conditions import` 0 hits——遷移徹底。

---

## 查證誠信段

**初判被查證推翻（機械 flag → 人工判定非 finding）**：
- `watchlist/AGENTS.md` `ranking.py:score_` — regex 誤抽自 `score_*()` 敘述，8 個 scoring function 存在
- `broker_flow_analysis/AGENTS.md:67` `brokers.py:29` — 即 `data/broker_breakdown/brokers.py:29 def broker_group`，逐行精確命中
- sj 家族裸檔名（constants.py/data.py/common.py/utils.py）— 全在上層 `adapters/sj/`，`shioaji_ts_to_utc_ns` 確在 utils.py
- `stubs/shioaji/_core.py` — 實為 `_core.pyi`（regex 截斷），存在＋`make sync-sj-stubs` Makefile:140
- `ci_buypoint_board.py`/`ci_wave_board.py` — 在 `scripts/research/`，文檔路徑明確
- `indicators/base/enums.py`、`labels` 的 `services/_label.py` — 文檔均自我標明歷史已清除/撤銷（commit c457cf87 驗證存在）
- `qlib/contrib/model/double_ensemble.py` — 文檔明示為上游「參考來源」
- `conditions` `_integration.py` — regex 子串誤抽（test_pattern_conditions_integration.py 的一部分）

**unverified / 範圍外**：SYSTEM-MAP.md 與 ai-analysis/blueprint 深查不在本次委派範圍；動態 import（字串拼接/getattr）超出靜態掃描能力；root env 表未列 `region.py:39 MOSAIC_MARKET_REGION`（表已聲明詳見 region.py，記為 P3 觀察未列入 finding 總數）。
