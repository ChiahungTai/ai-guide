# Work Order — AIR-38 實作委派（muse bridge task）：四家比較路由反饋七項（S1-S4＋F 掃描）

## 1. 紅線（首段，違反＝失敗）

- 禁 `git add`／`git commit`／`git push`／改任何 backlog 卡狀態——止步於 working tree 編輯
- 禁把任何產物寫到 `/tmp` 或 repo 外（含 memory 池）；中間筆記不留檔
- 修改 `.md` 一律「讀目標節全文 → 精確區塊替換」；禁 `sed`／regex 批次改 .md
- 範圍外檔案禁順手修（見 §6）

## 2. 目標（一句話）

把 mosaic 四家模型比較的路由反饋七項落地：handoff 路由資訊欄、架構級 EP family 出口＋旗艦資格條款（含詞形統一「隨意→一般」）、開卡風險屬性標註、自報元資料 claim、D 但書查證記錄、F 單一源掃描（EP S1-S4，S5 結案主 session 自做）。

## 3. Baseline identity

- repo root：`/Users/ctai/Github/ai-rules`（主 working tree）
- base commit：`7ef65c6`（其後有 AIR-37 落地 commit——以 working tree 現況為準）
- 並行改動聲明（dirty mode，不屬本次範圍勿動）：`skills/model-routing/SKILL.md` 決策樹「收法分流」修正（pre-existing 一處未 commit）＋`backlog/` AIR-38 卡（M，desc 已含七項）＋兩個任務家目錄（untracked）。注意：你本次**也會動** `skills/model-routing/SKILL.md`（S2）——該檔決策樹 :153 附近的 pre-existing 修正**保留不動**，你只動 EP 指名段落（tier 段/gate/family 表/解析表）。

## 4. 必讀（按序）

1. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-07-routing-feedback-tier/ep.md`——**全文**（含 GLM 11＋muse 5 findings 修正與 Review Record——條文以修正後 EP 為準）
2. `/Users/ctai/Github/ai-rules/ai-analysis/_tasks/09-07-routing-feedback-tier/spec.md`——user 拍板與證據錨點（A 項三條件原文、G 五項條款草案全文）
3. `/Users/ctai/Github/ai-rules/skills/self-contained-prompt/SKILL.md`（S1 schema :42-49）
4. `/Users/ctai/Github/ai-rules/skills/handoff/SKILL.md`（S1 消費側＋「八欄」:54＋Phase 3 機密檢查）
5. `/Users/ctai/Github/ai-rules/skills/model-routing/SKILL.md`＋`/Users/ctai/Github/ai-rules/rules/model-routing.md`（S2 落點群）
6. `/Users/ctai/Github/ai-rules/rules/acceptance-evidence.md`（claim 群 :19-24）＋`/Users/ctai/Github/ai-rules/skills/acceptance-evidence/SKILL.md`（S4 詳案例段）
7. `/Users/ctai/Github/ai-rules/skills/execution-plan/SKILL.md`（S3：UC 盤點建卡指引處——注意 :90 已有 AIR-37 落地的「同主題 memory 條目盤點」子步，你的 S3 屬性標註加在建卡指引（`backlog task create` 說明）處，不相鄰不衝突）＋`/Users/ctai/Github/ai-rules/skills/kanban-board/SKILL.md`（desc gate 段）

## 5. 已決策（勿重辯）＋矛盾例外

- 核心裁決：路由詞彙一律「旗艦／一般」tier 抽象；模型名只在 tier→(model,effort) 解析層；family 軸是第二軸非 tier 降級
- tier 英文 token（full/lite/vision）不動——「隨意→一般」只改**中文標籤**四處（rule:11 詞彙句、skill :3 frontmatter、:12 tier 詞定義、:18 表列標籤）；`flow-review:33`「降隨意性」日常詞與 backlog 歸檔卡**不在此列不回改**
- G 分層：資格條款五項全文入 skill tier 段（大綱層）；坐位註記**只記變動欄位**（候選觀察＋升坐位法）——現值坐位不重複記載（＝tier 表 full 行 zai 欄）
- gate 收斂＝**增第六條**（不行內註記分支）；rule:34 枚舉詞「五條」→「六條」
- 兩套降級條件管轄邊界寫死：分工律三件＝spawn 執行層降級；handoff tier 欄三條件（spec A 原文）＝handoff 路由建議——在分工律段補對照句
- D：rg 產品面（rules/skills/agents）查 `43-57|省.*%` ——無標的則條文不動，交付報告記錄「未落地理由」＋掃描證據
- S3 依賴已解除（AIR-37 S2 已落地）——正常做
- 詞形：「建議執行 tier」「旗艦資格條款」「坐位」「屬性標註」「自報元資料」「結案蒸餾範圍」（最後一詞已在 repo，沿用）
- 矛盾例外：發現檔案實際與 EP 衝突 → 停下舉證（file:line＋逐字引用）

## 6. 範圍限定

- **動（僅此八檔、僅指名節段）**：
  - `skills/self-contained-prompt/SKILL.md`——schema 表加第 9 欄「建議執行 tier」（條件式，指向 skill 條款不重抄五項全文）＋第 10 欄「workspace／卡歸屬」（強制欄：repo/WT 路徑＋卡 id）
  - `skills/handoff/SKILL.md`——「八欄」→「十欄」（:54 唯一處）；Phase 1 套 schema 處提新欄一句；Phase 3 機密檢查補「workspace/卡歸屬＝內部拓撲資訊」跨 provider 判定項
  - `skills/model-routing/SKILL.md`——①角色→family→profile 映射（:86-96）加「架構級 EP（blueprint）」行（eligibility 前提＝使用者會話在場裁決）②eligibility gate（:110）增第六條③tier 段加「旗艦資格條款（五項）」小節（spec G 草案全文收斂版，每項一句＋證據指針一句，≤10 行）④解析表後坐位註記單行（只記候選觀察＋升坐位法）⑤詞形四處「隨意→一般」⑥分工律段補兩套條件管轄對照句⑦:3 frontmatter description 同步（旗艦資格條款/坐位入列舉）
  - `rules/model-routing.md`——:11 詞彙句「隨意」→「一般」；:34「五條」→「六條」；tier 詞彙句後加 G pointer 行
  - `skills/CLAUDE.md`——:132 model-routing 行同步（旗艦資格條款／坐位註記入列舉＋「一般」）
  - `skills/execution-plan/SKILL.md`——建卡指引處補「desc『已決策』段可含風險面屬性標註（寫入契約首改／跨文件交叉推導／無保護面新能力）——handoff『建議執行 tier』的輸入」
  - `skills/kanban-board/SKILL.md`——desc gate 段補一句（屬性標註是「已決策」段合法內容形態）
  - `rules/acceptance-evidence.md`＋`skills/acceptance-evidence/SKILL.md`——claim 群加第五條「自報元資料不可信」（rule 一行版）＋skill 詳案例（vision 111 案自報 contradicts 漏報 44——llm_label vs 標準答案逐案機械比對，禁用自報欄位做統計）＋Review 雙向應用對應觸發形態；`skills/review-engine/SKILL.md` rg 查「自報」——無命中則跳過（記錄）
- **不動**：`skills/model-routing/SKILL.md` 決策樹 :153 附近 pre-existing 修正、`backlog/`、任務家、memory 池（repo 外）、其他一切
- 交付報告附 `git diff --name-only` 舉證

## 7. 工具接線

cat/rg/ls（一律 rg）；修改＝讀全文→精確區塊替換；三禁令（code-reality 寫入面禁／repo 外輸出禁／缺口停下舉證禁繞路）

## 8. 驗收（命令＋預期，逐條實跑）

1. `rg -n "建議執行 tier" skills/self-contained-prompt/SKILL.md skills/handoff/SKILL.md` → 兩檔命中
2. `rg -n "旗艦資格條款" skills/model-routing/SKILL.md rules/model-routing.md skills/CLAUDE.md` → 三檔命中（條款＋pointer＋索引）
3. `rg -n "坐位" skills/model-routing/SKILL.md` → 命中且**不含模型名**（坐位行只記候選觀察/升坐位法）
4. `rg -n "六條" skills/model-routing/SKILL.md rules/model-routing.md` → 兩處命中（gate＋rule 枚舉）
5. `rg -n "架構級 EP" skills/model-routing/SKILL.md` → 命中（family 行）
6. tier 標籤殘留：`rg -n "隨意" rules/model-routing.md skills/model-routing/SKILL.md` → 零命中（:3/:12/:18/:11 四處已改「一般」）；`rg -n "隨意" skills/flow-review/SKILL.md` → 仍命中（日常詞，不動——證明排除清單被遵守）
7. `rg -n "自報元資料" rules/acceptance-evidence.md skills/acceptance-evidence/SKILL.md` → 兩檔命中
8. `rg -n "屬性標註" skills/execution-plan/SKILL.md skills/kanban-board/SKILL.md` → 兩檔命中
9. `rg -n "八欄" skills/` → 零命中（:54 已改十欄；歸檔卡在 backlog/ 不掃）
10. `rg -c "43-57|省.*%" rules/ skills/ agents/` → 零命中（D 無標的證據——排除本弧任務家）
11. `git diff --name-only` → 僅八檔（＋不動的 pre-existing model-routing 決策樹 hunks 共存同檔屬預期——報告區分）

## 9. 證據紀律＋PII 禁令

宣稱落地≠落地——每項附 rg/內容證據；驗收附完整命令與原始輸出；「沒改 X」附 git diff 舉證；禁 PII；失敗如實記錄。

## 10. 交付報告格式（最終回覆承載，不寫檔）

1. 改檔清單（含 pre-existing hunk 區分）
2. 七項 A-G 逐項落實說明（file:line 對照；D 附查證證據；G 附條款五項收斂版全文）
3. F 掃描資料：本弧改動的每個定義源（tier 詞彙/gate/schema 欄/claim 群/「八欄」）→ rg 引用面清單（命中檔列表＋需同步/不需動一行判定）——主 session 收案時消費
4. 驗收 1-11 命令與原始輸出
5. 偏差記錄＋未驗證項＋建議 reviewer 聚焦點
