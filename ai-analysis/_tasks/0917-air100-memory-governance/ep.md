# AIR-100 memory 寫入治理——enforcement 落地＋staging＋存量收編（full tier standalone EP）

> **ep_type**: implementation
> baseline: `ece1dcf74486403493b7573ea7166ef0774e0c2f`（EP 撰寫當下 main HEAD）；開工時 main 已前進（≥`1613113`）——dirty 與 baseline 以**開工日 `git status`/`git log -1`** 重刷為準，不沿用本聲明。
> 追蹤卡：`backlog/tasks/air-100 - *.md`（In Progress）；整併 AIR-90（P3 後綴擋）／AIR-83（P4 夜波——D5 退役後本 EP 不含波次腳本改造）。

## 實作總覽

本 EP 是 AIR-100 治理弧的 enforcement＋staging＋存量收編落地段。前期調查（guides-refactoring 弧，產物 digest＝`ai-analysis/reports/guides-refactoring/air100-handoff.md`）與裁決已完成；已完成項見下方「已完成不重做」節。

段落：**Segment 0（runtime 探針，架構凍結前跑完）→ S-A codex path-deny hook → S-B 狀態後綴擋 → S-C NotebookEdit dead-matcher 處置 → S-D staging 落地（auto-memory 導流）→ S-E approve-drift monitor cron**。順序原則＝先堵後清（codex 意見第 2 點）：cutover snapshot（S-D 內）→ 堵新污染源 → 補 forward guard（S-A/B/C）→ 存量處置（S-D）→ reconcile acceptance（收尾）。

## 已裁決勿重辯（caller＋三顧問共識＋user 0917 拍板）

- **D1 admission 唯一化**：consolidation＝唯一入池權威；所有背景 writer divert-or-stage。
- **D2 enforcement AC 強制 closure 三層閘**：已入册 `skills/acceptance-evidence/SKILL.md`「Closure 三層閘」節——本 EP 各 enforcement 段 AC 直接消費該契約（自我示範）。
- **D3 crash 分級**：品質門 fail-open、admission 門 fail-closed。
- **D4 codex 補最小 path-deny-all**：tool 名禁照抄 `Edit|Write`，探針先行（Segment 0）。
- **D5 退役快照結算**：夜波 cron 已改 D5 版（今晚零工程、停波＝正確行為）——本 EP 不含波次腳本改造。
- **subagent＝detected-only**：接受現況＋spawn contract 禁碰池約束（本 EP 收尾落地 agent-workflow skill——見收尾步驟 2）。
- 另：air-100 卡 Plan〔已決策勿重辯〕①–⑦（auto-memory 機制定論／staging＋單向晉升／存量範圍含污染基線重審／清洗標的／AIR-90·83 整併／memory-audit:147 訂正／池鐵律）以卡面為準，此處指針引用不重述。

## 已完成不重做（禁再列 AC）

1. **S1 sensor `--source` 修復**：`hooks/memory-write-sensor.py`＋CC/ZCode hooks 註冊＋範本，合成 payload 驗證 PASS。
2. **muse plugin 從 canonical 重裝＋re-approve**：source.path 已正、`trusted_enabled`。
3. **closure 三層閘入册**：AIR-115 S0（`skills/acceptance-evidence/SKILL.md`）。
4. **rule 第一線強化**：Q1 禁令＋desc 三不進 always-on。
5. **夜波 cron D5 改寫**（退役快照結算）。
6. **91 條收編分診表**：`.agent-tmp/guides-refactoring/consolidation-triage.md`（收編 35／修寫 30／退役 22／拆分 4）——等 user 人裁後於 S-D 執行。

## UC 盤點

元專案（docs mode 對照）：掃受影響命令/rules 清單，無 library Capabilities 表格。

### Backlog 關聯
- 本 EP 對應卡：AIR-100（In Progress）。相鄰卡：AIR-93（Done，muse teardown 繞閘）、AIR-63（inbox pending 覆層，feature）、AIR-85（Done，projection）。
- 自動建卡：無新增 UC 需建卡（本 EP 全部能力由 AIR-100 承接；下游「跨 harness 統一安裝包」已建 AIR-116）。

### 卡 AC 對照（A1–A6）
- **A1**：原「第五寫入源＋夜波 quarantine allow-list」經 D1（admission 唯一化）＋D5（夜波退役）後語義失效——auto-memory 導流由 S-D staging＋AC-D5 晉升程序條文承接；**回寫卡 A1**：範圍變更為「memory-audit 含 staging／晉升條文（AC-D5 rg 可驗）」，quarantine allow-list 項隨 D5 作廢。
- **A2**：S-D AC-D2/D3 承接（41＋19 已擴為 91 條分診表口徑——數字變更同步回寫卡面）。
- **A3**：後半（實測一筆）＝S-B AC-B3；前半「成對殘留偵測跑一輪」**不另做獨立掃描**——由 S-D 處置表銷帳（每條 disposition 對帳即成對殘留偵測）＋reconcile exit 0 吸收，**回寫卡 A3** 註明此吸收路徑。
- **A4**：D5 退役後 moot（夜波半機械化不再需要），**回寫卡 A4** 宣告隨 AIR-83 整併＋D5 作廢。
- **A5**：**本 EP 承接**——收尾步驟 2 memory-audit 清單加一行：「訂正 ：149 stale 句（AIR-85 已 Done、projection 在場）——刪『尚未落地…不得據此排除』改為『projection 已落地（AIR-85），path-scoping 排除判準照 residency 三測試』」。
- **A6**：S-D AC-D6 承接。

