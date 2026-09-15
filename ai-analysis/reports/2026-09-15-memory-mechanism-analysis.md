# 記憶機制總分析——拓撲／各家作法／CRUD 原則／與開發流程關係／compact 優化

> 日期：2026-09-15。單一源：`skills/memory-audit/SKILL.md`（治理全文）、`muse-plugins/memory-governance/README.md`、`rules/context-management.md`、`ai-analysis/schedule-registry.md`、`skills/compact-prep/SKILL.md`、`hooks/compact-tail-inject.py`、`skills/kanban-board/SKILL.md`、`.agents/memory/_audit-state.md`。
> 現況數字為本報告撰寫當下實測（`ls`／`rg`／`wc`），非轉抄舊報告。
> user 原問另含截斷句「哪些是 backlog card, 哪些是…」——§5 按「哪些放 memory／卡／EP／skill-rule／scratch／git」全光譜回答。

## 0. 一頁總覽

```
                    ┌─ CC auto memory ──→ 直寫主體（hooks 全套）
                    ├─ ZCode ──→ 同主體（symlink 雙跳；hooks 子集；cron 載體）
  寫入源 ───────────┼─ muse ──→ plugin 閘 → inbox → consolidation 站 → 主體
                    ├─ codex ──→ ✕ 唯讀（自家另有 ~/.codex/memories）
                    └─ 夜波／audit ──→ 收斂寫入（池 git 基線）

  主體 repo/.agents/memory（B 形態：MEMORY 常駐12條 ＋ _inventory 全量303條）
                    ├─ 開場注入：CC/ZCode 讀 MEMORY（200行/25k截斷）／muse memory_pack（120行+8KB）
                    ├─ 按需：rg _inventory → Read 條目 body
                    └─ 跨池：~/.agents/memory-spine（ai-guide 寫、他池讀；缺席降級）
```

核心設計句：**主體在 repo、單一寫入點是條目檔 frontmatter、索引是機械投影、寫入摩擦前置、存量收斂靠夜波＋稽核、跨 session 接續另有 STATE／compact-context 三層分工。**

---

## 1. 拓撲：主體、鏈路、spine（各家 harness 作法）

### 1.1 主體與 symlink 鏈（實測）

| harness | 記憶路徑 | 到主體的鏈路 | 驗證 |
|---|---|---|---|
| 主體 | `/Users/ctai/Github/ai-guide/.agents/memory/` | 自帶池 git（local-only，不設 remote） | 308 個 .md（含 `_` 前綴非條目） |
| Claude Code | `~/.claude/projects/-Users-ctai-Github-ai-guide/memory` | **目錄 symlink 直指主體**（一跳） | `ls -la` 確認 → `.../ai-guide/.agents/memory` |
| ZCode | `~/.zcode/cli/memories/projects/ai-guide-*/memory` | **雙跳**：zcode → CC 路徑 → 主體 | `ls -la` 確認 → `~/.claude/projects/.../memory` |
| Muse | project scope 原生讀主體 | 直連（`read_memory`；開場注入 MEMORY.md） | AGENTS＋inbox receipt 實證 |
| Codex | `~/.codex/memories/`（自家：MEMORY.md＋memory_summary.md＋raw＋rollout_summaries＋sqlite） | **不連主體**；讀 ai-guide 池走 `rg _inventory.md`＋Read（唯讀） | `ls ~/.codex/memories` 在場 |

含義：CC/ZCode/muse 三家**共享同一主體**（單一真相）；codex 自家另有一套（任務導向的 rollout summaries），對本池只有讀權——寫入拓撲是「三寫一讀」。

### 1.2 各家讀寫面對照

