# AIR-328：有事件才通知的監控契約

> **ep_type**: implementation
> classification: boundary — 跨 context 收取責任與控制面決策。
> 狀態：計畫審查中，未授權 worker 提前實作。

## 目標與既定裁決

使用者的問題是 session 被定時監控洗版。成功條件：一般監控使用既有 observer；無變化留在程序內等待，有事件才依真實 carrier 能力通知；沒有 after-turn delivery 的 carrier 誠實用活躍回合 bounded wait，或留待收入口。不藉 recurring automation 增加空回合。使用者明示的時間工作（包含 recurring 報表）不受此限制。

架構不是最小補丁：移除相互矛盾的 definitions，建立唯一 notification/delivery 契約，保留不同 domain 的 state ownership。GLM-5.3 初審與重评 job-mv6djzrv-3nlfkl / job-mv6dvbhz-u3ng2x；Muse 初審 job-mv6fgb9g-9d0wp0。原分析 ai-analysis/reports/2026-10-13-monitoring-architecture.md；逐項裁決 evidence/design-adjudication.md。使用者已同意「5.3, muse 審查過後，ＯＫ就開使實作吧，這次flash 實作 sol, muse 審查，你judge」。

不做：新增 daemon、统一 observer state/cursor、carrier adapter、SIGTERM reaper、自重啟避回收、143≈正常五小時回收推論、修改外 repo/plugin、全域禁 recurring。SC stub 規範來信不併本卡。

## 段落 0：現況、責任與依賴

已核 source：bridge-dispatch:46,51 的 heartbeat mandate、deep-work:71-85 三層標配、model-routing:332 起重複收法、mail-watch:57 普遍 exit-push 宣稱、mail_autoarm.py:181 的「已掛哨」假成功提示。hooks/AGENTS.md:50 與 test_mail_autoarm 對同一句有對應；voice-notification、skills/AGENTS、work-order/task-recovery 亦引用收法。文件拓樸透過 rg 查證；不將文本引用當 runtime graph。

既有機制：mail_waiter start/worker/stop/status＋per-repo generation/cursor、bridge_waiter fan-in 與 124 內消化、harness_waiter registry/attempt/timebox、mail_autoarm 唯讀 hook。保留其各自資料模型、退出碼與 stop 權威。當前支援活躍工具 bounded wait，未驗證的 after-turn delivery 標 unverified-by-live-trace。

| 責任 | 唯一 owner | 消費者 |
|---|---|---|
| 通知能力選擇／無事件不注入回合 | 新 skills/_common/waiter-charter.md | mail-watch、bridge-dispatch、agent-workflow、deep-work、autonomous-execution |
| collection-owner invariant／supervision 裁決 | skills/agent-workflow/SKILL.md | 上列 workflows、model-routing 指針 |
| Bridge receipt acceptance／transport 操作 | 已安裝 delegate plugin | guide 只引用、不重定義 |
| Mail 觀察／generation／游標與夜間上限 | mail-watch 與既有 mail_waiter | mail-handle、deep-work |
| Mail read／待回信／idempotent reply | mail-handle／duty_receive | 收信 owner |
| 時間排程工作 | 各排程 skill 與 carrier | user 明示時間工作 |

反補丁檢查：刪 heartbeat mandate 時仍保留 collection obligation、checkpoint、advisory、retry-safe fences；不可把有界收取改成提早結束工作。不刪服務合法時間工作或 child telemetry 的 heartbeat 工具。State 寫入面不變；hook 永不寫入或 spawn。新 charter 不可把 mail cursor 當 processing exactly-once key。

結構 evidence：建本 WT current-tree graph，查 hooks/mail_autoarm.py impact；producer 結果及 runtime source核查落 evidence，測試集合再以 literal 反查補足動態 import。無 fresh index 時標 unverified-by-graph，不能作負存在結論。

## UC／受影響面盤點