### SYSTEM-MAP 影響
- 無 SYSTEM-MAP.md，跳過（元專案正當跳過）。

### 掃描範圍
- `AGENTS.md`（memory 主體／Muse memory 節）、`rules/context-management.md`、`skills/memory-audit/SKILL.md`、`skills/acceptance-evidence/SKILL.md`（closure 三層閘）、air-100 卡。

### 同主題 memory 條目（結案蒸餾範圍）
- `rg` 主題詞（memory governance／auto-memory／reconcile）掃池：`reference_muse-code-cli-facts`、`memory-pool-89-adjudication-pending`（隨流入快照移除）等命中——多數已在 91 條分診表列管（收編／修寫／退役由 S-D 逐筆消化，本 EP 結案蒸餾第三動只登記不重複處置）。

### 既有 UC 狀態
| 能力 | 狀態 | 來源 | 影響 | 說明 |
|------|------|------|------|------|
| memory 寫入防護（主 session Write/Edit） | ✅ | hooks/block-memory-index-write.py | 不變 | 已 prevented，本 EP 補缺口不動主體 |
| 狀態後綴硬擋 | ❌ 零實作 | air-90 決策文本 | 新增（S-B 落地） | closure 反例（skills/acceptance-evidence/SKILL.md「AIR-90 狀態後綴」節） |
| codex 對池唯讀（機械化） | ❌ unsupported | AGENTS.md 紀律行 | 新增（S-A 落地） | 紀律→最小 path-deny |
| auto-memory staging＋單向晉升 | 📋 | air-100 卡 Plan | 新增（S-D 落地） | 形態 (a)/(b) 二選一 |
| muse approve 漂移監控 | ❌ 缺件 | mech-synthesis §2 D3 | 新增（S-E 落地） | 四件套唯一缺件 |

### 新增 UC
| 能力 | 狀態 | 實作路徑 |
|------|------|---------|
| codex 寫池 path-deny | 📋 | `hooks/codex_memory_path_deny.py`＋`~/.codex/config.toml` 註冊 |
| 狀態後綴條目擋＋inbox 消費側對等檢查 | 📋 | `hooks/block-memory-index-write.py`＋memory-audit skill |
| staging（auto-memory 導流）＋91 條 reviewed admission | 📋 | symlink 手術＋consolidation 程序（S-D） |
| approve-drift monitor | 📋 | `scripts/muse_approve_monitor.py`＋cron |

## Scenario Matrix

| # | 場景 | 觸發 | 預期行為 | Checkpoint | 對應能力 |
|---|------|------|---------|------------|---------|
| SM-1 | codex session 嘗試寫池內條目 | codex 寫入工具對 `.agents/memory/` 路徑 | PreToolUse path containment deny＋stderr 回報指針「交 CC/ZCode 側」 | hook log／deny receipt | codex 寫池 path-deny |
| SM-2 | 新建條目帶狀態後綴 | Write `*-inflight.md` 等六後綴至池 | exit-2 硬擋＋stderr 指引 | hook receipt | 後綴擋 |
| SM-3 | 合法新條目（無後綴、desc 合規） | Write 正常條目 | 放行（positive control 不得過擋） | hook receipt | 後綴擋 |
| SM-4 | inbox 消費側遇帶後綴轉寫 | consolidation 轉寫時 source 檔名帶後綴 | 對等檢查擋下（非機械保證的語義面須文件化判準） | memory-audit 條文＋實測一筆 | 後綴擋（消費側） |
| SM-5 | NotebookEdit 寫池 | matcher 觸發 NotebookEdit 對池路徑 | 處置後 matcher↔handler parity：要麼真擋要麼 matcher 不再宣稱 | parity assertion 測試 | NotebookEdit 處置 |
| SM-6 | ZCode auto-memory 背景寫入 | session 結束背景蒸餾 | 寫入落 staging（永不自動進池／進 inbox）；池 HEAD 保持 approved | staging 目錄＋reconcile exit 0 | staging |
| SM-7 | staging 前置驗證（關閉 auto-memory 回退） | ZCode UI 關 Memory 開關後新 session | 回退原生 index 無痛（pull 路由不受影響） | Segment 0 探針 | staging |
| SM-8 | muse plugin update 後未 re-approve | content update 後 runtime 閘靜默下線 | monitor cron 偵測 `trusted_enabled` 消失並告警 | cron 輸出 | approve-drift monitor |
| SM-9 | hook crash（guard 例外路徑） | 注入 crash payload | 品質門非阻斷（fail-open）／admission 門 deny（fail-closed）——依 D3 分級 | crash 注入測試 | crash 分級（消費：AC-B7） |
| SM-10 | 91 條存量逐筆處置 | user 人裁分診表後 | 收編 commit／修寫／退役各有留痕；池 git 僅增補 | 處置表＋git log | reviewed admission |

## 測試規劃段（TC 凍結）

> author_family: glm（ZCode 側 authoring）。oracle 獨立性＝closure 三層閘契約＋實測命令輸出，非待測實作自證。amendment 附錄見檔尾。

