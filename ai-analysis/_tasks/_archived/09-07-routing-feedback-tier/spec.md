# Spec — ai-rules 修訂：四家比較路由反饋（model-routing／handoff／開卡三處）

> 來源：mosaic 2026-09-06/07 四家模型比較（旗艦 tier／lite tier／muse／codex 同尺評測）的跨 repo handoff（user 貼入，2026-09-07）。AIR-38 的 spec 輸入——EP 規劃讀本檔，證據自包含（不需讀 mosaic repo）。

## 核心裁決（user 拍板，勿重辯）

路由詞彙一律用「旗艦／一般」tier 抽象（跨 provider 穩定）；具體模型名只在 tier→(model,effort) 解析層出現；family 軸（muse/codex）是第二軸非 tier 降級。

## 修訂清單（七項，依優先序）

### A. handoff skill 加「建議執行 tier」欄（最高價值）
- 現況：schema 八欄無路由資訊。但 handoff 是路由實際發生點（user 拿 prompt 開 session 的瞬間），路由決策目前只活在 user 腦中。
- 修法：schema 加一欄「建議執行 tier」——內容是**條件式**不是斷言：
  - 「一般（lite）」需三條件全滿：保護面厚（既有測試釘住）＋EP 條款機械可判＋審查鏈全開
  - 「旗艦 only」五項不可讓：judge／編排／post-build 終審／跨文件交叉推導（docstring↔斷言、EP↔code、caller↔callee 型）／寫入契約首次改動
  - family 軸另註：架構級 EP 可交跨家族 runtime（muse 類）但 eligibility 前提＝使用者會話在場裁決
- 同步強制欄：**workspace／卡歸屬**（跨 worktree 教訓：runtime 的 workspace＝TUI cwd，它不會自己管卡歸屬）。

### B. external-runtime family 表加「架構級 EP」角色行
- 現況：`rules/model-routing.md` 角色表「EP 規劃＝full 能力檔（不可條件降級）」——語義正確但漏了 family 軸出口。
- 修法：external-runtime routing 段加「架構級 EP（blueprint）」角色行，eligibility gate 增一條「使用者會話在場裁決」（實證：muse 在 user 對話裁決下產出架構翻轉級 blueprint——它提候選→user 質疑→它收斂的模式成立；無 user 在場的證據面為零）。

### C. 開卡（execution-plan 段落 0）——不動卡結構，加任務屬性標註
- 裁決理由：卡是長期追蹤物、模型可用性會變（額度/新模型），卡上寫死 model 會 stale；但任務屬性不會變。
- 修法：desc「已決策」段可含風險面屬性標註（「寫入契約首改」「跨文件交叉推導」「無保護面新能力」）——作為 handoff 路由的輸入。

### D. flash／lite tier 成本行加 off-peak 但書
- 「lite 省 43-57% token」為 off-peak 弧偏樣本（user 2026-09-07 校正）：排除 off-peak 活動、2026-02 前不一定省——省幅宣稱只在可比時窗內引用。

### E. acceptance-evidence／review-engine 新增 claim 類型：自報元資料不可信
- 既有「量測數字必獨立重測」（跨家族條目）旁加 lite tier 版：**自報分類／判讀元資料必機械比對**（實證：vision 判讀 111 案中自報 contradicts 漏報 44/111——模型給了不同 label 卻自報未推翻；正解＝llm_label vs 標準答案逐案機械比對，禁用 agent 自報欄位做統計）。

### F. 單一源掃描義務
- 改 model-routing 角色表／tier 定義時，`rg` 掃所有引用該定義的 skill／rule 逐檔同步（ai-rules 自家的 single-source drift 防護條款）。

