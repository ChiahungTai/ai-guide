# Handoff → ai-rules session：post-build metadata-sync 補「改名符號→掃 instruction 檔」機械步驟

> 來源：mosaic_alpha 2026-09-09 一致性地毯掃描弧（三 flash agents＋主 session 統合）。mosaic session 不改 ai-rules——以下為反饋（證據＋proposed patch 方向），交 ai-rules session 固化。

## 任務一句話

ai-rules 的 post-build skill（metadata-sync 段）補一個機械步驟：EP 結案時用「本次 rename/move/retire 的舊符號清單」rg 掃 instruction 檔家族，防止文檔 drift 系統性累積。

## 證據（為什麼值得改）

2026-09-09 對 mosaic_alpha 做三 agent 地毯掃描（A=文檔軸 lite-verify、B=藍圖軸 cr-research、C=smell 軸 spec-miner；主 session 抽驗 12/12 load-bearing findings 屬實）：

- Agent A 機械驗證 44 個模組 AGENTS.md 共 ~1173 條 .py 引用，失效僅 7 條——但 **5/8 條 P1+P2 全部源自兩個 EP（09-04 research-family-split、09-06 market-regime-profile）結案後受影響 AGENTS.md 未同步**（符號改名/下沉：`TW_STOCK_REGIME`→`TW_STOCK_ANALYSIS`、`_to_pandas` 下沉 `presentation/windowing.py`、`_compute_current_boxes` 下沉 `research_app_shell.py` 等）
- Agent B 驗證藍圖層：慢 drift 檔（architecture.md）核心宣稱全綠；drift 集中在自述「快 drift」的 uc/ 家族（daily-ops-map 列已退役步驟、observation-carriers line-pin 抽 5 中 1）——**快 drift 檔靠人工記憶更新，正是會漏的那層**
- 共通根因：EP 的 rename/move/retire 發生在 code，結案流程（階段 5a metadata-sync）沒有「拿舊符號名反掃文檔」的機械動作——改名知識只活在 EP 段落裡，文檔同步靠 session 記得

## Proposed patch 方向（ai-rules session 判斷最終形狀）

post-build skill metadata-sync 段（或 execution-plan 階段 5a checklist）補機械步驟：

1. 從本次變更 git diff 萃取 rename/move/retire 符號清單（舊符號名）
2. `rg "<舊符號>" <repo> --type md`（或至少掃 AGENTS.md 家族＋專案自述快 drift 的檔——各 repo 藍圖層慣例不同，步驟寫成「掃 instruction 檔＋專案快 drift 檔清單」的參數化形式）
3. 命中即修（改名後新錨點）或顯式記 drift；零命中 = 步驟完成證據

不改的：不要求每個 EP 全文檔重驗（A 證明基礎命中率很高、平時不漂）——只掃「本次動過的符號」，成本與弧大小成正比。

## 驗收

- 步驟文件化進 post-build skill（metadata-sync 段）
- 可選：未來某弧 dogfood 一次（rename 型 EP 結案跑步驟，驗命中）

## 建議執行 tier

主 session（instruction 檔手術——判斷密集，非機械段）。

## 證據檔案（mosaic 側，7 天後 .agent-tmp 夜掃會清——要留先 copy）

- `.agent-tmp/consistency-sweep-2026-09-09/agent-a-report.md`（文檔軸 14 findings＋查證誠信）
- `.agent-tmp/consistency-sweep-2026-09-09/agent-b-report.md`（藍圖軸 14 findings）
- `.agent-tmp/consistency-sweep-2026-09-09/01-synthesis.md`（統合判讀）