| TC-ID | claim | Given-When | oracle（predicate） | oracle_source | evidence class | uncovered |
|-------|-------|------------|---------------------|---------------|----------------|-----------|
| TC-1 | codex deny 對池路徑 containment 生效 | 註冊後合成 payload（Segment 0 探得的 tool 名）寫池內路徑 | P1-1 exit/deny 訊息出現；P1-2 池外路徑放行 | codex hook 官方語義＋closure 三層閘 Behavior 層 | L4 | codex 端 actual-runtime（需 codex session 實跑，Segment 0/驗收各一次） |
| TC-2 | 後綴擋 negative | Write 新建 `x-inflight.md` 於池 | P2-1 exit 2；P2-2 stderr 含後綴指引 | air-90 決策文本（卡 `:20`）＋D2 契約 | L4 | CJK 緊貼邊界（歸夜間掃尾，同現有三 pattern 邊界） |
| TC-3 | 後綴擋 positive control | Write 新建無後綴合規條目 | P3-1 exit 0 放行；P3-2 既有條目「收斂方向」編輯不受影響 | closure 三層閘 Behavior 層（雙向） | L4 | — |
| TC-4 | 後綴六枚舉全涵蓋 | 單元測試逐一後綴 | P4-1 六後綴各一 case 全擋 | air-90 卡 `:20` 決策文本（六後綴枚舉凍結源） | L2 | 近義新後綴（新增走 amendment） |
| TC-5 | NotebookEdit parity | 處置落地後跑 parity assertion | P5-1 matcher 字面集合＝handler 分支集合 | closure 三層閘 Existence 層反假綠 | L2 | NotebookEdit 實跑（本 seat 無工具——標 unsupported 並文件化） |
| TC-6 | staging 後池基線恢復 | symlink 手術後 auto-memory 寫入 | P6-1 寫入落 staging 非池；P6-2 reconcile 對池 exit 0 | reconcile腳本不變式（HEAD＝approved） | L4 | 背景寫入者是否寫 index（Segment 0 P0-3 探針涵蓋） |
| TC-7 | approve monitor 告警 | `trusted_enabled` 缺失時（mock inspect 輸出） | P7-1 非零 exit／告警行 | muse plugins inspect 語義（AGENTS.md 運維節） | L2 | monitor 自身 cron 掛點失敗（launchd 面，人工檢查） |

## 段落 0：runtime 探針（架構凍結前跑完——所有段落設計前提）

> handoff 九條 runtime validation 中未完成項（#1 main live 部分／#2 NotebookEdit／#5 teardown live／#6 後綴擋前置由 S-B 自帶／#8 轉寫稽核）＋ S-A/S-D 專屬前置。已跑項（#3 subagent 負對照、#4 muse 三斷言、#7 codex 讀面）不重跑。

### 探針清單

| # | 探針 | 方法 | 產出餵給 |
|---|------|------|---------|
| P0-1 | **codex 寫入 tool 名實測** | codex session 內以寫入工具觸發（或 sandbox 合成 payload 對 `~/.codex/config.toml` 註冊的 matcher 逐字驗證）；記下實際 `tool_name` 字串 | S-A matcher（禁照抄 `Edit|Write`） |
| P0-2 | **codex hook 機制確認** | 查 codex 官方文檔（`ref-docs/harness/codex/`）＋config.toml hooks 段語義：事件鍵、deny 語義（exit code／輸出協定） | S-A 註冊形態 |
| P0-3 | **ZCode auto-memory 關閉回退驗證** | ZCode UI（設定→通用→Memory，預設關、v3.6.4+、僅新 session 生效）關閉→新 session 觀察：(1) 開場注入是否回退原生 index（無痛）；(2) 背景寫入者是否停寫；(3) 若改指 `memory-auto/`，其 MEMORY.md 是否被背景寫入者覆寫（air-100 notes 0915 P0 項 1-3） | S-D staging 形態 (a)/(b) 拍板輸入——**落地當日記錄理由** |
| P0-4 | **NotebookEdit dead-matcher 確認** | 合成 NotebookEdit payload 餵 `hooks/block-memory-index-write.py`，確認直落 exit 0（dead-matcher 假設成立） | S-C 處置寫死理由 |
| P0-5 | **主 session Write live 重放**（handoff #1 未完成部分） | generator 池內合成七形 payload（desc>100／hash／日期／sess_／新建>3K／膨脹>12K／放行對照）——CC 或 ZCode 端實跑一次 tool 事件（非 pipe 餵 script） | 三層閘 Behavior 層基線；S-B 驗證複用本形 |
| P0-6 | **consolidation 轉寫稽核**（handoff #8） | 抽查最近一次 inbox→pool 消費的 git log，確認轉寫由主 session tool 發起（非背景） | S-D admission 程序可信度 |
| P0-7 | **teardown 直寫偵測鏈驗證**（handoff #5） | 手放檔模擬直寫→`reconcile_memory_pool.py` exit 2；（可選）真 muse session-end 重放 | 收尾 reconcile acceptance 前置 |

**致命先驗**：P0-1/P0-2（codex hook 語義）——若 codex hooks 不支援 PreToolUse deny 形態，S-A 整段重設計（改 detection-only＋擴大 reconcile 面）。P0-3 若背景寫入者會 write-through index，staging 形態 (b)/(c) 受限、退 (a)。

---

## S-A｜codex path-deny hook

