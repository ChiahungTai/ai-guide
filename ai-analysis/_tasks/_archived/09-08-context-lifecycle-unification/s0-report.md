# S0 Report：前置研究與 probe（AIR-45 context 統一生命週期機制）

> 執行：S0 實作 agent（ZCode subagent）｜baseline 7566bab｜日期 2026-09-08
> 方法：六項獨立 probe，逐項 append（增量寫入，防中途失憶）。機械證據＝命令＋輸出節錄。

## 結論表（P1-P6 verdict 一覽）

| # | 項目 | verdict |
|---|------|---------|
| P1 | ZCode 召回機制鑑識 | **無 desc-matching 動態召回——僅靜態 instruction bundle＋被動工具載入；注入管道＝synthetic user messages（機制座位存在，memory 未接上）** |
| P2 | OpenCode AGENTS.md 上限 | **文檔面：無任何上限/截斷條款（鏡像全掃零命中）；runtime 行為：未驗證（CLI 缺場）** |
| P3 | muse mosaic lane 行為 | **mosaic rules_file 實測 65,536B（截斷；rendered 123,208B、砍 47%）；cap=65,536（trusted）／32,000（untrusted＋project 跳過）；23,583＝ai-rules 串接渲染值（已解）** |
| P4 | mosaic root AGENTS.md 組成 | **42,740B：必中集 ~11.5KB／下沉目錄層 ~5.7KB／走觸發層 ~25.5KB（模組觸發器表 9,881B＝條目化原型）；重分配後 root 可收斂至 ~11KB** |
| P5 | desc 用語樣本 10 條 | **10 條 before/after 完成（after 全部 ≤100 chars，機械驗證）；文法規則草案 5 條待 user 校準** |
| P6 | codex knob runtime 認證 | **deferred——主 session 執行：`codex exec` 一次即失敗（API 400：gpt-6-astra 需新版 CLI，v0.152.0 過舊），請求未達模型；靜態面 knob 已確認在場** |

---

## P1：ZCode 召回機制鑑識

### Verdict

**無 desc-matching 動態召回。** ZCode 的 memory 到達 context 只有兩條被動路徑：①明確的 `Read MEMORY.md`／`read_memory` tool call（agent/skill 主動發起），②compaction 後把先前 tool 結果重放為 synthetic 訊息。**不存在**「user message 進來→desc 配對→注入條目」的機制證據。

### 機制發現（比預期更有用）

ZCode 把 runtime 注入建模為 **synthetic user messages**，帶 `semantics.kind`／`semantics.origin`／`synthetic`／`visibility` 欄位，全部持久化在 `message` 表。全 db 17,736 條 user message 的 kind 分佈（`SELECT json_extract(data,'$.semantics.kind'), COUNT(*) ... GROUP BY`）：

| kind | origin | 數量 | 內容 |
|------|--------|------|------|
| user_prompt | real_user | 8,449 | 真實使用者輸入 |
| todo_reminder | agent_runtime | 5,795 | todo 清單狀態提醒（synthetic=1） |
| background_notification | agent_runtime | 3,209 | `<task-notification>` subagent 完成通知 |
| **system_reminder** | agent_runtime/system | **195＋15** | compaction 重放鏈（見下） |
| compact_summary | agent_runtime | 41 | compaction 摘要 |
| subagent_notification | agent_runtime | 25 | subagent 通知 |
| fork_notice | system | 8 | side-chat 繼承告知 |

**關鍵缺席**：分佈中**沒有任何 memory-recall kind**。

### system_reminder 210 條的鑑識

- 內容分類（全數 210 掃描）：file_read_warning／Read 重放 131、memory 內容 57（**全是** compaction 前曾 `Read` memory 檔的 tool result 重放，非召回）、fork 繼承/「was read before summarized」通知 22。
- 相鄰性：`system_reminder after system_reminder` 154、`after compact_summary` 41（=compaction 後重放鏈）、其餘零星。
- `time_compacting` 全 db 0 條（暫態欄位，compaction 進行中才寫）。
- 字面 `<system-reminder>` 122 parts：**全部**落在 assistant-role 的 tool parts（Read「檔案比 offset 短」警告等）；**user-role 零命中**——證明 harness 在 request 組裝時注入的 system-reminder（如本 session 收到的 agentsMd 靜態 bundle）**不持久化**，持久化的只有 synthetic message 這條管。

