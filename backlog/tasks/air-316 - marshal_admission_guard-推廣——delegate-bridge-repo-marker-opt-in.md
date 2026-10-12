---
id: AIR-316
title: marshal_admission_guard 推廣——delegate-bridge repo marker opt-in
status: In Progress
assignee: []
created_date: '2026-10-12 06:29'
updated_date: '2026-10-12 06:30'
labels: []
dependencies: []
references:
  - AIR-316
ordinal: 301000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
AIR-312 事故 repo（delegate-bridge）未啟用 marshal_admission_guard 的 marker（SC-199.1：非 canonical WT 寫 sourceRoots 需在場 work-order 憑證，缺席 deny）——閘已存在但沒蓋到出事的 repo。

**這卡做什麼**
- 查證 delegate-bridge marker 現況與 guard 版本相容性
- 啟用 marker（該 repo 落 opt-in 檔）＋攔截行為驗證（無憑證寫 sourceRoots 被 deny）

**不做什麼**
- 不改 guard 語義（self-issuance bypass 與 subagent 寫入面為已知決策殘餘，不動）

```mermaid
flowchart LR
  V["查證 marker 現況＋guard 版本"] --> M["落 opt-in marker 檔"]
  M --> P["攔截驗證：無憑證寫 sourceRoots"]
  P -->|"deny＋修法提示"| OK["防線蓋到事故 repo"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 1. delegate-bridge marker 現況有查證證據（在場/缺席＋guard 版本）
2. marker 落地且攔截行為實測（無憑證寫 sourceRoots＝deny＋修法提示）
3. 豁免面不回歸（backlog metadata/.agent-tmp/docs 照舊可寫）
4. card_validate PASS
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide b0b9c2f4＋delegate-bridge 現行 main〕〔已決策勿重辯：①guard 語義不動（SC-199.1 既有）；②self-issuance bypass＋subagent 面為已知殘餘〕範圍：查證 delegate-bridge marker 現況＋guard 版本→落 opt-in marker（跨 repo 主權面：僅隔離 marker 檔，user 已授權「follow-up 都做」）→攔截行為驗證（deny 路徑實測）→hook 註冊面核對（zcode user-level registration 對該 repo 生效）。
<!-- SECTION:PLAN:END -->
