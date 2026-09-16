# EP: 四家比較路由反饋修訂——handoff tier 欄／架構級 EP 出口／開卡屬性標註／旗艦資格條款（七項）

> **ep_type**: implementation（docs mode——product 全為 instruction/documentation 檔）

baseline: 7ef65c6

## 實作總覽

基於 mosaic 2026-09-06/07 四家模型比較（旗艦／lite／muse／codex 同尺評測）修訂 ai-rules 路由體系七項（spec：`ai-analysis/_tasks/09-07-routing-feedback-tier/spec.md`——含證據錨點與 user 拍板，EP 引用不重抄）。

**核心裁決（勿重辯）**：路由詞彙一律「旗艦／一般」tier 抽象；模型名只在 tier→(model,effort) 解析層；family 軸（muse/codex）是第二軸非 tier 降級。

**本弧查證事實**（規劃時 rg 實測）：
- 八欄 schema 單一源＝`skills/self-contained-prompt/SKILL.md`（handoff 是消費側——A 項落點在此非 handoff skill 本體）
- eligibility gate 五條＝`skills/model-routing/SKILL.md:110`（B 項增條對象）
- claim 群＝`rules/acceptance-evidence.md:19-24`（:19 引言＋四條 bullets，E 項加第五條）
- **D 項「lite 省 43-57% token」在 ai-rules 產品面（rules/skills/agents，排除任務家）查無此行**（rg `43-57|43～57` 零命中）——該宣稱是 mosaic 側樣本；ai-rules 僅有「省成本層」泛稱（skill :12/:28）——D 處置＝S2 內標的查證後記錄（無標的不虛構但書；「省成本」泛稱若日後引入省幅數字，可比時窗原則進 G 坐位註記側欄語義）

## UC 盤點

### Backlog 關聯
- AIR-38（本弧追蹤卡，7ef65c6）
- 關聯弧：AIR-24（flash 分工律——G 資格條款是其深化）、AIR-29（agents 兩軸重構——family 軸語義）、AIR-37（memory 閘門——S3 同檔 execution-plan，**依賴其 S2 先落地**）

### SYSTEM-MAP 影響
- 無（元專案無 SYSTEM-MAP.md）

### 掃描範圍
- 變更面：`skills/self-contained-prompt/SKILL.md`（schema）、`skills/handoff/SKILL.md`（消費側）、`skills/model-routing/SKILL.md`（family 表/eligibility gate/tier 段/坐位註記）、`rules/model-routing.md`（pointer 行）、`skills/execution-plan/SKILL.md`（C 項，排 AIR-37 後）、`skills/kanban-board/SKILL.md`（desc gate 屬性標註語義）、`rules/acceptance-evidence.md`（claim 群）、`skills/acceptance-evidence/SKILL.md`（詳案例）

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| handoff 標準 schema（八欄） | ✅ | self-contained-prompt skill | 更新 | 加兩欄（建議執行 tier＋workspace/卡歸屬） |
| external-runtime eligibility gate（五條） | ✅ | model-routing skill :110 | 更新 | 增「使用者會話在場裁決」（架構級 EP 前提） |
| flash 分工律 | ✅ | model-routing skill | 擴展 | G 資格條款＝分工律的旗艦側資格線深化 |
| 同型 claim 群 | ✅ | rules/acceptance-evidence.md | 更新 | 加「自報元資料不可信」型 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| handoff 路由資訊欄（建議執行 tier＋卡歸屬） | 📋 | self-contained-prompt＋handoff skill |
| 架構級 EP（blueprint）family 軸出口 | 📋 | model-routing skill family 表＋gate |
| 旗艦 tier 資格條款（五項）＋坐位註記 | 📋 | model-routing skill tier 段＋解析表側欄 |
| 開卡風險屬性標註 | 📋 | execution-plan＋kanban desc gate |
| 自報元資料不可信 claim | 📋 | rules/acceptance-evidence＋skill |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | handoff 產交接 prompt | 任意交接 | schema 含「建議執行 tier」（條件式：一般三條件全滿／旗艦五項不可讓）＋workspace/卡歸屬欄 | 無 | handoff 路由欄 |
| SM-1b | 跨 provider 交接 | handoff Phase 3 機密檢查場景 | workspace/卡歸屬欄＝內部拓撲資訊——對外暴露面判定（抽象化/省略）；tier 欄對無 ai-rules 詞彙背景的接手方自足 | 無 | handoff 路由欄 |
| SM-2 | 架構級 EP（blueprint）委派 | 大型規劃跨家族 | eligibility gate 增「使用者會話在場裁決」——無 user 在場證據面為零，不放行 | 無 | 架構級 EP 出口 |
| SM-3 | tier 詞彙寫作 | 任意 routing 文檔 | 旗艦/一般（tier 層）；模型名只在解析表——混用即 drift | 無 | tier 抽象 |
| SM-4 | 候選模型升旗艦坐位 | 換代/新模型 | 既有比較尺（四軸＋五項任務）跑一弧實測→坐位註記單行改——條款不動；「候選觀察：X（觀察中未升）」寫入/清除同此行 | 無 | 旗艦資格條款 |
| SM-5 | 開卡帶風險屬性 | EP 建卡 | desc「已決策」段可含屬性標註（寫入契約首改/跨文件交叉推導/無保護面新能力）——handoff tier 欄的輸入 | 無 | 開卡屬性標註 |
| SM-6 | agent 自報判讀統計 | vision 判讀/分類彙算 | 自報分類/判讀元資料禁當統計源——llm_label vs 標準答案逐案機械比對 | 無 | 自報元資料 claim |
| SM-7 | D 項成本宣稱 | 引用省幅數字 | 標的查證：ai-rules 查無「43-57%」行→記錄不落地；未來引入省幅數字時限可比時窗 | 無 | — |
| SM-8 | 定義源修改後同步 | 本弧任一 tier/gate/schema 定義變更 | F 執行：rg 掃引用面清單→逐檔同步判定→證據入收尾報告 | 無 | —（F 執行義務） |