### 排除的假陽性（鑑識過程）

1. `data LIKE '%system-reminder%'` 636 hits——多為 memory 條目 desc/正文**提到** "system-reminder" 字樣（如 full-read-base 條目）＋本任務自身 planning session（sess_e9d91786）的自我回聲。
2. `%recalled memor%` 31 hits——全部是 sess_e9d91786（本 EP 規劃 session）的 reasoning/tool 自我回聲。
3. background_notification 7 條含 `description:`＋`memory`——全是 subagent 審查結果恰好引用 memory code 的 task-notification。

### 輔助證據

- 325 sessions 的 tool parts 提及 MEMORY.md（靜態索引靠 Read tool 載入的規模）。
- `local_setting` 24 條全為 permission/mode/reasoningLevel——**無任何 memory/recall 開關**。

### 方法論限制（如實記錄）

本鑑識覆蓋「被持久化的」。request 組裝時注入且從不落 db 的注入理論上無法單靠 db 排除；但 ZCode 已證明其 runtime 注入（todo_reminder 等 9,287 條 synthetic）**會**持久化——「唯獨 memory 召回不持久化」需要額外特設前提。佐證：本 session 自身收到的 system-reminder 靜態 bundle 只含 AGENTS.md/rules（instruction 檔），**不含任何 memory 條目**。

### 對 master EP 的意義

1. **觸發面自建**：desc 用語治理（P5）的投資報酬不能假設 harness 幫你召回——召回入口必須由 master EP 自己建（routing / 索引切片 / 明確 read 契約）。
2. **注入座位已存在**：synthetic user message 管道（todo_reminder/background_notification 同型）機制上就是「每輪可注入動態內容」的先例——master EP 若要做動態召回，ZCode 端有現成形態可循（差的是 memory source 沒接上，不是管道不存在）。
3. **compaction 重放是隱性成本**：57 條 memory 重放代表 compaction 會把舊 Read 的 memory 檔重放進 context——統一生命週期設計須把「compaction 後 memory 狀態」納入考量。

probe scripts：`s0-probes/p1_schema.py`、`p1_scan1-10.py`（含輸出 .out）。

---

## P2：OpenCode AGENTS.md 上限驗證

### Verdict

**文檔面：無上限。** 官方文檔（鏡像 crawl 2026-09-04）**未記載任何** AGENTS.md 大小上限或截斷行為。**runtime 行為：未驗證（CLI 缺場）**——`which opencode` 無結果，live probe 不做（EP 指示不在場即標未驗證）。

### 機械證據

1. CLI 缺場：
   ```
   $ which opencode
   opencode not found
   ```
2. 鏡像（`ref-docs/harness/opencode/docs/rules.md`，manifest `generated_at 2026-09-04T22:15:44+00:00`）主檔全文掃描：
   ```
   $ rg -n -i "truncat|limit|size|bytes|max\b|budget" docs/rules.md
   （零命中，rg exit 1）
   ```
3. 鏡像全域掃 `truncat`：唯一命中 `docs/cli.md:371`——session 標題用截斷 prompt，與 instruction 載入無關。
4. 載入模型文檔記載（`docs/rules.md`）：project root `AGENTS.md`＋global `~/.config/opencode/AGENTS.md`＋CLAUDE.md fallback＋`opencode.json` 的 `instructions` 陣列（支援 glob）＋remote instructions（5s timeout）——「All instruction files are combined with your AGENTS.md files」，**無 size 條款**。

### 對 master EP 的意義

- OpenCode lane 依文檔可承載大檔（無記載上限）——但這是「文檔未記載」非「驗證過無上限」；S2 條目化/切片設計不應把 OpenCode 當「有硬上限需切割」的 lane，行為驗證留待 CLI 在場時補 probe（deferred）。


## P3：muse 於 mosaic 工作區的 lane 行為（forensics only，未跑任何 muse 命令）

### Verdict

