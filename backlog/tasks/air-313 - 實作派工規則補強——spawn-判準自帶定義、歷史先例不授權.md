---
id: AIR-313
title: 實作派工規則補強——spawn 判準自帶定義、歷史先例不授權
status: To Do
assignee: []
created_date: '2026-10-12 05:48'
updated_date: '2026-10-12 05:48'
labels: []
dependencies: []
ordinal: 298000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
一個 session 在別的 repo 做卡時，查了 git 歷史發現以前類似的小卡都是「session 自己改」，就照做自己在 worktree 裡改了 code——繞過了「實作一律派 writer」的規則，自寫自審還把手改作廢重做。

**這卡做什麼**
- 把全域指南 Marshal 姿勢節的派工條款改成自帶判準（改到會影響行為的產物＝實作，一行也算；主 session 只做本職與零行為文書）
- 補一句「歷史先例只回答怎麼做、不回答誰來做」——先例不得當授權依據

**不做什麼**
- 不搬完整派工表進指南（bundle 有尺寸預算；細則留 agent-workflow skill）
- 不新建機械閘（既有 work-order 憑證閘推廣是另卡的事）
- 不處理漏收信問題（歸 AIR-312 信箱採用面）

```mermaid
flowchart LR
  A["session 查 git 歷史先例"] --> B{"先例說以前都自己做？"}
  B -->|是| C["新規則擋下：先例不授權"]
  C --> D["實作一律派 writer"]
  B -->|否| D
  D --> E["主 session 留在編排與審查"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. Marshal 姿勢節 spawn 條款自帶判準（behavior-bearing 或其驗證物、一行也算；豁免＝Marshal 本職與可證零行為 editorial；失派禁代寫；細則指 agent-workflow skill）
2. 先例句落地：小卡「直行」只簡化規劃流程不授權自做；git 歷史先例不作角色分工或授權依據
3. 單一源紀律：rg 掃 spawn／直行／先例 引用面零漂移；skills desc gate FAIL=0；card_validate PASS
4. 部署投影更新：merge 後 main 重跑 deploy，四端 bundle 含新條文（規範載入驗證非僅 source 存在）
5. 落地前審查閘回執四欄齊（classification=boundary／review 腿＋evidence／session-freshness／deployment-surfaces）
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 33731634d522cccc818ec3bf4d013dcd1a85c623〕
〔已決策勿重辯：①設計討論 muse job-mv4tpdid-8bj8un＋codex job-mv4tpdlo-o8fjl4 雙腿審議、Marshal 裁定收斂（.agent-tmp/air313-adjudication.md）②判準復用 agents/AGENTS.md 注 b 既有詞彙（behavior-bearing／一行也算）不造第二定義源 ③豁免＝原則式「Marshal 本職與可證零行為 editorial」，不用列舉 ④P2 只落 Marshal 姿勢節單一源 ⑤「直行」術語須消歧（UC 規模段流程直行≠姿態授權）⑥指針給 skill 名（agent-workflow——部署面可達）不寫外 repo 路徑 ⑦不新建機械閘（hook 三判準缺二；marshal_admission_guard 推廣另卡）⑧效力範圍限縮——不寫成跨層級全序〕
範圍：ai-development-guide.md Marshal 姿勢節兩句條文（定稿見 .agent-tmp/air313-adjudication.md）＋bundle 再生驗證；落地前審查閘 boundary（fresh＋intent＋跨家族腿＋四欄回執）。Follow-up 不入本卡：implement Apply Changes vs 注 b 矛盾、collaboration-constraints:32 消歧、guard marker 推廣、漏收信 admission。
<!-- SECTION:PLAN:END -->
