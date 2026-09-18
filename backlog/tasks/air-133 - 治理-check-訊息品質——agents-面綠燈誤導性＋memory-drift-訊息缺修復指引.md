---
id: AIR-133
title: 治理 --check 訊息品質——agents 面綠燈誤導性＋memory drift 訊息缺修復指引
status: To Do
assignee: []
created_date: '2026-09-18 02:34'
updated_date: '2026-09-18 02:34'
labels: []
dependencies: []
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
兩個 --check 訊息問題：agents 面只驗 repo 生成物 parity 就亮綠燈，機器活視圖（skills symlink）沒驗，誤導「已防護」；memory 面在「muse CLI 在但 plugins build 不支援」場景的 drift 訊息沒給修復指引。發現點＝AIR-126 新 clone 模擬（fake HOME 實查）。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 agents 面：無 symlink 的機器跑 --check 有顯性訊號（非靜默綠燈；fail-loud 形態照 guard/monitor 警示先例）
- [ ] #2 memory 面「plugins build 不支援」場景的 drift 訊息含修復指引
- [ ] #3 新行為各有測試（修前紅修後綠）＋全量零回歸
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：/Users/ctai/Github/ai-guide main@0f6035c8〕〔已決策勿重辯：①agents 面補機器活 symlink 存在性探針——檢查面非安裝面；缺席→顯性訊號（drift 或明示未驗，fail-loud 形態照 AIR-126 guard/monitor 警示先例）②memory drift 訊息補一行修復指引（對齊同款警示形態）③退出碼契約照 AIR-126 先例：警示不改退出碼、drift 仍 exit 1④兩者皆有測試修前紅修後綠⑤來源＝AIR-126 新 clone 模擬 fake HOME 實查〕範圍——改：governance/install.py（check 訊息面）、tests/test_governance_check.py；不動 bootstrap 編排。AC 見卡面。
<!-- SECTION:PLAN:END -->
