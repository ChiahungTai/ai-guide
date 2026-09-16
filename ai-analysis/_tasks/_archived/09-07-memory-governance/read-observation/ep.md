# AIR-41 — 覆蓋限定的 Memory body Read 觀測

> **ep_type**: implementation
> **parent**: ai-analysis/_tasks/09-07-memory-governance/ep.md
> **baseline**: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a
> **depends-on**: AIR-40 正式 reader 與首跑證據
> **status**: S1-S3 全部已實作（206148a：reads 投影＋TDD＋live 首跑＋skill 接入）——待母卡 AIR-42 整體驗收

## 實作總覽

新增 `memory_telemetry.py reads` 投影，量測明確成功的條目本體 Read，分開工作／維護／未知用途，產生可觀測窗內未見Read候選。90日為requested window；不宣稱從未讀、無用、可刪。不把零Read轉cold，不刪改memory/rank，不建立常駐排程。資料缺失要可見，零候選/全部保留合法。

## UC 盤點

新增UC：body Read觀測與覆蓋限定候選（AIR-41，母卡AIR-42）；更新既有memory-audit內容核實的證據入口。已有卡不新增。依賴AIR-40 Event/Coverage；掃描root AGENTS、skills/CLAUDE、memory-audit、standup read_hotspots、backlog search。元專案無library Capabilities或對應SYSTEM-MAP。

同主題memory清單：feedback_memory-failsoft-importance-ordering.md、project_memory-desc-loop-posture-pending.md；先驗只列，不審改共享池。候選不是結案蒸餾授權。

## Scenario Matrix

| ID | 觸發 | 預期行為 | Checkpoint | UC |
|---|---|---|---|---|
| R1 | 雙源成功Read | join result後計body讀取，保留range | evidence | Read觀測 |
| R2 | error/unmatched/只索引/rg | error 不計接觸；unmatched/unknown 計接觸不計成功（unpaired_reads 揭露）；盲區顯示 | diagnostics | Read觀測 |
| R3 | audit或蒸餾讀遍全池 | 維護Read與工作Read分開 | purpose ledger | 用途判讀 |
| R4 | 缺來源、malformed、保留期不足 | observed-window/partial，不能產全域零讀結論 | coverage | 覆蓋 |
| R5 | zeroRead但hot/近30日/活躍弧 | 豁免候選；豁免原因仍可觀測 | exclusions | 候選 |
| R6 | owner未知、rename/刪除重建不明 | HOLD，不自動合併身分 | inventory identity | 候選 |
| R7 | 全保留/零候選 | 合法驗收，不要求處置 | advisory | 候選 |
| R8 | 只有description已足夠 | body metric維持零，但不推無用 | limitation | 用途判讀 |
| R9 | Codex/Muse或Bash讀取不在collector | 明列harness/tool缺席，不能稱全使用率 | manifest | 覆蓋 |
| R10 | 大窗/掃描中新writer/重跑 | streaming、固定上界、inventory hash，變動標stale | receipt | 覆蓋 |

## 段落0 — 研究與假設

[母家POC](../evidence/README.md)已證實現存ZCode/本次CC範圍不足90日，且維護Read未分類。raw zero-body-Read數不是可刪候選數。origin非operation actor；沿用AIR-40 identity，不另寫去重器。

既有錨點（source/rg）：`read_hotspots.main` 在 `skills/standup/scripts/read_hotspots.py:31`，由standup skill讀取熱點流程消費；不直接複用其 compact-JSON LIKE 或未判成功的counts。`memory-audit/SKILL.md:45` 內容核實是本卡consumer，`:59`治理三分離、`:95`狀態戳。rank來源 `generate_index.py:98 parse_rank`，本卡只讀不改；直接引用目前輸出或解析受支持frontmatter，不增加第二套rank政策。

CR查詢缺index，bridge無refs；source-read僅提供結構先例，不等於runtime驗收。依賴AIR-40新collector是planned，開工需先讀其最終程式/測試與卡Done證據。若其schema變更，先更新本EP錨點與fixture，不猜欄位。沒有完整retention manifest時，不補造歷史覆蓋。

## S1：Read與coverage投影

Context：實作UC「body Read觀測／覆蓋」。依賴AIR-40成功結果join、path normalization、lineage去重；共享Event/Coverage，不重讀standup摘要。Invariant Impact：無交易domain invariant；分析約束＝unknown不變零、維護不冒充工作、工具成功不冒充知識被使用。

檔案：修改 `skills/memory-audit/scripts/memory_telemetry.py`，新增 `tests/test_memory_read_observation.py`。CLI `reads --pool --zcode-db --cc-root`（重複可列多目錄）、`--since/--until`（預設90日）、`--output`；沿用AIR-40輸入/輸出路徑邊界。

