---
id: AIR-54
title: 跨池記憶主體遷移——muse project memory 一等公民＋CC/ZCode symlink＋inbox 寫入流（含 mosaic 移植）
status: Done
assignee: []
created_date: '2026-09-09 02:47'
updated_date: '2026-09-09 23:01'
labels:
  - memory
  - governance
  - cross-harness
dependencies: []
references:
  - >-
    http://127.0.0.1:6421/viewer/_md-viewer.html?p=/ai-analysis/_tasks/_archived/09-09-memory-spine-migration/ep.md
  - ai-analysis/_tasks/_archived/09-09-memory-spine-migration/ep.md
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔baseline：09-09 實驗鏈全驗——muse project scope 注入（14 檔 copy 投影實測：MEMORY.md 全文＋清單列 13 檔）、hooks deny 契約（hookSpecificOutput/permissionDecision，擋 add_memory 實證）、add_memory 裸寫（純 content 零 frontmatter 不動 index）、memory 機制拒 symlink（read_memory 報錯）；材料＝.agent-tmp/muse-hooks-findings.md＋poc_muse_projection.py〕目標：記憶主體遷至 <repo>/.agents/memory/（muse project memory），CC 端 ~/.claude/projects/<encoded>/memory 換目錄 symlink 透明讀寫，ZCode 既有鏈雙跳；muse 從唯讀消費者升一等公民（CP 最高 runtime 零適配），寫入流走 inbox（hook 導流→CC/ZCode consolidation 補 frontmatter＋六問）。〔已決策勿重辯：①主體＝project scope repo 內＋gitignore（非 personal_project——路徑文檔化合約、不怕 muse 重置私有資料；user 09-09）②寫入流＝inbox 先行（「先 inbox 看看」，直寫主體留後議）③一張卡含 mosaic 移植④與 AIR-48 平行推進——muse 品質閘引用其三判準（純機械/單入口/無語義例外）⑤copy 投影過渡形態遷移完成即退役⑥AGENTS.md「Muse memory 唯讀」段隨弧改寫（muse 成受約束寫入者）〕〔驗收：①三端等距驗證——CC/ZCode 開場經 symlink 載入主體如常、muse read_memory project scope 可讀 ②池 git 歷史連續（.git 搬家後夜間收斂波正常跑）③治理路徑全同步（generator/Stop hook/夜間 cron/telemetry——rg 掃描舊路徑零殘留）④muse hooks 品質閘＋inbox 流落地可跑 ⑤mosaic 多 worktree 解法落地（owning 線實體＋其餘 symlink）⑥過渡投影退役＋AGENTS.md/條目/文檔同步〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
〔開工 handoff 09-09 晚——AIR-50 閉環後 center 交接〕排序拍板不變（51✓→53✓→50✓→**54 開工**→52）。baseline：8c4fa14（main HEAD；最後一顆 86e0602 已 push、8c4fa14 待 push）。開工起手式：checkout -b air-54（自 main）→ task edit air-54 -s In Progress → 開工雙 ref → code-reality snapshot --label air-54（勿跳——handoff 續跑弧 4/4 漏這步實證）→ 讀 EP 進 /implement。EP＝本任務家 ep.md（167b87d 定稿——獨立 context review 16 findings 全 apply；S0 段已砍〔user 討論定案〕、S1 手術程序＝mv＋側備份＋併發 guard、S3 hook 絕對路徑、SM 擴至 14 場景）。已決策勿重辯：①Muse 在本 repo 只讀不寫（禁 add_memory/edit_memory——共用池寫入由 ZCode/CC 側）；②memory spine 住 ~/.agents/memory-spine/（plain md＋frontmatter，條目 ai-rules 側寫入、各池 generator 認養 routing 行段）；③過渡形態：.agents/ 投影由冪等腳本 .agent-tmp/poc_muse_projection.py 刷新（結案蒸餾後手動重跑）；④23:40 cron 動檔順序 54 先改路徑 52 後改口徑。在飛事項：AIR-50 審計弧的 muse 跨家族 review 腿背景執行中（bridge job——findings 回來若有採納項由現 session 修正補 commit，不阻塞 54 開工）；hook live 觸發驗證＝下個 CC session 的 hook log（memory-hook-events.jsonl 首筆）。tier：主弧 GLM in-harness。workspace：ai-rules 主 WT（main）。卡歸屬：AIR-54 本 repo board。