| 面 | CC | ZCode | Muse | Codex |
|---|---|---|---|---|
| 開場讀 | MEMORY.md 全文（200行/25k截斷） | 同左（同主體） | memory_pack：索引120行＋單條inline 8KB | 自家 MEMORY.md；本池不自動進場 |
| 寫 | auto memory 直寫主體（hooks 全套） | 直寫主體（hooks 子集） | 經 plugin 閘→inbox→consolidation | 禁寫本池（發現交 CC/ZCode 側） |
| hooks | PreToolUse＋PostToolUse＋Stop＋SessionStart（watch-seed＋compact-tail） | PostToolUse 在場；SessionStart(compact) 死路；SessionEnd 缺席 | PreToolUse 唯一閘（plugin）；teardown 旁路繞閘（AIR-93） | 不碰 |
| 觀測 | transcripts 進 telemetry | db.sqlite 進 telemetry | reads 不入 telemetry（盲區） | reads 不入 telemetry（盲區） |
| 特殊約束 | transcript JSONL 可供 tail 注入 | hook＝OS python3.9（禁3.10+語法）；hooks per-session 快照；description>1024 整顆 drop | 每次 plugin update 後重 approve，否則停火 fail-open | — |

### 1.3 Spine（跨池共享層）

`~/.agents/memory-spine/`：plain md＋同格式 frontmatter；**條目由 ai-guide 側寫、他池只讀**；缺席時各池回退本池不報錯（degraded 聲明）。現況僅兩檔：`index.md`（位置決議＋各池 routing 認養表）＋`reference_model-runtime-entitlements.md`（額度/訂閱現值，as-of rolling state；政策不住此）。
認養現況：ai-guide ✅／CC ✅（原生可達）／ZCode 待辦／muse ✅（主體直連）／codex 不碰確認。

### 1.4 B 形態索引（實測數）

- `MEMORY.md`：26 行（常駐 12 條＋routing），常駐面約 2,302 chars／6,000 gate。
- `_inventory.md`：315 行、303 條目（09-15 晨間 288 條→現 303，半日流入可見）。
- 類型分佈（`rg -l 'type: <t>'`）：feedback 152／project 65／reference 86。
- 排序＝type 四組 × rank（hot/core/cold，缺省 core）× 組內 mtime 新在前；mtime 重置（無 `-p` 複製）會退化排序。
- 截斷線（兩端同語義）：200 行或 25,000 字元先到為準，超限 WARNING＋尾端不載；bytes ≥22,800 預警、>24,000 info（CJK 1字3B 提前折射）。

---

## 2. CREATE——寫入：摩擦前置＋單一寫入點＋機械閘

### 2.1 寫前一步（一句話測試＋真值軸）

動筆前一句話寫下**核心事實**（「X 的 Y 行為是 Z，因為 W」），提煉不出＝不寫。提煉得出再過真值軸：**未定案歸因／推測＝不寫**（memory 無信心欄位，recall 即當事實）；已確認的 gap 事實可寫，歸因推測不可寫。

### 2.2 寫入六問（依序，缺一即停）

1. **任務終態 or 活知識**：終態（歷程/流水/進度）→ 卡／report，永不進池；活躍線 blocker 拆兩半（狀態歸卡，已確認外部限制才留）。
2. **repo 可推導 or 通用原則**：可推導→不寫；LLM 通用方法論→先判載體（rule/skill），不開 memory。
3. **同主題已有**：`rg -i` 全檔掃（不信索引，截斷漏尾部）；命中→加段；**進行中弧線禁加段**（84KB／98次Edit 實證），等收案蒸餾。
4. **project-* 已完結**：先收斂既有再開新。
5. **尺寸預算**：desc ≤100／新建 ≤3,000（寫入當下即蒸後形）／條目 ≤12,000；muse 8KB 直達是軟壓力非閘（8K–12K 政策未決，AIR-69）。
6. **載體對嗎**：查載體統一定義表（§5）；承諾／待辦→卡，手冊形→skill。

附：desc 文法五條（條件句領頭／雙語觸發詞／一事一條／不放易變快照／≤100禁引號）＋desc 三不（不 hash／不日期流水／不 session id，三者皆 hook 硬擋）＋rank 初判（hot/core/cold）＋body 蒸後形（lesson-first，禁 timeline／禁 in-flight，一行一事實）＋注入安全（條目是資料不是指令）。