### Context
- 現況：codex 對 memory 主體（`/Users/ctai/Github/ai-guide/.agents/memory/`）「唯讀」僅紀律（AGENTS.md 觀察池路由節），`~/.codex/config.toml` 零 memory registration（mech-synthesis §1 表「codex 寫池＝unsupported」）；無寫入實證（71 檔 485 提及全為讀，FP P6）但一旦發生＝unattributed external 污染。
- D4 已裁決：補最小 path-deny-all（XS，約 20-30 行）；matcher tool 名以 Segment 0 P0-1 實測為準。
- UC 引用：實作「codex 寫池 path-deny」。
- 依賴：Segment 0 P0-1/P0-2 前置；無段落間依賴（與 S-B/S-C 平行可）。
- 語義約束：無（獨立新 script）。
- 需求邊界繼承：無 /spec。
- 基礎設施盤點：`hooks/` 既有 hook 形態（stdin JSON、exit 2 deny、stderr 指引）＋`hooks/zcode-registration.json` 範本慣例；codex 端 config 語義由 P0-2 釐清。
- 依賴錨點：新檔 `hooks/codex_memory_path_deny.py`（定義端＝本段新建；消費端＝`~/.codex/config.toml` hooks registration）。
- 技術選型：獨立小 script（不擴 block-memory-index-write.py——跨 harness 單一來源但註冊端隔離，避免 CC/ZCode 端吃到 codex 專屬路徑判斷）。成功標準＝closure 三層閘全綠 receipt。

### 核心實作要點
- 邏輯：stdin JSON 取寫入目標路徑 → `Path.resolve()` 是否落池根（含 memory-inbox、memory-auto staging）→ 命中即 exit deny＋stderr 回報指針「主體對 codex 唯讀——有該寫的發現交 CC/ZCode 側 session（AGENTS.md 觀察池路由節）」；未命中 exit 0。
- **admission 門 fail-closed**（D3）：路徑解析失敗／stdin parse error → deny（非放行）——此門是 admission 面（防污染入池），非品質門。
- 註冊：`~/.codex/config.toml` 加 hooks 段（語義按 P0-2；不觸 repo 外其他 config 鍵）。

### Pseudo Code
```
hooks/codex_memory_path_deny.py
  main():
    data = json.load(stdin)  # parse 失敗 → exit 1（fail-closed 家族，deny 並 stderr 說明）
    file_path = data[tool_input][file_path]  # 鍵名依 P0-1 探得 payload 形狀
    if not file_path: exit 0
    root = Path(POOL_ROOTS).resolve()  # .agents/memory、.agents/memory-inbox、.agents/memory-auto
    if any(root in Path(file_path).resolve().parents): 
        stderr("主體對 codex 唯讀…交 CC/ZCode 側")
        exit <deny code 依 P0-2>
    exit 0
```

### 驗證策略（closure 三層閘 receipt）
- **AC-A1（Existence）**：`rg -n "memory" ~/.codex/config.toml` → registration 條目在場（wiring 錨）；`ls hooks/codex_memory_path_deny.py` → 存在；`rg -c "resolve|parents" hooks/codex_memory_path_deny.py` → containment 邏輯可達。
- **AC-A2（Invocation）**：registration 錨（config.toml 行號）→ handler 入口（script main）鏈結成立——receipt 記兩端 file:line。
- **AC-A3（Behavior negative，TC-1 P1-1）**：合成池內路徑 payload 餵 script → deny exit＋指針 stderr 出現。
- **AC-A4（Behavior positive，TC-1 P1-2）**：池外路徑（如 `/tmp/x.md`）payload → exit 0 放行。
- **AC-A5（failure-path，D3）**：malformed stdin → fail-closed（deny 或 loud 錯誤，非靜默放行 exit 0）。
- **AC-A6（actual-runtime）**：codex session 實跑一次寫池嘗試 → deny receipt（codex 端證據——靜態接線不可替代）。
- 已知未覆蓋：codex 端 Bash redirect 直寫（hook 面不可見，與 CC/ZCode 同邊界——reconcile detected 兜底）。

---

## S-B｜後綴擋 P3 落地（air-90 決策、air-100 P3 承接）

### Context
- 現況：`hooks/block-memory-index-write.py` 全文零 stem-suffix 邏輯（273 行入册實測；closure 反例節）——air-90 卡面 Done 但 enforcement 零實作。
- 決策：新建條目 stem 帶狀態後綴（`-pending`／`-inflight`／`-in-flight`／`-landed`／`-done`／`-closed` 六枚舉，凍結於 TC-4）→ exit 2。
- UC 引用：實作「狀態後綴條目擋＋inbox 消費側對等檢查」。
- 依賴：無段落依賴；與 S-A 平行。
- 語義約束：與 S-C 共享「matcher↔handler parity」測試形態（同測試檔消費）。
- 基礎設施盤點：`hooks/block-memory-index-write.py` 既有結構（`is_entry_file` 判準、Write/Edit 分流、exit 2＋stderr 慣例）——後綴檔在到達 desc 檢查前就該擋（更上游）。
- 依賴錨點：`is_entry_file` → 定義 `hooks/block-memory-index-write.py:91`／消費 `hooks/block-memory-index-write.py:162`；新增分支插在 `:162`（is_entry_file 通過後、desc 檢查前）。
- 成功標準：三層閘全綠＋單元測試六後綴全涵蓋。

### 核心實作要點
- 新 `STEM_SUFFIX_RE = re.compile(r"-(pending|inflight|in-flight|landed|done|closed)$")` 對 `Path(file_path).stem` 判；新建（`cur_len==0`）且命中 → exit 2＋stderr 指引（「弧狀態屬卡/report 域，非記憶定義域——重命名後再寫，內容歸屬見六問 Q1」）。
- **只擋新建**：既有條目收斂編輯（含改名退役流程的暫時寫入）放行——存量處置（S-D）不被迫改走 `--no-verify` 逃生口。
- **inbox 消費側對等檢查**（非機械保證，文件化判準）：memory-audit skill「Inbox 消費」節補一條——consolidation 轉寫時 source 檔名/擬定 name 帶後綴即停手改寫（轉寫是間接過閘，機械面只在主 session Write——對等檢查把同一 invariant 延到人/LLM 判斷面）。
- Edit 面：Edit 無法改檔名，後綴只能在 Write（新建）出現——Edit 分支不重複實作（parity 明載）。

