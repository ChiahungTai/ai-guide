---
card_id: MOS-23
task_baseline: 31b3084b
title: factors cache 回歸 OHLCV 派生模型 — EP 導讀
report_type: delta-report
task_type: architecture
status: done
ep_path: ai-analysis/_tasks/done/09-04-factors-cache-incremental/ep.md
diagram_heights:
  arch: 640
  daily-flow: 720
---

<!-- section-group: {"id": "why", "title": "① 為什麼——三五天消失的 266GB", "sub": "本 EP 修的是讓它不再發生的架構"} -->
**事件**：9/1～9/4 磁碟可用空間 ~400G → 134G。主凶 `~/.mosaic/data/cache/factors/`（清理前 161G）。
根因＝四因子相乘（GLM + muse 兩家獨立調查對照一致）：specs sprint 四代 key 連翻、set 級全量 key、全量重算＋全史覆寫、零清理。
<!-- fold: comparison -->
現況病灶：一個 specs key 統治 hive＋trees＋pivots 三種儲存——specs 動一欄，三種全作廢。目標：hive 用 specs key（年段覆寫、零殘留）；sidecar 用自己的 structure_key（與 feature specs 無關）。

<!-- section-group: {"id": "assets", "title": "② 資產與命運", "sub": "保留／退役／修正三分"} -->
| 資產 | 命運 | 說明 |
|---|---|---|
| _extend_from_frozen（service.py:980） | ✅ 保留——設計本體 | hit → frozen 全史＋extension 尾窗（EXTEND_RIGHT 本體） |
| tree snapshot sidecar | 🗑️ S1 退役持久化 | dense 重建 0.12s vs 載入 2.52s（bit-equal）——退役的是 persistence |
| pivot event sidecar | 🔧 S2 保留並修正 | 固定檔名＋structure input hash 進 manifest＋atomic |
| 夜間掃描清殘留 | ❌ 否決 | 零殘留架構內建，不是事後清掃 |

<!-- section-group: {"id": "target", "title": "③ 目標形態——canonical prefix 單一心智模型", "sub": "catalog OHLCV＝唯一真相源；cache＝可丟棄派生物"} -->
三個 cache action：**HIT**／**EXTEND_RIGHT**（prefix 保留、只補 tail——跨年非特殊分支）／**REBUILD_PREFIX**（頭缺、中洞、identity 壞、correction 自癒）。
<!-- diagram-assign: {"id": "arch", "src": "diagram-architecture.html", "title": "key 分層架構圖（archify）"} -->

<!-- section-group: {"id": "plan", "title": "④ 推進與驗收 S0–S5", "sub": "核心驗收：非跨年日磁碟淨增 ≈ 0"} -->
- S0 Tree Replay POC——2330 dense 重建前 8,072 bars bit-equal、重建 0.12s vs 載入 2.52s
- S1 退役 TreeSnapshotStorage 持久化鏈——runtime trees 由 dense 記憶體重建
- S3a PIT payload gate——position 欄 frozen offset rebase；correctness gate 高於 routing gate
- S3b prefix state machine——CacheDecision（HIT｜EXTEND_RIGHT｜REBUILD_PREFIX）集中在 FeatureService

<!-- section-group: {"id": "daily", "title": "⑤ 穩態日路徑——daily workflow 的正確形態", "sub": "gate → extension 尾窗 → append-only"} -->
目標行為：15:30 daily → catalog 載入 → cache 判定（三 action）→ hit：零寫入、只 slice；miss → REBUILD_PREFIX。
<!-- diagram-assign: {"id": "daily-flow", "src": "diagram-workflow.html", "title": "穩態日增量路徑流程圖（archify）"} -->

<!-- section-group: {"id": "risk", "title": "⑥ 風險與降級", "sub": "資料正確性高於效能數字"} -->
| 風險 | 等級 | 處置 |
|---|---|---|
| S0 多檔／多 interval 等價外推 | 致命 | 3-5 檔 × 1d/1w/1mo 確認外推——不過即停 S1 重新裁決 |
| extension payload 43-68 欄 exact mismatch | 高 | S3a 修復目標；等價測試全綠前 fallback REBUILD_PREFIX |
| 並發三寫入者（daily／盤中／research） | 高 | S4 physical-path lock＋same-dir pending＋fsync＋manifest-last |
