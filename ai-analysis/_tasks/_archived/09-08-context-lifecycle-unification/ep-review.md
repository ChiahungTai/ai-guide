# AIR-45 blueprint 審查

狀態：最終審查紀錄；F1–F5 獨立審查已回收，findings 17–20 已回寫 master 對應段落。17–19 的 implemented 僅表示藍圖修正入檔；20 的禁引號取捨仍 needs-confirmation。結論：有條件展開子 EP，S1 文法拒寫 gate 須先裁定，不代表 production 可實作放行或 runtime 驗收完成。

範圍：master `ep.md` 與 S0 證據對照；不實作、不部署、不改 backlog。

已核對並採納：

- SM-1 用 rg 命中衡量 findability，未測無提示任務是否先觸發查詢、讀正確 body 並採用約束；不能承擔 S1 的 routing go/no-go。P5 A/B 材料已直接提供候選清單（`s0-probes/p5_ab_material.md`），飽和命中不能補此缺口。
- S0 P3 報告及 `s0-probes/p3_blocks.out:3` 有 untrusted 32,000 bytes／project 跳過證據；master S3/SM-4/5 未承接 trust 軸。須加 supported/degraded 狀態與部署後驗收，不自動變更 trust。
- `scripts/deploy_agents.py:11-12,59-63` 明示 Claude 不經 bundle，target 只有 ZCode/Codex/Muse；`rules/AGENTS.md:21` 明示原始 rules symlink 即時同步。user 澄清「claude code 本身就用 rules, BUNDLE DEPLOＹ 不會影響 calude.md」後，僅修正 master 的「四投放」及 rank 適用範圍；不採 reviewer 提議的 Claude adapter 改造，原生 rules 路徑是本輪明確約束。
- 決策 10 的固定開頭與禁引號，和已批准 P5 B3/B5/B6/B8 樣本有張力；S1 lint 須以批准樣本作正例，機械文法邊界需明確。

已排除：S0 report 頂表的 P6 deferred 已被尾端結案補記取代；不可再報 Codex probe 未執行。其 probe 是否能單獨歸因 knob，是不同證據問題。

回寫位置：核心設計、Findings 17–20、受影響載體、SM-1/2/4/5、S1/S3/S5/S6 承接約束、整合策略 no-go 限定。原 findings 1–16 為前輪紀錄；其舊行號與中間預算不作本輪權威，現行段落為準。

| 維度 | 本輪結果 |
|---|---|
| F1 完整性 | 補無提示觸發驗收與 trust 分支；詳細實作仍留子 EP |
| F2 合規 | 情境句不得窄化為固定 prefix；禁引號與 B5 衝突待確認 |
| F3 一致性／架構 | 保留載體分立、memory-audit 引擎／instruction-* 工具分工；區分三端 bundle 與 Claude 原生 rules |
| F4 遺漏 | 部署消費面獨立驗收；不要求 blueprint 提前展開全量測試檔案 |
| F5 場景 | 補自然任務、負例、切片外、compact 接續、trust/degraded；no-go 不可改口徑自動通過 |

證據限制：本次讀 master、S0 EP/report（含尾端補記）、P5 A/B 原始材料、P3 留存輸出及現行 deploy/rules 說明；Muse trust 為留存證據，未重跑 harness。P6 尾端探針成功沿用報告，不宣稱本輪重驗或可由單一尾端可見性完全隔離 knob 因果。獨立 reviewer 確認 graph.db 在場，工作以 Markdown 合約及指定腳本直接閱讀為主，沒有全 repo 動態依賴窮盡宣稱。未實作、未部署、未改 trust、未改 backlog、未 commit。

待決僅文法引號：保留禁引號並改 B5 表達，或將禁令限於實證引句而允許指令引句。已在 S1 回寫，不留待實作者猜。
