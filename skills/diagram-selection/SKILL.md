---
name: diagram-selection
description: "畫圖前選載體的判準與跨載體共性慣例——mermaid／HTML 塊圖／表格／domain 渲染器。觸發詞：選圖、畫圖工具、圖表選型、載體選擇、report shell 補圖、換形態、vision 判讀契約、圖表渲染管線。判準四問（邊有無通道／交錯度／是否圖論問題／成本軸）＋vision 三段式契約＋渲染/判讀分離。"
when_to_use: "任何要畫圖的時刻——/illustrate 選輸出模式、EP/殼規劃期圖型分派、report shell 補圖、vision 批量判讀派發前。選型預設 mermaid／HTML 塊（舊互動圖渲染產線已退役，AIR-74）。"
---

# Diagram Selection — 畫圖載體選型與產線共性

> **職責邊界**：本 skill 管「**用什麼載體畫**」（選型判準＋跨載體共性慣例）。「畫什麼 artifact」（boundary/sequence/call-graph 等 SA/SD 語義）歸 illustrate [artifact menu](../_common/illustrate-artifact-menu.md)；「怎麼嵌進殼」歸 [illustrate-html-mode](../_common/illustrate-html-mode.md)；各載體實作配方在各自 skill/role（見文末指針）。

## 選型優先序（先語義後載體）

1. **artifact type 判斷先於 output carrier**——先辨識關係語義（繼承／時序／資料流／層次…）定 SA/SD artifact，再選輸出載體（console／md／svg／html）；順序反了，載體習慣會吞掉語義。
2. **標準圖語義優先進候選**——user 請求的結構有 SA/SD 標準圖形（classDiagram／sequenceDiagram／erDiagram…）時，標準圖直接進候選；因載體限制降級須**顯式回報 user**，禁默默吞掉標準圖換自創投影。
   真實案例：user 請求 illustrate 圖解 study area 類別結構，AI 第一輪只出 console ASCII、未提 UML classDiagram，被指正才補——條文對 classDiagram 全面負面＋降級不回報，標準圖就被默默吞掉。

## 判準四問（順序回答）

1. **邊有沒有結構化通道？** 時間軸（sequence）、線性管線（flowchart LR）、狀態轉移（stateDiagram）、樹形繼承（classDiagram——單 parent 繼承鏈沿 parent 邊走）、層次/泳道柵格（HTML 塊 grid/layer）是天然通道——邊沿通道走零交錯。有通道 → mermaid 一次可成（層次柵格通道由 HTML 塊承載）。
2. **交錯度多高？** 自由 node-link（邊要自己找路、交錯不可避免）是 auto-layout 死穴——user 判決錨：「如果圖的物件線條要交錯太複雜，不好用」。決策流程的**分支匯流是臨界**（分支少 mermaid 勉強、再多換載體）。
3. **是不是圖論問題？** 層次對照、前後比較、分類學——內容本質沒有 edge routing 需求 → **HTML 塊（div/flex/grid）或表格**，不是圖的東西別硬畫圖。
4. **成本軸**：mermaid 宣告式 1 輪；HTML 塊零渲染管線；domain 資料圖機械渲染秒級。小圖的資訊密度撐不起額外渲染管線成本。

## 載體對照（實證版）

| 載體 | 適用 | 邊界/實證 |
|------|------|----------|
| mermaid `sequenceDiagram` | 呼叫鏈/互動序/雙路徑 | **最強形態**（`alt/loop/note` 承載分支；隱藏容器渲染免疫）；1 輪 |
| mermaid `stateDiagram-v2` | lifecycle/狀態機 | 5 狀態/8 邊/label ≤20 字是餘裕上限；self-loop 表 idempotent 自然；1 輪 |
| mermaid `erDiagram` | 實體關係 | 實體 ≤6、關係邊為鍵語義時清楚；1 輪 |
| mermaid `flowchart LR` | 管線/單向流程 | 單向無分支零交叉，資訊密度與布局成本最低；1 輪 |
| mermaid `flowchart TB` 自由 | 小型組件圖 | ≤8 節點勉強（永遠殘留小 crossing）；畫前先問能否換形態；~3 輪 |
| mermaid `classDiagram` | 樹形／森林繼承 | **正答形態**——單 parent、約 10 class 內，繼承鏈沿 parent 邊走零交錯；多向交錯（多 parent／realization 網）無通道可救＝負面實證域，降表格＋刪邊；1 輪 |
| **HTML 塊圖**（殼內 div/flex/grid） | 層次架構/多分支決策/前後對照 | 零渲染管線、殼原生一體；「不是圖論問題」的結構首選；色彩語義可承載（如 rose=痛點/green=改善） |
| **表格** | 分類學/型別對照/多向交錯 class 結構 | 型別｜職責｜依賴比交錯繼承圖好讀好維護 |
| **domain 渲染器**（如 mosaic kchart） | 真實資料綁定圖（K 棒/行情） | 機械渲染（秒級、確定性、與 token 脫鉤）＋LLM 只在判讀端——複用單位是「圖形契約」lib＋領域薄殼，不是成品圖 |
| **刪邊/降文字記載** | 交錯度超標的取捨 | 第三選項（不是只有換工具/硬畫二選一）——取捨顯式記錄在圖備註/卡，事實不丟 |