1. **mosaic 實測**：trusted mosaic worktree 的 `rules_file` text_bytes = **65,536（釘死在 cap）**；`rendered_bytes` 122,913–123,208（= user 79,287 + project 42,740 + framing ~1.1–1.2KB）→ **~47% 內容被截掉**。EP 假設「user floor＋mosaic 單檔裝不進單 64KiB lane」在現行 user 檔下**證實**。
2. **23,583 之謎已解**：它是 **ai-rules workspace session 的 rules_file lane 渲染值**（09/07 早上 user rules ~11,027B＋ai-rules AGENTS.md 12,556B＋framing），不是任何單一已知檔。鐵證＝cli log：`event="rules.context_load" ... sources=2 user_sources=1 project_sources=1 ... rendered_bytes=23583`。
3. **lane 模型修正**（三點，與 EP 已知事實有出入）：
   - 65,536 cap 是 **trusted workspace 的 rules_file lane 總預算**（user＋project 串接共享一個池），不是 user-rules block 專屬上限。
   - **untrusted workspace：cap 降為 32,000 ＋ project source 整檔跳過**（`skipped_untrusted=1`、`project_sources=0`）——trading_lab 因 `~/.config/muse/trust.json` 缺記錄（`trust.resolve outcome="untrusted" source="missing_record"`）。新發現，master EP 的 lane 表須加 trust 軸。
   - EP 已知事實「檔 79,287B 時 produced 92,940B」需要修正：92,940 是 `rendered_bytes`（全量渲染 log 值），**實際入 context 是 65,53x**（diagnostic `text_bytes`）——muse 先渲染後截斷；`skipped_oversize=0` 全程未觸發（截斷在 lane 層非 source 層）。

### 機械證據

掃描 `~/.local/share/muse/sessions/2026/09/{07,08}` 共 55 sessions（`p3_scan.py`，逐行串流，含 40MB 大檔未全讀）：

- rules_file text_bytes 時間線（顯著值）：
  - 09/07 早上（user 檔 ~11KB 時代）：ai-rules=23,583、mosaic/offline=53,701（=42,740+10,961，**未超 cap**）
  - 09/07 晚起（user 檔部署為 ~79KB）：ai-rules/mosaic/offline=65,534 → 09/08=65,536/65,535/65,533（皆釘在 cap±3B＝UTF-8 邊界微調）
  - trading_lab（untrusted）：31,999／32,000（釘在 32,000 cap）
- log 對照表（`rules.context_load` 行 vs diagnostic text_bytes）：

| session | 時間 | workspace | rendered_bytes | text_bytes | 備註 |
|---|---|---|---|---|---|
| 01a07951 | 09/07 00:43 | ai-rules | 23,583 | 23,583 | 未超 cap |
| 01a07ba2 | 09/07 11:30 | ai-rules | 12,989 | 12,989 | user 檔當時 ~0.4KB |
| 01a07ba3-ac45 | 09/07 11:31 | ai-rules | 91,307 | 65,534 | 截斷 |
| 01a07c20 | 09/07 13:48 | trading_lab | 80,139 | 32,000 | project 跳過＋32K cap |
| 01a07d6f | 09/07 19:53 | mosaic | 122,913 | 65,534 | 截斷 |
| 01a07e71 | 09/08 00:35 | mosaic | 123,208 | 65,536 | 截斷（最大 rendered） |
| 01a07f13 | 09/08 03:33 | ai-rules | 92,940 | 65,533 | EP 已知事實 92,940 的真身＝rendered |

- trust 證據：`~/.config/muse/trust.json` 列 ai-rules／mosaic_alpha／mosaic_alpha_offline_backtesting／codex-plugin-cc／grok-build-plugin-cc／muse-plugin-cc 為 trusted；**mosaic_alpha_trading_lab 缺記錄**。
- 其他 lane（session_start diagnostics）：skills_catalog ~31.6KB、memory_snapshot 327–559B、subagent_delegation 956B——muse 有 memory 注入座位但承載極小。
- 三 mosaic worktree 現檔同為 42,740B（`wc -c`）；`~/.config/muse/AGENTS.md`=79,287B（Sep 8 11:28）、`.bak`=60B（Sep 7 19:31）——user 檔 09/07 一日三變（~11KB→~0.4KB→78.6KB→79,287）。

### 對 master EP 的意義

