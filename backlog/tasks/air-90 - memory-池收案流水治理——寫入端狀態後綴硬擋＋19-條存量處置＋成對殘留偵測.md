---
id: AIR-90
title: memory 池收案流水治理——寫入端狀態後綴硬擋＋19 條存量處置＋成對殘留偵測
status: Done
assignee: []
created_date: '2026-09-13 22:44'
updated_date: '2026-09-15 14:34'
labels: []
dependencies: []
ordinal: 76000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕
夜間六問抽檢三晚顯示：收案 session 把「弧進度/收案記錄」寫進 memory 池（Q1 違規 87.5%→100%），昨晚 19 條待處置、另有 3 對同名新舊檔並存。這卡做四件事：寫入端把帶狀態後綴的新條目擋在門外、把 19 條存量逐條處置（可留教訓留、接續事實搬回卡）、夜波加成對殘留偵測、結案流程加清池檢查項。經 GLM 調查＋codex（chatgpt-web/high, job-mu0bz05t）討論，方向已定。

〔baseline：ai-rules 97e17d5；memory 池 git 0d9b7fd〕
〔已決策勿重辯：①寫入端主槓桿＝狀態後綴 deny——檔名 stem 以 -pending/-inflight/-in-flight/-landed/-done/-closed 結尾的新建條目硬擋（exit 2）；exact stem suffix 非 substring（「pending-order-behavior」類教學/引用命名不擋）；只擋新建、既有檔編輯放行（留人工修復路）；project_* 全擋已否決（常駐集有合法 project 事實）②開弧 pending 條目＝port-to-card-then-delete：接續事實先搬對應卡 notes 再刪池檔，HOLD-until-close 否決（＝延後污染）；port 由 owning session/接手者做、夜波 cron 不自動搬；治理報告留 ported_to audit 行③19 條批量處置＝專責 session＋user 核可，非週日 cron——cron 角色＝detect/report/queue，禁 judge/rewrite/delete（審計獨立）；「34 條累積」係波報告重複計數（前兩晚 14 條已 bee40fa+286b037 白天人裁處置），實際待處置 19 條（機械枚舉 2777de3..756ef98 project 新檔）④成對殘留根因＝memory 是最低摩擦的自動載入接續帳本（派工寫 -pending、收案因禁加段另寫 -landed 無人清舊檔）；「缺 checkpoint 載體」不另建新基礎設施——.at-contexts/EP 結算/卡 notes/journal 既有＋session 開場導引已上線，以導引被遵守＋硬擋收口⑤stderr 送達（EP A3 deferred）驗證平行補做、不擋硬擋——硬擋 invariant＝「這名字代表狀態非知識」，不依賴提醒送達；軟閘效果判「unproven/likely insufficient」非「stderr 無效」⑥codex 長線提案 kind=lesson|decision|fact schema 欄＝緩——metadata 填寫回歸語義判斷非強制，留作 triage 加速器另案評估〕
〔驗收：①hooks/block-memory-index-write.py 加 exact-suffix deny＋單元測試：六後綴新建擋、substring 反面例（*-order-behavior 等）與既有檔編輯放行（紅→綠）②19 條處置落池 git：逐條處置 commit＋audit 行（removed reason/ported_to）；開弧三條（AIR-81/85/89 相關 pending）port 進對應卡 notes 後才刪；處置後 inventory 條目數下降且 --check 綠③夜波 cron prompt 加 twin 偵測腿（同 stem 異狀態後綴並存→報告清單）並 CronUpdate 完成④kanban-board SKILL.md 結案/弧結案蒸餾段加「rg 池內本弧條目→逐條處置或附理由」清單項⑤stderr 送達 probe 實測落地，結論記錄（送達/未送達＋證據）〕

範圍：hooks/block-memory-index-write.py＋tests／memory 池 19 條處置（池 git commits，非 ai-rules repo）／host 側夜波 cron prompt（CronUpdate，repo 侧無檔）／skills/kanban-board/SKILL.md 清單項／stderr probe（一次性實測，結論入 EP）。錨點：ai-analysis/nightly-convergence.log 09-13 段（100% 實證＋錯誤的 34 條累積說）；fabf4e7 處置鏈先例（刪 5/重寫 1/併 1 淨瘦 18.8K）；AIR-83＝偵測側姊妹卡（夜波初篩 script——本卡是其決策②切出的寫入端單案）。
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
併入 AIR-100（P3 寫入防護＋P2 存量對帳）——memory 域整併單一治理弧防 wave/治理檔互踩；原 AC 由 AIR-100 A3/A2 承接，未動工即併、無遺留工作。
<!-- SECTION:FINAL_SUMMARY:END -->