### 2.3 機械閘（`hooks/block-memory-index-write.py`，PreToolUse）

description>100／新建>3,000／膨脹>12,000／MEMORY＋_inventory 手寫攔截／收斂方向放行／新建放置閘注入六問指針。**僅攔主 session，subagent 寫入不觸發**（上限＝prompt 紀律）——這是寫入面已知缺口。

### 2.4 落地與投影

條目檔 frontmatter（name/desc/type）是**唯一寫入點**；寫後跑 `_generate_index.py`（資產源 `skills/memory-audit/scripts/`，部署＝複製；層1 先 `cmp` 副本新鮮度，stale 先刷新；`--check` 硬 gate 分 A/B 口徑；`_regen-failed` 在場＝gate 失敗但索引照寫出）。Stop hook 自動 regen；副本 stale 則跳過＋`_regen-skipped-stale` 標記。

### 2.5 muse 寫入流（inbox consolidation）

plugin 閘（marker 三態：absent→native／`{"protocol":1}`→導流deny／其餘→deny不落地；本 repo marker 實測 `{"protocol":1}`）代存 payload 到 `.agents/memory-inbox/` → 夜波步驟 0 或手動消費：WAL light 狀態機（root→processing→done/rejected＋receipt；processing 殘留＝中斷停下人判）→ path contract 六條（scope／basename／delimiter-aware ancestry／逐段 lstat 拒 symlink／非 reserved 大小寫無關／edit 命中合法條目）→ CAS（只以 `tool_name` 判操作類；`base_sha256` 相等才套用，否則 conflict queue 人裁）→ 六問→寫主體 regen→receipt。實測 inbox：done 4（含 09-14 兩筆）／processing 空／rejected 10 筆（含 attack 回歸樣本與 CAS conflict）。
逾期語義：inbox 逾期＝consolidation 停擺警訊；watchdog＝daily-maintain Phase 0 雙檢查（age 連兩週期→🔴，processing 殘留/直寫立即🔴）。

---

## 3. READ——讀取：開場定額＋按需兩跳＋觀測非真值

### 3.1 三種讀形態

| 形態 | 載體 | 上限 | 含義 |
|---|---|---|---|
| 開場注入（CC/ZCode） | MEMORY.md 常駐面 | 200行/25k chars（B 形態 gate 6,000） | 只保證 12 條常駐在場，其餘不保證 |
| 開場注入（muse） | memory_pack | 索引 120 行＋單條 inline 8KB | 超 8KB 條目僅列名（兩跳讀不受限） |
| 按需檢索（三家） | `rg _inventory.md` → Read 條目 body | 無（rg 可達全量） | 真正的全量入口；走 CC 舊徑做目錄級操作需 `-L` |

codex 讀法同按需（唯讀）；spine 讀法＝直讀 `~/.agents/memory-spine/`（跨池共享現值）。

### 3.2 觀測層（telemetry reads——線索非真值）

`memory_telemetry.py reads`（90 日窗）：body Read 觀測＋zero-body-read 候選。機械豁免 hot／近 30d mtime；用途（work/maintenance/unknown）須 LLM 沿 event 重放判讀；identity 線索（rename/刪建）→ HOLD 不自動合併；`coverage_limited`（窗短／源缺）時 zero 候選只證窗內無讀。**不隨觀測改 rank／刪條目。**盲區：muse/codex reads 不入 telemetry。

---

## 4. UPDATE＋DELETE——更新與刪除：蒸餾、收斂波、稽核三分離

### 4.1 更新路徑

