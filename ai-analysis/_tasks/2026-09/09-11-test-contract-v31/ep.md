# EP：測試契約 v3.1 六檔落檔（materialization）

> **ep_type**: implementation
> 本 EP 不宣告 docs mode 主體（S1 觸 `scripts/sync_agents.py` pins 一行＝executable source，按 docs mode 機械判準退出）；全 `.md` 段（S2-S7）段內採 docs-style 驗證（rg 殘留＋跨檔一致性＋/consistency），S1 保留機械驗證（generator 實跑＋diff 對照＋pytest baseline）

baseline: 4b0d2b7ebd02a741643817a26fd68ba42e4d6db7

## 實作總覽

**任務一句話**：把三方裁決定案的測試契約 v3.1（reports/2026-09-11-test-contract-design.md）從 blueprint 沉澱落檔到六個 skill＋研究鏈 routing＋附帶同步面——兩天最大定案的最大零承載弧收斂。

**設計核心**（v3.1 終態，勿重辯）：family separation 放在 **judgment boundary**，不放在 every authorship boundary——獨立性買在「審規格」（challenge）與「審結構」（review 軸B），不買在「把 oracle 抄成 pytest」。分層：

```
EP（GLM full）：凍結 TC ——oracle 層獨立（top-level 測試規劃段在實作段落前）
  ↓ 高風險/P0：pre-RED challenge（跨家族 advisory·fresh·blind derive→reveal＋completeness）
  ↓ oracle 錯→judge/人類→EP amendment（authority 四分）
實作家族（單一 model·context 連續）：照凍結 TC 寫 RED
  ↓ RED 三 gate 當場驗：STRUCT_OK／SEM_OK／BEFORE_GREEN＋contract-test digest 凍結
  ↓ GREEN（frozen contract test 唯讀）→ REFACTOR
  ↓ 撞牆→mutation authority gate（TC oracle→停 GREEN→amendment）
audit-test（軸A 機械）：七項對帳
code-review（軸B 架構面·跨 session dual-context）：六項；翻譯忠實度明寫不歸它
judge-review＋修正迴圈（現行）
```

**已決策（三方 r3 同向同意＋user 拍板，勿重辯）**：
- 契約層先、分離後；TC 凍結在 EP top-level（文件順序＝時間順序）
- RED provenance 三栓：①RED receipt 落檔存證（TC-ID＋baseline 身份＋test digest＋failing predicate，非中途 commit）②gate 過後 digest 凍結（GREEN 不得靜默改 frozen test）③基線跑法（新測試在 pre-change baseline 上必須紅——baseline 綠＝vacuous 劇場化，直接退回）
- **digest 算式（凍結）**：sha256 of frozen test 檔案 bytes；凍結時點＝RED receipt 落檔時記錄；GREEN 後重算不一致＝靜默改（Critical）
- 第三家族寫手（test-gen）＝P0 最後手段，啟用條件預寫死（MVP 證明 challenge＋review 擋不住 fixture fidelity 級穿透才啟用）——AIR-70 幽靈角色答案反轉：**不生成 registry 定義檔**，僅入 lifecycle 表註記
- amendment 語義：EP 可改、TC baseline 凍結；authority 四分（invariant/reference truth 可證偽→judge；新 integration evidence→judge；user intent／product policy→人類；來源矛盾→人類）；「實作現況」永遠不是證據；deviation log（前線提案）與 amendment（判決）分離
- cr-research 升 full（user 拍板「研究不派 flash」）；**僅 cr-research 一角**——Explore fallback（Claude 端 registry 缺場時）維持 lite 不動；機械子腿（逐字引用、CR 查詢執行）仍可 flash 承接——作為 full 研究者的下游查詢
- same-family precondition：EP author family ≠ implement family 是 oracle 獨立性前提；不成立（如 GLM author→GLM impl）→ 強制 challenge 或明示 degraded（codex r1 獨有發現）——**producer（S2 記錄欄位）＋consumer（S3 dispatch gate）兩端都要落**

**跨弧編輯面宣告**（tri-audit ①）：AIR-67（CR quick-wins 含 cr-research 角色定義修正）——本 EP S1 動 roles/cr-research.md 的 tier 面，AIR-67 之後動同一檔的「角色定義修正」面，兩者接觸但不重疊；AIR-67 開工時讀本弧終態。bundle 減量弧（已 commit ac5ddfd）不在 working tree，無衝突。

**止血項時點**：EP 定稿建卡後（本 session /implement 前）即刻落 `rules/model-routing.md:21` 止血行（working tree 變更，隨 S1 開工 commit）——防建卡→開工窗口內新 EP 段落 0 錯派 lite。S0 起手式 rg 確認止血在場。

---

## UC 盤點

### Backlog 關聯

- **本 EP 追蹤卡**：`v3.1 測試契約六檔落檔——materialization`（建卡隨本 EP 定稿，desc 見 kanban-board 契約）
- AIR-70（一致性修復弧，To Do）：照舊範圍結案；本弧 test-gen 結論 materialize 為 AIR-70 的 lifecycle 表註記輸入（裁決 §7）——**不擴 AIR-70 scope**
- AIR-67（CR quick-wins，To Do）：cr-research 定義檔接觸面（見跨弧宣告）；AIR-67 desc 不改
- 去重檢查：`backlog task list --plain` 無既有測試契約卡（X1 交叉命中證實零承載；三方審查複驗 `rg -i "測試契約|test-contract"` 零命中）；`ai-analysis/_inbox/pending-decisions.md` 無相關待處置指針

### SYSTEM-MAP 影響

無 SYSTEM-MAP.md（元專案，正當跳過）。

### 掃描範圍

- skills/{execution-plan,implement,code-review,audit-test,fix-test,model-routing}/SKILL.md（六檔全文已讀）＋ skills/code-review-and-quality/SKILL.md（軸B 六項定義源落點——三方審查新增）
- rules/model-routing.md、agents/AGENTS.md（contract 表＋projection map）、agents/roles/cr-research.md、scripts/sync_agents.py:33
- ai-analysis/blueprint/workflow.md（②⑤站＋v3.1 定案節）、skills/CLAUDE.md（工作流索引）
- backlog task list --plain（去重）

### 同主題 memory 條目（結案蒸餾範圍）

- `project_ep-test-contract-top-level-before-impl`——v3.1 定案待建卡狀態詞（弧流水形態，結案時蒸餾終態）
- `project_test-family-separation-consult-0910`——R1 諮詢已吸收進 v3.1（勿重跑記錄，保留）