〔開工 handoff 09-09 command center〕S1-S5 本 session（S6 mosaic 後延另 handoff）。baseline d430b0f。前置檢查：AIR-50 muse 跨家族補審是否收斂（未收斂→先做只讀盤點、勿進 S1 手術）。起手式：checkout -b air-54 → In Progress → 開工雙 ref → code-reality snapshot --label air-54。S1 手術時序避 23:40±30min；whole-rename＋側備份＋E2E 矩陣全綠才刪 .bak（EP 內程序自足）。muse bridge task ×3 驗證點（S1 read_memory／S3 攔截實測／recall sentinel）。勿重辯：主體 project scope／inbox 流／WAL light／CAS v1／mosaic 直寫廢止。收尾含整體記憶機制審視（含 ZCode）——EP 收尾步驟 6。

〔Muse 續跑 09-09 15:00-15:30——ZCode sess_c6f260d0 停於 Desc gate 後無活動〕recall sentinel 綠（自然腿 _inventory 定位→讀 body＋顯式腿 read_memory 逐字一致，一等公民 gate 關閉）；收尾5 tests/test_muse_memory_inbox.py 新增 3 tests 綠（同族 18 綠）；收尾6 drafts/draft-4 落地（三端鏈路總圖＋ZCode 待辦＋P1-P4）；收尾1/4 零改驗畢；S5 舊敘述 rg 零殘留。待：今晚首波驗證→刪 .bak；post-build 鏈＋commit 待 user 確認。

〔T3 終審返修 09-09 16:00 Muse〕7 findings 裁決 6✅1⚠️全落地：T3-1 hook lexical gate＋測試檔 7 綠（同族 90 綠）；T3-2/3 contract 文字硬化（lstat＋尾slash＋inbox 回歸樣本）；T3-4 Phase0 第二檢查＋P5 執行者缺口（dirty-sensor live 未驗、daily-maintain 無排程——judge 比原文深一層）；T3-5 sentinel 重做（canary 2.3GB/483/tool_usage＋telemetry oracle PASS＋快照缺席 negative control）；T3-6 行為釘測試；T3-7 大小寫註記（池全ASCII）。EP 補第三輪紀錄＋draft-4 補 P5。待：今晚首波、P5 拍板、commit 確認。

〔T3 複審返修 Muse〕T3-1b：alias/secret.md 中間段穿透反例成立（舊邏輯覆現確認）→hook 補 intermediate 逐段 lstat＋2 測試（alias 反例＋nested 正例），測試檔 9 綠、同族全綠；T3-2/3/5/6/7 複審關閉；T3-4 維持開放＝P5 已知殘餘。EP/draft-4 同步。待：今晚首波、P5、commit 確認。

〔T4 接合處審查返修 Muse〕2 findings 全✅：T4-1 異常篩移到流入快照提交前（三 allow＋quarantine 停波；驗證待首波）；T4-2 合約收緊池根 basename＋hook 跳過 slash enrichment（T3-1b walk 移除更簡）＋nested 測試翻轉；ruff PLC0415 修畢（93 綠、ruff/diff-check 綠）。EP 補第四輪。待：今晚首波、P5、commit 確認。

〔註記更正〕前兩則註記有兩處已過時：①daily-maintain 執行者歸屬改為未驗證（skill 記 23:20 vs registry 無此條，AIR-52 解綁處理中）——前稱無排程執行者收回；②T3-1b walk 已被 T4-2 slash 規則取代移除。Phase0 注記與 draft-4 P5 已同步修正口徑。

