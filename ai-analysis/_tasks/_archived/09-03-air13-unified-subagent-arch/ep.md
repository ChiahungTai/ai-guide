# AIR-13 統一 external-runtime subagent 架構 — Execution Plan

> **ep_type**: implementation（**docs mode**——本 EP 變更全為 `rules/`、`skills/`、`agents/` 下 `.md`，無 `.py` callable 符號；驗證=rg 殘留＋跨檔一致性＋`/consistency`＋deploy cmp）

baseline: 63f2041fbc33ff399559ba7d460146752df1947a

關聯卡：AIR-13（backlog/tasks/，狀態 In Progress）

---

## 實作總覽

把 09-03「三臭皮匠」（GLM＋muse＋codex 三方獨立調查）合併定案的**統一 external-runtime subagent 架構**落地：三層（路由表／介面層／協議層）＋治理契約，並以首批真實工單示範新架構。變更全為文檔（rule/skill/registry/模板），其中 S5 的兩項內容手術經 muse 工單委派執行（背景跑），GLM reviewer 按新契約驗收——S5 同時是新架構的首用量測批。

**核心原則（全程約束）**：
- **model id 單一源（兩層契約）**：①權威值（model/effort/容量現值）只在 `skills/model-routing/SKILL.md` 解析表——model 演進只改一處；②`agents/zcode/` frontmatter pin 是既有允許的 materialization（治理歸 agents/AGENTS.md），須與解析表一致（收尾做一致性比對）；③本 EP 新增內容（rule external-routing 節／flag profile 表／工單模板）只准 family（GLM/muse/codex）與 profile 詞彙，**禁 model id 與容量數字**（與 model id 同演化節奏）
- **subagent 派發一律背景跑**（全域規則 rules/tool-discipline 已承載，本 EP 不重述、只引用）
- 元資訊禁止（instruction-writing）：新增段落不加版本號／日期／統計

---

## 段落 0：全域研究摘要（本 session 三臭皮匠調查，已執行）

**方法**：GLM 主 session 實機掃描（`muse --help`/`muse skills list`/jobs 帳本/ref-docs 鏡像）＋ muse 委派調查（bridge job `job-mtlfet2m`）＋ codex 調查（thread `01a066fa`）三份獨立報告合併。以下為證據要點：

**使用軌跡**（`.muse-bridge/jobs.json`＋`jobs/*.jsonl`，09-02~09-03，11 jobs）：
- 分類計數（11 筆全核對）：review×5（3 有 verdict＋1 completed-但外層誠實回報失敗＋1 interrupted）＋sandbox-error×2（早期 prompt 誤含委派語言→muse-in-muse EPERM）＋advisory×1（memory 池數字盤點，品質佳）＋implement×2（AIR-14 post-build docs 鏈、AIR-18 L1-L9 手術批——**均完成且嚴守止步 commit 前，GLM 獨立驗收過**）＋本弧委派調查×1
- 失敗模式定案：ledger status ≠ 工作成果（`completed` 可為「外層誠實回報失敗」；exit 0＋verdict needs-attention 並存）→ transport status / verification / review verdict 三欄分立

**能力面**（ref-docs/harness/meta/ 鏡像＋CLI 1.0.2 `--help` 實機）：
- 文檔載明：session messaging（interactive 限定，headless 不適用）、workflows（aarch64 缺引擎死路）、hooks 13 事件、observers×4（含 Verification——但同 runtime，**不可替代跨家族 reviewer**）、`/goal` requirement-by-requirement check（interactive surface，headless 以工單話術補償）、`muse exec --session-id` headless resume、`muse export/trace`
- **僅 --help 可見（文檔鏡像落後，勿因「文檔無」否定）**：`--disable-write`、`--disable-shell`、`--agents <JSON>` overlay、`--permission-profile`、`-w/--worktree create|existing`、`--context-compaction-strategy`、`--max-tool-output-bytes`、`--image`（muse 具視覺輸入能力）
- bridge `task` 現只暴露：model/effort/steps/network/trust-workspace/yolo/sessionId——上列 flag 多數**未暴露**（→ bridge roadmap，見收尾）

**治理前車之鑑**：`~/Github/muse-plugin-cc/FIX-S3-R2.md:49`——routing policy 混入 transport agent 造成 trigger collision 與自相矛盾，後移出。D2 thin forwarder 的實證依據。

**用語勘誤（user 09-03 澄清，落地時勿再生）**：09-02 所謂「PAYG 被裁定排除」是誤傳——user 從未用 PAYG（講的是 coding plan 訂閱）；API-provider 接線議題屬 **muse-plugin-cc 側**，本 repo 架構不對 PAYG 做任何特化（既不排除也不設計）。三家現行載體全為 flat-rate（GLM=ZCode 內建、codex=ChatGPT OAuth、muse=訂閱 5h 窗）。

