# 工單：S4 直做三項＋dispatch 協議補入＋WO-1 審查三小修（WO-2）

> 定位：ai-rules 文檔七處小手術批次——S4 三項（背景句 pointer／相對 import 行／at-skill miss codify）＋B-1/B-2 dispatch 協議（agents/AGENTS.md）＋WO-1 acceptance review 三項小修。

## 紅線（違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡——止步於 working tree 編輯
- 只准動「範圍限定」節列出的 7 個檔案
- 禁把產物寫到 /tmp 或 repo 外；驗證一律管線組合不落檔
- 新增內容禁版本號／日期／統計數字（元資訊禁止）
- model id 與容量數字不得出現在本工單觸及的架構層檔案（解析表檔除外，見範圍註記）

## 目標（一句話）

把 EP 的 S4 三項、Build 期新發現 B-1/B-2（dispatch face 與三態判定）、WO-1 審查 F-1/F-2/F-4 三項小修，一次批次落進七個檔案。

## Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`
- base commit：`63f2041`；**working tree 已有 WO-1 的未 commit 修改**（rules/model-routing.md、skills/model-routing/SKILL.md、agents/AGENTS.md、skills/_common/work-order.md 新建＋本弧任務家 untracked）——這是既有狀態，你的編輯在其上進行，不是衝突

## 必讀（按序，絕對路徑）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-03-air13-unified-subagent-arch/ep.md`——讀「Build 期新發現」表 B-1/B-2/B-3 與「委派工單 reviewer record」表 WO-1 列（F-1/F-2/F-4 定義來源）
2. 各目標檔現況（見範圍限定清單，逐檔讀相關段落）

## 已決策（勿重辯）＋矛盾例外

1. **S4-1 review-engine 背景句＝最小 pointer**：只在審查執行預設段補一行「審查類命令 spawn agent 預設背景跑（細則見 rules/tool-discipline 背景執行段）」——不重述細則（tool-discipline 與 agents/AGENTS.md 已兩處承載，此為第三載體只做導航）
2. **S4-2 python-standards 相對 import 行**：在 `__init__.py` 禁 re-export 段的「遷移既有 re-export」小節附近補一行——語義：「re-export 遷移掃消費端時，相對 import（`from .submodule import X`）消費者同樣要改成完整路徑——相對 import 穿透 `__init__` 邊界，rg `from \.` 也要掃」
3. **S4-3 at-skill miss codify（允許 no-op）**：先讀 `/Users/ctai/.zcode/cli/memories/projects/ai-rules-01610fbb20315a8b/memory/at-skill-zcode-cron-gaps.md`（唯讀）提煈「排程 miss／cron 平台落差」教訓，再對照 `skills/at/SKILL.md` 現況（task hint＋resume 時 STATE＋git 重建已在場）——**現有流程已覆蓋該教訓則 no-op 並附行號證據，不為湊數重寫相近規則**；確有缺口才補一句/小節（自包含，禁引用 memory 檔名）
4. **B-1 dispatch face**：agents/AGENTS.md「Thin forwarder 與 flag profile」節內新增小節「dispatch face 與收法」：(a) muse 委派預設＝**主 session 直呼 bridge CLI**（背景 Bash＋`.muse-bridge/jobs.json` 輪詢；wrapper agent 形態為別名，續用時收法＝resume-to-poll）——理由：wrapper 會在 runtime 未終局時提前 complete（生命週期錯位，本弧實證）(b) codex 委派＝wrapper＋標準收法 resume-to-poll＋prompt 內預寫 env fallback（plugin root 路徑）
5. **B-2 三態判定表**：同小節內，三欄表（症狀／證據／處置）：①transport 未啟動（env/module 錯誤、log `MODULE_NOT_FOUND` exit 1）→ 可安全重派；②transport 在跑、wrapper 已收（jobs.json running／ps 進程在）→ poll 收集，**禁重派（雙跑）**；③transport 死中途、wrapper 空轉（進程亡、jobs.json 停滯）→ 機械驗收（working tree＋jobs.json 終局）＋TaskStop wrapper
6. **F-1**：skills/model-routing/SKILL.md external-runtime family 表 GLM 行的 model/effort 欄改「見 tier 表」（容量對比與備註欄保留）——消除同檔雙維護點
7. **F-2**：rules/model-routing.md 尾部 on-demand pointer 句的枚舉補上 external-runtime family 解析表
8. **F-4**：skills/_common/work-order.md 驗收節（第 8 節）清單標題或首行加「（例——填單時替換為本工單實際命令）」marker，與目標節「例句型」標法對齊

**矛盾例外**：發現檔案現況與上述決策具體衝突時，停下舉證，不自行改設計。

## 範圍限定

- 動：`skills/review-engine/SKILL.md`、`rules/python-standards.md`、`skills/at/SKILL.md`、`agents/AGENTS.md`、`rules/model-routing.md`、`skills/model-routing/SKILL.md`、`skills/_common/work-order.md`
- 不動：其他一切（含 memory 檔——唯讀；rules/tool-discipline.md；skills/CLAUDE.md）

## 工具接線

- bash（cat/rg/ls）；字串搜尋一律 rg；禁 CR 寫入面；禁 /tmp 落檔

## 驗收（命令＋預期，逐條實跑）

1. `rg -n "背景跑" skills/review-engine/SKILL.md` → ≥1 命中（S4-1）
2. `rg -n "相對 import" rules/python-standards.md` → ≥1 命中（S4-2）
3. S4-3：`rg -n "<你補的教訓關鍵詞>" skills/at/SKILL.md` 命中，**或**報告附 no-op 判定＋`skills/at/SKILL.md` 行號證據
4. `rg -n "dispatch face|直呼" agents/AGENTS.md` → 命中（B-1）
5. `rg -n "三態" agents/AGENTS.md` → 命中且三列齊（B-2，逐列核對症狀/證據/處置）
6. `rg -n "見 tier 表" skills/model-routing/SKILL.md` → 命中（F-1）
7. `rg -c "external-runtime" rules/model-routing.md` → 計數比現況 +1（F-2 尾 pointer 行）
8. `rg -n "填單時替換" skills/_common/work-order.md` → 命中（F-4）
9. 負向：`rg -n "muse-spark|gpt-|glm-" rules/ agents/ skills/_common/` → 零命中（現況已零，你的新增不得破壞）

## 證據紀律＋PII 禁令

每條驗收附完整命令與原始輸出；`git diff --name-only` 佐證範圍；報告禁 email／人名等 PII；宣稱 no-op 須附行號證據。

## 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（對應 git diff，與範圍限定對照）
2. 逐項落實說明（S4-1/2/3、B-1、B-2、F-1、F-2、F-4）
3. 驗收 1-9 命令與原始輸出
4. 偏差記錄
5. 未驗證項
6. 建議 reviewer 聚焦點
