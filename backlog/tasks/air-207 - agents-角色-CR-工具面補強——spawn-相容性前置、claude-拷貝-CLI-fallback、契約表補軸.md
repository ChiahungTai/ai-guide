---
id: AIR-207
title: agents-角色-CR-工具面補強——spawn-相容性前置、claude-拷貝-CLI-fallback、契約表補軸
status: In Progress
assignee: []
created_date: '2026-09-26 01:58'
updated_date: '2026-09-26 01:58'
labels: []
dependencies: []
ordinal: 193000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
昨夜 AIR-205 弧的架構盤點發現 agents/ 三個改善點：①五個角色掛 CR MCP 全名白名單，在沒有 CR 外掛的 session 會直接派發失敗（啟動快照炸彈），而 205 落的注入邊界檢查攔不到這種死法——補一條派發前置：判斷本 session 有無 CR 面，沒有就改派無白名單角色加命令列字串；②claude 端拷貝生成器會剝掉 CR 工具行，等於 claude 端審查者結構性沒有 CR——在角色本文補「MCP 缺場改用 CLI 等效命令」的降級指引，讓剝行從缺陷變降級路徑；③契約表補上派工面註記軸的文件行，並檢查角色本文有無與單一源重複的 CR 條文要改指針。

```mermaid
graph LR
A[快照炸彈：白名單角色派發失敗] --> B[派發前置：session 有無 CR 面]
B --> C[無面改派＋CLI 字串]
D[claude 拷貝剝 CR 行] --> E[角色本文 CLI 降級指引]
F[契約表缺註記軸] --> G[補文件行＋條文去重]
```
<!-- SECTION:DESCRIPTION:END -->
