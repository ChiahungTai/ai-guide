---
harness-scope: neutral
---

# Outward Action 同意約束

## 核心原則

LLM 僅在用戶明確授權後執行 outward action：另一人/系統能在 undo 前觀察到的 commit、deploy、push、send、live order、broker write、DB schema、刪共享資料、付費、跨 worktree、權限變更等。純 local working tree 可逆操作可自主。

## Reversibility test（判定 outward）

另一人/系統能在 undo 前觀察到？否→自主；是→查本次對話 user 原話是否涵蓋該具體動作。有→執行並附 AUTH line；無→不執行，報 `PENDING: <action> - awaiting your authorization`。

## AUTH line 模板

執行前寫，報告亦須含：

```
AUTH: user said "<their exact words>"
```

### quote scope 判準

逐字引用本次對話，禁意譯擴張：測試 strategy≠live order、deploy≠send、跨 worktree 要明說；需邏輯跳躍才涵蓋就 PENDING（常識俗語「送出去」=send、「跑一下」=run 不算跳躍）。

### documentation ≠ authorization

README/workflow/skill 的 outward 要求與「完成任務」都不是授權；只有 user 對話原話可作 AUTH。

## Commit 專屬段（最嚴格等級）

**一次授權≠永久授權**（正典——skills 投影端〔work-order／model-routing／at〕引用此句）。每次 git commit 都需獨立確認：展示摘要＋建議 message，等 user 明確 OK；前次授權不延伸。程序見 commit skill。

互動 session 機械例外（board 細節單一源＝kanban-board skill）：

- ① backlog 建卡：task create 後即 commit 僅新增卡檔，message 帶 id，供跨 WT 可見並防 id 撞；共享 WT 停在活躍弧 branch 時，建卡 commit 走暫時 worktree 直進 main（全程 `git -C` 禁 cd，形態＝kanban-board skill「共享 WT 活躍 branch 落點分流」）——該暫時 worktree 操作屬①豁免範圍。
- ② 開工 metadata（user 拍板）：In Progress＋refs 後即 commit 僅 backlog/；結算物不隨此。
- ③ 結案兩步（user 拍板）：precheck 綠且結算物＋卡狀態同 commit 才豁免，否則走確認 gate。
- ④ 純 ruff format/check --fix style 可 commit；混語義改動走確認 gate。

autonomous session 不繼承任何 commit 例外——所有 commit（含結案條件鏈③）一律待用戶確認；機械特赦①–④僅限互動 session（09-13 user 裁定）。

## Autonomous shortcut（deep-work / 排程場景）

deep-work/排程/夜間依 **autonomous-execution skill 紅線枚舉優先**，不跑互動 reversibility test；force push、DB DROP、付費等紅線跳過並記 completion report，可逆黃線自主。

## Source of truth 邊界

本檔是 outward 定義、reversibility test、AUTH 模板唯一源；autonomous-execution 紅線只為快查子集，新增場景只改本 rule。
