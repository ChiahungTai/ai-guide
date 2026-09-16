---
name: read-tool-source-before-upgrade-proposals
description: 提案「升級/修改某 tool/skill」前必讀其原始碼——能力假設錯會污染整條提案鏈（kanban-board 零渲染實證）
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
---

2026-09-02 kanban-board 案例：我提案「升級 kanban-board skill 掃四源 → HTML 線×階段 board」，user 直問「但是做得到嗎？你有理解他這原理嗎？這是個 repo，你有去查原始碼嗎」。查證結果——skill 目錄**當時只有一個 SKILL.md、零腳本**（純卡片操作指令：建卡/搬卡/格式；09-03 起有 `scripts/backlog_precheck.sh`——仍零渲染機制，本案例教訓不變），**從頭到尾沒有 HTML 渲染機制**；mosaic `.kanban/` 現存與 git 全歷史均無任何 html。user 說的「有一個 html 我可以理解有哪些要做」實為 **EP 任務導讀殼**（index.html，每任務目錄一個）——不是 kanban 產物。

**Why**：能力假設會沿提案鏈傳播——不但提案本身錯（「升級」實為「從零新增生成機制」），連已寫進 EP 的 R6 驗證項（「kanban-board 渲染一次 board 驗證」）都建立在同一錯誤假設上＝驗證項本身無從執行。名字暗示的能力（"board" → 想像它渲染 board）≠ 實際能力。

**How to apply**：提案修改/升級任何既有 tool/skill 前，①Read 其完整 SKILL.md（全文，非片段）＋②fd 該 skill 目錄看有無 scripts——能力＝程式實際做的事，非名稱語義；③若新功能實為「從零新增機制」，明說「新增」不說「升級」（工作量與風險表述完全不同）；④user 引用的功能體感（「那個 html」）先定位實際來源再設計。同族：[[feedback_arch-impossibility-needs-topology-grounding]]（架構宣稱前查拓撲）——本條是工具能力宣稱版。