### 受影響命令（docs mode UC 形態——命令行為將改變者）

| 命令/rule | 行為變更 | 狀態 |
|---|---|---|
| `/execution-plan` | 新增 top-level 測試規劃段生成（TC 格式＋凍結語義＋amendment 附錄＋author_family 欄位）；高風險/P0 產 challenge 工單；段落 0 研究派工改 full | 📋 新增能力面 |
| `/implement` | same-family dispatch gate（階段 0/1）；RED 三 gate 當場驗＋receipt 落檔＋digest 凍結；frozen TC carve out（裁量權不覆蓋契約面） | 📋 新增能力面 |
| `/audit-test` | 軸A 機械對帳擴充（角度 8：七項對帳） | 📋 擴充 |
| `/code-review` | dual-context（模式 B）兩側注入測試架構六項（diff 含 test files 時）；六項定義住 code-review-and-quality | 📋 擴充 |
| `/fix-test` | Type B/C/E 掛 TC escalation＋mutation authority gate 互指 | 📋 擴充 |
| model-routing（rule+skill+registry） | cr-research full；test-gen 移出常設 full 行改 P0 註記 | 📋 變更 |
| workflow viewport（blueprint） | ②⑤站 challenge/mutation gate 半句＋v3.1 節狀態翻新（含 :16/:19 狀態詞） | 📋 同步 |

---

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 新 EP 屬高風險/P0 | /execution-plan 生成 EP | 測試規劃段凍結 TC＋產 pre-RED challenge 工單（跨家族 fresh·blind-derive）＋author_family 欄位 | challenge findings→amendment 或放行 | execution-plan 測試規劃段 |
| SM-2 | 新 EP 中風險（非 P0） | /execution-plan | 測試規劃段凍結 TC＋author_family 欄位；challenge 跳過 | — | 同上 |
| SM-3 | EP author 與實作者同家族 | /implement 階段 0/1 dispatch gate | gate 攔截：RED 前須 challenge completed 或 degraded 明示記錄（EP 欄位），否則不得進 RED | gate 記錄 | implement same-family gate |
| SM-4 | implement RED 階段完成 | /implement 階段 2 | 三 gate 當場驗＋RED receipt 落檔＋digest 記錄 | receipt 檔在任務家 | implement RED provenance |
| SM-5 | GREEN 期實作者想改 frozen test | mutation 誘惑 | frozen TC carve out：裁量權不覆蓋契約面——停 GREEN→mutation authority gate→amendment（「實作現況」非證據） | amendment 附錄記錄 | implement＋fix-test 互掛 |
| SM-6 | audit-test 掃本弧 test 變更 | /audit-test | 角度 8 七項機械對帳（含 receipt/digest 驗證、基線跑法、oracle 圓形依賴） | findings | audit-test 軸A |
| SM-7 | code-review dual-context 審測試變更 | /code-review 模式 B（diff 含 test files） | 兩側 spawn prompt 均注入六項；primed 額外拿 frozen TC；翻譯忠實度不歸它（明寫） | findings | code-review 軸B |
| SM-8 | fix-test 遇 Type B/C/E 且測試對應凍結 TC | /fix-test 階段 2 | mutation authority gate：查 amendment authority，非直接重寫/刪 | 分類報告含 escalation 欄 | fix-test escalation |
| SM-9 | EP 段落 0 研究派工 | /execution-plan 段落 0 | cr-research 以 full 派（非 flash）；Explore fallback（Claude 端）維持 lite | spawn 確認印 tier | model-routing 研究鏈 |
| SM-10 | 有人想啟用 test-gen | 委派測試寫手 | P0 最後手段：啟用條件預寫死（MVP 證據），非常設 role；不滿足→拒 | lifecycle 表條目 | model-routing test-gen |
| SM-11 | MVP 不過線 | S0 跑完量測 | fail-loud：**僅 S1 可跑；S2-S7 全停**，blueprint 保持 ⚠️，回報 user 裁決 | MVP 報告 gate | S0 |
| SM-12 | 消費端（mosaic 等）讀取新 skill | 部署 sync | 全域 guide bundle 不含 skills（on-demand symlink）——無 bundle 尺寸影響 | deploy gate | 部署面 |

---

## 段落劃分原則

- **single-source 原子性**：routing 鏈（roles→sync_agents→生成物→rule→skill→execution-plan 措辭）是一個定義源的同步面，拆開製造中間態 drift——S1 一段原子完成
- **詞彙先於消費者**：S2 定義 TC 格式/amendment 語彙（契約層是其他段的引用源），S3-S6 消費；S7 收尾同步導航面
- **驗證前置**：S0 MVP 是設計的致命先驗（blind-derive protocol 未實證），過線才落檔
- **失敗路徑隔離**：S0 不過線→S2-S7 全凍結（防 blueprint 假狀態投影——false-green）
- 可平行：S4/S5/S6 互不依賴（皆消費 S2 語彙）；S0 與 S1 無依賴可平行

---

## S0：MVP seeded fault-injection（設計驗證——卡內第一步）

### Context

**背景**：裁決報告 §9 誠實聲明——challenge blind-derive protocol 是設計推論未跑過；MVP 過線不代表 production 有效，但量已知壞樣的 discriminating power。§6 定義 MVP 為「卡內第一步」：**先驗設計、後落檔**。

**需求邊界繼承**（無 /spec）：Always＝過線標準預凍結（跑之前寫死，防事後合理化；expected-routing 表同此）；Ask First＝MVP 不過線時暫停落檔回報 user；Never＝禁把 MVP 結果外推為 production 有效性宣稱。

**UC 引用**：驗證「execution-plan 測試規劃段」與「audit-test 軸A／code-review 軸B」的設計偵測力。

**依賴關係**：無上游依賴（考的是設計中的檢查項，非已落檔 skill——spawn prompt 直接攜帶 v3.1 檢查項文本）。起手式：rg 確認止血行在場（`rg "v3.1" rules/model-routing.md` 命中——建卡後本 session 已落；若缺且 S1 不即刻跑，先補落）。

**語義約束**：與 S2-S6 共享同一套檢查項語彙——MVP 用的文本即落檔文本的候選，發現缺陷回饋 S2-S6 修正。

**基礎設施盤點**：delegate-bridge `task --family muse`（跨家族 advisory·fresh）；in-harness spawn（模擬 audit/review prompt——**spawn tier 口徑＝registry lite（glm-5.3-flash）**，對應部署面真實 reviewer 配置；量的是部署面 discriminating power，非主 session full 模擬——實驗形態明示）；歷史案例素材（mosaic mutmut spike 的 critical path 形態——會計/單位邊界題材，取其**形態**在 ai-rules 側構造迷你 TC，不跨 repo 寫入）。

