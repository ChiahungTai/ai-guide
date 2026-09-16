---
card_id: MOS-22.2
task_baseline: 10de6050
title: StudyArea LLM 判定管線 lib 化——disposition→分K/日K 共用
report_type: study-notes
task_type: none
ep_path: ai-analysis/_tasks/09-03-studyarea-llm-lib/ep.md
---

<!-- section-group: {"id": "snapshot", "title": "0｜一句話＋快照", "sub": "interval-agnostic core lib，薄 adapter 還原兩域語義——零漂移"} -->
「StudyArea→圖/數值混合證據包→雙軌盲判→tags」已在 TWSE 208 全清實戰中打磨定型；本 EP 把它從 disposition 專用抽成 core lib。
208 可判讀全清・proposed 199＋9 held-out・四原則定案・雙軌共識 76%

<!-- section-group: {"id": "why", "title": "1｜為什麼要做分類（交易思想——user 原話）", "sub": "處置分類的產品是可推廣的自動判型器"} -->
> user（8/13，goal-and-constraints）：收斂/多頭拉回會持續許多K棒，然後會有個攻擊…根據分類看要套哪種**分K策略**。
處置分類天然要餵分K策略——這就是 lib 化的需求源頭。research-loop 的 ANNOTATE 瓶頸被解開後，整條 FOLD→策略鏈才通。

<!-- section-group: {"id": "pipeline", "title": "2｜管線全景（七組件——每件都是本週某個決策生的）", "sub": "位置與來源對照"} -->
| # | 組件 | 位置 |
|---|---|---|
| 1 | StudyArea model（時空錨統一） | research/study_set.py（lean 純值） |
| 2 | 特徵窗（窗口聚合單源） | classification_features.py:331 |
| 5 | 雙軌判讀（跨家族盲判） | kbar-form-analysis dispatch＋verdicts-{vision,muse} |
| 7 | Custody（proposed→overlay） | golden_writer/loader |

<!-- section-group: {"id": "evolution", "title": "3｜演化年表——這條管線怎麼被 user 一週塑出來的", "sub": "user 原話逐字＋後果"} -->
| 時刻 | user 原話（逐字） | 後果 |
|---|---|---|
| 09-01 23:06 | 「這不是要做一個分類器，這是要標記」 | 定調 tagging 而非分類器——今天的 lib 化正是這句的兌現 |
| 09-02 22:40 | 「同樣的圖片你也丟給 muse 判斷看看」 | quorum 雙軌誕生 |
| 09-03 13:13 | 「3669根本沒有拉回…抓1.5% buffer」 | 機械破線尺誕生→B2 S1 |
<!-- fold: evidence -->
完整時間軸 30 條帶 session 證據——含並行上限史（3+3）、額度天花板（1308）、muse 被採納/推翻案例全錄。

<!-- section-group: {"id": "principles", "title": "4｜四原則（B2 refit 的機器輸入——本 EP 的語義地基）", "sub": "四原則定案"} -->
- ① 日線自足——週K 只作修飾不推翻主類（8429/6573 各被自己 focus-only 推翻）
- ② 拉回＝趨勢前提 AND 破 10MA（1.5% buffer）
- ③ 收斂三條件——糾結＋中長收口＋量縮放量；不足→其他
- ④ 乖離時態——主類記窗極值、修飾記「已回 10MA」

<!-- section-group: {"id": "plan", "title": "6｜EP 三段與驗收設計", "sub": "S1 core lib → S2 disposition adapter → S3 strategy adapter"} -->
SM-1 零漂移：舊路徑 vs adapter→core 逐案 final_tags 等值——**非 0 即 blocker**。
最大風險＝區間語義：日K MA25＝25 日；分K MA25＝25 棒≈125 分鐘——**不是月線**。防線：圖題＋prompt header 雙重宣告 `K線週期：5m`。
