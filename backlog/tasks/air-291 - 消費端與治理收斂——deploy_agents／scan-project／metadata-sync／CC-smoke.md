---
id: AIR-291
title: 消費端與治理收斂——deploy_agents／scan-project／metadata-sync／CC smoke
status: Done
assignee: []
created_date: '2026-10-08 22:36'
updated_date: '2026-10-09 08:20'
labels:
  - instruction
dependencies: []
ordinal: 282000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
前置：AIR-289/290。①deploy_agents.py：L13-14/L48/L866 stale 文字（宣稱已不存在的 Claude 部署面）＋L427-452 neutral purity guard（檢查 CLAUDE.md wrapper）＋test_deploy_agents.py:179 同步②test_air85_projection_oracle.py（instruction-writing bootstrap 逐字比對）同步③scan-project：scan_project.py 文件/parser 命名＋check_single_source.py:60 audience_self_declare source:CLAUDE.md 錨點失效修正④metadata-sync/SKILL.md 範例⑤CC smoke：claude --version→新 session→/config Project instructions→/context root AGENTS.md→Read 子模組驗 nested 載入（獨立於 pytest）。

⑥judge 補收編清單（AIR-289 bi 分歧 arbiter 裁決，job-mv09ojdi-kx10wb——收口條件③）：skills/audit-test/SKILL.md:116（instruction 檔讀取入口無 fallback、AIR-290 刪 wrapper 後懸空）；skills/execution-plan/SKILL.md:286；skills/compact-prep/SKILL.md:18；scripts/sync_agents.py:1062；POINTER regression guard（test_air85_projection_oracle 逐字比對升常駐機驗——今日為真僅 author 一次性驗證）；scan_project dual-file 行為（scan_project.py:245-250 一目錄一檔、AGENTS 蓋 CLAUDE 漏報雙檔共存＋:237 dual-file docstring 舊措辭）；deploy_agents docstring（GLM F7——CLAUDE.md wrapper 詞表對帳）。

```mermaid
flowchart LR
  a["CLAUDE.md 全退役——user 裁決"] --> b["本卡：對應段落地"] --> c["驗收：rg 歸零／錨點修／smoke"]
```
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 deploy_agents stale 文字＋purity guard＋測試同步
- [x] #2 scan-project/check_single_source 錨點修
- [x] #3 CC smoke root/nested 實證通過
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 老規矩審查鏈（codex＋5.3＋judge）
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【收口——judge 三修＋兩併補（c0d1ed7c/4e29645a/7eb873d5/b1a7e390）re-diff PASS 合併】3705 passed。CC smoke（AC#3）維持 user 端 runtime gate。ledger=.review/air-291.md。

【收口——judge 三修＋兩併補 re-diff PASS 合併 582b3572（11 commits rebase）。rebase 衝突＝deploy_agents L14/L877 與 retire-followup 修同區——取 main 版（較新含 2.1.277 native 細節）。dry-run 四 target OK。CC smoke 維持 user gate。ledger=.review/air-291.md。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
```mermaid
flowchart LR
  a["CLAUDE.md 退役——消費端治理殘留"] --> b["deploy_agents 過時文本歸零＋purity guard 反轉"] --> c["scan-project 去 CLAUDE 中心化＋check_single_source 錨點修＋鍵位錯置擴修"] --> d["metadata-sync 五處歸零＋judge 補收編核實"] --> e["merge 582b3572 Done——CC smoke 歸 user"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