**技術選型**：synthetic 迷你 TC（8 份 Lane A＋六類 mutant Lane B），agent 評審。**成功標準**：預凍結過線（見驗證策略）。

### 核心實作要點

1. **素材構造**（Lane A）：8 份迷你 TC——4 clean＋4 oracle mutant。題材取會計/單位邊界形態（張↔股換算、除權息調整、時區跨界各至少一份）。每份含 claim／Given-When／oracle（predicate-ID 拆分）／oracle_source。oracle mutant 形態：oracle 公式錯（如除權息基準日錯側）、單位換算係數錯、邊界 off-by-one、oracle_source 指向實作本身（圓形依賴）
2. **Lane B 素材**：六類 test 架構 mutant＋**expected-routing 表（預凍結——跑前寫死）**：

   | mutant 類 | 預期路由 | 備註 |
   |---|---|---|
   | 幽靈斷言升級形（斷言與 TC predicate 脫鉤） | audit（機械對帳項 1 抓） | |
   | 同義反覆（test 硬編碼 impl 值） | **audit 抓到後 escalate challenge**（oracle 類 specimen——圓形依賴面） | 路由歸屬：機械層 audit 命中、判定層屬 oracle 級 |
   | evidence fidelity 缺陷（mock 回傳值即 oracle） | review（軸B evidence fidelity 項）＋audit（mock↔evidence class 項）雙命中可接受 | |
   | shared dependency 污染（fixture 跨測試殘留） | review（軸B shared dependency 項） | |
   | 符號≠路徑（symbol import 無路徑驅動） | audit（對帳項 7→角度 4 引用） | |
   | 層級失衡（unit-only 驗證整合器變更） | review（軸B 層級平衡項） | |

3. **Lane A 執行**（考 challenge，~2 agent call）：spawn 跨家族 advisory（muse bridge `task --family muse`，fresh context）——prompt 攜帶 blind-derive protocol：先自行推導 oracle（不 reveal）→ reveal 比對 → 產 falsifiable 探針＋completeness 檢查。8 份逐份 verdict
4. **Lane B 執行**（考 audit＋review，~1-2 agent call）：分別 spawn audit 形態（機械對帳 prompt）與 review 形態（架構面 prompt）各跑六類 mutant；**加一步 escalate 驗證**：取一份 Lane A oracle mutant 混入 Lane B 餵 audit/review——預期正確 escalate 到 challenge（標記轉介）而非硬吞為自己的 finding
5. **量測四軸**：recall（mutant 抓到率）／誤報（clean 誤殺）／attribution accuracy（缺陷歸因正確——防「每題建議再確認」假 recall）／defect routing correctness（依 expected-routing 表逐類判）
6. **產出**：`ai-analysis/_tasks/2026-09/09-11-test-contract-v31/mvp-report.md`（素材清單＋verdict＋四軸數字＋過線判定）

### 修改要點

無 product 檔修改；產出 mvp-report.md（evidence artifact，非 production consumer 引用）。素材與 verdict 留任務家 `mvp/` 子目錄。

### 驗證策略

**過線標準（預凍結——本 EP 定稿即凍結，跑之前不得改）**：
- Lane A challenge：oracle mutant recall ≥ 3/4 **且** clean 誤報 ≤ 1
- Lane B routing：六類 mutant 至少 5/6 被預期路由的軸抓到（依 expected-routing 表）；混入的 oracle mutant 被 escalate（標記轉介 challenge）而非硬吞
- attribution：每個 caught mutant 的歸因正確率 ≥ 5/6（歸因錯＝有抓到但指錯機制）

**失敗處置**：任一軸不過線 → **S2-S7 全凍結（僅 S1 可跑）**，blueprint 保持 ⚠️，回報 user（SM-11）；協議修正候選（blind-derive 加錨定防護、檢查項加細）記入報告。

**已知未覆蓋**：MVP 量已知壞樣靈敏度，非 production 有效性；個位數樣本只判 discriminating power（裁決 §6 誠實邊界原文）。

---

## S1：研究鏈 routing 原子切（cr-research 升 full＋test-gen P0 化）

### Context

**背景**：cr-research 升 full 已裁決（user 拍板「研究不派 flash」——段落 0 全域研究含風險假設識別是判斷密集位；淺研究「自信但薄」→EP 重造既有/漏致命假設，省的 token 遠小於錯 EP 的重工）。tri-audit X2（3/3 交叉命中）：裁決已定但五處 live routing 仍 lite——減量弧還把舊值重固化。test-gen 佔 model-routing 常設 full 行（tri-audit 獨有成立項）。

**語義約束**：與 agents/AGENTS.md contract 表、rules/model-routing.md、skills/model-routing/SKILL.md 三處表共享 tier 詞彙；**僅 cr-research 一角升 full**——Explore fallback（registry 缺場時）維持 lite；機械子腿仍可 flash——「full 研究者的下游查詢」語意須在 role 描述中表達（非全面禁 flash）。

**基礎設施盤點**：`scripts/sync_agents.py`（生成器；`uv run python scripts/sync_agents.py` 重新生成雙 registry）；`tests/test_sync_agents.py`（生成對帳 baseline）。

**依賴錨點**（機械掃描 2026-09-11，rg "cr-research" 全 repo；三方審查複驗全命中）：
| 錨點 | 位置 | 動作（含半句框定——防誤改相鄰陳述） |
|---|---|---|
| roles authoring | `agents/roles/cr-research.md:3`（description 開頭「〔tier: lite〕」——**注意：該行不含 "cr-research" 字串，rg 掃不到，須點名讀檔**） | 改 full＋下游 flash 承接語意 |
| pins dict | `scripts/sync_agents.py:33`（`"cr-research": "lite"`） | 改 `"full"` |
| 生成物 | `agents/zcode/cr-research.md`、`agents/claude/cr-research.md` | 跑 generator 重生成（禁手改） |
| rule 表 | `rules/model-routing.md:21`（研究行「…全域研究用 registry cr-research（ZCode lite＋CR 白名單）」——**前半句講 Explore 繼承主模型，維持不動**） | 僅 cr-research 半句改 full；Explore 半句不動 |
| skill dispatch 段 | `skills/model-routing/SKILL.md:43`（「重實作段 muse、lite 機械段 glm-5.3-flash；CR 工具鏈 agent（cr-research 等）同收斂 muse＋glm-5.3-flash」——**前半 implement-profile 收斂語意保留**） | 刪「cr-research 等」的 flash 半句，改「CR 工具鏈 agent（cr-research 等）＝muse 收斂＋GLM 側 full（cr-research 升 full，user 09-11）；機械子腿 flash 承接」 |
| skill tier 表 | `skills/model-routing/SKILL.md:64`（lite 行含 cr-research；:62 full 行「（空——…非 role）」） | cr-research 移入 full 行；full 行附註改寫（「cr-research（研究判斷密集，user 09-11）；judge／EP 規劃仍主 session」） |
| contract 表 | `agents/AGENTS.md:39`（研究行 tier=lite——**行內 spec-miner 同列，維持 lite 不動**）＋`:66`（projection map） | 研究行 cr-research 改 full（spec-miner 不動）；projection map 同步 |
| 段落 0 措辭 | `skills/execution-plan/SKILL.md:165`（「cr-research（掛 CR MCP 白名單、lite pin；CR 查詢 in-path）」——**同行 fallback「research/explore＝lite」維持不動**） | 僅 registry pin 半句改 full；Explore fallback 半句不動 |

