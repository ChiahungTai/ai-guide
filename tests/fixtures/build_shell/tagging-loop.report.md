---
card_id: 09-02-tagging-machine-loop
task_baseline: 60f3f10d
title: tagging 機器循環 — EP 導讀
report_type: task-plan
task_type: flow
ep_path: ai-analysis/_tasks/09-02-tagging-machine-loop/ep.md
---

<!-- section-group: {"id": "onto", "title": "① 本體論（2026-09-02 定案——最高層，凌駕一切設計）", "sub": "condition ─組成→ tag ─組合→ setup"} -->
**tagging**＝給 tag 的行為（標記平台職責）。**tag**＝標記單位，**平級、不分主副**（明令禁這詞）。**setup**＝多 tag 組合。
標記的產物是 tag set（可疊加）：多頭拉回・負乖離修正・大型拉回——1435 這種案從此不用擠進一個詞。
`alpha_forge/condition_mappings.yaml` v4.1 就是現成的 tag 註冊表——中文 tag 名、每個 tag 帶 conditions（欄位/運算子/門檻）、YAML 驅動。本弧是**接上主幹，不是新造**。

<!-- section-group: {"id": "why", "title": "② 為什麼＋五必修", "sub": "動機：人看 208 案已是極限，升級成機器循環"} -->
```
①語料   user 裁 tag sets → golden ≈250 案
②引擎   naive 規則版（已落地 64.6%）＋全池掃描
③漏斗   機器掃 → LLM 補低信心/分歧 → user 裁難案
```
深度審查五必修（不補會撞牆）：
- P0 held-out 六類空缺——eval/test 密封語料是三類的，S1 補標前 B4 對新 tag 無牙齒
- P1 漏斗經濟學未量測——「LLM 量掉一個數量級」是宣稱，S2 量出真實分歧率才算數
- P1 單選鍵遷移——schema/判決書全鍵在單選三類上，S6 換樹前必須完成

<!-- section-group: {"id": "assets", "title": "③ 現有資產", "sub": "接上既有主幹，非新造"} -->
| 資產 | 狀態 | 說明 |
|---|---|---|
| tag 註冊表（condition_mappings.yaml） | ✅ 既有主幹 | 11 category、中文 tags、YAML 換檔＝rolling 機制本體 |
| 首批六 tags | ✅ | 收斂/多頭拉回/負乖離過大/正乖離過大/低調吸籌/其他 |
| naive 引擎 v0 | 🟡 收案中 | rule_classifier.py 級聯；審查 R1 slice bug 修復中；64.6% |

<!-- section-group: {"id": "map", "title": "④ 全案地圖 S0–S7", "sub": "你的五步映射：①＝S1、②＝已落地＋S2、③＝S5、④＝S6、⑤＝S7"} -->
```
        ┌─→ S1 語料整備 ─────────────┐
S0 收案 ─┼─→ S2 聚合上抽＋全池掃描 ─┬─→ S5 漏斗接線 ─┤
     │                            └─→ S4 註冊表收斂 ─┤
     └─→ S3 multi-tag annotate 改造 ────────────────┴─→ S6 refit＋held-out ─→ S7 實體化
```
並行：S1（人裁）與 S2/S3（工程）互不阻塞。S4 等兄弟線 commit。

<!-- section-group: {"id": "risk", "title": "⑥ 風險與退場", "sub": "致命風險先量再接"} -->
| 風險 | 等級 | 退場 |
|---|---|---|
| naive 全池分歧率過高→LLM 沒縮 | 致命 | S2 先量再接；無效益回歸現行夜跑 |
| refit 過擬合（薄 tag：正乖離 6/收斂 8） | 高 | B4 held-out 唯一採納依據；退回 naive |
| 註冊表 per-bar vs 窗口聚合格式不相容 | 中 | S4 先驗證格式；不通則定義橋接層 |

<!-- section-group: {"id": "decide", "title": "⑦ 已定案不得重辯（2026-09-02）", "sub": "乾淨重寫版，含 F1-F17 審查吸收表"} -->
- **本體論**：condition → tag → setup；tag 平級禁主/副；label 留給 ML
- 首批六 tags＋修飾 tags 全平級；1435 型＝tag 疊加
- 主幹＝condition_mappings.yaml（既有系統，接上非新造）
- 機器 tagging 三層動線（naive→refit→LLM 補難案）——訂閱改制保險
