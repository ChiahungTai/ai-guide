---
id: AIR-167
title: >-
  AIR-135 amendment——四條 invariant 增補（owner／freshness／advisory
  startup／supervision fence）
status: To Do
assignee: []
created_date: '2026-09-22 14:28'
labels:
  - instruction-layer
dependencies: []
ordinal: 153000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
**這卡解什麼**：AIR-163 tri 收斂產出的 AIR-135 amendment 四條 invariant 落地——只寫判準句與指針，不複製 AIR-164 實作細節；實作歸各 repo 主權線。
1.「每個 durable mechanism 必須在誕生弧取得 instruction owner；coverage 看 owner 不看文件數」——已基本 canonical（AIR-164），只加 pointer
2.「derived evidence 消費前驗 producer freshness；lifecycle refresh 只是 optimization」——補 dirty-WT source identity 判準句（fresh ⇔ indexed_source_identity == requested_consumer_source_identity；算法實作歸 code-reality repo）
3.「startup hook 只可 advisory；correctness gate 必須在 consumer boundary」——候選新增
4.「supervision 弱訊號只 wake；hard death／redispatch 需 authoritative evidence＋fence」——agent-workflow supervision contract 已 canonical，列為 Marshal 必守 invariant
正典落點：ai-development-guide.md（AIR-135 區段）增補＋相關 skill 指針同步（single-source drift 義務）。

**不做什麼**：不重定義 supervision table／不重抄 coverage predicate 全文（指針到 instruction-writing）／source identity 算法實作（歸 code-reality repo）／各 repo 落地（歸各主權線，見落點表 .agent-tmp/survey-backup-20260922/per-repo-landing-tri-consolidated.md）。

```mermaid
flowchart LR
  A["四條 invariant"] --> B["ai-development-guide.md<br/>AIR-135 區段增補"]
  B --> C["skill 指針同步<br/>（single-source drift 義務）"]
  C --> D["各 repo 主權線<br/>按落點表落地"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 四條 invariant 在 ai-development-guide.md AIR-135 區段在場（rg 可查）
- [ ] #2 dirty-WT source identity 判準句在場（含 fresh 定義式）；無實作細節重複
- [ ] #3 相關 skill 引用面同步（instruction-writing/review-engine/agent-workflow 指針無 drift）
<!-- AC:END -->