test-gen 面：
| 錨點 | 位置 | 動作 |
|---|---|---|
| rule 常設行 | `rules/model-routing.md:16`（「impl / test-gen \| full 基準；…lite test 只算規格陳述」） | 拆行：impl 留 full；test-gen 改「P0 最後手段（啟用條件預寫死：MVP 證明 challenge＋review 擋不住 fixture fidelity 級穿透才啟用；非常設 role 不生成 registry 定義檔）」獨立行 |
| contract 表 | `agents/AGENTS.md:36-51` | 加 test-gen 註記行（同上語意；非 stage 行——掛表後註記） |

**技術選型＋成功標準**：原子一次切齊九錨點；sync_agents 重生成後 diff 僅含預期變更；pytest baseline 綠。

### 修改要點

1. 上表逐錨點 Edit（roles→pins→rule→skill→contract→execution-plan 措辭），逐錨點遵守半句框定
2. `uv run python scripts/sync_agents.py` 重生成
3. 止血行吸收：rule :21 的 full 半句即止血終態（EP 定稿後本 session 已先落 working-tree 止血行——S1 段將其改為終態措辭並隨段 commit）

### 驗證策略

- `uv run python scripts/sync_agents.py --map` 輸出 cr-research/full
- `rg -n "cr-research" rules/ skills/ agents/ scripts/` 逐命中核對無 lite 殘留（生成物除外——生成物由 generator 保證）
- **roles 檔直驗（gate 盲區補）**：`rg -n "tier: lite" agents/roles/cr-research.md` 零命中（該行不含 "cr-research" 字串，上條 rg 抓不到）
- **Explore fallback 未誤升**：`rg -n "research/explore" rules/model-routing.md skills/execution-plan/SKILL.md` 仍為 lite 語意
- `uv run pytest tests/test_sync_agents.py -v`（背景跑，exit 0）
- `git diff agents/zcode/ agents/claude/` 僅 cr-research 相關行變更
- test-gen：`rg -n "test-gen" rules/ skills/ agents/` 確認無「常設 full」語意殘留

---

## S2：execution-plan skill——測試規劃段＋amendment＋same-family precondition（producer 側）

### Context

**背景**：契約層是 v3.1 的根。EP top-level「測試規劃」段放在實作段落之前（文件順序＝時間順序）；oracle 獨立性由「EP 作者↔實作者本來就跨家族」兌現（same-family 時此前提裂縫——codex 發現；**本段是 producer 側（記錄欄位＋產條件），consumer 側 gate 在 S3**）。

**UC 引用**：實作「/execution-plan 測試規劃段」（UC 盤點 📋）。

**依賴關係**：下游 S3（RED receipt 引 TC-ID＋same-family gate 讀 author_family 欄位）、S4/S5/S6（引用 TC 格式語彙）、S7（workflow ②⑤站投影）。本段是詞彙定義源。

**語義約束**：TC 格式與 audit-test 軸A、code-review 軸B 的檢查項一一對應（predicate-ID 拆分↔對帳項）；amendment authority 四分與 fix-test escalation 共用語彙（S6）。

**基礎設施盤點**：execution-plan skill 現有結構——UC 盤點→Scenario Matrix→段落 0→段落設計標準（Context/1b/2/3/4）；測試規劃段插入位置＝Scenario Matrix 之後、段落 0 之前（top-level 區段序）。

### 修改要點

1. **新增 top-level「測試規劃段」規範**（skill 新區段，放 Scenario Matrix 後）：
   - 何時需要：中型以上且 EP 含可執行碼（純文檔 EP 跳過——標記理由）
   - **TC 格式**：每條 TC 含 claim（驗證什麼行為主張）／Given-When／oracle（**predicate-ID 拆分**——每個可獨立斷言的 predicate 一個 ID，禁複合斷言）／oracle_source（oracle 值的獨立來源——規格、領域恆等式、歷史數據；**禁指向待測實作**）／evidence class（L1-L6 對應）／uncovered（明示不覆蓋面）
   - **凍結語義**：TC 在實作段落設計前凍結；凍結後 EP 可改（其他段落）、TC baseline 不動；改 TC 走 amendment
   - **amendment 附錄**：old/new oracle＋reason＋independent evidence＋authority。**authority 四分**：invariant/reference truth 可證偽→judge；新 integration evidence→judge；user intent／product policy→人類；來源矛盾→人類。「實作現況」永遠不是證據。deviation log（前線提案，段落內記錄）與 amendment（判決，附錄記錄）兩份分離
   - **pre-RED challenge**（高風險/P0 觸發）：跨家族 advisory、fresh context、blind derive→reveal（先自行推 oracle 再比對，防錨定）＋completeness（抓漏場景）；必產 falsifiable 探針。觸發判準＝流程規模分級 full 檔＋silent-corruption path 命中
   - **same-family precondition（producer 側）**：EP 整合策略記 `author_family: <family>` **metadata 欄位**（非 prose）；消費端 gate 在 implement（S3）
2. **驗證策略段（段落設計標準 §4）退化自足**：含凍結 TC 的 EP，各實作段落的驗證策略須引用 TC-ID（＋必要時抄關鍵 predicate）——session 退化 handoff 後新 session 不需回讀 top-level 即可執行 RED（段落自足原則的 TC 延伸）
3. **skill 結構盤點面三處同步**：(a) 輸出結構行（「實作總覽→UC 盤點→Scenario Matrix→**測試規劃段**→段落…」）；(b) 段落設計檢查清單加「測試規劃段已完成（適用時）」列；(c) docs mode EP 元素對照表加測試規劃段行（純文檔 EP 跳過落點）
4. **段落 0 措辭**：cr-research full pin（S1 已動，本段核對無殘留＋Explore fallback 未誤升）