**class 圖三層判準**（依序問，上層命中即停）：

1. **型別對照**（誰是什麼、職責為何，無繼承軸）→ **表格**
2. **樹形／森林繼承**（單 parent、約 10 class 內）→ **mermaid classDiagram 是正答**——繼承鏈天然有通道，不降級
3. **多向交錯**（多 parent／realization 網交錯）→ **表格＋刪邊記載**——classDiagram 負面實證有效域收窄至此域（多向交錯無通道可救；樹形域不適用負面條）

## 換形態設計招（比換工具有效）

1. **組件圖 → sequence**：多數「組件關係」真實問題是「執行時誰呼叫誰」＝時序，畫成 sequence 立刻有通道
2. **自由 flowchart → 分層**：節點按依賴方向分 layer/subgraph（HTML 塊 grid）——分層架構圖的本質
3. **class 圖多向交錯 → 表格＋刪邊記載**：繼承/組合列欄位；樹形繼承域不降級（classDiagram 直出，見三層判準）
4. **低價值邊先砍**：backward/交叉邊移除、語義沉到 sublabel 或 cards，比硬繞 via 便宜

## 跨載體共性慣例池（多弧同構：圖表渲染線/kchart 線/事件分析線各自獨立收斂）

**vision 判讀契約（三段式）**——派 vision-review 判讀圖時 prompt 必含：①逐張結構化輸出（一行固定欄位）②**誠實段**（目視分不出來明說、無從判斷不腦補）③跨案觀察段。配套：**每 agent ≤10-15 張**（超過 token 爆炸）；**抽樣錨定全樣本**——只看輸家（或贏家）子集的 vision 結論是倖存者偏差，會被全樣本數字反駁；產出要能**回數字驗證**（機械綠/parse OK ≠ 渲染 OK ≠ 佈局可讀——vision 是後兩層唯一防線）。

**盲判＝Writer/Reviewer 分離**——既有結論/人標不進判讀包（防引導偏差；分歧＝浮出候選非缺陷）；渲染端可機制化（如 `--blind` 撤結論欄）。預期描述須 code＋文檔**雙源核對**（文檔 drift 會直接污染判讀 prompt）。

**self-contained 圖**——給 agent 的圖把關鍵數值/週期宣告燒進圖題（agent 不用回查表；OCR 不可靠所以 caller prompt 自帶 header 重複宣告）；事件錨點直接標在圖上。

**渲染/判讀分離**——畫圖走機械 code path（確定、秒級、可批次、與 token 脫鉤），LLM 只放消費端（判讀）；一次渲染多方消費（agent 判讀＋人審圖牆）攤薄判讀成本。工具演化靠 code commit＋review，非逐圖 LLM 迴圈。

**fail-visible 批次**——單案渲染 FAIL 不拖垮批次；manifest 逐案增量記（中斷續跑）；無圖有降級路徑（標「無輔助」可判讀）。

**契約 lib 化＋領域薄殼**——複用單位是「圖形契約」（標記原語＋匯出管線）不是成品圖；新研究線只寫同款薄殼，lib 不隨領域演化。暫存 code 有「.agent-tmp 先暫存→正式化上抽 repo」生命週期。

**人類板設計**——圖牆/殼為人類瀏覽設計：正反分頁、按家族分組、worst-first、每卡自帶 gate 數值、iframe lazy loading。人類目檢是最後一道（會抓到 AI 數字分析的盲區）。

**載體限制顯式登記**——渲染端已知限制（避讓缺失/座標裁切/合成事件釘不住）寫進 instruction 檔方法論限制段，不是每次重踩。

**git policy**——源＋殼＋svg 渲染全進 git（AIR-74；條目詳 [illustrate-html-mode](../_common/illustrate-html-mode.md) git 段，單一源）。

## 邊界與指針（配方不重述）

| 要做什麼 | 去哪 |
|---------|------|
| mermaid 渲染配方（style 規範/mmdc 管線/殼內嵌 lazy render） | [mermaid](../mermaid/SKILL.md) |
| 殼整合（嵌圖形態/hook 時間點/重生） | [illustrate-html-mode](../_common/illustrate-html-mode.md) |
| UI 驗收編排（三鏈/截圖量測/盲判 spawn/pytest 沉澱） | [ui-visual-verify](../ui-visual-verify/SKILL.md) |
| domain 判讀契約實例（K 線三證據層/七項清單） | [kbar-form-analysis](../kbar-form-analysis/SKILL.md) |
