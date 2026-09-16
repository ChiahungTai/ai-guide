# S5 子 EP：instruction-* skill 家族重構

> **ep_type**: implementation（docs/refactor mode——四 skill 對齊統一機制＋引用面同步；writing 28KB 瘦身走精煉紀律，無 production 行為碼；無 TDD）
> **parent**: ai-analysis/_tasks/09-08-context-lifecycle-unification/ep.md（master blueprint，S5 段）
> baseline: 28734c5

## Context

承接 S2（條目化）與 S4（已驗證四動流程）的輸出；writing/init 可與 S3 部分平行（staging 保留），clean/sync 須在 S4 後。依賴 S2/S4。

## 做什麼

- writing＝寫入文法權威：吸收觸發 desc 文法（S1 定案可執行部分）＋層級判準表＋座標欄位規範；28KB 瘦身重構（禁引號待確認條款未裁定前不寫入拒寫規則）。寫入門檻：預設少寫——既有載體有位置就更新，一次性資訊留任務文件，只有新增 memory 或全域常駐內容才做嚴格必要性判斷（呼應既有一句話測試/六問/確定才寫）。
- init＝新專案載體初始化：依層級判準表產 user/project/目錄層骨架＋座標欄位。
- clean＝精煉/淘汰工具：承接 S4 已驗證流程（非自創新流程）。
- sync＝掃描/新鮮度：跨 lane 投影新鮮度（deploy_bundle_freshness 一般化；執行 S4 引擎定義的動作）。
- 引用面同步：`rules/instruction-writing.md`、`rules/context-management.md`、`rules/AGENTS.md`、`ai-development-guide.md`、`skills/CLAUDE.md`；SKILL.md 原檔先快照進 version 目錄。

## 驗收

SM-8（init 產物 lint）/SM-9（已裁定機械可驗部分；批准樣本正例全過）＋引用面 rg 零殘留＋clean/sync 重構驗收：沿用 S4 證據案例經改寫後入口重跑，核對候選→判準→處置→投影→消費端驗證全鏈（含證據不足不處置案例）；S4 舊工具證據不得直接沿用。

## 產出

`s5-report.md`（四 skill 變更對照＋引用面核對表）。