〔多機支援 Muse〕clone 支援落地（未 commit）：setup-memory-symlinks.sh（命名規則雙實測＋dry-run＋bak）＋verify-memory-topology.sh（只讀＋smoke）＋MULTI-MACHINE.md runbook＋5 測試（98 綠同族）；深層限制＝雙池無同步、主機模型。commit 包再擴大，待你那句。

〔收尾補記 09-09〕draft-4/draft-5 出處：muse session（09-09 下午）順產——draft-4＝EP 收尾步驟 6 的審視產出、draft-5＝pending 讀取覆層設計定案（user 09-09 拍板「只做設計不寫程式」，AIR-57 建卡承接——5a6ce2e 建卡 commit 落 air-54 branch 為 muse 越界〔建卡紀律應在 owning 線〕，隨收尾 merge 進 main、message 已帶正確 id，歷史交 git log）；air-58 為獨立任務卡（非本弧）。post-build 三視角（primed/fresh/codex）22 findings 裁決全 apply——帳本 .review/air-54.md；VP3 recall sentinel 結論＝僅 explicit 過＝召回面受限（EP 風險 7 已補記）。

〔VP3 更正 09-09〕前則「僅 explicit 過＝召回面受限」為單腿結論——與 muse 15:00 工具鏈腿（_inventory.md 直讀→定位→讀 body，綠）合成後正解：一等公民 gate 關閉（observer 工具鏈召回可達）＋直達注入限清單內（深度記錄）。EP 風險 7 已更新。

〔AIR-54 收尾 handoff 09-10 CC〕S1-S5 已進 main（e417693）＋首波/驗證綠＋.bak 刪。收尾段＝①S6 mosaic 移植（EP :252-284 自足：前置 muse 自建三檔過六問併入或遷 processing→主體進駐 mosaic repo .agents/memory〔owning=main WT、版控排除沿用 exclude〕→CC dir 換 symlink→次 WT symlink F2 實測〔拒則顯性降級 read_file 絕對路徑〕→hooks.json+AGENTS.md+memory-policy.md 直寫政策改寫→夜波路徑比照 S2+repo 外 bundle G2-11）②SM-12：三端開場+WT inode 一致+夜波一輪③ai-rules 欠項×2：memory-audit SKILL 補「Inbox 消費」節（源=23:40 cron prompt 步驟 0）＋registry 條 4 重放（.agent-tmp/air-54-registry-row4-*）④EP 收尾步驟 1-5＋結案兩步＋弧結案蒸餾。開場帶一句：mosaic MOS-86 源卡結案回報（mosaic 側懸掛，errata 已閉環於 ai-rules main）。勿重辯：直寫 MLM 廢止、WAL=LIGHT、CAS v1、exclude 慣例不強推 gitignore。

〔CC 緊急補充 09-10——S6 基線漂移〕EP :258『muse 自建三檔』情報已過時：mosaic_alpha/.agents/memory/ 已進化為完整 B 形態治理池（_generate_index.py/_resident-set.md/_inventory.md/_audit-state.md＋數十條目，含 feedback-subagent-serial-background 等）——S6 前置處置（三檔過六問併入）須改為『既有治理池整體搬遷/對接』重新盤點，非三檔小併。已知一條漂移待修：project-memory-audit-advisory-only.md desc 稱『AIR-54 S6 主體進 repo』——S6 未收斂，宣稱過早。S6 session 動手前先 ls 池現況對帳。

