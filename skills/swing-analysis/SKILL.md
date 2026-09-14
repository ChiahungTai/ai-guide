---
name: swing-analysis

description: "Swing Analysis 協作模式 — 啟動 Backbone Trajectory Viewer 並監控 [ACTION] 操作日誌"
when_to_use: "Launch the Backbone Trajectory Viewer UI and monitor [ACTION] logs so the LLM can understand user UI interactions in real time."
argument-hint: "無參數"
allowed-tools: ["Bash", "Read", "Write", "Monitor"]
---

# Swing Analysis 協作模式

> **🔴 mosaic 專屬**：本命令耦合 mosaic 專案的 Backbone Trajectory Viewer 與 `alpha_forge` 符號，屬 `instruction-writing.md` 的專案特定工具例外（同 `upgrade-nt`/`upgrade-sj` 類別），寄住 ai-guide 便於跨 worktree 共用。

啟動 Backbone Trajectory Viewer 並監控 `[ACTION]` 操作日誌，讓 LLM 即時理解使用者 UI 操作上下文。

通用協作模式（背景執行、Monitor、討論記錄）見 [ui-collab skill](../ui-collab/SKILL.md)。

## Phase 1：啟動 UI

```bash
uv run python -u scripts/offline_analysis/run.py
```

就緒信號：`[OK] load_data`

## Phase 2：監控操作日誌

按 ui-collab skill 的 Monitor 模式啟動監控。

## Phase 3：讀取 Swing 分析

收到 `[LOG] ai-analysis/llm-analysis/{stock}/swings/{swing_id}_{start}_{end}/swing.md` 後，
主動讀取該檔案。swing.md 包含完整的結構分析、KC 標記、軌跡、Setup 定義等。

需要更多上下文時，透過 `[LOG] rg 'ui_action.*seq=N' {log_path}` 查詢 Logger。

## Phase 4：操作對照表

| [ACTION] 名稱 | 觸發時機 | LLM 應理解的上下文 | 伴隨輸出 |
|---------------|---------|-------------------|---------|
| `select_swing` | 選取 swing | 使用者正在分析哪個 swing | `[LOG]` swing.md 路徑 → 讀取分析 |
| `change_threshold` | 調整閾值 | 使用者在篩選感興趣的 swing 範圍 | — |
| `select_wave` | 選取 wave node | 使用者正在檢視哪個波段的結構 | — |
| `switch_instrument` | 切換股票 | 使用者轉移注意力到新標的 | — |
| `toggle_condition` | 勾選/取消指標 | 使用者關注哪些技術指標 | — |
| `generate` | 點擊 Generate | 使用者觸發重新分析 | — |
| `rebuild_ui` | UI 重建完成 | 數據載入完成，可互動 | — |

## Phase 5：輔助查詢（MLDataset + 經典技術分析）

使用者討論過程中常需要查詢歷史技術指標（RSI、MA 等）。**必須使用 MLDataset 已計算的資料，禁止重算指標。**

### 分析視角要求

討論股票走勢時，載入 `trading-analysis` skill（三層框架：經典 TA → 量化 → 第二層思考整合）。Layer 2 的量化指標用 MLDataset 已計算資料（禁止重算，見上節）。

### 為什麼用 MLDataset

- MLDataset 已過完整 pipeline（features → conditions → transitions → wave scalars）
- 重算會用錯參數（如 RSI(14) vs RSI(6)）、用錯 smoothing 方法
- 重算浪費時間且結果不可靠

### 為什麼用 Merge 版本（get_features()）

MLDataset 有兩種取資料方式：

| 方式 | API | 用途 | Anti-leakage |
|------|-----|------|-------------|
| Per-interval | `dataset.features_by_interval[Interval.WEEKLY]` | 查原始週線值 | **無** — 直接取週線收盤值，可能用到未完成的 bar |
| **Merge（推薦）** | `dataset.get_features()` | 查某日的跨級別指標 | **有** — 週/月線已 shift + forward fill，確保只用已完成 bar |

Merge 版本做了 anti-leakage shift：低頻資料的 datetime 往前推一根 bar，值不動，確保只用已完成的 bar。例如 5 月的日線查 `1w_rsi_6`，拿到的是上一根已完成週線的值，不是當週可能未完成的值。

### 資料取得

```python
from datetime import date
from mosaic_alpha.alpha_forge import PerStockDataPipeline
from mosaic_alpha.config.recipes import create_backbone_recipe, RecipePresets
import polars as pl

recipes = create_backbone_recipe(params=RecipePresets.BACKBONE_WATCHLIST)
dataset = PerStockDataPipeline().build("2374", recipes[0])  # ⚠️ recipes 是 list，取 [0]

merged = dataset.get_features()  # Merge 版本（anti-leakage）；欄位帶 interval 前綴 1d_/1w_/1mo_，wave scalars 為 1d_prev1_structure
```

### 查詢模式

```python
# datetime 是 datetime 型別，filter 用 date() 非字串
df = merged.filter(
    (pl.col("datetime") >= date(1999, 5, 1)) &
    (pl.col("datetime") <= date(1999, 7, 12))
)
result = df.select(["datetime", "1d_close", "1d_rsi_6", "1w_rsi_6", "1mo_rsi_6"])
```

### 注意事項

- **datetime 是 datetime 型別**：filter 時用 `date(1999, 2, 1)`，不能用字串 `"1999-02-01"`
- **欄位帶 interval 前綴**：merge 版本的欄位是 `1d_rsi_6`, `1w_rsi_6`, `1mo_rsi_6`（非原始的 `rsi_6`）
- **Anti-leakage 語意**：`1w_rsi_6` 在某根日 K 上代表「上一根已完成的週線 RSI」，不是「當週即時 RSI」
- **MLDataset 會被快取**：第一次 build 較慢，後續讀快取很快
- **backbone recipe 對應 `Experiment.early()`**：早期區間（7% 漲跌幅制度）
- **merge 後欄位眾多**：查詢時明確 select 需要的欄位，不要 `print(df)` 全部輸出

## Phase 6：討論記錄

按 ui-collab skill 的討論記錄模式寫入：

```
llm-discussions/{stock}/YYYY-MM-DD_trajectory-viewer_{topic-slug}.md
```
