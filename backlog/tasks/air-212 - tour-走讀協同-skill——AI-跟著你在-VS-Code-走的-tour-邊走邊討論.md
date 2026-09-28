---
id: AIR-212
title: tour 走讀協同 skill——AI 跟著你在 VS Code 走的 tour 邊走邊討論
status: In Progress
assignee: []
created_date: '2026-09-28 13:07'
updated_date: '2026-09-28 13:08'
labels: []
dependencies: []
references:
  - skills/tour-collab/SKILL.md
ordinal: 198000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
接續 muse session 調查（09-28）：mosaic 的 UI-LLM 協同做法有兩層——通用哲學（ui-collab）＋工作台接線（annotate-collab，mosaic 專屬）。其中「跟隨 user 走 SC tour」的行為目前以 ~8 行摘要嵌在 mosaic annotate-collab Phase 2，但它其實與 mosaic 無關：任一 repo＋South Chariot extension＋tour-actions.log 都能用。本卡把這塊抽成 ai-guide 全域薄 skill `tour-collab`。

**做什麼**：LLM 輪詢 workspace 根 `.agent-tmp/tour-actions.log`，被動得知 user 在 SC extension 走讀的 tour／步／語義位置，邊走邊上下文感知討論；討論記錄走 llm-discussions/ 慣例。

**不做什麼**：tour corpus 製作（歸 tour-bootstrap）；mosaic 工作台操作協同（歸 annotate-collab）；位置契約本身——line schema／anchor 語義／rotation 單一源＝southchariot 契約文檔，本 skill 只寫消費端紀律＋指針，不重抄。

**本卡不做**：mosaic 端 annotate-collab Phase 2 第二事件源縮為指針＝跨 repo 連動，mosaic 側另動手，本卡只報。

**規矩**：位置判讀只信語義錨（step_file＋anchor_status＋resolved_line＋ref）；ref 非 null 一律 git show 讀歷史版，禁拿 HEAD 回答 historical tour。

```mermaid
flowchart LR
    U["user 在 VS Code 走 tour"] --> SC["SC extension 寫入 tour-actions.log"]
    SC --> LLM["LLM 每輪整檔重讀，以 writer 加 seq 去重"]
    LLM --> AN{"語義錨判讀"}
    AN -->|exact| CODE["讀 code 回應討論"]
    AN -->|none| NARR["敘事頁，不讀 code"]
    AN -->|ref 非 null| HIST["git show ref 讀歷史版"]
    CODE --> REC["討論記錄 llm-discussions/"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 skills/tour-collab/SKILL.md 存在，frontmatter 過 desc gate（uv run python scripts/scan_skills_desc.py 零 fail，desc 值含引號 ≤1024 chars）
- [ ] #2 skills/AGENTS.md 索引含 tour-collab 行（工作流 skills 區，desc 語義與 SKILL.md 一致）
- [ ] #3 SKILL.md 涵蓋五塊：前置偵測（tour-actions.log 在場檢查＋不在場零成本跳過）／輪詢紀律（整檔重讀禁 offset、(writer_id, seq) 去重、tour_stop 會話邊界、CC Monitor／ZCode 每輪 rg 雙形態）／語義錨判讀紅線（display_* 僅 UI context、none＝敘事頁、ref 非 null 禁 HEAD）／討論記錄（ui-collab 哲學＋llm-discussions/）／單一源指針（southchariot 契約＋tour-bootstrap 分工）
- [ ] #4 五維檢查通過：引用目標存在、無元資訊、術語一致、無矛盾、格式正確
- [ ] #5 落地前審查閘回執四欄齊（classification／review／session-freshness／deployment-surfaces）——landing 前補齊，authoring 期可 pending
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
〔baseline：ai-guide 48b85e70b562b80163a6d9dffbb9f9dd2c79ecef〕
〔已決策勿重辯：①載體＝skill 非 rule（on-demand、多階段程序、有觸發語、harness 雙形態——muse 01a0e6ad 調查裁定）②位置＝ai-guide 全域 skills/tour-collab/（走讀消費與 mosaic 無關，非 repo-local）③thin 單一源——line schema／source enum／anchor 語義／rotation／多 writer 邊界一律指針 ~/Github/southchariot/docs/tour-action-log.md（sc-281），本 skill 不重抄④行為哲學繼承 ui-collab（觀察→等待→上下文感知→記錄），記錄走 llm-discussions/ 慣例⑤corpus 生產歸 tour-bootstrap、工作台操作歸 annotate-collab，本 skill 不跨界⑥控制面 authoring 走 persistent card WT（AIR-106 隔離閘），landing（merge/deploy）前須審查分類＋審查腿回執〕
範圍：新增 skills/tour-collab/SKILL.md＋skills/AGENTS.md 索引行＋desc gate（scripts/scan_skills_desc.py）；mosaic annotate-collab Phase 2 縮指針＝跨 repo 連動另辦（mosaic 側動手，本卡只報）
<!-- SECTION:PLAN:END -->
