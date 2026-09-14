---
id: AIR-94
title: ai-rules→ai-guide 改名落地——全表面遷移（DRAFT-8 觸發；deep-work 弧）
status: Done
assignee: []
created_date: '2026-09-14 08:17'
updated_date: '2026-09-14 12:29'
labels:
  - rename
dependencies: []
ordinal: 80000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
baseline＝.agent-tmp/ai-guide-rename/investigation.md（S1–S10 全表面調查＋驗收 8 條）。已決策：target=ai-guide（DRAFT-8 三輪定案勿重辯）；user 2026-09-14 拍板立即執行（原 SouthChariot-同批觸發作廢，codex 裁定零技術耦合）；deep-work 弧全程禁 commit/push（consent 在 user）；目錄 mv＝flash 主 session 最終段親執行。鏈路：flash 調查→muse EP→codex ep-review→flash implement→muse post-build→codex code-review→codex judge-review。驗收：investigation.md 驗收節 1–8。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【09-14 晚間修復弧補記】改名後自動化掃尾（本卡驗收延伸）：① 三條 ZCode cron 因 workspace key 失效——每晚 23:40 已於 ai-guide workspace 原樣重建＝automation-c9eb6495（首發 09-14 23:40）；週日／週六兩條待建（spec 版控＝ai-analysis/_tasks/done/09-14-ai-guide-rename/cron-rebuild-prompts.md；harness 限一 session 一排程）。② launchd com.ai-guide.backlog-cleanup 上線（label/path/log 三改，舊件 retired）。③ ~/.codex/hooks.json 三 hook 舊路徑修復（曾致 codex shell 全被 PreToolUse fail-closed 擋下——實證發現）。④ 卡 id 前綴定案＝A 保留 AIR（codex 兩輪裁決：round1 A GO／round2 user 同號映射變體 GO-with-gates，user 拍板 A）；AGENTS.md 已載 AIR＝歷史沿革 namespace。⑤ mosaic 側兩條夜間排程 prompt 內嵌 ai-rules 路徑——工單＝ai-analysis/_tasks/done/09-14-ai-guide-rename/mosaic-side-ticket.md（跨 workspace 待 user/mosaic session）。⑥ schedule-registry.md 全同步；topology 驗證 5 passed。機械事實：task_prefix 改 aig 而卡檔未 rename＝舊卡全隱形＋編號重啟 AIG-1（沙盒實證）。尚未 commit——consent 在 user。

【09-14 深夜追加——:6421 退出後續】F4 殘項（下一個 docs 弧承接）：check_report_shells.py 訊息文本仍教 viewer 契約（viewer URL 白名單＋violation 文案）——需反轉 lint 規則（旗 viewer URL、放行相對 .md）＋訊息文本更新；注意歷史殼 12 個會因此觸旗，需 carve-out 或批次勘正。judge 認可本輪延後（避免擴 diff）。

【F4 已收口（09-14 深夜，本弧內處理——原列後續 docs 弧，user 裁決當場做）】check_report_shells.py lint 規則反轉落地：viewer URL 形態在活躍殼＝violation（新訊息教 repo 相對路徑合約）、歷史位置（_tasks/done/＋reports/＋blueprint/）豁免留歷史態；測試 TDD 8 passed（含活躍觸旗／歷史豁免／相對路徑不觸／新文案四案例）；12 歷史殼豁免實證、零 index.html 被改。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
ai-rules→ai-guide 改名全表面落地＋掃尾完成（四主 commit d6b05d0／6ba5c29／a027dbe／fb6d3e2＋judge 裁決修正 c63e8d6）。機械面：目錄 mv＋symlink 鏈＋hooks 註冊（CC/ZCode/codex）＋deploy 產物＋記憶池/spine；排程：三條 ZCode cron 於新 workspace 全數重建（c9eb6495／23c773b9／c52d4574）＋舊三條 sqlite 收除＋launchd com.ai-guide.backlog-cleanup；bounded say 30s 自清（mosaic 事故弧收尾）。決策：卡前綴保留 AIR（codex 兩輪＋user 拍板）；ai-guide 退出 :6421（viewer 形態退役、lint 反轉＋歷史豁免）。審查：post-build 三輪 muse/codex＋5.3 judge converged（judge 追加修：M2 log 合流、M3 server mount、registry 五處、F2/F3/F5、E1-E3）；pytest 433→429→433 全綠。跨 repo：mosaic 工單完成（兩排程 CronUpdate＋server 死 mount 刪除 96829c6a7＋三卡 refs 清理 458bb49ce）。教訓入池：reference_zcode-cron-workspace-scoping（workspace-key／一 session 一排程／db 考古／.venv shebang）。
<!-- SECTION:FINAL_SUMMARY:END -->