## 段落劃分原則

定義源（schema/routing 條款）先行；同檔聚集（model-routing 三項一併）；C 項依賴 AIR-37 S2 落地（execution-plan 同檔）排後；docs mode 全段。

---

## S1：handoff 路由資訊欄（A 項——schema 定義源）

### Context
- **UC 引用**：實作「handoff 路由資訊欄」
- schema 單一源＝`skills/self-contained-prompt/SKILL.md`（八欄表 :42 起）；handoff skill 是消費側（Phase 1 套 schema）——**A 項落點在本檔**（spec 寫 handoff skill，查證後單一源在 self-contained-prompt——改定義源＋消費側同步）
- **語義約束**：tier 欄內容是**條件式不是斷言**（與 G 資格條款同詞源：「一般」三條件全滿＝保護面厚＋EP 條款機械可判＋審查鏈全開；「旗艦 only」五項不可讓＝judge／編排／post-build 終審／跨文件交叉推導／寫入契約首次改動）；模型名不進此欄（tier 層）
- **基礎設施盤點**：schema 八欄表、handoff skill Phase 1/2（嵌入程度）、`rules/model-routing.md` tier 詞彙句（引用源）
- **依賴錨點**：`skills/self-contained-prompt/SKILL.md:42-49`（schema 表，表頭 :40 起）、`skills/handoff/SKILL.md` Phase 1 段

### 修改要點（docs mode）
1. schema 表加第 9 欄「**建議執行 tier**」——內容規範為條件式（一般 vs 旗艦 only 兩分支，條款文字與 model-routing skill G 資格條款同一詞源——此處一行濃縮＋指向，不重抄五項全文）
2. schema 表加第 10 欄「**workspace／卡歸屬**」——強制欄（跨 worktree 教訓：runtime 的 workspace＝TUI cwd，不會自己管卡歸屬；內容＝repo/WT 路徑＋卡 id 歸屬）
3. handoff skill Phase 1 消費側同步：套 schema 處提及新欄（「建議執行 tier」是 user 開 session 的路由輸入）；參數表/執行約束相應一行
4. **SM-1b 落點（muse review F2）**：handoff Phase 3 機密檢查清單補判定項——「workspace／卡歸屬欄＝內部拓撲資訊」：跨 provider 形態下的抽象化／省略判定（tier 欄條件式自足、無模型名，逕用）

### 驗證策略（docs mode）
- `rg "建議執行 tier|卡歸屬" skills/self-contained-prompt/SKILL.md skills/handoff/SKILL.md` → 兩檔命中
- 欄數宣稱同步：「八欄」字樣改「十欄」（rg 掃殘留）
- 詞形與 S2 G 條款對齊（跨檔 rg）

