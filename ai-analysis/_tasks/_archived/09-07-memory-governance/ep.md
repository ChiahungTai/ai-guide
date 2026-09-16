# AIR-42 — Memory 知識治理改善協調計畫

> **ep_type**: implementation
> **product-type**: docs（母卡協調與整體驗收；不是 blueprint，不直接實作子卡）
> **baseline**: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a
> **status**: 已落地（AIR-40/41/42.1 三子卡全 Done——collector 35 tests＋6 份 live evidence＋分流 advisory＋規則修訂；本檔隨歸檔收案）

## 實作總覽

目的：下次遇到相關情境時，AI 能召回已確認、會影響行動的事實與約束。任務歷程由 Backlog.md、EP、git 承載。先建立可信觀測，再校準載體分流。禁止以寫入量、低 Read、刪除數或 token 減量替代知識品質。

母卡只管理依賴與整體驗收；不另寫泛用 telemetry framework、不加 hook/寫入閘門、不調 rank、不自動修改共享 memory 或現有排程。user 本輪授權卡片、規劃、telemetry 查證與 POC，未開始 production /implement。

## UC 盤點

| 卡 | 能力 | 計畫 | 狀態／依賴 |
|---|---|---|---|
| AIR-42 | 協調、證據與分流驗收 | 本檔 | 子卡成果皆驗收後才 Done |
| AIR-40 | 成功寫入歸因與分量觀測 | [write-attribution/ep.md](write-attribution/ep.md) | 第一個實作 |
| AIR-41 | 覆蓋限定的 body Read 觀測 | [read-observation/ep.md](read-observation/ep.md) | 依赖 AIR-40 reader 合約 |
| AIR-42.1 | 載體分流樣本與文件校準 | [knowledge-routing/ep.md](knowledge-routing/ep.md) | 依賴 AIR-40、AIR-41 首跑證據 |
| AIR-39 | type×rank×mtime 索引排序 | 既有完成卡 | f03d346 已含，不重做 |

Card tree：AIR-42 的 children 為 AIR-40、AIR-41、AIR-42.1；執行 dependency 是 AIR-40 → AIR-41 → AIR-42.1。母子關係不作 dependency，避免循環。

掃描：root AGENTS.md、hooks/AGENTS.md、skills/CLAUDE.md、memory-audit/corrections-weekly/standup skills、backlog search memory。元專案沒有受影響 library Capabilities；SYSTEM-MAP 無對應項，不新增。pending-decisions 指定檔在此基線不存在。新增母卡 AIR-42 與子卡 AIR-42.1；AIR-40/41 復用。

同主題 memory（清單級，不代表已核實）：project_memory-desc-loop-posture-pending.md、feedback_memory-failsoft-importance-ordering.md、project_agents-registry-split-design.md；池為 `~/.claude/projects/-Users-ctai-Github-ai-rules/memory`。僅作結案時 owner 分類候選，禁止本輪自動蒸餾；外部並行 writer 與非本弧內容保守保留。

## 段落 0 研究與先驗

[evidence/README.md](evidence/README.md) 與 [telemetry.json](evidence/telemetry.json) 是實跑證據；[POC](poc/poc_telemetry.py) 是唯讀、metadata-only 假設探測，不是正式報告 collector。寫入序號、原始 session ID、成功狀態、input hash 可追溯，不保存對話正文。

已證實：現存雙源不足 90 天；origin 不能直接代表最新寫入者；fork/side-chat 改寫 callID 並複製既有事件；失敗操作存在，不能計入成功寫入。這些前提若不先修，AIR-40/41 會產錯誤證據。

架構：純事件投影/分組在 memory-audit 的小型 collector；ZCode/CC adapters 僅讀來源，週報與 audit 透過 CLI/JSON 消費。standup digest 是有損敘事，不借為 evidence reader；不反向 import hooks、不改 generator parser ownership。

CR research 已嘗試 callers，当前 WT 缺 `.code-reality/scip/index.scip`；bridge 無 refs 面。依賴描述為 source/rg 查閱，不宣稱 graph 驗證。無 production 符號接線變更在本輪發生；正式 build 重新確認索引與引用。

## Scenario Matrix

| 場景 | 觸發 | 預期行為 | Checkpoint | UC |
|---|---|---|---|---|
| 正常執行 | AIR-40 首跑可追證 | 接 AIR-41，再做分流 | 各子卡報告 | 協調 |
| coverage 不足 | 請求90天但只留數週 | 交付限定觀测，禁止從未讀推論 | coverage receipt | 協調 |
| 找不到問題 | 零違規/零候選/全保留 | 可驗收，不湊處置 | 判讀紀錄 | 協調 |
| 新 writer 改條目 | 樣本後 sha 改變 | 樣本 stale，重新核實，不覆寫 | hash+觀測時間 | 分流 |
| 大量歷史 | 雙源掃描增大 | streaming、固定上界，報告耗時/掃描量；不建常駐服务 | manifest | 觀测 |

## S1：交付實作順序與自足子 EP

Context：實作「協調、證據與分流驗收」。本文件是母卡執行清單，不是五段中型 blueprint。依賴為現有卡及本輪先驗；語義約束＝觀测不等於價值、計畫不等於能力已上線。Invariant Impact：無交易 domain invariant；保護資料唯讀、unknown 不轉零。

修改要點：三張子卡各有完整 UC/SM/段落/驗收/收尾；母卡保留整體目的與範圍，不重複子 EP 實作細節。既有卡不重新編號；以 parent_task_id 和 dependencies 表達兩種关系。

驗證：CLI view JSON 讀回 parent/dependency/ref；本地殼連結與 EP SHA 檢查；獨立 EP review 後修回子 EP 與卡 desc。新卡初始 commit 依建卡免確認例外，後續計畫修改保留 working tree 待一般 commit gate。

## S2：子卡落地後整體驗收

Context：依賴 AIR-40、AIR-41、AIR-42.1 真實完成成果。本段不重做 collector 或規則設計。成功標準：可由事件證據追到候選，再追到載體判斷，沒有把 telemetry 當真值裁判。

驗證：讀三份首跑/樣本報告；抽一個已還原寫入、一个觀测受限 Read、一個全保留或分流決策；每项核實原始证据／权威目的地。不能以 POC 成功或 EP 齊全結案。

## 整合與收尾

baseline: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a

實作各卡在同 owning branch 順序完成，跨 session 用卡+EP，不依本對話。共享檔案先重讀最新內容。子卡進度更新各自殼；母卡最後更新殼實作章節與狀態，再結案兩步，隨任務家歸檔同步所有子路徑 references。沒有新增測試的純協調段不跑 audit-test；程式子卡必跑。記憶池不在本次寫入範圍，結案只列 owner 後續候選。

## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| 1 | 🟡 建議 | S1 | `product-type: docs` 非 EP schema 標準欄位 | 保留（implement 掃描只認 ep_type/parent/baseline，不影響）；不擴散到子 EP | implemented |
| 2 | ℹ️ 提醒 | 全文 | 「分量觀测」簡體 typo 已修；evidence/README.md 已補 | 無 | implemented |

審查結論：有條件執行（F1–F5 通過；依賴無循環已驗；POC 前提成立）。審查者：muse-code（跨家族獨立審查），2026-09-07。