### 驗證策略

- `rg -n "predicate-ID|amendment|oracle_source|author_family" skills/execution-plan/SKILL.md` 命中新區段＋整合策略欄位
- `rg -n "blind.derive|same-family" skills/` 各命中一處定義源（execution-plan）
- 結構三處：`rg -n "測試規劃段" skills/execution-plan/SKILL.md` ≥4 命中（區段本體＋結構行＋檢查清單＋docs mode 表）
- 跨檔一致性：TC 格式語彙與 audit-test（S4）、code-review（S5）、fix-test（S6）的引用方向一致（定義源只此一處，消費端引用不重複定義——single-source drift 防護）
- `/consistency skills/execution-plan/SKILL.md`

---

## S3：implement skill——same-family gate（consumer 側）＋RED provenance 三栓＋frozen TC carve out

### Context

**背景**：v3.1 圖實作層——RED 三 gate 當場驗＋receipt 落檔＋digest 凍結＋same-family dispatch gate（S2 的 consumer 端）＋frozen TC 與既有裁量權契約的 carve out（codex F3：現行「EP 是收斂方向…前線 LLM 有裁量權」與「frozen test 唯讀」兩條高階規則衝突，LLM 自判 precedence 不足以支撐 provenance gate）。

**UC 引用**：實作「/implement RED provenance＋same-family gate」（UC 盤點 📋）。

**依賴關係**：消費 S2 的 TC-ID 格式＋author_family 欄位；與 S6（fix-test mutation authority gate）互掛——implement 撞牆（想改 truth 側）時的出口指向 fix-test 的 gate。

**語義約束**：三栓語彙（receipt／digest 凍結／基線跑法）與 audit-test 角度 8 對帳項**精確同名**（STRUCT_OK／SEM_OK／BEFORE_GREEN 三 gate 名進 audit-test 對帳敘述——對帳鍵單一套）。

**基礎設施盤點**：implement 階段 0（EP 快檢）＋階段 1（準備，含 backlog 更新）；「EP 段落元素→TDD 步驟」映射表（`skills/implement/SKILL.md:91-98`——驗證策略列對應 RED 步驟，**三 gate 掛此格**，非獨立 TDD 表）；「EP 專屬約束」段（:125-134 裁量權條款——carve out 落點）。

### 修改要點

1. **same-family dispatch gate**（掛階段 0/1）：EP 整合策略讀 `author_family` 欄位 → 對照本弧 resolved implement family → 相同時：RED 前必須 `challenge completed`（challenge findings 已 absorbed）或 `degraded: 明示記錄`（EP 欄位），兩者皆缺 → **不得進入 RED**（fail-loud 印 `[Same-Family Gate] blocked——需 challenge 或 degraded 標記`）
2. **三 gate**（掛「EP 段落元素→TDD 步驟」映射表的驗證策略→RED 格）：**STRUCT_OK**（測試結構可判 RED——非 skip/xfail 偽裝）／**SEM_OK**（斷言語義對應 TC predicate——凍結 TC 存在時逐 TC-ID 核對）／**BEFORE_GREEN**（基線跑法：新測試在 pre-change baseline 必須紅——baseline 綠＝vacuous/test-after 劇場化，直接退回）
3. **RED receipt 落檔**：RED 完成即寫（TC-ID＋baseline 身份＋test 檔 sha256 digest＋failing predicate 清單）——落任務家 `red-receipts.md`（非中途 commit；隨弧結案進版控）。digest 算式＝凍結定義（sha256 of test 檔 bytes，receipt 落檔時記）
4. **digest 凍結**：GREEN 前記 contract-test digest；GREEN 期 frozen test 唯讀——重算不一致＝靜默改（audit 角度 8 抓）
5. **frozen TC carve out**（掛「EP 專屬約束」段）：EP 一般為收斂方向、前線有裁量權——**但 frozen TC／oracle／contract-test digest 與其 authority/amendment 狀態不屬實作者自由裁量面**；遇此類衝突不套「記錄疑慮不中斷」：停 GREEN → mutation authority gate（S6）→ amendment 或 reject change；偏差走 deviation log（S2 定義）
6. 量級控制：核心入口（gate 行＋receipt 行＋carve out 行）＋最小必要展開，禁把 v3.1 全圖複述進 implement（細節住 execution-plan 測試規劃段＋本 EP）

### 驗證策略

- `rg -n "STRUCT_OK|SEM_OK|BEFORE_GREEN|red-receipt|Same-Family Gate|author_family" skills/implement/SKILL.md` 全命中
- `rg -n "mutation authority" skills/implement/SKILL.md skills/fix-test/SKILL.md` 兩檔互指一致（S6 完成後驗）
- 三栓語彙與 audit-test 角度 8 同名（`rg "STRUCT_OK|receipt|digest|基線跑法" skills/audit-test/SKILL.md`——S4 完成後驗）
- carve out 落點：讀「EP 專屬約束」段確認裁量權條款與 carve out 並存且 precedence 明確
- `/consistency skills/implement/SKILL.md`

---

## S4：audit-test skill——軸A 機械對帳擴充（角度 8 七項）

### Context

**背景**：審計層七項（裁決 §3 圖）：predicate 對帳／mock↔evidence class／oracle 圓形依賴／RED receipt＋digest／基線跑法／fixture provenance／路徑覆蓋反查。現有角度 1-7（反模式/覆蓋對稱/mock 健康/消費端/漸進/必要性/變異抽查）——七項是**測試契約消費面的對帳軸**，以獨立角度 8 擴充。

**UC 引用**：擴充「/audit-test 軸A」（UC 盤點 📋）。

**依賴關係**：消費 S2 TC 格式（predicate-ID 為對帳鍵）＋S3 receipt 檔（對帳對象）。

**語義約束**：機械對帳＝可 rg/檔案比對的操作型檢查項；對帳鍵語彙與 implement 三栓精確同名（STRUCT_OK/SEM_OK/BEFORE_GREEN 進對帳敘述）；判斷密集（如「mock 回傳值是否即 oracle」的 fidelity 裁決）標「需查證」交下游——與 audit 誠信約束一致。

**基礎設施盤點**：audit-test 檢查角度總表＋詳細定義節＋執行流程表＋健康度計算段（既有計數文字已 stale：寫「5 角度／6 角度」實際 7——本段順手修正）。

