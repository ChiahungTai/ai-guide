---
name: feedback-shell-diagram-quality-bar
description: task brief 殼門檻：流程圖必備、首屏見圖、美感有底線；SA 選型已落地 diagram-selection skill；殼內 mmdc/CDN 渲染＋-I 唯一 id
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_7622de15-8cf2-4fc5-a0b2-49b7f5f19f0b
---

2026-09-03 AIR-14 兩次退回：①基礎款純文字殼（79 行表格）→「為何沒有流程圖？好好重寫，你這很難懂，認真點」；②muse 的摺疊 sidebar＋U.3 模板 demo→「你弄的好醜」→整個還原。

2026-09-05 圖表選型兩段勘正（AIR-29 殼）：①初版「小圖用 mermaid 勿強用 archify」→AI 三張全用 flowchart 被 user 點破「flowchart 我覺得很難用 mermaid，class 圖也難用——**如果圖的物件線條要交錯太複雜，不好用**；循序圖等比較有規律的 mermaid 好用」；②殼連結 .md 的 mermaid code block 在 file:// 不渲染（「沒法直接內嵌 mermaid 嗎？且這種點進去沒用 md preview，這之前不是說不能這樣用？」）。

**Why**：mermaid 自動布局（dagre）撐不住自由 node-link 交錯——規律結構（剛性時間軸/網格）零布局問題，自由交錯（多分支/class 網）節點亂跳線交叉；殼是靜態 HTML，未渲染的 md 連結＝死內容。

**How to apply**：畫圖前按圖型選工具——**循序圖✅**（最強項）／**stateDiagram-v2✅**（AIR-29 dogfood 驗證：6 態生命週期零交錯）／gantt・ER✅／**flowchart LR 線性✅**（AIR-30 裁定包：有通道即 1 輪）／單主幹流程≤2分支⚠️／**多分支決策・交錯資料流❌→HTML 塊圖**（分層橫條/表格/左右欄——層次與對照本質非圖論）／**class・繼承網❌→兩層判準**（型別對照→表格；繼承網→archify）／**架構全景空間探索❌→archify**（pan/zoom 本質優勢）。殼的圖一律渲染產物或 HTML 塊：mermaid 用 **mmdc（`npx -y @mermaid-js/mermaid-cli`，本機免裝）渲染 SVG** 或 CDN lazy render（無 mmdc 環境 fallback；配方見 mermaid skill 殼內嵌段）。**mmdc id 碰撞解方＝每張帶唯一 `-I <svgId>`**（AIR-30 POC 實證：id/marker/style selector 全隨之改寫，可多張 inline）；無 `-I` 產物才限 inline ≤1/頁、其餘存 `diagram-*.svg` 檔＋iframe。`.mmd` 源隨殼進 git（AIR-30 補，與 JSON IR 對位）；gitignore `diagram-*.svg` 維持渲染產物不進。user 要求「先 dogfood 不要光說不練」——選型表須以實際畫出的圖交付，非口頭整理（AIR-29 殼五圖：seq×2＋state×1 inline/iframe、HTML×2、archify×1）。選型判準已落地 `skills/diagram-selection/SKILL.md`（AIR-30——判準四問＋成本軸＋跨載體共性）。相關：[[agents-registry-split-design]]、[[project_archify-illustrate-html-mode-eval]]、[[archify-illustrate-html-mode-eval]]。
