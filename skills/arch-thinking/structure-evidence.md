# 結構證據配方

由 [arch-thinking](SKILL.md) 觸發表載入，只取能回答目前問題的資料。工具選擇依 [symbol-query-routing](../../rules/symbol-query-routing.md) 與 [cr-query](../cr-query/SKILL.md)；這裡定義證據形態，不複製工具能力表。

## product-type：依材料分流

- 程式碼：依語言與當前工具的實際 coverage 查 symbol／graph／type；[scan-project](../scan-project/SKILL.md) 的 Python dep_graph、Rust workspace 等資料只用於各自支援範圍。
- 文件：rg 查命令／skill／rule 的引用和指令語義；所得為文件拓樸，不是 runtime 呼叫圖或載入證據。
- 混合 repo：每個 claim 分別使用對應材料。缺 Python 不表示是 docs；無對應工具則標查證缺口。

## City Map 資料生成

以模組為節點，記錄 `A uses B` 依賴方向、依賴負擔（dep weight）、已識別消費者、跨界關係與 evidence。lean/heavy 是候選分類，需查實際依賴／載入路徑才推論傳遞成本。

反向耦合候選：lean 廣用模組 → heavy 實作。heavy → lean 本身正常。graph community 只提示耦合，不能直接當 DDD context；依語義、authority、source 與模組設計宣稱確認邊界。

## Call Graph 資料生成

以指定 entry symbol／scenario 為界，先查直接 caller/callee；關鍵影響尚未釐清才沿相應邊向外走，記錄查詢深度與未展開處。每條 edge 標明靜態或 runtime 證據及來源；不得把靜態可能呼叫呈現成已發生順序。

## Type Structure 資料生成

取與當前 contract 問題有關的 Protocol／abstract／繼承或實作關係；只補解釋契約差異所需的 member，不傾倒 concrete member 清單。工具只能找 references 而非確證實作時，回 source 核對；metaclass／動態型別等缺口保留 partial。

## Data-Flow 資料生成

取 producer→transform→consumer，以及「欄位／量由誰發布」的 authority edge；型別與 contract 可確認時附上。call edge 不能單獨證明某個欄位沿該路徑流動，須查實際參數、回傳或中間存取。runtime 值、事件順序與 invariant 正確性需另外執行驗證。

## Domain grounding

對外部框架的能力、會計量、生命週期或執行語義作結論前，查當前安裝／fork 的 source、stub 與契約。stub 可確認介面，行為宣稱仍需 source 或 runtime 證據。官方文件可補概念，不替代 fork 差異；未確認標 open。查 API 用法由對應 query skill 主導，實作／review 使用同一證據標準。

## Core identification for review prioritization

產出審查排序的依據，不決定人類或機器審查形式：

- **core 候選**：廣用且影響傳遞大，或位於 domain critical path；少 caller 的會計／安全節點仍可能是 core。
- **leaf 候選**：末端消費者、已確認影響局部且非 critical path；零搜尋結果不能證明是 leaf。
- 每個候選交代消費範圍、耦合／hotspot、domain invariant、未知與信心依據。缺資料保留未定，不強塞二分。
- 參考 scan-project、CR 與 repo 的 dependency-graph／architecture 語義；機械耦合與人工宣稱衝突時核對 source，不直接選一方。
- 變更類型只是定位訊號：generated 須確認生成源與可重現性；rename／comment／logging 須確認是否被動態名稱、instruction 或自動化消費。確認不改行為契約後才建議降低查證深度，不能按類型直接放行。

人類逐行讀／spot-read／behavior-only 的政策由 [illustrate 的 Selective Review Matrix](../_common/illustrate-structure-viewport.md) 決定；finding 嚴重度交 review 消費端。
