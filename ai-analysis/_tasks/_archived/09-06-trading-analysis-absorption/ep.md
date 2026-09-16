# EP — MOS-42 交易方法論吸收：trading-analysis 擴充回測/事件研究紀律

> **ep_type**: implementation（docs mode — product 全為 `.md`）
> **baseline**: `128186e`
> **來源**: mosaic MOS-42 現增事件弧 2026-09-05 交接稿（user 指定整理轉交 ai-rules 固化；handoff 已 user 核可）

## 實作總覽

把 MOS-42 事件弧的交易方法論四塊吸收進 `skills/trading-analysis/SKILL.md`：②回測模擬語意陷阱、③單位單一源、④point-in-time 紀律、⑥探索↔正式化界線。同弧①（數字↔視覺雙向驗證迴路）⑤（圖表渲染 for vision）已由 AIR-30 收進 diagram-selection 共性池——本弧**禁重複收錄**，僅 pointer 交叉引用。

**已決策（user 裁定，勿重辯）**：
- kchart 分析不是 report shell 載體；交易方法論走 trading-analysis 另弧、不混圖選型線
- 邊界：kbar-form-analysis＝「怎麼看圖判讀」（pipeline）；本弧＝「分析紀律」（模擬語意/單位/時間點/檢定）——重疊處 pointer 不重述
- 寫作約束（instruction-writing）：領域例子可用穩定概念（洗盤/回補），**精確統計數字不寫進 skill**——數量級描述＋材料錨（MOS-42 現增事件弧、2026-09-05）
- **EP review F4 裁決（judge，2026-09-06）**：源檔⑤首條「判讀用 raw、統計用 adjusted」經查證未被 AIR-30 吸收（rg `adjusted|複權|adj_close` 對 skills/＋rules/ 0 hits）——handoff「⑤已收」前提部分不成立，此條屬漏收非重複收錄；與③口徑單一源同族，併入③小節（一行形態）

## UC 盤點（docs mode — 受影響命令/rules 清單）

| 檔案 | 角色 | 動作 |
|------|------|------|
| `skills/trading-analysis/SKILL.md` | 主體擴充（新章節＋frontmatter description） | 修改 |
| `skills/CLAUDE.md`（工作流索引 :158） | trading-analysis 索引行 description | 同步 |
| `skills/diagram-selection/SKILL.md` | ①⑤ 已收（跨載體共性慣例池）——驗證在場後 pointer | 唯讀 |
| `skills/kbar-form-analysis/SKILL.md` | 邊界對照（判讀 pipeline vs 分析紀律） | 唯讀 |

Backlog：無既有卡（`backlog search trading/方法論` 0 hits、pending-decisions 0 hits）→ 新建 AIR-31（labels: docs,skills,trading）。SYSTEM-MAP：ai-rules 無此檔（元專案正當跳過）。

## Scenario Matrix（docs mode — 文檔語境）

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | 回測/事件研究方法論被查詢 | session 涉及回測紀律、事件窗量測、單位口徑、data snooping | 載入 trading-analysis 後四塊章節在場、可引用 | — | 四塊吸收 |
| SM-2 | 圖判讀/圖選型主題混入 | 涉及 K 線判讀或畫圖選型 | pointer 指 kbar-form-analysis / diagram-selection，內容不重述 | — | 邊界宣告 |
| SM-3 | 機械驗收 | EP 驗證階段 | 五組 rg 關鍵詞命中（見 S1 驗證策略）＋精確數字 0 hits | — | 寫作約束 |

## 段落劃分原則

兩段：S1 核心寫作（SKILL.md 主體）、S2 機械同步（索引＋跨檔一致性）。S2 依賴 S1 的章節名。

## S1 — trading-analysis SKILL.md 主體擴充

### Context

- 現結構：三層分析框架（Layer 1 經典 TA / Layer 2 量化 / Layer 3 第二層思考）＋輸出要求（共識/歧異對照表）。三層是「怎麼判斷走勢」；MOS-42 四塊是「回測/事件研究的量測紀律」——正交維度，新 top-level 章節容納，不塞進三層內。
- 語義約束：與 S2 共享章節標題（S2 索引行引用「回測/事件研究量測紀律」概念）。
- 基礎設施盤點：已完成——diagram-selection「跨載體共性慣例池」（:46 起，收①⑤）、kbar-form-analysis（三證據層 pipeline）。兩者為 pointer 目標，不重述。
- 依賴錨點：`skills/trading-analysis/SKILL.md:3`（frontmatter description）、`:44`（`## 輸出要求` 章節頭——新章節插於本章節之後，即檔尾 :57 之後）；`skills/CLAUDE.md:158`（S2）。

