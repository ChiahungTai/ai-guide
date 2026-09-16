---
name: commit-finalization-gate
description: commit finalization 閘門：2.8 對帳＋孤兒結算＋docs 單檔閘＋footer 中性化＋ruff 機械改動免確認
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

commit 漏帶是機率性漏失——閘門（對帳＋半套偵測）＋孤兒結算回收＋機械改動免確認三件套。

> merged_from: project_commit-footer-harness-neutral, feedback_format-spillover-style-commit, 2026-09-07 cluster-merge wave

## 2.8 閘門＋孤兒結算（original: project，keeper 本體）

2026-09-05 user 報案「/commit 流程容易漏 backlog 卡相關 commit」：同 skill 三 session 只 1 帶齊。**三形態現場**：完整對照 trading_lab `95709128a`／半套 mosaic `6bc648698`（refs 指未落地路徑）／事後回寫 offline `1abf2085a`（hash 記不進被記的 commit——雞生蛋懸掛）。**落地**（`1bfefa2`＋`154d29c`）：skills/commit 階段 **2.8 Finalization 對帳閘門**（status 掃 finalization 路徑面＋半套歸檔偵測＋歸屬判定）＋階段 6 pre-commit 結算（無 hash、禁 post-commit 回寫）＋AIR-24 卡結案兩步 pre-commit 同 commit 落地。**閘門首戰抓自己**：目錄級 `git add backlog/` 把並行卡混入——staged 核對＋soft reset 重組（目錄級 add＝小範圍 `git add .`，並行期目錄 add 後必掃 staged 清單）。

**孤兒結算（user 抓到）**：卡 Done＋Final Summary 在場、owning session 已結束、從未 commit＝孤兒（非並行遺留）→ 收編；**commit 標題寫結算≠真結算**（`2a4b43a` 當時卡仍 In Progress——讀卡 frontmatter 非標題）。→ 判定表第三列：活躍排除 vs 孤兒收編（`270551b`＋`0379275`）。**docs 單檔閘門**（`836c645`）：純 `.md` 直 commit 未跑 post-build → commit 前跑 `/consistency`（放執行約束非 2.5——捷徑跳過 2.5）。**殘項指針**：mosaic 補 commit×2＋三池歸因＋版權 lint 已 handoff 轉出（09-05，狀態見 mosaic 側）；池結構問題由 [[memory-cc-alignment-diagnosis-0905]]（AIR-25）接手。相關 [[feedback_verify-wt-before-commit]]（防多面）、[[flash-forensic-0905]]、[[feedback_inflow-needs-outflow]]。

## footer harness 中性化（original: project，純機械事實）

載體是 `skills/commit/SKILL.md` 寫死的 `Co-Authored-By: Claude`（非 git template——`~/.stCommitMsg` 是空 SourceTree 殘留）。已 commit `eeb1be5`：footer＝`Co-Authored-By: <當前 harness 名>`——**刻意不寫死**（skill 四 harness 共用）；歷史 commit 不動。**pre-existing 未決**：階段編號 2.7→4 跳號；L172 link text 舊名（目標存在）。

## ruff 機械改動免確認（original: feedback，09-06 一般化裁定已規則化）

user 兩段裁定：「ruff 自動修改直接 commit 不用確認」＋「混批不拆分隨所在 commit 走」——落地 outward-action-consent 例外二，僅互動 session。**Why**：零語義改動逐次確認無風險對沖；溢出長期滯留污染 status 判讀。**How**：純 ruff→`style:` 直接 commit（具名 add 遵守 [[feedback_verify-wt-before-commit]]）；無主改動先 `git diff -w`——零殘留即同型收清，有殘留＝並行進行中不碰。
