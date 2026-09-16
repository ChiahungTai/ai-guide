---
id: AIR-81
title: blueprint 導覽網頁刷新——補優先序治理段與載體結構章投影
status: In Progress
assignee: []
created_date: '2026-09-12 13:28'
updated_date: '2026-09-16 11:09'
labels: []
dependencies: []
references:
  - ai-analysis/blueprint/index.html
ordinal: 67000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
blueprint 的人類導覽網頁（index.html）是治理檔的投影，目前需同步三類內容：09-12 拍板的多卡優先序治理（Priority backbone 段，48f2f88 已改 AGENTS.md 但投影未刷）、同日新增的載體結構章（structure.md，五層載體×四邊型），以及 section 02「一件工作的八站生命週期」的逐站導引——八站目前只有敘事／載體／現況，缺「此站該從哪個 command/skill 進入、去哪讀方法論」的人類導航。

〔baseline：ai-rules a21ced6〕
〔已決策勿重辯：①投影形態＝手寫＋殼 codegen（AIR-74 裁決：報告殼全走手寫＋codegen，index.html 進版控）②載體 graph 常設位＝blueprint/structure.md 第四檔（09-12 user 拍板；dependency-graph.md 慣例語義為功能 repo 不適用 ai-rules）③**workflow.md「逐站怎麼做」導引層為本卡唯一授權的 source 側改動**（09-13 已先行落地——八站→入口命令/詳讀連結的人類 lifecycle mapping 單一源；不重述 command 內部步驟；其餘 blueprint source 不因刷新投影改寫——取代原「本卡只刷新投影，不改四檔內容」條款）④index.html 是 human viewport projection，不成為 command/rule 第二權威；Priority backbone 與 structure 章既有裁決維持〕
〔驗收：①index.html 含 Priority backbone 段投影 ②含 structure 章投影（至少：五層載體表＋四邊型清單＋斷鏈表；structure.md 已加 bundle role 欄——96dd283）③頁頭生成註釋更新為四檔投影 ④自包含單檔、file: 直開成立（viewport 慣例：資產內嵌、無外部 fetch）⑤index.html section 02 八站皆能直接點到相應 command/skill/method authority（投影自 workflow.md 導引層——渲染形態＝保留 Mermaid＋總覽表，加八張 compact guide cards；⑤站 code-review 不作主入口、屬⑥收斂站）⑥③④站明確顯示 target vs 現行做法，不產生 wt-open 已落地假象 ⑦HTML 不複製 SKILL.md 內部步驟〕

開工提示：894 行手寫檔刷新屬 AIR-73 build_shell.py codegen 可承接域——若 AIR-73 已落地優先走 codegen；未落地則手寫刷新。**index projection 現況 stale 範圍＝backbone 段＋structure 章＋八站導引卡，由本卡一次收斂（source 側 workflow.md 已先行，drift 有 owner）**。斷鏈表中「投影無 gate」弱點的機械防線不在本卡範圍（另行評估）。
<!-- SECTION:DESCRIPTION:END -->
