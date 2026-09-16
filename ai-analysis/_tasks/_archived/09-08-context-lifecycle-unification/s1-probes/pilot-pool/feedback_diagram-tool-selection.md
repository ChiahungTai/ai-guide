---
name: diagram-tool-selection
description: 畫圖工具選型判準（user 裁定＋MOS-41 形式化）——判準＝邊有無結構化通道＋成本軸（kchart ~8s 機械｜mermaid
  1 輪｜archify ~9 輪/圖）；archify=非必要不用（user 明示）、>4 輪不收斂=spec 過重；機械綠≠可讀 vision 不可砍；mermaid HTML 殼內顯示要無縫融合一體
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_f748b62f-1779-46e9-9d95-4f8a68737f58
---

user 09-05 裁定（AIR-29 殼六圖 dogfood 實證）：**「如果圖的物件線條要交錯太複雜，mermaid 不好用」**——工具按圖型分流，不強用 archify 也不強用 mermaid。

**Why**：mermaid 自動布局（dagre）對自由 node-link 交錯會亂跳亂穿（user 點名 flowchart 與 class 圖難用）；剛性結構（時間軸/狀態機）它一次成功。層次與對照的本質不是圖論——HTML div 反而最乾淨。

**How to apply**（選型表）：
- ✅ mermaid：sequenceDiagram（調用序——最強項）、stateDiagram-v2（≤6 態規律機）、erDiagram、gantt
- ❌ mermaid→**HTML 塊圖**：多分支決策/分層架構（div/flex 一層一塊）、前後對照（左右欄＋色彩語義）
- ❌ mermaid→**archify**：架構全景空間探索（pan/zoom/search 本質優勢）、class/繼承網
- 渲染管線：`npx -y @mermaid-js/mermaid-cli -i x.mmd -o x.svg -b transparent`；**mmdc SVG 全帶 `id="my-svg"`＋同名 style——同頁多張 inline 互污染**：至多一張 inline，其餘存檔＋iframe（id 空間隔離）或 id 重寫；`.gitignore` 擴 `diagram-*.svg`（渲染產物不進 git）
- **.mmd 源要進 git**（AIR-29 實證缺口：只留 gitignored .svg、源沒落檔 → clone 後圖死鏈不可重渲染；與 archify JSON IR 進 git 對位）
- 殼內嵌原則：圖要在頁面上——file:// 開 md 的 mermaid code block 不渲染，別把未渲染 md 連結放殼

**判準形式化（mosaic MOS-41 殼四圖四形態實證，09-05 轉交）**：好不好用由**邊有沒有結構化通道**決定——時間軸（sequence）/管線（LR）/狀態轉移/層次泳道（archify layer/lanes）＝天然通道，邊沿通道零交錯；無通道自由圖（組件/class）auto-layout 排不出乾淨拓撲——user「難用」體感的根因。量化邊界：sequence/LR-flowchart 1 輪過；stateDiagram 5 狀態/8 邊/label ≤20 字＝餘裕上限；TB 自由 flowchart ≤8 節點仍殘小 crossing；classDiagram/ER→**改表格**（型別｜職責｜依賴）。換形態招（比換工具有效）：組件圖→sequence（真實問題常是「執行時誰呼叫誰」）、自由 flowchart→分層、class→表格。

**archify 使用紀律**：最後手段非預設——≤3 張純敘事、無互動導航需求 → mermaid；archify 獨有價值＝lanes 柵格防交錯＋validate 佈局 gate＋互動（節點護照/回源）。**>4 輪不收斂＝caller spec 結構過重，非 agent 不努力**——回頭瘦身 spec（減 lanes/去堆疊/砍 sublabel/次要事實沉 cards）重跑，別讓 agent 空轉（mosaic B 組判例：6 欄＋長 CJK＋同 lane 堆疊＝數學不可解，瘦身後首輪全綠）；archify-gen 無權刪 caller 事實，長文案由 caller 收進 cards。validate 診斷附的建議值（labelAt/座標）直接抄，別盲猜座標。

**機械綠 ≠ 可讀**：label↔label 互撞是 layout validation 盲區——9/9 checks＋visual-check exit 0 全綠，vision 補審四張全 FAIL；**vision 補審是 label 級唯一防線，降本不可砍它**（要從「少進重產線」下手）。同 mermaid：parse OK ≠ 渲染 OK ≠ 佈局可讀，三層各有失敗面。

**殼內嵌補充（nav 切換式殼）**：`section{display:none}` 下 flowchart getBBox 量測全 0 → 圖面紅 bomb「Syntax error」**假語法錯誤**（乾淨 parse 實際 OK；sequence 線性佈局免疫）。解法＝lazy render 逐節補渲染：`startOnLoad:false`＋nav click 後 `mermaid.run({querySelector:'section#id.show pre.mermaid:not(:has(svg))'})`——`:has(svg)` 排除已渲染者是關鍵（單次 `_mmRendered` flag 只渲染第一個含圖節）。parse 除錯須從 html 原始檔正則抽乾淨源碼（失敗後 DOM textContent 已被 error SVG 汙染，恆報誤導訊息）。

**MOS-27 補判準（user 09-05 拍板）**：決策流程**分支匯流是臨界**——分支少 mermaid flowchart 勉強（一 diamond＋三平行分支）、再多去 archify；erDiagram 實體 ≤6 且關係邊為鍵語義可 mermaid，交錯則 archify；**class 兩層判準**（調和 MOS-41「→表格」vs MOS-27「→archify」）：先問是不是圖論問題——型別/職責對照→表格，真繼承網且要圖→archify。**第三選項**：交錯度超標時除「換工具/硬畫」外可**降級為文字記載**——刪邊取捨顯式記在圖備註/卡（事實不丟、圖不爛），禁靜默刪邊也禁硬塞邊讓 auto-layout 崩。**靜態/動態分工**：archify 管靜態結構（依賴/分層/管線 DAG）、mermaid 管動態（時序/狀態/gate 流）——EP/殼**規劃期**就分派圖型，不是產完補救。

**containment ≠ 圖壞（MOS-27 NEW-2）**：多節點縱向組成本來超一屏，visual-check overflowY fail≠圖壞；readability（投影字 ≥6px）才是底線、**不為 containment 硬壓字級**；殼內 iframe 可捲，containment 只在獨立全屏頁致命；緊緻重構兩輪無改善即停，exit 0＋containment fail 如實並列、不宣稱視覺全過。**locale 定案**：renderer 只有 en/zh-CN——繁中內容**省略 meta.locale**＋顯式揭露「Viewer UI 退 English」，勿填 zh-CN 假裝繁中（用詞差異滲 UI 文案）。**輪數主因在 caller 端再證**：同產線 spec 品質好＝5 輪單調收斂（errors 11→1→1→1→1→0、9/9 checks、0 crossings）、spec 差＝16 輪/40.8min；R1 爆 11 errors 根因＝「拓撲寫完、幾何沒規劃」——修復期規則**前移 author 期**：每邊 author 時分級（跨 >2 node 欄寬禁 auto、必給 via/釘 fromSide/toSide）、稠密區 label 先佔位、viewBox 寬×字級連動、節點離邊框留距、meta 欄位先查 schema enum（schema_version 是 per-type const：architecture=1/workflow=2）。修復迴圈**每次修一類、同類全修**防擠牙膏（每輪恰 1 error＝沒順手預防同類）；修復順序固定 routing→label→rhythm/readability。

相關：[[feedback_shell-diagram-quality-bar]]（殼品質門檻軸）、[[agents-registry-split-design]]（六圖 dogfood 現場）、[[archify-illustrate-html-mode-eval]]（成本檢討線）