### 修改要點

新增「角度 8：測試契約對帳（EP 含凍結 TC 時）」——七項操作型檢查：

| # | 對帳項 | 機械操作 |
|---|---|---|
| 1 | predicate 對帳 | TC predicate-ID ↔ test 斷言逐一映射（rg TC-ID in test；缺漏列 finding） |
| 2 | mock↔evidence class | TC 標 L4-L6 的項若以 mock 驅動→finding（evidence 降級）；mock 回傳值來源比對 oracle_source |
| 3 | oracle 圓形依賴 | oracle_source 指向待測實作（或 test 硬編碼 impl 值）→Critical（此類屬 oracle 級：標記 escalate challenge，非 audit 自斷） |
| 4 | RED receipt＋digest | receipt 檔存在、TC-ID 齊、sha256 與 frozen test 現值一致（不一致＝GREEN 期靜默改——Critical） |
| 5 | 基線跑法（BEFORE_GREEN） | receipt 記 failing predicate；抽查測試在 baseline（`git stash` 形態）確實紅；STRUCT_OK/SEM_OK gate 痕跡核對 |
| 6 | fixture provenance | fixture 值來源標注（歷史數據/構造）；無源 fixture 用於 oracle 級斷言→finding |
| 7 | 路徑覆蓋反查 | 既有角度 4 引用（符號≠路徑）——TC 對應消費端路徑驅動確認，不重複定義、掛引用 |

同步面：檢查角度總表加行、執行流程表加步驟（條件觸發）、**健康度計算段既有 stale 計數一併修正**（5→7→8 角度計數＋角度 8 條件觸發計分規則：EP 含凍結 TC 才進分母）。

**觸發輸入 operationalize**：角度 8 觸發判定輸入＝任務家 `ep.md` 探測（arc/獨立跑形態——讀 EP 整合策略有無凍結 TC 段）或 session context EP（in-context 形態）；兩者皆缺→角度跳過（standalone 無 EP 的存量測試不適用）。

### 驗證策略

- `rg -n "角度 8|predicate 對帳|圓形依賴|fixture provenance|STRUCT_OK|BEFORE_GREEN" skills/audit-test/SKILL.md` 命中（三 gate 語彙在場——對帳鍵單一套）
- 角度總表/詳細定義/執行流程/健康度四處同步（rg 角度計數無 stale 數字）
- 與角度 4 的引用關係正確（路徑覆蓋不重複定義——rg 確認單一源）
- `/consistency skills/audit-test/SKILL.md`

---

## S5：code-review skill＋code-review-and-quality——軸B 測試架構面六項（dual-context wiring）

### Context

**背景**：審查層（user r3 刀二）：「先審 test」若只審「忠實翻譯 TC」是機械軸（歸 audit）；review 層做**架構面**——這次 diff 的整體測試邏輯作為系統守不守得住。六項：拓撲 vs blast radius／層級平衡／符號≠路徑／evidence fidelity／shared dependency／耦合面。**翻譯忠實度（test 是否忠實翻譯 TC）明寫不歸它**（歸軸A）。

**wiring 決策（凍結——三方審查修正）**：六項掛 **dual-context（模式 B）兩側 spawn prompt 的共用檢查面**（`diff 含 test files` 時注入 fresh-eyes＋primed 兩側；primed 額外拿 frozen TC 作 context）——模式 B 是非 ultracode 的預設審查路徑且「跨 session dual-context」正是裁決 §3 指名載體；Workflow 模式 A 的 axis 3 啟用面同步加（兩模式都接）。六項**定義源住 code-review-and-quality skill 架構 checklist 節**（六軸定義單一源紀律），code-review SKILL.md 只留啟用條件＋pointer。

**UC 引用**：擴充「/code-review 軸B」（UC 盤點 📋）。

**依賴關係**：無上游（六項是 diff 結構面判讀，不依賴 TC 存在）。與 S4 正交分工：機械→軸A、結構→軸B。

**基礎設施盤點**：code-review 模式 B（dual-context 表 :99-105）、模式 A 啟用軸表；code-review-and-quality ### 3（Architecture checklist——六項定義落點）＋### 1（Correctness checklist 含 "Tests cover the change…"——排除面劃清對象）。

### 修改要點

1. **code-review-and-quality `### 3` 加六項定義**（定義源）：拓撲 vs blast radius（測試拓撲與變更 blast radius 對稱——高 ripple 低覆蓋→finding）／層級平衡（unit/integration 分佈與變更性質匹配）／符號≠路徑（引用 audit 語彙不重複定義）／evidence fidelity（測試宣稱證據等級與實際機制相符——標 E2E 實為 mock 鏈→finding）／shared dependency（測試間共享狀態/fixture 污染面）／耦合面（test 與 impl 耦合深度）
2. **code-review SKILL.md 掛 wiring**：模式 B——`diff 含 test files` 時 fresh＋primed 兩側 prompt 注入六項（primed 加 frozen TC）；模式 A——axis 3 啟用條件加「diff 含 test files」＋六項 pointer
3. **排除面聲明**（兩處）：(a) 翻譯忠實度（test↔TC 逐條對帳）不歸軸B——歸 audit-test 軸A；(b) Correctness 面 "Tests cover the change…" 的結構面充分（軸B 判）vs 逐條 TC 對帳（軸A 判）劃清——防越權回流

### 驗證策略

- `rg -n "拓撲|evidence fidelity|shared dependency|翻譯忠實" skills/code-review/SKILL.md skills/code-review-and-quality/SKILL.md` ——定義只在後者、啟用/pointer 在前者（rg 跨檔對照無重複定義）
- 模式 B wiring：`rg -n "diff 含 test|fresh.*primed|dual-context" skills/code-review/SKILL.md` 命中注入條款
- 排除面兩處在場且指向 audit-test
- `/consistency skills/code-review/SKILL.md`＋`/consistency skills/code-review-and-quality/SKILL.md`

---

## S6：fix-test skill——mutation authority gate＋Type B/C/E escalation

### Context

**背景**：撞牆處置（v3.1 圖）：想改哪側 truth→有沒有 authority；TC oracle→停 GREEN→amendment。fix-test 是測試修改的主入口（分類 A-E）——Type B（契約變更）/Type E（過時）正是「改測試側 truth」的分類位，掛 TC escalation。**Type C（測試腐化，行動同為重寫）同納**——gate 本質是「改測試側 truth 需 authority」，C 路徑重寫同樣改 truth（裁決 §5 只寫 B/E，C 是 EP 層完形）。

