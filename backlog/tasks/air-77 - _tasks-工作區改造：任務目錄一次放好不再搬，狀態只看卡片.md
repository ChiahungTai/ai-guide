---
id: AIR-77
title: _tasks 工作區改造：任務目錄一次放好不再搬，狀態只看卡片
status: Done
assignee: []
created_date: '2026-09-11 22:51'
updated_date: '2026-09-16 22:52'
labels:
  - structure
  - migration
dependencies: []
references:
  - ai-analysis/blueprint/workflow.md
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕把弧工作區改成「一次放好、永不搬家」：新任務目錄按月份歸檔，舊的一次遷進 _archived，之後卡片狀態是唯一的生命週期訊號、連結永不因搬移而斷。

〔baseline：ai-rules 882c9b5〕
〔已決策勿重辯：①append-only——task path 只表達 identity＋建立時間，不表達 lifecycle；lifecycle 唯一源＝卡 status ②新弧落 _tasks/YYYY-MM/<弧名>/，永不搬移 ③done/ 26 已閉弧＋AIR-45 兩已閉弧一次遷入 _tasks/_archived/，遷後凍結（可讀可引用、不再新增不再搬）④path→status 消費者翻轉為 card-status 判讀——metadata-sync（:41,45）、memory-audit（:91）、kanban 結案 refs 重寫、check_report_shells.py（:5-10），外加 memory_telemetry.py／scan_project.py 的 depth 假設 ⑤finalization 定義剔除 filesystem relocation ⑥supersession-move（report/blueprint 退役制防雙真相）不變 ⑦月份目錄優於平面——平面 MM-DD 跨年失年份＋碰撞空間（codex 顧問意見）⑧finalization 原子性改寫：badge／卡 status／summary 照舊收斂，filesystem relocation 退出 ⑨三方諮詢（GLM-5.3 主 session 分析＋codex chatgpt-web 段落級複核 09-12；glm 載具回信未及併入，開工時補查）。風險面：寫入契約首改（收尾慣例全 consumer 翻轉）＋跨文件交叉推導〕
〔驗收：rg 全掃 _tasks/done/ 舊路徑引用零殘留；四處 path→status 消費者改讀卡 status 附 rg 機械證據；3 支 script 月份層 depth 假設掃描通過；活弧 09-11-test-contract-v31 遷 2026-09/ 且 AIR-76 refs 更新；workflow.md 放置規則＋illustrate-html-mode＋execution-plan/implement/commit 等 13+16 檔慣例文本同步；一次性遷移在單 commit 內可 revert〕
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 done/ 26 弧＋AIR-45 兩已閉弧遷入 _tasks/_archived/；rg 全掃無殘留舊路徑引用
- [ ] #2 path→status 四處消費者改讀卡 status，附 rg 機械證據
- [ ] #3 3 支 script（check_report_shells／memory_telemetry／scan_project）月份層 depth 假設通過
- [ ] #4 新弧出生落 _tasks/YYYY-MM/；活弧 test-contract-v31 遷移＋AIR-76 refs 更新
- [ ] #5 workflow.md／illustrate-html-mode 等 13+16 檔慣例文本同步；單 commit 可 revert
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
mosaic 腿（跨 repo）：handoff 已產出交 mosaic 側自行派工——評估 _projects/<線>/tasks/ 同型慣例跟進或分岔；ai-rules 側不 wait mosaic，兩腿獨立結算。

〔09-12 設計修訂：user 重申維持 _archived 遷移（動機＝目錄整潔優先，mosaic_alpha 目錄混亂為反面印證）；glm 凍結案已知悉不採，代價與 mitigation 併入如下〕
① 遷移範圍：done/ 26 弧＋AIR-45 兩已閉弧 → _tasks/_archived/；_archived/ 放墓碑 README（legacy frozen、生命週期唯一源＝卡 status、新弧落 YYYY-MM/ 永不搬）；空 done/ 目錄移除
② 30 張 completed 卡 references 的 done/ 路徑機械批次改寫為 _archived/，rg 全掃驗證零殘留（歷史卡只改路徑不改內容，git 保留歷史）
③ 無卡弧豁免條款：免 UC 小修／研究弧無卡，天生即終態，目錄即全部事實，不參與 lifecycle 追蹤——防原則被合理繞過
④ 弧 refs 出生即寫（路徑生而恆定）；kanban 結案補寫 refs 退化為可選
⑤ supersession（弧目錄）＝就地墓碑（檔頭 superseded-by 指標），不搬——零搬移貫徹
⑥ EP 待裁：月內弧命名終局形態——主題-only（glm 指日期雙重編碼為長期醜態）vs 保留 MM-DD 前綴；開工時定並寫入慣例文件
⑦ 證據源註記：glm 載具（bridge --family glm）實跑 GLM-5.3-Flash 非 5.3 旗艦；codex＝chatgpt-web/high

〔09-12 補裁決〕卡 notes ⑥ 結案：月內弧命名終局形態＝保留 MM-DD 前綴，即 _tasks/2026-09/<MM-DD-主題>/——user 拍板；glm「日期雙重編碼」意見已知悉不採。慣例文件同步時寫明此終局形態。另：Done/completed 兩階段行為查證（backlog CLI 源碼）未完成，卡平面後續想法擱置不擴張。

〔09-12 查證結案〕Done/completed 兩階段行為經 lite-verify 源碼＋runtime 雙證據裁決：user 主張成立——Done＝board 可見終態（檔留 tasks/），task complete＝手動 cleanup 封存（completed/，board/list/search 全隱形），官方 help 明言僅供 cleanup/archive 用，上游 repo 自身留 165 張 Done 卡在 tasks/。先前顧問「Done 留 tasks/＝漂移」宣稱不成立；「廢 task complete」後續卡想法撤銷。board 過濾憑目錄成員資格非 status 欄；backlog CLI 只讀 backlog/ 樹，與本卡（ai-analysis/_tasks）零接觸。

〔wt-close 首例 receipt（人肉補記，marshal 2026-09-16——執行輸出節錄自收線 session）〕①preflight：P2 clean／P2.5 池 symlink 無／P3 1 顆全屬 air-77／P4 WARN owning 線已前進／P5 rebase 可行。②因分叉先 rebase main（→74d483d 零衝突）＋post-rebase 驗證（殘留 0／lint 0／664 tests）＋user gate ①核准。③ff-only 吸收 f827231→74d483d（443 檔）。④wt-close full 調用：首次誤帶 --full（旗標不存在——usage 教訓）→ 正確調用成功：Already up to date→Deleted branch air-77→已移除 WT＋branch。⑤殘留清理：gitignored 目錄殼（done/＋09-08-unification，僅 .bak fixture）手動移除；期間平行 followup session 落 ea94964（linear 譜系已驗）。後續自動化＝AIR-112 receipt 落盤卡。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
_tasks 工作區改造完成（74d483d 進 main，443 檔）：_archived 一次遷入＋月份層＋path→status 消費者翻轉；wt-close full 首例收線（WT/branch 已移除，receipt 人肉補記 notes :54）；自動化後續＝AIR-112
<!-- SECTION:FINAL_SUMMARY:END -->
