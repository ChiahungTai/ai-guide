---
id: AIR-335
title: D-011 抓地——probe／spine 的 muse unknown 與 codex 分帳消費語義可執行化
status: In Progress
assignee: []
created_date: '2026-10-14 12:25'
updated_date: '2026-10-14 12:40'
labels: []
dependencies: []
ordinal: 320000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
D-011 correction 重演：「codex webgpt／muse 額度」兩個 model 事實政策已三層編碼（always-on 指針／on-demand skill/catalog／機械 probe+bridge），他 session 仍誤讀——洞定位為「unknown/exhausted 的消費動作在判讀現場不可執行」（probe 說「禁推定」但沒說「該做什麼」）。本卡讓 muse＋codex 討論出具體抓地設計，judge 裁決後落地。

**做什麼**
- bi-panel 討論：probe_entitlements.py 輸出訊息可執行化＋spine muse/codex 行消費語義補強（＋第三案評估）
- judge 裁決→實作→部署驗證

**不做什麼**
- 不做 hook/閘強制（AIR-135 條 3：startup 只 advisory、gate 在 consumer boundary；muse 無機械探測面可擋）
- 不改 catalog 三級表／routing 政策本身

**規矩**
- 事實三層現狀是對的，只修「判讀現場訊息的可執行性」；訊息措辭禁元資訊

```mermaid
flowchart LR
  D["D-011 重演"] --> V["viewport 定位：消費動作不可執行"]
  V --> P["muse+codex 討論設計"]
  P --> J["judge 裁決"]
  J --> I["實作＋驗證"]
```
<!-- SECTION:DESCRIPTION:END -->
