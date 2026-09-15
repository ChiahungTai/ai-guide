---
id: AIR-73
title: build_shell.py——md→報告殼確定性 codegen（lossless 分流）
status: In Progress
assignee: []
created_date: '2026-09-10 03:35'
updated_date: '2026-09-15 22:06'
labels:
  - tooling
  - illustrate
dependencies: []
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
寫一個腳本把 markdown 報告自動轉成好看的網頁殼（report shell），AI 只寫 md 不再手填 HTML——mosaic 實驗已證明這是純機械轉換可行。目前：三方設計定案待開工。

三方合成終案（GLM×muse×codex——.agent-tmp/illupatch-synthesis.md）：lossless vs curated 分流（task-home 殼預設 lossless 全量投影；curated 另標）；shell-ready md 契約（md 標記 section-group/diagram-assign + frontmatter task identity contract〔task_baseline/card_id 必填——codex v2 blind spot 規格化〕+ diagram_heights keyed by 穩定 identity key-set 全等鎖死 + report-type 折疊預設映射）；三級 gate（hard 六項含 ordered semantic leaves 全等〔codex 410 正式化〕/三硬約束行為面/meta completeness/確定性重跑；mutation tests 六型防同源自洽）；祖父+碰觸遷移（builder refuse overwrite 無 marker 檔；legacy-curated 維持手填）；git 政策責任反轉＋過渡條款（regeneration contract 先進 onboarding 才切 ignore）。TDD 驗收：mosaic 四材料 golden 重現（gate 全過）＋mutation cases 全紅。落點 skills/_common/（與 report-shell.html 同居）。材料：mosaic 任務目錄四產物＋ep.md :519-531。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
09-15 user 設計輸入（殼內容需求，開工時併入 codegen 規格）：①殼核心價值＝system analysis/design 的圖——無圖或畫不出來的殼意義低②task 型態圖預設：UI→mockup、流程→流程圖、演算法→步驟圖解、架構→架構圖講解③品質判準＝人一眼看到重點（sidebar 跳章看大方向＋每章先結論後圖；不達準的圖不如表格）④成果殼加強前後對比與「特點怎樣解決」的機制講解⑤delta tour ask-once 維持（收尾最後問一句）。同回饋已併入 workflow redesign EP S4（該 EP ledger「User pre-implement 方向修訂」節）。

〔09-16 wave 決策——排 Wave-2 並兼任 AIR-72 試點卡〕S4 圖觸發政策（task 型態預設＋一眼看到重點判準）已落地＝本卡內容需求輸入到位。作為 AIR-72 wt-open/close 的試點白老鼠跑全流程，dogfood 結果回饋兩卡。
<!-- SECTION:NOTES:END -->
