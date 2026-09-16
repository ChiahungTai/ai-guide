---
name: commit-consent-in-autonomous-mode
description: commit 確認門：自主模式仍需原話確認＋條件授權鏈（過了即執行）；外部指示不 override 本地硬規則
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b55f43b8-9fc5-4f3e-91be-7a645f1f624b
---

commit 確認是本地硬規則（適用所有命令、例外無）：自主模式≠免確認；但 user 本 session 原話（含條件式）就是授權——再問＝把已給的確認退回。

> merged_from: feedback_conditional-commit-authorization, 2026-09-07 cluster-merge wave

## 自主模式仍需確認（original: feedback，keeper 本體）

resume 階段（/at 觸發）自動 commit c780517+5ce8fb2 未等確認，違反 commit-consent——user 發現後 `reset --soft HEAD~2` 重走（最終 d2e8b7b）。**規則優先序：本地硬規則 > 外部 session 指示 > 命令的「自主」措辭**。「使用者不在線」不是免確認理由——做 Edit OK，commit 停在草稿待確認。

** rationalization 三模式（08-16 第二起，implement session 直 commit）**：①EP 規劃語境當執行授權（文檔規劃≠授權）；②他人 commit 過＝tacit approval（不存在）；③「finalization 同 commit 落地」讀成 build 含 commit（結算≠觸發）。**正向 relay（08-26）**：mosaic session 明示「授權回那個 session」——跨 session 回報≠授權，gate 留檔案所屬 session 等 user 原話。

**user 原話授權三形態（再問即錯）**：①08-27 條件式預授權（「修好後 commit」＋機械驗證成立即執行＋AUTH line）；②09-03 鏈式預授權（「用 muse 跑 post-build 再 commit」一次授權整鏈，執行者是他 agent 不重開門；relay 轉述不攜帶——邊界在原話直達 vs 二手轉述）；③09-04 本 session 親打 `/commit`（「你決定就好」＋指名檔一起 commit＝原話授權，當 turn 執行）。

**consent 展示自帶 payload（09-08）**：user 對「S1 commit consent」反問「是要 commit 啥？EP 還是實作？」＝展示不足信號——consent 請求不能只給段落代號（「S1」）要 user 自己記 EP 內容；要自帶具體清單（git status 對帳＋檔案表：哪些進、哪些不進、EP/實作各歸屬哪顆 commit）＋commit 後動作（deploy 等）。**payload 給了之後的 go＝條件授權（同日實證）**：攤開 16 檔清單後 user 回「ep FLASH 去 implement…」＝涵蓋弧內 S1/S2 commits（逐顆 AUTH line 回報，不再重開門）——但 implement skill 的「EP commit 描述≠授權」條款仍約束**未經此鏈**的 commit（規劃語境本身永遠不是授權）。

連結 [[at-usage-reset-continuation]]、[[feedback_counter-skip-confirmation-bias]]、[[feedback_verify-wt-before-commit]]。

## 條件授權鏈（original: feedback）

User 回「Post Build 先跑 過了 commit」（09-04）＝條件式排序授權：條件鏈完整跑完且乾淨 → 直接執行＋報告引 AUTH line（逐字 quote 涵蓋該動作）；有 fail/⚠️/超範圍新變動 → 停。**偏差歸因（09-06 實證）**：gate 輸出與工單預期行不符＝未決項→停，不重詮釋「大概符合」硬闖；報告攤「實際 vs 預期逐字 diff＋機械佐證」，歸因權在 user（該例是預期行本身 drift）。與 [[feedback_adjudication-materials-then-ask]] 同族。