- 統一模型必須是「**共享預算池**」語義：muse lane 的 65,536 是 user+project 合計，任何 project 檔（如 mosaic 42,740）都吃掉 65% 預算——分層設計（全域/專案/模組各限）比單一大檔更抗截斷。
- trust 是隱藏軸：同一 project 檔在 untrusted worktree 完全消失（靜默）——跨 worktree 工作流要機械檢查 trust 記錄。
- 截斷是靜默的（diagnostic 只記 action=observed status=supported；無 truncation 警告 event）——需要把 rendered_bytes vs text_bytes 差值監控起來（cli log `rules.context_load` 行可 rg）。

probe scripts：`s0-probes/p3_scan.py`（＋`p3_scan.out`）、`p3_debug.py`、`p3_debug2.py`、`p3_blocks.out`。


## P4：mosaic root AGENTS.md 組成分析

### Verdict

42,740B／379 行，11 個 top-level section。三層分類統計：**必中集 ~11.5KB、下沉目錄層 ~5.7KB、走觸發層 ~25.5KB**。重分配後 root 可收斂至 **~11KB**（−74%），走觸發層全數可被 master EP S2 條目化承接——root 的「🎯 模組觸發器」表（9,881B，42 個觸發列）**本身就是 walk-in routing 表的成熟原型**，S2 條目化＝把它轉成 desc-matching 條目庫，不是從零設計觸發面。

### 組成表（段落×bytes×分類×去向；section bytes 機械切分見 `s0-probes/p4_sections.out`）

| 段落（行） | bytes | 分類 | 去向建議 |
|---|---|---|---|
| Header＋語言＋環境（L1-8） | 474 | 必中 | 留 |
| 專案概述（L9-14） | 215 | 必中 | 留 |
| 架構文檔地圖雙軌（L15-32） | 1,828 | 走觸發 | 條目化；root 留「開桌第一檔＝SYSTEM-MAP」一行 |
| **模組觸發器（L33-85）** | **9,881** | **走觸發（特殊）** | **S2 條目化原型**——42 列觸發詞→資源映射直接轉條目；root 刪表 |
| 每日流程映射（L86-91） | 216 | 必中 | 留（已是指針） |
| 系統路線圖（L92-97） | 463 | 走觸發 | 條目化 |
| 環境配置（L98-164） | 9,459 | 混合 | 拆四份，見下 |
| — `make sync` 鐵律（L102,106） | ~1,600 | **必中（高風險）** | 留、壓至 ~800B（失敗教訓實例保留一句） |
| — 核心路徑 env 表（L108-119） | ~2,200 | 下沉 | → `mosaic_alpha/common/AGENTS.md`（已存在，23,894B）；root 留 2 行指針 |
| — NT Repo 佈局 v1/v2（L121-141） | ~4,000 | 走觸發 | 條目化（既有觸發器「NT Rust 實作」列已指向本段——改指條目） |
| — Paper Dashboard 啟動＋log 路徑（L143-154） | ~1,700 | 下沉 | → `mosaic_alpha/apps/AGENTS.md`（6,702B）；log 路徑 debug 部分併條目 |
| — 查證策略（L156-161） | ~1,200 | 走觸發 | 條目化（與觸發器表 Shioaji/NT 列重複，合併去重） |
| 專案特定規範（L165-312） | 15,055 | 混合 | 拆八份，見下 |
| — 待裁決 inbox（L167-169） | ~1,400 | 必中 | 留、壓至 ~600B |
| — Backlog board（L171-179） | ~3,500 | 必中（收窄） | 留紅線（禁手改 md、一卡一 WT、Done 留板）＋CLI 對接表；操作細節由 ai-rules kanban-board skill 承載（單一源） |
| — ai-rules 邊界（L181-183） | 250 | 必中 | 留 |
| — 命名／Import／Interval／noqa（L185-205） | ~1,500 | 必中 | 留（noqa 4 條可壓至 2 行） |
| — Volume 單位（L207-221） | ~3,200 | **必中（風控級）** | 留核心規則＋三出口邊界（壓至 ~1.2KB）；階段全表 → `adapters/sj/AGENTS.md`（22,916B） |
| — 時區慣例（L223-232） | ~1,300 | 必中 | 壓至 ~400B（＋8h 規則一行＋失敗案例一句）；→ common/time_utils docstring 承載 |
| — SJ 帳號都能下單（L234-258） | ~4,500 | **必中（風控級失敗教訓）** | 留核心事實＋禁止推論清單（~1.2KB）；功能對照表 → `adapters/sj/AGENTS.md` |
| — 版權聲明（L260-281） | ~1,500 | 走觸發 | 條目化（「新增檔案」觸發）＋既有 tools/ 版權年 lint gate 機械承接 |
| — 向後相容（L283-285） | 150 | 必中 | 留 |
| — Logging（L287-293） | ~500 | 下沉 | → `mosaic_alpha/common/AGENTS.md` |
| — 跨模組熱點 Ripple（L295-305） | ~2,800 | **必中（sizing 行風控級）** | 留 sizing/會計總量行＋Interval/Recipe/Pipeline 行（~1KB）；全表 → blueprint/architecture.md §3.4（已指針） |
| — Task labels（L307-309） | ~800 | 下沉 | 併入 Backlog 段（同屬卡操作語義） |
| UC-Driven（L313-326） | 941 | 必中 | 壓至目錄映射 3 行 |
| 開發策略＋`make test-par`（L327-349） | 1,616 | **必中** | 留（build/commit 驗證鐵律） |
| Code Intelligence LSP（L350-369） | 1,783 | 走觸發 | 條目化（stub 維護工作流；日常 `make sync` 鐵律已留 root） |
| 交易哲學（L370-379） | 798 | 走觸發 | 條目化（核心假說 3 行併入；純理論已指針 trading_philosophy.md） |

