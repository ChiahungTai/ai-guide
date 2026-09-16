---
name: feedback_no-sandbox-layer
description: User 覺得 sandbox 不好用而關掉；解決寫入權限時別提議 sandbox.allowWrite，動 permission list / defaultMode
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 658a85ac-a2cf-425c-b622-91a55088b7e5
---

User 全局 `settings.json` 設 `sandbox.enabled: false`（原 `true` 是 drift —— settings.json gitignored、無 git 軌跡，AI 一度誤以為 sandbox 擋住 /tmp 寫入）。

**Why**：user 覺得 sandbox **不好用** —— 高 IO / 跨多專案 workflow（mosaic data、DB、Redis、Docker、跨 project 讀檔）會一直被擋、要反覆補 allowWrite，operationally 跟 workflow 對著幹。**不是原則性反對，是實用判斷**。附帶好處：sandbox 在開放的 permission list 底下偷擋寫入，製造「permission 開了卻寫不進」的誤解（user 原話「以免誤解」），關掉後設定 WYSIWYG。User 跑高信任低摩擦：`defaultMode: acceptEdits` + 龐大 allow-list。

**How to apply**：解決「某路徑寫不進去 / 該不該開寫入」時，動 permission list（`Write(...)` / `Bash(...)`）或 `defaultMode`，**不要提議 `sandbox.filesystem.allowWrite`** —— 那層被刻意關掉。`enabled: false` 時，sandbox block 下的 `autoAllowBashIfSandboxed` / `filesystem` 是 dead config（清掉以維持 WYSIWYG）。

判斷設定是否 drift：設定檔 gitignored（`git check-ignore`）+ 無 commit 軌跡（`git log -- <file>`）+ 與 user 記憶矛盾 = 高機率 drift。

相關：[[global-vs-project-permissions]]、[[feedback_permission-layer-no-behavioral]]。
