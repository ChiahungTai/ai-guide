# S3 Report：投影器與層級軸（ai-rules 側；mosaic 主案出判準）

## 投影決策（deploy_agents.py）
- scope∩ 機制保留；新增 per-target 配置（路徑＋scope＋排除＋獨立 gate）＋muse 變體（draft-3 A 案 5 排除，rules 單一源不動，改名即測試大聲失敗）。
- rank 排序未做：需 S2-expansion 的 rule 欄位（已登記延期），pilot 不硬造。
- muse gate 50KiB：实测變體 51,180B 通過（餘 20B—— hair-trigger，按設計 fail-loud；後續 rule 增長即觸發 slim 紀律）。
- codex/zcode 面：僅 slim 段移除（重建舊 bundle diff 驗證，無意外移除），內容零排除。

## Slim 清單（bundle 標記；Claude 源碼面不受影響）
acceptance-evidence Claim 詳例＋關係段／design-thinking 例句＋信號＋載體＋mosaic 範例／llm-output 單檔＋namespace 細節／collaboration YAGNI（改 1 行指針）／edit 兩示例／must-execute POC 段／edit 原理。總計 79,241→51,180（muse）／73,962（另兩端）。全數有 skill 家或教義背書，post-build 複核。

## 探针（`s3-probes/deploy_probe.out`）
三端 gate＋哨兵全 PASS；Claude symlink 未動；池 31,309B＜65,536；lane 64,825≤65,536（餘 711B，專案層增長即重算）。

## Trust 分支
三端部署＋Claude 抽驗分立；untrusted/project 省略 degraded＝已設計、runtime 未驗（記缺口，不冒充）。

## draft-3 吸收（結案）
muse 64KiB 截斷裁決＝A 案＋本段實作（變體 51,180B＋50KiB gate＋部署後探针）。B 案全域瘦身不採（四家陪葬）；C 退出已排除。Lane 合流語義（user＋project 共享 64KiB）已入探针 lane 數學。draft-3 標已吸收。

## mosaic 判準表（mosaic 側 session 執行，本 EP 只出判準＋驗收）
1. 先 mosaic root 組成分析（必中集/下沉目錄/觸發比例），S0 幅度為候選。
2. 每下沉單位：原保障行為／新位置入口／上層短指引／盲測任務；適用範圍≠目錄。
3. 驗收：代表性任務行為對照（bytes 不判）＋SM-2/3/4/5；S4 後才擴大。
4. Owning：mosaic 側 session；user 可改指。

## 行為抽查（1 盲探針）
變體面提問「只做一次單測能上嗎」→ 回 L2 塌縮＋消費端驗證＋L4＋錯誤路徑（修復前被截斷的尾巴今可達）。通過。

## 版本快照（回滾面）
- 部署前三端同 hash `c132afea`（單一舊 bundle）；部署後 per-target 各異（探针記錄尺寸）。
- Script＋tests：`scripts/deploy_agents.py`、`tests/test_deploy_agents.py`（26＋4＝全綠，另 single-source 全綠）。