### 三層 bytes 統計

| 層 | bytes | 佔比 | 內容 |
|---|---|---|---|
| 必中集 | ~11,500 | 27% | make sync／make test-par／Volume／SJ 帳號／sizing ripple／時區／命名／Import／backlog 紅線／inbox／邊界 |
| 下沉目錄層 | ~5,700 | 13% | 核心路徑 env（→common）、Paper Dashboard（→apps）、Logging（→common）、Task labels（→backlog 段） |
| 走觸發層 | ~25,500 | 60% | 模組觸發器表 9,881＋NT Repo 4,000＋文檔地圖 1,828＋LSP 1,783＋查證 1,200＋版權 1,500＋路線圖 463＋哲學 798＋環境/規範內已指針化殘段 |

### 重分配草案（S3 消費）

1. **root 收斂目標 ~11KB**：必中集壓縮（15.1KB 規範段→約 6KB；風控級三段 Volume/SJ/ripple 全留但表格瘦身），走觸發層全退場。
2. **下沉目的地已核實存在**：`mosaic_alpha/common/AGENTS.md`（23,894B）、`mosaic_alpha/apps/AGENTS.md`（6,702B）、`mosaic_alpha/adapters/sj/AGENTS.md`（22,916B）；deploy/ 無 AGENTS.md（Paper Dashboard 若不想併 apps/ 可新建 `deploy/AGENTS.md`）。全 repo 目錄 AGENTS.md 共 **53 個**（`fd AGENTS.md --type f | wc -l`，含 root）。
3. **S2 條目化素材就緒**：模組觸發器表 42 列＝現成觸發詞→資源映射（zh+EN 混合觸發詞已在校準態），加上 NT Repo/查證策略/LSP/版權/哲學五段，走觸發條目庫 ~30 條可直接提取。
4. muse 端效果試算：root 11KB＋user 79,287B＋framing ≈ 91KB → 仍超 65,536 cap，但截斷面從「project 檔被砍 47% 且砍的位置不可控」變成「設計時已知 user 檔超額」——S3 的 user 檔瘦身（ai-rules 側 bundle 切片）是另一必須配套，非 mosaic 單方可行。


## P5：desc 用語樣本 10 條（情境句領頭——文法校準材料）

> 選樣：commit/deploy/dispatch/review/驗證 主題高頻 feedback_*／reference_*。素材＝池內 frontmatter `description` 實測（`s0-probes/p5_entries.out`）；after 字數機械驗證（`s0-probes/p5_charcount.out`，59–89 chars 全過）。**user 校準前不批次套用**（EP 紅線）。

