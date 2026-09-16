---
name: feedback_engine-skill-trigger-collision
description: 第三方引擎掛到自家入口命令時，引擎自身的 agent skill 別進清單——description 觸發詞重疊 = 路由歧義（raw
  vs grounded 行為分岔）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_da1739eb-475e-45a3-80cf-531cd44124c7
---

整合外部引擎到自家入口命令（如 archify 之於 /illustrate html）時，若引擎自己的 agent skill 也裝進 skills 清單，兩個 description 的觸發詞會搶同一批請求（「畫架構圖」「visualize pipeline」）——AI 挑哪個非確定，且行為實質分岔：入口命令走 grounding（讀 code→事實→渲染），引擎 standalone 走 raw 渲染（憑口述/Mermaid 直畫）。

**Why**: skill 發現機制 = description 語意匹配；兩個語意重疊的清單項 = 同一請求兩個候選。對「理解既有系統」型命令，走錯邊（raw 而非 grounded）是實質風險非理論問題。

**How to apply**: 解法優先序——①引擎不入清單（CLI-only／clone 形態擔任純引擎，入口命令是唯一觸發面；archify 08-31 裁決刪 npx 版即此）②若引擎必須在清單，入口 skill 文檔寫分工聲明（誰服務什麼意圖）。raw 渲染殘餘需求（貼 JSON 直渲）罕見，口頭指揮 CLI 即可。同構實證鑑：muse-plugin-cc `FIX-S3-R2.md:49`（resume heuristic＋proactive routing 混進 thin forwarder→自相矛盾＋trigger collision 被移出；AIR-13 D2 裁決依據）。關聯 [[feedback_llm-native-no-skill]]（skills 治理）、[[project_archify-illustrate-html-mode-eval]]。
