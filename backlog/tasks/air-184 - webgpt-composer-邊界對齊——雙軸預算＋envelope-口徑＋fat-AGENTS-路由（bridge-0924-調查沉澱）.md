---
id: AIR-184
title: webgpt-composer-邊界對齊——雙軸預算＋envelope-口徑＋fat-AGENTS-路由（bridge-0924-調查沉澱）
status: Done
assignee: []
created_date: '2026-09-24 06:48'
updated_date: '2026-09-24 07:06'
labels: []
dependencies: []
ordinal: 170000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
delegate-bridge 0924 調查弧（sess_d6e3e495，southchariot codex web 三連敗）收斂出新邊界：死亡線 [~100K, ~126K] composer chars；核心教訓「工單小≠payload 小」（composer＝CLI 序列化整包＝工單＋AGENTS.md 鏈＋全域 ~30K＋buffer ~20K；實例 3KB 工單在 fat-AGENTS repo 仍落 126K）。本卡把 ai-guide 側派工指引寫齊四要素：預算值、envelope 口徑、估算式、替代路由。muse＋codex 討論雙腿收斂（receipts＝.agent-tmp/air-135/webgpt-{muse,codex}.md）：雙軸命名分離——材料軸（≤8KB inline，09-16 既有）vs 整包軸（composer <100K），禁共用「上限/安全線」一詞。

```mermaid
flowchart LR
  J["派工評估<br/>codex web"] --> A{"材料軸<br/>inline ≤8KB？"}
  A -->|超| C["chunk／改檔案路徑形態"]
  A -->|過| B{"整包軸<br/>工單＋AGENTS 鏈＋~30K＋~20K<br/>< 100K？"}
  B -->|超| F["fat-AGENTS 替代：<br/>降 payload→native codex→muse/glm"]
  B -->|過| D["派工"]
```

**不做什麼**：不動 delegate-bridge 側（其 AGENTS.md webgpt 段來源弧已更新）；不把實測值升格永久規格（CLI drift 觀察項承載）；不開架構工程（純文檔釐清）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔已決策勿重辯（muse＋codex 雙腿收斂 0924）〕①載體分配：預算值一行進 rules/bridge-dispatch.md（always-on gate 數字）；envelope 口徑＋估算式＋雙軸表述＋fat-AGENTS 判準與替代順序＋觀察項住 skills/bridge-dispatch/SKILL.md webgpt 節（單一源）；model-routing codex row 只加一行指針（不持 payload 數字）②雙軸命名：材料軸（≤8KB inline）／整包軸（composer <100K＝工單＋repo AGENTS 鏈＋全域 ~30K＋buffer ~20K）——每軸各寫量什麼＋超了怎麼辦 ③fat-AGENTS：判準以估算式為準（repo AGENTS ≳50K 進估算參考錨）；順序＝降 payload（檔案路徑/chunk）→native codex→muse/glm→in-harness ④觀察項三筆（CLI 注入量 drift as-of 標記／buffer 漂移／回應段死×整包交互）進 skill webgpt 節末 bullet，不進 rule；可選 dispatch 前 wc -c AGENTS.md 記 residue

〔範圍〕動＝rules/bridge-dispatch.md（一行）、skills/bridge-dispatch/SKILL.md（webgpt 節）、skills/model-routing/SKILL.md（codex row 一行指針）；不動＝delegate-bridge repo、daemon 源碼歸因

〔落地前審查閘分類〕ordinary（dispatch 程序指引非 authorization 語義）；驗收＝四要素齊＋rg 舊數字掃描＋單一源無雙寫

〔規模分級〕simple~standard——三檔文檔編輯
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0924 marshal 收線】worker receipt 全 DONE-WHEN 過（三檔恰如工單；model-routing 指針零數字＝偏差①裁定正確；skill 舊『只派路徑』句與 09-16 內聯規則矛盾＝偏差②一併收編為材料軸未驗形態）。部署閘事件：rule 一行使 muse bundle 30,772B 超 30,720 gate（fail-loud 攔住）→hotfix 657f3d08 預算行合併壓縮→30,699B 回落 gate 內 3/3 部署。residue：muse bundle 餘裕僅 21B——下次 rules 變更前先瘦身（歸後續維護批）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
as-built 終態圖：

```mermaid
flowchart LR
  B["bridge 0924 調查<br/>死亡線 ~100K–126K"] --> D{"雙軸預算<br/>派 codex web 前"}
  D --> A["材料軸：inline ≤8KB<br/>超→chunk／改形態"]
  D --> W["整包軸：工單＋AGENTS 鏈<br/>＋~30K＋~20K < 100K<br/>超→fat-AGENTS 替代"]
  W --> R["①降 payload→②native codex<br/>→③muse/glm→④in-harness"]
  A --> L["rules 一行預算值＋<br/>skill 單一源＋觀察項三筆"]
  W --> L
```

Final Summary：三檔落地（rule 預算行＋skill webgpt 節雙軸與替代路由與觀察項＋model-routing 指針）；muse/codex 雙腿事前收斂＋marshal 親驗；部署閘 hotfix 一輪（30,699B）。residue：muse bundle 餘裕 21B 記後續瘦身。
<!-- SECTION:FINAL_SUMMARY:END -->
