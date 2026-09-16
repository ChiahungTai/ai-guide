---
name: absorb-patterns-not-tools
description: user 設計原則——CC 官方工具不直用（「直接用可能會出事」）、參考作法重實現；deep-research 亂 web search 體感差→吸收編排模式＋源枚舉制
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

User 09-05 裁定（cross-verify 泛用命令設計時）：CC 的 `/deep-research` 他用過體感不好——**會亂找 web search**；「可參考作法，但是不要直接用，基本上 CC 的東西直接用可能會出事」。

**Why**：CC 官方功能為其生態設計（web 源優先、自由探索），直搬到 ai-rules 體系＝源不受控＋行為不可預期；正確姿態是**吸收編排模式、用我們的約束重實現**。

**How to apply**：吸收外部（CC/Anthropic plugin）功能時——(1) 提煉模式（如多源交叉驗證＝fan-out→對帳→合成）而非搬工具；(2) 加我們的約束（源枚舉制：軸=本機證據源 db.sqlite/git/log/memory/CR graph，web 軸必須顯式點名才開、預設不存在）；(3) 用實證原型校準（flash 三軸鑑識＝手工同型、零 web search）。對照反例：P1-P7 吸收全走「重寫素材禁照抄」（殘留內部引用同理）。

相關：[[agents-registry-split-design]]（cross-verify 設計定案）、[[project_plugin-review-absorption-p1-p7]]
