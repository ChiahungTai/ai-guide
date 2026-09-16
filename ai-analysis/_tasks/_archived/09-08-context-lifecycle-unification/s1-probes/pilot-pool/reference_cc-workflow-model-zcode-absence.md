---
name: cc-workflow-model-zcode-absence
description: CC dynamic workflow 心智模型（script 持計畫/resume/確定性）＋ZCode 無此概念；deepwork 化=CC 原生＋ZCode 模式等價（落檔 findings）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

**ZCode 無 workflow 概念**（09-05 鏡像查證：welcome.md 僅散文 "real coding workflows"、跨 harness 對照 contracts.md 零 workflow 條目）——「workflow 化」在 ZCode 端只能是模式等價物非原生工具。

**CC dynamic workflow 本質**（ref-docs/harness/claude-code/docs/en/workflows.md，432 行）：Claude 寫 JavaScript script、runtime 背景執行、協調數十至數百 subagent。核心軸＝**誰持有計畫／中間結果住哪**：subagent/skill＝LLM turn-by-turn＋結果進 context；workflow＝script（程式碼）持迴圈/分支＋**中間結果在 script 變數不進 context**（最值錢性質）＋編排可存檔/diff/重跑＋同 session resume（完成 agent 回快取、首分歧後全重跑）＋確定性（Date.now/Math.random 在 script 內 throw）。原語：`agent()`/`pipeline()`/`parallel()`/`phase()`；caps：16 並發/單 call 4096 items/單 run 1000 agents；size guideline：small<5/medium<15/large<50 agents（值得抄成 deepwork spawn 預算語義）；ultracode keyword 或 /effort ultracode 觸發；無 mid-run user input（對 deep-work 無人值守是 feature）。品質模式＝對抗交叉驗證（findings 互駁才浮出、驗不了標 unverified 非 refuted）。

**deepwork workflow 化雙軌策略**（09-05 討論定調＋user 裁定範圍＝**整個生命週期 開卡→commit**，不限 Agent Review Cycle／deep-work 內——「不在 deep-work 也照這作法」；dw 已整理流程但**規劃段（execution-plan）最會漏**、全鏈每段用適合 agent）：
- **CC 端接原生**——review-engine/implement 的 Workflow mode 已有線（ultracode 觸發、Verify phase、/workflows 監控、acceptEdits-always 警告），deepwork 做的是延伸進多階段 loop
- **ZCode 端模式等價物**——findings 落檔（.review/ finding record 形態）＋主 session 只讀 digest（context economy 逼近）＋背景 agent 群＝fan-out＋skill 即 script（LLM 解釋器非確定性 runtime——機械段用落檔補）＋被殺 agent 產物存活於檔案系統（resume 逼近）
- **反面實證**：三軸 flash 鑑識的三份大報告全進主 session context＝CC workflow 要避免的模式；分級 verify node（lite-verify 錨點批次 vs quorum）兩端共用同一 review 方法論

相關：[[reference_zcode-platform-facts]]、[[reference_cc-agent-view-bg-sessions]]（CC 背景 session substrate：`--agent --bg` 分發）、[[multi-harness-architecture-direction]]、[[project_plugin-review-absorption-p1-p7]]（P1 分級驗證落地形態）