**風險假設**：
- 中｜bridge flag 可用性：advisory profile 的 `--disable-write`、impl 隔離的 `-w worktree` **bridge 未暴露**——EP 對策：profile 文檔標「bridge 暴露前以工單紅線（S3 模板首段）替代」，flag 暴露列 muse-plugin-cc roadmap（本 EP 只記錄不改跨 repo）
- 中｜批次項現況不明：queue 記錄顯示部分批次項（review-engine 背景句、python-standards 相對 import 行）可能已部分承載——各段先 rg 現況查證再動筆，已承載則標 done 不重加
- 低｜model id 漂移：靠「解析表單處維護」紀律＋收尾 rg 驗證（架構層 `rg "muse-spark|gpt-" rules/ agents/ skills/_common/` 應零命中）

---

## UC 盤點（docs mode：受影響 rules/skills 清單）

### Backlog 關聯
- AIR-13（本卡，In Progress）——EP 即其執行計畫；無其他新建卡（能力屬治理文檔，非 library UC）

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md（元專案）→ 跳過

### 掃描範圍
- `rules/model-routing.md`、`skills/model-routing/SKILL.md`、`agents/AGENTS.md`、`skills/review-engine/SKILL.md`、`rules/python-standards.md`、`skills/at/SKILL.md`、`rules/quality-constraints.md`、`skills/cr-query/SKILL.md`、`skills/implement/SKILL.md`、`skills/post-build/SKILL.md`、`skills/_common/`（模板新居民）、本弧任務家產物（`work-orders/`、EP 內 review record 與量測節——S5 定義）

### 既有 UC 狀態
| 能力（文檔形態） | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| model-routing 角色→tier 解析 | ✅ | rules/model-routing.md＋skill | 更新 | 擴 external-runtime routing 節（family 軸） |
| agents registry 治理（兩跳解析） | ✅ | agents/AGENTS.md | 更新 | 增 flag profile 治理；thin forwarder 定案 |
| 委派工單形態（BUILD-S3 式） | ✅（住 muse-plugin-cc） | BUILD-*.md/FIX-*.md | 遷移泛化 | 本 repo 固化 `_common/work-order.md` |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| external-runtime 委派路由（family 軸＋eligibility gate＋reviewer 契約） | 📋 | rules/model-routing.md＋skills/model-routing/SKILL.md |
| foreign-runtime 工單模板 | 📋 | skills/_common/work-order.md（新） |

---

## Scenario Matrix（docs mode：觸發/預期以 rg 命中與殘留掃描表述）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 主 session 判斷任務是否委派 | 任務規劃時查 routing 節 | 五條 eligibility gate 逐條判（決策凍結／條款客觀化／單一 writer 無待決／主價值=承接 implementation loop／環境可啟動）；任一不過→主 session 直做；「≥30 分鐘」僅提醒信號非機械判準 | 無 | 委派路由 |
| SM-2 | advisory 工單派 muse | 掃描類任務 | profile=advisory：read-only 紅線在工單首段（bridge 暴露 `--disable-write` 前由紅線承載）；effort 依解析表（機械掃描低檔） | 無 | 工單模板＋profile |
| SM-3 | muse 完成回報 → review | implement 工單收尾 | reviewer 契約：讀料順序 work order→diff→evidence→writer report 最後；產出 accept/reject/needs-fix record；無 record 不得結卡 | reviewer record | reviewer 契約 |
| SM-4 | model 家族改版（spark-1.3/gpt-6/新 GLM） | 模型升級日 | 只改 `skills/model-routing/SKILL.md` 解析表；架構層零改動（rg 驗證零 hardcode） | 解析表 | model 演進防漂移 |
| SM-5 | 大 context 工單誤考慮 codex | 工單 sizing | 解析表 capacity 註記：codex 約 200K 禁大工單→大 context 任務改派 muse（長 context 面強） | 無 | 委派路由 |
| SM-6 | 視覺驗收考慮 muse | 圖檔判讀任務 | family 表註記 muse 具視覺能力（`--image`）；in-harness vision-review（GLM vision pin）仍為預設路由，muse 為跨家族備選 | 無 | 委派路由 |
| SM-7 | sandbox-error 重試衝動 | 委派啟動失敗 | gate 鐵則：禁以 `--yolo` 賭重試（實證無法突破父層沙箱）；分類走 auth-failed/environment 分類，修因後重派 | 無 | 委派路由 |
| SM-8 | 派單前 bridge 未就緒 | setup.json 非綠／binary 缺場 | preflight：主 session 自主補跑 setup（既有定案）；仍非綠→降級主 session 直做＋EP 記錄 | setup.json | 委派路由 |
| SM-9 | muse 5h 窗口中途耗盡 | job 中斷／usage-limit | 以 job 的 session id 走 `muse exec --session-id` resume 接續（baseline identity 欄位支撐）；**禁重派新工單（雙跑）**；當日額度盡→排下窗口 | jobs.json＋session id | 工單模板＋契約 |
| SM-10 | job 卡住／wrapper 空轉 | wrapper complete 但底層進程仍在跑或已死 | 機械驗收優先：jobs.json 狀態＋ps 進程＋working tree 落地證據；死進程→TaskStop wrapper 收場，不重派 | jobs.json＋ps | 委派路由 |
| SM-11 | reviewer 不可用／record 不合格 | reviewer session 失敗或 record 缺欄位 | 暫停不結段（無 record 不得結卡）；重跑 reviewer 或主 session 補審補齊 record | EP S5 record 表 | reviewer 契約 |
| SM-12 | needs-fix 無限重工 | 修輪反覆 | 封頂 3 輪→停卡回報 user 裁決（post-build 先例） | EP 量測節輪次計數 | 工單模板 |

