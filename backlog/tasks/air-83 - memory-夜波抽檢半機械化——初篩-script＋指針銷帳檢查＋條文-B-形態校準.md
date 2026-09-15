---
id: AIR-83
title: memory 夜波抽檢半機械化——初篩 script＋指針銷帳檢查＋條文 B 形態校準
status: Done
assignee: []
created_date: '2026-09-12 21:58'
updated_date: '2026-09-15 14:34'
labels: []
dependencies: []
ordinal: 69000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
夜間 memory 六問抽檢目前全靠夜波 LLM 裁量，兩晚 project_ 違規率 87.5% 同模式。這卡做三件小事：寫一支初篩 script（新流入 Q1 評分排序＋指針條目銷帳檢查）、修 memory-audit 一句 A 形態遺留條文、host 側 cron prompt 接線——降低夜波裁量負擔與品質浮動。

〔baseline：ai-rules d8060dd；memory 池 git bee40fa〕
〔已決策勿重辯：①人裁不自動刪——script 只產候選/提醒，判定權仍在人②放置閘（d8060dd）為寫入端單案；desc 觸發語句硬閘（M3）掛 09-13/09-14 夜波收斂觀察，非本卡範圍③夜波 cron prompt 住 host automation 側——接線走 CronUpdate，repo 只放 script 與 skill 條文④subagent 寫入覆蓋缺口暫不管（觸發條件＝首個寫池 subagent 角色定義時 roles/ body 自含六問一行）〕
〔驗收：①script 對 09-12 夜波窗口重跑，nightly-convergence.log 該晚 7 條 project_ 退回候選至少 6 條被初篩命中（對照測試）②ep-test-contract 指針被銷帳檢查命中（AIR-76 在 board——rg backlog 判卡存在）③memory-audit「索引預算」行 150 行軟上限 scoped 為 A 形態、B 形態訊號指向既有 inventory chars 增量口徑（rg 驗證）④script unit tests（project_ 前綴＋終態詞彙 scoring、指針標記偵測〔desc/body 含「建卡後刪」「in-flight」〕、backlog 卡匹配）⑤CronUpdate 後首晚夜波輸出含 prescreen 段〕

範圍：skills/memory-audit/scripts/ 新 script（pool git -C 窗口枚舉新流入；候選表含評分與理由；_ 前綴檔排除）＋skills/memory-audit/SKILL.md 夜波段接線句與條文校準＋tests/＋host cron prompt 更新（自動化 #1 memory-audit）。錨點：ai-analysis/nightly-convergence.log 09-11/09-12 兩段（87.5% 實證）；hooks/block-memory-index-write.py docstring（放置閘③）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
寫入端單案已建卡：AIR-90（狀態後綴硬擋＋19 條存量處置＋twin 偵測＋結案清池項；codex 討論共識已凍結在卡 desc）——本卡與其互補：AIR-83 偵測側（夜波初篩）、AIR-90 攔截＋處置側。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
併入 AIR-100（P4 夜波半機械化：初篩 script＋指針銷帳＋條文校準＋cron 接線）——同域整併；原 AC 由 AIR-100 A4 承接，未動工即併、無遺留工作。
<!-- SECTION:FINAL_SUMMARY:END -->