---

## S2：model-routing 三項（B 架構級 EP 出口＋D 但書＋G 資格條款）

### Context
- **UC 引用**：實作「架構級 EP family 出口」＋「旗艦資格條款與坐位註記」
- 落點：`skills/model-routing/SKILL.md`——family 表/角色域（B）、eligibility gate :110（B 增條）、tier 段（G 條款主體）、tier 表側欄（G 坐位註記）、flash 分工律段（G 詞源銜接）；`rules/model-routing.md` 加 G pointer 行（rule 骨架不膨脹——bundle 預算紀律）
- **語義約束**：與 S1 共享條款詞源；「資格條款（大綱層，穩定）vs 坐位註記（解析表側欄，單行，換代只改此行）」分層——G 核心；與既有「tier 詞＝requirement token」同構表述
- **依賴關係**：S1 的條件式欄引用本段條款
- **基礎設施盤點**：角色→family→profile 映射表 :86-96（B 行落點）、family→(model,effort) 表 :100-106、eligibility gate :110、role→requirement 表 :46-52、tier 詞定義 :12、解析表 :16-18、flash 分工律段（詞形對齊對象）
- **依賴錨點**：`skills/model-routing/SKILL.md:110`（gate 五條）、:12（tier 詞定義）、:16-18（解析表）

### 修改要點
1. **B**：external-runtime 角色→family→profile 映射域（:86-96）加「架構級 EP（blueprint）」行——eligibility 前提「**使用者會話在場裁決**」（證據：muse 在 user 質疑收斂模式下產出架構翻轉級 blueprint；無 user 在場證據面為零）；**gate 增此為第六條**（不採行內註記分支——枚舉結構保持顯式）；`rules/model-routing.md:34` 枚舉詞「eligibility gate 五條」→「六條」同步（列入變更面）
2. **G 條款**：tier 段加「旗艦資格條款（五項）」小節——跨文件交叉推導力／judge 否決力／規劃的契約查證力／長弧查證紀律／寫入邊界首改的邊界意識（每項一句＋證據指針一句，全文五項 ≤10 行——spec 詳版自包含，skill 收濃縮版＋指向 spec？不——spec 是弧產物會歸檔；條款全文入 skill〔它是 method 載體〕，spec 證據錨點不複製）
3. **G 坐位註記**：tier 解析表後單行——**只記變動欄位**：「候選觀察：無；升坐位法：既有比較尺（四軸＋旗艦不可讓五項任務）跑一弧實測」——**現值坐位不重複記載**（＝tier 表 full 行 zai 欄，單一記載形態），換代只改表行
4. **D**：標的查證記錄（rg 產品面 `43-57|省.*%` 掃描證據入 EP 對照）；無標的→條文不動，本 EP 記錄「未落地理由」；「省成本」泛稱不動
5. **詞形對齊（review F5/F2）**：①lite 中文標籤「隨意」→「**一般**」統一（`rules/model-routing.md:11` 詞彙句、skill :3 frontmatter、:12 tier 詞定義、:18 表列標籤——**英文 token full/lite/vision 不動**，動的只是中文語義標籤）；②兩套降級條件管轄邊界寫死一句：flash 分工律三件（既有測試釘住＋驗證閉環＋非跨邊界語義面）＝**spawn 執行層降級**判定；handoff tier 欄三條件（保護面厚＋EP 條款機械可判＋審查鏈全開，spec A 原文）＝**handoff 路由建議**判定——兩個管轄面詞形各異非 drift，在分工律段補此對照句
6. **內容列舉同步（review F7）**：skill :3 frontmatter description＋`skills/CLAUDE.md:132` 索引行——「旗艦資格條款／坐位註記」入列舉、「隨意」→「一般」
7. `rules/model-routing.md` tier 詞彙句後加一行 pointer：「旗艦資格條款（五項）與坐位註記見 model-routing skill」（rule 留骨架）
8. **F 預備**：本段改 tier 定義/gate/角色——觸發單一源掃描（S5 執行）