### Pseudo Code
```
# hooks/block-memory-index-write.py 插在 :162（is_entry_file 通過後、desc 檢查前）
STEM_SUFFIX_RE = ...
if cur_len == 0 and STEM_SUFFIX_RE.search(target.stem):
    stderr("[Hook Blocked] 新建條目檔名含弧狀態後綴…")
    exit(2)
# 單元測試：tests/test_block_memory_hook_suffix.py——六後綴各一 negative、無後綴 positive、
# 既有條目（cur_len>0）帶後綴編輯放行 positive、stem 邊界（done-requested 類前綴含 done 但尾碼不同）不誤傷
```

### 驗證策略（closure 三層閘 receipt）
- **AC-B1（Existence）**：`rg -n -e "STEM_SUFFIX" -e "inflight" hooks/block-memory-index-write.py` → 兩 pattern 皆命中帶行號；單元測試檔存在。
- **AC-B2（Invocation）**：CC/ZCode hooks registration 既有 matcher `Edit|Write|NotebookEdit` → handler 分支可達（既有接線不動，receipt 引現有 registration 錨）＋單元測試直接呼叫分支。
- **AC-B3（Behavior negative，TC-2）**：池內合成新建 `test-x-inflight.md` payload → exit 2。
- **AC-B4（Behavior positive，TC-3）**：無後綴合規新建 → exit 0；既有條目收斂編輯 → exit 0（不得過擋）。
- **AC-B5（parity／枚舉全涵蓋，TC-4）**：單元測試跑六後綴 case 全綠（`uv run pytest tests/... -k suffix`）。
- **AC-B6（消費側條文在場）**：`rg -n "後綴" skills/memory-audit/SKILL.md` → Inbox 消費節對等檢查條文＋一筆實測（轉寫模擬帶後綴 source → 停手證據記卡 notes）。
- **AC-B7（failure-path，D3）**：crash 注入——malformed stdin（非 JSON）與強制例外（如 monkeypatch `Path.stem` raise）各一 → 記錄實際 exit/放行行為＋log 訊號可觀察證據。門別＝admission 意圖門；載體 crash 語義 fail-open（hook 協定事實，`block-memory-index-write.py:36` 自載）為已知缺口，偵測兜底＝reconcile porcelain delta（detected），coverage matrix 後綴 invariant 格 crash 面註記此缺口。
- 已知未覆蓋：CJK 緊貼檔名（路徑面罕見）、Edit 改名不存在、subagent/Bash 面（全域邊界，reconcile 兜底）。

---

## S-C｜NotebookEdit dead-matcher 處置

### Context
- 現況：CC/ZCode 註冊 matcher 含 `NotebookEdit` 字面，但 `hooks/block-memory-index-write.py` 只有 `Write`／`Edit` 分支——NotebookEdit 直落 `sys.exit(0)`（dead-matcher 偽裝 covered，mech-synthesis §1「unsupported」）。
- 處置二擇一（**寫死理由，落地時不重開**）：本 EP 選 **(a) 移 matcher 字面**。理由：池治理場景 NotebookEdit 零實測流量（.md 條目非 notebook 域）、script 補 `.ipynb` 分支＝為零流量路徑加維護面；matcher 宣稱範圍收縮到真實擋面，coverage matrix 誠實化。若 P0-4 顯示 payload 未直落 exit 0（handler 對 NotebookEdit 有任何非放行行為）→ 改走 (b) 補同形分支；『實際 NotebookEdit 流量』觀測列 out-of-scope 文件化（script docstring 記），不作觸發條件——二擇一以探針結果定，落地當日記錄。
- UC 引用：更新「memory 寫入防護」（matcher 範圍校準）。
- 依賴：Segment 0 P0-4 前置。
- 語義約束：與 S-B 共享測試形態。
- 基礎設施盤點：CC `~/.claude/settings.json`、ZCode `~/.zcode/cli/config.json`（範本 `hooks/zcode-registration.json`）兩處 matcher 字面；script 本身。
- 依賴錨點：matcher 字面 → 註冊端兩處 config ／ handler 分支 `hooks/block-memory-index-write.py:169,221`（Write/Edit 兩分支）。
- 成功標準：parity assertion 防再生＋closure receipt。

### 核心實作要點
- 移除兩處 registration 的 `|NotebookEdit`（CC settings.json、ZCode config.json＋範本同步——merge 進去非整檔覆蓋，AGENTS.md hooks 節）。
- script docstring 覆蓋邊界更新（NotebookEdit 明載 out-of-scope）。
- **parity assertion**：單元測試解析兩處註冊範本的 matcher 字面集合，斷言 ⊆ handler 分支集合（`{"Write","Edit"}`）——未來再加 matcher 字面而無分支＝測試紅，防 dead-matcher 再生。