---

## 段落劃分原則

依賴序：S1（路由表）→ S2（registry profile，引用 S1 family 詞彙）→ S3（工單模板，引用 S2 profile）→ S4（獨立直做批，可與 S1-S3 平行）→ S5（首批委派，依賴 S1 契約＋S3 模板）。語義約束：三段共用「family／profile／gate」詞彙，定義以 S1 為單一源，S2/S3 只引用不重定義。

---

## S1：model-routing 擴 external-runtime routing 節

### Context
- 背景：三家族（GLM in-harness／muse／codex）分工已事實存在但無 routing 真相源；AIR-13 D1 定案（落 model-routing，定位=external implementation-runtime routing policy，非 tier→model 映射擴充、非 registry pin）
- 依賴錨點：`rules/model-routing.md`（定義端：角色→tier 表＋兩跳解析；消費端：`agents/AGENTS.md` 治理段、`skills/model-routing/SKILL.md` 解析表）——Edit 前 rg 驗證現段落結構
- 語義約束：與 S2 共享 family/profile 詞彙；與 S3 共享 gate 名稱
- 基礎設施盤點：既有「角色 → tier」表＋tier 詞彙單一源句；新節複用同一詞彙風格

### 修改要點（docs mode，無 pseudo code）
1. `rules/model-routing.md` 新增一節「External-runtime routing（family 軸）」，內容三塊（精簡、每條一行級）：
   - **family 表**：`角色 → family → profile → 備註`（實作→muse/implement；external second-opinion review→muse/review；in-harness acceptance reviewer→GLM——驗收委派工單的主審，兩種 review 的角色邊界在本節一句定義，避免混淆；診斷 rescue→codex/implement；advisory 掃描→muse/advisory；機械驗證/探索→GLM/lite；視覺→GLM vision〔預設〕，muse 具視覺能力為跨家族備選）。容量只寫相對措辭「容量不足的家族禁派大工單——現值見解析表」，**數字與型號例子不入 rule**（易過時事實）
   - **五條 eligibility gate**（SM-1 措辭）＋「≥30 分鐘=提醒信號」＋ sandbox-error 禁 `--yolo` 賭重試（SM-7）
   - **reviewer 交接契約**：muse/codex 完成回報固定欄位（jobId 或 thread id／base commit／改檔清單／實跑驗收命令與原始輸出／未驗證項）；reviewer 讀料順序 work order→diff→evidence→writer report 最後讀；產出 accept/reject/needs-fix；無 reviewer record 不得結卡
2. `skills/model-routing/SKILL.md` 解析表新增 external-runtime 段：family→(model, effort, 容量現值, 備註) 具體值——**唯一 model id 與容量數字落腳處**（容量屬「需現況查證」性質，隨 model 世代更新）；加一行維護原則（model 演進只改此表）。**必做同步**：skill frontmatter description 觸發詞（加 external-runtime／委派／工單）＋`skills/CLAUDE.md` 索引行——此為語義必然變化，非條件項
3. rule 尾部 tier 詞彙單一源句補 family 詞彙歸屬（單一句，不展開）

### 驗證策略（docs mode）
- `rg "external-runtime|eligibility|reviewer record" rules/model-routing.md skills/model-routing/SKILL.md` 命中且語義一致
- 新增內容掃描（與整合策略同口徑三路徑）：`rg "muse-spark|gpt-|glm-" rules/ agents/ skills/_common/` 零命中（family/profile-only）；materialized pin 一致性：`agents/zcode/*.md` frontmatter model 值逐一與解析表比對（兩層契約②）
- `/consistency rules/model-routing.md` 過