- **加段**：同主題命中→既有檔加段（段標保留原始 name、標 original type）；進行中弧線禁加段。
- **desc 掃尾**：夜波全池常態（>100 改寫；壓縮非截斷——被刪細節先落 body）。
- **desc 事實 drift 當晚修正**：僅 desc 層，body 歸 owner；已關閉弧線 owner-touch 失效故夜波執行（MOS-25 案例）。
- **弧結案蒸餾**（kanban 結案第三動）：本弧條目重寫為終態 facts；蒸餾＝刪 repo 已承載（逐項 rg 驗證）＋軌跡記卡，不新建歸檔檔；肥條目（>30K）派 mem-distill 隔離消化（實證 −96%／−86%）。
- **固化→濃縮同步**：經驗固化成 skill/rule 後，部分覆蓋→已承載段壓成指針；完全覆蓋→列退出候選交 user 裁，不自行刪。
- **排序鍵維護**：rank（hot/core/cold）＋mtime；結案蒸餾時併調 rank。

### 4.2 夜間收斂波（每晚 23:40，寫手腿）

波前二分（池 git 化：`git -C <pool>`；`_wave-in-progress` 在場＝上波中斷→三方對照報告，禁自動 reset）→ **池 delta gate**（`reconcile_memory_pool.py --json` 波前第一步：exit 0 開波／exit 2 先 T4-1 異常篩〔消費 reconciler output 禁重跑；三 allow：inbox done-receipt／CC hook-event／已知自產出；三無→quarantine 停波待裁〕／exit 1 停波）→ quarantine 空後看 mtime（全>30min→流入快照 commit 後開波；任一<30min→停波防撞波）→ 波次（decay 候選＋`--check`＋hot 計數＋弧線軟預警＋desc 掃尾→觸發→cluster merge→regen 至過；marker 留至波後差異處置完成）→ 波後差異處置（逐差異確認歸屬；只 stage 已確認；禁整池 reset／git clean；untracked 一律保留；待裁留 marker 停波）。`_trash` 慣例已退役。09-15 晨間實例：5 quarantine 人裁全成立流入快照 ea0ba36。

### 4.3 稽核兩級＋狀態戳

- **Full 四層**：層1 索引機械量測（`--check`＋副本 cmp＋`_regen-failed` 判讀）→ 層2 內容核實 vs repo（預設必做；每檔 3–6 load-bearing claims；verdict ✅/🟡/❌/➖；self-report discount 實跑 repro；條目多 spawn 序列一次一個，失敗降級主 session 分批）→ 層3 清理執行（user 核可後；刪前 rg 反向引用＋mtime 稽核＋多池殘留＋cluster merge 機械觸發 ≥3＋mem-distill＋收斂落點判定）→ 層4 EP/任務盤點（完成信號→清理候選；未完成交 user 逐項）→ 寫狀態戳。
- **Lite**：層1＋層2'（git log 主題→rg 命中→只核實命中）＋流入率監控（B 口徑 inventory chars；日增>300＝mini-merge 觸發；bytes≥22,800 同列候選）。
- **狀態戳** `.agents/memory/_audit-state.md`：實測 full 09-03／lite 09-13／base 97e17d5／coverage 56；last_index_chars 記 09-15 晨間波快照。
- **治理三分離**：advisory 報告→user 核可→執行；每項附機械證據。

### 4.4 對帳網與已知缺口（AIR-93）

`scripts/reconcile_memory_pool.py`：唯讀；invariant＝池 HEAD 是 approved 基線，working tree delta 即 flag；exit 0/1/2；`GIT_OPTIONAL_LOCKS=0`。已知缺口：muse runtime session 結束後以非 tool 路徑原生直寫池（teardown 學習；PreToolUse＋sandbox 皆不涵蓋；mosaic 09-14 實證；dossier 在 `ai-analysis/_tasks/09-14-air93-muse-session-end-bypass/`）；掛點＝consolidation 開頭／memory-audit 機械層。另：subagent 寫入 hook 不觸發（§2.3）；telemetry muse/codex 盲區（§3.2）；hook fail-open 窗口（plugin update 後未 approve 停火）。

---