### Pseudo Code
```
# tests/test_matcher_parity.py
def test_matcher_lives_within_handler_branches():
    matchers = parse_matchers(hooks/zcode-registration.json) ∪ parse(~/.claude/settings.json hooks 段) ∪ parse(~/.zcode/cli/config.json hooks 段)  # live config 為 enforcement 面；檔缺席→skip＋marker live-config-absent，不得靜默綠
    handled = {"Write", "Edit"}  # 由 script 分支 rg 機械抽取，非手寫
    assert matchers <= handled
```

### 驗證策略（closure 三層閘 receipt）
- **AC-C1（Existence）**：`rg "NotebookEdit" hooks/ ~/.claude/settings.json ~/.zcode/cli/config.json` 對 registration 段零命中；docstring 命中限 `out-of-scope` 字行（`rg -n "NotebookEdit.*out-of-scope"` ≥1）；`ls tests/test_matcher_parity.py` → 在場。
- **AC-C2（Invocation）**：parity 測試綠（`uv run pytest tests/test_matcher_parity.py`）——三來源（範本＋CC settings＋ZCode live config）matcher 集合可被解析且 ⊆ handler 分支；live config 缺席時 skip＋標記，不得靜默綠。
- **AC-C3（Behavior）**：合成 Write/Edit payload 各一 → 擋面不因 matcher 縮減而回歸（重跑 S-B AC-B3/B4 即可，receipt 共用）。
- **AC-C4（防再生）**：人工在範本加回 `NotebookEdit` → parity 測試轉紅（negative 驗證測試本身有效，還原後綠）。
- 已知未覆蓋：真 NotebookEdit 工具事件（本 seat 無工具——coverage matrix 該格維持 `unsupported` 並文件化，不得標 covered）。

---

## S-D｜staging 落地（auto-memory 導流）＋91 條 reviewed admission

### Context
- 決策（卡 Plan ②，勿重辯）：auto-memory 產物永不自動進池、永不自動進 inbox；晉升＝pull 逐條重寫六問形狀＋provenance 標籤。staging 形態二選一：(a) 拆 symlink→ZCode 原生目錄即 staging；(b) symlink 改指 `.agents/memory-auto/`（repo 內 staging、gitignored）＋變體 (c) memory-auto/MEMORY.md symlink 連池 index。
- **形態拍板輸入＝Segment 0 P0-3**（關閉 auto-memory 回退驗證＋背景寫入者是否寫 index）——落地當日記錄理由於卡 notes。
- 現況事實：池 dirty 91 檔（FP P4）、reconciler `HEAD＝approved` 前提目前為假。
- UC 引用：實作「staging＋單向晉升」「reviewed admission（91 條）」。
- 依賴：S-A/S-B/S-C 先行（先堵後清——堵完才清 stock，防 moving target；P0-3 前置）。建議 S-A/B/C 全收斂、user 人裁分診表後才動池。
- 語義約束：與 S-B 共享「後綴擋」——退役處置的暫時性寫入不得被後綴擋誤傷（S-B 已設「只擋新建」對齊）。
- 基礎設施盤點：`scripts/reconcile_memory_pool.py`（唯讀對帳，exit 0/1/2）；分診表（開工時複製為任務家 `references/consolidation-triage.md`——持久副本，源檔 `.agent-tmp/` 在清淤區）；池 git（自帶）；wt-open/close 的池 symlink 敘述（air-100 notes 0916 要點③——若形態 (b) 動 `.agents/memory*` symlink 族，`scripts/wt-open.sh` 相關敘述同步檢查）。
- 依賴錨點：symlink 現況 → ZCode memory dir 雙跳指 `.agents/memory/`（實際 readlink 以落地時為準，落地段先記錄現值）；reconciler POOL_REL `scripts/reconcile_memory_pool.py:34`。
- 成功標準：staging 生效後 auto-memory 寫入不進池 git 歷史；91 條全處置留痕；reconcile 對池 exit 0。

### 核心實作要點
- **cutover snapshot**（第一步，凍結 moving target）：處置開始前對池 working tree 現況快照存任務家 `references/cutover-snapshot.txt`（清單＋mtime），之後 delta 以此為對照。
- **staging 形態**（P0-3 結果定）：
  - (a) 拆 ZCode 雙跳 symlink→原生目錄；AGENTS.md 路由行（pull 面）不動；池 HEAD 恢復乾淨。
  - (b) symlink 改指 `.agents/memory-auto/`（gitignored）＋(c) 其 MEMORY.md symlink 連池投影（若 P0-3 證實背景寫入者不寫 index 才可用 (c)；否則手寫指針 fallback，air-100 notes 0915 方案）。
- **91 條 reviewed admission**：user 人裁分診表（退役 22／拆分 4／A 誤置 5 指針化）後逐筆執行——收編（過六問重寫＋commit）、修寫後收編（desc 壓 ≤100 等）、退役（`git rm` 留痕）、拆分（抽出 feedback/開卡承接）；處置表落任務家 `references/disposition-91.md`（每條 disposition＋證據：commit hash／卡 notes 指針／刪除 hash）。
- **污染基線重審**：`git log -S originSessionId -- .agents/memory/` 定量後逐條重審（卡 Plan ③）。
- 池鐵律：僅增補 commit，禁 force/reset/git clean；untracked 處置全程留痕。