---

## S2：agents/AGENTS.md registry 治理段——thin forwarder 定案＋flag profile

### Context
- 背景：AIR-13 D2 定案（thin forwarder 維持；特化長 spawn flag profile 不長 agent 定義）；實證鑑=`~/Github/muse-plugin-cc/FIX-S3-R2.md:49`
- 依賴錨點：`agents/AGENTS.md` 治理段（消費 S1 family 詞彙；`agents/zcode/` 七定義檔現況為 GLM tier-pinned——不動）
- 語義約束：profile 三型（advisory／implement／review）詞彙定義引用 S1，不重定義

### 修改要點
1. 治理段新增小節「Thin forwarder 與 flag profile」：
   - 原則一句：muse/codex 家族入口=單一 thin forwarder（工單即介面），**不長特化 agent**——routing 混入 transport agent 的前車之鑑（FIX-S3-R2）
   - **flag profile 表**：`profile × family → spawn 參數`（advisory：read-only 紅線〔bridge 暴露 `--disable-write` 前由工單紅線承載，暴露後改 flag〕；implement：muse=trust-workspace、codex=workspace-write；review：muse=bridge `review` 子命令〔schema verdict〕、codex=`--output-schema`）——flag 具體值引用 skills/model-routing 解析表，此表只寫形態
   - 外部 runtime flag 未暴露項的對策句（紅線替代）＋「bridge roadmap 記錄在 muse-plugin-cc 側」
2. registry 職責句**直接寫入** external-runtime 面（09-03 審查預跑定案：`agents/AGENTS.md` 現況零 muse 字樣、僅一處 codex-rescue 命中——無需再判斷）：補 profile 指針一句

### 驗證策略
- `rg "thin forwarder|flag profile|FIX-S3-R2" agents/AGENTS.md` 命中
- 與 S1 詞彙零 drift（`rg "advisory" rules/model-routing.md agents/AGENTS.md` 兩處語義一致）
- `/consistency agents/AGENTS.md` 過

---

## S3：skills/_common/work-order.md——foreign-runtime 工單模板（新檔）

### Context
- 背景：AIR-13 D3 定案（模板固化＋泛化為 muse/codex 共用）；形態源=muse-plugin-cc BUILD-S3/S5＋AIR-14/AIR-18 實戰工單＋三臭皮匠修訂（紅線首段／證據紀律／baseline identity／矛盾例外／PII）
- 依賴錨點：`skills/_common/` 既有共用子範本慣例（`state-md-write.md`、`illustrate-html-mode.md` 等——同層新居民）；消費端=未來委派工單撰寫（S5 首用）＋`skills/model-routing`（routing 節指向此模板路徑）
- 語義約束：節名與 S1 契約欄位名對齊（reviewer 讀料順序、交付欄位）

### 修改要點（模板結構——十節硬欄位）
1. **紅線（首段）**：預設禁 `git add`／commit／push／改卡狀態（「止步 commit 前」不夠——AIR-18 自行 staged 9 檔的教訓）；read-only 任務禁任何寫入；禁 `/tmp` 落產物；紅線違反=失敗非風格
2. **目標（背景一句話）**
3. **Baseline identity**：repo root／工作目錄／base commit／已知並行改動聲明
4. **必讀**（按序、絕對路徑，可執行讀取）
5. **已決策（勿重辯）＋矛盾例外**：凍結決策逐條列；**例外**——發現具體證據（程式碼／官方文檔／驗收輸出）與凍結決策衝突時，停下舉證回報，禁為服從工單靜默做錯
6. **範圍限定**（動什麼/不動什麼，檔案級列舉）
7. **工具接線**（最小可用＋三禁令：禁 CR write face、禁 /tmp、禁自行妥協路徑）
8. **驗收**（每條=命令＋預期結果，機械可判）
9. **證據紀律＋PII 禁令**：每條驗收附命令與原始輸出；`user_email`/`user_full_name` 禁入輸出
10. **交付報告格式**：jobId/thread id、改檔清單、實跑命令與輸出、未驗證項、建議 reviewer 聚焦點（=completion-check 話術的承載節）
- 檔頭比照 `_common` 層慣例：`# 標題`＋blockquote 定位句，**無 YAML frontmatter**（層慣例實測：state-md-write.md、workflow-review-pattern.md 皆此形態）；加一句消費形態（skill 間引用＋主 session 直接填寫）＋「foreign runtime（muse bridge task／codex）共用；prompt 為任務本文，禁含委派語言」（muse-in-muse EPERM 教訓）

