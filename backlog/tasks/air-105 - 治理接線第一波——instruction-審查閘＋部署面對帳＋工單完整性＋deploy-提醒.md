---
id: AIR-105
title: 治理接線第一波——instruction 審查閘＋部署面對帳＋工單完整性＋deploy 提醒
status: To Do
assignee: []
created_date: '2026-09-16 02:16'
updated_date: '2026-09-16 02:16'
labels: []
dependencies: []
ordinal: 90000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
今天四個小事故（條文無外審落地、freshness 沒對自己執行、部署面漂移、工單錨定）的收口：把既有零件接起來而不是新造治理。codex＋muse 兩家顧問收斂方案，user 拍板第一波＝A＋C＋D 縮版＋B 窄版。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 instruction-writing rule/skill 含語義分類路由到 review-engine profile＋fail-closed＋無 self-exemption 特權
- [ ] #2 post-build 含部署面對帳條件閘（觸及才跑、surface 自帶探針、失敗擋收線）
- [ ] #3 work-order §8 含 contract-completeness invariant＋review variant 同步
- [ ] #4 deploy_agents.py 僅實際寫入時印 ACTION 提醒＋變更 rule 名單
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 06bd79d〕
〔風險分類：boundary（控制面 authority/gate/acceptance 語義——改變何時閘、誰可落地）；審查腿：fresh＋intent 分離＋跨家族外審（muse，Tandem 腿）＋judge 主 session；分類依據：review-engine 風險 profile 判定表（控制面 authority/gate 屬 boundary）〕
〔已決策勿重辯：①不新造風險分類——路由到既有 review-engine profile②judge 腿永不降級③D 採 codex 縮版（contract-completeness invariant，不加風險大欄）④B 僅實際寫入時印⑤兩家顧問原始 verdict 在 .agent-tmp/air-101/（codex job-mu3gjvtj／muse job-mu3gjvye）〕
範圍：P1 instruction-writing（rule pointer 一句＋skill 細則：分類路由/fail-closed/無 self-exemption/回執欄）；P2 post-build 部署面對帳條件閘；P3 work-order §8 invariant＋variant 同步；P4 deploy_agents.py 條件提醒。
<!-- SECTION:PLAN:END -->
