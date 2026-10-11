---
id: AIR-304
title: illustrate 標準圖優先——classDiagram 三層判準＋顯式降級
status: To Do
assignee: []
created_date: '2026-10-11 02:19'
updated_date: '2026-10-11 02:55'
labels: []
dependencies: []
ordinal: 40
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
user 請 illustrate 圖解 study area 類別結構，第一輪只出 console ASCII、沒想到 UML classDiagram，被指正後才補。根因有二：diagram-selection 現行條文對 classDiagram 全面負面（實證其實只適用多向交錯），且與 artifact-menu 已定義 Contract Class Slice 用 classDiagram 內部矛盾。

**做什麼**
- class 圖判準兩層→三層：型別對照→表格；樹形／森林繼承（單 parent、約 10 class 內）→mermaid classDiagram 是正答；多向交錯→表格＋刪邊記載（負面實證有效域收窄到此）
- 新原則條：user 請求的結構有 SA/SD 標準圖形時，標準圖語義優先進候選；因載體限制降級須顯式回報 user（禁默默吞掉標準圖）
- artifact type 判斷先於 output carrier（先辨識關係語義再選 console／md／svg／html）
- console 投影＝縮排樹（樹形繼承域）；md＝classDiagram 檔＋回報路徑（durable＝ai-analysis/reports/、ephemeral＝.agent-tmp/illustrate/；svg 預渲染為 opt-in 增益）

**不做什麼**
- 不改「console 禁 mermaid 語法」既有約束（console 給縮排樹非 mermaid 原始碼）
- chat 點連結直達渲染（svg 極限形態）以實測 POC 收，不預先宣稱

```mermaid
flowchart LR
  A["結構圖解請求"] --> B["辨識關係語義"]
  B --> C{"何種關係?"}
  C -->|"繼承樹形"| D["mermaid classDiagram"]
  C -->|"型別對照"| E["表格"]
  C -->|"多向交錯"| F["表格＋刪邊顯式降級"]
  D --> G["md 落檔＋回報路徑"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 diagram-selection 三層判準落地＋classDiagram 負面條收窄到交錯域
- [ ] #2 illustrate＋artifact-menu 連動更新（內部張力消除：兩檔對 classDiagram 立場一致）
- [ ] #3 事件重放 receipt：study-area 形態請求第一輪命中標準圖或主動建議 md classDiagram
- [ ] #4 C3 實測記錄：svg 點開直達＋md preview 路徑各驗一次（可點性未查證面轉實證）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 2d9a5203〕〔已決策勿重辯：①三層判準取代現行兩層（型別對照→表格／樹形繼承單 parent 約 10 class 內→classDiagram／多向交錯→表格＋刪邊）②「標準圖語義優先進候選、降級須顯式回報 user」原則條——現行條文讓 AI 默默吞掉標準圖是事件真根因③artifact type 判斷先於 output carrier（codex 意見採納）④內部張力一併消除：illustrate-artifact-menu class-slice 已用 classDiagram，與 diagram-selection 負面條對齊⑤console 投影＝縮排樹（保留 console 禁 mermaid 語法約束）；md＝classDiagram 檔回報路徑，durable＝ai-analysis/reports/、ephemeral＝.agent-tmp/illustrate/；svg 預渲染 opt-in⑥chat 點連結（C3）標未查證——AC 以實測收。素材源＝sess_de3fdb12＋user steering 原話＋.agent-tmp/improve-20261011/opinion-*.md Q3 節。範圍：skills/diagram-selection、skills/illustrate、skills/_common/illustrate-artifact-menu.md 三檔連動。落地前載 instruction-writing skill。〕

〔SC 收編 2026-10-11：①「點開直達」AC 直接吃 SC atlas S0（command 回傳 opened/failed，atlas/extension.ts:539-550）＋S1（md/html 走 chariotAtlas.openHtmlReport report viewer 含 mermaid 渲染、零 wire 改動）——SC 既有 L3 機械證據（report-resources.vscode-test.ts R3）已覆蓋相容性假設；②POC 裁決＝不需新寫 POC：實測＝一次 F5 手動確認（http anchor host 級行為）＋S1 交付正式測試；③「inline code 內 path/path:line 轉可點」應提前分期（ZCode DB 14 天 17,554 則統計：backtick 路徑引用 3,643 則 vs 裸路徑 420 則——多數引用現況不可點）；④SC 側設計全文＝southchariot .agent-tmp/sc-chat-openlink-seat-{glm,codex}.md＋sc-chat-openlink-brief.md（7d 窗）；跨 repo 依賴：S0-S3 歸 SC 側弧〕
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SC 回信已收（reply_type=completed、envelope 41fe234c-4d56-46eb-bd68-85aa7aa6e843；reply raw＝.agent-tmp/improve-20261011/sc-reply-raw.json，7d 窗）——五題全表態＋SC 側 chat 連結設計結論，本信閉環
<!-- SECTION:NOTES:END -->
