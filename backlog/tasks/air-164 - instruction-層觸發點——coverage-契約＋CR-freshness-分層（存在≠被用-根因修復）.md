---
id: AIR-164
title: instruction 層觸發點——coverage 契約＋CR freshness 分層（存在≠被用 根因修復）
status: To Do
assignee: []
created_date: '2026-09-22 11:55'
labels:
  - instruction-layer
dependencies: []
ordinal: 150000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**這卡解什麼**：「存在≠被用」三案（code-reality 工具鏈在場沒人用／SC-199 規則有機制無／AIR-155 要人提醒才外部化）的根因修復——135 流程的 instruction 同步義務缺「生成面」（新機制誕生→instruction 真空），CR freshness 缺「消費前正確性 chokepoint」。雙腿＋bridge 既有機制合流後的落地設計：兩面補齊。

**不做什麼**：Planning Contract 第七欄／per-script AGENTS 全補／root 結構節膨脹／hook 自動 build／bridge 碰 write-face／instruction-sync --all 常駐／第二 inbox ledger／graph.db mtime 判 freshness。

**改動一：AGENTS.md coverage（生成面補齊）**
- implement 5b 加生成分支：新目錄/新可執行 → create-or-sync AGENTS face（predicate：可執行入口被 workflow/control 面消費、bounded context 根 ≥3 源碼、public contract）
- post-build 階段 4 加 candidate detector（機械 Detect→Extract→Delegate）
- scripts/AGENTS.md 新建（responsibility cluster 導航）＋governance/AGENTS.md 新建＋skills/CLAUDE.md 升 AGENTS source
- Planning Contract Scope/Integration 加 instruction surfaces 子欄
- ai-development-guide.md dependency-graph 角色行更新（CR 取代手繪依賴圖）

**改動二：CR freshness 分層**
- instruction-init L0：缺 .code-reality/graph.db → 引導 harness 面 build；build 失敗 → 明文降級收據禁全綠
- review-engine L2 dispatch preflight：cheap check（存在性＋identity 對照）同步；stale → rebuild 異步或明文降級——吸收 AIR-161 改動點 4
- wt-close 條件式提醒（trunk 前進 → receipt 提醒 marshal；非正確性依賴）

```mermaid
flowchart LR
  B[\"新機制誕生\"] -->|\"5b 生成分支\"| AG[\"AGENTS face create-or-sync\"]
  AG --> PB[\"post-build candidate detector\"]
  PB -->|\"零 gap\"| OK[\"settlement pass\"]
  II[\"instruction-init\"] -->|\"L0 缺 graph.db\"| HB[\"引導 harness build\"]
  RD[\"review dispatch\"] -->|\"L2 preflight\"| FC{\"fresh?\"}
  FC -->|\"stale\"| RB[\"rebuild 異步或降級\"]
  FC -->|\"fresh\"| OK
  WC[\"wt-close\"] -->|\"trunk 前進\"| RM[\"receipt 提醒非正確性\"]
```

〔已決策勿重辯〕①predicate 機械化：MUST＝(a) 跨 session 消費者契約可執行入口 (b) bounded context 根 ≥3 源碼 (c) public contract／控制面 authority；MUST NOT＝純產物鏡像；CONDITIONAL＝混住②implement 5b 加生成分支＋post-build 加 detector，不加第七欄③scripts/ 單檔 AGENTS（responsibility cluster）非 per-script④CR freshness＝source identity 非 graph.db mtime⑤bridge 永不碰 write-face⑥L2 禁阻塞式 rebuild（cheap check 同步＋rebuild 異步或降級）⑦wt-close 不自動 build（印提醒＋receipt，marshal 決策）⑧雙腿收斂溯源：instruction-layer-codex-result.md（8871B）＋instruction-layer-muse-result.md（7071B）＋bridge 線 post-build 三路徑確認。開工時依 card Planning Contract 補 AC/Plan。
<!-- SECTION:DESCRIPTION:END -->