## 5. 記憶與開發流程的關係：哪些放哪（載體全光譜）

> 判準單一源＝memory-audit「載體統一定義表」：**先判層級**（user 知識禁以 project 載體為權威源，反之亦然），**再判稀缺**（常駐→任務載入→按需檢索→零 context）。

| 內容性質 | 放哪 | 為什麼是它 | 誤置的後果（taxonomy） |
|---|---|---|---|
| 跨 session user/專案綁定事實（偏好／糾正／教訓／外部限制） | **memory 條目** | 索引常駐＋body 按需；確定才寫 | 任務終態入池（M1）／repo 可推導佔主體（M4） |
| 任務狀態／承諾／待辦／弧工作單元 | **backlog 卡** | 按需查詢不進 context；建卡即 commit；卡拼裝即 handoff | 承諾進 memory＝recall 污染（六問 Q1 擋） |
| 弧規劃／段落／進度結算 | **EP 檔** | session 按需讀；段落自足可接續 | 進度進 memory＝每 session 膨脹（禁加段） |
| 有可靠 trigger 的方法論／深層 body | **skill** | metadata 常駐＋body 按需 | 手冊形進 memory＝觸發面錯置（Q6 擋） |
| 首個有後果決策前必須在場的最小核心 | **rule** | 開場常駐最貴；三測試＋資格公式 | 通用原則進 memory＝scope 錯置（Q2 擋） |
| 模組層約束與入口 | **模組 AGENTS.md** | 路徑觸發載入 | project 知識上提 user-level（B） |
| 跨 repo user state 現值（額度/訂閱/帳號） | **spine** | 跨池共享 as-of；政策不住此 | 現值進 instruction（V）／desc 放快照（M2） |
| 中間產物／草稿迭代 | **scratch `.agent-tmp/`** | 零 context；夜掃 7d | 草稿進 memory＝stale-collision（M3） |
| 可推導事實（log/程式碼/commit） | **git repo** | rg/git 查詢零 context | 重複記憶＝正回授膨脹（08-30 56.6KB 實證） |
| 純機械判定 | **hook** | 執行時觸發零 context | 語義判斷進 hook＝假確定性（禁） |

### 記憶在流程中的掛點（何時讀寫 memory）

- **compact-prep 步驟 3**：本 session 裁決/教訓是否已入池（cluster-first），缺則補寫——compact 前最後的記憶結算點。
- **commit 2.8 memory 池對帳腿**：掃 `_inventory`＋MEMORY＋條目，命中三分歸屬（活知識錨保留／弧流水當場蒸餾／終態過）；卡未 Done 命中＝in-flight 不動。
- **結案蒸餾第三動**：本弧條目重寫終態（§4.1）。
- **flow-review memory-routing 判定**：教訓→Skill／STATE／棄。
- **STATE.md vs memory 分工**：STATE＝Last session 觀察層（卡在哪/為何轉向/起手點，覆寫）；memory＝跨 session 活知識（確定才寫）；journal 可記未定案（不觸發 memory）。
- **at/deep-work**：resume 讀 STATE；deep-work 收尾寫 STATE。

---

## 6. 現行 compact 機制全圖（放在 context 框架下看）

> 擁有權前提（codex 報告 §1）：compact 本體是 harness 擁有的黑盒，我們只能做「壓縮前外部化＋壓縮後恢復」。下圖是現行三層接續結構。

```
compact 前                    compact 本體              compact 後
（我們擁有）                  （harness 黑盒）            （我們＋hook）

compact-prep ①錨定session ─┐
②落檔 preserve-list        │                        ┌─ CC：compact-tail-inject
  .agent-tmp/compact-      ├─→ /compact ──→ 摘要 ──┤   （raw tail 20KB＋STATE 4KB，
  context-<date>.md        │    （壓掉 verbatim）     │    32KB guard，防遞迴 marker）
③memory 新鮮度檢查 ────────┘                        ├─ ZCode：死路，靠手動三動作
④請 user 跑＋提醒首句讀檔                            └─ ⑤讀 context 檔恢復脈絡
```

