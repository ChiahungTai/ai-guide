# S1 子 EP：memory 讀取路徑 pilot（三臂比較）

> **ep_type**: implementation（pilot/compare mode——單池三臂比較＋最小可行改造；產物為凍結口徑、三臂證據、勝出方案與 S2 範圍建議；完整候選臂含 generator 最小改造，屬 pilot 工具非 production 定型）
> **parent**: ai-analysis/_tasks/09-08-context-lifecycle-unification/ep.md（master blueprint，S1 段＋方向承接第二輪）
> baseline: 28734c5

## Context

Master S1 段＋兩輪承接：以單池三臂比較決定取用方案，不預設完整候選必勝。Pilot 池＝ai-rules 專案池（`~/.claude/projects/-Users-ctai-Github-ai-rules/memory/`，單池即可，不依賴 S6 spine）。

S0 輸入（直接用，不重做）：P5 A/B 材料（`s0-probes/p5_ab_material.md`，B 為情境句草案）與方法論限制（同源飽和、鑑別力留 S1）；P3 lane 模型（65,536 trusted／32,000＋project 跳過 untrusted）；P6 codex skills-budget 縮短觀察（S6 跨池重跑時用）。依賴 S0④（mosaic root 組成分析方法）⑤（desc 用語樣本）；吸收 `project_memory-desc-loop-posture-pending`（姿態句順帶裁）。

**前置待確認（開工前 user 裁定，否則 Phase 1 懸置 B5 相關拒寫條件）**：禁引號與 B5 指令引句衝突——選「保留禁引號、改 B5 表達」或「禁令僅限實證引句」。未裁定前：lint 以已裁定條款＋批准樣本正例為準，不批次套用相衝突拒寫條件。

## Phase 0：凍結（改造前，門檻先行）

1. 任務集：≥10 自然任務（不提示查 memory、不塞條目名/搜尋指令/答案）＋無關負例＋同義改寫＋切片外條目＋compact 後接續各 ≥2；答案與評分口徑留控制端（主 session 持有，執行 session 不可見）。
2. 行為門檻：觸發率／正確 body 讀取率／採用率下界＋誤觸發與載入成本上界；必中案例不得漏。P5 配對成績不抵此門。
3. 必要集合初判：依漏掉後果＋有無可靠後續觸發點列 pilot 必要常駐集合（含低頻不可漏約束，不等讀兩次）；rank 只排集合內順序。初判交 user 確認後凍結。
4. 批准樣本 fixtures：P5 B1–B10 為文法正例；情境句領頭不限固定前綴（`^當你要` 誤收即判 lint 錯）。
5. 快照：舊 MEMORY.md 進任務家 version 目錄（回滾面）。凍結清冊納入控制資料與輸入索引（任務/答案/門檻/必要集合/各臂索引/inventory/fixtures），每次 run 記錄清冊識別；凍結後修改須重凍，不得沿用舊凍結宣稱。

## Arm 定義（同任務、同來源快照、可比模型/工具條件、獨立 session）

- **Arm A 現況**：池不動，記 baseline 四指標＋軌跡。
- **Arm B 最小修法**：精簡常駐（Phase 0 集合）＋工作節點取用＋既有索引。節點：接手恢復／改模組／調工具派 agent／commit 部署——僅任務範圍或所需契約切換時重判知識需求；已讀仍有效沿用，來源變更或 compact 後無法確認在場時重取。確定性入口交程式驗，相關性判斷量漏觸發率。
- **Arm C 完整候選**：B＋三段式 MEMORY.md（觸發地圖／按必要性選定的常駐條目／不預載 `_inventory.md` 指針）＋generator 最小改造（routing 段生成＋inventory 分離；資產源 `skills/memory-audit/scripts/generate_index.py`，部署副本先對帳刷新）。三段式與寫入閘放寬皆為待比較設計，不預設必採；`hooks/block-memory-index-write.py` 調整僅評估不實裝（S1 驗收只用已裁定攔截）。Arm C 禁改正式共用資產源與任何正式池：三臂使用隔離的資產源拷貝、池副本與 hook 驗證路徑；測實際 hook 須另備等效隔離入口，收尾對帳證明正式源與其他池未受影響。

## 執行協議（盲測紀律）

執行載體：獨立 session（in-harness 新 session 或 bridge task，執行者選；互不知答案）。載入合約：凍結同一比較組的 harness／model／工具條件與啟動方式；每臂載入根＝本任務家 `s1-probes/`，索引條目連結以前綴 `pilot-pool/` 重定位；可讀＝該臂索引＋`pilot-pool/`＋`fixtures/`（`fixtures/scratch/` 可寫，其餘禁寫）；控制端答案隔離（executor 可見路徑白名單制）。正式開跑前驗證有效載入內容、body 路徑可達、無跨臂污染。記錄工具軌跡（是否發起查詢／讀哪個 body／何時採用）＋提醒次數（user 按劇本自然提醒，執行者記次不引導）。telemetry（`skills/memory-audit/scripts/memory_telemetry.py`）與回報只產候選，不直接改集合或 rank。

## 評估與裁決

主指標：必要知識漏用、錯誤/過時知識誤用、無關載入成本、提醒次數；軌跡用來歸因（沒發起查／不知去哪／讀了不用）。計分按案例分 A（常駐已載入：驗到達＋採用，不強迫重查；漏必中即該臂否決）／B（按需取用：計 trigger/read/use）兩類，分母、成本單位與否決門檻見 freeze-answers；問答題為 smoke，正式行為腿為 fixture＋真實 compact（未執行標未驗證）。最小修法達標時完整候選須有額外收益才擴大（收益含治理成本粗比較：建立驗證＋反覆載入＋查讀判斷＋維護，用既有 usage/軌跡/維護步驟，不新造 telemetry；無明顯收益即停最小修法）；三臂未達門檻→軌跡定位→向 user 提交調整節點、重判集合或縮減後續方案（no-go 判定權在 user；擴大集合須列新增知識＋必要性＋各端容量證據；S2+ 不自動放行）。產出：`s1-report.md`（三臂證據＋勝出方案＋S2 最小改造範圍建議）＋`s1-probes/`（凍結任務/答案/評分腳本與執行軌跡，可重放）。T18 任務、恢復材料與評分口徑須在正式三臂前補齊重凍；三臂共用同一集合，不得臨場各出不同題。

## 驗收對照

SM-1（三臂行為＋N≥10 檢索 findability 分列；S6 跨池版留 S6）、SM-2（pilot 必要集合在場，低頻不可漏到達）、SM-3（非必要常駐成長不增加 floor 成本）、SM-6（二次教訓產候選核實，rank 只改順序）、SM-9（lint/hook 擋已裁定機械可驗部分＋批准樣本正例；不代替行為驗收）。