### 修改要點（docs mode 裁剪 pseudo code）

1. **frontmatter description 擴充**：三層框架之後追加「＋事件研究與回測量測紀律（可回補模擬、單位單一源、point-in-time、探索↔正式化界線）」；觸發詞補「回測紀律、事件研究、point-in-time、data snooping、單位口徑」。
2. **新章節「事件研究與回測量測紀律」**（插在「輸出要求」之後）——頭部一句視角定位（與三層的關係）＋四小節＋尾部材料源/pointer 段：
   - **回測模擬語意（trailing 紀律類）**：進出場紀律必須模擬「可回補」（trailing MA 出場後能再進場；single-shot 把大漲案 med 砍到近零——贏家普遍主升前先跌破短均線洗盤，洗盤→主升是常態路徑）；「站上 X 才買」單獨無防護（極短時間人人都觸發，含後來崩跌的——防護在出場端破線賣，非進場端）；事後確認進場吃不到溢價（邊際都在事前特徵；V 訊號/低點確認/強度確認三次獨立實證同結論）；量測面窗末持倉成本用 per-case `ceil(switches/2)`。
   - **單位單一源（管線防 bug 鐵律）**：管線內部/CSV 存檔一律 fraction、顯示時 ×100（三層分明）；bug 形態——CSV 存百分比值卻拿 fraction 門檻比較（篩選差兩個數量級）、display ×100 把負報酬顯示成荒謬值；跨 CSV join 是單位/撞鍵溫床（中繼產物每多一跳、單位口徑與複合鍵風險各乘一次；多腳本串接收斂單一源曾回收多案漏失樣本）；**複權口徑同律（F4 併入）**——統計用 adjusted（`adj_close` 欄）、判讀用 raw，讀錯欄會得「調整是 no-op」假象。
   - **point-in-time 紀律（特徵工程）**：基本面特徵用 `announcement_date <= 錨點日`（公告日錨非月份推斷——月營收次月 10 日前公布）；環比必須季節調整（MoM − 同日曆月全市場中位數，否則事件窗落在幾月決定量測）；事後特徵（窗內低點位置/dip 深度）禁止進事前分組——可作描述與出場規則素材、禁作進場訊號（base rate 反覆否決）；事件資料 guard——同 code 兩 event_year 掛同組日期用機械 guard 攔。
   - **探索↔正式化界線**：幾十次 in-sample 切分無多重檢定控制＝每格都可能 data snooping——報告顯式分離「探索性/確認性」結論；預註冊式驗證（規則文字凍結 gates/進出場→未參與探索的新樣本重驗，倖存/陣亡訊號如實分欄）；年度切分是最低成本偽 walk-forward——「相對報酬/防禦型」與「年年賺」宣稱分開講。
   - **尾部 pointer 段**：材料錨（MOS-42 現增事件弧 2026-09-05 心得稿）＋交叉引用（數字↔視覺雙向驗證、vision 契約、人類板設計→diagram-selection 跨載體共性慣例池；K 線判讀 pipeline→kbar-form-analysis）。

### 驗證策略（docs mode）

- 機械 rg 驗收（handoff 指定五組，**一律限定 `skills/trading-analysis/SKILL.md`**——F6：不限定會被 ep.md 自身/backlog 卡/其他 skills false positive 滿足）：`可回補|出場端|事後確認|ceil\(switches`（②）、`fraction|撞鍵|join`（③）、`point-in-time|announcement_date|季節調整|事前分組`（④）、`預註冊|探索性|data snooping`（⑥）、`diagram-selection|kbar-form-analysis`（交叉引用）——全命中。
- **數字禁令（F5 擴充）**：`rg '30\.5|\+2\.7|\+1\.0|7\.6|4\.87|28\.9|487|238|326|9/10|1\.5|3-25|2465|3162|112|22 支|16%|25%|3/5' skills/trading-analysis/SKILL.md` **0 hits**（材料源精確統計數字全攔；對整檔跑——現有 Fibonacci 值不誤傷）。
- 邊界驗證（F6 校準）：`rg '三段式|self-contained' skills/trading-analysis/SKILL.md` **0 hits**——①⑤ 規格不重述（pointer 段僅提 skill 名與能力詞，不含規格術語）。
- 純文檔修改——無執行義務（must-execute 例外：rules/skills 下 `.md`）。

## S2 — 索引同步與跨檔一致性

