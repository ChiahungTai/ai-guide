---
id: AIR-93
title: muse 原生 session-end 記憶寫入繞閘——governance 覆蓋缺口修復（mosaic 證據鏈承接）
status: In Progress
assignee: []
created_date: '2026-09-14 03:13'
updated_date: '2026-09-14 04:59'
labels: []
dependencies: []
references:
  - ai-analysis/_tasks/09-14-air93-muse-session-end-bypass/dossier.md
ordinal: 79000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
〔human-summary〕mosaic 發現 muse 在 session 結束時會用「非 tool 呼叫」的原生路徑直接寫記憶池，繞過我們的 governance 閘（閘只能攔 tool 呼叫）。這張卡先確認機制，再把閘的覆蓋補起來或加上偵測網。

〔baseline：ai-rules main @ 807ace5〕證據源＝mosaic_alpha 池兩檔 mtime 2026-09-14 10:43:51（model-quota-status.md／model-routing-four-family-comparison.md，同秒批量寫入）晚於 governance tool deny 10:41:54、無 inbox receipt；mosaic 側 journal 有完整證據鏈（讀 mosaic_alpha .agent-tmp/ 或向 mosaic session 索引）

〔已決策勿重辯：①缺口成立——PreToolUse 閘只能攔 tool 呼叫，原生 session-end 寫入路徑不經 tool 層（mosaic 實證）②本卡歸 ai-rules（plugin 與治理設計所有權；mosaic 不改 ai-rules 已聲明）③修法候選待機制確認後裁：muse 設定關閉原生寫入（查 meta 鏡像 configuration.md）／sandbox .agents read-only 與 --yolo 的相剋（implement 委派一律 yolo 是 user 通則，動不得）／偵測網（池條目無對應 inbox receipt＝flag，併 memory-audit 機械層）④修復不得破壞 implement 委派 --yolo 通則〕

〔驗收：①機制確認落卡（muse 原生寫入的觸發條件與路徑，文檔或實測證據）②閘覆蓋修復落地或偵測網上線（擇一或並行，user 拍板）③重放驗證：模擬 session-end 寫入被攔/被偵測④文檔同步（README 運維節＋AGENTS.md Muse memory 段若受影響）〕
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[09-14 機制確認 AC① 中間檢查點] 調查完成（文檔+binary+session log 鑑識+canary 自然實驗+bridge runner 源碼）：①寫入者=muse runtime teardown 行為（session.end 後 103s、log 已關、零 tool 事件、5 檔 working tree 直寫無 commit）②PreToolUse 天然攔不到＋sandbox 只罩 shell tool（且 yolo 全關）＝兩道既有防線皆無效 ③官方設定面無開關；binary 候選 env var MUSE_EXPERIMENTAL_MEMORY_REPOSITORY_SYNC 語義未證（bridge runner 無注入、unset 仍寫入）④非每 session 觸發（canary 零寫入）——觸發條件 H1(memory 意圖)/H2(池在場) 未區分 ⑤SessionEnd hook observational＝偵測可行攔截不可行。修法評估＋討論問題 Q1-Q5 見 dossier：ai-analysis/_tasks/09-14-air93-muse-session-end-bypass/dossier.md。下一步：codex+5.3 雙討論收斂修法（user 09-14 指令）

[09-14 雙討論收斂（user 指令：調查好與 codex+5.3 討論後定修法）] codex advisory job-mu0oz3v8-pi9rat（chatgpt-web/high）＋GLM-5.3 judge job-mu0oz4ai-t4rs7o。兩家獨立收斂：①主防線＝池 state 對帳網（非事件攔截）——5.3：git delta 對帳掛 memory-audit 機械層（全樹含索引、基線＝上線 commit、AC 措辭『結算時對帳』）；codex：approved-state reconciliation 為 correctness boundary（cutover baseline、禁 receipt 回填）——調和＝池已是 git repo，git HEAD 即 approved baseline，porcelain delta 即偵測面；威脅模型通案化（一切無收編池寫入，不限 muse）②SessionEnd hook 降級 telemetry/早報（兩家都抓到時序缺陷：hook fire 早於寫入 103s）——v1 不做③env var MUSE_EXPERIMENTAL_MEMORY_REPOSITORY_SYNC 須 live probe 實證（字串存在≠disable 語義；disposable fixture A/B），證實後 bridge 注入＝prevention 噪音抑制、明文非防線（bridge 只罩 bridge session、TUI 直開不保護）④sandbox ③棄⑤H1/H2 觸發條件不值得單獨花額度（state invariant 條件無關）⑥驗收兩層＝synthetic regression（無 receipt 池寫入→detector fire）＋一次真 muse session-end replay（disposable fixture）⑦codex 抓到 dossier 證據錯誤已修：10:43:51 波實為 3 檔（含 tpex＝被拒工作單目標條目——teardown 套用被拒內容證據更強），08:45:48 為同日另一波 3 檔——非孤立事件。待 user 拍板 AC② 修法後實作（跨 repo 面：bridge 注入＋bridge-exit 對帳列 delegate-bridge followup）

