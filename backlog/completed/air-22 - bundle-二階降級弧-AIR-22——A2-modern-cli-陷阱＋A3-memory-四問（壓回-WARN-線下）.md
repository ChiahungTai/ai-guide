---
id: AIR-22
title: bundle 二階降級弧 AIR-22——A2 modern-cli 陷阱＋A3 memory 四問（壓回 WARN 線下）
status: Done
assignee: []
created_date: '2026-09-03 22:56'
updated_date: '2026-09-03 23:02'
labels:
  - governance
  - bundle-diet
dependencies: []
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-20 聯合弧的 A2/A3 尾巴，user 09-04 裁定做、兩項綁一弧。目標：bundle 81,039B→~77.5K（84.2% gate），首次壓回 WARN 線（78,336B/85%）下——單做任一項都還在 WARN 區。〔已決策勿重辯〕A2＝modern-cli-preference 陷阱目錄（~2.0K：fd pattern/隱藏檔旗標跨工具/rg alternation \|/grep 旗標遷移/-g 錨定/git pathspec 三陷阱/head 截斷/雙掃）搬新薄 skill（~40 行；description 觸發詞：rg 陷阱、fd、pathspec、截斷、計數），rule 留「文字 rg／檔案 fd」分工句＋一行 pointer。A3＝context-management「Memory 生命周期」段（寫入四問＋單一寫入點＋cluster-first，~1.5K）搬既有 memory-audit skill（rg 驗證 skill 現無此段＝搬移非去重），rule 留「寫 memory 前必跑四問——見 memory-audit skill」。證據：兩檔 inbound 全場最低（各 1 檔）；always-on 不防踩實證（rg \| 陷阱在 rule 裡照踩，GLM 審查抓到）；A3 機械層已重疊（hook desc gate/generator gate/夜間 cron 紀律）。風險緩解：A2 觸發詞覆蓋要準；A3 pointer 必須「寫前必查」語義（四問第①問是 hook 擋不了的語義閘門）。驗收：deploy exit 0 且 bundle<78,336；陷阱目錄 rg 僅存 skill；四問 rg 僅存 skill＋rule pointer 在場；deployed 端點抽查 0 殘留；consistency。〔baseline：ai-rules ae3bc28〕census/advisory 詳情＝AIR-20 卡 notes＋ai-analysis/_tasks/_archived/09-04-rules-bundle-diet/ep.md
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
A2/A3 降級完結——modern-cli 陷阱目錄（rule 4,058→916B）搬新薄 skill、memory 四問（rule 3,997→1,606B）搬 memory-audit skill「寫入端紀律」段（含 frontmatter 觸發詞補強）；bundle 81,039→75,657B（88%→82% gate）首次壓回 WARN 線下、deploy 3/3 三端 identical、端點殘留掃描零（唯一命中＝既有合法 pointer）；muse review 3 findings 全閉環
<!-- SECTION:FINAL_SUMMARY:END -->
