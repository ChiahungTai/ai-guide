# AIR-66 review 帳本（branch air-66）

## Header

- 任務：AIR-66 muse user bundle 36KiB 自限（guide/三肥段瘦身＋MUSE_USER_BUDGET gate＋cr-audit R8/R5 合流）
- 審查形態：user 指示「改好給 muse codex 看看，看會不會刪太過頭」——delegate-bridge 雙 runtime 審（muse job-mtundxjo-mk5pb6／codex job-mtune2gr-knrwkj），標的＝slim-diff.txt（366 行）
- verdict 全文：`.agent-tmp/air66-review/{muse,codex}-verdict.md`

## Findings 與 judge 決策

| # | 來源 | finding（嚴重度） | 決策 | 處置 |
|---|------|------------------|------|------|
| 1 | muse 🟡＋codex 🟡共識 | crash-only 適用域「量化交易、高頻」被刪——集合縮窄非壓縮；guide 量化鐵律指過來 | ✅ 採納 | qc 回補「適用量化交易、高頻、實時風控、批次」 |
| 2 | muse 🟡＋codex 🟡共識 | `.at-contexts/` 7d、`.review/` 30d 保留期被壓掉；at/SKILL.md:69 指回 rule 形成真斷鏈 | ✅ 採納 | cc Agent 注入③回補完整 TTL（7d/7d/30d） |
| 3 | muse 🟡＋codex 🟢 | vision-review「可裁切/跨圖佐證/禁單發 image-analysis」無深層可接——pointer 不完全 | ✅ 採納（codex 落點建議：搬 agent 定義） | 契約寫入 agents/roles/vision-review.md 紀律段＋sync_agents 三份部署驗證 |
| 4 | muse 🟡 | 消費端驗證真資料例（watchlist/除權息真 K——silent-corruption 高危區）被壓掉 | ✅ 採納 | qc 消費端段回補真資料例 |
| 5 | muse 🟡 | acceptance-evidence「低風險不需六層」「L5 自畫靶」疫苗隨「與既有規則的關係」節同刪 | ✅ 採納（回補精簡形態非整節） | ae「禁用低層…」行回補兩疫苗一句 |
| 6 | codex 🟢 | 4 個 heading 錨點被砍/改名，5 個 skill 用舊段名定位（execution-plan/implement/symbol-query-routing/tour-bootstrap/test-driven-development）＋audit-test 稱「表格」實已散文 | ✅ 採納（heading 成本低於改 5 引用） | 「變更規模分級」「## 工具選擇原則」「zsh 動態 flag 組合」「### 誤用警告」heading 回補；audit-test「表格」→「段」；rg 雙端命中驗證 |
| 7 | codex 🟢 | guide 評估要求少「里程碑」——獨立 requirement 非排序可推 | ✅ 採納 | 回補「里程碑」 |
| 8 | muse 🟢 | MUSE_USER_BUDGET 注解緩衝數字對不上（宣稱 ≥3.2KiB，實 ~3KiB） | ✅ 採納 | 注解改 ~3KiB＋project layer 24.1KiB 正確值 |

## 不採納

（無——兩家 findings 全數成立採納）

## 收斂帳

- 回補 8 項 ≈ +396B（37,252B 峰值）→ advisory floor 再砍（outward/python-standards/context-management/symbol-query-routing/model-routing/_ai-behavior/guide/td/qc/must-execute 微刀）→ **終態 36,752B**
- 省 40,092−36,752＝**3,340B ≥ advisory 5% floor（3,318B）**；7.5% target（35,136B）未達——advisory「佳」非必達，水位落 warn 區間，如實標報
- mosaic 串接 36,752+24,660+825＝62,237 ≤ 65,536（緩衝 3,299B）
- 驗證：3-way cmp 一致＋288 passed＋check_single_source 10 invariants 綠＋heading 錨點 rg 雙端命中＋vision-review 契約三份部署命中