〔CC 快訊 09-10 給續 session（sess_a167e4c3）——執行前必讀：世界已前進〕①結案兩步＋EP 歸檔 done/＋欠項② 已由 CC 補收（2d06dbb）：欠項②處置＝**作廢重放**（cron automation-d64fd994 已於 09-10 晨提前手動執行＋刪除——照原 diff git apply 會讓 registry 記不存在的 cron 造成週日比對 drift；已改更新時點歷史記載句存查）——**禁再 git apply air-54-registry-row4-pending.diff**。②欠項① skill Inbox 節已在場（對照 cron prompt 後預期零改或小補）。③前置 gate 已解除：air-66 弧已收斂（卡 Done、WT 回 main 乾淨）。④你的正當剩餘＝EP 收尾步驟 1-6（尤其步驟 6 三端鏈路總圖＋ZCode 待辦清點——提案落 drafts/）＋弧結案蒸餾三條（muse-memory-mechanism-divergence 終態化／muse-code-cli-facts 收斂＋S6 後形態／memory-cc-alignment-diagnosis 補 mosaic 新拓撲）。⑤卡已 Done——不重跑結案兩步；你的產出（總圖/清點/蒸餾）直接落檔＋commit（message 帶 air-54）。⑥mosaic 主體 git 基線 1e3da43＋收斂 3cfb464 供對帳。

〔AIR-54 蒸餾尾段 09-10 ZCode sess_a167e4c3——CC 快訊指派項全清〕欠項①：SKILL「Inbox 消費」節對照 23:40 cron prompt 步驟 0＝機械步驟零缺（WAL 三態/path contract①-⑥/CAS/六問/receipts/quarantine 全在場），小補一行 S6 消費端事實（memory_pack 1.1.1＝索引 120 行＋單條 8KB inline 超限僅列名＋deny 1.1.1 相容——寫入 Q5 尺寸判斷消費面）。EP 收尾步驟驗證：1/4 零改（skills/CLAUDE.md 索引層零涉池路徑；context-management pointer 語義未變）、3 SYSTEM-MAP 不存在跳過、5 test_muse_memory_inbox.py 10 綠；步驟 6 draft-4 修訂至 S6 後形態（總圖 muse 讀取分級＋mosaic 同構＋P1/P3/P4 ✅＋ZCode 待辦補 8KB 消費面張力註 AIR-69 承接）。弧結案蒸餾三條落地：divergence 終態重寫（清 09-10 過時「S6 未跑」段＋desc 懸空指針）、muse-code-cli-facts 補 S6 後形態＋AIR-66 改已落地、cc-alignment 補 mosaic 同構拓撲；池 regen 綠（resident 2,257/6,000、inventory 26,448）。池 git 不自行收斂（多檔並行流入，留今晚 23:40 波次快照）。

〔AIR-54 post-build 三路審查收斂 09-10〕flash fresh（5 sugg）＋flash primed（3 sugg，意圖九元素全 ✅）＋codex chatgpt-web/high（job-mtuou4f1-wt7hfk，Conditional Pass→1 Important）——0 Critical；採納 6：SKILL :80 校準（8KB＝消費端軟壓力非寫入閘、Q5 hard gate 12,000 不變、8K-12K 政策歸 AIR-69）＋:214 Q5 指針＋升版重驗錨；draft-4 :27 watchdog 口徑對齊 P5＋:34 8KB 單位語義未實測註記＋:42 P5 AIR-52 A1 已落地更新。reject 3（cron 五條措辭/跨池時刻/updated_date 時鐘）——前二轉 AIR-69 對帳清單（已落卡 notes）。帳本 .review/air-54.md（commit 後清）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
跨池記憶主體遷移全弧閉環：S1-S5 主體進 main（63a8a19 線——repo .agents/memory/ 主體＋CC/ZCode symlink＋muse inbox hooks＋WAL/CAS）；首波驗證 09-09 23:40 六判據全綠→09-10 晨 CC 提前手動執行（memory.bak 刪除閉環＋08:30 cron 收除）；S6 mosaic 移植由收尾 session＋mosaic mos-88 分工吸收（8e33163fe：inbox hooks＋AGENTS.md 觸發器；mos-88：池 B 形態遷移結案——S6 基線漂移〔三檔→完整治理池〕經 CC 緊急警訊正確處置）；欠項：skill Inbox 消費節已補、registry 條 4 重放經判讀作廢（cron 已刪，照原 diff 重放會造週日比對 drift——改更新時點歷史記載句存查）；結案兩步＋EP 歸檔 done/＋registry 記載由 CC 補收（session 遺留三件）。
<!-- SECTION:FINAL_SUMMARY:END -->