```python
events, coverage = collect_normalized_events(args)
inventory = snapshot_entries_with_hash_rank_mtime(args.pool)
reads = select_successful_body_reads(events)
report = project_reads_by_entry_and_source(reads, inventory, coverage)
```

Read覆蓋粒度：部分Read也計明確body接觸，但不宣稱全文讀完；record range/partial可得就保留。index、系統底線檔不算entry。日界用UTC aware半開窗，mtime只用豁免不當creation。coverage列請求期間、各源observed bounds、掃描目錄、excluded roots、read/parse errors、未知shape與instrumented harness/tool清單。observed bounds不是連續保留證明；缺一源則partial，不把另一源零命中寫全域零。

CC掃描根明確列出現存/已移除worktree歷史目錄的發現與漏失；當前worktree list不足以保證所有歷史。允許CLI顯式追加來源root。無rename映射時按現存canonical path觀测，不把舊名零命中當新條目無用；重建同名歷史混淆標identity_unknown。所有候選附scope，不自稱全harness召回率。

驗證：沿用真正SQLite/JSONL CLI fixture，success/error/out-of-order/unmatched/partialRead/indexOnly/alias/relativePath/removedWT/emptyReadable/missing/malformed；缺源須partial與非零診斷狀態，不能「成功零讀」。穩定fixture重跑一致、來源hash不變。正式live首跑必重新產，不能沿用前期POC raw counts。

## S2：用途判讀、候選與豁免

Context：實作UC「用途判讀／候選」。依賴S1 observation report與當次inventory，不依description語義猜owner，不使用mtime推讀取時間。LLM可讀有限原始session context判讀，但collector不輸出整段對話。

用途帳以report中的event/session source_ref為鍵：work/maintenance/unknown＋一行證據。known maintenance來源如明確audit/mem-distill委派上下文；不能只靠title包含audit就自動定性，也不能把整session所有Read視為同用途。unknown不自動轉work。

候選輸出分兩表：① observed-window未見任何成功body Read；② 有維護Read但未見已確認work Read。第二表與未知用途僅作人工調查，不冒充零Read。共同豁免 hot、近30天mtime、活躍弧；owner無法確認、identity未知、來源盲區重要時HOLD，仍可顯示受限觀测事實。

```python
for entry in inventory:
    observation = report.for_entry(entry)
    decision = apply_exemptions_or_hold(entry, owner_evidence)
    emit_observation_and_advisory(observation, decision, purpose_evidence)
```

不把零Read當cold，不隨collector修改rank；AIR-39保留目前語義。條目description已足夠、低頻重大約束、其他工具讀取均是保留理由。缺失資料可以導致全HOLD，仍可完成觀測能力驗收。

驗證：fixture覆蓋三豁免、owner未知、mtime邊界/未來時間、rename、只維護Read、未知用途、描述足夠。live首跑人工抽實際候選（不足則全取，零候選以受控fixture驗候選路徑），每項回查雙源與coverage；允許全部保留。不能以>=1處置作完成條件。

## S3：接入memory-audit與收尾

Context：更新既有audit內容核實UC。修改 `skills/memory-audit/SKILL.md` lite/full入口與內容層、`skills/CLAUDE.md`索引。先消費已產report，缺資料才按需調reads；不新建cron、不每輪強制重掃所有transcripts。

修改要點：觀测是內容核實的取樣線索；full/lite仍需對repo查真值。advisory→核可→執行不變，本卡只交候選與判讀，不跨池寫入。新用途欄不變成另一份權威memory，只是本輪報告。

驗證：按skill走一次reads→用途判讀→advisory，三份輸出source_refs可追；`rg '死亡|從沒被讀|未觀測|memory_telemetry' skills/`逐項判歷史vs活規範；不改歷史archive。targeted pytest覆蓋AIR-40+本卡測試、ruff、audit-test、獨立review/judge；無配置mypy記適用性。不以字符串測試冒充live evidence。

## 整合與收尾

baseline: f03d3460c9c157e1dc6079ccdfb7acd680bbe25a

AIR-40之後順序build，同script衝突先re-read。更新skills描述、索引與殼證據；元專案無library Capabilities/SYSTEM-MAP變更。AIR-41達行為驗收才結案兩步；母家活躍時保留子目錄位置，母卡歸檔統一更新refs。memory/shared configs不寫。結案蒸餾只列owner候選，不自動改其他弧條目。

## EP Review Findings

| ID | 嚴重度 | EP 段落 | 問題 | 建議 | 狀態 |
|----|--------|---------|------|------|------|
| 1 | 🟡 建議 | S1 | 依賴 AIR-40 reader schema（planned 狀態），schema 漂移則本 EP 錨點/ fixture 全錯 | EP 已載「開工先讀最終程式」條款；施工嚴格執行，不猜欄位 | implemented |
| 2 | ℹ️ 提醒 | S2 | R8（description 已足夠）與 K6（42.1）同語義，兩處一致（皆保留） | 無，口徑一致 | implemented |