**UC 引用**：擴充「/fix-test mutation authority gate」（UC 盤點 📋）。

**依賴關係**：消費 S2 amendment 語彙（引用不重複定義——authority 四分映射不在此重列）；與 S3 互掛（implement 撞牆出口指向本 gate）。

**語義約束**：escalation 是 signal 不是自動判決——分類仍走現有決策樹，gate 後掛在 B/C/E 判定後（確認清單加一項），決策樹結構不改道。

### 修改要點

1. **mutation authority gate**（新小節，掛階段 2 分類後、階段 3 確認前）：測試對應凍結 TC 時，Type B/C/E 判定後強制過 gate——
   - 查 authority：變更理由屬 amendment authority 四分哪類？（四分定義見 execution-plan 測試規劃段——**本處引用不重列映射**）
   - 「實作現況」作為重寫理由→擋下，指向 amendment（走 execution-plan amendment 附錄）
   - 無凍結 TC（舊 EP/存量）→gate 跳過，沿用現行必要性審查（B/C 重寫前審查不變）
2. **escalation signal**：分類報告（階段 3）表格加欄「TC escalation」——Type B/C/E 對應 TC-ID 與 authority 判定結果；人類確認時一併裁決
3. 語彙互掛：implement（S3）的「想改 frozen test」出口指向本 gate；本 gate 的 amendment 指向 execution-plan 附錄（S2）

### 驗證策略

- `rg -n "authority|amendment|escalation" skills/fix-test/SKILL.md` 命中；**authority 四分映射不在此檔重列**（rg "invariant.*judge" skills/fix-test/SKILL.md 零命中——引用句形態）
- 決策樹（階段 2）未被破壞——gate 是後掛非改道（讀現行決策樹結構確認）
- `/consistency skills/fix-test/SKILL.md`

---

## S7：附帶同步面（導航/投影/索引）

### Context

**背景**：tri-audit 修正方向①的附帶清單＋handoff scope 附帶項。全部是小改（半句～一行級），收斂成一個掃尾段。**gate：本段整體 gate 在 S2-S6 完成後**（狀態投影/索引描述反映終態——S0 失敗時本段全停，防 false-green）。

**依賴關係**：最後段（S2-S6 落檔後）。

### 修改要點

1. **workflow viewport ②⑤站**：`ai-analysis/blueprint/workflow.md` ②規劃站補「高風險/P0 pre-RED challenge（跨家族 blind-derive）」半句；⑤驗證站既有句補 mutation authority gate 字樣；**:16/:19 兩處「（v3.1 定案，落檔隨測試契約卡）」狀態詞隨終態翻新**（刪 pending 語意）
2. **blueprint v3.1 節狀態**：`workflow.md` 測試契約節標題「⚠️ 架構定案（三方裁決 v3.1），六檔落檔待建卡」→「✅ 已落檔」終態（一句寫死，不留中間態）
3. **skills/CLAUDE.md 五命令索引**：execution-plan／implement／code-review／audit-test／fix-test 的 description 行補測試契約面（各半句：測試規劃段凍結 TC＋author_family／same-family gate＋RED 三栓／dual-context 軸B 架構面／角度 8 七項對帳／authority gate）
4. **/commit 例外清單複驗**：rg 已確認 `skills/commit/SKILL.md:168,188` 為 pointer 形態——tri-audit 該子項已完成；`rg -n "建卡.*ruff|ruff.*建卡" skills/commit/SKILL.md` 零命中即通過
5. **rules/model-routing.md 段落 0 消費端**：rg `skills/execution-plan/SKILL.md` 段落 0 無 lite pin 殘留＋Explore fallback 未誤升（S1 已動，複驗）

### 驗證策略

- 全域 rg 殘留掃（見整合策略）
- `skills/CLAUDE.md` 索引與六檔現行為對照（抽 3 條敘述核對）
- workflow.md 內部狀態一致：`rg -n "落檔隨測試契約卡|待建卡" ai-analysis/blueprint/workflow.md` 零命中（終態後）

---

## 整合策略

- 段序：S0（MVP）→ S1（routing 原子切）→ S2（詞彙源）→ S3→ {S4, S5, S6 平行} → S7（掃尾）
- **S0 不過線：僅 S1 可跑；S2-S7 全停**，blueprint 保持 ⚠️，回報 user 裁決（SM-11）——S7 的狀態投影/索引 gate 在 S2-S6 完成後，失敗弧中照跑＝false-green
- **全域最終驗證（S7 後）**：
  - `rg -n "predicate-ID" skills/ rules/` ——定義源僅 execution-plan，消費端引用不重複定義
  - `rg -n "authority 四分|amendment authority" skills/` ——定義源僅 execution-plan（fix-test 引用句形態，無映射重列）
  - `rg -in "cr-research" rules/ skills/ agents/ scripts/` 全命中為 full 語意（無 lite 殘留）＋`rg -n "tier: lite" agents/roles/cr-research.md` 零命中＋Explore fallback 仍 lite
  - `rg -n "STRUCT_OK|SEM_OK|BEFORE_GREEN|red-receipt" skills/` 命中 implement＋audit-test（**對帳鍵單一套——audit-test 角度 8 敘述含三 gate 名**）
  - 六檔＋code-review-and-quality 逐一 `/consistency`
  - `uv run pytest tests/test_sync_agents.py` 綠
  - deploy 驗證：`uv run python scripts/deploy_agents.py`（skills 是 symlink 非 bundle 內容——跑 gate 確認無增量）
- **commit 分組**：S1+S2 一組（routing＋契約層）、S3-S6 一組（執行/審計/審查/修復鏈）、S7 一組（投影/索引）——實際分組隨 /commit 慣例（EP 描述是規劃語境非授權）

## 收尾步驟

1. **文檔收尾**：
   - `skills/CLAUDE.md` 工作流索引已同步（S7）
   - blueprint workflow.md v3.1 節翻 ✅（S7）
   - tri-audit synthesis X1/X2 對應項標 materialized（本 EP 提交訊息帶入，synthesis 檔本身不改——報告是時點快照）
2. **測試契約 self-dogfood**：本 EP 自身無凍結 TC（product 全文檔無可執行碼面）——MVP 報告即本弧 evidence artifact
3. **backlog**：追蹤卡結案兩步（`-s Done --final-summary` → `--ref` done/ URL）＋AIR-70 卡 notes 補一行「test-gen P0 結論已落 lifecycle 表（本弧）」
4. **memory 結案蒸餾**：`project_ep-test-contract-top-level-before-impl` 蒸餾終態（待建卡→已落檔）
5. **/audit-test**：無新 pytest（MVP 素材非 pytest）——跳過標記理由；S1 的 pytest baseline 已在段內跑

