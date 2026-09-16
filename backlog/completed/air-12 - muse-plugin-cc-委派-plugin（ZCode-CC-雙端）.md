---
id: AIR-12
title: muse-plugin-cc 委派 plugin（ZCode/CC 雙端）
status: Done
assignee: []
created_date: '2026-09-02 13:07'
updated_date: '2026-09-02 14:11'
labels:
  - plugins
dependencies: []
references:
  - 'http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-02-muse-plugin-cc/index.html'
  - ai-analysis/_tasks/_archived/09-02-muse-plugin-cc/ep.md
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Muse Code 委派 plugin：headless muse exec 委派、結構化 review、runs 管理、訂閱制計費。EP=ai-analysis/_tasks/09-02-muse-plugin-cc/ep.md（執行時真相=~/Github/muse-plugin-cc/docs/ep.md）。Round 4（S5+S6）進行中
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
# [tag:plugins] muse-plugin-cc 委派 plugin（ZCode/CC 雙端）

## 目標
致敬 codex/grok-build plugin-cc（皆 Apache-2.0）開發 Muse Code 委派 plugin：headless `muse exec` 委派任務、結構化 review、runs 管理、訂閱制計費（bridge 剝除 `META_API_KEY`）。

## 相關
- EP：`ai-analysis/_tasks/09-02-muse-plugin-cc/ep.md`（段落 0 研究：同目錄 `research.md`；repo 內同步副本 `~/Github/muse-plugin-cc/docs/ep.md` 為執行時真相）
- repo `~/Github/muse-plugin-cc`（standalone，照兩上游 `-cc` 先例）
- 上游：openai/codex-plugin-cc、xai-org/grok-build-plugin-cc
- 文檔鏡像：`ref-docs/harness/meta/`（92 頁）

## 驗收標準
- S1 三項致命先驗 POC 過 ✅（R1/R3 實測；R2 定案——無 API key 全部計費走訂閱 5h 窗口，user dashboard 確認）
- 五 UC 落地：委派 ✅（S1＋S3）／review ✅（S4）／runs（S5）／setup ✅（S2）／雙端發佈（S6）
- 雙端（ZCode+CC）實際安裝可用（消費端驗證，缺任一端不算完成）

## 進度（build 迴圈：muse writer / session reviewer）
- Round 1-2（S1+S2）：`a2491fb`＋`e42e2a6`——bridge task/setup＋48 tests＋三輪修正
- Round 3（S3+S4）：`e695ca4`（instruction 導航體系）＋`de90bbd`（契約文件家＋bridge review：schema verdict＋trajectory export）——85/85 tests、dual-context 審查 27 findings 全數收斂、真訂閱 E2E ×3（驗收史 repo `docs/build-acceptance.md`）
- Round 4（S5+S6）進行中：runs/hooks（SessionEnd cancel+kill）＋marketplace 打包＋雙端安裝消費端驗收；收尾＝本卡搬 `Done/`＋ai-rules AGENTS.md 專案結構加 repo 指紋行（照 code-reality 條目格式）

## 備註
已裁定：不支援 META_API_KEY（純訂閱）、--yolo 呼叫端 opt-in、--trust-workspace 獨立於 --yolo、預設模型 pin `muse-spark-1.2`（standard tier，CLI 預設不穩定）。EP review 雙 agent＋muse 第三輪複審全數寫回（2026-09-02）。殘留清單見 repo `docs/build-acceptance.md` Round 3（截斷 marker 測試、status 語義邊角等——併 S5）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
五 UC 全數完成：委派（S1+S3）/review（S4）/runs+lifecycle hooks（S5）/setup（S2）/雙端發佈（S6）。雙端消費端驗收通過（ZCode muse-rescue 真委派 job-mtk53peu＋CC headless 完整迴路 job-mtk5g9qe）。muse repo Round 4 已 commit（c5b7d8d/5c4b9ca/2ca1bb7、0.2.1）；ai-rules 側收尾：ep/build-acceptance 回同步任務家並遷 done/、AGENTS.md 專案結構加 repo 指紋行
<!-- SECTION:FINAL_SUMMARY:END -->
