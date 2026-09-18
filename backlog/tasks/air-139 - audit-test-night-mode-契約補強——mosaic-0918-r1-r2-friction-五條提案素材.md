---
id: AIR-139
title: audit-test night-mode 契約補強——mosaic 0918 r1/r2 friction 五條提案素材
status: To Do
assignee: []
created_date: '2026-09-18 19:25'
updated_date: '2026-09-18 19:26'
labels: []
dependencies: []
ordinal: 125000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
mosaic audit-test --night 首跑（night-mode-0918，r1 中止＋r2 完成）的 friction 實證回饋，五條 skill 改進提案素材。源弧＝mosaic 主 repo pending-decisions〔night-mode-0918-r2〕（AIR-124 notes 有完整 verdict 與指針）；素材僅指針＋path:line，逐條來源＝弧 WT `/Users/ctai/Github/mosaic_alpha-audit/.agent-tmp/night-mode-0918/friction.log`。五條提案：

1. **night-mode 契約 4 補條款**：零 commit 環境下 P5 rerun 必須 `rm -rf mutants/` 全清——mutmut git-change-detection 對未提交變更（config 與 test 皆）不失效快取（r1+r2 兩次實證）。
2. **mutmut timeout 分類≠config artifact**（60× 不變，r2 證偽 r1 假設）——基線口徑應把 timeout 單獨列示、不入 kill-rate 分母。
3. **契約 1 補 verbatim 條款**：manifest／工單 invariant 逐字引用來源，壓縮措辭＝改 oracle（r1 codex 偽陽性根因）。
4. **執行主體 repo 歸屬**（user 已拍板）：專用弧 worktree 形態（main WT 唯一寫入＝sink append）——SKILL night-mode 節 open item 可回填。
5. **P2 工單模板補**：muse sandbox 擋 `uv run`（cache 拒寫）→ 直接指定 `.venv/bin/python`。
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 五條提案逐條裁決（採納／駁回／緩議），裁決結果回執 mosaic 對應卡（跨 repo 指針照 135.5 token 慣例）
- [ ] #2 採納條目落地 audit-test skill 條文與（可行處）測試，條文變更走 instruction-writing 落地前審查閘
- [ ] #3 SKILL night-mode 節既有 open item（執行主體 repo 歸屬）回填收斂
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【0918 開卡】源＝mosaic night-mode-0918 audit 弧跨 repo 通知（素材由 mosaic 側整理、ai-guide 側固化——「ai-guide 檔案由你側固化；素材僅指針」分工）。provenance：muse job-mu6yzg11-m5pm16＋codex job-mu6yzg4f-plwh5a（bridge ledger 在 mosaic 弧 WT）。查證層級：friction.log／ledgers 檔案存在性已驗，提案內容為 mosaic 側自報，落地前逐條對 friction.log 原文核對。
<!-- SECTION:NOTES:END -->