審查結論：有條件執行（F1–F5 通過；須在 AIR-40 Done 後開工）。審查者：muse-code（跨家族獨立審查），2026-09-07。

## Build 後 dual review 與修正輪（2026-09-07）

實作（206148a）與結案（4051f3b）後 dual review 到件（muse 重審工單 `re-review-workorder-i1234.md`＋GLM fresh-eyes）：I1-I4 全 fixed 為兩家共識；GLM 新提 F1（mirror 引號空白家族——generator 頂層雙趟/巢狀單趟正規化不對稱）＋F2（reads 路徑缺 generators identity）經 judge 採納修正（F1 remedy 修正為層次模擬，非四趟統一——後者會在巢狀案例反向分歧）；F4（CC unmatched direct fixture）＋N1（R2 行 doc 同步）一併落地；F3/F5/N2 記債。修正輪 followup 複驗：F1 經獨立 26 案例 battery 零分歧、F2 hash 重算驗真——四項 CLOSED，複驗通過。live 證據 `../evidence/reads-post-i1234.json`（generators/window_shortfall/reads_without_entry 在場）。

## Judge-review 第二輪（muse-code 獨立裁決，2026-09-07）

第一輪 dual review（relay I1–I4＋S1–S9＋S10）對修正輪 3cc3284 的獨立裁決（code 實讀＋測試重跑＋lint 重跑，非轉述）：

| 項 | 決策 | 機械證據 |
|----|------|---------|
| I1 rank mirror | ✅ adopted | `_frontmatter_rank` docstring 等價契約＋test_i1/test_i1b＋SKILL 漂移警示行 |
| I2 unmatched 計接觸 | ✅ adopted | `unpaired` 計數＋CLI 行＋test_i2 |
| I3 shortfall 旗標 | ✅ adopted | `window_shortfall`→partial＋CLI 行＋test_i3 |
| I4 HOLD 口徑 | ✅ adopted（選項 b：EP 級 LLM 裁決） | `reads_without_entry`＋SKILL 47 行 HOLD doctrine＋test_i4 |
| S10 RUF059 | ✅ adopted | ruff 全綠（本輪重跑） |
| fresh F3 basename key／F5 命名 | ❌ 不採納 | 單池為文件示範用法；改 key 會 churn 剛落地的週報模板，成本＞收益；多池 reads 上線時重開 |
| fresh F7 死碼／F8 mutate | ❌ 不採納 | 前者 defense-in-depth 保留，後者無行為差異 |
| fresh F4 OSError／F6 靜態 manifest | ✅ 採納未落地 | 問題真實且便宜，但弧已結案——待 user 決定是否另開 fix（見主報告） |
| primed F3/F4 | ✅ 被 I2/tests 覆蓋；reads determinism 缺 pin 併入上行 follow-up | grep 確認 reads 無 rerun 測試 |

自查（反 sycophancy）：否證重查 F5——改名確實要 churn S3 剛加的模板消費行，維持 ❌；否證 I1——mirror＋hash 漂移偵測比 import 更適合 per-pool generator 拓撲（import 需 sys.path 接線 CLI 單檔執行），維持 ✅。35 tests＋ruff 重跑全綠為本輪實測（非轉述 commit 數）。

**Judge 處置（主 session，2026-09-07）**：F6（uninstrumented 靜態性註解）當下落地；F4（resolve OSError 揭露）不做——觸發前提 near-impossible（工具實錄路徑不 resolve 失敗），與 drafts YAGNI 同型，不開卡攢批。

## Codex 整弧審查 judge 裁決（2026-09-07）

codex dual-context 整弧審查（`35b8ab9..115227d`，findings `memory-governance-35b8ab9-115227d.md`——中間檢查點：核心重現完成、fresh 側最終驗證因 usage limit 中斷）。Judge 逐項獨立查證（非轉述重現；R1 親重現）後 **6/6 採納**：

