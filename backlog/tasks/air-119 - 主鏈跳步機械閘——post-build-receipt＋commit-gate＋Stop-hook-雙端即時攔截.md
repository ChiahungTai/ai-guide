---
id: AIR-119
title: 主鏈跳步機械閘——post-build receipt＋commit gate＋Stop hook 雙端即時攔截
status: Done
assignee: []
created_date: '2026-09-17 08:35'
updated_date: '2026-09-17 11:21'
labels: []
dependencies: []
references:
  - hooks/post-build-gate.py
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
implement build 收斂後直接停、跳過 /post-build——LLM 紀律失敗（0917 實例：三 commit 完即回報等 user）。落地機械閘兩件：A＝事後收口（/post-build 末尾寫 receipt＋/commit 新增階段 2.95 檢查 receipt）；B＝即時攔截（Stop hook 於卡 branch 且無有效 receipt 的 turn 結束 block 續跑——CC＋ZCode 雙端註冊）。豁免（窄、純機械）：branch=main；或 vs merge-base 改動全 .md（純文檔／卡務／排程 session）。ZCode Stop hook block 續跑已 POC 實證（0917——sentinel mtime＋reason 注入＋3 次上限，證據 .agent-tmp/stop-poc/）。
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【spec gate——已決策勿重辯（0917 user 工單＋POC 實證）】baseline＝main@收線後 HEAD（開工重刷）。八點已決策：①問題＝implement 跳過 /post-build（0917 實例三 commit 即停）②ZCode Stop hook block 續跑已 POC（fire/block/reason 注入/#N 計數/上限 3——證據 .agent-tmp/stop-poc/ read-only 禁刪）③豁免＝branch main 或 vs merge-base 全 .md（純文檔／卡務／nightly 排程 commit 涵蓋）④ZCode 無 SessionEnd——B 只掛 Stop⑤A/B 共用判定函式單一源（hooks/post-build-gate.py：純機械 git＋檔案存在、<1s、內部錯誤 exit 0 fail-open、arm-gated 單發 self-limiting）⑥receipt＝.agent-tmp/post-build-receipts/<branch>.json（branch/head_sha/legs 結算/completed_at/report 指針；head≠HEAD＝stale 要求重跑；7 天清淤可接受）⑦/post-build 階段 6 末寫 receipt；/commit 階段 2.95（2.9 後）無 receipt→fail-loud 指引、stale→列差異⑧B 註冊 fold-in 序列保 AIR-116 byte-parity：先 live 註冊（ZCode hooks.events.Stop＋CC settings hooks.Stop，備份＋parse 驗證，ZCode 只動 hooks 子樹——或直接走 governance installer --surface hooks）→再更新 manifest [surfaces.hooks].scripts＋模板→installer --check 綠。已決策：live config 禁殘留 stop-hook-poc（已拆勿復原）。實作約束：動 skill 檔前載 instruction-writing；完成後 fresh-eyes 審查腿（gate 面＝非 lite）；建議 tier 一般以上。AC 草案：A＝docs-only 不擋／code 無 receipt fail-loud／有 receipt＋head 一致通過／stale 擋並列差異；B＝卡 branch 無 receipt turn 結束 block 一次（reason 可見）／post-build 後放行／main·docs-only·排程不觸發；CC＋ZCode 各一輪 live 驗證 receipt 附完成報告。同步點（muse 腿補抓）：implement SKILL.md 六處、handoff 承接面、blueprint workflow、guide bundle 側。

0917 實作結算（待審查腿＋live 驗證後收線）：①B 腿設計具體化（spec ⑤ arm-gated 單發→per-branch 終身 block 預算 2——『弧完成』無法機械判定，逐段結算弧的每輪 turn end 都會命中；預算制把噪音上限鎖在 2 次，reason 自帶『弧未完成可忽略』指令；receipt 有效即清預算＝新工作新預算。此為 spec 具體化非重辯，依 EP amendment 慣例記 old/new/reason）②hooks/post-build-gate.py 落地（3.9 相容、A/B 共用 evaluate()、fail-open、四條件判定＋receipt 三態）——fixture 測試 8/8 雙解譯器綠（python3 3.9.6＋uv 3.14，.agent-tmp/air119/test_gate_fixture.py；t4 首敗為測試序型 bug 非產品 bug）③fold-in 走 installer（工單原序列退役，implementer ①號建議採納）：manifest scripts＋cc/zcode 模板加 Stop group→install.py --surface hooks 落 live（CC/ZCode written、codex noop、備份＋preimage 免費拿）→--check 五面 parity 綠 exit 0→symlink 完好＋JSON parse 驗證④skill 編輯：/post-build 收尾報告加 receipt 寫入行、/commit 新階段 2.95（receipt 閘，判定單一源指針 evaluate() 禁重寫）；同步點四處（implement/handoff/blueprint workflow/guide）掃描＝描述鏈引用無矛盾，免改；guide bundle 未動免重部署⑤788 pytest 基線綠。待辦：fresh-eyes 審查腿（背景執行中）→findings 處置→live 驗證（ZCode 新 session block 兩次→post-build 寫 receipt→放行；CC 一輪）→commit gate。回執四欄（初稿，收線時定稿）：classification=boundary（gate 面 instruction 語義＋hook）／review=fresh-eyes 背景腿執行中＋intent 本 session；跨家族外審腿待額度評估（不足則依 model-routing 記錄降級由 in-harness 雙 context 承接）／session-freshness=fresh（POC 與設計脈絡全在本 session）／deployment-surfaces=pending（live 註冊已落，行為驗證未跑）。