### 驗證策略
- 欄位級 checklist（非計數——十個任意標題不得通過）：`rg -n "紅線|Baseline|矛盾例外|PII|交付報告格式" skills/_common/work-order.md` 各命中且指向預期節；負向：模板無 write-scope 容許語句、無 `git add` 容許語句
- `skills/model-routing` routing 節含模板路徑指針（S1 已寫）——交叉 rg
- 試填實證：S5 兩張工單即試填（各含檔案級 scope＋驗收命令＋預期輸出＋reviewer record 欄位）

---

## S4：批次直做三小項（主 session 直接 Edit，不委派）

### Context
- 背景：muse triage 定案的直做項（委派開銷>收益）。**現況已預跑定案（09-03 雙 reviewer 一致 rg 實測）：項 1、項 2 目標內容均未承載（零命中），直接落筆**；項 3 允許 no-op（見下）
- 語義約束：無跨段依賴（可平行）

### 修改要點（逐項：現況查證命令→若未承載的落點）
1. **review-engine 背景句**（最小 pointer 形態——tool-discipline 與 agents/AGENTS.md 已兩處承載，此為第三載體只做導航不重述）：在審查執行預設段補一行「審查類命令 spawn agent 預設背景跑（細則見 rules/tool-discipline 背景執行段）」
2. **python-standards 相對 import 行**：查 `rg -n "相對 import|相對import" rules/python-standards.md`——遷移段若無「相對 import 穿透」（re-export 遷移時相對 import 消費者也需改）則補一行
3. **at-skill miss codify（允許 no-op）**：讀 `skills/at/SKILL.md`（task hint＋resume 時 STATE＋git 重建已在場——codex 審查指認可能已覆蓋）＋memory `at-skill-zcode-cron-gaps` 的 miss 教訓；**若現有流程已覆蓋該教訓則標 no-op 附行號證據，不為湊批次重寫相近規則**；確有缺口才提煈一句/小節（自包含、不引用 memory 檔名）

### 驗證策略
- 項 1/2 rg 命中；項 3 rg 命中**或 no-op 證據**（skills/at/SKILL.md 行號）回寫 EP；`/consistency skills/at/SKILL.md` 過
- 元資訊禁止自檢（新增行無日期/版本）

---

## S5：首批委派工單（新架構首用＋量測）

### Context
- 背景：muse triay 定案的兩個高工單化項；同時是 S1-S3 架構的首批實戰（dogfood 閉環）與 codex 建議的首批量測
- 依賴：S1（gate＋契約）、S3（模板）；執行載體=muse bridge task（**背景跑**）
- 語義約束：工單=任務本文（S3 禁委派語言款）；GLM reviewer 契約欄位=S1 定義

### 修改要點
1. **產物路徑與 owner（單一落點，R2）**：兩張工單落 `ai-analysis/_tasks/09-03-air13-unified-subagent-arch/work-orders/`（`a-affected-test-set.md`、`b-post-build-gaps.md`，主 session 寫）；review record 落點唯一＝本 EP S5 節末表格（主 session 寫入）；量測四欄落點唯一＝本 EP S5 量測小節。任務家產物納入本 EP 變更清單
2. **工單 A：受影響測試集機械列舉三處**（範圍：`rules/quality-constraints.md` 機制句——「受影響」測試集必須 cr `callers`/`impact_radius` 或 `rg "<符號>" tests/ -l` 機械反查、禁目錄直覺；`skills/cr-query/SKILL.md` 標準配方〔修改檔→受影響 test files〕；`skills/implement/SKILL.md` 驗證段指針）。**Baseline identity 釘 repo root `~/Github/mosaic_alpha`**（mosaic 三 worktree 之一，`9f151add` 在此，唯讀）；回歸錨預期＝反查應列出 `tests/unit_tests/alpha_forge/` 相關測試檔（MOS-13 漏網形態；確切檔名以反查輸出回填）。**證據三級標記**：graph-derived（CR）／text-derived（rg）／未驗證 dynamic consumers——沿用 cr-query graph 缺場 `[WARN]` gate，rg 命中≠完整 impact
3. **工單 B：post-build 四通用缺口**（範圍：`skills/post-build/SKILL.md` 補四條——額度降級措辭鐵律／增量≥3 檔補審／階段 0 背景寫入者前置／並行線排除明列；**現況已預跑：四條全未承載**，直接落筆）
4. **Preflight（SM-8）**：派單前主 session 查 `.muse-bridge/setup.json` green＋muse binary 在場；非綠→自主補跑 setup（既有定案）或降級主 session 直做＋EP 記錄
5. 兩張工單皆用 S3 模板填寫（十節齊）→ bridge task `--trust-workspace` **背景**派 muse（bridge 派發為既有常規操作；user 中止則工單列 PENDING 不派）
6. **GLM acceptance reviewer 契約逐字注入（R4）**——不依賴 reviewer 自行查 model-routing：reviewer prompt 必含讀料順序（work order→diff→evidence→writer report 最後讀）、固定交付欄位、accept/reject/needs-fix schema、無 record 不結段；record 寫入本 EP S5 表
7. **重工上限**：needs-fix 修輪封頂 3 輪（post-build 先例）；超頂→停卡回報 user
8. **量測記錄**（codex 建議，落點＝本 EP S5 量測小節）：sandbox-error 率／review 抓到的 defects 數／重工輪次／主 session context 體感節省——作為擴大委派的數據依據

