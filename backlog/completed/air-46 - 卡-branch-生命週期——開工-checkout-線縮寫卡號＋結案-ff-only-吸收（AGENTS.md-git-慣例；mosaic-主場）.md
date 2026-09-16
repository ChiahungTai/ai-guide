---
id: AIR-46
title: 卡 branch 生命週期——開工 checkout 線縮寫+卡號＋結案 ff-only 吸收（AGENTS.md git 慣例；mosaic 主場）
status: Done
assignee: []
created_date: '2026-09-08 07:51'
updated_date: '2026-09-08 22:11'
labels:
  - git
  - workflow
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-08-card-branch-lifecycle/index.html
  - ai-analysis/_tasks/_archived/09-08-card-branch-lifecycle/ep.md
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
卡開工 checkout 以線縮寫+卡號命名的 branch（ai-rules=air-46；mosaic=lab-77/bt-77/mos-77），結案 /commit 確認後回 owning 線 merge --ff-only 吸收、刪 branch；ambient 顯示（線+卡）＋整卡 diff 邊界＋整卡可拋棄。〔baseline：ai-rules d4c98ab〕〔已決策勿重辯：①主場=mosaic——user 三 VSCode=三 WT（main/v2/warrant），branch 顯示=線+卡是唯一 ambient UI；②建卡不開 branch、開工（implement 階段1 起手式⑤後）才 checkout；③收尾=回 owning 線 --ff-only 吸收非 merge（/rebase 兩步）；④線判定路徑查表（toplevel basename）；⑤owning 線記卡 desc＋開工驗證 checkout 起點；⑥規則落 ai-rules/AGENTS.md git 慣例節，mosaic 落地由 MOS 衍生卡承接（不在 ai-rules 動 mosaic 檔）〕〔驗收：AGENTS.md git 慣例節落地＋EP SM-1..16 文檔化＋muse ep-review findings 處置完畢＋/consistency 綠〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
命名修正（user 開工前拍板，F-1 型回寫）：branch prefix 恆取所在線 branch 名——ai-rules=main-46、mosaic=main-77/war-77/v2-77；air-/mos- repo 前綴移除（v2/war 是 branch 名，非 WT 路徑名）。desc 已決策①以此為準。

命名最終版（覆前 note——前 note 的 main-46/war-77/v2-77 作廢）：prefix=WT toplevel basename 縮寫（線身份=WT 路徑，branch 開卡後會換）——ai-rules=air-46、mosaic=lab-77（trading_lab/warrant）/bt-77（offline_backtesting/v2）/mos-77（mosaic_alpha/main）。branch 已正名 air-46。

消費場景（SM 提煉，自包含）：開工後 harness/VSCode 恆顯 branch 名即當前卡（air-46=AIR-46）；跨 session review 用 git diff main..air-46 取整卡邊界；探索失敗刪 branch 即整卡丟棄（需 user 確認）；結案 ff-only 吸收 main 歷史恆直線；/rebase all 前必查無進行中卡 branch

F7 triage（muse code review 狗糧發現）：AIR-50 建卡 commit 0cd90a5 落在 air-46 上（平行 session 於 WT 停卡 branch 時建卡即 commit）——吸收時隨 ff 流回 main 屬無害歸位（建卡本該在 main），commit message 明示帶走。防護已入 kanban 建卡段（建卡前確認 branch＝owning 線）。F10：/consistency 證據——AGENTS.md＋kanban SKILL 六維 100/100（implement 期跑＋修正後重驗）。muse 10 findings 全採納（F1-F10）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
卡 branch 生命週期落地——AGENTS.md git 慣例節＋kanban 差異宣告/起手式⑥pointer（F3-1/F3-2 must-fix 解）；命名=WT basename 縮寫（air-46/lab-77/bt-77/mos-77）；muse 18 findings 全採納；本卡 dogfood 全程示範（air-46 branch 開工→吸收）
<!-- SECTION:FINAL_SUMMARY:END -->