0917 fresh-eyes 審查腿回報：9 findings（2🔴2🟡5🟢）全數 confirmed、全數修復，修後 fixture 回歸 16/16 雙解譯器綠＋pytest 788。要點：F1🔴生命週期 off-by-one（post-build receipt 寫於 commit 前→/commit 推進 HEAD 必變 stale→正確走主鏈的弧必被誤攔）→修法＝/commit 階段 6 成功後機械刷新 receipt head_sha＋stale reason 補逃生口；F2🔴slash branch（feature/x）marker 路徑缺中間目錄→預算防線靜默失效→修法＝_branch_key() 統一 → 編碼（receipt＋marker 雙側）；F3🟡commit skill 捷徑模式枚舉補 2.95；F4🟡A 腿 stringly-typed→新增 --verdict tri-state CLI（2.95 消費 JSON，禁 import 連字號檔名）；F5-F9🟢docstring／缺 head_sha 歸 missing／trunk 硬編碼限制文件化／detached HEAD 豁免／ensure_ascii 防禦。審查中自測額外抓到：_budget_consume 自截斷 bug（"w" 開檔截斷後同檔讀→計數恆 1→預算永不到頂）——測試序型＋產品各一處學費。回執四欄更新：review=fresh-eyes 獨立 context（85 萬 tokens／21 工具調用／sandbox 實證，9 findings confirmed）＋intent 本 session；跨家族外審腿未派——顯式記錄降級（本日多弧並行額度評估），由 in-harness fresh-eyes 完整承接（instruction-writing 落地前審查閘第 2 點）。

更正補記：F2 編碼細節＝branch 進檔名前把斜線替換為雙底線（_branch_key 函式，receipt 與 marker 雙側同函式）——前文『統一 → 編碼』因 shell substitution 缺字。

0917 live 驗證 ZCode 腿證據（落盤）：Stop hook 於新 session（builder session 結束後重開、config 由 installer 落 live）turn end 實際 fire＋block——reason 注入可見、預算計數 #1 顯示、branch=air-119 判定正確（領先 main 1 commit＋無 receipt→block）。機械證據＝Stop hook additional context 注入本 session（『本弧尚無有效 post-build receipt（branch=air-119，領先 main 1 個 commit）…此提醒有預算上限』）。剩：/post-build 寫 receipt→turn end 放行驗證；CC 一輪待跑。

0917 19:10 讓位聲明（跨 session 協調）：偵測到並行 session 於本共享 WT 實作卡驅動豁免（hooks/post-build-gate.py＋skills/commit/SKILL.md 已 staged 未 commit；AIR-122 卡已開）——本 session /post-build 暫停、不寫 receipt（寫了必 stale）；A 腿 2.95 會強制 commit 者自跑收尾鏈，收尾歸 commit session 承接。本 session 既有產出：①block #1 live 證據（前則 notes）②fresh-eyes F1/F2/F4 修復抽查機械證實（commit SKILL:190 刷新／_branch_key 雙側／--verdict CLI）③tests/test_post_build_gate.py（untracked）＝fixture 提煉的永久場景測試，現編碼舊豁免矩陣——卡豁免落地後需補 fixture 卡（backlog/tasks/card-x - *.md，照 .agent-tmp fixture 75-76 行模式）才綠：可採納改寫或刪除，禁留紅燈入 suite。賽跑時間線證據：19:00 舊版 hook fixture 16/16 雙解譯器綠→19:01-02 對方 stage＋更新 fixture→19:01 pytest 對新版 exempt 而敗（非測試缺陷）。Stop hook 預算 2/2 已耗畢——本 branch turn-end 靜默＝設計行為非閘故障；receipt 寫入後自動清預算。

0917 補記（前則 append 因 backlog CLI 不支援 --quiet 未落地）：設計修訂三落地完成——_card_exists 改 backlog CLI task view 權威（probe：小寫/大寫 id 解析 exit 0、查無 exit 1、耗時 200ms）；tests/test_post_build_gate.py 對齊新語義（fixture 由真 CLI init+create 建、branch=CLI 配的 id 小寫、無卡豁免案例 t9、F2 降函式級直測 _branch_key＋預算讀寫）789 全綠，已 amend 進 5169fec。協調收斂：讓位聲明所指並行 writer＝本弧 owning session（amend 的 add→pre-commit 24s 窗口被觀察為 staged；HEAD 已推進 5169fec）；殘項對帳——test file 已由 owning session 重寫並 commit（『舊豁免矩陣』狀態失效，勿重做）；receipt 本補記後寫入（head=5169fec 版本）。

0917 live 驗證雙腿完成：①ZCode——接手驗證 session（gate 註冊後新開的真實 session）turn end 被 block #1（reason 注入可見、預算 #1），第二次 block 後預算 2/2 耗畢轉靜默（設計行為）；②CC——headless claude -p 實測：暫移 receipt 後 Stop hook 觸發 block ×2（budget marker=2 機械證據）、第三輪放行 exit 0，receipt 還原後 --verdict=ok 並清預算。AC 雙端 live 驗證齊備。本弧收線：結案兩步＋merge。蒸餾：無相關 memory 條目需處置（知識已住 repo：gate 腳本＋卡 notes＋POC 證據）。
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
主鏈跳步機械閘落地——post-build receipt＋commit 2.95 閘＋Stop hook 雙端（ZCode 真實新 session block 實證＋CC headless block ×2）；fresh-eyes 9 findings 全修；無卡豁免＋backlog CLI 卡判定＋block 預算 2 自限
<!-- SECTION:FINAL_SUMMARY:END -->