### G. 旗艦 tier 資格判定（eligibility criteria）——大綱層，user 2026-09-07 定調
- **定位**：定義「有資格被解析為旗艦（full）」的**模型能力條款**——資格線穩定；同 tier 內模型強弱排行＝註記層（變化快，非契約，頂多加註不進條款）。與既有「tier 詞＝requirement token、provider 演進只改解析表」同構。
- **資格條款草案（五項，由 mosaic 09-06/07 比較證據反推）**——旗艦候選模型需全部滿足：
  1. **跨文件交叉推導力**：docstring↔斷言、EP↔code、caller↔callee 型不一致能抓（證據：MOS-41 P1-P5 五項 lite+跨家族都漏、唯旗艦終審抓到；flash 弱項=自我一致性、跨家族受限項=工單 context 邊界——兩者的交集正是此型）
  2. **judge 否決力**：對高信心措辭的 finding 有否決傾向而非順勢採納（反例證據：lite judge 首輪 10/10 全採納傾向；「judge 層品質是有沒有被迫去拿反證的流程問題」——資格線是模型能支撐這個流程）
  3. **規劃的契約查證力**：EP 階段會把既有測試契約（parity 測試/aria baseline）當設計約束、會推導決策前提失效（證據：MOS-62 的 wrapper parity 約束＋「砍信心欄前提已失效」推導）
  4. **長弧查證紀律**：查證密度不隨 session 長度衰減（反例：lite 後段 judge 淺驗、D5 自證迴路鐵證）
  5. **寫入邊界首改的邊界意識**：首次改動寫入契約/human truth 層時主動設唯一入口與 crash-only 防線（證據：MOS-65 的 replace_overlay_entry 唯一刪改入口——但該案是跨家族 runtime 在紅線寫死到 handoff 密度下做到；旗艦資格=紅線沒寫那麼死時也自有此意識）
- **放置位置**：`rules/model-routing.md` tier 定義段（或 model-routing skill 權威表的 tier 段）——資格條款進大綱；**強弱註記**放解析表側欄（如「當前坐位：GLM-5.3；候選觀察：…」——單行註記，換代只改此行）。
- **入選驗法（輕量，不建考試制度）**：候選模型用既有比較尺（四軸＋旗艦不可讓五項任務）跑一弧實測再升坐位——沿用本次比較的方法論，不做獨立 benchmark。

## 證據錨點（mosaic 側，自包含摘要——均為 2026-09-06/07 實測）

1. **muse 整弧（MOS-65，EP+實作）**：EP A-（依賴考古發現 writer 無刪除能力／Codex checkpoint 6 項推翻全吸收／未竟獨立審自知登記）；實作 A（EP→code 逐項吻合＋兩處超越；寫入契約零稀釋；主 session 重跑全綠驗證）。Codex（ASTRA）的 checkpoint 推翻經驗證成立（「human_overlay.json 是 dict 覆寫非 append-only」）——**跨家族 review 抓設計錯誤實證**。
2. **muse 架構 blueprint（MOS-67，in-flight）**：補償邏輯盤點教科書應用（near-tie/co-label/secondary＝mutex 樹補償件，原子退役「拆 A 不拆 B＝double-count」）＋量綱分析→flag-not-rank（user 質疑跨樹統一純量後收斂）＋自我消除技術盲區（existence_gap 禁復用 nearest_alt_gap——識別互斥語義不可移植）。弱點實證：跨 WT 意識（卡在 v2、實作全在 warrant 未登記）。
3. **旗艦 worker EP 同尺抽審（MOS-62/63/64）＝A 級，剖面＝契約查證與整合**（wrapper parity 測試契約當設計約束／決策前提失效推導／跨模組 ripple 盤點）——與 muse 的「設計推演」剖面正交。
4. **跨文件交叉推導實證（MOS-41）**：P1-P5 五項 flash+muse 都漏、唯旗艦終審抓到——共同型別＝docstring↔斷言、EP↔code、caller↔callee 交叉（「跨文件一致性查證必須由同時持有兩側文件的層做」）。
5. **lite tier 保護面厚度解釋變數（MOS-25/26/28/29 多弧）**：保護面厚＋EP 硬＝A；新能力無保護面＝跨邊界語義靜默錯＋測試合法化自己的 bug——「lite 的測試只能當規格陳述非驗收證據」。
6. **judge 層 sycophancy（多弧）**：lite judge 首輪全採納傾向；「judge 層品質不是模型能力問題，是有沒有被迫去拿反證的流程問題」。

## 驗收

- 七項逐項落地（或記錄不採納理由）
- F 的 rg 掃描證據（改動定義的引用面清單）
- 修訂處 tier 詞彙一致性：旗艦／一般（tier 層）vs 模型名（解析層）不混用

## 承接不重做

- tier 詞彙體系（full/lite/vision＝requirement token）不動——本次只在 handoff/開卡/external-runtime 三處擴充路由出口
- 不重推四家比較本身（結論已定案，如需詳情看本檔證據錨點即可）
