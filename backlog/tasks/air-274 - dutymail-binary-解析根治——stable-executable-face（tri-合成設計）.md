---
id: AIR-274
title: dutymail binary 解析根治——stable executable face（tri 合成設計）
status: In Progress
assignee: []
created_date: '2026-10-07 11:26'
updated_date: '2026-10-07 11:26'
labels:
  - dutymail
dependencies: []
references:
  - scripts/duty_receive.py
ordinal: 265000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
dutymail binary 裝在 plugin cache 的版本目錄裡（升級即砍舊版），三個消費工具各自 runtime glob「猜最新版」——與 harness 的 live 版本管理語義錯位（muse retention_refused 抖動即實證：盤上最新≠harness 願意 surface 的版）。tri（muse/codex/GLM-5.3）合成根修＝delegate-bridge 提供 cache 外的穩定執行檔 face，消費端停止猜測。

**根因一句話**：消費端用「盤上 max 版本 glob」猜一個「harness 以 live 版本語義管理」的路徑。
**根修一句話**：bridge 在 install/update 階段把驗證過的 dutymail provision 到 cache 外的 stable face（atomic flip），消費端只跟隨不猜測。

**里程碑**：M1（本卡可做，ai-guide 側）＝消音缺口服務——BinaryMissing typed error＋hook 連續 miss advisory（exit 恆 0 但不再靜默）＋CLI/face 一致處理；M2（bridge 側，另信請求）＝provisioner＋stable face＋文件修正（三份禁 shim 文檔、DB-80.6 通知義務）；M3（ai-guide 側，綁 M2）＝cutover——移除 cache glob。
**不做**：bridge_sweeper 不動（它解析的是 delegate-bridge 不是 dutymail——tri 糾正）；scbus home 不動（INTENT-02）。

```mermaid
flowchart LR
  i[\"plugin cache 版本目錄 會被砍\"] --> x[\"消費端 glob 猜版本 錯位\"]
  x --> m1[\"M1 消音缺口 BinaryMissing+advisory\"]
  m1 --> m2[\"M2 bridge provisioner stable face\"]
  m2 --> m3[\"M3 cutover 移除 glob\"]
  m3 --> ok[\"升級自動跟隨 無猜測\"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AC1 BinaryMissing typed error（resolver 全 miss 時拋出，有別於 store-absent 合法軟 path）
- [ ] #2 AC2 hook 面 consecutive-miss 計數（state/sidecar）達門檻升級 surface 可見 advisory；exit 恆 0
- [ ] #3 AC3 CLI 面接 BinaryMissing → typed exit（不再 traceback）
- [ ] #4 AC4 測試：typed error/advisory/CLI 三面＋既有 103 案零回歸
- [ ] #5 AC5 bi+judge（若分歧）+post-build 全鏈
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 037a659c〕
〔已決策勿重辯：①tri 合成（muse job-muy09tfy/codex job-muy09ti3/GLM-5.3 job-muy09u4u）——根修方向＝bridge stable executable face；無 postinstall 機制（三 harness 皆無 lifecycle）故 provisioner＝bridge 自有 idempotent 指令/release SOP 步驟 ②本卡只做 M1（消音缺口服務）；M2 歸 bridge（另信請求）；M3 綁 M2 後另弧 ③bridge_sweeper out-of-scope（解析目標不同）④fail-soft 修正窄幅：不翻 exit code（hook 非零擋 prompt），消滅靜默——BinaryMissing typed error＋consecutive-miss advisory〕
〔範圍：動 scripts/duty_receive.py＋hooks/duty_receive.py＋tests/test_duty_receive.py；不動其他〕
<!-- SECTION:PLAN:END -->
