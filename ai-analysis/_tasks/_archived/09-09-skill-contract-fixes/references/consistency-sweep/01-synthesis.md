# 統合判讀（主 session 5.3）——2026-09-09 一致性地毯掃描

> 狀態：**最終**。三 flash agents（A=lite-verify 文檔軸／B=cr-research 藍圖軸／C=spec-miner smell 軸）收齊；主 session 抽驗 load-bearing findings **12/12 全部屬實**（C-P0×3、A-P1×3、B-P1+P2×4、親驗四項：exporter 三路／candidates alias／services re-export／case_pack）。零誤報抽驗樣本。

## 總圖

- **藍圖核心架構宣稱全部機械驗證成立**（B）：依賴塔 L0-L5 零違規、adapters↔data 唯一剩環屬實、§3.4 ripple 表精確到檔數、parity matrix 釘點全中。架構層真相源可信。
- **導航文檔健康面高**（A）：root Tier-1 全綠（57 路徑/7 env vars/6 plist/8 慣例）、44 模組 AGENTS.md ~1173 條引用僅 7 條失效、MOS-74 六包根乾淨、phantom API 零、library→上層依賴零。
- **真正的洞集中在四群**（下方 prioritized）。

## 討論清單（prioritized）

### 🔴 1. 會計/sizing 路徑吞錯三件（唯一「code bug」級）
同根模式：`except Exception` 包 `cache.positions_open()` → 靜默回空。
- `trading/bar_equity_recorder.py:108-111`（equity 靜默退化純 cash）
- `trading/margin_ledger.py:223-226`（maintenance_ratio 警示靜默缺席；另 :248-250 malformed position 僅 debug log）
- `strategies/margin_momentum.py:257-269`（overlay recovery 吞錯；註解自證只為 unit test——測試相容 workaround 住進 production 的形態）
判讀：crash-only「沒有數據冒充有數據」。修法方向＝修 seam（顯式 readiness gate / 窄化例外型別），非加 log 了事。

### 🟠 2. equity 表示三路並存＋研究腳本吃已知扭曲路徑
- `strategies/exporter.py` 同流程並寫：export_equity（:142）＋export_nt_returns（:349，docstring 自證 MARGIN 下「虧損可能報正值、多部位漏算」）＋export_equity_curve（:183，新正確路徑）
- `scripts/research/backtesting/ranked_watchlist_backtest.py:201-203,541-543` 頭條 Sharpe/Sortino/Calmar 仍走 NT returns 路徑（同檔 :136 顯示 equity_curve.parquet 也在餵——新舊並存）
- `strategies/metrics.py:316` deprecated `build_equity_curve_from_nt_returns` 宣稱「保留向後相容（既有 caller）」但 production 零 caller（僅 tests 餵活）＝死碼＋宣稱失真
- `alpha_forge/setup_classifier.py:61` `candidates` alias「backward compat」但 production 自己（backbone_report.py:950,954,961,1273）就還在用 alias——遷移半途

### 🟠 3. 文檔 drift 群（兩 EP 後未同步；機械批次可修）
高誤導性：
- `research/AGENTS.md:42` buffer 單源指向不存在符號 `TW_STOCK_REGIME`（實際鏈 analysis_policy.py:239 → resolver.py:161；照文檔改值＝改錯地方，KC threshold silent-corruption 鄰接面）
- `venues/tw/AGENTS.md:59` regime 表符號全數過時（現為 TW_STOCK_ANALYSIS/ANALYSIS_PROFILES/AnalysisProfile）
- `alpha_forge/watchlist_pipeline.md:113` import 範例 runtime 即 ImportError
- `uc/daily-ops-map.md:93` LabelsExtend 仍列每日步驟（09-04 已移除，33min/天白算的退役項）
次級：root AGENTS.md:305 RiskGuard 位置（實在 apps/_shared/risk_guard.py:55）、SYSTEM-MAP 19→18 步／10→11 rules／execution.py:1179→1450、vocabulary.md:24＋research-loop.md:47 golden_tree.json（已隨 MOS-67 S6 退役，現行=per_label_trees.json）、observation-carriers line-pin 大面積漂移（5 抽 1 中）＋DashboardMode 成員過時、architecture.md services Facade 低報 apps+cli 消費者。
根因觀察：09-04 research-family-split 與 09-06 market-regime-profile 兩弧結案時 metadata-sync 沒打到受影響 AGENTS.md；快 drift 檔自述快 drift 但滯後。

### 🟡 4. volume 單一源宣稱 vs 鏡像現實
- `adapters/sj/units.py:31`「唯一合法出現點」失真：positions.py:32（自承 mirror）、dynamic_chart.py:87-89、config/tw_market.py:43、kc_momentum_naive.py:104 各有 1000 常量
- broker_flow_analysis 裸 ÷1000 五筆（verdict.py:70,155-156,191-192、analyzer.py:130，有註解）
- `ui/kchart/case_pack.py:142` 是÷1000 display 第五邊界，docstring 自稱已登記於慣例表但 root AGENTS.md 表只列 dynamic_chart 四 caller——F-B regression 同型風險面（表未列＝下個人不知道）
選項：收斂單一源 vs 承認鏡像並修宣稱。

### 🟡 5. MOS-74 尾波
- `services/__init__.py:17-26` re-export 三 Service＋__all__（8 消費者）——與全域禁令矛盾；但子模組是私有名（_catalog/_intel/_market），直接退役 re-export 會逼消費者 import 私有模組（更糟）。正解形狀＝子模組公有化＋退役 re-export。
- 13+ 子套件 __init__ re-export 殘留（data/fetchers、data/catalogs、model/ensemble、ui/kchart 等）

### 🟡 6. silent stubs 半實作
- `adapters/sj/data.py:2524-2532` quote/trade ticks 請求 stub（2025-11 起 ~9.5 個月）——NT DataClient silent no-op
- `adapters/sj/execution.py:1962` PENDING_CANCEL 僅 TODO＋warning（SJ↔NT order 狀態 desync 可能性——觸發條件待判讀）
- `alpha_forge/filter_tree_pipeline.py:782` DOWN sub-tree 未實作（2026-04 起）
判讀方向：crash-only 下 silent no-op＝「查無資料」冒充——至少要 fail loud 或明示 not-supported。

### 🟢 7. 衛生批
- scripts 摸 library 私有 6 筆（closed_loop_analysis.py:49-51 一次摸 watchlist.ranking 三個私有常數）——library 重構無 scripts 測試保護；依 lib-grade 準則該上抽公有
- duplicated helpers：_to_int/_to_float ×4、_default_root ×4
- `Optional[` ×9（typing 別名，禁用寫法殘留——ruff 未開 UP？）
- 空目錄殼：feed/、apps/feed/、.kanban/
- P3 文檔殘留群（A-P3×6、B-P3×5）

## 開放問題（討論用）

1. 🔴 三件吞錯：開小 EP 修 seam？（唯一建議動 code 的項）
2. 🟠 equity 三路：research 腳本頭條指標改走 equity_curve 路徑？舊兩路是否排退場？
3. 🟠 文檔 drift：機械批次一個 commit 修掉（含 buffer 單源指正）？根因——post-build metadata-sync 對「受影響模組 AGENTS.md」的覆蓋要不要加機械化（如 EP 階段 5a checklist 注入「本次改名的符號清單→rg 掃 AGENTS.md」）？
4. 🟡 volume：收斂 or 修宣稱？
5. 🟡 services re-export：子模組公有化＋退役（MOS-74 波 7）？
6. 🟡 stubs：fail loud / 實作 / 明示 not-supported 三選一逐件裁決？