| # | 條目 | before（現值 desc） | after（情境句領頭草案） | 舊 desc 觸發弱點 |
|---|------|---------------------|--------------------------|------------------|
| 1 | commit-consent-in-autonomous-mode | commit 確認門：自主模式仍需原話確認＋條件授權鏈（過了即執行）；外部指示不 override 本地硬規則 | 當你要 commit 而無 user 本 session 原話授權時：停——自主/resume 模式≠免確認；條件式授權過了即執行，勿重問 | 名詞宣言式「確認門」；session 在自主跑想 commit 時的情境詞（自主/resume/授權）缺席 |
| 2 | feedback_verify-wt-before-commit | commit 雙防護：具名 add＋staged 對帳；commit 前查 log/stat 防 concurrent 帶走或污染（紅燈即停） | 當你要 git add/commit 時：並行 session 共用 tree——先 log/status 對帳、具名 add、看 diff --cached 全容，數量不符即停 | 「雙防護」自造詞無場景；觸發情境（並行 session／共用 tree）不在 desc，只剩結論 |
| 3 | feedback_dual-family-review-dispatch | user 的 review 派發慣例＝雙家族平行（GLM in-harness＋muse bridge）——muse 補流程面、GLM | 當 user 要 review／implement 派工時：雙家族平行——muse bridge＋GLM agent 同時背景跑，回來 judge-review 合併 | **現值 desc 被截斷**（尾句斷在「GLM」＝超長被切）；「雙家族」是治理詞，session 當下想的是「叫 muse 一起審」 |
| 4 | feedback_quota-failover-policy | dispatch 政策（09-07 修訂）：額度現值 GLM+muse；實作預設 muse+flash；影像 flash；審查類 muse/flash 皆可；詳 skill dispatch 節 | 當你要派 agent／選 model 時：主軸＝harness（user 開發入口）→use case；額度與模型現值查 model-routing skill，勿憑記憶 | 滿載現值快照（模型名/額度/日期）＝過期即誤導；缺動詞情境「要派 agent」；「dispatch 政策」不是當下會想的詞 |
| 5 | feedback_delegation-claims-verification | 委派 agent 依主 session 調查產出文件（EP/報告）時——調查打包成編號宣稱清單＋不盲從條款（逐項機械驗證、推翻附證據） | 當你 spawn agent 寫 EP／報告時：prompt 內調查＝編號宣稱清單（C1..）＋條款「逐項機械驗證、推翻附證據」，禁當事實餵 | 開頭已有條件句但繞長（「依主 session 調查產出文件」）；缺 spawn/派發 觸發詞；「不盲從條款」治理味重 |
| 6 | feedback_relay-claims-verify-current-state | 跨 session relay/通知對「接收方現況」的宣稱常過時（傳送方 snapshot 落後）——接手第一動＝機械驗證當前狀態，勿照 relay 描述行動 | 當你收到 handoff／relay／通知要接手時：其現況描述是過時快照——第一動機械驗證磁碟/git 實況，勿照描述行動 | 主詞是名詞（relay）非情境；收 handoff 的人想「接手第一步」——desc 沒有 handoff/接手 詞（僅 relay/通知） |
| 7 | feedback_read-current-file-before-reviewing | 評論/引用任一產物檔前必讀當前檔——平行 session 可能已覆寫，context 版本記憶只是歷史非現況（「剛剛codex不是有重寫你有看嗎」實證） | 當你要 review／評論／引用產物檔時：先 Read 磁碟當前版——平行 session 可能已全文覆寫，記憶＝歷史 | 「評論/引用」非當下動詞（想的是 review/給意見）；實證引句吃掉 20 字擠壓觸發詞空間 |
| 8 | feedback_review-even-on-quick-fix | review 三則：quick-fix 也跑收尾鏈＋結構化產物驗證五條＋per-project 引用查證範圍 | 當你改動很小（quick-fix）想跳過審查時：不行——post-build 收尾鏈照跑；gate 跳過須明示，測試綠≠可免審 | 清點式（三則/五條）無情境；「收尾鏈」治理詞——session 想的是「改動小可以跳 post-build 嗎」的念頭本身 |
| 9 | feedback_dispatch-reread-governing-docs | 派發/決策當下重讀治理檔——session 記憶對快速演進域過期；看 commit 標題≠重讀條文；startup memory | 當你要派發 codex／muse／subagent 或依舊慣例決策時：先重讀現行治理檔條文——記憶與 commit 標題≠條文現況 | 「治理檔」抽象；觸發對象（codex/muse/subagent）沒列；尾詞「startup memory」孤立無義 |
| 10 | feedback_full-read-base-not-context-copy | 全檔重寫 base 必須全文 Read（context 副本會被 elide）；staleness 擋門兩型鑑別——HEAD 位移時 git diff 空是假陰性，re-Read 一律全文禁片段 | 當你要 Write 全檔重寫既有檔時：base 須本 session 全文 Read——context 副本會被 elide，片段/diff 空是假陰性 | 兩主題擠一條（重寫 base＋staleness 鑑別）把觸發詞推到第二句；session 當下的動作念頭是「Write 覆寫這個檔」 |

