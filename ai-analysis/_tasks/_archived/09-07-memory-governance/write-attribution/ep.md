# AIR-40 — Memory 成功寫入歸因與分量報告

> **ep_type**: implementation
> **parent**: ai-analysis/_tasks/09-07-memory-governance/ep.md
> **baseline**: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a
> **status**: S1-S3 全部已實作（S1＝4b20db8；S2＋首跑＋S3＝本弧 commits）——待母卡 AIR-42 整體驗收

## 實作總覽與已決策

新增目的明確的唯讀 memory telemetry collector。分辨成功/失敗/未完成，還原跨 session 複製事件，輸出 session×條目×操作分量供治理判讀。主入口 `skills/memory-audit/scripts/memory_telemetry.py writes`，週期消費端為 corrections-weekly；先手動首跑，再修改 skill 編排，不改排程配置。不加 hook/寫入閘門，不改 memory/generator，不按 chars 自動判違規。

## UC 盤點

新增 UC：成功寫入歸因、資料覆蓋與分量報告（AIR-40，母卡 AIR-42）。後續 consumer AIR-41 只復用經驗證的事件讀取/identity。掃描 root AGENTS、hooks/AGENTS、skills/CLAUDE、memory-audit、corrections-weekly、standup、backlog search memory；元專案無 library Capabilities，SYSTEM-MAP 無對應項。

同主題 memory 清單：project_memory-desc-loop-posture-pending.md、project_agents-registry-split-design.md；只供 owner 結案判讀，不改 memory。UC 已有卡，不另建 parser/測試卡。

## Scenario Matrix

| ID | 場景/觸發 | 預期行為 | Checkpoint | UC |
|---|---|---|---|---|
| W1 | completed Write/Edit | 完整 actor/session/id/time/path 與 payload | evidence JSON | 寫入歸因 |
| W2 | Write error、未有 result | attempt/error/unknown 分開，不列成功 | diagnostics | 寫入歸因 |
| W3 | fork/side-chat 複製 ancestor | lineage+time+input fingerprint 證實後折疊，保留 aliases | dedup ledger | 寫入歸因 |
| W4 | fork 新寫入/兩次相同內容 | 不整批排除 fork，不只按內容去重 | event id | 寫入歸因 |
| W5 | parent 已不在/時間缺失 | origin unknown，排除確定 actor 榜，另列 | ambiguity ledger | 寫入歸因 |
| W6 | 缺 DB/CC、壞 JSON、未知 shape | requested/observed/unknown 分列，來源失敗不回空成功 | coverage | 資料覆蓋 |
| W7 | Write 無前態/Edit replace_all | 淨變化 unknown；literal delta 不冒充全檔 delta | provenance | 分量報告 |
| W8 | 多 alias、相對路徑、移除 WT | 正規化 pool+entry；相對路徑需 cwd，未知不猜 | path ledger | 資料覆蓋 |
| W9 | zero events | 成功空集合需來源可讀，允許零問題 | report | 寫入歸因 |
| W10 | 大窗、同時寫DB、重跑 | 固定UTC半開窗、DB read transaction、JSONL記scan時檔長；streaming；同snapshot同輸出 | manifest | 資料覆蓋 |

## 段落 0 — 已有研究與致命先驗

[POC evidence](../evidence/README.md)：DB 開 `mode=ro`，part 有 session_id/data/time_created；tool 在 data.tool、input/status/time 在 data.state。CC 以 assistant tool_use 與 user tool_result join。現存 ZCode 從8/16、此次 CC main directory 從8/12；不是完整90天。

已觀測 origin≠最後寫入者、fork改寫 callID且复制 input/operation time。故 origin 只當條目 provenance；callID 單獨不足跨 session 去重。POC raw top 含複製，不可當正式榜單。尚未證實 metadata.readFileState.content 為哪個時點，禁止直接當 before-image；正式重建前用受控 fixture＋歷史連續性比對。

可複用先例與雙端錨點（source/rg-derived）：

- `cr_usage.main`：定義 `skills/corrections-weekly/scripts/cr_usage.py:27`；CLI 消費 `skills/corrections-weekly/SKILL.md:27`。借 SQLite mode=ro/fail-loud 模式，不 import 敘事腳本。
- `digest_session`：`skills/standup/scripts/aggregate_sessions.py:142`，消費 `aggregate` 同檔:312；去重與截短有損，不借其輸出。
- pool identity 先例 `hooks/memory-index-regen.py:37`；consumer `run_for_cwd` 同檔:54。不 import hook；測試用共同案例驗 identity。
- 索引 inflow 定義 `skills/memory-audit/SKILL.md:93` 是 index chars，不是 body payload。

CR callers 實查缺 index；bridge無refs，以上非 graph 驗證。collector 是新 CLI leaf，沒有更動既有函式簽名；不預先建立跨模組框架或假想 projection graph。實作前再確認可用 CR 與字串 CLI 引用。

## S1：唯讀來源讀取與操作 identity

Context：實作 UC「成功寫入歸因／資料覆蓋」。無前置 production 段落；後續 S2、AIR-41 共享 Event/Coverage 定義。內聚在一支腳本，純轉換不依 CLI；SQLite/JSONL adapter 依輸出資料結構。成功標準：可由 source_ref 追到原始事件，缺資料不被計成零。Invariant Impact：無交易 invariant；分析 invariant＝來源唯讀、成功證據完整、歸因不重複。

檔案：新增 `skills/memory-audit/scripts/memory_telemetry.py`、`tests/test_memory_telemetry.py`。具名 Event/Coverage dataclass，外部 JSON 邊界可用 dict，核心轉換明確欄位。CLI 參數：`writes --pool --zcode-db --cc-root`（可重複）、`--since/--until`（帶時區；defaults 7日）、`--output`。明確限制 output 不在來源 DB/CC/memory 池內。

