---
id: AIR-76
title: v3.1 測試契約六檔落檔——materialization
status: Done
assignee: []
created_date: '2026-09-11 05:50'
updated_date: '2026-09-15 21:17'
labels:
  - governance
  - testing
dependencies: []
references:
  - ai-analysis/_tasks/09-11-test-contract-v31/ep.md
  - ai-analysis/_tasks/09-11-test-contract-v31/mvp-report.md
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
兩天最大定案零承載收斂（tri-audit X1/X2 雙 🔴）：測試契約 v3.1（三方裁決 reports/2026-09-11-test-contract-design.md）落檔六 skill＋routing 鏈＋附帶同步面。〔baseline：ai-rules 4b0d2b7〕〔已決策勿重辯：①v3.1 終態——獨立性買 judgment boundary（challenge＋軸B review）非 every authorship；②RED provenance 三栓（receipt 落檔/sha256 digest 凍結/基線跑法）；③test-gen＝P0 最後手段不生成 registry 檔（AIR-70 答案反轉）；④cr-research 升 full 僅一角（Explore fallback 維 lite）；⑤amendment authority 四分——實作現況永遠非證據；⑥same-family precondition producer（EP author_family 欄）＋consumer（implement gate）雙端；⑦MVP 過線標準預凍結，不過線僅 S1 可跑 S2-S7 全停〕風險面：寫入契約首改（六 skill 行為控制面）＋跨文件交叉推導（TC 語彙六檔共享）。跨弧編輯面：AIR-67 同檔異面（roles tier vs 角色定義）、AIR-70 notes 收 test-gen 結論。〔驗收：①MVP 報告過線（challenge recall ≥3/4 誤報 ≤1＋routing 5/6＋attribution 5/6）或 fail-loud 回報；②九 routing 錨點全 full（rg＋roles 直驗＋Explore fallback 未誤升）；③六檔＋code-review-and-quality /consistency 全綠；④全域 rg 殘留掃清單（EP 整合策略）逐條 exit 0；⑤pytest test_sync_agents 綠＋sync_agents --map cr-research=full；⑥blueprint v3.1 節翻 ✅＋workflow ②⑤站補半句〕EP：ai-analysis/_tasks/09-11-test-contract-v31/ep.md（三方審查 22 findings 已吸收：muse 13/GLM 17/codex 5，judge 21 ✅＋1 gate 候選）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔09-16 開工 batch1（marshal 派 worker）〕drift 盤點 PASS：S1 routing 原子切確認已由 AIR-91 S2/AIR-96 落地（九錨點漂移對照表 .agent-tmp/air-76/drift-audit.md；--map cr-research=full＝full yes yes；test_sync_agents 99 passed）；唯一真缺已補＝test-gen P0 註記行 agents/AGENTS.md:60（非常設/P0 最後手段/不生成 registry 檔）。S2–S6 六檔 v3.1 語彙零命中＝仍缺、凍結正確，錨點新行號已錄。S7-4 持續 PASS。Explore fallback 現行記「繼承主 session 模型」非誤升勿回寫 lite。S0 kit 備妥＝.agent-tmp/air-76/s0-kit.md（Lane A 8 迷你 TC 4clean+4mutant；Lane B 六類 pytest 標本；過線標準預凍結 recall≥3/4 誤報≤1 routing 5/6 attribution 5/6）。S0 實驗由 marshal 編排中，過線後素材複製任務家 mvp/。

〔09-16 S0 MVP 過線——凍結解除〕四軸全 PASS：challenge recall 4/4（muse 盲推 A5/A6/A7/A8 全抓、推導值全對）、clean 誤報 0、routing 6/6（M-3 依『任一即計』由 audit 項2 計入，review 腿漏檢已註記）、escalate 轉介（audit Critical＋review 不吞）、attribution 7/7。 falsifiable 探針 4 枚（A5-SIGN/A6-UNIT/A7-MIDNIGHT/A8-CIRCULAR）。報告＝ai-analysis/_tasks/09-11-test-contract-v31/mvp-report.md（素材 transcript 全存 mvp/）。協議修正候選：軸B evidence fidelity 文本加機械觸發問句（S5 落檔時吸收）。S2–S7 解凍，worker 派出。

〔09-16 batch2 S2–S7 落檔 PASS〕execution-plan 測試規劃段＋amendment 附錄＋author_family（+35）；implement same-family gate＋三栓＋frozen TC carve out（+13）；audit-test 角度 8 七項＋四處同步＋stale 計數修正（+30）；code-review-and-quality 六項定義源（含 MVP 修正候選問句）＋code-review 雙側注入 wiring＋排除面兩處；fix-test mutation authority gate＋escalation 欄（+24）；workflow.md 三處翻 ✅＋skills/CLAUDE.md 五命令索引。marshal 抽驗：S4 舊計數零殘留、S6 映射零重複、S5 定義單一源、S3 三栓雙檔在場。八檔 +116/−20 留 working tree。卡面剩：post-build 鏈＋review 鏈＋結算。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
v3.1 測試契約全段落檔：S1 經 AIR-91/AIR-96 落地（--map cr-research=full 機械驗證）＋test-gen P0 註記補齊；S0 MVP 四軸全 PASS（recall 4/4、誤報 0、routing 6/6、attribution 7/7；muse challenge 4 探針＋lite audit/review 雙腿）；S2–S7 六檔＋audit-test 角度 8＋fix-test authority gate＋藍圖翻 ✅；muse 外審 F1–F5 裁決修復（status 單一寫入者 fence、profile primacy 句、hash-object 正典）。MVP 修正候選（evidence fidelity 機械觸發問句）已吸收進 S5。驗收①–⑥全綠。
<!-- SECTION:FINAL_SUMMARY:END -->