### desc 文法規則草案（S1 lint 候選，3-5 條）

1. **條件句領頭**：desc 第一分句必為「當你要〈任務動詞〉…時」形（lint：開頭 pattern `^當你`）；禁名詞宣言式（「XX 三則」「XX 門」「XX 政策」）。
2. **觸發詞雙語覆蓋**：desc 內至少含 1 個 session 當下會想的 zh 動詞＋1 個 EN 術語（commit/add、spawn/派、review/審查）；治理自造詞（雙防護／收尾鏈／治理檔）不得作為唯一觸發詞。
3. **一條一事實**：兩主題擠一條會稀釋觸發詞——desc 內出現第二個獨立情境即拆條（merged 條目驗收檢查點）。
4. **現值快照禁入 desc**：模型名／額度／日期（`\d{2}-\d{2}`）等會過期值放 body 或 skill 單一源；desc 留恆常機制＋「查〈skill〉」指針（防 P3 實證的「desc 過期快照主動誤導」）。
5. **長度與引句**：≤100 chars（PreToolUse hook 上限）；實證引句禁入 desc（吃字數、非觸發詞）——lint：長度檢查＋引號字元檢查。


## P6：codex knob runtime 認證（best-effort，一次為限）

### Verdict

**deferred——主 session 執行。** live probe 一次即失敗（EP 紅線：只試一次禁重試），runtime 行為未驗證。靜態面已完成：

- knob 在場：`~/.codex/config.toml:13` = `project_doc_max_bytes = 102400`（TOML 解析過，EP 已知事實；`rg -n` 實測命中）。
- 檔案關係成立：`~/.codex/AGENTS.md` = 79,287B ＜ 102,400B → knob 生效則全檔載入；若回落 32KiB 預設（32,768B）則 79,287B 被截斷、尾端 sentinel `<!-- bundle-end -->`（實測在檔尾 40 bytes 內）不可見——判準設計有效。
- CLI 在場：`/Users/ctai/.npm-global/bin/codex`，v0.152.0。

### live probe 記錄（唯一一次）

```
$ codex exec "逐字引用你載入的全域指引（~/.codex/AGENTS.md）的最後一行…"（cwd=/Users/ctai/Github/ai-rules）
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
 "message":"The 'gpt-6-astra' model requires a newer version of Codex. Please upgrade to the latest app or CLI and try again."}}
（exit 1；完整輸出 s0-probes/p6_codex.out）
```

- 失敗點＝API 400 拒絕（CLI 0.152.0 對 `gpt-6-astra` 過舊），請求未達模型、未耗生成額度；但紅線禁重試，runtime 認證移交主 session（CLI 升級後同一 probe 可直跑）。
- 附帶觀察（對 master EP 有用）：session header 顯示 `approval: never / sandbox: workspace-write`；並出現 `warning: Skill descriptions were shortened to fit the skills context budget`——**codex 對 skill descriptions 有獨立 context budget 並自動縮短**（行為與 muse 的 lane 截斷同族，S2 條目化設計可引用）。另 `http://127.0.0.1:5555/mcp` 連線失敗（本機 MCP server 未啟）與 probe 判準無關。

### 主 session 執行指引（deferred 接手）

升級 codex CLI 後跑同一命令（cwd=ai-rules repo）：
`codex exec "逐字引用你載入的全域指引（~/.codex/AGENTS.md）的最後一行，只要那一行，不要解釋"`
- 回答含 `<!-- bundle-end -->` → knob runtime 生效（102,400B 全載）。
- 回答為檔案中段任意行／拒答 → knob 未生效或截斷在別處，需再查。


---

## 修正記錄（post-build 修正迴圈 R1——muse review 3 findings 全採）

