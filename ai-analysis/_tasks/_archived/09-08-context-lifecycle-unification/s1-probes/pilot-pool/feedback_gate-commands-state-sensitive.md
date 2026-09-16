---
name: gate-commands-state-sensitive
description: handoff/排程清單內嵌腳本閘，編進新 prompt 前先驗腳本對當前狀態行為——狀態敏感閘會死鎖（precheck×In Progress 實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_e28d19a8-78ba-41fa-a503-b57fa798f3a5
---

handoff comment／cron prompt 等繼承清單內嵌「跑某腳本、exit 1=停」的閘指令時，把它編進新排程／流程前，必先對照腳本源碼對**當前狀態**的行為——腳本閘是狀態敏感的，在設計用途外套用可能固定失敗。

真實案例（2026-09-04 AIR-17）：handoff 清單要求「結案前跑 backlog_precheck.sh（exit 1=停）」，但該腳本對 In Progress 卡固定輸出不可清＋exit 1（它是歸檔/清板專用閘；kanban-board skill 明文「結案兩步本身不需 precheck」）——照字面編進驗證 one-shot，autonomous session 會永遠停在結案前。修正＝改跑等價跨線檢查 `git log --all --not HEAD --grep <卡id>`（非空=停手不結案），並把修正記回卡 notes 供追溯。

**Why**：繼承指令的作者與執行 session 不同——作者複製 skill 模式沒對準用途；機械閘一旦固定失敗，autonomous session「合法停手」不結案，任務懸空且無人察覺。
**How to apply**：收到含機械閘的繼承清單→先讀腳本對當前狀態的分支行為再編碼；發現死鎖＝以 skill 明文的正確適用範圍＋等價命令替代，修正記回卡。與 [[feedback_conditional-gates-test-condition-not-exit-code]]（驗條件非 exit code）、[[feedback_read-tool-source-before-upgrade-proposals]]（動 tool 前讀源碼）同家族。