[09-14 實作結算：對帳網 v1＋synthetic 層（user 拍板範圍）✅] scripts/reconcile_memory_pool.py（唯讀偵測器：marker 三態同源 hook、porcelain delta 即 flag、fail-closed 三態 git 缺席/pool 無 git/marker malformed、--json 機器面、exit 0/1/2 契約）＋tests/test_reconcile_memory_pool.py 21 條（雙 layout nested/flat、索引污染 R3、gitignored 豁免、唯讀保證、CLI exit code）。TDD RED（collection error 證 missing）→GREEN 21/21；全量 417 passed（基線 396＋21）。真池 smoke：mosaic clean（regen 後）；ai-rules dirty 22 條（真實欠結算流入——通案語義 flag 交 consolidation 六問，非本卡處置範圍）。掛點＝consolidation 開頭＋memory-audit 機械層（AC④ 文檔同步時寫入 ops 慣例；muse-plugins/ package 檔禁動——README 在 package 內會觸發 def_hash 重釘，併最終批次）。待：live replay probe（下段——disposable fixture）＋bridge 注入（跨 repo followup）

[09-14 post-build 鏈結算 ✅] codex fresh-eyes review（job-mu0q2pim，chatgpt-web/high）：needs-fix 6 findings＋caller 自抓 F7（pool 整刪早退 clean）→帳本 .review/main.md 7 條。GLM-5.3 judge（job-mu0qba26）：7/7 全採納零否決、修正許可 GO（逐條 hook 單一源行號覆核，非順勢）。修正迴圈 1 輪收斂：F1 --untracked-files=all／F2 broken-symlink marker fail-closed（-e -L 同源）／F3 protocol 1.0/1e0 數值相等（jq 同源）／F4 porcelain XY 兩欄 R/C 配對＋malformed loud／F5 GIT_OPTIONAL_LOCKS=0 唯讀保證／F7 pool-absent 走 repo_root rev-parse（nested 極限 docstring 如實標註）／F6 六釘測試。驗收：reconciler suite 31/31＋全量 427 passed＋F5 index-hash 機械複驗；帳本 7/7 verified。池 consolidation 補審（user 指令）同段完成：22 條流入全 CC/ZCode provenance（零 muse 直寫）→commit 6947df6＋2 筆 probe canary rejected＋投影 regen B gate 綠→對帳網重掃 clean。遺留待辦：①live replay probe（env var A/B＋真 teardown）②bridge 注入＋bridge-exit 對帳（delegate-bridge followup）③AC④ 文檔同步（muse-plugins README 動觸 def_hash 重釘併最終批次）④池 reference_muse-code-cli-facts 12,374c 超閘待壓縮＋project_* 7 條終態收斂（弧結案蒸餾時點）

[09-14 live replay probe 結果——正控制失敗，誠實記錄] Arm 1（positive control，job-mu0qou9y）：disposable fixture（nested pool＋marker＋memory-intent 工作單）＋bridge muse task --trust-workspace --yolo——hook deny＋inbox 代存精確重現（receipt 20260914-122517）但 session.end 後 240s 窗零池寫入（porcelain 0 行＋reconciler clean）；session log teardown 段靜默與 incident 同形態。Arm 2（SYNC=0）取消——正控制失敗下 A/B 無對照意義，省額度。觸發條件假說收窄：表面條件（yolo＋池＋edit_memory deny＋memory 意圖）不充分——候選殘餘：工作單內容豐度（incident 是 MOS-104 蒸餾稿）/上游灰度 rollout/池歷史差異，皆無法外部區分。AC③ live 層覆蓋如實：①detector 對真實未收編 delta 會 fire＝已驗（ai-rules 池 22 條真實流入 flag exit 2）；②真 muse teardown 寫入觸發重放＝未驗（重現失敗）——但偵測路徑寫入者無關（porcelain delta 通案），synthetic 31 條＋真實流入兩層覆蓋。重試決策交 user：每次 probe 一發 muse 額度、重現率未知（可試蒸餾稿形態工作單）。probe fixture 保留 .agent-tmp/air93-probe/ 供後續重試

[09-14 probe 清場＋檢查載體查證] user 裁定驗完清理：probe fixtures（arm1-ws/arm2-ws/workorder）＋/tmp 驗證 scratch＋8 個工作單/回覆暫存全刪（內容已蒸餾卡＋ledger jobs/*.jsonl 持久）。重試需依 dossier＋卡配方重建 fixture。檢查載體查證：ai-rules workspace 有排程承載——schedule-registry 條 1（automation-751ecce2，每晚 23:40 memory 收斂波＋inbox 消費，波前 porcelain 檢查在流程內）＋條 2（automation-fed036ff，週日 23:00 治理看照，watchdog 含雙池 porcelain-vs-receipt）——但 reconcile_memory_pool.py 尚未機械接線（夜波走 memory-audit 配方的 LLM 判讀形態）；本 workspace（ai-lifecycle）CronList 空＝ZCode automation workspace 綁定，接線須 ai-rules workspace session 或改 skill 配方
<!-- SECTION:NOTES:END -->