更新既有：mail 掛哨與恢復、bridge/原生 agent 收取、deep-work 自主執行、startup 缺哨提醒。新共用單元是 instruction charter，不是新 runtime service。相關舊卡 AIR-146/147/149/160/266/301/312/318/322 皆已 Done；搜尋未見本次架構重編排的 active owning card，建立 AIR-328。SYSTEM-MAP.md 不在場；不為本卡重造地圖。同主題 memory project_agent-liveness-handoff-pending 為 AIR-89 終態教訓保留，Codex 對池唯讀；不寫 memory。

預期寫入清單：skills/_common/waiter-charter.md、skills/mail-watch/SKILL.md、skills/mail-handle/SKILL.md、skills/bridge-dispatch/SKILL.md、skills/agent-workflow/SKILL.md、skills/model-routing/SKILL.md、skills/deep-work/SKILL.md、skills/autonomous-execution/SKILL.md；引用同步 skills/voice-notification/SKILL.md、skills/AGENTS.md、skills/_common/work-order.md、skills/_common/task-recovery.md；hooks/mail_autoarm.py、tests/test_mail_autoarm.py、hooks/AGENTS.md、scripts/AGENTS.md。文字 ref scan 可發現其他直接消費者，worker 提報再由 Marshal 判 scope；不修改 frozen 歷史報告。rules 若需新增唯一源指針必先報 scope，不能默默改全域 bundle。

## Scenario Matrix／凍結驗收（author_family=codex）

| ID | 情境／觸發 | 預期 consumer 行為 | 證據／oracle |
|---|---|---|---|
| TC1 | Codex 多顆長工、無外部 exit push，時間壓力＋既有三層規則＋便宜 cron 誘因 | 不建 recurring monitor；記 owner並活躍 bounded wait，不假稱 turn 後續跑 | user 原話＋fresh-context baseline/treatment action dry-run；不得冒充 live trace |
| TC2 | 既已授權 watch，使用者追問有沒有收信；state running/stale、marker absent | status不撤銷意圖；核當前state與owner，re-arm既有watch；不再次索取同意 | 歷史 H3 frozen corpus，及對稱 explicit stop variation |
| TC3 | 最新 explicit stop 或 desired stopped，僅 status 或 startup opt-in marker | 不自動 arm，status不變generation；後來明示start才可重新啟動 | 既有 mail_waiter stop/status tests；hook禁止副作用 |
| TC4 | 缺哨／stale＋valid marker的 SessionStart | advisory說明尚未掛哨；不可宣稱完成；無marker保持silent，malformed fail-loud | test_mail_autoarm 原測試和新增negative predicate；先RED再GREEN |
| TC5 | 多輪 timeout、事件重放、caller退出後恢復、雙arm與等待中stop | timeout內消化，domain身份不混用；requery不漏pending；mail可重喚醒但處置依S2冪等；bridge124不重派 | 既有 mail/bridge/harness suites選對case，subprocess整合測試，缺口顯式列出 |
| TC6 | 使用者明示每天報表 | 採時間排程既有入口，不以監控charter阻擋 | fresh-context nonmatch dry-run |
| TC7 | 143/空輸出/約5h | 不推固定正常收割；核state與權威死因再依domain流程 | counterexample dry-run、source review |
| TC8 | watcher fresh但沒有deliverychannel／native與external混合 | 只證observer最近活動；各自capability判定、路由正確收取owner | 本弧實際 bridge dispatch→wait→show 收線記錄；無跨carrier blanket宣稱 |

壓力與判分在 treatment 前凍結：TC1壓力＝快收線、沉沒三層配置、舊條文權威；TC2壓力＝多次追問、怕越權、stale顯示失效。PASS看選擇的操作，不看複述規則。基準已有 H3/Terra FAIL；本次以相同scenario/material輸入新舊arm各fresh context。provider失敗算INCONCLUSIVE，不retry挑綠；baseline未失敗不宣稱因果改善。activation面變更用positive/nonmatch測實際載入，若僅frontmatter機械縮述则聲明直接載入測試，不能稱desc觸發。