### 驗證策略
- 兩工單落地後：各落點指定精確詞 rg 命中（工單 A＝「機械反查／impact_radius」於三落點；工單 B＝四條各自關鍵詞）＋`/consistency` 過
- reviewer record 存在於本 EP S5 表（SM-3/SM-11）；transport status／verification／review verdict 三欄分立
- 量測四欄有值（無值則標「未觀測到」勿留空）；重工輪次 ≤3

### 委派工單 reviewer record（唯一落點）

| 工單 | 內容 | writer | reviewer | verdict | findings 摘要 |
|------|------|--------|----------|---------|--------------|
| WO-1（S1+S2+S3） | 三層架構核心文檔 | muse（bridge task，一次成功） | GLM acceptance reviewer（fresh agent，讀料順序契約） | **accept**（2026-09-03） | 9/9 驗收獨立重跑全過；範圍零越界（含 mtime 取證）；writer 六偏差全判合理；**writer 報告層兩失準**（原 description 尺寸數字錯——實測 573 字元/850 bytes 本就低於門檻、壓縮動機不成立但無害；「1024 bytes 上限」無 grounding）；6ℹ️——F-1/F-2/F-4（→ 併 WO-2 落地）；F-3 不改（:40 備註已澄清）、F-5 報告層失準知悉、F-6 /tmp 技術性觸線已清 |
| WO-2（S4＋B-1/B-2＋審查三小修） | 七檔小手術批次 | muse（bridge 直呼——B-1 形態首用，通知直達零 wrapper 介入） | GLM acceptance reviewer（fresh agent） | **accept**（2026-09-03） | 9/9 驗收獨立重跑過（驗收 9 字面不符但實質過——工單規格缺陷：「現況已零」前提為假，base commit 已有 5 個 agents/zcode/ pins〔兩層契約②允許〕，writer 如實揭露）；8/8 file:line 驗證正確；S4-3「有缺口」判定被 memory 源檔證實（原文自稱尚未 codify）；三態表判互斥/完備/可操作；4ℹ️——工單負向掃描 scope 應排除 agents/zcode/ pins（規格教訓）、thin-forwarder 節首句與 dispatch face 小節可補一句指針（reviewer 側已補）、at:145 因果子句 hedged 可接受、jobs.json 措辭隨意（不改） |
| WO-3（S5-A 受影響測試集） | 三落點＋mosaic 回歸錨 | muse（bridge 直呼） | GLM acceptance reviewer（fresh agent） | **accept**（2026-09-03） | 6/6 驗收獨立重跑過；矛盾例外 baseline 驗證（三檔 63f2041 零命中）；**回歸錨裁定成立**——text-derived（rg 6 檔）與 graph-derived（impact_radius 15 test 檔）交叉一致涵蓋 alpha_forge 3 檔、ef114979 message 直接釘住 8 FAIL 根因三角，證明機械反查可擋歷史漏網；3ℹ️——implement:151 條件化措辭窄於無條件源＋句內冗餘（兩項 reviewer 側已修：收斂為單句無條件）、「目錄直覺歸因」屬推斷無直接證據（引用時標推斷性質——防護價值獨立成立不受影響） |
| WO-4（S5-B post-build 四缺口） | 四句寄生既有段落 | muse（bridge 直呼） | GLM acceptance reviewer（fresh agent） | **accept**（2026-09-03） | 6/6 驗收獨立重跑過；scope 歸屬逐檔交叉比對（11 檔 diff 全數有 WO 歸屬）；跨引用三目標（quality-constraints:41 Fail Loud／code-review:98 dual-context／collaboration-constraints:75 並行原則）全部存在且 base 版可達；no-duplication 加驗（pre-change 關鍵詞＋同義詞掃描——四條均真增量）；3ℹ️ 全「可不改」（模板條件行後續優化／「已觸發」雙讀行為收斂／heading 計數口徑） |