### 6.1 compact-prep（skill，LLM 判斷層）

六步：①db 錨定 session（join user-role part 防誤中 subagent）②掃全 session 落 preserve-list 檔（目標/決策/已讀改路徑/測試 verbatim/懸掛動作/計數；禁時序流水）③memory 新鮮度檢查（裁決/教訓入池沒）④交付確認＋請 user 跑 /compact＋提醒首句讀檔 ⑤恢復 ⑥清理。搭檔 compact-audit（重大弧線選配：乾淨 agent 獨立提煉 15–20 要點 vs 摘要三色比對；數 M tokens 高成本；摘要以 user-role 注入須排除）。

### 6.2 compact-tail-inject.py（CC 端機械 verbatim 復原層）

SessionStart(compact) hook（settings.json matcher=compact）：由 transcript JSONL 唯讀取壓縮前最後幾輪原文（掃描窗口 60 entries，tail 20KB＋STATE 4KB，總 guard 30KB<32KB 協議上限）＋STATE.md 注入；`INJECT_MARKER` 跳過上代注入防連續 compact 遞迴膨脹；fail-open（任何錯誤空輸出 exit 0）。**ZCode 端不註冊**（compact 不派發 SessionStart，08-24 L4 終驗死路）。

### 6.3 三層接續分工（memory／STATE／compact-context）

| 層 | 生命週期 | 內容 | 消費者 |
|---|---|---|---|
| memory 條目 | 跨 session durable | 確定的活知識（教訓/偏好/約束） | 未來所有 session（開場＋按需） |
| STATE.md | Last session 觀察層（覆寫） | 卡在哪/為何轉向/起手點 | 下一個 session 開場（at resume） |
| compact-context 檔 | 單次 compact 接續（ephemeral，用完即棄） | preserve-list：verbatim 交付物＋懸掛動作 | 壓縮後的新 context 首句 |

三層互不取代：memory 不收任務終態、STATE 不記完成度（走 git＋卡面）、compact-context 不進任何索引。

---

## 7. 對照：外部 compaction 報告 vs 現行機制

> 外部報告＝`~/Downloads/context_compaction_recommendations.md`（已查證）＋本 repo codex 報告 §10。對照只列「有／無／半」。

| 外部建議 | 現行對應 | 狀態 |
|---|---|---|
| append-only transcript | session DB（ZCode sqlite／CC JSONL／codex rollout） | ✅ 有（harness 擁有，可查不可控） |
| recent raw tail lossless | CC tail-inject（20KB）／ZCode 無 | 🟡 半（ZCode 缺） |
| incremental checkpoint（prev summary＋cold delta） | 無（harness 黑盒；我們只有外部化檔） | ❌ 無 |
| deterministic GC（stale tool output 先丟） | 無（harness 內） | ❌ 無 |
| verification 層（Gemini 式 v1→verifier→v2） | compact-audit（重大弧線選配，高成本） | 🟡 半（門檻太高，例行不跑） |
| semantic boundary trigger | 無（何時 /compact 全憑感覺） | ❌ 無 |
| artifact index 獨立於 summary | 部分：EP/卡/git 承載事實；但無機械 artifact 追蹤 | 🟡 半 |
| compact state 可重寫非累加 | STATE.md 覆寫制 | ✅ 有 |
| durable memory 少＋provenance | memory 六問＋蒸餾＋spine | ✅ 有 |
| summary＝routing index（可回查 transcript） | compact-context 檔無 transcript 錨（只有 session id）；audit 時摘要本體未存檔 | 🟡 半 |
| window 代際鏈（window_number＋previous 指針） | compact-context 檔只有 date 後綴，無代際鏈 | ❌ 無 |
| pre/post compact 兩鉤 | pre 無（靠人工程序）；post 僅 CC 有（tail-inject） | 🟡 半 |