| 項 | 決策 | 查證證據 | 修復 |
|----|------|---------|------|
| R1 報告可覆寫來源 | ✅ | 親重現：relative 同檔 `[OK]`＋SQLite 檔頭變 JSON；protection 比較 resolved vs raw | source 清單統一 resolve＋symlink alias 攔截；`--baseline-dir` 納入保護（池/source 內拒絕）——test_r1/r1b |
| R2 record 預篩誤窗 | ✅ | SQL 純 `time_created` 窗讀碼＋codex 真 DB 抽查（1420 筆 op≠record） | SQL 撈寬一個窗長 margin；事件納入=operation 優先且排他（op 窗外排除、無 op 才 record fallback）——test_r2 兩向 |
| R3 unreadable/malformed 不抬 partial | ✅ | partial 判定零消費該二鍵（讀碼） | `unreadable`/`malformed` 併入 partial（R3）——test_r3 |
| R4 多池 basename 混合 | ✅ 最小修 | by_entry key=basename 讀碼；上輪「多池上線再開」被正確反駁（不能接受輸入並產錯誤觀察） | 跨池同名 entry fail-loud（不擴 schema）——test_r4 |
| R5 用途判讀未接線 | ✅ | SKILL 無消費步驟；EP S2 兩表設計（第二表）無載體 | skill 補「用途判讀帳」段（event/source_ref 三值帳＋第二表，全 HOLD 合法） |
| R6 baseline 指舊路徑 | ✅ | skill :39 舊路徑 `test -d` 不存在（歸檔搬移造成） | 常態目錄 `ai-analysis/memory-telemetry/baselines/`＋既有 baseline 遷入＋承接驗收（delta 非 null） |

否證重查：R1 親重現（不轉述 codex fixture）；R4「既有 judge 曾拒」反駁成立性複查（拒的理由=改 schema 成本，最小修不動 schema——維持 ✅）。修正輪 195 passed＋ruff clean。codex 屍體考古：fresh agent 撞 usage limit 於「獨立錨點驗證」步——本輪 judge 查證即補上該步。

**Followup review（muse job-mtra5khf，2026-09-07）：通過——R1-R6 全 closed（6/6）**，每項實跑證據（40 passed 全集＋定向 5 passed＋/tmp 承接重跑 run2 delta 非 null＋lint 全綠）；兩條 ℹ️ 選項（O1 margin limitation 註解、O2 unreadable 專屬測例）記錄不擋。工單 `followup-workorder-r1r6.md` 可重放。

## Codex 二輪驗收 judge 裁決（2026-09-08，`memory-governance-followup-bbd4467.md`）

codex 額度恢復後正式驗收 `bbd4467`：R1/R3 verified；反駁 muse「6/6 closed」——**F1/F2/F3 三項實跑反例均採納**（judge 親驗修法設計後修正）：

| 項 | 反例 | 修復 |
|----|------|------|
| F1 margin 非契約 | 1 秒窗＋record 早 op 2 秒 → successful=0（margin 隨窗縮水） | SQL 選取改 operation 等價：`json_extract('$.state.time.start')` 可解析即 op 窗、缺 op 才 record 窗、SQLite 不可解析的 op 全撈交 Python 層判——margin 移除——test_f1（窄窗長 drift） |
| F2 guard 只掃現存檔 | B 池已刪 `note.md` 的歷史 Read 掛到 A 池同名（退出零讀候選）；同池 aliases 雙計 entries | **單池契約**：canonical 去重 aliases（同池 symlink 合一）＋拒絕第二個不同 pool——歷史事件混合在單池下不存在——test_f2 |
| F3 None 進分組鍵（既有債，非 bbd4467 引入） | 父子同 key＋時間都缺 → aliases=1 basis「lineage+time+hash」（無時間證據當確定複本） | 折疊加時間證據 gate：任一側 operation_start 缺 → 不折疊、ambiguous 揭露（reason 標 missing time evidence）——test_f3（successful=2 計數不縮水） |

Suggestion（baseline 副本驗證）採納：work-order review variant §8 補「驗證 baseline 用副本」；R6 驗收推進的正式 baseline 差值報告已補保存 `ai-analysis/memory-telemetry/r6-baseline-advance-20260907.json`（不倒回）。修正輪 198 passed＋ruff clean。

**Followup review（muse job-mtrnmdec，2026-09-08）：通過——F1/F2/F3 全 closed**。每項讀碼＋定向測試＋自構反例（1 秒窗 1 小時 drift → successful=1；歷史碰撞多池 → exit 2；完整時間父子 clone 照折疊 2 tests）；三檔全集 95 passed；read-only 前後一致。無新 finding。

## Codex 三輪驗收 N1（2026-09-08，`memory-governance-followup-bf38afb.md`）

F2/F3 verified、F1 原反例過；新揪 **N1：SQLite `datetime()` 截斷小數秒**——ISO 窗 `[10:00:00.250, 10:00:00.750)`＋op `.500` 在 SQL 上界 `<` 比較被排除（numeric 對照正常，既有週報不受污染）。Judge 採納：SQL 預選需為 Python 精判半開窗的 superset——**op 窗上界 `<`→`<=`**（datetime() 截秒下同秒全含、Python 層半開窗排除多餘；下界 `>=` 截尾後天然 superset）＋註解固化語義。test_n1 三 case：.500 納入／.750=until 排除／同秒低於 since 排除——199 passed。
