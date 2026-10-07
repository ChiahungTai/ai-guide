---
id: AIR-271
title: agent_liveness_sweep bounded/增量掃描——根治 sitrep 面5 耗時
status: To Do
assignee: []
created_date: '2026-10-07 04:09'
labels:
  - scripts
dependencies: []
ordinal: 262000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
sitrep 面5 的 bridge job 盤點用 `agent_liveness_sweep.py`，但它對雙根 `jobs/*.jsonl` 全量逐檔 read_text（GB 級、只增不減），實測 22–30s+ 才一次性輸出——違「快速快照」體感。AIR-269 judge 裁定 skill 端以「耗時須知＋≥300s 逾時指引＋急巡跳過」收斂（已落地），根治解＝sweep 腳本本身加 bounded/增量掃描面（檔數/bytes 上限或 mtime 增量視窗），屬 bridge 收線觀測基建。

**做什麼**：sweep 加上限參數（如 --max-files／--max-bytes 或 --since）＋輸出加「掃描覆蓋率」聲明（bounded 時如實標未掃部分）；sitrep skill 面5 同步補 bounded 呼叫式。
**不做什麼**：不動分類語義（terminal-unclaimed/zombie 判準）；不重刻 bridge-dispatch 收線契約。

```mermaid
flowchart LR
  s[\"sitrep 面5\"] --> b[\"sweep bounded 呼叫\"]
  b --> q[\"秒級回報 覆蓋率如實標\"]
  q --> f[\"GB 級全量掃描退役為深查模式\"]
```
<!-- SECTION:DESCRIPTION:END -->