Pseudo code（意圖，實作可調整內部名稱）：

```python
manifest = validate_inputs_and_freeze_window(args)
z_events, z_coverage = read_zcode_read_transaction(manifest)
c_events, c_coverage = stream_cc_tool_pairs(manifest)
events = normalize_paths_and_results(z_events + c_events)
canonical, aliases, ambiguous = resolve_lineage_copies(events)
```

Event 保留 source/session/parent/task_type/event id/call id/operation start-end/record time/raw path/canonical path/status/input hash/payload字元數/source定位；不在報告複製對話/條目正文。保留取消/錯誤診斷。CC result join 在同 transcript/agent namespace 中，不跨 agent 僅靠 call id；未匹配 result 不算成功。ZCode event window 優先操作時間，record time fallback需標，複製時間不能冒充新寫入。半開窗 [since,until)。

去重：同祖先鏈、同操作時間、tool、canonical path、input hash，且祖先原事件在場才標 confirmed copy；不同 operation time 為獨立事件；跨無關 session 同內容不合併。缺祖先或可能多 writer 時列 ambiguous，不硬選 creator。保留原始 row counts與操作 counts，顯示差異。

驗證：真 SQLite fixture以獨立規格造 Write/error/fork-copy/fork-new/side-chat/同內容不同時間；CC JSONL fixture含 success/error/out-of-order/unmatched/partial malformed。以 CLI subprocess 驅動真輸入檔，核對事件與 source_ref，不 mock DB driver。來源檔 sha 前後不變；output escape被拒絕；固定資料重跑一致。先RED再實作。metadata時點未知保持unknown不阻整卡。

## S2：寫入投影、分量與首跑

Context：UC「分量報告」，依賴 S1 normalized events，不直接重讀另一套來源。資料 invariant 同 S1；數值未知用 null＋reason，不填0。成功標準：能回答誰執行哪個成功操作，且不把流量當存量。

核心要點：payload是Write.content/Edit.new_string長度；檔案delta僅有可證明前後全態且連續性成立才算，否則unknown。replace_all 沒前態次數未知，不能用literal new-old冒充。索引delta僅比較同pool/同單位/同generator identity的兩個已存snapshot；沒有起點就建立本次report baseline供下一輪使用（報告目錄，不寫memory）。generator版本不匹配或條目rename/deletion未還原時列incomparable。

```python
successful = [e for e in canonical if e.status == "completed"]
groups = group_by_actor_and_entry(successful)
report = writes_projection(groups, aliases, ambiguous, coverage)
report.net_delta = reconstruct_only_proven_transitions(successful)
report.index_delta = compare_compatible_snapshots_or_unknown()
write_report_outside_sources(report)
```

JSON輸出schema version、window、source coverage、inventory timestamp、counts、排行榜、unknown／ambiguous及source_refs；文字輸出概要與證據路徑。排名保留已刪除條目歷史事件但不混入現存存量。origin/role缺失不猜subagent是否mem-distill；違規判斷留LLM抽驗，合規寫入同樣列事實。

驗證：CLI整合測試覆蓋縮檔大payload/只改body索引不變/新建短body索引增/缺snapshot/單位差/兩次同內容/跨別名；真ai-rules 7日首跑放任務 evidence，核對一個成功寫入與一組複製事件；已知大寫入只驗還原，不強制報違規。POC不足以替代正式首跑。

## S3：接入既有週報並收尾

Context：UC「週期治理消費」，依賴 S2 可用 CLI。修改 `skills/corrections-weekly/SKILL.md` 與 `skills/CLAUDE.md`；不改現有排程，不 import standup，不動 hooks。定義源為 collector 的輸出語義，skill只描述如何讀、如何判。

修改要點：在現有機械量測後調CLI，報告給top/unknown/coverage/單位；失敗不冒充無寫入；附原始artifact路徑，維持週報摘要精簡。週期班次仍corrections-weekly，audit可按需使用，不另建常駐巡檢。

驗證：按skill手動跑完整新增步驟，驗報告與JSON可追源；`rg 'memory_telemetry|寫入歸因' skills/` 引用一致。`git diff -- hooks/` 為空。對新增測試跑 audit-test、獨立 code-review/judge、ruff、targeted pytest；本repo未配置mypy，記適用性不臆造全repo型別綠。測試集合含新增檔及被實際改到的共享parser測試（本EP不改generator則不額外宣稱其驗收）。

## 整合策略與收尾

baseline: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a

無SYSTEM-MAP/Capabilities新增，更新skills索引與相關instruction描述。production完成後 AIR-40 結案兩步，殼補實作證據與baseline/source SHA；父家尚活躍時不单独移动子目錄，由母卡統一歸檔同步refs。POC屬母家研究證據，不直接引用為production code；驗證結論已由正式測試/報告承接後再處置。memory池唯讀，結案蒸餾只交候選給owner。本EP規劃完成不代表子卡Done。

## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| 1 | 🟡 建議 | S3 | corrections-weekly 插入點假設「現有機械量測後」結構，施工時若 skill 已改需重定位 | 施工前重讀該 SKILL 對應段，錨點漂移則先更新 EP 錨再動手 | implemented |
| 2 | ℹ️ 提醒 | S1 | CC result join 跨 agent 只靠 call id 不可行已寫明；ZCode record-time fallback 需標記已寫明 | 無，條款充分 | implemented |

審查結論：有條件執行（F1–F5 通過；11 引用錨點全存在且語義對；TDD 先RED已載明）。審查者：muse-code（跨家族獨立審查），2026-09-07。