## 段落 1：契約遷移

Context：TC1/2/3/5/6/7/8。Read本EP、裁決、所有受影響原文。Flash只執行已定設計，遇新boundary提問不自決。

修改要點：charter定觀察與投遞分界、能力選擇、無事件留observer、當次 exposed capability 優先／歷史表僅 prior；有confirmed event route才用，否則活躍boundedwait，無路徑留durablepending＋限制。charter引用 collection-owner＋各domain，不複製其判斷。將model-routing收法決策樹刪成navigation，原transport知識指plugin。各skill刪換名三層／mandatory heartbeat與通用exit-push；description與引用一起同步。

watch intent priority：最新明示stop優先；較新的明示start可覆蓋。當次explicitwatch或已核實的prior running intent延續；status只讀、不授權亦不撤銷。marker僅opt-in advisory；absent不抹除explicitwatch，malformed使autoarm提示fail-loud。watcher freshness不證callback接線。Domain annex只解釋各自rearm/replay/stop指向，不合併state，也不增加exactly-once保證。

驗證：rg semantic反掃定義與全部直接引用；人工五維一致性；link有效性；TC1/2/3/6/7/8新舊arm dry-run；拿实际bridge收線作本弧第一consumer。不得用字數／零數字／零keyword計數冒充語義驗收。

## 段落 2：缺哨 advisory

Context：TC3/4，run()已唯讀；僅修正錯誤訊息及對應doc/tests。先加可觀察assert：valid缺哨輸出含需啟動指示、不得宣稱已掛哨；stopped/fresh/absent沉默；status不改state；不新增spawn或statewrite。先跑pytest見預期RED，改訊息後GREEN；不得把所有assert弱化成非空。

Pseudo code：existing run branches remain → missing/stale advisory says 尚未掛哨 and start→worker sequence → return existing hook JSON。命令 `uv run pytest tests/test_mail_autoarm.py -q`；`printf '%s' '{}' | uv run python hooks/mail_autoarm.py` 真實入口；ruff/mypy scoped（存量債歸因，禁以大範圍format污染）。引用hooks/AGENTS同步，保留安全callback/marker邊界。

## 整合與收尾

integration baseline: f0a81c83f5bd11716ff497878d6a5642b8c446d0（前弧完成點；卡 metadata commit 不計product差異）。Flash write scope僅本隔離WT，無git stage/commit、board/memory、外部send/cron/deploy。更新tests需實跑，使用現有TDD skill。writer沉澱 `.agent-tmp/air328-writer/receipt.md`（changed paths、actual tests/exit、unverified、scope/identity）；主session測執行面全套、instruction試驗、audit-test。

Sol fresh code/architecture review＋Muse intent/control-plane review（跨家族），主sessionJudge；必要修正再Flash，followup收斂。boundary receipt四欄、reviewledger、projection/source freshness與capability分層明示。scope sync/rootAGENTS不新增service宣稱。持久task shell用既有模板產生，卡refs並列EP/殼。post-build通過前不Done；新弧merge依當次fresh receipt與授權判準。無push。來源landing與未驗證carrier live能力分開。

## EP review／進度

初稿由 Marshal 產出；Muse F1-F7 按 evidence/design-adjudication.md 寫回本文（含F2/F4/F6糾正）。等待 Muse intent followup 與 GLM-5.3 fresh EP review。全部terminal＋判定無阻塞才交Flash。

> 接手注記（2026-10-13）：來源 codex session `01a133d2` 於 08:50Z 建 WT＋EP 後結束；ZCode 接手 session 落位 evidence/design-adjudication.md（自 primary `.agent-tmp/monitoring-design/adjudication.md`）並 commit 凍結送審 baseline。Muse intent followup 走原 design review session（`01a13468-551b-7022-857e-da7c960b5d92`）續卷；GLM-5.3 fresh EP review 獨立新卷。jobId 見本 WT `.delegate-bridge/` ledger。
