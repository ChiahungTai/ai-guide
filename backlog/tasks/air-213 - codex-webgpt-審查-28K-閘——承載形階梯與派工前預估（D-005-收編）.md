---
id: AIR-213
title: codex webgpt 審查 28K 閘——承載形階梯與派工前預估（D-005 收編）
status: In Progress
assignee: []
created_date: '2026-09-28 22:50'
updated_date: '2026-09-28 22:50'
labels: []
dependencies: []
references:
  - skills/bridge-dispatch/SKILL.md
ordinal: 199000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
delegate-bridge db-69 弧實證（D-005 correction，scbus 信 2de711db）：codex webgpt review 撞 28K payload 閘時，正確反應是**換承載形**——不是換 model，更不是把 codex 全家判死。本卡把這條收編進 bridge-dispatch skill 的「webgpt 大內容」節。

**做什麼**：①補 review-face 28K 承載形階梯——(a) thin-slice 較窄 --base、(b) 改 task face＋工單派 repo 檔路徑（reviewer 自跑 git diff；db-69 實證 62K-token diff 完全可用）、(c) in-harness subagent ②加派工前 diff token 估量句（超限直接走 (b)，不試錯燒次數）③補 transport 池判讀半句（native plan 額度 ≠ web payload 閘；native 掛→web 續用非棄家族）。

**不做什麼**：不動 availability 機械面；不加 automation；model-routing 昨日新判準已指到本節（指針不變、零 drift）。

**規矩**：boundary 條文（dispatch policy）——三腿審查閘照走。

```mermaid
flowchart LR
    HIT["review 撞 28K 閘"] --> Q["派工前先估 diff token"]
    Q -->|"超限"| B["task face：WO 派 repo 檔路徑"]
    Q -->|"未超限"| A["thin-slice 較窄 base"]
    A -->|"仍拒"| B
    B -->|"仍不可行"| C["in-harness subagent"]
    N["native 撞 plan 額度"] --> W["web pool 續用，非棄家族"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 bridge-dispatch「webgpt 大內容」節含 review-face 28K 承載形階梯：(a) thin-slice 較窄 --base／(b) task-face WO 檔案承載（db-69 實證錨 job-mulsjljd-q71eco）／(c) in-harness——換承載形不是換 model
- [ ] #2 派工前 review diff token 估量句在場（超限直接 WO 形，不試錯）
- [ ] #3 transport 池判讀（native plan 額度 ≠ web payload 閘，判讀面＝ledger stamp＋錯誤文案）＋native 掛→web WO 續用非棄家族 半句在場
- [ ] #4 desc gate FAIL=0＋五維檢查通過
- [ ] #5 落地前審查閘回執四欄 landing 前補齊
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 9644e2a5〕
〔已決策勿重辯：①載體＝bridge-dispatch「webgpt 大內容」節（D-005 附信點名＋scbus 信 2de711db 值星評估裁定收編；user 拍板「修」）②S1 承載形階梯＋S4 派工前估量全收，S2 transport 判讀＋S3 降級最小以半句併入③boundary 條文（dispatch policy）——三腿閘照走（fresh＋intent＋跨家族 muse）④model-routing 9644e2a5 新判準指針指本節，本卡修完指針更準、禁動 model-routing⑤ACK 回信（in_reply_to=2de711db）待 user AUTH，不在本卡範圍⑥authoring 走 card WT；landing 前審查閘回執四欄〕
範圍：skills/bridge-dispatch/SKILL.md 一節（webgpt 大內容）；不新增檔案
<!-- SECTION:PLAN:END -->