### 驗證策略
- `rg "旗艦資格條款|坐位" skills/model-routing/SKILL.md` 命中；`rg "旗艦資格條款" rules/model-routing.md` pointer 命中
- `rg "六條"` gate 段與 rule:34 枚舉詞一致（增條後兩處同步）
- `rg "隨意"` **tier 標籤殘留歸零**——僅計 rule:11／skill:3/:12/:18 四處形態；`flow-review:33`「降隨意性」等日常中文詞與歸檔卡歷史字樣**不在此列**（不回改，見 S5 規則）
- 詞彙一致：條款文字無模型名（tier 層純淨）——rg 條款段 `GLM|muse|flash` 零命中（坐位註記行除外）
- D 查證輸出入段落對照（產品面措辭）

---

## S3：開卡風險屬性標註（C 項——依賴 AIR-37 S2 落地後執行）

### Context
- **UC 引用**：實作「開卡風險屬性標註」
- **依賴關係**：🔴 `skills/execution-plan/SKILL.md` 與 AIR-37 S2（UC 盤點加 memory 登記行）同檔——本段**排 AIR-37 實作完成後**執行（避免並行編輯衝突）；AIR-37 未落地前本段懸置
- **語義約束**：屬性標註進 desc「已決策」段（卡是長期追蹤物——寫屬性不寫 model 名，模型可用性會變）；屬性是 handoff tier 欄（S1）的路由輸入
- **基礎設施盤點**：execution-plan UC 盤點步驟 3 建卡指引（desc gate 三必有）；kanban skill desc gate 段
- **依賴錨點**：`skills/execution-plan/SKILL.md` 建卡指引處；`skills/kanban-board/SKILL.md` desc gate 段

### 修改要點
1. execution-plan 建卡指引（UC 盤點步驟 3 的 `backlog task create` 說明）補一句：desc「已決策」段可含**風險面屬性標註**（「寫入契約首改」「跨文件交叉推導」「無保護面新能力」）——作為後續 handoff「建議執行 tier」的輸入
2. kanban skill desc gate 段補對應語義一句（屬性標註是「已決策」段的合法內容形態）

### 驗證策略
- `rg "屬性標註" skills/execution-plan/SKILL.md skills/kanban-board/SKILL.md` 命中
- 與 S1 詞形銜接（handoff tier 欄讀的屬性詞形一致）

---

## S4：自報元資料不可信 claim（E 項）

### Context
- **UC 引用**：實作「自報元資料不可信 claim」
- 落點：`rules/acceptance-evidence.md:19-21` 同型 claim 群（加一條）；`skills/acceptance-evidence/SKILL.md` 詳案例段（vision 111 案 44 漏報實證）；`skills/review-engine/SKILL.md` 掃「自報」相關條文，有則同步（無則跳過——rg 查證）
- **語義約束**：與既有「量測數字必獨立重測」同型並列（lite tier 版：自報分類/判讀元資料必機械比對）
- **依賴錨點**：`rules/acceptance-evidence.md:19`（同型 claim 群標題行）

### 修改要點
1. claim 群加一條：**自報元資料不可信**——自報分類／判讀元資料（agent 對自己輸出的 label 統計）禁當驗收統計源；正解＝llm_label vs 標準答案逐案機械比對（rule 一行版）
2. acceptance-evidence skill 對應詳案例段補實證（vision 判讀 111 案自報 contradicts 漏報 44——模型給了不同 label 卻自報未推翻）＋「Review 雙向應用」的對應觸發形態
3. review-engine skill rg 查「自報」——有 spawn prompt/驗證條文觸及則補一句，無則跳過

### 驗證策略
- `rg "自報元資料" rules/acceptance-evidence.md skills/acceptance-evidence/SKILL.md` 命中
- rule 一行版 vs skill 詳版的分層（rule 不膨脹）

---

## S5：單一源掃描（F 項執行）＋收尾

### Context
- F 是**執行義務**非新條文——`rules/_ai-behavior-constraints.md` 既有 single-source drift 防護已涵蓋（改定義源掃引用逐檔同步）；本段執行它並產出證據

### 修改要點
1. **F 執行**：本弧改動的定義源（tier 詞彙/gate/角色表/schema 欄/claim 群）——`rg` 掃引用面清單（每個定義源的關鍵詞→引用檔列表），逐一判讀同步需求，證據入收尾報告。**掃描判定追加項（review F8/F9）**：①`agents/AGENTS.md:34`「EP 規劃不 agent 化」與 B 出口（family 軸非 agent 化）語義張力——補 pointer 或記錄免改理由；②`skills/_common/agent-review-cycle.md:60` 引用 self-contained-prompt **原則**（原則第二消費側——schema 加欄對 subagent prompt 形態影響待判）；③backlog 歸檔卡（如 air-14）含「八欄」歷史字樣——**歸檔卡不回改**（歷史記錄），掃描命中僅註記
2. 卡結案兩步＋第三動（本弧 memory 蒸餾——routing 反饋相關條目若在池中）；**卡標題「（六項）」→「（七項）」同步**（review F11——G 追加時未同步標題）
3. /audit-test：docs mode 跳過（標記）