量測結算（B-3 最終值，2026-09-03 build 收尾）：muse 工單 4 發 4 中（全一次成功、sandbox-error 0）；dispatch 形態轉移實證——WO-1 wrapper 形態需 1 次 resume-to-poll 介入，WO-2/3/4 改 B-1 直呼形態後**零介入**（通知直達）；GLM acceptance reviewer 4發 4 accept（產品缺陷 0🔴0🟡；ℹ️ 改善 16 項、落地 6 項其餘記錄）；writer 報告層失準 3 處被 reviewer 獨立查證抓出（description 尺寸、1024 bytes 無據、驗收 9 過述）——契約「讀料順序＋獨立重跑」有效；重工輪次 0；context 節省顯著（4 次手術全在 muse runtime context 消化，主 session 只收報告與驗收）。結論：架構成立，可擴大委派。

---

## 整合策略

- 跨檔一致性 rg 清單（收尾一次跑）：family/profile 詞彙三處（model-routing rule＋skill＋agents/AGENTS.md）語義一致；`work-order.md` 被引用指針有效；架構層零 model id（`rg "muse-spark|gpt-" rules/ agents/ skills/_common/` 零命中）
- sync-sources：model-routing 為定義源變更——`rg "model-routing" rules/ skills/ agents/` 掃引用（實測 13 檔命中），產出 **consumer disposition table**：每命中檔標 update／no-change＋一行理由。`rules/AGENTS.md` 索引行與 `skills/CLAUDE.md` 索引行**列為預計 update**（現況將 model-routing 描述為 tier/兩跳，擴充後必然不完整）；`skills/agent-workflow`、`skills/execution-plan`、`skills/review-engine`、`_common/` 兩 review 模板逐檔判讀（多為並發表/tier 語義引用，no-change 需附理由）
- deploy：`uv run python scripts/deploy_agents.py` 重跑＋三 harness 部署檔 `cmp` 一致＋90KiB gate 未爆

## 收尾步驟

1. deploy＋gate＋sync-sources 掃描（上節）
2. `skills/CLAUDE.md` 工作流索引：work-order 模板若屬共用子範本則無需列（`_common` 非 skill）；model-routing description 若語義變了同步一句
3. AIR-13 結案兩步（commit 後）：`-s Done --final-summary` → `--ref` 換 done/ URL
4. **bridge roadmap 三條記錄輸出**（跨 repo 歸 muse-plugin-cc 側，本 session 只在完成報告列清單不動跨 repo）：`--disable-write` 暴露／`-w worktree` 暴露／task 類 job 加 `muse export`
5. **後議三項輸出邊界問題清單**（供 user 裁決後另開工單/卡）：四律九律分拆落位（人定邊界）、debugging＋modern-cli 擇要（人擇要）、contracts.md muse 對照欄（人給鏡像邊界——「過時以原站為準＋每格附行號」硬約束）

---

## EP Review Findings