---

## EP Review Findings

> 三方獨立審查（muse `job-mtwis8ej` xhigh 13 findings／GLM 側背景 agent 17 findings／codex `job-mtwis8kb` chatgpt-web/high 5 findings）→ 主 session judge 裁決（21 ✅ 採納全部落地於上方段落、1 項列 gate 候選）。原始報告：`.agent-tmp/ep-review-{muse,codex}.out`＋GLM agent transcript（7 天區）。

| ID | 來源 | 嚴重度 | 問題摘要 | 決策 | 落點 |
|----|------|--------|---------|------|------|
| F1 | codex | 🔴 | same-family precondition 只有 producer 無 consumer gate（producer/consumer 斷鏈） | ✅ | S2 加 author_family metadata 欄位；S3-1 same-family dispatch gate（RED 前攔截） |
| F2 | codex＋GLM＃1＋muse＃8b | 🔴 | S0 失敗仍跑 S7 → blueprint 假狀態 false-green | ✅ | 整合策略改「S0 不過線僅 S1 可跑；S2-S7 全停」；S7 Context 加 gate 宣告 |
| F3 | codex＋GLM＃15 | 🔴 | frozen TC 與 implement「EP 只是方向」裁量權正面衝突，LLM 自判 precedence 不足 | ✅ | S3-5 carve out（契約面不屬裁量面；衝突停 GREEN 走 gate 不套「不中斷」） |
| F4 | codex＋GLM＃4＋muse＃11 | 🟡 | docs mode 宣告自創「配置值例外」違反單一源判準 | ✅（採 codex 處方） | 檔頭改不宣告 docs mode；全 md 段段內 docs-style 驗證；S1 機械驗證。**gate 候選：docs-mode config-value 例外條款（交 user）** |
| F5 | codex＋GLM＃6＋muse＃6 | 🟡 | 軸B 六項掛 axis 3 只覆蓋 Workflow 模式；預設 dual-context（模式 B）無掛點；定義源漏 code-review-and-quality | ✅ | S5 wiring 重寫：dual-context 兩側注入＋定義源住 code-review-and-quality ### 3＋模式 A/B 都接 |
| F6 | muse＃1＋GLM＃3 | 🟡 | Lane B expected-routing 未凍結＋oracle escalate 條款無觸發構造 | ✅ | S0-2 六行 expected-routing 表（預凍結）＋S0-4 混入 oracle mutant 驗 escalate＋同義反覆歸屬釐清 |
| F7 | muse＃3 | 🟡 | :165/:21 一行兩 tier 陳述，誤改會把 Explore fallback 一併升 full | ✅ | S1 錨點表加半句框定欄＋驗證策略加 Explore fallback 未誤升檢查 |
| F8 | muse＃4 | 🟡 | roles 檔 :3 不含 "cr-research" 字串——rg 驗證抓不到 tier 殘留（gate 盲區） | ✅ | S1 驗證策略加 `rg "tier: lite" agents/roles/cr-research.md` 直驗 |
| F9 | muse＃2 | 🟡 | :43 目標措辭未給（muse 收斂/flash 半句糾纏） | ✅ | S1 錨點表給目標句式（muse 收斂保留、tier 轉 full） |
| F10 | GLM＃5 | 🟡 | S2 漏 skill 結構盤點面三處（輸出結構行/檢查清單/docs mode 對照表） | ✅ | S2 修改要點 3 |
| F11 | GLM＃2 | 🟡 | 對帳鍵 token 兩套（STRUCT_OK vs receipt/digest）不一致——整合驗證 rg 必 miss | ✅ | S4 語義約束＋對帳項 5 含三 gate 名；整合驗證單一套 |
| F12 | muse＃7 | 🟡 | S6 括號重述 authority 四分映射違反自家單一源規則 | ✅ | S6 改引用句＋驗證策略加「無映射重列」rg |
| F13 | muse＃8a＋GLM＃13 | 🟡 | 止血項時點（建卡→開工窗口無防護） | ✅ | 實作總覽止血時點段（EP 定稿建卡後本 session 即落 working tree）；S0 起手式 rg 確認 |
| F14 | GLM＃7 | 💡 | 「AIR-76」前向引用未驗證（卡未建）＋S7-2 三重描述矛盾 | ✅ | S7-2 一句寫死終態、刪 AIR-76 字樣 |
| F15 | GLM＃10 | 💡 | digest 算式未釘死（S3 記錄/S4 比對無共同算式） | ✅ | 已決策段凍結：sha256 of test 檔 bytes、receipt 落檔時記 |
| F16 | GLM＃9 | 💡 | Type C（腐化重寫）繞過 gate（行動同為重寫） | ✅ | S6 gate 覆蓋 B/C/E |
| F17 | muse＃12＋GLM＃16 | 💡 | audit-test 健康度計數既有 stale（5/6 vs 實際 7） | ✅ | S4 同步面明寫修正計數（→8＋條件觸發計分） |
| F18 | muse＃13＋GLM＃8 | 💡 | ⑤站 challenge 半句二選一未寫死＋:16/:19 狀態詞殘留 | ✅ | S7-1 寫死（②補 challenge、⑤補 mutation gate）＋狀態詞翻新＋rg 驗證 |
| F19 | GLM＃11 | 💡 | MVP spawn tier 口徑未明（full 模擬會高估部署面能力） | ✅ | S0 基礎設施盤點明寫 registry lite 口徑（實驗形態明示） |
| F20 | muse＃9 | 💡 | 「TDD 表 RED 列」錨點不精確（實為映射表驗證策略→RED 格） | ✅ | S3-2 點名 `skills/implement/SKILL.md:91-98` 映射表格 |
| F21 | muse＃10 | 💡 | 排除面只擋「翻譯忠實度」，Correctness checklist 越權回流風險 | ✅ | S5-3 排除面兩處（軸B 結構面 vs 軸A 逐條對帳劃清） |
| F22 | GLM＃17 | 💡 | 角度 8 觸發輸入未 operationalize（standalone 跑不知 EP 存在） | ✅ | S4 觸發輸入段（任務家 ep.md 探測/context EP；皆缺→跳過） |

**gate 候選清單（judge 提案，交 user）**：docs-mode 判準的 config-value 例外條款（pins dict 類值變更——本弧以「normal EP＋段內驗證」繞過；若未來同形態再撞，值得在 execution-plan skill docs mode 段正式立例外行）。