---

## 8. 優化方向（供思考的選項，非 verdict）

按「成本由小到大」排；每條標動哪個現有物。

1. **compact-context 檔加代際鏈**：檔頭加 `window_number`（本 session 第幾次 compact）＋`previous_file` 指針（codex 報告 §10.4 同條）。純約定零依賴；compact-audit 三色比對可按 window 歸檔。動：compact-prep skill。
2. **摘要本體存檔**：compact-audit 跑時把壓縮摘要本體與外部化檔放同一目錄，形成「摘要＋落檔」成對材料（codex 報告 §10.8 同條）。動：compact-prep 搭檔段。
3. **pre/post 標定**：compact-prep 步驟按 pre（②落檔）／post（⑤恢復）標好；若 harness 將來開鉤整段搬（codex 報告 §10.3 同條）。動：compact-prep skill。
4. **換模型先 compact 紀律**：換主力模型後第一個大任務前先 compact 一次（codex 報告 §10.9 同條）。動：model-routing 或 at skill 操作段。
5. **verification 常態化降級版**：compact-audit 全量太貴（數 M tokens），可做輕量版——只對「懸掛動作＋verbatim 交付物」兩類做摘要存在性 grep（機械，不跑 LLM 提煉）。動：新增 script＋compact-prep 搭檔段。
6. **semantic boundary 指引**：何時 /compact 從憑感覺改為指引——subtask 完成／test 全綠／決策剛定時壓；debug 半程／多檔改一半／root cause 未明時不壓（外部報告 §11 縮減版；hard 阈值我們拿不到用量計，做不了，維持人工判斷）。動：compact-prep 邊界段。
7. **ZCode tail 缺口補償**：ZCode 無 post 鉤，compact-context 檔是唯一接續材料——考慮把 tail 預算寫進步驟 2（最近 N 輪原文逐字附錄成段），讓 ZCode 檔自帶 raw tail。代價是檔變大；與「禁時序流水」原則的衝突需裁決。動：compact-prep skill（需 user 拍板原則）。
8. **transcript 錨**：compact-context 檔內關鍵交付物附 transcript 座標（如 `message.sequence` 範圍、檔行），讓回查有路徑（routing index 化）。動：compact-prep 步驟 2＋db 查詢配方。
9. **memory 新鮮度檢查半自動化**：步驟 3 目前全靠 LLM 自覺——可加機械前置：列本 session 新寫/改的 memory 檔（`fd --changed-within`）＋本弧卡 notes 未蒸餾段落，LLM 只判「夠不夠」。動：compact-prep 步驟 3。
10. **不做的**：deterministic GC、incremental checkpoint、用量計 trigger、server 端壓縮——皆 harness 內能力，無對應施力點；列此說明已看過非遺漏。

---

## 9. 改善思考入口（記憶機制本身的待問）

1. subagent 寫入 hook 不觸發——prompt 紀律的實際違規率多少？telemetry attribution 能否量化（actor×entry 排行）？
2. muse session-end bypass（AIR-93）根治 vs 維持對帳網偵測——teardown 直寫的頻率與內容性質值得先量測再定。
3. B 形態常駐 12 條的選擇標準與輪替機制——誰決定進出？目前是 user 凍結清單＋手動。
4. 8K–12K 區間政策（AIR-69）未決——muse 直達面 vs 寫入閘的落差要不要收斂？
5. 流入率：inventory 09-15 晨間 288→現 303（半日 +15）——夜波收斂速率跟不跟得上？lite 流入率監控（>300/day）會不會響？
6. telemetry muse/codex 盲區——observer 缺兩家，decay/attribution 的結論要打幾折？
7. 載體誤置 taxonomy（A/B/V/M1–M5）的現況分佈——下次 full audit 可出各類計數，看哪類是最大宗。

*附：靜態盤點＋機制理解，數字以報告內註明的實測命令為準；repo 演進後以各單一源 skill／池現況為準。*