審查：muse（job `job-mtlfet2m` 後續，09-03）＋codex（thread 09-03，重派版）雙報告；judge 由主 session GLM 執行。兩家結論：muse「有條件執行」、codex「需修正後重新審查」——判讀：codex 五🔴全為文本級可修（非結構重寫），與 muse 唯一🔴同性質；全數採納或部分採納、無否決項，修正封閉於本表，**修正後=有條件執行已滿足**。

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| M-F1＋C-D1 | 🔴 | S1/SM-5 | capacity 數字（codex 約 200K）計畫落 rule＋解析表雙落點，違單一源；數字/型號例子屬易過時事實 | 數字只住解析表；rule 只寫相對措辭＋指針 | implemented（核心原則＋S1＋SM-5 已改） |
| C-R1 | 🔴 | 核心原則/整合策略 | 「禁 hardcode」與 agents/zcode materialized pin 機制矛盾；掃描 regex 漏 glm-/sonnet | 兩層契約：權威值在解析表；pin=允許 materialization 須比對一致；新內容掃描 family-only 三路徑 | implemented |
| C-R2 | 🔴 | S5 | 工單/reviewer record/量測無固定產物路徑與 owner；工單 A 未列預期 test path | 產物路徑單一落點（work-orders/、EP S5 表、量測節）；釘 mosaic_alpha repo root＋預期 alpha_forge 測試 | implemented |
| C-R3＋M-F5 | 🔴 | Scenario Matrix/S5 | 外部 runtime 失敗生命週期未覆蓋（setup 非綠/quota 盡/job 卡住/reviewer 缺/重工上限） | 補 SM-8~12＋S5 preflight | implemented |
| C-R4 | 🔴 | S1/S5 | 「審查第二意見→muse」與「GLM reviewer 驗收」角色未拆名；契約未注入 reviewer prompt | 拆名 external second-opinion vs in-harness acceptance reviewer；契約逐字注入 reviewer prompt | implemented |
| C-R5 | 🔴 | S3 驗收 | 十節計數驗收可被任意標題滿足 | 欄位級 checklist＋負向檢查 | implemented |
| M-F2 | 🟡 | S3 | `_common` 慣例實為標題＋blockquote 無 YAML frontmatter | 檔頭照層慣例 | implemented |
| M-F3 | 🟡 | S1/收尾 | model-routing skill description 觸發詞未同步（委派場景載入不到） | description＋skills/CLAUDE.md 索引列必做同步 | implemented |
| M-F4 | 🟡 | S4 項1 | review-engine 背景句=第三載體，無漏跑實證 | 縮為最小 pointer 形態 | implemented（保留——導航價值） |
| C-D2＋M-F11 | 🟡 | 整合策略 | sync 清單未成逐檔 disposition；rules/AGENTS.md、skills/CLAUDE.md 必然需更新 | consumer disposition table（13 檔） | implemented |
| C-D3 | 🟡 | S4 項3 | at-skill miss 無可驗證情境；現況可能已覆蓋 | 允許 no-op 附證據，不為湊批次重寫 | implemented |
| C-D4 | 🟡 | S5 工單 A | callers/impact_radius/rg 證據強度不同未分級；graph 缺場無降級標記 | 證據三級標記＋沿用 cr-query WARN gate | implemented |
| C-D5 | 🟡 | S5/收尾 | deploy 寫外部 harness 檔、bridge 派發是 outward 形態 | 標常規操作；user 中止→PENDING fallback | implemented（輕量——兩者皆既有常規） |
| M-F6 | ℹ️ | 段落 0 | 11 筆計數「含」字歧義 | 精確分類計數 | implemented |
| M-F7 | ℹ️ | 卡↔EP | 卡 desc 七節/兩條 roadmap vs EP 十節/三條 drift | 動筆時同步卡 | implemented（本回寫同批已改卡） |
| M-F8＋C-I3 | ℹ️ | S4/S5 | 「可能已承載」假設——預跑結果全未承載 | 標注定案，直接落筆 | implemented |
| M-F9 | ℹ️ | S2/S5 | codex `--output-schema` 未驗證 | 工單前核實 | resolved——本 session `codex exec --help` 實機已見（"JSON Schema file describing the model's final response shape"），非傳聞 |
| M-F10 | ℹ️ | S5 工單 A | mosaic 非單一 repo，錨未釘路徑 | 釘 `~/Github/mosaic_alpha` | implemented |
| M-F12 | ℹ️ | S1 驗證 | model id 掃描命令兩處口徑不一 | 統一三路徑 | implemented |
| M-F13 | ℹ️ | S2 | registry 現況零 muse 字樣，條件句白寫 | 直接定案需寫入 | implemented |
| C-I1 | ℹ️ | baseline | 卡 modified＋EP untracked 勿誤當 S1-S5 已完成 | 保留 baseline 認知 | noted |
| C-I4 | ℹ️ | S5 | lifecycle/產物/review handoff 隱含成無名第四層 | R2-R4 顯性化 | implemented（同 C-R2/R3/R4） |

### Build 期新發現（本弧首批量測數據——dispatch 失敗三態全數實遇）

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| B-1 | 🟡 | S2 | **wrapper 提前 complete 是系統性常態而非例外**（本弧 muse×2＋codex×2：wrapper 在 runtime 未終局時就收工）——收法靠主 session 即興 SendMessage resume，未標準化 | dispatch protocol 入 agents/AGENTS.md flag-profile 節：標準收法兩式——①muse 優先**主 session 直呼 bridge CLI**（背景 Bash＋jobs.json 輪詢，繞開 wrapper 生命週期錯位；terminal text 數 KB 不需中轉）②wrapper 形態續用時收法＝resume-to-poll（禁重派） | pending（WO-1 驗收後 reviewer 側補入） |
| B-2 | 🟡 | S2 | **dispatch 失敗三態未分類**——本弧三態全遇：①transport 未啟動（CLAUDE_PLUGIN_ROOT 空→MODULE_NOT_FOUND，job 未建立→**可安全重派**）②transport 在跑、wrapper 已收（→poll 收集，**禁重派**）③transport 死中途、wrapper 空轉（→機械驗收＋TaskStop） | 三態判定表（症狀→證據→處置）入 agents/AGENTS.md dispatch 段，判定錯誤的代價＝雙跑或丟失結果 | pending（同上） |
| B-3 | ℹ️ | S5 量測 | 首批量測數據開始累積（本弧即首批樣本）：sandbox-error 0／wrapper 生命週期事件 3（muse×2、codex×2 中 2 次需介入）／env 失敗 1（重派解決）／重工 0／主 session context 節省顯著（審查報告由 runtime context 消化） | 量測節照實記錄，此表為數據源 | pending（收尾時結算） |
