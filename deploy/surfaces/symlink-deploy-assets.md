---
surface: symlink-deploy-assets
owner: 各 link 目標 owner（agents/ skills/ rules/ 的全域 symlink 視圖）
---

## touches（候選偵測）

`deploy/**`＋本 diff 觸及的 link；已知清單缺登記則註明未覆全。

## probe（唯讀健康探針）

link target 存在性＋type/content identity（`ls -l`／`readlink` 對 canonical 比對）。

## health 判準

link 活（指向 canonical、type 正確）＝healthy；斷鏈或指錯＝unhealthy。