### Pseudo Code（程序性）
```
0. 分診表持久化：`cp .agent-tmp/guides-refactoring/consolidation-triage.md references/consolidation-triage.md`——人裁與銷帳以持久副本為準
1. cutover snapshot → references/cutover-snapshot.txt
2. staging 手術（形態 a/b 按 P0-3；記理由卡 notes；(b) 檢查 wt-open.sh 池 symlink 敘述）
3. 91 條逐筆（按 user 人裁）：收編/修寫/退役/拆分 → disposition-91.md 銷帳（每筆一列：id→disposition→證據）
4. 污染基線 git log -S originSessionId 重審（同處置路徑）
5. regen index：`uv run python .agents/memory/_generate_index.py`（或 Stop hook 自動）
6. reconcile 驗收
```

### 驗證策略
- **AC-D1（staging 生效，TC-6 P6-1）**：staging 手術後觸發（或等待）一次 auto-memory 背景寫入 → 寫入落 staging 路徑、池 `git status --porcelain` 對該寫入零 delta。誘發程序寫死＝新開 ZCode session 並觸發收尾蒸餾（或等一個自然 session 結束），不得以『無寫入』替代觀察。
- **AC-D2（池基線恢復，TC-6 P6-2）**：91 條處置完＋index regen 後 `uv run python scripts/reconcile_memory_pool.py /Users/ctai/Github/ai-guide` → exit 0（或殘留全為處置日後新流入且明列於 disposition 表尾）。
- **AC-D3（處置留痕）**：`wc -l references/disposition-91.md` → 91+ 條全銷帳；每條帶證據欄非空（rg 抽查）。
- **AC-D4（開場注入）**：形態落地後新開 ZCode session → 開場注入吃到預期 index（(c) 成功）或指針 MEMORY.md（(a)/(fallback)）——session 首屏可觀察，receipt 記卡 notes。
- **AC-D5（晉升程序在場）**：`rg -n "晉升|memory-auto" skills/memory-audit/SKILL.md` → pull 式晉升程序條文（staging→六問重寫→provenance 標籤）在場。
- **AC-D6（池 git 純增補）**：`git -C .agents/memory log --diff-filter=D --since=<cutover日>` 對照 disposition 表——刪除全對應「退役」處置，無整池 reset 痕跡（`reflog` 抽查）。
- 已知未覆蓋：muse teardown 直寫（prevention 機制上不可能，reconcile detected 兜底——coverage matrix 維持 `detected`）。

---

## S-E｜approve-drift monitor cron

### Context
- muse governance plugin 每次 content update 後須重新 approve，否則閘靜默下線（fail-open 窗口）；真訊號＝`muse plugins inspect <id> --json` 的 `runtime_capabilities[].status`（`trusted_enabled`）。drift monitor 是 MM 四件套唯一缺件（mech-synthesis §2 D3）。
- UC 引用：實作「approve-drift monitor」。
- 依賴：無（XS，可最先做）。
- 語義約束：無。
- 基礎設施盤點：`deploy/`（launchd plist 版控先例 `deploy/entitlements-probe.plist`）；monitor 形態走 cron 或 launchd 擇一（先例齊）。
- 依賴錨點：`muse plugins inspect` CLI（外部）；新 `scripts/muse_approve_monitor.py`。
- 成功標準：非 trusted 時告警可觀察（TC-7）。

### 核心實作要點
- `scripts/muse_approve_monitor.py`：跑 `muse plugins inspect <plugin-id> --json` → assert `trusted_enabled` 在 `runtime_capabilities[].status`；缺失/命令失敗 → 非零 exit＋告警行（stdout／notification）。fail-closed（查不到＝告警非靜默綠）。
- 排程：deploy/ 落 plist 源（或既有 cron 面），日頻；輸出日志可回溯。

### Pseudo Code
```
main():
    j = run("muse plugins inspect muse-memory-governance --json")  # 失敗 → print 告警, exit 1
    caps = j["runtime_capabilities"]
    if not any(c["status"] == "trusted_enabled" for c in caps):
        print("[muse-approve-drift] governance plugin 非 trusted——重跑 approve（muse-plugins/memory-governance/README.md 運維節）")
        exit 1
    exit 0
```

### 驗證策略
- **AC-E1（Existence）**：`ls scripts/muse_approve_monitor.py deploy/*approve*` → 源在場；排程載體（plist/cron 條目）在場。
- **AC-E2（Behavior positive）**：現況（已 re-approve）實跑 `uv run python scripts/muse_approve_monitor.py` → exit 0。
- **AC-E3（Behavior negative，TC-7 P7-1）**：mock inspect 輸出（無 trusted_enabled）餵判定函式 → 告警行＋非零 exit（單元測試，不動真 plugin）。
- **AC-E4（排程實跑）**：排程觸發一次 → 日志出現一筆 monitor 執行紀錄。
- 已知未覆蓋：launchd 本身故障（面外）。

---

## 整合策略

- 段落執行序：**Segment 0（全部探針，架構凍結前）→ S-E（XS，獨立）∥ S-A ∥ S-B → S-C → S-D（最後，先堵後清）**。S-A/B/C 平行可（不同檔案）；S-D 依賴堵面收斂＋user 人裁。
- 整合點：S-B/S-C 共享 `tests/` pytest 基面（`tests/`＋`conftest.py`＋`test_reconcile_memory_pool.py` 實證在場，`uv run pytest`）；S-D 動 `.agents/memory*` symlink 族時檢查 `scripts/wt-open.sh` 敘述連動。
- 本 EP 自我消費 AIR-115 closure 契約：S-A/S-B/S-C 全部 AC 按三層閘（Existence／Invocation／Behavior 雙向）出證，S-A 另帶 actual-runtime receipt（codex 端實跑）、S-B 另帶 failure-path receipt（AC-B7——admission 意圖門，載體 fail-open 缺口誠實標記）——S-A admission 門帶 fail-closed failure-path（AC-A5）。
- 每段收斂即更新 coverage matrix（writer×防線，`skills/acceptance-evidence/SKILL.md` 防線標記制）：codex 格 unsupported→prevented（S-A）、後綴 invariant 格 unsupported→prevented＋crash 面 fail-open 缺口註記（S-B）、NotebookEdit 格維持 `unsupported`＋備註 out-of-scope（S-C）。聯合矩陣更新版落卡 notes。