### Context

- 依賴 S1 章節定稿。`skills/CLAUDE.md:158` 現行：「`trading-analysis` — 股票 / 市場走勢三層分析（經典 TA → 量化 → 第二層思考）」——未反映新維度。

### 修改要點

1. `skills/CLAUDE.md:158` 同步：追加「＋事件研究與回測量測紀律（MOS-42 吸收）」（字串與 S1 章節名一致——F2）。
2. 跨檔一致性：SKILL.md frontmatter description 與 CLAUDE.md 索引行語義對齊（同一能力描述兩處口徑一致）。

### 驗證策略（docs mode）

- `rg -n '回測|事件研究' skills/CLAUDE.md` 命中索引行；兩處描述無矛盾。
- `/consistency`（post-build 收尾鏈承載）。

## 整合策略

- 兩段序列執行（S2 引用 S1 章節名）；無程式碼整合。
- 收尾（docs mode）：受影響命令行為已反映（trading-analysis 載入時新章節在場）＋`skills/CLAUDE.md` 索引同步＋卡結案兩步（AIR-31）＋EP 歸檔（任務家 done/）。

## 收尾步驟

1. S1+S2 完成後：五組 rg 驗收全綠＋數字禁令 0 hits＋邊界無重述。
2. `skills/CLAUDE.md` 索引同步（S2）。
3. post-build 收尾鏈（code-review → judge-review → 修正 → consistency → metadata-sync）→ 止步 commit 前（commit 需 user 確認）。
4. 卡 AIR-31 結案兩步（`-s Done --final-summary` → `--ref` 換 done/ URL）。

## EP review Findings（2026-09-06，獨立 Explore agent → 主 agent judge）

| id | title | severity | decision | status | 處置 |
|----|-------|----------|----------|--------|------|
| F1 | 錨點語義標註不準（:44 是章節頭非尾） | P2 | ✅ | implemented | 依賴錨點標註改「章節頭——插於本章節之後即檔尾」 |
| F2 | S1/S2 章節名字串不一致 | P2 | ✅ | implemented | 統一「事件研究與回測量測紀律」（description 追加語＋S2） |
| F3 | description 與小節名概念軸錯位 | P2 | ✅ | implemented | description 對齊「探索↔正式化界線」 |
| F4 | raw/adjusted 口徑條落縫隙（AIR-30 未收、本弧整塊排除⑤） | P1 | ✅ | implemented | 併入③一行（複權口徑同律）；已決策區記裁決理由；卡 desc 回寫 |
| F5 | 數字禁令漏列源檔多數精確數字 | P1 | ✅ | implemented | 禁令擴充至 18 pattern（對整檔 0 hits 判準） |
| F6 | 五組 rg 未限定目標檔可被 false positive 滿足 | P1 | ✅ | implemented | 五組＋禁令＋邊界驗證全補 `skills/trading-analysis/SKILL.md` 限定；邊界改 0 hits 判準 |

總結論：PASS with findings——三 P1 均 EP 文本層可修，設計（四塊劃分/插入點/pointer 策略/邊界宣稱）經驗證成立。

## Build review Findings（2026-09-06，獨立 Explore agent 六軸 → 主 agent judge）

| id | title | severity | decision | status | 處置 |
|----|-------|----------|----------|--------|------|
| B1 | pointer 段漏「數字↔視覺雙向驗證」「人類板設計」能力詞（EP :57 規格 vs 實作） | P2 | ✅ | implemented | pointer 補全兩能力詞（能力詞引用不觸發重述禁令） |
| B2 | 「三層分明」撞檔內主導詞「三層框架」 | P2 | ✅ | implemented | 改回源檔原話「三者分層」 |
| B3 | CLAUDE.md 索引行「（MOS-42 吸收）」為導航行首見 arc-ID、changelog 味 | P2 | ✅ | implemented | 移除括注——材料錨已在 SKILL.md body；導航索引全檔無 arc-ID 慣例（EP S2 字面偏差，judge 裁定 reviewer 理由成立） |
| B4 | working tree 混有 memory-audit 非本弧變更 | P2 | ✅ | adopted | 程序面：commit 採 file-scoped staging（既有 verify-wt 紀律），無檔案編輯 |

六軸：軸 4（跨檔一致）、軸 6（觸發路由）乾淨；無 P0/P1。**總結 PASS with findings**。修正後機械閘門全綠（五組 rg＋18-pattern 禁令＋邊界＋F1/F2/F3 逐項驗證）——loop 一輪收斂。
