---
harness-scope: neutral
---

# Outward Action 同意約束

## 核心原則

LLM 僅在用戶明確授權後執行 outward action：另一人/系統能在 undo 前觀察到的 commit、deploy、push、send、live order、broker write、DB schema、刪共享資料、付費、跨 worktree、權限變更等。純 local working tree 可逆操作可自主。

## Reversibility test（判定 outward）

另一人/系統能在 undo 前觀察到？否→自主；是→查本次對話 user 原話是否涵蓋該具體動作。有→執行並附 AUTH line；無→不執行，報 `PENDING: <action> - awaiting your authorization`。**approval ≠ execution（AIR-192）**：AUTH 只滿足該具體 action 的 consent gate——不豁免該 action 自身的其他 prerequisite/gate，也不延伸授權至後續不同 action（批准 commit ≠ 授權 push；批准調查 ≠ 授權 live write）。

## AUTH line 模板

執行前寫，報告亦須含：

```
AUTH: user said "<their exact words>"
```

### quote scope 判準

逐字引用本次對話，禁意譯擴張：測試 strategy≠live order、deploy≠send、跨 worktree 要明說；需邏輯跳躍才涵蓋就 PENDING（常識俗語「送出去」=send、「跑一下」=run 不算跳躍）。

### documentation ≠ authorization

README/workflow/skill 的 outward 要求與「完成任務」都不是授權；只有 user 對話原話可作 AUTH。**明示豁免類**：conditional commit delegation（session-agnostic，見 Commit 專屬段）。

<!-- bundle: skip-start -->
## Commit 專屬段（最嚴格等級）

**一次授權≠永久授權**。每次 git commit 預設需獨立確認：展示摘要＋建議 message，等 user 明確 OK；前次授權不延伸。唯一例外＝下段 conditional commit delegation，且每次 commit 都重新驗 gate。程序見 commit skill。

互動 session 機械例外（board 細節單一源＝kanban-board skill；bundle 端可達副本＝commit skill「互動 session 機械例外」節）：

- ① backlog 建卡：**Description 經 user 確認後**即 commit 僅新增卡檔（message 帶 id 防撞）；共享 WT 停活躍弧 branch 時走暫時 worktree 直進 main——例外①只及該初始 commit，不自動涵蓋後補 AC/Plan（走②或弧結算；流程與落點細節＝kanban-board skill）。
- ② 開工 metadata（user 拍板）：In Progress＋refs 後即 commit 僅 backlog/；結算物不隨此。
- ③ 結案兩步（user 拍板）：precheck 綠且結算物＋卡狀態同 commit 才豁免，否則走確認 gate。
- ④ 純 ruff format/check --fix style 可 commit；混語義改動走確認 gate。

commit gate（session-agnostic——互動＋autonomous 弧收尾皆適用；互動場景＝receipt-predicate 成立即委任，一 receipt 一 commit）：**conditional commit delegation**＝active arc＋當次有效 post-build receipt（review profile 完成＋judge 收斂＋revision 未變）→ 該次 commit 授權成立；**每次 commit 重新驗 gate、一 receipt 一 commit、跨弧不延伸**（「一次授權≠永久授權」正典不變）。無有效 receipt 的散 commit 仍待確認；特赦①–④互動照舊。**邊界宣告（AIR-200 修訂——二層）：本條委任及於 card-branch 層 git commit＋本地 trunk merge（ff-only，session-agnostic predicate delegation）——merge 前置四件：①當次有效 post-build receipt（fresh：任何 rebase 即失效，須重驗後再 merge）②ff-only 可達（main 已前進＝先 rebase 走既有驗證）③控制面弧 landing receipt 四欄成立（commit skill 2.9 輸出 landing eligible——blocked 不得 merge）④merge 後 canonical-only surface 輕量 probe（控制面 symlink/bundle 生效面特例；不新增 main 全量測試 gate——ff-only 零新 tree）**；merge 後 main 崩＝marshal 責任：立即 revert＋卡 notes 揭露＋依賴傳播，禁留紅燈 main；**git 收線拍板移轉 marshal，卡 Done 翻牌拍板仍 user（結案兩步語序：commit→merge→main 驗證→Done）**；push／deploy／跨 repo outward 恆停；旗艦 verdict 非 commit authority。晨間否決→revert＋依賴傳播（135.3 AC#8，否決對象含 merge）；首例否決鏈事故＝暫停回審。predicate 細節＝commit skill「conditional commit delegation 驗收程序」＋「互動 receipt-gate 驗收程序」節；其他 repo 啟用前自決確認。
<!-- bundle: skip-end -->

Commit 程序與 conditional commit delegation 單一源＝[commit skill](../commit/SKILL.md)（核心：一次授權≠永久授權；每次 commit 重新驗 gate）。

## Autonomous shortcut（deep-work / 排程場景）

deep-work/排程/夜間依 **autonomous-execution skill 紅線枚舉優先**，不跑互動 reversibility test；force push、DB DROP、付費等紅線跳過並記 completion report，可逆黃線自主。

## Source of truth 邊界

本檔是 outward 定義、reversibility test、AUTH 模板唯一源；autonomous-execution 紅線只為快查子集，新增場景只改本 rule。