### 驗證策略
- F 掃描證據清單（定義源×引用面×同步/不需動判定）
- 卡 Done＋雙 ref；EP 歸檔

---

## 整合策略

- baseline: 7ef65c6
- 執行順序：S1→S2（詞源鏈）→S4（獨立）→**S3（等 AIR-37 S2）**→S5；**S3 升級路徑（review F10/F5）**：implementer 在 S3 開工前查 AIR-37 卡狀態判定是否停滯並記錄——判定停滯（卡長期 In Progress 無進度）→ 升 user 裁決（S3 拆小卡轉掛 / AIR-38 先結案 S3 另開補弧）——不無限等待
- spec 證據錨點自包含於任務家（EP 引用不重抄——歸檔後 spec 隨任務家保存）

## EP Review Record（GLM fresh-eyes 09-07 完成；muse 腿 fire-and-forget 補審修正版）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| F1 | G 坐位行重複記載模型現值（與 tier 表 full 行）——「換代只改此行」自破 | M/0.85 | ✅採納 | 坐位行只記候選觀察＋升坐位法，現值指向 full 行 |
| F2 | S1 三條件＝第三份降級條件枚舉（與分工律三件詞形出入）＋分工律落點 dangling | M/0.8 | ✅採納 | S2 要點 5 管轄邊界寫死＋落點/要點對應 |
| F3 | family 表/role 表行號錨點失準 | M/0.9 | ✅採納 | :86-96/:100-106/:46-52 修正 |
| F4 | claim 群錨點短報（:19-21→:19-24） | L/0.7 | ✅採納 | 修正 |
| F5 | 「一般」與既有 lite 標籤「隨意」雙標籤——SM-3 自檢命中自己 | H/0.75 | ✅採納 | 四處「隨意」→「一般」（token 不動，動中文標籤） |
| F6 | gate 增條「或行內註記」分支未收斂＋rule:34 枚舉詞未列變更面 | M/0.75 | ✅採納 | 收斂第六條＋rule:34 同步 |
| F7 | frontmatter＋skills/CLAUDE.md 索引未列同步 | M/0.7 | ✅採納 | S2 要點 6 |
| F8 | agents/AGENTS.md:34 與 B 出口語義張力未判定 | L/0.6 | ✅採納 | S5 掃描判定項 |
| F9 | schema 第二消費側（agent-review-cycle）＋歸檔卡「八欄」未判定 | L/0.65 | ✅採納 | S5 追加項＋歸檔卡不回改規則 |
| F10 | S3 懸置無升級路徑 | M/0.7 | ✅採納 | 整合策略補升級句 |
| F11 | 卡標題「六項」vs 七項不一致 | L/0.55 | ✅採納 | S5 結案同步 |

### muse 補審（job-mtqs2rfz，額度重置後；GLM 11 項修正全確認）

| # | Finding | 嚴重度/信心 | 裁決 | 處置 |
|---|---------|------------|------|------|
| mF1 | 驗證判準「rg 隨意歸零」必敗——flow-review:33「降隨意性」日常詞會誤殺 | M/0.9 | ✅採納 | 驗證句限縮 tier 標籤四處形態、排除清單明列 |
| mF2 | SM-1b 跨 provider 暴露面無修改要點落點 | M/0.65 | ✅採納 | S1 要點 4（handoff Phase 3 判定項） |
| mF3 | schema 錨點 :42-50 差一格 | L/0.85 | ✅採納 | :42-49 |
| mF4 | 「schema 第二消費側」定性微偏（實引原則） | L/0.7 | ✅採納 | 改「原則第二消費側」 |
| mF5 | S3 升級「2 日」閾值無判定主體 | L/0.55 | ✅採納（修法二：implementer 開工前查卡判定＋記錄） | 整合策略改寫 |

## 收尾步驟

（S5 全涵：F 掃描證據＋卡結案兩步＋memory 蒸餾；無 Capabilities/SYSTEM-MAP/audit-test）