- **F1（medium）**：`p1_scan7.py` 崩潰——原版 `substr(m.data,1,2500)` 截斷 JSON 後 `json.loads` 必炸（.out 是 traceback 非證據）。已改 SQL `json_extract` 拉欄位並重跑——四段完整輸出（per-kind 取樣＋synthetic 全文段補齊）。
- **F2（low）**：5 個孤兒 `.out` 無生成腳本——補建等值腳本（`p1_local_setting.py`/`p4_sections.py`/`p5_entries.py`/`p5_charcount.py`）重跑覆寫；出處清冊見 `s0-probes/PROVENANCE.md`。
- **F3（low）**：`p3_debug.py`/`p3_debug2.py`（hardcode 單 session 的 throwaway，被 `p3_scan.py` 取代）已刪除。
- 5.3 主審抽驗（六項 load-bearing claims）：23,583 鐵證在場（兩處 log）／下沉目的地逐 byte 吻合／knob+sentinel 在場／P5 字數 69-85 全過／P1 system_reminder=210 逐數吻合（user messages 17,736→17,747 為活 db 漂移）——**verdict 全數成立**。

---

## P5 附錄：A/B recall dry-run 結果（09-08 晚，user 指定以實證代替人工校準）

材料：`s0-probes/p5_ab_material.md`（清單 A=現行 desc／B=情境句草案；S1-S10 中性任務語境；答案 key 不隨題發）。兩家族獨立受測：

| 腿 | 模型/effort | A 命中 | B 命中 | 定性觀察 |
|---|---|---|---|---|
| GLM（flash） | lite-verify agent | 10/10 | 10/10 | B「當你要X時」與任務語句結構同構、匹配更直接（S5/S8/S10 尤明顯）；A 靠主題詞可中但多一層語義對應 |
| muse | muse-spark-1.3/xhigh（bridge task job-mts981lr） | 10/10 | 10/10 | B 領頭即觸發條件可直接對號入座；A 需先解碼術語再映射 |

**結論**：B 形態零退化＋解析成本優——支持採用情境句領頭文法（S1 lint 規則 1 的實證背書）。**方法論限制（誠實段）**：hit-rate 在 10 條乾淨材料下飽和（兩家族雙雙全中），且情境由知悉條目者撰寫（語義空間同源）；鑑別力測試留給 S1 SM-1（136 條全索引＋截斷切片＋routing 條件）。codex 腿（terra/high）待 CLI 升級後同材料補跑。

---

## P6 結案補記（09-08 晚——CLI 升級後雙探針全綠）

升級 `npm install -g @openai/codex@latest`：0.152.0 → **0.153.4**（gpt-6-astra 400 消失）。

- 探針 1（尾端 sentinel）：回答 `<!-- bundle-end -->` ✅——79,287B 檔的尾端在 context
- 探針 2（71.5KB 處 rule）：逐字回引「**核心原則**：exit code 是閘門依據，pipe 會被最後一環蓋掉。」✅——32KiB 預設下不可見的中段 rule 可見

**verdict：`project_doc_max_bytes=102400` runtime 生效，codex 側根治確認（雙探針、兩個獨立位置）。**

附帶觀察（清理候選，未動）：codex config 的 `http://127.0.0.1:5555/mcp` MCP 條目連線失敗刷屏（5555＝CRG 已退役服務——config 殘留）；「Skill descriptions were shortened to fit the skills context budget」警告＝codex 有獨立 skills context budget 且自動縮短 desc（S6 觸發面對齊的輸入）。

**P5 codex 腿：取消（user 拍板 09-08 晚）**——astra 額度成本高於此測試價值；GLM＋muse 雙腿結論已足（B 零退化＋定性勝）。另：`terra` 模型在 ChatGPT 帳號認證下不可用（API 400 實證）。

**P5 codex 腿補記（09-08 晚，user 自跑）**：前述「取消」由 user 自行執行取代——`codex exec`（gpt-5.5/low effort，54,731 tokens）＝**A=10/10、B=10/10**；觀察與另兩腿一致：「B 用『當你要／收到／改動』直接對齊使用情境，A 較像抽象索引名與壓縮描述」。**三家族（GLM flash／muse 1.3 xhigh／codex gpt-5.5）全數零退化＋定性 B 勝——文法採用的跨家族實證完備。**附註：升級 0.153.4 後 codex 預設模型為 gpt-5.5（早場同 config 為 gpt-6-astra）。
