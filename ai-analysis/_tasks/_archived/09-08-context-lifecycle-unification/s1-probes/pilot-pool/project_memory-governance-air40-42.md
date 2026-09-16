---
name: memory-governance-air40-42
description: memory 知識治理線終態（AIR-40/41/42 全閉＋codex 反例驅動修復 R1-R6→F1-F3→N1）——寫入歸因＋Read 觀測 telemetry＋載體分流；源覆蓋 drafts 全暫緩
metadata:
  node_type: memory
  type: project
  originSessionId: sess_5fcef0cd-2b0f-4e95-8a02-4feb508cc4cc
---

memory 知識治理線（AIR-40→41→42.1→母卡 42）全閉（2026-09-07，歸檔 `ai-analysis/_tasks/_archived/09-07-memory-governance/`）。代碼/條文單一源：`skills/memory-audit/scripts/memory_telemetry.py`（writes/reads 雙子命令）＋memory-audit skill 層 2；全套 195 tests。

**核心語義（用時記住）**：寫入量是流量非品質/存量——違規判斷留 LLM 抽驗（追 source_ref），不按 chars 自動判；Read 觀測「未觀測到讀」限 observed window＋coverage（`window_shortfall`：源 bounds 晚於窗起點即 partial——兩源 live 皆 shortfall，勿稱 90 天未讀）；unmatched/unknown Read 計接觸（`unpaired_reads`）非 zero 候選；`reads_without_entry`＝rename/刪除 identity 線索→HOLD（LLM 裁決不自動合併身分）；rank 解析＝generator 行為 mirror（`_frontmatter_rank`，per-pool hash 隨報告 `generators` map 對帳）。telemetry top_entries 是 7 日寫入流量——與現存 inventory 不同集合，absent≠zero-read。ZCode 遙測 db＝`~/.zcode/cli/db/db.sqlite`（頂層 `~/.zcode/cli/db.sqlite` 0-byte 殘檔陷阱）。

**codex 審查鏈修復語義（R1-R6→F1-F3→N1 三輪反例驅動，最終態）**：時間窗＝operation time 優先**且排他**（op 在窗外排除、無 op 才 record fallback）；SQL 選取與事件契約**等價**而非 margin 補償——`json_extract('$.state.time.start')` 可解析即 op 窗、上界用 `<=`（SQLite `datetime()` 截小數秒，同秒全含保持 superset、Python 半開窗精判排除多餘）；路徑保護比較必須兩側統一 resolve（relative/symlink alias 會繞過）；CC unreadable/malformed 抬 partial；**單池契約**（canonical 去重 aliases＋第二個不同 pool 拒絕——guard 掃現存檔擋不住已刪條目的歷史事件跨池混合）；lineage 折疊需**時間證據充分**（任一側 op time 缺 → ambiguous 揭露，None==None 是「無證據」非「時間相同」）；baseline/週報住常態目錄 `ai-analysis/memory-telemetry/`（不隨任務家歸檔移動）；唯讀驗證 baseline 用副本（work-order §8）。用途判讀帳（EP S2 第二表）已接進 skill 層 2。

**載體分流規則沉澱（42.1，條文在 memory-audit skill）**：先判用途與最小範圍（通用≠rule）；固化分層＝部分覆蓋壓指針／完全覆蓋列退出候選交 user——**判完全覆蓋前必須 rg 驗條目每個行動增量段**（review 實證：F7 條款增量險漏）；cluster 合併判準＝同召回情境非同 prefix；blocker 拆任務狀態（歸卡）／已確認外部限制（留 memory）。

**遺留 user 裁量（已收斂）**：09-07 user「你覺得合理就都做」授權——capability-tier 已刪（rule 完整承載）、no-backward-compat 已指針化（F7 增量留）、code-review-settings-sync 已遷 code-review skill 收尾步驟＋源條目刪（池 129→127）；rules bundle 已 deploy（muse 同日加入 TARGETS 第四家，路徑見 [[muse-code-cli-facts]]）。

**telemetry 源覆蓋面（09-08 user 質問後開 drafts，45c4bc3）**：歸因現僅 ZCode(SQLite)＋CC(JSONL) 雙源，其餘在 `uninstrumented` 揭露——DRAFT-1 codex 源接線（`~/.codex/sessions/**/rollout-*.jsonl` 在場、格式已解過，可行性高）；DRAFT-2 muse/grok 記錄面探測（muse 有 export/trace 但本地僅 config、grok-build runs 面路徑待探；bridge ledger 只覆蓋 bridge 派發任務）；bash-rg 無記錄面＝定義性盲區不開卡。

**unknown writer 線索**：top 寫入者全是 subagent sessions（最大戶 6 寫 74K）——單一寫入者拓撲有破口，source_ref 可追，抽驗留週報班次。

相關：[[memory-card-lifecycle-gate]]、[[memory-failsoft-importance-ordering]]、[[air-38-routing-feedback-tier]]、[[project-codex-quota-death-durable-checkpoint]]。
