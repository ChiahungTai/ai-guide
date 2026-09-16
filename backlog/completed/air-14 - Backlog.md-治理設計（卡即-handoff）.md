---
id: AIR-14
title: Backlog.md 治理設計（卡即 handoff）
status: Done
assignee: []
created_date: '2026-09-03 04:31'
updated_date: '2026-09-03 09:46'
labels:
  - governance
  - backlog
  - handoff
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/ai-rules/_tasks/_archived/09-03-backlog-governance-design/index.html
  - ai-analysis/_tasks/_archived/09-03-backlog-governance-design/ep.md
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
中繼站治理設計（兩族合一，2026-09-03 開卡）。〔baseline：ai-rules d121837〕〔已決策勿重辯：①兩族合一框架（任務型+檔案型）user 09-03 裁定 ②討論題即時不建卡——對話即載體，session 斷才落 draft ③drafts=未承諾/觸發型進口（rules-audit draft 首例）④AIR-4 退場走 archive 非 delete（可復活）⑤_inbox 傾向不採——drafts 即進口（待本卡定案）⑥卡三層分工 desc=決策層/EP=規劃層/notes=留言層〕設計問題：卡即 handoff 契約（desc 何時夠格當 handoff——本卡自身即測試案例）、drafts 進口慣例、升卡流程、notes 治理（長度/結案蒸餾/與 EP 邊界）、兩層判定（small 卡即 handoff vs standard+ 卡＋EP）、「做 AIR-N」起手式、EP 修訂時 desc 同步義務；檔案型——.agent-tmp 清淤（36 檔殘留實證）、新 dot-area 門檻、夜間 cron 掃殘留腿、.at-contexts 退場、.review 健康形態參照；共同問法：誰進來/停多久/誰清/清去哪（有進有出）；排程清單單一真相源需求（cron 職責散在 prompt 無總覽——本 session 兩次認知過時實證）。〔驗收：設計文件覆蓋上述全部＋以 MOS-14 卡/EP 與本卡群（AIR-13~17 開卡過程）為回歸樣本；文檔化落地清單（kanban-board/handoff/execution-plan/collaboration-constraints 手術）含 sync-sources 檢查〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
接手指針（09-03 開卡 session 留）：①活實踐樣本＝今天開 AIR-13~17 全過程——進入判準三條實戰（建卡=scope 定+跨 session+可驗收；draft=觸發型；不進=session 內可消化）、兩次 desc 漂移修正（AIR-16 .gitignore 項被並行 commit 搶走→如實化；AIR-15 標題帶舊 scope→改名）、合併先例（②暫存區併入本卡）。②卡即 handoff 張力實證：desc 摘要層裝不下 handoff 八欄——本卡補法=desc 收不變決策+驗收、notes 收接手交代；設計時把這個模式定案或改進。③mosaic 原稿七問在 09-03 handoff（用戶可提供）；MOS-14 卡+EP 絕對路徑：/Users/ctai/Github/mosaic_alpha/backlog/tasks/ 與 ai-analysis/_tasks/。④夜間 23:40 收斂 cron 已運行（automation-751ecce2）——檔案型中繼站的清淤腿可考慮掛它。⑤dual-family 審查（GLM+muse）模式今天首發，可作設計參考

接續進度（muse 續接 zcode sess_7622）：
- 兩張 archify 流程圖已 showcase validate 9/9 過，deliver + visual-check 8/8 PASS（vision-review 已判讀，CJK 無亂碼、邊標籤齊），gitignore 已補 `ai-analysis/_tasks/**/diagram-*.html` 等 4 條。
- design.md 已落 `ai-analysis/_tasks/09-03-backlog-governance-design/design.md`（311 行，§0-§6 齊，R-1~R-8 對應處置：連結 ../../../ 深度已驗、可解析；URL 形態 `ai-rules/<相對於 ai-analysis/ 的路徑>` 文內註 200/404 實證；automationId 三條與 CronList 逐字比對通過）。
- schedule-registry.md 初版已建 `ai-analysis/schedule-registry.md`（三條全名 + backlog-browser plist + 跨 repo 指針）。
- §5 七樣本對照（MOS-14 + AIR-13~17）與 §6 L1-L8 落地清單 + sync-sources 三類掃描已入 design.md；術語 drift 掃描當前為 0（落地後才長新詞）。
- 待你審閱 design + 殼（http://127.0.0.1:6421/ai-rules/_tasks/09-03-backlog-governance-design/index.html）後，執行結案兩步與任務家遷 done/。

接管記錄（09-03 晚，ZCode 接手 muse session 01a065fb）：muse 後段討論已定案但漏同步的四項，本 session 已補齊——①兩層判定時點前移到承諾時（升卡跑 /execution-plan 分級；起手式只讀卡知形態不重判；執行中 scope 漲→升 EP 是逃逸口）——同步 ep S1 2.3/2.5/2.7、design §2.3/2.4/2.6、殼 s3、card-lifecycle 圖（重構：規模判定門→EP 分支→建卡，vision-review 4/4 PASS 確認分岔位置）②design §3 出口改兩腿（post-build 預設清第一腿＋夜掃兜底；muse 只寫進 ep SM-5 與殼、design 本體漏）③handoff --save 退場（SM-12 改 --comment）＋.review arch 評可退場——同步 design §3.1/3.2/3.3、ep S2、relay 圖（tag 為 fine-detail 層初始視角不顯示，語義由註解卡承載，grep 實證字串在場）④落地清單 L2/L4/L5/L6 改寫＋新增 L9（post-build skill 收尾段）→ 全文 L1-L9。側項：backlog/config.yml 的 Pending Review 狀態欄無授權無引用→已還原；repo 根 `.taskwright/`（worktree-guard/warn hooks，非本弧產物）留置待 user 裁決。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
設計文件兩族治理＋registry 初版＋七樣本回歸＋L1-L9 落地清單，接管修正四處同步後定稿
<!-- SECTION:FINAL_SUMMARY:END -->
