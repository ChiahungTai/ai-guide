---
card_id: MOS-80
task_baseline: e37412f849
title: MOS-80 volume 單位單一源 — EP 規劃殼
report_type: task-plan
task_type: architecture
status: done
diagram_heights:
  lot-map: 640
---

<!-- section-group: {"id": "s1", "title": "總覽", "sub": "volume 單位單一源重塑——對齊 NT lot_size（venue 層擁有）；設計定稿展開，非重新設計"} -->
台股 lot 常數（1 張＝1000 股）與張↔股換算收斂到 `venues/tw` 單一源，消除散落的 1000 魔術數字——**轉換值全程不變**（pure value-source reshaping）。
```
src: adapters/sj/units.py（唯一合法出現點）  ─→  hub: venues/tw lot.py
src: tools/ntv2/*（散落 1000）               ─→  hub: venues/tw lot.py
src: features/*（張股換算）                   ─→  hub: venues/tw lot.py
```
NT `Instrument.lot_size` 是純 metadata（引擎零消費），對齊的是概念歸屬（lot 知識屬 venue domain）。
- 十二定義點：`TW_STOCK_LOT_SIZE` 單一常數、import mosaic_alpha 收斂
- 十三定義點：`unit or 1000` fallback 無法收斂——venv 邊界物理約束，allowlist

<!-- section-group: {"id": "s2", "title": "段落計畫", "sub": "S1→S2→S3→S4 單向依賴；全段共通驗證基調＝值鎖定（重構前後轉換輸出逐位相同）"} -->
- S1 建立單一源——venues/tw lot.py＋常數輸出＋值鎖定測試
- S2 遷移 SJ 線——adapters/sj/units.py 改消費單一源
- S3 遷移 tools/features——ntv2 與 features 側散落 1000 收編
- S4 清理與驗收——rg 殘留清零＋全 suite 值鎖定綠

<!-- section-group: {"id": "s3", "title": "EP Review 記錄", "sub": "獨立 Explore agent 四軸審查（展開忠實度／錨點／遺漏／可實作性）——8 findings 全數採納入 EP"} -->
<!-- fold: appendix -->
審查逐條：展開忠實度（設計決策未走樣）、錨點（path:line 全數核對）、遺漏（venv 邊界的第十三定義點補入）、可實作性（S 段切分可單獨驗收）。

<!-- section-group: {"id": "s4", "title": "回源", "sub": "殼是展示層——本體（source of record）與證據鏈全在 repo"} -->
本體 `ai-analysis/_tasks/done/09-09-mos80-volume-lot-single-source/ep.md` @ baseline e37412f849。
<!-- diagram-assign: {"id": "lot-map", "title": "lot 常數收斂地圖"} -->