## 明列不做（範圍外對照）

- **AIR-113**（skills fleet：domain skills 遷出、desc 瘦身、instruction-testing 去留）——零重疊：本 EP 不動 skills fleet 的 desc/結構，僅 memory-audit skill 補消費側條文（S-B AC-B6）與晉升程序（S-D AC-D5），屬本卡治理域。
- **AIR-115**（closure 契約）——已落地，本 EP 只消費不修改 `skills/acceptance-evidence/SKILL.md`。
- **AIR-116**（跨 harness 統一安裝包）——本 EP 下游收斂的新卡，禁提前吸收。
- 夜波波次腳本改造（S4/S5 per-file stability、scoped snapshot 鏈）——D5 裁決退役後 moot。
- muse plugin 重裝（已完成）、sensor `--source` 修復（已完成）、subagent 機制升級（detected-only 已拍板）。
- 不整池重寫、不做額度經濟學、不動 muse teardown prevention（機制上不可能，reconcile detected 兜底）。

## 回復方式（rollback）

- S-A：`~/.codex/config.toml` 移除 hooks 段即回復；script 留 `hooks/` 無接線＝dead but harmless（回收隨收案）。
- S-B：後綴分支獨立 commit，`git revert` 該 commit 即回復；既有 desc 檢查不觸。
- S-C：matcher 字面加回兩處 registration 即回復（parity 測試會轉紅——回復屬人工決策，紅燈即提示）。
- S-D：staging symlink 手術前記錄現值（readlink 輸出落卡 notes）——回復＝按現值重建 symlink；池 git 僅增補，退役條目可由 git 歷史找回（處置表記刪除 hash）。
- S-E：移除排程載體＋保留 script 即停用。

## 給 implement LLM 的接手入口

- 進場＝讀本 EP＋air-100 卡＋`ai-analysis/reports/guides-refactoring/air100-handoff.md`（調查 digest）。`.agent-tmp/guides-refactoring/` 為暫存區，弧後會清——引用以 handoff＋`sources/` 為持久源。
- **Red lines**：🚫 禁 deploy（`scripts/deploy_agents.py`——本 EP 不觸 bundle 部署面，rules 若有改由 user 走部署紀律）；🚫 autonomous 禁 commit（收斂後交 `/commit` gate，user 確認）；🚫 禁碰 AIR-113/115/116 卡面與其範圍；🚫 池 git 禁 force/reset/clean；🚫 禁重辯 D1-D5 與卡 Plan ①-⑦。
- 開工形態：照 AGENTS.md git 慣例（branch `air-100`；控制面路徑若觸 canonical main 由 pre-commit guard 擋——hook 腳本屬控制面路徑，commit 走卡 branch）。
- Compact 壓力：每段自足（Context＋AC 帶命令）；段落收斂即結算進度，接續走 `/at`＋EP 段落。

## 收尾步驟

1. coverage matrix 更新版＋91 條處置表＋closure receipts 掛回 AIR-100 卡（`--append-notes`）；AIR-90/83 歸屬記 final summary（卡 Plan ⑤）。回寫卡 AC：A1 範圍變更（staging/晉升條文承接，quarantine allow-list 項隨 D5 作廢）、A3 註明吸收路徑（S-D 處置表銷帳＋reconcile exit 0）、A4 宣告隨 AIR-83 整併＋D5 作廢——`--append-notes` 時一併改 AC 文本＋變更理由。
2. 受影響 instruction 檔同步：AGENTS.md 觀察池路由節（codex 唯讀由紀律→機械，行文更新）；`skills/memory-audit/SKILL.md`（消費側條文＋晉升程序，AC-B6/D5 已列；訂正 :149 stale 句——AIR-85 已 Done、projection 在場，刪「尚未落地…不得據此排除」改為「projection 已落地（AIR-85），path-scoping 排除判準照 residency 三測試」）；`skills/agent-workflow/SKILL.md` spawn 前檢查清單新增：「🚫 spawned agent 禁寫記憶池面（`.agents/memory*`——含 pool／inbox／memory-auto staging）——發現類內容以最終回報交回主 session，由主 session 走 consolidation」（驗證：`rg -n "spawned agent 禁寫|禁寫.*agents/memory" skills/agent-workflow/SKILL.md` 命中）；`skills/CLAUDE.md` 索引若有 description 變動同步。
3. rules 若有被觸（預期無——本 EP 以 hooks/scripts/skill 為載體）：走 `rules/AGENTS.md` 部署紀律＋`/sync-sources` 綠。
4. `/audit-test`：對 S-B/S-C/E 單元測試與 monitor 稽核，receipt 附完成報告。
5. memory 結案蒸餾：本弧教訓蒸餾（closure 三層閘實戰消費經驗、staging 形態落地理由）——走 consolidation（唯一入池權威，D1 自我消費）。

## amendment 附錄（TC 變更判決落點）

（空——凍結後 TC 變更須記 old/new oracle＋reason＋authority 於此）




